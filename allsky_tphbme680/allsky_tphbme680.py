'''
allsky_tphbme680.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import bme680


metaData = {
	"name": "tphbme680 (Temperature, Humidity, Pressure)",
	"description": "Provides T,H,P levels",
	"module": "allsky_tphbme680",
	"version": "v1.0.0",    
	"events": [
	    "periodic"
	],
	"experimental": "true",    
	"arguments":{
	    "tempoffset": "0"
	},
	"argumentdetails": {   
	    "tempoffset" : {
	        "required": "false",
	        "description": "Temperature Offset of the sensor",
	        "help": "Use this if there is an offset between the bme680 temperature and the real temperature"        
	    }
	},
	"enabled": "false"            
}

def tphbme680(params, event):
	tempoffset = params["tempoffset"]
	temperature = None
	humidity = None
	pressure = None
	dewpoint = None

	try:
	    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
	except (RuntimeError, IOError):
	    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

	sensor.set_humidity_oversample(bme680.OS_2X)
	sensor.set_pressure_oversample(bme680.OS_4X)
	sensor.set_temperature_oversample(bme680.OS_8X)
	sensor.set_filter(bme680.FILTER_SIZE_3)

	try:
	    if sensor.get_sensor_data():
	        temperature = sensor.data.temperature
	        humidity = sensor.data.humidity
	        pressure = sensor.data.pressure
	        dewpoint = temperature - ((100 - humidity) / 5)

	    extraData = {}
	    extraData["AS_BME680TEMPERATURE"] = str(temperature)
	    extraData["AS_BME680HUMIDITY"] = str(humidity)
	    extraData["AS_BME680PRESSURE"] = str(pressure)
	    extraData["AS_BME680DEWPOINT"] = str(dewpoint)

	    s.saveExtraData("allskybme680.json", extraData)

	    result = f"bme680 Read Ok Temperature={temperature} Humidity={humidity} Pressure={pressure} Dewpoint={dewpoint}"
	    s.log(4,f"INFO: {result}")
	except ValueError:
	    result = "Error reading bme680"
	    pass

	return result
