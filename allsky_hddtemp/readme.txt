This module reads temperatures for hard drives to be displayed on overlays.

The module requires the following:

- One or more hard drives, note that SD cards are NOT supported.
- A USB to SATA controller that supports S.M.A.R.T.

The module will read all available devices that are supported and provide the following variables for use on overlays:

* AS_HDD{name}TEMP - i.e. AS_HDDSDATEMP for the current temperature of SDA.
* AS_HDD{name}TEMPMAX - i.e. AS_HDDSDATEMPMAX for the max temperature of SDA.

If any of the values cannot be read from S.M.A.R.T id 194 then they will not be made available, at log level 4 a message will be displayed in the main allsky.log file.

You can choose to colour the temperatures based upon a max good value.
