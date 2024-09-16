Allsky Temperature Sensor Module

Status: Stable
Level: Experienced
Runs In: Periodic

This module allows you to read upto 3 different temperature sensors and optionally control a gpio pin. The data from the module is also available for use in the overlay editor

Settings
--------

Delay - This defines in seconds how frequently the data is read. Setting this to zero will read the sensors every time the module is run from a flow 
Extra Data Filename - This is the name of the file the sensor data will be written to. There is normally no need to change this 
Units - This is NOT USED. Please use the temperature units settings in the main Allsky settings


For each of the three sensors the following fields are available.

Sensor Type - Select the sensor type
Name Of Sensor - (REQUIRED) This is used as a prefix for the sensor data, this allows you to use the data as fields in the overlay manager
Input Pin - (REQUIRED FOR DHT SENSORS) This is the GPIO pin that the sensor is connected to
i2c address - This can be used to override the default addresses for i2c devices. Some devices allow the address to be selected. The address MUST be entered in hex i.e. 0x45
DS18B20 Address - Required for DS18B20 devices, see notes below on these devices
Retry Count - The number of times to retry a DHTXX sensor if a reading fails.
Delay - The delay, in milliseconds between each retry for the DHTXX sensors 
Enable SHT31 Heater - Most users will not need to enable this. Typically only required in very high humidity areas. Refer to the device datasheet for more details and to see if you may need it
Max Temp - (OPTIONAL) Above this temperature the selected GPIO pin will be enabled.
GPIO Pin - (OPTIONAl) The GPIO pin to control based upon the temperature
GPIO On - The Human Readable value to use when the GPIO pin is enabled. This value is written to the overlay variable AS_GPIOSTATEX i.e. (AS_GPIOSTATE1 for the first sensor)
GPIO Off - The Human Readable value to use when the GPIO pin is disabled. This value is written to the overlay variable AS_GPIOSTATEX i.e. (AS_GPIOSTATE1 for the first sensor)


NOTE: If No GPIO pin is selected or the Max temp is not entered then the values for GPIOState will be N/A

Example Extra Data File
-----------------------

{
    "AS_GPIOSTATE1": "Off",                   <-- GPIO state of the first sensor
    "AS_TEMPSENSOR1": "DS18B20",              <-- Sensor 1 Type
    "AS_TEMPSENSORNAME1": "DS1",              <-- Sensor 1 Name
    "AS_TEMPAMBIENT1": "21.875",              <-- Sensor 1 Temperature
    "AS_TEMPDEW1": "None",                    <-- Sensor 1 Dew Point (Since this is a DS18B20 there is no Dew Point value)
    "AS_TEMPHUMIDITY1": "None",               <-- Sensor 1 Humidity (Since this is a DS18B20 there is no Humidity value)
    "AS_GPIOSTATE2": "N/A",                   <-- GPIO state of the second sensor (This is N/A as no GPIO pin is defined)
    "AS_TEMPSENSOR2": "DS18B20",              <-- Sensor 2 Type
    "AS_TEMPSENSORNAME2": "DS2",              <-- Sensor 2 Name
    "AS_TEMPAMBIENT2": "22.25",               <-- Sensor 2 Temperature
    "AS_TEMPDEW2": "None",                    <-- Sensor 2 Dew Point (Since this is a DS18B20 there is no Dew Point value)
    "AS_TEMPHUMIDITY2": "None",               <-- Sensor 2 Humidity (Since this is a DS18B20 there is no Humidity value)
    "AS_GPIOSTATE3": "N/A",                   <-- GPIO state of the third sensor (This is N/A as no GPIO pin is defined)
    "AS_TEMPSENSOR3": "SHT31",                <-- Sensor 3 Type
    "AS_TEMPSENSORNAME3": "bme",              <-- Sensor 3 Name
    "AS_TEMPAMBIENT3": "24.56",               <-- Sensor 3 Temperature
    "AS_TEMPDEW3": "19.22",                   <-- Sensor 3 Dew Point
    "AS_TEMPHUMIDITY3": "72.21"               <-- Sensor 3 Humidity
}

DS18B20 devices
---------------

Support for these on the raspberry pi requires some manual steps.

1) Use the raspi-config utility to ensure that the 1-wire interface is enabled.
2) Ensure the kernel modules are loaded From a command line enter the following

    sudo modprobe w1-gpio
    sudo modprobe w1-therm

You may need to add these devices to /etc/modules to ensure they are loaded following a reboot. Just add the w1-gpi and w1-therm on separate lines

You will also need to know the address data for the DS18B20. This can be found by entering the following command after the sensors are connected and the kernel modules loaded

sudo ls /sys/bus/w1/devices

You should see output similar to the following

28-3ce1d4438dc0  28-3ce1d443cdb1  w1_bus_master1

Each file starting with 28- is a DS18B20 sensor, in this example I have two connected, 28-3ce1d4438dc0 and 28-3ce1d443cdb1. This filename is the name you enter in the DS18B20 Address field

NOTE: The DS18B20 ONLY returns temperature