""" allsky_script.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will run a custom script
"""
import allsky_shared as s
import os 
import subprocess

metaData = {
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

def script(params, event):
	script = params["scriptlocation"]

	if script:
		if os.path.isfile(script):
			if os.access(script, os.X_OK):
				script_result = subprocess.run(script, text=True, capture_output=True)
				result = f"Script {script} Executed."
				s.log(4, f"INFO: Script result Exit Code - {script_result.returncode} Output - {script_result.stdout}")
			else:
				result = f"Script {script} Is NOT Executeable."
				s.log(0, f"ERROR: {result}")
		else:
			result = f"Script {script} Not Found."
			s.log(0, f"ERROR: {result}")
	else:
		result = f"Script cannot be empty."
		s.log(0, f"ERROR: {result}")
     
	return result