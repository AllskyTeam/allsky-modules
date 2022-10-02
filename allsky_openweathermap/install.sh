#!/bin/bash

if (whiptail --title "AllSky Open Weather Map Module" --yesno "You will need to register for a free API key. Please see the README for more information Do you want to install the Open Weather Map module?" 12 78); then
    reset
    echo "Installing dependencies. This may take a while"
    pip3 install --no-warn-script-location -r requirements.txt > dependencies.log 2>&1
	if [ $? -ne 0 ]; then
        whiptail --textbox --title "ERROR Installing AOpen Weather Map Module" dependencies.log 10 100 --scrolltext
    else
        sudo cp allsky_openweathermap.py /etc/allsky/modules
        sudo chown www-data:www-data /etc/allsky/modules/allsky_openweathermap.py
        whiptail --msgbox --title "AllSky Open Weather Map Module" "The Open Weather Map module has been installed. Don't forget to register for a free API key." 8 80
    fi
fi