#!/bin/bash

[[ -z "${ALLSKY_HOME}" ]] && export ALLSKY_HOME="$( realpath "$( dirname "${BASH_ARGV0}" )/.." )"

#shellcheck source-path=.
source "${ALLSKY_HOME}/variables.sh"            || exit "${ALLSKY_ERROR_STOP}"
#shellcheck source-path=scripts
source "${ALLSKY_SCRIPTS}/functions.sh"         || exit "${ALLSKY_ERROR_STOP}"

trap "exit 0" SIGTERM SIGINT

echo "Validating and launching installer"
echo

sudo apt install -y pip

#
# If a using bookworm or later then use a venv
#
if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
    source "${ALLSKY_HOME}/venv/bin/activate"
    echo "INFO - Using Python venv"
fi

pip3 install packaging
pip3 install whiptail-dialogs

python3 module-installer.py

#
# Deactivate the Python Virtual Environment if we used it
#
if  [[ ${PI_OS} != "buster" ]] && [[ ${PI_OS} != "bullseye" ]] ; then
    deactivate
fi