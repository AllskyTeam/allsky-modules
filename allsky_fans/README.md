# Pi Fan Control Module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

This module allows a fan to be controlled based upon a temperature - either be from the internal CPU temperature sensor or an external sensor.
The module can be used to either cool the CPU or the enclosure via a fan.

The module requires an external fan such as a 5V fan (like a Noctua NF-A4x20 PWM), or a 12V fan via a switch, connected to one of the Raspberry Pi's GPIO pins.

The module contains the following options:

## Sensor Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| Sensor Type          | The type of sensor to read temperatures from, see below for a list.
| Read Every           | Interval in seconds at which the CPU temperature is read.
| Fans Relay Pin       | The GPIO pin the fan control relay is connected to.
| Invert Relay         | Normally the GPIO pin will be set High when the fan is required. This option will set the GPIO pin Low instead.
| CPU Temp. Limit      | The CPU temperature limit beyond which fans are activated, only used when NOT using PWM fan control.

## PWM Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| Use PWM              | If selected then the 'CPU Temp Limit' is ignored and the fan speed set via PWM.
| PWM Pin              | The pin the PWM control line is connected to, see the notes below on PWM pins.
| PWM Min Temp         | Below this temperature the fan will be off.
| PWM Max Temp         | At and above this temperature the fan will run at 100% speed. The fan speed (Duty Cycle) with be linearly interpolated between the min and max temperature.

## Internal Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| CPU Temp. Limit      | The CPU temperature limit beyond which fans are activated, only used when NOT using PWM fan control.

## DHTXX Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| Sensor Temp. Limit   | The temperature limit beyond which fans are activated, only used when NOT using PWM fan control.
| Input Pin            | The GPIO pin the DHTXX is connected to.
| Retry Count          | Number of attempt to read the DHTXX before an error is displayed.
| Delay                | The delay in milliseconds between failed sensor reads.

## BME280-I2C Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| I2C Address          | The address of the sensor if not using the standard i2c address 0x77.
| Sensor Temp. Limit   | The temperature limit beyond which fans are activated, only used when NOT using PWM fan control.

## BMP280-I2C Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| I2C Address          | The address of the sensor if not using the standard i2c address 0x58.
| Sensor Temp. Limit   | The temperature limit beyond which fans are activated, only used when NOT using PWM fan control.

## SHT31 Tab
| Setting              | Description
|---------------|---------------------------------------------------------------------------------------|
| I2C Address          | The address of the sensor if not using the standard i2c address 0x44.
| Enable Heater        | Enable the onboard heater on the sht31.
| Sensor Temp. Limit   | The temperature limit beyond which fans are activated, only used when NOT using PWM fan control.

## Available Sensors
| Sensor Type   | Description
|---------------|---------------------------------------------------------------------------------------|
| Internal      | Reads the cpu temperature from the onboard sensor.
| DHTXX/AM230X  | Read the temperature from a DHTXX/AM230X connected to a gpio pin, requires the **DHTXX Tab** details to be completed.
| BME280-I2C    | Read the temperature from a BME280-I2C connected to the i2c bus, requires the **BME280-I2C Tab** details to be completed.
| BMP280-I2C    | Read the temperature from a BMP280-I2C connected to the i2c bus, requires the **BMP280-I2C Tab** details to be completed.
| SHT31         | Read the temperature from a SHT31 connected to the i2c bus, requires the **SHT31 Tab** details to be completed.

Notes on PWM Fans:

* PWM fans require a kernel module to be loaded.

* On the Pi 4 add `dtoverlay=pwm-2chan` to /boot/firmware/config.txt (or /boot/config.txt for older Pi OS releases).
* On the PI 5 add `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4` to /boot/firmware/config.txt.

* This defaults to GPIO_18 as the pin for PWM0 and GPIO_19 as the pin for PWM1.
Alternatively, you can change GPIO_18 to GPIO_12 and GPIO_19 to GPIO_13 using `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`.
* On the Pi 5, use channels 0 and 1 to control GPIO_12 and GPIO13, respectively; use channels 2 and 3 to control GPIO_18 and GPIO_19, respectively.
On all other models, use channels 0 and 1 to control GPIO-18 and GPIO_19, respectively.
