# AllSky DFR0672 Fan Light Control Module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

This module works with th DFRobot0672 HAT to control the onboard fan and 3x multicolor LEDs
The fan is controlled based on internal CPU temperature exceeding a set limit, to cool the fan.

## Available Sensors
| Sensor Type   | Description
|---------------|---------------------------------------------------------------------------------------------------------------------|
| Internal      | Reads the cpu temperature from the onboard sensor                                
 

The module contains the following options
## Sensor Tab
| Setting              | Description                                                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Read Every           | Interval in seconds at which the CPU temperature is read                                                                              |
| CPU Temp. Limit      | The CPU temperature limit beyond which fans are activated, only used when NOT using PWM fan control                                   |

## Internal Tab
| Setting              | Description                                                                                                                           |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| CPU Temp. Limit      | The CPU temperature limit beyond which fans are activated, only used when NOT using PWM fan control                                   |

