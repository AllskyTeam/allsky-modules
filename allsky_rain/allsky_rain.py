'''
allsky_rain.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will interface to a digital rain detector

Expected parameters:
None
'''
import allsky_shared as s
import os 
import RPi.GPIO as GPIO

metaData = {
    "name": "Rain detection",
    "description": "Detects rain via an external digital sensor",
    "module": "allsky_rain",       
    "events": [
        "day",
        "night"
    ],
    "arguments":{
        "inputpin": "",
        "invertsensor": "false"
    },
    "argumentdetails": {
        "inputpin": {
            "required": "true",
            "description": "Input Pin",
            "help": "The input pin for the digital rain sensor",
            "type": {
                "fieldtype": "gpio"
            }           
        },
        "invertsensor" : {
            "required": "false",
            "description": "Invert Sensor",
            "help": "Normally the sensor will be high for clear and low for rain. This settign will reverse this",
            "type": {
                "fieldtype": "checkbox"
            }               
        }        
    }      
}

def rain(params, event):
    result = ""

    inputpin = params["inputpin"]
    invertsensor = params["invertsensor"]

    try:
        inputpin = int(inputpin)
    except ValueError:
        inputpin = 0

    if inputpin != 0:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(inputpin, GPIO.IN)

        pinState = GPIO.input(inputpin)

        resultState = "Not Raining"
        raining = ""
        rainFlag = False
        if not invertsensor:
            if pinState == 0:
                raining = "Raining"
                resultState = raining
                rainFlag = True
        else:
            if pinState == 1:
                raining = "Raining"
                resultState = raining
                rainFlag = True

        os.environ["AS_RAINSTATE"] = raining
        os.environ["AS_ALLSKYRAINFLAG"] = str(rainFlag)

        result = "Rain State: Its {}".format(resultState)
        s.log(1, "INFO: {}".format(result))
    else:
        result = "Invalid GPIO pin ({})".format(params["inputpin"])
        s.log(0, "ERROR: {}".format(result))

    return result