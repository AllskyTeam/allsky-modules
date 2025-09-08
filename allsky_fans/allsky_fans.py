'''
allsky_fans.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Disable bcm2835 on pi 4 as it interferes with the hardware pwm
# Enable audio (loads snd_bcm2835)
#dtparam=audio=on

dtoverlay=pwm-2chan

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
import requests

class ALLSKYFANS(ALLSKYMODULEBASE):
    
	meta_data = {
		"name": "Control Allsky Fans",
		"description": "Start A Fans when the CPU or external sensor reaches a set temperature",
		"module": "allsky_fans",    
		"version": "v1.0.3",
		"testable": "true",
		"centersettings": "false", 
		"events": [
			"night",
			"day",
			"periodic"
		],
		"enabled": "false",    
		"experimental": "false",
		"extradatafilename": "allsky_fans.json",
		"group": "Environment Control",
        "graphs": {
			"chart1": {
				"icon": "fas fa-chart-line",
				"title": "Fan Speed",
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
						"text": "Fans"
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
								"text": "Fan Speed"
							} 
						}
					]
				},
				"series": {
					"fan1speed": {
						"name": "Fan 1",
						"yAxis": 0,
						"variable": "AS_FANS_PWM_DUTY_CYCLE1"                 
					},
					"fan2speed": {
						"name": "Fan 2",
						"yAxis": 0,
						"variable": "AS_FANS_PWM_DUTY_CYCLE2"
					}               
				}
			},
            "guage1": {
				"icon": "fa-solid fa-gauge",
				"title": "Fan 1 Speed",
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
						"text": "Fan 1 Speed"
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
						"name": "Speed",
						"data": "AS_FANS_PWM_DUTY_CYCLE1",
						"tooltip": {
							"valueSuffix": " %"
						},
						"dataLabels": {
							"format": "{y} %",
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
            },
            "guage2": {
				"icon": "fa-solid fa-gauge",
				"title": "Fan 2 Speed",
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
						"text": "Fan 2 Speed"
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
						"name": "Speed",
						"data": "AS_FANS_PWM_DUTY_CYCLE2",
						"tooltip": {
							"valueSuffix": " %"
						},
						"dataLabels": {
							"format": "{y} %",
							"borderWidth": 0,
							"color": "#333333",
							"style": {
								"fontSize": "16px"
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
				"table": "allsky_fans",
				"include_all": "true"
			},
			"values": {
				"AS_FANS_ENABLE1": {
					"name": "${FANS_ENABLE1}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 enabled",
					"type": "bool"
				},       
				"AS_FANS_FAN_STATE1": {
					"name": "${FANS_FAN_STATE1}",
					"format": "{yesno}",
					"sample": "",                
					"group": "Fan",
					"description": "Fan 1 Status",
					"type": "bool"
				},
				"AS_FANS_TEMPERATURE1": {
					"name": "${FANS_TEMPERATURE1}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 module Temperature",
					"type": "temperature"
				},             
				"AS_FANS_TEMP_LIMIT1": {
					"name": "${FANS_TEMP_LIMIT1}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 Activation Temperature",
					"type": "temperature"
				},
				"AS_FANS_USE_PWM1": {
					"name": "${FANS_USE_PWM1}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 use PWM",
					"type": "bool"
				},
				"AS_FANS_PWM_ENABLED1": {
					"name": "${FANS_PWM_ENABLED1}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 PWM enabled",
					"type": "bool"
				},
				"AS_FANS_PWM_DUTY_CYCLE1": {
					"name": "${FANS_PWM_DUTY_CYCLE1}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 1 PWM Duty Cycle",
					"type": "number"
				},
				"AS_FANS_ENABLE2": {
					"name": "${FANS_ENABLE2}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 enabled",
					"type": "bool"
				},     
				"AS_FANS_FAN_STATE2": {
					"name": "${FANS_FAN_STATE2}",
					"format": "{yesno}",
					"sample": "",                
					"group": "Fan",
					"description": "Fan 2 Status",
					"type": "bool"
				},
				"AS_FANS_TEMPERATURE2": {
					"name": "${FANS_TEMPERATURE2}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 module Temperature",
					"type": "temperature"
				},             
				"AS_FANS_TEMP_LIMIT2": {
					"name": "${FANS_TEMP_LIMIT2}",
					"format": "{dp=2|deg|unit}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 Activation Temperature",
					"type": "temperature"
				},
				"AS_FANS_USE_PWM2": {
					"name": "${FANS_USE_PWM2}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 use PWM",
					"type": "bool"
				},
				"AS_FANS_PWM_ENABLED2": {
					"name": "${FANS_PWM_ENABLED2}",
					"format": "{yesno}",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 PWM enabled",
					"type": "bool"
				},
				"AS_FANS_PWM_DUTY_CYCLE2": {
					"name": "${FANS_PWM_DUTY_CYCLE2}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan 2 PWM Duty Cycle",
					"type": "number"
				}
			}
		}, 
		"arguments":{
			"enable1": "False",
			"sensor_type1": "Internal",
			"period1": 60,
			"fanpin1": "18",
			"invertrelay1": "False",        
			"usepwm1": "false",
			"pwmmin1": 0,
			"pwmmax1": 100,
			"limitInternal1": 60,
			"temperature1": "AS_TEMP",

			"enable2": "False",
			"sensor_type2": "Internal",
			"period2": 60,
			"fanpin2": "18",
			"invertrelay2": "False",        
			"usepwm2": "false",
			"pwmmin2": 0,
			"pwmmax2": 100,
			"limitInternal2": 60,
			"temperature2": "AS_TEMP",

			"enabledataage": "false",
			"dataage": "0"
		},
		"argumentdetails": {
			"enable1" : {
				"required": "false",
				"description": "Enable Fan",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "checkbox"
				}
			},      
			"sensor_type1" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used. 'internal' will read the cpu temperature of the PI. 'Allsky' will allow you to select an environment sensor from the 'Allsky Environment' module",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "select",
					"values": "Internal,Allsky",
					"default": "Internal"
				}
			},
			"temperature1": {
				"required": "false",
				"description": "Temperature Variable",
				"help": "The Variable to use for the temperature",
				"tab": "Fan 1",
				"filters": {
					"filter": "sensor_type1",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable"
				}                             
			},
			"limitInternal1" : {
				"required": "false",
				"description": "Temp. Limit",
				"help": "The temperature limit beyond which fans are activated",
				"tab": "Fan 1",
				"filters": {
					"filter": "sensor_type1",
					"filtertype": "show",
					"values": [
						"Internal",
						"Allsky"
					]
				},     
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 75,
					"step": 1
				}     
			},  
			"period1" : {
				"required": "true",
				"description": "Read Every",
				"help": "How frequently to read the temperature data, in seconds",                
				"tab": "Fan 1",
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 600,
					"step": 1
				}          
			},
			"fanpin1": {
				"required": "false",
				"description": "Fans Output Pin",
				"help": "The GPIO pin for the fan or PWM",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "gpio"
				}           
			},         
			"invertrelay1" : {
				"required": "false",
				"description": "Invert Output",
				"help": "Invert the output.",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"usepwm1" : {
				"required": "false",
				"description": "Use PWM",
				"help": "Use PWM Fan control. Please see the module documentation BEFORE using this feature",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"pwmmin1" : {
				"required": "false",
				"description": "Min PWM Temp",
				"help": "Below this temp the fan will be off. This equates to 0% PWM duty cycle",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm1",
					"filtertype": "show",
					"values": [
						"usepwm1"
					]
				}      
			},
			"pwmmax1" : {
				"required": "false",
				"description": "Max PWM Temp",
				"help": "Below this temp the fan will be on. This equates to 100% PWM duty cycle",
				"tab": "Fan 1",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm1",
					"filtertype": "show",
					"values": [
						"usepwm1"
					]
				}
			},

			"enable2" : {
				"required": "false",
				"description": "Enable Fan",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "checkbox"
				}
			},      
			"sensor_type2" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used. 'internal' will read the cpu temperature of the PI. 'Allsky' will allow you to select an environment sensor from the 'Allsky Environment' module",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "select",
					"values": "Internal,Allsky",
					"default": "Internal"
				}
			},
			"temperature2": {
				"required": "false",
				"description": "Temperature Variable",
				"help": "The Variable to use for the temperature",
				"tab": "Fan 2",
				"filters": {
					"filter": "sensor_type2",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable"
				}                             
			},
			"limitInternal2" : {
				"required": "false",
				"description": "Temp. Limit",
				"help": "The temperature limit beyond which fans are activated",
				"tab": "Fan 2",
				"filters": {
					"filter": "sensor_type2",
					"filtertype": "show",
					"values": [
						"Internal",
						"Allsky"
					]
				},     
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 75,
					"step": 1
				}     
			},  
			"period2" : {
				"required": "true",
				"description": "Read Every",
				"help": "How frequently to read the temperature data, in seconds",                
				"tab": "Fan 2",
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 600,
					"step": 1
				}          
			},
			"fanpin2": {
				"required": "false",
				"description": "Fans Output Pin",
				"help": "The GPIO pin for the fan or PWM",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "gpio"
				}           
			},         
			"invertrelay2" : {
				"required": "false",
				"description": "Invert Output",
				"help": "Invert the output.",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"usepwm2" : {
				"required": "false",
				"description": "Use PWM",
				"help": "Use PWM Fan control. Please see the module documentation BEFORE using this feature",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"pwmmin2" : {
				"required": "false",
				"description": "Min PWM Temp",
				"help": "Below this temp the fan will be off. This equates to 0% PWM duty cycle",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm2",
					"filtertype": "show",
					"values": [
						"usepwm2"
					]
				}      
			},
			"pwmmax2" : {
				"required": "false",
				"description": "Max PWM Temp",
				"help": "Below this temp the fan will be on. This equates to 100% PWM duty cycle",
				"tab": "Fan 2",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				},
				"filters": {
					"filter": "usepwm2",
					"filtertype": "show",
					"values": [
						"usepwm2"
					]
				}         
			},
			"enabledataage" : {
				"required": "false",
				"description": "Custom Data Expiry",
				"help": "Enable custom data expiry. This will overrides the default in the module manager",
				"tab": "Data Control",
    			"type": {
					"fieldtype": "checkbox"
				}
			},  
			"dataage" : {
				"required": "false",
				"description": "Data Age",
				"help": "After this number of seconds if the module data is not updated it will be removed.",
				"tab": "Data Control",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 60000,
					"step": 1
				},
				"filters": {
					"filter": "enabledataage",
					"filtertype": "show",
					"values": [
						"enabledataage"
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
					"author": "Lorenzi70",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.1" : [
				{
					"author": "Tamas Maroti (CapricornusObs)",
					"authorurl": "https://github.com/CapricornusObs",
					"changes": [
						"Added external temperature sensors to control fan",
						"Added BMP280 sersor control code"
					]
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Added PWM options for fan control",
						"Added SHT31 temperature sensor"
					]
				}
			],
			"v1.0.3" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Converted to new module format",
						"Removed all external sensors - Use allsky_temp module to read sensors"
					]
				}
			]       
		}
	}    

	_temperature = 0
	_temperature_limit = 0
	_fan_pin = 0
	_invert_relay = False
	_debugmode = False
	_pwm_map = ['4B', '5B']

	def _get_cpu_temperature(self):
		temp_c = 0
		try:
			temp = allsky_shared.get_pi_info(allsky_shared.Pi_INFO_CPU_TEMPERATURE)
			temp_c = float(temp)
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module _get_cpu_temperature - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')   

		return temp_c

	def _get_allsky_temperature(self):
		temperature = 0
		try:
			allsky_variable = self.get_param(f'temperature{self._fan_number}', 'AS_TEMP')
			temperature = allsky_shared.get_allsky_variable(allsky_variable)
			temperature = float(temperature)
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Fan {self._fan_number} - Module _get_cpu_temperature - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')   

		return temperature

	def _set_gpio_pin_state(self, state):
		if self._invert_relay:
			state = not state
			
		result = allsky_shared.set_gpio_pin(self._fan_pin, state)

		return result

	def _turn_fan_on(self):
		return self._set_gpio_pin_state(1)

	def _turn_fan_off(self):
		return self._set_gpio_pin_state(0)

	def _display_status(self, value):
		return 'On' if value else 'Off'

	def _use_bool_fan_control(self, fan_number):
		error = False
		state = False
  
		try:  
			allsky_shared.stop_pwm(self._fan_pin)

			if (self._temperature > self._temperature_limit):
				fan_result = self._turn_fan_on()
				fan_status = True
				result = f'Fan {self._fan_number} - {self._temperature} is higher then set limit of {self._temperature_limit}, Fans are {self._display_status(fan_status)} via fan pin {self._fan_pin}'
				state= True
			else:
				fan_result = self._turn_fan_off()
				fan_status = False
				result = f'Fan {self._fan_number} - {self._temperature} is lower then set limit of {self._temperature_limit}, Fans are {self._display_status(fan_status)} via fan pin {self._fan_pin}'

			if not fan_result:
				result = f'Fan {self._fan_number} - Failed to set the fan status check pigpiod is running'
				error = True

		except requests.exceptions.ConnectionError  as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Fan {self._fan_number} - Module _use_bool_fan_control - Unable to connect to the Allsky server. Is it running?'
			allsky_shared.log(0, f'ERROR: {result}')
			error = True 
      
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Fan {self._fan_number} - Module _use_bool_fan_control - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')      
			error = True 
   
		return result, error, state

	def _temperature_to_pwm_duty(self, temp, min_temp, max_temp):
		if temp <= min_temp:
			return 0
		elif temp >= max_temp:
			return 65535
		else:
			ratio = (temp - min_temp) / (max_temp - min_temp)
			return int(ratio * 65535)
    
	def _use_pwm_fan_control(self, fan_number):
		pwm_min = self.get_param(f'pwmmin{fan_number}', 0, int)
		pwm_max = self.get_param(f'pwmmax{fan_number}', 100, int)
		result = ''
		pwm_enabled = 0
		pwm_duty_cycle = 0
		error = False
		status = False

		try:
			if self._fan_pin != 0:
				model = allsky_shared.get_pi_info(allsky_shared.PI_INFO_MODEL)
				if model in self._pwm_map:
					pwm_duty_cycle = self._temperature_to_pwm_duty(self._temperature, pwm_min, pwm_max)
					pwm_result = allsky_shared.set_pwm(self._fan_pin, pwm_duty_cycle)
					status = True     
					if pwm_result:
						pwm_enabled = 1
						duty_percent = round((pwm_duty_cycle / 65535) * 100,2)
						result = f'Fan {self._fan_number} - PWM duty cycle set to {pwm_duty_cycle}, {duty_percent}% on pin {self._fan_pin}'
					else:
						result = f'Fan {self._fan_number} - Failed to set the fan status check pigpiod is running'
				else:
					result = f'Pi Model ({model}) is not supported for PWM'
					allsky_shared.log(0, f'ERROR: {result}')
			else:
				result = 'Fan {self._fan_number} - PWM Pin is invalid'
				allsky_shared.log(0, f'ERROR: {result}')
		except requests.exceptions.ConnectionError  as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Fan {self._fan_number} - Module _use_pwm_fan_control - Unable to connect to the Allsky server. Is it running?'
			allsky_shared.log(0, f'ERROR: {result}')
			error = True 
      
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Fan {self._fan_number} - Module _use_pwm_fan_control - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')      
			error = True 

		return result, pwm_duty_cycle, pwm_enabled, error, status
		
	def run(self):
		result = ''
		extra_data = {}

		self._debugmode = self.get_param('ALLSKYTESTMODE', False, bool)  

		for fan_number in range(1,3):
			enabled = self.get_param(f'enable{fan_number}', False, bool)
			if enabled:
				fan_status = ''
				sensor_type = self.get_param(f'sensor_type{fan_number}', 'internal')
				run_period = self.get_param(f'period{fan_number}', 60, int)
				self._temperature_limit = self.get_param(f'limitInternal{fan_number}', 0, int)
				self._fan_pin = self.get_param(f'fanpin{fan_number}', None, int)
				self._invert_relay = self.get_param(f'invertrelay{fan_number}', False, bool)
				use_pwm = self.get_param(f'usepwm{fan_number}', False, bool)
				self._fan_number = fan_number
				self._temperature = None
				fan_status = False
				error = False
				module = self.meta_data['module']
				run_code = f'{module}-{fan_number}'
				try:
					should_run, diff = allsky_shared.shouldRun(run_code, run_period)
					if should_run or self._debugmode:
						if self._fan_pin is not None:

							if sensor_type == 'Internal':
								self._temperature = self._get_cpu_temperature()
							if sensor_type == 'Allsky':
								self._temperature = self._get_allsky_temperature()

							if self._temperature is not None:
								if use_pwm:
									result, pwm_duty_cycle, pwm_enabled, error, fan_status = self._use_pwm_fan_control(fan_number)
								else:
									result, error, fan_status = self._use_bool_fan_control(fan_number)

								if not error:
									extra_data[f'AS_FANS_FAN_STATE{fan_number}'] = fan_status
									extra_data[f'AS_FANS_TEMP_LIMIT{fan_number}'] = self._temperature_limit
									extra_data[f'AS_FANS_TEMPERATURE{fan_number}'] = self._temperature
									extra_data[f'AS_FANS_USE_PWM{fan_number}'] = True if use_pwm else False
									if use_pwm:
										extra_data[f'AS_FANS_PWM_ENABLED{fan_number}'] = True if pwm_enabled == 1 else False
										extra_data[f'AS_FANS_PWM_DUTY_CYCLE{fan_number}'] = pwm_duty_cycle
									else:
										extra_data[f'AS_FANS_PWM_DUTY_CYCLE{fan_number}'] = 100

								allsky_shared.setLastRun(run_code)
							else:
								result = f'Failed to get temperature for fan {fan_number}'
								allsky_shared.log(0, f'ERROR: {result}')
						else:
							result = f'fan pin not defined or invalid for fan {fan_number}'
							allsky_shared.log(0, f'ERROR: {result}')
					else:
						result = f'Fan {fan_number} Will run in {(run_period - diff):.0f} seconds'
				except Exception as e:
					exception_type, exception_object, exception_traceback = sys.exc_info()
					result = f'Fan Module run - Fan {fan_number} - {exception_traceback.tb_lineno} - {e}'
					allsky_shared.log(4, f'ERROR: {result}')    

				if not error:
					allsky_shared.log(4,f'INFO: {result}')
			else:
				allsky_shared.log(4,f'INFO: FAN {fan_number} skipped as its disabled')

		if extra_data:
			allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])

		return result

def fans(params, event):
	allsky_fans = ALLSKYFANS(params, event)
	result = allsky_fans.run()

	return result    

def fans_cleanup():
	moduleData = {
		"metaData": ALLSKYFANS.meta_data,
		"cleanup": {
			"files": {
				ALLSKYFANS.meta_data['extradatafilename']
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)
