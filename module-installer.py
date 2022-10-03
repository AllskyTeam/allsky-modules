#!/usr/bin/python

from whiptail import Whiptail
import os
import sys

if os.geteuid() == 0:
    print("\nDO NOT run this as root. Run the installer as the same user as AllSky was installed\n")
    sys.exit(0)

moduleDirs = [] 
dirs = os.listdir()
for dir in dirs:
    if dir.startswith("allsky_"):
        moduleDirs.append(dir)

w = Whiptail(title="Select Modules", backtitle="AllSky Module Installer", height=20, width = 40)

checkList = w.checklist("Select the Modules To Install", moduleDirs)[0]

basePath = os.path.dirname(os.path.realpath(__file__))
destPath = "/etc/allsky/modules"
os.system("clear")
user = os.getlogin()
for module in checkList:
    failed = ""
    title = f"Installing {module}"
    print(title)
    print("="*len(title))
    modulePath = os.path.join(basePath, module)
    scriptPath = os.path.join(basePath, module, module + ".py")
    requirementsPath = os.path.join(modulePath, "requirements.txt")
    logPath = os.path.join(modulePath, "dependencies.log")
    if os.path.exists(requirementsPath):
        print("INFO: Installing dependencies")
        result = os.system(f"pip3 install --no-warn-script-location -r {requirementsPath} > {logPath} 2>&1")
        if result != 0:
            failed = f"Check {logPath} for any errors"

    print(f"INFO: Installing {module} module")
    cmd = f"cp {scriptPath} {destPath}"
    result = os.system(cmd)
    if result == 0:
        destFile = os.path.join(destPath, module + ".py")
        cmd = f"sudo chown {user}:www-data {destFile}"
        result = os.system(cmd)
        if result == 0:
            print(f"SUCCESS: Module {module} Installed")
        else:
            failed = f"Could not set permissions on {destFile}"
    else:
        failed = f"Could not copy module from {scriptPath} to {destPath}"

    if failed != "":
        print(f"ERROR: Installation of {module} Failed, {failed}")

    print("\n\n")