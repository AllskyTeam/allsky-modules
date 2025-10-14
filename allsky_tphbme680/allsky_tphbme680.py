'''
allsky_tphbme680.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

'''
import allsky_shared as s

metaData = {
	"name": "tphbme680 (Temperature, Humidity, Pressure)",
	"description": "Provides T,H,P levels",
	"module": "allsky_tphbme680",
	"version": "v1.0.0",    
	"events": [
		"periodic"
	],
	"group": "Data Capture",
	"deprecation": {
		"fromversion": "v2024.12.06_01",
		"removein": "v2024.12.06_01",
		"notes": "This module has been deprecated. Please use the Environment Monitor module",
		"replacedby": "allsky_temp",
		"deprecated": "true"
	}, 
	"experimental": "true",    
	"arguments":{
	},
	"argumentdetails": {   
	},
	"enabled": "false"            
}

def tphbme680(params, event):
	return "Deprecated - Please use the Envorinment Monitor module"

	return result
