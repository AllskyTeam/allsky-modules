# AllSky Subscribe to MQTT topic Module

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Periodic |

This module subscribes to a specified MQTT topic that contains a JSON object and makes the 'Keys' available as variables in the overlay module.


The module contains the following options

| Setting              | Description                      |Required or Optional |Default Value
|----------------------|----------------------------------|---------------------|-----------
| mqttserver           | MQTT Server name or IP address   |Required             |-
| mqttport             | MQTT Port (usually 1883)         |Optional             |1883
| mqtttopic            | MQTT topic to subscribe to       |Required             |-
| mqttusername         | Username for MQTT broker         |Optional             |-
| mqttpassword         | Password for MQTT broker         |Optional             |-
| extradatafilename    | Name to use for extradata file   |Optional             |allskymqttsubscribe.json
| period               | Update frequency                 |Optional             |60 seconds
| Prefix               | 

NOTE: Set retain flag for your MQTT messages. Otherwise the client may miss the message if data gets published while the script is waiting for the next run.
 
## Allsky Overlay (the values to the top right with 'MQTT' in the name)

![alt text](image-1.png)

## Example output 

MQTT Topic data on Mmosquitto as seen using MQTT Explorer

![alt text](image.png)

JSON from MQTT topic saved to `/home/pi/allsky/config/overlay/extra/allskymqttsubscribe.json`

```json
{
    "MQTT_Heater_Control": "ON",
    "RMS": "0.76",
    "timestamp": "20:11:42"
}
```

Log output from `/var/log/allskyperiodic.log` with DEBUG level set to `4` in AllSky settings

```shell
2024-12-20T20:15:10.014662-06:00 allskypi5 allskperiodic[116931]: INFO: --------------- Running Module allsky_mqttsubscribe ---------------
2024-12-20T20:15:10.014678-06:00 allskypi5 allskperiodic[116931]: INFO: Connected to MQTT server 192.168.1.250:1883
2024-12-20T20:15:10.014697-06:00 allskypi5 allskperiodic[116931]: INFO: Received message: {
2024-12-20T20:15:10.014717-06:00 allskypi5 allskperiodic[116931]:   "MQTT_Heater_Control": "ON",
2024-12-20T20:15:10.014733-06:00 allskypi5 allskperiodic[116931]:   "RMS": "0.76",
2024-12-20T20:15:10.014752-06:00 allskypi5 allskperiodic[116931]:   "timestamp": "20:11:42"
2024-12-20T20:15:10.014766-06:00 allskypi5 allskperiodic[116931]: }
2024-12-20T20:15:10.014780-06:00 allskypi5 allskperiodic[116931]: INFO: Final result: {'MQTT_Heater_Control': 'ON', 'RMS': '0.76', 'timestamp': '20:11:42'}
```

JSON payload can also be nested:

```json
{
  "name": "Heater",
  "gpio": 21,
  "properties": {
    "direction": "out",
    "state": "off"
  }
}
```

in which case, root keys are appended as suffixes to the child keys (in this case, `properties` is appended)

```shell
2024-12-21T17:13:15.771164-06:00 allskypi5 allskperiodic[45626]: INFO: --------------- Running Module allsky_mqttsubscribe ---------------
2024-12-21T17:13:15.771181-06:00 allskypi5 allskperiodic[45626]: INFO: Connected to MQTT server 192.168.1.250:1883
2024-12-21T17:13:15.771199-06:00 allskypi5 allskperiodic[45626]: INFO: Received message: {
2024-12-21T17:13:15.771216-06:00 allskypi5 allskperiodic[45626]:   "name": "Heater",
2024-12-21T17:13:15.771234-06:00 allskypi5 allskperiodic[45626]:   "gpio": 21,
2024-12-21T17:13:15.771250-06:00 allskypi5 allskperiodic[45626]:   "properties": {
2024-12-21T17:13:15.771265-06:00 allskypi5 allskperiodic[45626]:     "direction": "out",
2024-12-21T17:13:15.771280-06:00 allskypi5 allskperiodic[45626]:     "state": "off"
2024-12-21T17:13:15.771309-06:00 allskypi5 allskperiodic[45626]:   }
2024-12-21T17:13:15.771325-06:00 allskypi5 allskperiodic[45626]: }
2024-12-21T17:13:15.771363-06:00 allskypi5 allskperiodic[45626]: INFO: Final result: {'name': 'Heater', 'gpio': 21, 'properties_direction': 'out', 'properties_state': 'off
```
