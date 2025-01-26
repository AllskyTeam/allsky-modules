'''
allsky_spaceweather.py

Part of allsky postprocess.py modules for Thomas Jacquin's AllSky.
https://github.com/AllskyTeam/allsky

This module retrieves space weather data from NOAA SWPC APIs and processes it for AllSky Overlays
'''
import allsky_shared as s
import sys
import requests
import json
from bs4 import BeautifulSoup
import ephem
import pytz
import datetime

metaData = {
	"name": "Space Weather",
	"description": "Retrieves and processes space weather data from NOAA SWPC for use in AllSky overlays",
	"module": "allsky_spaceweather",
	"version": "v1.0.0",
	"events": [
	    "periodic"
	],
	"arguments": {
	    "latitude": "",
	    "longitude": "",
	    "period": 300,
	    "filename": "spaceweather.json"
	},
	"argumentdetails": {
	    "latitude": {
	        "required": "true",
	        "description": "Latitude",
	        "help": "Your observation latitude (e.g. 43.61N or 43.61)"
	    },
	    "longitude": {
	        "required": "true", 
	        "description": "Longitude",
	        "help": "Your observation longitude (e.g. -116.20 or 116.20W)"
	    },
	    "filename": {
	        "required": "true",
	        "description": "Output Filename",
	        "help": "The name of the file that will be written to the allsky/tmp/extra directory"
	    },
	    "period": {
	        "required": "true",
	        "description": "Update Period",
	        "help": "How often to fetch new data (in seconds). 300 seconds minimum (5 minutes) to avoid overloading the API",
	        "type": {
	            "fieldtype": "spinner",
	            "min": 300,
	            "max": 3000,
	            "step": 60
	        }
	    }
	},
	"changelog": {
	    "v1.0.0": [
	        {
	            "author": "Jim Cauthen",
	            "authorurl": "https://github.com/jcauthen78/",
	            "changes": "Initial Release"
	        }
	    ]
	}
}

def get_color(value, ranges, colors):
	"""Helper function to determine color based on value ranges"""
	for i in range(len(ranges) - 1):
	    if ranges[i] <= value < ranges[i+1]:
	        return colors[i]
	return colors[-1]

def safe_float_conversion(data, default='xxx'):
	"""Safely convert string to float with default value"""
	try:
	    return float(data)
	except (TypeError, ValueError):
	    return default

def process_solar_wind_data(data):
	"""Process solar wind data and return formatted values with colors"""
	density = safe_float_conversion(data[-1][1])
	speed = safe_float_conversion(data[-1][2])
	temp = safe_float_conversion(data[-1][3])
	temp_fmt = format(temp, ',').rstrip('0').rstrip('.') if temp != 'xxx' else temp

	# Color determination logic
	density_color = "#10e310"  # default green
	if isinstance(density, float):
	    if density > 6:
	        density_color = "#10e310"  # green
	    elif 2 <= density <= 6:
	        density_color = "#ffec00"  # yellow
	    else:
	        density_color = "#f56b6b"  # red

	speed_color = "#10e310"  # default green
	if isinstance(speed, float):
	    if speed > 550:
	        speed_color = "#f56b6b"  # red
	    elif 500 <= speed <= 550:
	        speed_color = "#ffec00"  # yellow
	    else:
	        speed_color = "#10e310"  # green

	temp_color = "#808080"  # default gray
	if isinstance(temp, float):
	    if temp >= 500001:
	        temp_color = "#f56b6b"  # red
	    elif temp >= 300001:
	        temp_color = "#ffec00"  # yellow
	    elif temp >= 100001:
	        temp_color = "#10e310"  # green
	    elif temp >= 50000:
	        temp_color = "#ffec00"  # yellow
	    else:
	        temp_color = "#f56b6b"  # red

	return {
	    "speed": {"value": speed, "color": speed_color},
	    "density": {"value": density, "color": density_color},
	    "temp": {"value": temp_fmt, "color": temp_color}
	}

def spaceweather(params, event):
	"""Main entry point for the module"""
	result = ""
	
	# API endpoints
	urls = {
	    "wind": "https://services.swpc.noaa.gov/products/solar-wind/plasma-6-hour.json",
	    "kp": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
	    "bz": "https://services.swpc.noaa.gov/products/solar-wind/mag-6-hour.json"
	}

	try:
	    # Get period from params, enforce minimum of 300 seconds
	    period = max(300, int(params.get("period", 300)))
	    module = metaData["module"]
	    
	    shouldRun, diff = s.shouldRun(module, period)
	    if not shouldRun:
	        result = f"Last run {diff} seconds ago. Running every {period} seconds"
	        s.log(1, f"INFO: {result}")
	        return result

	    # Calculate sun angle
	    utcnow = datetime.datetime.now(tz=pytz.UTC)
	    dtUtc = utcnow.replace(microsecond=0, tzinfo=None)
	    
	    obs = ephem.Observer()
	    obs.lat = str(s.convertLatLon(params["latitude"].strip()))
	    obs.long = str(s.convertLatLon(params["longitude"].strip()))
	    obs.date = dtUtc.strftime("%Y-%m-%d %H:%M:%S")

	    sun = ephem.Sun(obs)
	    sun.compute(obs)
	    sun_angle = round(float(sun.alt) * 57.2957795, 1)

	    # Initialize data dictionary
	    space_weather_data = {
	        "SWX_S_ANGLE": {
	            "value": sun_angle,
	            "expires": 0
	        }
	    }

	    # Fetch and process solar wind data
	    response = requests.get(urls["wind"])
	    wind_data = json.loads(response.content)
	    solar_wind = process_solar_wind_data(wind_data)
	    
	    space_weather_data.update({
	        "SWX_SWIND_SPEED": {
	            "value": solar_wind["speed"]["value"],
	            "fill": solar_wind["speed"]["color"],
	            "expires": 0
	        },
	        "SWX_SWIND_DENSITY": {
	            "value": solar_wind["density"]["value"],
	            "fill": solar_wind["density"]["color"],
	            "expires": 0
	        },
	        "SWX_SWIND_TEMP": {
	            "value": solar_wind["temp"]["value"],
	            "fill": solar_wind["temp"]["color"],
	            "expires": 0
	        }
	    })

	    # Fetch and process Kp index
	    response = requests.get(urls["kp"])
	    kp_data = json.loads(response.content)
	    kp_value = float(kp_data[-1][1])
	    kp_color = "#10e310"  # default green
	    if kp_value > 5:
	        kp_color = "#f56b6b"  # red
	    elif kp_value >= 4:
	        kp_color = "#ffec00"  # yellow

	    space_weather_data["SWX_KPDATA"] = {
	        "value": kp_value,
	        "fill": kp_color,
	        "expires": 0
	    }

	    # Fetch and process Bz data
	    response = requests.get(urls["bz"])
	    bz_data = json.loads(response.content)
	    bz_value = float(bz_data[-1][3])
	    bz_color = "#10e310"  # default green
	    if bz_value <= -15:
	        bz_color = "#f56b6b"  # red
	    elif bz_value <= -6:
	        bz_color = "#ffec00"  # yellow

	    space_weather_data["SWX_BZDATA"] = {
	        "value": bz_value,
	        "fill": bz_color,
	        "expires": 0
	    }

	    # Save data to file
	    s.saveExtraData(params["filename"], space_weather_data)
	    result = f"Space weather data successfully written to {params['filename']}"
	    s.log(1, f"INFO: {result}")
	    s.setLastRun(module)

	except Exception as e:
	    eType, eObject, eTraceback = sys.exc_info()
	    result = f"Module spaceweather failed on line {eTraceback.tb_lineno} - {e}"
	    s.log(0, f"ERROR: {result}")

	return result

def spaceweather_cleanup():
	"""Cleanup function for the module"""
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "spaceweather.json"
	        },
	        "env": {}
	    }
	}
	s.cleanupModule(moduleData)
