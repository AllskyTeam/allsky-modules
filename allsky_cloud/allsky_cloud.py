'''
allsky_cloud.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import os
import math
import board
import adafruit_mlx90614

metaData = {
    "name": "Determines cloud cover",
    "description": "Determines cloud cover using an MLX90614",
    "module": "allsky_cloud",
    "version": "v1.0.0",    
    "events": [
        "night",
        "day"
    ],
    "experimental": "true",    
    "arguments":{
        "i2caddress": "",
        "clearbelow": -10,
        "cloudyabove": 5
    },
    "argumentdetails": {                   
        "i2caddress": {
            "required": "true",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor"
        },
        "clearbelow" : {
            "required": "true",
            "description": "Clear Below &deg;C",
            "help": "When the sky temperature is below this value the sky is assumed to be clear",
            "tab": "Settings",            
            "type": {
                "fieldtype": "spinner",
                "min": -60,
                "max": 10,
                "step": 1
            }          
        },
        "cloudyabove" : {
            "required": "true",
            "description": "Cloudy Above &deg;C",
            "help": "When the sky temperature is above this value the sky is assumed to be cloudy",
            "tab": "Settings",            
            "type": {
                "fieldtype": "spinner",
                "min": -60,
                "max": 100,
                "step": 1
            }          
        }
    },
    "enabled": "false"            
}

def getsign(d):
    if d < 0:
        return -1.0
    if d == 0:
        return 0.0
    return 1.0


def calculateSkyState(skyambient, skyobject, clearbelow, cloudyabove):
    cloudCover = 'Partial'

    if skyambient <= clearbelow:
        cloudCover = 'Clear'

    if skyambient >= cloudyabove:
        cloudCover = 'Cloudy'

    return cloudCover


def cloud(params):
    i2caddress = params["i2caddress"]
    clearbelow = int(params["clearbelow"])
    cloudyabove = int(params["cloudyabove"])

    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except:
            result = "Address {} is not a valid i2c address".format(i2caddress)
            s.log(0,"ERROR: {}".format(result))

    i2c = board.I2C()
    if i2caddress != "":
        mlx = adafruit_mlx90614.MLX90614(i2c, i2caddressInt)
    else:
        mlx = adafruit_mlx90614.MLX90614(i2c)

    skyambient = mlx.ambient_temperature
    skyobject = mlx.object_temperature

    cloudCover = calculateSkyState(skyambient, skyobject, clearbelow, cloudyabove)

    os.environ["AS_CLOUDAMBIENT"] = str(skyambient)
    os.environ["AS_CLOUDSKY"] = str(skyobject)
    os.environ["AS_CLOUDCOVER"] = cloudCover

    result = "Cloud state - {0}. Sky Temp {1}, Ambient {2}".format(cloudCover, skyobject, skyambient)
    s.log(1, "INFO: {}".format(result))

    return result   