from whiptail import Whiptail
import os
import sys
import json
import subprocess
import tempfile
import re
import smbus
import shutil
import argparse
from pathlib import Path
from platform import python_version
from packaging import version
from urllib.request import urlopen as url
from git import Repo
from gpiozero import Device
import importlib.util
from json import JSONDecodeError


class ALLSKYMODULE:
    _module_name = None
    _module_installer_base_folder = None
    _dest_path = '/opt/allsky/modules'
    _meta_data = {}
    _installed_meta_data = {}
    _installer_data = {}
    _installed_file_path = None

    def __init__(self, module_name):
        self._module_name = module_name
        self._module_installer_base_folder = os.path.dirname(os.path.realpath(__file__)) 
        self._installed_file_path = os.path.join(self._dest_path, module_name + '.py')
        self._read_module_data()
        if self.installed:
            self._installed_meta_data = self._get_meta_data_from_file(True)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()

    @property
    def name(self):
        return self._module_name

    @name.setter
    def name(self, value):
        self._module_name = value

    @property
    def meta_data(self):
        return self._meta_data

    @property
    def installer_data(self):
        return self._installer_data

    @property
    def requirements(self):
        return self._installer_data['requirements']

    @property
    def os_packages(self):
        return self._installer_data['packages']

    @property
    def post_run(self):
        return self._installer_data['post-install']['run']

    @property
    def installed(self):
        return os.path.exists(self._installed_file_path) and os.path.isfile(self._installed_file_path)

    @property
    def winstalled(self):
        return 'ON' if self.installed else 'OFF'

    @property
    def python_version(self):
        return self._meta_data['pythonversion'] if 'pythonversion' in self._meta_data else None

    @property
    def experimental(self):
        return self._meta_data['experimental'] if 'experimental' in self._meta_data else False

    @property
    def description(self):
        return self._meta_data['description'] if 'description' in self._meta_data else ''

    @property
    def change_log(self):
        return self._meta_data['changelog'] if 'changelog' in self._meta_data else {}

    @property
    def version(self):
        return self._meta_data['version'] if 'version' in self._meta_data else ''

    @property
    def installed_version(self):
        return self._installed_file_path['version'] if 'version' in self._installed_file_path else ''

    def _get_meta_data_from_file(self, installed=False):
        if installed:
            file_name = os.path.join(self._dest_path, self.name + '.py')
        else:
            file_name = os.path.join(self._module_installer_base_folder, self.name, self.name + '.py')

        meta_data = self._get_meta_data_from_file_by_name(file_name, 'meta_data')
        if not meta_data:
            meta_data = self._get_meta_data_from_file_by_name(file_name, 'metaData')

        try:
            meta_data = json.loads(meta_data)
        except JSONDecodeError:
            meta_data = {}

        meta_data = self._fix_module_meta_data(meta_data)

        return meta_data

    def _get_meta_data_from_file_by_name(self, file_name, meta_variable_name):
        meta_data = ''
        if os.path.exists(file_name) and os.path.isfile(file_name):
            with open(file_name, 'r', encoding='utf-8') as file:
                file_contents = file.readlines()
            found = False
            level = 0

            for source_line in file_contents:

                if source_line.rstrip().endswith('{'):
                    level += 1

                if source_line.lstrip().startswith('}'):
                    level -= 1

                if source_line.lstrip().startswith(meta_variable_name):
                    found = True
                    source_line = source_line.replace(f"{meta_variable_name}", "").replace("=", "").replace(" ", "")
                if found:
                    meta_data += source_line
                if source_line.lstrip().rstrip() == '}' and found and level == 0:
                    break

        return meta_data

    def _fix_module_meta_data(self, meta_data):

        if 'experimental' not in meta_data:
            meta_data['experimental'] = False

        if 'name' not in meta_data:
            meta_data['name'] = 'Unknown'

        if 'version' not in meta_data:
            meta_data['version'] = 'Unknown'

        if 'description' not in meta_data:
            meta_data['description'] = ''

        if 'longdescription' not in meta_data:
            meta_data['longdescription'] = ''

        if 'changelog' not in meta_data:
            meta_data['changelog'] = {}

        return meta_data

    def _read_module_data(self):
        source_folder = os.path.join(self._module_installer_base_folder, self.name)
        self._meta_data  = self._get_meta_data_from_file()

        installer_json = os.path.join(self._module_installer_base_folder, self.name, 'installer.json')
        file_path = Path(installer_json)
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, 'r', encoding='UTF-8') as file:
                    self._installer_data = json.load(file)
            except json.JSONDecodeError:
                print('Error: Invalid json installer file')  #TODO DO SOMETHING !
        else:
            self._installer_data = {
                    "requirements": [],
                    "packages": [],
                    "post-install": {
                        "run": []
                    }
                }
            requirements_file = os.path.join(source_folder, 'requirements.txt')
            file_path = Path(requirements_file)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='UTF-8') as file:
                    lines = file.readlines()
                    self._installer_data['requirements'] = [line.strip() for line in lines]

            packages_file = os.path.join(source_folder, 'packages.txt')
            file_path = Path(packages_file)
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'r', encoding='UTF-8') as file:
                    lines = file.readlines()
                    self._installer_data['packages'] = [line.strip() for line in lines]

    def _get_module_info(self):
        data = ''
        new_version = ''
        if self.installed_version:
            if version.parse(self.installed_version) < version.parse(self.version):
                new_version = 'New Version Available'

        data = f'{self.name}\n'
        data += f"{'-'*76}\n\n"
        data += f'Description: {self.description}\n\n'
        data += f'Version: {self.installed_version} {self.version}\n'
        if self.installed:
            data += "Installed: Yes\n"
        else:
            data += "Installed: No\n"

        if self.experimental:
            data += "Experimental: Yes (This module may not be stable)\n"
        else:
            data += "Experimental: No\n"

        data += '\n\nReadme\n'
        data += f"{'-'*40}\n\n"  
        readme_file = os.path.join(self._dest_path, 'moduledata', 'info', self.name, 'readme.txt')
        if os.path.exists(readme_file):
            f = open(readme_file, 'r')
            readme_text = f.read()
            f.close()          
            data += readme_text
        else:
            readme_file = os.path.join(self._dest_path, 'moduledata', 'info', self.name, 'README.md')
            if os.path.exists(readme_file):
                f = open(readme_file, 'r')
                readme_text = f.read()
                f.close()          
                data += readme_text
            else:
                data += 'No readme.txt file available'

        data += '\n\nChangelog\n'
        data += f"{'-'*40}\n\n"
        if self.change_log:
            for module_version in self.change_log:
                data += f'Version: {module_version}\n'
                change_list = self.change_log[module_version]
                for change in change_list:
                    data += f"  Author: {change['author']}\n"
                    if isinstance(change['changes'], list):
                        for change_item in change['changes']:
                            data += f"    - {change_item}\n"                            
                    else:
                        data += f"    - {change['changes']}\n"
                data += "\n"
        else:
            data += 'No changelog available'

        return data


class ALLSKYMODULEINSTALLER:
    base_path = None
    dest_path = None
    dest_path_deps = None
    dest_path_info = None
    user = None
    module_dirs = []
    modules = []
    check_list = []
    debug_mode = False
    module_list = []

    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.base_path = os.path.dirname(os.path.realpath(__file__))
        self.dest_path = '/opt/allsky/modules'
        self.module_path_base = os.path.join(self.dest_path, 'moduledata')
        self.module_path_data = os.path.join(self.module_path_base, 'data')
        self.dest_path_installer = os.path.join(self.module_path_base, 'installer')
        self.dest_path_info = os.path.join(self.module_path_base, 'info')
        self.dest_path_log = os.path.join(self.module_path_base, 'logfiles')

        self.install_errors = {}

    def _add_installer_error(self, module, error):
        self.install_errors.setdefault(module.name, []).append(error)

    def _pre_checks(self):
        result = True

        if not os.path.exists(self.dest_path):
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
        self.module_list = []
        dirs = os.listdir()
        for dir in dirs:
            if dir.startswith('allsky_') and not os.path.isfile(dir):
                self.module_list.append(ALLSKYMODULE(dir))

        self.module_list = sorted(self.module_list, key=lambda p: p.name)

    def _display_install_dialog(self):
        module_list = []
        for module in self.module_list:
            module_list.append((module.name, '', module.winstalled))
        w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width=40)
        modules_to_install = w.checklist('Select the Modules To Install', module_list)[0]

        return modules_to_install

    def _check_python_version(self, module):
        result = True
        minimum_python_version = module.python_version
        if minimum_python_version is not None:
            if version.parse(python_version()) < version.parse(minimum_python_version):
                error = f'This module requires Python version {minimum_python_version} you have {python_version()} installed'
                self._add_installer_error(module.name, error)
                print(error)
                result = False

        return result

    def _install_packages(self, module):
        result = True
        print('INFO: Installing package dependencies')
        for package in module.os_packages:
            cmd = f'sudo apt-get install -y {package} > /dev/null 2>&1'
            try:
                apt_result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            except Exception as e:
                if self.debug_mode:
                    eType, eObject, eTraceback = sys.exc_info()
                    error_message = f'ERROR: _install_packages failed on line {eTraceback.tb_lineno} - {e}'
                else:
                    error_message = f'ERROR: failed to install OS package {package}'
                self._add_installer_error(module, error_message)
                result = False

        return result

    def _install_python_libraries(self, module):
        result = True
        log_folder = os.path.join(self.dest_path_log, module.name)
        log_folder_path = Path(log_folder)
        log_folder_path.mkdir(parents=True, exist_ok=True)        
        log_path = os.path.join(log_folder, 'dependencies.log')
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.writelines(line + '\r\n' for line in module.requirements)
            temp_file.flush()

            print('INFO: Installing Python dependencies')
            pip_result = 0
            try:
                pip_result = os.system(f'pip3 install --no-warn-script-location -r {temp_file.name} > {log_path} 2>&1')
            except Exception as e:
                if self.debug_mode:                
                    eType, eObject, eTraceback = sys.exc_info()
                    error_message = f'ERROR: _install_python_libraries failed on line {eTraceback.tb_lineno} - {e}'
                else:
                    error_message = f'ERROR: failed to install Python modules {", ".join(module.requirements)}'
                self._add_installer_error(module, error_message)
                result = False

            if pip_result != 0 and pip_result != 512:
                self._add_installer_error(module, f'Check {log_path} {pip_result} for any errors') 
                result = False

        return result

    def _install_dependencies(self, module):
        result = False

        if self._install_packages(module):
            if self._install_python_libraries(module):
                result = True

        return result

    def _create_directory(self, directory):
        destination_folder = Path(directory)
        destination_folder.mkdir(parents=True, exist_ok=True)

    def _copy_file(self, source, dest):
        result = True
        if os.path.exists(source):
            self._create_directory(dest)

            command = f'cp {source} {dest}'
            copy_result = os.system(command)
            if copy_result == 0:
                command = f'sudo chown {self.user}:www-data {dest}'
                chown_result = os.system(command)
                if chown_result != 0:
                    result = f'Could not set permissions on {dest}\n\n'
            else:
                result = f'Could not copy module from {source} to {dest}\n\n'

        return result

    def _install_module(self, module):
        result = True
        print(f'INFO: Installing {module} module')
        source = os.path.join(self.base_path, module.name, module.name + '.py')
        dest = self.dest_path
        result = self._copy_file(source, dest)
        if result:
            self._create_directory(self.module_path_data)
            self._create_directory(os.path.join(self.dest_path_info, module.name))

            doc_files = ['readme.txt', 'README.txt', 'README.md']
            for file_type in doc_files:
                source = os.path.join(self.base_path, module.name, file_type)
                dest = os.path.join(self.dest_path_info, module.name)
                self._copy_file(source, dest)

            module_data_path = os.path.join(self.base_path, module.name, module.name)
            if os.path.exists(module_data_path) and os.path.isdir(module_data_path):
                command = f'cp -ar {module_data_path} {self.module_path_data}'
                os.system(command)

            installer_folder = os.path.join(self.dest_path_installer, module.name)
            self._create_directory(installer_folder)
            installer_file = os.path.join(installer_folder, 'installer.json')
            with open(installer_file, 'w', encoding='UTF-8') as file:
                json.dump(module.installer_data, file, indent=4)        

        else:
            self._add_installer_error(module.name, result)

        return result

    def _find_module(self, module_name):
        found_module = None
        for module in self.module_list:
            if module.name == module_name:
                found_module = module
                break

        return found_module

    def _run_post_installaton(self, module):
        post_run_script = module.post_run
        if post_run_script:
            module_data_folder = os.path.join(self.module_path_data, module.name)
            post_run_script = post_run_script.replace('{install_data_dir}', module_data_folder)
            print(f'Runing post install routine {os.path.basename(post_run_script)}')
            subprocess.run(post_run_script, shell=True)

    def _do_install(self, modules_to_install):
        result = True

        os.system('clear')

        for module_name in modules_to_install:
            module = self._find_module(module_name)
            if module is not None:
                title = f'Installing {module.name}'
                print(title)
                print('='*len(title))

                if (result := self._check_python_version(module)):
                    if (result := self._install_dependencies(module)):
                        if (result := self._install_module(module)):
                            self._run_post_installaton(module)
                            print(f'SUCCESS: Module "{module}" installed\n\n')
                        else:
                            error = f'ERROR: Module "{module}" failed to install'
                            self._add_installer_error(module, f'{error}')
                            print(f'{error}\n\n')

                if not result:
                    self._display_install_errors()
                    break

    def _display_install_errors(self):
        message_text = ''
        for module_with_errors in self.install_errors:
            message_text = message_text + f'ERRORS Installing {module_with_errors}\n'
            message_text = message_text + '\n'.join(self.install_errors[module_with_errors])
        w = Whiptail(title='Install Errors', backtitle='AllSky Module Manager', height=30, width=80)
        msgbox = w.msgbox(message_text)

    def _display_module_info_dialog(self, module):
        data = module._get_module_info()

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
            module_list = []
            for module in self.module_list:
                module_list.append((module.name, '', 'OFF'))            
            w = Whiptail(title='Select Modules', backtitle='AllSky Module Manager', height=20, width=40)
            module_name, return_code = w.radiolist('Select Module', module_list)

            if return_code != 1:
                module_name = module_name[0]
                module = ALLSKYMODULE(module_name)
                self._display_module_info_dialog(module)
            else:
                done = True

    def _display_modules_info(self):
        self._read_modules()
        self._display_info_list_dialog()
        pass

    def _get_i2c_devices(self, bus=None):

        devices = []

        if bus is None:
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
            message = "You are using the dev branch of the Allsky extra modules.\nThis branch contains work that may not be complete nor fully tested\n\nUsage of this branch is entirely at your own risk"
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
                        modules_to_install = self._display_install_dialog()
                        self._do_install(modules_to_install)
                    else:
                        sys.exit(0)
            else:
                done = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Allsky extra module installer")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode, shows more detailed errors')
    args = parser.parse_args()

    module_installer = ALLSKYMODULEINSTALLER(args.debug)
    module_installer.run()
