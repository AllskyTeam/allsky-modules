import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import sys
import board
from barbudor_ina3221.full import *
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219

class ALLSKYPOWER(ALLSKYMODULEBASE):
	params = []
	event = ''
 
	meta_data = {
		"name": "Current/voltage monitoring",
		"description": "Monitors current and voltage using an ina219/ina3221",
		"module": "allsky_power",
		"version": "v1.0.0",
		"centersettings": "false",
		"testable": "true",
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradatafilename": "allsky_power.json", 	
		"experimental": "false",
		"group": "Data Sensor",
		"graphs": {
			"chart1": {
				"icon": "fas fa-chart-line",
				"title": "Power Usage",
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
						"text": "Power"
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
								"text": "Voltage"
							} 
						},
						{ 
							"title": {
								"text": "Current"
							},
       						"opposite": "true"
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
					"c1voltage": {
						"name": "Channel 1 Voltage",
						"yAxis": 0,
						"variable": "AS_POWER_VOLTAGE1"                 
					},
					"c2voltage": {
						"name": "Channel 2 Voltage",
						"yAxis": 0,
						"variable": "AS_POWER_VOLTAGE2"
					},
					"c3voltage": {
						"name": "Channel 3 Voltage",
						"yAxis": 0,
						"variable": "AS_POWER_VOLTAGE3"
					},
					"c1current": {
						"name": "Channel 1 Current",
						"yAxis": 1,
						"variable": "AS_POWER_CURRENT2"                 
					},
					"c2current": {
						"name": "Channel 2 Current",
						"yAxis": 1,
						"variable": "AS_POWER_CURRENT3"                 
					},
					"c3current": {
						"name": "Channel 3 Current",
						"yAxis": 1,
						"variable": "AS_POWER_CURRENT1"                 
					}      
				}
			}
		}, 
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_power",
				"include_all": "true"    
			},     
			"values": {
				"AS_POWER_NAME1": {
					"name": "${POWER_NAME1}",
					"format": "",
					"sample": "",                
					"group": "Power",
					"description": "Name of Channel 1",
					"type": "string"
				},              
				"AS_POWER_VOLTAGE1": {
					"name": "${POWER_VOLTAGE1}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 1 voltage",
					"type": "number"
				},
				"AS_POWER_CURRENT1": {
					"name": "${POWER_CURRENT1}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 1 current",
					"type": "number"
				},
				"AS_POWER_BUS_VOLTAGE1": {
					"name": "${POWER_BUS_VOLTAGE1}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 1 bus voltage",
					"type": "number"
				},
				"AS_POWER_SHUNT_VOLTAGE1": {
					"name": "${POWER_SHUNT_VOLTAGE1}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 1 shunt voltage",
					"type": "number"
				},
				"AS_POWER_POWER1": {
					"name": "${POWER_POWER1}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 1 power (w)",
					"type": "number"
				},         
				"AS_POWER_NAME2": {
					"name": "${POWER_NAME2}",
					"format": "",
					"sample": "",                
					"group": "Power",
					"description": "Name of Channel 2",
					"type": "string"
				},              
				"AS_POWER_VOLTAGE2": {
					"name": "${POWER_VOLTAGE2}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 2 voltage",
					"type": "number"
				},
				"AS_POWER_CURRENT2": {
					"name": "${POWER_CURRENT2}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 2 current",
					"type": "number"
				},
				"AS_POWER_BUS_VOLTAGE2": {
					"name": "${POWER_BUS_VOLTAGE2}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 2 bus voltage",
					"type": "number"
				},
				"AS_POWER_SHUNT_VOLTAGE2": {
					"name": "${POWER_SHUNT_VOLTAGE2}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 2 shunt voltage",
					"type": "number"
				},
				"AS_POWER_POWER2": {
					"name": "${POWER_POWER2}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 2 power (w)",
					"type": "number"
				},           
				"AS_POWER_NAME3": {
					"name": "${POWER_NAME3}",
					"format": "",
					"sample": "",                
					"group": "Power",
					"description": "Name of Channel 3",
					"type": "string"
				},              
				"AS_POWER_VOLTAGE3": {
					"name": "${POWER_VOLTAGE3}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 3 voltage",
					"type": "number"
				},
				"AS_POWER_CURRENT3": {
					"name": "${POWER_CURRENT3}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 3 current",
					"type": "number"
				},
				"AS_POWER_BUS_VOLTAGE3": {
					"name": "${POWER_BUS_VOLTAGE3}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 3 bus voltage",
					"type": "number"
				},
				"AS_POWER_SHUNT_VOLTAGE3": {
					"name": "${POWER_SHUNT_VOLTAGE3}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 3 shunt voltage",
					"type": "number"
				},
				"AS_POWER_POWER3": {
					"name": "${POWER_POWER3}",
					"format": "",
					"sample": "",                 
					"group": "Power",
					"description": "Channel 3 power (w)",
					"type": "number"
				}
			}                         
		}, 
		"arguments":{
			"type": "",
			"i2caddress": "",
			"c1enable": "false",
			"c1name": "",
			"c2enable": "false",
			"c2name": "",
			"c3enable": "false",
			"c3name": ""               
		},
		"argumentdetails": {
			"type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor that is being used.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "select",
					"values": "None,ina219,ina3221",
					"default": "None"
				}
			},     
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x40",
				"tab": "Sensor",
				"type": {
					"fieldtype": "i2c"
				},         
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina219",
						"ina3221"
					]
				}                 
			},
			"c1enable" : {
				"required": "false",
				"description": "Enable Channel 1",
				"help": "Enable channel 1 on the sensor",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},         
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"c1name" : {
				"required": "false",
				"description": "Channel 1 name",
				"help": "Name of the channel 1 allsky overlay variable",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},         
				"tab": "Sensor"         
			},
			"c2enable" : {
				"required": "false",
				"description": "Enable Channel 2",
				"help": "Enable channel 2 on the sensor",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},                  
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"c2name" : {
				"required": "false",
				"description": "Channel 2 name",
				"help": "Name of the channel 2 allsky overlay variable",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},         
				"tab": "Sensor"         
			},
			"c3enable" : {
				"required": "false",
				"description": "Enable Channel 3",
				"help": "Enable channel 3 on the sensor",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},                 
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"c3name" : {
				"required": "false",
				"description": "Channel 3 name",
				"help": "Name of the channel 3 allsky overlay variable",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina3221"
					]
				},         
				"tab": "Sensor"         
			},
			"ina219name" : {
				"required": "false",
				"description": "Channel name",
				"help": "Name of the channel for the allsky overlay variable",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"ina219"
					]
				},         
				"tab": "Sensor"         
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
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			]                                            
		}  
	}
 
	def _ina219(self):
		result = 'Ina219 read ok'
		extra_data = {}

		try:
			i2c_bus = board.I2C()

			ina219 = INA219(i2c_bus)

			bus_voltage = ina219.bus_voltage
			shunt_voltage = ina219.shunt_voltage
			current = ina219.current / 1000
			power = ina219.power
			voltage = round(bus_voltage + shunt_voltage,2)

			channel_name = self.get_param(f'c1name', f'INA219_C1', str, True) 
			extra_data[f'AS_POWER_NAME1'] = channel_name
			extra_data[f'AS_POWER_VOLTAGE1'] = voltage
			extra_data[f'AS_POWER_CURRENT1'] = current
			extra_data[f'AS_POWER_BUS_VOLTAGE1'] = bus_voltage
			extra_data[f'AS_POWER_SHUNT_VOLTAGE1'] = shunt_voltage
			extra_data[f'AS_POWER_POWER1'] = power

			allsky_shared.log(4, f'INFO: voltage {voltage}, current {current}. Bus Voltage {bus_voltage}, Shunt Voltage {shunt_voltage}, Power {power}')

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'_ina219 failed on line {eTraceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')
		
		return result, extra_data

	def _read_ina3221_channel(self, ina3221, channel):
		ina3221.enable_channel(channel)
		bus_voltage = ina3221.bus_voltage(channel)
		shunt_voltage = ina3221.shunt_voltage(channel)
		current = ina3221.current(channel)
		voltage = round(bus_voltage + shunt_voltage,2)
		current = round(abs(current),3)
		power = voltage * current

		allsky_shared.log(4, f'INFO: Channel {channel} read, voltage {voltage}, current {current}. Bus Voltage {bus_voltage}, Shunt Voltage {shunt_voltage}, Power {power}')
							
		return voltage, current, bus_voltage, shunt_voltage, power

	def _ina3221(self):
		result = 'Ina3221 read ok'
		extra_data = {}

		try:
			i2cBus = board.I2C()
			ina3221 = INA3221(i2cBus)

			if INA3221.IS_FULL_API:
				ina3221.update(reg=C_REG_CONFIG,
							mask=C_AVERAGING_MASK |
							C_VBUS_CONV_TIME_MASK |
							C_SHUNT_CONV_TIME_MASK |
							C_MODE_MASK,
							value=C_AVERAGING_128_SAMPLES |
							C_VBUS_CONV_TIME_8MS |
							C_SHUNT_CONV_TIME_8MS |
							C_MODE_SHUNT_AND_BUS_CONTINOUS)

			channel_read = False
			for i in range(1, 4):
				channel_enabled = self.get_param(f'c{i}enable', False, bool)
				if channel_enabled:
					channel_read = True
					channel_name = self.get_param(f'c{i}name', f'INA3221_C{i}', str, True) 
					extra_data[f'AS_POWER_NAME{i}'] = channel_name
					extra_data[f'AS_POWER_VOLTAGE{i}'] = 'N/A'
					extra_data[f'AS_POWER_CURRENT{i}'] = 'N/A'          
					extra_data[f'AS_POWER_BUS_VOLTAGE{i}'] = 'N/A'          
					extra_data[f'AS_POWER_SHUNT_VOLTAGE{i}'] = 'N/A'          

					voltage, current, bus_voltage, shunt_voltage, power = self._read_ina3221_channel(ina3221, i)

					extra_data[f'AS_POWER_VOLTAGE{i}'] = voltage
					extra_data[f'AS_POWER_CURRENT{i}'] = current
					extra_data[f'AS_POWER_BUS_VOLTAGE{i}'] = bus_voltage
					extra_data[f'AS_POWER_SHUNT_VOLTAGE{i}'] = shunt_voltage
					extra_data[f'AS_POWER_POWER{i}'] = power

			if not channel_read:
				result = 'No channels are enabled so none read'
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'_ina3221 failed on line {eTraceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')
		
		return result, extra_data

	def run(self):
		extra_data = {}

		sensor_type = self.get_param('type', '', str)  
		if sensor_type == 'ina3221':
			result, extra_data = self._ina3221()
		else:
			if sensor_type == 'ina219':
				result, extra_data = self._ina219()       
			else:
				result = f'power module - invalid sensor type "{sensor_type}"'

		allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
		allsky_shared.log(4, f'INFO: {result}')
		return result
				
def power(params, event):
	allsky_power = ALLSKYPOWER(params, event)
	result = allsky_power.run()

	return result 
    
def power_cleanup():
	moduleData = {
		"metaData": ALLSKYPOWER.meta_data,
		"cleanup": {
			"files": {
				ALLSKYPOWER.meta_data['extradatafilename']
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)

