# TODO: Add units to data
# TODO: Use units for OW
# TODO: Add ability to make fields manatory depending upon a select value
# TODO: Add much better validation for params, like on OW
import allsky_shared as s
import time
import sys
import os
import json
import urllib.request
import requests
import json
import board
import math
from pathlib import Path
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
from digitalio import DigitalInOut, Direction, Pull
from DS18B20dvr.DS18B20 import DS18B20
	
metaData = {
	"name": "Environment Monitor",
	"description": "Reads upto 3 environment sensors",
	"module": "allsky_temp",
	"version": "v1.0.2",
	"events": [
	    "periodic",
	    "day",
	    "night"
	],
	"experimental": "false",
	"centersettings": "false",
	"testable": "true",
	"extradata": {
	    "info": {
	        "count": 4,
	        "firstblank": "true"
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
	            "type": "float"
	        },
	        "AS_PRESSURE${COUNT}": {
	            "name": "${PRESSURE${COUNT}}",
	            "format": "",
	            "sample": "",                 
	            "group": "Environment",
	            "description": "Pressure from ${AS_TEMPSENSORNAME${COUNT}}",
	            "type": "float"
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
	            "type": "float"
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
		"owapikey": "",        
		"owfilename": "",        
		"owperiod": "",        
		"owunits": "",        
		"owexpire": "",
  
	    "type1": "None",
	    "name1": "",
	    "inputpin1": "",
	    "i2caddress1": "",
	    "ds18b20address1": "",
	    "dhtxxretrycount1": "2",
	    "dhtxxdelay1" : "500",
	    "sht31heater1": "False",
	    "temp1": "",
	    "gpio1": "",
	    "gpioon1": "On",
	    "gpiooff1": "Off",
		"owapikey1": "",        
		"owfilename1": "",        
		"owperiod1": "",        
		"owunits1": "",        
		"owexpire1": "",  
	    
	    "type2": "None",
	    "name2": "",
	    "inputpin2": "",
	    "i2caddress2": "",
	    "ds18b20address2": "",
	    "dhtxxretrycount2": "2",
	    "dhtxxdelay2" : "500",
	    "sht31heater2": "False",
	    "temp2": "",
	    "gpio2": "",
	    "gpioon2": "On",
	    "gpiooff2": "Off",
		"owapikey2": "",        
		"owfilename2": "",        
		"owperiod2": "",        
		"owunits2": "",        
		"owexpire2": "",  
	         
	    "type3": "None",
	    "name3": "",
	    "inputpin3": "",
	    "i2caddress3": "",
	    "ds18b20address3": "",
	    "dhtxxretrycount3": "2",
	    "dhtxxdelay3" : "500",
	    "sht31heater3": "False",
	    "temp3": "",
	    "gpio3": "",
	    "gpioon3": "On",
	    "gpiooff3": "Off",
		"owapikey3": "",
		"owfilename3": "",
		"owperiod3": "",
		"owunits3": "",
		"owexpire3": ""
	    
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
	            "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,OpenWeather",
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
	            	"BME280-I2C",
	            	"HTU21",
	             	"AHTx0"
				]
			}            
	    },
	    "ds18b20address": {
	        "required": "false",
	        "description": "DS18B20 Address",
	        "tab": "Core",
	        "help": "Filename in /sys/bus/w1/devices",
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
	        "help": "Your Open Weather Map API key."         ,
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
		"noticecore" : {
	        "tab": "Core",      
			"message": "This sensor is used by Allksy for basic temperature information. The following Variables will be created<br>AS_TEMP - The temperature<br>AS_HUMIDITY - The Humidity<br>AS_DEWPOINT - the dew point<br>AS_HEATINDEX - The heatindex<br>AS_PRESSURE - <Only if supported by the sensor> Barometric Pressure<br>AS_ALTITUDE - <Only if supported by the sensor> The altitude",
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
	            "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,OpenWeather",
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
	                "OpenWeather"
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
	            	"BME280-I2C",
	            	"HTU21",
	             	"AHTx0"
				]
			}            
	    },
	    "ds18b20address1": {
	        "required": "false",
	        "description": "DS18B20 Address",
	        "tab": "Sensor 1",
	        "help": "Filename in /sys/bus/w1/devices",
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
	        "tab": "Sensor 1",            
	        "help": "Your Open Weather Map API key."         ,
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	            "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,OpenWeather",
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
	                "OpenWeather"
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
	            	"BME280-I2C",
	            	"HTU21",
	             	"AHTx0"
				]
			}            
	    },
	    "ds18b20address2": {
	        "required": "false",
	        "description": "DS18B20 Address",
	        "tab": "Sensor 2",
	        "help": "Filename in /sys/bus/w1/devices",
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
	        "tab": "Sensor 2",            
	        "help": "Your Open Weather Map API key."         ,
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	            "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,DS18B20,OpenWeather",
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
	                "OpenWeather"
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
	            	"BME280-I2C",
	            	"HTU21",
	             	"AHTx0"
				]
			}            
	    },
	    "ds18b20address3": {
	        "required": "false",
	        "description": "DS18B20 Address",
	        "tab": "Sensor 3",
	        "help": "Filename in /sys/bus/w1/devices",
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
	        "tab": "Sensor 3",            
	        "help": "Your Open Weather Map API key."         ,
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
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
	                "DHT22",
	                "DHT11",
	                "AM2302",
	                "BME280-I2C",
	                "HTU21",
	                "AHTx0",
	                "DS18B20",
	                "OpenWeather"
				]
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
					"Added new meta options for better structure in the module manager"
				]
	        }
	    ]                                                          
	}
}

	
def readSHT31(sht31heater, i2caddress):
	temperature = None
	humidity = None

	if i2caddress != "":
		try:
			i2caddressInt = int(i2caddress, 16)
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			s.log(0, f"ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}")
				
	try:
		i2c = board.I2C()
		if i2caddress != "":
			sensor = adafruit_sht31d.SHT31D(i2c, i2caddressInt)
		else:
			sensor = adafruit_sht31d.SHT31D(i2c)
		sensor.heater = sht31heater
		temperature = sensor.temperature
		humidity = sensor.relative_humidity
	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(4, f"ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}")
		return temperature, humidity

	return temperature, humidity


def doDHTXXRead(inputpin):
	temperature = None
	humidity = None

	try:
		pin = s.getGPIOPin(inputpin)
		dhtDevice = adafruit_dht.DHT22(pin, use_pulseio=False)
		try:
			temperature = dhtDevice.temperature
			humidity = dhtDevice.humidity
		except RuntimeError as e:
			eType, eObject, eTraceback = sys.exc_info()
			s.log(4, f"ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")
	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(4, f"WARNING: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")

	return temperature, humidity


def readDHT22(inputpin, dhtxxretrycount, dhtxxdelay):
	temperature = None
	humidity = None
	count = 0
	reading = True

	while reading:
		temperature, humidity = doDHTXXRead(inputpin)

		if temperature is None and humidity is None:
			s.log(4, "WARNING: Failed to read DHTXX on attempt {}".format(count+1))
			count = count + 1
			if count > dhtxxretrycount:
				reading = False
			else:
				time.sleep(dhtxxdelay/1000)
		else:
			reading = False

	return temperature, humidity


def readBme280I2C(i2caddress):
	temperature = None
	humidity = None
	pressure = None
	relHumidity = None
	altitude = None

	if i2caddress != "":
		try:
			i2caddressInt = int(i2caddress, 16)
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

	try:
		i2c = board.I2C()
		if i2caddress != "":
			bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, i2caddressInt)
		else:
			bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

		temperature =  bme280.temperature
		humidity = bme280.humidity
		relHumidity = bme280.relative_humidity
		altitude = bme280.altitude
		pressure = bme280.pressure
	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

	return temperature, humidity, pressure, relHumidity, altitude


def readHtu21(i2caddress):
	temperature = None
	humidity = None

	if i2caddress != "":
		try:
			i2caddressInt = int(i2caddress, 16)
		except:
			result = "Address {} is not a valid i2c address".format(i2caddress)
			s.log(0,"ERROR: {}".format(result))

	try:
		i2c = board.I2C()
		if i2caddress != "":
			htu21 = HTU21D(i2c, i2caddressInt)
		else:
			htu21 = HTU21D(i2c)

		temperature =  htu21.temperature
		humidity = htu21.relative_humidity
	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(4, f"ERROR: Module readHtu21 failed on line {eTraceback.tb_lineno} - {e}")
		
	return temperature, humidity


def readAHTX0(i2caddress):
	temperature = None
	humidity = None

	if i2caddress != "":
		try:
			i2caddressInt = int(i2caddress, 16)
		except:
			result = "Address {} is not a valid i2c address".format(i2caddress)
			s.log(0,"ERROR: {}".format(result))

	try:
		i2c = board.I2C()
		sensor = adafruit_ahtx0.AHTx0(i2c)
		temperature = sensor.temperature
		humidity = sensor.relative_humidity
	except ValueError as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(4, f"ERROR: Module readAHTX0 failed on line {eTraceback.tb_lineno} - {e}")

	return temperature, humidity


def readDS18B20(address):
	humidity = None
	temperature = None

	one_wire_base_dir = Path('/sys/bus/w1/devices/')
	one_wire_sensor_dir = Path(os.path.join(one_wire_base_dir, address))

	if one_wire_base_dir.is_dir():
		if one_wire_sensor_dir.is_dir():
			try:
				device = DS18B20(address)
				temperature = device.read_temperature()
			# pylint: disable=broad-exception-caught
			except Exception as ex:
				_, _, trace_back = sys.exc_info()
				s.log(4, f"ERROR: Module readDS18B20 failed on line {trace_back.tb_lineno} - {ex}")
		else:
			s.log(4, f'ERROR: (readDS18B20) - "{address}" is not a valid DS18B20 address. Please check /sys/bus/w1/devices')
	else:
		s.log(4, 'ERROR: (readDS18B20) - One Wire is not enabled. Please use the raspi-config utility to enable it')

	return temperature, humidity


def getOWValue(field, jsonData, fileModifiedTime):
	result = False    

	if field in jsonData:
		result = jsonData[field]["value"]

	if "expires" in jsonData[field]:
		maxAge = jsonData[field]["expires"]
		age = int(time.time()) - fileModifiedTime
		if age > maxAge:
			s.log(4, f"WARNING: field {field} has expired - age is {age}")
			result = None
			
	return result

	                
def getOWValues(fileName):
	temperature = None
	humidity = None
	pressure = None
	dewPoint = None

	allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
	extraDataFileName = os.path.join(allskyPath, "config", "overlay", "extra", fileName)

	if os.path.isfile(extraDataFileName):
		fileModifiedTime = int(os.path.getmtime(extraDataFileName))
		with open(extraDataFileName,"r") as file:
			jsonData = json.load(file)
			temperature = getOWValue("AS_OWTEMP", jsonData, fileModifiedTime)
			humidity = getOWValue("AS_OWHUMIDITY", jsonData, fileModifiedTime)
			pressure = getOWValue("AS_OWPRESSURE", jsonData, fileModifiedTime)
			dewPoint = getOWValue("AS_OWDEWPOINT", jsonData, fileModifiedTime)

	return temperature, humidity, pressure, dewPoint

def createCardinal(degrees):
	try:
		cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
		cardinal = cardinals[round(degrees / 22.5)]
	except Exception:
		cardinal = 'N/A'

	return cardinal

def processResult(data, expires, units):
	extraData = {}
	#rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
	#data = json.loads(rawData)
	setExtraValue("weather.main", data, "OWWEATHER", expires, extraData)
	setExtraValue("weather.description", data, "OWWEATHERDESCRIPTION", expires, extraData)

	setExtraValue("main.temp", data, "OWTEMP", expires, extraData)
	setExtraValue("main.feels_like", data, "OWTEMPFEELSLIKE", expires, extraData)
	setExtraValue("main.temp_min", data, "OWTEMPMIN", expires, extraData)
	setExtraValue("main.temp_max", data, "OWTEMPMAX", expires, extraData)
	setExtraValue("main.pressure", data, "OWPRESSURE", expires, extraData)
	setExtraValue("main.humidity", data, "OWHUMIDITY", expires, extraData)

	setExtraValue("wind.speed", data, "OWWINDSPEED", expires, extraData)
	setExtraValue("wind.deg", data, "OWWINDDIRECTION", expires, extraData)
	setExtraValue("wind.gust", data, "OWWINDGUST", expires, extraData)

	setExtraValue("clouds.all", data, "OWCLOUDS", expires, extraData)

	setExtraValue("rain.1hr", data, "OWRAIN1HR", expires, extraData)
	setExtraValue("rain.3hr", data, "OWRAIN3HR", expires, extraData)

	setExtraValue("sys.sunrise", data, "OWSUNRISE", expires, extraData)
	setExtraValue("sys.sunset", data, "OWSUNSET", expires, extraData)

	temperature = float(getValue("main.temp", data))
	humidity = float(getValue("main.humidity", data))
	if units == "imperial":
		t = Temp(temperature, 'f')
		dewPoint = dew_point(t, humidity).f
		heatIndex = heat_index(t, humidity).f

	if units == "metric":
		t = Temp(temperature, 'c')        
		dewPoint = dew_point(temperature, humidity).c
		heatIndex = heat_index(temperature, humidity).c

	if units == "standard":
		t = Temp(temperature, 'k')        
		dewPoint = dew_point(temperature, humidity).k
		heatIndex = heat_index(temperature, humidity).k

	degress = getValue('wind.deg', data)
	cardinal = createCardinal(degress)

	extraData["AS_OWWINDCARDINAL"] = {
		"value": cardinal,
		"expires": expires
	}
	            
	extraData["AS_OWDEWPOINT"] = {
	    "value": round(dewPoint,1),
	    "expires": expires
	}
	    
	extraData["AS_OWHEATINDEX"] = {
	    "value": round(heatIndex,1),
	    "expires": expires
	}
	
	return extraData


def setExtraValue(path, data, extraKey, expires, extraData):
	value = getValue(path, data)
	if value is not None:
	    extraData["AS_" + extraKey] = {
	        "value": value,
	        "expires": expires
	    }


def getValue(path, data):
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


def readOpenWeather(params):
	expire = int(params["expire"])
	period = int(params["period"])
	apikey = params["apikey"]
	fileName = params["filename"]
	module = metaData["module"]
	units = params["units"]
	temperature = None
	humidity = None
	pressure = None
	dewPoint = None

	try:
		shouldRun, diff = s.shouldRun(module, period)
		if shouldRun:
			if apikey != "":
				if fileName != "":
					lat = s.getSetting("latitude")
					if lat is not None and lat != "":
						lat = s.convertLatLon(lat)
						lon = s.getSetting("longitude")
						if lon is not None and lon != "":
							lon = s.convertLatLon(lon)
							try:
								resultURL = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&units={2}&appid={3}".format(lat, lon, units, apikey)
								s.log(4,f"INFO: Reading Openweather API from - {resultURL}")
								response = requests.get(resultURL)
								if response.status_code == 200:
									rawData = response.json()
									extraData = processResult(rawData, expire, units)
									s.saveExtraData(fileName, extraData )
									result = f"Data acquired and written to extra data file {fileName}"
									s.log(1,f"INFO: {result}")
								else:
									result = f"Got error from Open Weather Map API. Response code {response.status_code}"
									s.log(0,f"ERROR: {result}")
							except Exception as e:
								result = str(e)
								s.log(0, f"ERROR: {result}")
							s.setLastRun(module)                            
						else:
							result = "Invalid Longitude. Check the Allsky configuration"
							s.log(0,f"ERROR: {result}")
					else:
						result = "Invalid Latitude. Check the Allsky configuration"
						s.log(0,f"ERROR: {result}")
				else:
					result = "Missing filename for data"
					s.log(0,f"ERROR: {result}")
			else:
				result = "Missing Open Weather Map API key"
				s.log(0,f"ERROR: {result}")
		else:
			s.log(4,f"INFO: Using Cached Openweather API data")

		temperature, humidity, pressure, dewPoint = getOWValues(fileName)                
	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		s.log(0, f"ERROR: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}")   

	return temperature, humidity, pressure, dewPoint


def getSensorReading(sensorType, inputpin, i2caddress, ds18b20address, dhtxxretrycount, dhtxxdelay, sht31heater, params):
	temperature = None
	humidity = None
	dewPoint = None
	heatIndex = None
	pressure = None
	relHumidity = None
	altitude = None

	if sensorType == "SHT31":
		temperature, humidity = readSHT31(sht31heater, i2caddress)
	elif sensorType == "DHT22" or sensorType == "DHT11" or sensorType == "AM2302":
		temperature, humidity = readDHT22(inputpin, dhtxxretrycount, dhtxxdelay)
	elif sensorType == "BME280-I2C":
		temperature, humidity, pressure, relHumidity, altitude = readBme280I2C(i2caddress)
	elif sensorType == "HTU21":
		temperature, humidity = readHtu21(i2caddress)
	elif sensorType == "AHTx0":
		temperature, humidity = readAHTX0(i2caddress)
	elif sensorType == "DS18B20":
		temperature, humidity = readDS18B20(ds18b20address)
	elif sensorType == "OpenWeather":
		temperature, humidity, pressure, dewPoint = readOpenWeather(params)        
	else:
		s.log(0,"ERROR: No sensor type defined")

	tempUnits = s.getSetting("temptype")
	if temperature is not None and humidity is not None:
		dewPoint = dew_point(temperature, humidity).c
		heatIndex = heat_index(temperature, humidity).c
		if tempUnits == 'F':
			temperature = (temperature * (9/5)) + 32
			dewPoint = (dewPoint * (9/5)) + 32
			heatIndex = (heatIndex * (9/5)) + 32
			s.log(4,"INFO: Converted temperature to F")

		temperature = round(temperature, 2)
		humidity = round(humidity, 2)
		dewPoint = round(dewPoint, 2)
		heatIndex = round(heatIndex, 2)
	else:
		if temperature is not None:
			if tempUnits == 'F':
				temperature = (temperature * (9/5)) + 32
				s.log(4,"INFO: Converted temperature ONLY to F")
				
	return temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude


def debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude):
	s.log(4,f"INFO: Sensor {sensorType} read. Temperature {temperature} Humidity {humidity} Relative Humidity {relHumidity} Dew Point {dewPoint} Heat Index {heatIndex} Pressure {pressure} Altitude {altitude}")

	
def temp(params, event):
	result = ""
	extraData = {}
	extradatafilename = params['extradatafilename']
	frequency = int(params["frequency"])
	shouldRun, diff = s.shouldRun('allskytemp', frequency)    

	try:
		debugMode = params["ALLSKYTESTMODE"]
	except ValueError:
		debugMode = False
					
	if shouldRun or debugMode:
		now = int(time.time())
		s.dbUpdate("allskytemp", now)                
		for sensorNumberItr in range(1,5):
			if sensorNumberItr == 1:
				sensorNumber = ""
			else:
				sensorNumber = sensorNumberItr - 1
				
			sensorType = params["type" + str(sensorNumber)]

			if sensorType != 'None':
				s.log(4,f"INFO: Reading sensor {sensorNumber}, {sensorType}")
				try:
					inputpin = int(params["inputpin" + str(sensorNumber)])
				except ValueError:
					inputpin = 0
				
				i2caddress = params["i2caddress" + str(sensorNumber)]
				dhtxxretrycount = int(params["dhtxxretrycount" + str(sensorNumber)])
				dhtxxdelay = int(params["dhtxxdelay" + str(sensorNumber)])
				sht31heater = params["sht31heater" + str(sensorNumber)]
				ds18b20address = params["ds18b20address" + str(sensorNumber)]
				name = params["name" + str(sensorNumber)]

				maxTempKey = "temp" + str(sensorNumber)
				maxTemp = -1
				if maxTempKey in params:
					try:
						maxTemp = int(params[maxTempKey])
					except ValueError:
						maxTemp = -1
				
				gpioKey =  "gpio" + str(sensorNumber)
				gpioPin = -1 
				if gpioKey in params:                                 
					try:
						gpioPin = int(params[gpioKey])
					except ValueError:
						gpioPin = -1                    
		
				temperature = 0
				humidity = 0
				dewPoint = 0
				heatIndex = 0

				temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude = getSensorReading(sensorType, inputpin, i2caddress, ds18b20address, dhtxxretrycount, dhtxxdelay, sht31heater, params)
				if temperature is not None:
					temperature = round(temperature, 2)
				if humidity is not None:
					humidity = round(humidity, 2)
				if dewPoint is not None:
					dewPoint = round(dewPoint, 2)
				if heatIndex is not None:
					heatIndex = round(heatIndex, 2)
				if pressure is not None:
					pressure = round(pressure, 0)
				if relHumidity is not None:
					relHumidity = round(relHumidity, 2)
				if altitude is not None:
					altitude = round(altitude, 0)
				debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude)

				if sensorNumber != '':
					gpioValue = False
					if temperature is not None and sensorNumber != "": 
						if maxTemp != -1 and gpioPin != -1:
							try:
								gpio = s.getGPIOPin(gpioPin)
								pin = DigitalInOut(gpio)
								pin.switch_to_output()                   
								if temperature > maxTemp:
									gpioValue = True
					
									s.log(4, f'INFO: Temperature {temperature} is greater than {maxTemp} so enabling GPIO {gpioPin}')
									pin.value = 1
								else:
									gpioValue = False
									s.log(4, f'INFO: Temperature {temperature} is less than {maxTemp} so disabling GPIO {gpioPin}')
									pin.value = 0
							except Exception as e:    
								eType, eObject, eTraceback = sys.exc_info()
								result = f"ERROR: Failed to set Digital IO to output {eTraceback.tb_lineno} - {e}"
								s.log(0, result)
							
				if temperature is not None:
					if sensorNumber != '':
						extraData["AS_GPIOSTATE" + str(sensorNumber)] = gpioValue
					extraData["AS_TEMPSENSOR" + str(sensorNumber)] = str(sensorType)
					extraData["AS_TEMPSENSORNAME" + str(sensorNumber)] = name
					extraData["AS_TEMP" + str(sensorNumber)] = str(temperature)
					extraData["AS_DEW" + str(sensorNumber)] = str(dewPoint)
					extraData["AS_HUMIDITY" + str(sensorNumber)] = str(humidity)
					if pressure is not None:
						extraData["AS_PRESSURE" + str(sensorNumber)] = pressure
					if relHumidity is not None:
						extraData["AS_RELHUMIDITY" + str(sensorNumber)] = relHumidity
					if altitude is not None:
						extraData["AS_ALTITUDE" + str(sensorNumber)] = altitude

		s.saveExtraData(extradatafilename, extraData, metaData["module"], metaData["extradata"])

	else:
		result = 'Will run in {:.2f} seconds'.format(frequency - diff)
		s.log(1,"INFO: {}".format(result))

	return result


def temp_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskytemp.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)