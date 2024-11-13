import allsky_shared as s
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
    "version": "v1.0.0",
    "testable": "true",
    "events": [
        "periodic"
    ],
    "experimental": "false",    
    "arguments": {
        "extradatafilename": "solarsystem.json",
        "moonEnabled": "false",
        "sunEnabled": "false",
        "planetMercuryEnabled": "false",
        "planetVenusEnabled": "false",
        "planetMarsEnabled": "false",
        "planetJupiterEnabled": "false",
        "planetSaturnEnabled": "false",
        "planetUranusEnabled": "false",
        "planetNeptuneEnabled": "false",
        "planetPlutoEnabled": "false",
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
        ]
    }
}

class ALLSKYSOLARSYSTEM:
    _overlayFolder = None
    _overlayTLEFolder = None
    _tmpFolder = None
    _enableSkyfield = False
    _debug = False
    _params = {}
    _observerLat = 0
    _observerLon = 0
    _extraData = {}
    _extradatafilename = ''

    def __init__(self, params):
        self._params = params
        s.setupForCommandLine()
        self._overlayFolder = s.getEnvironmentVariable('ALLSKY_OVERLAY')
        self._tmpFolder = os.path.join(self._overlayFolder, 'tmp')
        
        self._overlayTLEFolder = os.path.join(self._tmpFolder , 'tle')
                
        self._enableSkyfield = True
        try:
            s.log(0, 'INFO: Downloading ephemeris data', sendToAllsky=False)
            Loader(self._tmpFolder, verbose=False)
            self._eph = load('de421.bsp')
        except Exception as err:
            s.log(0, f'ERROR: Unable to download de421.bsp: {err}', sendToAllsky=True)
            self._enableSkyfield = False
        self._observerLat = s.getSetting('latitude')
        self._observerLon = s.getSetting('longitude')
        self._debug = True
        
        s.validateExtraFileName(params, 'solarsystem', 'extradatafilename')
        self._extradatafilename = params['extradatafilename']
        
        self._visible = {}

    def _initialiseExtraData(self):
        self._extraData = {}

    def _saveExtraData(self):
        s.log(4, f'INFO: Saving {self._extradatafilename}')
        #s.var_dump(self._extraData)
        s.saveExtraData(self._extradatafilename, self._extraData)

    def _calculateMoon(self):
        try:
            if self._enableSkyfield:
                lat = radians(s.convertLatLon(self._observerLat))
                lon = radians(s.convertLatLon(self._observerLon))

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

                lunation=(observer.date-pnm)/(nnm-pnm)
                symbol=lunation*26
                if symbol < 0.2 or symbol > 25.8 :
                    symbol = '1'  # new moon
                else:
                    symbol = chr(ord('A')+int(symbol+0.5)-1)

                az_temp = str(moon.az).split(":")
                moon_azimuth = az_temp[0]
                moon_elevation = str(round(degrees(moon.alt),2))
                moon_illumination = str(round(moon.phase, 2))
                moon_phase_symbol  = symbol

                if moon.alt > 0:
                    moonrise = observer.previous_rising(moon)
                else:
                    moonrise = observer.next_rising(moon)

                moonset = observer.next_setting(moon)

                moonrise_locale_full = ephem.localtime(moonrise).strftime('%c')
                moonrise_locale_date = ephem.localtime(moonrise).strftime('%x')
                moonrise_locale_time = ephem.localtime(moonrise).strftime('%X')
                moonset_locale_full = ephem.localtime(moonset).strftime('%c')
                moonset_locale_date = ephem.localtime(moonset).strftime('%x')
                moonset_locale_time = ephem.localtime(moonset).strftime('%X')

                next_full_moon = ephem.next_full_moon(observer.date)
                next_new_moon = ephem.next_new_moon(next_full_moon)

                next_full_moon_locale = ephem.localtime(next_full_moon).strftime('%c')
                next_full_moon_date = ephem.localtime(next_full_moon).strftime('%x')
                next_full_moon_time = ephem.localtime(next_full_moon).strftime('%X')
                next_new_moon_locale = ephem.localtime(next_new_moon).strftime('%c')
                next_new_moon_date = ephem.localtime(next_new_moon).strftime('%x')
                next_new_moon_time = ephem.localtime(next_new_moon).strftime('%X')
                
                self._extraData['AS_MOON_AZIMUTH'] = moon_azimuth
                self._extraData['AS_MOON_ELEVATION'] = moon_elevation
                self._extraData['AS_MOON_ILLUMINATION'] = moon_illumination
                self._extraData['AS_MOON_SYMBOL'] = moon_phase_symbol
                
                self._extraData['AS_MOON_RISE_FULL'] = moonrise_locale_full
                self._extraData['AS_MOON_RISE_DATE'] = moonrise_locale_date
                self._extraData['AS_MOON_RISE_TIME'] = moonrise_locale_time

                self._extraData['AS_MOON_SET_FULL'] = moonset_locale_full
                self._extraData['AS_MOON_SET_DATE'] = moonset_locale_date
                self._extraData['AS_MOON_SET_TIME'] = moonset_locale_time

                self._extraData['AS_MOON_NEXT_FULL_FULL'] = next_full_moon_locale
                self._extraData['AS_MOON_NEXT_FULL_DATE'] = next_full_moon_date
                self._extraData['AS_MOON_NEXT_FULL_TIME'] = next_full_moon_time
                
                self._extraData['AS_MOON_NEXT_NEW_FULL'] = next_new_moon_locale
                self._extraData['AS_MOON_NEXT_NEW_DATE'] = next_new_moon_date
                self._extraData['AS_MOON_NEXT_NEW_TIME'] = next_new_moon_time
                

            else:
                s.log(0,'ERROR: Moon enabled but cannot use due to prior error initialising skyfield.', sendToAllsky=True)

        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f'ERROR: _calculateMoon failed on line {eTraceback.tb_lineno} - {e}', sendToAllsky=True)
        return True    

    def _getSunTimes(self, location, date):
        sunData = sun(location, date=date)
        az = azimuth(location, date)
        el = elevation(location, date)
        sunData['azimuth'] = az
        sunData['elevation'] = el
        return sunData

    def _getTimeZone(self):
        try:
            file = open('/etc/timezone', 'r')
            tz = file.readline()
            tz = tz.strip()
            file.close()
        except:
            tz = "Europe/London"

        return tz, timezone(tz)

    def _calculateSun(self):
        try:

            lat = s.convertLatLon(self._observerLat)
            lon = s.convertLatLon(self._observerLon)

            tzName, tz = self._getTimeZone()
            location = Observer(lat, lon, 0)

            today = datetime.now(tz)
            tomorrow = today + timedelta(days = 1)
            yesterday = today + timedelta(days = -1)

            yesterdaySunData = self._getSunTimes(location, yesterday)
            todaySunData = self._getSunTimes(location, today)
            tomorrowSunData = self._getSunTimes(location, tomorrow)

            if s.TOD == 'day':
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

            format = s.getSetting("timeformat")
            
            self._extraData['AS_SUN_DAWN'] = dawn.strftime(format)
            self._extraData['AS_SUN_SUNRISE'] = sunrise.strftime(format)
            self._extraData['AS_SUN_NOON'] = noon.strftime(format)
            self._extraData['AS_SUN_SUNSET'] = sunset.strftime(format)
            self._extraData['AS_SUN_DUSK'] = dusk.strftime(format)
            
            self._extraData['AS_SUN_AZIMUTH'] = str(int(todaySunData["azimuth"]))
            self._extraData['AS_SUN_ELEVATION'] = str(int(todaySunData["elevation"]))
        except Exception as e:
            eType, eObject, eTraceback = sys.exc_info()
            s.log(0, f'ERROR: _initialiseSun failed on line {eTraceback.tb_lineno} - {e}', sendToAllsky=True)

        return True

    def _set_planet_data(self, planet, observer_location, planet_name):

        s.log(4, f'INFO: Calculating position of {planet_name}')
        timescale = load.timescale()
        time_now = timescale.now()

        astrometric = observer_location.at(time_now).observe(planet).apparent()
        alt, az, distance = astrometric.altaz()
        
        alt_dms = alt.dms()
        az_dms = az.dms()
        
        astrometric = self._eph['earth'].at(time_now).observe(planet)
        ra, dec, distance = astrometric.radec()
        
        self._extraData[f'AS_{planet_name}_ALT'] = str(alt)
        self._extraData[f'AS_{planet_name}_ALTD'] = str(int(alt_dms[0]))
        self._extraData[f'AS_{planet_name}_ALTM'] = str(int(abs(alt_dms[1])))
        self._extraData[f'AS_{planet_name}_ALTS'] = str(int(abs(alt_dms[2])))

        self._extraData[f'AS_{planet_name}_AZ'] = str(az)
        self._extraData[f'AS_{planet_name}_AZD'] = str(int(az_dms[0]))
        self._extraData[f'AS_{planet_name}_AZM'] = str(int(abs(az_dms[1])))
        self._extraData[f'AS_{planet_name}_AZS'] = str(int(abs(az_dms[2])))
        
        self._extraData[f'AS_{planet_name}_RA'] = str(ra)
        self._extraData[f'AS_{planet_name}_DEC'] = str(dec)

        distance_km = int(distance.km)
        distance_km_str = locale.format_string('%d', distance_km, grouping=True)
        distance_miles = int(distance_km * 0.621371)
        distance_miles_str = locale.format_string('%d', distance_miles, grouping=True)
        
        self._extraData[f'AS_{planet_name}_DISTANCE_KM'] = str(distance_km)
        self._extraData[f'AS_{planet_name}_DISTANCE_KM_FORMATTED'] = str(distance_km_str)
        self._extraData[f'AS_{planet_name}_DISTANCE_MILES'] = str(distance_miles)
        self._extraData[f'AS_{planet_name}_DISTANCE_MILES_FORMATTED'] = str(distance_miles_str)
                
        if alt.degrees > 15:
            self._extraData[f'AS_{planet_name}_VISIBLE'] = 'Yes'           
        else:
            self._extraData[f'AS_{planet_name}_VISIBLE'] = 'No'

    def _calculate_planets(self):

        earth = self._eph['earth']
        latitude = s.convertLatLon(self._observerLat)
        longitude = s.convertLatLon(self._observerLon)
        observer_location = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)
        
        if self._params['planetMercuryEnabled']:
            self._set_planet_data(self._eph['MERCURY BARYCENTER'], observer_location, 'Mercury')

        if self._params['planetVenusEnabled']:
            self._set_planet_data(self._eph['VENUS BARYCENTER'], observer_location, 'Venus')

        if self._params['planetMarsEnabled']:
            self._set_planet_data(self._eph['MARS BARYCENTER'], observer_location, 'Mars')

        if self._params['planetJupiterEnabled']:
            self._set_planet_data(self._eph['JUPITER BARYCENTER'], observer_location, 'Jupiter')

        if self._params['planetSaturnEnabled']:
            self._set_planet_data(self._eph['SATURN BARYCENTER'], observer_location, 'Saturn')

        if self._params['planetUranusEnabled']:
            self._set_planet_data(self._eph['URANUS BARYCENTER'], observer_location, 'Uranus')                    

        if self._params['planetNeptuneEnabled']:
            self._set_planet_data(self._eph['NEPTUNE BARYCENTER'], observer_location, 'Neptune')                    

        if self._params['planetPlutoEnabled']:
            self._set_planet_data(self._eph['PLUTO BARYCENTER'], observer_location, 'Pluto')  

    def _fetch_tle_from_celestrak(self, data_key, verify=True):
        s.log(4, f'INFO: Loading Satellite {data_key}', True)

        data_filename = os.path.join(self._overlayTLEFolder , data_key + '.tle')
        s.createTempDir(self._overlayTLEFolder)

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

            s.log(4, ' TLE file over 2 days old so downloaded')

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
            s.log(4, ' TLE loaded from cache')

        return tle_data

    def _calcSatellites(self):
        satellites = self._params['tles']
        satellites = satellites.strip()
        
        if satellites != '':
            satelliteArray = list(map(str.strip, satellites.split(',')))
            for tle_key in satelliteArray:
                tle_data = self._fetch_tle_from_celestrak(tle_key)
                for _, tle in tle_data.items():
                    self._calculate_satellite(tle)
        
      
            self._visible = dict(sorted(self._visible.items(), key=lambda item: item[1]['elevation'], reverse=True))
            counter = 1
            for key, item in self._visible.items():
                prefix = f'VISIBLE{counter}_'
                self._add_satellite_to_extra_data(item['norad_id'], item['alt'], item['az'], item['distance'], item['name'], prefix)
                counter = counter + 1

    def _calculate_satellite(self, tle):

        try:
            sat_min_elevation = int(self._params['sat_min_elevation'])
        except:
            sat_min_elevation = 15
        
        latitude = s.convertLatLon(self._observerLat)
        longitude = s.convertLatLon(self._observerLon)
        altitude = 0
        
        observer_location = Topos(latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=altitude)

        time_scale = load.timescale()
        sat_time = time_scale.now()

        satellite = EarthSatellite(tle['line2'], tle['line3'], tle['line1'], time_scale)
        s.log(4, f' Calculating {satellite.name}')
        norad_id = str(satellite.model.satnum)

        difference = satellite - observer_location

        topocentric = difference.at(sat_time)
        alt, az, distance = topocentric.altaz()
        sunlit = satellite.at(sat_time).is_sunlit(self._eph)
                
        self._add_satellite_to_extra_data(norad_id, alt, az, distance, satellite.name)

        if alt.degrees > sat_min_elevation and sunlit:
            self._extraData['AS_' + norad_id + 'VISIBLE'] = 'Yes'
            self._visible[norad_id] = {
                'norad_id': norad_id,
                'name': satellite.name,
                'elevation': alt.degrees,
                'alt' : alt,
                'az': az,
                'distance': distance
            }
        else:
            self._extraData['AS_' + norad_id + 'VISIBLE'] = 'No'

        return True

    def _add_satellite_to_extra_data(self, norad_id, alt, az, distance, name, prefix=''):
        alt_dms = alt.dms()
        az_dms = az.dms()
        self._extraData[f'AS_{prefix}{norad_id}_NAME'] = name
        self._extraData[f'AS_{prefix}{norad_id}_ALT'] = str(alt)
        self._extraData[f'AS_{prefix}{norad_id}_ALTD'] = str(int(alt_dms[0]))
        self._extraData[f'AS_{prefix}{norad_id}_ALTM'] = str(int(abs(alt_dms[1])))
        self._extraData[f'AS_{prefix}{norad_id}_ALTS'] = str(int(abs(alt_dms[2])))

        self._extraData[f'AS_{prefix}{norad_id}_AZ'] = str(az)
        self._extraData[f'AS_{prefix}{norad_id}_AZD'] = str(int(az_dms[0]))
        self._extraData[f'AS_{prefix}{norad_id}_AZM'] = str(int(abs(az_dms[1])))
        self._extraData[f'AS_{prefix}{norad_id}_AZS'] = str(int(abs(az_dms[2])))
        self._extraData[f'AS_{prefix}{norad_id}_DISTANCE'] = str(distance.km)

    def run(self):
        # check Skyfield initilaised ok
        self._initialiseExtraData()

        if self._params['moonEnabled']:
            self._calculateMoon()

        if self._params['sunEnabled']:
            self._calculateSun()

        self._calculate_planets()
        
        self._calcSatellites()

        self._saveExtraData()
        
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
    s.cleanupModule(moduleData)