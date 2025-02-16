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
from gpiozero import CPUTemperature
from digitalio import DigitalInOut, Direction, Pull

import sys
from rpi_hardware_pwm import HardwarePWM, HardwarePWMException
from gpiozero import Device

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
		"extradata": {
			"values": {
				"AS_FANS_FAN_STATE": {
					"name": "${FANS_FAN_STATE}",
					"format": "",
					"sample": "",                
					"group": "Fan",
					"description": "Fan Status",
					"type": "bool"
				},
				"AS_FANS_TEMPERATURE": {
					"name": "${FANS_TEMPERATURE}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "Fan module Temperature",
					"type": "temperature"
				},             
				"AS_FANS_TEMP_LIMIT": {
					"name": "${FANS_TEMP_LIMIT}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "Activation Temperature",
					"type": "temperature"
				},
				"AS_FANS_USE_PWM": {
					"name": "${FANS_USE_PWM}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "Use PWM Fan Control",
					"type": "bool"
				},
				"AS_FANS_PWM_ENABLED": {
					"name": "${FANS_PWM_ENABLED}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "PWM Fan control enabled",
					"type": "bool"
				},
				"AS_FANS_PWM_DUTY_CYCLE": {
					"name": "${FANS_PWM_DUTY_CYCLE}",
					"format": "",
					"sample": "",                 
					"group": "Fan",
					"description": "PWM Duty Cycle",
					"type": "Number"
				}
			}
		}, 
		"arguments":{
			"sensor_type": "Internal",
			"period": 60,
			"fanpin": "18",
			"invertrelay": "False",        
			"usepwm": "false",
			"pwmmin": 0,
			"pwmmax": 100,
			"limitInternal": 60,
			"temperature": "AS_TEMP"
		},
		"argumentdetails": {
			"sensor_type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "select",
					"values": "Internal,Allsky",
					"default": "Internal"
				}
			},
			"temperature": {
				"required": "false",
				"description": "Temperature Variable",
				"help": "The Variable to use for the temperature",
				"tab": "Sensor",
				"filters": {
					"filter": "sensor_type",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable"
				}                             
			},
			"limitInternal" : {
				"required": "false",
				"description": "Temp. Limit",
				"help": "The temperature limit beyond which fans are activated",
				"tab": "Sensor",
				"filters": {
					"filter": "sensor_type",
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
			"period" : {
				"required": "true",
				"description": "Read Every",
				"help": "Reads data every x seconds.",                
				"tab": "Sensor",
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 600,
					"step": 1
				}          
			},
			"fanpin": {
				"required": "false",
				"description": "Fans Relay Pin",
				"help": "The GPIO pin for the fan relay or PWM",
				"tab": "Sensor",
				"type": {
					"fieldtype": "gpio"
				}           
			},         
			"invertrelay" : {
				"required": "false",
				"description": "Invert Relay",
				"help": "Invert relay activation logic from pin HIGH to pin LOW",
				"tab": "Sensor",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"usepwm" : {
				"required": "false",
				"description": "Use PWM",
				"help": "Use PWM Fan control. Please see the module documentation BEFORE using this feature",
				"tab": "PWM",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"pwmmin" : {
				"required": "false",
				"description": "Min PWM Temp",
				"help": "Below this temp the fan will be off. This equates to 0% PWM duty cycle",
				"tab": "PWM",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				}     
			},
			"pwmmax" : {
				"required": "false",
				"description": "Max PWM Temp",
				"help": "Below this temp the fan will be on. This equates to 100% PWM duty cycle",
				"tab": "PWM",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
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
	_pwm_map = {
		"4B": {
			"enabled": "/sys/class/pwm/pwmchip0/pwm%CHANNEL%/enable",
			"chip": 0,
			"addresses": {
				18: 0,
				19: 1,
				12: 0,
				13: 1
			}
		},
		"5B": {
			"enabled": "/sys/class/pwm/pwmchip2/pwm%CHANNEL%/enable",
			"chip": 2,
			"addresses": {
				18: 0,
				19: 1,
				12: 0,
				13: 1
			}
		}
	}

	def _get_cpu_temperature(self):
		temp_c = 0
		try:
			temp = CPUTemperature().temperature
			temp_c = float(temp)
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module _get_cpu_temperature - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')   
     
		return temp_c

	def _get_allsky_temperature(self):
		temperature = 0
		try:
			temperature = allsky_shared.get_allsky_variable(self._params['temperature'])
			temperature = float(temperature)
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module _get_cpu_temperature - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')   

		return temperature

	def _turn_fan_on(self, fan_pin, invert_relay):
		pin = DigitalInOut(fan_pin)
		pin.switch_to_output()
		
		if invert_relay:
			pin.value = 0
		else:
			pin.value = 1

	def _turn_fan_off(self, fan_pin, invert_relay):
		pin = DigitalInOut(fan_pin)
		pin.switch_to_output()

		if invert_relay:
			pin.value = 1
		else:    
			pin.value = 0

	def _display_status(self, value):
		return 'On' if value else 'Off'
    
	def _use_bool_fan_control(self):
		error = False
         
		if (self._temperature > self._temperature_limit):
			self._turn_fan_on(self._fan_pin, self._invert_relay)
			fan_status = True
			result = f'{self._temperature} is higher then set limit of {self._temperature_limit}, Fans are {self._display_status(fan_status)} via fan pin {self._fan_pin}'
		else:
			self._turn_fan_off(self._fan_pin, self._invert_relay)
			fan_status = False
			result = f'{self._temperature} is lower then set limit of {self._temperature_limit}, Fans are {self._display_status(fan_status)} via fan pin {self._fan_pin}'

		return result, error
     
	def _use_pwm_fan_control(self):
		pwm_min = self.get_param('pwmmin', 0, int)
		pwm_max = self.get_param('pwmmax', 0, int)
		result = ''
		pwm_enabled = '0'
		pwm_duty_cycle = 0
		error = False
  
		try:
			if self._fan_pin != 0:
				Device.ensure_pin_factory()
				pi_info = Device.pin_factory.board_info
				model = pi_info.model
				if model in self._pwm_map:
					pwm_channel =  self._pwm_map[model]['addresses'][self._fan_pin]
					enabled_file = self._pwm_map[model]['enabled']
					chip = self._pwm_map[model]['chip']
					enabled_file = enabled_file.replace('%CHANNEL%', str(pwm_channel))
					try:
						with open(enabled_file, 'r', encoding='utf-8') as file:
							pwm_enabled = file.readline().strip()
					except FileNotFoundError:
						pwm_enabled = '0'

					pwm = HardwarePWM(pwm_channel=pwm_channel, hz=60, chip=chip)
					if pwm_enabled == '0':
						pwm.start(0)
						pwm.change_frequency(25_000)

					if self._temperature <= pwm_min:
						pwm_duty_cycle = 0
					elif self._temperature > pwm_max:
						pwm_duty_cycle = 100
					else:
						pwm_duty_cycle = int(((self._temperature - pwm_min) / (pwm_max - pwm_min)) * 100)

					pwm.change_duty_cycle(pwm_duty_cycle)
					
					if pwm_duty_cycle == 0:
						pwm.stop()
		
					result = f'PWM duty cycle set to {pwm_duty_cycle} on pin {self._fan_pin}'
				else:
					result = f'Pi Model ({model}) is not supported for PWM'
					allsky_shared.log(0, f'ERROR: {result}')
			else:
				result = 'PWM Pin is invalid'
				allsky_shared.log(0, f'ERROR: {result}')
		except HardwarePWMException as e:
			result = f'There is a problem with the PWM hardware. Please refer to the module documentation for help - "{e}"'
			allsky_shared.log(0, f'ERROR: {result}')
			error = True
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module _use_pwm_fan_control - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')      

		return result, pwm_duty_cycle, pwm_enabled, error
		
	def run(self):
		result = ''
		fan_status = ''
		sensor_type = self.get_param('sensor_type', 'internal')
		run_period = self.get_param('period', 60, int)
		self._temperature_limit = self.get_param('limitInternal', 0, int)
		self._fan_pin = self.get_param('fanpin', None, int)
		self._invert_relay = self.get_param('invertrelay', False, bool)
		self._debugmode = self.get_param('ALLSKYTESTMODE', False, bool)  
		use_pwm = self.get_param('usepwm', False, bool)
		self._temperature = None
		fan_status = False
		error = False
		
		try:
			should_run, diff = allsky_shared.shouldRun(self.meta_data['module'], run_period)
			if should_run or self._debugmode:
				extra_data = {}
				if self._fan_pin is not None:

					if sensor_type == 'Internal':
						self._temperature = self._get_cpu_temperature()
					if sensor_type == 'Allsky':
						self._temperature = self._get_allsky_temperature()

					if self._temperature is not None:
						if use_pwm:
							result, pwm_duty_cycle, pwm_enabled, error = self._use_pwm_fan_control()
						else:
							self._fan_pin = allsky_shared.getGPIOPin(self._fan_pin)         
							result, error = self._use_bool_fan_control()

						if not error:
							extra_data['AS_FANS_FAN_STATE'] = fan_status
							extra_data['AS_FANS_TEMP_LIMIT'] = self._temperature_limit
							extra_data['AS_FANS_TEMPERATURE'] = self._temperature
							if use_pwm:
								extra_data['AS_FANS_USE_PWM'] = True if use_pwm else False
								extra_data['AS_FANS_PWM_ENABLED'] = True if pwm_enabled == '1' else False
								extra_data['AS_FANS_PWM_DUTY_CYCLE'] = pwm_duty_cycle
										
							allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data["module"], self.meta_data["extradata"])
						
						allsky_shared.setLastRun(self.meta_data['module'])
					else:
						result = 'Failed to get temperature'
						allsky_shared.log(0, f'ERROR: {result}')
				else:
					result = 'fan pin not defined or invalid'
					allsky_shared.log(0, f'ERROR: {result}')
			else:
				result = f'Will run in {(run_period - diff):.0f} seconds'
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module run - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')    
     
		if not error:
			allsky_shared.log(4,f'INFO: {result}')

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
