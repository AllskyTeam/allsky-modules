# AllSky Influxdb Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Day time, Night time |


This module allows data to be sent to a Influxdb database. 

|  Setting | Description  |
| ------------ | ------------ |
| Influxdb host | The hostname or IP address of the Influxdb server. In most cases this will be 'localhost' |
| Influxdb Port | The port number the Influx database server is listening on. The default is 8086 and you should not normally need to change this |
| Username | The username to loginto the Influx database server with |
| Password | The password for the user |
| Database | The database on the influx server to update. **NOTE: This database must exist** |
| Values | A comma seperated list of the variables to send to the database |

The Values parameter is a comma seperated list of variables from AllSky to send to the database. The available variables can be found in the overlay editor, under the field list.

An example might look like

`AS_GAIN,AS_EXPOSURE_US`

The will send the Gain and Exposure 