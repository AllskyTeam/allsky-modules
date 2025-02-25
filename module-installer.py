from whiptail import Whiptail
import os
import sys
import json
import subprocess
import tempfile
import re
import smbus
import shutil
from pathlib import Path
from platform import python_version
from packaging import version
from urllib.request import urlopen as url
from git import Repo
from gpiozero import Device
import importlib.util


class ALLSKYMODULEINSTALLER:
    base_path = None
    dest_path = None
    dest_path_deps = None
    dest_path_info = None
    user = None
    module_dirs = []
    modules = []
    check_list = []

    def __init__(self):
        self.base_path = os.path.dirname(os.path.realpath(__file__))
        self.dest_path = '/opt/allsky/modules'
        self.dest_path_deps = os.path.join(self.dest_path, 'dependencies')
        self.dest_path_info = os.path.join(self.dest_path, 'info')

    def _check_installed(self, path):
        if os.path.exists(path):
            return True
        else:
            return False 

    def _pre_checks(self):
        result = True
        
        if not self._check_installed(self.dest_path):
            print('AllSky does not seem to be installed. The /opt/allsky directory does not exist. Please install AllSky before installing the modules')
            result = False
            
        if os.geteuid() == 0:
            print('DO NOT run this as root. Run the installer as the same user as AllSky was installed')
            result = False
                
        try:
            self.user = os.getlogin()
        except:
            if 'LOGNAME' in os.environ:
                self.user = os.environ['LOGNAME']
            else:
                print('Cannot determine user - Aborting')
                result = False
                        
        return result  

    def _read_modules(self):
        self.module_dirs = [] 
        dirs = os.listdir()
        for dir in dirs:
            if dir.startswith('allsky_') and not os.path.isfile(dir):
                module_path, script_path, module_data, installed_path = self._get_module_data(dir)
                installed = 'OFF'
                if os.path.exists(installed_path):
                    installed = 'ON'
                self.module_dirs.append((dir, '', installed))
                self.modules.append(dir)

    def _display_install_dialog(self):
        w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width = 40)
        self.check_list = w.checklist('Select the Modules To Install', self.module_dirs)[0]

    def _get_module_data(self, module):
        module_path = os.path.join(self.base_path, module)
        script_path = os.path.join(self.base_path, module, module + '.py')
        module_data = self._read_module_meta_data(script_path)
        installed_path = os.path.join(self.dest_path, module + '.py')

        return module_path, script_path, module_data, installed_path

    def _read_module_meta_data(self, module_path):

        f = open(module_path, "r")
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
            module_data = json.loads(rawMeta)
        except:
            module_data = {}

        module_data = self._fix_module_meta_data(module_data)
  
        return module_data

    def _check_python_version(self, module_data):
        result = True
        if module_data is not None:
            if 'pythonversion' in module_data:
                if version.parse(python_version()) < version.parse(module_data['pythonversion']):
                    print(f'This module requires Python version {module_data["pythonversion"]} you have {python_version()} installed')
                    result = False
        return result

    def _install_packages(self, module, module_path):
        result = True
        packagesPath = os.path.join(module_path, 'packages.txt')
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
                        print(f'ERROR: _install_packages failed on line {eTraceback.tb_lineno} - {e}')                        
                        result = False
        
            if result:
                packageDestPath = os.path.join(self.dest_path_deps,module)
                if not os.path.isdir(packageDestPath):
                    os.mkdir(packageDestPath)
                            
                cmd = f'cp {packagesPath} {packageDestPath}'
                depResult = os.system(cmd)
                if depResult != 0:
                    print(f'Failed to copy requirements from {packagesPath} to {packageDestPath}')
                    result = False
                    
        return result                      

    def _install_python_libraries(self, module, module_path):
        result = True
        requirementsPath = os.path.join(module_path, 'requirements.txt')
        logPath = os.path.join(module_path, 'dependencies.log')
        if os.path.exists(requirementsPath):
            print('INFO: Installing Python dependencies')
            pipResult = 0
            try:
                pipResult = os.system(f'pip3 install --no-warn-script-location -r {requirementsPath} > {logPath} 2>&1')
            except Exception as e:
                eType, eObject, eTraceback = sys.exc_info()
                print(f'ERROR: _install_python_libraries failed on line {eTraceback.tb_lineno} - {e}')                        
                result = False
                         
            if pipResult != 0:
                failed = f'Check {logPath} for any errors'
                result = False

            if result:
                packageDestPath = os.path.join(self.dest_path_deps,module)
                if not os.path.isdir(packageDestPath):
                    os.mkdir(packageDestPath)
                        
                cmd = f'cp {requirementsPath} {packageDestPath}'
                depResult = os.system(cmd)
                if depResult != 0:
                    print(f'Failed to copy requirements from {requirementsPath} to {packageDestPath}')
                    result = False

        return result

    def _install_dependencies(self, module, module_path):
        result = False

        if self._install_packages(module, module_path):
            if self._install_python_libraries(module, module_path):
                result = True

        return result

    def _install_module(self, module, script_path, installed_path, module_path):
        result = True
        print(f'INFO: Installing {module} module')
        cmd = f'cp {script_path} {self.dest_path}'
        copy_result = os.system(cmd)
        if copy_result == 0:
            cmd = f'sudo chown {self.user}:www-data {installed_path}'
            chown_result = os.system(cmd)
            if chown_result != 0:
                failed = f'Could not set permissions on {installed_path}\n\n'
                result = False
        else:
            failed = f'Could not copy module from {script_path} to {self.dest_path}\n\n'
            result = False

        if result:
            info_path = os.path.join(module_path, 'readme.txt')
            if os.path.exists(info_path):
                package_info_path = os.path.join(self.dest_path_info,module)
                if not os.path.isdir(package_info_path):
                    os.makedirs(package_info_path, mode=0o777, exist_ok=True)

                cmd = f'cp {info_path} {package_info_path}'
                os.system(cmd)

            info_path = os.path.join(module_path, 'README.md')
            if os.path.exists(info_path):
                package_info_path = os.path.join(self.dest_path_info,module)
                if not os.path.isdir(package_info_path):
                    os.makedirs(package_info_path, mode=0o777, exist_ok=True)

                cmd = f'cp {info_path} {package_info_path}'
                os.system(cmd)

            directories = [entry for entry in os.listdir(module_path) if os.path.isdir(os.path.join(module_path, entry))]
            for directory in directories:
                source_directory = os.path.join(module_path, directory)
                command = f'cp -ar {source_directory} {self.dest_path}'
                os.system(command)

        return result

    def _install_module_data(self, module):
        result = True
        data_dir = os.path.join(self.base_path, module, module.replace('allsky_', ''))
        if Path(data_dir).is_dir():
            try:
                shutil.copytree(data_dir, self.dest_path)
            except FileExistsError:
                print('Destination directory already exists.')
                result = False
            except Exception as exception:
                print(f'Error occurred: {exception}')
                result = False

        return result

    def _do_install(self):
        os.system('clear')

        if not os.path.isdir(self.dest_path_deps):
            os.mkdir(self.dest_path_deps)

        for module in self.check_list:
            title = f'Installing {module}'
            print(title)
            print('='*len(title))

            module_path, script_path, module_data, installed_path = self._get_module_data(module)
            if self._check_python_version(module_data):
                if self._install_dependencies(module, module_path):
                    if self._install_module(module, script_path, installed_path, module_path):
                        if self._install_module_data(module):
                            print(f'SUCCESS: Module "{module}" installed\n\n')
                        else:
                            print(f'ERROR: Module "{module}" failed to installed\n\n')
                    else:
                        print(f'ERROR: Module "{module}" failed to installed\n\n')
        self._check_gpio_status()

    def _fix_module_meta_data(self, module_data):
        
        if 'experimental' not in module_data:
            module_data['experimental'] = False
                    
        if 'name' not in module_data:
            module_data['name'] = 'Unknown'
            
        if 'version' not in module_data:
            module_data['version'] = 'Unknown'

        if 'description' not in module_data:
            module_data['description'] = ''

        if 'longdescription' not in module_data:
            module_data['longdescription'] = ''

        if 'changelog' not in module_data:
            module_data['changelog'] = {}

        return module_data

    def _display_module_info_dialog(self, module_data, installed_module_data, module_path, module):        
        data = ''
        newVersion = ''
        if installed_module_data:
            if version.parse(installed_module_data['version']) < version.parse(module_data['version']):
                newVersion = 'New Version Available'

        data = f"{module_data['name']}\n"
        data += f"{'-'*76}\n\n"
        data += f"Description: {module_data['description']}\n\n"
        data += f"Version: {module_data['version']} {newVersion}\n"
        if installed_module_data:
            data += "Installed: Yes\n"
        else:
            data += "Installed: No\n"

        if module_data['experimental'] :
            data += "Experimental: Yes (This module may not be stable)\n"
        else:
            data += "Experimental: No\n"

        data += '\n\nReadme\n'
        data += f"{'-'*40}\n\n"  
        readmeFile = os.path.join(module_path, 'readme.txt')
        if os.path.exists(readmeFile):
            f = open(readmeFile, 'r')
            readmeText = f.read()
            f.close()          
            data += readmeText
        else:
            readmeFile = os.path.join(module_path, 'README.md')
            if os.path.exists(readmeFile):
                f = open(readmeFile, 'r')
                readmeText = f.read()
                f.close()          
                data += readmeText
            else:
                data += 'No readme.txt file available'
                     
        data += '\n\nChangelog\n'
        data += f"{'-'*40}\n\n"
        if module_data['changelog']:
            for moduleVersion in module_data['changelog']:
                data += f"Version: {moduleVersion}\n"
                changeList = module_data['changelog'][moduleVersion]
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

    def _display_info_list_dialog(self):
        done = False

        while not done:
            w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width = 40)
            module, return_code = w.radiolist('Select Module', self.modules)

            if return_code != 1:
                if module:
                    module = module[0]
                    module_path, script_path, module_data, installed_path = self._get_module_data(module)
                    installed = False
                    if os.path.exists(installed_path):
                        installed = True
                    module_data = self._read_module_meta_data(script_path)

                    installed_module_data = {}
                    script_path = os.path.join(self.dest_path, module + '.py')
                    if os.path.exists(script_path):
                        installed_module_data = self._read_module_meta_data(script_path)

                    self._display_module_info_dialog(module_data, installed_module_data, module_path, module)
            else:
                done = True

    def _display_modules_info(self):
        self._read_modules()
        self._display_info_list_dialog()
        pass

    def _get_i2c_devices(self, bus=None):

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

    def _check_internet(self):
        result = 'Yes'
        try:
            url('https://www.google.com/', timeout=3)
        except ConnectionError as ex: 
            result = 'No'
        
        return result

    def _check_gpio_status(self):        
        pi_version = self._get_pi_version()
        if pi_version[0] == '5':
            print('INFO: Found the rpi.gpio module so uninstalling it\n\n')
            subprocess.run(['pip3', 'uninstall', '-y', 'rpi.gpio'], check=False)
        else:
            print(f'Pi version is "{pi_version}" so not modifying gpio libraries')

    def _check_pip_package_installed(self, package_name):
        return importlib.util.find_spec(package_name) is not None

    def _get_pi_version(self):
        Device.ensure_pin_factory()
        piVersion = Device.pin_factory.board_info.model

        return piVersion

    def _display_system_checks(self):
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
            i2cDevices = self._get_i2c_devices()
        onlineStatus = self._check_internet()
        piVersion = self._get_pi_version()

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

    def _get_git_branch(self):
        local_branch = Repo().head.ref.name
        
        return local_branch

    def run(self):
        done = False
        
        git_branch = self._get_git_branch()
        
        if git_branch == 'dev':
            w = Whiptail(title='warning', backtitle='AllSky Module Manager', height=20, width=80)
            message = "You are using the dev branch of the Allsk extra modules.\nThis branch contains work that may not be complete nor fully tested\n\nUsage of this branch is entirely at your own risk"
            w.msgbox(message)
                
        while not done:
            w = Whiptail(title='Main Menu', backtitle='AllSky Module Manager', height=20, width = 40)
            menu_option, return_code = w.menu('', ['Install/Remove Modules', 'Module Information', 'System Checks', 'Exit'])

            if return_code == 0:
                if menu_option == 'Exit':
                    done = True
                if menu_option == 'Module Information':
                    self._display_modules_info()
                if menu_option == 'System Checks':
                    self._display_system_checks()                    
                if menu_option == 'Install/Remove Modules':
                    if self._pre_checks():
                        self._read_modules()
                        self._display_install_dialog()
                        self._do_install()
                    else:
                        sys.exit(0)
            else:
                done = True


if __name__ == '__main__':
    module_installer = ALLSKYMODULEINSTALLER()
    module_installer.run()