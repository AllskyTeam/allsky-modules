'''
allsky_boilerplate.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


'''
import allsky_shared as s
import json
import os
import time
import paho.mqtt.client as mqtt

metaData = {
    "name": "Subscribes to MQTT topic and gets messages",
    "description": "Obtains JSON payload from given MQTT topic for use in overlay manager",
    "module": "allsky_mqttsubscribe",
    "version": "v1.0.0",    
    "events": [
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "extradatafilename": "allskymqttsubscribe.json",
        "period": 60,     
        "prefix": "",
        "mqttserver": "",
        "mqttport": 1883,
        "mqtttopic": "",
        "mqttusername": "",
        "mqttpassword": ""
        },
    "argumentdetails": {
        "mqttserver": {
            "required": "true",
            "description": "MQTT server to connect to",
            "help": "Example: 192.168.1.250"
        },  
        "mqttport": {
            "required": "true",
            "description": "MQTT port to connect to",
            "help": "Example: 1883"
        },  
        "mqtttopic": {
            "required": "true",
            "description": "MQTT Topic to subscribe to",
            "help": "Example: astro/NINA"
        },
        "mqttusername": {
            "required": "false",
            "description": "MQTT Username",
            "help": "Username for MQTT server"
        },
        "mqttpassword": {
            "required": "false",
            "description": "MQTT Password",
            "help": "Password for MQTT server"
        },
        "extradatafilename" : {
            "required": "true",
            "description": "Extra Data Filename",
            "help": "The prefix for variables - DO NOT CHANGE unless you have multiple variables that clash"
        },
        "period" : {
            "required": "false",
            "description": "Read Every",
            "help": "Reads data every x seconds.. Zero will disable this and run the check every time the periodic jobs run",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 1
            }
        },
        "prefix" : {
            "required": "false",
            "description": "Prefix for MQTT messages",
            "help": "The prefix to add to the MQTT messages"
        }
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ]                              
    },
    "businfo": [
    ],
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Kumar Challa",
                "authorurl": "https://github.com/chvvkumar",
                "changes": "Initial Release"
            }
        ]
    }
}

def mqttimport(params, event):
    result = ""
    extra_data = {}
    extradatafilename = params['extradatafilename']
    prefix = params['prefix']
    period = int(params['period'])
    mqtt_server = params['mqttserver']
    mqtt_port = int(params['mqttport'])
    mqtt_topic = params['mqtttopic']


    should_run, diff = s.shouldRun(metaData['module'], period)

    if should_run:
        try:
            client = mqtt.Client()
            client.connect(mqtt_server, mqtt_port, 60)
            client.loop_start()
            client.subscribe(mqtt_topic)
            s.log(4, f'INFO: Connected to MQTT server {mqtt_server} on port {mqtt_port} and subscribed to topic {mqtt_topic}')
            def on_message(client, userdata, message):
                nonlocal extra_data
                try:
                    payload = json.loads(message.payload.decode("utf-8"))
                    extra_data.update(payload)
                    with open(extradatafilename, 'w') as outfile:
                        json.dump(extra_data, outfile)
                    s.log(4, f'INFO: Received and saved message: {payload}')
                except json.JSONDecodeError as e:
                    s.log(1, f'ERROR: Failed to decode JSON message: {e}')
            client.on_message = on_message
            result = 'Data retrieved ok at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
            time.sleep(1)
            client.loop_stop()
            client.disconnect()
            s.log(4, f'INFO: Disconnected from MQTT server {mqtt_server}')
        
        except Exception as e:
            s.log(1, f'ERROR: Failed to connect to MQTT server: {e}')
            return "Failed to connect to MQTT server"
    else:
        result = f'Will run in {(period - diff):.2f} seconds'
        s.log(1,f'INFO: {result}')

def mqttimport():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyboiler.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
