import sys
import time
import datetime
import subprocess
import board
import busio
import allsky_shared as s
from adafruit_ina3221 import INA3221

metaData = {
    "name": "Current/voltage monitoring",
    "description": "Monitors current and voltage using an INA3221",
    "module": "allsky_ina3221",
    "version": "v2.0.0",
    "events": [
        "periodic"
    ],
    "experimental": "true",
    "arguments": {
        "i2caddress": "",
        "c1enable": "true",
        "c1name": "solar",
        "c2enable": "true",
        "c2name": "battery",
        "c3enable": "true",
        "c3name": "usb",
        "extradatafilename": "allskyina3221.json",
        "shutdownenable": "false",
        "shutdownchannel": "2",
        "shutdownvoltage": "11.5",
        "shutdowndelay": "+1",
        "shuntresistance": "0.05"
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard I2C address for the device. Leave blank to use the default 0x40. NOTE: Value must be hex i.e. 0x41"
        },
        "c1enable": {
            "required": "false",
            "description": "Enable Channel 1",
            "help": "Enable channel 1 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c1name": {
            "required": "false",
            "description": "Channel 1 name",
            "help": "Name of the channel 1 AllSky overlay variable"
        },
        "c2enable": {
            "required": "false",
            "description": "Enable Channel 2",
            "help": "Enable channel 2 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c2name": {
            "required": "false",
            "description": "Channel 2 name",
            "help": "Name of the channel 2 AllSky overlay variable"
        },
        "c3enable": {
            "required": "false",
            "description": "Enable Channel 3",
            "help": "Enable channel 3 on the sensor",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "c3name": {
            "required": "false",
            "description": "Channel 3 name",
            "help": "Name of the channel 3 AllSky overlay variable"
        },
        "shuntresistance": {
            "required": "false",
            "description": "Shunt Resistance (Ohms)",
            "help": "The shunt resistor value in ohms used on your board. The Adafruit INA3221 breakout uses 0.05 ohms. Change this only if you are using a different board or custom hardware."
        },
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "tab": "Extra Data",
            "help": "The name of the file to create with the voltage/current data for the overlay manager"
        },
        "shutdownenable": {
            "required": "false",
            "description": "Enable Low Voltage Shutdown",
            "help": "Monitor a channel and shut the system down if voltage drops below the threshold. The selected channel must be enabled on the main tab.",
            "tab": "Shutdown",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "shutdownchannel": {
            "required": "false",
            "description": "Shutdown Monitor Channel",
            "help": "The channel to monitor for low voltage shutdown. Must be enabled on the main tab.",
            "tab": "Shutdown",
            "type": {
                "fieldtype": "select",
                "values": "1,2,3",
                "labels": "Channel 1,Channel 2,Channel 3"
            }
        },
        "shutdownvoltage": {
            "required": "false",
            "description": "Shutdown Voltage Threshold (V)",
            "help": "If the monitored channel voltage drops below this value the system will log a warning and shut down after the configured delay",
            "tab": "Shutdown"
        },
        "shutdowndelay": {
            "required": "false",
            "description": "Shutdown Delay",
            "help": "How long to wait before shutting down after a low voltage trigger. Allows time for logs and housekeeping to complete. Value is passed directly to 'sudo shutdown -h'.",
            "tab": "Shutdown",
            "type": {
                "fieldtype": "select",
                "values": "+1,+5,+15,+30,+60",
                "labels": "1 Minute,5 Minutes,15 Minutes,30 Minutes,60 Minutes"
            }
        }
    },
    "businfo": [
        "i2c"
    ]
}


def to_bool(value):
    """Safely convert a param value to bool.
    Handles both bool and string inputs since AllSky may pass either."""
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def read_channel(ina, channel):
    """Read voltage, current, and power from the given channel (1-indexed).

    The Adafruit INA3221 library uses 0-based indexing internally,
    so channel 1 maps to ina[0], channel 2 to ina[1], etc.

    - bus_voltage: volts
    - shunt_voltage: millivolts
    - current_amps: amps

    Current is not abs()-filtered, allowing monitoring of bi-directional
    current flow (e.g. battery charge/discharge). Units are Amps and Watts.
    """
    ch = ina[channel - 1]
    bus_voltage = ch.bus_voltage
    shunt_voltage_mv = ch.shunt_voltage
    current = round(ch.current_amps, 3)
    voltage = round(bus_voltage + (shunt_voltage_mv / 1000), 2)
    power = round(voltage * current, 3)

    s.log(4, f"INFO: Channel {channel} read — voltage {voltage}V, current {current}A, "
             f"bus voltage {bus_voltage}V, shunt voltage {shunt_voltage_mv}mV, power {power}W")

    return voltage, current, power


def is_shutdown_pending():
    """Check whether a system shutdown is already scheduled.

    Uses 'shutdown --show' which exits with code 0 if a shutdown is
    scheduled, or non-zero if no shutdown is pending. This prevents
    the module from rescheduling the shutdown countdown on every run.
    """
    try:
        result = subprocess.run(
            ["shutdown", "--show"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def check_shutdown(voltage, channel, threshold, delay):
    """Log a warning and shut down if voltage is below threshold.

    Uses 'sudo shutdown -h <delay>' to schedule a kernel-managed shutdown.
    The delay is configured via params and passed directly to the shutdown
    command (e.g. '+1' for 1 minute, '+5' for 5 minutes). This is handled
    by the OS independently of any running processes, allowing logs and
    housekeeping to complete before power off.

    Checks whether a shutdown is already scheduled before issuing the command
    to prevent the countdown being reset on every module run.

    IMPORTANT: The AllSky user must have passwordless sudo rights for the
    shutdown command. Add the following line via 'sudo visudo':
        allsky ALL=(ALL) NOPASSWD: /sbin/shutdown
    """
    if voltage < threshold:
        delay_label = delay.replace("+", "")
        if is_shutdown_pending():
            s.log(1, f"INFO: Channel {channel} voltage {voltage}V is below threshold "
                     f"— shutdown already scheduled, not rescheduling.")
            return
        s.log(0, f"WARNING: Channel {channel} voltage {voltage}V is below shutdown "
                 f"threshold {threshold}V — system will shut down in {delay_label} minute(s).")
        try:
            result = subprocess.run(
                ["sudo", "shutdown", "-h", delay],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                s.log(0, f"INFO: Shutdown command accepted successfully.")
            else:
                s.log(0, f"ERROR: Shutdown command failed (exit code {result.returncode}). "
                         f"stdout: {result.stdout.strip()} stderr: {result.stderr.strip()}. "
                         f"Ensure the AllSky user has passwordless sudo for /sbin/shutdown. "
                         f"Run: sudo visudo and add: allsky ALL=(ALL) NOPASSWD: /sbin/shutdown")
        except subprocess.TimeoutExpired:
            s.log(0, "ERROR: Shutdown command timed out — sudo may be waiting for a password. "
                     "Run: sudo visudo and add: allsky ALL=(ALL) NOPASSWD: /sbin/shutdown")
        except Exception as e:
            s.log(0, f"ERROR: Shutdown command raised an exception — {e}")


def ina3221(params, event):
    result = "INA3221 read ok"

    try:
        c1_enabled = to_bool(params.get("c1enable", "true"))
        c1_name = params.get("c1name", "solar").upper()
        c2_enabled = to_bool(params.get("c2enable", "true"))
        c2_name = params.get("c2name", "battery").upper()
        c3_enabled = to_bool(params.get("c3enable", "true"))
        c3_name = params.get("c3name", "usb").upper()
        extradatafilename = params.get("extradatafilename", "allskyina3221.json")

        shutdown_enabled = to_bool(params.get("shutdownenable", "false"))
        shutdown_channel = int(params.get("shutdownchannel", "2"))
        shutdown_voltage = float(params.get("shutdownvoltage", "11.5"))
        shutdown_delay = params.get("shutdowndelay", "+1")
        shunt_resistance = float(params.get("shuntresistance", "0.05"))

        # Warn at startup if the shutdown channel is not enabled, as it will
        # never be read and the shutdown trigger will never fire.
        channel_enabled_map = {1: c1_enabled, 2: c2_enabled, 3: c3_enabled}
        if shutdown_enabled and not channel_enabled_map.get(shutdown_channel, False):
            s.log(0, f"WARNING: Low voltage shutdown is enabled but channel "
                     f"{shutdown_channel} is disabled — shutdown will never trigger.")

        # Use a custom I2C address if one has been provided, otherwise use the
        # default board I2C bus which auto-detects the device at 0x40.
        i2c_address = params.get("i2caddress", "").strip()
        if i2c_address:
            i2c_bus = busio.I2C(board.SCL, board.SDA)
            ina = INA3221(i2c_bus, address=int(i2c_address, 16))
        else:
            i2c_bus = board.I2C()
            ina = INA3221(i2c_bus)

        # Apply shunt resistance to all channels.
        # Default is 0.05 ohms to match the Adafruit INA3221 breakout board.
        # Correct shunt resistance is required for accurate current readings.
        for i in range(3):
            ina[i].shunt_resistance = shunt_resistance

        # Allow time for the first conversion cycle to complete.
        # Without this the sensor returns 0.0 on the first read.
        time.sleep(0.5)

        # Pre-populate all channels with N/A so the overlay always has valid keys,
        # even if a channel is disabled or fails to read.
        extra_data = {
            f"AS_{c1_name}VOLTAGE": "N/A",
            f"AS_{c1_name}CURRENT": "N/A",
            f"AS_{c1_name}POWER": "N/A",
            f"AS_{c2_name}VOLTAGE": "N/A",
            f"AS_{c2_name}CURRENT": "N/A",
            f"AS_{c2_name}POWER": "N/A",
            f"AS_{c3_name}VOLTAGE": "N/A",
            f"AS_{c3_name}CURRENT": "N/A",
            f"AS_{c3_name}POWER": "N/A",
            "AS_INA3221TIME": datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        }

        channels = [
            (c1_enabled, c1_name, 1),
            (c2_enabled, c2_name, 2),
            (c3_enabled, c3_name, 3),
        ]

        for enabled, name, channel in channels:
            if enabled:
                voltage, current, power = read_channel(ina, channel)
                extra_data[f"AS_{name}VOLTAGE"] = str(voltage)
                extra_data[f"AS_{name}CURRENT"] = str(current)
                extra_data[f"AS_{name}POWER"] = str(power)

                if shutdown_enabled and channel == shutdown_channel:
                    check_shutdown(voltage, channel, shutdown_voltage, shutdown_delay)

        s.saveExtraData(extradatafilename, extra_data)

    except Exception as e:
        _, _, eTraceback = sys.exc_info()
        s.log(0, f"ERROR: ina3221 failed on line {eTraceback.tb_lineno} - {e}")

    return result


def ina3221_cleanup():
    module_data = {
        "metaData": metaData,
        "cleanup": {
            "files": [
                "allskyina3221.json"
            ],
            "env": {}
        }
    }
    s.cleanupModule(module_data)
