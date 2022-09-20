#!/bin/bash

if (whiptail --title "AllSky GPIO Module" --yesno "Please note that this module is experimantal. Please ensure that you understand its operation before installing. For this module to appear you must enable the 'Show Experimantal' modules in the module editor options. Do you want to install the discord module?" 12 78); then
    sudo cp allsky_gpio.py /etc/allsky/modules
    sudo chown www-data:www-data /etc/allsky/modules/allsky_gpio.py
    whiptail --msgbox --title "AllSky GPIO Module" "The GPIO module has been installed. Don't forget to enable the 'Experimental modules' in the module editor settings." 8 80
fi