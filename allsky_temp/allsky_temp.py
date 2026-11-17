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
import glob
import math
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

class ALLSKYTEMP(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Environment Monitor",
		"description": "Obtain environment data (temperature/humidity) from external sensors",
		"docs": "docs/allsky_modules/extra/environment.html",    
		"module": "allsky_temp",
		"version": "v1.0.6",
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
		"extradata": {
			"schema_version": 2,
			"info": {
				"count": 5,
				"firstblank": "true"
			},
			"database": {
				"enabled": "True",
				"table": "allsky_temp",
				"include_all": "true",
    			"pk": "id",
    			"pk_type": "int",    
       			"time_of_day_save": {
					"day": "always",
					"night": "always",
					"nightday": "always",
					"daynight": "always",
					"periodic": "always"
				}      
			},   
			"migrations": [
				{
					"from_schema_version": 1,
					"to_schema_version": 2,
					"breaking": "true",
					"title": "Environment monitor extra data names changed",
					"message": "Temperature monitor extra-data keys were renamed from the AS_TEMPMON_* format to the current AS_* format. Update overlays, templates, and integrations that still use the older names.",
					"changes": {
						"renamed": {
							"AS_TEMPMON_MAXTEMP${COUNT}": "AS_MAXTEMP${COUNT}",
							"AS_TEMPMON_DEADBAND${COUNT}": "AS_DEADBAND${COUNT}",
							"AS_TEMPMON_CONTROLSTATE${COUNT}": "AS_CONTROLSTATE${COUNT}",
							"AS_TEMPMON_GPIOSTATE${COUNT}": "AS_GPIOSTATE${COUNT}",
							"AS_TEMPMON_SENSOR${COUNT}": "AS_TEMPSENSOR${COUNT}",
							"AS_TEMPMON_SENSORNAME${COUNT}": "AS_TEMPSENSORNAME${COUNT}",
							"AS_TEMPMON_AMBIENT${COUNT}": "AS_TEMP${COUNT}",
							"AS_TEMPMON_DEW${COUNT}": "AS_DEW${COUNT}",
							"AS_TEMPMON_HUMIDITY${COUNT}": "AS_HUMIDITY${COUNT}",
							"AS_TEMPMON_PRESSURE${COUNT}": "AS_PRESSURE${COUNT}",
							"AS_TEMPMON_RELHUMIDITY${COUNT}": "AS_RELHUMIDITY${COUNT}",
							"AS_TEMPMON_ALTITUDE${COUNT}": "AS_ALTITUDE${COUNT}"
						},
						"added": [
							"AS_CO2${COUNT}"
						],
						"removed": []
					}
				}
			],
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
					"type": "temperature",
					"source": "sensor"
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
					"type": "number",
					"source": "sensor"     
				},
				"AS_PRESSURE${COUNT}": {
					"name": "${PRESSURE${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Pressure from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "pressure",
					"source": "sensor"     
				},
				"AS_RELHUMIDITY${COUNT}": {
					"name": "${RELHUMIDITY${COUNT}}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Relative Humidity from ${AS_TEMPSENSORNAME${COUNT}}",
				"type": "number",
				"source": "sensor"
				},
				"AS_ALTITUDE${COUNT}": {
					"name": "${ALTITUDE${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Altitude from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number",
					"source": "sensor"     
				},
				"AS_CO2${COUNT}": {
					"name": "${CO2${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Co2 from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number",
					"source": "sensor"     
				},
				"AS_MAXTEMP${COUNT}": {
					"name": "${MAXTEMP${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Maximum temperature from ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				},
				"AS_DEADBAND${COUNT}": {
					"name": "${DEADBAND${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Deadband for ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "number"
				},
				"AS_CONTROLSTATE${COUNT}": {
					"name": "${CONTROLSTATE${COUNT}}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Control state for ${AS_TEMPSENSORNAME${COUNT}}",
					"type": "string"
				}             
			}                         
		},
		"arguments":{
			"frequency": "0",
			"extradatafilename": "allsky_temp.json",
			"units": "metric",

			"type": "None",
			"name": "Allsky",
			"inputpin": "",
			"i2caddress": "",
			"ds18b20address": "",
			"dhtxxretrycount": "2",
			"dhtxxdelay" : "500",
			"dhtxxpower": "",
			"sht31heater": "False",
			"sht41mode": "0xE0",
			"owapikey": "",        
			"owfilename": "",        
			"owperiod": "",        
			"owunits": "metric",
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
			"hasspressureunit": "hPa",
			"deadband": "0",
			"temp": "",
			"gpio": "",
			"gpioon": "On",
			"gpiooff": "Off",
			"invertgpio": "False",
			"temp_offset": "0",
			"pressure_offset": "0",
			"humidity_offset": "0",

			"type1": "None",
			"name1": "",
			"inputpin1": "",
			"i2caddress1": "",
			"ds18b20address1": "",
			"dhtxxretrycount1": "2",
			"dhtxxdelay1" : "500",
			"dhtxxpower1" : "",   
			"sht31heater1": "False",
			"sht41mode1": "0xE0",
			"temp1": "",
			"gpio1": "",
			"gpioon1": "On",
			"gpiooff1": "Off",
			"invertgpio1": "False",   
			"owapikey1": "",        
			"owfilename1": "",        
			"owperiod1": "",        
			"owunits1": "metric",
			"owexpire1": "",  
			"ecowittapplication1": "",
			"ecowittapikey1": "",
			"ecowittmac1": "",
			"ecowittlocalurl1": "",
			"hasspressureunit1": "hPa",
			"deadband1": "0",
			"temp_offset1": "0",
   		"pressure_offset1": "0",
			"humidity_offset1": "0", 
   
			"type2": "None",
			"name2": "",
			"inputpin2": "",
			"i2caddress2": "",
			"ds18b20address2": "",
			"dhtxxretrycount2": "2",
			"dhtxxdelay2" : "500",
			"dhtxxpower2" : "",   
			"sht31heater2": "False",
			"sht41mode2": "0xE0",
			"temp2": "",
			"gpio2": "",
			"gpioon2": "On",
			"gpiooff2": "Off",
			"invertgpio2": "False",    
			"owapikey2": "",        
			"owfilename2": "",        
			"owperiod2": "",        
			"owunits2": "metric",
			"owexpire2": "",  
			"ecowittapplication2": "",
			"ecowittapikey2": "",
			"ecowittmac2": "",
			"ecowittlocalurl2": "",
			"hasspressureunit2": "hPa",
			"deadband2": "0",
			"temp_offset2": "0",
   		"pressure_offset2": "0",
			"humidity_offset2": "0", 
      				
			"type3": "None",
			"name3": "",
			"inputpin3": "",
			"i2caddress3": "",
			"ds18b20address3": "",
			"dhtxxretrycount3": "2",
			"dhtxxdelay3" : "500",
			"dhtxxpower3" : "",
			"sht31heater3": "False",
			"sht41mode3": "0xE0",
			"temp3": "",
			"gpio3": "",
			"gpioon3": "On",
			"gpiooff3": "Off",
			"invertgpio3": "False",   
			"owapikey3": "",
			"owfilename3": "",
			"owperiod3": "",
			"owunits3": "metric",
			"owexpire3": "",
			"ecowittapplication3": "",
			"ecowittapikey3": "",
			"ecowittmac3": "",
			"ecowittlocalurl3": "",
			"hasspressureunit3": "hPa",
			"deadband3": "0",
			"temp_offset3": "0",
   		"pressure_offset3": "0",
			"humidity_offset3": "0"   
   			
		},
		"argumentdetails": {
			"notice" : {
				"tab": "Home",      
				"message": "This module provides centralised temperature, humidity, and pressure data to other modules. This should be used in favour of dedicated sensors in any other modules which will be removed in a future release.",
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
				"help": "The delay between sensor reads in seconds. Zero will disable this and run the check every time the periodic jobs run.",
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
				"help": "The name of the file created with environment data for the Overlay Manager."
			},
			"units" : {
				"required": "false",
				"description": "Units",
				"help": "Legacy setting. Set units on each OpenWeather sensor instead.",
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
				"help": "The name of the sensor, will be added as a variable."
			},
			"deadband" : {
					"required": "false",
					"description": "Deadband Range",
					"help": "Deadband around Max Temp before changing state of the gpio pin",
					"tab": "Core",
					"type": {
							"fieldtype": "spinner",
							"min": 1,
							"max": 10,
							"step": 1
					}            
			},


   
     
          
			"inputpin": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices.",
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
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x76.",
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
				"help": "Filename in /sys/bus/w1/devices.",
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
				"help": "The number of times to retry the DHTXX sensor read.",
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
				"help": "The delay between faild DBTXX sensor reads in milliseconds.",
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
			"dhtxxpower": {
				"required": "false",
				"description": "DHT Power Pin",
				"help": "GPIO pin used to power the DHT sensor during a reading.",
				"tab": "Core",
				"type": {"fieldtype": "gpio"},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": ["DHT22", "DHT11", "AM2302"]
				}
			},
			"sht31heater" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31.",
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
				"help": "Sets the SHT4x power mode.",
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
				"help": "The name of the file that will be written to the allsky/tmp/extra directory.",
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
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day.",
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
			"owunits": {
				"required": "false",
				"description": "OpenWeather Units",
				"help": "Units requested from OpenWeather for this sensor.",
				"tab": "Core",
				"type": {
					"fieldtype": "select",
					"values": "metric,imperial,standard",
					"default": "metric"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": ["OpenWeather"]
				}
			},
			"owexpire" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value.",
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
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/.",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. Enter the gateway base URL, for example http://192.168.1.25. The module adds the data endpoint. See the documentation on how to obtain this URL.",
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
				"help": "Base URL of the Ecowitt gateway, for example http://192.168.1.25.",
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
				"help": "The URL of your Homeassistant server, for example: http://192.168.1.196:8123.",
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
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab.",
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
				"help": "The temperature units used in Homeassistant.",
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
				"help": "The id of the temperature sensor to read from Homeassistant.",
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
				"help": "The id of the humidity sensor to read from Homeassistant.",
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
				"help": "The id of the pressure sensor to read from Homeassistant.",
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
			"hasspressureunit": {
				"required": "false",
				"description": "Pressure Unit",
				"tab": "Core",
				"help": "Units reported by the Home Assistant pressure sensor; converted to hPa for overlays.",
				"type": {
					"fieldtype": "select",
					"values": "hPa,mbar,inHg,mmHg,kPa,Pa",
					"default": "hPa"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": ["Homeassistant"]
				}
			},
			"offset": {
				"description": "Sensor Offsets",
				"tab": "Core",
				"temp": {
					"id": "temp_offset"
				},
				"pressure": {
					"id": "pressure_offset"
				},
				"humidity": {
					"id": "humidity_offset"
				},
				"type": {
					"fieldtype": "offset"
				},
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"temp" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin.",
				"tab": "Core",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 120,
					"step": 1
				},
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"gpio": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp.",
				"type": {
					"fieldtype": "gpio"
				},
				"tab": "Core",
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"invertgpio" : {
				"required": "false",
				"description": "Invert GPIO",
				"help": "Select this option if the device is wired to activate on the GPIO pin going Low",
				"tab": "Core",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"gpioon": {
				"required": "false",
				"description": "GPIO On",
				"help": "Label used when GPIO control is enabled.",
				"tab": "Core",
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"gpiooff": {
				"required": "false",
				"description": "GPIO Off",
				"help": "Label used when GPIO control is disabled.",
				"tab": "Core",
				"filters": {
					"filter": "type",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}
			},
			"noticecore" : {
				"tab": "Core",      
				"message": "This sensor is used by Allsky for basic temperature information. The following variables will be created<br>AS_TEMP, AS_HUMIDITY, AS_DEW, AS_PRESSURE, AS_ALTITUDE",
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
				"help": "The name of the sensor, will be added as a variable.",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
      			"SHT4x",
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
			"deadband1" : {
					"required": "false",
					"description": "Deadband Range",
					"help": "Deadband around Max Temp before changing state of the gpio pin",
					"tab": "Sensor 1",
					"type": {
							"fieldtype": "spinner",
							"min": 1,
							"max": 10,
							"step": 1
					}            
			},   
			"inputpin1": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices.",
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
			"dht221": {
				"required": "false",
				"description": "Retry Settings",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "dht22"
				},    
				"retry": {
					"id": "dhtxxretrycount1"
				},
				"delay": {
					"id": "dhtxxdelay1"
				},
				"power": {
					"id": "dhtxxpower1"
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
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x76.",
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
				"help": "Filename in /sys/bus/w1/devices.",
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
			"sht31heater1" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31.",
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
				"help": "Sets the SHT4x power mode.",
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
				"help": "The name of the file that will be written to the allsky/tmp/extra directory.",
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
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day.",
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
			"owunits1": {
				"required": "false",
				"description": "OpenWeather Units",
				"help": "Units requested from OpenWeather for this sensor.",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "select",
					"values": "metric,imperial,standard",
					"default": "metric"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": ["OpenWeather"]
				}
			},
			"owexpire1" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value.",
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
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/.",
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext1": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. Enter the gateway base URL, for example http://192.168.1.25. The module adds the data endpoint. See the documentation on how to obtain this URL.",
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
				"help": "Base URL of the Ecowitt gateway, for example http://192.168.1.25.",
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
				"help": "The url of your homeassistant server, will be something liek http://192.168.1.196:8123.",
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
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab.",
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
				"help": "The temperature units used in Homeassistant.",
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
				"help": "The id of the temperature sensor to read from Homeassistant.",
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
				"help": "The id of the humidity sensor to read from Homeassistant.",
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
				"help": "The id of the pressure sensor to read from Homeassistant.",
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
   		"offset1": {
				"description": "Sensor Offsets",
				"tab": "Sensor 1",
				"temp": {
					"id": "temp_offset1"
				},
				"pressure": {
					"id": "pressure_offset1"				
				},
				"humidity": {
					"id": "humidity_offset1"				
				},
				"type": {
					"fieldtype": "offset"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}    
			},
			"hasspressureunit1": {
				"required": "false",
				"description": "Pressure Unit",
				"tab": "Sensor 1",
				"help": "Units reported by the Home Assistant pressure sensor; converted to hPa for overlays.",
				"type": {
					"fieldtype": "select",
					"values": "hPa,mbar,inHg,mmHg,kPa,Pa",
					"default": "hPa"
				},
				"filters": {
					"filter": "type1",
					"filtertype": "show",
					"values": ["Homeassistant"]
				}
			},
			"temp1" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin.",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}             
			},        
			"gpio1": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                      
			},
			"invertgpio1" : {
				"required": "false",
				"description": "Invert GPIO",
				"help": "Select this option if the device is wired to activate on the GPIO pin going Low",
				"tab": "Sensor 1",
				"type": {
					"fieldtype": "checkbox"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}    
			},   
			"gpioon1": {
				"required": "false",
				"description": "GPIO On",
				"help": "Label used when GPIO control is enabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                      
			},
			"gpiooff1": {
				"required": "false",
				"description": "GPIO Off",
				"help": "Label used when GPIO control is disabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
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
				"help": "The name of the sensor, will be added as a variable.",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
      			"SHT4x",      
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
			"deadband2" : {
					"required": "false",
					"description": "Deadband Range",
					"help": "Deadband around Max Temp before changing state of the gpio pin",
					"tab": "Sensor 2",
					"type": {
							"fieldtype": "spinner",
							"min": 1,
							"max": 10,
							"step": 1
					}            
			},       
			"inputpin2": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for DHT type sensors, not required for i2c devices.",
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
			"dht222": {
				"required": "false",
				"description": "Retry Settings",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "dht22"
				},    
				"retry": {
					"id": "dhtxxretrycount2"
				},
				"delay": {
					"id": "dhtxxdelay2"
				},
				"power": {
					"id": "dhtxxpower2"
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
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x76.",
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
				"help": "Filename in /sys/bus/w1/devices.",
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
			"sht31heater2" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31.",
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
				"help": "Sets the SHT4x power mode.",
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
				"help": "The name of the file that will be written to the allsky/tmp/extra directory.",
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
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day.",
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
			"owunits2": {
				"required": "false",
				"description": "OpenWeather Units",
				"help": "Units requested from OpenWeather for this sensor.",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "select",
					"values": "metric,imperial,standard",
					"default": "metric"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": ["OpenWeather"]
				}
			},
			"owexpire2" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value.",
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
				"help": "The URL of your Homeassistant server, for example: http://192.168.1.196:8123.",
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
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab.",
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
				"help": "The temperature units used in Homeassistant.",
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
				"help": "The id of the temperature sensor to read from Homeassistant.",
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
				"help": "The id of the humidity sensor to read from Homeassistant.",
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
				"help": "The id of the pressure sensor to read from Homeassistant.",
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
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/.",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"hasspressureunit2": {
				"required": "false",
				"description": "Pressure Unit",
				"tab": "Sensor 2",
				"help": "Units reported by the Home Assistant pressure sensor; converted to hPa for overlays.",
				"type": {
					"fieldtype": "select",
					"values": "hPa,mbar,inHg,mmHg,kPa,Pa",
					"default": "hPa"
				},
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": ["Homeassistant"]
				}
			},
			"ecowittapikey2": {
				"required": "false",
				"description": "API Key",
				"tab": "Sensor 2",            
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/.",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},
			"ecowittlocalurltext2": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. Enter the gateway base URL, for example http://192.168.1.25. The module adds the data endpoint. See the documentation on how to obtain this URL.",
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
				"help": "Base URL of the Ecowitt gateway, for example http://192.168.1.25.",
				"filters": {
					"filter": "type2",
					"filtertype": "show",
					"values": [
						"Ecowitt Local"
					]
				}    				
			},    
   		"offset2": {
				"description": "Sensor Offsets",
				"tab": "Sensor 2",
				"temp": {
					"id": "temp_offset2"
				},
				"pressure": {
					"id": "pressure_offset2"
				},
				"humidity": {
					"id": "humidity_offset2"				
				},
				"type": {
					"fieldtype": "offset"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}     
			},          
			"temp2" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin.",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}            
			},        
			"gpio2": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                     
			},
			"invertgpio2" : {
				"required": "false",
				"description": "Invert GPIO",
				"help": "Select this option if the device is wired to activate on the GPIO pin going Low",
				"tab": "Sensor 2",
				"type": {
					"fieldtype": "checkbox"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}    
			},    
			"gpioon2": {
				"required": "false",
				"description": "GPIO On",
				"help": "Label used when GPIO control is enabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                     
			},
			"gpiooff2": {
				"required": "false",
				"description": "GPIO Off",
				"help": "Label used when GPIO control is disabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
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
				"help": "The name of the sensor, will be added as a variable.",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"SHT31",
						"DHT22",
						"DHT11",
      			"SHT4x",      
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
			"deadband3" : {
					"required": "false",
					"description": "Deadband Range",
					"help": "Deadband around Max Temp before changing state of the gpio pin",
					"tab": "Sensor 3",
					"type": {
							"fieldtype": "spinner",
							"min": 1,
							"max": 10,
							"step": 1
					}            
			},           
			"inputpin3": {
				"required": "false",
				"description": "Input Pin",
				"help": "DHTxx Input pin",    
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
			"dht223": {
				"required": "false",
				"description": "Retry Settings",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "dht22"
				},    
				"retry": {
					"id": "dhtxxretrycount3"
				},
				"delay": {
					"id": "dhtxxdelay3"
				},
				"power": {
					"id": "dhtxxpower3"
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
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x76.",
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
				"help": "Filename in /sys/bus/w1/devices,",
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
			"sht31heater3" : {
				"required": "false",
				"description": "Enable SHT31 Heater",
				"help": "Enable the inbuilt heater on the SHT31,",
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
				"help": "Sets the SHT4x power mode,",
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
				"message": "<b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the Open Weather Map module as well. If you are using this function then please remove the Open Weather Map module as both create the same overlay data,",
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
				"help": "The name of the file that will be written to the allsky/tmp/extra directory.",
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
				"help": "Reads data every x seconds. Be careful of the free 1000 request limit per day.",
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
			"owunits3": {
				"required": "false",
				"description": "OpenWeather Units",
				"help": "Units requested from OpenWeather for this sensor.",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "select",
					"values": "metric,imperial,standard",
					"default": "metric"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": ["OpenWeather"]
				}
			},
			"owexpire3" : {
				"required": "false",
				"description": "Expiry Time",
				"help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value.",
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
				"help": "The Ecowitt application key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt api key. This is created in your user profile on https://www.ecowitt.net/.",
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
				"help": "The Ecowitt MAC Address. This can be found in your devices page on https://www.ecowitt.net/.",
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": [
						"Ecowitt"
					]
				}    				
			},   
			"ecowittlocalurltext3": {
				"message": "To use this sensor you will require an Ecowitt Gateway such as the GW2000. Enter the gateway base URL, for example http://192.168.1.25. The module adds the data endpoint. See the documentation on how to obtain this URL.",
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
				"help": "Base URL of the Ecowitt gateway, for example http://192.168.1.25.",
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
				"help": "The url of your Homeassistant server, for example: http://192.168.1.196:8123.",
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
				"help": "The Homeassistant long term token, generated in your hass user profile under the security tab.",
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
				"help": "The temperature units used in Homeassistant.",
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
				"help": "The id of the temperature sensor to read from Homeassistant.",
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
				"help": "The id of the humidity sensor to read from Homeassistant.",
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
				"help": "The id of the pressure sensor to read from Homeassistant.",
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
   		"offset3": {
				"description": "Sensor Offsets",
				"tab": "Sensor 3",
				"temp": {
					"id": "temp_offset3"
				},
				"pressure": {
					"id": "pressure_offset3"
				},
				"humidity": {
					"id": "humidity_offset3"
				},
				"type": {
					"fieldtype": "offset"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}     
			},            
			"hasspressureunit3": {
				"required": "false",
				"description": "Pressure Unit",
				"tab": "Sensor 3",
				"help": "Units reported by the Home Assistant pressure sensor; converted to hPa for overlays.",
				"type": {
					"fieldtype": "select",
					"values": "hPa,mbar,inHg,mmHg,kPa,Pa",
					"default": "hPa"
				},
				"filters": {
					"filter": "type3",
					"filtertype": "show",
					"values": ["Homeassistant"]
				}
			},
			"temp3" : {
				"required": "false",
				"description": "Max Temp",
				"help": "Above this temperature trigger the gpio pin.",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "spinner",
					"min": -100,
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}            
			},        
			"gpio3": {
				"required": "false",
				"description": "GPIO Pin",
				"help": "The GPIO pin to set high when the temp is above the Max Temp.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                    
			},
			"invertgpio3" : {
				"required": "false",
				"description": "Invert GPIO",
				"help": "Select this option if the device is wired to activate on the GPIO pin going Low",
				"tab": "Sensor 3",
				"type": {
					"fieldtype": "checkbox"
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}    
			},    
			"gpioon3": {
				"required": "false",
				"description": "GPIO On",
				"help": "Label used when GPIO control is enabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
					]
				}                     
			},
			"gpiooff3": {
				"required": "false",
				"description": "GPIO Off",
				"help": "Label used when GPIO control is disabled.",
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
						"BME680",
						"Ecowitt",
						"Ecowitt Local",
						"Homeassistant"
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
			],
			"v1.0.3" : [
				{
					"author": "Neil nbl1268",
					"authorurl": "https://github.com/nbl1268",
					"changes": [
						"Add Deadband logic",
						"Added addition extra data values"
					]
				},
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Fixed bug with sht4x sensor name"
					]
				}    
			],
			"v1.0.4" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Added offsets for temp, humidity and pressure",
      			"Added option to power DHTxx from GPIO pin"
					]
				}
			],
			"v1.0.5" : [
				{
					"author": "Benjamin Hartwich (Agent assisted)",
					"authorurl": "https://github.com/benhartwich/",
					"changes": "The pressure variables have the type pressure, so the Overlay Editor offers the pressure formats (hPa, inHg, mmHg)"
				}
			],
			"v1.0.6" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Lots of minor bug fixes detailed below",
						"Add missing Core sensor controls, DHT power pin, and per-sensor OpenWeather unit settings",
						"Remove the unsupported Allsky Sensor selection from Core sensor settings",
						"Correct setting filters and defaults for Core and Sensors 1-3, including negative Max Temp thresholds",
						"Correct extra data metadata, including the relative humidity field type",
						"Correct the default extra data filename to allsky_temp.json",
						"Fix OpenWeather unit selection, API and cache handling, dew point calculation, and API key redaction in errors",
						"Use separate OpenWeather polling and cache data for each sensor, and read rain fields using the current API keys",
						"Record module runs correctly for frequency scheduling",
						"Handle missing DS18B20 devices and failed reads; use the DHT11 driver for DHT11 sensors and release DHT devices after reading",
						"Correct BME280 relative humidity output and handle missing Ecowitt data or URL endpoint suffixes",
						"Allow partial Home Assistant sensor configuration and convert pressure to hPa with a per-sensor unit setting",
						"Reject non-finite sensor readings and invalid dew point inputs before publishing data",
						"Apply offsets consistently, including relative humidity and recalculated dew point",
						"Correct Core and additional sensor GPIO state, labels, deadband reporting, and output when only non-temperature readings are available",
						"Clear stale extra data when no sensors return readings",
						"Refresh the README to show current settings and extra data keys"
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

	def _finite_number(self, value, name):
		if value is None:
			return None
		try:
			number = float(value)
		except (TypeError, ValueError, OverflowError):
			self.log(3, f'WARNING: Ignoring non-numeric {name}: {value}')
			return None
		if not math.isfinite(number):
			self.log(3, f'WARNING: Ignoring non-finite {name}: {value}')
			return None
		return number

	def _calculate_dew_point(self, temperature, humidity):
		try:
			if not 1 <= humidity <= 100:
				self.log(3, f'WARNING: Cannot calculate dew point with humidity {humidity}; expected 1-100%')
				return None
			return dew_point(temperature, humidity)
		except (TypeError, ValueError, OverflowError, ZeroDivisionError) as error:
			self.log(3, f'WARNING: Cannot calculate dew point: {error}')
			return None

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

		self._set_extra_value('rain.1h', data, 'OWRAIN1HR', expires, extra_data)
		self._set_extra_value('rain.3h', data, 'OWRAIN3HR', expires, extra_data)

		self._set_extra_value('sys.sunrise', data, 'OWSUNRISE', expires, extra_data)
		self._set_extra_value('sys.sunset', data, 'OWSUNSET', expires, extra_data)
		extra_data['AS_OWUNITS'] = units

		the_dew_point = None
		temperature = self._finite_number(self._get_value('main.temp', data), 'OpenWeather temperature')
		humidity = self._finite_number(self._get_value('main.humidity', data), 'OpenWeather humidity')
		if temperature is not None and humidity is not None:
			try:
				unit_code = {'imperial': 'f', 'standard': 'k'}.get(units, 'c')
				t = Temp(float(temperature), unit_code)
				point = self._calculate_dew_point(t, humidity)
				if point is not None:
					the_dew_point = self._finite_number(getattr(point, unit_code), 'OpenWeather dew point')
			except (TypeError, ValueError) as error:
				self.log(3, f'WARNING: Cannot calculate OpenWeather dew point: {error}')

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

		if the_dew_point is not None:
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
		if isinstance(value, (int, float)) and self._finite_number(value, f'OpenWeather {path}') is None:
			return
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
		cached_units = None

		extra_path = allsky_shared.get_extra_dir(True)
		extra_data_fileName = os.path.join(extra_path, file_name)

		try:
			if os.path.isfile(extra_data_fileName):
				file_modified_time = int(os.path.getmtime(extra_data_fileName))
				with open(extra_data_fileName, 'r', encoding='utf-8') as file:
					json_data = json.load(file)
					cached_units = json_data.get('AS_OWUNITS')
					if cached_units in ('metric', 'imperial', 'standard'):
						temperature = self._get_ow_Value('AS_OWTEMP', json_data, file_modified_time)
						humidity = self._get_ow_Value('AS_OWHUMIDITY', json_data, file_modified_time)
						pressure = self._get_ow_Value('AS_OWPRESSURE', json_data, file_modified_time)
						the_dew_point = self._get_ow_Value('AS_OWDEWPOINT', json_data, file_modified_time)
		except (OSError, ValueError, TypeError, AttributeError) as error:
			self.log(3, f'WARNING: Invalid OpenWeather cache {file_name}: {error}')
			return None, None, None, None, None

		return temperature, humidity, pressure, the_dew_point, cached_units

	def _get_ow_Value(self, field, json_data, file_modified_time):
		entry = json_data.get(field)
		if entry is None:
			return None

		result = entry.get('value')
		if 'expires' in entry:
			max_age = entry['expires']
			age = int(time.time()) - file_modified_time
			if age > max_age:
				self.log(4, f'WARNING: field {field} has expired - age is {age}')
				result = None
				
		return result

	def _get_value(self, path, data):
		result = None
		keys = path.split('.')
		if keys[0] in data:
			sub_data = data[keys[0]]
			
			if isinstance(sub_data, list):
				if sub_data and isinstance(sub_data[0], dict):
					result = sub_data[0].get(keys[1])
			elif isinstance(sub_data, dict):
				result = sub_data.get(keys[1])

		return result

	def _read_open_weather(self, sensor_number):
		expire = self.get_param('owexpire' + sensor_number, 600, int)
		period = self.get_param('owperiod' + sensor_number, 60, int)
		api_key = self.get_param('owapikey' + sensor_number, '', str)
		file_name = self.get_param('owfilename' + sensor_number, f'allsky_owdata{sensor_number}.json', str, True)
		units = self.get_param('owunits' + sensor_number, 'metric', str) or 'metric'
		if units not in ('metric', 'imperial', 'standard'):
			self.log(3, f'WARNING: Invalid OpenWeather units {units}; using metric')
			units = 'metric'
		module = f"{self.meta_data['module']}_ow_{sensor_number or 'core'}"

		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None

		try:
			_, _, _, _, cached_units = self._get_ow_values(file_name)
			should_run, diff = allsky_shared.shouldRun(module, period)
			if should_run or self.debug_mode or cached_units not in ('metric', 'imperial', 'standard'):
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
									self.log(4, f"INFO: Reading OpenWeather API at {lat}, {lon} with {units} units")
									response = requests.get(ow_url, timeout=10)
									if response.status_code == 200:
										raw_data = response.json()
										extra_data = self._process_ow_result(raw_data, expire, units)
										allsky_shared.saveExtraData(file_name, extra_data, 'internal')
										allsky_shared.setLastRun(module)
										result = f'Data acquired and written to extra data file {file_name}'
										self.log(4, f'INFO: {result}')
									else:
										result = f'Got error from Open Weather Map API. Response code {response.status_code}'
										self.log(0, f'ERROR in {__file__}: {result}')
								except Exception as e:
									eType, eObject, eTraceback = sys.exc_info()            
									result = str(e).replace(api_key, '[redacted]')
									self.log(0, f'ERROR in {__file__}: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {result}')
							else:
								result = 'Invalid Longitude. Check the Allsky configuration'
								self.log(0, f'ERROR in {__file__}: {result}')
						else:
							result = 'Invalid Latitude. Check the Allsky configuration'
							self.log(0, f'ERROR in {__file__}: {result}')
					else:
						result = 'Missing filename for data'
						self.log(0, f'ERROR in {__file__}: {result}')
				else:
					result = 'Missing Open Weather Map API key'
					self.log(0, f'ERROR in {__file__}: {result}')
			else:
				self.log(4, f'INFO: Using Cached Openweather API data')

			temperature, humidity, pressure, the_dew_point, cached_units = self._get_ow_values(file_name)
			if temperature is not None:
				if cached_units == 'imperial':
					temperature = (temperature - 32) * 5 / 9
				elif cached_units == 'standard':
					temperature -= 273.15
			if the_dew_point is not None:
				if cached_units == 'imperial':
					the_dew_point = (the_dew_point - 32) * 5 / 9
				elif cached_units == 'standard':
					the_dew_point -= 273.15

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			safe_error = str(e).replace(api_key, '[redacted]') if api_key else str(e)
			self.log(0, f'ERROR in {__file__}: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {safe_error}')

		return temperature, humidity, pressure, the_dew_point	

	def _read_ds18B20(self, sensor_number="", retries=3):
		"""Read a DS18B20 temperature in Celsius."""
		device_id = self.get_param('ds18b20address' + sensor_number, '', str)
		base_path = "/sys/bus/w1/devices"
		devices = ([f"{base_path}/{device_id}/w1_slave"] if device_id
			else glob.glob(f"{base_path}/28-*/w1_slave"))

		if not devices:
			self.log(0, f'ERROR in {__file__}: No DS18B20 device found. Check /sys/bus/w1/devices')
			return None, None

		for _ in range(retries):
			try:
				with open(devices[0], "r", encoding="utf-8") as sensor_file:
					lines = sensor_file.read().splitlines()
				if len(lines) >= 2 and lines[0].strip().endswith("YES") and "t=" in lines[1]:
					temp_milli = int(lines[1].split("t=", 1)[1])
					return round(temp_milli / 1000.0, 2), None
			except (OSError, ValueError) as error:
				self.log(0, f'ERROR in {__file__}: Failed to read DS18B20: {error}')
				return None, None
			time.sleep(0.2)

		self.log(0, f'ERROR in {__file__}: DS18B20 CRC check failed')
		return None, None
  
	def _read_htu21(self, sensor_number):
		temperature = None
		humidity = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)    
		if i2c_address != '':
			try:
				i2c_address_int = int(i2c_address, 16)
			except:
				result = f'Address {i2c_address} is not a valid i2c address'
				self.log(0, f'ERROR in {__file__}: {result}')

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
			self.log(0, f'ERROR in {__file__}: Module read_htu21 failed on line {eTraceback.tb_lineno} - {e}')
			
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
				self.log(0, f'ERROR in {__file__}: {result}')

		try:
			i2c = board.I2C()
			if i2c_address != "":  
				sensor = adafruit_ahtx0.AHTx0(i2c, i2c_address_int)
			else:
				sensor = adafruit_ahtx0.AHTx0(i2c)
			temperature = sensor.temperature
			humidity = sensor.relative_humidity
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(0, f"ERROR in {__file__}: Module read_ahtx0 failed on line {eTraceback.tb_lineno} - {e}")

		return temperature, humidity

	def _do_dhtxx_read(self, input_pin, sensor_type='DHT22'):
		temperature = None
		humidity = None
		dht_device = None

		try:
			pin = allsky_shared.getGPIOPin(input_pin)
			device_class = adafruit_dht.DHT11 if sensor_type == 'DHT11' else adafruit_dht.DHT22
			dht_device = device_class(pin, use_pulseio=False)
			try:
				temperature = dht_device.temperature
				humidity = dht_device.humidity
			except RuntimeError as e:
				eType, eObject, eTraceback = sys.exc_info()
				self.log(3, f'ERROR in {__file__}: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(3, f'WARNING: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}')
		finally:
			if dht_device is not None:
				try:
					dht_device.exit()
				except Exception as e:
					self.log(3, f'WARNING: Failed to release DHT sensor: {e}')

		return temperature, humidity

	def _read_dht22(self, sensor_number, sensor_type='DHT22'):
		temperature = None
		humidity = None
		count = 0
		reading = True

		input_pin = self.get_param('inputpin' + sensor_number, 0, int)
		dhtxx_retry_count = self.get_param('dhtxxretrycount' + sensor_number, 0, int)
		dhtxx_delay = self.get_param('dhtxxdelay' + sensor_number, 0, int)

		dhtxx_power = self.get_param('dhtxxpower' + sensor_number, 0, int)

		if dhtxx_power != 0:
					allsky_shared.set_gpio_pin(dhtxx_power, "on", f"Sensor {sensor_number} Power DHTxx")
					time.sleep(1)

		while reading:
			temperature, humidity = self._do_dhtxx_read(input_pin, sensor_type)
			if temperature is None and humidity is None:
				self.log(3, f'WARNING: Failed to read DHTXX on attempt {count+1}')
				count = count + 1
				if count > dhtxx_retry_count:
					reading = False
				else:
					time.sleep(dhtxx_delay/1000)
			else:
				reading = False

		if dhtxx_power != 0:
    			allsky_shared.set_gpio_pin(dhtxx_power, "off")
       
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
					self.log(0, f'ERROR in {__file__}: Module read_bme680 failed on line {eTraceback.tb_lineno} - {e}')

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
			self.log(0, f'ERROR in {__file__}: Module read_bme680 failed on line {eTraceback.tb_lineno} - {e}')
    
		return temperature, humidity, pressure

	def _read_bme280_i2c(self, sensor_number):
		temperature = None
		humidity = None
		pressure = None
		rel_humidity = None
		altitude = None

		i2c_address = self.get_param('i2caddress' + sensor_number, '', str)	
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				self.log(0, f'ERROR in {__file__}: Module read_bme280_i2c failed on line {eTraceback.tb_lineno} - {e}')

		try:
			i2c = board.I2C()
			if i2c_address != "":
				bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, i2c_address_int)
			else:
				bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

			temperature =  bme280.temperature
			humidity = bme280.humidity
			rel_humidity = bme280.relative_humidity
			altitude = bme280.altitude
			pressure = bme280.pressure
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(0, f'ERROR in {__file__}: Module read_bme280_i2c failed on line {eTraceback.tb_lineno} - {e}')

		return temperature, humidity, pressure, rel_humidity, altitude

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
				self.log(0, f'ERROR in {__file__}: {result}')
					
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
			self.log(0, f'ERROR in {__file__}: Module read_sht31 failed on line {eTraceback.tb_lineno} - {e}')
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
				self.log(0, f'ERROR in {__file__}: {result}')
					
		try:
			i2c = board.I2C()
			if i2c_address != '':
				sensor = adafruit_sht4x.SHT4x(i2c, i2c_address_int)
			else:
				sensor = adafruit_sht4x.SHT4x(i2c)
			sensor.mode = sht41_mode
			self.log(4, f'INFO: Current mode is {adafruit_sht4x.Mode.string[sensor.mode]}')
			temperature, humidity = sensor.measurements
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			self.log(0, f'ERROR in {__file__}: Module _read_sht4x failed on line {eTraceback.tb_lineno} - {e}')
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
				self.log(0, f'ERROR in {__file__}: {result}')
					
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
			self.log(0, f'ERROR in {__file__}: Module _read_scd30 failed on line {eTraceback.tb_lineno} - {e}')

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
		if not isinstance(data, dict):
			self.log(0, f'ERROR in {__file__}: Ecowitt data unavailable: {data}')
			return None, None, None, None

		outdoor = data.get('outdoor') or {}
		pressure_data = data.get('pressure') or {}
		temperature = outdoor.get('temperature')
		humidity = outdoor.get('humidity')
		pressure = pressure_data.get('relative')
		the_dew_point = outdoor.get('dew_point')
  
		return temperature, humidity, pressure, the_dew_point	
    
	def _read_ecowitt_local(self, sensor_number):
     
		temperature = None
		humidity = None
		pressure = None
		the_dew_point = None
  
		local_url = self.get_param('ecowittlocalurl' + sensor_number, '', str).strip()
		for endpoint in ('/get_livedata_info?', '/get_livedata_info'):
			if local_url.endswith(endpoint):
				local_url = local_url[:-len(endpoint)]
				break
		local_url = local_url.rstrip('/')
		if not local_url:
			self.log(0, f'ERROR in {__file__}: Local Ecowitt base URL is required')
			return None, None, None, None

		data = allsky_shared.get_ecowitt_local_data(local_url)
		if not isinstance(data, dict):
			self.log(0, f'ERROR in {__file__}: Local Ecowitt data unavailable: {data}')
			return None, None, None, None

		outdoor = data.get('outdoor') or {}
		pressure_data = data.get('pressure') or {}
		temperature = outdoor.get('temperature')
		humidity = outdoor.get('humidity')
		pressure = pressure_data.get('relative')
		the_dew_point = outdoor.get('dew_point')
  
		return temperature, humidity, pressure, the_dew_point	

	def _read_homeassistant(self, sensor_number):
		temperature = None
		humidity = None
		pressure = None

		hass_url = self.get_param('hassurl' + sensor_number, '', str)
		hass_ltt = self.get_param('hassltt' + sensor_number, '', str)
		hass_unit = self.get_param('hassunit' + sensor_number, '', str)
		hass_pressure_unit = self.get_param('hasspressureunit' + sensor_number, 'hPa', str)
		hass_temperature = self.get_param('hasstemp' + sensor_number, '', str)
		hass_humidity = self.get_param('hasshumidity' + sensor_number, '', str)
		hass_pressure = self.get_param('hasspressure' + sensor_number, '', str)

		if not hass_url or not hass_ltt:
			self.log(0, f'ERROR in {__file__}: Home Assistant URL and token are required')
			return None, None, None
		if not any((hass_temperature, hass_humidity, hass_pressure)):
			self.log(0, f'ERROR in {__file__}: Configure at least one Home Assistant sensor')
			return None, None, None

		if hass_temperature:
			temperature = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_temperature)
		if hass_humidity:
			humidity = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_humidity)
		if hass_pressure:
			pressure = allsky_shared.get_hass_sensor_value(hass_url, hass_ltt, hass_pressure)
			pressure = self._finite_number(pressure, 'Home Assistant pressure')
			if pressure is not None:
				pressure_factors = {
					'hpa': 1.0,
					'mbar': 1.0,
					'inhg': 1 / 0.0295299830714,
					'mmhg': 1 / 0.750061683,
					'kpa': 10.0,
					'pa': 0.01,
				}
				factor = pressure_factors.get(hass_pressure_unit.strip().lower())
				if factor is None:
					self.log(0, f'ERROR in {__file__}: Unsupported Home Assistant pressure unit {hass_pressure_unit}')
					pressure = None
				else:
					pressure = self._finite_number(pressure * factor, 'converted Home Assistant pressure')

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
			temperature, humidity = self._read_dht22(sensor_number, sensor_type)
		elif sensor_type == 'BME280-I2C':
			temperature, humidity, pressure, rel_humidity, altitude = self._read_bme280_i2c(sensor_number)
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
			self.log(0, f'ERROR in {__file__}: No sensor type defined')

		temperature = self._finite_number(temperature, f'{sensor_type} temperature')
		humidity = self._finite_number(humidity, f'{sensor_type} humidity')
		the_dew_point = self._finite_number(the_dew_point, f'{sensor_type} dew point')
		pressure = self._finite_number(pressure, f'{sensor_type} pressure')
		rel_humidity = self._finite_number(rel_humidity, f'{sensor_type} relative humidity')
		altitude = self._finite_number(altitude, f'{sensor_type} altitude')
		co2 = self._finite_number(co2, f'{sensor_type} CO2')

		temp_units = allsky_shared.getSetting('temptype')
		if temperature is not None and humidity is not None:
			point = self._calculate_dew_point(temperature, humidity)
			the_dew_point = point.c if point is not None else None
		if temp_units == 'F':
			if temperature is not None:
				temperature = (temperature * (9/5)) + 32
			if the_dew_point is not None:
				the_dew_point = (the_dew_point * (9/5)) + 32
		if temperature is not None:
			temperature = round(temperature, 2)
		if humidity is not None:
			humidity = round(humidity, 2)
		if the_dew_point is not None:
			the_dew_point = round(the_dew_point, 2)
					
		return temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2

	def _debug_output(self, sensor_type, temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2, temp_offset, humidity_offset, pressure_offset):
		self.log(4, f'INFO: Sensor {sensor_type} read. Temperature {temperature} Humidity {humidity} Relative Humidity {rel_humidity} Dew Point {the_dew_point} Pressure {pressure} Altitude {altitude} Co2 {co2}')
  
		if temp_offset != 0 or humidity_offset != 0 or pressure_offset != 0:
			self.log(4, f'INFO: Offsets applied. Temperature offset {temp_offset} Humidity offset {humidity_offset} Pressure offset {pressure_offset}')

	def run(self):
		result = ''
		extra_data = {}
		self._run_interval = self.get_param('frequency', 60, int)  

		should_run, diff = allsky_shared.shouldRun('allskytemp', self._run_interval)      


		if should_run or self.debug_mode:
			allsky_shared.setLastRun('allskytemp')
			for sensor_number_itr in range(1,5):
				if sensor_number_itr == 1:
					sensor_number = ""
				else:
					sensor_number = str(sensor_number_itr - 1)

				sensor_type = self.get_param('type' + sensor_number, 'None', str)

				if sensor_type != 'None':
					self.log(4, f'INFO: Reading sensor {sensor_number}, {sensor_type}')
					name = self.get_param('name' + sensor_number, 'Unknown', str)
					invert_gpio = self.get_param('invertgpio' + sensor_number, False, bool)
					dead_band = self.get_param('deadband' + sensor_number, 0, int)
     
					temp_offset = self._finite_number(self.get_param('temp_offset' + sensor_number, 0.0, float), 'temperature offset')
					if temp_offset is None:
						temp_offset = 0.0
					pressure_offset = self.get_param('pressure_offset' + sensor_number, 0, int)
					humidity_offset = self.get_param('humidity_offset' + sensor_number, 0, int)
          
					control_state = "Unknown"
     
					max_temp_key = "temp" + sensor_number
					max_temp = self._finite_number(self.get_param(max_temp_key, None, float), 'Max Temp')
					
					gpio_key =  'gpio' + sensor_number
					gpio_pin = self.get_param(gpio_key, -1, int)          
					gpio_on_label = self.get_param('gpioon' + sensor_number, 'On', str)
					gpio_off_label = self.get_param('gpiooff' + sensor_number, 'Off', str)
			
					temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2 = self._get_sensor_reading(sensor_type, sensor_number)
					if temperature is not None:
						temperature = self._finite_number(temperature + temp_offset, 'adjusted temperature')
						if temperature is not None:
							temperature = round(temperature, 2)
					if humidity is not None:
						humidity = self._finite_number(humidity + humidity_offset, 'adjusted humidity')
						if humidity is not None:
							humidity = round(humidity, 2)
					if temperature is not None and humidity is not None and (temp_offset or humidity_offset):
						temp_units = allsky_shared.getSetting('temptype')
						temperature_c = (temperature - 32) * 5 / 9 if temp_units == 'F' else temperature
						point = self._calculate_dew_point(temperature_c, humidity)
						the_dew_point = point.c if point is not None else None
						if temp_units == 'F' and the_dew_point is not None:
							the_dew_point = (the_dew_point * 9 / 5) + 32
					if the_dew_point is not None:
						the_dew_point = self._finite_number(the_dew_point, 'adjusted dew point')
						if the_dew_point is not None:
							the_dew_point = round(the_dew_point, 2)
					if pressure is not None:
						pressure = self._finite_number(pressure + pressure_offset, 'adjusted pressure')
						if pressure is not None:
							pressure = round(pressure, 0)
					if rel_humidity is not None:
						rel_humidity = self._finite_number(rel_humidity + humidity_offset, 'adjusted relative humidity')
						if rel_humidity is not None:
							rel_humidity = round(rel_humidity, 2)
					if altitude is not None:
						altitude = self._finite_number(altitude, 'altitude')
						if altitude is not None:
							altitude = round(altitude, 0)
					if co2 is not None:
						co2 = self._finite_number(co2, 'CO2')
						if co2 is not None:
							co2 = round(co2, 0)
					self._debug_output(sensor_type, temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2, temp_offset, humidity_offset, pressure_offset)

					gpio_state = 'N/A'
					if temperature is not None:
						if max_temp is not None and gpio_pin != -1:
							try:
								if temperature >= (max_temp + dead_band):
									pin_state = 'off' if invert_gpio else 'on'
									allsky_shared.set_gpio_pin(gpio_pin, pin_state, f"Temp {sensor_number or 'Core'}")
									gpio_state = gpio_on_label
									control_state = f"Temperature {temperature} is above the threshold, so GPIO {gpio_pin} is enabled."
								elif temperature <= (max_temp - dead_band):
									pin_state = 'on' if invert_gpio else 'off'
									allsky_shared.set_gpio_pin(gpio_pin, pin_state, f"Temp {sensor_number or 'Core'}")
									gpio_state = gpio_off_label
									control_state = f"Temperature {temperature} is below the threshold, so GPIO {gpio_pin} is disabled."
								else:
									pin_is_on = allsky_shared.get_gpio_pin(gpio_pin)
									gpio_state = gpio_on_label if pin_is_on != invert_gpio else gpio_off_label
									control_state = f"Temperature {temperature} is within the deadband, so GPIO {gpio_pin} is unchanged."
								self.log(4, f'INFO: {control_state}')
							except Exception as e:
								eType, eObject, eTraceback = sys.exc_info()
								result = f'ERROR in {__file__}: Failed to access GPIO {gpio_pin} on line {eTraceback.tb_lineno} - {e}'
								self.log(0, result)
						else:
							control_state = f"GPIO not enabled for sensor {sensor_number or 'Core'}."
							self.log(4, f'INFO: {control_state}')
					else:
						control_state = f"Temperature reading failed so leaving GPIO {gpio_pin} as is."
						self.log(4, f'INFO: {control_state}')
								
					if any(value is not None for value in (temperature, humidity, the_dew_point, pressure, rel_humidity, altitude, co2)):
						extra_data['AS_GPIOSTATE' + sensor_number] = gpio_state
						extra_data['AS_TEMPSENSOR' + sensor_number] = str(sensor_type)
						extra_data['AS_TEMPSENSORNAME' + sensor_number] = name
						if temperature is not None:
							extra_data['AS_TEMP' + sensor_number] = temperature
						if the_dew_point is not None:
							extra_data['AS_DEW' + sensor_number] = the_dew_point
						if humidity is not None:
							extra_data['AS_HUMIDITY' + sensor_number] = humidity
						if max_temp is not None:
							extra_data['AS_MAXTEMP' + sensor_number] = max_temp
						extra_data['AS_DEADBAND' + sensor_number] = dead_band
						extra_data['AS_CONTROLSTATE' + sensor_number] = control_state
						if pressure is not None:
							extra_data["AS_PRESSURE" + sensor_number] = pressure
						if rel_humidity is not None:
							extra_data["AS_RELHUMIDITY" + sensor_number] = rel_humidity
						if altitude is not None:
							extra_data["AS_ALTITUDE" + sensor_number] = altitude
						if co2 is not None:
							extra_data["AS_CO2" + sensor_number] = co2
					else:
						if sensor_number == "":
							self.log(4, 'INFO: Core sensor returned no data')
						else:
							self.log(4, f'INFO: Sensor {sensor_number} returned no data')
			if extra_data:
				allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
			else:
				allsky_shared.saveExtraData(self.meta_data['extradatafilename'], {}, self.meta_data['module'])

		else:
			result = 'Will run in {:.2f} seconds'.format(self._run_interval - diff)
			self.log(4, f'INFO: {result}')

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
