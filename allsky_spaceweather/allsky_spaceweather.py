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
		"version": "v1.0.1",
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
			"v1.0.0": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updates for new module system"
				}
			]     
		}
	}

	_urls = {
		"wind": "https://services.swpc.noaa.gov/products/solar-wind/plasma-6-hour.json",
		"kp": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
		"bz": "https://services.swpc.noaa.gov/products/solar-wind/mag-6-hour.json"
	}
    
	_GREEN = '#10e310'
	_RED = '#f56b6b'
	_YELLOW = '#ffec00'
        
	def _get_color(self, value, ranges, colors):
		"""Helper function to determine color based on value ranges"""
		for i in range(len(ranges) - 1):
			if ranges[i] <= value < ranges[i+1]:
				return colors[i]
		return colors[-1]

	def _safe_float_conversion(self, data, default='xxx'):
		"""Safely convert string to float with default value"""
		try:
			return float(data)
		except (TypeError, ValueError):
			return default

	def _process_solar_wind_data(self, data):
		"""Process solar wind data and return formatted values with colors"""
		density = self._safe_float_conversion(data[-1][1])
		speed = self._safe_float_conversion(data[-1][2])
		temp = self._safe_float_conversion(data[-1][3])
		temp_fmt = format(temp, ',').rstrip('0').rstrip('.') if temp != 'xxx' else temp

		# Color determination logic
		density_color = self._GREEN
		if isinstance(density, float):
			if density > 6:
				density_color = self._GREEN
			elif 2 <= density <= 6:
				density_color = self._YELLOW
			else:
				density_color = self._RED

		speed_color = self._GREEN
		if isinstance(speed, float):
			if speed > 550:
				speed_color = self._RED
			elif 500 <= speed <= 550:
				speed_color = self._YELLOW
			else:
				speed_color = self._GREEN

		temp_color = "#808080"  # default gray
		if isinstance(temp, float):
			if temp >= 500001:
				temp_color = self._RED
			elif temp >= 300001:
				temp_color = self._YELLOW
			elif temp >= 100001:
				temp_color = self._GREEN
			elif temp >= 50000:
				temp_color = self._YELLOW
			else:
				temp_color = self._RED

		return {
			"speed": {"value": speed, "color": speed_color},
			"density": {"value": density, "color": density_color},
			"temp": {"value": temp_fmt, "color": temp_color}
		}

	def run(self):
		"""Main entry point for the module"""
		result = ''
		
		period = self.get_param('period', 300, int)  
  
		try:
			# Get period from params, enforce minimum of 300 seconds
			module = self.meta_data['module']
			
			shouldRun, diff = allsky_shared.shouldRun(module, period)
			if not shouldRun and not self._debugmode:
				result = f'Last run {diff} seconds ago. Running every {period} seconds.'
				self.log(4, f'INFO: {result}')
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

			# Fetch and process solar wind data
			response = requests.get(self._urls['wind'])
			wind_data = json.loads(response.content)
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

			# Fetch and process Kp index
			response = requests.get(self._urls['kp'])
			kp_data = json.loads(response.content)
			kp_value = float(kp_data[-1][1])
			kp_color = self._GREEN
			if kp_value > 5:
				kp_color = self._RED
			elif kp_value >= 4:
				kp_color = self._YELLOW

			space_weather_data["SWX_KPDATA"] = {
				"value": kp_value,
				"fill": kp_color,
				"expires": 0
			}

			# Fetch and process Bz data
			response = requests.get(self._urls['bz'])
			bz_data = json.loads(response.content)
			bz_value = float(bz_data[-1][3])
			bz_color = self._GREEN
			if bz_value <= -15:
				bz_color = self._RED
			elif bz_value <= -6:
				bz_color = self._YELLOW

			space_weather_data["SWX_BZDATA"] = {
				"value": bz_value,
				"fill": bz_color,
				"expires": 0
			}

			# Save data to file
			allsky_shared.saveExtraData(self.meta_data['extradatafilename'], space_weather_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
			result = f"Space weather data successfully written to {self.meta_data['extradatafilename']}"
			self.log(1, f"INFO: {result}")
			allsky_shared.setLastRun(module)

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f"Module spaceweather failed on line {eTraceback.tb_lineno} - {e}"
			self.log(0, f"ERROR in {__file__: {result}")

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
