# AllSky wsUPShat Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Periodic |

A simple module to read sensor values from Waveshare UPS hat (D) via i2c bus
i2c Bus address
- 0x2d MCU chip
- 0x43 INA219

INA219 register values available
- 01 shunt voltage (mV)
- 02 bus voltage (V)
- 03 power (W)
- 04 current (mA)
- 05 calibration (conf)

Example Extra Data File
-----------------------
{
    "AS_WS_UPS_PSU_VOLTAGE_V"       <-- Source Power Supply Voltage
    "AS_WS_UPS_SHUNT_VOLTAGE_V"     <-- Voltage across internal Shunt
    "AS_WS_UPS_BUS_VOLTAGE_V"       <-- Bus Voltage - Effectively Internal Battery Voltage
    "AS_WS_UPS_CURRENT_A"           <-- Current flowing via Shunt
    "AS_WS_UPS_POWER_W"             <-- Power being consumed by load
    "AS_WS_UPS_PERCENT"             <-- Indicative Percentage charge in internal batteries
}  
