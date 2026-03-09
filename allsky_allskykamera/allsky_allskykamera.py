'''
allsky_allskykamera.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky
'''

import importlib.util
import json
import os
import pwd
from datetime import datetime, timezone

import requests

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE


class ALLSKYALLSKYKAMERA(ALLSKYMODULEBASE):

	API_ENDPOINT = "https://allskykamera.space/api/v1/weather.php"
	ASK_SECRET_FILE = "AllSkyKamera/askutils/ASKsecret.py"

	meta_data = {
		"name": "Allsky Kamera",
		"description": "Send mapped Allsky variable data to the Allsky Kamera API",
		"module": "allsky_allskykamera",
		"version": "v1.1.0",
		"centersettings": "false",
		"testable": "true",
		"group": "Data Export",
		"events": [
			"day",
			"night",
			"periodic"
		],
		"experimental": "false",
		"arguments": {
			"apikey": "",
			"mapping": ""
		},
		"argumentdetails": {
			"apikey": {
				"required": "false",
				"description": "API Key",
				"help": "API key used to authenticate requests to the Allsky Kamera service. If not provided it will be read from the AllskyKamera installation.",
				"tab": "General",
				"secret": "true"
			},
			"mapping": {
				"required": "false",
				"description": "Kamera Mapping",
				"help": "Configure the Allsky Kamera entry and field mappings.",
				"tab": "General",
				"type": {
					"fieldtype": "allskykamera"
				}
			}
		},
		"enabled": "false",
		"changelog": {
			"v1.0.0": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial release"
				}
			],
			"v1.1.0": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Added mapping parsing via get_param()",
						"Added API key fallback from AllSkyKamera installation",
						"Added per-entry POST requests to the Allsky Kamera API"
					]
				}
			]
		}
	}

	def _parse_mapping_config(self, mapping_text):
		if mapping_text == "":
			return {"version": 1, "daily_limit": 5000, "entries": []}

		try:
			parsed_mapping = json.loads(mapping_text)
		except json.JSONDecodeError:
			parsed_mapping = mapping_text

		if isinstance(parsed_mapping, str):
			try:
				parsed_mapping = json.loads(parsed_mapping)
			except json.JSONDecodeError as error:
				self.log(0, f"ERROR: Invalid Allsky Kamera mapping JSON: {error}")
				return {"version": 1, "daily_limit": 5000, "entries": []}

		if not isinstance(parsed_mapping, dict):
			self.log(0, "ERROR: Allsky Kamera mapping must resolve to a JSON object.")
			return {"version": 1, "daily_limit": 5000, "entries": []}

		return parsed_mapping

	def _load_install_api_key(self):
		owner_name = str(allsky_shared.get_environment_variable("ALLSKY_OWNER") or "").strip()
		secret_file = ""
		module_name = "asksecret_dynamic"

		if owner_name == "":
			self.log(0, "ERROR: ALLSKY_OWNER environment variable is not set.")
			return ""

		try:
			owner_home = pwd.getpwnam(owner_name).pw_dir
		except KeyError:
			self.log(0, f"ERROR: Unable to resolve home directory for ALLSKY_OWNER '{owner_name}'.")
			return ""

		secret_file = os.path.join(owner_home, self.ASK_SECRET_FILE)

		if not os.path.isfile(secret_file):
			self.log(0, f"ERROR: Allsky Kamera secret file not found: {secret_file}")
			return ""

		try:
			spec = importlib.util.spec_from_file_location(module_name, secret_file)
			if spec is None or spec.loader is None:
				self.log(0, f"ERROR: Unable to load Allsky Kamera secret file: {secret_file}")
				return ""

			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
		except Exception as error:  # pylint: disable=broad-exception-caught
			self.log(0, f"ERROR: Failed reading Allsky Kamera secret file: {error}")
			return ""

		return str(getattr(module, "API_KEY", "")).strip()

	def _get_api_key(self):
		api_key = self.get_param("apikey", "", str, True).strip()
		if api_key != "":
			return api_key

		return self._load_install_api_key()

	def _get_current_period(self):
		tod = allsky_shared.get_value_from_debug_data('AS_DAY_OR_NIGHT')
		if tod is not None:
			tod = tod.lower()
		else:
			tod = ''
           
		return str(tod).strip().lower()

	def _should_send_entry(self, entry):
		run_at = str(entry.get("run_at", "both")).strip().lower()
		current_period = self._get_current_period()

		if run_at not in ["day", "night", "both"]:
			run_at = "both"

		if run_at == "both":
			return True

		self.log(4, f"INFO: Checking if entry with run_at='{run_at}' should run during current period '{current_period}'.")
		return current_period == run_at

	def _should_run_entry_frequency(self, entry):
		entry_name = str(entry.get("ext_sensor", "")).strip()
		frequency_minutes = entry.get("frequency_minutes", 0)
		frequency_seconds = 0
		module_key = f"{self.meta_data['module']}_{entry_name}"

		try:
			frequency_seconds = int(frequency_minutes) * 60
		except (TypeError, ValueError):
			frequency_seconds = 0

		if frequency_seconds < 1:
			frequency_seconds = 60

		should_run, diff = allsky_shared.should_run(module_key, frequency_seconds)
		if should_run or self.debug_mode:
			return True

		self.log(4, f"INFO: Skipping '{entry_name}' because only {diff:.0f}s of {frequency_seconds}s have elapsed.")
		return False

	def _coerce_numeric_value(self, raw_value):
		if raw_value is None:
			return None

		value = str(raw_value).strip()
		if value == "":
			return None

		try:
			if any(character in value for character in [".", "e", "E"]):
				return float(value)
			return int(value)
		except ValueError:
			try:
				return float(value)
			except ValueError:
				return None

	def _build_entry_payload(self, entry):
		fields_payload = {}

		for field in entry.get("fields", []):
			field_name = str(field.get("name", "")).strip()
			variable_name = str(field.get("variable", "")).strip()

			if field_name == "" or variable_name == "":
				continue

			raw_value = allsky_shared.get_allsky_variable(variable_name)
			numeric_value = self._coerce_numeric_value(raw_value)
			if numeric_value is None:
				self.log(4, f"INFO: Skipping field '{field_name}' because variable '{variable_name}' is blank or not numeric.")
				continue

			fields_payload[field_name] = numeric_value

		return {
			"timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
			"ext_sensor": str(entry.get("ext_sensor", "")).strip(),
			"fields": fields_payload
		}

	def _post_payload(self, api_key, payload):
		headers = {
			"X-API-Key": api_key,
			"Content-Type": "application/json"
		}
		self.log(4, f"INFO: Allsky Kamera payload for '{payload['ext_sensor']}':\n{json.dumps(payload, indent=4)}")

		try:
			response = requests.post(self.API_ENDPOINT, headers=headers, json=payload, timeout=30)
		except requests.RequestException as error:
			self.log(0, f"ERROR: Allsky Kamera request failed for '{payload['ext_sensor']}': {error}")
			return False

		self.log(4, f"INFO: Allsky Kamera response for '{payload['ext_sensor']}': HTTP {response.status_code}")

		if response.status_code in [200, 201]:
			self.log(4, f"INFO: Allsky Kamera payload sent for '{payload['ext_sensor']}'.")
			return True

		error_messages = {
			400: "Invalid request",
			401: "Missing or invalid API key",
			405: "Wrong HTTP method",
			429: "Too Many Requests",
			500: "Internal server error"
		}
		error_message = error_messages.get(response.status_code, f"Unexpected HTTP {response.status_code}")
		response_text = response.text.strip()
		if response_text != "":
			self.log(0, f"ERROR: Allsky Kamera API returned {response.status_code} ({error_message}) for '{payload['ext_sensor']}': {response_text}")
		else:
			self.log(0, f"ERROR: Allsky Kamera API returned {response.status_code} ({error_message}) for '{payload['ext_sensor']}'.")

		return False

	def run(self):
		mapping_text = self.get_param("mapping", "", str, True)
		mapping_config = self._parse_mapping_config(mapping_text)
		api_key = self._get_api_key()
		entries = mapping_config.get("entries", [])
		sent_count = 0
		skipped_count = 0

		if api_key == "":
			self.log(0, "ERROR: No Allsky Kamera API key available.")
			return "No Allsky Kamera API key available."

		if not isinstance(entries, list) or len(entries) == 0:
			self.log(4, "INFO: No Allsky Kamera entries configured.")
			return "No Allsky Kamera entries configured."

		for entry in entries:
			if not isinstance(entry, dict):
				continue

			if not self._should_send_entry(entry):
				skipped_count += 1
				continue

			if not self._should_run_entry_frequency(entry):
				skipped_count += 1
				continue

			payload = self._build_entry_payload(entry)
			if payload["ext_sensor"] == "":
				self.log(0, "ERROR: Skipping Allsky Kamera entry with no ext_sensor.")
				continue

			if len(payload["fields"]) == 0:
				self.log(0, f"ERROR: Skipping Allsky Kamera entry '{payload['ext_sensor']}' because it has no numeric field values.")
				continue

			if self._post_payload(api_key, payload):
				allsky_shared.set_last_run(f"{self.meta_data['module']}_{payload['ext_sensor']}")
				sent_count += 1

		result = f"Sent {sent_count} Allsky Kamera entr"
		result += "y" if sent_count == 1 else "ies"
		if skipped_count > 0:
			result += f"; skipped {skipped_count} due to schedule or day/night mode"

		self.log(4, f"INFO: {result}")
		return result


def allskykamera(params, event):
	allsky_allskykamera = ALLSKYALLSKYKAMERA(params, event)
	result = allsky_allskykamera.run()

	return result


def allskykamera_cleanup():
	moduleData = {
		"metaData": ALLSKYALLSKYKAMERA.meta_data,
		"cleanup": {
			"files": {},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)
