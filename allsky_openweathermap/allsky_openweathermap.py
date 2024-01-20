'''
allsky_openweathermap.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from the Open Weather Map API

'''
import allsky_shared as s
import sys
import requests
import json
from meteocalc import heat_index
from meteocalc import dew_point, Temp

metaData = {
    "name": "Open Weather Map",
    "description": "Gets weather data from the Open Weather Map service",
    "module": "allsky_openweathermap",
    "version": "v1.0.1",   
    "events": [
        "periodic"
    ],
    "arguments":{
        "apikey": "",
        "period": 120,
        "expire": 240,
        "filename": "openweather.json",
        "units": "metric"
    },
    "argumentdetails": {
        "apikey": {
            "required": "true",
            "description": "API Key",
            "help": "Your Open Weather Map API key"         
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
            "help": "Units of measurement. standard, metric and imperial",
            "type": {
                "fieldtype": "select",
                "values": "standard,metric,imperial"
            }                
        },        
        "expire" : {
            "required": "true",
            "description": "Expiry Time",
            "help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
            "type": {
                "fieldtype": "spinner",
                "min": 61,
                "max": 1500,
                "step": 1
            }          
        }                    
    },
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
                    "Added Cardinal wind direction",
                    "Converted to f-strings",
                    "Improved error handling"
                ]
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
    
def processResult(data, expires, units):
    #rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
    #data = json.loads(rawData)
    setExtraValue("weather.main", data, "OWWEATHER", expires)
    setExtraValue("weather.description", data, "OWWEATHERDESCRIPTION", expires)

    setExtraValue("main.temp", data, "OWTEMP", expires)
    setExtraValue("main.feels_like", data, "OWTEMPFEELSLIKE", expires)
    setExtraValue("main.temp_min", data, "OWTEMPMIN", expires)
    setExtraValue("main.temp_max", data, "OWTEMPMAX", expires)
    setExtraValue("main.pressure", data, "OWPRESSURE", expires)
    setExtraValue("main.humidity", data, "OWHUMIDITY", expires)

    setExtraValue("wind.speed", data, "OWWINDSPEED", expires)
    setExtraValue("wind.deg", data, "OWWINDDIRECTION", expires)
    setExtraValue("wind.gust", data, "OWWINDGUST", expires)

    setExtraValue("clouds.all", data, "OWCLOUDS", expires)

    setExtraValue("rain.1hr", data, "OWRAIN1HR", expires)
    setExtraValue("rain.3hr", data, "OWRAIN3HR", expires)

    setExtraValue("sys.sunrise", data, "OWSUNRISE", expires)
    setExtraValue("sys.sunset", data, "OWSUNSET", expires)

    temperature = float(getValue("main.temp", data))
    humidity = float(getValue("main.humidity", data))
    if units == "imperial":
        t = Temp(temperature, 'f')
        dewPoint = dew_point(t, humidity).f
        heatIndex = heat_index(t, humidity).f
    
    if units == "metric":
        t = Temp(temperature, 'c')        
        dewPoint = dew_point(temperature, humidity).c
        heatIndex = heat_index(temperature, humidity).c

    if units == "standard":
        t = Temp(temperature, 'k')        
        dewPoint = dew_point(temperature, humidity).k
        heatIndex = heat_index(temperature, humidity).k

    degress = getValue('wind.deg', data)
    cardinal = createCardinal(degress)

    extraData["AS_OWWINDCARDINAL"] = {
        "value": cardinal,
        "expires": expires
    }
                
    extraData["AS_OWDEWPOINT"] = {
        "value": round(dewPoint,1),
        "expires": expires
    }
        
    extraData["AS_OWHEATINDEX"] = {
        "value": round(heatIndex,1),
        "expires": expires
    }

def setExtraValue(path, data, extraKey, expires):
    global extraData
    value = getValue(path, data)
    if value is not None:
        extraData["AS_" + extraKey] = {
            "value": value,
            "expires": expires
        }

def getValue(path, data):
    result = None
    keys = path.split(".")
    if keys[0] in data:
        subData = data[keys[0]]
        
        if isinstance(subData, list):        
            if keys[1] in subData[0]:
                result = subData[0][keys[1]]
        else:
            if keys[1] in subData:
                result = subData[keys[1]]
    
    return result

def openweathermap(params, event):
    global extraData    
    result = ""

    expire = int(params["expire"])
    period = int(params["period"])
    apikey = params["apikey"]
    fileName = params["filename"]
    module = metaData["module"]
    units = params["units"]

    try:
        shouldRun, diff = s.shouldRun(module, period)
        if shouldRun:
            if fileName != "":
                if apikey != "":
                    allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
                    if allskyPath is not None:
                        lat = s.getSetting("latitude")
                        if lat is not None and lat != "":
                            lat = s.convertLatLon(lat)
                            lon = s.getSetting("longitude")
                            if lon is not None and lon != "":
                                lon = s.convertLatLon(lon)
                                try:
                                    resultURL = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&units={2}&appid={3}".format(lat, lon, units, apikey)
                                    s.log(4,f"INFO: URL - {resultURL}")
                                    response = requests.get(resultURL)
                                    if response.status_code == 200:
                                        rawData = response.json()
                                        processResult(rawData, expire, units)
                                        s.saveExtraData(fileName,extraData )
                                        result = f"Data acquired and written to extra data file {fileName}"
                                        s.log(1,f"INFO: {result}")
                                    else:
                                        result = f"Got error from Open Weather Map API. Response code {response.status_code}"
                                        s.log(0,f"ERROR: {result}")
                                except Exception as e:
                                    result = str(e)
                                    s.log(0, f"ERROR: {result}")
                            else:
                                result = "Invalid Longitude. Check the Allsky configuration"
                                s.log(0,f"ERROR: {result}")
                        else:
                            result = "Invalid Latitude. Check the Allsky configuration"
                            s.log(0,f"ERROR: {result}")
                    else:
                        result = "Cannot find ALLSKY_HOME Environment variable"
                        s.log(0,f"ERROR: {result}")                    
                else:
                    result = "Missing Open Weather Map API key"
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
        s.log(0, f"ERROR: Module openweathermap failed on line {eTraceback.tb_lineno} - {e}")    
        
    return result

def openweathermap_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "openweather.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)