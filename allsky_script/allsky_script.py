""" allsky_script.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will run a custom script
"""
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os 
import subprocess

class ALLSKYSCRIPT(ALLSKYMODULEBASE):

	meta_data = {
		"name": "AllSKY Script",
		"description": "Runs a custom script",
		"version": "v1.0.1",
		"testable": "true", 
		"events": [
			"day",
			"night",
			"daynight",
			"nightday",
			"periodic"
		],
		"experimental": "false",    
		"arguments":{
			"scriptlocation": "",
			"useshell": "false"
		},
		"argumentdetails": {
			"scriptlocation" : {
				"required": "true",
				"description": "File Location",
				"help": "The location of the script to run"
			},
			"shellnotice": {
				"message": "<strong>NOTE</strong> Use this with extereme caution. If you are unsure of the implications do not select this option",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "danger"
						}
					}
				}
			},      
			"useshell" : {
				"required": "false",
				"description": "Use Shell",
				"help": "Runs the command in a shell",
				"type": {
					"fieldtype": "checkbox"
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
			],
			"v1.0.1" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updated to new module format"
				}
			]                                                
		}           
	}

    
	def run(self):
		script = self.get_param('scriptlocation', '', str, True)

		if script:
			if os.path.isfile(script):
				if os.access(script, os.X_OK):
					script_result = subprocess.run(script, text=True, capture_output=True)
					result = f"Script {script} Executed."
					allsky_shared.log(4, f"INFO: Script result Exit Code - {script_result.returncode} Output - {script_result.stdout}")
				else:
					result = f"Script {script} Is NOT Executeable."
					allsky_shared.log(0, f"ERROR: {result}")
			else:
				result = f"Script {script} Not Found."
				allsky_shared.log(0, f"ERROR: {result}")
		else:
			result = f"Script cannot be empty."
			allsky_shared.log(0, f"ERROR: {result}")
		
		return result


def script(params, event):
	allsky_script = ALLSKYSCRIPT(params, event)
	result = allsky_script.run()

	return result   
