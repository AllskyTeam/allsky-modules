'''
allsky_influxdb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

To install InfluxDB v1 on a pi run the following as root

sudo apt update
sudo apt upgrade
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
gpg --with-fingerprint --show-keys ./influxdata-archive_compat.key
cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo rm -f /etc/apt/trusted.gpg.d/influxdb.gpg
sudo apt update
sudo apt install influxdb
sudo systemctl unmask influxdb
sudo systemctl enable influxdb
sudo systemctl start influxdb

To create a database run

influx
CREATE DATABASE <databasename>
CREATE USER <username> WITH PASSWORD '<password>' WITH ALL PRIVILEGES

The in /etc/influxdb/influxdb.conf add the following lines below the [HTTP] entry
auth-enabled = true
pprof-enabled = true
pprof-auth-enabled = true
ping-auth-enabled = true

Then restart infludb

sudo systemctl restart influxdb

Test the login

influx -username <username -password <password>

Changelog
v1.0.1 by Damian Grocholski (Mr-Groch)
- Added support for InfluxDB v2
v1.0.2 by Damian Grocholski (Mr-Groch)
- Added protection for non numeric variables values

'''
import allsky_shared as s
import datetime
import json
import os
from influxdb_client import InfluxDBClient

metaData = {
	"name": "Allsky influxdb",
	"description": "Saves values from allsky to influxdb",
	"version": "v1.0.2",
	"events": [
	    "day",
	    "night"
	],
	"experimental": "true",
	"arguments":{
	    "host": "http://localhost",
	    "port": "8086",
	    "user": "",
	    "password": "",
	    "token": "",
	    "v2bucket": "False",
	    "database": "",
	    "org": "-",
	    "values": ""
	},
	"argumentdetails": {
	    "host": {
	        "required": "true",
	        "description": "InfluxDB Host",
	        "help": "URL of InfluxDB server (with protocol, for example http://localhost)"
	    },
	    "port": {
	        "required": "true",
	        "description": "InfluxDB Port",
	        "help": "InfluxDB server listening port (default 8086)",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 65535,
	            "step": 1
	        }
	    },
	    "user": {
	        "required": "false",
	        "description": "InfluxDB Username",
	        "help": "InfluxDB user login (mostly for InfluxDB v1, InfluxDB v2 uses Access Tokens as default)"
	    },
	    "password": {
	        "required": "false",
	        "description": "InfluxDB Password",
	        "help": "InfluxDB user password (mostly for InfluxDB v1, InfluxDB v2 uses Access Tokens as default)"
	    },
	    "token": {
	        "required": "false",
	        "description": "InfluxDB Access Token",
	        "help": "InfluxDB user access token (if not using username and password)"
	    },
	    "v2bucket": {
	        "required": "true",
	        "description": "InfluxDB v2 Bucket",
	        "help": "Enable if you're using InfluxDB v2",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "database": {
	        "required": "true",
	        "description": "InfluxDB v1 Database / v2 Bucket",
	        "help": "Name of InfluxDB database for v1 or bucket for v2"
	    },
	    "org": {
	        "required": "true",
	        "description": "InfluxDB Organization",
	        "help": "Name of the InfluxDB organization in which the database/bucket is located. Leave default (-) if you're using InfluxDB v1 default installation"
	    },
	    "values": {
	        "required": "true",
	        "description": "AllSky Values",
	        "help": "AllSky Values to save, comma seperated",
	        "type": {
	            "fieldtype": "multivariables"
	        }
	    }
	},
	"enabled": "false"
}


def createJSONData(values):

	vars = values.split(",")
	fields = {}
	for var in os.environ:
	    if var.startswith("AS_") or var.startswith("ALLSKY_"):
	        if var in vars:
	            try:
	                fields[var] = s.asfloat(s.getEnvironmentVariable(var))
	            except:
	                pass

	now = datetime.datetime.utcnow()
	time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
	jsonData = [
	    {
	        "measurement": "AllSky",
	        "time": time,
	        "fields":  fields
	    }
	]

	return jsonData

def influxdb(params, event):
	host = params["host"]
	port = params["port"]
	username = params["user"]
	password = params["password"]
	token = params["token"]
	v2bucket = params["v2bucket"]
	database = params["database"]
	org = params["org"]
	values = params["values"]
	retention_policy = 'autogen'

	jsonData = createJSONData(values)

	bucket = database if v2bucket else f'{database}/{retention_policy}'
	host = f'{host}:{port}'
	credentials = token if token != "" else f'{username}:{password}'

	try:
	    with InfluxDBClient(url=host, token=credentials, org=org) as client:
	        with client.write_api() as write_api:
	            write_api.write(bucket, record=jsonData)
	except Exception as e:
	    s.log(0,"Error: {}".format(e))
