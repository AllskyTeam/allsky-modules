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
	"extradatafilename": "allsky_hddtemp.json",   
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
	_params = []
	_event = ''
	_use_colour = False
	_ok_temp = 0
	_ok_colour = '#00ff00'
	_bad_colour = '#ff0000'
	_debugmode = False
 
	def _init_(self, params, event):
		self._params = params
		self._event = event

	def _get_device_list(self):
		device_list = None
		try:
			SMARTCTL.sudo = True
			device_list = DeviceList()
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module _get_device_list - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')
   
		return device_list
     
	def run(self):
		extra_data = {}
		result = ''
		self._use_colour = allsky_shared.get_param('usecolour', self._params, False, bool)
		self._ok_temp = allsky_shared.get_param('oktemp', self._params, 0, int)  
		self._ok_colour = allsky_shared.get_param('okcolour', self._params, '#00ff00', str)  
		self._bad_colour = allsky_shared.get_param('badcolour', self._params, '#ff0000', str)  
		self._debugmode = allsky_shared.get_param('ALLSKYTESTMODE', self._params, False, bool)  

		device_list = self._get_device_list()
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
							if self._use_colour:
								colour = self._ok_colour if temp <= self._ok_temp else self._bad_colour
								extra_data[hdd_name] = {
									'value': str(temp),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}C, using colour ({colour}), max is {self._ok_temp}C')
							else:
								extra_data[hdd_name] = str(temp)
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}')
						else:
							result = f'No temperature data available for {name}'
							allsky_shared.log(4, f'ERROR: {result}')

						if temp_max is not None:
							hdd_name = f'AS_HDD{name}TEMPMAX'
							if self._use_colour:
								colour = self._ok_colour if temp_max <= self._ok_temp else self._bad_colour
								extra_data[hdd_name] = {
									'value': str(temp_max),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Max temperature of {name} is {temp_max}C, using colour ({colour}), max is {self._ok_temp}C')
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

						if self._debugmode:
							allsky_shared.log(4, result)
							
						allsky_shared.saveExtraData(metaData['extradatafilename'], extra_data, metaData['module'], metaData['extradata'])

					else:
						allsky_shared.log(4, f'ERROR: No temperature data (S.M.A.R.T 194) available for {name}')
			else:
				allsky_shared.deleteExtraData(metaData['extradatafilename'])
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
	            metaData['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)