'''
allsky_openweathermap.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

This module will retrieve data from the Open Weather Map API

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import json
import requests
from meteocalc import heat_index
from meteocalc import dew_point, Temp

REQUEST_TIMEOUT = 15      # seconds; without it a dead connection hangs the flow
REPORT_AFTER = 3          # failed downloads in a row before it becomes a WebUI message
FAILURE_FILE = os.path.join(allsky_shared.ALLSKY_TMP, "allsky_openweathermap_failures.json")

class ALLSKYOPENWEATHERMAP(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Open Weather Map",
		"description": "Obtain weather data from the Open Weather Map service",
		"docs": "docs/allsky_modules/extra/owm.html",  
		"module": "allsky_openweathermap",
		"version": "v1.0.3",
		"centersettings": "false",
		"testable": "true",
		"extradatafilename": "allsky_openweathermap.json",
		"group": "Data Capture", 
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradata": {
			"values": {
				"AS_OWWEATHER": {
					"name": "${OWWEATHER}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Weather Summary",
					"type": "string"
				},
				"AS_OWWEATHERDESCRIPTION": {
					"name": "${OWWEATHERDESCRIPTION}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Weather Description",
					"type": "string"
				},
				"AS_OWTEMP": {
					"name": "${OWTEMP}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Temperature",
					"type": "temperature"
				},
				"AS_OWDEWPOINT": {
					"name": "${OWDEWPOINT}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Dew Point",
					"type": "temperature"
				},
				"AS_OWHEATINDEX": {
					"name": "${OWHEATINDEX}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Heat Index",
					"type": "temperature"
				},                     
				"AS_OWTEMPFEELSLIKE": {
					"name": "${OWTEMPFEELSLIKE}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Temperature Feels Like",
					"type": "temperature"
				},                                          
				"AS_OWTEMPMIN": {
					"name": "${OWTEMPMIN}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Minimum Temperature",
					"type": "temperature"
				},
				"AS_OWTEMPMAX": {
					"name": "${OWTEMPMAX}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Maximum Temperature",
					"type": "temperature"
				},
				"AS_OWPRESSURE": {
					"name": "${OWPRESSURE}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Pressue",
					"type": "number"
				},
				"AS_OWHUMIDITY": {
					"name": "${OWHUMIDITY}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Humidity",
					"type": "number"
				},
				"AS_OWWINDSPEED": {
					"name": "${OWWINDSPEED}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Wind Speed",
					"type": "number"
				},
				"AS_OWWINDGUST": {
					"name": "${OWWINDGUST}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Wind Gust",
					"type": "number"
				},         
				"AS_OWWINDDIRECTION": {
					"name": "${OWWINDDIRECTION}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Wind Direction",
					"type": "azimuth"
				},
				"AS_OWWINDCARDINAL": {
					"name": "${OWWINDCARDINAL}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Cardinal Wind Direction",
					"type": "azimuth"
				},
				"AS_OWCLOUDS": {
					"name": "${OWCLOUDS}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Cloud Cover %",
					"type": "number"
				},
				"AS_OWRAIN1HR": {
					"name": "${OWRAIN1HR}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW mm of rain in the last hour",
					"type": "number"
				},
				"AS_OWRAIN3HR": {
					"name": "${OWRAIN3HR}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW mm of rain in the last hour",
					"type": "number"
				},
				"AS_OWSUNRISE": {
					"name": "${OWSUNRISE}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Sunrise",
					"type": "string"
				},
				"AS_OWSUNSET": {
					"name": "${OWSUNSET}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "OW Sunrise",
					"type": "string"
				}                                                                                                              
			}                         
		},
		"arguments":{
			"apikey": "",
			"period": 120,
			"expire": 240,
			"units": "metric"
		},
		"argumentdetails": {
			"apikey": {
				"required": "true",
				"description": "API Key",
				"secret": "true",         
				"help": "Your Open Weather Map API key."
			},      
			"period" : {
				"required": "true",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day.",
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				}          
			},
			"units" : {
				"required": "false",
				"description": "Units",
				"help": "Units of measurement. standard, metric and imperial.",
				"type": {
					"fieldtype": "select",
					"values": "standard,metric,imperial"
				}                
			},        
			"expire" : {
				"required": "true",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value.",
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				}          
			}                    
		},
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.1" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Added Cardinal wind direction",
						"Converted to f-strings",
						"Improved error handling"
					]
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updated for new module system"
				}
			],
			"v1.0.3" : [
				{
					"author": "Benjamin Hartwich",
					"authorurl": "https://astronomy.garden",
					"changes": [
						"The download times out after 15 seconds instead of waiting forever",
						"A failed download because of the network (no connection, DNS, timeout) is logged as a warning; only 3 failures in a row become a WebUI error message, once until the next successful download",
						"The API key is hidden in error messages; the network errors contained the full URL with the key"
					]
				}
			]
		}            
	}

	_extra_data = {}
 
	def _process_result(self, data, expires, units):
		#rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
		#data = json.loads(rawData)
		try:
			self._set_extra_value('weather.main', data, 'OWWEATHER', expires)
			self._set_extra_value('weather.description', data, 'OWWEATHERDESCRIPTION', expires)

			self._set_extra_value('main.temp', data, 'OWTEMP', expires)
			self._set_extra_value('main.feels_like', data, 'OWTEMPFEELSLIKE', expires)
			self._set_extra_value('main.temp_min', data, 'OWTEMPMIN', expires)
			self._set_extra_value('main.temp_max', data, 'OWTEMPMAX', expires)
			self._set_extra_value('main.pressure', data, 'OWPRESSURE', expires)
			self._set_extra_value('main.humidity', data, 'OWHUMIDITY', expires)

			self._set_extra_value('wind.speed', data, 'OWWINDSPEED', expires)
			self._set_extra_value('wind.deg', data, 'OWWINDDIRECTION', expires)
			self._set_extra_value('wind.gust', data, 'OWWINDGUST', expires)

			self._set_extra_value('clouds.all', data, 'OWCLOUDS', expires)

			self._set_extra_value('rain.1hr', data, 'OWRAIN1HR', expires)
			self._set_extra_value('rain.3hr', data, 'OWRAIN3HR', expires)

			self._set_extra_value('sys.sunrise', data, 'OWSUNRISE', expires)
			self._set_extra_value('sys.sunset', data, 'OWSUNSET', expires)

			temperature = float(self._get_value('main.temp', data))
			humidity = float(self._get_value('main.humidity', data))
			if units == 'imperial':
				t = Temp(temperature, 'f')
				the_dew_point = dew_point(t, humidity).f
				the_heat_index = heat_index(t, humidity).f

			if units == 'metric':
				the_dew_point = dew_point(temperature, humidity).c
				the_heat_index = heat_index(temperature, humidity).c

			if units == 'standard':
				the_dew_point = dew_point(temperature, humidity).k
				the_heat_index = heat_index(temperature, humidity).k

			degress = self._get_value('wind.deg', data)
			cardinal = allsky_shared.create_cardinal(degress)

			self._extra_data['AS_OWWINDCARDINAL'] = {
				'value': cardinal,
				'expires': expires
			}
						
			self._extra_data['AS_OWDEWPOINT'] = {
				'value': round(the_dew_point, 1),
				'expires': expires
			}
				
			self._extra_data['AS_OWHEATINDEX'] = {
				'value': round(the_heat_index, 1),
				'expires': expires
			}
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(0, f'ERROR in {__file__}: Module openweathermap failed on line {eTraceback.tb_lineno} - {e}')
   
	def _set_extra_value(self, path, data, extra_key, expires):
		value = self._get_value(path, data)
		if value is not None:
			self._extra_data['AS_' + extra_key] = {
				'value': value,
				'expires': expires
			}

	def _hide_key(self, text, api_key):
		"""Error texts from requests contain the full URL, including the API key.
		They end up in the log and the WebUI's messages, so hide the key."""
		if api_key:
			text = text.replace(api_key, allsky_shared.obfuscate_secret(api_key))
		return text

	def _read_failures(self):
		try:
			with open(FAILURE_FILE) as fh:
				return json.load(fh)
		except Exception:
			return {"count": 0, "reported": False}

	def _network_ok(self):
		if os.path.exists(FAILURE_FILE):
			try:
				os.remove(FAILURE_FILE)
			except OSError:
				pass

	def _network_error(self, message):
		"""Count failed downloads in a row. The first few are logged as warnings only;
		from REPORT_AFTER in a row it is reported once as an error (WebUI message),
		and again only after a successful download."""
		failures = self._read_failures()
		failures["count"] = failures.get("count", 0) + 1
		result = f'Could not reach Open Weather Map ({failures["count"]} in a row): {message}'
		if failures["count"] >= REPORT_AFTER and not failures.get("reported"):
			failures["reported"] = True
			self.log(0, f'ERROR in {__file__}: {result}')
		else:
			self.log(1, f'WARNING in {__file__}: {result}')
		try:
			with open(FAILURE_FILE, "w") as fh:
				json.dump(failures, fh)
		except OSError:
			pass
		return result

	def _get_value(self, path, data):
		result = None
		keys = path.split(".")
		if keys[0] in data:
			sub_data = data[keys[0]]
			
			if isinstance(sub_data, list):        
				if keys[1] in sub_data[0]:
					result = sub_data[0][keys[1]]
			else:
				if keys[1] in sub_data:
					result = sub_data[keys[1]]

		return result

	def run(self):
		result = ""

		period = self.get_param('period', 120, int)
		expire = self.get_param('expire', 240, int)
		api_key = self.get_param('apikey', '', str)
		requested_units = self.get_param('units', 'metric', str)
		module = self.meta_data['module']
  
		try:
			should_run, diff = allsky_shared.shouldRun(module, period)
			if should_run or self.debugmode:
				if api_key != "":
					lat, lon = allsky_shared.get_lat_lon()
					if lat is not None and lon is not None:
						try:
							api_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={requested_units}&appid={api_key}'
							log_api_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={requested_units}&appid={allsky_shared.obfuscate_secret(api_key)}'
							self.log(4, f'INFO: URL - {log_api_url}')
							response = requests.get(api_url, timeout=REQUEST_TIMEOUT)
							if response.status_code == 200:
								raw_data = response.json()
								self._process_result(raw_data, expire, requested_units)
								allsky_shared.saveExtraData(self.meta_data['extradatafilename'], self._extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
								result = f"Data acquired and written to extra data file {self.meta_data['extradatafilename']}"
								self.log(4, f'INFO: {result}')
								self._network_ok()
							else:
								result = f'Got error from Open Weather Map API. Response code {response.status_code}'
								self.log(0, f'ERROR in {__file__}: {result}')
						except requests.exceptions.RequestException as e:
							# no network, DNS failure, timeout: usually a short outage of the Pi's
							# connection, so only report it in the WebUI when it keeps happening
							result = self._network_error(self._hide_key(str(e), api_key))
						except Exception as e:
							eType, eObject, eTraceback = sys.exc_info()
							result = f'ERROR: Failed to download Open Weather Map data {eTraceback.tb_lineno} - {self._hide_key(str(e), api_key)}'
							self.log(0, f'ERROR in {__file__}: {result}')
					else:
						result = 'Invalid Latitude/Longitude. Check the Allsky configuration'
						self.log(0, f'ERROR in {__file__}: {result}')
				
				else:
					result = 'Missing Open Weather Map API key'
					self.log(0, f'ERROR in {__file__}: {result}')


				allsky_shared.setLastRun(module)
			else:
				result = f'Last run {diff} seconds ago. Running every {period} seconds'
				self.log(4, f'INFO: {result}')

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(0, f"ERROR in {__file__}: Module openweathermap failed on line {eTraceback.tb_lineno} - {e}")    
			
		return result

def openweathermap(params, event):
	allsky_openweathermap = ALLSKYOPENWEATHERMAP(params, event)
	result = allsky_openweathermap.run()

	return result   

def openweathermap_cleanup():
	moduleData = {
	    "metaData": ALLSKYOPENWEATHERMAP.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYOPENWEATHERMAP.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
