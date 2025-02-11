""" allsky_publishdata.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will publish data to Redis, MQTT or REST

"""
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import json
import datetime
import glob
import requests
import paho.mqtt.client as paho
from paho import mqtt
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import redis
import sys

metaData = {
	"name": "AllSKY Redis/MQTT/REST/influxDB Data Publish",
	"description": "Publish AllSKY data to Redis, MQTT, influxDB or REST",
	"module": "allsky_publishdata",
	"version": "v1.0.3",
	"centersettings": "false",
	"testable": "true", 
	"events": [
	    "day",
	    "night",
	    "periodic"
	],
	"experimental": "yes",
	"arguments": {
	    "extradata": "",
		"influxEnabled": "false",
		"influxhost": "",
		"influxport": "8086",
		"influxtoken": "",
		"influxbucket": "",
		"influxorg": "",
		"influxtypes": "number,temperature",  
	    "redisEnabled": "false",
		"redisTimestamp": "true",
		"redisDatabase": "0",
	    "redisHost": "",
	    "redisPort": "6379",
	    "redisKey": "",
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
	    "extradata1": {
	        "required": "false",
	        "description": "Extra data to export",
	        "help": "Comma seperated list of additional variables to export to json",
	        "tab": "General",
	        "type": {
	            "fieldtype": "variable"
	        }                             
	    },
	    "influxEnabled": {
	        "required": "false",
	        "description": "Publish to influx",
	        "tab": "Influx",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },     
		"influxhostdetails": {
      		"description": "Influx Host",
			"help": "The url and port number of the influxdb host",
			"tab": "Influx",
			"url": {
				"id": "influxhost"
			},
			"port": {
				"id": "influxport"				
			},
	        "type": {
	            "fieldtype": "host"
	        }     
		},      
	    "influxtoken": {
	        "required": "false",
	        "description": "InfluxDB Access Token",
	        "help": "InfluxDB user access token",
			"secret": "true",         
	        "tab": "Influx"             
	    },       
	    "influxbucket": {
	        "required": "false",
	        "description": "InfluxDB Bucket",
	        "help": "Name of InfluxDB bucket",
	        "tab": "Influx"       
	    },
	    "influxorg": {
	        "required": "false",
	        "description": "InfluxDB Organization",
	        "help": "Name of the InfluxDB organization in which the database/bucket is located. Leave default (-) if you're using InfluxDB v1 default installation",
	        "tab": "Influx"         
	    },
	    "influxtypes": {
	        "required": "false",
	        "description": "Data Types",
	        "help": "Allsky datatypes that can be sent to influx",
	        "tab": "Influx"     
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
	        "description": "Address of the redis Host",
	        "help": "Host",
	        "tab": "Redis"          
	    },
	    "redisPort": {
	        "required": "false",
	        "description": "Redis Port",
	        "help": "The port number for the redis server, fefaults to 6379",
	        "tab": "Redis" 
	    },
	    "redisDatabase" : {
	        "required": "false",
	        "description": "Redis Database",
	        "help": "Select the redis database (0-3) to publish to",
	        "tab": "Redis",        
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 3,
	            "step": 1
	        }                     
	    },     
	    "redisTimestamp": {
	        "required": "false",
	        "description": "Use timestamp",
	        "help": "Use the current timestamp as the redis key",         
	        "tab": "Redis",
	        "type": {
	            "fieldtype": "checkbox"
	        } 
	    },     
	    "redisKey": {
	        "required": "false",
	        "description": "Redis Key",
	        "help": "Use a specific redis key",          
	        "tab": "Redis" 
	    },
	    "redisPassword": {
	        "required": "false",
	        "description": "Password for the redis server if required",
	        "tab": "Redis",
			"secret": "true"
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
	            "changes":[
                 	"Set correct data types in json (Issue 129)",
					"Added influxdb"
				]
	        }
	    ]                                                         
	}    
}

class ALLSKYPUBLISHDATA(ALLSKYMODULEBASE):
	_required_variables = {}
	_all_variables = {}
 
	def _send_to_influxdb(self):
		influx_host = self.get_param('influxhost', '', str)
		influx_port = self.get_param('influxport', 8086, int)      
		influx_token = self.get_param('influxtoken', '', str)
		influx_org = self.get_param('influxorg', '', str)
		influx_bucket = self.get_param('influxbucket', '', str)
		influx_types_string = self.get_param('influxtypes', 'number,temperature', str, True)

		influx_types = influx_types_string.split(',')
		influx_host = f'{influx_host}:{influx_port}'


		#try:
		allsky_shared.log(4, f'Sending to {influx_host}, org {influx_org}, bucket {influx_bucket}')
		write_client = influxdb_client.InfluxDBClient(url=influx_host, token=influx_token, org=influx_org)
		
		ping_result = write_client.ping()
		if ping_result:
			influxdb_version = write_client.version()
			allsky_shared.log(4, f'INFO: Ping InfluxDB server at {influx_host}:{influx_port} succeeded. Version {influxdb_version} found')
			write_api = write_client.write_api(write_options=SYNCHRONOUS)
			
			points = []
			for variable in self._required_variables:
				if variable:
					if variable in self._all_variables:
						if self._all_variables[variable]['type'] in influx_types:
							points.append(
								Point(variable).tag(variable, self._all_variables[variable]['value']).field(variable, self._all_variables[variable]['value'])
							)
							allsky_shared.log(4, f'Sending {variable} = {self._all_variables[variable]["value"]}')
						else:
							allsky_shared.log(4, f'{variable} cannot be sent to InfluxDB as its of type "{self._all_variables[variable]["type"]}", valid types are "{influx_types_string}"')
					else:
						allsky_shared.log(4, f'Sending {variable} not found')
				else:
					allsky_shared.log(4, f'{variable} is false!!!')
		
			if points:
				write_api.write(bucket=influx_bucket, org=influx_org, record=points)
				result = f'Data written to InfluxDB server at {influx_host}:{influx_port}'
				allsky_shared.log(4, f'INFO: {result}')     
		else:
			result = f'Failed to ping InfluxDB server at {influx_host}:{influx_port}'
			allsky_shared.log(0, f'ERROR: {result}')
   
   			#except Exception as e:
			#	eType, eObject, eTraceback = sys.exc_info()
			#	allsky_shared.log(0, f'ERROR: Module influxdb failed on line {eTraceback.tb_lineno} - {e}')
   
        
	def _get_utc_timestamp(self):
		dt = datetime.datetime.now(datetime.timezone.utc)
		utc_time = dt.replace(tzinfo=datetime.timezone.utc)
		utc_timestamp = utc_time.timestamp()
		return int(utc_timestamp)

	def _mqtt_on_connect(self, client, userdata, flags, rc, properties=None): 
		allsky_shared.log(4, f"INFO: MQTT - CONNACK received with code {rc}.")

	def _mqtt_on_publish(self, client, userdata, mid, properties=None):
		allsky_shared.log(4, f"INFO: MQTT - Message published {mid}.")

	def _change_type(self, value):
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
			
	def run(self):
		result = 'No result returned'
		self._required_variables = self.get_param('extradata', '', str, True)
		use_redis = self.get_param('redisEnabled', False, bool)
		use_influx = self.get_param('influxEnabled', False, bool)
  
		json_data = {}
		self._all_variables = allsky_shared.get_all_allsky_variables(True, '', True, True)
		self._required_variables = self._required_variables.split(',')
		for variable in self._required_variables:
			if variable:
				if variable in self._all_variables:
					variable_value = self._all_variables[variable]['value']
					#variable_value = self._change_type(variable_value)
					json_data[variable] = variable_value
				else:
					allsky_shared.log(0, f'ERROR: Cannot locate environment variable {variable} specified in the extradata')
			else:
				allsky_shared.log(0, 'ERROR: Empty environment variable specified in the extradata field. Check commas!')

			json_data['utc'] = self._get_utc_timestamp()
   
		if use_redis:
			redis_usetimestamp = self.get_param('redisTimestamp', True, bool)
			redis_database = self.get_param('redisDatabase', 0, int)
			redis_key = self.get_param('redisKey', 'Allsky', str, True)
			redis_host = self.get_param('redisHost', 'localhost', str, True)
			redis_password = self.get_param('redisPassword', '', str, True)
			redis_port = self.get_param('redisPort', 6379, int)
   
			if redis_host:
				if redis_key:
					if redis_usetimestamp:
						redis_key = self._get_utc_timestamp()
					try:
						redis_object = redis.Redis(host=redis_host, port=redis_port, db=redis_database, password=redis_password)
						redis_object.set(redis_key, json.dumps(json_data))
						allsky_shared.log(1, f'INFO: Published to Redis server at {redis_host}:{redis_port}, Database: {redis_database}, Key: {redis_key}')        
					except Exception as e:    
						eType, eObject, eTraceback = sys.exc_info()
						result = f'ERROR: Failed to connect to the Redis server at {redis_host}:{redis_port} {eTraceback.tb_lineno} - {e}'
						allsky_shared.log(0, result)      
				else:
					result = f'Please specify a topic for Redis to publish to'
					allsky_shared.log(0, f'ERROR: {result}')

			else:
				result = f'Please specify a host for Redis to publish to'
				allsky_shared.log(0, f'ERROR: {result}')

		if use_influx:
			self._send_to_influxdb()

       
		'''
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
		'''
		return result


def publishdata(params, event):
	allsky_publishdata = ALLSKYPUBLISHDATA(params, event, metaData)
	result = allsky_publishdata.run()

	return result  
