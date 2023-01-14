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
    "version": "v1.0.0",    
    "events": [
        "daynight",
        "nightday"
    ],
    "experimental": "true",    
    "arguments":{
        "gpio": 0,
        "state": 0
    },
    "argumentdetails": {
        "gpio": {
            "required": "false",
            "description": "GPIO Pin",
            "help": "",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 30,
                "step": 1
            }             
        },
        "state": {
            "required": "false",
            "description": "Pin State",
            "help": "",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1,
                "step": 1
            }             
        }                     
    },
    "enabled": "false"            
}

def crop(params, event): 
    pass