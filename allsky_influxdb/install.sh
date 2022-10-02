#!/bin/bash

if (whiptail --title "AllSky InfluxDB Module" --yesno "Please note that this module is experimantal. Please ensure that you understand its operation before installing. For this module to appear you must enable the 'Show Experimantal' modules in the module editor options. Do you want to install the InfluxDB module?" 12 78); then
    reset
    echo "Installing dependencies. This may take a while"
    pip3 install --no-warn-script-location -r requirements.txt > dependencies.log 2>&1
	if [ $? -ne 0 ]; then
        whiptail --textbox --title "ERROR Installing AllSky InfluxDB Module" dependencies.log 10 100 --scrolltext
    else
        sudo cp allsky_influxdb.py /etc/allsky/modules
        sudo chown www-data:www-data /etc/allsky/modules/allsky_influxdb.py
        whiptail --msgbox --title "AllSky InfluxDB Module" "The InfluxDB module has been installed. Don't forget to enable the 'Experimental modules' in the module editor settings." 8 80
    fi
fi