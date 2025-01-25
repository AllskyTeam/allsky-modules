import allsky_shared as s
import time
import requests
import json


metaData = {
	"name": "Import JSON",
	"description": "Reads data from a json web source",
	"module": "allsky_jsonimport",
	"version": "v1.0.1",
	"events": [
	    "periodic"
	],
	"experimental": "false",
	"arguments":{
	    "jsonurl": "",
	    "prefix": "",
	    "extradatafilename": "jsonimport.json",
	    "period": 60
	},
	"argumentdetails": {
	    "period" : {
	        "required": "false",
	        "description": "Read Every",
	        "help": "Reads data every x seconds.. Zero will disable this and run the check every time the periodic jobs run",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 1000,
	            "step": 1
	        }
	    },         
	    "jsonurl": {
	        "required": "false",
	        "description": "JSON Data URL",
	        "help": "The full URL to read the json data from"
	    },
	    "prefix": {
	        "required": "true",
	        "description": "Variable Prefix",
	        "help": "The prefix for variables - DO NOT CHANGE unless you have multiple variables that clash"
	    },
	    "extradatafilename": {
	        "required": "true",
	        "description": "Extra Data Filename",
	        "help": "The name of the file to create with the json data for the overlay manager"
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

	
def jsonimport(params, event):    
	result = ""
	extra_data = {}
	extradatafilename = params['extradatafilename']
	json_url = params['jsonurl']
	prefix = params['prefix']
	period = int(params['period'])

	should_run, diff = s.shouldRun(metaData['module'], period)

	if should_run:
	    try:
	        response = requests.get(json_url, timeout=10)
	        response.raise_for_status()
	        json_data = response.json()

	        s.log(4, f'INFO: Retrieved {json_data} from {json_url}')

	        for key in json_data:
	            extra_data[f'AS_{prefix}{key.upper()}'] = json_data[key]

	        result = 'Data retrieved ok'
	    except requests.exceptions.RequestException as json_exception:
	        result = f'Request Error: {json_exception}'
	        s.log(0,f'ERROR: {result}')
	    except json.JSONDecodeError:
	        result = 'Error decoding JSON.'
	        s.log(0,f'ERROR: {result}')            
	    except Exception as json_exception:
	        result = f'An unexpected error occurred: {json_exception}'
	        s.log(0,f'ERROR: {result}')

	    s.saveExtraData(extradatafilename, extra_data)
	    
	    s.setLastRun(metaData['module'])
	else:
	    result = f'Will run in {(period - diff):.2f} seconds'
	    s.log(1,f'INFO: {result}')

	return result

def jsonimport_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskytemp.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)