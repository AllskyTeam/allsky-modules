'''
allsky_DFRobot0672.py
I2C address
- 0x0d  LED and Fan Control
    LED Control - 3x RGB addressable LEDs
    Fan Control - onboard PWM controlled fan
'''

import allsky_shared as s
import time
import os
import shutil
from vcgencmd import Vcgencmd
import board
import busio
import sys

metaData = {
    "name": "DFRobot0672 HAT with Fan and Multicolor LEDs",
    "description": "Makes use of DFRobot0672 HAT with onboard fan to cool CPU when sensor reaches a set temperature, optional use of onboard LEDS to indicate approx temperature (via green, amber, red illumination)",
    "module": "allsky_DFRobot0672",    
    "version": "v0.0.1",    
    "events": [
        "periodic"
    ],
    "enabled": "false",    
    "experimental": "true",    
    "arguments":{
        "i2caddress": "0x0D",
        "readperiod": 60,
        "extradatafilename": "allskyDFRobot0672.json",
        "fanenabled": "False",
        "fanregister": "0x08",
        "sensor_type": "CPU",
        "FanOffTemp": 40,
        "FanOnTemp": 50,
        "LEDsenabled": "False",
        "LEDsoffregister": "0x07"
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "tab": "Common",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x40"
	    },
        "readperiod" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds.",                
            "tab": "Common",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 600,
                "step": 1
            }          
        },
        "extradatafilename": {
            "required": "true",
            "description": "Data Filename",
            "tab": "Common",
            "help": "The name of the file to create with the sensor data for the overlay manager"
        },
        "fanenabled" : {
            "required": "false",
            "description": "Enable Fan Control",
            "help": "If checked, then onboard fan speed will be controlled based on CPU temperature",
            "tab": "Temp Control",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "sensor_type" : {
            "required": "false",
            "description": "Sensor Type",
            "help": "The type of sensor that is being used.",
            "tab": "Temp Control",
            "type": {
                "fieldtype": "select",
                "values": "CPU",
                "default": "CPU"
            }
        },
        "FanOffTemp" : {
            "required": "false",
            "description": "Fan Off Temp. Limit",
            "help": "If CPU temperature below this, then onboard fan is turned off, else fan runs proportional speed up to Fan On Temp. Limit",
            "tab": "Temp Control",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 75,
                "step": 1
            }     
        },
        "FanOnTemp" : {
            "required": "false",
            "description": "Fan On Temp. Limit",
            "help": "If CPU temperature above which the onboard fan is turned on 100%, else fan runs proportional speed up to Fan On Temp. Limit",
            "tab": "Temp Control",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 75,
                "step": 1
            }     
        },
        "LEDsenabled" : {
            "required": "false",
            "description": "Enable LED light Control",
            "help": "If checked, then onboard LEDs will be controlled based on CPU temperature (showing green, amber, red illumination), else they will be turned off",
            "tab": "Temp Control",
            "type": {
                "fieldtype": "checkbox"
            }
        }
    },
    "businfo": [
        "i2c"
    ]
}


def getCPUTemperature():
    # returns temp of CPU
    tempC = None
    vcgm = Vcgencmd()
    temp = vcgm.measure_temp()
    tempC = round(temp,1)

    return tempC


# https://emalliab.wordpress.com/2022/01/04/reading-i2c-registers-from-circuitpython/
def i2c_read_reg(i2cbus, addr, reg, result):
    while not i2cbus.try_lock():
        pass
    try:
        i2cbus.writeto_then_readfrom(addr, bytes([reg]), result)
        return result
    finally:
        i2cbus.unlock()
        return None

def i2c_write_reg(i2cbus, addr, reg, data):
    while not i2cbus.try_lock():
        pass
    try:
        buf = bytearray(1)
        buf[0] = reg
        buf.extend(data)
        i2cbus.writeto(addr, buf)
    finally:
        i2cbus.unlock()


def turnFanOn(i2caddress):
    result = "Turning Fan ON"
    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass

    try:
        i2c.writeto(0x0D, bytes([0x08, 0x01]))
        pass

    finally:
        i2c.unlock()
        pass

    s.log(4,f"INFO: {result}")

def turnFanOff(i2caddress):
    result = "Turning Fan OFF"
    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass

    try:
        i2c.writeto(0x0D, bytes([0x08, 0x00]))
        pass

    finally:
        i2c.unlock()
        pass

    s.log(4,f"INFO: {result}")

def setFanSpeed(i2caddress):
    result = "Setting Fan Speed to ..."

    # FAN Control - onboard PWM controlled fan
    # reg
    #   0x08    Fan Speed
    # value
    #   0x00 - stop
    #   ...
    #   0x02 - 20%  (min) 
    #   0x03 - 30%
    #   0x04 - 40%
    #   0x05 - 50%
    #   0x06 - 60%
    #   0x07 - 70%
    #   0x08 - 80%
    #   0x09 - 90%
    #   0x01 - 100% (max)    
    
    # i2c = busio.I2C(board.SCL, board.SDA)
    # while not i2c.try_lock():
    #     pass
    # 
    # try:
    #     #i2c.writeto(0x0D, bytes([0x08, 0x01]))
    #     pass
    # 
    # finally:
    #     i2c.unlock()
    #     pass

    s.log(4,f"INFO: {result}")    


def turnLightsOn():
    result = "Turning LEDs ON"
    
    # LED control - 3x RGB addressable LEDs
    #   reg     value
    #   0x00    Address of LED      (when viewed from end pf RPI with status leds)
    #           0x00    LED 1       Front (center)
    #           0x01    LED 2       Right (rear)
    #           0x02    LED 3       Left (rear)
    #           0xFF    All LEDS
    #   0x01    RED Value (0 - 255)
    #   0x02    GREEN Value (0 - 255)    
    #   0x03    BLUE Value (0 - 255)

    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass

    try:
        # Send i2c command 0x00 to reg 0x07 - to turn all LEDs off
        i2c.writeto(0x0D, bytes([0x00, 0x00]))
        i2c.writeto(0x0D, bytes([0x01, 0x00]))
        i2c.writeto(0x0D, bytes([0x02, 0xFF]))
        i2c.writeto(0x0D, bytes([0x03, 0x00]))
        pass

    finally:
        i2c.unlock()
        pass
        
    s.log(4,f"INFO: {result}") 

def turnLightsOff():
    result = "Turning All LEDs OFF"

    # LED control - 3x RGB addressable LEDs
    #   0x07    0x00    ALL LEDS OFF

    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        pass

    try:
        # Send i2c command 0x00 to reg 0x07 - to turn all LEDs off
        i2c.writeto(0x0D, bytes([0x07, 0x00]))
        pass

    finally:
        i2c.unlock()
        pass

    s.log(4,f"INFO: {result}")


def debugOutput(sensor_type, temperature):
    extra_text = ""
    if temperature is None:
        temperature = 0
    s.log(3,f"DEBUG: Sensor {sensor_type} read. Temperature {temperature:.2f} {extra_text}")


def DFRobot0672(params, event):
    result = ''
    fan_status = ''
    LEDS_status = ''
    result_text = ""
    limit = 0

    # get parameter values
    i2caddress = params["i2caddress"]
    try:
        period = int(params['readperiod'])
    except ValueError:
        period = 60

    extradatafilename = params['extradatafilename']
    fanenabled = params["fanenabled"]
    LEDsenabled = params["LEDsenabled"]
    LEDsoffregister = params["LEDsoffregister"]

    # set local variables 
    temperature = None
    fan_status = "Unknown"
    LEDS_status = "Unknown" 

    #initialise i2c
    # i2c = busio.I2C()
    i2c = busio.I2C(board.SCL, board.SDA)
    
    should_run, diff = s.shouldRun(metaData["module"], period)
    if should_run:
        extra_data = {}
        result = "Checking... "
        
        # Get CPU Temp
        sensor_type = params["sensor_type"]
        if sensor_type == "CPU":
            temperature = getCPUTemperature()

        if temperature is not None:
            result += f"CPU Temp: {temperature}, "
            extra_data["DFR_CPU_TEMP"] = temperature
            
        ## Test code - reading i2c bus
        # result += "Test code - reading i2c bus... "
        # while not i2c.try_lock():
        #     pass
        # 
        # try:
        #     result += "I2CScan... "
        #     i2c.scan()
        #     for x in i2c.scan():
        #         result += hex(x) + ", "
        # 
        #     i2c.writeto(0x0D, bytes([0x08, 0x01]))
        # 
        # finally:
        #     i2c.unlock()

        if fanenabled:
            result += "FAN enabled, "
            fanregister = params["fanregister"]

            try:
                FanOffTemp = int(params['FanOffTemp'])
            except ValueError:
                FanOffTemp = 40

            try:
                FanOnTemp = int(params['FanOnTemp'])
            except ValueError:
                FanOnTemp = 50

            extra_data["DFR_FAN_ENABLED"] = fanenabled
            extra_data["DFR_FAN_OFF_TEMP"] = FanOffTemp
            extra_data["DFR_FAN_ON_TEMP"] = FanOnTemp

            result += f"FanOffTemp: {FanOffTemp}, "
            result += f"FanOnTemp: {FanOnTemp}, "

            if temperature is not None:
                debugOutput(sensor_type, temperature)

                if (temperature > FanOnTemp):
                    fan_status = "On"
                    result += f"{temperature}, higher than set limit of {FanOnTemp}, CPU fan is {fan_status}, "
                    turnFanOn(i2caddress)
                    extra_data["DFR_FAN_STATUS"] = "ON"
                    if s.dbHasKey("DFR_FAN_STATUS"):
                        s.dbUpdate("DFR_FAN_STATUS", "ON")
                    else:
                        s.dbAdd("DFR_FAN_STATUS", "ON")
                    pass

                elif (temperature > FanOffTemp) and (temperature < FanOnTemp):
                    fan_status = "Unchanged"
                    if s.dbHasKey("DFR_FAN_STATUS"):
                        extra_data["DFR_FAN_STATUS"] = s.dbGet("DFR_FAN_STATUS")
                        fan_status = s.dbGet("DFR_FAN_STATUS")
                    result += f"{temperature}, is within limits eg greater than {FanOffTemp} and less than {FanOnTemp}, CPU fan is {fan_status}, "
                    pass
                    
                elif (temperature < FanOffTemp):
                    fan_status = "Off"
                    result += f"{temperature}, lower than set limit of {FanOffTemp}, CPU fan is {fan_status}, "
                    turnFanOff(i2caddress)
                    extra_data["DFR_FAN_STATUS"] = "OFF"
                    if s.dbHasKey("DFR_FAN_STATUS"):
                        s.dbUpdate("DFR_FAN_STATUS", "OFF")
                    else:
                        s.dbAdd("DFR_FAN_STATUS", "OFF")
                    pass                

            else:
                result += "Failed to get temperature!.. "
                s.log(0, f"ERROR: {result}")

        else:
            extra_data["DFR_FAN_ENABLED"] = fanenabled
            result += "FAN not enabled! "
            s.log(0, f"ERROR: {result}")

        if LEDsenabled:
            extra_data["DFR_LED_ENABLED"] = LEDsenabled
            result += "LEDs enabled, "

            # Test
            if temperature is not None:
                debugOutput(sensor_type, temperature) 
            
                # turn the internal LEDs on
                #turnLightsOn()
                #result += "Turn LEDs On "

                if (temperature > FanOnTemp):
                    turnLightsOn()
                    result += "Turn LEDs On "
                    extra_data["DFR_LED_STATUS"] = "ON"
                    pass

                elif (temperature > FanOffTemp) and (temperature < FanOnTemp):
                    pass

                elif (temperature < FanOffTemp):
                    fan_status = "Off"
                    turnLightsOff()
                    result += "Turn LEDs Off "
                    extra_data["DFR_LED_STATUS"] = "OFF"
                    pass                

        else:
            # turn the internal LEDs off
            extra_data["DFR_LED_ENABLED"] = LEDsenabled
            result += "LEDs not enabled! "
            turnLightsOff()
            result += "Turn LEDs Off "
            extra_data["DFR_LED_STATUS"] = "OFF"

        s.saveExtraData(extradatafilename, extra_data)
        s.setLastRun(metaData["module"])
        result += "... completed ok."
        i2c.unlock()

    else:
        result = f'Will run in {(period - diff):.0f} seconds'

    i2c.unlock()
    s.log(4,f"INFO: {result}")
    return result


def DFRobot0672_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyDFRobot0672.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
