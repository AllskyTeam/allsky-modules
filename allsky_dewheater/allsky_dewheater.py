'''
allsky_dewheater.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Changelog
v1.0.1 by Damian Grocholski (Mr-Groch)
- Added extra pin that is triggered with heater pin
- Fixed dhtxxdelay (was not implemented)
- Fixed max heater time (was not implemented)
V1.0.2 by Alex Greenland
- Updated code for pi 5
V1.0.3 by Alex Greenland
- Add AHTx0 i2c sensor
V1.0.4 by Andreas Schminder 
- Added Solo Cloudwatcher
'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import time
import sys
import os
import json
import urllib.request
import requests
import json
import subprocess
from meteocalc import heat_index
from meteocalc import dew_point, Temp
import board
import adafruit_sht31d
import adafruit_dht
import adafruit_ahtx0
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_htu21d import HTU21D
from meteocalc import heat_index
from meteocalc import dew_point
import time
from datetime import datetime, timedelta

class ALLSKYDEWHEATER(ALLSKYMODULEBASE):

	meta_data = {
		"name": "AllSky Dew Heater Control",
		"description": "Controls a dew heater via a temperature and humidity sensor",
		"module": "allsky_dewheater",
		"version": "v1.0.8",
		"events": [
			"periodic",
			"day",
			"night"
		],
		"experimental": "false",
		"testable": "true",
		"centersettings": "false",
		"dependency": "allsky_temp.py",
		"group": "Environment Control",
		"deprecation": {
			"fromversion": "v2024.12.06_01",
			"removein": "TBC",
			"notes": "All sensors apart from the 'allsky' sensor will be removed in future updates. Please use the 'allsky environment' module to define any sensors you require. Please see the Allsky help for more information",
			"deprecated": "false",
			"partial": "true"
		},   
		"extradatafilename": "allsky_dew.json",
        "graphs": {
            "chart1": {
				"icon": "fa-solid fa-temperature-arrow-up",
				"title": "Dew Heater",
				"group": "Environment",    
				"main": "true",    
				"config": {
					"chart": {
						"type": "spline",
						"zooming": {
							"type": "x"
						}
					},
					"title": {
						"text": "Temperature, Dew Point, Humidity, Duty Cycle"
					},
					"lang": {
						"noData": "No data available"
					},
					"noData": {
						"style": {
							"fontWeight": "bold",
							"fontSize": "16px",
							"color": "#666"
						}
					},
					"xAxis": {
						"type": "datetime",
						"dateTimeLabelFormats": {
							"day": "%Y-%m-%d",
							"hour": "%H:%M"
						}
					},
					"yAxis": [
						{ 
							"title": {
								"text": "Temperature & Dew Point (°C)"
							} 
						},
						{
							"title": { 
								"text": "Humidity (%) & Duty Cycle (%)"
							}, 
							"opposite": "true"
						}
					]
				},
				"series": {
					"heater": {
						"name": "Heater",
						"yAxis": 0,
						"variable": "AS_DEWCONTROLPWMDUTYCYCLE"                 
					},
					"temperature": {
						"name": "Temperature",
						"yAxis": 1,
						"variable": "AS_DEWCONTROLAMBIENT"
					},
					"dewpoint": {
						"name": "Dew Point",                    
						"yAxis": 0,
						"variable": "AS_DEWCONTROLDEW"
					},
					"humidity": {
						"name": "Humidity",                    
						"yAxis": 1,
						"variable": "AS_DEWCONTROLHUMIDITY"
					}                
				}
			},
			"guageheater": {
				"icon": "fa-solid fa-toggle-on",
				"title": "Heater",
				"group": "Environment",
				"type": "gauge",
				"config": {
					"chart": {
						"type": "solidgauge"
					},
					"title": {
						"text": "System Status",
						"style": {
							"fontSize": "18px"
						}
					},
					"pane": {
						"center": ["50%", "85%"],
						"size": "100%",
						"startAngle": -90,
						"endAngle": 90,
						"background": {
							"backgroundColor": "#EEE",
							"innerRadius": "60%",
							"outerRadius": "100%",
							"shape": "arc"
						}
					},
					"tooltip": {
						"enabled": "false"
					},
					"yAxis": {
						"min": 0,
						"max": 1,
						"stops": [
							[0, "#DF5353"],
							[1, "#55BF3B"]
						],
						"lineWidth": 0,
						"tickWidth": 0,
						"labels": {
							"enabled": "false"
						}
					},
					"plotOptions": {
						"solidgauge": {
							"dataLabels": {
								"y": -20,
								"borderWidth": 0,
								"useHTML": "true"
							}
						}
					},
					"series": [{
						"name": "Status",
						"data": "AS_DEWCONTROLHEATERINT"
					}]
				}           
			}
		},

		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_dewheater",
    			"include_all": "true"
			},
			"values": {
				"AS_DEWCONTROLSENSOR": {
					"name": "${DEWCONTROLSENSOR}",
					"format": "",
					"sample": "",                
					"group": "Dew Heater",
					"description": "Dew Heater Sensor",
					"type": "string"
				},              
				"AS_DEWCONTROLAMBIENT": {
					"name": "${DEWCONTROLAMBIENT}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Ambient",
					"type": "temperature"
				},
				"AS_DEWCONTROLDEW": {
					"name": "${DEWCONTROLDEW}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew heater Dew Point",
					"type": "temperature"
				},
				"AS_DEWCONTROLHUMIDITY": {
					"name": "${DEWCONTROLHUMIDITY}",
					"format": "{dp=2|per}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Humidity",
					"type": "number"
				},
				"AS_DEWCONTROLHEATER": {
					"name": "${DEWCONTROLHEATER}",
					"format": "{onoff}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Status",
					"type": "gpio"
				},
				"AS_DEWCONTROLHEATERINT": {
					"name": "${DEWCONTROLHEATERINT}",
					"format": "",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Status (int)",
					"type": "number"
				},
				"AS_DEWCONTROLPRESSURE": {
					"name": "${DEWCONTROLPRESSURE}",
					"format": "",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Pressure",
					"type": "pressure"
				},
				"AS_DEWCONTROLRELHUMIDITY": {
					"name": "${DEWCONTROLRELHUMIDITY}",
					"format": "{dp=2|per}",
					"sample": "",                  
					"group": "Dew Heater",
					"description": "Dew Heater Relative Humidity",
					"type": "number"
				},
				"AS_DEWCONTROLALTITUDE": {
					"name": "${DEWCONTROLALTITUDE}",
					"format": "",
					"sample": "",                   
					"group": "Dew Heater",
					"description": "Dew Heater Altitude",
					"type": "altitude"
				},
				"AS_DEWCONTROLPWMDUTYCYCLE": {
					"name": "${DEWCONTROLPWMDUTYCYCLE}",
					"format": "{dp=0|per}",
					"sample": "",                   
					"group": "Dew Heater",
					"description": "Dew Heater Duty Cycle",
					"type": "number"
				}
			}                         
		},
		"arguments":{
			"type": "None",
			"inputpin": "",
			"heaterpin": "",
			"extrapin": "",
			"temperature": "AS_TEMP",
			"humidity": "AS_HUMIDITY",
			"i2caddress": "",
			"heaterstartupstate": "OFF",
			"invertrelay": "False",
			"invertextrapin": "False",
			"frequency": "0",
			"limit": "10",
			"force": "0",
			"max": "0",
			"dhtxxretrycount": "2",
			"dhtxxdelay" : "500",
			"sht31heater": "False",
			"solourl": "",
			"apikey": "",
			"period": 120,
			"expire": 240,
			"filename": "openweather.json",
			"units": "metric",
			"daydisable": "False",
			"usepwm": "false",
			"pwmmin": 1,
			"pwmmax": 100,
			"extrausepwm": "false",
			"enabledebug": "False",
			"debugtemperature": 0,
			"debugdewpoint": 0
		},
		"argumentdetails": {
			"type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "select",
					"values": "None,Allsky,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,SOLO-Cloudwatcher,OpenWeather",
					"default": "None"
				}
			},
			"temperature": {
				"required": "false",
				"description": "Temperature Variable",
				"help": "The Variable to use for the temperature",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable",
					"selectmode": "multi"
				}                             
			},
			"humidity": {
				"required": "false",
				"description": "Humidity Variable",
				"help": "The Variable to use for the humidity",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable"
				}                                         
			},                
			"inputpin": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				},            
				"type": {
					"fieldtype": "gpio"
				}
			},
			"dhtxxretrycount" : {
				"required": "false",
				"description": "Retry Count",
				"help": "The number of times to retry the sensor read",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				},            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5,
					"step": 1
				}
			},
			"dhtxxdelay": {
				"required": "false",
				"description": "Delay",
				"help": "The delay between faild sensor reads in milliseconds",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 1
				}
			},          
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SHT31",
						"BME280-I2C",
						"HTU21",
						"AHTx0"
					]
				},            
				"type": {
					"fieldtype": "i2c"
				}            
			},		
			"sht31heater" : {
				"required": "false",
				"description": "Enable Heater",
				"help": "Enable the inbuilt heater on the SHT31",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SHT31"
					]
				},              
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"solourl": {
				"required": "false",
				"description": "URL from solo",
				"help": "Read weather data from lunaticoastro.com 'Solo Cloudwatcher'",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SOLO-Cloudwatcher"
					]
				}            
			},
			"owtext": {
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data",
				"tab": "Sensor",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "danger"
						}
					}
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}              						
			},        
			"apikey": {
				"required": "false",
				"description": "API Key",
				"secret": "true",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				},                       
				"help": "Your Open Weather Map API key."         
			},       
			"period" : {
				"required": "true",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				},                        
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
				"help": "Units of measurement. standard, metric and imperial",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				},                        
				"type": {
					"fieldtype": "select",
					"values": "standard,metric,imperial"
				}                
			},        
			"expire" : {
				"required": "true",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				},                                 
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				}          
			},              
			"filename": {
				"required": "true",
				"description": "Filename",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				},                       
				"help": "The name of the file that will be written to the allsky/tmp/extra directory"         
			},         
			"heaterpin": {
				"required": "false",
				"description": "Heater Pin",
				"help": "The pin the heater control relay is connected to",
				"tab": "Heater",
				"type": {
					"fieldtype": "gpio"
				}
			},
			"usepwm" : {
				"required": "false",
				"description": "Use PWM",
				"help": "Use PWM Heater control. Please see the module documentation BEFORE using this feature",
				"tab": "Heater",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"pwmmin" : {
				"required": "false",
				"description": "Min PWM Temp",
				"help": "This equates to 0% PWM duty cycle",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm",
					"filtertype": "show",
					"values": [
						"usepwm"
					]
				}      
			},
			"pwmmax" : {
				"required": "false",
				"description": "Max PWM Temp",
				"help": "This equates to 100% PWM duty cycle. This is based upon the difference between the dew point and temperature.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm",
					"filtertype": "show",
					"values": [
						"usepwm"
					]
				}         
			},   
			"extrapin": {
				"required": "false",
				"description": "Extra Pin",
				"help": "Extra pin that will be triggered with heater pin",
				"tab": "Heater",
				"type": {
					"fieldtype": "gpio"
				}
			},
			"extrausepwm" : {
				"required": "false",
				"description": "Use PWM",
				"help": "Use PWM Heater control on the extra pin. Please see the module documentation BEFORE using this feature",
				"tab": "Heater",
				"type": {
					"fieldtype": "checkbox"
				}
			},     
			"heaterstartupstate" : {
				"required": "false",
				"description": "heater Startup State",
				"help": "The initial state of the dew heater when allsky is started. This is only used if there is no previous status",
				"tab": "Heater",
				"type": {
					"fieldtype": "select",
					"values": "ON,OFF",
					"default": "OFF"
				}
			},
			"invertrelay" : {
				"required": "false",
				"description": "Invert Relay",
				"help": "Selecting this option if the relay is wired to activate on the GPIO pin going Low",
				"tab": "Heater",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"invertextrapin" : {
				"required": "false",
				"description": "Invert Extra Pin",
				"help": "Selecting this option inverts extra pin to go low when enabling heater",
				"tab": "Heater",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"frequency" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between sensor reads in seconds. Zero will disable this and run the check every time the module run",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 1000,
					"step": 1
				}
			},
			"limit" : {
				"required": "false",
				"description": "Limit",
				"help": "If the temperature is within this many degrees of the dew point the heater will be enabled or disabled",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"force" : {
				"required": "false",
				"description": "Forced Temperature",
				"help": "Always enable the heater when the ambient termperature is below this value, zero will disable this.",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"max" : {
				"required": "false",
				"description": "Max Heater Time",
				"help": "The maximum time in seconds for the heater to be on. Zero will disable this.",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 86400,
					"step": 1
				}
			},
			"daydisable" : {
				"required": "false",
				"description": "Daytime Disable",
				"help": "If checked the dew control module will be disabled during the daytime",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"enabledebug" : {
				"required": "false",
				"description": "Set Debug Mode",
				"help": "Enabling this will use the other values on this tab rather than values read from any sensor.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debugtemperature": {
				"required": "false",
				"description": "Temperature Value",
				"help": "The Variable to use for the temperature",
				"tab": "Debug",
				"filters": {
					"filter": "enabledebug",
					"filtertype": "show",
					"values": [
						"enabledebug"
					]
				},            
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"debugdewpoint": {
				"required": "false",
				"description": "Dewpoint value",
				"help": "The Variable to use for the dew point",
				"tab": "Debug",
				"filters": {
					"filter": "enabledebug",
					"filtertype": "show",
					"values": [
						"enabledebug"
					]
				},            
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"graph": {
				"required": "false",
				"tab": "History",
				"type": {
					"fieldtype": "graph"
				}
			}	   
		},
		"businfo": [
			"i2c"
		],    
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
					"author": "Damian Grocholski (Mr-Groch)",
					"authorurl": "https://github.com/Mr-Groch",
					"changes": [
						"Added extra pin that is triggered with heater pin",
						"Fixed dhtxxdelay (was not implemented)",
						"Fixed max heater time (was not implemented)"
					]
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.4" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Add AHTx0 i2c sensor"
				},            
				{
					"author": "Andreas Schminder",
					"authorurl": "https://github.com/Adler6907",
					"changes": "Added Solo Cloudwatcher"
				}
			],
			"v1.0.5" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added OpenWeather option"
				}
			],
			"v1.0.6" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added option to disable heater during the day"
				}
			],
			"v1.0.7" : [
				{
					"author": "Damian Grocholski (Mr-Groch)",
					"authorurl": "https://github.com/Mr-Groch",
					"changes": [
						"Refactored tabs for easier use",
						"Added Allsky as data source option"
					]
				}
			],
			"v1.0.8" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Refactored for new module and variable system",
						"Added PWM Control for heater pins"
					]
				}
			]                                             
		}
	}

	def _run_command (self, cmd):
		proc = subprocess.Popen(cmd,
								stdout=subprocess.PIPE,
								stderr=subprocess.PIPE,
								shell=True,
								universal_newlines=True)
		std_out, std_err = proc.communicate()
		return proc.returncode, std_out, std_err

	def _get_time_of_day(self): 
		angle = allsky_shared.get_setting('angle')
		lat = allsky_shared.get_setting('latitude')
		lon = allsky_shared.get_setting('longitude')
		tod = 'Unknown'

		try:
			cmd = f'sunwait poll exit set angle {angle} {lat} {lon}'
			returncode, stdout, stderr = self._run_command(cmd)
			
			if returncode == 2:
				tod = 'day'
			if returncode == 3:
				tod = 'night'
		except Exception:
			allsky_shared.log(0, f'ERROR running {cmd}')
		return tod 

	def _create_cardinal(self, degrees):
		try:
			cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
			cardinal = cardinals[round(degrees / 22.5)]
		except Exception:
			cardinal = 'N/A'

		return cardinal

	def _set_extra_value(self, path, data, extraKey, expires, extraData):
		value = self._get_value(path, data)
		if value is not None:
			extraData["AS_" + extraKey] = {
				"value": value,
				"expires": expires
			}

	def _get_value(self, path, data):
		result = None
		keys = path.split(".")
		if keys[0] in data:
			subData = data[keys[0]]
			
			if isinstance(subData, list):        
				if keys[1] in subData[0]:
					result = subData[0][keys[1]]
			else:
				if keys[1] in subData:
					result = subData[keys[1]]

		return result

	def _process_openweather_result(self, data, expires, units):
		extraData = {}
		#rawData = '{'coord':{'lon':0.2,'lat':52.4},'weather':[{'id':802,'main':'Clouds','description':'scattered clouds','icon':'03d'}],'base':'stations','main':{'temp':291.84,'feels_like':291.28,'temp_min':290.91,'temp_max':292.65,'pressure':1007,'humidity':58},'visibility':10000,'wind':{'speed':8.23,'deg':250,'gust':10.8},'clouds':{'all':40},'dt':1664633294,'sys':{'type':2,'id':2012440,'country':'GB','sunrise':1664603991,'sunset':1664645870},'timezone':3600,'id':2633751,'name':'Witchford','cod':200}'
		#data = json.loads(rawData)
		self._set_extra_value('weather.main', data, 'OWWEATHER', expires, extraData)
		self._set_extra_value('weather.description', data, 'OWWEATHERDESCRIPTION', expires, extraData)

		self._set_extra_value('main.temp', data, 'OWTEMP', expires, extraData)
		self._set_extra_value('main.feels_like', data, 'OWTEMPFEELSLIKE', expires, extraData)
		self._set_extra_value('main.temp_min', data, 'OWTEMPMIN', expires, extraData)
		self._set_extra_value('main.temp_max', data, 'OWTEMPMAX', expires, extraData)
		self._set_extra_value('main.pressure', data, 'OWPRESSURE', expires, extraData)
		self._set_extra_value('main.humidity', data, 'OWHUMIDITY', expires, extraData)

		self._set_extra_value('wind.speed', data, 'OWWINDSPEED', expires, extraData)
		self._set_extra_value('wind.deg', data, 'OWWINDDIRECTION', expires, extraData)
		self._set_extra_value('wind.gust', data, 'OWWINDGUST', expires, extraData)

		self._set_extra_value('clouds.all', data, 'OWCLOUDS', expires, extraData)

		self._set_extra_value('rain.1hr', data, 'OWRAIN1HR', expires, extraData)
		self._set_extra_value('rain.3hr', data, 'OWRAIN3HR', expires, extraData)

		self._set_extra_value('sys.sunrise', data, 'OWSUNRISE', expires, extraData)
		self._set_extra_value('sys.sunset', data, 'OWSUNSET', expires, extraData)

		temperature = float(self._get_value('main.temp', data))
		humidity = float(self._get_value('main.humidity', data))
		if units == 'imperial':
			t = Temp(temperature, 'f')
			dewPoint = dew_point(t, humidity).f
			heatIndex = heat_index(t, humidity).f

		if units == 'metric':
			t = Temp(temperature, 'c')        
			dewPoint = dew_point(temperature, humidity).c
			heatIndex = heat_index(temperature, humidity).c

		if units == 'standard':
			t = Temp(temperature, 'k')        
			dewPoint = dew_point(temperature, humidity).k
			heatIndex = heat_index(temperature, humidity).k

		degress = self._get_value('wind.deg', data)
		cardinal = self._create_cardinal(degress)

		extraData['AS_OWWINDCARDINAL'] = {
			'value': cardinal,
			'expires': expires
		}
					
		extraData['AS_OWDEWPOINT'] = {
			'value': round(dewPoint,1),
			'expires': expires
		}
			
		extraData['AS_OWHEATINDEX'] = {
			'value': round(heatIndex,1),
			'expires': expires
		}

		return extraData

	def _get_openweather_Value(self, field, json_data, file_modified_time):
		result = False    

		if field in json_data:
			result = json_data[field]['value']

		if 'expires' in json_data[field]:
			max_age = json_data[field]['expires']
			age = int(time.time()) - file_modified_time
			if age > max_age:
				allsky_shared.log(4, f'WARNING: field {field} has expired - age is {age}')
				result = None
				
		return result

	def _get_openwaether_values(self, file_name):
		temperature = None
		humidity = None
		pressure = None
		dewPoint = None

		allsky_path = allsky_shared.get_environment_variable('ALLSKY_HOME')
		extra_data_fileName = os.path.join(allsky_path, 'config', 'overlay', 'extra', file_name)

		if os.path.isfile(extra_data_fileName):
			file_modified_time = int(os.path.getmtime(extra_data_fileName))
			with open(extra_data_fileName,"r") as file:
				json_data = json.load(file)
				temperature = self._get_openweather_Value('AS_OWTEMP', json_data, file_modified_time)
				humidity = self._get_openweather_Value('AS_OWHUMIDITY', json_data, file_modified_time)
				pressure = self._get_openweather_Value('AS_OWPRESSURE', json_data, file_modified_time)
				dewPoint = self._get_openweather_Value('AS_OWDEWPOINT', json_data, file_modified_time)

		return temperature, humidity, pressure, dewPoint
	
	def _read_open_weather(self, params):
		expire = self.get_param('expire', 600, int)
		period = self.get_param('period', 60, int)
		api_key = self.get_param('apikey', '', str)
		file_name = self.get_param('filename', 'allsky_openweather.json', str)
		units = self.get_param('units', 'metric', str)
		module = self.meta_data['module']

		temperature = None
		humidity = None
		pressure = None
		dewPoint = None
		
		try:
			should_run, diff = allsky_shared.shouldRun(module, period)
			if should_run or self.debug_mode:
				if api_key != "":
					if file_name != "":
						lat = allsky_shared.get_setting('latitude')
						if lat is not None and lat != "":
							lat = allsky_shared.convert_lat_lon(lat)
							lon = allsky_shared.get_setting('longitude')
							if lon is not None and lon != '':
								lon = allsky_shared.convert_lat_lon(lon)
								try:
									resultURL = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={api_key}'
									allsky_shared.log(4,f"INFO: Reading Openweather API from - {resultURL}")
									response = requests.get(resultURL)
									if response.status_code == 200:
										rawData = response.json()
										extraData = self._process_openweather_result(rawData, expire, units)
										allsky_shared.save_extra_data(file_name, extraData )
										result = f'Data acquired and written to extra data file {file_name}'
										allsky_shared.log(1, f'INFO: {result}')
									else:
										result = f'Got error from Open Weather Map API. Response code {response.status_code}'
										allsky_shared.log(0,f'ERROR: {result}')
								except Exception as e:
									result = str(e)
									allsky_shared.log(0, f'ERROR: {result}')
								allsky_shared.set_last_run(module)
							else:
								result = 'Invalid Longitude. Check the Allsky configuration'
								allsky_shared.log(0, f'ERROR: {result}')
						else:
							result = 'Invalid Latitude. Check the Allsky configuration'
							allsky_shared.log(0, f'ERROR: {result}')
					else:
						result = 'Missing filename for data'
						allsky_shared.log(0, f'ERROR: {result}')
				else:
					result = 'Missing Open Weather Map API key'
					allsky_shared.log(0, f'ERROR: {result}')
			else:
				allsky_shared.log(4, f'INFO: Using Cached Openweather API data')
				
			temperature, humidity, pressure, dewPoint = self._get_openweather_values(file_name)                
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(0, f'ERROR: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, pressure, dewPoint

	def _read_sht31(self, sht31_heater, i2c_address):
		temperature = None
		humidity = None

		if i2c_address != '':
			try:
				i2caddressInt = int(i2c_address, 16)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}')
				return temperature, humidity
					
		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_sht31d.SHT31D(i2c, i2caddressInt)
			else:
				sensor = adafruit_sht31d.SHT31D(i2c)
			sensor.heater = sht31_heater
			temperature = sensor.temperature
			humidity = sensor.relative_humidity
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity

	def _do_dhtxx_read(self, input_pin):
		temperature = None
		humidity = None

		try:
			pin = allsky_shared.get_gpio_pin(input_pin)
			dht_device = adafruit_dht.DHT22(pin, use_pulseio=False)
			try:
				temperature = dht_device.temperature
				humidity = dht_device.humidity
			except RuntimeError as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(4, f'ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'WARNING: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity

	def _read_dht22(self, input_pin, dhtxx_retry_count, dhtxx_delay):
		temperature = None
		humidity = None
		count = 0
		reading = True

		while reading:
			temperature, humidity = self._do_dhtxx_read(input_pin)

			if temperature is None and humidity is None:
				allsky_shared.log(4, f'WARNING: Failed to read DHTXX on attempt {count+1}')
				count = count + 1
				if count > dhtxx_retry_count:
					reading = False
				else:
					time.sleep(dhtxx_delay/1000)
			else:
				reading = False

		return temperature, humidity

	def _read_bme280_i2c(self, i2c_address):
		temperature = None
		humidity = None
		pressure = None
		relHumidity = None
		altitude = None

		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}')

		try:
			i2c = board.I2C()
			if i2c_address != '':
				bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, i2c_address_int)
			else:
				bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

			temperature =  bme280.temperature
			humidity = bme280.humidity
			relHumidity = bme280.relative_humidity
			altitude = bme280.altitude
			pressure = bme280.pressure
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(0, f'ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, pressure, relHumidity, altitude

	def _read_htu21(self, i2c_address):
		temperature = None
		humidity = None

		if i2c_address != "":
			try:
				i2caddress_int = int(i2c_address, 16)
			except:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')

		try:
			i2c = board.I2C()
			if i2c_address != '':
				htu21 = HTU21D(i2c, i2caddress_int)
			else:
				htu21 = HTU21D(i2c)

			temperature =  htu21.temperature
			humidity = htu21.relative_humidity
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module readHtu21 failed on line {eTraceback.tb_lineno} - {e}')
			
		return temperature, humidity

	def _read_ahtx0(self, i2c_address):
		temperature = None
		humidity = None

		if i2c_address != "":
			try:
				i2caddress_int = int(i2c_address, 16)
			except:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')

		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_ahtx0.AHTx0(i2c, i2caddress_int)
			else:
				sensor = adafruit_ahtx0.AHTx0(i2c)
			temperature = sensor.temperature
			humidity = sensor.relative_humidity
		except ValueError as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module readAHTX0 failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity

	def _read_solo(self, url):
		temperature = None
		humidity = None
		pressure = None
		dewPoint = None

		try: 
			#Read Weaterdata from SOLO Website
			json_data = urllib.request.urlopen(url).read()  
			current_weather_data =  json.loads(json_data)['LastReadings']

			# that is what you should receive
			#    { "LastReadings": {
			#    "dataGMTTime" : "2023/12/17 22:52:40",
			#    "cwinfo" : "Serial: 2550, FW: 5.89",
			#    "clouds" : -14.850000,
			#    "cloudsSafe" : "Unsafe",
			#    "temp" : 8.450000,
			#    "wind" : 12,
			#    "windSafe" : "Safe",
			#    "gust" : 13,
			#    "rain" : 3072,
			#    "rainSafe" : "Safe",
			#    "lightmpsas" : 20.31,
			#    "lightSafe" : "Safe",
			#    "switch" : 0,
			#    "safe" : 0,
			#    "hum" : 65,
			#    "humSafe" : "Safe",
			#    "dewp" : 2.250000,
			#    "rawir" : -19.150000,
			#    "abspress" : 1003.600000,
			#    "relpress" : 1032.722598,
			#    "pressureSafe" : "Safe"
			#    }
			#    }        
				
			temperature = float(current_weather_data['temp'])
			humidity = float(current_weather_data['hum'])
			pressure = float(current_weather_data['relpress'])
			dewPoint = float(current_weather_data['dewp'])
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module readSolo failed on line {eTraceback.tb_lineno} - {e}')
				
		return temperature, humidity, pressure, dewPoint

	def _read_allsky(self):
		temperature = None
		humidity = None
		dew_point = None
		heat_index = None
		pressure = None
		rel_humidity = None
		altitude = None

		#TODO: Check this logic

		environment_data = allsky_shared.load_extra_data_file('allskytemp.json')
		temperature = allsky_shared.get_allsky_variable('AS_TEMP')
		humidity = allsky_shared.get_allsky_variable('AS_HUMIDITY')
		dew_point = allsky_shared.get_allsky_variable('AS_DEW')
		heat_index = allsky_shared.get_allsky_variable('AS_HEATINDEX')
		pressure = allsky_shared.get_allsky_variable('AS_PRESSURE')
		rel_humidity = allsky_shared.get_allsky_variable('AS_RELHUMIDITY')
		altitude = allsky_shared.get_allsky_variable('AS_ALTITUDE')
		if temperature is not None:
			temperature = float(temperature)
		if humidity is not None:
			humidity = float(humidity)
		if dew_point is not None:
			dew_point = float(dew_point)
		if heat_index is not None:
			heat_index = float(heat_index)
		if pressure is not None:
			pressure = float(pressure)
		if rel_humidity is not None:
			rel_humidity = float(rel_humidity)
		if altitude is not None:
			altitude = float(altitude)
												
		return temperature, humidity, pressure, rel_humidity, altitude

	def _temperature_to_pwm_duty(self, temp):
		pwm_min = self.get_param('pwmmin', 0, int)
		pwm_max = self.get_param('pwmmax', 100, int)
		if temp <= pwm_min:
			return 0
		elif temp >= pwm_max:
			return 65535
		else:
			ratio = (temp - pwm_min) / (pwm_max - pwm_min)
			return int(ratio * 65535)

	def _set_pwm_state(self, heater_pin, duty_cycle):
		result = allsky_shared.set_pwm(heater_pin, duty_cycle)

		return result

	def _set_gpio_pin_state(self, state, invert_relay, heater_pin):
		if invert_relay:
			state = not state

		result = allsky_shared.set_gpio_pin(heater_pin, state)

		return result

	def _turn_heater_on(self, heater_pin, invert_relay, extra=False, use_pwm=False, duty_cycle=0):
		if extra:
			type = 'Extra'
		else:
			type = 'Heater'

		if use_pwm:
			duty_cycle_percent = round((duty_cycle / 65535) * 100,2)
			result = f'Turning {type} on using pwm on pin {heater_pin}. Duty Cycle {duty_cycle}, {duty_cycle_percent}%'
			allsky_shared.log(4, f'INFO: {result}')
			self._set_pwm_state(heater_pin, duty_cycle)
		else:
			result = f'Turning {type} on using pin {heater_pin}'
			if self._set_gpio_pin_state(1, invert_relay, heater_pin):
				if not allsky_shared.db_has_key('dewheaterontime'):
					now = int(time.time())
					allsky_shared.db_add('dewheaterontime', now)
				allsky_shared.log(1, f'INFO: {result}')
			else:
				result = f'ERROR: (Heater On) Failed to set Digital IO to output. Check pigpiod is running'
				allsky_shared.log(0, result)

	def _turn_heater_off(self, heater_pin, invert_relay, extra=False, use_pwm=False):
		if extra:
			type = 'Extra'
		else:
			type = 'Heater'
						

		if use_pwm:
			allsky_shared.log(4, f'INFO: Turning {type} off using pwm on pin {heater_pin}.')
			self._set_pwm_state(heater_pin, 0)
		else:  
			result = f"Turning {type} off using pin {heater_pin}"
			if self._set_gpio_pin_state(0, invert_relay, heater_pin):
				if allsky_shared.db_has_key('dewheaterontime'):
					allsky_shared.db_delete_key('dewheaterontime')
				allsky_shared.log(1, f'INFO: {result}')
			else:
				result = f'ERROR: (Heater Off) Failed to set Digital IO to output. Check pigpiod is running'
				allsky_shared.log(0, result)

	def _get_sensor_reading(self, sensor_type, input_pin, i2c_address, dhtxx_retry_count, dhtxx_delay, sht31_heater, solo_url, params):
		temperature = None
		humidity = None
		the_dew_point = None
		the_heat_index = None
		pressure = None
		rel_humidity = None
		altitude = None

		if sensor_type == "SHT31":
			temperature, humidity = self._read_sht31(sht31_heater, i2c_address)
		elif sensor_type == "DHT22" or sensor_type == "DHT11" or sensor_type == "AM2302":
			temperature, humidity = self._read_dht22(input_pin, dhtxx_retry_count, dhtxx_delay)
		elif sensor_type == "BME280-I2C":
			temperature, humidity, pressure, rel_humidity, altitude = self._read_bme280_i2c(i2c_address)
		elif sensor_type == "HTU21":
			temperature, humidity = self._read_htu21(i2c_address)
		elif sensor_type == "AHTx0":
			temperature, humidity = self._read_ahtx0(i2c_address)
		elif sensor_type == "SOLO-Cloudwatcher":
			temperature, humidity, pressure, the_dew_point = self._read_solo(solo_url)
		elif sensor_type == 'OpenWeather':
			temperature, humidity, pressure, the_dew_point = self._read_open_weather(params)
		elif sensor_type == 'Allsky':
			temperature, humidity, pressure, rel_humidity, altitude = self._read_allsky()
		else:
			allsky_shared.log(0, 'ERROR: No sensor type defined')

		if temperature is not None and humidity is not None:
			the_dew_point = dew_point(temperature, humidity).c
			the_heat_index = heat_index(temperature, humidity).c

			tempUnits = allsky_shared.get_setting('temptype')
			if tempUnits == 'F':
				temperature = (temperature * (9/5)) + 32
				the_dew_point = (the_dew_point * (9/5)) + 32
				the_heat_index = (the_heat_index * (9/5)) + 32
				allsky_shared.log(4, 'INFO: Converted temperature to F')

			temperature = round(temperature, 2)
			humidity = round(humidity, 2)
			the_dew_point = round(the_dew_point, 2)
			the_heat_index = round(the_heat_index, 2)

		return temperature, humidity, the_dew_point, the_heat_index, pressure, rel_humidity, altitude

	def _get_last_run_time(self):
		last_run = None

		if allsky_shared.db_has_key('dewheaterlastrun'):
			last_run = allsky_shared.db_get('dewheaterlastrun')

		return last_run

	def _debug_output(self, sensor_type, temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude):
		allsky_shared.log(1, f'INFO: Sensor {sensor_type} read. Temperature {temperature} Humidity {humidity} Relative Humidity {rel_humidity} Dew Point {dew_point} Heat Index {heat_index} Pressure {pressure} Altitude {altitude}')

	def _pwm_high_time(self, frequency, duty_cycle):
		period = 1 / frequency
		high_time = (duty_cycle / 100) * period
		return high_time
	
	def run(self):    
		result = ""
		sensor_type = self.get_param('type', '', str)
		heater_startup_state = self.get_param('heaterstartupstate', 'OFF', str)
		heater_pin = self.get_param('heaterpin', 0, int)
		extra_pin = self.get_param('extrapin', 0, int)
		force = self.get_param('force', 0, int)
		limit = self.get_param('limit', 0, int)
		invert_relay = self.get_param('invertrelay', False, bool)
		invert_extra_pin = self.get_param('invertextrapin', False, bool)
		input_pin = self.get_param('inputpin', 0, int)
		frequency = self.get_param('frequency', 0, int)
		max_on_time = self.get_param('max', 0, int)
		i2c_address = self.get_param('i2caddress', '', str)
		dhtxx_retry_count = self.get_param('dhtxxretrycount', 3, int)
		dhtxx_delay = self.get_param('dhtxxdelay', 0, int)
		sht31_heater = self.get_param('sht31heater', False, bool)
		solo_url = self.get_param('solourl', '', str)
		daytime_disable = self.get_param('daydisable', True, bool)
		use_pwm = self.get_param('usepwm', False, bool)
		extra_use_pwm = self.get_param('extrausepwm', False, bool)
		debug_mode = self.get_param('enabledebug', False, bool)
		debug_temperature = self.get_param('debugtemperature', 0, int)
		debug_dew_point = self.get_param('debugdewpoint', 0, int)

		tod = self._get_time_of_day(); 
						
		temperature = 0
		humidity = 0
		dew_point = 0
		heat_index = 0
		heater = False

		ok_to_run = True
		if daytime_disable:
			if tod == 'day':
				ok_to_run = False

		if ok_to_run or self.debug_mode:            
			should_run, diff = allsky_shared.should_run('allskydew', frequency)    
			if should_run or self.debug_mode:
				if heater_pin != 0:
					last_run_time = self._get_last_run_time()
					if last_run_time is not None:
						now = int(time.time())
						lastRunSecs = now - last_run_time
						if (lastRunSecs >= frequency) or self.debug_mode:
							allsky_shared.db_update('dewheaterlastrun', now)
							if not debug_mode:
								temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude = self._get_sensor_reading(sensor_type, input_pin, i2c_address, dhtxx_retry_count, dhtxx_delay, sht31_heater, solo_url, self.params)
							else:
								temperature = debug_temperature
								dew_point = debug_dew_point
								humidity = 0
								heat_index = 0
								pressure = 0
								rel_humidity = 0
								altitude = 0
							if temperature is not None:
								temperature = round(temperature, 2)
							if humidity is not None:
								humidity = round(humidity, 2)
							if dew_point is not None:
								dew_point = round(dew_point, 2)
							if heat_index is not None:
								heat_index = round(heat_index, 2)
							if pressure is not None:
								pressure = round(pressure, 0)
							if rel_humidity is not None:
								rel_humidity = round(rel_humidity, 2)
							if altitude is not None:
								altitude = round(altitude, 0)
        
							self._debug_output(sensor_type, temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude)
        
							if temperature is not None:
								last_on_seconds = 0
								if allsky_shared.db_has_key('dewheaterontime'):
									last_on_time = allsky_shared.db_get('dewheaterontime')
									last_on_seconds = now - last_on_time
								if max_on_time != 0 and last_on_seconds >= max_on_time:
									result = f'Heater was on longer than maximum allowed time {max_on_time}'
									allsky_shared.log(1, f'INFO: {result}')
									self._turn_heater_off(heater_pin, invert_relay, False, use_pwm)
									if extra_pin != 0:
										self._turn_heater_off(extra_pin, invert_extra_pin, False, extra_use_pwm)
									heater = False
								elif force != 0 and temperature <= force:
									result = f'Temperature below forced level {force}'
									allsky_shared.log(1, f'INFO: {result}')
									duty_cycle = 65535         
									self._turn_heater_on(heater_pin, invert_relay, False, use_pwm, duty_cycle)
									if extra_pin != 0:
										self._turn_heater_on(extra_pin, invert_extra_pin, True, extra_use_pwm, duty_cycle)
									heater = True
								else:                           
									if ((temperature - limit) <= dew_point):
										result = f'Temperature within limit temperature {temperature}, limit {limit}, dewPoint {dew_point}'
										allsky_shared.log(1, f'INFO: {result}')
										temp_dew_diff = abs(temperature - dew_point)
										if temp_dew_diff > 10:
											temp_dew_diff = 10

										#duty_cycle = round(temp_dew_diff * 10, 2)
										duty_cycle = self._temperature_to_pwm_duty(temp_dew_diff)
										self._turn_heater_on(heater_pin, invert_relay, False, use_pwm, duty_cycle)
										if extra_pin != 0:
											self._turn_heater_on(extra_pin, invert_extra_pin, True, extra_use_pwm, duty_cycle)
										heater = True
									else:
										result = f'Temperature outside limit temperature {temperature}, limit {limit}, dewPoint {dew_point}'
										allsky_shared.log(1, f'INFO: {result}')
										duty_cycle = 0
										self._turn_heater_off(heater_pin, invert_relay, False, use_pwm)
										if extra_pin != 0:
											self._turn_heater_off(extra_pin, invert_extra_pin, True, use_pwm)
										heater = False
									
								extraData = {}
								if sensor_type == 'Allsky':
									extraData['AS_DEWCONTROLHEATER'] = heater
									extraData['AS_DEWCONTROLHEATERINT'] = 1 if heater else 0
									extraData['AS_DEWCONTROLAMBIENT'] = temperature
									extraData['AS_DEWCONTROLDEW'] = dew_point
									extraData['AS_DEWCONTROLHUMIDITY'] = humidity
									extraData['AS_DEWCONTROLPWMDUTYCYCLE'] = 100
								else:
									extraData['AS_DEWCONTROLPWMDUTYCYCLE'] = 100            
									extraData['AS_DEWCONTROLSENSOR'] = sensor_type
									extraData['AS_DEWCONTROLAMBIENT'] = temperature
									extraData['AS_DEWCONTROLDEW'] = dew_point
									extraData['AS_DEWCONTROLHUMIDITY'] = humidity
									extraData['AS_DEWCONTROLHEATER'] = heater
									extraData['AS_DEWCONTROLHEATERINT'] = 1 if heater else 0
									if pressure is not None:
										extraData['AS_DEWCONTROLPRESSURE'] = pressure
									if rel_humidity is not None:
										extraData['AS_DEWCONTROLRELHUMIDITY'] = rel_humidity
									if altitude is not None:
										extraData['AS_DEWCONTROLALTITUDE'] = altitude
								
								if use_pwm:
									high_time = self._pwm_high_time(1000, duty_cycle)
									extraData['AS_DEWCONTROLPWMDUTYCYCLE'] = duty_cycle

								allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extraData, self.meta_data['module'], self.meta_data['extradata'])

								history_data = allsky_shared.load_extra_data_file('dewheaterhistory', 'json')
								current_time = int(time.time())

								heater_state = 0
								if use_pwm:
									heater_state = duty_cycle
								else:
									if heater:
										heater_state = 100

								history_data[current_time] = {
									"heater": heater_state,
									"temperature": temperature,
									"dew_point": dew_point,
									"humidity": humidity
								}

								cutoff_time = int(time.time()) - 86400
								history_data = {ts: val for ts, val in history_data.items() if int(ts) > cutoff_time}
        
								allsky_shared.save_extra_data('dewheaterhistory', history_data)

							else:
								result = "Failed to read sensor"
								allsky_shared.log(0, f'ERROR: {result}')
								allsky_shared.delete_extra_data(self.meta_data['extradatafilename'])
						else:
							result = f'Not run. Only running every {frequency}s. Last ran {lastRunSecs}s ago'
							allsky_shared.log(1, f'INFO: {result}')
					else:
						now = int(time.time())
						allsky_shared.db_add('dewheaterlastrun', now)
						allsky_shared.log(1, 'INFO: No last run info so assuming startup')
						if heater_startup_state == 'ON':
							self._turn_heater_on(heater_pin, invert_relay)
							if extra_pin != 0:
								self._turn_heater_on(extra_pin, invert_extra_pin)
							heater = True
						else:
							self._turn_heater_off(heater_pin, invert_relay)
							if extra_pin != 0:
								self._turn_heater_off(extra_pin, invert_extra_pin)
							heater = False
				else:
					allsky_shared.delete_extra_data(self.meta_data['extradatafilename'])
					result = 'heater pin not defined or invalid'
					allsky_shared.log(0, f'ERROR: {result}')

				allsky_shared.set_last_run('allskydew')

			else:
				result = 'Will run in {:.2f} seconds'.format(frequency - diff)
				allsky_shared.log(1, f'INFO: {result}')
		else:
			if heater_pin != 0:
				heater_pin = allsky_shared.get_gpio_pin(heater_pin)
				self._turn_heater_off(heater_pin, invert_relay)
			if extra_pin != 0:
				extra_pin = allsky_shared.get_gpio_pin(extra_pin)
				self._turn_heater_off(extra_pin, invert_extra_pin, True)

			extra_data = {}
			extra_data['AS_DEWCONTROLSENSOR'] = sensor_type
			extra_data['AS_DEWCONTROLAMBIENT'] = 0
			extra_data['AS_DEWCONTROLDEW'] = 0
			extra_data['AS_DEWCONTROLHUMIDITY'] = 0
			extra_data['AS_DEWCONTROLHEATER'] = 'Disabled'
			allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
				
			result = 'Dew control disabled during the day'
			allsky_shared.log(1, f"INFO: {result}")
			
		return result

def dewheater(params, event):
	allsky_dewheater = ALLSKYDEWHEATER(params, event)
	result = allsky_dewheater.run()

	return result       
    
def dewheater_cleanup():
	moduleData = {
		"metaData": ALLSKYDEWHEATER.meta_data,
		"cleanup": {
			"files": {
				ALLSKYDEWHEATER.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanup_module(moduleData)