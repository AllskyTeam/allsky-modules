'''
allsky_openweathermap.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve data from the Open Weather Map API

'''
import allsky_shared as s
import os
import requests
import json

metaData = {
    "name": "Open Weather Map",
    "description": "Gets weather data from the Open Weather Map service",
    "module": "allsky_openweathermap",       
    "events": [
        "periodic"
    ],
    "arguments":{
        "apikey": "",
        "period": 120,
        "expire": 240,
        "filename": "openweather.json"
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
    }      
}

extraData = {}

def processResult(rawData, expires):
    rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
    data = json.loads(rawData)
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

    shouldRun, diff = s.shouldRun(module, period)
    if shouldRun:
        if fileName != "":
            if apikey != "":
                allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
                if allskyPath is not None:
                    extraDataPath = os.path.join(allskyPath, "tmp", "extra")
                    s.checkAndCreatePath(extraDataPath)
                    extraDataFilename = os.path.join(extraDataPath, fileName)
                    lat = s.getSetting("latitude")
                    if lat is not None and lat != "":
                        lat = s.convertLatLon(lat)
                        lon = s.getSetting("longitude")
                        if lon is not None and lon != "":
                            lon = s.convertLatLon(lon)
                            try:
                                resultURL = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&appid={2}".format(lat, lon, apikey)
                                response = requests.get(resultURL)
                                if response.status_code == 200:
                                    rawData = response.json()
                                    processResult(rawData, expire)
                                    with open(extraDataFilename, "w") as file:
                                        formattedJSON = json.dumps(extraData, indent=4)
                                        file.write(formattedJSON)
                                    result = "Data acquired and written to extra data file {}".format(extraDataFilename)
                                    s.log(1,"INFO: {}".format(result))
                                else:
                                    result = "Got error from Open Weather Map API. Response code {}".format(response.status_code)
                                    s.log(0,"ERROR: {}".format(result))
                            except Exception as e:
                                result = str(e)
                                s.log(0, "ERROR: {}".format(result))
                        else:
                            result = "Invalid Longitude. Check the Allsky configuration"
                            s.log(0,"ERROR: {}".format(result))
                    else:
                        result = "Invalid Latitude. Check the Allsky configuration"
                        s.log(0,"ERROR: {}".format(result))
                else:
                    result = "Cannot find ALLSKY_HOME Environment variable"
                    s.log(0,"ERROR: {}".format(result))                    
            else:
                result = "Missing Open Weather Map API key"
                s.log(0,"ERROR: {}".format(result))
        else:
            result = "Missing filename for data"
            s.log(0,"ERROR: {}".format(result))

        s.setLastRun(module)
    else:
        result = "Last run {} seconds ago. Running every {} seconds".format(diff, period)
        s.log(1,"INFO: {}".format(result))

    return result