'''
allsky_fans.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import time
import os
import shutil
from vcgencmd import Vcgencmd
import board
from digitalio import DigitalInOut, Direction, Pull

import sys
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_bmp280 as adafruit_bmp280
import adafruit_dht

metaData = {
    "name": "Control Allsky Fans",
    "description": "Start Allsky Fans when the CPU reaches a set temperature",
    "module": "allsky_fans",    
    "version": "v1.0.1",    
    "events": [
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "sensortype": "Internal",
        "DHTinputpin": "",
        "dhtxxretrycount": "2",
        "dhtxxdelay" : "500",
        "i2caddress_BME280_I2C": "",
        "i2caddress_BMP280_I2C": "",
        "period": 60,
        "fanpin": "",
        "invertrelay": "False",
        "limit_BME280_I2C" : 30,
        "limit_BMP280_I2C" : 30,
        "limit_DHT" : 30,
        "limitInternal": 60
    },
    "argumentdetails": {
        "sensortype" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor",
            "type": {
                "fieldtype": "select",
                "values": "Internal,DHT22,DHT11,AM2302,BME280-I2C,BMP280-I2C",
                "default": "Internal"
            }
        },                   
        "limitInternal" : {
            "required": "false",
            "description": "CPU Temp. Limit",
            "help": "The CPU temperature limit beyond which fans are activated",
            "tab": "Internal sensor",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 75,
                "step": 1
            }          
        },
        "DHTinputpin": {
            "required": "false",
            "description": "Input Pin",
            "help": "The input pin for DHT type (DHT11, DHT22, AM2302) sensors",
            "tab": "DHTXX",
            "type": {
                "fieldtype": "gpio"
            }
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
            "help": "The delay between failed sensor reads in milliseconds",
            "tab": "DHTXX",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5000,
                "step": 1
            }
        },
        "i2caddress_BME280_I2C": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "BME280-I2C"
        },
        "i2caddress_BMP280_I2C": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "BMP280-I2C"
        },
        "period" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds.",                
            "tab": "Sensor",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 600,
                "step": 1
            }          
        },
        "fanpin": {
            "required": "false",
            "description": "Fans Relay Pin",
            "help": "The GPIO pin the fan control relay is connected to",
            "tab": "Sensor",
            "type": {
                "fieldtype": "gpio"
            }           
        },
        "invertrelay" : {
            "required": "false",
            "description": "Invert Relay",
            "help": "Invert relay activation logic from pin HIGH to pin LOW",
            "tab": "Sensor",
            "type": {
                "fieldtype": "checkbox"
            }               
        },
        "limit_DHT" : {
            "required": "false",
            "description": "Sensor Temp. Limit",
            "help": "The sensor temperature limit beyond which fans are activated",
            "tab": "DHTXX",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 45,
                "step": 1
            }          
        },                   
        "limit_BME280_I2C" : {
            "required": "false",
            "description": "Sensor Temp. Limit",
            "help": "The sensor temperature limit beyond which fans are activated",
            "tab": "BME280-I2C",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 45,
                "step": 1
            }          
        },                   
        "limit_BMP280_I2C" : {
            "required": "false",
            "description": "Sensor Temp. Limit",
            "help": "The sensor temperature limit beyond which fans are activated",
            "tab": "BMP280-I2C",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 45,
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
                "author": "Lorenzi70",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1" : [
            {
                "author": "Tamas Maroti (CapricornusObs)",
                "authorurl": "https://github.com/CapricornusObs",
                "changes": [
                    "Added external temperature sensors to control fan",
                    "Added BMP280 sersor control code"
                ]
            }
        ]
    },
    "enabled": "false"
}

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
            s.log(0, f"ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module doDHTXXRead failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity

def readDHT22(inputpin, dhtxxretrycount, dhtxxdelay):
    temperature = None
    humidity = None
    count = 0
    reading = True

    while reading:
        temperature, humidity = doDHTXXRead(inputpin)

        if temperature is None and humidity is None:
            s.log(4, "INFO: Failed to read DHTXX on attempt {}".format(count+1))
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
    except ValueError as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity, pressure, relHumidity, altitude
    
def readBmp280I2C(i2caddress):
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
            s.log(0, f"ERROR: Module readBmp280I2C failed on line {eTraceback.tb_lineno} - {e}")

    try:
        i2c = board.I2C()
        if i2caddress != "":
            bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, i2caddressInt)
        else:
            bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

        temperature =  bmp280.temperature
        altitude = bmp280.altitude
        pressure = bmp280.pressure
    except ValueError as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module readBmp280I2C failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, pressure, altitude

def getTemperature():
    tempC = None
    vcgm = Vcgencmd()
    temp = vcgm.measure_temp()
    tempC = round(temp,1)

    return tempC
    

def turnFansOn(fanpin, invertrelay):
    result = "Turning Fans ON"
    pin = DigitalInOut(fanpin)
    pin.switch_to_output()
    
    if invertrelay:
        pin.value = 0
    else:
        pin.value = 1

    s.log(4,f"INFO: {result}")
    
def turnFansOff(fanpin, invertrelay):
    result = "Turning Fans OFF"
    pin = DigitalInOut(fanpin)
    pin.switch_to_output()

    if invertrelay:
        pin.value = 1
    else:    
        pin.value = 0
        
    s.log(4,f"INFO: {result}")

def debugOutput(sensorType, temperature, humidity, pressure, relHumidity, altitude):
    s.log(3,f"DEBUG: Sensor {sensorType} read. Temperature {temperature} Humidity {humidity} Relative Humidity {relHumidity} Pressure {pressure} Altitude {altitude}")

def fans(params, event):
    s.log(4, "INFO: enter method fans with parameters {}".format(str(params)))
    result = ''
    cfans = ''
    resultText = ""
    limit = 0
    sensorType = params["sensortype"]
    period = int(params['period'])
    fanpin = int(params["fanpin"])
    invertrelay = params["invertrelay"]
    i2caddress_BME280_I2C = params['i2caddress_BME280_I2C']
    i2caddress_BMP280_I2C = params['i2caddress_BMP280_I2C']
    dhtxxretrycount = int(params["dhtxxretrycount"])
    dhtxxdelay = int(params["dhtxxdelay"])
    try:
        DHTinputpin = int(params["DHTinputpin"])
    except ValueError:
        DHTinputpin = 0

    temperature = None
    humidity = None
    pressure = None
    relHumidity = None
    altitude = None
    cfans = "Unkn"
    shouldRun, diff = s.shouldRun('fans', period)
    
    if shouldRun:
        extraData = {}
        try:
            fanpin = int(fanpin)
        except ValueError:
            fanpin = 0
        if fanpin != 0:
            fanpin = s.getGPIOPin(fanpin)
# read parameters from selected sensor           
            if sensorType == "Internal":
                temperature = getTemperature()
                limit = int(params["limitInternal"])
                resultText = "CPU Temp is "
            elif sensorType == "BME280-I2C":
                temperature, humidity, pressure, relHumidity, altitude = readBme280I2C(i2caddress_BME280_I2C)
                limit = int(params["limit_BME280_I2C"])
                resultText = "BME280 Temp is "
            elif sensorType == "BMP280-I2C":
                temperature, pressure, altitude = readBmp280I2C(i2caddress_BMP280_I2C)
                limit = int(params["limit_BMP280_I2C"])
                resultText = "BMP280 Temp is "
            elif sensorType == "DHT22" or sensorType == "DHT11" or sensorType == "AM2302":
                temperature, relHumidity = readDHT22(DHTinputpin, dhtxxretrycount, dhtxxdelay)
                limit = int(params["limit_DHT"])
                resultText = "DHTXX Temp is "
#all parameters were read                
            if temperature is not None:
                if (temperature > limit):
                    turnFansOn(fanpin, invertrelay)
                    cfans = "On"
                    result = resultText + "{} and higher then set limit of {}, Fans are {} via fan pin {}".format(temperature, limit, cfans, fanpin)
                else:
                    turnFansOff(fanpin, invertrelay)
                    cfans = "Off"
                    result = resultText + "{} and lower then set limit of {}, Fans are {} via fan pin {}".format(temperature, limit, cfans, fanpin)
                extraData["OTH_FANS"] = cfans
                extraData["OTH_FANT"] = limit
                extraData["OTH_TEMPERATURE"] = temperature
                if pressure is not None:
                    extraData["OTH_PRESSURE"] = pressure
                if altitude is not None:
                    extraData["OTH_ALTITUDE"] = altitude
                if humidity is not None:
                    extraData["OTH_HUMIDITY"] = humidity
                if relHumidity is not None:
                    extraData["OTH_RELHUMIDITY"] = relHumidity
                    
                s.saveExtraData("allskyfans.json", extraData)
                
                debugOutput(sensorType, temperature, humidity, pressure, relHumidity, altitude)

            else:
                result = "Failed to get temperature"
                s.log(0, "ERROR: {}".format(result))
        else:
            result = "fan pin not defined or invalid"
            s.log(0, "ERROR: {}".format(result))
    else:
        result = 'Will run in ' + str(period - diff) + ' seconds'
        
    s.log(4,"INFO: {}".format(result))
    
    return result

def fans_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyfans.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
