'''
allsky_ltr390.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import board
import sys
from adafruit_ltr390 import LTR390, MeasurementDelay, Resolution, Gain


metaData = {
	"name": "LTR390 (UV Level)",
	"description": "Provides UV Levels",
	"module": "allsky_ltr390",
	"version": "v1.0.1",
	"events": [
	    "periodic"
	],
	"experimental": "true",    
	"arguments":{
	    "i2caddress": "",
	    "resolution": "",
	    "gain": "",
	    "measurementdelay": ""
	},
	"argumentdetails": {   
	    "i2caddress" : {
	        "required": "false",
	        "description": "I2C Address",
	        "help": "The i2c address of the ltr390. Defauults to 0x53"        
	    },
	    "resolution" : {
	        "required": "false",
	        "description": "Sensor Resoluton",
	        "help": "The resolution of the internal ADC",
	        "type": {
	            "fieldtype": "select",
	            "values": "Default,13Bit,16Bit,17Bit,18Bit,19Bit,20Bit",
	            "default": "None"
	        }                
	    },
	    "gain" : {
	        "required": "false",
	        "description": "Gain",
	        "help": "ALS and UVS gain range",
	        "type": {
	            "fieldtype": "select",
	            "values": "Default,1x,3x,6x,9x,18x",
	            "default": "None"
	        }                
	    },
	    "measurementdelay" : {
	        "required": "false",
	        "description": "Delay",
	        "help": "Delay between measurements, useful for power saving",
	        "type": {
	            "fieldtype": "select",
	            "values": "Default,25ms,50ms,100ms,200ms,500ms,1000ms,2000ms",
	            "default": "None"
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
	                "Moved to periodic flow",
	                "Added addition error logging"
	            ]
	        }
	    ]                                                   
	}                  
}

def ltr390(params, event):
	i2caddress = params["i2caddress"]
	resolution = params["resolution"]
	measurementdelay = params["measurementdelay"]
	gain = params["gain"]    
	uvs = None
	light = None
	uvi = None
	lux = None
	ok = True

	if i2caddress != "":
	    try:
	        i2caddressInt = int(i2caddress, 16)
	    except:
	        result = f"Address {i2caddress} is not a valid i2c address"
	        s.log(0,f"ERROR: {result}")
	        ok = False

	if ok:
	    try:
	        i2c = board.I2C()
	        if i2caddress != "":
	            ltr = LTR390(i2c, i2caddressInt)
	        else:
	            ltr = LTR390(i2c)

	        if resolution != "":
	            if resolution == "13Bit":
	                ltr.resolution = Resolution.RESOLUTION_13BIT
	            if resolution == "16Bit":
	                ltr.resolution = Resolution.RESOLUTION_16BIT
	            if resolution == "17Bit":
	                ltr.resolution = Resolution.RESOLUTION_17BIT
	            if resolution == "18Bit":
	                ltr.resolution = Resolution.RESOLUTION_18BIT
	            if resolution == "19Bit":
	                ltr.resolution = Resolution.RESOLUTION_19BIT
	            if resolution == "20Bit":
	                ltr.resolution = Resolution.RESOLUTION_20BIT
	                
	        if gain != "":
	            if gain == "1x":
	                ltr.gain = Gain.GAIN_1X
	            if gain == "3x":
	                ltr.gain = Gain.GAIN_3X
	            if gain == "6x":
	                ltr.gain = Gain.GAIN_6X
	            if gain == "9x":
	                ltr.gain = Gain.GAIN_9X
	            if gain == "18x":
	                ltr.gain = Gain.GAIN_18X

	        if measurementdelay != "":
	            if measurementdelay == "25ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_25MS
	            if measurementdelay == "50ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_50MS
	            if measurementdelay == "100ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_100MS
	            if measurementdelay == "200ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_200MS
	            if measurementdelay == "500ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_500MS
	            if measurementdelay == "1000ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_1000MS
	            if measurementdelay == "2000ms":
	                ltr.measurement_delay = MeasurementDelay.DELAY_2000MS


	        uvs = ltr.uvs
	        light = ltr.light
	        uvi = ltr.uvi
	        lux = ltr.lux

	        extraData = {}
	        extraData["AS_LTR390UVS"] = str(uvs)
	        extraData["AS_LTR390LIGHT"] = str(light)
	        extraData["AS_LTR390UVI"] = str(uvi)
	        extraData["AS_LTR390LUX"] = str(lux)
	        
	        s.saveExtraData("allskyltr390.json", extraData)

	        result = f"LTR390 Read Ok UVS={uvs} LIGHT={light} UVI={uvi} LUX={lux} Resolution {Resolution.string[ltr.resolution]} Gain {Gain.string[ltr.gain]} Delay {MeasurementDelay.string[ltr.measurement_delay]}"
	        s.log(4,f"INFO: {result}")
	    except Exception as e:
	        eType, eObject, eTraceback = sys.exc_info()
	        result = f"Module ltr390 failed on line {eTraceback.tb_lineno} - {e}"
	        s.log(1, f"ERROR: {result}")

	return result

def ltr390_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskyltr390.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)