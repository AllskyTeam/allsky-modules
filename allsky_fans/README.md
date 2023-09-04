# AllSky Fan Control Module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

This module allows for control of a fan according to the CPU internal temperature vs a set value.
The module requires an external 5V fan (like a Noctua NF-A4x20 PWM), or a 12V fan via a relay, connected to one of the Raspberry Pis GPIO pins. 

The module contains the following options

| Setting              | Description                                                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Read Every           | Interval in seconds at which the CPU temperature is read                                                                              |
| Fans Relay Pin       | The GPIO pin the fan control relay is connected to                                                                                    |
| Invert Relay         | Normally the GPIO pin will be set High when the fan is required. This option will set the GPIO pin Low when the fan is required       |
| CPU Temp. Limit      | The CPU temperature limit beyond which fans are activated                                                                             |



