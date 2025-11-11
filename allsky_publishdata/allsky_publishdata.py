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
import paho.mqtt.client as mqtt
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import redis
import sys
from typing import Optional, Union
import ssl
import threading
import uuid

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
			"redisList": "",
			"mqttEnabled": "false",
			"mqttusesecure": "true",
			"mqttHost": "",
			"mqttPort": "1883",
			"mqttQos": "2",
			"mqttTopic": "",
      "mqttSelfSigned": "",
   		"mqttpem": "",
			"mqttUsername": "",
			"mqttPassword": "",
			"postEnabled": "false",
			"postEndpoint": ""
		},
		"argumentdetails": {
			"extradata1": {
				"required": "false",
				"description": "Extra data to export",
				"help": "Comma seperated list of additional variables to export to json.",
				"tab": "General"
			},
			"extradata": {
				"required": "false",
				"description": "Extra data to export",
				"help": "Comma seperated list of additional variables to export to json.",
				"tab": "General",
				"type": {
					"fieldtype": "variable",
					"select": "multi"
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
			"redishostdetails": {
				"description": "Redis Host",
				"help": "Address of the redis Host",
				"tab": "Redis",
				"secret": "true",    
				"url": {
					"id": "redisHost"
				},
				"port": {
					"id": "redisPort"				
				},
				"type": {
					"fieldtype": "host"
				}     
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
				"description": "Use Specific Key",
				"help": "Use a spcific key rather than the current timestamp.",
				"tab": "Redis",
				"type": {
					"fieldtype": "checkbox"
				} 
			},     
			"redisKey": {
				"required": "false",
				"description": "Redis Key",
				"help": "Use a specific redis key.",
				"tab": "Redis",
				"filters": {
					"filter": "redisTimestamp",
					"filtertype": "show",
					"values": [
						"redisTimestamp"
					]
				}    
			},
			"redisList": {
				"required": "false",
				"description": "Redis List",
				"help": "Append to the redis key rather than replace it.",
				"tab": "Redis",
				"type": {
					"fieldtype": "checkbox"
				},    
				"filters": {
					"filter": "redisTimestamp",
					"filtertype": "show",
					"values": [
						"redisTimestamp"
					]
				}    
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
			"mqttSelfSigned": {
				"required": "false",
				"description": "Use self signed cert",
				"tab": "MQTT",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "mqttusesecure",
					"filtertype": "show",
					"values": [
						"mqttusesecure"
					]
				}      
			},
			"mqttpem": {
				"required": "false",
				"description": "Path to PEM",
				"tab": "MQTT",
				"filters": {
					"filter": "mqttSelfSigned",
					"filtertype": "show",
					"values": [
						"mqttSelfSigned"
					]
				}      
			},     
			"mqtthostdetails": {
				"description": "MQTT Host",
				"help": "The url and port number of the mqtt host, 1883 for NON SSL or 8883 for SSL.",
				"tab": "MQTT",
				"secret": "true",    
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
			"mqttTopic": {
				"required": "false",
				"description": "MQTT Topic",
				"tab": "MQTT" 
			},
			"mqttUsername": {
				"required": "false",
				"description": "Username",
				"secret": "true",    
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
				"secret": "true",    
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
				self.log(0, f'ERROR in {__file__}: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			result = f'Module influxdb failed on line {eTraceback.tb_lineno} - {e}'
			self.log(0, f'ERROR in {__file__}: {result}')
   
		return result
   
	def _send_to_redis(self):
		redis_usetimestamp = self.get_param('redisTimestamp', True, bool)
		redis_database = self.get_param('redisDatabase', 0, int)
		redis_key = self.get_param('redisKey', 'Allsky', str, True)
		redis_host = self.get_param('redisHost', 'localhost', str, True)
		redis_password = self.get_param('redisPassword', '', str, True)
		redis_port = self.get_param('redisPort', 6379, int)
		redis_list = self.get_param('redisList', False, bool)


		if redis_host:     
			if redis_key:
				if not redis_usetimestamp:
					redis_key = self._get_utc_timestamp()
				try:
					redis_object = redis.Redis(host=redis_host, port=redis_port, db=redis_database, password=redis_password)
			
					if redis_list:
						redis_object.rpush(redis_key, json.dumps(self._json_data))
					else:
						redis_object.set(redis_key, json.dumps(self._json_data))
			
					self.log(4, f'INFO: Published to Redis server at {redis_host}:{redis_port}, Database: {redis_database}, Key: {redis_key}')        
				except Exception as e:    
					eType, eObject, eTraceback = sys.exc_info()
					result = f'Failed to connect to the Redis server at {redis_host}:{redis_port} {eTraceback.tb_lineno} - {e}'
					self.log(0, f'ERROR in {__file__}: {result}')
			else:
				result = f'Please specify a topic for Redis to publish to'
				self.log(0, f'ERROR in {__file__}: {result}')

		else:
			result = f'Please specify a host for Redis to publish to'
			self.log(0, f'ERROR in {__file__}: {result}')

	def _publish_mqtt_tls(
			self,
			host: str,
			port: int,
			topic: str,
			payload: Union[str, bytes],
			*,
			username: Optional[str] = None,
			password: Optional[str] = None,
			ca_cert: Optional[str] = None,         # path to CA or server PEM (for self-signed)
			client_cert: Optional[str] = None,     # for mTLS
			client_key: Optional[str] = None,      # for mTLS
			tls_version: str = "TLSv1_2",          # "TLS", "TLSv1_2", "TLSv1_3"
			insecure: bool = False,                # skip verification (DEV ONLY)
			client_id: Optional[str] = None,
			keepalive: int = 30,
			qos: int = 0,
			retain: bool = False,
			connect_timeout: float = 2.0,
			publish_timeout: float = 2.0,
			use_secure: bool = True
	) -> bool:

			# Build TLS context only if secure
			def _tls_ctx() -> ssl.SSLContext:
					ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

					# Load your CA or server PEM for self-signed
					if ca_cert:
							ctx.load_verify_locations(cafile=ca_cert)

					# Client certs (mTLS)
					if client_cert and client_key:
							ctx.load_cert_chain(certfile=client_cert, keyfile=client_key)

					# TLS versions
					tv = tls_version.upper()
					if tv in ("TLSV1_3", "TLS1_3", "TLS_1_3"):
							ctx.minimum_version = ssl.TLSVersion.TLSv1_3
					else:
							ctx.minimum_version = ssl.TLSVersion.TLSv1_2

					# Insecure mode: accept any cert (DEV/LOCAL only)
					if insecure:
							ctx.check_hostname = False
							ctx.verify_mode = ssl.CERT_NONE

					return ctx

			connect_evt = threading.Event()
			publish_evt = threading.Event()

			# Ensure non-empty client_id
			if not client_id:
					client_id = f"client-{uuid.uuid4().hex[:8]}"

			result_ok = False

			client = mqtt.Client(client_id=client_id, clean_session=True)

			if username:
					client.username_pw_set(username, password)

			if use_secure:
					ctx = _tls_ctx()
					client.tls_set_context(ctx)
					# Keep paho's internal flag consistent with our context
					client.tls_insecure_set(insecure)

			def on_connect(cli, userdata, flags, rc, properties=None):
					if rc == 0:
							self.log(4, f"Connected to {host}:{port}")
					else:
							self.log(4, f"Connecting to {host}:{port} failed rc = {rc}")
					connect_evt.set()

			def on_publish(cli, userdata, mid):
					publish_evt.set()

			def on_log(cli, userdata, level, buf):
					self.log(4, f"Level = {level}, Buf = {buf}")

			client.on_connect = on_connect
			client.on_publish = on_publish
			client.on_log = on_log

			self.log(4, f"Connecting to {host}:{port}, use Secure: {use_secure} - Certs: {ca_cert}, QoS: {qos}")
			try:
					client.connect(host, port, keepalive)
			except Exception as e:
					self.log(4, f"Connecting to {host}:{port} failed: {e}")
					return False

			client.loop_start()

			if not connect_evt.wait(timeout=connect_timeout):
					client.loop_stop()
					self.log(4, f"Connecting to {host}:{port} Timed out")
					return False

			# If broker refused (rc!=0), on_connect already logged it
			# We still attempt publish only if connected OK per event timing,
			# but paho won't publish if not connected anyway.

			try:
					info = client.publish(topic, payload=payload, qos=qos, retain=retain)
			except Exception as e:
					client.loop_stop()
					self.log(4, f"Publish call failed: {e}")
					return False

			# Wait for publish (event for all QoS; QoS 0 may be immediate)
			if not publish_evt.wait(timeout=publish_timeout):
					# Fallback: check helper flag
					try:
							if not info.is_published():
									client.loop_stop()
									self.log(4, "Publish timeout")
									return False
					except Exception:
							client.loop_stop()
							self.log(4, "Publish status unknown (timeout)")
							return False

			try:
					client.disconnect()
					result_ok = True
			finally:
					client.loop_stop()

			self.log(4, "Data Published")
			return result_ok
			
	def _send_to_mqtt(self):
		result = ''
		mqtt_topic = self.get_param('mqttTopic', 'allsky', str, True)
		mqtt_username = self.get_param('mqttUsername', '', str)
		mqtt_password = self.get_param('mqttPassword', '', str)
		mqtt_secure = self.get_param('mqttusesecure', True, bool)
		mqtt_host = self.get_param('mqttHost', '127.0.0.1', str, True)
		mqtt_port = self.get_param('mqttPort', 8883, int)
		mqtt_qos = self.get_param('mqttQos', 2, int)
		mqtt_self = self.get_param('mqttSelfSigned', False, bool)
		mqtt_pem = self.get_param('mqttpem', '', str, True)

		if mqtt_self:
			certs = mqtt_pem
		else:
			certs = "/etc/ssl/certs/ca-certificates.crt"

		try:
			result = self._publish_mqtt_tls(
					host=mqtt_host,
					port=mqtt_port,
					topic=mqtt_topic,
					payload=json.dumps(self._json_data),
					username=mqtt_username,
					password=mqtt_password,
					ca_cert=certs,
					tls_version="TLSv1_2",
					qos=mqtt_qos,
					retain=False,
					use_secure = mqtt_secure,
					client_id=mqtt_username
			)
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			L = eTraceback.tb_lineno
			nextL = eTraceback.tb_next.tb_lineno
			message = f"ERROR: Failed on line {nextL} {e}"
   
		return result

	def _send_to_post(self):
		post_url = self.get_param('postEndpoint', '', str)
		headers = {"Content-Type": "application/json"}

		try:
				response = requests.post(post_url, headers=headers, json=self._json_data, timeout=5)
				response.raise_for_status()  # raise HTTPError for bad responses
				self.log(4, f'Data posted to {post_url}')
		except requests.exceptions.Timeout:
				self.log(4, f'ERROR in {__file__}: Request timed out acessing {post_url}')
		except requests.exceptions.ConnectionError as e:
				self.log(4, f'ERROR in {__file__}: Connection error {e} acessing {post_url}')    
		except requests.exceptions.HTTPError as e:
				self.log(4, f'ERROR in {__file__}: HTTP error {e} acessing {post_url}')    
		except Exception as e:
				self.log(4, f'ERROR in {__file__}: Unexpected error{e} acessing {post_url}')    
           

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
		use_post = self.get_param('postEnabled', False, bool)
  
		self._all_variables = allsky_shared.get_all_allsky_variables(True, '', True, True)
		self._required_variables = self._required_variables.split(',')
		for variable in self._required_variables:
			clean_variable = variable.strip()
			if clean_variable:
				if clean_variable in self._all_variables:
					variable_value = self._all_variables[clean_variable]['value']
					self._json_data[clean_variable] = variable_value
				else:
					self.log(0, f'ERROR in {__file__}: Cannot locate environment variable {variable} specified in the extradata')
			else:
				self.log(0, 'ERROR in {__file__}: Empty environment variable specified in the extradata field. Check commas!')

			self._json_data['utc'] = self._get_utc_timestamp()
   
		if use_redis:
			self._send_to_redis()

		if use_influx:
			self._send_to_influxdb()

		if use_mqtt:
			self._send_to_mqtt()
   
		if use_post:
			self._send_to_post()
		'''
		if params["postEnabled"]:
			url = params['postEndpoint']
			if url == "":
				s.log(0, "ERROR in {__file__}: Please specify an endpoint to publish to")
				return

			r = requests.post(params["postEndpoint"], json=jsonData)
			s.log(4, f"INFO: POST status code {r.status_code}")
		'''
		return result


def publishdata(params, event):
	allsky_publishdata = ALLSKYPUBLISHDATA(params, event)
	result = allsky_publishdata.run()

	return result  
