'''
allsky_hddtemp.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
from pySMART import SMARTCTL, DeviceList

metaData = {
    "name": "HDD Temp",
    "description": "Provides HDD Temps",
    "module": "allsky_hddtemp",
    "version": "v1.0.0",    
    "events": [
        "night",
        "day",
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "usecolour": "False",
        "oktemp": 30,
        "okcolour": "green",
        "badcolour": "red"
    },
    "argumentdetails": {   
        "usecolour" : {
            "required": "false",
            "description": "Use Colour",
            "help": "Use colour for temperature fields",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "oktemp" : {
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
        "okcolour" : {
            "required": "true",
            "description": "Ok Colour",
            "help": "Colour for an Ok temeprature"        
        },
        "badcolour" : {
            "required": "true",
            "description": "Bad Colour",
            "help": "Colour for a Bad temeprature"        
        }                                                       
    },
    "enabled": "false"            
}

def hddtemp(params, event):
    useColour = params['usecolour']
    okTemp = int(params['oktemp'])
    okColour = params['okcolour']
    badColour = params['badcolour']

    SMARTCTL.sudo = True
    devlist = DeviceList()
    extraData = {}

    result = ""

    if len(devlist.devices) > 0:
        for dev in devlist:
            name = dev.name.upper()
            tempData = dev.attributes[194]
            if tempData is not None:
                 def smart_temp_signed(val):
                     if val is None:
                         return None
                 return val - 256 if val > 127 else val

                 temp = smart_temp_signed(tempData.raw_int)
                 tempMax = smart_temp_signed(tempData.worst)

                if temp is not None:
                    hddName = f"AS_HDD{name}TEMP"
                    if useColour:
                        extraData[hddName] = {
                            "value": str(temp),
                            "fill": okColour if temp <= okTemp else badColour
                        }
                    else:
                        extraData[hddName] = str(temp)
                else:
                    result = f"No temperature data available for {name}"
                    s.log(4,f"ERROR: {result}")
                
                if tempMax is not None:
                    hddName = f"AS_HDD{name}TEMPMAX"
                    if useColour:
                        extraData[hddName] = {
                            "value": str(tempMax),
                            "fill": okColour if tempMax < okTemp else badColour
                        }
                    else:
                        extraData[hddName] = str(tempMax)
                else:
                    result1 = f"No max temperature data available for {name}"
                    s.log(4,f"ERROR: {result1}")

                    if result != "":
                        result = f"{result}, {result1}"
                    else:
                        result = result1

                if result == "":
                    result = f"Ok Current: {temp}, Max: {tempMax}"
                
                s.saveExtraData("allskyhddtemp.json",extraData)                        

            else:
                s.log(4,f"ERROR: No temperature data (S.M.A.R.T 194) available for {name}")
    else:
        s.deleteExtraData("allskyhddtemp.json")
        result = "No S.M.A.R.T devices found"
        s.log(4,f"INFO: {result}")


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
