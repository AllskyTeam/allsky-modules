# Changelog — allsky_ina3221

---

## v2.0.0 — 2026-03-07

### Breaking Changes
- Replaced `barbudor_ina3221` library with `adafruit-circuitpython-ina3221`. Update your Pi with:
  ```
  pip3 install adafruit-circuitpython-ina3221 --break-system-packages
  ```
- Channel reading API updated internally to use 0-based index property access (`ina[n].bus_voltage`) instead of method calls (`ina3221.bus_voltage(channel)`)

### New Features
- **Low voltage shutdown** — monitors a configurable channel and triggers a kernel-managed `sudo shutdown -h` when voltage drops below a set threshold
- **Shutdown delay** — configurable dropdown (1, 5, 15, 30, or 60 minutes) to allow AllSky logs and housekeeping to complete before power off
- **Shunt resistance** — configurable via the UI; defaults to 0.05 ohms to match the Adafruit INA3221 breakout board
- **Custom I2C address** — `i2caddress` param is now wired up and functional; uses `busio.I2C` with the specified hex address when set
- **Shutdown channel validation** — logs a warning at startup if low voltage shutdown is enabled but the selected monitor channel is disabled
- **Shutdown channel dropdown** — `shutdownchannel` is now a select field (Channel 1/2/3) instead of a free-text field, preventing invalid input
- **UI tabs** — settings are now organised across three tabs: main settings, Extra Data, and Shutdown

### Bug Fixes
- Fixed critical shutdown logic flaw — the shutdown countdown was being rescheduled on every module run (every ~1 minute), resetting the timer indefinitely and preventing the system from ever shutting down. Log showed 65+ consecutive WARNING entries over nearly 2 hours with the voltage dropping from 11.98V to 10.97V while the system stayed running
- Added `is_shutdown_pending()` helper that calls `shutdown --show` to check whether a shutdown is already scheduled before issuing a new one. If a shutdown is already pending, the module logs a quieter level 1 info message and skips the command entirely
- Fixed low voltage shutdown silently failing when the AllSky user lacked passwordless sudo rights for `/sbin/shutdown`. `subprocess.run` with `check=False` was swallowing the failure with no log output
- Replaced `check=False` with full output capture — shutdown command result (success or failure) is now always logged at level 0
- Added `timeout=10` to the subprocess call to prevent hanging if sudo prompts for a password
- All failure paths now log a clear actionable error message including the exact `visudo` entry required:
  ```
  allsky ALL=(ALL) NOPASSWD: /sbin/shutdown
  ```
- Fixed `cleanup` using a Python `set` (`{}`) instead of a `list` (`[]`) for the files array — this would have caused `ina3221_cleanup()` to fail silently
- Fixed `shunt_voltage` unit handling — the Adafruit library returns millivolts; value is now correctly divided by 1000 before being added to `bus_voltage`
- Fixed sensor returning 0.0 on first read — added `time.sleep(0.5)` after init to allow the first conversion cycle to complete
- Fixed `params` key access using direct `[]` indexing — all params now use `.get()` with safe defaults, preventing `KeyError` crashes when the module config is missing newly added keys (e.g. after an upgrade)
- Fixed `to_bool()` helper to handle AllSky passing channel enable params as either `bool` or `str` depending on context
- Removed never-called `debugOutput()` function that referenced wrong sensor variables (temperature, humidity etc.) — was copied from another module
- Removed `barbudor`-specific `IS_FULL_API` configuration block

### Installation
- Added `requirements.txt` for automatic dependency installation by the AllSky module installer
- Dependencies: `adafruit-circuitpython-ina3221`, `adafruit-blinka`, `adafruit-circuitpython-busdevice`
- No pinned versions to avoid conflicts with other AllSky modules that share the same Adafruit dependencies

### Cleanup
- Renamed all functions and variables to PEP 8 snake_case (`readChannel` → `read_channel` etc.)
- Replaced three repeated `if c1/c2/c3` channel read blocks with a single loop over a `channels` list
- Replaced wildcard import (`from barbudor_ina3221.full import *`) with explicit import
- Added `to_bool()`, `read_channel()`, and `check_shutdown()` as named, documented helper functions
- Added docstrings to all functions
- Added `subprocess` and `busio` imports required for shutdown and custom I2C address support
- Version bumped from v1.1.1 to v2.0.0 reflecting library replacement and new features

---

## v1.1.1 — original release
- Initial implementation using `barbudor_ina3221` library
- Basic voltage, current, and power monitoring across three channels
- AllSky overlay variable output via `saveExtraData`
