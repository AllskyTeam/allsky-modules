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
import adafruit_sht31d

from rpi_hardware_pwm import HardwarePWM
from gpiozero import Device

metaData = {
    "name": "Control Allsky Fans",
    "description": "Start A Fans when the CPU or external sensor reaches a set temperature",
    "module": "allsky_fans",    
    "version": "v1.0.2",    
    "events": [
        "periodic"
    ],
    "enabled": "false",    
    "experimental": "true",    
    "arguments":{
        "sensor_type": "Internal",
        "period": 60,
        "fanpin": "",
        "invertrelay": "False",        
        "DHTinputpin": "",
        "usepwm": "false",
        "pwmpin": "18",
        "pwmmin": 0,
        "pwmmax": 100,
        "dhtxxretrycount": "2",
        "dhtxxdelay" : "500",
        "i2caddress_BME280_I2C": "",
        "i2caddress_BMP280_I2C": "",
        "limit_BME280_I2C" : 30,
        "limit_BMP280_I2C" : 30,
        "limit_DHT" : 30,
        "limitInternal": 60,
        "i2caddress_SHT31_I2C": "",
        "sht31heater": "false",
        "limit_SHT31": 30
    },
    "argumentdetails": {
        "sensor_type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Sensor",
            "type": {
                "fieldtype": "select",
                "values": "Internal,DHT22,DHT11,AM2302,BME280-I2C,BMP280-I2C,SHT31",
                "default": "Internal"
            }
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
        "usepwm" : {
            "required": "false",
            "description": "Use PWM",
            "help": "Use PWM Fan control. Please see the module documentation BEFORE using this feature",
            "tab": "PWM",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "pwmpin": {
            "required": "false",
            "description": "PWM Pin",
            "help": "The GPIO pin for PWM. Please see the module documentation BEFORE using this feature",
            "tab": "PWM",
            "type": {
                "fieldtype": "gpio"
            }
        },
        "pwmmin" : {
            "required": "false",
            "description": "Min PWM Temp",
            "help": "Below this temp the fan will be off. This equates to 0% PWM duty cycle",
            "tab": "PWM",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 200,
                "step": 1
            }     
        },
        "pwmmax" : {
            "required": "false",
            "description": "Max PWM Temp",
            "help": "Below this temp the fan will be on. This equates to 100% PWM duty cycle",
            "tab": "PWM",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 200,
                "step": 1
            }     
        },         
        "limitInternal" : {
            "required": "false",
            "description": "CPU Temp. Limit",
            "help": "The CPU temperature limit beyond which fans are activated",
            "tab": "Internal",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 75,
                "step": 1
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
        "limit_BME280_I2C" : {
            "required": "false",
            "description": "Sensor Temp. Limit",
            "help": "The sensor temperature limit beyond which fans are activated",
            "tab": "BME280-I2C",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 100,
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
                "max": 100,
                "step": 1
            }
        },
        "i2caddress_SHT31_I2C" : {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x76",
            "tab": "SHT31"         
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
        "limit_SHT31" : {
            "required": "false",
            "description": "Sensor Temp. Limit",
            "help": "The sensor temperature limit beyond which fans are activated",
            "tab": "SHT31",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 100,
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
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Added PWM options for fan control",
                    "Added SHT31 temperature sensor"
                ]
            }
        ]        
    }
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
    rel_humidity = None
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
        rel_humidity = bme280.relative_humidity
        altitude = bme280.altitude
        pressure = bme280.pressure
    except ValueError as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: Module readBme280I2C failed on line {eTraceback.tb_lineno} - {e}")

    return temperature, humidity, pressure, rel_humidity, altitude

def readBmp280I2C(i2caddress):
    temperature = None
    humidity = None
    pressure = None
    rel_humidity = None
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

def debugOutput(sensor_type, temperature, humidity, rel_humidity, usepwm, duty_cycle):
    extra_text = ""
    if usepwm:
        extra_text = f"Using PWM duty cycle set to {duty_cycle}"
    if temperature is None:
        temperature = 0
    if humidity is None:
        humidity = 0
    if rel_humidity is None:
        rel_humidity = 0
    s.log(3,f"DEBUG: Sensor {sensor_type} read. Temperature {temperature:.2f} Humidity {humidity:.2f} Relative Humidity {rel_humidity:.2f} {extra_text}")

def fans(params, event):
    result = ''
    fan_status = ''
    result_text = ""
    limit = 0
    sensor_type = params["sensor_type"]
    fanpin = params['fanpin']
    try:
        period = int(params['period'])
    except ValueError:
        period = 60
    invertrelay = params["invertrelay"]
    i2caddress_BME280_I2C = params['i2caddress_BME280_I2C']
    i2caddress_BMP280_I2C = params['i2caddress_BMP280_I2C']
    dhtxxretrycount = int(params["dhtxxretrycount"])
    dhtxxdelay = int(params["dhtxxdelay"])
    try:
        DHTinputpin = int(params["DHTinputpin"])
    except ValueError:
        DHTinputpin = 0
    i2caddress_SHT31 = params['i2caddress_SHT31_I2C']
    SHT31_heater = params['sht31heater']

    usepwm = params["usepwm"]
    try:
        pwmpin = int(params["pwmpin"])
    except ValueError:
        pwmpin = 0

    try:
        pwmmin = int(params["pwmmin"])
    except ValueError:
        pwmpin = 0

    try:
        pwmmax = int(params["pwmmax"])
    except ValueError:
        pwmmax = 0

    pwm_map = {
        "4B": {
            "enabled": "/sys/class/pwm/pwmchip0/pwm%CHANNEL%/enable",
            "chip": 0,
            "addresses": {
                18: 0,
                19: 1,
                12: 0,
                13: 1
            }
        },
        "5B": {
            "enabled": "/sys/class/pwm/pwmchip2/pwm%CHANNEL%/enable",
            "chip": 2,
            "addresses": {
                18: 0,
                19: 1,
                12: 0,
                13: 1
            }
        }
    }

    pwm_duty_cycle = 0
    pwm_enabled = "0"
    temperature = None
    humidity = None
    pressure = None
    rel_humidity = None
    altitude = None
    fan_status = "Unknown"

    should_run, diff = s.shouldRun(metaData["module"], period)
    if should_run:
        extra_data = {}
        try:
            fanpin = int(fanpin)
        except ValueError:
            fanpin = 0
        if fanpin != 0:
            fanpin = s.getGPIOPin(fanpin)         
            if sensor_type == "Internal":
                temperature = getTemperature()
                limit = int(params["limitInternal"])
                result_text = "CPU Temp is "
            elif sensor_type == "BME280-I2C":
                temperature, humidity, pressure, rel_humidity, altitude = readBme280I2C(i2caddress_BME280_I2C)
                limit = int(params["limit_BME280_I2C"])
                result_text = "BME280 Temp is "
            elif sensor_type == "BMP280-I2C":
                temperature, pressure, altitude = readBmp280I2C(i2caddress_BMP280_I2C)
                limit = int(params["limit_BMP280_I2C"])
                result_text = "BMP280 Temp is "
            elif sensor_type == "DHT22" or sensor_type == "DHT11" or sensor_type == "AM2302":
                temperature, rel_humidity = readDHT22(DHTinputpin, dhtxxretrycount, dhtxxdelay)
                limit = int(params["limit_DHT"])
                result_text = "DHTXX Temp is "
            elif sensor_type == "SHT31":
                limit = int(params["limit_SHT31"])                
                temperature, humidity = readSHT31(SHT31_heater, i2caddress_SHT31)
              
            if temperature is not None:
                if usepwm:
                    if pwmpin != 0:
                        Device.ensure_pin_factory()
                        pi_info = Device.pin_factory.board_info
                        model = pi_info.model
                        if model in pwm_map:
                            pwm_channel =  pwm_map[model]["addresses"][pwmpin]
                            enabled_file = pwm_map[model]["enabled"]
                            chip = pwm_map[model]["chip"]
                            enabled_file = enabled_file.replace("%CHANNEL%", str(pwm_channel))
                            try:
                                with open(enabled_file, 'r', encoding="utf-8") as file:
                                    pwm_enabled = file.readline().strip()
                            except FileNotFoundError:
                                pwm_enabled = "0"

                            pwm = HardwarePWM(pwm_channel=pwm_channel, hz=60, chip=chip)
                            if pwm_enabled == "0":
                                pwm.start(0)
                                pwm.change_frequency(25_000)

                            if temperature <= pwmmin:
                                pwm_duty_cycle = 0
                            elif temperature > pwmmax:
                                pwm_duty_cycle = 100
                            else:
                                pwm_duty_cycle = int(((temperature - pwmmin) / (pwmmax - pwmmin)) * 100)

                            pwm.change_duty_cycle(pwm_duty_cycle)
                            
                            if pwm_duty_cycle == 0:
                                pwm.stop()
                        else:
                            result = f"Pi Model ({model}) is not supported for PWM"
                            s.log(0, f"ERROR: {result}")
                    else:
                        result = "PWM Pin is invalid"
                        s.log(0, f"ERROR: {result}")
                else:
                    if (temperature > limit):
                        turnFansOn(fanpin, invertrelay)
                        fan_status = "On"
                        result = result_text + f"{temperature} is higher then set limit of {limit}, Fans are {fan_status} via fan pin {fanpin}"
                    else:
                        turnFansOff(fanpin, invertrelay)
                        fan_status = "Off"
                        result = result_text + f"{temperature} is lower then set limit of {limit}, Fans are {fan_status} via fan pin {fanpin}"

                extra_data["OTH_FANS"] = fan_status
                extra_data["OTH_FANT"] = limit
                extra_data["OTH_USE_PWM"] = "Yes" if usepwm else "No"
                extra_data["OTH_PWM_ENABLED"] = "Yes" if pwm_enabled == "1" else "No"
                extra_data["OTH_PWM_DUTY_CYCLE"] = pwm_duty_cycle
                extra_data["OTH_TEMPERATURE"] = temperature
                if pressure is not None:
                    extra_data["OTH_PRESSURE"] = pressure
                if altitude is not None:
                    extra_data["OTH_ALTITUDE"] = altitude
                if humidity is not None:
                    extra_data["OTH_HUMIDITY"] = humidity
                if rel_humidity is not None:
                    extra_data["OTH_rel_humidity"] = rel_humidity
                    
                s.saveExtraData("allskyfans.json", extra_data)
                
                debugOutput(sensor_type, temperature, humidity, rel_humidity, usepwm, pwm_duty_cycle)
                s.setLastRun(metaData["module"])
            else:
                result = "Failed to get temperature"
                s.log(0, f"ERROR: {result}")
        else:
            result = "fan pin not defined or invalid"
            s.log(0, f"ERROR: {result}")
    else:
        result = f'Will run in {(period - diff):.0f} seconds'
        
    s.log(4,f"INFO: {result}")
    
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
