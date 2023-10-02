# AllSky Dew Heater Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | schedule  |


This module allows for control of a dew heater via a relay connected to one of the Raspberry Pis GPIO pins.

The module requires an external temperature and humidity sensor. Currently the following sensors are supported

- SHT31
- DHT11
- DHT22
- BME280

The module contains the following options

|  Setting | Description  |
| ------------ | ------------ |
| Sensor Type  | The type of external sensor being used  |
| Input Pin  | The GPIO pin used for non i2c sensors such as the DHT11/22  |
| i2c Address  | Override the default i2c address for the selected device.   |
| Heater Pin  | The GPIO pin the heater relay is connected to  |
| Extra Pin | Extra pin that will be triggered with heater pin |
| Heater Startup State  | The state of the heater when starting allsky  |
| Invert Relay  | Normally the GPIO pin will be set High when the heater is required. This option will set the GPIO pin Low when the heater is required  |
| Invert Extra Pin | Normally a GPIO extra pin will go high when ebabling heater. Selecting this option inverts extra pin to go low when enabling heater |
| Delay  | The time in seconds between readings  |
| Limit  | If the temperature is this number of degrees above the dew point the heater will be enabled  |
| Forced Temperature  | Below this temperature the heater will allways be enabled  |


