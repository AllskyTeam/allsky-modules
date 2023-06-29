'''
allsky_fans.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import time
import os
import shutil
from vcgencmd import Vcgencmd
import board
import RPi.GPIO as GPIO

metaData = {
    "name": "Control Allsky Fans",
    "description": "Start Allsky Fans when the CPU reaches a set temperature",
    "module": "allsky_fans",    
    "version": "v1.0.0",    
    "events": [
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "period": 60,
        "fanpin": "",
        "invertrelay": "False",
        "limit": 60
    },
    "argumentdetails": {
        "period" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds.",                
            "type": {
                "fieldtype": "spinner",
                "min": 60,
                "max": 600,
                "step": 1
            }          
        },
        "fanpin": {
            "required": "false",
            "description": "Fans Relay Pin",
            "help": "The GPIO pin the fan control relay is connected to",
            "type": {
                "fieldtype": "gpio"
            }           
        },
        "invertrelay" : {
            "required": "false",
            "description": "Invert Relay",
            "help": "Invert relay activation logic from pin HIGH to pin LOW",
            "type": {
                "fieldtype": "checkbox"
            }               
        },
        "limit" : {
            "required": "false",
            "description": "CPU Temp. Limit",
            "help": "The CPU temperature limit beyond which fans are activated",
            "type": {
                "fieldtype": "spinner",
                "min": 40,
                "max": 75,
                "step": 1
            }          
        }                   
    },
    "enabled": "false"
}

def getTemperature():
    tempC = None
    vcgm = Vcgencmd()
    temp = vcgm.measure_temp()
    tempC = round(temp,1)

    return tempC
    
def setmode():
    try:
        GPIO.setmode(GPIO.BOARD)
    except:
        pass

def turnFansOn(fanpin, invertrelay):
    result = "Turning Fans ON"
    setmode()
    GPIO.setup(fanpin.id, GPIO.OUT)
    if invertrelay:
        if GPIO.input(fanpin.id) == 0:
            result = "Leaving Fans ON"
        GPIO.output(fanpin.id, GPIO.LOW)
    else:
        if GPIO.input(fanpin.id) == 1:
            result = "Leaving Fans ON"
        GPIO.output(fanpin.id, GPIO.HIGH)
    s.log(1,"INFO: {}".format(result))
    
def turnFansOff(fanpin, invertrelay):
    result = "Turning Fans OFF"
    setmode()
    GPIO.setup(fanpin.id, GPIO.OUT)

    if invertrelay:
        if GPIO.input(fanpin.id) == 1:
            result = "Leaving Fans OFF"        
        GPIO.output(fanpin.id, GPIO.HIGH)
    else:    
        if GPIO.input(fanpin.id) == 0:
            result = "Leaving Fans OFF"       
        GPIO.output(fanpin.id, GPIO.LOW)
    s.log(1,"INFO: {}".format(result))

def fans(params, event):
    result = ''
    cfans = ''
    period = int(params['period'])
    fanpin = int(params["fanpin"])
    limit = int(params["limit"])
    invertrelay = params["invertrelay"]

    temperature = 0
    cfans = "Unkn"
    shouldRun, diff = s.shouldRun('fans', period)
    
    if shouldRun:
        extraData = {}
        try:
            fanpin = int(fanpin)
        except ValueError:
            fanpin = 0
        if fanpin != 0:
            fanpin = s.getGPIOPin(fanpin)
            temperature = getTemperature()
            if temperature is not None:
                if (temperature > limit):
                    turnFansOn(fanpin, invertrelay)
                    cfans = "On"
                    result = "CPU Temp is {} and higher then set limit of {}, Fans are {} via fan pin {}".format(temperature, limit, cfans, fanpin)
                else:
                    turnFansOff(fanpin, invertrelay)
                    cfans = "Off"
                    result = "CPU Temp is {} and lower then set limit of {}, Fans are {} via fan pin {}".format(temperature, limit, cfans, fanpin)
                extraData["OTH_FANS"] = cfans
                extraData["OTH_FANT"] = limit
                s.saveExtraData("allskyfans.json", extraData)
            else:
                result = "Failed to get temperature"
                s.log(0, "ERROR: {}".format(result))
        else:
            result = "fan pin not defined or invalid"
            s.log(0, "ERROR: {}".format(result))
    else:
        result = 'Will run in ' + str(period - diff) + ' seconds'
        
    s.log(1,"INFO: {}".format(result))
    
    return result

def fans_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyfans.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
