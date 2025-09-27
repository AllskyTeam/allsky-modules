#TODO Events
'''
allsky_weatherunderground.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from the WeatherUnderground API

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
from wunderground_pws import WUndergroundAPI, units

class ALLSKYWEATHERUNDERGROUND(ALLSKYMODULEBASE):

	meta_data = {
		"name": "WeatherUnderground",
		"description": "Obtains weather data from WeatherUnderground",
		"module": "allsky_weatherunderground",
		"version": "v1.0.1",   
		"events": [
			"day",
			"night",
			"periodic"
		],
		"group": "Data Capture",
		"centersettings": "false",
		"testable": "true",
		"extradatafilename": "allsky_weatherunderground.json",
		"extradata": {              
			"values": {
				"AS_WUSTATIONID": {
					"name": "${WUSTATIONID}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Station ID",
					"type": "string"
				},
				"AS_WUELEVATION": {
					"name": "${WUELEVATION}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Station Elevation",
					"type": "number"
				},
				"AS_WUQNH": {
					"name": "${WUELEVATION}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Atmospheric pressure at mean sea level",
					"type": "number"
				},
				"AS_WUQFE": {
					"name": "${WUELEVATION}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Atmospheric pressure at station",
					"type": "number"
				},                              
				"AS_WUOBSTIME": {
					"name": "${WUOBSTIME}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Observation Date/Time (Local)",
					"type": "string"
				},
				"AS_WURADIATION": {
					"name": "${WURADIATION}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Solar Radiation",
					"type": "number"
				},
				"AS_WUUV": {
					"name": "${WUUV}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU UV Level",
					"type": "number"
				},
				"AS_WUTEMP": {
					"name": "${WUTEMP}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Temperature",
					"type": "temperature"
				},
				"AS_WUHEATINDEX": {
					"name": "${WUHEATINDEX}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Heat Index",
					"type": "temperature"
				},
				"AS_WUDEWPOINT": {
					"name": "${WUDEWPOINT}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Dew Point",
					"type": "temperature"
				},
				"AS_WUWINDDIR": {
					"name": "${WUWINDDIR}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Wind Direction",
					"type": "azimuth"
				},
				"AS_WUWINDCARDINAL": {
					"name": "${WUWINDCARDINAL}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Cardinal Wind Direction",
					"type": "string"
				},         
				"AS_WUWINDSPEED": {
					"name": "${WUWINDSPEED}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Wind Speed",
					"type": "number"
				},
				"AS_WUWINDGUST": {
					"name": "${WUWINDGUST}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Wind Gust",
					"type": "number"
				},                   
				"AS_WUWINDCHILL": {
					"name": "${WUWINDCHILL}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Wind Chill",
					"type": "temperature"
				},
				"AS_WUPRECIPRATE": {
					"name": "${WUPRECIPRATE}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Precipitation Rate",
					"type": "number"
				},
				"AS_WUPRECIPTOTAL": {
					"name": "${WUPRECIPTOTAL}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "WU Precipitation Total",
					"type": "number"
				}       
			}
		},
		"arguments": {
			"apikey": "",
			"stationid": "",
			"period": 120,
			"units": "metric"
		},
		"argumentdetails": {
			"apikey": {
				"required": "true",
				"description": "API Key",
				"secret": "true",
				"help": "Your WeatherUnderground API key"         
			},
			"stationid": {
				"required": "true",
				"description": "Station ID",
				"secret": "true",
				"help": "Your WeatherUnderground station ID"
			},      
			"period" : {
				"required": "true",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
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
				"help": "Units of measurement. SI, metric, imperial and hybrid",
				"type": {
					"fieldtype": "select",
					"values": "metric_si,metric,imperial,uk_hybrid"
				}                
			}        
		},
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Michel Moriniaux",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.0": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updates for new module system"
				}
			]     
		}            
	}


	_extra_data = {}

	def _process_result(self, units, data):
		self._extra_data['AS_WUSTATIONID'] = data['stationID']
		self._extra_data['AS_WUOBSTIME'] = data['obsTimeLocal']
		self._extra_data['AS_WURADIATION'] = data['solarRadiation']
		self._extra_data['AS_WUUV'] = data['uv']
		self._extra_data['AS_WUWINDDIR'] = data['winddir']
		self._extra_data['AS_WUWINDCARDINAL'] = allsky_shared.create_cardinal(data['winddir'])
		self._extra_data['AS_WUTEMP'] = data[units]['temp']
		self._extra_data['AS_WUHEATINDEX'] = data[units]['heatIndex']
		self._extra_data['AS_WUDEWPOINT'] = data[units]['dewpt']
		self._extra_data['AS_WUWINDCHILL'] = data[units]['windChill']
		self._extra_data['AS_WUWINDGUST'] = data[units]['windGust']
		self._extra_data['AS_WUWINDSPEED'] = data[units]['windSpeed']
		self._extra_data['AS_WUPRECIPRATE'] = data[units]['precipRate']
		self._extra_data['AS_WUPRECIPTOTAL'] = data[units]['precipTotal']
		self._extra_data['AS_WUELEVATION'] = data[units]['elev']
		self._extra_data['AS_WUQNH'] = data[units]['pressure']
		if units == 'uk_hybrid':
			self._extra_data['AS_WUQFE'] = float(self._extra_data['AS_WUQNH']) - (1.0988 * float(self._extra_data['AS_WUELEVATION']) / 30)
		if 'metric' in units:
			self._extra_data['AS_WUQFE'] = float(self._extra_data['AS_WUQNH']) - (0.12 * float(self._extra_data['AS_WUELEVATION']))
		else:
			self._extra_data['AS_WUQFE'] = float(self._extra_data['AS_WUQNH']) - (0.97 * float(self._extra_data['AS_WUELEVATION']) / 900)

	def run(self):   
		result = ''

		period = self.get_param('period', 120, int)
		api_key = self.get_param('apikey', '', str)
		station_id = self.get_param('stationid', '', str)
		requested_units = self.get_param('units', 'metric', str)
		module = self.meta_data['module']
		
		if requested_units == 'metric':
			unit = units.METRIC_UNITS
		if requested_units == 'metric_si':
			unit = units.METRIC_SI_UNITS
		if requested_units == 'imperial':
			unit = units.ENGLISH_UNITS
		if requested_units == 'uk_hybrid':
			unit = units.HYBRID_UNITS

		try:
			shouldRun, diff = allsky_shared.shouldRun(module, period)
			if shouldRun or self.debugmode:
				if api_key != '':
					if station_id != '':
						try:
							message = f'Connecting using station id: {allsky_shared.obfuscate_secret(station_id)} api key: {allsky_shared.obfuscate_secret(api_key)}'
							allsky_shared.log(4, f'INFO: {message}')
							wu = WUndergroundAPI(api_key=api_key, default_station_id=station_id, units=unit)
							response = wu.current()['observations'][0]
							self._process_result(requested_units, response)
							allsky_shared.saveExtraData(self.meta_data['extradatafilename'], self._extra_data, self.meta_data['module'], self.meta_data['extradata'])
							result = f"Data acquired and written to extra data file {self.meta_data['extradatafilename']}"
							allsky_shared.log(4, f'INFO: {result}')
						except Exception as e:
							eType, eObject, eTraceback = sys.exc_info()
							result = f'ERROR: Failed to download weather underground data {eTraceback.tb_lineno} - {e}'
							allsky_shared.log(0, result)
					else:
						result = 'Missing WeatherUnderground Station ID'
						allsky_shared.log(0, f'ERROR: {result}')
				else:
					result = 'Missing WeatherUnderground API key'
					allsky_shared.log(0, f'ERROR: {result}')
				allsky_shared.setLastRun(module)
			else:
				result = f'Last run {diff} seconds ago. Running every {period} seconds'
				allsky_shared.log(1, f'INFO: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'Module weatherunderground failed on line {eTraceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')
			
		return result

def weatherunderground(params, event):
	allsky_weatherunderground = ALLSKYWEATHERUNDERGROUND(params, event)
	result = allsky_weatherunderground.run()

	return result  

def weatherunderground_cleanup():
	moduleData = {
	    "metaData": ALLSKYWEATHERUNDERGROUND.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYWEATHERUNDERGROUND.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
