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
import paho.mqtt.client as mqtt
import redis

metaData = {
    "name": "AllSKY Redis/MQTT/REST Data Publish",
    "description": "Publish AllSKY data to Redis, MQTT or REST",
    "module": "allsky_publishdata",
    "events": [
        "day",
        "night"
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
        "mqttHost": "",
        "mqttPort": "1883",
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
        "mqttHost": {
            "required": "false",
            "description": "MQTT Host",
            "help": "Host",
            "tab": "MQTT"
        },
        "mqttPort": {
            "required": "false",
            "description": "MQTT Port",
            "help": "Default: 1883. Websocket 9001",
            "tab": "MQTT"
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
    }
}


def get_utc_timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return int(utc_timestamp)


def read_extra_data():
    json_data = dict()
    extra_data_path = s.getEnvironmentVariable("ALLSKY_EXTRA")
    if extra_data_path is not None:
        files = glob.glob(extra_data_path + "/*.json")
        for f in files:
            extra_name = os.path.basename(f)
            extra_name = extra_name.split(".")[0]

            with open(f, "r") as fp:
                json_data[extra_name] = json.load(fp)

    return json_data


def publishdata(params, event):
    s.env = {}
    json_data = read_extra_data()

    extra_entries = params["extradata"].split(",")
    for env_var in extra_entries:
        env_var = env_var.lstrip()
        env_var = env_var.rstrip()
        env_var_value = s.getEnvironmentVariable(env_var)
        if env_var:
            if env_var_value is not None:
                json_data[env_var] = env_var_value
                s.env[env_var] = env_var_value
            else:
                s.log(0, "ERROR: Cannot locate environment variable {0} specified in the extradata".format(env_var))
        else:
            s.log(0, "ERROR: Empty environment variable specified in the extradata field. Check commas!")

    json_data["utc"] = get_utc_timestamp()

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

        red.publish(params["redisTopic"], json.dumps(json_data))
        s.log(1, f"INFO: Published to Redis on channel: {channel_topic}")

    if params["mqttEnabled"]:
        channel_topic = params['mqttTopic']
        if channel_topic == "":
            s.log(0, "ERROR: Please specify a topic to publish")
            return

        client = mqtt.Client("AllSkyMeta", transport='websockets')
        if params["mqttUsername"] != "" and params["mqttPassword"] != "":
            client.username_pw_set(params["mqttUsername"], params["mqttPassword"])

        if params["mqttHost"] == "":
            s.log(0, "ERROR: Please specify a MQTT host to publish to")
            return

        client.connect(params["mqttHost"], int(params["mqttPort"]))
        client.publish(params["mqttTopic"], json.dumps(json_data))
        s.log(1, f"INFO: Published to MQTT on channel: {channel_topic}")

    if params["postEnabled"]:
        url = params['postEndpoint']
        if url == "":
            s.log(0, "ERROR: Please specify an endpoint to publish to")
            return

        r = requests.post(params["postEndpoint"], json=json_data)
        s.log(1, f"INFO: POST status code {r.status_code}")

    return "Allsky data published"
