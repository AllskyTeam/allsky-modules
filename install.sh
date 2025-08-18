#!/bin/bash

[[ -z "${ALLSKY_HOME}" ]] && export ALLSKY_HOME="$( realpath "$( dirname "${BASH_ARGV0}" )/.." )"

#shellcheck source=/home/pi/allsky/variables.sh
source "${ALLSKY_HOME}/variables.sh"            || exit "${ALLSKY_ERROR_STOP}"
#shellcheck source=/home/pi/allsky/scripts/functions.sh
source "${ALLSKY_SCRIPTS}/functions.sh"         || exit "${ALLSKY_ERROR_STOP}"

trap "exit 0" SIGTERM SIGINT

clear
echo "Validating and launching installer."
echo

#
# Check to ensure we have python 3.9 or greater
#
#ver=$(python -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
#if [ "$ver" -lt "39" ]; then
#    echo -e "\n\nThe Allsky extra modules require python 3.9 or greater\n\n"
#    exit 1
#fi

#
# If there is a Python Virtual Environment then activate it
#
if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
    # shellcheck disable=SC1090
    source "${ALLSKY_HOME}/venv/bin/activate"
    echo -e "INFO - Using Python venv\n\n"
fi

echo -n "Please Wait ...."

#
# Install the installer dependencies
#
pythonPackages=("packaging" "gitpython" "whiptail-dialogs" "smbus")
aptPackages=("pip")

true > moduleinstalldebug.log

for str in "${aptPackages[@]}"; do
    echo -n "..."
    sudo apt install -y "${str}" >> moduleinstalldebug.log 2>&1
    RESULT=$?
    if [[ ${RESULT} != 0 ]]; then
        echo -e "\n\nERROR: ${str} Failed to install please check the moduleinstalldebug.log file\n\n"
        exit 1
    fi
done

for str in "${pythonPackages[@]}"; do
    echo -n "..."
    pip3 install "${str}" >> moduleinstalldebug.log 2>&1
    RESULT=$?
    if [[ ${RESULT} != 0 ]]; then
        echo -e "\n\nERROR: ${str} Failed to install please check the moduleinstalldebug.log file\n\n"
        exit 1
    fi
done 


python3 module-installer.py

#
# Deactivate the Python Virtual Environment if we used it
#
if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
    deactivate
fi

