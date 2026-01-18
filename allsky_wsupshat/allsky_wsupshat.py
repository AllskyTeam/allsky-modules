import sys
import board
import datetime
import allsky_shared as s
import time
import smbus
import smbus2

# source https://github.com/adafruit/Adafruit_CircuitPython_INA219/tree/main
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219

params = []
event = ''

metaData = {
    "name": "Waveshare UPS Hat (D)",
    "description": "Monitors Waveshare UPS HAT(D) INA219 sensor values (powersupply voltage, shunt voltage, battery voltage, current, power, percent) via i2c bus",
    "module": "allsky_wsupshat",
    "version": "v0.0.4",
    "events": [
        "periodic"
    ],
    "experimental": "true",
    "arguments":{
        "i2caddress": "0x43",
        "extradatafilename": "allskywsupshat.json"
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "INA219 - I2C Address",
            "tab": "UPS HAT",
            "help": "Override the standard i2c address for a device. NOTE: This value must be hex i.e. 0x40"
	    },
        "extradatafilename": {
            "required": "true",
            "description": "Data Filename",
            "tab": "Data File",
            "help": "The name of the file to create with the sensor data for the overlay manager"
        }
    },
    "businfo": [
        "i2c"
    ]
}

# Config Register (R/W)
_REG_CONFIG                 = 0x00

# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE           = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE             = 0x02

# POWER REGISTER (R)
_REG_POWER                  = 0x03

# CURRENT REGISTER (R)
_REG_CURRENT                = 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION            = 0x05

class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous



class INA219:
    """Driver for the INA219 current sensor"""
    # Basic API:

    # INA219( i2c_bus, addr)  Create instance of INA219 sensor
    #    :param i2c_bus          The I2C bus the INA219is connected to
    #    :param addr (0x40)      Address of the INA219 on the bus (default 0x40)

    # shunt_voltage               RO : shunt voltage scaled to Volts
    # bus_voltage                 RO : bus voltage (V- to GND) scaled to volts (==load voltage)
    # current                     RO : current through shunt, scaled to mA
    # power                       RO : power consumption of the load, scaled to Watt
    # set_calibration_32V_2A()    Initialize chip for 32V max and up to 2A (default)
    # set_calibration_32V_1A()    Initialize chip for 32V max and up to 1A
    # set_calibration_16V_400mA() Initialize chip for 16V max and up to 400mA

    # Advanced API:
    # config register break-up
    #   reset                     WO : Write Reset.RESET to reset the chip (must recalibrate)
    #   bus_voltage_range         RW : Bus Voltage Range field (use BusVoltageRange.XXX constants)
    #   gain                      RW : Programmable Gain field (use Gain.XXX constants)
    #   bus_adc_resolution        RW : Bus ADC resolution and averaging modes (ADCResolution.XXX)
    #   shunt_adc_resolution      RW : Shunt ADC resolution and averaging modes (ADCResolution.XXX)
    #   mode                      RW : operating modes in config register (use Mode.XXX constants)

    # raw_shunt_voltage           RO : Shunt Voltage register (not scaled)
    # raw_bus_voltage             RO : Bus Voltage field in Bus Voltage register (not scaled)
    # conversion_ready            RO : Conversion Ready bit in Bus Voltage register
    # overflow                    RO : Math Overflow bit in Bus Voltage register
    # raw_power                   RO : Power register (not scaled)
    # raw_current                 RO : Current register (not scaled)
    # calibration                 RW : calibration register (note: value is cached)
    
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus2.SMBus(i2c_bus);
        self.addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_16V_5A()

    def read(self,address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256 ) + data[1])

    def write(self,address,data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)

    def set_calibration_16V_5A(self):
        """Configures to INA219 to be able to measure up to 16V and 5A of current. Counter
           overflow occurs at 16A.
           ..note :: These calculations assume a 0.01 shunt ohm resistor is present
        """
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 16V             (Assumes 16V, can also be set to 32V)
        # VSHUNT_MAX = 0.08          (Assumes Gain 2, 80mV, can also be 0.32, 0.16, 0.04)
        # RSHUNT = 0.01               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 8.0A

        # 2. Determine max expected current
        # MaxExpected_I = 5.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.0001529              (61uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0,0012207              (488uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.00016 (uA per bit)
        self._current_lsb = 0.1524  # Current LSB = 100uA per bit

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 13434 (0x347a)

        self._cal_value = 26868

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = 0.003048  # Power LSB = 2mW per bit

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 3.2767A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.32V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 3.2 * 32V
        # MaximumPower = 102.4W

        # Set Calibration register to 'Cal' calculated above
        self.write(_REG_CALIBRATION,self._cal_value)

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_16V
        self.gain = Gain.DIV_2_80MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)

    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def getPower_W(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb


def wsupshat(params, event):
    result = "INA219 sensor read: "

    i2caddress = params['i2caddress']
    extradatafilename = params['extradatafilename']

    try:
        extra_data = {}
        result = result + "started... "

        # Create an INA219 instance.
        ina219 = INA219(i2c_bus=1,addr=0x43)

        # Read Sensor values        
        shunt_voltage = round(ina219.getShuntVoltage_mV() / 1000, 4) # voltage between V+ and V- across the shunt
        bus_voltage = round(ina219.getBusVoltage_V(), 4)             # voltage on V- (load side)
        psu_voltage = round(bus_voltage + shunt_voltage, 2)
        current = round(-ina219.getCurrent_mA() / 1000, 2)           # current in A
        power = round(ina219.getPower_W(), 2)                        # power in W
        p = round((bus_voltage - 3)/1.2*100, 2)                      # percent charged
        if(p > 100):p = 100
        if(p < 0):p = 0

#        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
#        print("PSU Voltage:   {:6.3f} V".format(bus_voltage + shunt_voltage))
#        print("Shunt Voltage: {:9.6f} V".format(shunt_voltage))
#        print("Load Voltage:  {:6.3f} V".format(bus_voltage))
#        print("Current:       {:6.3f} A".format(current/1000))
#        print("Power:         {:6.3f} W".format(power))
#        print("Percent:       {:3.1f}   %".format(p))

        # Show sensor values in Module Manager Debug Information form
        result += ' PSU_voltage: ' + str(psu_voltage) + ','
        result += ' shunt_voltage: ' + str(shunt_voltage) + ','
        result += ' bus_voltage: ' + str(bus_voltage) + ','
        result += ' current: ' + str(current) + ','
        result += ' power: ' + str(power) + ','
        result += ' percent: ' + str(p) + ''        

        # update json file for use by Overlay Module
        extra_data[f'AS_WS_UPS_PSU_VOLTAGE_V'] = psu_voltage
        extra_data[f'AS_WS_UPS_SHUNT_VOLTAGE_V'] = shunt_voltage
        extra_data[f'AS_WS_UPS_BUS_VOLTAGE_V'] = bus_voltage
        extra_data[f'AS_WS_UPS_CURRENT_A'] = current
        extra_data[f'AS_WS_UPS_POWER_W'] = power
        extra_data[f'AS_WS_UPS_PERCENT'] = p
        s.saveExtraData(extradatafilename,extra_data)
        
        result = result + " ... completed ok."
#		s.log(4, f'INFO: wsupshat WS_UPS_HAT(D) - PSU Voltage {psu_voltage}, Shunt Voltage {shunt_voltage}, Bus Voltage {bus_voltage}, current {current}, power {power}, percent {p}')
        s.log(4, f"INFO: {result}")

    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        s.log(0, f'ERROR: wsupshat WS_UPS_HAT(D) - failed on line {eTraceback.tb_lineno} - {e}')
        result = result + " ... failed on line {eTraceback.tb_lineno} - {e}."

    return result


def wsupshat_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskywsupshat.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)

