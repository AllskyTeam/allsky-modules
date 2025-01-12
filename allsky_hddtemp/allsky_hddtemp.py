'''
allsky_hddtemp.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
from pySMART import SMARTCTL, DeviceList
import sys

metaData = {
	"name": "HDD Temp",
	"description": "Provides HDD Temps",
	"module": "allsky_hddtemp",
	"version": "v1.0.1",
	"events": [
	    "night",
	    "day",
	    "periodic"
	],
	"experimental": "true",
	"centersettings": "false",
	"testable": "true",    
	"extradata": {
	    "info": {
	        "count": 4,
	        "firstblank": "true"
	    },
	    "values": {
	        "AS_HDDSDATEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sda in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDATEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sda in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDBTEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sdb in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDBTEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sdb in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDCTEMP": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Current temperature of sdc in C",
	            "type": "temperature"
	        },
	        "AS_HDDSDCTEMPMAX": {
	            "format": "",
	            "sample": "",
	            "group": "Environment",
	            "description": "Maximum temperature of sdc in C",
	            "type": "temperature"
	        }
	    }
	},
	"arguments": {
	    "usecolour": "False",
	    "oktemp": 30,
	    "okcolour": "green",
	    "badcolour": "red"
	},
	"argumentdetails": {
	    "hddnotice": {
	        "message": "<strong>NOTE</strong> S.M.A.R.T temperatures are always returned in degrees Celsius, use the overlay manager to reformat to another temperature unit if required",
	        "type": {
	            "fieldtype": "text",
	            "style": {
	                "width": "full",
					"alert": {
						"class": "info"
					}
				}
	        }
	    },        
	    "usecolour": {
	        "required": "false",
	        "description": "Use Colour",
	        "help": "Use colour for temperature fields",
	        "type": {
	            "fieldtype": "checkbox"
	        }          
	    },
	    "oktemp": {
	        "required": "true",
	        "description": "Ok Temp",
	        "help": "At or below this temperature hdd temp is ok",                
	        "type": {
	            "fieldtype": "spinner",
	            "min": 1,
	            "max": 100,
	            "step": 1
	        }
	    },
	    "okcolour": {
	        "required": "true",
	        "description": "Ok Colour",
	        "help": "Colour for an Ok temeprature"        
	    },
	    "badcolour": {
	        "required": "true",
	        "description": "Bad Colour",
	        "help": "Colour for a Bad temeprature"        
	    }
	},
	"enabled": "false",
	"changelog": {
	    "v1.0.0": [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Initial Release"
	        }
	    ],
	    "v1.0.1": [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": [
	                "Add exception handling",
	                "Converted to new format"
	            ]
	        }
	    ]
	}
}


def hddtemp(params, event):
	useColour = params['usecolour']
	okTemp = int(params['oktemp'])
	okColour = params['okcolour']
	badColour = params['badcolour']

	try:
	    debugMode = params["ALLSKYTESTMODE"]
	except ValueError:
	    debugMode = False
	    
	try:
	    SMARTCTL.sudo = True
	    devlist = DeviceList()
	    extraData = {}

	    result = ""

	    if len(devlist.devices) > 0:
	        for dev in devlist:
	            name = dev.name.upper()
	            tempData = dev.attributes[194]
	            if tempData is not None:
	                temp = tempData.raw_int
	                tempMax = tempData.worst

	                if temp is not None:
	                    hddName = f"AS_HDD{name}TEMP"
	                    if useColour:
	                        colour = okColour if temp <= okTemp else badColour
	                        extraData[hddName] = {
	                            "value": str(temp),
	                            "fill": colour
	                        }
	                        s.log(4, f"INFO: Temperature of {name} is {temp}C = {colour}, max is {okTemp}C")
	                    else:
	                        extraData[hddName] = str(temp)
	                        s.log(4, f"INFO: Temperature of {name} is {temp}")
	                else:
	                    result = f"No temperature data available for {name}"
	                    s.log(4, f"ERROR: {result}")

	                if tempMax is not None:
	                    hddName = f"AS_HDD{name}TEMPMAX"
	                    if useColour:
	                        colour = okColour if tempMax <= okTemp else badColour
	                        extraData[hddName] = {
	                            "value": str(tempMax),
	                            "fill": colour
	                        }
	                        s.log(4, f"INFO: Max temperature of {name} is {tempMax}C = {colour}, max is {okTemp}C")                            
	                    else:
	                        extraData[hddName] = str(tempMax)
	                        s.log(4, f"INFO: Max temperature of {name} is {temp}")
	                else:
	                    result1 = f"No max temperature data available for {name}"
	                    s.log(4, f"ERROR: {result1}")

	                    if result != "":
	                        result = f"{result}, {result1}"
	                    else:
	                        result = result1

	                if result == "":
	                    result = f"Ok Current: {temp}, Max: {tempMax}"

	                if debugMode:
	                    s.log(4, result)
	                    
	                s.saveExtraData("allskyhddtemp.json", extraData, metaData["module"], metaData["extradata"])

	            else:
	                s.log(4, f"ERROR: No temperature data (S.M.A.R.T 194) available for {name}")
	    else:
	        s.deleteExtraData("allskyhddtemp.json")
	        result = "No S.M.A.R.T devices found"
	        s.log(4, f"INFO: {result}")
	except Exception:
	    eType, eObject, eTraceback = sys.exc_info()
	    result = f"ERROR: Reading S.M.A.R.T attributes {eTraceback.tb_lineno} - {e}"
	    s.log(0, result)
	    
	return result


def hddtemp_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskyhddtemp.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)