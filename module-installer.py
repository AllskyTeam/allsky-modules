#!/usr/bin/python3

from whiptail import Whiptail
import os
import sys
import re
import json
import subprocess
from platform import python_version
from packaging import version

def readModuleMetaData(modulePath):

    f = open(modulePath,"r")
    rawLines = f.readlines()

    gotStart = False
    rawMeta = ""
    for line in rawLines:

        if not gotStart:
            clean = line.strip()
            if clean.startswith("metaData = {"):
                rawMeta = "{"
                gotStart = True
        else:
            if not line.startswith("}"):
                rawMeta = rawMeta + line
            else:
                rawMeta = rawMeta + line
                break

    try:
        moduleData = json.loads(rawMeta)
    except:
        moduleData = None

    return moduleData


basePath = os.path.dirname(os.path.realpath(__file__))
destPath = "/etc/allsky/modules"

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

os.system("clear")

try:
    user = os.getlogin()
except:
    if "LOGNAME" in os.environ:
        user = os.environ["LOGNAME"]
    else:
        print("Cannot determine user - Aborting")
    
for module in checkList:
    failed = ""
    title = f"Installing {module}"
    print(title)
    print("="*len(title))
    modulePath = os.path.join(basePath, module)
    scriptPath = os.path.join(basePath, module, module + ".py")


    moduleData = readModuleMetaData(scriptPath)
    okToInstall = True
    if moduleData is not None:
        if "pythonversion" in moduleData:
            if version.parse(python_version()) < version.parse(moduleData["pythonversion"]):
                failed = "This module requires Python version {0} you have {1} installed".format(moduleData["pythonversion"], python_version())
                okToInstall = False

    if okToInstall:
        
        
        packagesPath = os.path.join(modulePath, "packages.txt")
        if os.path.exists(packagesPath):
            with open(packagesPath, "r") as fp:
                packages = fp.read()
                packages = packages.splitlines()
                for package in packages:
                    cmd = "sudo apt-get install -y {}".format(package)
                    try:
                        result = subprocess.check_output(cmd, shell=True).decode("utf-8")
                    except Exception as err:
                        print(err)        
        
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