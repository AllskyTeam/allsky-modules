# AllSky INA3221 Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Periodic |

A module to read voltage, current, and power from 1 to 3 channels of an INA3221 triple-channel power monitor. Each channel is independently configurable with a custom name that maps directly to an AllSky overlay variable.

## Use Cases

- **Solar power systems** — monitor solar panel output voltage and current alongside battery state and load consumption simultaneously across all three channels
- **Battery monitoring** — track battery voltage over time and use the low voltage shutdown feature to safely power down the Pi before the battery is fully depleted, protecting both the battery and the filesystem
- **Dew heater monitoring** — confirm a dew heater is drawing the expected current and flag if it has failed or disconnected
- **USB power monitoring** — monitor the voltage and current being delivered to the camera or other USB peripherals
- **Bi-directional current monitoring** — current readings are not abs()-filtered, so the module can detect both charge and discharge current on a battery channel

## Hardware

This module supports the [Adafruit INA3221 Triple-Channel DC Voltage and Current Sensor Breakout](https://www.adafruit.com/product/6062). The board monitors up to three independent channels at 0–26V and ±3.2A via I2C.

Default I2C address: `0x40`

Shunt resistor value: `0.05 ohms` (Adafruit breakout default)

## Installation

Install the required Python libraries on your Raspberry Pi:

```bash
pip3 install -r requirements.txt --break-system-packages
```

Or let the AllSky module installer handle this automatically via `requirements.txt`.

### Sudoers Configuration (required for low voltage shutdown)

If you intend to use the low voltage shutdown feature, the AllSky user must have passwordless sudo rights for the shutdown command. Run:

```bash
sudo visudo -f /etc/sudoers.d/allsky-shutdown
```

Add the following line (replace `allsky` with your AllSky user if different):

```
allsky ALL=(ALL) NOPASSWD: /sbin/shutdown
```

## Configuration

Settings are organised across three tabs in the AllSky WebUI.

### Main Tab

| Parameter | Description | Default |
| --- | --- | --- |
| I2C Address | Override the default I2C address. Leave blank for `0x40`. Must be hex e.g. `0x41` | _(blank)_ |
| Enable Channel 1 | Enable reading from channel 1 | `true` |
| Channel 1 Name | AllSky overlay variable name prefix for channel 1 | `solar` |
| Enable Channel 2 | Enable reading from channel 2 | `true` |
| Channel 2 Name | AllSky overlay variable name prefix for channel 2 | `battery` |
| Enable Channel 3 | Enable reading from channel 3 | `true` |
| Channel 3 Name | AllSky overlay variable name prefix for channel 3 | `usb` |
| Shunt Resistance | Shunt resistor value in ohms. Change only if using a non-Adafruit board | `0.05` |

### Extra Data Tab

| Parameter | Description | Default |
| --- | --- | --- |
| Extra Data Filename | JSON file written with voltage/current data for the overlay manager | `allskyina3221.json` |

### Shutdown Tab

| Parameter | Description | Default |
| --- | --- | --- |
| Enable Low Voltage Shutdown | Monitor a channel and shut down when voltage drops below the threshold | `false` |
| Shutdown Monitor Channel | Channel to monitor (1, 2, or 3) | `2` |
| Shutdown Voltage Threshold | Voltage in volts below which shutdown is triggered | `11.5` |
| Shutdown Delay | How long after the trigger before the system shuts down | `1 Minute` |

## Overlay Variables

For each enabled channel, the following variables are written to the extra data JSON file and are available in the AllSky overlay manager. Variable names are based on the channel name configured in settings (uppercased).

Using the default channel names `solar`, `battery`, and `usb`:

| Variable | Description | Units |
| --- | --- | --- |
| `AS_SOLARVOLTAGE` | Channel 1 voltage | V |
| `AS_SOLARCURRENT` | Channel 1 current | A |
| `AS_SOLARPOWER` | Channel 1 power | W |
| `AS_BATTERYVOLTAGE` | Channel 2 voltage | V |
| `AS_BATTERYCURRENT` | Channel 2 current | A |
| `AS_BATTERYPOWER` | Channel 2 power | W |
| `AS_USBVOLTAGE` | Channel 3 voltage | V |
| `AS_USBCURRENT` | Channel 3 current | A |
| `AS_USBPOWER` | Channel 3 power | W |
| `AS_INA3221TIME` | Timestamp of last successful read | MM/DD/YYYY HH:MM:SS |

Disabled channels will show `N/A` in the overlay.

## Low Voltage Shutdown

When enabled, the module monitors the configured channel on every periodic run. If the voltage drops below the threshold, a warning is logged and a kernel-managed shutdown is scheduled via `sudo shutdown -h`. The shutdown is handled by the OS independently of AllSky, allowing logs and housekeeping to complete before power off.

The module checks whether a shutdown is already pending before scheduling a new one, preventing the countdown from being reset on every module run.

## Notes

- The module requires a short initialisation delay (`0.5s`) after connecting to the sensor to allow the first conversion cycle to complete. Without this, the first read returns `0.0`.
- Current readings are not abs()-filtered, allowing detection of bi-directional current flow (e.g. battery charging vs discharging).
- If using a non-Adafruit INA3221 board, check the shunt resistor value printed on the PCB and update the **Shunt Resistance** setting accordingly. An incorrect value will result in inaccurate current and power readings.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.
