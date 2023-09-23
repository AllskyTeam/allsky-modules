'''
allsky_dewheater.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Changelog
v1.0.1 by Damian Grocholski (Mr-Groch)
- Added extra pin that is triggered with heater pin
- Fixed dhtxxdelay (was not implemented)
- Fixed max heater time (was not implemented)

'''
import allsky_shared as s
import time
import adafruit_sht31d
import adafruit_dht
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_htu21d import HTU21D
import board
import busio
import RPi.GPIO as GPIO
from meteocalc import heat_index
from meteocalc import dew_point

metaData = {
    "name": "Sky Dew Heater Control",
    "description": "Controls a dew heater via a temperature and humidity sensor",
    "module": "allsky_dewheater",
    "version": "v1.0.1",
    "events": [
        "periodic"
    ],
    "experimental": "true",
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
        "maxhumidity": "0",
        "max": "0",
        "dhtxxretrycount": "2",
        "dhtxxdelay" : "500",
        "extradatafilename": "allskydew.json",
        "sht31heater": "False"
    },
    "argumentdetails": {
        "type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor",
            "type": {
                "fieldtype": "select",
                "values": "None,SHT31,DHT22,DHT11,AM2302,BME280-I2C,HTU21",
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
        "maxhumidity" : {
            "required": "false",
            "description": "Max Humidity",
            "help": "If the humidity is above this value, heater will not be enabled. Zero will disable this.",
            "tab": "Dew Control",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
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
        }
    }
}

def readSHT31(sht31heater):
    temperature = None
    humidity = None
    try:
        i2c = board.I2C()
        sensor = adafruit_sht31d.SHT31D(i2c)
        sensor.heater = sht31heater
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
    except:
        pass

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
        except RuntimeError as error:
            s.log(4, "INFO: {}".format(error))
    except Exception as error:
        s.log(4, "INFO: {}".format(error))

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
        except:
            result = "Address {} is not a valid i2c address".format(i2caddress)
            s.log(0,"ERROR: {}".format(result))

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
    except ValueError:
        pass

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
    except ValueError:
        pass

    return temperature, humidity

def setmode():
    try:
        GPIO.setmode(GPIO.BOARD)
    except:
        pass

def turnHeaterOn(heaterpin, invertrelay):
    result = "Turning Heater on"
    setmode()
    GPIO.setup(heaterpin.id, GPIO.OUT)
    if invertrelay:
        if GPIO.input(heaterpin.id) == 0:
            result = "Leaving Heater on"
        GPIO.output(heaterpin.id, GPIO.LOW)
    else:
        if GPIO.input(heaterpin.id) == 1:
            result = "Leaving Heater on"
        GPIO.output(heaterpin.id, GPIO.HIGH)
    if not s.dbHasKey("dewheaterontime"):
        now = int(time.time())
        s.dbAdd("dewheaterontime", now)
    s.log(1,"INFO: {}".format(result))

def turnHeaterOff(heaterpin, invertrelay):
    result = "Turning Heater off"
    setmode()
    GPIO.setup(heaterpin.id, GPIO.OUT)
    if invertrelay:
        if GPIO.input(heaterpin.id) == 1:
            result = "Leaving Heater off"
        GPIO.output(heaterpin.id, GPIO.HIGH)
    else:
        if GPIO.input(heaterpin.id) == 0:
            result = "Leaving Heater off"
        GPIO.output(heaterpin.id, GPIO.LOW)
    if s.dbHasKey("dewheaterontime"):
        s.dbDeleteKey("dewheaterontime")
    s.log(1,"INFO: {}".format(result))

def getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater):
    temperature = None
    humidity = None
    dewPoint = None
    heatIndex = None
    pressure = None
    relHumidity = None
    altitude = None

    if sensorType == "SHT31":
        temperature, humidity = readSHT31(sht31heater)
    elif sensorType == "DHT22" or sensorType == "DHT11" or sensorType == "AM2302":
        temperature, humidity = readDHT22(inputpin, dhtxxretrycount, dhtxxdelay)
    elif sensorType == "BME280-I2C":
        temperature, humidity, pressure, relHumidity, altitude = readBme280I2C(i2caddress)
    elif sensorType == "HTU21":
        temperature, humidity = readHtu21(i2caddress)
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
    maxhumidity = int(params["maxhumidity"])
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
                    temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude = getSensorReading(sensorType, inputpin, i2caddress, dhtxxretrycount, dhtxxdelay, sht31heater)
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
                                turnHeaterOff(extrapin, invertextrapin)
                            heater = 'Off'
                        elif force != 0 and temperature <= force:
                            result = "Temperature below forced level {}".format(force)
                            s.log(1,"INFO: {}".format(result))
                            turnHeaterOn(heaterpin, invertrelay)
                            if extrapin != 0:
                                turnHeaterOn(extrapin, invertextrapin)
                            heater = 'On'
                        else:
                            if ((temperature-limit) <= dewPoint) and (maxhumidity == 0 or humidity < maxhumidity):
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
                                    turnHeaterOff(extrapin, invertextrapin)
                                heater = 'Off'

                        extraData = {}
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
