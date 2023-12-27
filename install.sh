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
echo -n "Please Wait ...."

error=""

error=$({ sudo apt install -y pip >&2; } 2>&1 >/dev/null)
RESULT=$?

if [[ ${RESULT} == 0 ]]; then
    echo -n "....."
    #
    # If a using bookworm or later then use a venv
    #
    if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
        # shellcheck disable=SC1090
        source "${ALLSKY_HOME}/venv/bin/activate"
        echo "INFO - Using Python venv"
    fi
    error=$({ pip3 install packaging >&2; } 2>&1 >/dev/null)
    RESULT=$?
    if [[ ${RESULT} == 0 ]]; then
        echo -n "....."
        error=$({ pip3 install whiptail-dialogs >&2; } 2>&1 >/dev/null)
        RESULT=$? 
        if [[ ${RESULT} == 0 ]]; then
            echo -n "....."
            python3 module-installer.py
            #
            # Deactivate the Python Virtual Environment if we used it
            #
            if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
                deactivate
            fi
        fi

    fi
fi