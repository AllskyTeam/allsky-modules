# TODO: Add units to data
# TODO: Use units for OW
# TODO: Add ability to make fields manatory depending upon a select value
# TODO: Add much better validation for params, like on OW
# TODO: Check rel humidity return values
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import time
import sys
import os
import json
import requests
import board
from pathlib import Path

from meteocalc import dew_point, Temp
import board
import adafruit_sht31d
import adafruit_sht4x
import adafruit_dht
import adafruit_ahtx0
import adafruit_scd30
import bme680
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_htu21d import HTU21D
from meteocalc import dew_point
from digitalio import DigitalInOut, Direction, Pull
from DS18B20dvr.DS18B20 import DS18B20

class ALLSKYTEMP(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Environment Monitor",
		"description": "Reads upto 3 environment sensors",
		"module": "allsky_temp",
		"version": "v1.0.2",
		"events": [
			"periodic",
			"day",
			"night"
		],
		"group": "Data Sensor",
		"experimental": "false",
		"centersettings": "false",
		"testable": "true",
		"extradatafilename": "allsky_temp.json",
		"graphs": {
			"chart1": {
				"icon": "fas fa-chart-line",
				"title": "Temperatures/Humidity",
				"group": "Environment",
				"animation": "false",    
				"main": "true",
				"config": {
					"chart": {
						"type": "spline",
						"animation": "false",
						"zooming": {
							"type": "x"
						}
					},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
					},
					"title": {
						"text": "Temperature / Humidity"
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
								"text": "Temperature"
							} 
						},
						{ 
							"title": {
								"text": "Humidity"
							},
							"opposite": "true"       
						}      
					]
				},
				"series": {
					"coretemp": {
						"name": "Core Temp",
						"yAxis": 0,
						"variable": "AS_TEMP"                 
					},
					"corehumidity": {
						"name": "Core Humdity",
						"yAxis": 1,
						"variable": "AS_HUMIDITY"
					},
					"temp1": {
						"name": "Temp 1",
						"yAxis": 0,
						"variable": "AS_TEMP1"
					},
					"humidity1": {
						"name": "Humdity 1",
						"yAxis": 1,
						"variable": "AS_HUMIDITY1"
					},
					"temp2": {
						"name": "Temp 2",
						"yAxis": 0,
						"variable": "AS_TEMP2"
					},
					"humidity2": {
						"name": "Humdity 2",
						"yAxis": 1,
						"variable": "AS_HUMIDITY2"
					},
					"temp3": {
						"name": "Temp 3",
						"yAxis": 0,
						"variable": "AS_TEMP3"
					},
					"humidity3": {
						"name": "Humdity 3",
						"yAxis": 1,
						"variable": "AS_HUMIDITY4"
					} 
				}    
			}
		},
		"extradata": {
			"info": {
				"count": 4,
				"firstblank": "true"
			},
			"database": {
				"enabled": "True",
				"table": "allsky_temp",
				"include_all": "true"    
			},   
			"values": {       
				"AS_GPIOSTATE${COUNT}": {
					"name": "${GPIOSTATE${COUNT}}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "State of the ${AS_TEMPSENSORNAME${COUNT}} gpio pin",
					"type": "gpio"
				},              
				"AS_TEMPSENSOR${COUNT}": {
					"name": "${TEMPSENSOR${COUNT}}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "${AS_TEMPSENSORNAME${COUNT}} Sensor type",
					"type": "string"
				},
				"AS_TEMPSENSORNAME${COUNT}": {
					"name": "${TEMPSENSORNAME${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Sensor ${COUNT} name ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "string"
				},
				"AS_TEMP${COUNT}": {
					"name": "${TEMP${COUNT}}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Temperature from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "temperature"
				},
				"AS_DEW${COUNT}": {
					"name": "${DEW${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Dewpoint from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "temperature"
				},
				"AS_HUMIDITY${COUNT}": {
					"name": "${HUMIDITY${COUNT}}",
					"format": "",
					"sample": "",                  
					"group": "Environment",
					"description": "Humidity from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				},
				"AS_PRESSURE${COUNT}": {
					"name": "${PRESSURE${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Pressure from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				},
				"AS_RELHUMIDITY${COUNT}": {
					"name": "${RELHUMIDITY${COUNT}}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Relative Humidity from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "temperature"
				},
				"AS_ALTITUDE${COUNT}": {
					"name": "${ALTITUDE${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Altitude from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				},
				"AS_CO2${COUNT}": {
					"name": "${CO2${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Co2 from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				}    
			}                         
		},
		"arguments":{
			"frequency": "0",
			"extradatafilename": "allskytemp.json",
			"units": "metric",

			"type": "None",
			"name": "Allsky",
			"inputpin": "",
			"i2caddress": "",
			"ds18b20address": "",
			"dhtxxretrycount": "2",
			"dhtxxdelay" : "500",
			"sht31heater": "False",
			"sht41mode": "0xE0",
			"owapikey": "",        
			"owfilename": "",        
			"owperiod": "",        
			"owunits": "",        
			"owexpire": "",
			"ecowittapplication": "",
			"ecowittapikey": "",
			"ecowittmac": "",
			"ecowittlocalurl": "",
			"hassurl": "",
			"hassltt": "",
			"hassunit": "",
			"hasstemp": "",
			"hasshumidity": "",
			"hasspressure": "",

			"type1": "None",
			"name1": "",
			"inputpin1": "",
			"i2caddress1": "",
			"ds18b20address1": "",
			"dhtxxretrycount1": "2",
			"dhtxxdelay1" : "500",
			"sht31heater1": "False",
			"sht41mode": "0xE0",
			"temp1": "",
			"gpio1": "",
			"gpioon1": "On",
			"gpiooff1": "Off",
			"owapikey1": "",        
			"owfilename1": "",        
			"owperiod1": "",        
			"owunits1": "",        
			"owexpire1": "",  
			"ecowittapplication1": "",
			"ecowittapikey1": "",
			"ecowittmac1": "",
			"ecowittlocalurl1": "",

   
			"type2": "None",
			"name2": "",
			"inputpin2": "",
			"i2caddress2": "",
			"ds18b20address2": "",
			"dhtxxretrycount2": "2",
			"dhtxxdelay2" : "500",
			"sht31heater2": "False",
			"sht41mode": "0xE0",     
			"temp2": "",
			"gpio2": "",
			"gpioon2": "On",
			"gpiooff2": "Off",
			"owapikey2": "",        
			"owfilename2": "",        
			"owperiod2": "",        
			"owunits2": "",        
			"owexpire2": "",  
			"ecowittapplication2": "",
			"ecowittapikey2": "",
			"ecowittmac2": "",
			"ecowittlocalurl2": "",
   				
			"type3": "None",
			"name3": "",
			"inputpin3": "",
			"i2caddress3": "",
			"ds18b20address3": "",
			"dhtxxretrycount3": "2",
			"dhtxxdelay3" : "500",
			"sht31heater3": "False",
			"sht41mode": "0xE0",     
			"temp3": "",
			"gpio3": "",
			"gpioon3": "On",
			"gpiooff3": "Off",
			"owapikey3": "",
			"owfilename3": "",
			"owperiod3": "",
			"owunits3": "",
			"owexpire3": "",
			"ecowittapplication3": "",
			"ecowittapikey3": "",
			"ecowittmac3": "",
			"ecowittlocalur3": ""
   
   			
		},
		"argumentdetails": {
			"notice" : {
				"tab": "Home",      
				"message": "This module will provide centralised temperature, humidity and pressure data to other modules. This should be used in favour of dedicated sensors in any other modules which will be removed in a future release",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				} 			
			},        
			"frequency" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between sensor reads in seconds. Zero will disable this and run the check every time the periodic jobs run",
				"tab": "Home",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 1000,
					"step": 1
				}
			},
			"extradatafilename": {
				"required": "true",
				"description": "Extra Data Filename",
				"tab": "Home",
				"disabled": "true",
				"help": "The name of the file to create with the dew heater data for the overlay manager"
			},
			"units" : {
				"required": "false",
				"description": "Units",
				"help": "Units of measurement. standard, metric and imperial",
				"tab": "Home",            
				"type": {
					"fieldtype": "select",
					"values": "standard,metric,imperial"
				}                
			},
			"type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Core",
				"type": {
					"fieldtype": "select",
					"values": "None,SHT31,SHT4x,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,SCD30,BME680,OpenWeather,Ecowitt,Ecowitt Local,Homeassistant",
					"default": "None"
				}
			},
			"name": {
				"required": "false",
				"description": "Name Of Sensor",
				"tab": "Core",
				"help": "The name of the sensor, will be added as a variable",
				"disabled": "true"            
			},        
			"inputpin": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices",
				"tab": "Core",
				"type": {
					"fieldtype": "gpio"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}            
			},
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
				"tab": "Core",
				"type": {
					"fieldtype": "i2c"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"SCD30",
						"BME680"
					]
				}            
			},
			"ds18b20address": {
				"required": "false",
				"description": "DS18B20 Address",
				"tab": "Core",
				"help": "Filename in /sys/bus/w1/devices",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=Onewire",
					"placeholder": "Select a One Wire device"
				},         
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DS18B20"
					]
				}             
			},        
			"dhtxxretrycount" : {
				"required": "false",
				"description": "Retry Count",
				"help": "The number of times to retry the DHTXX sensor read",
				"tab": "Core",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5,
					"step": 1
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"dhtxxdelay" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between faild DBTXX sensor reads in milliseconds",
				"tab": "Core",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 1
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"sht31heater" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31",
				"tab": "Core",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SHT31"        
					]
				}             
			},
			"sht41mode" : {
				"required": "false",
				"description": "SHT4x Power Mode",
				"help": "Sets the SHT4x power mode",
				"tab": "Core",
				"type": {
					"fieldtype": "select",
					"values": "0xFD|No heater - high precision,0xF6|No heater - med precision,0xE0|No heater - low precision (Lowest Power Mode),0x39|High heat - 1 second (Highest Power Mode),0x32|High heat - 0.1 second,0x2F|Med heat - 1 second,0x24|Med heat - 0.1 second,0x1E|Low heat - 1 second, 0x15|Low heat - 0.1 second",
					"default": "None"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"SHT4x"
					]
				}             
			},     
			"owtext": {
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data",
				"tab": "Core",
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
			"owapikey": {
				"required": "false",
				"description": "API Key",
				"tab": "Core",
				"secret": "true",         
				"help": "Your Open Weather Map API key.",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}             
			},
			"owfilename": {
				"required": "false",
				"description": "Filename",
				"tab": "Core",            
				"help": "The name of the file that will be written to the allsky/tmp/extra directory",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                     
			},        
			"owperiod" : {
				"required": "false",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
				"tab": "Core",            
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},       
			"owexpire" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
				"tab": "Core",            
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},          
			"ecowittapplication": {
				"required": "false",
				"description": "Application Key",
				"tab": "Core",            
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittapikey": {
				"required": "false",
				"description": "API Key",
				"tab": "Core",            
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittmac": {
				"required": "false",
				"description": "MAC Address",
				"tab": "Core",            
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. The URL will look like http://192.168.1.25/get_livedata_info?. See the documentation on howto obtain this url.",
				"tab": "Core",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "success"
						}
					}
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}              						
			},
			"ecowittlocalurl": {
				"required": "false",
				"description": "Local URL",
				"tab": "Core",            
				"help": "The local URL of the Ecowitt Hub",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}    				
			},
			"hassurl": {
				"required": "false",
				"description": "URL",
				"tab": "Core",            
				"help": "The url of your homeassistant server, will be something liek http://192.168.1.196:8123",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassltt": {
				"required": "false",
				"description": "Long Term Token",
				"tab": "Core",            
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassunit": {
				"required": "false",
				"description": "Temperature Unit",
				"tab": "Core",            
				"help": "The temperature units used in Homeassistant",
				"type": {
					"fieldtype": "select",
					"values": "Metric,Imperial",
					"default": "None"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasstemp": {
				"required": "false",
				"description": "Temperature Sensor",
				"tab": "Core",            
				"help": "The id of the temperature sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl",
						"hassltt"
					]
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasshumidity": {
				"required": "false",
				"description": "Humidity Sensor",
				"tab": "Core",            
				"help": "The id of the humidity sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl",
						"hassltt"
					]
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasspressure": {
				"required": "false",
				"description": "Pressure Sensor",
				"tab": "Core",            
				"help": "The id of the pressure sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl",
						"hassltt"
					]
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},           
			"noticecore" : {
				"tab": "Core",      
				"message": "This sensor is used by Allksy for basic temperature information. The following Variables will be created<br>AS_TEMP, AS_HUMIDITY, AS_DEWPOINT, AS_PRESSURE, AS_ALTITUDE",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				} 			
			},    
   			"type1" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "select",
					"values": "None,SHT31,SHT4x,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,SCD30,BME680,OpenWeather,Ecowitt,Ecowitt Local,Homeassistant",
					"default": "None"
				}
			},
			"name1": {
				"required": "false",
				"description": "Name Of Sensor",
				"tab": "Sensor 1",
				"help": "The name of the sensor, will be added as a variable",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"SCD30",
						"BME680",
						"OpenWeather",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}            
			},        
			"inputpin1": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "gpio"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}            
			},
			"i2caddress1": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "i2c"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"SCD30",
						"BME680"
					]
				}            
			},
			"ds18b20address1": {
				"required": "false",
				"description": "DS18B20 Address",
				"tab": "Sensor 1",
				"help": "Filename in /sys/bus/w1/devices",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=Onewire",
					"placeholder": "Select a One Wire device"
				},          
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"DS18B20"
					]
				}             
			},        
			"dhtxxretrycount1" : {
				"required": "false",
				"description": "Retry Count",
				"help": "The number of times to retry the DHTXX sensor read",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5,
					"step": 1
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"dhtxxdelay1" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between faild DBTXX sensor reads in milliseconds",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 1
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"sht31heater1" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31"
					]
				}             
			},
			"sht41mode1" : {
				"required": "false",
				"description": "SHT4x Power Mode",
				"help": "Sets the SHT4x power mode",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "select",
					"values": "0xFD|No heater - high precision,0xF6|No heater - med precision,0xE0|No heater - low precision (Lowest Power Mode),0x39|High heat - 1 second (Highest Power Mode),0x32|High heat - 0.1 second,0x2F|Med heat - 1 second,0x24|Med heat - 0.1 second,0x1E|Low heat - 1 second, 0x15|Low heat - 0.1 second",
					"default": "0xE0"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT4x"
					]
				}             
			},      
			"owtext1": {
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data",
				"tab": "Sensor 1",
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
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}              						
			},
			"owapikey1": {
				"required": "false",
				"description": "API Key",
				"secret": "true",         
				"tab": "Sensor 1",
				"help": "Your Open Weather Map API key.",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}             
			},
			"owfilename1": {
				"required": "false",
				"description": "Filename",
				"tab": "Sensor 1",            
				"help": "The name of the file that will be written to the allsky/tmp/extra directory",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                     
			},        
			"owperiod1" : {
				"required": "false",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
				"tab": "Sensor 1",            
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},       
			"owexpire1" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
				"tab": "Sensor 1",            
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},                 
			"ecowittapplication1": {
				"required": "false",
				"description": "Application Key",
				"tab": "Sensor 1",            
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittapikey1": {
				"required": "false",
				"description": "API Key",
				"tab": "Sensor 1",            
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittmac1": {
				"required": "false",
				"description": "MAC Address",
				"tab": "Sensor 1",            
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext1": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. The URL will look like http://192.168.1.25/get_livedata_info?. See the documentation on howto obtain this url.",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "success"
						}
					}
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}              						
			},
			"ecowittlocalurl1": {
				"required": "false",
				"description": "Local URL",
				"tab": "Sensor 1",            
				"help": "The local URL of the Ecowitt Hub",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}    				
			}, 
			"hassurl1": {
				"required": "false",
				"description": "URL",
				"tab": "Sensor 1",            
				"help": "The url of your homeassistant server, will be something liek http://192.168.1.196:8123",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassltt1": {
				"required": "false",
				"description": "Long Term Token",
				"tab": "Sensor 1",            
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassunit1": {
				"required": "false",
				"description": "Temperature Unit",
				"tab": "Sensor 1",            
				"help": "The temperature units used in Homeassistant",
				"type": {
					"fieldtype": "select",
					"values": "Metric,Imperial",
					"default": "None"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasstemp1": {
				"required": "false",
				"description": "Temperature Sensor",
				"tab": "Sensor 1",            
				"help": "The id of the temperature sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl1",
						"hassltt1"
					]
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasshumidity1": {
				"required": "false",
				"description": "Humidity Sensor",
				"tab": "Sensor 1",            
				"help": "The id of the humidity sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl1",
						"hassltt1"
					]
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasspressure1": {
				"required": "false",
				"description": "Pressure Sensor",
				"tab": "Sensor 1",            
				"help": "The id of the pressure sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl1",
						"hassltt1"
					]
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},    
			"temp1" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 120,
					"step": 1
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}             
			},        
			"gpio1": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp",
				"type": {
					"fieldtype": "gpio"
				},            
				"tab": "Sensor 1",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                      
			},
			"gpioon1": {
				"required": "false",
				"description": "GPIO On",
				"help": "The Label to use when the GPIO pin is high",
				"tab": "Sensor 1",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                      
			},
			"gpiooff1": {
				"required": "false",
				"description": "GPIO Off",
				"help": "The Label to use when the GPIO pin is low",
				"tab": "Sensor 1",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                    
			},                    			
   			"type2" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "select",
					"values": "None,SHT31,SHT4x,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,SCD30,BME680,OpenWeather,Ecowitt,Ecowitt Local,Homeassistant",
					"default": "None"
				}
			},
			"name2": {
				"required": "false",
				"description": "Name Of Sensor",
				"tab": "Sensor 2",
				"help": "The name of the sensor, will be added as a variable",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"SCD30",
						"BME680",
						"OpenWeather",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"      
					]
				}            
			},        
			"inputpin2": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "gpio"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}            
			},
			"i2caddress2": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "i2c"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"SCD30",
						"BME680"
					]
				}            
			},
			"ds18b20address2": {
				"required": "false",
				"description": "DS18B20 Address",
				"tab": "Sensor 2",
				"help": "Filename in /sys/bus/w1/devices",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=Onewire",
					"placeholder": "Select a One Wire device"
				},         
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"DS18B20"
					]
				}             
			},        
			"dhtxxretrycount2" : {
				"required": "false",
				"description": "Retry Count",
				"help": "The number of times to retry the DHTXX sensor read",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5,
					"step": 1
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"dhtxxdelay2" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between faild DBTXX sensor reads in milliseconds",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 1
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"sht31heater2" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31"
					]
				}             
			},
			"sht41mode2" : {
				"required": "false",
				"description": "SHT4x Power Mode",
				"help": "Sets the SHT4x power mode",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "select",
					"values": "0xFD|No heater - high precision,0xF6|No heater - med precision,0xE0|No heater - low precision (Lowest Power Mode),0x39|High heat - 1 second (Highest Power Mode),0x32|High heat - 0.1 second,0x2F|Med heat - 1 second,0x24|Med heat - 0.1 second,0x1E|Low heat - 1 second, 0x15|Low heat - 0.1 second",
					"default": "0xE0"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT4x"
					]
				}             
			},     
			"owtext2": {
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data",
				"tab": "Sensor 2",
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
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}              						
			},
			"owapikey2": {
				"required": "false",
				"description": "API Key",
				"secret": "true",         
				"tab": "Sensor 2",            
				"help": "Your Open Weather Map API key.",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}             
			},
			"owfilename2": {
				"required": "false",
				"description": "Filename",
				"tab": "Sensor 2",            
				"help": "The name of the file that will be written to the allsky/tmp/extra directory",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                     
			},        
			"owperiod2" : {
				"required": "false",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
				"tab": "Sensor 2",            
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},       
			"owexpire2" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
				"tab": "Sensor 2",            
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},
			"hassurl2": {
				"required": "false",
				"description": "URL",
				"tab": "Sensor 2",            
				"help": "The url of your homeassistant server, will be something liek http://192.168.1.196:8123",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassltt2": {
				"required": "false",
				"description": "Long Term Token",
				"tab": "Sensor 2",
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassunit2": {
				"required": "false",
				"description": "Temperature Unit",
				"tab": "Sensor 2",            
				"help": "The temperature units used in Homeassistant",
				"type": {
					"fieldtype": "select",
					"values": "Metric,Imperial",
					"default": "None"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasstemp2": {
				"required": "false",
				"description": "Temperature Sensor",
				"tab": "Sensor 2",            
				"help": "The id of the temperature sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl2",
						"hassltt2"
					]
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasshumidity2": {
				"required": "false",
				"description": "Humidity Sensor",
				"tab": "Sensor 2",            
				"help": "The id of the humidity sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl2",
						"hassltt2"
					]
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasspressure2": {
				"required": "false",
				"description": "Pressure Sensor",
				"tab": "Sensor 2",            
				"help": "The id of the pressure sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl2",
						"hassltt2"
					]
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},       
   			"ecowittapplication2": {
				"required": "false",
				"description": "Application Key",
				"tab": "Sensor 2",            
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittapikey2": {
				"required": "false",
				"description": "API Key",
				"tab": "Sensor 2",            
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittmac2": {
				"required": "false",
				"description": "MAC Address",
				"tab": "Sensor 2",            
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext2": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. The URL will look like http://192.168.1.25/get_livedata_info?. See the documentation on howto obtain this url.",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "success"
						}
					}
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}              						
			},
			"ecowittlocalurl2": {
				"required": "false",
				"description": "Local URL",
				"tab": "Sensor 2",            
				"help": "The local URL of the Ecowitt Hub",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}    				
			},                
			"temp2" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 120,
					"step": 1
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}            
			},        
			"gpio2": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp",
				"type": {
					"fieldtype": "gpio"
				},            
				"tab": "Sensor 2",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                     
			},
			"gpioon2": {
				"required": "false",
				"description": "GPIO On",
				"help": "The Label to use when the GPIO pin is high",
				"tab": "Sensor 2",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                     
			},
			"gpiooff2": {
				"required": "false",
				"description": "GPIO Off",
				"help": "The Label to use when the GPIO pin is low",
				"tab": "Sensor 2",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                    
			}, 
			"type3" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "select",
					"values": "None,SHT31,SHT4x,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,SCD30,BME680,OpenWeather,Ecowitt,Ecowitt Local,Homeassistant",
					"default": "None"
				}
			},
			"name3": {
				"required": "false",
				"description": "Name Of Sensor",
				"tab": "Sensor 3",
				"help": "The name of the sensor, will be added as a variable",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}            
			},        
			"inputpin3": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "gpio"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}            
			},
			"i2caddress3": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "i2c"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"SCD30",
						"BME680"
					]
				}            
			},
			"ds18b20address3": {
				"required": "false",
				"description": "DS18B20 Address",
				"tab": "Sensor 3",
				"help": "Filename in /sys/bus/w1/devices",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=Onewire",
					"placeholder": "Select a One Wire device"
				},         
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"DS18B20"
					]
				}             
			},        
			"dhtxxretrycount3" : {
				"required": "false",
				"description": "Retry Count",
				"help": "The number of times to retry the DHTXX sensor read",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5,
					"step": 1
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"dhtxxdelay3" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between faild DBTXX sensor reads in milliseconds",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 1
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"DHT22",
						"DHT11",
						"AM2302"
					]
				}             
			},
			"sht31heater3" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31"
					]
				}             
			},
			"sht41mode3" : {
				"required": "false",
				"description": "SHT4x Power Mode",
				"help": "Sets the SHT4x power mode",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "select",
					"values": "0xFD|No heater - high precision,0xF6|No heater - med precision,0xE0|No heater - low precision (Lowest Power Mode),0x39|High heat - 1 second (Highest Power Mode),0x32|High heat - 0.1 second,0x2F|Med heat - 1 second,0x24|Med heat - 0.1 second,0x1E|Low heat - 1 second, 0x15|Low heat - 0.1 second",
					"default": "None"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT4x"
					]
				}             
			},     
			"owtext3": {
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data",
				"tab": "Sensor 3",
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
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}              						
			},
			"owapikey3": {
				"required": "false",
				"description": "API Key",
				"secret": "true",
				"tab": "Sensor 3",            
				"help": "Your Open Weather Map API key.",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}             
			},
			"owfilename3": {
				"required": "false",
				"description": "Filename",
				"tab": "Sensor 3",            
				"help": "The name of the file that will be written to the allsky/tmp/extra directory",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                     
			},        
			"owperiod3" : {
				"required": "false",
				"description": "Read Every",
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
				"tab": "Sensor 3",            
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},       
			"owexpire3" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
				"tab": "Sensor 3",            
				"type": {
					"fieldtype": "spinner",
					"min": 61,
					"max": 1500,
					"step": 1
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"OpenWeather"
					]
				}                       
			},  
   			"ecowittapplication3": {
				"required": "false",
				"description": "Application Key",
				"tab": "Sensor 3",            
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittapikey3": {
				"required": "false",
				"description": "API Key",
				"tab": "Sensor 3",            
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittmac3": {
				"required": "false",
				"description": "MAC Address",
				"tab": "Sensor 3",            
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},   
			"ecowittlocalurltext3": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. The URL will look like http://192.168.1.25/get_livedata_info?. See the documentation on howto obtain this url.",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "success"
						}
					}
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}              						
			},
			"ecowittlocalurl3": {
				"required": "false",
				"description": "Local URL",
				"tab": "Sensor 3",            
				"help": "The local URL of the Ecowitt Hub",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}    				
			},     
			"hassurl3": {
				"required": "false",
				"description": "URL",
				"tab": "Sensor 3",
				"help": "The url of your homeassistant server, will be something liek http://192.168.1.196:8123",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassltt3": {
				"required": "false",
				"description": "Long Term Token",
				"tab": "Sensor 3",
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hassunit3": {
				"required": "false",
				"description": "Temperature Unit",
				"tab": "Sensor 3",
				"help": "The temperature units used in Homeassistant",
				"type": {
					"fieldtype": "select",
					"values": "Metric,Imperial",
					"default": "None"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasstemp3": {
				"required": "false",
				"description": "Temperature Sensor",
				"tab": "Sensor 3",
				"help": "The id of the temperature sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl3",
						"hassltt3"
					]
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasshumidity3": {
				"required": "false",
				"description": "Humidity Sensor",
				"tab": "Sensor 3",            
				"help": "The id of the humidity sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl3",
						"hassltt3"
					]
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},
			"hasspressure3": {
				"required": "false",
				"description": "Pressure Sensor",
				"tab": "Sensor 3",            
				"help": "The id of the pressure sensor to read from Homeassistant",
				"type": {
					"fieldtype": "dependentselect",
					"action": "hasssensors",
					"dependenciesset": [
						"hassurl3",
						"hassltt3"
					]
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Homeassistant"
					]
				}    				
			},        
			"temp3" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 120,
					"step": 1
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}            
			},        
			"gpio3": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp",
				"type": {
					"fieldtype": "gpio"
				},            
				"tab": "Sensor 3",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                    
			},
			"gpioon3": {
				"required": "false",
				"description": "GPIO On",
				"help": "The Label to use when the GPIO pin is high",
				"tab": "Sensor 3",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
				}                     
			},
			"gpiooff3": {
				"required": "false",
				"description": "GPIO Off",
				"help": "The Label to use when the GPIO pin is low",
				"tab": "Sensor 3",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"SHT4x",              
						"DHT22",
						"DHT11",
						"AM2302",
						"BME280-I2C",
						"HTU21",
						"AHTx0",
						"DS18B20",
						"OpenWeather",
						"SCD30",
						"BME680"
					]
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
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added DS1820"
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Add Openweather",
						"Add Ecowitt",
						"Add Ecowitt Local",
						"Added Homeassistant",
						"Added new meta options for better structure in the module manager"
					]
				}
			]                                                          
		}
	}

	def _create_cardinal(self, degrees):
		try:
			cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
			cardinal = cardinals[round(degrees / 22.5)]
		except Exception:
			cardinal = 'N/A'

		return cardinal

	def _process_ow_result(self, data, expires, units):
		extra_data = {}
		#rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
		#data = json.loads(rawData)
		self._set_extra_value('weather.main', data, 'OWWEATHER', expires, extra_data)
		self._set_extra_value('weather.description', data, 'OWWEATHERDESCRIPTION', expires, extra_data)

		self._set_extra_value('main.temp', data, 'OWTEMP', expires, extra_data)
		self._set_extra_value('main.feels_like', data, 'OWTEMPFEELSLIKE', expires, extra_data)
		self._set_extra_value('main.temp_min', data, 'OWTEMPMIN', expires, extra_data)
		self._set_extra_value('main.temp_max', data, 'OWTEMPMAX', expires, extra_data)
		self._set_extra_value('main.pressure', data, 'OWPRESSURE', expires, extra_data)
		self._set_extra_value('main.humidity', data, 'OWHUMIDITY', expires, extra_data)

		self._set_extra_value('wind.speed', data, 'OWWINDSPEED', expires, extra_data)
		self._set_extra_value('wind.deg', data, 'OWWINDDIRECTION', expires, extra_data)
		self._set_extra_value('wind.gust', data, 'OWWINDGUST', expires, extra_data)

		self._set_extra_value('clouds.all', data, 'OWCLOUDS', expires, extra_data)

		self._set_extra_value('rain.1hr', data, 'OWRAIN1HR', expires, extra_data)
		self._set_extra_value('rain.3hr', data, 'OWRAIN3HR', expires, extra_data)

		self._set_extra_value('sys.sunrise', data, 'OWSUNRISE', expires, extra_data)
		self._set_extra_value('sys.sunset', data, 'OWSUNSET', expires, extra_data)

		temperature = float(self._get_value('main.temp', data))
		humidity = float(self._get_value('main.humidity', data))
		if units == 'imperial':
			t = Temp(temperature, 'f')
			the_dew_point = dew_point(t, humidity).f

		if units == 'metric':
			t = Temp(temperature, 'c')        
			the_dew_point = dew_point(temperature, humidity).c

		if units == 'standard':
			t = Temp(temperature, 'k')        
			the_dew_point = dew_point(temperature, humidity).k

		degress = self._get_value('wind.deg', data)
		cardinal = self._create_cardinal(degress)

		extra_data['AS_OWWINDCARDINAL'] = {
			'name': '${' + 'OWWINDCARDINAL' + '}',
			'format': '',
			'sample': '',
			'group': 'Environment',
			'value': cardinal,
			'source': 'allsky_temp',         
			'expires': expires
		}

		extra_data['AS_OWDEWPOINT'] = {
			'name': '${' + 'OWDEWPOINT' + '}',
			'format': '',
			'sample': '',
			'group': 'Environment',
			'value': round(the_dew_point,1),
			'source': 'allsky_temp',         
			'expires': expires
		}

		
		return extra_data

	def _set_extra_value(self, path, data, extra_key, expires, extra_data):
		value = self._get_value(path, data)
		if value is not None:
			extra_data["AS_" + extra_key] = {
				"name": "${" + extra_key + "}",
				"format": "",
				"sample": "",
				"group": "Environment",
				"value": value,
				"source": "allsky_temp",         
				"expires": expires
			}
		
	def _get_ow_values(self, file_name):
		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None

		allskyPath = allsky_shared.getEnvironmentVariable('ALLSKY_HOME')
		extra_data_fileName = os.path.join(allskyPath, 'config', 'overlay', 'extra', file_name)

		if os.path.isfile(extra_data_fileName):
			file_modified_time = int(os.path.getmtime(extra_data_fileName))
			with open(extra_data_fileName, 'r', encoding='utf-8') as file:
				json_data = json.load(file)
				temperature = self._get_ow_Value('AS_OWTEMP', json_data, file_modified_time)
				humidity = self._get_ow_Value('AS_OWHUMIDITY', json_data, file_modified_time)
				pressure = self._get_ow_Value('AS_OWPRESSURE', json_data, file_modified_time)
				the_dew_point = self._get_ow_Value('AS_OWDEWPOINT', json_data, file_modified_time)

		return temperature, humidity, pressure, the_dew_point

	def _get_ow_Value(self, field, json_data, file_modified_time):
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

	def _get_value(self, path, data):
		result = None
		keys = path.split('.')
		if keys[0] in data:
			sub_data = data[keys[0]]
			
			if isinstance(sub_data, list):        
				if keys[1] in sub_data[0]:
					result = sub_data[0][keys[1]]
			else:
				if keys[1] in sub_data:
					result = sub_data[keys[1]]

		return result

	def _read_open_weather(self, sensor_number):
		expire = self.get_param('owexpire' + sensor_number, 600, int)
		period = self.get_param('owperiod' + sensor_number, 60, int)
		api_key = self.get_param('owapikey' + sensor_number, '', str)
		file_name = self.get_param('owfilename' + sensor_number, 'allsky_owdata.json', str, True)
		units = self.get_param('units' + sensor_number, '', str)
		module = self.meta_data['module']

		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None

		try:
			should_run, diff = allsky_shared.shouldRun(module, period)
			if should_run or self.debug_mode:
				if api_key != '':
					if file_name != '':
						lat = allsky_shared.getSetting('latitude')
						if lat is not None and lat != '':
							lat = allsky_shared.convertLatLon(lat)
							lon = allsky_shared.getSetting('longitude')
							if lon is not None and lon != '':
								lon = allsky_shared.convertLatLon(lon)
								try:
									ow_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={api_key}"
									allsky_shared.log(4,f"INFO: Reading Openweather API from - {ow_url}")
									response = requests.get(ow_url)
									if response.status_code == 200:
										raw_data = response.json()
										extra_data = self._process_ow_result(raw_data, expire, units)
										allsky_shared.saveExtraData(file_name, extra_data, 'internal')
										result = f'Data acquired and written to extra data file {file_name}'
										allsky_shared.log(1, f'INFO: {result}')
									else:
										result = f'Got error from Open Weather Map API. Response code {response.status_code}'
										allsky_shared.log(0,f'ERROR: {result}')
								except Exception as e:
									eType, eObject, eTraceback = sys.exc_info()            
									result = str(e)
									allsky_shared.log(0, f'ERROR: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}')
								allsky_shared.setLastRun(module)                            
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

			temperature, humidity, pressure, the_dew_point = self._get_ow_values(file_name)                
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(0, f'ERROR: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, pressure, the_dew_point	

	def _read_ds18B20(self, sensor_number):
		humidity = None
		temperature = None

		ds18b20_address = self.get_param('ds18b20address' + sensor_number, '', str)    
		one_wire_base_dir = Path('/sys/bus/w1/devices/')
		one_wire_sensor_dir = Path(os.path.join(one_wire_base_dir, ds18b20_address))
	
		if one_wire_base_dir.is_dir():
			if one_wire_sensor_dir.is_dir():
				try:
					device = DS18B20(ds18b20_address)
					temperature = device.read_temperature()
				# pylint: disable=broad-exception-caught
				except Exception as ex:
					_, _, trace_back = sys.exc_info()
					allsky_shared.log(4, f'ERROR: Module readDS18B20 failed on line {trace_back.tb_lineno} - {ex}')
			else:
				allsky_shared.log(4, f'ERROR: (readDS18B20) - "{ds18b20_address}" is not a valid DS18B20 address. Please check /sys/bus/w1/devices')
		else:
			allsky_shared.log(4, 'ERROR: (readDS18B20) - One Wire is not enabled. Please use the raspi-config utility to enable it')

		return temperature, humidity

	def _read_htu21(self, sensor_number):
		temperature = None
		humidity = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)    
		if i2c_address != '':
			try:
				i2c_address_int = int(i2c_address, 16)
			except:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')

		try:
			i2c = board.I2C()
			if i2c_address != '':
				htu21 = HTU21D(i2c, i2c_address_int)
			else:
				htu21 = HTU21D(i2c)

			temperature =  htu21.temperature
			humidity = htu21.relative_humidity
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module read_htu21 failed on line {eTraceback.tb_lineno} - {e}')
			
		return temperature, humidity

	def _read_ahtx0(self, sensor_number):
		temperature = None
		humidity = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)  
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')

		try:
			i2c = board.I2C()
			if i2c_address != "":  
				sensor = adafruit_ahtx0.AHTx0(i2c, i2c_address_int)
			else:
				sensor = adafruit_ahtx0.AHTx0(i2c)
			temperature = sensor.temperature
			humidity = sensor.relative_humidity
		except ValueError as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f"ERROR: Module read_ahtx0 failed on line {eTraceback.tb_lineno} - {e}")

		return temperature, humidity

	def _do_dhtxx_read(self, input_pin):
		temperature = None
		humidity = None

		try:
			pin = allsky_shared.getGPIOPin(input_pin)
			dhtDevice = adafruit_dht.DHT22(pin, use_pulseio=False)
			try:
				temperature = dhtDevice.temperature
				humidity = dhtDevice.humidity
			except RuntimeError as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(4, f'ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'WARNING: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity

	def _read_dht22(self, sensor_number):
		temperature = None
		humidity = None
		count = 0
		reading = True

		input_pin = self.get_param('inputpin' + sensor_number, 0, int)
		dhtxx_retry_count = self.get_param('dhtxxretrycount' + sensor_number, 0, int)
		dhtxx_delay = self.get_param('dhtxxdelay' + sensor_number, 0, int)

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

	def _read_bme680(self, sensor_number):
		temperature = None
		humidity = None
		pressure = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)

		try:
			if i2c_address != "":
				try:
					i2c_address_int = int(i2c_address, 16)
				except Exception as e:
					eType, eObject, eTraceback = sys.exc_info()
					allsky_shared.log(0, f'ERROR: Module read_bme680 failed on line {eTraceback.tb_lineno} - {e}')

			if i2c_address != "":
				sensor = bme680.BME680(i2c_address_int)
			else:
				sensor = bme680.BME680()

			sensor.set_humidity_oversample(bme680.OS_2X)
			sensor.set_pressure_oversample(bme680.OS_4X)
			sensor.set_temperature_oversample(bme680.OS_8X)
			sensor.set_filter(bme680.FILTER_SIZE_3)

			if sensor.get_sensor_data():
				temperature = sensor.data.temperature
				humidity = sensor.data.humidity
				pressure = sensor.data.pressure
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(0, f'ERROR: Module read_bme680 failed on line {eTraceback.tb_lineno} - {e}')
    
		return temperature, humidity, pressure

	def _read_bme280_i2c(self, sensor_number):
		temperature = None
		humidity = None
		pressure = None
		relHumidity = None
		altitude = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)	
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module read_bme280_i2c failed on line {eTraceback.tb_lineno} - {e}')

		try:
			i2c = board.I2C()
			if i2c_address != "":
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
			allsky_shared.log(0, f'ERROR: Module read_bme280_i2c failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, pressure, altitude

	def _read_sht31(self, sensor_number):
		temperature = None
		humidity = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)
		sht31_heater = self.get_param('sht31heater' + sensor_number, False, bool)
    
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')
					
		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_sht31d.SHT31D(i2c, i2c_address_int)
			else:
				sensor = adafruit_sht31d.SHT31D(i2c)
			sensor.heater = sht31_heater
			temperature = sensor.temperature
			humidity = sensor.relative_humidity
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module read_sht31 failed on line {eTraceback.tb_lineno} - {e}')
			return temperature, humidity

		return temperature, humidity

	def _read_sht4x(self, sensor_number):
		temperature = None
		humidity = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)
		sht41_mode_code = self.get_param('sht41mode' + sensor_number, '0xE0', str)
    
		sht41_mode = int('0xe0', 16)
		try:
			sht41_mode = int(sht41_mode_code, 16)
		except Exception as e:
			pass

		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')
					
		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_sht4x.SHT4x(i2c, i2c_address_int)
			else:
				sensor = adafruit_sht4x.SHT4x(i2c)
			sensor.mode = sht41_mode
			allsky_shared.log(4, f'INFO: Current mode is {adafruit_sht4x.Mode.string[sensor.mode]}')
			temperature, humidity = sensor.measurements
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module _read_sht4x failed on line {eTraceback.tb_lineno} - {e}')
			return temperature, humidity

		return temperature, humidity

	def _read_scd30(self, sensor_number):
		temperature = None
		humidity = None
		co2 = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)
    
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				result = f'Address {i2c_address} is not a valid i2c address'
				allsky_shared.log(0, f'ERROR: {result}')
					
		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_scd30.SCD30(i2c, 0, i2c_address_int)
			else:
				sensor = adafruit_scd30.SCD30(i2c)

			if sensor.data_available:
				co2 = sensor.CO2
				temperature = sensor.temperature
				humidity = sensor.relative_humidity

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(4, f'ERROR: Module _read_scd30 failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, co2

	def _read_ecowitt(self, sensor_number):

		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None
		
		app_key = self.get_param('ecowittapplication' + sensor_number, '', str)
		api_key = self.get_param('ecowittapikey' + sensor_number, '', str)
		mac_address = self.get_param('ecowittmac' + sensor_number, '', str)

		data = allsky_shared.get_ecowitt_data(api_key, app_key, mac_address)

		temperature = data['outdoor']['temperature']
		humidity = data['outdoor']['humidity']
		pressure = data['pressure']['relative']
		the_dew_point = data['outdoor']['dew_point']
  
		return temperature, humidity, pressure, the_dew_point	
    
	def _read_ecowitt_local(self, sensor_number):
     
		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None
  
		LOCAL_URL = self.get_param('ecowittlocalurl' + sensor_number, '', str)

		data = allsky_shared.get_ecowitt_local_data(LOCAL_URL)
   

		temperature = data['outdoor']['temperature']
		humidity = data['outdoor']['humidity']
		pressure = data['pressure']['relative']
		the_dew_point = data['outdoor']['dew_point']
  
		return temperature, humidity, pressure, the_dew_point	

	def _read_homeassistant(self, sensor_number):
		temperature = None
		humidity = None
		pressure = None

		hass_url = self.get_param('hassurl' + sensor_number, '', str)
		hass_ltt = self.get_param('hassltt' + sensor_number, '', str)
		hass_unit = self.get_param('hassunit' + sensor_number, '', str)
		hass_temperature = self.get_param('hasstemp' + sensor_number, '', str)
		hass_humidity = self.get_param('hasshumidity' + sensor_number, '', str)
		hass_pressure = self.get_param('hasspressure' + sensor_number, '', str)

		required_vars = ['hass_url', 'hass_ltt', 'hass_unit', 'hass_temperature', 'hass_humidity', 'hass_pressure']
		missing_variables = [name for name in required_vars if locals().get(name) == '']

		if missing_variables:
			allsky_shared.log(0, f"Error: The following variables are not set: {', '.join(missing_variables)}")
		else:
			temperature = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_temperature)
			humidity = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_humidity)
			pressure = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_pressure)

			if hass_unit == 'Imperial' and temperature is not None:
				temperature = (temperature - 32) * 5 / 9
			
		return temperature, humidity, pressure
     
	def _get_sensor_reading(self, sensor_type, sensor_number):
		temperature = None
		humidity = None
		the_dew_point = None
		pressure = None
		rel_humidity = None
		altitude = None
		co2 = None

		if sensor_type == 'SHT31':
			temperature, humidity = self._read_sht31(sensor_number)
		elif sensor_type == 'SHT4x':
			temperature, humidity = self._read_sht4x(sensor_number)   
		elif sensor_type == 'DHT22' or sensor_type == 'DHT11' or sensor_type == 'AM2302':
			temperature, humidity = self._read_dht22(sensor_number)
		elif sensor_type == 'BME280-I2C':
			temperature, humidity, pressure, altitude = self._read_bme280_i2c(sensor_number)
		elif sensor_type == 'HTU21':
			temperature, humidity = self._read_htu21(sensor_number)
		elif sensor_type == 'AHTx0':
			temperature, humidity = self._read_ahtx0(sensor_number)
		elif sensor_type == 'DS18B20':
			temperature, humidity = self._read_ds18B20(sensor_number)
		elif sensor_type == 'SCD30':
			temperature, humidity, co2 = self._read_scd30(sensor_number)
		elif sensor_type == 'OpenWeather':
			temperature, humidity, pressure, the_dew_point = self._read_open_weather(sensor_number)
		elif sensor_type == 'BME680':
			temperature, humidity, pressure = self._read_bme680(sensor_number)
		elif sensor_type == 'Ecowitt':
			temperature, humidity, pressure, the_dew_point = self._read_ecowitt(sensor_number) 
		elif sensor_type == 'Ecowitt Local':
			temperature, humidity, pressure, the_dew_point = self._read_ecowitt_local(sensor_number)
		elif sensor_type == 'Homeassistant':
			temperature, humidity, pressure = self._read_homeassistant(sensor_number) 
		else:
			allsky_shared.log(0, 'ERROR: No sensor type defined')

		temp_units = allsky_shared.getSetting('temptype')
		if temperature is not None and humidity is not None:
			the_dew_point = dew_point(temperature, humidity).c
			if temp_units == 'F':
				temperature = (temperature * (9/5)) + 32
				the_dew_point = (the_dew_point * (9/5)) + 32
				allsky_shared.log(4, 'INFO: Converted temperature to F')

			temperature = round(temperature, 2)
			humidity = round(humidity, 2)
			the_dew_point = round(the_dew_point, 2)
		else:
			if temperature is not None:
				if temp_units == 'F':
					temperature = (temperature * (9/5)) + 32
					allsky_shared.log(4, 'INFO: Converted temperature ONLY to F')
					
		return temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2

	def _debug_output(self, sensor_type, temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2):
		allsky_shared.log(4,f'INFO: Sensor {sensor_type} read. Temperature {temperature} Humidity {humidity} Relative Humidity {rel_humidity} Dew Point {the_dew_point} Pressure {pressure} Altitude {altitude} Co2 {co2}')

	def run(self):
		result = ''
		extra_data = {}
		self._run_interval = self.get_param('frequency', 60, int)  

		should_run, diff = allsky_shared.shouldRun('allskytemp', self._run_interval)      


		if should_run or self.debug_mode:
			now = int(time.time())
			allsky_shared.dbUpdate('allskytemp', now)
			for sensor_number_itr in range(1,5):
				if sensor_number_itr == 1:
					sensor_number = ""
				else:
					sensor_number = str(sensor_number_itr - 1)
					
				sensor_type = self.get_param('type' + sensor_number, 'None', str)

				if sensor_type != 'None':
					allsky_shared.log(4, f'INFO: Reading sensor {sensor_number}, {sensor_type}')
					name = self.get_param('name' + sensor_number, 'Unknown', str)
					max_temp_key = "temp" + sensor_number
					max_temp = self.get_param(max_temp_key, -1, float)       
					
					gpio_key =  'gpio' + sensor_number
					gpio_pin = self.get_param(gpio_key, -1, int)          
			
					temperature = 0
					humidity = 0
					the_dew_point = 0
					co2 = 0

					temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2 = self._get_sensor_reading(sensor_type, sensor_number)
					if temperature is not None:
						temperature = round(temperature, 2)
					if humidity is not None:
						humidity = round(humidity, 2)
					if the_dew_point is not None:
						the_dew_point = round(the_dew_point, 2)
					if pressure is not None:
						pressure = round(pressure, 0)
					if rel_humidity is not None:
						rel_humidity = round(rel_humidity, 2)
					if altitude is not None:
						altitude = round(altitude, 0)
					if co2 is not None:
						co2 = round(co2, 0)      
					self._debug_output(sensor_type, temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2)

					if sensor_number != '':
						gpio_value = False
						if temperature is not None and sensor_number != "": 
							if max_temp != -1 and gpio_pin != -1:
								try:
									gpio = allsky_shared.getGPIOPin(gpio_pin)
									pin = DigitalInOut(gpio)
									pin.switch_to_output()                   
									if temperature > max_temp:
										gpio_value = True
						
										allsky_shared.log(4, f'INFO: Temperature {temperature} is greater than {max_temp} so enabling GPIO {gpio_pin}')
										pin.value = 1
									else:
										gpio_value = False
										allsky_shared.log(4, f'INFO: Temperature {temperature} is less than {max_temp} so disabling GPIO {gpio_pin}')
										pin.value = 0
								except Exception as e:    
									eType, eObject, eTraceback = sys.exc_info()
									result = f'ERROR: Failed to set Digital IO to output {eTraceback.tb_lineno} - {e}'
									allsky_shared.log(0, result)
								
					if temperature is not None:
						if sensor_number != '':
							extra_data['AS_GPIOSTATE' + sensor_number] = gpio_value
						extra_data['AS_TEMPSENSOR' + sensor_number] = str(sensor_type)
						extra_data['AS_TEMPSENSORNAME' + sensor_number] = name
						extra_data['AS_TEMP' + sensor_number] = temperature
						extra_data['AS_DEW' + sensor_number] = the_dew_point
						extra_data['AS_HUMIDITY' + sensor_number] = humidity
						if pressure is not None:
							extra_data["AS_PRESSURE" + sensor_number] = pressure
						if rel_humidity is not None:
							extra_data["AS_RELHUMIDITY" + sensor_number] = rel_humidity
						if altitude is not None:
							extra_data["AS_ALTITUDE" + sensor_number] = altitude
						if co2 is not None:
							extra_data["AS_CO2" + sensor_number] = co2       
			if extra_data:
				allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])

		else:
			result = 'Will run in {:.2f} seconds'.format(self._run_interval - diff)
			allsky_shared.log(1, f'INFO: {result}')

		return result

def temp(params, event):
	allsky_temp = ALLSKYTEMP(params, event)
	result = allsky_temp.run()

	return result   
    
def temp_cleanup():
	module_data = {
		"metaData": ALLSKYTEMP.meta_data,
		"cleanup": {
			"files": {
				ALLSKYTEMP.meta_data['extradatafilename']
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(module_data)