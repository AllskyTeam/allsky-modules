'''
allsky_weatherunderground.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from the WeatherUnderground API

'''
import allsky_shared as s
import sys
from wunderground_pws import WUndergroundAPI, units

metaData = {
    "name": "WeatherUnderground",
    "description": "Gets weather data from the WeatherUnderground service",
    "module": "allsky_weatherunderground",
    "version": "v1.0.0",   
    "events": [
        "periodic"
    ],
    "arguments": {
        "apikey": "",
        "stationid": "",
        "period": 120,
        "filename": "wunderground.json",
        "units": "metric"
    },
    "argumentdetails": {
        "apikey": {
            "required": "true",
            "description": "API Key",
            "help": "Your WeatherUnderground API key"         
        },
        "stationid": {
            "required": "true",
            "description": "Station ID",
            "help": "Your WeatherUnderground station ID"
        },
        "filename": {
            "required": "true",
            "description": "Filename",
            "help": "The name of the file that will be written to the allsky/tmp/extra directory"         
        },        
        "period" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
            "type": {
                "fieldtype": "spinner",
                "min": 60,
                "max": 1440,
                "step": 1
            }          
        },
        "units" : {
            "required": "false",
            "description": "Units",
            "help": "Units of measurement. SI, metric, imperial and hybrid",
            "type": {
                "fieldtype": "select",
                "values": "metric_si,metric,imperial,uk_hybrid"
            }                
        }        
    },
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Michel Moriniaux",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ]
    }            
}

extraData = {}

def createCardinal(degrees):
    try:
        cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
        cardinal = cardinals[round(degrees / 22.5)]
    except Exception:
        cardinal = 'N/A'
    
    return cardinal


def processResult(params, data):
    extraData["AS_WUSTATIONID"] = data['stationID']
    extraData["AS_WUOBSTIME"] = data['obsTimeLocal']
    extraData["AS_WURADIATION"] = data['solarRadiation']
    extraData["AS_WUUV"] = data['uv']
    extraData["AS_WUWINDDIR"] = data['winddir']
    extraData["AS_WUWINDCARDINAL"] = createCardinal(data['winddir'])
    extraData["AS_WUTEMP"] = data[params['units']]['temp']
    extraData["AS_WUHEATINDEX"] = data[params['units']]['heatIndex']
    extraData["AS_WUDEWPOINT"] = data[params['units']]['dewpt']
    extraData["AS_WUWINDCHILL"] = data[params['units']]['windChill']
    extraData["AS_WUWINDGUST"] = data[params['units']]['windGust']
    extraData["AS_WUWINDSPEED"] = data[params['units']]['windSpeed']
    extraData["AS_WUPRECIPRATE"] = data[params['units']]['precipRate']
    extraData["AS_WUPRECIPTOTAL"] = data[params['units']]['precipTotal']
    extraData["AS_WUELEVATION"] = data[params['units']]['elev']
    extraData["AS_WUQNH"] = data[params['units']]['pressure']
    if params['units'] == "uk_hybrid":
        extraData["AS_WUQFE"] = str(float(extraData["AS_WUQNH"]) - (1.0988 * float(extraData["AS_WUELEVATION"]) / 30))
    if "metric" in params['units']:
        extraData["AS_WUQFE"] = str(float(extraData["AS_WUQNH"]) - (0.12 * float(extraData["AS_WUELEVATION"])))
    else:
        extraData["AS_WUQFE"] = str(float(extraData["AS_WUQNH"]) - (0.97 * float(extraData["AS_WUELEVATION"]) / 900))

def weatherunderground(params, event):
    global extraData    
    result = ""

    period = int(params["period"])
    apikey = params["apikey"]
    stationid = params["stationid"]
    fileName = params["filename"]
    module = metaData["module"]
    

    if params["units"] == "metric":
        unit = units.METRIC_UNITS
    if params["units"] == "metric_si":
        unit = units.METRIC_SI_UNITS
    if params["units"] == "imperial":
        unit = units.ENGLISH_UNITS
    if params["units"] == "uk_hybrid":
        unit = units.HYBRID_UNITS

    try:
        shouldRun, diff = s.shouldRun(module, period)
        if shouldRun:
            if fileName != "":
                if apikey != "":
                    if stationid != "":
                        allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
                        if allskyPath is not None:
                            try:
                                wu = WUndergroundAPI(api_key=apikey, default_station_id=stationid, units=unit)
                                response = wu.current()['observations'][0]
                                processResult(params, response)
                                print(extraData)
                                s.saveExtraData(fileName,extraData)
                                result = f"Data acquired and written to extra data file {fileName}"
                                s.log(1,f"INFO: {result}")
                                s.log(0,f"ERROR: {result}")
                            except Exception as e:
                                result = str(e)
                                s.log(0, f"ERROR: {result}")
                    else:
                        result = "Missing WeatherUnderground Station ID"
                        s.log(0,f"ERROR: {result}")                    
                else:
                    result = "Missing WeatherUnderground API key"
                    s.log(0,f"ERROR: {result}")
            else:
                result = "Missing filename for data"
                s.log(0,f"ERROR: {result}")

            s.setLastRun(module)
        else:
            result = f"Last run {diff} seconds ago. Running every {period} seconds"
            s.log(1,f"INFO: {result}")

    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module weatherunderground failed on line {eTraceback.tb_lineno} - {e}")    
        
    return result

def weatherunderground_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "wunderground.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
