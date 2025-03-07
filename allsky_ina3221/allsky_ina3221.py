import sys
import board
import allsky_shared as s
from barbudor_ina3221.full import *

metaData = {
    "name": "Current/voltage monitoring",
    "description": "Monitors current and voltage using an ina3221",
    "module": "allsky_ina3221",
    "version": "v1.0.1",
    "events": [
        "periodic"
    ],
    "experimental": "true",
    "arguments":{
        "i2caddress": "",
        "c1enable": "false",
        "c1name": "",
        "c2enable": "false",
        "c2name": "",
        "c3enable": "false",
        "c3name": "",
        "extradatafilename": "allskyina3221.json"                  
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x40"
        },
        "c1enable" : {
            "required": "false",
            "description": "Enable Channel 1",
            "help": "Enable channel 1 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c1name" : {
            "required": "false",
            "description": "Channel 1 name",
            "help": "Name of the channel 1 allsky overlay variable"
        },
        "c2enable" : {
            "required": "false",
            "description": "Enable Channel 2",
            "help": "Enable channel 2 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c2name" : {
            "required": "false",
            "description": "Channel 2 name",
            "help": "Name of the channel 2 allsky overlay variable"
        },
        "c3enable" : {
            "required": "false",
            "description": "Enable Channel 3",
            "help": "Enable channel 3 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c3name" : {
            "required": "false",
            "description": "Channel 3 name",
            "help": "Name of the channel 3 allsky overlay variable"
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Extra Data",
            "help": "The name of the file to create with the voltage/current data for the overlay manager"
        }
    },
    "businfo": [
        "i2c"
    ] 
}


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

def ina3221(params, event):
    result = "Ina3221 read ok"

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
    