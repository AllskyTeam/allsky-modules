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
from digitalio import DigitalInOut, Direction, Pull

metaData = {
    "name": "Rain detection",
    "description": "Detects rain via an external digital sensor",
    "module": "allsky_rain",       
    "events": [
        "periodic"
    ],
    "arguments":{
        "inputpin": "",
        "invertsensor": "false",
        "extradatafilename": "allskyrain.json"
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
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Misc",              
            "help": "The name of the file to create with the rain data for the overlay manager"         
        }              
    }      
}

def rain(params, event):
    result = ""

    inputpin = params["inputpin"]
    invertsensor = params["invertsensor"]
    extradatafilename = params['extradatafilename']
    
    try:
        inputpin = int(inputpin)
    except ValueError:
        inputpin = 0

    if inputpin != 0:
        try:
            rainpin = s.getGPIOPin(inputpin)
            pin = DigitalInOut(rainpin)

            pinState = pin.value

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

            extraData = {}
            extraData["AS_RAINSTATE"] = raining
            extraData["AS_ALLSKYRAINFLAG"] = str(rainFlag)
            s.saveExtraData(extradatafilename,extraData)

            result = "Rain State: Its {}".format(resultState)
            s.log(1, "INFO: {}".format(result))
        except Exception as ex:
            result = "Unable to read Rain sensor {}".format(ex)
            s.log(0, "ERROR: {}".format(result))
            s.deleteExtraData(extradatafilename)
    else:
        result = "Invalid GPIO pin ({})".format(params["inputpin"])
        s.log(0, "ERROR: {}".format(result))
        s.deleteExtraData(extradatafilename)
        
    return result

def rain_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyrain.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)