#!/bin/bash

if (whiptail --title "AllSky Rain Module" --yesno "Please note that this module is experimantal. Please ensure that you understand its operation before installing. For this module to appear you must enable the 'Show Experimantal' modules in the module editor options. Do you want to install the Rain module?" 12 78); then
    sudo cp allsky_rain.py /etc/allsky/modules
    sudo chown www-data:www-data /etc/allsky/modules/allsky_rain.py
    whiptail --msgbox --title "AllSky Rain Module" "The Rain module has been installed. Don't forget to enable the 'Experimental modules' in the module editor settings." 8 80
fi