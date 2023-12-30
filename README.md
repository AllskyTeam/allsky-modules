# AllSky Modules

## Installation

### NOTE: These modules require version v2023.05.01_04 or later of Allsky

This repository contains additional modules that can be used with Allsky. To install the modules first clone this repository.

`git clone https://github.com/AllskyTeam/allsky-modules.git`

Then run the installer

`./install.sh`

> **NOTE:** If you are using any other branch other than master a warning will be displayed


### Moving around the menu
Use the up and down arrow keys to move the highlighted selection between the options available. Pressing the right arrow key will jump out of the options menu and take you to the `<Ok>` and `<Finish>` buttons. Pressing left will take you back to the options. Alternatively, use the Tab key to switch between these.

When a list is displayed the `<space>` bar can be used to select or unselect an option


### Module Installer Main Menu

 ![Main Menu](/images/menu.png)

### Install/Remove Modules

 ![Main Menu](/images/modules.png)

This option will display all of the available modules. If a module is already installed then it will be selected by default, this allows previously installed modules to be updated.

You can select or unselect a module. If a module is unselected but currently installed then it will be uninstalled

> **NOTE:**  If you uninstall a module then please ensure you check the overlay editor to ensure that you have removed and variables the module may generate.

### Module information
 ![Main Menu](/images/infomenu.png)

This option will display a list of modules. Selecting a module, using the `<space>` bar and pressing `<enter` will display information about the module.

 ![Main Menu](/images/moduleinfo.png)

### System Checks
This option will display information about the system.

 ![Main Menu](/images/systeminfo.png)


## Available Module

| Module  | Description  |
|---|---|
| allsky_ai | Determines Cloud Cover using AI|
| allsky_boilerplate | Example Boilerplate module |
| allsky_border | Expands a captured image adding a border |
| allsky_dewheater | Managed a dewheater |
| allsky_discordsend | Send images to Discord channels |
| allsky_fans | Controls the Pi Fans |
| allsky_gpio | Control a GPIO Pin |
| allsky_hddtemp | Reads Hard Drive temperatures |
| allsky_ina3221 | Reads current and voltage |
| allsky_influxdb | Writes data to an Influxdb database |
| allsky_light | Estimates the sky brightness using an external sensor |
| allsky_lightgraph | Displays sun information |
| allsky_ltr390 | Measures UV levels via an external sensor |
| allsky_mlx90640 | Generates an IR image |
| allsky_openweathermap | Reads weather data from OpenWeather maps |
| allsky_pigps | REads position data from an attached GPS |
| allsky_publishdata |   |
| allsky_rain | Detects rainfall via an external sensor |
| allsky_script | Allows a script to be run during day/night and night/day transitions |
| allsky_sqm | Sqky Quality Module |
| allsky_test | Module for testing the installer - DO NOT USE |


## Custom Modules

It is possible to write your own modules for AllSky using Python. Details of how to create modules can be found in the wiki.

If you feel a module would be of help to the community then please consider contributing it to this repository.
