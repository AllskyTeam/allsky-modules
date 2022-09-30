# AllSky Rain Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Day time, Night time  |


This module allows the interfacing of a cheap digital rain detector. If rain is detected then
an environment vairable is set that can be used in other modules. For example there is no point
trying to calaculate sky quality or star counts if its raining.

|  Setting | Description  |
| ------------ | ------------ |
| Input Pin | The gpio pin the detector is connected to  |
| Invert  | Normally the cheap sensors are high when its not raining and low when it is. THis setting will reverse this |
