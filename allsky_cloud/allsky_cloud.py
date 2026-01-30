'''
allsky_cloud.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
import math
import board
import adafruit_mlx90614

class ALLSKYCLOUD(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Determine Cloud Cover",
		"description": "Determine the cloud cover using an MLX90614",
		"module": "allsky_cloud",
		"version": "v1.0.2",
		"testable": "true",
		"centersettings": "false",
		"extradatafilename": "allsky_cloud.json",
		"group": "Image Analysis",
		"deprecation": {
			"fromversion": "v2024.12.06_02",
			"removein": "v2024.12.06_04",
			"notes": "This module is deprecated due to its unreliable nature. If you wish to take over the maintenance of this module please contact the Allsky team.",
			"replacedby": "None"
		},
		"events": [
			"night",
			"day",
			"periodic"
		],
		"experimental": "true",
		"extradata": {
			"values": {
				"AS_CLOUDAMBIENT": {
					"name": "${CLOUDAMBIENT}",
					"format": "",
					"sample": "",                
					"group": "Cloud",
					"description": "Ambient Temperature",
					"type": "number"
				},              
				"AS_CLOUDSKY": {
					"name": "${CLOUDSKY}",
					"format": "",
					"sample": "",                 
					"group": "Cloud",
					"description": "Sky Temperature",
					"type": "number"
				},
				"AS_CLOUDCOVER": {
					"name": "${CLOUDCOVER}",
					"format": "",
					"sample": "",                 
					"group": "Cloud",
					"description": "Cloud cover",
					"type": "string"
				},
				"AS_CLOUDCOVERPERCENT": {
					"name": "${CLOUDCOVERPERCENT}",
					"format": "",
					"sample": "",                 
					"group": "Cloud",
					"description": "Cloud cover percentage",
					"type": "number"
				}
			}                         
		},     
		"arguments":{
			"i2caddress": "",
			"clearbelow": -10,
			"cloudyabove": 5,
			"advanced": "false",
			"k1": 33,
			"k2": 0,
			"k3": 4,
			"k4": 100,
			"k5": 100,
			"k6": 0,
			"k7": 0
		},
		"argumentdetails": {                   
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "i2c"
				}         
			},
			"clearbelow" : {
				"required": "false",
				"description": "Clear Below &deg;C",
				"help": "When the sky temperature is below this value the sky is assumed to be clear.",
				"tab": "Settings",            
				"type": {
					"fieldtype": "spinner",
					"min": -60,
					"max": 10,
					"step": 1
				}          
			},
			"cloudyabove" : {
				"required": "false",
				"description": "Cloudy Above &deg;C",
				"help": "When the sky temperature is above this value the sky is assumed to be cloudy.",
				"tab": "Settings",            
				"type": {
					"fieldtype": "spinner",
					"min": -60,
					"max": 100,
					"step": 1
				}          
			},       
			"advanced" : {
				"required": "false",
				"description": "Use advanced mode",
				"help": "Provides a polynomial adjustment for the sky temperature.",
				"tab": "Advanced",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"k1" : {
				"required": "false",
				"description": "k1",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k2" : {
				"required": "false",
				"description": "k2",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k3" : {
				"required": "false",
				"description": "k3",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k4" : {
				"required": "false",
				"description": "k4",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k5" : {
				"required": "false",
				"description": "k5",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k6" : {
				"required": "false",
				"description": "k6",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
				}          
			},
			"k7" : {
				"required": "false",
				"description": "k7",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 1
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
						"Added module to periodic flow",
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
						"Updated for new module system",
						"Added deprecation"
					]
				}
			]                                
		}                  
	}
 
	def __get_sign(self, d):
		if d < 0:
			return -1.0
		if d == 0:
			return 0.0
		return 1.0

	def __calculate_sky_state_advanced(self, sky_ambient, sky_object, clear_below, cloudy_above):
		k1 = self.get_param('k1', 0, int)  
		k2 = self.get_param('k2', 0, int)  
		k3 = self.get_param('k3', 0, int)  
		k4 = self.get_param('k4', 0, int)  
		k5 = self.get_param('k5', 0, int)  
		k6 = self.get_param('k6', 0, int)  
		k7 = self.get_param('k7', 0, int)  
  
		if abs((k2 / 10.0 - sky_ambient)) < 1:
			t67 = self.__get_sign(k6) * self.__get_sign(sky_ambient - k2 / 10.) * abs((k2 / 10. - sky_ambient))
		else:
			t67 = k6 / 10. * self.__get_sign(sky_ambient - k2 / 10.) * (math.log(abs((k2 / 10. - sky_ambient))) / math.log(10) + k7 / 100)

		td = (k1 / 100.) * (sky_ambient - k2 / 10.) + (k3 / 100.) * pow((math.exp(k4 / 1000. * sky_ambient)), (k5 / 100.)) + t67

		tsky = sky_object - td
		if tsky < clear_below:
			tsky = clear_below
		elif tsky > cloudy_above:
			tsky = cloudy_above
		cloudcoverPercentage = ((tsky - clear_below) * 100.) / (cloudy_above - clear_below)
		cloudcover, percent = self._calculate_sky_state(sky_ambient, sky_object, clear_below, cloudy_above)
		return cloudcover, cloudcoverPercentage

	def __calculate_sky_state(self, sky_ambient, sky_object, clear_below, cloudy_above):
		cloudCover = 'Partial'

		if sky_object <= clear_below:
			cloudCover = 'Clear'

		if sky_object >= cloudy_above:
			cloudCover = 'Cloudy'

		return cloudCover, 0

	def run(self):
		advanced = self.get_param('advanced', False, bool)
		i2c_address = self.get_param('i2caddress', '', str)
		clear_below = self.get_param('clearbelow', 0, int)
		cloudy_above = self.get_param('cloudyabove', 0, int)

		extra_data = {}

		try:    
			if i2c_address != '':
				try:
					i2c_address_int = int(i2c_address, 16)
				except:
					result = f'Address {i2c_address} is not a valid i2c address'
					self.log(0, f'ERROR in {__file__}: {result}')

			i2c = board.I2C()
			if i2c_address != '':
				mlx = adafruit_mlx90614.MLX90614(i2c, i2c_address_int)
			else:
				mlx = adafruit_mlx90614.MLX90614(i2c)

			sky_ambient = mlx.ambient_temperature
			sky_object = mlx.object_temperature

			if advanced:
				cloud_cover, percentage = self.__calculate_sky_state_advanced(sky_ambient, sky_object, clear_below, cloudy_above)
			else:
				cloud_cover, percentage = self.__calculate_sky_state(sky_ambient, sky_object, clear_below, cloudy_above)

			extra_data['AS_CLOUDAMBIENT'] = sky_ambient
			extra_data['AS_CLOUDSKY'] = sky_object
			extra_data['AS_CLOUDCOVER'] = cloud_cover
			extra_data['AS_CLOUDCOVERPERCENT'] = percentage
			allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)

			result = f'Cloud state - {cloud_cover} {percentage}%. Sky Temp {sky_object}, Ambient {sky_ambient}'
			self.log(1, f'INFO: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'Module cloud failed on line {eTraceback.tb_lineno} - {e}'
			self.log(4, f'ERROR in {__file__}: {result}')
			
		return result 

def cloud(params, event):
	allsky_cloud = ALLSKYCLOUD(params, event)
	result = allsky_cloud.run()

	return result

def cloud_cleanup():
	moduleData = {
	    "metaData": ALLSKYCLOUD.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYCLOUD.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
