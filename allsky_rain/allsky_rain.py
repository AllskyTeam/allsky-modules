'''
allsky_rain.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will interface to a digital rain detector

Expected parameters:
None
'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys 

class ALLSKYRAIN(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Rain detection",
		"description": "Detects rain via an external digital sensor",
		"module": "allsky_rain",
		"centersettings": "false",
		"testable": "true", 
		"version": "v1.0.1", 
		"group": "Data Sensor",     
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradatafilename": "allsky_rain.json",
        "graphs": {
			"chart1": {
				"icon": "fas fa-chart-line",
				"title": "Rain State",
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
						"text": "Rain State"
					},
					"xAxis": {
						"type": "datetime",
						"dateTimeLabelFormats": {
							"day": "%Y-%m-%d",
							"hour": "%H:%M"
						}
					},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
					},
					"yAxis": [
						{ 
							"title": {
								"text": "Raining"
							} 
						}
					]
				},
				"series": {
					"rain": {
						"name": "Rain State",
						"yAxis": 0,
						"variable": "AS_ALLSKYRAINFLAGINT"                 
					}           
				}
			}
		},
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_rain",
				"include_all": "true"    
			},
			"values": {
				"AS_RAINSTATE": {
					"name": "${RAINSTATE}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Rain state human readable",
					"type": "string"
				},
				"AS_ALLSKYRAINFLAG": {
					"name": "${ALLSKYRAINFLAG}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Rain state boolean",
					"type": "bool"
				},
				"AS_ALLSKYRAINFLAGINT": {
					"name": "${ALLSKYRAINFLAGINT}",
					"format": "",
					"sample": "",                
					"group": "Environment",
					"description": "Rain state integer",
					"type": "number"
				}
			}                         
		},
		"arguments":{
			"inputpin": "",
			"invertsensor": "false"
		},
		"argumentdetails": {
			"inputpin": {
				"required": "true",
				"description": "Input Pin",
				"help": "The input pin for the digital rain sensor",
				"type": {
					"fieldtype": "gpio"
				}           
			},
			"invertsensor" : {
				"required": "false",
				"description": "Invert Sensor",
				"help": "Normally the sensor will be high for clear and low for rain. This settign will reverse this",
				"type": {
					"fieldtype": "checkbox"
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
					"changes": "Refactored for new module and variable system"
				}
			]                                    
		}         
	}

	def run(self):
		try:
			result = ''

			input_pin = self.get_param('inputpin', 0, int)
			invert_sensor = self.get_param('invertsensor', False, bool)
		
			if input_pin != 0:
				try:
					pin_state = allsky_shared.read_gpio_pin(input_pin)
					if pin_state is not None:
						if not invert_sensor:
							if pin_state == 1:
								result_state = 'Raining'
								rain_flag = True
							else:
								result_state = 'Not Raining'
								rain_flag = False
						else:
							if pin_state == 1:
								result_state = 'Not Raining'
								rain_flag = False
							else:
								result_state = 'Raining'
								rain_flag = True

						extra_data = {}
						extra_data['AS_RAINSTATE'] = result_state
						extra_data['AS_ALLSKYRAINFLAG'] = rain_flag
						extra_data['AS_ALLSKYRAINFLAGINT'] = int(bool(rain_flag))
      
						allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])

						result = f'Rain State: Its {result_state}'
						allsky_shared.log(1, f'INFO: {result}')
					else:
						result = f'Unable to read Rain sensor - Error reading gpio pin {input_pin}'
						allsky_shared.log(0, f'ERROR: {result}')
						allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])

				except Exception as ex:
					result = f'Unable to read Rain sensor {ex}'
					allsky_shared.log(0, f'ERROR: {result}')
					allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])
			else:
				result = f'Invalid GPIO pin ({input_pin})'
				allsky_shared.log(0, f'ERROR: {result}')
				allsky_shared.deleteExtraData(self.meta_data['extradatafilename'])

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()            
			result = str(e)
			allsky_shared.log(0, f'ERROR: Module rain failed on line {eTraceback.tb_lineno} - {e}')

		return result
        
def rain(params, event):
	allsky_rain = ALLSKYRAIN(params, event)
	result = allsky_rain.run()

	return result   

def rain_cleanup():
	moduleData = {
		"metaData": ALLSKYRAIN.meta_data,
		"cleanup": {
			"files": {
				ALLSKYRAIN.meta_data['extradatafilename']
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)