'''
allsky_ltr390.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

'''
import allsky_shared as s
import board
import sys
from adafruit_ltr390 import LTR390, MeasurementDelay, Resolution, Gain


metaData = {
	"name": "LTR390 (UV Level)",
	"description": "Estimate UV Levels from an LTR390 sensor",
	"module": "allsky_ltr390",
	"version": "v1.0.2",
	"centersettings": "false",
	"events": [
		"day",
		"night",
		"periodic"
	],
	"experimental": "false",
	"group": "Data Sensor",
	"deprecation": {
		"fromversion": "v2024.12.06_01",
		"removein": "v2024.12.06_01",
		"notes": "This module has been deprecated. Please use the allsky_light module",
		"replacedby": "allsky_light",
		"deprecated": "true"
	},  
	"arguments":{
	},
	"argumentdetails": {                                                                  
	},
	"enabled": "false",
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
				"changes": [
					"Moved to periodic flow",
					"Added addition error logging"
				]
			}
		],
		"v1.0.2" : [
			{
				"author": "Alex Greenland",
				"authorurl": "https://github.com/allskyteam",
				"changes": "Deprecated, code moved tio light module"
			}
		]                                              
	}                  
}

def ltr390(params, event):


	return ""
