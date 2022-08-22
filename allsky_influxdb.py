'''
allsky_influxdb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

To install on a pi run the following as root

sudo apt update
sudo apt upgrade
curl https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /usr/share/keyrings/influxdb-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/influxdb-archive-keyring.gpg] https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
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
from influxdb import InfluxDBClient

metaData = {
    "name": "Allsky influxdb",
    "description": "Saves values from allsky to influxdb",
    "events": [
        "day",
        "night",
        "endofnight",
        "daynight",
        "nightday"
    ],
    "experimental": "true",    
    "arguments":{
        "host": "localhost",
        "port": "8086",
        "user": "",
        "password": "",
        "database": "",
        "tags": ""
    },
    "argumentdetails": {
        "host": {
            "required": "true",
            "description": "Influxdb host",
            "help": ""           
        },
        "port": {
            "required": "true",
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
            "required": "true",
            "description": "Username",
            "help": ""           
        },                             
        "password": {
            "required": "true",
            "description": "Password",
            "help": ""           
        },                             
        "database": {
            "required": "true",
            "description": "Database",
            "help": ""           
        },
        "tags": {
            "required": "true",
            "description": "Tags",
            "help": "Format tag:value,tag:value"
        }        
    },
    "enabled": "false"            
}

def createJSONData():
    now = datetime.datetime.utcnow()
    time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    jsonData = [
        {
            "measurement": "AllSky",
            "tags": {
                "location": "Ely",
            },
            "time": time,
            "fields": {
                "test": 1.2
            }
        }
    ]

    return jsonData

def influxdb(params): 
    host = params["host"]
    port = params["port"]
    user = params["user"]
    password = params["password"]
    database = params["database"]

    influxClient = InfluxDBClient(host, port, user, password, database)

    jsonData = createJSONData()
    
    #try:
    influxClient.write_points(jsonData)
    #except Exception as e:
    #    pass