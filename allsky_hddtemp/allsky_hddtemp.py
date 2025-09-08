'''
allsky_hddtemp.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
from pySMART import SMARTCTL, DeviceList
import sys

class ALLSKYHDDTEMP(ALLSKYMODULEBASE):

	meta_data = {
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
		"group": "Hardware",
        "graphs": {
            "hddtemp": {
				"icon": "fa-solid fa-chart-line",
				"title": "HDD Temp",
				"group": "Hardware",
				"main": "true",
				"config": {
					"chart": {
						"type": "spline",
						"zooming": {
							"type": "x"
						}
					},
					"title": {
						"text": "HDD Temp"
					},
					"plotOptions": {
						"series": {
							"animation": "false"
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
								"text": "Temp"
							} 
						}
					],
					"lang": {
						"noData": "No data available"
					},
					"noData": {
						"style": {
							"fontWeight": "bold",
							"fontSize": "16px",
							"color": "#666"
						}
					}
				},
				"series": {
					"hdda": {
						"name": "sda Temp",
						"yAxis": 0,
						"variable": "AS_HDDSDATEMP"                 
					},
					"hddb": {
						"name": "sdb Temp",
						"yAxis": 0,
						"variable": "AS_HDDSDBTEMP"                 
					},
					"hddc": {
						"name": "sdc Temp",
						"yAxis": 0,
						"variable": "AS_HDDSDCTEMP"                 
					} 
				}
			},
            "guagehdda": {
				"icon": "fa-solid fa-gauge",
				"title": "HDA Temp",
				"group": "Hardware",
				"type": "gauge",
				"config": {
					"chart": {
						"type": "gauge",
						"plotBorderWidth": 0,
						"height": "50%",
						"plotBackgroundColor": "",
						"plotBackgroundImage": ""
					},
					"title": {
						"text": "HDA Temp"
					},
					"pane": {
						"startAngle": -90,
						"endAngle": 89.9,
						"center": ["50%", "75%"],
						"size": "110%",
						"background": ""
					},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
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
					"yAxis": {
						"min": 0,
						"max": 100,
						"tickPixelInterval": 72,
						"tickPosition": "inside",
						"tickColor": "#FFFFFF",
						"tickLength": 20,
						"tickWidth": 2,
						"labels": {
							"distance": 20,
							"style": {
								"fontSize": "14px"
							}
						},
						"lineWidth": 0,
						"plotBands": [{
							"from": 0,
							"to": 70,
							"color": "#55BF3B",
							"thickness": 20
						}, {
							"from": 60,
							"to": 80,
							"color": "#DDDF0D",
							"thickness": 20
						}, {
							"from": 80,
							"to": 100,
							"color": "#DF5353",
							"thickness": 20
						}]
					},
					"series": [{
						"name": "Temperature",
						"data": "AS_HDDSDATEMP",
						"tooltip": {
							"valueSuffix": ""
						},
						"dataLabels": {
							"format": "{y}",
							"borderWidth": 0,
							"color": "#333333",
							"style": {
								"fontSize": "16px"
							}
						},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
					},
						"dial": {
							"radius": "80%",
							"backgroundColor": "gray",
							"baseWidth": 12,
							"baseLength": "0%",
							"rearLength": "0%"
						},
						"pivot": {
							"backgroundColor": "gray",
							"radius": 6
						}

					}]        
				}            
            }
		},   
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_hddtemp",
				"include_all": "true"
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
			},
			"graph": {
				"required": "false",
				"tab": "History",
				"type": {
					"fieldtype": "graph"
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

	_use_colour = False
	_ok_temp = 0
	_ok_colour = '#00ff00'
	_bad_colour = '#ff0000'
 
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
		self._use_colour = self.get_param('usecolour', False, bool)
		self._ok_temp = self.get_param('oktemp', 0, int)
		self._ok_colour = self.get_param('okcolour', '#00ff00', str, True)
		self._bad_colour = self.get_param('badcolour', '#ff0000', str, True)  
   
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
									'value': float(temp),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}C, using colour ({colour}), max is {self._ok_temp}C')
							else:
								extra_data[hdd_name] = float(temp)
								allsky_shared.log(4, f'INFO: Temperature of {name} is {temp}')
						else:
							result = f'No temperature data available for {name}'
							allsky_shared.log(4, f'ERROR: {result}')

						if temp_max is not None:
							hdd_name = f'AS_HDD{name}TEMPMAX'
							if self._use_colour:
								colour = self._ok_colour if temp_max <= self._ok_temp else self._bad_colour
								extra_data[hdd_name] = {
									'value': float(temp_max),
									'fill': colour
								}
								allsky_shared.log(4, f'INFO: Max temperature of {name} is {temp_max}C, using colour ({colour}), max is {self._ok_temp}C')
							else:
								extra_data[hdd_name] = float(temp_max)
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

						if self.debug_mode:
							allsky_shared.log(4, result)
							
						allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])

					else:
						allsky_shared.log(4, f'ERROR: No temperature data (S.M.A.R.T 194) available for {name}')
			else:
				allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])
				result = 'No S.M.A.R.T devices found'

def hddtemp(params, event):
	allsky_hddtemp = ALLSKYHDDTEMP(params, event)
	result = allsky_hddtemp.run()

	return result        
    
def hddtemp_cleanup():
	moduleData = {
	    "metaData": ALLSKYHDDTEMP.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYHDDTEMP.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)