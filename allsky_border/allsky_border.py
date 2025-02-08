'''
allsky_border.py

Part of allsky flow-runner.py modules.
https://github.com/thomasjacquin/allsky

This module will allow an image to be enlarged with a coloured border, primarilly to 
allow the overlay data to be displayed

Expected parameters:
None
'''
import allsky_shared as allsky_shared
import sys
import cv2

metaData = {
	"name": "Add Border",
	"description": "Expands a captured image adding a border",
	"module": "allsky_border",
	"version": "v1.0.1",      
	"events": [
	    "day",
	    "night"
	],
	"arguments":{
	    "left": "0",
	    "right": "0",
	    "top": "0",
	    "bottom": "0",
	    "colour": "0,0,0"
	},
	"argumentdetails": {
	    "left" : {
	        "required": "false",
	        "description": "Left Size",
	        "help": "The number of pixels to add to the left of the captured image",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 10,
	            "max": 1000,
	            "step": 1
	        }          
	    },       
	    "right" : {
	        "required": "false",
	        "description": "Right Size",
	        "help": "The number of pixels to add to the right of the captured image",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 10,
	            "max": 1000,
	            "step": 1
	        }          
	    },       
	    "top" : {
	        "required": "false",
	        "description": "Top Size",
	        "help": "The number of pixels to add to the top of the captured image",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 10,
	            "max": 1000,
	            "step": 1
	        }          
	    },
	    "bottom" : {
	        "required": "false",
	        "description": "Bottom Size",
	        "help": "The number of pixels to add to the bottom of the captured image",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 10,
	            "max": 1000,
	            "step": 1
	        }          
	    },
	    "colour": {
	        "required": "false",
	        "description": "Border Colour",            
	        "help": "The RGB colour of the border, default to black. This should be comma separated values i.e. 255,0,0 for Red",
	        "type": {
	            "fieldtype": "colour"
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
				"changes": [
        			"Added Colour Picker",
					"Updated for new module format"
				]
			}
		]                                    
	}           
}

def border(params, event):
	result = ""

	try:
		left = int(params['left'])
		right = int(params['right'])
		top = int(params['top'])
		bottom = int(params['bottom'])
		colours = params['colour']

		# Set the colours for the border. The colour MUST be specified as R,G,B. If there are ANY errors detected
		# in the colour options then black will be used.
		colour_array = colours.split(',')
		if len(colour_array) == 3 and colour_array[0].isdigit() and colour_array[1].isdigit() and colour_array[2].isdigit():
			colour = [int(colour_array[2]),int(colour_array[1]),int(colour_array[0])]
		else:
			colour = [0,0,0]

		allsky_shared.image = cv2.copyMakeBorder(allsky_shared.image, top, bottom, left, right, cv2.BORDER_CONSTANT, None, colour)

	except Exception as e:
		eType, eObject, eTraceback = sys.exc_info()
		allsky_shared.log(0, f'ERROR: border failed on line {eTraceback.tb_lineno} - {e}')
   		
	return result

def border_cleanup():
	pass