'''
allsky_pigps.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import time
import datetime
import subprocess
from gps import *
from datetime import timedelta

class ALLSKYGPS(ALLSKYMODULEBASE):

	meta_data = {
		"name": "AllSKY GPS",
		"description": "Sets date/time and position from an attached GPS",
		"version": "v2.0.0",
		"module": "allsky_pigps", 
		"centersettings": "false",
		"testable": "true",
		"group": "Data Sensor", 
		"events": [
			"periodic"
		],
		"extradatafilename": "allsky_gps.json",
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_gps",
    			"include_all": "false",       
    			"pk": "id",
    			"pk_type": "int",    
       			"time_of_day_save": {
					"day": "always",
					"night": "always",
					"nightday": "always",
					"daynight": "always",
					"periodic": "always"
				}    
			},      
			"values": {
				"AS_PIGPSFIXDISC": {
					"name": "${PIGPSFIXDISC}",
					"format": "",
					"sample": "",                
					"group": "GPS",
					"description": "GPS and Allsky position discrepancy",
					"type": "string",
					"database": {
						"include" : "true"
					}      
				},
				"AS_PIGPSLAT": {
					"name": "${PIGPSLAT}",
					"format": "",
					"sample": "",                
					"group": "GPS",
					"description": "GPS Latitude",
					"type": "latitude",
					"database": {
						"include" : "true"
					} 
				},
				"AS_PIGPSLON": {
					"name": "${PIGPSLON}",
					"format": "",
					"sample": "",                
					"group": "GPS",
					"description": "GPS Longitude",
					"type": "longitude",
					"database": {
						"include" : "true"
					}   
				},
				"AS_PIGPSFIX": {
					"name": "${PIGPSFIX}",
					"format": "",
					"sample": "",                
					"group": "GPS",
					"description": "GPS Fix",
					"type": "string"      
				},
				"AS_PIGPSFIXBOOL": {
					"name": "${PIGPSFIXBOOL}",
					"format": "",
					"sample": "",                
					"group": "GPS",
					"description": "GPS Fix",
					"type": "number",
					"database": {
						"include" : "true"
					}       
				}
			}                         
		},
		"arguments":{
			"warnposition": "True",
			"setposition": "False",
			"settime": "True",
			"timeperiod": "60",
			"extradataposdisc": "GPS Position differs from AllSky",
			"obfuscate": "False",
			"obfuscatelatdistance": 0,
			"obfuscatelondistance": 0
		},
		"argumentdetails": {
			"warnposition" : {
				"required": "false",
				"description": "Lat/Lon Warning",
				"help": "Warn if the GPS position doesnt match the AllSky position",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"setposition" : {
				"required": "false",
				"description": "Set Lat/Lon",
				"help": "Sets the Latitude and Longitude in the AllSky Config",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"settime" : {
				"required": "false",
				"description": "Set Time",
				"help": "Sets the local time, based upon timezone, from the gps data",
				"type": {
					"fieldtype": "checkbox"
				}          
			},        
			"timeperiod" : {
				"required": "true",
				"description": "Set Every",
				"help": "How frequently (in seconds) to set the time",                
				"type": {
					"fieldtype": "spinner",
					"min": 60,
					"max": 1440,
					"step": 1
				}          
			},
			"extradataposdisc": {
				"required": "true",
				"description": "Discrepancy Warning",
				"help": "Message to set when the GPS coordinates differ from the AllSky settings"         
			},
			"obfuscate" : {
				"required": "false",
				"description": "Obfuscate Position",
				"help": "Adds the values below to the lat/lon to prevent youre precise location being available",
				"tab": "Obfuscation",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"obfuscatelatdistance" : {
				"description": "Latitude Metres",
				"help": "Number of metres to add to the latitude",
				"tab": "Obfuscation",                       
				"type": {
					"fieldtype": "spinner",
					"min": -10000,
					"max": 10000,
					"step": 1
				}          
			},
			"obfuscatelondistance" : {
				"description": "Longitude Metres",
				"help": "Number of metres to add to the longitude",                
				"tab": "Obfuscation",            
				"type": {
					"fieldtype": "spinner",
					"min": -10000,
					"max": 10000,
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

	def _compare_gps_and_allsky(self, lat, lon):
		allsky_lat = allsky_shared.getSetting('latitude')
		allsky_lon = allsky_shared.getSetting('longitude')

		allsky_lat_cardinal = allsky_lat[-1]
		allsky_lon_compass = allsky_lon[-1]
		
		allsky_lat = float(self._truncate(allsky_lat[:-1]))
		allsky_lon = float(self._truncate(allsky_lon[:-1]))
		
		allsky_lat = f'{allsky_lat}{allsky_lat_cardinal}'
		allsky_lon = f'{allsky_lon}{allsky_lon_compass}'
		
		if lat > 0:
			lat_cardinal = 'N'
		else:
			lat_cardinal = 'S'

		if lon > 0:
			lon_cardinal = 'E'
		else:
			lon_cardinal = 'W'

		lat = str(abs(lat))
		lon = str(abs(lon))

		lat = float(self._truncate(lat[:-1]))
		lon = float(self._truncate(lon[:-1]))

		lat = f'{lat}{lat_cardinal}'
		lon = f'{lon}{lon_cardinal}'
		
		result = False
		if allsky_lat != lat or allsky_lon != lon:
			result = True
		
		return result, allsky_lat, allsky_lon, lat, lon

	def _truncate(self, val):
		if '.' in val:
			val = val.split(".")
			val[1] = val[1][:3]
			val = ".".join(val)
		else:
			val = f'{val}.000'
		
		return val
 
	def _check_time_sync_running(self):
		active = False
		status = subprocess.check_output('timedatectl status | grep service', shell=True).decode('utf-8')
		status = status.splitlines()
		status = status[0].lower()
		if status.find(' active') > -1:
			active = True    

		synced = False
		status = subprocess.check_output('timedatectl status | grep System', shell=True).decode('utf-8')
		status = status.splitlines()
		status = status[0].lower()
		if status.find(' yes') > -1:
			synced = True
		self.log(4, f'INFO: Time sync active {active}, time synched {synced}')

		result = False
		if active and synced:
			result = True
							
		return result

	def _deg_to_dms(self, deg, type='lat'):
		decimals, number = math.modf(deg)
		d = int(number)
		m = int(decimals * 60)
		s = (deg - d - m / 60) * 3600.00
		compass = {
			'lat': ('N','S'),
			'lon': ('E','W')
		}
		compass_str = compass[type][0 if d >= 0 else 1]
		return '{}º{}\'{:.2f}"{}'.format(abs(d), abs(m), abs(s), compass_str) 

	def run(self):
		ONEMETER = 0.00001
		extra_data =  {
			'AS_PIGPSFIX': {
				'value': 'No',
				'fill': "#ff0000"
			},
   			'AS_PIGPSFIXBOOL': 0,
			'AS_PIGPSTIME': 'Disabled',
			'AS_PIGPSUTC': '',
			'AS_PIGPSLOCAL': '',
			'AS_PIGPSOFFSET': '',
			'AS_PIGPSLAT': '',
			'AS_PIGPSLON': '',
			'AS_PIGPSLATDEC': '',
			'AS_PIGPSLONDEC': '',
			'AS_PIGPSFIXDISC': ''
		}
		set_position = self.get_param('setposition', False, bool)
		warn_position = self.get_param('warnposition', False, bool)
		set_time = self.get_param('settime', False, bool)
		period = self.get_param('period', 60, int)
		extra_data_pos_disc = self.get_param('extradataposdisc', '', str)
		obfuscate = self.get_param('obfuscate', False, bool)
		obfuscate_lat_distance = self.get_param('obfuscatelatdistance', 0, int)
		obfuscate_lon_distance = self.get_param('obfuscatelondistance', 0, int)
  
		should_run, diff = allsky_shared.shouldRun('pigps', period)

		gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
		if should_run or self.debug_mode:
			if set_time:
				if not self._check_time_sync_running():
					try:
						timeout = time.time() + 3
						while True:
							report = gpsd.next()
							if report['class'] == 'TPV':
								mode = getattr(report,'mode',1)
								if mode != MODE_NO_FIX:                            
									if set_time:
										#s.log(4,"INFO: Got UTC date info {} from gpsd in {:.2f} seconds".format(gpsd.utc, timeout - time.time())) 
										offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
										offset = offset / 60 / 60 * -1
										
										timeUTC = getattr(report, 'time', '')
										
										year = int(timeUTC[0:4])
										month = int(timeUTC[5:7])
										day = int(timeUTC[8:10])
										
										hour = int(timeUTC[11:13])
										min = int(timeUTC[14:16])
										sec = int(timeUTC[17:19])
							
										utc = datetime.datetime(year, month, day, hour, min, sec, 0)
										local = utc - timedelta(hours=offset)
										self.log(4, f'INFO: GPS UTC time {utc}. Local time {local}. TZ Diff {offset}') 
										extra_data['AS_PIGPSUTC'] = str(utc)
										extra_data['AS_PIGPSLOCAL'] = str(local)
										extra_data['AS_PIGPSOFFSET'] = str(offset)                                
										date_string = utc.strftime("%c")
										os.system(f'sudo date -u --set="{date_string}"')
										result = 'Time set to {date_string}'
										break
							
							if time.time() > timeout:
								result = 'No date returned from gpsd'
								self.log(1, f'ERROR: {result}')
								break
					except Exception as err:
						result = f'No GPS found. Please check gpsd is configured and running - {err}'
						self.log(1, f'ERROR: {result}')                                                                                        
				else:
					result = "Time is synchronised from the internet - Ignoring any gps data"
					self.log(4, f'INFO: {result}')
			else:
				result = "Time update disabled"
				self.log(4, f"INFO: {result}")
			              
			try:
				if gpsd is None:
					gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
				timeout = time.time() + 3
				while True:
					report = gpsd.next()
					if report['class'] == 'TPV':
						mode = getattr(report,'mode',1)
						lat = getattr(report,'lat',0.0)
						lon = getattr(report,'lon',0.0)
						
						if mode != MODE_NO_FIX:
							if lat != 0 and lon != 0:
								
								if obfuscate:
									lat = lat + (obfuscate_lat_distance * ONEMETER)
									lon = lon + (obfuscate_lon_distance * ONEMETER)
									self.log(4, f"INFO: Offsetting latitude by {obfuscate_lat_distance}m and longitude by {obfuscate_lon_distance}m")
								discResult, discAllSkyLat, discAllSkyLon, strLat, strLon = self._compare_gps_and_allsky(lat, lon)
								if discResult:
									extra_data['AS_PIGPSFIXDISC'] = extra_data_pos_disc
								
								if set_position and discResult:
									updateData = []
									updateData.append({"latitude": strLat})
									updateData.append({"longitude": strLon})
									allsky_shared.updateSetting(updateData)
									self.log(4, f'INFO: AllSky Lat/Lon updated to {strLat},{strLon} - An AllSky restart will be required for them to take effect')
								else:
									if discResult:
										positionResult = f'GPS position differs from AllSky position. AllSky {discAllSkyLat} {discAllSkyLon}, GPS {strLat} {strLon}'
									else:
										positionResult = f'Lat {lat:.6f} Lon {lon:.6f} - {strLat},{strLon}'
									result = result + f'. {positionResult}'
									self.log(4, f'INFO: {positionResult}')
									
								extra_data['AS_PIGPSLAT'] = strLat
								extra_data['AS_PIGPSLON'] = strLon
								extra_data['AS_PIGPSFIX']['value'] = 'Yes'
								extra_data['AS_PIGPSFIX']['fill'] = '#00ff00'
								extra_data['AS_PIGPSFIXBOOL'] = 1
								break
							else:
								self.log(4, 'INFO: No GPS Fix. gpsd returned 0 for both lat and lon')
								break                       
						else:
							extra_data['AS_PIGPSFIX']['value'] = 'No'
							extra_data['AS_PIGPSFIX']['fill'] = '#ff0000'
							extra_data['AS_PIGPSFIXBOOL'] = 0
                  
					if time.time() > timeout:
						result = 'No position returned from gpsd'
						self.log(1, f'ERROR: {result}') 
						break                    
			
				allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
				allsky_shared.setLastRun('pigps')
   
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				result = f'ERROR: Module pigps failed on line {eTraceback.tb_lineno} - {e}'
				self.log(1, result)   
		else:
			result = f'Will run in {(period - diff):.0f} seconds'
			self.log(4, f'INFO: {result}')
   
		return result

def pigps(params, event):
	allsky_gps = ALLSKYGPS(params, event)
	result = allsky_gps.run()
 
	return result

def pigps_cleanup():
	moduleData = {
	    "metaData": ALLSKYGPS.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYGPS.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)