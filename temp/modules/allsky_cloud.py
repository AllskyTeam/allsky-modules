'''
allsky_cloud.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import sys
import math
import board
import adafruit_mlx90614

metaData = {
	"name": "Determines cloud cover",
	"description": "Determines cloud cover using an MLX90614",
	"module": "allsky_cloud",
	"version": "v1.0.1",    
	"events": [
	    "night",
	    "day",
	    "periodic"
	],
	"experimental": "true",    
	"arguments":{
	    "i2caddress": "",
	    "clearbelow": -10,
	    "cloudyabove": 5,
	    "advanced": "false",
	    "k1": 33,
	    "k2": 0,
	    "k3": 4,
	    "k4": 100,
	    "k5": 100,
	    "k6": 0,
	    "k7": 0,
	    "extradatafilename": "allskcloud.json"
	},
	"argumentdetails": {                   
	    "i2caddress": {
	        "required": "false",
	        "description": "I2C Address",
	        "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
	        "tab": "Sensor"
	    },
	    "clearbelow" : {
	        "required": "false",
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
	        "required": "false",
	        "description": "Cloudy Above &deg;C",
	        "help": "When the sky temperature is above this value the sky is assumed to be cloudy",
	        "tab": "Settings",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": -60,
	            "max": 100,
	            "step": 1
	        }          
	    },
	    "extradatafilename": {
	        "required": "true",
	        "description": "Extra Data Filename",
	        "tab": "Advanced",
	        "help": "The name of the file to create with the data for the overlay manager"
	    },        
	    "advanced" : {
	        "required": "false",
	        "description": "Use advanced mode",
	        "help": "Provides a polynomial adjustment for the sky temperature",
	        "tab": "Advanced",
	        "type": {
	            "fieldtype": "checkbox"
	        }          
	    },
	    "k1" : {
	        "required": "false",
	        "description": "k1",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k2" : {
	        "required": "false",
	        "description": "k2",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k3" : {
	        "required": "false",
	        "description": "k3",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k4" : {
	        "required": "false",
	        "description": "k4",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k5" : {
	        "required": "false",
	        "description": "k5",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k6" : {
	        "required": "false",
	        "description": "k6",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    },
	    "k7" : {
	        "required": "false",
	        "description": "k7",
	        "tab": "Advanced",            
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 500,
	            "step": 1
	        }          
	    }        
	},
	"enabled": "false",
	"businfo": [
	    "i2c"
	],
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
	                "Added extra error handling",
	                "Added module to periodic flow",
	                "Added ability to change the extra data filename",
	                "Added changelog to metadata"
	            ]
	        }
	    ]                                
	}                  
}

def getsign(d):
	if d < 0:
	    return -1.0
	if d == 0:
	    return 0.0
	return 1.0

def calculateSkyStateAdvanced(skyambient, skyobject, clearbelow, cloudyabove, params):
	k1 = int(params["k1"])
	k2 = int(params["k2"])
	k3 = int(params["k3"])
	k4 = int(params["k4"])
	k5 = int(params["k5"])
	k6 = int(params["k6"])
	k7 = int(params["k7"])

	if abs((k2 / 10.0 - skyambient)) < 1:
	    t67 = getsign(k6) * getsign(skyambient - k2 / 10.) * abs((k2 / 10. - skyambient))
	else:
	    t67 = k6 / 10. * getsign(skyambient - k2 / 10.) * (math.log(abs((k2 / 10. - skyambient))) / math.log(10) + k7 / 100)

	td = (k1 / 100.) * (skyambient - k2 / 10.) + (k3 / 100.) * pow((math.exp(k4 / 1000. * skyambient)), (k5 / 100.)) + t67

	tsky = skyobject - td
	if tsky < clearbelow:
	    tsky = clearbelow
	elif tsky > cloudyabove:
	    tsky = cloudyabove
	cloudcoverPercentage = ((tsky - clearbelow) * 100.) / (cloudyabove - clearbelow)
	cloudcover, percent = calculateSkyState(skyambient, skyobject, clearbelow, cloudyabove)
	return cloudcover, cloudcoverPercentage

def calculateSkyState(skyambient, skyobject, clearbelow, cloudyabove):
	cloudCover = 'Partial'

	if skyobject <= clearbelow:
	    cloudCover = 'Clear'

	if skyobject >= cloudyabove:
	    cloudCover = 'Cloudy'

	return cloudCover, 0

def cloud(params, event):
	i2caddress = params["i2caddress"]
	clearbelow = int(params["clearbelow"])
	cloudyabove = int(params["cloudyabove"])
	extradatafilename = params['extradatafilename']
	
	advanced = params["advanced"]

	data = {}
	
	try:    
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

	    if advanced:
	        cloudCover, percentage = calculateSkyStateAdvanced(skyambient, skyobject, clearbelow, cloudyabove, params)
	    else:
	        cloudCover, percentage = calculateSkyState(skyambient, skyobject, clearbelow, cloudyabove)

	    data["AS_CLOUDAMBIENT"] = str(skyambient)
	    data["AS_CLOUDSKY"] = str(skyobject)
	    data["AS_CLOUDCOVER"] = cloudCover
	    data["AS_CLOUDCOVERPERCENT"] = str(percentage)
	    s.saveExtraData(extradatafilename, data)

	    result = "Cloud state - {0} {1}. Sky Temp {2}, Ambient {3}".format(cloudCover, percentage, skyobject, skyambient)
	    s.log(1, "INFO: {}".format(result))
	except Exception as e:
	    eType, eObject, eTraceback = sys.exc_info()
	    result = f"ERROR: Module cloud failed on line {eTraceback.tb_lineno} - {e}"
	    s.log(4, result)
	    
	return result 

def cloud_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskcloud.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)