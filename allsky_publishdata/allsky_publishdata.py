""" allsky_publishdata.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will publish data to Redis, MQTT or REST

"""
import allsky_shared as s
import os
import json
import datetime
import glob
import requests
import paho.mqtt.client as paho
from paho import mqtt
import redis

metaData = {
    "name": "AllSKY Redis/MQTT/REST Data Publish",
    "description": "Publish AllSKY data to Redis, MQTT or REST",
    "module": "allsky_publishdata",
    "version": "v1.0.3",
    "events": [
        "day",
        "night",
        "periodic"
    ],
    "experimental": "yes",
    "arguments": {
        "extradata": "CAMERA_TYPE,DAY_OR_NIGHT,CURRENT_IMAGE,FULL_FILENAME,ALLSKY_VERSION",
        "redisEnabled": "false",
        "redisHost": "",
        "redisPort": "6379",
        "redisTopic": "",
        "redisPassword": "",
        "mqttEnabled": "false",
        "mqttusesecure": "true",
        "mqttHost": "",
        "mqttPort": "1883",
        "mqttloopdelay": "5",
        "mqttTopic": "",
        "mqttUsername": "",
        "mqttPassword": "",
        "postEnabled": "false",
        "postEndpoint": ""
    },
    "argumentdetails": {
        "extradata": {
            "required": "false",
            "description": "Extra data to export",
            "help": "Comma seperated list of additional variables to export to json",
            "tab": "General"
        },
        "redisEnabled": {
            "required": "false",
            "description": "Publish to Redis",
            "tab": "Redis",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "redisHost": {
            "required": "false",
            "description": "Redis Host",
            "help": "Host",
            "tab": "Redis"
        },
        "redisPort": {
            "required": "false",
            "description": "Redis Port",
            "help": "Default: 6379",
            "tab": "Redis"
        },
        "redisTopic": {
            "required": "false",
            "description": "Redis Topic",
            "tab": "Redis"
        },
        "redisPassword": {
            "required": "false",
            "description": "Password",
            "tab": "Redis"
        },
        "mqttEnabled": {
            "required": "false",
            "description": "Publish to MQTT",
            "tab": "MQTT",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "mqttusesecure": {
            "required": "false",
            "description": "Use Secure Connection",
            "tab": "MQTT",
            "type": {
                "fieldtype": "checkbox"
            }
        },        
        "mqttHost": {
            "required": "false",
            "description": "MQTT Host",
            "tab": "MQTT"
        },
        "mqttPort": {
            "required": "false",
            "description": "MQTT Port",
            "help": "1883 for NON SSL or 8883 for SSL.",
            "tab": "MQTT"
        },
        "mqttloopdelay": {
            "required": "false",
            "description": "Loop Delay(s)",
            "help": "The loop delay, only increase this if you experience issues with messages missing in the broker",
            "tab": "MQTT",
            "type": {
                "fieldtype": "spinner",
                "min": 0.5,
                "max": 10,
                "step": 0.5
            }              
        },        
        "mqttTopic": {
            "required": "false",
            "description": "MQTT Topic",
            "tab": "MQTT"
        },
        "mqttUsername": {
            "required": "false",
            "description": "Username",
            "tab": "MQTT"
        },
        "mqttPassword": {
            "required": "false",
            "description": "Password",
            "tab": "MQTT"
        },
        "postEnabled": {
            "required": "false",
            "description": "Publish to endpoint",
            "tab": "POST",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "postEndpoint": {
            "required": "false",
            "description": "POST endpoint",
            "help": "Host",
            "tab": "POST"
        }
    },
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Fix MQTT SSL",
                    "Add MQTT timeout"
                ]
            } 
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Added module to periodic flow"
            }
        ],
        "v1.0.3" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Set correct data types in json (Issue 129)"
            }
        ]                                                         
    }    
}


def get_utc_timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return int(utc_timestamp)


def read_extra_data():
    jsonData = dict()
    extra_data_path = s.getEnvironmentVariable("ALLSKY_EXTRA")
    if extra_data_path is not None:
        files = glob.glob(extra_data_path + "/*.json")
        for f in files:
            extra_name = os.path.basename(f)
            extra_name = extra_name.split(".")[0]

            with open(f, "r") as fp:
                data = json.load(fp)
                for var in data:
                    jsonData[var] = data[var]

    return jsonData

def MQTTonConnect(client, userdata, flags, rc, properties=None): 
    s.log(4, f"INFO: MQTT - CONNACK received with code {rc}.")

def MQTTonPublish(client, userdata, mid, properties=None):
    s.log(4, f"INFO: MQTT - Message published {mid}.")

def changeType(value):
    if value.lower() in ['true', 'false'] or value.lower() in ['on', 'off']:
        if value == 'true' or value == 'on':
            value = True
        if value == 'false' or value == 'off':
            value = False
        return value
    
    try:
        value = int(value)
        return value
    except ValueError:
        pass
    
    try:
        if '.' in value or 'e' in value.lower():
            value = float(value)
            return value
    except ValueError:
        pass
    
    return value
        
def publishdata(params, event):
    s.env = {}
    extraData = read_extra_data()
    jsonData = {}
    extraEntries = params["extradata"].split(",")
    for envVar in extraEntries:
        envVar = envVar.lstrip()
        envVar = envVar.rstrip()
        envVarValue = s.getEnvironmentVariable(envVar)
        if envVar:
            if envVarValue is None:
                if envVar in extraData:
                    envVarValue = extraData[envVar]
                    
            if envVarValue is not None:
                envVarValue = changeType(envVarValue)
                jsonData[envVar] = envVarValue
                s.env[envVar] = envVarValue
            else:
                s.log(0, "ERROR: Cannot locate environment variable {0} specified in the extradata".format(envVar))
        else:
            s.log(0, "ERROR: Empty environment variable specified in the extradata field. Check commas!")

    jsonData["utc"] = get_utc_timestamp()
        
    if params["redisEnabled"]:
        channel_topic = params['redisTopic']
        if channel_topic == "":
            s.log(0, "ERROR: Please specify a topic to publish")
            return
        if params["redisHost"] == "":
            s.log(0, "ERROR: Please specify a host for Redis to publish to")
            return

        red = redis.StrictRedis(params["redisHost"], int(params["redisPort"]), charset="utf-8",
                                password=params["redisPassword"])
        if params["redisTopic"] == "":
            s.log(0, "ERROR: Please specify a topic for Redis to publish to")
            return

        red.publish(params["redisTopic"], json.dumps(jsonData))
        s.log(1, f"INFO: Published to Redis on channel: {channel_topic}")

    if params["mqttEnabled"]:
        channel_topic = params['mqttTopic']
        if channel_topic == "":
            s.log(0, "ERROR:MQTT - Please specify a topic to publish")
            return

        client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        client.on_connect = MQTTonConnect
        client.on_publish = MQTTonPublish        
        if params["mqttUsername"] != "" and params["mqttPassword"] != "":
            client.username_pw_set(params["mqttUsername"], params["mqttPassword"])

        if params["mqttHost"] == "":
            s.log(0, "ERROR: MQTT - Please specify a MQTT host to publish to")
            return

        if params["mqttusesecure"]:
            client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

        client.connect(params["mqttHost"], int(params["mqttPort"]))

        client.publish(params["mqttTopic"], json.dumps(jsonData),qos=1)
        s.log(1, f"INFO: MQTT - Published to MQTT on channel: {channel_topic}")
        delay = int(params['mqttloopdelay'])
        client.loop(delay)
        client.disconnect()
        
    if params["postEnabled"]:
        url = params['postEndpoint']
        if url == "":
            s.log(0, "ERROR: Please specify an endpoint to publish to")
            return

        r = requests.post(params["postEndpoint"], json=jsonData)
        s.log(1, f"INFO: POST status code {r.status_code}")

    return "Allsky data published"
