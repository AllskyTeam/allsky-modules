import subprocess

def is_i2c_enabled():
    result = subprocess.run(
        ["sudo", "raspi-config", "nonint", "get_i2c"],
        stdout=subprocess.DEVNULL
    )
    return result.returncode == 0

if is_i2c_enabled():
    print("I2C is enabled")
else:
    print("I2C is disabled")
