import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import sys
from pms7003 import Pms7003Sensor, PmsSensorException

class ALLSKYPMSX003(ALLSKYMODULEBASE):
	'''
	pm1_0cf1 - PM1.0 concentration in μg/m3 (corrected to standard conditions)
	pm2_5cf1 - PM2.5 concentration in μg/m3 (corrected to standard conditions)
	pm10cf1 - PM10 concentration in μg/m3 (corrected to standard conditions)
	pm1_0 - PM1.0 concentration in μg/m3 (under atmospheric conditions)
	pm2_5 - PM2.5 concentration in μg/m3 (under atmospheric conditions)
	pm10 - PM10 concentration in μg/m3 (under atmospheric conditions)
	n0_3 - number of particles with diameter greater than 0.3 μm (in 100 ml of air)
	n0_5 - number of particles with diameter greater than 0.5 μm (in 100 ml of air)
	n1_0 - number of particles with diameter greater than 1.0 μm (in 100 ml of air)
	n2_5 - number of particles with diameter greater than 2.5 μm (in 100 ml of air)
	n5_0 - number of particles with diameter greater than 5.0 μm (in 100 ml of air)
	n10 - number of particles with diameter greater than 10 μm (in 100 ml of air)
 
	Air quality index calculations from https://en.wikipedia.org/wiki/Air_quality_index#Computing_the_AQI
	'''

	meta_data = {
		"name": "Air Quality Monitor",
		"description": "Monitors air quality using a pms5003, pms7003 or pmsa003",
		"module": "allsky_pmsx003",
		"version": "v1.0.2",
		"events": [
			"periodic",
			"day",
			"night"
		],
		"experimental": "false",
		"centersettings": "false",
		"testable": "true",
		"extradatafilename": "allsky_pmsx003.json",
		"group": "Data Sensor",
        "graphs": {
            "chart1": {
				"icon": "fas fa-scale-balanced",
				"title": "Air Quality",
				"group": "Environment",
				"main": "true",    
				"config": {
					"chart": {
						"type": "spline",
						"zooming": {
							"type": "x"
						}
					},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
					},
					"title": {
						"text": "Air Quality"
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
								"text": "Particle Count"
							} 
						}
					]
				},
				"series": {
					"1um": {
						"name": "1um",
						"yAxis": 0,
						"variable": "AS_N1_0"                 
					},
					"25um": {
						"name": "2.5um",
						"yAxis": 0,
						"variable": "AS_N2_5"
					},
					"5um": {
						"name": "5um",
						"yAxis": 0,
						"variable": "AS_N5_0"
					},
					"10um": {
						"name": "10um",
						"yAxis": 0,
						"variable": "AS_N10"
					}           
				}
			}
		},  
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_airquality",
				"include_all": "true"    
			},      
			"values": {
				"AS_PM1_0CF1": {
					"name": "${PM1_0CF1}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM1.0 concentration in μg/m3 (corrected to standard conditions)",
					"type": "number"
				},
				"AS_PM2_5CF1": {
					"name": "${PM2_5CF1}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM2.5 concentration in μg/m3 (corrected to standard conditions)",
					"type": "number"
				},
				"AS_PM10CF1": {
					"name": "${PM10CF1}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM10 concentration in μg/m3 (corrected to standard conditions)",
					"type": "number"
				},
				"AS_PM1_0": {
					"name": "${PM1_0}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM1.0 concentration in μg/m3 (under atmospheric conditions)",
					"type": "number"
				},
				"AS_PM2_5": {
					"name": "${PM2_5}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM2.5 concentration in μg/m3 (under atmospheric conditions)",
					"type": "number"
				},
				"AS_PM10": {
					"name": "${PM10}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "PM10 concentration in μg/m3 (under atmospheric conditions)",
					"type": "number"
				},
				"AS_N0_3": {
					"name": "${N0_3}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 0.3 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_N0_5": {
					"name": "${N0_5}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 0.5 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_N1_0": {
					"name": "${N1_0}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 1.0 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_N2_5": {
					"name": "${N2_5}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 2.5 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_N5_0": {
					"name": "${N5_0}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 5.0 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_N10": {
					"name": "${N10}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Number of particles with diameter greater than 10 μm (in 100 ml of air)",
					"type": "number"
				},
				"AS_AQI": {
					"name": "${AQI}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Air quality index",
					"type": "number"
				},
				"AS_AQI_TEXT": {
					"name": "${AQI_TEXT}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Air quality index, Human Readable",
					"type": "string"
				}                                    
			}                         
		},
		"arguments":{
			"serialport": "serial0"
			
		},
		"argumentdetails": {
			"serialport": {
				"required": "false",
				"description": "Serial port",
				"tab": "Home",
				"help": "The serial port the sensor is connected to",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=SerialPorts",
					"placeholder": "Select a serial port"
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

	_AQI_DATA = (
		(0, 50),
		(51, 100),
		(101, 150),
		(151, 200),
		(201, 300),
		(301, 400),
		(401, 500),
	)

	_PM2_5_DATA = (
		(0, 12),
		(12.1, 35.4),
		(35.5, 55.4),
		(55.5, 150.4),
		(150.5, 250.4),
		(250.5, 350.4),
		(350.5, 500.4),
	)

	_PM10_0_DATA = (
		(0, 54),
		(55, 154),
		(155, 254),
		(255, 354),
		(355, 424),
		(425, 504),
		(505, 604),
	)
    
	def _PM2_5(self, data):
		return self._calculate_aqi(self._PM2_5_DATA, data)

	def _PM10_0(self, data):
		return self._calculate_aqi(self._PM10_0_DATA, data)

	def _calculate_aqi(self, breakpoints, data):
		for index, data_range in enumerate(breakpoints):
			if data <= data_range[1]:
				break

		i_low, i_high = self._AQI_DATA[index]
		C_low, c_high = data_range
		return (i_high - i_low) / (c_high - C_low) * (data - C_low) + i_low

	def _get_air_quality_text(self, air_quality_index):
		if air_quality_index <= 50:
			return 'Good'
		elif air_quality_index <= 100:
			return 'Moderate'
		elif air_quality_index <= 150:
			return 'Unhealthy for Sensitive Groups'
		elif air_quality_index <= 200:
			return 'Unhealthy'
		elif air_quality_index <= 300:
			return 'Very Unhealthy'
		else:
			return 'Hazardous'
    
	def _air_quality_index(self, pm2_5_atm, pm10_0_atm):
		pm2_5 = self._PM2_5(pm2_5_atm)
		pm10_0 = self._PM10_0(pm10_0_atm)
		return max(pm2_5, pm10_0)
        
	def run(self):
		extra_data = {}
		serial_port = self.get_param('serialport', 'serial0', str, True)   

		allsky_shared.log(4, f'INFO: Using device "/dev/{serial_port}"')
		try:
			sensor = Pms7003Sensor(f'/dev/{serial_port}')
  
			sensor_values = sensor.read()
			for key, value in sensor_values.items():
				extra_data[f'AS_{key.upper()}'] = value

			air_quality_index = self._air_quality_index(extra_data['AS_PM2_5'], extra_data['AS_PM10'])
			air_quality_index_text = self._get_air_quality_text(air_quality_index)
		
			extra_data['AS_AQI'] = air_quality_index
			extra_data['AS_AQI_TEXT'] = air_quality_index_text
			allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
			result = f'Sensor Data read and written the the {self.meta_data["extradatafilename"]} extra data file'
			allsky_shared.log(4, f'INFO: {result}')
		except PmsSensorException:
			result = 'Cannot connect to the sensor'
			allsky_shared.log(0, f'ERROR: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}'
			allsky_shared.log(0, f'ERROR: {result}')      

		return result

def pmsx003(params, event):
	allsky_pmsx003 = ALLSKYPMSX003(params, event)
	result = allsky_pmsx003.run()

	return result   
    
def pmsx003_cleanup():
	module_data = {
	    "metaData": ALLSKYPMSX003.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYPMSX003.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(module_data)