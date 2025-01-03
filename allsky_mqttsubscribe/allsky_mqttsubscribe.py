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
from flatten_json import flatten

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
            "help": "The name for the extra variables file"
        },
        "period" : {
            "required": "false",
            "description": "Read Every",
            "help": "Reads data every x seconds.. Zero will disable this and run the check every time the periodic jobs run",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 600,
                "step": 1
            }
        }
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

def mqttsubscribe(params, event):
    """
    Subscribes to an MQTT topic and processes incoming messages.
    Args:
        params (dict): A dictionary containing the following keys:
            - 'extradatafilename' (str): The filename to save extra data.
            - 'period' (int): The period to check if the module should run.
            - 'mqttserver' (str): The MQTT server address.
            - 'mqttport' (int): The MQTT server port.
            - 'mqtttopic' (str): The MQTT topic to subscribe to.
            - 'mqttusername' (str, optional): The MQTT username for authentication.
            - 'mqttpassword' (str, optional): The MQTT password for authentication.
    Returns:
        str: The result of the MQTT subscription process. It could be the received message,
             "Invalid JSON" if the message is not a valid JSON, "No message received" if no
             message was received, or an error message if the connection to the MQTT server failed.
    """
    result = ""
    extra_data = {}
    extradatafilename = params['extradatafilename']
    period = int(params['period'])
    mqtt_server = params['mqttserver']
    mqtt_port = int(params['mqttport'])
    mqtt_topic = params['mqtttopic']

    # Check if the module should run
    should_run, diff = s.shouldRun(metaData['module'], period)

    if should_run:
        try:
            # MQTT client callbacks for connection
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    s.log(1, f'INFO: Connected to MQTT server {mqtt_server}:{mqtt_port}')
                    client.subscribe(mqtt_topic)
                else:
                    s.log(1, f'ERROR: Connection to MQTT server failed with code {rc}')

            # MQTT client callbacks for message
            def on_message(client, userdata, msg):
                nonlocal result
                nonlocal extra_data
                try:
                    payload = msg.payload.decode('utf-8')
                    s.log(1, f'INFO: Received message: {payload}')
                    json_data = json.loads(payload)
                    extra_data = json_data
                except json.JSONDecodeError as e:
                    s.log(1, f'ERROR: Failed to decode JSON message: {e}')
                    result = "Invalid JSON"

            # Create MQTT client and connect to the server
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message

            # Set MQTT username and password if provided
            if params['mqttusername'] and params['mqttpassword']:
                client.username_pw_set(params['mqttusername'], params['mqttpassword'])

            client.connect(mqtt_server, mqtt_port, 60)

            # Run the client for a second to connect and receive messages
            client.loop_start()
            time.sleep(1)
            client.loop_stop()
            client.disconnect()

            # Check if a message was received
            if not extra_data:
                result = "No message received"

            # Flatten the object (in case this is a nested JSON) and save the extra data and set the last run
            extra_data = flatten(extra_data)
            result = extra_data  # Update the result with the flattened data
            s.log(1, f'INFO: Final result: {result}')
            s.saveExtraData(extradatafilename, extra_data)
            s.setLastRun(metaData['module'])

        # Handle exceptions
        except Exception as e:
            s.log(1, f'ERROR: Failed to connect to MQTT server: {e}')
            result = "Failed to connect to MQTT server"

    # Return the result if the module should not run yet    
    else:
        result = f'Will run in {(period - diff):.2f} seconds'
        s.log(1,f'INFO: {result}')
        return result

    return result

# Cleanup function to be called when the module is disabled
def mqttimport_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": [
                "allskymqttsubscribe.json"
            ],
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
