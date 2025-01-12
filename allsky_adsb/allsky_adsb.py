#TODO: Sort events
'''
allsky_adsb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import sys
import requests
import math
import json
import os

from unidecode import unidecode
from requests.exceptions import MissingSchema, JSONDecodeError

metaData = {
	"name": "ADSB - Aircraft tracking",
	"description": "Provides aircraft data for display in the captured images",
	"module": "allsky_adsb",    
	"version": "v1.0.0",
	"events": [
	    "periodic",
	    "day",
	    "night"
	],
	"enabled": "false",    
	"experimental": "true",
	"testable": "true",  
	"centersettings": "false",
	"extradata": {
	    "info": {
	        "count": 20,
	        "firstblank": "false"
	    },
	    "values": {
	        "AS_AIRCRAFT_AZIMUTH${COUNT}": {
	            "group": "ADSB Data",
	            "type": "azimuth",                
	            "description": "Aircraft ${COUNT} azimuth"
	        },
	        "AS_AIRCRAFT_ELEVATION${COUNT}": {
	            "group": "ADSB Data",
	            "type": "elevation",                
	            "description": "Aircraft ${COUNT} elevation"
	        },
	        "AS_AIRCRAFT_ALTITUDE${COUNT}": {
	            "group": "ADSB Data",
	            "type": "int",                
	            "description": "Aircraft ${COUNT} altitude"
	        },                        
	        "AS_AIRCRAFT_TYPE${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} type"
	        },              
	        "AS_AIRCRAFT_OWNER${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} owner"
	        },
	        "AS_AIRCRAFT_REGISTRATION${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} registration"
	        },
	        "AS_AIRCRAFT_MANUFACTURER${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} manufacturer"
	        },
	        "AS_AIRCRAFT_MILITARY${COUNT}": {
	            "group": "ADSB Data",
	            "type": "bool",                
	            "description": "Aircraft ${COUNT} military flag"
	        },
	        "AS_AIRCRAFT_TEXT${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",
	            "description": "Aircraft ${COUNT} short text (reg, bearing)"
	        },
	        "AS_AIRCRAFT_LONGTEXT${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} medium text (reg, type, bearing, distance, alt, speed)"
	        },
	        "AS_AIRCRAFT_SHORT_ROUTE${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} short route (ICAO -> ICAO)"
	        },
	        "AS_AIRCRAFT_MEDIUM_ROUTE${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} short route (City -> CITY)"
	        },
	        "AS_AIRCRAFT_LONG_ROUTE${COUNT}": {
	            "group": "ADSB Data",
	            "type": "string",                
	            "description": "Aircraft ${COUNT} long route (ICAO - City -> ICAO - CITY)"
	        }
	    }
	},
	"arguments":{
	    "period": 60,
	    "data_source": "Local",
	    "aircraft_data": "local",
	    "aricraft_route": "true",
	    "distance_limit": 50,
	    "timeout": 10,
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
	            "values": "Local,OpenSky,AirplanesLive,adsbfi",
	            "default": "Local"
	        }
	    },        
 
 		"noticeal" : {
	        "tab": "Data Source",      
			"message": "There are no settings required for AirplanesLive",
	        "type": {
	            "fieldtype": "text",
	            "style": {
	                "width": "full",
					"alert": {
						"class": "info"
					}
				}
	        },
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"AirplanesLive"
				]
			}              			
		}, 
 		"noticefi" : {
	        "tab": "Data Source",      
			"message": "There are no settings required for adsbfi",
	        "type": {
	            "fieldtype": "text",
	            "style": {
	                "width": "full",
					"alert": {
						"class": "info"
					}
				}
	        },
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"adsbfi"
				]
			}              			
		},    
	    "local_adsb_url": {
	        "required": "false",
	        "description": "Local ADSB Address",
	        "help": "See the help for how to obtain this address",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"Local"
				]
			}             
	    },
	    "opensky_username": {
	        "required": "false",
	        "description": "OpenSky Username",
	        "help": "Your username for the Opensky Network. See the module documentaiton for details on the api limits with and without a username",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },
	    "opensky_password": {
	        "required": "false",
	        "description": "OpenSky Password",
	        "help": "Your password for the Opensky Network",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },        
	    "opensky_lat_min": {
	        "required": "false",
	        "description": "Min latitude",
	        "help": "The minimum latitude of the bounding box. Use a site like http://bboxfinder.com/ to determine the bounding box",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },
	    "opensky_lon_min": {
	        "required": "false",
	        "description": "Min longitude",
	        "help": "The minimum longitude of the bounding box.",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },
	    "opensky_lat_max": {
	        "required": "false",
	        "description": "Max latitude",
	        "help": "The minimum latitude of the bounding box.",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },
	    "opensky_lon_max": {
	        "required": "false",
	        "description": "Max longitude",
	        "help": "The maximum longitude of the bounding box.",
	        "tab": "Data Source",
	        "filters": {
	            "filter": "data_source",
	            "filtertype": "show",
	            "values": [
	            	"OpenSky"
				]
			}            
	    },
	    
	    
	    "aircraft_data" : {
	        "required": "false",
	        "description": "Aircraft Type Data Source",
	        "help": "The source for the aircraft data, see the documentaiton for details",
	        "tab": "Settings",
	        "type": {
	            "fieldtype": "select",
	            "values": "Local,Hexdb",
	            "default": "Local"
	        }
	    },
	    "aricraft_route" : {
	        "required": "false",
	        "description": "Get flight route",
	        "help": "Get the flights route if possible",
	        "tab": "Settings",
	        "type": {
	            "fieldtype": "checkbox"
	        }          
	    },
	    "distance_limit" : {
	        "required": "true",
	        "description": "Limit Distance",
	        "help": "Only include aircraft inside this distance",
	        "tab": "Settings",                        
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 250,
	            "step": 1
	        }
	    },         
	    "observer_altitude" : {
	        "required": "true",
	        "description": "Altitude",
	        "help": "Your altitude in metres.",
	        "tab": "Settings",                        
	        "type": {
	            "fieldtype": "spinner",
	            "min": 0,
	            "max": 1000,
	            "step": 10
	        }
	    },
	    "period" : {
	        "required": "true",
	        "description": "Read Every",
	        "help": "Reads data every x seconds. Be careful of any api limits when setting this",
	        "tab": "Settings",                          
	        "type": {
	            "fieldtype": "spinner",
	            "min": 60,
	            "max": 1440,
	            "step": 1
	        }
	    },
	    "timeout" : {
	        "required": "true",
	        "description": "Timeout",
	        "help": "The number of seconds to wait for a response from the api before aborting",
	        "tab": "Settings",                        
	        "type": {
	            "fieldtype": "spinner",
	            "min": 1,
	            "max": 20,
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

def local_adsb(local_adsb_url, observer_location, timeout):
	''' Retreives data from a local ADSB source
	'''
	found_aircraft = {}
	result = ''
	s.log(4, 'INFO: Getting data from local ADSB receiver')
	
	try:
		response = requests.get(local_adsb_url, timeout=timeout)

		if response.status_code == 200:
			aircraft_data = response.json()

			s.log(4, f'INFO: Retrieved {len(aircraft_data["aircraft"])} aircraft from local ADSB server')
			for aircraft in aircraft_data['aircraft']:

				if 'flight' not in aircraft or aircraft['flight'].replace(' ', '') == '':
					aircraft['flight'] = aircraft['hex'].rstrip()

				if 'ias' not in aircraft:
					if 'gs' in aircraft:
						aircraft['ias'] = aircraft['gs']

				if 'ias' in aircraft:
					if 'lat' in aircraft:
						aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), feet_to_meters(int(aircraft['alt_baro'])))
						aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)

						found_aircraft[aircraft['hex']] = {
							'hex': aircraft['hex'].rstrip(),
							'flight': aircraft['flight'].rstrip(),
							'distance': aircraft_distance,
							'distance_miles': meters_to_miles(aircraft_distance),
							'altitude': get_flight_level(aircraft['alt_baro']),
							'altituderaw': aircraft['alt_baro'],
							'ias': aircraft['ias'] if 'ias' in aircraft else '',
							'tas': aircraft['tas'] if 'tas' in aircraft else '',
							'mach': aircraft['mach'] if 'mach' in aircraft else '',
							'azimuth': aircraft_azimuth,
							'elevation': aircraft_elevation                   
						}
					else:
						s.log(4, f'INFO: Ignoring {aircraft["flight"].rstrip()} as the latitude missing')
				else:
					s.log(4, f'INFO: Ignoring {aircraft["flight"].rstrip()} as the airspeed missing')
		else:
			result = f'ERROR: Failed to retrieve data from "{local_adsb_url}". {response.status_code} - {response.text}'
	except MissingSchema:
		result = f'ERROR: The provided local adsb URL "{local_adsb_url}" is invalid'
	except JSONDecodeError:
		result = f'ERROR: The provided local adsb URL "{local_adsb_url}" is not returning JSON data'

	return found_aircraft, result

def airplaneslive_adsb(params, observer_location, timeout):
	''' Retreives data from Airplanes live
	'''

	found_aircraft = {}
	result = ''

	radius = params['distance_limit']

	s.log(4, 'INFO: Getting data from Airplanes Live Network')  
	url = f'https://api.airplanes.live/v2/point/{observer_location[0]}/{observer_location[1]}/{radius}'
	try:
		response = requests.get(url, timeout=timeout)

		if response.status_code == 200:
			aircraft_data = response.json()
			s.log(4, f'INFO: Retrieved {len(aircraft_data["ac"])+1} aircraft from AirplanesLive Network')
			for aircraft in aircraft_data['ac']:
				flight = aircraft['flight'] if 'flight' in aircraft else 'Unknown'

				if 'ias' not in aircraft:
					if 'gs' in aircraft:
						aircraft['ias'] = aircraft['gs']
							
				if 'lat' in aircraft:
					if 'alt_baro' in aircraft:
						if aircraft['alt_baro'] != 'ground':

							aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), int(feet_to_meters(aircraft['alt_baro'])))
							aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)

							icao = aircraft['hex']

							found_aircraft[icao] = {
								'hex': icao,
								'flight': flight,
								'distance': aircraft_distance,
								'distance_miles' : meters_to_miles(aircraft_distance),                          
								'altitude': get_flight_level(aircraft['alt_baro']),
								'altituderaw': aircraft['alt_baro'],
								'ias': aircraft['ias'] if 'ias' in aircraft else '',
								'tas': aircraft['tas'] if 'tas' in aircraft else '',
								'mach': aircraft['mach'] if 'mach' in aircraft else '',
								'azimuth': aircraft_azimuth,
								'elevation': aircraft_elevation   
							}
						else:
							s.log(4, f'INFO: {flight} is on the ground so ignoring')
					else:
							s.log(4, f'INFO: {flight} no altitude available so ignoring')
				else:
					s.log(4, f'INFO: {flight} has no location so ignoring')
		else:
			result = f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}'
	except Exception as data_exception:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
		
	return found_aircraft, result

def opensky_adsb(params, observer_location, timeout):
	''' Retreives data from Opensky
	'''
	found_aircraft = {}
	result = ''

	lat_min = params['opensky_lat_min']
	lon_min = params['opensky_lon_min']
	lat_max = params['opensky_lat_max']
	lon_max = params['opensky_lon_max']
	username = params['opensky_username'] if params['opensky_username'] != '' else None
	password = params['opensky_password'] if params['opensky_password'] != '' else None

	url = f'https://opensky-network.org/api/states/all?lamin={lat_min}&lamax={lat_max}&lomin={lon_min}&lomax={lon_max}'
	s.log(4, 'INFO: Getting data from OpenSky Network')

	try:
		if username is not None and password is not None:
			response = requests.get(url,timeout=timeout,auth=(username, password))
		else:
			response = requests.get(url,timeout=timeout)

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
					'distance_miles': meters_to_miles(aircraft_distance),                
					'altitude': get_flight_level(aircraft[7]),
					'altituderaw': aircraft[7],
					'ias': int(aircraft[9]),
					'tas': int(aircraft[9]),
					'mach': knots_to_mach(aircraft[9]),
					'azimuth': aircraft_azimuth,
					'elevation': aircraft_elevation    
				}
		else:
			result = f'ERROR: Failed getting data from OpenSky Network "{url}". {response.status_code} - {response.text}'
	except Exception as data_exception:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
		
	return found_aircraft, result

def adsbfi_adsb(params, observer_location, timeout):
	''' Retreives data from Airplanes live
	'''

	found_aircraft = {}
	result = ''
	radius = params['distance_limit']

	s.log(4, 'INFO: Getting data from Adsb.fi Network')  
	url = f'https://opendata.adsb.fi/api/v2/lat/{observer_location[0]}/lon/{observer_location[1]}/dist/{radius}'
	try:
		response = requests.get(url, timeout=timeout)

		if response.status_code == 200:
			aircraft_data = response.json()
			s.log(4, f'INFO: Retrieved {len(aircraft_data["aircraft"])+1} aircraft from Adsb.fi Network')
			for aircraft in aircraft_data['aircraft']:
				
				if 'ias' not in aircraft:
					if 'gs' in aircraft:
						aircraft['ias'] = aircraft['gs']
						
				flight = aircraft['flight'] if 'flight' in aircraft else 'Unknown'                    
				if 'lat' in aircraft:
					if 'alt_baro' in aircraft:
						if aircraft['alt_baro'] != 'ground':

							aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), int(feet_to_meters(aircraft['alt_baro'])))
							aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = look_angle(aircraft_pos, observer_location)

							icao = aircraft['hex']
						
							found_aircraft[icao] = {
								'hex': icao,
								'flight': flight,
								'distance': aircraft_distance,
								'distance_miles' : meters_to_miles(aircraft_distance),                          
								'altitude': get_flight_level(aircraft['alt_baro']),
								'altituderaw': aircraft['alt_baro'],                                
								'ias': aircraft['ias'] if 'ias' in aircraft else '',
								'tas': aircraft['tas'] if 'tas' in aircraft else '',
								'mach': aircraft['mach'] if 'mach' in aircraft else '',
								'azimuth': aircraft_azimuth,
								'elevation': aircraft_elevation   
							}
						else:
							s.log(4, f'INFO: {flight} is on the ground so ignoring')
					else:
							s.log(4, f'INFO: {flight} no altitude available so ignoring')
				else:
					s.log(4, f'INFO: {flight} has no location so ignoring')
		else:
			if response.status_code == 429:
				result = 'ERROR: You are making too many requests to adsb.fi. increase the time between runs'
			else:
				result = f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}'
	except Exception as data_exception:
		exception_type, exception_object, exception_traceback = sys.exc_info()
		result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
		
	return found_aircraft, result

def knots_to_mach(knots, speed_of_sound_knots=661.5):
	''' Converts knots to an estimated mach number
	'''    
	return knots / speed_of_sound_knots

def get_flight_level(altitude):
	''' Converts an altitude in meters to a flight levek
	'''
	
	if altitude < 1000:
		result = f'{altitude}ft'
	else: 
		result = f'FL{int(altitude / 100):03}'
		
	return result

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

def _get_aircraft_info(icao, timeout, aircraft_data):

	aircraft_info = {
	    'ICAOTypeCode': '', 
	    'Manufacturer': '', 
	    'ModeS': '', 
	    'OperatorFlagCode': '', 
	    'RegisteredOwners': '', 
	    'Registration': '', 
	    'Type': '',
	    'Military': ''
	}
	
	if aircraft_data == 'Hexdb':
		url = f'https://hexdb.io/api/v1/aircraft/{icao}'
		try:
			response = requests.get(url, timeout=timeout)

			if response.status_code == 200:
				aircraft_info = response.json()

				aircraft_info['TypeLong'] = aircraft_info['Type']
				aircraft_info['Type'] = aircraft_info['Type'].split()[0]
				aircraft_info['Military'] = ''
			else:
				s.log(4, f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}')
		except MissingSchema:
			s.log(4, f'The provided URL "{url}" is invalid')
		except JSONDecodeError:
			s.log(4, f'The provided URL "{url}" is not returning JSON data')
	else:
		database_dir = '/opt/allsky/modules/adsb/adsb_data'
		icao_key = icao[:2]
		icao_file = f'{icao_key}.json'
		file_path = os.path.join(database_dir, icao_file)

		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				ac_data = json.load(file)

			if icao in ac_data:
				ac_info = ac_data[icao]
				aircraft_info = {
					'ICAOTypeCode': ac_info['st'], 
					'Manufacturer': ac_info['m'], 
					'ModeS': '', 
					'OperatorFlagCode': '', 
					'RegisteredOwners': ac_info['o'], 
					'Registration': ac_info['r'], 
					'Type': ac_info['it'],
					'TypeLong': ac_info['it'],
					'Military': ''
				}
				if ac_info['ml']:
					aircraft_info['Military'] = 'Mil'
		except FileNotFoundError:
			pass

	return aircraft_info

def _get_route(flight, timeout, get_aircraft_route):
	route_data = {
	    'origin_icao': '',
	    'origin_name': '',
	    'origin_municipality': '',
	    'destination_icao': '',
	    'destination_name': '',
	    'destination_municipality': '',
	    'short_route': 'No Route',
	    'medium_route': '',
	    'long_route': ''              
	}
	
	if get_aircraft_route:
		try:
			url = f'https://api.adsbdb.com/v0/callsign/{flight}'
			response = requests.get(url, timeout=timeout)

			if response.status_code == 200:
				json_data = response.json()

				if 'response' in json_data:
					if 'flightroute' in json_data['response']:
						aircraft_route = json_data['response']['flightroute']
						route_data['origin_icao'] = aircraft_route['origin']['icao_code']
						route_data['origin_name'] = aircraft_route['origin']['name']
						route_data['origin_municipality'] = aircraft_route['origin']['municipality']

						route_data['destination_icao'] = aircraft_route['destination']['icao_code']
						route_data['destination_name'] = aircraft_route['destination']['name']
						route_data['destination_municipality'] = aircraft_route['destination']['municipality']
						
						route_data['short_route'] = f'{route_data["origin_icao"]} -> {route_data["destination_icao"]}'
						route_data['medium_route'] = f'{route_data["origin_municipality"]} -> {route_data["destination_municipality"]}'
						route_data['long_route'] = f'({route_data["origin_icao"]}) {route_data["origin_name"]} -> ({route_data["destination_icao"]}) {route_data["destination_name"]}'

						route_data['medium_route'] = unidecode(route_data['medium_route'])
						route_data['long_route'] = unidecode(route_data['long_route'])

		except Exception as data_exception:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
			s.log(4, result)
		
	return route_data
	
def adsb(params, event):
	''' The entry point for the module called by the module manager
	'''
	result = ''
	module = metaData['module']
	period = int(params['period'])
	timeout = int(params['timeout'])
	distance_limit = int(params['distance_limit'])
	data_source = params['data_source']
	local_adsb_url = params['local_adsb_url']
	observer_altitude = int(params['observer_altitude'])
	aircraft_data = params['aircraft_data']
	get_aircraft_route = params["aricraft_route"]

	try:
		debugMode = params["ALLSKYTESTMODE"]
	except ValueError:
		debugMode = False
		
	should_run, diff = s.shouldRun(module, period)
	if should_run or debugMode:
		lat = s.getSetting('latitude')
		if lat is not None and lat != '':
			lat = s.convertLatLon(lat)
			lon = s.getSetting('longitude')
			if lon is not None and lon != '':
				lon = s.convertLatLon(lon)

				observer_location = (lat, lon, observer_altitude)

				extra_data = {}

				if data_source == 'Local':
					aircraft_list, result = local_adsb(local_adsb_url, observer_location, timeout)

				if data_source == 'AirplanesLive':
					aircraft_list, result = airplaneslive_adsb(params, observer_location, timeout)

				if data_source == 'OpenSky':
					aircraft_list, result = opensky_adsb(params, observer_location, timeout)

				if data_source == 'adsbfi':
					aircraft_list, result = adsbfi_adsb(params, observer_location, timeout)

				if result == '':
					aircraft_list = dict(sorted(aircraft_list.items(), key=lambda item: item[1]['distance']))

					counter = 1
					for aircraft in aircraft_list.values():
						if aircraft['distance_miles'] <= distance_limit:
							aircraft['info'] = _get_aircraft_info(aircraft['hex'], timeout, aircraft_data)
							aircraft['route'] = _get_route(aircraft['flight'].rstrip(), timeout, get_aircraft_route)

							extra_data[f'AS_AIRCRAFT_HEX{counter}'] = aircraft['hex']
							extra_data[f'AS_AIRCRAFT_AZIMUTH{counter}'] = int(aircraft['azimuth'])
							extra_data[f'AS_AIRCRAFT_ELEVATION{counter}'] = int(aircraft['elevation'])
							extra_data[f'AS_AIRCRAFT_ALTITUDE{counter}'] = int(aircraft['altituderaw'])
							extra_data[f'AS_AIRCRAFT_TYPE{counter}'] = aircraft['info']['Type']
							extra_data[f'AS_AIRCRAFT_OWNER{counter}'] = aircraft['info']['RegisteredOwners']
							extra_data[f'AS_AIRCRAFT_REGISTRATION{counter}'] = aircraft['info']['Registration']
							extra_data[f'AS_AIRCRAFT_MANUFACTURER{counter}'] = aircraft['info']['Manufacturer']
							extra_data[f'AS_AIRCRAFT_MILITARY{counter}'] = aircraft['info']['Military']
							extra_data[f'AS_AIRCRAFT_TEXT{counter}'] = f"{aircraft['flight'].strip()} {aircraft['azimuth']:.0f}°"
							extra_data[f'AS_AIRCRAFT_LONGTEXT{counter}'] = f"{aircraft['flight'].strip()} {aircraft['info']['Type']} {aircraft['azimuth']:.0f}° {aircraft['distance_miles']:.0f}Miles {aircraft['altitude']}  {aircraft['ias']}kts"
							extra_data[f'AS_AIRCRAFT_SHORT_ROUTE{counter}'] = aircraft['route']['short_route']
							extra_data[f'AS_AIRCRAFT_MEDIUM_ROUTE{counter}'] = aircraft['route']['medium_route']
							extra_data[f'AS_AIRCRAFT_LONG_ROUTE{counter}'] = aircraft['route']['long_route']
							counter = counter + 1
						else:
							s.log(4,f'INFO: Aicraft {aircraft["flight"]} excludes as beyond {distance_limit} miles')
					result = f'Wrote {counter} aircraft to extra data file allskyadsb.json'
					s.saveExtraData('allskyadsb.json', extra_data, metaData["module"], metaData["extradata"])
					s.setLastRun(module)
					s.log(4,f'INFO: {result}')
				else:
					s.log(0, result)
			else:
				result = f'The longitude in the main Allsky settings is invalid "{lon}"'
				s.log(0, f'ERROR: {result}')
		else:
			result = f'The latitude in the main Allsky settings is invalid "{lat}"'
			s.log(0, f'ERROR: {result}')
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
