'''
allsky_light.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
import math
import board
import busio
import adafruit_tsl2591
import adafruit_tsl2561

class ALLSKYLIGHT(ALLSKYMODULEBASE):

	meta_data = {
		"name": "AllSky Light Meter",
		"description": "Estimates sky brightness",
		"module": "allsky_light",
		"version": "v1.0.3",
		"centersettings": "false",
		"testable": "true",    
		"events": [
			"day",
			"night",
			"periodic"
		],
		"experimental": "false",
		"extradatafilename": "allsky_light.json",  
		"extradata": {
			"values": {
				"AS_LIGHTLUX": {
					"name": "${LIGHTLUX}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Lux level",
					"type": "Number"
				},
				"AS_LIGHTBORTLE": {
					"name": "${LIGHTBORTLE}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Approximate Bortle level",
					"type": "Number"
				}           
			}                         
		},  
		"arguments":{
			"type": "",
			"i2caddress": "",
			"tsl2591gain": "25x",
			"tsl2591integration": "100ms",
			"tsl2561gain": "Low",
			"tsl2561integration": "0"
		},
		"argumentdetails": {
			"type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor",         
				"type": {
					"fieldtype": "select",
					"values": "None,TSL2591,TSL2561",
					"default": "None"
				}                
			},        
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"tab": "Sensor",         
				"help": "Override the standard i2c address for the sensor. NOTE: This value must be hex i.e. 0x76",
				"type": {
					"fieldtype": "i2c"
				}         
			},
			"tsl2591gain" : {
				"required": "false",
				"description": "TSL2591 Gain",
				"help": "The gain for the TSL2591 sensor.",
				"tab": "Sensor",         
				"type": {
					"fieldtype": "select",
					"values": "Low,Med,High,Max",
					"default": "Low"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"TSL2591"
					]
				}                       
			},
			"tsl2591integration" : {
				"required": "false",
				"description": "TSL2591 Integration time",
				"help": "The integration time for the TSL2591 sensor.",
				"tab": "Sensor",         
				"type": {
					"fieldtype": "select",
					"values": "100ms,200ms,300ms,400ms,500ms,600ms",
					"default": "100ms"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"TSL2591"
					]
				}                
			},
			"tsl2561gain" : {
				"required": "false",
				"description": "TSL2561 Gain",
				"help": "The gain for the TSL2561 sensor.",
				"tab": "Sensor",         
				"type": {
					"fieldtype": "select",
					"values": "0|Low,1|High",
					"default": "Low"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"TSL2561"
					]
				}                
			},
			"tsl2561integration" : {
				"required": "false",
				"description": "TSL2561 Integration time",
				"help": "The integration time for the TSL2561 sensor.",
				"tab": "Sensor",         
				"type": {
					"fieldtype": "select",
					"values": "0|13.7ms,1|101ms,2|402ms",
					"default": "0"
				},
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"TSL2561"
					]
				}                
			}                                                                                           
		},
		"enabled": "false",
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
					"changes": [
						"Added extra error handling",
						"Added ability to change the extra data filename",
						"Added changelog to metadata"
					]
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Fixed error where i2c address was not passed to python modules",
						"Added additional error handling"
					]
				}
			],
			"v1.0.3" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Refactored for new module system",
						"Changed formulae for lux to sqm"
					]
				}
			]                                               
		}           
	}
 
	def __read_TSL2591(self):
		sensor = None
		i2c = board.I2C()
		i2c_address = self.get_param('i2caddress', '', str, True)
		if i2c_address != '':
			try:
				i2caddress_int = int(i2c_address, 16)
				sensor = adafruit_tsl2591.TSL2591(i2c, i2caddress_int)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module readTSL2591 failed on line {eTraceback.tb_lineno} - {e}')
		else: 
			sensor = adafruit_tsl2591.TSL2591(i2c)

		allsky_shared.log(4, f'Using TSL2591 on i2c address {i2c_address}')
			
		lux = None
		infrared = None
		visible = None
						
		if sensor is not None:    
			gain_name = self.get_param('tsl2591gain', 'LOW', str, True).upper()
			gain_variable = f'GAIN_{gain_name}'
			sensor.gain = getattr(adafruit_tsl2591, gain_variable)

			integration_name = self.get_param('tsl2591integration', '100MS', str, True).upper()
			integration_variable = f'INTEGRATIONTIME_{integration_name}'
			sensor.integration_time = getattr(adafruit_tsl2591, integration_variable)

			try:
				lux = sensor.lux
				infrared = sensor.infrared
				visible = sensor.visible

				allsky_shared.log(4, f'TSL2591 read values - lux {lux}, infrared {infrared}, visible {visible}')
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module __read_TSL2591 failed on line {eTraceback.tb_lineno} - {e}')
        
		return lux, infrared, visible

	def __read_TSL2561(self):
		tsl = None
		i2c = busio.I2C(board.SCL, board.SDA)
		
		i2c_address = self.get_param('i2caddress', '', str, True)
		if i2c_address != '':
			try:
				i2caddress_int = int(i2c_address, 16)
				tsl = adafruit_tsl2561.TSL2561(i2c, i2caddress_int)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				allsky_shared.log(0, f'ERROR: Module readTSL2561 failed on line {eTraceback.tb_lineno} - {e}')
		else: 
			tsl = adafruit_tsl2561.TSL2561(i2c)
		
		allsky_shared.log(4, f'Using TSL2561 on i2c address {i2c_address}')
    
		lux = None
		infrared = None
		visible = None
		if tsl is not None:
			gain = self.get_param('tsl2561gain', 0, int, True)
			tsl.gain = gain
			
			integration = self.get_param('tsl2561integration', 0, int, True)
			tsl.integration_time = integration
				
			visible = tsl.broadband
			infrared = tsl.infrared

			lux = tsl.lux
			if lux is None:
				lux = 0

		allsky_shared.log(4, f'TSL2561 read values - lux {lux}, infrared {infrared}, visible {visible}')
   
		return lux, infrared, visible

	def __lux_to_bortle(self, lux):
		if lux <= 0.1:
			return 1  # Excellent dark-sky site
		elif lux <= 0.25:
			return 2  # Good dark-sky site
		elif lux <= 0.5:
			return 3  # Rural sky
		elif lux <= 1.0:
			return 4  # Suburban sky
		elif lux <= 2.0:
			return 5  # Urban sky
		elif lux <= 3.0:
			return 6  # Suburban/urban transition
		elif lux <= 5.0:
			return 7  # Urban sky
		elif lux <= 10.0:
			return 8  # Suburban/urban
		else:
			return 9  # Inner-city sky
    		
	def run(self):
		result = ''
  
		sensor = self.get_param('type', 'none', str, True).lower()
		if sensor != "none":
			if sensor == "tsl2591":
				lux, infrared, visible = self.__read_TSL2591()

			if sensor == "tsl2561":
				lux, infrared, visible = self.__read_TSL2561()
					
			if lux is not None:
				try:
					bortle = self.__lux_to_bortle(lux)
     
					extra_data = {}
					extra_data['AS_LIGHTLUX'] = lux
					extra_data['AS_LIGHTBORTLE'] = bortle
					allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
     
					result = f'Lux {lux}, Bortle {bortle}'
					allsky_shared.log(4, f"INFO: {result}")		
				except Exception as e:
					eType, eObject, eTraceback = sys.exc_info()        
					result = f'Failed to calculate sqm or nelm, lux = {lux}, line {eTraceback.tb_lineno} {e}'
					allsky_shared.log(0, f'ERROR: {result}')
			else:
				allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])
				result = f'Error reading {sensor}'
				allsky_shared.log(0, f'ERROR: {result}')
		else:
			allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])
			result = 'No sensor defined'
			allsky_shared.log(0, f'ERROR: {result}')
			
		return result

def light(params, event):
	allsky_light = ALLSKYLIGHT(params, event)
	result = allsky_light.run()

	return result

def light_cleanup():
	moduleData = {
	    "metaData": ALLSKYLIGHT.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYLIGHT.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)