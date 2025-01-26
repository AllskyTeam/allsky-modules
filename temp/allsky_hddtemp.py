'''
allsky_hddtemp.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as allsky_shared
from pySMART import SMARTCTL, DeviceList
import sys

metaData = {
	"name": "HDD Temp",
	"description": "Provides HDD Temps",
	"module": "allsky_hddtemp",
	"version": "v1.0.1",
	"events": [
	    "night",
	    "day",
	    "periodic"
	],
	"experimental": "true",
	"centersettings": "false",
	"testable": "true",    
	"extradata": {
	    "info": {
	        "count": 4,
	        "firstblank": "true"
	    },
	    "values": {
	        "AS_HDDSDATEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sda in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDATEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sda in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDBTEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sdb in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDBTEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sdb in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDCTEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sdc in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDCTEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sdc in C",
	            "type": "temperature"
	        }
	    }
	},
	"arguments": {
	    "usecolour": "False",
	    "oktemp": 30,
	    "okcolour": "green",
	    "badcolour": "red"
	},
	"argumentdetails": {
	    "hddnotice": {
	        "message": "<strong>NOTE</strong> S.M.A.R.T temperatures are always returned in degrees Celsius, use the overlay manager to reformat to another temperature unit if required",
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
	    "usecolour": {
	        "required": "false",
	        "description": "Use Colour",
	        "help": "Use colour for temperature fields",
	        "type": {
	            "fieldtype": "checkbox"
	        }          
	    },
	    "oktemp": {
	        "required": "true",
	        "description": "Ok Temp",
	        "help": "At or below this temperature hdd temp is ok",                
	        "type": {
	            "fieldtype": "spinner",
	            "min": 1,
	            "max": 100,
	            "step": 1
	        }
	    },
	    "okcolour": {
	        "required": "true",
	        "description": "Ok Colour",
	        "help": "Colour for an Ok temeprature",
	        "type": {
	            "fieldtype": "colour"             
			}                 
	    },
	    "badcolour": {
	        "required": "true",
	        "description": "Bad Colour",
	        "help": "Colour for a Bad temeprature",
	        "type": {
	            "fieldtype": "colour"             
			}       
	    }
	},
	"enabled": "false",
	"changelog": {
	    "v1.0.0": [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Initial Release"
	        }
	    ],
	    "v1.0.1": [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": [
	                "Add exception handling",
	                "Converted to new format"
	            ]
	        }
	    ]
	}
}


class ALLSKYHDDTEMP:
	__params = []
	__event = ''
	__use_colour = False
	__ok_temp = 0
	__ok_colour = '#00ff00'
	__bad_colour = '#ff0000'
	__debugmode = False
 
	def __init__(self, params, event):
		self.__params = params
		self.__event = event

	def __get_device_list(self):
		device_list = None
		try:
			SMARTCTL.sudo = True
			device_list = DeviceList()
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module __get_device_list - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')
   
		return device_list
     
	def run(self):
		extra_data = {}
		result = ''
		self.__use_colour = allsky_shared.get_param('usecolour', self.__params, False, bool)
		self.__ok_temp = allsky_shared.get_param('oktemp', self.__params, 0, int)  
		self.__ok_colour = allsky_shared.get_param('okcolour', self.__params, '#00ff00', str)  
		self.__bad_colour = allsky_shared.get_param('badcolour', self.__params, '#ff0000', str)  
		self.__debugmode = allsky_shared.get_param('ALLSKYTESTMODE', self.__params, False, bool)  

		device_list = self.__get_device_list()
		if device_list is not None:
			if len(device_list.devices) > 0:
				for dev in device_list:
					name = dev.name.upper()
					temp_data = dev.attributes[194]
					if temp_data is not None:
						temp = temp_data.raw_int
						temp_max = temp_data.worst

						if temp is not None:
							hdd_name = f'AS_HDD{name}TEMP'
							if self.__use_colour:
								colour = self.__ok_colour if temp <= self.__ok_temp else self.__bad_colour
								extra_data[hdd_name] = {
									'value': str(temp),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}C, using colour ({colour}), max is {self.__ok_temp}C')
							else:
								extra_data[hdd_name] = str(temp)
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}')
						else:
							result = f'No temperature data available for {name}'
							allsky_shared.log(4, f'ERROR: {result}')

						if temp_max is not None:
							hdd_name = f'AS_HDD{name}TEMPMAX'
							if self.__use_colour:
								colour = self.__ok_colour if temp_max <= self.__ok_temp else self.__bad_colour
								extra_data[hdd_name] = {
									'value': str(temp_max),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Max temperature of {name} is {temp_max}C, using colour ({colour}), max is {self.__ok_temp}C')
							else:
								extra_data[hdd_name] = str(temp_max)
								allsky_shared.log(4, f'INFO: Max temperature of {name} is {temp}')
						else:
							result1 = f'No max temperature data available for {name}'
							allsky_shared.log(4, f"ERROR: {result1}")

							if result != '':
								result = f'{result}, {result1}'
							else:
								result = result1

						if result == '':
							result = f'Ok Current: {temp}, Max: {temp_max}'

						if self.__debugmode:
							allsky_shared.log(4, result)
							
						allsky_shared.saveExtraData('allskyhddtemp.json', extra_data, metaData['module'], metaData['extradata'])

					else:
						allsky_shared.log(4, f'ERROR: No temperature data (S.M.A.R.T 194) available for {name}')
			else:
				allsky_shared.deleteExtraData('allskyhddtemp.json')
				result = 'No S.M.A.R.T devices found'

def hddtemp(params, event):
	allsky_hddtemp = ALLSKYHDDTEMP(params, event)
	result = allsky_hddtemp.run()

	return result        
    
def hddtemp_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskyhddtemp.json"
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)