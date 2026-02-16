import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import time
import board
import digitalio
import sparkfun_qwiicas3935

class ALLSKYLIGHTNING(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Lightning Detection",
		"description": "Detects lightning using an as3935 sensor",
		"version": "v1.0.0",
		"module": "allsky_lightning", 
		"centersettings": "false",
		"testable": "true",
		"experimental": "true",
		"group": "Data Sensor",
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradatafilename": "allsky_lightning.json", 
		"extradata": {
			"values": {
				"AS_LIGHTNING_COUNT": {
					"name": "${LIGHTNING_COUNT}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Number of lightning strikes",
					"type": "number"
				},
				"AS_LIGHTNING_DIST": {
					"name": "${LIGHTNING_DIST}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Approx distance of last strike",
					"type": "number"
				},
				"AS_LIGHTNING_ENERGY": {
					"name": "${LIGHTNING_ENERGY}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Energy of last strike",
					"type": "number"
				},
				"AS_LIGHTNING_LAST": {
					"name": "${LIGHTNING_LAST}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Date/Time of last strike",
					"type": "timestamp"
				}                                        
			}                
		},
		"arguments":{
			"i2caddress": "",
			"interruptpin": "",
			"maskdisturbers": "True",
			"noiselevel": 2,
			"watchdogthreshold": 2,
			"spikerejection": 2,
			"lightningthreshold": 1,
			"expirestrikes": 600
		},
		"argumentdetails": {
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x03.",
				"type": {
					"fieldtype": "i2c"
				}           
			},
			"interruptpin": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for the lightning sensor.",
				"type": {
					"fieldtype": "gpio"
				}           
			},
			"maskdisturbers" : {
				"required": "false",
				"description": "Mask disturbers",
				"help": "If enabled disturbers will be ignored.",
				"tab": "Advanced",
				"type": {
					"fieldtype": "checkbox"
				}            
			},
			"noiselevel" : {
				"required": "false",
				"description": "Noise level",
				"help": "Sets the base noise level, 1 is lowest 7 is highest ambient noise.",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 7,
					"step": 1
				}                      
			},
			"watchdogthreshold" : {
				"required": "false",
				"description": "Watchdog Threshold",
				"help": "Minimum signal level to trigger the lightning verification algorithm (1-10).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 1
				}                      
			},
			"spikerejection" : {
				"required": "false",
				"description": "Spike Rejection",
				"help": "The default setting is two. The shape of the spike is analyzed during the chip's validation routine. You can round this spike at the cost of sensitivity to distant events (1-11).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 11,
					"step": 1
				}                      
			},
			"lightningthreshold" : {
				"required": "false",
				"description": "Strike Threshold",
				"help": "The number of strikes detected before an event is triggered.",
				"tab": "Advanced",
				"type": {
					"fieldtype": "select",
					"values": "1,5,9,16",
					"default": "None"
				}
			},
			"expirestrikes" : {
				"required": "false",
				"description": "Expire Strikes",
				"help": "If a strike is detected then after this number of seconds of no strikes the strikes overlay variable and strike counter will be reset. Default is 600 seconds (10 minutes).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 3600,
					"step": 1
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
			]                              
		}         
	}
    
	def run(self):
     
		mask_disturbers = self.get_param('maskdisturbers', True, bool)
		noise_level = self.get_param('noiselevel', 2, int)
		watchdog_threshold = self.get_param('watchdogthreshold', 2, int)
		spike_rejection = self.get_param('spikerejection', 2, int)
		lightning_threshold = self.get_param('lightningthreshold', 1, int)
		expire_strikes = self.get_param('expirestrikes', 600, int)
  
		as3935_interrupt_pin = digitalio.DigitalInOut(board.D21)
		as3935_interrupt_pin.direction = digitalio.Direction.INPUT
		as3935_interrupt_pin.pull = digitalio.Pull.DOWN
		i2c = board.I2C()

		i2c_address = self.get_param('i2caddress', '', str)
		if i2c_address != "":
			try:
				i2c_address_int = int(i2c_address, 16)
			except Exception as e:
				result = 'Address {i2c_address} is not a valid i2c address'
				self.log(0, "ERROR in {__file__}: {}".format(result))
    
		if i2c_address != "":    
			lightning = sparkfun_qwiicas3935.Sparkfun_QwiicAS3935_I2C(i2c, i2c_address_int)
		else:
			lightning = sparkfun_qwiicas3935.Sparkfun_QwiicAS3935_I2C(i2c)

		if lightning.connected:
			self.log(4, 'INFO: Lightning Detector Ready')
		
			afe_mode = lightning.indoor_outdoor
			if afe_mode == lightning.OUTDOOR:
				self.log(4, 'INFO: The Lightning Detector is in the Outdoor mode.')
			elif afe_mode == lightning.INDOOR:
				self.log(4, 'INFO: The Lightning Detector is in the Indoor mode.')
			else:
				self.log(4, f'INFO: The Lightning Detector is in an Unknown mode. Mode = {afe_mode}')
			
			lightning.mask_disturber = mask_disturbers
			if lightning.mask_disturber:
				self.log(4, 'INFO: Disturbers are being masked.')
			else:
				self.log(4, 'INFO: Disturbers are not being masked.')

			lightning.noise_level = noise_level
			self.log(4, f'INFO: Noise level is set at: {noise_level}')

			lightning.watchdog_threshold = watchdog_threshold
			self.log(4, f'INFO: Watchdog Threshold is set to: {watchdog_threshold}')

			lightning.spike_rejection = spike_rejection
			self.log(4, f'INFO: Spike Rejection is set to: {spike_rejection}')

			lightning.lightning_threshold = lightning_threshold
			self.log(4, f'INFO:The number of strikes before interrupt is triggered: {lightning_threshold}')
 
			if as3935_interrupt_pin.value:
				interrupt_value = lightning.read_interrupt_register()
				#interrupt_value = lightning.LIGHTNING
				if interrupt_value == lightning.NOISE:
					self.log(4, f'INFO: Noise detected')
				elif interrupt_value == lightning.DISTURBER:
					self.log(4, f'INFO: Disturber detected')
				elif interrupt_value == lightning.LIGHTNING:
					distance_to_storm = lightning.distance_to_storm
					lightning_energy = lightning.lightning_energy
					count = allsky_shared.db_get('allsky_lightning_strike_counter')
					if count is None:
						count = 1
					else:
						count = int(count) + 1
		
					last_strike_time = int(time.time()) 
					extra_data = {}
					extra_data['AS_LIGHTNING_COUNT'] = count
					extra_data['AS_LIGHTNING_LAST'] = last_strike_time
					extra_data['AS_LIGHTNING_DIST'] = distance_to_storm    
					extra_data['AS_LIGHTNING_ENERGY'] = lightning_energy    
					allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
		
					allsky_shared.dbUpdate('allsky_lightning_strike_counter', count)
					allsky_shared.dbUpdate('allsky_lightning_last_strike', last_strike_time)    
					self.log(4, f'INFO: Strike detected. Approx distance: {distance_to_storm}km, Energy: {lightning_energy}, Total Strikes: {count}')
				else:
					self.log(4, f'INFO: Unknown event detected')
			else:
				self.log(4, f'INFO: No event detected')

			last_strike_time = allsky_shared.db_get('allsky_lightning_last_strike')
			if last_strike_time is not None:
				now = int(time.time())
				if (now - last_strike_time) > expire_strikes:
					allsky_shared.db_delete_key('allsky_lightning_last_strike')
					extra_data = {}
					extra_data['AS_LIGHTNING_COUNT'] = count
					extra_data['AS_LIGHTNING_LAST'] = last_strike_time
					extra_data['AS_LIGHTNING_DIST'] = 0    
					extra_data['AS_LIGHTNING_ENERGY'] = 0    
					allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
       
		else:
			result = 'Lightning Detector does not appear to be connected. Please check wiring.'
			self.log(0, f'ERROR in {__file__}: {result}')
   							
def lightning(params, event):
	allsky_lightning = ALLSKYLIGHTNING(params, event)
	result = allsky_lightning.run()
 
	return result

def lightning_cleanup():
	moduleData = {
	    "metaData": ALLSKYLIGHTNING.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYLIGHTNING.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
