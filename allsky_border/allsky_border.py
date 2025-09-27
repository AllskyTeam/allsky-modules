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
from allsky_base import ALLSKYMODULEBASE
import sys
import cv2

class ALLSKYBORDER(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Add Border",
		"description": "Expands a captured image adding a border",
		"module": "allsky_border",
		"version": "v1.0.1",
		"group": "Image Adjustments",
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

	def run(self):
		result = 'Border Added'

		try:
			left = self.get_param('left', 0, int)       
			right = self.get_param('right', 0, int)       
			top = self.get_param('top', 0, int)       
			bottom = self.get_param('bottom', 0, int)       
			colours = self.get_param('colour', '0,0,0', str, True)       

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
			result = f'Border failed on line {eTraceback.tb_lineno} - {e}'
			self.log(0, f'ERROR: {result}')
			
		return result

def border(params, event):
	allsky_border = ALLSKYBORDER(params, event)
	result = allsky_border.run()

	return result  