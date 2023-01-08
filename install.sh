#!/bin/bash

echo "Validating and launching installer"
echo

sudo apt install pip
pip3 install whiptail-dialogs

python3 module-installer.py