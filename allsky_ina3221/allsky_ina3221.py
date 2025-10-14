import allsky_shared as allsky_shared

metaData = {
	"name": "Monitor Pi Current and Voltage",
	"description": "Monitor Pi current and voltage using an ina3221",
	"module": "allsky_ina3221",
	"version": "v1.0.1",
	"group": "Hardware",
	"deprecation": {
		"fromversion": "v2024.12.06_02",
		"removein": "v2024.12.06_02",
		"notes": "This module has been deprecated. Please use the 'Pi Power Monitoring' module.",
		"replacedby": "allsky_power",
		"deprecated": "true"
	}, 
	"events": [
		"day",
		"night",
	    "periodic"
	],
	"experimental": "true",
	"arguments":{
		"dummy": ""
	},
	"argumentdetails": {
		"notice": {
			"message": "This module is no longer in use and has been replaced by the 'Pi Power Monitoring' module.",
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
	    "i2c"
	] 
}

def ina3221(params, event):
	result = "Module deprecated - please use the 'Pi Power Monitoring' module instead."
	allsky_shared.log(0, f'ERROR: {result}')
	return result
