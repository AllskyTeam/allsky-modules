"""

Part of AllSkyAI. To create a custom model or find more info please visit https://www.allskyai.com
Written by Christian Kardach - The Crows Nest Astro
info@allskyai.com

"""
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

class ALLSKYAI(ALLSKYMODULEBASE):

	metaData = {
		"name": "AllSkyAI",
		"description": "Classify the current sky with ML. More info https://www.allskyai.com",
		"module": "allsky_ai",
		"version": "v1.0.5",
		"extradatafilename": "allsky_ai.json",
		"centersettings": "false",
		"group": "Image Analysis",
		"deprecation": {
			"fromversion": "v2024.12.06_04",
			"removein": "v2024.12.06_04",
			"notes": "This module has been deprecated as the author no longer supports it",
			"deprecated": "true"
		}, 
		"events": [
			"day",
			"night"
		],
		"experimental": "yes",
		"arguments":{
			"dummy": ""
		},
		"argumentdetails": {
			"notice": {
				"message": "This module is no longer in use",
				"tab": "Sensor",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "danger"
						}
					}
				}            						
			}
		},
		"businfo": [
		],
		"changelog": {
			"v1.0.0": [
				{
					"author": "Christian Kardach",
					"authorurl": "https://www.allskyai.com",
					"changes": "Initial Release"
				}
			],
			"v1.0.4": [
				{
					"author": "Christian Kardach",
					"authorurl": "https://www.allskyai.com",
					"changes": "Bug Fixes"
				}
			],
			"v1.0.5": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updates for new module system"
				}
			],
			"v1.0.6": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Removed module as Christian is no longer maintaining it."
				}
			]
		}
	}


def ai(params, event):
	result = 'Module deprecated please use the allsky_power module instead'

	allsky_shared.log(0, f'ERROR: {result}')
	return result
