#TODO - Fix QOS 2 on MQTT
""" allsky_publishdata.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

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

class ALLSKYPUBLISHDATA(ALLSKYMODULEBASE):
    
	meta_data = {
		"name": "Publish Data to Redis/MQTT/REST/influxDB",
		"description": "Publish Allsky data to Redis, MQTT, REST, or influxDB",
		"module": "allsky_publishdata",
		"version": "v1.0.3",
		"centersettings": "false",
		"testable": "true",
		"group": "Data Export",
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
			"mqttQos": "2",
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
				"help": "Comma seperated list of additional variables to export to json.",
				"tab": "General"
			},
			"extradata1": {
				"required": "false",
				"description": "Extra data to export",
				"help": "Comma seperated list of additional variables to export to json.",
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
				"help": "The url and port number of the influxdb host.",
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
				"help": "InfluxDB user access token.",
				"secret": "true",         
				"tab": "Influx"             
			},       
			"influxbucket": {
				"required": "false",
				"description": "InfluxDB Bucket",
				"help": "Name of InfluxDB bucket.",
				"tab": "Influx"       
			},
			"influxorg": {
				"required": "false",
				"description": "InfluxDB Organization",
				"help": "Name of the InfluxDB organization in which the database/bucket is located. Leave default (-) if you're using InfluxDB v1 default installation.",
				"tab": "Influx"         
			},
			"influxtypes": {
				"required": "false",
				"description": "Data Types",
				"help": "Allsky datatypes that can be sent to influx.",
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
				"help": "Host.",
				"tab": "Redis"          
			},
			"redisPort": {
				"required": "false",
				"description": "Redis Port",
				"help": "The port number for the redis server, defaults to 6379.",
				"tab": "Redis" 
			},
			"redisDatabase" : {
				"required": "false",
				"description": "Redis Database",
				"help": "Select the redis database (0-3) to publish to.",
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
				"help": "Use the current timestamp as the redis key.",
				"tab": "Redis",
				"type": {
					"fieldtype": "checkbox"
				} 
			},     
			"redisKey": {
				"required": "false",
				"description": "Redis Key",
				"help": "Use a specific redis key.",
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
			"mqtthostdetails": {
				"description": "MQTT Host",
				"help": "The url and port number of the mqtt host, 1883 for NON SSL or 8883 for SSL.",
				"tab": "MQTT",
				"url": {
					"id": "mqttHost"
				},
				"port": {
					"id": "mqttPort"				
				},
				"type": {
					"fieldtype": "host"
				}     
			},
			"mqttloopdelay": {
				"required": "false",
				"description": "Loop Delay(s)",
				"help": "The loop delay, only increase this if you experience issues with messages missing in the broker.",
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
				"secret": "true",
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
				"help": "Host.",
				"tab": "POST" 
			},
			"mqttQos": {
				"required": "false",
				"description": "MQTT QoS",
				"help": "0 - (At most once) No guarantee of delivery (fire and forget), 1 - (At least once) Ensures message is delivered at least once (may be duplicated), 2 - (Exactly once) Ensures message is delivered only once (most reliable, but slower).",
				"tab": "MQTT",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2,
					"step": 1
				}          
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
    
	_required_variables = {}
	_all_variables = {}
	_json_data = {}
 
	def _send_to_influxdb(self):
		result = ''
		influx_host = self.get_param('influxhost', '', str)
		influx_port = self.get_param('influxport', 8086, int)      
		influx_token = self.get_param('influxtoken', '', str)
		influx_org = self.get_param('influxorg', '', str)
		influx_bucket = self.get_param('influxbucket', '', str)
		influx_types_string = self.get_param('influxtypes', 'number,temperature', str, True)

		influx_types = influx_types_string.split(',')
		influx_host = f'{influx_host}:{influx_port}'

		try:
			self.log(4, f'Sending to {influx_host}, org {influx_org}, bucket {influx_bucket}')
			write_client = influxdb_client.InfluxDBClient(url=influx_host, token=influx_token, org=influx_org)
			
			ping_result = write_client.ping()
			if ping_result:
				influxdb_version = write_client.version()
				self.log(4, f'INFO: Ping InfluxDB server at {influx_host}:{influx_port} succeeded. Version {influxdb_version} found')
				write_api = write_client.write_api(write_options=SYNCHRONOUS)
				
				points = []
				for variable in self._required_variables:
					if variable:
						if variable in self._all_variables:
							if self._all_variables[variable]['type'] in influx_types:
								points.append(
									Point(variable).tag(variable, self._all_variables[variable]['value']).field(variable, self._all_variables[variable]['value'])
								)
								self.log(4, f'Sending {variable} = {self._all_variables[variable]["value"]}')
							else:
								self.log(4, f'{variable} cannot be sent to InfluxDB as its of type "{self._all_variables[variable]["type"]}", valid types are "{influx_types_string}"')
						else:
							self.log(4, f'Sending {variable} not found')
					else:
						self.log(4, f'{variable} is false!!!')
				if points:
					write_api.write(bucket=influx_bucket, org=influx_org, record=points)
					result = f'Data written to InfluxDB server at {influx_host}:{influx_port}'
					self.log(4, f'INFO: {result}')
				else:
					result = f'NO data written to InfluxDB server at {influx_host}:{influx_port} as no valid variables found'
					self.log(4, f'WARNING: {result}')
        
			else:
				result = f'Failed to ping InfluxDB server at {influx_host}:{influx_port}'
				self.log(0, f'ERROR in {__file__: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'Module influxdb failed on line {eTraceback.tb_lineno} - {e}'
			self.log(0, f'ERROR in {__file__: {result}')
   
		return result
   
	def _send_to_redis(self):
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
					redis_object.set(redis_key, json.dumps(self._json_data))
					self.log(4, f'INFO: Published to Redis server at {redis_host}:{redis_port}, Database: {redis_database}, Key: {redis_key}')        
				except Exception as e:    
					eType, eObject, eTraceback = sys.exc_info()
					result = f'Failed to connect to the Redis server at {redis_host}:{redis_port} {eTraceback.tb_lineno} - {e}'
					self.log(0, f'ERROR in {__file__: {result}')
			else:
				result = f'Please specify a topic for Redis to publish to'
				self.log(0, f'ERROR in {__file__: {result}')

		else:
			result = f'Please specify a host for Redis to publish to'
			self.log(0, f'ERROR in {__file__: {result}')
    
	def _send_to_mqtt(self):
		result = ''
		mqtt_topic = self.get_param('mqttTopic', 'allsky', str, True)
		mqtt_username = self.get_param('mqttUsername', '', str)
		mqtt_password = self.get_param('mqttPassword', '', str)
		mqtt_secure = self.get_param('mqttusesecure', True, bool)
		mqtt_host = self.get_param('mqttHost', '127.0.0.1', str, True)
		mqtt_port = self.get_param('mqttPort', 1883, int)
		mqtt_loop_delay = self.get_param('mqttloopdelay', 5, int)
		mqtt_qos = self.get_param('mqttQos', 2, int)

		if mqtt_host:
			if mqtt_topic:
       
				mqtt_data = {}
				for variable in self._required_variables:
					if variable:
						if variable in self._all_variables:
								mqtt_data[variable] = self._all_variables[variable]["value"]
								self.log(4, f'MQTT - Sending {variable} = {self._all_variables[variable]["value"]}')
						else:
							self.log(4, f'MQTT - Sending {variable} not found')
					else:
						self.log(4, f'MQTT - {variable} is false!!!')

				if mqtt_data:
					mqtt_data['utc'] = self._get_utc_timestamp()

					client = paho.Client(protocol=paho.MQTTv5)
					#client.on_connect = self._mqtt_on_connect
					#client.on_publish = self._mqtt_on_publish        
					if mqtt_username and mqtt_password:
						client.username_pw_set(mqtt_username, mqtt_password)

					if mqtt_secure:
						client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

					client.connect(mqtt_host, mqtt_port)
					message_info = client.publish(mqtt_topic, json.dumps(mqtt_data), qos=mqtt_qos)
					message_info.wait_for_publish(mqtt_loop_delay)
					client.loop(mqtt_loop_delay)
					is_published = message_info.is_published()
					client.disconnect()
					if is_published:
						self.log(4, f'INFO: MQTT - Published to MQTT on topic: {mqtt_topic}')
					else:
						self.log(4, f'ERROR: MQTT - No data published to topic: {mqtt_topic}')
				else:
					result = f'NO data written to MQTT server at {mqtt_host}:{mqtt_port} as no valid variables found'
					self.log(4, f'WARNING: {result}')
		
			else:
				result = f'MQTT - Please specify a topic to publish'
				self.log(0, f'ERROR in {__file__: {result}')
		else:
			result = f'MQTT - Please specify a MQTT host to publish to'
			self.log(0, f'ERROR in {__file__: {result}')
       
		return result
            
	def _get_utc_timestamp(self):
		dt = datetime.datetime.now(datetime.timezone.utc)
		utc_time = dt.replace(tzinfo=datetime.timezone.utc)
		utc_timestamp = utc_time.timestamp()
		return int(utc_timestamp)
  
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
		use_mqtt = self.get_param('mqttEnabled', False, bool)
  
		self._all_variables = allsky_shared.get_all_allsky_variables(True, '', True, True)
		self._required_variables = self._required_variables.split(',')
		for variable in self._required_variables:
			if variable:
				if variable in self._all_variables:
					variable_value = self._all_variables[variable]['value']
					#variable_value = self._change_type(variable_value)
					self._json_data[variable] = variable_value
				else:
					self.log(0, f'ERROR in {__file__: Cannot locate environment variable {variable} specified in the extradata')
			else:
				self.log(0, 'ERROR in {__file__: Empty environment variable specified in the extradata field. Check commas!')

			self._json_data['utc'] = self._get_utc_timestamp()
   
		if use_redis:
			self._send_to_redis()

		if use_influx:
			self._send_to_influxdb()

		if use_mqtt:
			self._send_to_mqtt()
   
		'''
		if params["postEnabled"]:
			url = params['postEndpoint']
			if url == "":
				s.log(0, "ERROR in {__file__: Please specify an endpoint to publish to")
				return

			r = requests.post(params["postEndpoint"], json=jsonData)
			s.log(4, f"INFO: POST status code {r.status_code}")
		'''
		return result


def publishdata(params, event):
	allsky_publishdata = ALLSKYPUBLISHDATA(params, event, metaData)
	result = allsky_publishdata.run()

	return result  
