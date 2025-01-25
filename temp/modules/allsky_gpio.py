'''
allsky_gpio.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import numpy as np
import board
from digitalio import DigitalInOut, Direction, Pull

metaData = {
	"name": "Sets a GPIO Pin",
	"description": "Sets a GPIO Pin",
	"version": "v1.0.0",
	"module": "allsky_gpio",
	"testable": "true",
	"centersettings": "false", 
	"events": [
	    "daynight",
	    "nightday"
	],
	"experimental": "false",
 	"extradata": {
		"values": {
			"AS_GPIO_PIN_STATE": {
				"name": "${GPIO_PIN_STATE}",
				"format": "",
				"sample": "",                
				"group": "Gpio",
				"description": "GPIO Pin Status",
				"type": "bool"
			}
		}
	},   
	"arguments":{
	    "gpio": 0,
	    "state": 0
	},
	"argumentdetails": {
	    "gpio": {
	        "required": "false",
	        "description": "GPIO Pin",
	        "help": "",
	        "type": {
	            "fieldtype": "gpio"
	        }             
	    },
	    "state": {
	        "required": "false",
	        "description": "Pin State",
	        "help": "",
	        "type": {
				"fieldtype": "checkbox"
	        }             
	    }                     
	},
	"enabled": "false",
	"changelog": {
		"v1.0.0" : [
			{
				"author": "Alex Greenland",
				"authorurl": "https://github.com/allskyteam",
				"changes": [
					"Initial version",
					"Converted to new module format"
				]
			}
		]   
	}           
}

class ALLSKYGPIO(ALLSKYMODULEBASE):
	def __init__(self, params, event):
		self.params = params
		self.event = event

	def run(self):
		try:
			gpio_pin = self.get_param('gpio', 0, int)
			gpio_state = self.get_param('state', False, bool)

			if gpio_pin is not 0:
				pin = allsky_shared.get_gpio_pin_details(gpio_pin)
				pin = DigitalInOut(pin)
				pin.switch_to_output()
				
				pin.value = gpio_state
				extra_data = {}
				extra_data['AS_GPIO_PIN_STATE'] = gpio_state 						
				allsky_shared.saveExtraData('allskygpio.json', extra_data, metaData['extradata'])

				result = f'INFO: GPIO pin {gpio_pin} set to {gpio_state}'
				allsky_shared.log(4, f'INFO: {result}')
			else:
				result = f'GPIO pin is invalid'
				allsky_shared.log(4, f'ERROR: {result}')     
		except Exception as e:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'Module gpio - {exception_traceback.tb_lineno} - {e}'
			allsky_shared.log(4, f'ERROR: {result}')   

		return result
    
def gpio(params, event): 
	allsky_gpio = ALLSKYGPIO(params, event)
	result = allsky_gpio.run()

	return result    

def gpio_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskygpio.json"
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)