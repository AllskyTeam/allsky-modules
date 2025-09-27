import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import requests
import json

class ALLSKYJSONIMPORT(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Import JSON",
		"description": "Reads data from a json web source for use in overlays",
		"module": "allsky_jsonimport",
		"version": "v1.0.1",
		"testable": "true",
		"centersettings": "false", 
		"group": "Data Capture",
		"events": [
			"day",
			"night",
			"periodic"
		],
		"experimental": "false",
		"arguments":{
			"jsonurl": "",
			"prefix": "",
			"extradatafilename": "allsky_jsonimport.json",
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
			],
			"v1.0.1" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updated for new module system"
				}
			]     
		}
	}
	
	def run(self):    
		result = ''
		extra_data = {}
  
		extra_data_filename = self.get_param('extradatafilename', 'allsky_jsonimport.json', str, True) 
		json_url = self.get_param('jsonurl', '', str) 
		prefix = self.get_param('prefix', '', str) 
		period = self.get_param('period', '', int) 
    
		should_run, diff = allsky_shared.shouldRun(self.meta_data['module'], period)

		if should_run or self.debug_mode:
			try:
				response = requests.get(json_url, timeout=10)
				response.raise_for_status()
				json_data = response.json()

				self.log(4, f'INFO: Retrieved {json_data} from {json_url}')

				for key in json_data:
					extra_data[f'AS_{prefix}{key.upper()}'] = json_data[key]

				result = 'Data retrieved ok'
			except requests.exceptions.RequestException as json_exception:
				result = f'Request Error: {json_exception}'
				self.log(0,f'ERROR: {result}')
			except json.JSONDecodeError:
				result = 'Error decoding JSON.'
				self.log(0,f'ERROR: {result}')            
			except Exception as json_exception:
				result = f'An unexpected error occurred: {json_exception}'
				self.log(0,f'ERROR: {result}')

			allsky_shared.saveExtraData(extra_data_filename, extra_data, self.meta_data['module'])
			
			allsky_shared.setLastRun(self.meta_data['module'])
		else:
			result = f'Will run in {(period - diff):.2f} seconds'
			self.log(1,f'INFO: {result}')

		return result

def jsonimport(params, event):
	allsky_json_import = ALLSKYJSONIMPORT(params, event)
	result = allsky_json_import.run()

	return result
    
def jsonimport_cleanup():
	moduleData = {
	    "metaData": ALLSKYJSONIMPORT.meta_data,
	    "cleanup": {
	        "files": {
	            "allsky_jsonimport.json"
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)