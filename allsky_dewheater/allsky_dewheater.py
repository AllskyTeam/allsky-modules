"""
Allsky module.

Modules in this directory are part of the Allsky post-processing and control
system. They are loaded by the Allsky module runner, configured through module
metadata, and can publish data for overlays, history, and database storage.
Each module is responsible for one focused piece of behaviour and is designed
to fit into the wider Allsky pipeline without requiring direct changes to the
core application.

This module provides dew heater control using Allsky environment data. Its job
is to keep a dome, window, or protective cover above the dew point so that
condensation does not form. It supports simple on/off control, variable PWM
control, manual override modes, startup and runtime safety limits, and the
export of overlay and database values describing the heater state.

The control logic is built around the *dew margin*:

``dew margin = ambient temperature - dew point``

As the dew margin shrinks, the risk of condensation increases. In automatic
modes the heater responds to that margin rather than to temperature alone,
which makes the behaviour much more useful in real conditions. The module also
includes hysteresis, PWM shaping, smoothing, fault handling, and minimum
on/off timers so that the heater behaves like a stable controller rather than
a simple threshold switch.
"""

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import time
import subprocess
from meteocalc import heat_index
from meteocalc import dew_point

class ALLSKYDEWHEATER(ALLSKYMODULEBASE):
	"""
	Dew heater controller module.

	The class is configured almost entirely from ``meta_data`` so the Module
	Editor can build the UI automatically. At runtime the module reads Allsky
	environment variables, determines the current dew margin, decides on the
	required heater output, applies that output through the GPIO API, and then
	writes a detailed state snapshot into Allsky extra data and dew heater
	history.

	High-level behaviour:

	- ``auto_onoff`` uses hysteresis around the configured on/off margins.
	- ``auto_pwm`` uses the same dew-margin logic but maps the margin onto a PWM
	  curve.
	- ``manual_off``, ``manual_on``, and ``manual_pwm`` bypass the automatic
	  decision making and force a known output.
	- Safety and stability features such as maximum heater time, minimum
	  on/off time, sensor smoothing, startup grace, and sensor fault handling
	  are applied around the core control mode.
	"""

	meta_data = {
		"name": "Dew Heater Control",
		"description": "Control a dew heater via a temperature and humidity sensor",
		"module": "allsky_dewheater",
		"version": "v2.0.0",
		"events": [
			"periodic",
			"day",
			"night"
		],
		"experimental": "false",
		"testable": "true",
		"centersettings": "false",
		"dependency": "allsky_temp.py",
		"group": "Environment Control",  
		"extradatafilename": "allsky_dew.json",
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_dewheater",
    			"pk": "id",
    			"pk_type": "int",    
    			"include_all": "true"
			},
			"values": {
				"AS_DEWCONTROLSENSOR": {
					"name": "${DEWCONTROLSENSOR}",
					"format": "",
					"sample": "",                
					"group": "Dew Heater",
					"description": "Dew Heater Sensor",
					"type": "string"
				},              
				"AS_DEWCONTROLAMBIENT": {
					"name": "${DEWCONTROLAMBIENT}",
					"format": "{dp=2|deg|temp_unit}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Ambient",
					"type": "temperature"
				},
				"AS_DEWCONTROLDEW": {
					"name": "${DEWCONTROLDEW}",
					"format": "{dp=2|deg|temp_unit}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew heater Dew Point",
					"type": "temperature"
				},
				"AS_DEWCONTROLMARGIN": {
					"name": "${DEWCONTROLMARGIN}",
					"format": "{dp=2|deg|temp_unit}",
					"sample": "",
					"group": "Dew Heater",
					"description": "Dew Heater Margin",
					"type": "temperature"
				},
				"AS_DEWCONTROLHUMIDITY": {
					"name": "${DEWCONTROLHUMIDITY}",
					"format": "{dp=2|per}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Humidity",
					"type": "number"
				},
				"AS_DEWCONTROLHEATER": {
					"name": "${DEWCONTROLHEATER}",
					"format": "{onoff}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Status",
					"type": "gpio"
				},
				"AS_DEWCONTROLLIMIT": {
					"name": "${DEWCONTROLLIMIT}",
					"format": "{onoff}",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Limit",
					"type": "number"
				},    
				"AS_DEWCONTROLHEATERINT": {
					"name": "${DEWCONTROLHEATERINT}",
					"format": "",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Status (int)",
					"type": "number"
				},
				"AS_DEWCONTROLPRESSURE": {
					"name": "${DEWCONTROLPRESSURE}",
					"format": "",
					"sample": "",                 
					"group": "Dew Heater",
					"description": "Dew Heater Pressure",
					"type": "pressure"
				},
				"AS_DEWCONTROLRELHUMIDITY": {
					"name": "${DEWCONTROLRELHUMIDITY}",
					"format": "{dp=2|per}",
					"sample": "",                  
					"group": "Dew Heater",
					"description": "Dew Heater Relative Humidity",
					"type": "number"
				},
				"AS_DEWCONTROLALTITUDE": {
					"name": "${DEWCONTROLALTITUDE}",
					"format": "",
					"sample": "",                   
					"group": "Dew Heater",
					"description": "Dew Heater Altitude",
					"type": "altitude"
				},
				"AS_DEWCONTROLPWMDUTYCYCLE": {
					"name": "${DEWCONTROLPWMDUTYCYCLE}",
					"format": "{dp=0|per}",
					"sample": "",                   
					"group": "Dew Heater",
					"description": "Dew Heater Duty Cycle",
					"type": "number"
				},
				"AS_DEWCONTROLPWMPERCENT": {
					"name": "${DEWCONTROLPWMPERCENT}",
					"format": "",
					"sample": "",                   
					"group": "Dew Heater",
					"description": "Dew Heater PWM %",
					"type": "number"
				}    
			}                         
		},
		"arguments":{
			"type": "None",
			"heaterpin": "",
			"settingslevel": "basic",
			"controlmode": "auto_onoff",
			"temperature": "AS_TEMP",
			"humidity": "AS_HUMIDITY",
			"heaterstartupstate": "OFF",
			"invertgpio": "False",
			"frequency": "0",
			"force": "0",
			"max": "0",
			"daydisable": "False",
			"dewmarginon": 3,
			"dewmarginoff": 4,
			"marginbias": 0,
			"fullheatmargin": 0.5,
			"minpwmpercent": 20,
			"maxpwmpercent": 100,
			"daymaxpwmpercent": 0,
			"minpwmchangepercent": 5,
			"manualpwmpercent": 0,
			"pwmcurve": "quadratic",
			"sensorfaultaction": "off",
			"minimumheatpercent": 20,
			"minimumontime": 0,
			"minimumofftime": 0,
			"sensoralpha": 0.3,
			"startupgraceperiod": 0,
			"enabledebug": "False",
			"debugtemperature": 0,
			"debugdewpoint": 0
		},
		"argumentdetails": {
			"type" : {
				"required": "false",
				"description": "Sensor Type",
				"help": "The type of sensor being used.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "select",
					"values": "None,Allsky|Allsky,allsky-sensor|Allsky Sensor",
					"default": "None"
				}
			},
			"temperature": {
				"required": "false",
				"description": "Temperature Variable",
				"help": "The Variable to use for the temperature.",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable",
					"selectmode": "multi"
				}                             
			},
			"humidity": {
				"required": "false",
				"description": "Humidity Variable",
				"help": "The Variable to use for the humidity.",
				"tab": "Sensor",
				"filters": {
					"filter": "type",
					"filtertype": "show",
					"values": [
						"Allsky"
					]
				},            
				"type": {
					"fieldtype": "variable"
				}                                         
			},
			"heaterpin": {
				"required": "false",
				"description": "Heater Pin",
				"help": "The GPIO pin used to control the heater",
				"tab": "Heater",
				"type": {
					"fieldtype": "gpio"
				}
			},
			"settingslevel" : {
				"required": "false",
				"description": "Setting Level",
				"help": "Choose whether to show the basic settings only or the full advanced tuning options.",
				"tab": "Heater",
				"type": {
					"fieldtype": "select",
					"values": "basic|Basic,advanced|Advanced",
					"default": "basic"
				}
			},
			"controlmode" : {
				"required": "false",
				"description": "Control Mode",
				"help": "Choose automatic on/off, automatic PWM, or a manual override mode.",
				"tab": "Heater",
				"type": {
					"fieldtype": "select",
					"values": "auto_onoff|Automatic On/Off,auto_pwm|Automatic PWM,manual_off|Manual Off,manual_on|Manual On,manual_pwm|Manual PWM",
					"default": "auto_onoff"
				}
			},
			"manualpwmpercent" : {
				"required": "false",
				"description": "Manual PWM %",
				"help": "Manual PWM duty cycle percentage used when control mode is set to manual_pwm.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": {
					"filter": "controlmode",
					"filtertype": "show",
					"values": [
						"manual_pwm"
					]
				}
			},
			"dewmarginon" : {
				"required": "false",
				"description": "Turn Heater On At",
				"help": "Turn the heater on when ambient temperature minus dew point is at or below this value.",
				"tab": "Heater",
				"layout": {
					"row": "heater-thresholds",
					"title": "Dew Margins",
					"label": "Turn On At",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": -20,
					"max": 50,
					"step": 0.1
				},
				"filters": {
					"filter": "controlmode",
					"filtertype": "show",
					"values": [
						"auto_onoff",
						"auto_pwm"
					]
				}
			},
			"dewmarginoff" : {
				"required": "false",
				"description": "Turn Heater Off Above",
				"help": "Turn the heater off when ambient temperature minus dew point rises above this value. Set this higher than the turn-on value to prevent rapid switching.",
				"tab": "Heater",
				"layout": {
					"row": "heater-thresholds",
					"title": "Dew Margins",
					"label": "Turn Off Above",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": -20,
					"max": 50,
					"step": 0.1
				},
				"filters": {
					"filter": "controlmode",
					"filtertype": "show",
					"values": [
						"auto_onoff",
						"auto_pwm"
					]
				}
			},
			"marginbias" : {
				"required": "false",
				"description": "Margin Bias",
				"help": "Adjust the effective dew margin used by the controller. Positive values make the heater respond more aggressively.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": -20,
					"max": 20,
					"step": 0.1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_onoff",
							"auto_pwm"
						]
					}
				]
			},
			"fullheatmargin" : {
				"required": "false",
				"description": "Full Heat Margin",
				"help": "At or below this ambient-minus-dew-point margin the PWM duty cycle will use the maximum PWM percentage.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": -20,
					"max": 20,
					"step": 0.1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"minpwmpercent" : {
				"required": "false",
				"description": "Min PWM %",
				"help": "Minimum PWM duty cycle to apply when PWM control is active.",
				"tab": "Heater",
				"layout": {
					"row": "heater-pwm-range",
					"title": "PWM Range",
					"label": "Min PWM %",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"maxpwmpercent" : {
				"required": "false",
				"description": "Max PWM %",
				"help": "Maximum PWM duty cycle to apply when the heater is at full output.",
				"tab": "Heater",
				"layout": {
					"row": "heater-pwm-range",
					"title": "PWM Range",
					"label": "Max PWM %",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"daymaxpwmpercent" : {
				"required": "false",
				"description": "Max Daytime PWM %",
				"help": "Maximum PWM duty cycle allowed during the day. Set to 0 to disable the daytime cap.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"minpwmchangepercent" : {
				"required": "false",
				"description": "Minimum PWM Change %",
				"help": "Only change the PWM output when the requested change is at least this large. Set to 0 to disable.",
				"tab": "Heater",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"pwmcurve" : {
				"required": "false",
				"description": "PWM Curve",
				"help": "Select how aggressively PWM ramps up as the ambient temperature approaches the dew point.",
				"tab": "Heater",
				"type": {
					"fieldtype": "select",
					"values": "linear,quadratic,aggressive",
					"default": "quadratic"
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_pwm"
						]
					}
				]
			},
			"heaterstartupstate" : {
				"required": "false",
				"description": "heater Startup State",
				"help": "The initial state of the dew heater when allsky is started. Only needed if there is no previous status.",
				"tab": "Heater",
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_onoff",
							"auto_pwm"
						]
					}
				],
				"type": {
					"fieldtype": "select",
					"values": "ON,OFF",
					"default": "OFF"
				}
			},
			"invertgpio" : {
				"required": "false",
				"description": "Invert GPIO",
				"help": "Select this option if the GPIO output should be inverted so the heater activates when the GPIO pin goes low.",
				"tab": "Heater",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"frequency" : {
				"required": "false",
				"description": "Delay",
				"help": "The delay between sensor reads in seconds. Zero disables this and runs the check every time the module runs.",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 1000,
					"step": 1
				}
			},
			"force" : {
				"required": "false",
				"description": "Forced Temperature",
				"help": "Always enable the heater when the ambient termperature is below this value; 0 disables this.",
				"tab": "Dew Control",
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "controlmode",
						"filtertype": "show",
						"values": [
							"auto_onoff",
							"auto_pwm"
						]
					}
				],
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"sensorfaultaction" : {
				"required": "false",
				"description": "Sensor Fault Action",
				"help": "Choose what the module should do if it cannot read a valid temperature or dew point value.",
				"tab": "Dew Control",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "select",
					"values": "off|Turn Off,keep_last|Keep Last State,minimum_heat|Use Minimum Heat",
					"default": "off"
				}
			},
			"minimumheatpercent" : {
				"required": "false",
				"description": "Minimum Heat %",
				"help": "When sensor fault action is set to minimum heat, use this PWM percentage. In on/off mode any non-zero value means heater on.",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 100,
					"step": 1
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "sensorfaultaction",
						"filtertype": "show",
						"values": [
							"minimum_heat"
						]
					}
				]
			},
			"max" : {
				"required": "false",
				"description": "Max Heater Time",
				"help": "The maximum time in seconds for the heater to be on. 0 disables this.",
				"tab": "Dew Control",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 86400,
					"step": 1
				}
			},
			"minimumontime" : {
				"required": "false",
				"description": "Minimum On Time",
				"help": "Minimum number of seconds the heater should stay on before it is allowed to turn off. Set to 0 to disable.",
				"tab": "Dew Control",
				"layout": {
					"row": "heater-min-times",
					"title": "Minimum Times",
					"label": "On Time",
					"width": 4
				},
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 86400,
					"step": 1
				}
			},
			"minimumofftime" : {
				"required": "false",
				"description": "Minimum Off Time",
				"help": "Minimum number of seconds the heater should stay off before it is allowed to turn on again. Set to 0 to disable.",
				"tab": "Dew Control",
				"layout": {
					"row": "heater-min-times",
					"title": "Minimum Times",
					"label": "Off Time",
					"width": 4
				},
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 86400,
					"step": 1
				}
			},
			"sensoralpha" : {
				"required": "false",
				"description": "Sensor Smoothing",
				"help": "Applies EMA (Exponential Moving Average) smoothing to temperature and dew point so the heater does not react too strongly to noisy sensor readings. Each new reading is blended with the previous smoothed value. 0 disables smoothing, lower values give steadier but slower response, and higher values follow new readings more quickly.",
				"tab": "Dew Control",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 1,
					"step": 0.05
				}
			},
			"startupgraceperiod" : {
				"required": "false",
				"description": "Startup Grace Period",
				"help": "Number of seconds after startup during which the current heater state will be preserved in automatic modes. Set to 0 to disable.",
				"tab": "Dew Control",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 3600,
					"step": 1
				}
			},
			"daydisable" : {
				"required": "false",
				"description": "Daytime Disable",
				"help": "Check to disable the dew control module during the daytime.",
				"tab": "Dew Control",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"enabledebug" : {
				"required": "false",
				"description": "Set Debug Mode",
				"help": "Check to use the other values on this tab rather than values read from any sensor.",
				"tab": "Debug",
				"filters": {
					"filter": "settingslevel",
					"filtertype": "show",
					"values": [
						"advanced"
					]
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debugtemperature": {
				"required": "false",
				"description": "Temperature Value",
				"help": "The Variable to use for the temperature.",
				"tab": "Debug",
				"layout": {
					"row": "debug-values",
					"title": "Debug Values",
					"label": "Temperature",
					"width": 4
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "enabledebug",
						"filtertype": "show",
						"values": [
							"enabledebug"
						]
					}
				],
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
				}
			},
			"debugdewpoint": {
				"required": "false",
				"description": "Dewpoint value",
				"help": "The Variable to use for the dew point.",
				"tab": "Debug",
				"layout": {
					"row": "debug-values",
					"title": "Debug Values",
					"label": "Dewpoint",
					"width": 4
				},
				"filters": [
					{
						"filter": "settingslevel",
						"filtertype": "show",
						"values": [
							"advanced"
						]
					},
					{
						"filter": "enabledebug",
						"filtertype": "show",
						"values": [
							"enabledebug"
						]
					}
				],
				"type": {
					"fieldtype": "spinner",
					"min": -100,
					"max": 100,
					"step": 1
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
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.1" : [
				{
					"author": "Damian Grocholski (Mr-Groch)",
					"authorurl": "https://github.com/Mr-Groch",
					"changes": [
						"Added extra pin that is triggered with heater pin",
						"Fixed dhtxxdelay (was not implemented)",
						"Fixed max heater time (was not implemented)"
					]
				}
			],
			"v1.0.2" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updated code for Pi 5"
				}
			],
			"v1.0.3" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Add AHTx0 i2c sensor"
				},            
				{
					"author": "Andreas Schminder",
					"authorurl": "https://github.com/Adler6907",
					"changes": "Added Solo Cloudwatcher"
				}
			],
			"v1.0.4" : [
				{
					"author": "Andreas Schminder",
					"changes": "Added Solo Cloudwatcher"
				}
			],
			"v1.0.5" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added OpenWeather option"
				}
			],
			"v1.0.6" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added option to disable heater during the day"
				}
			],
			"v1.0.7" : [
				{
					"author": "Damian Grocholski (Mr-Groch)",
					"authorurl": "https://github.com/Mr-Groch",
					"changes": [
						"Refactored tabs for easier use",
						"Added Allsky as data source option"
					]
				}
			],
			"v1.0.8" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Refactored for new module and variable system",
						"Added PWM Control for heater pins"
					]
				}
			],
			"v2.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Removed all Sensors, uses Environment module now",
						"Complete refactor of all code to improve pwm"
					]
				}
			]                                             
		}
	}

	def _run_command (self, cmd):
		"""Run a shell command and return ``(returncode, stdout, stderr)``."""
		proc = subprocess.Popen(cmd,
								stdout=subprocess.PIPE,
								stderr=subprocess.PIPE,
								shell=True,
								universal_newlines=True)
		std_out, std_err = proc.communicate()
		return proc.returncode, std_out, std_err

	def _get_time_of_day(self):
		"""
		Determine whether Allsky currently considers it day or night.

		The module uses ``sunwait`` with the configured site latitude, longitude,
		and sun angle. The return code is mapped into ``"day"``, ``"night"``, or
		``"Unknown"`` if the command cannot be evaluated.
		"""
		angle = allsky_shared.get_setting('angle')
		lat = allsky_shared.get_setting('latitude')
		lon = allsky_shared.get_setting('longitude')
		tod = 'Unknown'

		try:
			cmd = f'sunwait poll exit set angle {angle} {lat} {lon}'
			returncode, stdout, stderr = self._run_command(cmd)
			
			if returncode == 2:
				tod = 'day'
			if returncode == 3:
				tod = 'night'
		except Exception:
			self.log(0, f'ERROR in {__file__} running {cmd}')
		return tod 

	def _create_cardinal(self, degrees):
		"""Convert a wind bearing in degrees into a cardinal direction string."""
		try:
			cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
			cardinal = cardinals[round(degrees / 22.5)]
		except Exception:
			cardinal = 'N/A'

		return cardinal

	def _set_extra_value(self, path, data, extraKey, expires, extraData):
		"""Copy a value from a nested data structure into an extra-data payload."""
		value = self._get_value(path, data)
		if value is not None:
			extraData["AS_" + extraKey] = {
				"value": value,
				"expires": expires
			}

	def _get_value(self, path, data):
		"""Resolve a dotted key path from a small nested structure."""
		result = None
		keys = path.split(".")
		if keys[0] in data:
			subData = data[keys[0]]
			
			if isinstance(subData, list):        
				if keys[1] in subData[0]:
					result = subData[0][keys[1]]
			else:
				if keys[1] in subData:
					result = subData[keys[1]]

		return result

	def _read_allsky(self):
		"""
		Read temperature-related values from the Environment module outputs.

		This is the preferred and current sensor source for the dew heater. The
		module expects the Environment module to have already published the usual
		Allsky variables such as ambient temperature, humidity, dew point,
		pressure, and altitude.
		"""
		temperature = None
		humidity = None
		dew_point = None
		heat_index = None
		pressure = None
		rel_humidity = None
		altitude = None

		# TODO: Check this logic

		environment_data = allsky_shared.load_extra_data_file('allskytemp.json')
		temperature = allsky_shared.get_allsky_variable('AS_TEMP')
		humidity = allsky_shared.get_allsky_variable('AS_HUMIDITY')
		dew_point = allsky_shared.get_allsky_variable('AS_DEW')
		heat_index = allsky_shared.get_allsky_variable('AS_HEATINDEX')
		pressure = allsky_shared.get_allsky_variable('AS_PRESSURE')
		rel_humidity = allsky_shared.get_allsky_variable('AS_RELHUMIDITY')
		altitude = allsky_shared.get_allsky_variable('AS_ALTITUDE')
		if temperature is not None:
			temperature = float(temperature)
		if humidity is not None:
			humidity = float(humidity)
		if dew_point is not None:
			dew_point = float(dew_point)
		if heat_index is not None:
			heat_index = float(heat_index)
		if pressure is not None:
			pressure = float(pressure)
		if rel_humidity is not None:
			rel_humidity = float(rel_humidity)
		if altitude is not None:
			altitude = float(altitude)

		if temperature is None:
			self.log(0, f'ERROR failed to read the Allsky Core temperature. Is the Environment module installed and configured?')
    
		return temperature, humidity, pressure, rel_humidity, altitude

	def _percent_to_duty_cycle(self, percent):
		"""Convert a 0-100 percentage into the 16-bit duty cycle used by the GPIO API."""
		percent = max(0.0, min(100.0, float(percent)))
		return int(round((percent / 100.0) * 65535))

	def _resolve_control_mode(self, control_mode, use_pwm):
		"""Normalise the configured control mode.

		The method currently returns the supplied value unchanged, but exists as a
		single place to preserve compatibility if future migrations or legacy mode
		mappings are needed again.
		"""
		return control_mode

	def _is_pwm_mode(self, control_mode):
		"""Return ``True`` when the current control mode expects PWM output."""
		return control_mode in ['auto_pwm', 'manual_pwm']

	def _heater_is_on(self):
		"""Check the persisted heater state used for timing and hysteresis decisions."""
		return allsky_shared.db_has_key('dewheaterontime')

	def _mark_heater_on(self):
		"""Persist the start time of the current heater-on period."""
		if not self._heater_is_on():
			now = int(time.time())
			allsky_shared.db_add('dewheaterontime', now)

	def _mark_heater_off(self):
		"""Persist the end of the current heater-on period and record the off time."""
		if self._heater_is_on():
			allsky_shared.db_delete_key('dewheaterontime')
		now = int(time.time())
		if allsky_shared.db_has_key('dewheaterofftime'):
			allsky_shared.db_update('dewheaterofftime', now)
		else:
			allsky_shared.db_add('dewheaterofftime', now)

	def _set_last_duty_cycle(self, duty_cycle):
		"""Persist the most recently applied PWM duty cycle."""
		if allsky_shared.db_has_key('dewheaterlastduty'):
			allsky_shared.db_update('dewheaterlastduty', int(duty_cycle))
		else:
			allsky_shared.db_add('dewheaterlastduty', int(duty_cycle))

	def _get_last_duty_cycle(self):
		"""Return the last duty cycle written by the controller."""
		if allsky_shared.db_has_key('dewheaterlastduty'):
			return int(allsky_shared.db_get('dewheaterlastduty'))

		return 0

	def _get_db_age(self, key):
		"""Return the age, in seconds, of a timestamp stored in the module database."""
		if allsky_shared.db_has_key(key):
			return int(time.time()) - int(allsky_shared.db_get(key))

		return None

	def _ensure_startup_time(self):
		"""Create and return a stable startup timestamp for the current Allsky run."""
		now = int(time.time())
		if allsky_shared.db_has_key('dewheaterstarttime'):
			return int(allsky_shared.db_get('dewheaterstarttime'))

		allsky_shared.db_add('dewheaterstarttime', now)
		return now

	def _effective_dew_margin(self, dew_margin):
		"""
		Apply the configured controller bias to the measured dew margin.

		A positive bias makes the controller more aggressive because it reduces the
		effective margin seen by the decision logic.
		"""
		margin_bias = self.get_param('marginbias', 0, float)
		return dew_margin - margin_bias

	def _smooth_value(self, key, value, alpha):
		"""
		Apply exponential moving average smoothing to a sensor value.

		The smoothed value is stored in the module database so it persists between
		module invocations.
		"""
		alpha = max(0.0, min(1.0, float(alpha)))
		if alpha <= 0:
			return value

		if allsky_shared.db_has_key(key):
			previous = float(allsky_shared.db_get(key))
			smoothed = (alpha * float(value)) + ((1 - alpha) * previous)
			allsky_shared.db_update(key, smoothed)
		else:
			smoothed = float(value)
			allsky_shared.db_add(key, smoothed)

		return smoothed

	def _apply_pwm_change_deadband(self, target_percent, currently_on):
		"""
		Suppress very small PWM changes when the heater is already running.

		This reduces unnecessary output rewrites caused by noisy readings or tiny
		controller adjustments that have no practical effect on heater behaviour.
		"""
		min_change = self.get_param('minpwmchangepercent', 5, float)
		if min_change <= 0 or not currently_on or target_percent <= 0:
			return target_percent

		current_percent = round((self._get_last_duty_cycle() / 65535) * 100, 2)
		if current_percent <= 0:
			return target_percent

		if abs(target_percent - current_percent) < min_change:
			return current_percent

		return target_percent

	def _apply_day_pwm_cap(self, target_percent, tod):
		"""Limit PWM output during daytime operation when a daytime cap is configured."""
		max_day_pwm_percent = self.get_param('daymaxpwmpercent', 0, float)
		if tod == 'day' and max_day_pwm_percent > 0:
			return min(target_percent, max_day_pwm_percent)

		return target_percent

	def _can_turn_on(self, currently_on, startup_grace_active):
		"""Return ``True`` if the heater is allowed to transition from off to on now."""
		if currently_on:
			return False
		if startup_grace_active:
			return False

		minimum_off_time = self.get_param('minimumofftime', 0, int)
		last_off_age = self._get_db_age('dewheaterofftime')
		if minimum_off_time > 0 and last_off_age is not None and last_off_age < minimum_off_time:
			return False

		return True

	def _can_turn_off(self, currently_on, startup_grace_active):
		"""Return ``True`` if the heater is allowed to transition from on to off now."""
		if not currently_on:
			return False
		if startup_grace_active:
			return False

		minimum_on_time = self.get_param('minimumontime', 0, int)
		last_on_age = self._get_db_age('dewheaterontime')
		if minimum_on_time > 0 and last_on_age is not None and last_on_age < minimum_on_time:
			return False

		return True

	def _calculate_pwm_percent(self, dew_margin):
		"""
		Map the current dew margin onto a PWM percentage.

		The output is shaped by the configured PWM curve and bounded by the
		configured minimum/maximum PWM percentages. Full heat is reached at or
		below ``fullheatmargin`` and zero heat is used above
		``Turn Heater Off Above``.
		"""
		margin_on = self.get_param('dewmarginon', 3, float)
		margin_off = self.get_param('dewmarginoff', 4, float)
		full_heat_margin = self.get_param('fullheatmargin', 0.5, float)
		min_pwm_percent = self.get_param('minpwmpercent', 20, float)
		max_pwm_percent = self.get_param('maxpwmpercent', 100, float)
		pwm_curve = self.get_param('pwmcurve', 'quadratic', str)

		if margin_off < margin_on:
			margin_off = margin_on
		if full_heat_margin > margin_on:
			full_heat_margin = margin_on
		if max_pwm_percent < min_pwm_percent:
			max_pwm_percent = min_pwm_percent

		if dew_margin >= margin_off:
			return 0
		if dew_margin <= full_heat_margin:
			return max_pwm_percent

		span = margin_off - full_heat_margin
		if span <= 0:
			return max_pwm_percent

		x = (dew_margin - full_heat_margin) / span
		x = max(0.0, min(1.0, x))

		if pwm_curve == 'linear':
			shaped = 1.0 - x
		elif pwm_curve == 'aggressive':
			shaped = 1.0 - (x * x * x)
		else:
			shaped = 1.0 - (x * x)

		return min_pwm_percent + (shaped * (max_pwm_percent - min_pwm_percent))

	def _set_pwm_state(self, heater_pin, duty_cycle):
		"""Send a PWM update to the Allsky GPIO API."""
		result = allsky_shared.set_pwm(heater_pin, duty_cycle, "Dew")

		return result

	def _set_gpio_pin_state(self, state, invert_gpio, heater_pin):
		"""Send a digital on/off update to the Allsky GPIO API."""
		if invert_gpio:
			state = not state

		result = allsky_shared.set_gpio_pin(heater_pin, state, "Dew")

		return result

	def _turn_heater_on(self, heater_pin, invert_gpio, extra=False, use_pwm=False, duty_cycle=0):
		"""
		Turn the main or extra heater output on.

		When PWM is active the given duty cycle is sent unchanged. When PWM is not
		active the method uses a digital output and records a full-scale duty cycle
		for consistency in the module database.
		"""
		if extra:
			type = 'Extra'
		else:
			type = 'Heater'

		if use_pwm:
			duty_cycle_percent = round((duty_cycle / 65535) * 100,2)
		
			result = f'Turning {type} on using PWM on pin {heater_pin}. Duty Cycle {duty_cycle} ({duty_cycle_percent}%)'
			self.log(4, f'INFO: {result}')
			self._set_pwm_state(heater_pin, duty_cycle)
			if not extra:
				self._set_last_duty_cycle(duty_cycle)
				self._mark_heater_on()
		else:
			if self._set_gpio_pin_state(1, invert_gpio, heater_pin):
				if not extra:
					self._set_last_duty_cycle(65535)
					self._mark_heater_on()
				self.log(4, f'INFO: Turning {type} on using pin {heater_pin}')
			else:
				result = f'ERROR in {__file__}: (Heater On) Failed to set Digital IO to output. Check that pigpiod is running.'
				self.log(0, result)

	def _turn_heater_off(self, heater_pin, invert_gpio, extra=False, use_pwm=False):
		"""
		Turn the main or extra heater output off.

		For PWM outputs this writes a zero-duty update. For digital outputs it
		drives the GPIO to the inactive state and clears the persisted heater
		timing state.
		"""
		if extra:
			type = 'Extra'
		else:
			type = 'Heater'
						

		if use_pwm:
			self.log(4, f'INFO: Turning {type} off using PWM on pin {heater_pin}.')
			self._set_pwm_state(heater_pin, 0)
			if not extra:
				self._set_last_duty_cycle(0)
				self._mark_heater_off()
		else:  
			if self._set_gpio_pin_state(0, invert_gpio, heater_pin):
				if not extra:
					self._set_last_duty_cycle(0)
					self._mark_heater_off()
				self.log(4, f'INFO: Turning {type} off using pin {heater_pin}')
			else:
				result = f'ERROR in {__file__}: (Heater Off) Failed to set Digital IO to output. Check that pigpiod is running.'
				self.log(0, result)

	def _get_sensor_reading(self, sensor_type, input_pin, i2c_address, dhtxx_retry_count, dhtxx_delay, sht31_heater, solo_url, params):
		"""
		Read the current environmental inputs for the controller.

		Although the refactored module is intended to use ``Allsky`` as its sensor
		source, the helper still retains support for several older sensor backends
		and service-based sources for compatibility and testing.
		"""
		temperature = None
		humidity = None
		the_dew_point = None
		the_heat_index = None
		pressure = None
		rel_humidity = None
		altitude = None

		if sensor_type == "SHT31":
			temperature, humidity = self._read_sht31(sht31_heater, i2c_address)
		elif sensor_type == "DHT22" or sensor_type == "DHT11" or sensor_type == "AM2302":
			temperature, humidity = self._read_dht22(input_pin, dhtxx_retry_count, dhtxx_delay)
		elif sensor_type == "BME280-I2C":
			temperature, humidity, pressure, rel_humidity, altitude = self._read_bme280_i2c(i2c_address)
		elif sensor_type == "HTU21":
			temperature, humidity = self._read_htu21(i2c_address)
		elif sensor_type == "AHTx0":
			temperature, humidity = self._read_ahtx0(i2c_address)
		elif sensor_type == "SOLO-Cloudwatcher":
			temperature, humidity, pressure, the_dew_point = self._read_solo(solo_url)
		elif sensor_type == 'OpenWeather':
			temperature, humidity, pressure, the_dew_point = self._read_open_weather(params)
		elif sensor_type == 'Allsky':
			temperature, humidity, pressure, rel_humidity, altitude = self._read_allsky()
		else:
			self.log(0, f'ERROR in {__file__}: No sensor type defined')

		if temperature is not None and humidity is not None:
			the_dew_point = dew_point(temperature, humidity).c
			the_heat_index = heat_index(temperature, humidity).c

			tempUnits = allsky_shared.get_setting('temptype')
			if tempUnits == 'F':
				temperature = (temperature * (9/5)) + 32
				the_dew_point = (the_dew_point * (9/5)) + 32
				the_heat_index = (the_heat_index * (9/5)) + 32
				self.log(4, 'INFO: Converted temperature to F')

			temperature = round(temperature, 2)
			humidity = round(humidity, 2)
			the_dew_point = round(the_dew_point, 2)
			the_heat_index = round(the_heat_index, 2)

		return temperature, humidity, the_dew_point, the_heat_index, pressure, rel_humidity, altitude

	def _get_last_run_time(self):
		"""Return the last dew heater evaluation timestamp, if one exists."""
		last_run = None

		if allsky_shared.db_has_key('dewheaterlastrun'):
			last_run = allsky_shared.db_get('dewheaterlastrun')

		return last_run

	def _debug_output(self, sensor_type, temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude):
		"""Write a single consolidated sensor snapshot to the log."""
		self.log(1, f'INFO: Sensor {sensor_type} read: Temperature {temperature}, Humidity {humidity}, Relative Humidity {rel_humidity}, Dew Point {dew_point}, Heat Index {heat_index}, Pressure {pressure}, Altitude {altitude}')

	def _pwm_high_time(self, frequency, duty_cycle):
		"""Return the theoretical PWM high time for a percentage duty cycle."""
		period = 1 / frequency
		high_time = (duty_cycle / 100) * period
		return high_time
	
	def run(self):
		"""
		Execute one control cycle of the dew heater.

		The run loop performs the following stages:

		1. Read configuration and current runtime context.
		2. Enforce daytime-disable and module frequency rules.
		3. Acquire sensor or debug values.
		4. Smooth and bias the readings where configured.
		5. Evaluate safety limits such as maximum heater time, startup grace, and
		   minimum on/off times.
		6. Apply the selected control mode and determine heater output.
		7. Write the output via the GPIO API.
		8. Publish extra-data and history records for overlays, charts, and
		   diagnostics.

		Returns:
			str: A short status message describing the most recent control decision.
		"""
		result = ""
		sensor_type = self.get_param('type', '', str)
		heater_startup_state = self.get_param('heaterstartupstate', 'OFF', str)
		heater_pin = self.get_param('heaterpin', 0, int)
		extra_pin = self.get_param('extrapin', 0, int)
		control_mode = self.get_param('controlmode', 'auto_onoff', str)
		force = self.get_param('force', 0, int)
		invert_gpio = self.get_param('invertgpio', False, bool)
		invert_extra_pin = self.get_param('invertextrapin', False, bool)
		input_pin = self.get_param('inputpin', 0, int)
		frequency = self.get_param('frequency', 0, int)
		max_on_time = self.get_param('max', 0, int)
		i2c_address = self.get_param('i2caddress', '', str)
		dhtxx_retry_count = self.get_param('dhtxxretrycount', 3, int)
		dhtxx_delay = self.get_param('dhtxxdelay', 0, int)
		sht31_heater = self.get_param('sht31heater', False, bool)
		solo_url = self.get_param('solourl', '', str)
		daytime_disable = self.get_param('daydisable', True, bool)
		manual_pwm_percent = self.get_param('manualpwmpercent', 0, float)
		dew_margin_on = self.get_param('dewmarginon', 3, float)
		dew_margin_off = self.get_param('dewmarginoff', 4, float)
		sensor_fault_action = self.get_param('sensorfaultaction', 'off', str)
		minimum_heat_percent = self.get_param('minimumheatpercent', 20, float)
		sensor_alpha = self.get_param('sensoralpha', 0.3, float)
		startup_grace_period = self.get_param('startupgraceperiod', 0, int)
		debug_mode = self.get_param('enabledebug', False, bool)
		debug_temperature = self.get_param('debugtemperature', 0, int)
		debug_dew_point = self.get_param('debugdewpoint', 0, int)
		control_mode = self._resolve_control_mode(control_mode, False)
		use_pwm = self._is_pwm_mode(control_mode)
		extra_use_pwm = use_pwm if extra_pin != 0 else False
		startup_time = self._ensure_startup_time()
  
		if not debug_mode:
			debug_temperature = 0
			debug_dew_point = 0

		tod = self._get_time_of_day(); 
						
		temperature = 0
		humidity = 0
		dew_point = 0
		heat_index = 0
		heater = False

		ok_to_run = True
		if daytime_disable:
			if tod == 'day':
				ok_to_run = False

		if ok_to_run or debug_mode:            
			should_run, diff = allsky_shared.should_run('allskydew', frequency)    
			if should_run or debug_mode:
				if heater_pin != 0:
					last_run_time = self._get_last_run_time()
					if last_run_time is not None:
						now = int(time.time())
						lastRunSecs = now - last_run_time
						if (lastRunSecs >= frequency) or debug_mode:
							allsky_shared.db_update('dewheaterlastrun', now)
							if not debug_mode:
								temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude = self._get_sensor_reading(sensor_type, input_pin, i2c_address, dhtxx_retry_count, dhtxx_delay, sht31_heater, solo_url, self.params)
							else:
								temperature = debug_temperature
								dew_point = debug_dew_point
								humidity = 0
								heat_index = 0
								pressure = 0
								rel_humidity = 0
								altitude = 0
	         
							if temperature is not None:
								temperature = round(temperature, 2)
							if humidity is not None:
								humidity = round(humidity, 2)
							if dew_point is not None:
								dew_point = round(dew_point, 2)
							if heat_index is not None:
								heat_index = round(heat_index, 2)
							if pressure is not None:
								pressure = round(pressure, 0)
							if rel_humidity is not None:
								rel_humidity = round(rel_humidity, 2)
							if altitude is not None:
								altitude = round(altitude, 0)

							if not debug_mode and temperature is not None and dew_point is not None:
								temperature = round(self._smooth_value('dewheatertempema', temperature, sensor_alpha), 2)
								dew_point = round(self._smooth_value('dewheaterdewema', dew_point, sensor_alpha), 2)

							self._debug_output(sensor_type, temperature, humidity, dew_point, heat_index, pressure, rel_humidity, altitude)
							currently_on = self._heater_is_on()
							current_duty_cycle = self._get_last_duty_cycle()
							last_on_seconds = self._get_db_age('dewheaterontime') or 0
							startup_grace_active = startup_grace_period > 0 and (now - startup_time) < startup_grace_period
							dew_margin = round(temperature - dew_point, 2) if temperature is not None and dew_point is not None else None
							effective_dew_margin = round(self._effective_dew_margin(dew_margin), 2) if dew_margin is not None else None
							duty_cycle = 0
							duty_cycle_percent = 0

							if temperature is None or dew_point is None:
								result = f'Sensor fault detected. Action: {sensor_fault_action}'
								self.log(0, f'WARN: {result}')
								if sensor_fault_action == 'keep_last':
									if currently_on:
										if use_pwm and current_duty_cycle > 0:
											duty_cycle = current_duty_cycle
											duty_cycle_percent = round((duty_cycle / 65535) * 100, 2)
											self._turn_heater_on(heater_pin, invert_gpio, False, True, duty_cycle)
											if extra_pin != 0:
												self._turn_heater_on(extra_pin, invert_extra_pin, True, True, duty_cycle)
										else:
											duty_cycle = self._percent_to_duty_cycle(100)
											duty_cycle_percent = 100
											self._turn_heater_on(heater_pin, invert_gpio, False, False)
											if extra_pin != 0:
												self._turn_heater_on(extra_pin, invert_extra_pin, True, False)
										heater = True
									else:
										self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
										if extra_pin != 0:
											self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
										heater = False
								elif sensor_fault_action == 'minimum_heat':
									duty_cycle_percent = minimum_heat_percent
									if use_pwm:
										duty_cycle = self._percent_to_duty_cycle(duty_cycle_percent)
									else:
										duty_cycle = self._percent_to_duty_cycle(100 if minimum_heat_percent > 0 else 0)
									if duty_cycle > 0:
										self._turn_heater_on(heater_pin, invert_gpio, False, use_pwm, duty_cycle)
										if extra_pin != 0:
											self._turn_heater_on(extra_pin, invert_extra_pin, True, extra_use_pwm, duty_cycle)
										heater = True
									else:
										self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
										if extra_pin != 0:
											self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
										heater = False
								else:
									self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
									if extra_pin != 0:
										self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
									heater = False
							else:
								if startup_grace_active and control_mode in ['auto_onoff', 'auto_pwm']:
									result = f'Startup grace period active for {startup_grace_period}s; preserving current heater state'
									self.log(4, f'INFO: {result}')
									if currently_on:
										if use_pwm:
											duty_cycle = current_duty_cycle if current_duty_cycle > 0 else self._percent_to_duty_cycle(100)
											duty_cycle_percent = round((duty_cycle / 65535) * 100, 2)
											self._turn_heater_on(heater_pin, invert_gpio, False, True, duty_cycle)
											if extra_pin != 0:
												self._turn_heater_on(extra_pin, invert_extra_pin, True, True, duty_cycle)
										else:
											duty_cycle = self._percent_to_duty_cycle(100)
											duty_cycle_percent = 100
											self._turn_heater_on(heater_pin, invert_gpio, False, False)
											if extra_pin != 0:
												self._turn_heater_on(extra_pin, invert_extra_pin, True, False)
										heater = True
									else:
										self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
										if extra_pin != 0:
											self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
										heater = False
								elif max_on_time != 0 and last_on_seconds >= max_on_time:
									result = f'Heater was on longer than maximum allowed time of {max_on_time}'
									self.log(4, f'INFO: {result}')
									self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
									if extra_pin != 0:
										self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
									heater = False
								elif control_mode == 'manual_off':
									result = 'Manual control mode forcing heater off'
									self.log(4, f'INFO: {result}')
									self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
									if extra_pin != 0:
										self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
									heater = False
								elif control_mode == 'manual_on':
									result = 'Manual control mode forcing heater on'
									self.log(4, f'INFO: {result}')
									duty_cycle = self._percent_to_duty_cycle(100)
									duty_cycle_percent = 100
									self._turn_heater_on(heater_pin, invert_gpio, False, False, duty_cycle)
									if extra_pin != 0:
										self._turn_heater_on(extra_pin, invert_extra_pin, True, False, duty_cycle)
									heater = True
								elif control_mode == 'manual_pwm':
									duty_cycle_percent = manual_pwm_percent
									duty_cycle = self._percent_to_duty_cycle(duty_cycle_percent)
									result = f'Manual PWM mode set to {round(duty_cycle_percent, 2)}%'
									self.log(4, f'INFO: {result}')
									if duty_cycle > 0:
										self._turn_heater_on(heater_pin, invert_gpio, False, True, duty_cycle)
										if extra_pin != 0:
											self._turn_heater_on(extra_pin, invert_extra_pin, True, True, duty_cycle)
										heater = True
									else:
										self._turn_heater_off(heater_pin, invert_gpio, False, True)
										if extra_pin != 0:
											self._turn_heater_off(extra_pin, invert_extra_pin, True, True)
										heater = False
								elif force != 0 and temperature <= force:
									result = f'Temperature below forced level of {force}'
									self.log(4, f'INFO: {result}')
									if use_pwm:
										duty_cycle_percent = self._apply_day_pwm_cap(100, tod)
									else:
										duty_cycle_percent = 100
									duty_cycle = self._percent_to_duty_cycle(duty_cycle_percent)
									if currently_on or self._can_turn_on(currently_on, startup_grace_active):
										self._turn_heater_on(heater_pin, invert_gpio, False, use_pwm, duty_cycle)
										if extra_pin != 0:
											self._turn_heater_on(extra_pin, invert_extra_pin, True, extra_use_pwm, duty_cycle)
										heater = True
									else:
										result = f'Waiting for minimum off time before turning heater on'
										self.log(4, f'INFO: {result}')
								else:
									target_heater_on = False
									if effective_dew_margin is not None and effective_dew_margin <= dew_margin_on:
										target_heater_on = True
										result = f'Effective dew margin of {effective_dew_margin} is within on margin of {dew_margin_on}'
									elif currently_on and effective_dew_margin is not None and effective_dew_margin <= dew_margin_off:
										target_heater_on = True
										result = f'Effective dew margin of {effective_dew_margin} is below off margin of {dew_margin_off}; keeping heater on'
									else:
										if effective_dew_margin is not None and effective_dew_margin > dew_margin_off:
											result = f'Effective dew margin of {effective_dew_margin} is above off margin of {dew_margin_off}'
										else:
											result = f'Effective dew margin of {effective_dew_margin} is between on margin of {dew_margin_on} and off margin of {dew_margin_off}; heater remains off'

									self.log(4 if target_heater_on else 1, f'INFO: {result}')

									if target_heater_on:
										if use_pwm:
											duty_cycle_percent = round(self._calculate_pwm_percent(effective_dew_margin), 2)
											duty_cycle_percent = self._apply_day_pwm_cap(duty_cycle_percent, tod)
											duty_cycle_percent = self._apply_pwm_change_deadband(duty_cycle_percent, currently_on)
											duty_cycle = self._percent_to_duty_cycle(duty_cycle_percent)
										else:
											duty_cycle_percent = 100
											duty_cycle = self._percent_to_duty_cycle(100)

										if currently_on or self._can_turn_on(currently_on, startup_grace_active):
											self._turn_heater_on(heater_pin, invert_gpio, False, use_pwm, duty_cycle)
											if extra_pin != 0:
												self._turn_heater_on(extra_pin, invert_extra_pin, True, extra_use_pwm, duty_cycle)
											heater = True
										else:
											result = 'Minimum off time active; heater remains off'
											self.log(4, f'INFO: {result}')
									else:
										if currently_on and (not self._can_turn_off(currently_on, startup_grace_active)):
											result = 'Minimum on time active; heater remains on'
											self.log(4, f'INFO: {result}')
											if use_pwm:
												duty_cycle = current_duty_cycle if current_duty_cycle > 0 else self._percent_to_duty_cycle(100)
												duty_cycle_percent = round((duty_cycle / 65535) * 100, 2)
												self._turn_heater_on(heater_pin, invert_gpio, False, True, duty_cycle)
												if extra_pin != 0:
													self._turn_heater_on(extra_pin, invert_extra_pin, True, True, duty_cycle)
											else:
												duty_cycle = self._percent_to_duty_cycle(100)
												duty_cycle_percent = 100
												self._turn_heater_on(heater_pin, invert_gpio, False, False)
												if extra_pin != 0:
													self._turn_heater_on(extra_pin, invert_extra_pin, True, False)
											heater = True
										else:
											self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
											if extra_pin != 0:
												self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)
											heater = False

							self.log(4, f'INFO: Control Mode {control_mode}, Dew Margin {dew_margin}, Effective Margin {effective_dew_margin}, Heater {heater}, Target PWM {round(duty_cycle_percent, 2)}%, Startup Grace {startup_grace_active}')

							extraData = {}
							extraData['AS_DEWCONTROLHEATER'] = heater
							extraData['AS_DEWCONTROLHEATERINT'] = 1 if heater else 0
							extraData['AS_DEWCONTROLAMBIENT'] = temperature
							extraData['AS_DEWCONTROLDEW'] = dew_point
							extraData['AS_DEWCONTROLMARGIN'] = dew_margin
							extraData['AS_DEWCONTROLLIMIT'] = dew_margin_on
							extraData['AS_DEWCONTROLHUMIDITY'] = humidity
							extraData['AS_DEWCONTROLPWMDUTYCYCLE'] = duty_cycle
							extraData['AS_DEWCONTROLPWMPERCENT'] = round(duty_cycle_percent, 2) if heater else 0
							if sensor_type != 'Allsky':
								extraData['AS_DEWCONTROLSENSOR'] = sensor_type

								if pressure is not None:
									extraData['AS_DEWCONTROLPRESSURE'] = pressure
								if rel_humidity is not None:
									extraData['AS_DEWCONTROLRELHUMIDITY'] = rel_humidity
								if altitude is not None:
									extraData['AS_DEWCONTROLALTITUDE'] = altitude

							if use_pwm:
								extraData['AS_DEWCONTROLPWMDUTYCYCLE'] = duty_cycle
								extraData['AS_DEWCONTROLPWMPERCENT'] = round(duty_cycle_percent, 2)

							allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extraData, self.meta_data['module'], self.meta_data['extradata'])

							history_data = allsky_shared.load_extra_data_file('dewheaterhistory', 'json')
							current_time = int(time.time())

							heater_state = 0
							if use_pwm:
								heater_state = duty_cycle
							else:
								if heater:
									heater_state = 100

							history_data[current_time] = {
								"heater": heater_state,
								"temperature": temperature,
								"dew_point": dew_point,
								"dew_margin": dew_margin,
								"humidity": humidity
							}

							cutoff_time = int(time.time()) - 86400
							history_data = {ts: val for ts, val in history_data.items() if int(ts) > cutoff_time}

							allsky_shared.save_extra_data('dewheaterhistory', history_data)
						else:
							result = f'Not run. Only running every {frequency}s. Last ran {lastRunSecs}s ago'
							self.log(4, f'INFO: {result}')
					else:
						now = int(time.time())
						allsky_shared.db_add('dewheaterlastrun', now)
						if allsky_shared.db_has_key('dewheaterstarttime'):
							allsky_shared.db_update('dewheaterstarttime', now)
						else:
							allsky_shared.db_add('dewheaterstarttime', now)
						self.log(4, 'INFO: No last run info so assuming startup')
						startup_use_pwm = self._is_pwm_mode(control_mode)
						if control_mode == 'manual_pwm':
							startup_duty_cycle = self._percent_to_duty_cycle(manual_pwm_percent)
							if startup_duty_cycle > 0:
								self._turn_heater_on(heater_pin, invert_gpio, False, True, startup_duty_cycle)
								if extra_pin != 0:
									self._turn_heater_on(extra_pin, invert_extra_pin, True, True, startup_duty_cycle)
								heater = True
							else:
								self._turn_heater_off(heater_pin, invert_gpio, False, True)
								if extra_pin != 0:
									self._turn_heater_off(extra_pin, invert_extra_pin, True, True)
								heater = False
						elif control_mode == 'manual_off':
							self._turn_heater_off(heater_pin, invert_gpio, False, startup_use_pwm)
							if extra_pin != 0:
								self._turn_heater_off(extra_pin, invert_extra_pin, True, startup_use_pwm)
							heater = False
						elif control_mode == 'manual_on' or heater_startup_state == 'ON':
							self._turn_heater_on(heater_pin, invert_gpio, False, startup_use_pwm, self._percent_to_duty_cycle(100))
							if extra_pin != 0:
								self._turn_heater_on(extra_pin, invert_extra_pin, True, startup_use_pwm, self._percent_to_duty_cycle(100))
							heater = True
						else:
							self._turn_heater_off(heater_pin, invert_gpio, False, startup_use_pwm)
							if extra_pin != 0:
								self._turn_heater_off(extra_pin, invert_extra_pin, True, startup_use_pwm)
							heater = False
				else:
					allsky_shared.delete_extra_data(self.meta_data['extradatafilename'])
					self.log(0, f'ERROR in {__file__}: heater pin not defined or invalid')

				allsky_shared.set_last_run('allskydew')

			else:
				self.log(4, f'INFO: Will run in {format(frequency - diff)} seconds')
		else:
			if heater_pin != 0:
				heater_pin = allsky_shared.get_gpio_pin(heater_pin)
				self._turn_heater_off(heater_pin, invert_gpio, False, use_pwm)
			if extra_pin != 0:
				extra_pin = allsky_shared.get_gpio_pin(extra_pin)
				self._turn_heater_off(extra_pin, invert_extra_pin, True, extra_use_pwm)

			extra_data = {}
			extra_data['AS_DEWCONTROLSENSOR'] = sensor_type
			extra_data['AS_DEWCONTROLAMBIENT'] = 0
			extra_data['AS_DEWCONTROLDEW'] = 0
			extra_data['AS_DEWCONTROLHUMIDITY'] = 0
			extra_data['AS_DEWCONTROLLIMIT'] = 0
			extra_data['AS_DEWCONTROLHEATER'] = 'Disabled'
			allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
			
			result = 'Dew control disabled during the day'
			self.log(4, f"INFO: {result}")
			
		return result

def dewheater(params, event):
	"""Module entry point used by the Allsky module loader."""
	allsky_dewheater = ALLSKYDEWHEATER(params, event)
	result = allsky_dewheater.run()

	return result       
    
def dewheater_cleanup():
	"""Return the cleanup instructions for temporary extra-data files."""
	moduleData = {
		"metaData": ALLSKYDEWHEATER.meta_data,
		"cleanup": {
			"files": {
				ALLSKYDEWHEATER.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanup_module(moduleData)
