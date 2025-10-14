'''
allsky_influxdb.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

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
import allsky_shared as allsky_shared

metaData = {
	"name": "Save Data to influxdb",
	"description": "Save data from Allsky to influxdb",
	"version": "v1.0.2",
	"events": [
	    "day",
	    "night"
	],
	"experimental": "true",
	"group": "Data Export",
	"deprecation": {
		"fromversion": "v2024.12.06_01",
		"removein": "v2024.12.06_01",
		"notes": "This module has been deprecated. Please use the 'Publish Data to Redis/MQTT/REST/influxDB' module instead.",
		"replacedby": "allsky_publishdata",
		"deprecated": "true"
	},  
	"arguments":{
	},
	"argumentdetails": {
	},
	"enabled": "false"
}

def influxdb(params, event):
	return "Deprectated - Please use the 'Publish Data to Redis/MQTT/REST/influxDB' module instead."
