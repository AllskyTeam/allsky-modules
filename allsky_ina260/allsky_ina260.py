'''
allsky_ina260.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Monitors voltage, current and power using an INA260 sensor
'''
import sys
import datetime
import allsky_shared as s
import smbus2


metaData = {
    "name": "Current/voltage/power monitoring (INA260)",
    "description": "Monitors current, voltage and power using an INA260 sensor",
    "module": "allsky_ina260",
    "version": "v1.0.0",
    "events": [
        "periodic"
    ],
    "experimental": "true",
    "arguments": {
        "i2caddress": "0x40",
        "i2cbus": "1",
        "sensorname": "INA260",
        "extradatafilename": "allskyina260.json"
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address for the device. NOTE: This value must be hex i.e. 0x40"
        },
        "i2cbus": {
            "required": "false",
            "description": "I2C Bus",
            "help": "I2C bus number (usually 1 for Raspberry Pi)"
        },
        "sensorname": {
            "required": "false",
            "description": "Sensor Name",
            "help": "Name prefix for the allsky overlay variables (e.g., INA260 will create AS_INA260VOLTAGE)"
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Extra Data",
            "help": "The name of the file to create with the voltage/current/power data for the overlay manager"
        }
    },
    "businfo": [
        "i2c"
    ]
}


class INA260:
    """
    Simple INA260 Power Monitor Reader
    Based on PiSQM implementation
    """
    REG_CURRENT = 0x01      # Current register (LSB = 1.25 mA)
    REG_VOLTAGE = 0x02      # Bus voltage register (LSB = 1.25 mV)
    REG_POWER = 0x03        # Power register (LSB = 10 mW)
    REG_MFG_ID = 0xFE       # Manufacturer ID (should be 0x5449 = "TI")
    REG_DIE_ID = 0xFF       # Die ID (should be 0x2270 for INA260)

    def __init__(self, bus=1, address=0x40):
        """Initialize INA260 with specified bus and address"""
        self.address = address
        self.bus = smbus2.SMBus(bus)

    def _read_register(self, reg):
        """Read a 16-bit register (big-endian)"""
        data = self.bus.read_i2c_block_data(self.address, reg, 2)
        return (data[0] << 8) | data[1]

    def _read_signed_register(self, reg):
        """Read a signed 16-bit register"""
        value = self._read_register(reg)
        if value >= 0x8000:
            value -= 0x10000
        return value

    def check_id(self):
        """Verify we're talking to an INA260"""
        mfg_id = self._read_register(self.REG_MFG_ID)
        die_id = self._read_register(self.REG_DIE_ID)
        if mfg_id != 0x5449 or die_id != 0x2270:
            raise RuntimeError(f"Failed to find INA260 chip (MFG_ID={mfg_id:04X}, DIE_ID={die_id:04X})")

    def read(self):
        """
        Reads the current, voltage and power from the INA260 sensor.
        Returns dict with current (A), voltage (V), and power (W)
        """
        # Read raw values
        voltage_raw = self._read_register(self.REG_VOLTAGE)
        current_raw = self._read_signed_register(self.REG_CURRENT)
        power_raw = self._read_register(self.REG_POWER)

        # Convert to real units
        voltage = voltage_raw * 1.25 / 1000    # Convert to Volts
        current = current_raw * 1.25 / 1000    # Convert to Amps
        power = power_raw * 10 / 1000          # Convert to Watts

        return {
            "current": current,
            "voltage": voltage,
            "power": power
        }

    def close(self):
        """Close the I2C bus"""
        self.bus.close()


def ina260(params, event):
    """Main entry point for the INA260 module"""
    result = "INA260 read ok"

    try:
        # Get parameters
        i2c_address_str = params["i2caddress"]
        i2c_bus = int(params["i2cbus"])
        sensor_name = params["sensorname"].upper()
        extradatafilename = params['extradatafilename']

        # Convert hex address string to int
        i2c_address = int(i2c_address_str, 16)

        s.log(4, f"INFO: Initializing INA260 on bus {i2c_bus} at address {i2c_address_str}")

        # Initialize sensor
        ina = INA260(bus=i2c_bus, address=i2c_address)
        
        # Verify sensor ID
        try:
            ina.check_id()
            s.log(4, "INFO: INA260 sensor verified successfully")
        except RuntimeError as e:
            s.log(0, f"ERROR: {e}")
            ina.close()
            return f"Failed to verify INA260: {e}"

        # Read sensor data
        data = ina.read()
        
        voltage = round(data["voltage"], 3)
        current = round(data["current"], 3)
        power = round(data["power"], 3)

        s.log(4, f"INFO: INA260 read - Voltage: {voltage}V, Current: {current}A, Power: {power}W")

        # Prepare extra data for overlay
        extraData = {}
        extraData[f"AS_{sensor_name}VOLTAGE"] = str(voltage)
        extraData[f"AS_{sensor_name}CURRENT"] = str(current)
        extraData[f"AS_{sensor_name}POWER"] = str(power)
        extraData[f"AS_{sensor_name}TIME"] = str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))

        # Save data
        s.saveExtraData(extradatafilename, extraData)
        
        # Close the bus
        ina.close()

        result = f"INA260 read ok - Voltage: {voltage}V, Current: {current}A, Power: {power}W"

    except ValueError as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f'ERROR: INA260 value error on line {eTraceback.tb_lineno} - {e}')
        result = f"INA260 read failed: {e}"
    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f'ERROR: INA260 failed on line {eTraceback.tb_lineno} - {e}')
        result = f"INA260 read failed: {e}"

    return result


def ina260_cleanup():
    """Cleanup function for the INA260 module"""
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyina260.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
