# AllSky Influxdb Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Day time, Night time |


This module allows data to be sent to a Influxdb database. 

|  Setting | Description  |
| ------------ | ------------ |
| InfluxDB Host | The hostname or IP address of the Influxdb server with protocol. In most cases this will be 'http://localhost' |
| InfluxDB Port | The port number the Influx database server is listening on. The default is 8086 and you should not normally need to change this |
| InfluxDB Username | The username to login to the Influx database server with (mostly for InfluxDB v1, InfluxDB v2 uses Access Tokens as default) |
| InfluxDB Password | The password for the user (mostly for InfluxDB v1, InfluxDB v2 uses Access Tokens as default) |
| InfluxDB Access Token | InfluxDB user access token (if not using username and password) |
| InfluxDB v2 Bucket | Enable if you're using InfluxDB v2 |
| InfluxDB v1 Database / v2 Bucket | The database for v1 or bucket for v2 on the influx server to update. **NOTE: This database/bucket must exist** |
| InfluxDB Organization | Name of the InfluxDB organization in which the database/bucket is located. Leave default (-) if you're using InfluxDB v1 default installation |
| AllSky Values | A comma seperated list of the variables to send to the database |

The Values parameter is a comma seperated list of variables from AllSky to send to the database. The available variables can be found in the overlay editor, under the field list.

An example might look like

`AS_GAIN,AS_EXPOSURE_US`

The will send the Gain and Exposure 
