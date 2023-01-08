#!/bin/bash

echo "Validating and launching installer"
echo

sudo apt install -y pip
pip3 install packaging
pip3 install whiptail-dialogs

python3 module-installer.py