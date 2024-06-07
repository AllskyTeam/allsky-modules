'''
allsky_dewheater.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Changelog
v1.0.1 by Damian Grocholski (Mr-Groch)
- Added extra pin that is triggered with heater pin
- Fixed dhtxxdelay (was not implemented)
- Fixed max heater time (was not implemented)
V1.0.2 by Alex Greenland
- Updated code for pi 5
V1.0.3 by Alex Greenland
- Add AHTx0 i2c sensor
V1.0.4 by Andreas Schminder 
- Added Solo Cloudwatcher
'''
import allsky_shared as s
import time
import sys
import os
import json
import urllib.request
import requests
import json
from meteocalc import heat_index
from meteocalc import dew_point, Temp
import board
import adafruit_sht31d
import adafruit_dht
import adafruit_ahtx0
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_htu21d import HTU21D
from meteocalc import heat_index
from meteocalc import dew_point
from digitalio import DigitalInOut, Direction, Pull
    
metaData = {
    "name": "Sky Dew Heater Control",
    "description": "Controls a dew heater via a temperature and humidity sensor",
    "module": "allsky_dewheater",
    "version": "v1.0.5",
    "events": [
        "periodic"
    ],
    "experimental": "false",
    "arguments":{
        "type": "None",
        "inputpin": "",
        "heaterpin": "",
        "extrapin": "",
        "i2caddress": "",
        "heaterstartupstate": "OFF",
        "invertrelay": "False",
        "invertextrapin": "False",
        "frequency": "0",
        "limit": "10",
        "force": "0",
        "max": "0",
        "dhtxxretrycount": "2",
        "dhtxxdelay" : "500",
        "extradatafilename": "allskydew.json",
        "sht31heater": "False",
        "solourl": "",
        "apikey": "",
        "period": 120,
        "expire": 240,
        "filename": "openweather.json",
        "units": "metric"        
    },
    "argumentdetails": {
        "type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0,SOLO-Cloudwatcher,OpenWeather",
                "default": "None"
            }
        },
        "inputpin": {
            "required": "false",
            "description": "Input Pin",
            "help": "The input pin for DHT type sensors, not required for i2c devices",
            "tab": "Sensor",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor"
        },
        "dhtxxretrycount" : {
            "required": "false",
            "description": "Retry Count",
            "help": "The number of times to retry the sensor read",
            "tab": "DHTXX",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5,
                "step": 1
            }
        },
        "dhtxxdelay" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between faild sensor reads in milliseconds",
            "tab": "DHTXX",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5000,
                "step": 1
            }
        },
        "heaterpin": {
            "required": "false",
            "description": "Heater Pin",
            "help": "The pin the heater control relay is connected to",
            "tab": "Heater",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "extrapin": {
            "required": "false",
            "description": "Extra Pin",
            "help": "Extra pin that will be triggered with heater pin",
            "tab": "Heater",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "heaterstartupstate" : {
            "required": "false",
            "description": "heater Startup State",
            "help": "The initial state of the dew heater when allsky is started. This is only used if there is no previous status",
            "tab": "Heater",
            "type": {
                "fieldtype": "select",
                "values": "ON,OFF",
                "default": "OFF"
            }
        },
        "invertrelay" : {
            "required": "false",
            "description": "Invert Relay",
            "help": "Normally a GPIO pin will go high to enable a relay. Selecting this option if the relay is wired to activate on the GPIO pin going Low",
            "tab": "Heater",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "invertextrapin" : {
            "required": "false",
            "description": "Invert Extra Pin",
            "help": "Normally a GPIO extra pin will go high when ebabling heater. Selecting this option inverts extra pin to go low when enabling heater",
            "tab": "Heater",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "frequency" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between sensor reads in seconds. Zero will disable this and run the check every time the periodic jobs run",
            "tab": "Dew Control",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 1
            }
        },
        "limit" : {
            "required": "false",
            "description": "Limit",
            "help": "If the temperature is within this many degrees of the dew point the heater will be enabled or disabled",
            "tab": "Dew Control",
            "type": {
                "fieldtype": "spinner",
                "min": -100,
                "max": 100,
                "step": 1
            }
        },
        "force" : {
            "required": "false",
            "description": "Forced Temperature",
            "help": "Always enable the heater when the ambient termperature is below this value, zero will disable this.",
            "tab": "Dew Control",
            "type": {
                "fieldtype": "spinner",
                "min": -100,
                "max": 100,
                "step": 1
            }
        },
        "max" : {
            "required": "false",
            "description": "Max Heater Time",
            "help": "The maximum time in seconds for the heater to be on. Zero will disable this.",
            "tab": "Dew Control",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 86400,
                "step": 1
            }
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Misc",
            "help": "The name of the file to create with the dew heater data for the overlay manager"
        },
        "sht31heater" : {
            "required": "false",
            "description": "Enable Heater",
            "help": "Enable the inbuilt heater on the SHT31",
            "tab": "SHT31",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "solourl": {
            "required": "false",
            "description": "URL from solo",
            "help": "Read weather data from lunaticoastro.com 'Solo Cloudwatcher'",
            "tab": "Solo"
        },
        
        "apikey": {
            "required": "false",
            "description": "API Key",
            "tab": "OpenWeather",            
            "help": "Your Open Weather Map API key. <b style='color: #ff0000'>IMPORTANT</b> Do not use this function and the OpenWeather API module as well. If you are using this function then please remove the OpenWeather Module as both create the same overlay data"         
        },
        "filename": {
            "required": "true",
            "description": "Filename",
            "tab": "OpenWeather",            
            "help": "The name of the file that will be written to the allsky/tmp/extra directory"         
        },        
        "period" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds. Be careful of the free 1000 request limit per day",                
            "tab": "OpenWeather",            
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
            "tab": "OpenWeather",            
            "type": {
                "fieldtype": "select",
                "values": "standard,metric,imperial"
            }                
        },        
        "expire" : {
            "required": "true",
            "description": "Expiry Time",
            "help": "Number of seconds the data is valid for MUST be higher than the 'Read Every' value",
            "tab": "OpenWeather",            
            "type": {
                "fieldtype": "spinner",
                "min": 61,
                "max": 1500,
                "step": 1
            }          
        }    
                        
    },
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
                "author": "Damian Grocholski (Mr-Groch)",
                "authorurl": "https://github.com/Mr-Groch",
                "changes": [
                    "Added extra pin that is triggered with heater pin",
                    "Fixed dhtxxdelay (was not implemented)",
                    "Fixed max heater time (was not implemented)"
                ]
            }
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.4" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Add AHTx0 i2c sensor"
            },            
            {
                "author": "Andreas Schminder",
                "authorurl": "https://github.com/Adler6907",
                "changes": "Added Solo Cloudwatcher"
            }
        ],
        "v1.0.5" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Added OpenWeather option"
            }
        ]                                        
    }
}

def createCardinal(degrees):
    try:
        cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW','W', 'WNW', 'NW', 'NNW', 'N']
        cardinal = cardinals[round(degrees / 22.5)]
    except Exception:
        cardinal = 'N/A'
    
    return cardinal

def setExtraValue(path, data, extraKey, expires, extraData):
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

def processResult(data, expires, units):
    extraData = {}
    #rawData = '{"coord":{"lon":0.2,"lat":52.4},"weather":[{"id":802,"main":"Clouds","description":"scattered clouds","icon":"03d"}],"base":"stations","main":{"temp":291.84,"feels_like":291.28,"temp_min":290.91,"temp_max":292.65,"pressure":1007,"humidity":58},"visibility":10000,"wind":{"speed":8.23,"deg":250,"gust":10.8},"clouds":{"all":40},"dt":1664633294,"sys":{"type":2,"id":2012440,"country":"GB","sunrise":1664603991,"sunset":1664645870},"timezone":3600,"id":2633751,"name":"Witchford","cod":200}'
    #data = json.loads(rawData)
    setExtraValue("weather.main", data, "OWWEATHER", expires, extraData)
    setExtraValue("weather.description", data, "OWWEATHERDESCRIPTION", expires, extraData)

    setExtraValue("main.temp", data, "OWTEMP", expires, extraData)
    setExtraValue("main.feels_like", data, "OWTEMPFEELSLIKE", expires, extraData)
    setExtraValue("main.temp_min", data, "OWTEMPMIN", expires, extraData)
    setExtraValue("main.temp_max", data, "OWTEMPMAX", expires, extraData)
    setExtraValue("main.pressure", data, "OWPRESSURE", expires, extraData)
    setExtraValue("main.humidity", data, "OWHUMIDITY", expires, extraData)

    setExtraValue("wind.speed", data, "OWWINDSPEED", expires, extraData)
    setExtraValue("wind.deg", data, "OWWINDDIRECTION", expires, extraData)
    setExtraValue("wind.gust", data, "OWWINDGUST", expires, extraData)

    setExtraValue("clouds.all", data, "OWCLOUDS", expires, extraData)

    setExtraValue("rain.1hr", data, "OWRAIN1HR", expires, extraData)
    setExtraValue("rain.3hr", data, "OWRAIN3HR", expires, extraData)

    setExtraValue("sys.sunrise", data, "OWSUNRISE", expires, extraData)
    setExtraValue("sys.sunset", data, "OWSUNSET", expires, extraData)

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
    
    return extraData

def getOWValue(field, jsonData, fileModifiedTime):
    result = False    
    
    if field in jsonData:
        result = jsonData[field]["value"]
    
    if "expires" in jsonData[field]:
        maxAge = jsonData[field]["expires"]
        age = int(time.time()) - fileModifiedTime
        if age > maxAge:
            s.log(4, f"WARNING: field {field} has expired - age is {age}")
            result = None
            
    return result
                    
def getOWValues(fileName):
    temperature = None
    humidity = None
    pressure = None
    dewPoint = None
    
    allskyPath = s.getEnvironmentVariable("ALLSKY_HOME")
    extraDataFileName = os.path.join(allskyPath, "config", "overlay", "extra", fileName)
    
    if os.path.isfile(extraDataFileName):
        fileModifiedTime = int(os.path.getmtime(extraDataFileName))
        with open(extraDataFileName,"r") as file:
            jsonData = json.load(file)
            temperature = getOWValue("AS_OWTEMP", jsonData, fileModifiedTime)
            humidity = getOWValue("AS_OWHUMIDITY", jsonData, fileModifiedTime)
            pressure = getOWValue("AS_OWPRESSURE", jsonData, fileModifiedTime)
            dewPoint = getOWValue("AS_OWDEWPOINT", jsonData, fileModifiedTime)

    return temperature, humidity, pressure, dewPoint
    
def readOpenWeather(params):
    expire = int(params["expire"])
    period = int(params["period"])
    apikey = params["apikey"]
    fileName = params["filename"]
    module = metaData["module"]
    units = params["units"]
    temperature = None
    humidity = None
    pressure = None
    dewPoint = None
    
    try:
        shouldRun, diff = s.shouldRun(module, period)
        if shouldRun:
            if apikey != "":
                if fileName != "":
                    lat = s.getSetting("latitude")
                    if lat is not None and lat != "":
                        lat = s.convertLatLon(lat)
                        lon = s.getSetting("longitude")
                        if lon is not None and lon != "":
                            lon = s.convertLatLon(lon)
                            try:
                                resultURL = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&units={2}&appid={3}".format(lat, lon, units, apikey)
                                s.log(4,f"INFO: Reading Openweather API from - {resultURL}")
                                response = requests.get(resultURL)
                                if response.status_code == 200:
                                    rawData = response.json()
                                    extraData = processResult(rawData, expire, units)
                                    s.saveExtraData(fileName, extraData )
                                    result = f"Data acquired and written to extra data file {fileName}"
                                    s.log(1,f"INFO: {result}")
                                else:
                                    result = f"Got error from Open Weather Map API. Response code {response.status_code}"
                                    s.log(0,f"ERROR: {result}")
                            except Exception as e:
                                result = str(e)
                                s.log(0, f"ERROR: {result}")
                            s.setLastRun(module)                            
                        else:
                            result = "Invalid Longitude. Check the Allsky configuration"
                            s.log(0,f"ERROR: {result}")
                    else:
                        result = "Invalid Latitude. Check the Allsky configuration"
                        s.log(0,f"ERROR: {result}")
                else:
                    result = "Missing filename for data"
                    s.log(0,f"ERROR: {result}")
            else:
                result = "Missing Open Weather Map API key"
                s.log(0,f"ERROR: {result}")
        else:
            s.log(4,f"INFO: Using Cached Openweather API data")
            
        temperature, humidity, pressure, dewPoint = getOWValues(fileName)                
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module readOpenWeather failed on line {eTraceback.tb_lineno} - {e}")   
    
    return temperature, humidity, pressure, dewPoint

def readSHT31(sht31heater, i2caddress):
    temperature = None
    humidity = None
    
    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f"ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}")
            return temperature, humidity
                
    try:
        i2c = board.I2C()
        if i2caddress != "":
            sensor = adafruit_sht31d.SHT31D(i2c, i2caddressInt)
        else:
            sensor = adafruit_sht31d.SHT31D(i2c)
        sensor.heater = sht31heater
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(4, f"ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity

def doDHTXXRead(inputpin):
    temperature = None
    humidity = None

    try:
        pin = s.getGPIOPin(inputpin)
        dhtDevice = adafruit_dht.DHT22(pin, use_pulseio=False)
        try:
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity
        except RuntimeError as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(4, f"ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(4, f"WARNING: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity

def readDHT22(inputpin, dhtxxretrycount, dhtxxdelay):
    temperature = None
    humidity = None
    count = 0
    reading = True

    while reading:
        temperature, humidity = doDHTXXRead(inputpin)

        if temperature is None and humidity is None:
            s.log(4, "WARNING: Failed to read DHTXX on attempt {}".format(count+1))
            count = count + 1
            if count > dhtxxretrycount:
                reading = False
            else:
                time.sleep(dhtxxdelay/1000)
        else:
            reading = False

    return temperature, humidity

def readBme280I2C(i2caddress):
    temperature = None
    humidity = None
    pressure = None
    relHumidity = None
    altitude = None

    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

    try:
        i2c = board.I2C()
        if i2caddress != "":
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, i2caddressInt)
        else:
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

        temperature =  bme280.temperature
        humidity = bme280.relative_humidity
        relHumidity = bme280.relative_humidity
        altitude = bme280.altitude
        pressure = bme280.pressure
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity, pressure, relHumidity, altitude

def readHtu21(i2caddress):
    temperature = None
    humidity = None

    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except:
            result = "Address {} is not a valid i2c address".format(i2caddress)
            s.log(0,"ERROR: {}".format(result))

    try:
        i2c = board.I2C()
        if i2caddress != "":
            htu21 = HTU21D(i2c, i2caddressInt)
        else:
            htu21 = HTU21D(i2c)

        temperature =  htu21.temperature
        humidity = htu21.relative_humidity
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(4, f"ERROR: Module readHtu21 failed on line {eTraceback.tb_lineno} - {e}")
        
    return temperature, humidity

def readAHTX0(i2caddress):
    temperature = None
    humidity = None

    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except:
            result = "Address {} is not a valid i2c address".format(i2caddress)
            s.log(0,"ERROR: {}".format(result))

    try:
        i2c = board.I2C()
        sensor = adafruit_ahtx0.AHTx0(i2c)
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
    except ValueError as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(4, f"ERROR: Module readAHTX0 failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity

def readSolo(url):
    temperature = None
    humidity = None
    pressure = None
    dewPoint = None
    
    try: 
        #Read Weaterdata from SOLO Website
        jsonData = urllib.request.urlopen(url).read()  
        currentWeatherdata =  json.loads(jsonData)['LastReadings']

        # that is what you should receive
        #    { "LastReadings": {
        #    "dataGMTTime" : "2023/12/17 22:52:40",
        #    "cwinfo" : "Serial: 2550, FW: 5.89",
        #    "clouds" : -14.850000,
        #    "cloudsSafe" : "Unsafe",
        #    "temp" : 8.450000,
        #    "wind" : 12,
        #    "windSafe" : "Safe",
        #    "gust" : 13,
        #    "rain" : 3072,
        #    "rainSafe" : "Safe",
        #    "lightmpsas" : 20.31,
        #    "lightSafe" : "Safe",
        #    "switch" : 0,
        #    "safe" : 0,
        #    "hum" : 65,
        #    "humSafe" : "Safe",
        #    "dewp" : 2.250000,
        #    "rawir" : -19.150000,
        #    "abspress" : 1003.600000,
        #    "relpress" : 1032.722598,
        #    "pressureSafe" : "Safe"
        #    }
        #    }        
            
        temperature = float(currentWeatherdata['temp'])
        humidity = float(currentWeatherdata['hum'])
        pressure = float(currentWeatherdata['relpress'])
        dewPoint = float(currentWeatherdata['dewp'])
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(4, f"ERROR: Module readSolo failed on line {eTraceback.tb_lineno} - {e}")
            
    return temperature, humidity, pressure, dewPoint

def turnHeaterOn(heaterpin, invertrelay, extra=False):
    if extra:
        type = 'Extra'
    else:
        type = 'Heater'
        
    result = f"Turning {type} on using pin {heaterpin}"
    pin = DigitalInOut(heaterpin)
    pin.switch_to_output()
    
    if invertrelay:
        pin.value = 0
    else:
        pin.value = 1

    if not s.dbHasKey("dewheaterontime"):
        now = int(time.time())
        s.dbAdd("dewheaterontime", now)
    s.log(1,f"INFO: {result}")

def turnHeaterOff(heaterpin, invertrelay, extra=False):
    if extra:
        type = 'Extra'
    else:
        type = 'Heater'
                    
    result = f"Turning {type} off using pin {heaterpin}"
    pin = DigitalInOut(heaterpin)
    pin.direction = Direction.OUTPUT
    
    if invertrelay:
        pin.value = 1
    else:
        pin.value = 0
        
    if s.dbHasKey("dewheaterontime"):
        s.dbDeleteKey("dewheaterontime")
    s.log(1,f"INFO: {result}")

def getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater, soloURL, params):
    temperature = None
    humidity = None
    dewPoint = None
    heatIndex = None
    pressure = None
    relHumidity = None
    altitude = None

    if sensorType == "SHT31":
        temperature, humidity = readSHT31(sht31heater, i2caddress)
    elif sensorType == "DHT22" or sensorType == "DHT11" or sensorType == "AM2302":
        temperature, humidity = readDHT22(inputpin, dhtxxretrycount, dhtxxdelay)
    elif sensorType == "BME280-I2C":
        temperature, humidity, pressure, relHumidity, altitude = readBme280I2C(i2caddress)
    elif sensorType == "HTU21":
        temperature, humidity = readHtu21(i2caddress)
    elif sensorType == "AHTx0":
        temperature, humidity = readAHTX0(i2caddress)
    elif sensorType == "SOLO-Cloudwatcher":
        temperature, humidity, pressure, dewPoint = readSolo(soloURL)
    elif sensorType == 'OpenWeather':
        temperature, humidity, pressure, dewPoint = readOpenWeather(params)
    else:
        s.log(0,"ERROR: No sensor type defined")

    if temperature is not None and humidity is not None:
        dewPoint = dew_point(temperature, humidity).c
        heatIndex = heat_index(temperature, humidity).c

        tempUnits = s.getSetting("temptype")
        if tempUnits == 'F':
            temperature = (temperature * (9/5)) + 32
            dewPoint = (dewPoint * (9/5)) + 32
            heatIndex = (heatIndex * (9/5)) + 32
            s.log(4,"INFO: Converted temperature to F")

        temperature = round(temperature, 2)
        humidity = round(humidity, 2)
        dewPoint = round(dewPoint, 2)
        heatIndex = round(heatIndex, 2)

    return temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude

def getLastRunTime():
    lastRun = None

    if s.dbHasKey("dewheaterlastrun"):
        lastRun = s.dbGet("dewheaterlastrun")

    return lastRun

def debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude):
    s.log(1,f"INFO: Sensor {sensorType} read. Temperature {temperature} Humidity {humidity} Relative Humidity {relHumidity} Dew Point {dewPoint} Heat Index {heatIndex} Pressure {pressure} Altitude {altitude}")
    
def dewheater(params, event):    
    result = ""
    sensorType = params["type"]
    heaterstartupstate = params["heaterstartupstate"]
    try:
        heaterpin = int(params["heaterpin"])
    except ValueError:
        heaterpin = 0
    try:
        extrapin = int(params["extrapin"])
    except ValueError:
        extrapin = 0
    force = int(params["force"])
    limit = int(params["limit"])
    invertrelay = params["invertrelay"]
    invertextrapin = params["invertextrapin"]
    try:
        inputpin = int(params["inputpin"])
    except ValueError:
        inputpin = 0
    frequency = int(params["frequency"])
    maxontime = int(params["max"])
    i2caddress = params["i2caddress"]
    dhtxxretrycount = int(params["dhtxxretrycount"])
    dhtxxdelay = int(params["dhtxxdelay"])
    extradatafilename = params['extradatafilename']
    sht31heater = params["sht31heater"]

    try:
        soloURL = params["solourl"]
    except ValueError:
        soloURL = ''
                
    temperature = 0
    humidity = 0
    dewPoint = 0
    heatIndex = 0
    heater = 'Off'

    shouldRun, diff = s.shouldRun('allskydew', frequency)

    if shouldRun:                        
        try:
            heaterpin = int(heaterpin)
        except ValueError:
            heaterpin = 0

        if heaterpin != 0:
            heaterpin = s.getGPIOPin(heaterpin)
            if extrapin !=0:
                extrapin = s.getGPIOPin(extrapin)
            lastRunTime = getLastRunTime()
            if lastRunTime is not None:
                now = int(time.time())
                lastRunSecs = now - lastRunTime
                if lastRunSecs >= frequency:
                    s.dbUpdate("dewheaterlastrun", now)
                    temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude = getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater, soloURL, params)
                    if temperature is not None:
                        lastOnSecs = 0
                        if s.dbHasKey("dewheaterontime"):
                            lastOnTime = s.dbGet("dewheaterontime")
                            lastOnSecs = now - lastOnTime
                        if maxontime != 0 and lastOnSecs >= maxontime:
                            result = "Heater was on longer than maximum allowed time {}".format(maxontime)
                            s.log(1,"INFO: {}".format(result))
                            turnHeaterOff(heaterpin, invertrelay)
                            if extrapin != 0:
                                turnHeaterOff(extrapin, invertextrapin, True)
                            heater = 'Off'
                        elif force != 0 and temperature <= force:
                            result = "Temperature below forced level {}".format(force)
                            s.log(1,"INFO: {}".format(result))
                            turnHeaterOn(heaterpin, invertrelay)
                            if extrapin != 0:
                                turnHeaterOn(extrapin, invertextrapin, True)
                            heater = 'On'
                        else:
                            if ((temperature-limit) <= dewPoint):
                                turnHeaterOn(heaterpin, invertrelay)
                                if extrapin != 0:
                                    turnHeaterOn(extrapin, invertextrapin)
                                heater = 'On'
                                result = "Temperature within limit temperature {}, limit {}, dewPoint {}".format(temperature, limit, dewPoint)
                                s.log(1,"INFO: {}".format(result))
                            else:
                                result = "Temperature outside limit temperature {}, limit {}, dewPoint {}".format(temperature, limit, dewPoint)
                                s.log(1,"INFO: {}".format(result))
                                turnHeaterOff(heaterpin, invertrelay)
                                if extrapin != 0:
                                    turnHeaterOff(extrapin, invertextrapin, True)
                                heater = 'Off'
                            
                        extraData = {}
                        extraData["AS_DEWCONTROLSENSOR"] = str(sensorType)
                        extraData["AS_DEWCONTROLAMBIENT"] = str(temperature)
                        extraData["AS_DEWCONTROLDEW"] = str(dewPoint)
                        extraData["AS_DEWCONTROLHUMIDITY"] = str(humidity)
                        extraData["AS_DEWCONTROLHEATER"] = heater
                        if pressure is not None:
                            extraData["AS_DEWCONTROLPRESSURE"] = pressure
                        if relHumidity is not None:
                            extraData["AS_DEWCONTROLRELHUMIDITY"] = relHumidity
                        if altitude is not None:
                            extraData["AS_DEWCONTROLALTITUDE"] = altitude

                        s.saveExtraData(extradatafilename,extraData)

                        debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude)

                    else:
                        result = "Failed to read sensor"
                        s.log(0, "ERROR: {}".format(result))
                        s.deleteExtraData(extradatafilename)
                else:
                    result = "Not run. Only running every {}s. Last ran {}s ago".format(frequency, lastRunSecs)
                    s.log(1,"INFO: {}".format(result))
            else:
                now = int(time.time())
                s.dbAdd("dewheaterlastrun", now)
                s.log(1,"INFO: No last run info so assuming startup")
                if heaterstartupstate == "ON":
                    turnHeaterOn(heaterpin, invertrelay)
                    if extrapin != 0:
                        turnHeaterOn(extrapin, invertextrapin)
                    heater = 'On'
                else:
                    turnHeaterOff(heaterpin, invertrelay)
                    if extrapin != 0:
                        turnHeaterOff(extrapin, invertextrapin)
                    heater = 'Off'
        else:
            s.deleteExtraData(extradatafilename)
            result = "heater pin not defined or invalid"
            s.log(0,"ERROR: {}".format(result))

        s.setLastRun('allskydew')

    else:
        result = 'Will run in {:.2f} seconds'.format(frequency - diff)
        s.log(1,"INFO: {}".format(result))

    return result

def dewheater_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskydew.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)