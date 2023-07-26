'''
allsky_influxdb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

To install on a pi run the following as root

sudo apt update
sudo apt upgrade
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
gpg --with-fingerprint --show-keys ./influxdata-archive_compat.key
cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo rm -f /etc/apt/trusted.gpg.d/influxdb.gpg
apt update
apt install influxdb
systemctl unmask influxdb
systemctl enable influxdb
systemctl start influxdb

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

systemctl restart influxdb

Test the login

influx -username <username -password <password>

'''
import allsky_shared as s
import datetime
import json
import os
from influxdb_client import InfluxDBClient

metaData = {
    "name": "Allsky influxdb",
    "description": "Saves values from allsky to influxdb",
    "version": "v1.0.0",
    "events": [
        "day",
        "night"
    ],
    "experimental": "true",    
    "arguments":{
        "host": "localhost",
        "port": "8086",
        "user": "",
        "password": "",
        "database": "",
        "values": ""
    },
    "argumentdetails": {
        "host": {
            "required": "false",
            "description": "Influxdb host",
            "help": ""           
        },
        "port": {
            "required": "false",
            "description": "Influxdb Port",
            "help": "",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 65535,
                "step": 1
            }             
        },
        "user": {
            "required": "false",
            "description": "Username",
            "help": ""           
        },                             
        "password": {
            "required": "false",
            "description": "Password",
            "help": ""           
        },                             
        "database": {
            "required": "false",
            "description": "Database",
            "help": ""           
        },    
        "values": {
            "required": "false",
            "description": "Values",
            "help": "Values to save",
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
                fields[var] = float(s.getEnvironmentVariable(var))

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
    database = params["database"]
    values = params["values"]
    retention_policy = 'autogen'

    jsonData = createJSONData(values)
    
    bucket = f'{database}/{retention_policy}'
    host = f'{host}:{port}'

    try:
        with InfluxDBClient(url=host, token=f'{username}:{password}', org='-') as client:
            with client.write_api() as write_api:
                write_api.write(bucket, record=jsonData)
    except Exception as e:
        s.log(0,"Error: {}".format(e))