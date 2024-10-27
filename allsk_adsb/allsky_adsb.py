'''
allsky_adsb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import requests
import math

metaData = {
    "name": "ADSB - Aircraft tracking",
    "description": "Tracks aircraft defined in the capatured image",
    "module": "allsky_adsb",    
    "version": "v1.0.0",
    "events": [
        "periodic"
    ],
    "enabled": "false",    
    "experimental": "true",    
    "arguments":{
        "period": 60,
        "data_source": "Local",
        "local_adsb_url": "",
        "observer_altitude": 0,
        "opensky_username": "",
        "opensky_password": "",
        "opensky_lat_min": 0,
        "opensky_lon_min": 0,
        "opensky_lat_max": 0,
        "opensky_lon_max": 0,
        "airplaneslive_radius": 50
    },
    "argumentdetails": {
         "data_source" : {
            "required": "false",
            "description": "Data Source",
            "help": "The source for the adsb data",
            "tab": "Data Source",
            "type": {
                "fieldtype": "select",
                "values": "Local,OpenSky,AirplanesLive",
                "default": "Local"
            }
        },
        "observer_altitude" : {
            "required": "true",
            "description": "Altitude",
            "help": "Your altitude in metres.",
            "tab": "Data Source",                        
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 10
            }
        },
        "local_adsb_url": {
            "required": "false",
            "description": "Local ADSB Address",
            "help": "See the help for how to obtain this address",
            "tab": "Local ADSB"
        },
        "opensky_username": {
            "required": "false",
            "description": "OpenSky Username",
            "help": "Your username for the Opensky Network. See the module documentaiton for details on the api limits with and without a username",
            "tab": "OpenSky"
        },
        "opensky_password": {
            "required": "false",
            "description": "OpenSky Password",
            "help": "Your password for the Opensky Network",
            "tab": "OpenSky"
        },        
        "opensky_lat_min": {
            "required": "false",
            "description": "Min latitude",
            "help": "The minimum latitude of the bounding box. Use a site like http://bboxfinder.com/ to determine the bounding box",
            "tab": "OpenSky"
        },
        "opensky_lon_min": {
            "required": "false",
            "description": "Min longitude",
            "help": "The minimum longitude of the bounding box.",
            "tab": "OpenSky"
        },
        "opensky_lat_max": {
            "required": "false",
            "description": "Max latitude",
            "help": "The minimum latitude of the bounding box.",
            "tab": "OpenSky"
        },
        "opensky_lon_max": {
            "required": "false",
            "description": "Max longitude",
            "help": "The maximum longitude of the bounding box.",
            "tab": "OpenSky"
        },
        "airplaneslive_radius" : {
            "required": "true",
            "description": "Radius",
            "help": "Tha maximum distance to return aircraft for.",
            "tab": "Airplanes Live",                        
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 250,
                "step": 1
            }
        }
    },
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

def local_adsb(local_adsb_url, observer_location):
    ''' Retreives data from a local ADSB source
    '''
    found_aircraft = {}
    result = ''
    
    s.log(4, 'INFO: Getting data from local ADSB receiver')  
    #url = 'http://192.168.1.28:8080/data/aircraft.json'
    response = requests.get(
        local_adsb_url,
        timeout=10
    )

    if response.status_code == 200:
        aircraft_data = response.json()

        s.log(4, f'INFO: Retrieved {len(aircraft_data["aircraft"])} aircraft from local ADSB server')
        for aircraft in aircraft_data['aircraft']:

            if 'lat' in aircraft and 'flight' in aircraft:
                aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), feet_to_meters(int(aircraft['alt_baro'])))
                aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)

                found_aircraft[aircraft['hex']] = {
                    'hex': aircraft['hex'],
                    'flight': aircraft['flight'],
                    'distance': aircraft_distance,
                    'distance_miles' : meters_to_miles(aircraft_distance),
                    'altitude': get_flight_level(aircraft['alt_baro']),
                    'ias': aircraft['ias'] if 'ias' in aircraft else '',
                    'tas': aircraft['tas'] if 'tas' in aircraft else '',
                    'mach': aircraft['mach'] if 'mach' in aircraft else '',
                    'azimuth': aircraft_azimuth,
                    'elevation': aircraft_elevation                   
                }
    else:
        result = f'ERROR: Failed to retrieve data from "{local_adsb_url}". {response.status_code} - {response.text}'

    return found_aircraft, result

def airplaneslive_adsb(params, observer_location):
    ''' Retreives data from Airplanes live
    '''
    
    found_aircraft = {}
    result = ''
    
    #url = 'https://api.airplanes.live/v2/point/52.4/0.2/50'

    radius = params['airplaneslive_radius']

    s.log(4, 'INFO: Getting data from OpenSky Network')  
    url = f'https://api.airplanes.live/v2/point/{observer_location[0]}/{observer_location[1]}/{radius}'
    response = requests.get(
        url,
        timeout=10
    )

    if response.status_code == 200:
        # Parsing the JSON response
        aircraft_data = response.json()
        s.log(4, f'INFO: Retrieved {len(aircraft_data["ac"])} aircraft from AirplanesLive Network')
        for aircraft in aircraft_data['ac']:
            if 'lat' in aircraft:
                if 'alt_baro' in aircraft:
                    if aircraft['alt_baro'] != 'ground':

                        aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), int(feet_to_meters(aircraft['alt_baro'])))
                        aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)
                        
                        icao = aircraft['hex']
                        flight = aircraft['flight'] if 'flight' in aircraft else 'Unknown'
                                    
                        found_aircraft[icao] = {
                            'hex': icao,
                            'flight': flight,
                            'distance': aircraft_distance,
                            'distance_miles' : meters_to_miles(aircraft_distance),                          
                            'altitude': get_flight_level(aircraft['alt_baro']),
                            'ias': aircraft['ias'] if 'ias' in aircraft else '',
                            'tas': aircraft['tas'] if 'tas' in aircraft else '',
                            'mach': aircraft['mach'] if 'mach' in aircraft else '',
                            'azimuth': aircraft_azimuth,
                            'elevation': aircraft_elevation   
                        }
                    else:
                        print(f'INFO: {flight} is on the ground so ignoring')
                else:
                        print(f'INFO: {flight} no altitude available so ignoring')                    
            else:
                print(f'INFO: {flight} has no location so ignoring')
    else:
        result = f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}'

    return found_aircraft, result

def opensky_adsb(params, observer_location):
    ''' Retreives data from Opensky
    '''    
    found_aircraft = {}
    result = ''
    #url='https://opensky-network.org/api/states/all?lamin=51.217207&lamax=52.895649&lomin=-1.016235&lomax=1.845703'

    lat_min = params['opensky_lat_min']
    lon_min = params['opensky_lon_min']
    lat_max = params['opensky_lat_max']
    lon_max = params['opensky_lon_max']
    username = params['opensky_username'] if params['opensky_username'] != '' else None
    password = params['opensky_password'] if params['opensky_password'] != '' else None

    url = f'https://opensky-network.org/api/states/all?lamin={lat_min}&lamax={lat_max}&lomin={lon_min}&lomax={lon_max}'
    s.log(4, 'INFO: Getting data from OpenSky Network')

    if username is not None and password is not None:
        response = requests.get(url,timeout=10,auth=(username, password))
    else:
        response = requests.get(url,timeout=10)

    if response.status_code == 200:
        aircraft_data = response.json()

        s.log(4, f'INFO: Retrieved {len(aircraft_data["states"])} aircraft from OpenSky Network') 
        for aircraft in aircraft_data['states']:
            aircraft_pos = (float(aircraft[6]), float(aircraft[5]), int(aircraft[7]))
            aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)

            icao = aircraft[0]
            flight = aircraft[1]
            found_aircraft[icao] = {
                'hex': icao,
                'flight': flight,
                'distance': aircraft_distance,
                'distance_miles' : meters_to_miles(aircraft_distance),                
                'altitude': get_flight_level(aircraft[7]),
                'ias': int(aircraft[9]),
                'tas': int(aircraft[9]),
                'mach': knots_to_mach(aircraft[9]),
                'azimuth': aircraft_azimuth,
                'elevation': aircraft_elevation    
            }
    else:
        result = f'ERROR: Failed getting data from OpenSky Network "{url}". {response.status_code} - {response.text}'

    return found_aircraft, result

def knots_to_mach(knots, speed_of_sound_knots=661.5):
    ''' Converts knots to an estimated mach number
    '''    
    return knots / speed_of_sound_knots

def get_flight_level(altitude):
    ''' Converts an altitude in meters to a flight levek
    '''        
    return f'FL{int(altitude / 100):03}'

def feet_to_meters(feet):
    ''' Converts feet to meters
    '''        
    return feet * 0.3048

def meters_to_miles(meters):
    ''' Converts meters to mils
    '''        
    return meters / 1609.344

def haversine_distance(lat1, lon1, lat2, lon2):
    '''Calculate greate circle distance between two points

    Thanks to ChatGPT for the function
    '''
    
    EARTH_RADIUS = 6371000
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula for distance on Earth's surface
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS * c
    return distance

def look_angle(aircraft_pos, observer_location):
    '''Calculate look angle between observer and aircraft

    Thanks to ChatGPT for the function
    '''
    lat1 = observer_location[0]
    lon1 = observer_location[1]
    alt1 = observer_location[2]

    lat2 = aircraft_pos[0]
    lon2 = aircraft_pos[1]
    alt2 = aircraft_pos[2]

    # Surface distance between points
    surface_distance = haversine_distance(lat1, lon1, lat2, lon2)

    # Azimuth calculation
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(math.radians(lat2))
    y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon)
    azimuth = math.degrees(math.atan2(x, y))
    azimuth = (azimuth + 360) % 360  # Normalize to 0-360 degrees

    # Elevation calculation
    alt_diff = alt2 - alt1
    slant_distance = math.sqrt(surface_distance ** 2 + alt_diff ** 2)
    elevation = math.degrees(math.asin(alt_diff / slant_distance))

    return azimuth, elevation, surface_distance, slant_distance

def adsb(params, event):
    ''' The entry point for the module called by the module manager
    '''        
    result = ''
    period = 1
    period = int(params["period"])
    
    data_source = params['data_source']
    local_adsb_url = params['local_adsb_url']
    observer_altitude = int(params['observer_altitude'])
    
    should_run, diff = s.shouldRun(metaData["module"], period)
    if should_run:
        
        lat = s.getSetting('latitude')
        if lat is not None and lat != '':
            lat = s.convertLatLon(lat)
            lon = s.getSetting('longitude')
            if lon is not None and lon != '':
                lon = s.convertLatLon(lon)
                
                observer_location = (lat, lon, observer_altitude)

                extra_data = {}

                if data_source == 'Local':
                    aircraft_list, result = local_adsb(local_adsb_url, observer_location)
                
                if data_source == 'AirplanesLive':
                    aircraft_list, result = airplaneslive_adsb(params, observer_location)

                if data_source == 'OpenSky':
                    aircraft_list, result = opensky_adsb(params, observer_location)

                if result == '':
                    aircraft_list = dict(sorted(aircraft_list.items(), key=lambda item: item[1]['distance']))        
                    
                    counter = 1
                    for aircraft in aircraft_list.values():
                        extra_data[f'aircraft_{counter}_hex'] = aircraft['hex']
                        extra_data[f'aircraft_{counter}_text'] = f"{aircraft['flight']} {aircraft['azimuth']:.0f}°"
                        extra_data[f'aircraft_{counter}_longtext'] = f"{aircraft['flight']} {aircraft['azimuth']:.0f}° {aircraft['distance_miles']:.0f}Miles {aircraft['altitude']}  {aircraft['ias']}kts"
                        counter = counter + 1
                    result = f'Wrote {len(aircraft_list)} aircraft to extra data file allskyadsb.json'
                    s.saveExtraData('allskyadsb.json', extra_data)
                    s.log(4,f'INFO: {result}')
                else:
                    s.log(0, result)
            else:
                result = f'The longitude in the main Allsky settings is invalid "{lon}"'
                s.log(4,f'ERROR: {result}')
        else:
            result = f'The latitude in the main Allsky settings is invalid "{lat}"'
            s.log(4,f'ERROR: {result}')            
    else:
        result = f'Will run in {(period - diff):.0f} seconds'
        s.log(4,f'INFO: {result}')

    return result

def adsb_cleanup():
    ''' Cleans up the module if it is removed from a flow, called by the module manager
    '''       
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyadsb.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
