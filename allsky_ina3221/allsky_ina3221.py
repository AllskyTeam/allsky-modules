<<<<<<< HEAD
import sys
import board
import datetime
import allsky_shared as s
from barbudor_ina3221.full import *
=======
import allsky_shared as allsky_shared
>>>>>>> upstream/v2024.12.06_01-Updates

metaData = {
	"name": "Current/voltage monitoring",
	"description": "Monitors current and voltage using an ina3221",
	"module": "allsky_ina3221",
	"version": "v1.0.1",
	"group": "Hardware",
	"deprecation": {
		"fromversion": "v2024.12.06_02",
		"removein": "v2024.12.06_02",
		"notes": "This module has been deprecated. Please use the allsky_power module",
		"replacedby": "allsky_power",
		"deprecated": "true"
	}, 
	"events": [
		"day",
		"night",
	    "periodic"
	],
	"experimental": "true",
	"arguments":{
		"dummy": ""
	},
	"argumentdetails": {
		"notice": {
			"message": "This module is no longer in use and has been replaced by the allsky_power module",
	        "tab": "Sensor",
	        "type": {
	            "fieldtype": "text",
	            "style": {
	                "width": "full",
					"alert": {
						"class": "danger"
					}
				}
	        }            						
		}
	},
	"businfo": [
	    "i2c"
	] 
}

<<<<<<< HEAD

def debugOutput(sensorType, temperature, humidity, dewPoint, heatIndex, pressure, relHumidity, altitude):
    s.log(1,f"INFO: Sensor {sensorType} read. Temperature {temperature} Humidity {humidity} Relative Humidity {relHumidity} Dew Point {dewPoint} Heat Index {heatIndex} Pressure {pressure} Altitude {altitude}")

def readChannel(ina3221, channel):
    ina3221.enable_channel(channel)
    busVoltage = ina3221.bus_voltage(channel)
    shuntVoltage = ina3221.shunt_voltage(channel)
    current = ina3221.current(channel)
    voltage = round(busVoltage + shuntVoltage,2)
    current = round(current,3)  # Removed the absolute value filter so this can be used to monitor current in and out of batteries. 
    power = round(voltage * current,3)  # Calculate the power (in watts) going across the bus.

    s.log(4, f"INFO: Channel {channel} read, voltage {voltage}, current {current}. Bus Voltage {busVoltage}, Shunt Voltage {shuntVoltage}, power {power}")
                        
    return voltage, current, power

=======
>>>>>>> upstream/v2024.12.06_01-Updates
def ina3221(params, event):
	result = 'Module deprecated please use the allsky_power module instead'

<<<<<<< HEAD
    try:
        c1enabled = params["c1enable"]
        c1name = params["c1name"].upper()
        c2enabled = params["c2enable"]
        c2name = params["c2name"].upper()
        c3enabled = params["c3enable"]
        c3name = params["c3name"].upper()
        extradatafilename = params['extradatafilename']

        i2cBus = board.I2C()
        ina3221 = INA3221(i2cBus)

        if INA3221.IS_FULL_API:
            ina3221.update(reg=C_REG_CONFIG,
                        mask=C_AVERAGING_MASK |
                        C_VBUS_CONV_TIME_MASK |
                        C_SHUNT_CONV_TIME_MASK |
                        C_MODE_MASK,
                        value=C_AVERAGING_128_SAMPLES |
                        C_VBUS_CONV_TIME_8MS |
                        C_SHUNT_CONV_TIME_8MS |
                        C_MODE_SHUNT_AND_BUS_CONTINOUS)

        extraData = {}
        extraData[f"AS_{c1name}VOLTAGE"] = "N/A"
        extraData[f"AS_{c1name}CURRENT"] = "N/A"
        extraData[f"AS_{c1name}POWER"] = "N/A"
        extraData[f"AS_{c2name}VOLTAGE"] = "N/A"
        extraData[f"AS_{c2name}CURRENT"] = "N/A"
        extraData[f"AS_{c2name}POWER"] = "N/A"
        extraData[f"AS_{c3name}VOLTAGE"] = "N/A"
        extraData[f"AS_{c3name}CURRENT"] = "N/A"
        extraData[f"AS_{c3name}POWER"] = "N/A"
        extraData[f"AS_INA3221TIME"] = str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))  # Adds timestamp to the json file when generated. Helpful in determining if the data is fresh. 

        if c1enabled:
            voltage, current, power = readChannel(ina3221,1)
            extraData[f"AS_{c1name}VOLTAGE"] = str(voltage)
            extraData[f"AS_{c1name}CURRENT"] = str(current)
            extraData[f"AS_{c1name}POWER"] = str(power)  

        if c2enabled:
            voltage, current, power = readChannel(ina3221,2)
            extraData[f"AS_{c2name}VOLTAGE"] = str(voltage)
            extraData[f"AS_{c2name}CURRENT"] = str(current)
            extraData[f"AS_{c2name}POWER"] = str(power) 
            
        if c3enabled:
            voltage, current, power = readChannel(ina3221,3)
            extraData[f"AS_{c3name}VOLTAGE"] = str(voltage)
            extraData[f"AS_{c3name}CURRENT"] = str(current)
            extraData[f"AS_{c3name}POWER"] = str(power) 

        s.saveExtraData(extradatafilename,extraData)                            
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f'ERROR: ina3221 failed on line {eTraceback.tb_lineno} - {e}')
        
    return result

def ina3221_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyina3221.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
    
=======
	allsky_shared.log(0, f'ERROR: {result}')
	return result
>>>>>>> upstream/v2024.12.06_01-Updates
