'''
allsky_light.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


'''
import allsky_shared as s
import sys
import math
import board
import busio
import adafruit_tsl2591
import adafruit_tsl2561

metaData = {
    "name": "AllSky Light Meter",
    "description": "Estimates sky brightness",
    "module": "allsky_light",
    "version": "v1.0.2",    
    "events": [
        "periodic"
    ],
    "experimental": "false",    
    "arguments":{
        "type": "",
        "i2caddress": "",
        "tsl2591gain": "25x",
        "tsl2591integration": "100ms",
        "tsl2561gain": "Low",
        "tsl2561integration": "101ms",
        "extradatafilename": "allskylight.json"
    },
    "argumentdetails": {
        "type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "type": {
                "fieldtype": "select",
                "values": "None,TSL2591,TSL2561",
                "default": "None"
            }                
        },        
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for the sensor. NOTE: This value must be hex i.e. 0x76"
        },
        "tsl2591gain" : {
            "required": "false",
            "description": "TSL2591 Gain",
            "help": "The gain for the TSL2591 sensor.",
            "tab": "TSL2591",            
            "type": {
                "fieldtype": "select",
                "values": "1x,25x,428x,9876x",
                "default": "25x"
            }                
        },
        "tsl2591integration" : {
            "required": "false",
            "description": "TSL2591 Integration time",
            "help": "The integration time for the TSL2591 sensor.",
            "tab": "TSL2591",            
            "type": {
                "fieldtype": "select",
                "values": "100ms,200ms,300ms,400ms,500ms,600m2",
                "default": "100ms"
            }                
        },
        "tsl2561gain" : {
            "required": "false",
            "description": "TSL2561 Gain",
            "help": "The gain for the TSL2561 sensor.",
            "tab": "TSL2561",            
            "type": {
                "fieldtype": "select",
                "values": "Low,High",
                "default": "Low"
            }                
        },
        "tsl2561integration" : {
            "required": "false",
            "description": "TSL2561 Integration time",
            "help": "The integration time for the TSL2561 sensor.",
            "tab": "TSL2561",
            "type": {
                "fieldtype": "select",
                "values": "13.7ms,101ms,402ms",
                "default": "101ms"
            }                
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Advanced",
            "help": "The name of the file to create with the data for the overlay manager"
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
                    "Added ability to change the extra data filename",
                    "Added changelog to metadata"
                ]
            }
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Fixed error where i2c address was not passed to python modules",
                    "Added additional error handling"
                ]
            }
        ]                                        
    }           
}

def readTSL2591(params):
    sensor = None
    i2c = board.I2C()
    i2caddress = params['i2caddress']
    if i2caddress != '':
        try:
            i2caddressInt = int(i2caddress, 16)
            sensor = adafruit_tsl2591.TSL2591(i2c, i2caddressInt)
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f"ERROR: Module readTSL2591 failed on line {eTraceback.tb_lineno} - {e}")
    else: 
        sensor = adafruit_tsl2591.TSL2591(i2c)
        
    lux = None
    infrared = None
    visible = None
                    
    if sensor is not None:    
        gain = params["tsl2591gain"]
        if gain == "1x":
            sensor.gain = adafruit_tsl2591.GAIN_LOW
        if gain == "25x":    
            sensor.gain = adafruit_tsl2591.GAIN_MED
        if gain == "428x":
            sensor.gain = adafruit_tsl2591.GAIN_HIGH
        if gain == "9876x":
            sensor.gain = adafruit_tsl2591.GAIN_MAX
        
        integration = params["tsl2591integration"]    
        if integration == "100ms":
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS
        if integration == "200ms":        
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_200MS
        if integration == "300ms":        
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_300MS
        if integration == "400ms":        
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_400MS
        if integration == "500ms":        
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_500MS
        if integration == "600ms":        
            sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_600MS
                
        lux = sensor.lux
        infrared = sensor.infrared
        visible = sensor.visible
    
    return lux, infrared, visible

def readTSL2561(params):
    tsl = None
    i2c = busio.I2C(board.SCL, board.SDA)
    
    i2caddress = params['i2caddress']
    if i2caddress != '':
        try:
            i2caddressInt = int(i2caddress, 16)
            tsl = adafruit_tsl2561.TSL2561(i2c, i2caddressInt)
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f"ERROR: Module readTSL2561 failed on line {eTraceback.tb_lineno} - {e}")
    else: 
        tsl = adafruit_tsl2561.TSL2561(i2c)
    
    lux = None
    infrared = None
    visible = None
    if tsl is not None:
        if params["tsl2561gain"] == "Low":
            tsl.gain = 0
        else:
            tsl.gain = 1        
        
        if params["tsl2561integration"] == "13.7ms":
            tsl.integration_time = 0
        if params["tsl2561integration"] == "101ms":
            tsl.integration_time = 1
        if params["tsl2561integration"] == "402ms":
            tsl.integration_time = 2
            
        visible = tsl.broadband
        infrared = tsl.infrared

        lux = tsl.lux
        if lux is None:
            lux = 0

    return lux, infrared, visible
    
def light(params, event):
    result = ''

    extradatafilename = params['extradatafilename']
    sensor = params["type"].lower()
    if sensor != "none":
        if sensor == "tsl2591":
            lux, infrared, visible = readTSL2591(params)

        if sensor == "tsl2561":
            lux, infrared, visible = readTSL2561(params)
                
        if lux is not None:
            sqm = math.log10(lux / 108000) / -0.45
            nelm = 7.93 - 5.0 * math.log10((pow(10, (4.316 - (sqm / 5.0))) + 1.0))
            
            extraData = {}
            extraData["AS_LIGHTLUX"] = str(lux)
            extraData["AS_LIGHTNELM"] = str(nelm)
            extraData["AS_LIGHTSQM"] = str(sqm)
            s.saveExtraData("allskylight.json",extraData)
            result = f"Lux {lux}, NELM {nelm}, SQM {sqm}"
            s.log(4, f"INFO: {result}")
        else:
            s.deleteExtraData(extradatafilename)
            s.log(0, f'ERROR: Error reading {sensor}')
    else:
        s.deleteExtraData(extradatafilename)
        result = "No sensor defined"
        s.log(0, f"ERROR: {result}")
        
    return result

def light_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskylight.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)