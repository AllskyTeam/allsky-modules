#!/bin/bash

if (whiptail --title "AllSky Script Module" --yesno "Please note that this module is experimantal. Please ensure that you understand its operation before installing. For this module to appear you must enable the 'Show Experimantal' modules in the module editor options. Do you want to install the Script module?" 12 78); then
    sudo cp allsky_script.py /etc/allsky/modules
    sudo chown www-data:www-data /etc/allsky/modules/allsky_script.py
    whiptail --msgbox --title "AllSky Script Module" "The Script module has been installed. Don't forget to enable the 'Experimental modules' in the module editor settings." 8 80
fi