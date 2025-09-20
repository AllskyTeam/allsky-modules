#TODO: Sort events
'''
allsky_adsb.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import sys
import requests
import math
import json
import os

from unidecode import unidecode
from requests.exceptions import MissingSchema, JSONDecodeError

class ALLSKYADSB(ALLSKYMODULEBASE):

	meta_data = {
		"name": "ADSB - Aircraft tracking",
		"description": "Provides aircraft data for display in the captured images",
		"module": "allsky_adsb",    
		"version": "v2.0.0",
		"group": "Data Capture",
		"events": [
			"periodic",
			"day",
			"night"
		],
		"enabled": "false",    
		"experimental": "true",
		"testable": "true",  
		"centersettings": "false",
		"extradatafilename": "allsky_adsb.json",
        "graphs": {
            "chart1": {
				"icon": "fa-solid fa-chart-line",
				"title": "ADSB Aircraft",
				"group": "ADSB",    
				"main": "true",    
				"config": {
					"chart": {
						"type": "spline",
						"animation": "false",
						"zooming": {
							"type": "x"
						}
					},
					"plotOptions": {
						"series": {
							"animation": "false"
						}
					},
					"title": {
						"text": "Total Aircraft"
					},
					"xAxis": {
						"type": "datetime",
						"dateTimeLabelFormats": {
							"day": "%Y-%m-%d",
							"hour": "%H:%M"
						}
					},
					"yAxis": [
						{ 
							"title": {
								"text": "Total"
							} 
						}
					]
				},
				"series": {
					"heater": {
						"name": "Total",
						"variable": "AS_TOTAL_AIRCRAFT"
					}
				}
			}
        },  
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_adsb"
			},      
			"info": {
				"count": 20,
				"firstblank": "false"
			},
			"values": {
				"AS_TOTAL_AIRCRAFT": {
					"group": "ADSB Data",
					"type": "number",                
					"description": "Total Aircraft",
					"database": {
						"include" : "true"
					}     
				},
				"AS_DISTANCE_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"format": "{allsky}",
					"type": "distance",            
					"description": "Aircraft ${COUNT} distance"
				},    
				"AS_AZIMUTH_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"format": "{dp=2|deg}",     
					"type": "azimuth",                
					"description": "Aircraft ${COUNT} azimuth"
				},
				"AS_ELEVATION_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"format": "{dp=2|deg}",     
					"type": "elevation",                
					"description": "Aircraft ${COUNT} elevation"
				},
				"AS_ALTITUDE_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"format": "{flightlevel}",
					"type": "altitude",                
					"description": "Aircraft ${COUNT} altitude"
				},                        
				"AS_TYPE_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} type"
				},              
				"AS_OWNER_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} owner"
				},
				"AS_REGISTRATION_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} registration"
				},
				"AS_MANUFACTURER_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} manufacturer"
				},
				"AS_MILITARY_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"format": "{yesno}",     
					"type": "bool",                
					"description": "Aircraft ${COUNT} military flag"
				},
				"AS_TEXT_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",
					"description": "Aircraft ${COUNT} short text (reg, bearing)"
				},
				"AS_LONGTEXT_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} medium text (reg, type, bearing, distance, alt, speed)"
				},
				"AS_SHORT_ROUTE_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} short route (ICAO -> ICAO)"
				},
				"AS_MEDIUM_ROUTE_AIRCRAFT${COUNT}": {
					"group": "ADSB Data",
					"type": "string",                
					"description": "Aircraft ${COUNT} short route (City -> CITY)"
				},
				"AS_LONG_ROUTE_AIRCRAFT${COUNT}": {
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
			"aircraft_route": "true",
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
				"secret": "true",
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
				"secret": "true",    
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
				"secret": "true",    
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
			"aircraft_route" : {
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
			},
			"graph": {
				"required": "false",
				"tab": "History",
				"type": {
					"fieldtype": "graph"
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
			],
			"v2.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updates for new module system"
				}
			]   
		}
	}

	_warnings = {}
	_missing_adsb_data = False
 
	def _local_adsb(self, local_adsb_url, observer_location, timeout):
		''' Retreives data from a local ADSB source
		'''
		found_aircraft = {}
		result = ''
		allsky_shared.log(4, 'INFO: Getting data from local ADSB receiver')
		
		try:
			response = requests.get(local_adsb_url, timeout=timeout)

			if response.status_code == 200:
				aircraft_data = response.json()

				allsky_shared.log(4, f'INFO: Retrieved {len(aircraft_data["aircraft"])} aircraft from local ADSB server')
				for aircraft in aircraft_data['aircraft']:

					if 'flight' not in aircraft or aircraft['flight'].replace(' ', '') == '':
						aircraft['flight'] = aircraft['hex'].rstrip()

					if 'ias' not in aircraft:
						if 'gs' in aircraft:
							aircraft['ias'] = aircraft['gs']

					if 'ias' in aircraft:
						if 'lat' in aircraft:
							aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), self._feet_to_meters(int(aircraft['alt_baro'])))
							aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = self._look_angle(aircraft_pos, observer_location)

							found_aircraft[aircraft['hex']] = {
								'hex': aircraft['hex'].rstrip(),
								'flight': aircraft['flight'].rstrip(),
								'distance': aircraft_distance,
								'distance_miles': self._meters_to_miles(aircraft_distance),
								'altitude': self._get_flight_level(aircraft['alt_baro']),
								'altituderaw': aircraft['alt_baro'],
								'ias': aircraft['ias'] if 'ias' in aircraft else '',
								'tas': aircraft['tas'] if 'tas' in aircraft else '',
								'mach': aircraft['mach'] if 'mach' in aircraft else '',
								'azimuth': aircraft_azimuth,
								'elevation': aircraft_elevation                   
							}
						else:
							self.__add_warning('latitude', aircraft['flight'].rstrip())
					else:
						self.__add_warning('airspeed', aircraft['flight'].rstrip())
			else:
				result = f'ERROR: Failed to retrieve data from "{local_adsb_url}". {response.status_code} - {response.text}'
		except MissingSchema:
			result = f'ERROR: The provided local adsb URL "{local_adsb_url}" is invalid'
		except JSONDecodeError:
			result = f'ERROR: The provided local adsb URL "{local_adsb_url}" is not returning JSON data'

		return found_aircraft, result

	def _airplaneslive_adsb(self, observer_location, timeout):
		''' Retreives data from Airplanes live
		'''

		found_aircraft = {}
		result = ''

		radius = self.get_param('distance_limit', 50, int)

		allsky_shared.log(4, 'INFO: Getting data from Airplanes Live Network')  
		url = f'https://api.airplanes.live/v2/point/{observer_location[0]}/{observer_location[1]}/{radius}'
		try:
			response = requests.get(url, timeout=timeout)

			if response.status_code == 200:
				aircraft_data = response.json()
				allsky_shared.log(4, f'INFO: Retrieved {len(aircraft_data["ac"])+1} aircraft from AirplanesLive Network')
				for aircraft in aircraft_data['ac']:
					flight = aircraft['flight'] if 'flight' in aircraft else 'Unknown'

					if 'ias' not in aircraft:
						if 'gs' in aircraft:
							aircraft['ias'] = aircraft['gs']
								
					if 'lat' in aircraft:
						if 'alt_baro' in aircraft:
							if aircraft['alt_baro'] != 'ground':

								aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), int(self._feet_to_meters(aircraft['alt_baro'])))
								aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = self._look_angle(aircraft_pos, observer_location)

								icao = aircraft['hex']

								found_aircraft[icao] = {
									'hex': icao,
									'flight': flight,
									'distance': aircraft_distance,
									'distance_miles' : self._meters_to_miles(aircraft_distance),                          
									'altitude': self._get_flight_level(aircraft['alt_baro']),
									'altituderaw': aircraft['alt_baro'],
									'ias': aircraft['ias'] if 'ias' in aircraft else '',
									'tas': aircraft['tas'] if 'tas' in aircraft else '',
									'mach': aircraft['mach'] if 'mach' in aircraft else '',
									'azimuth': aircraft_azimuth,
									'elevation': aircraft_elevation   
								}
							else:
								code = "Unknown"
								if "flight" in aircraft:
									code = aircraft['flight'].rstrip()
								if "hex" in aircraft:
									code = aircraft['hex'].rstrip()
			
								self.__add_warning('ground', code)
						else:
							code = "Unknown"
							if "flight" in aircraft:
								code = aircraft['flight'].rstrip()
							if "hex" in aircraft:
								code = aircraft['hex'].rstrip()         
							self.__add_warning('altitude', code)
					else:
						code = "Unknown"
						if "flight" in aircraft:
							code = aircraft['flight'].rstrip()
						if "hex" in aircraft:
							code = aircraft['hex'].rstrip()          
						allsky_shared.log(4, f'INFO: {code} has no location so ignoring')
			else:
				result = f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}'
		except Exception as data_exception:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
			
		return found_aircraft, result

	def _opensky_adsb(self, observer_location, timeout):
		''' Retreives data from Opensky
		'''
		found_aircraft = {}
		result = ''

		lat_min = self.get_param('opensky_lat_min', 0, float)  
		lon_min = self.get_param('opensky_lon_min', 0, float)  
		lat_max = self.get_param('opensky_lat_max', 0, float)  
		lon_max = self.get_param('opensky_lon_max', 0, float)  
		username = self.get_param('opensky_username', None, str, True)
		password = self.get_param('opensky_password', None, str, True)

		url = f'https://opensky-network.org/api/states/all?lamin={lat_min}&lamax={lat_max}&lomin={lon_min}&lomax={lon_max}'
		allsky_shared.log(4, 'INFO: Getting data from OpenSky Network')

		try:
			if username is not None and password is not None:
				response = requests.get(url,timeout=timeout,auth=(username, password))
			else:
				response = requests.get(url,timeout=timeout)

			if response.status_code == 200:
				aircraft_data = response.json()

				allsky_shared.log(4, f'INFO: Retrieved {len(aircraft_data["states"])} aircraft from OpenSky Network') 
				for aircraft in aircraft_data['states']:
					aircraft_pos = (float(aircraft[6]), float(aircraft[5]), int(aircraft[7]))
					aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = self._look_angle(aircraft_pos, observer_location)

					icao = aircraft[0]
					flight = aircraft[1]
					found_aircraft[icao] = {
						'hex': icao,
						'flight': flight,
						'distance': aircraft_distance,
						'distance_miles': self._meters_to_miles(aircraft_distance),                
						'altitude': self._get_flight_level(aircraft[7]),
						'altituderaw': aircraft[7],
						'ias': int(aircraft[9]),
						'tas': int(aircraft[9]),
						'mach': self._knots_to_mach(aircraft[9]),
						'azimuth': aircraft_azimuth,
						'elevation': aircraft_elevation    
					}
			else:
				result = f'ERROR: Failed getting data from OpenSky Network "{url}". {response.status_code} - {response.text}'
		except Exception as data_exception:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
			
		return found_aircraft, result

	def _adsbfi_adsb(self, observer_location, timeout):
		''' Retreives data from Airplanes live
		'''

		found_aircraft = {}
		result = ''
		radius = self.get_param('distance_limit', 50, int)

		allsky_shared.log(4, 'INFO: Getting data from Adsb.fi Network')  
		url = f'https://opendata.adsb.fi/api/v2/lat/{observer_location[0]}/lon/{observer_location[1]}/dist/{radius}'
		try:
			response = requests.get(url, timeout=timeout)

			if response.status_code == 200:
				aircraft_data = response.json()
				allsky_shared.log(4, f'INFO: Retrieved {len(aircraft_data["aircraft"])+1} aircraft from Adsb.fi Network')
				for aircraft in aircraft_data['aircraft']:
					
					if 'ias' not in aircraft:
						if 'gs' in aircraft:
							aircraft['ias'] = aircraft['gs']
							
					flight = aircraft['flight'] if 'flight' in aircraft else 'Unknown'                    
					if 'lat' in aircraft:
						if 'alt_baro' in aircraft:
							if aircraft['alt_baro'] != 'ground':

								aircraft_pos = (float(aircraft['lat']), float(aircraft['lon']), int(self._feet_to_meters(aircraft['alt_baro'])))
								aircraft_azimuth, aircraft_elevation, aircraft_distance, slant_distance = self._look_angle(aircraft_pos, observer_location)

								icao = aircraft['hex']
							
								found_aircraft[icao] = {
									'hex': icao,
									'flight': flight,
									'distance': aircraft_distance,
									'distance_miles' : self._meters_to_miles(aircraft_distance),                          
									'altitude': self._get_flight_level(aircraft['alt_baro']),
									'altituderaw': aircraft['alt_baro'],                                
									'ias': aircraft['ias'] if 'ias' in aircraft else '',
									'tas': aircraft['tas'] if 'tas' in aircraft else '',
									'mach': aircraft['mach'] if 'mach' in aircraft else '',
									'azimuth': aircraft_azimuth,
									'elevation': aircraft_elevation   
								}
							else:
								self.__add_warning('ground', aircraft['flight'].rstrip())
						else:
							self.__add_warning('altitude', aircraft['flight'].rstrip())
					else:
						self.__add_warning('location', aircraft['flight'].rstrip())
			else:
				if response.status_code == 429:
					result = 'ERROR: You are making too many requests to adsb.fi. increase the time between runs'
				else:
					result = f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}'
		except Exception as data_exception:
			exception_type, exception_object, exception_traceback = sys.exc_info()
			result = f'ERROR: Failed to retrieve data from {url} - {exception_traceback.tb_lineno} - {data_exception}'
			
		return found_aircraft, result

	def _knots_to_mach(self, knots, speed_of_sound_knots=661.5):
		''' Converts knots to an estimated mach number
		'''    
		return knots / speed_of_sound_knots

	def _get_flight_level(self, altitude):
		''' Converts an altitude in meters to a flight level
		'''
		
		if altitude < 1000:
			result = f'{altitude}ft'
		else: 
			result = f'FL{int(altitude / 100):03}'
			
		return result

	def _feet_to_meters(self, feet):
		''' Converts feet to meters
		'''        
		return feet * 0.3048

	def _meters_to_miles(self, meters):
		''' Converts meters to mils
		'''        
		return meters / 1609.344

	def _haversine_distance(self, lat1, lon1, lat2, lon2):
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

	def _look_angle(self, aircraft_pos, observer_location):
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
		surface_distance = self._haversine_distance(lat1, lon1, lat2, lon2)

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

	def _get_aircraft_info(self, icao, timeout, aircraft_data):

		aircraft_info = {
			'ICAOTypeCode': '', 
			'Manufacturer': '', 
			'ModeS': '', 
			'OperatorFlagCode': '', 
			'RegisteredOwners': '', 
			'Registration': '', 
			'Type': '',
			'Military': False
		}
		
		if aircraft_data == 'Hexdb':
			url = f'https://hexdb.io/api/v1/aircraft/{icao}'
			try:
				response = requests.get(url, timeout=timeout)

				if response.status_code == 200:
					aircraft_info = response.json()

					aircraft_info['TypeLong'] = aircraft_info['Type']
					aircraft_info['Type'] = aircraft_info['Type'].split()[0]
					aircraft_info['Military'] = False
				else:
					allsky_shared.log(4, f'ERROR: Failed to retrieve data from "{url}". {response.status_code} - {response.text}')
			except MissingSchema:
				allsky_shared.log(4, f'The provided URL "{url}" is invalid')
			except JSONDecodeError:
				allsky_shared.log(4, f'The provided URL "{url}" is not returning JSON data')
		else:
			script_dir = os.path.dirname(os.path.abspath(__file__))
			database_dir = os.path.join(script_dir, 'moduledata', 'data', 'allsky_adsb', 'adsb_data')
			if os.path.isdir(database_dir):
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
							'Military': False
						}
						if ac_info['ml']:
							aircraft_info['Military'] = True
				except FileNotFoundError:
					pass
			else:
				self._missing_adsb_data = True

		return aircraft_info

	def _get_route(self, flight, timeout, get_aircraft_route):
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
				allsky_shared.log(4, result)
			
		return route_data
	
	def run(self):
		result = ''

		try:
			module = self.meta_data['module']
			period = self.get_param('period', 60, int)  
			timeout = self.get_param('timeout', 10, int)  
			distance_limit = self.get_param('distance_limit', 50, int)  
			data_source = self.get_param('data_source', 'Local', str, True)  
			local_adsb_url = self.get_param('local_adsb_url', '', str, True)  
			observer_altitude = self.get_param('observer_altitude', 0, int)  
			aircraft_data = self.get_param('aircraft_data', 'local', str, True)  
			get_aircraft_route = self.get_param('aircraft_route', False, bool)
				
			should_run, diff = allsky_shared.shouldRun(module, period)
			if should_run or self.debugmode:
				lat = allsky_shared.getSetting('latitude')
				if lat is not None and lat != '':
					lat = allsky_shared.convertLatLon(lat)
					lon = allsky_shared.getSetting('longitude')
					if lon is not None and lon != '':
						lon = allsky_shared.convertLatLon(lon)

						observer_location = (lat, lon, observer_altitude)

						extra_data = {}

						if data_source == 'Local':
							aircraft_list, result = self._local_adsb(local_adsb_url, observer_location, timeout)

						if data_source == 'AirplanesLive':
							aircraft_list, result = self._airplaneslive_adsb(observer_location, timeout)

						if data_source == 'OpenSky':
							aircraft_list, result = self._opensky_adsb(observer_location, timeout)

						if data_source == 'adsbfi':
							aircraft_list, result = self._adsbfi_adsb(observer_location, timeout)

						if result == '':
							aircraft_list = dict(sorted(aircraft_list.items(), key=lambda item: item[1]['distance']))

							counter = 1
							for aircraft in aircraft_list.values():
								if aircraft['distance_miles'] <= distance_limit:
									aircraft['info'] = self._get_aircraft_info(aircraft['hex'], timeout, aircraft_data)
									aircraft['route'] = self._get_route(aircraft['flight'].rstrip(), timeout, get_aircraft_route)

									extra_data[f'AS_DISTANCE_AIRCRAFT{counter}'] = round(aircraft['distance_miles'], 2)
									extra_data[f'AS_HEX_AIRCRAFT{counter}'] = aircraft['hex']
									extra_data[f'AS_AZIMUTH_AIRCRAFT{counter}'] = round(aircraft['azimuth'],2)
									extra_data[f'AS_ELEVATION_AIRCRAFT{counter}'] = round(aircraft['elevation'],2)
									extra_data[f'AS_ALTITUDE_AIRCRAFT{counter}'] = int(aircraft['altituderaw'])
									extra_data[f'AS_TYPE_AIRCRAFT{counter}'] = aircraft['info']['Type'] if aircraft['info']['Type'] != '' else aircraft['hex']
									extra_data[f'AS_OWNER_AIRCRAFT{counter}'] = aircraft['info']['RegisteredOwners']
									extra_data[f'AS_REGISTRATION_AIRCRAFT{counter}'] = aircraft['info']['Registration']
									extra_data[f'AS_MANUFACTURER_AIRCRAFT{counter}'] = aircraft['info']['Manufacturer']
									extra_data[f'AS_MILITARY_AIRCRAFT{counter}'] = aircraft['info']['Military']
									extra_data[f'AS_TEXT_AIRCRAFT{counter}'] = f"{aircraft['flight'].strip()} {aircraft['azimuth']:.0f}°"
									extra_data[f'AS_LONGTEXT_AIRCRAFT{counter}'] = f"{aircraft['flight'].strip()} {aircraft['info']['Type']} {aircraft['azimuth']:.0f}° {aircraft['distance_miles']:.0f}Miles {aircraft['altitude']}  {aircraft['ias']}kts"
									extra_data[f'AS_SHORT_ROUTE_AIRCRAFT{counter}'] = aircraft['route']['short_route']
									extra_data[f'AS_MEDIUM_ROUTE_AIRCRAFT{counter}'] = aircraft['route']['medium_route']
									extra_data[f'AS_LONG_ROUTE_AIRCRAFT{counter}'] = aircraft['route']['long_route']
									counter = counter + 1
								else:
									self.__add_warning('excluded', aircraft["flight"])
							result = f'Wrote {counter} aircraft to extra data file allskyadsb.json'
							extra_data['AS_TOTAL_AIRCRAFT'] = counter-1
							allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
							allsky_shared.setLastRun(module)
							allsky_shared.log(4,f'INFO: {result}')
						else:
							allsky_shared.log(0, result)
					else:
						result = f'The longitude in the main Allsky settings is invalid "{lon}"'
						allsky_shared.log(0, f'ERROR: {result}')
				else:
					result = f'The latitude in the main Allsky settings is invalid "{lat}"'
					allsky_shared.log(0, f'ERROR: {result}')

				if self._missing_adsb_data:
					allsky_shared.log(4, 'ERROR: The aircarft database has not been initialised so no aircraft information available. Please check the adsb module documentation')

				message = self.__get_warnings('excluded')
				if message != '':
					allsky_shared.log(4, f'INFO: Aicraft {message} excludes as beyond {distance_limit} miles')

				message = self.__get_warnings('latitude')
				if message != '':
					allsky_shared.log(4, f'INFO: Ignoring {message} as their latitude missing')

				message = self.__get_warnings('airspeed')
				if message != '':
					allsky_shared.log(4, f'INFO: Ignoring {message} as their airspeed missing')

				message = self.__get_warnings('altitude')
				if message != '':
					allsky_shared.log(4, f'INFO: {message} have no altitude available so ignoring')

				message = self.__get_warnings('ground')
				if message != '':
					allsky_shared.log(4, f'INFO: {message} are on the ground so ignoring')

				message = self.__get_warnings('location')
				if message != '':
					allsky_shared.log(4, f'INFO: {message} have no location so ignoring')

			else:
				result = f'Will run in {(period - diff):.0f} seconds'
				allsky_shared.log(4,f'INFO: {result}')
		except Exception as e:
			eType, eObject, eTraceback = sys.exc_info()
			allsky_shared.log(0, f"ERROR: adsb failed on line {eTraceback.tb_lineno} - {e}")    
		return result

	def __add_warning(self, warning_key, warning_text):
		if not warning_key in self._warnings:
			self._warnings[warning_key] = []

		self._warnings[warning_key].append(warning_text)
    
	def __get_warnings(self, warning_key):
		result = ''
		if warning_key in self._warnings:
			result = ', '.join(self._warnings[warning_key])

		return result
  
def adsb(params, event):
	allsky_adsb = ALLSKYADSB(params, event)
	result = allsky_adsb.run()

	return result    
    
def adsb_cleanup():
	''' Cleans up the module if it is removed from a flow, called by the module manager
	'''       
	moduleData = {
	    "metaData": ALLSKYADSB.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYADSB.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
