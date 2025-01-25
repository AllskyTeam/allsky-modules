#TODO: Events
import allsky_shared as shared
import os
import time
import sys
import ephem
import requests
import locale

from math import radians
from math import degrees
from datetime import datetime, timedelta, date

from skyfield.api import EarthSatellite, load, wgs84, Loader, Topos
from skyfield.api import N, S, E, W
from skyfield import almanac
from pytz import timezone

from astral.sun import sun, azimuth, elevation, night
from astral import LocationInfo, Observer

metaData = {
	"name": "AllSky Solar System",
	"description": "Produce data for Solar System objects",
	"module": "allsky_solarsystem",
	"version": "v1.0.1",
	"testable": "true",
	"centersettings": "false",    
	"events": [
	    "periodic",
	    "day",
	    "night"
	],
	"experimental": "false",
	"extradata": {   
	    "values": {
	        "AS_MOON_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The Moons azimuth"
	        },
	        "AS_MOON_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The Moons elevation"
	        },
	        "AS_MOON_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is the Moon visible"
	        },
	        "AS_MOON_ILLUMINATION": {
	            "group": "Solar System",
	            "type": "float",
	            "description": "The Moons illumination %"
	        },
	        "AS_MOON_SYMBOL": {
	            "group": "Solar System",
	            "type": "string",
	            "description": "The moon phase symbol (use moon ttf)"
	        },
	        "AS_MOON_RISE_TIME": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The moon rise timestamp"
	        },
	        "AS_MOON_SET_TIME": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The moon set timestamp"
	        },
	        "AS_MOON_NEW_TIME": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The next new moon timestamp"
	        },
	        "AS_MOON_FULL_TIME": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The next full moon timestamp"
	        },
	        "AS_SUN_DAWN": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The timestamp for Dawn"
	        },
	        "AS_SUN_SUNRISE": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The timestamp for Sun Rise"
	        },
	        "AS_SUN_NOON": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The timestamp for Noon"
	        },
	        "AS_SUN_SUNSET": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The timestamp for Sun Set"
	        },
	        "AS_SUN_DUSK": {
	            "group": "Solar System",
	            "type": "timestamp",
	            "description": "The timestamp for Dusk"
	        },
	        "AS_SUN_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The azimuth of the Sun"
	        },
	        "AS_SUN_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of the Sun"
	        },
	        "AS_MERCURY_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Mercury"
	        },            
	        "AS_MERCURY_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Mercury"
	        },
	        "AS_MERCURY_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mercury visible"
	        },
	        "AS_VENUS_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Venus"
	        },
	        "AS_VENUS_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Venus"
	        },
	        "AS_VENUS_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Venus visible"
	        },
	        "AS_MARS_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Mars"
	        },
	        "AS_MARS_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Mars"
	        },
	        "AS_MARS_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars visible"
	        },
	        "AS_JUPITER_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Jupiter"
	        },
	        "AS_JUPITER_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Jupiter"
	        },
	        "AS_JUPITER_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars Jupiter"
	        },
	        "AS_SATURN_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Saturn"
	        },
	        "AS_SATURN_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Saturn"
	        },
	        "AS_SATURN_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars Saturn"
	        },
	        "AS_URANUS_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Uranus"
	        },
	        "AS_URANUS_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Uranus"
	        },
	        "AS_URANUS_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars Uranus"
	        },
	        "AS_NEPTUNE_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Neptune"
	        },
	        "AS_NEPTUNE_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Neptune"
	        },
	        "AS_NEPTUNE_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars Neptune"
	        },
	        "AS_PLUTO_ELEVATION": {
	            "group": "Solar System",
	            "type": "elevation",
	            "description": "The elevation of Pluto"
	        },
	        "AS_PLUTO_AZIMUTH": {
	            "group": "Solar System",
	            "type": "azimuth",
	            "description": "The AZIMUTH of Pluto"
	        },
	        "AS_PLUTO_VISIBLE": {
	            "group": "Solar System",
	            "type": "bool",
	            "description": "Is Mars Pluto"
	        }
	    }
	},    
	"arguments": {
	    "extradatafilename": "solarsystem.json",
	    "moonEnabled": "false",
	    "moonElevation": "5",
	    "sunEnabled": "false",
	    "planetMercuryEnabled": "false",
	    "planetVenusEnabled": "false",
	    "planetMarsEnabled": "false",
	    "planetJupiterEnabled": "false",
	    "planetSaturnEnabled": "false",
	    "planetUranusEnabled": "false",
	    "planetNeptuneEnabled": "false",
	    "planetPlutoEnabled": "false",
	    "planetElevation": "5",
	    "tles": "",
	    "sat_min_elevation": 15
	},
	"argumentdetails": {
	    "extradatafilename": {
	        "required": "true",
	        "description": "Extra Data Filename",
	        "tab": "General",
	        "help": "The name of the file to create with the solar system data for the overlay manager"
	    },
	    "moonEnabled": {
	        "required": "false",
	        "description": "Enable the Moon",
	        "help": "Enable calculation of Moon Data",
	        "tab": "Moon",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "moonElevation": {
	        "required": "false",
	        "description": "Minimum elevation",
	        "help": "Above this value the Moon will be considered visible",
	        "tab": "Moon",
	        "type": {
	            "fieldtype": "spinner",
	            "min": -10,
	            "max": 90,
	            "step": 1
	        }           
	    },        
	    "sunEnabled": {
	        "required": "false",
	        "description": "Enable the Sun",
	        "help": "Enable calculation of Sun Data",
	        "tab": "Sun",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetMercuryEnabled": {
	        "required": "false",
	        "description": "Enable Mercury",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetVenusEnabled": {
	        "required": "false",
	        "description": "Enable Venus",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetMarsEnabled": {
	        "required": "false",
	        "description": "Enable Mars",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetJupiterEnabled": {
	        "required": "false",
	        "description": "Enable Jupiter",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetSaturnEnabled": {
	        "required": "false",
	        "description": "Enable Saturn",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetUranusEnabled": {
	        "required": "false",
	        "description": "Enable Uranus",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetNeptuneEnabled": {
	        "required": "false",
	        "description": "Enable Neptune",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetPlutoEnabled": {
	        "required": "false",
	        "description": "Enable Pluto",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    },
	    "planetElevation": {
	        "required": "false",
	        "description": "Minimum elevation",
	        "help": "Above this value the planets will be considered visible",
	        "tab": "Planets",
	        "type": {
	            "fieldtype": "spinner",
	            "min": -10,
	            "max": 90,
	            "step": 1
	        }           
	    },        
	    "tles": {
	        "required": "false",
	        "description": "Norad Id's",
	        "help": "List of NORAD Id's to calculate satellite positions for, satellite Id's can be found on the <a href=\"https://celestrak.org/satcat/search.php\" target=\"_blank\">Celestrak</a> website. See the documentaiton for more details",
	        "tab": "Satellites"
	    },
	    "sat_min_elevation" : {
	        "required": "true",
	        "description": "Minimum Elevation",
	        "help": "Satellites will only be classed as visible if above this elevation, in degrees and sunlit",
	        "tab": "Satellites",                        
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 90,
	            "step": 1
	        }
	    }         
	},
	"enabled": "false",
	"businfo": [
	],
	"changelog": {
	    "v1.0.0" : [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Initial Release"
	        }
	    ],
	    "v1.0.1" : [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Updates for new variables system"
	        }
	    ]     
	}
}

class ALLSKYSOLARSYSTEM:
	__overlay_folder = None
	__overlay_tle_folder = None
	__tmp_folder = None
	__enable_skyfield = False
	__params = {}
	__observer_lat = 0
	__observer_lon = 0
	__extra_data = {}
	__custom_fields = {}
	__extra_data_filename = ''

	def __init__(self, params):
		self.__params = params
		shared.setupForCommandLine()
		self.__overlay_folder = shared.getEnvironmentVariable('ALLSKY_OVERLAY')
		self.__tmp_folder = os.path.join(self.__overlay_folder, 'tmp')
		self.__overlay_tle_folder = os.path.join(self.__tmp_folder , 'tle')
		self.__enable_skyfield = True
		try:
			ephemeris_path = os.path.join(self.__tmp_folder, 'de421.bsp')
			skyfield_loader = Loader(self.__tmp_folder, verbose=False)
			if (skyfield_loader.exists(ephemeris_path)):
				shared.log(4, 'INFO: Using cached ephemeris data')
			else:
				shared.log(4, 'INFO: Downloading ephemeris data')
			self._eph = skyfield_loader('de421.bsp')
		except Exception as err:
			shared.log(0, f'ERROR: Unable to download de421.bsp: {err}')
			self.__enable_skyfield = False
		self.__observer_lat = shared.getSetting('latitude')
		self.__observer_lon = shared.getSetting('longitude')
		
		shared.validateExtraFileName(params, 'solarsystem', 'extradatafilename')
		self.__extra_data_filename = params['extradatafilename']
		
		self._visible = {}

	def __initialiseExtraData(self):
		self.__extra_data = {}

	def __saveExtraData(self):
		shared.log(4, f'INFO: Saving {self.__extra_data_filename}')
		shared.saveExtraData(self.__extra_data_filename, self.__extra_data, metaData["module"], metaData["extradata"], self.__custom_fields)

	def __convert_ephem_date(self, ephem_date):
		date_tuple = ephem_date.tuple()

		date_timestamp = datetime(date_tuple[0], date_tuple[1], date_tuple[2], date_tuple[3], date_tuple[4], int(date_tuple[5]))
		return date_timestamp

	def __calculateMoon(self):
		try:
			if self.__enable_skyfield:
				lat = radians(shared.convertLatLon(self.__observer_lat))
				lon = radians(shared.convertLatLon(self.__observer_lon))

				now = time.time()
				utc_offset = (datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)).total_seconds()

				observer = ephem.Observer()
				observer.lat = lat
				observer.long = lon
				moon = ephem.Moon()
				obs_date = datetime.now() - timedelta(seconds=utc_offset)
				observer.date = obs_date
				moon.compute(observer)

				nnm = ephem.next_new_moon(observer.date)
				pnm = ephem.previous_new_moon(observer.date)

				lunation = (observer.date-pnm)/(nnm-pnm)
				symbol = lunation*26
				if symbol < 0.2 or symbol > 25.8:
					symbol = '1'  # new moon
				else:
					symbol = chr(ord('A')+int(symbol+0.5)-1)

				az_temp = str(moon.az).split(":")
				moon_azimuth = az_temp[0]
				moon_elevation = round(degrees(moon.alt),2)
				moon_illumination = round(moon.phase, 2)
				moon_phase_symbol = symbol

				if moon.alt > 0:
					moon_rise = observer.previous_rising(moon)
				else:
					moon_rise = observer.next_rising(moon)

				moon_rise_timestamp = self.__convert_ephem_date(moon_rise)
				moon_set = observer.next_setting(moon)
				moon_set_timestamp = self.__convert_ephem_date(moon_set)

				next_full_moon = ephem.next_full_moon(observer.date)
				next_new_moon = ephem.next_new_moon(next_full_moon)

				moon_next_full_timestamp = self.__convert_ephem_date(next_full_moon)
				moon_next_new_timestamp = self.__convert_ephem_date(next_new_moon)

				self.__extra_data['AS_MOON_AZIMUTH'] = moon_azimuth
				self.__extra_data['AS_MOON_ELEVATION'] = moon_elevation
				self.__extra_data['AS_MOON_ILLUMINATION'] = moon_illumination
				self.__extra_data['AS_MOON_SYMBOL'] = moon_phase_symbol

				self.__extra_data['AS_MOON_RISE_TIME'] = moon_rise_timestamp.timestamp()
				self.__extra_data['AS_MOON_SET_TIME'] = moon_set_timestamp.timestamp()
				self.__extra_data['AS_MOON_NEW_TIME'] = moon_next_new_timestamp.timestamp()
				self.__extra_data['AS_MOON_FULL_TIME'] = moon_next_full_timestamp.timestamp()

				try:
					moon_min_elevation = int(self.__params['moonElevation'])
				except Exception:
					moon_min_elevation = 0

				if moon_elevation > moon_min_elevation:
					self.__extra_data['AS_MOON_VISIBLE'] = 'Yes'
				else:
					self.__extra_data['AS_MOON_VISIBLE'] = 'No'

				shared.log(4, 'INFO: Moon data calculated')
			else:
				shared.log(0, 'ERROR: Moon enabled but cannot use due to prior error initialising skyfield.')

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f'ERROR: __calculateMoon failed on line {eTraceback.tb_lineno} - {e}')
		return True 

	def __getSunTimes(self, location, date):
		sunData = None
		try:
			sunData = sun(location, date=date)
			az = azimuth(location, date)
			el = elevation(location, date)
			sunData['azimuth'] = az
			sunData['elevation'] = el
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f'ERROR: __getSunTimes failed on line {eTraceback.tb_lineno} - {e}')
		return sunData

	def __getTimeZone(self):
		try:
			file = open('/etc/timezone', 'r')
			tz = file.readline()
			tz = tz.strip()
			file.close()
		except:
			tz = "Europe/London"

		return tz, timezone(tz)

	def __calculateSun(self):
		try:

			lat = shared.convertLatLon(self.__observer_lat)
			lon = shared.convertLatLon(self.__observer_lon)

			tzName, tz = self.__getTimeZone()
			location = Observer(lat, lon, 0)

			today = datetime.now(tz)
			tomorrow = today + timedelta(days = 1)
			yesterday = today + timedelta(days = -1)

			yesterdaySunData = self.__getSunTimes(location, yesterday)
			todaySunData = self.__getSunTimes(location, today)
			tomorrowSunData = self.__getSunTimes(location, tomorrow)

			if shared.TOD == 'day':
				dawn = todaySunData["dawn"]
				sunrise = todaySunData["sunrise"]
				noon = todaySunData["noon"]
				sunset = todaySunData["sunset"]
				dusk = todaySunData["dusk"]
			else:
				now = datetime.now(tz)
				if now.hour > 0 and now < todaySunData["dawn"]:
					dawn = todaySunData["dawn"]
					sunrise = todaySunData["sunrise"]
					noon = todaySunData["noon"]
					sunset = yesterdaySunData["sunset"]
					dusk = yesterdaySunData["dusk"]
				else:
					dawn = tomorrowSunData["dawn"]
					sunrise = tomorrowSunData["sunrise"]
					noon = tomorrowSunData["noon"]
					sunset = todaySunData["sunset"]
					dusk = todaySunData["dusk"]

			self.__extra_data['AS_SUN_DAWN'] = dawn.timestamp()
			self.__extra_data['AS_SUN_SUNRISE'] = sunrise.timestamp()
			self.__extra_data['AS_SUN_NOON'] = noon.timestamp()
			self.__extra_data['AS_SUN_SUNSET'] = sunset.timestamp()
			self.__extra_data['AS_SUN_DUSK'] = dusk.timestamp()
			
			self.__extra_data['AS_SUN_AZIMUTH'] = str(int(todaySunData["azimuth"]))
			self.__extra_data['AS_SUN_ELEVATION'] = str(int(todaySunData["elevation"]))
			
			shared.log(4, 'INFO: Sun data calculated')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f'ERROR: __calculateSun failed on line {eTraceback.tb_lineno} - {e}')

		return True

	def __set_planet_data(self, planet, observer_location, planet_name):
		try:
			shared.log(4, f'INFO: Calculating position of {planet_name}')
			timescale = load.timescale()
			time_now = timescale.now()

			astrometric = observer_location.at(time_now).observe(planet).apparent()
			alt, az, distance = astrometric.altaz()

			alt_dms = alt.dms()
			az_dms = az.dms()
			planet_key = planet_name.upper()
			self.__extra_data[f'AS_{planet_key}_ELEVATION'] = int(alt_dms[0])
			self.__extra_data[f'AS_{planet_key}_AZIMUTH'] = int(az_dms[0])

			try:
				planet_min_elevation = int(self.__params['planetElevation'])
			except Exception:
				planet_min_elevation = 0
						
			if alt.degrees > planet_min_elevation:
				self.__extra_data[f'AS_{planet_key}_VISIBLE'] = 'Yes'
			else:
				self.__extra_data[f'AS_{planet_key}_VISIBLE'] = 'No'
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __set_planet_data failed on line {eTraceback.tb_lineno} - {e}")
   
	def __calculate_planets(self):
		try:
			earth = self._eph['earth']
			latitude = shared.convertLatLon(self.__observer_lat)
			longitude = shared.convertLatLon(self.__observer_lon)
			observer_location = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)
			
			if self.__params['planetMercuryEnabled']:
				self.__set_planet_data(self._eph['MERCURY BARYCENTER'], observer_location, 'Mercury')

			if self.__params['planetVenusEnabled']:
				self.__set_planet_data(self._eph['VENUS BARYCENTER'], observer_location, 'Venus')

			if self.__params['planetMarsEnabled']:
				self.__set_planet_data(self._eph['MARS BARYCENTER'], observer_location, 'Mars')

			if self.__params['planetJupiterEnabled']:
				self.__set_planet_data(self._eph['JUPITER BARYCENTER'], observer_location, 'Jupiter')

			if self.__params['planetSaturnEnabled']:
				self.__set_planet_data(self._eph['SATURN BARYCENTER'], observer_location, 'Saturn')

			if self.__params['planetUranusEnabled']:
				self.__set_planet_data(self._eph['URANUS BARYCENTER'], observer_location, 'Uranus')                    

			if self.__params['planetNeptuneEnabled']:
				self.__set_planet_data(self._eph['NEPTUNE BARYCENTER'], observer_location, 'Neptune')                    

			if self.__params['planetPlutoEnabled']:
				self.__set_planet_data(self._eph['PLUTO BARYCENTER'], observer_location, 'Pluto')  

			shared.log(4, 'INFO: Planet data calculated')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __calculate_planets failed on line {eTraceback.tb_lineno} - {e}")
   
	def __fetch_tle_from_celestrak(self, data_key, verify=True):
		tle_data = {}
		try:
		
			shared.log(4, f'INFO: Loading Satellite {data_key}', True)

			data_filename = os.path.join(self.__overlay_tle_folder , data_key + '.tle')
			shared.createTempDir(self.__overlay_tle_folder)

			if os.path.exists(data_filename):
				file_modified_time = int(os.path.getmtime(data_filename))
				file_age = int(time.time()) - file_modified_time
				file_age = file_age / 60 / 60 / 24
			else:
				file_age = 9999

			if file_age > 2:
				if data_key[0].isdigit():
					response = requests.get(f'https://www.celestrak.com/NORAD/elements/gp.php?CATNR={data_key}', timeout=5)
					response.raise_for_status()

					if response.text == 'No GP data found':
						raise LookupError

					tle_data = response.text.split('\r\n')

					umask = os.umask(0)
					with open(os.open(data_filename, os.O_CREAT | os.O_WRONLY, 0o777), 'w', encoding='utf-8') as outfile:
						outfile.write(tle_data[0].strip() + os.linesep)
						outfile.write(tle_data[1].strip() + os.linesep)
						outfile.write(tle_data[2].strip() + os.linesep)
					os.umask(umask)
				else:

					url = f'https://celestrak.org/NORAD/elements/gp.php?GROUP={data_key}&FORMAT=tle'
					try:
						response = requests.get(url, timeout=10)
						if response.status_code == 200:
							tle_data = response.content.decode('utf-8').split('\r\n')

						with open(os.open(data_filename, os.O_CREAT | os.O_WRONLY, 0o777), 'w', encoding='utf-8') as outfile:
							for line in tle_data:
								outfile.write(line.strip() + os.linesep)
					except Exception as data_exception:
						exception_type, exception_object, exception_traceback = sys.exc_info()
						result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'

				shared.log(4, ' TLE file over 2 days old so downloaded')

			tle_data = {}
			if data_key[0].isdigit():
				with open(data_filename, encoding="utf-8") as file:
					lines = [next(file, None) for _ in range(3)]
					tle_data[0] = {
						'line1': lines[0].replace(os.linesep,''),
						'line2': lines[1].replace(os.linesep,''),
						'line3': lines[2].replace(os.linesep,'')
					}
			else:
				counter = 0
				with open(data_filename, encoding="utf-8") as file:
					while True:
						lines = [next(file, None) for _ in range(3)]
						if not any(lines):
							break

						if lines[0] != os.linesep and lines[0] is not None:
							tle_data[counter] = {
								'line1': lines[0].replace(os.linesep,''),
								'line2': lines[1].replace(os.linesep,''),
								'line3': lines[2].replace(os.linesep,'')
							}
						counter = counter + 1
				shared.log(4, ' TLE loaded from cache')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __fetch_tle_from_celestrak failed on line {eTraceback.tb_lineno} - {e}")
		return tle_data

	def __calcSatellites(self):
		try:
			satellites = self.__params['tles']
			satellites = satellites.strip()
			
			if satellites != '':
				satelliteArray = list(map(str.strip, satellites.split(',')))
				for tle_key in satelliteArray:
					tle_data = self.__fetch_tle_from_celestrak(tle_key)
					for _, tle in tle_data.items():
						self.__calculate_satellite(tle)
			
			
				self._visible = dict(sorted(self._visible.items(), key=lambda item: item[1]['elevation'], reverse=True))
				counter = 1
				for key, item in self._visible.items():
					prefix = f'VISIBLE{counter}_'
					self.__add_satellite_to_extra_data(item['norad_id'], item['alt'], item['az'], item['distance'], item['name'], True, prefix)
					counter = counter + 1
		except Exception as e:     
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __calcSatellites failed on line {eTraceback.tb_lineno} - {e}")    

	def __calculate_satellite(self, tle):
		try:
			try:
				sat_min_elevation = int(self.__params['sat_min_elevation'])
			except:
				sat_min_elevation = 15
			
			latitude = shared.convertLatLon(self.__observer_lat)
			longitude = shared.convertLatLon(self.__observer_lon)
			altitude = 0
			
			observer_location = Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=altitude)

			time_scale = load.timescale()
			sat_time = time_scale.now()

			satellite = EarthSatellite(tle['line2'], tle['line3'], tle['line1'], time_scale)
			shared.log(4, f' Calculating {satellite.name}')
			norad_id = str(satellite.model.satnum)

			difference = satellite - observer_location

			topocentric = difference.at(sat_time)
			alt, az, distance = topocentric.altaz()
			sunlit = satellite.at(sat_time).is_sunlit(self._eph)

			visible = False
			if alt.degrees > sat_min_elevation and sunlit:
				visible = True
	
			self.__add_satellite_to_extra_data(norad_id, alt, az, distance, satellite.name, visible)

			if visible:
				self.__extra_data['AS_' + norad_id + 'VISIBLE'] = 'Yes'
				self._visible[norad_id] = {
					'norad_id': norad_id,
					'name': satellite.name,
					'elevation': alt.degrees,
					'alt' : alt,
					'az': az,
					'distance': distance
				}
			else:
				self.__extra_data['AS_' + norad_id + 'VISIBLE'] = 'No'

		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __calculate_satellite failed on line {eTraceback.tb_lineno} - {e}")
   
		return True

	def __add_satellite_to_extra_data(self, norad_id, alt, az, distance, name, visible, prefix=''):
		try:
			self.__custom_fields[f'AS_{prefix}{norad_id}_NAME'] = {
				'value': norad_id,
				'group': 'Solar System',
				'type': 'string',
				'description': 'Satellite name'
			}
			self.__custom_fields[f'AS_{prefix}{norad_id}_ALT'] = {
				'value': float(alt.degrees),      
				'group': 'Solar System',
				'type': 'altitude',
				'description': 'Satellite altitude'
			}
			self.__custom_fields[f'AS_{prefix}{norad_id}_AZ'] = {
				'value': float(az.degrees),
				'group': 'Solar System',
				'type': 'azimuth',
				'description': 'Satellite azimuth'
			}
			self.__custom_fields[f'AS_{prefix}{norad_id}_DISTANCE'] = {
				'value': float(distance.km),
				'group': 'Solar System',
				'type': 'integer',
				'description': 'Satellite distance in KM'
			}
			self.__custom_fields[f'AS_{prefix}{norad_id}_VISIBLE'] = {
				'value': visible,
				'group': 'Solar System',
				'type': 'bool',
				'description': 'Satellite visible'
			}
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			shared.log(0, f"ERROR: __add_satellite_to_extra_data failed on line {eTraceback.tb_lineno} - {e}")    
  
	def run(self):
		# check Skyfield initilaised ok
		self.__initialiseExtraData()

		if self.__params['moonEnabled']:
			self.__calculateMoon()

		if self.__params['sunEnabled']:
			self.__calculateSun()

		self.__calculate_planets()
		
		self.__calcSatellites()

		self.__saveExtraData()
		
		return 'OK'

def solarsystem(params, event):
	allskySolarSystem = ALLSKYSOLARSYSTEM(params)
	result = allskySolarSystem.run()

	return result

def solarsystem_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {
	            "allskysolarsystem.json"
	        },
	        "env": {}
	    }
	}
	shared.cleanupModule(moduleData)
