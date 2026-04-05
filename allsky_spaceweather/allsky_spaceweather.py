#TODO Events
'''
allsky_spaceweather.py

Part of allsky postprocess.py modules for Thomas Jacquin's AllSky.
https://github.com/AllskyTeam/allsky

This module retrieves space weather data from NOAA SWPC APIs and processes it for AllSky Overlays
'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
import requests
import json
import ephem
import pytz
import datetime

class ALLSKYSPACEWEATHER(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Space Weather",
		"description": "Retrieve space weather data from NOAA SWPC",
		"module": "allsky_spaceweather",
		"version": "v1.0.2",
		"centersettings": "false",
		"testable": "true", 
		"extradatafilename": "allsky_spaceweather.json",
		"group": "Data Capture", 
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradata": {
			"values": {
				"SWX_SWIND_SPEED": {
					"name": "${SWIND_SPEED}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "Solar wind speed",
					"type": "number"
				},
				"SWX_SWIND_DENSITY": {
					"name": "${SWIND_DENSITY}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "Solar wind density",
					"type": "number"
				},
				"SWX_SWIND_TEMP": {
					"name": "${SWIND_TEMP}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "Solar wind temperature",
					"type": "number"
				},
				"SWX_KPDATA": {
					"name": "${KPDATA}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "KP Data",
					"type": "number"
				},
				"SWX_BZDATA": {
					"name": "${BZDATA}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "BZ Data",
					"type": "number"
				},
				"SWX_S_ANGLE": {
					"name": "${S_ANGLE}",
					"format": "",
					"sample": "",
					"group": "Space",
					"description": "Sun Angle",
					"type": "number"
				}
			}                         
		}, 
		"arguments": {
			"latitude": "",
			"longitude": "",
			"period": 300,
			"filename": "spaceweather.json"
		},
		"argumentdetails": {
			"period": {
				"required": "true",
				"description": "Update Period",
				"help": "How often to fetch new data (in seconds). 300 seconds minimum (5 minutes) to avoid overloading the API.",
				"type": {
					"fieldtype": "spinner",
					"min": 300,
					"max": 3000,
					"step": 60
				}
			}
		},
		"changelog": {
			"v1.0.0": [
				{
					"author": "Jim Cauthen",
					"authorurl": "https://github.com/jcauthen78/",
					"changes": "Initial Release"
				}
			],
			"v1.0.1": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updates for new module system"
				}
			],
      "v1.0.2": [
      	{
          "author": "Jim Cauthen",
          "authorurl": "https://github.com/jcauthen78/",
          "changes": "Fixed NOAA API format handling (list-of-lists vs list-of-dicts), added per-endpoint error handling and HTTP status checks"
        }
			]     
		}
	}
    
	# ---------------------------------------------------------------------------
	# Helper: extract a value from a NOAA API record that may be either a list
	# (old format: [time_tag, val1, val2, ...]) or a dict (new format:
	# {"time_tag": "...", "Kp": "...", ...}).
	# ---------------------------------------------------------------------------
	def _get_record_value(self, record, index_or_key, key_name=None):
			"""
			Retrieve a value from a NOAA API record.
			
			Handles both formats:
				- list-of-lists:  record[index_or_key]
				- list-of-dicts:  record[key_name]  (falls back to index_or_key if key_name is None)
			
			Args:
					record:       A single data row (list or dict)
					index_or_key: Integer index for list format, or string key for dict format
					key_name:     Explicit dict key to use when record is a dict. If None,
												index_or_key is used directly (works when it's a string).
			Returns:
					The raw value (usually a string) from the record.
			"""
			if isinstance(record, dict):
					# Dict format – use the explicit key name if provided
					k = key_name if key_name is not None else index_or_key
					return record[k]
			else:
					# List format – use the integer index
					return record[index_or_key]

	def _safe_float_conversion(self, data, default='xxx'):
			"""Safely convert string to float with default value"""
			try:
					return float(data)
			except (TypeError, ValueError):
					return default

	def _fetch_json(self, url, label=""):
			"""
			Fetch JSON from a NOAA SWPC endpoint with HTTP status checking.
			
			Args:
					url:   The API URL
					label: Human-readable label for log messages
			Returns:
					Parsed JSON data (list or dict), or None on failure.
			"""
			response = requests.get(url, timeout=30)
			if response.status_code != 200:
					allsky_shared.log(0, f"ERROR: {label} API returned HTTP {response.status_code}")
					return None
			try:
					data = json.loads(response.content)
			except json.JSONDecodeError as e:
					allsky_shared.log(0, f"ERROR: {label} API returned invalid JSON: {e}")
					return None
			# Sanity check: must be a non-empty list
			if not isinstance(data, list) or len(data) < 2:
					allsky_shared.log(0, f"ERROR: {label} API returned unexpected data structure")
					return None
			return data

	def _process_solar_wind_data(self, data):
			"""Process solar wind data and return formatted values with colors"""
			# --- Get the last record, handling both list and dict formats ---
			last = data[-1]
			density = self._safe_float_conversion(data[-1][1])
			speed = self._safe_float_conversion(data[-1][2])
			temp = self._safe_float_conversion(data[-1][3])
			temp_fmt = format(temp, ',').rstrip('0').rstrip('.') if temp != 'xxx' else temp


			# Color determination logic
			density_color = "#10e310"  # default green
			if isinstance(density, float):
					if density > 6:
							density_color = "#10e310"  # green
					elif 2 <= density <= 6:
							density_color = "#ffec00"  # yellow
					else:
							density_color = "#f56b6b"  # red

			speed_color = "#10e310"  # default green
			if isinstance(speed, float):
					if speed > 550:
							speed_color = "#f56b6b"  # red
					elif 500 <= speed <= 550:
							speed_color = "#ffec00"  # yellow
					else:
							speed_color = "#10e310"  # green

			temp_color = "#808080"  # default gray
			if isinstance(temp, float):
					if temp >= 500001:
							temp_color = "#f56b6b"  # red
					elif temp >= 300001:
							temp_color = "#ffec00"  # yellow
					elif temp >= 100001:
							temp_color = "#10e310"  # green
					elif temp >= 50000:
							temp_color = "#ffec00"  # yellow
					else:
							temp_color = "#f56b6b"  # red

			return {
					"speed": {"value": speed, "color": speed_color},
					"density": {"value": density, "color": density_color},
					"temp": {"value": temp_fmt, "color": temp_color}
			}


	def run(self):
		"""Main entry point for the module"""
		result = ""
		
		# API endpoints
		urls = {
				"wind": "https://services.swpc.noaa.gov/products/solar-wind/plasma-6-hour.json",
				"kp": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
				"bz": "https://services.swpc.noaa.gov/products/solar-wind/mag-6-hour.json"
		}

		try:
				# Get period from params, enforce minimum of 300 seconds
				period = self.get_param('period', 300, int)
    
				module = self.meta_data['module']
				
				shouldRun, diff = allsky_shared.shouldRun(module, period)
				if not shouldRun:
						result = f"Last run {diff} seconds ago. Running every {period} seconds"
						allsky_shared.log(1, f"INFO: {result}")
						return result

				# Calculate sun angle
				utcnow = datetime.datetime.now(tz=pytz.UTC)
				dtUtc = utcnow.replace(microsecond=0, tzinfo=None)
				
				lat = allsky_shared.getSetting('latitude')
				lat = allsky_shared.convertLatLon(lat)
				lon = allsky_shared.getSetting('longitude')
				lon = allsky_shared.convertLatLon(lon)
						
				obs = ephem.Observer()
				obs.lat = lat
				obs.long = lon
				obs.date = dtUtc.strftime('%Y-%m-%d %H:%M:%S')

				sun = ephem.Sun(obs)
				sun.compute(obs)
				sun_angle = round(float(sun.alt) * 57.2957795, 1)

				# Initialize data dictionary
				space_weather_data = {
						"SWX_S_ANGLE": {
								"value": sun_angle,
								"expires": 0
						}
				}

				# ---------------------------------------------------------------
				# Fetch and process solar wind data
				# ---------------------------------------------------------------
				wind_data = self._fetch_json(urls["wind"], "Solar Wind")
				if wind_data is not None:
						try:
								solar_wind = self._process_solar_wind_data(wind_data)
								space_weather_data.update({
										"SWX_SWIND_SPEED": {
												"value": solar_wind["speed"]["value"],
												"fill": solar_wind["speed"]["color"],
												"expires": 0
										},
										"SWX_SWIND_DENSITY": {
												"value": solar_wind["density"]["value"],
												"fill": solar_wind["density"]["color"],
												"expires": 0
										},
										"SWX_SWIND_TEMP": {
												"value": solar_wind["temp"]["value"],
												"fill": solar_wind["temp"]["color"],
												"expires": 0
										}
								})
						except Exception as e:
								allsky_shared.log(0, f"ERROR: Failed to process solar wind data: {e}")
				
				# ---------------------------------------------------------------
				# Fetch and process Kp index
				# ---------------------------------------------------------------
				kp_data = self._fetch_json(urls["kp"], "Kp Index")
				if kp_data is not None:
						try:
								last_kp = kp_data[-1]
								# Handle both list and dict formats for Kp value
								kp_value = float(self._get_record_value(last_kp, 1, "Kp"))
								kp_color = "#10e310"  # default green
								if kp_value > 5:
										kp_color = "#f56b6b"  # red
								elif kp_value >= 4:
										kp_color = "#ffec00"  # yellow

								space_weather_data["SWX_KPDATA"] = {
										"value": kp_value,
										"fill": kp_color,
										"expires": 0
								}
						except Exception as e:
								allsky_shared.log(0, f"ERROR: Failed to process Kp data: {e}")

				# ---------------------------------------------------------------
				# Fetch and process Bz data
				# ---------------------------------------------------------------
				bz_data = self._fetch_json(urls["bz"], "Bz")
				if bz_data is not None:
						try:
								last_bz = bz_data[-1]
								# Handle both list and dict formats for Bz value
								bz_value = float(self._get_record_value(last_bz, 3, "bz_gsm"))
								bz_color = "#10e310"  # default green
								if bz_value <= -15:
										bz_color = "#f56b6b"  # red
								elif bz_value <= -6:
										bz_color = "#ffec00"  # yellow

								space_weather_data["SWX_BZDATA"] = {
										"value": bz_value,
										"fill": bz_color,
										"expires": 0
								}
						except Exception as e:
								allsky_shared.log(0, f"ERROR: Failed to process Bz data: {e}")
        
						# Save data to file
						allsky_shared.saveExtraData(self.meta_data['extradatafilename'], space_weather_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
						result = f"Space weather data successfully written to {self.meta_data['extradatafilename']}"
						self.log(1, f"INFO: {result}")
						allsky_shared.setLastRun(module)

		except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				result = f"Module spaceweather failed on line {eTraceback.tb_lineno} - {e}"
				allsky_shared.log(0, f"ERROR: {result}")

		return result

def spaceweather(params, event):
	allsky_space_weather = ALLSKYSPACEWEATHER(params, event)
	result = allsky_space_weather.run()
 
	return result

def spaceweather_cleanup():
	"""Cleanup function for the module"""
	moduleData = {
	    "metaData": ALLSKYSPACEWEATHER.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYSPACEWEATHER.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
