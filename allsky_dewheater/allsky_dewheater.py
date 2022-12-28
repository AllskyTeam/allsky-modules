'''
allsky_dewheater.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


pip3 install adafruit-circuitpython-sht31d

'''
import allsky_shared as s
import os
import time
import adafruit_sht31d
import adafruit_dht
from adafruit_bme280 import basic as adafruit_bme280
import board
import RPi.GPIO as GPIO
from meteocalc import heat_index
from meteocalc import dew_point

metaData = {
    "name": "Sky Dew Heater Control",
    "description": "Controls a dew heater via a temperature and humidity sensor",
    "module": "allsky_dewheater",
    "version": "v1.0.0",    
    "events": [
        "day",
        "night",
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "type": "None",
        "inputpin": "",
        "heaterpin": "",
        "i2caddress": "",
        "heaterstartupstate": "OFF",
        "invertrelay": "False",
        "frequency": "0",
        "limit": "10",
        "force": "0",
        "max": "0"        
    },
    "argumentdetails": {   
        "type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,BME280-I2C",
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
        } ,                    
        "heaterpin": {
            "required": "false",
            "description": "Heater Pin",
            "help": "The pin the heater control relay is connected to",
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
        "frequency" : {
            "required": "false",
            "description": "Delay",
            "help": "The delay between sensor reads in seconds. Zero will disable this and run the check after every frame",
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
                "min": -60,
                "max": 50,
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
                "min": -60,
                "max": 50,
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
        }                                                                
    },
    "enabled": "false"            
}

def readSHT31():
    temperature = None
    humidity = None
    try:
        i2c = board.I2C()
        sensor = adafruit_sht31d.SHT31D(i2c)
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
    except:
        pass

    return temperature, humidity

def readDHT22(inputpin):
    temperature = None
    humidity = None

    try:
        inputpin = int(inputpin)

        dhtDevice = adafruit_dht.DHT22(inputpin)
        try:
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity
        except RuntimeError as error:
            s.log(0,"ERROR: Failed to read DHT22")
            pass
        except Exception as error:
            dhtDevice.exit()
            raise error

    except ValueError:
        inputpin = 0

    return temperature, humidity

def readBme280I2C(i2caddress):
    temperature = None
    humidity = None


    if i2caddress != "":
        try:
            i2caddressInt = int(i2caddress, 16)
        except:
            result = "Address {} is not a valid i2c address".format(i2caddress)
            s.log(0,"ERROR: {}".format(result))

    i2c = board.I2C()
    if i2caddress != "":
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, i2caddressInt)
    else:
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

    temperature =  bme280.temperature
    humidity = bme280.relative_humidity

    return temperature, humidity

def setmode():
    try:
        GPIO.setmode(GPIO.BOARD)
    except:
        pass

def turnHeaterOn(invertrelay):
    setmode()
    GPIO.setup(27, GPIO.OUT)
    if invertrelay:
        GPIO.output(27, GPIO.LOW)
    else:
        GPIO.output(27, GPIO.HIGH)
    s.log(1,"INFO: Turning Heater on")

def turnHeaterOff(invertrelay):
    setmode()
    GPIO.setup(27, GPIO.OUT)
    if invertrelay:
        GPIO.output(27, GPIO.HIGH)
    else:    
        GPIO.output(27, GPIO.LOW)
    s.log(1,"INFO: Turning Heater off")

def getSensorReading(sensorType, inputpin, i2caddress):
    temperature = None
    humidity = None
    dewPoint = None
    heatIndex = None

    if sensorType == "SHT31":
        temperature, humidity = readSHT31()
    elif sensorType == "DHT22" or sensorType == "DHT11":
        temperature, humidity = readDHT22(inputpin)
    elif sensorType == "BME280-I2C":
        temperature, humidity = readBme280I2C(i2caddress)
    else:
        s.log(0,"ERROR: No sensor type defined")

    if temperature is not None and humidity is not None:
        dewPoint = dew_point(temperature, humidity).c
        heatIndex = heat_index(temperature, humidity).c

        temperature = round(temperature, 2)
        humidity = round(humidity, 2)
        dewPoint = round(dewPoint, 2)
        heatIndex = round(heatIndex, 2)

    return temperature, humidity, dewPoint, heatIndex

def getLastRunTime():
    lastRun = None

    if s.dbHasKey("dewheaterlastrun"):
        lastRun = s.dbGet("dewheaterlastrun")

    return lastRun

def debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex):
    s.log(1,"INFO: Sensor {0} read. Temperature {1} Humidity {2} Dew Point {3} Heat Index {4}".format(sensorType, temperature, humidity, dewPoint, heatIndex))

def dewheater(params, event):
    result = ""
    sensorType = params["type"]
    heaterstartupstate = params["heaterstartupstate"]
    heaterpin = params["heaterpin"]
    force = int(params["force"])
    limit = int(params["limit"])
    invertrelay = params["invertrelay"]
    inputpin = params["inputpin"]
    frequency = int(params["frequency"])
    i2caddress = params["i2caddress"]

    temperature = 0
    humidity = 0
    dewPoint = 0
    heatIndex = 0
    heater = 'Off'

    try:
        heaterpin = int(heaterpin)
    except ValueError:
        heaterpin = 0

    if heaterpin != 0:
        lastRunTime = getLastRunTime()
        if lastRunTime is not None:
            now = int(time.time())            
            lastRunSecs = now - lastRunTime
            if lastRunSecs >= frequency:
                s.dbUpdate("dewheaterlastrun", now)
                temperature, humidity, dewPoint, heatIndex = getSensorReading(sensorType, inputpin, i2caddress)
                if temperature is not None:
                    if force != 0 and temperature <= force:
                        result = "Temperature below forced level {}".format(force)
                        s.log(1,"INFO: {}".format(result))
                        turnHeaterOn(invertrelay)
                        heater = 'On'
                    else:
                        if ((temperature-limit) <= dewPoint):
                            turnHeaterOn(invertrelay)
                            heater = 'On'
                            result = "Temperature within limit temperature {}, limit {}, dewPoint {}".format(temperature, limit, dewPoint)
                            s.log(1,"INFO: {}".format(result))
                        else:
                            result = "Temperature outside limit temperature {}, limit {}, dewPoint {}".format(temperature, limit, dewPoint)
                            s.log(1,"INFO: {}".format(result))
                            turnHeaterOff(invertrelay)
                            heater = 'Off'

                    debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex)
            else:
                result = "Not run. Only running every {}s. Last ran {}s ago".format(frequency, lastRunSecs)
                s.log(1,"INFO: {}".format(result))
        else:
            now = int(time.time())
            s.dbAdd("dewheaterlastrun", now)
            s.log(1,"INFO: No last run info so assuming startup")
            if heaterstartupstate == "ON":
                turnHeaterOn(invertrelay)
                heater = 'On'
            else:
                turnHeaterOff(invertrelay)
                heater = 'Off'

        os.environ["AS_DEWCONTROLAMBIENT"] = str(temperature)
        os.environ["AS_DEWCONTROLDEW"] = str(dewPoint)
        os.environ["AS_DEWCONTROLHUMIDITY"] = str(humidity)
        os.environ["AS_DEWCONTROLHEATER"] = heater
    else:
        result = "heater pin not defined or invalid"
        s.log(0,"ERROR: {}".format(result))

    return result