'''
allsky_gpio.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import cv2
import numpy as np

metaData = {
    "name": "Sets a GPIO Pin",
    "description": "Sets a GPIO Pin",
    "events": [
        "daynight",
        "nightday"
    ],
    "experimental": "true",    
    "arguments":{
        "gpio": 0
    },
    "argumentdetails": {
        "gpio": {
            "required": "true",
            "description": "GPIO Pin",
            "help": "",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 30,
                "step": 1
            }             
        }                  
    },
    "enabled": "false"            
}

def crop(params): 
    pass