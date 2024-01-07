'''
allsky_border.py

Part of allsky flow-runner.py modules.
https://github.com/thomasjacquin/allsky

This module will allow an image to be enlarged with a coloured border, primarilly to 
allow the overlay data to be displayed

Expected parameters:
None
'''
import allsky_shared as s
import os
import cv2

metaData = {
    "name": "Add Border",
    "description": "Expands a captured image adding a border",
    "module": "allsky_border",
    "version": "v1.0.0",      
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
            "help": "The RGB colour of the border, default to black. This shoudl be comma separated values i.e. 255,0,0 for Red"
        }           
    },
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

def border(params, event):
    result = ""

    left = int(params["left"])
    right = int(params["right"])
    top = int(params["top"])
    bottom = int(params["bottom"])
    colours = params["colour"]

    # Set the colours for the border. The colour MUST be specified as R,G,B. If there are ANY errors detected
    # in the colour options then black will be used.
    colourArray = colours.split(",")
    if len(colourArray) == 3 and colourArray[0].isdigit() and colourArray[1].isdigit() and colourArray[2].isdigit():
        colour = [int(colourArray[2]),int(colourArray[1]),int(colourArray[0])]
    else:
        colour = [0,0,0]

    s.image = cv2.copyMakeBorder(s.image, top, bottom, left, right, cv2.BORDER_CONSTANT, None, colour)
     
    return result

def border_cleanup():
    pass