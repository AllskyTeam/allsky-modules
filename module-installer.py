from whiptail import Whiptail
import os
import sys
import json
import subprocess
import tempfile
import re
import smbus
from platform import python_version
from packaging import version
from urllib.request import urlopen as url
from git import Repo
from gpiozero import pi_info
import importlib.util

class ALLSKYMODULEINSTALLER:
    _basePath = None
    _destPath = None
    _destPathDeps = None
    _destPathInfo = None
    _user = None
    _moduleDirs = []
    _modules = []
    _checkList = []
    
    def __init__(self):
        self._basePath = os.path.dirname(os.path.realpath(__file__))
        self._destPath = '/opt/allsky/modules'
        self._destPathDeps = os.path.join(self._destPath,'dependencies')
        self._destPathInfo = os.path.join(self._destPath,'info')
    
    def _checkInstalled(self, path):
        if os.path.exists(path):
            return True
        else:
            return False 
        
    def _preChecks(self):
        result = True
        
        if not self._checkInstalled(self._destPath):
            print('AllSky does not seem to be installed. The /opt/allsky directory does not exist. Please install AllSky before installing the modules')
            result = False
            
        if os.geteuid() == 0:
            print('DO NOT run this as root. Run the installer as the same user as AllSky was installed')
            result = False
                
        try:
            self._user = os.getlogin()
        except:
            if 'LOGNAME' in os.environ:
                self._user = os.environ['LOGNAME']
            else:
                print('Cannot determine user - Aborting')
                result = False
                        
        return result  
    
    def _readModules(self):
        self._moduleDirs = [] 
        dirs = os.listdir()
        for dir in dirs:
            if dir.startswith('allsky_'):
                modulePath, scriptPath, moduleData, installedPath = self._getModuleData(dir)
                installed = 'OFF'
                if os.path.exists(installedPath):
                    installed = 'ON'
                self._moduleDirs.append((dir,"",installed))
                self._modules.append(dir)

    def _displayInstallDialog(self):
        w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width = 40)
        self._checkList = w.checklist('Select the Modules To Install', self._moduleDirs)[0]
        
    def _getModuleData(self, module):
        modulePath = os.path.join(self._basePath, module)
        scriptPath = os.path.join(self._basePath, module, module + '.py')
        moduleData = self._readModuleMetaData(scriptPath)
        installedPath = os.path.join(self._destPath,module + '.py')
        
        return modulePath, scriptPath, moduleData, installedPath

    def _readModuleMetaData(self, modulePath):

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
            moduleData = {}

        moduleData = self._fixModuleMetaData(moduleData)
        
        return moduleData
    
    def _checkPythonVersion(self, moduleData):
        result = True
        if moduleData is not None:
            if 'pythonversion' in moduleData:
                if version.parse(python_version()) < version.parse(moduleData['pythonversion']):
                    print(f'This module requires Python version {moduleData["pythonversion"]} you have {python_version()} installed')
                    result = False
        return result

    def _installPackages(self, module, modulePath):
        result = True
        packagesPath = os.path.join(modulePath, 'packages.txt')
        if os.path.exists(packagesPath):
            print('INFO: Installing package dependencies')
            with open(packagesPath, 'r') as fp:
                packages = fp.read()
                packages = packages.splitlines()
                for package in packages:
                    cmd = f'sudo apt-get install -y {package}'
                    try:
                        aptResult = subprocess.check_output(cmd, shell=True).decode('utf-8')
                    except Exception as e:
                        eType, eObject, eTraceback = sys.exc_info()
                        print(f'ERROR: _installPackages failed on line {eTraceback.tb_lineno} - {e}')                        
                        result = False
        
            if result:
                packageDestPath = os.path.join(self._destPathDeps,module)
                if not os.path.isdir(packageDestPath):
                    os.mkdir(packageDestPath)
                            
                cmd = f'cp {packagesPath} {packageDestPath}'
                depResult = os.system(cmd)
                if depResult != 0:
                    print(f'Failed to copy requirements from {packagesPath} to {packageDestPath}')
                    result = False
                    
        return result                      

    def _installPythonLibraries(self, module, modulePath):
        result = True
        requirementsPath = os.path.join(modulePath, 'requirements.txt')
        logPath = os.path.join(modulePath, 'dependencies.log')
        if os.path.exists(requirementsPath):
            print('INFO: Installing Python dependencies')
            pipResult = 0
            try:
                pipResult = os.system(f'pip3 install --no-warn-script-location -r {requirementsPath} > {logPath} 2>&1')
            except Exception as e:
                eType, eObject, eTraceback = sys.exc_info()
                print(f'ERROR: _installPythonLibraries failed on line {eTraceback.tb_lineno} - {e}')                        
                result = False
                         
            if pipResult != 0:
                failed = f'Check {logPath} for any errors'
                result = False

            if result:
                packageDestPath = os.path.join(self._destPathDeps,module)
                if not os.path.isdir(packageDestPath):
                    os.mkdir(packageDestPath)
                        
                cmd = f'cp {requirementsPath} {packageDestPath}'
                depResult = os.system(cmd)
                if depResult != 0:
                    print(f'Failed to copy requirements from {requirementsPath} to {packageDestPath}')
                    result = False

        return result

    def _installDependencies(self, module, modulePath):
        result = False
        
        if self._installPackages(module, modulePath):
            if self._installPythonLibraries(module, modulePath):
                result = True
  
        return result

    def _installModule(self, module, scriptPath, installedPath, modulePath):
        result = True
        print(f'INFO: Installing {module} module')
        cmd = f'cp {scriptPath} {self._destPath}'
        cpResult = os.system(cmd)
        if cpResult == 0:
            cmd = f'sudo chown {self._user}:www-data {installedPath}'
            chownResult = os.system(cmd)
            if chownResult != 0:
                failed = f'Could not set permissions on {installedPath}\n\n'
                result = False
        else:
            failed = f'Could not copy module from {self._scriptPath} to {self._destPath}\n\n'
            result = False
        
        if result:
            infoPath = os.path.join(modulePath, 'readme.txt')
            if os.path.exists(infoPath):
                packageInfoPath = os.path.join(self._destPathInfo,module)
                if not os.path.isdir(packageInfoPath):
                    os.makedirs(packageInfoPath, mode = 0o777, exist_ok = True)
                            
                cmd = f'cp {infoPath} {packageInfoPath}'
                os.system(cmd)
            
        return result

    def _doInstall(self):
        os.system('clear')
        
        if not os.path.isdir(self._destPathDeps):
            os.mkdir(self._destPathDeps)

        for module in self._checkList:
            title = f'Installing {module}'
            print(title)
            print('='*len(title))

            modulePath, scriptPath, moduleData, installedPath = self._getModuleData(module)
            if self._checkPythonVersion(moduleData):
                if self._installDependencies(module, modulePath):
                    if self._installModule(module, scriptPath, installedPath, modulePath):
                        print(f'SUCCESS: Module "{module}" installed\n\n')
                    else:
                        print(f'ERROR: Module "{module}" failed to installed\n\n')
        self._check_gpio_status()
        
    def _fixModuleMetaData(self, moduleData):
        
        if 'experimental' not in moduleData:
            moduleData['experimental'] = False
                    
        if 'name' not in moduleData:
            moduleData['name'] = 'Unknown'
            
        if 'version' not in moduleData:
            moduleData['version'] = 'Unknown'

        if 'description' not in moduleData:
            moduleData['description'] = ''

        if 'longdescription' not in moduleData:
            moduleData['longdescription'] = ''

        if 'changelog' not in moduleData:
            moduleData['changelog'] = {}

        return moduleData
                                
    def _displayModuleInfoDialog(self, moduleData, installedModuleData, modulePath, module):
        data = ''
        newVersion = ''
        if installedModuleData:
            if version.parse(installedModuleData['version']) < version.parse(moduleData['version']):
                newVersion = 'New Version Available'
        
        data = f"{moduleData['name']}\n"
        data += f"{'-'*76}\n\n"
        data += f"Description: {moduleData['description']}\n\n"
        data += f"Version: {moduleData['version']} {newVersion}\n"
        if installedModuleData:
            data += "Installed: Yes\n"
        else:
            data += "Installed: No\n"
            
        if moduleData['experimental'] :
            data += "Experimental: Yes (This module may not be stable)\n"
        else:
            data += "Experimental: No\n"

        data += '\n\nReadme\n'
        data += f"{'-'*40}\n\n"  
        readmeFile = os.path.join(modulePath, 'readme.txt')
        if os.path.exists(readmeFile):
            f = open(readmeFile, 'r')
            readmeText = f.read()
            f.close()          
            data += readmeText
        else:
            data += 'No readme.txt file available'

        data += '\n\nChangelog\n'
        data += f"{'-'*40}\n\n"
        if moduleData['changelog']:
            for moduleVersion in moduleData['changelog']:
                data += f"Version: {moduleVersion}\n"
                changeList = moduleData['changelog'][moduleVersion]
                for change in changeList:
                    data += f"  Author: {change['author']}\n"
                    if type(change['changes']) == list:
                        for changeItem in change['changes']:
                            data += f"    - {changeItem}\n"                            
                    else:
                        data += f"    - {change['changes']}\n"
                data += "\n"
        else:
            data += 'No changelog available'
                        
        tempFileHandle = tempfile.NamedTemporaryFile(mode='w+t')
        tempFileName = tempFileHandle.name
        tempFileHandle.close()
        try: 
            f = open(tempFileName, 'w')
            f.write(data)
            f.close()
            w = Whiptail(title=f'{module} Information', backtitle='AllSky Module Manager', height=30, width = 80)
            msgbox = w.textbox(tempFileHandle.name)
        finally: 
            os.remove(tempFileName)                
        
    def _displayInfoListDialog(self):
        done = False
        
        while not done:
            w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width = 40)
            module, returnCode = w.radiolist('Select Module', self._modules)
        
            if returnCode != 1:
                if module:
                    module = module[0]
                    modulePath, scriptPath, moduleData, installedPath = self._getModuleData(module)
                    installed = False
                    if os.path.exists(installedPath):
                        installed = True
                    moduleData = self._readModuleMetaData(scriptPath)
                    
                    installedModuleData = {}
                    scriptPath = os.path.join(self._destPath, module + '.py')
                    if os.path.exists(scriptPath):
                        installedModuleData = self._readModuleMetaData(scriptPath)
                            
                    self._displayModuleInfoDialog(moduleData, installedModuleData, modulePath, module)
            else:
                done = True
        
    def _displayModulesInfo(self):
        self._readModules()
        self._displayInfoListDialog()
        pass

    def _getI2Cevices(self, bus=None):

        devices = []
        
        if bus == None:
            try:
                bus = smbus.SMBus(1)
                for _address in range(128):
                    try:
                        bus.read_byte(_address)
                        devices.append(' %02x' % _address)
                    except Exception as e:
                        pass
            except Exception:
                pass
                            
        return devices
    
    def _checkInternet(self):
        result = 'Yes'
        try:
            url('https://www.google.com/', timeout=3)
        except ConnectionError as ex: 
            result = 'No'
        
        return result

    def _check_gpio_status(self):
        pi_version = self._getPiVersion()
        if pi_version[0] == '5':
            print('INFO: Found the rpi.gpio module so uninstalling it\n\n')
            subprocess.run(['pip3', 'uninstall', '-y', 'rpi.gpio'], check=False)
        else:
            print(f'Pi version is "{pi_version}" so not modifying gpio libraries')

    def _check_pip_package_installed(self, package_name):
        return importlib.util.find_spec(package_name) is not None
    
    def _getPiVersion(self):
        info = pi_info()
        piVersion = info.model

        return piVersion
                    
    def _displaySystemChecks(self):
        configFile = '/boot/firmware/config.txt'
        if not os.path.exists(configFile):
            configFile = '/boot/config.txt'

        f = open(configFile, 'r')
        bootFileText = f.read()
        f.close()

        regex = r"""^(device_tree_param|dtparam)=([^,]*,)*i2c(_arm)?(=(on|true|yes|1))?(,.*)?$"""
        i2cEnabled = bool(re.search(regex, bootFileText, re.MULTILINE | re.VERBOSE))
        
        i2cDevices = ''
        if i2cEnabled:
            i2cDevices = self._getI2Cevices()
        onlineStatus = self._checkInternet()
        piVersion = self._getPiVersion()

        try:
            allSkyInstalled = os.environ['ALLSKY_HOME']
        except:
            allSkyInstalled = 'Not Installed'
                                            
        data = f"System Checks\n"
        data += f"{'-'*76}\n\n"
        
        data += f"Pi Version: {piVersion}\n\n"
        data += f"Allsky Location: {allSkyInstalled}\n\n"        
        data += f"i2c Enabled: {i2cEnabled}"
        if i2cEnabled:
            data += f"\ni2c Devices: {','.join(i2cDevices)}"

        data += f"\n\nOnline: {onlineStatus}"

                    
        tempFileHandle = tempfile.NamedTemporaryFile(mode='w+t')
        tempFileName = tempFileHandle.name
        tempFileHandle.close()
        try: 
            f = open(tempFileName, 'w')
            f.write(data)
            f.close()
            w = Whiptail(title='Allsky Module System Checks', backtitle='AllSky Module Manager', height=30, width = 80)
            msgbox = w.textbox(tempFileHandle.name)
        finally: 
            os.remove(tempFileName)
        pass
    
    def _getGitBranch(self):
        local_branch = Repo().head.ref.name
        
        return local_branch
    
    def run(self):
        done = False
        
        gitBranch = self._getGitBranch()
        
        if gitBranch == 'dev':
            w = Whiptail(title='warning', backtitle='AllSky Module Manager', height=20, width=80)
            message = "You are using the dev branch of the Allsk extra modules.\nThis branch contains work that may not be complete nor fully tested\n\nUsage of this branch is entirely at your own risk"
            msgbox = w.msgbox(message)
                
        while not done:
            w = Whiptail(title='Main Menu', backtitle='AllSky Module Manager', height=20, width = 40)
            menuOption, returnCode = w.menu('', ['Install/Remove Modules', 'Module Information', 'System Checks', 'Exit'])

            if returnCode == 0:
                if menuOption == 'Exit':
                    done = True
                if menuOption == 'Module Information':
                    self._displayModulesInfo()
                if menuOption == 'System Checks':
                    self._displaySystemChecks()                    
                if menuOption == 'Install/Remove Modules':
                    if self._preChecks():
                        self._readModules()
                        self._displayInstallDialog()
                        self._doInstall()            
                    else:
                        sys.exit(0)
            else :
                done = True

if __name__ == '__main__':
    moduleInstaller = ALLSKYMODULEINSTALLER()
    moduleInstaller.run()