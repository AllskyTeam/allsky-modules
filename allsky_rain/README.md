# Rain Detection Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Daytime, Capture Nighttime Capture  |


This module allows the interfacing of a cheap digital rain detector. If rain is detected then
an environment vairable is set that can be used in other modules. For example there is no point
trying to calaculate sky quality or star counts if it's raining.

|  Setting | Description  |
| ------------ | ------------ |
| Input Pin | The gpio pin the detector is connected to.  |
| Invert  | Normally the cheap sensors are high when it's not raining and low when it is. This setting reverse that. |


The following variables are set by this module and can be used in modules:

|  Variable set | Description  |
| ----------------------- | ------------ |
| AS_RAINSTATE | Either "Raining" or "Not Raining".  |
| AS_ALLSKYRAINFLAG  | Either True if it's raining, or False if it's not. |
| AS_ALLSKYRAINFLAGINT  | Either 1 if it's raining, or 0 if it's not. |
