Environment Monitor Module

Status: Stable
Level: Experienced
Runs In: Periodic

This module reads one Core sensor and up to three additional temperature sensors. Each sensor can optionally control a GPIO pin. The data is also available for use in the Overlay Editor.

Settings
--------

Delay - This defines in seconds how frequently the data is read. Setting this to zero will read the sensors every time the module is run from a flow.
Extra Data Filename - This is the name of the file the sensor data will be written to. There is normally no need to change this.
Units - Legacy setting. Use the OpenWeather Units setting for an OpenWeather sensor and the temperature unit setting in the main Allsky settings for output.


For the Core sensor and each of the three additional sensors the following fields are available:

Sensor Type - Select the sensor type.
Name Of Sensor - (REQUIRED) This is used as a prefix for the sensor data, this allows you to use the data as fields in the Overlay Manager.
Input Pin - (REQUIRED FOR DHT SENSORS) This is the GPIO pin that the sensor is connected to.
i2c address - This can be used to override the default addresses for i2c devices. Some devices allow the address to be selected. The address MUST be entered in hex, i.e., 0x45.
DS18B20 Address - Required for DS18B20 devices, see notes below on these devices.
Retry Count - The number of times to retry a DHTXX sensor if a reading fails.
Delay - The delay, in milliseconds between each retry for the DHTXX sensors.
DHT Power Pin - (OPTIONAL) GPIO pin used to power a DHT sensor during a reading.
Enable SHT31 Heater - Most users will not need to enable this. Typically only required in very high humidity areas. Refer to the device datasheet for more details and to see if you may need it.
Sensor Offsets - Adjust the reported temperature, humidity and pressure readings. Temperature offsets support half-degree steps.
OpenWeather Units - Select metric, imperial or standard units for this sensor's OpenWeather request.
Max Temp - (OPTIONAL) Above this temperature the selected GPIO pin will be enabled.
Deadband Range - Range around Max Temp where the GPIO pin keeps its current state.
GPIO Pin - (OPTIONAl) The GPIO pin to control based upon the temperature.
Invert GPIO - Use when the connected device activates when the GPIO pin goes low.
GPIO On - Label written to AS_GPIOSTATE (Core) or AS_GPIOSTATE1/2/3 when GPIO control is enabled.
GPIO Off - Label written to AS_GPIOSTATE (Core) or AS_GPIOSTATE1/2/3 when GPIO control is disabled.


NOTE: If No GPIO pin is selected or the Max temp is not entered then the values for GPIOState will be N/A.

Example Extra Data Values
-------------------------

The extra-data file stores each available field with a value and metadata. This
abbreviated example shows the values for three configured sensors:

{
    "AS_TEMP1": {"value": 21.88},
    "AS_TEMP2": {"value": 22.25},
    "AS_TEMP3": {"value": 24.56},
    "AS_DEW3": {"value": 19.22},
    "AS_HUMIDITY3": {"value": 72.21}
}

DS18B20 sensors report temperature only. Their dew point and humidity fields
are omitted. Core sensor keys use the same names without a numeric suffix.

DS18B20 devices
---------------

Support for these on the Raspberry Pi requires some manual steps.

1) Use the raspi-config utility to ensure that the 1-wire interface is enabled.
2) Ensure the kernel modules are loaded From a command line enter the following:

    sudo modprobe w1-gpio
    sudo modprobe w1-therm

You may need to add these devices to /etc/modules to ensure they are loaded following a reboot. Just add the w1-gpi and w1-therm on separate lines.

You will also need to know the address data for the DS18B20. This can be found by entering the following command after the sensors are connected and the kernel modules loaded.

sudo ls /sys/bus/w1/devices

You should see output similar to the following:

28-3ce1d4438dc0  28-3ce1d443cdb1  w1_bus_master1


Each file starting with 28- is a DS18B20 sensor, in this example I have two connected, 28-3ce1d4438dc0 and 28-3ce1d443cdb1. This filename is the name you enter in the DS18B20 Address field.

NOTE: The DS18B20 ONLY returns temperature.
