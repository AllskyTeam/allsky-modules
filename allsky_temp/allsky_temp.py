import allsky_shared as s
import time
import sys
import os
import json
import urllib.request
import requests
import json
import board
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
    "name": "Temperature Monitor",
    "description": "Reads upto 3 temperature sensors",
    "module": "allsky_temp",
    "version": "v1.0.0",
    "events": [
        "periodic"
    ],
    "experimental": "false",
    "arguments":{
        "frequency": "0",
        "extradatafilename": "allskytemp.json",
        "units": "metric",

        "type1": "None",
        "name1": "",
        "inputpin1": "",
        "i2caddress1": "",
        "dhtxxretrycount1": "2",
        "dhtxxdelay1" : "500",
        "sht31heater1": "False",
        "temp1": "",
        "gpio1": "",
        "gpioon1": "On",
        "gpiooff1": "Off",
        
        "type2": "None",
        "name2": "",
        "inputpin2": "",
        "i2caddress2": "",
        "dhtxxretrycount2": "2",
        "dhtxxdelay2" : "500",
        "sht31heater2": "False",
        "temp2": "",
        "gpio2": "",
        "gpioon2": "On",
        "gpiooff2": "Off",
                       
        "type3": "None",
        "name3": "",
        "inputpin3": "",
        "i2caddress3": "",
        "dhtxxretrycount3": "2",
        "dhtxxdelay3" : "500",
        "sht31heater3": "False",
        "temp3": "",
        "gpio3": "",
        "gpioon3": "On",
        "gpiooff3": "Off"
        
    },
    "argumentdetails": {
        "frequency" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between sensor reads in seconds. Zero will disable this and run the check every time the periodic jobs run",
            "tab": "Misc",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 1
            }
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Misc",
            "help": "The name of the file to create with the dew heater data for the overlay manager"
        },
        "units" : {
            "required": "false",
            "description": "Units",
            "help": "Units of measurement. standard, metric and imperial",
            "tab": "Misc",            
            "type": {
                "fieldtype": "select",
                "values": "standard,metric,imperial"
            }                
        }, 
                             
        "type1" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0",
                "default": "None"
            }
        },
        "name1": {
            "required": "false",
            "description": "Name Of Sensor",
            "tab": "Sensor 1",
            "help": "The name of the sensor, will be added as a variable"
        },        
        "inputpin1": {
            "required": "false",
            "description": "Input Pin",
            "help": "The input pin for DHT type sensors, not required for i2c devices",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "i2caddress1": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor 1"
        },
        "dhtxxretrycount1" : {
            "required": "false",
            "description": "Retry Count",
            "help": "The number of times to retry the DHTXX sensor read",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5,
                "step": 1
            }
        },
        "dhtxxdelay1" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between faild DBTXX sensor reads in milliseconds",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5000,
                "step": 1
            }
        },
        "sht31heater1" : {
            "required": "false",
            "description": "Enable SHT31 Heater",
            "help": "Enable the inbuilt heater on the SHT31",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "temp1" : {
            "required": "false",
            "description": "Max Temp",
            "help": "Above this temperature trigger the gpio pin",
            "tab": "Sensor 1",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 120,
                "step": 1
            }
        },        
        "gpio1": {
            "required": "false",
            "description": "GPIO Pin",
            "help": "The GPIO pin to set high when the temp is above the Max Temp",
            "type": {
                "fieldtype": "gpio"
            },            
            "tab": "Sensor 1"         
        },

        "gpioon1": {
            "required": "false",
            "description": "GPIO On",
            "help": "The Label to use when the GPIO pin is high",
            "tab": "Sensor 1"         
        },
        "gpiooff1": {
            "required": "false",
            "description": "GPIO Off",
            "help": "The Label to use when the GPIO pin is low",
            "tab": "Sensor 1"         
        },
                        
        "type2" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0",
                "default": "None"
            }
        },
        "name2": {
            "required": "false",
            "description": "Name Of Sensor",
            "tab": "Sensor 2",
            "help": "The name of the sensor, will be added as a variable"
        },          
        "inputpin2": {
            "required": "false",
            "description": "Input Pin",
            "help": "The input pin for DHT type sensors, not required for i2c devices",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "i2caddress2": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor 2"
        },
        "dhtxxretrycount2" : {
            "required": "false",
            "description": "Retry Count",
            "help": "The number of times to retry the DHTXX sensor read",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5,
                "step": 1
            }
        },
        "dhtxxdelay2" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between faild DBTXX sensor reads in milliseconds",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5000,
                "step": 1
            }
        },
        "sht31heater2" : {
            "required": "false",
            "description": "Enable SHT31 Heater",
            "help": "Enable the inbuilt heater on the SHT31",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "temp2" : {
            "required": "false",
            "description": "Max Temp",
            "help": "Above this temperature trigger the gpio pin",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 120,
                "step": 1
            }
        },        
        "gpio2": {
            "required": "false",
            "description": "GPIO Pin",
            "help": "The GPIO pin to set high when the temp is above the Max Temp",
            "tab": "Sensor 2",
            "type": {
                "fieldtype": "gpio"
            }           
        },        
        "gpioon2": {
            "required": "false",
            "description": "GPIO On",
            "help": "The Label to use when the GPIO pin is high",
            "tab": "Sensor 2"         
        },
        "gpiooff2": {
            "required": "false",
            "description": "GPIO Off",
            "help": "The Label to use when the GPIO pin is low",
            "tab": "Sensor 2"         
        },
        
        "type3" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21,AHTx0",
                "default": "None"
            }
        },
        "name3": {
            "required": "false",
            "description": "Name Of Sensor",
            "tab": "Sensor 3",
            "help": "The name of the sensor, will be added as a variable"
        },          
        "inputpin3": {
            "required": "false",
            "description": "Input Pin",
            "help": "The input pin for DHT type sensors, not required for i2c devices",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "i2caddress3": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor 3"
        },
        "dhtxxretrycount3" : {
            "required": "false",
            "description": "Retry Count",
            "help": "The number of times to retry the DHTXX sensor read",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5,
                "step": 1
            }
        },
        "dhtxxdelay3" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between faild DBTXX sensor reads in milliseconds",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 5000,
                "step": 1
            }
        },
        "sht31heater3" : {
            "required": "false",
            "description": "Enable SHT31 Heater",
            "help": "Enable the inbuilt heater on the SHT31",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "temp3" : {
            "required": "false",
            "description": "Max Temp",
            "help": "Above this temperature trigger the gpio pin",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 120,
                "step": 1
            }
        },        
        "gpio3": {
            "required": "false",
            "description": "GPIO Pin",
            "help": "The GPIO pin to set high when the temp is above the Max Temp",
            "tab": "Sensor 3",
            "type": {
                "fieldtype": "gpio"
            }           
        },
        "gpioon3": {
            "required": "false",
            "description": "GPIO On",
            "help": "The Label to use when the GPIO pin is high",
            "tab": "Sensor 3"         
        },
        "gpiooff3": {
            "required": "false",
            "description": "GPIO Off",
            "help": "The Label to use when the GPIO pin is low",
            "tab": "Sensor 3"         
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
        ]                                       
    }
}

    
def readSHT31(sht31heater, i2caddress):
    temperature = None
    humidity = None
    
    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f"ERROR: Module readSHT31 failed on line {eTraceback.tb_lineno} - {e}")
                
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

def getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater, params):
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

def debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude):
    s.log(4,f"INFO: Sensor {sensorType} read. Temperature {temperature} Humidity {humidity} Relative Humidity {relHumidity} Dew Point {dewPoint} Heat Index {heatIndex} Pressure {pressure} Altitude {altitude}")
    
def temp(params, event):    
    result = ""
    extraData = {}
    extradatafilename = params['extradatafilename']
    frequency = int(params["frequency"])
    shouldRun, diff = s.shouldRun('allskytemp', frequency)    
    
    if shouldRun:
        now = int(time.time())
        s.dbUpdate("allskytemp", now)                
        for sensorNumber in range(1,4):
            sensorType = params["type" + str(sensorNumber)]

            if sensorType != 'None':
                s.log(4,f"INFO: Reading sensor {sensorNumber}, {sensorType}")
                try:
                    inputpin = int(params["inputpin" + str(sensorNumber)])
                except ValueError:
                    inputpin = 0
                
                i2caddress = params["i2caddress" + str(sensorNumber)]
                dhtxxretrycount = int(params["dhtxxretrycount" + str(sensorNumber)])
                dhtxxdelay = int(params["dhtxxdelay" + str(sensorNumber)])
                sht31heater = params["sht31heater" + str(sensorNumber)]
                name = params["name" + str(sensorNumber)]

                try:
                    maxTemp = int(params["temp" + str(sensorNumber)])
                except ValueError:
                    maxTemp = -1
                    
                try:
                    gpioPin = int(params["gpio" + str(sensorNumber)])
                except ValueError:
                    gpioPin = -1                    
        
                temperature = 0
                humidity = 0
                dewPoint = 0
                heatIndex = 0

                temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude = getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater, params)
                debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude)

                gpioValue = 'N/A'
                if maxTemp != -1 and gpioPin != -1:
                    gpio = s.getGPIOPin(gpioPin)
                    pin = DigitalInOut(gpio)
                    pin.switch_to_output()
                    if temperature > maxTemp:
                        
                        gpioValue = 'On'
                        if 'gpioon' + str(sensorNumber) in params:
                            gpioValue = params['gpioon' + str(sensorNumber)]
        
                        s.log(4, f'INFO: Temperatture {temperature} is greater than {maxTemp} so enabling GPIO {gpioPin}')
                        pin.value = 1
                    else:
                        gpioValue = 'Off'
                        if 'gpiooff' + str(sensorNumber) in params:
                            gpioValue = params['gpiooff' + str(sensorNumber)]
                        s.log(4, f'INFO: Temperatture {temperature} is less than {maxTemp} so disabling GPIO {gpioPin}')
                        pin.value = 0
                    
                if temperature is not None:
                    extraData["AS_GPIOSTATE" + str(sensorNumber)] = gpioValue                   
                    extraData["AS_TEMPSENSOR" + str(sensorNumber)] = str(sensorType)
                    extraData["AS_TEMPSENSORNAME" + str(sensorNumber)] = name
                    extraData["AS_TEMPAMBIENT" + str(sensorNumber)] = str(temperature)
                    extraData["AS_TEMPDEW" + str(sensorNumber)] = str(dewPoint)
                    extraData["AS_TEMPHUMIDITY" + str(sensorNumber)] = str(humidity)
                    if pressure is not None:
                        extraData["AS_TEMPPRESSURE" + str(sensorNumber)] = pressure
                    if relHumidity is not None:
                        extraData["AS_TEMPRELHUMIDITY" + str(sensorNumber)] = relHumidity
                    if altitude is not None:
                        extraData["AS_TEMPALTITUDE" + str(sensorNumber)] = altitude

        s.saveExtraData(extradatafilename,extraData)

    else:
        result = 'Will run in {:.2f} seconds'.format(frequency - diff)
        s.log(1,"INFO: {}".format(result))

    return result

def temp_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskytemp.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)