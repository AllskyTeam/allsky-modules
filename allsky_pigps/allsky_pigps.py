'''
allsky_pigps.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import os
import sys
import time
import datetime
import subprocess
from gps import *
from datetime import timedelta
    
metaData = {
    "name": "AllSKY GPS",
    "description": "Sets date/time and position from an attached GPS",
    "version": "v1.0.0",    
    "events": [
        "periodic"
    ],
    "arguments":{
        "warnposition": "True",
        "setposition": "False",
        "settime": "True",
        "timeperiod": "60",
        "extradatafilename": "pigps.json",
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
        "extradatafilename": {
            "required": "true",
            "description": "Extra Data Filename",
            "help": "The name of the file to create with the GPS data for th eoverlay manager"         
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
        }                           
    },
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

def checkTimeSyncRunning():
    active = False
    status = subprocess.check_output("timedatectl status | grep service", shell=True).decode("utf-8")
    status = status.splitlines()
    status = status[0].lower()
    if status.find(" active") > -1:
        active = True    

    synced = False
    status = subprocess.check_output("timedatectl status | grep System", shell=True).decode("utf-8")
    status = status.splitlines()
    status = status[0].lower()
    if status.find(" yes") > -1:
        synced = True
    s.log(4, "INFO: Time sync active {}, time synched {}".format(active, synced))

    result = False
    if active and synced:
        result = True
                        
    return result

def truncate(val):
    if '.' in val:
        val = val.split(".")
        val[1] = val[1][:3]
        val = ".".join(val)
    else:
        val = f'{val}.000'
    
    return val
    
def compareGPSandAllSky(lat, lon):
    allSkyLat = s.getSetting("latitude")
    allSkyLon = s.getSetting("longitude")

    allSkyLatCompass = allSkyLat[-1]
    allSkyLonCompass = allSkyLon[-1]
    
    allSkyLat = float(truncate(allSkyLat[:-1]))
    allSkyLon = float(truncate(allSkyLon[:-1]))
    
    allSkyLat = "{}{}".format(allSkyLat, allSkyLatCompass)
    allSkyLon = "{}{}".format(allSkyLon, allSkyLonCompass)
    
    if lat > 0:
        latCompass = "N"
    else:
        latCompass = "S"

    if lon > 0:
        lonCompass = "E"
    else:
        lonCompass = "W"

    lat = str(abs(lat))
    lon = str(abs(lon))

    lat = float(truncate(lat[:-1]))
    lon = float(truncate(lon[:-1]))

    lat = f"{lat}{latCompass}"
    lon = f"{lon}{lonCompass}"
    
    result = False
    if allSkyLat != lat or allSkyLon != lon:
        result = True
    
    return result, allSkyLat, allSkyLon, lat, lon
       
def deg_to_dms(deg, type='lat'):
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
 
def pigps(params, event):
    ONEMETER = 0.00001
    setposition = params['setposition']
    warnposition = params['warnposition']
    settime = params['settime']
    period = int(params['timeperiod'])
    extradatafilenam = params['extradatafilename']
    extradataposdisc = params['extradataposdisc']
    shouldRun, diff = s.shouldRun('pigps', period)

    obfuscate = params['obfuscate']    
    obfuscatelatdistance = int(params['obfuscatelatdistance'])
    obfuscatelondistance = int(params['obfuscatelondistance'])
        
    result = ""
    gpsd = None
    extraData = {
        "AS_PIGPSFIX": {
            "value": "No",
            "fill": "#ff0000"
        },
        "AS_PIGPSTIME": "Disabled",
        "AS_PIGPSUTC": "",
        "AS_PIGPSLOCAL": "",
        "AS_PIGPSOFFSET": "",        
        "AS_PIGPSLAT": "",
        "AS_PIGPSLON": "",
        "AS_PIGPSLATDEC": "",
        "AS_PIGPSLONDEC": "",
        "AS_PIGPSFIXDISC": ""
    }

    if shouldRun:
        if settime:
            if not checkTimeSyncRunning():
                try:
                    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
                    timeout = time.time() + 3
                    while True:
                        report = gpsd.next()
                        if report["class"] == 'TPV':
                            mode = getattr(report,'mode',1)
                            if mode != MODE_NO_FIX:                            
                                if settime:
                                    #s.log(4,"INFO: Got UTC date info {} from gpsd in {:.2f} seconds".format(gpsd.utc, timeout - time.time())) 
                                    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
                                    offset = offset / 60 / 60 * -1
                                    
                                    timeUTC = getattr(report,"time","")
                                    
                                    year = int(timeUTC[0:4])
                                    month = int(timeUTC[5:7])
                                    day = int(timeUTC[8:10])
                                    
                                    hour = int(timeUTC[11:13])
                                    min = int(timeUTC[14:16])
                                    sec = int(timeUTC[17:19])
                        
                                    utc = datetime.datetime(year, month, day, hour, min, sec, 0)
                                    local = utc - timedelta(hours=offset)
                                    s.log(4,"INFO: GPS UTC time {}. Local time {}. TZ Diff {}".format(utc, local, offset)) 
                                    extraData["AS_PIGPSUTC"] = str(utc)
                                    extraData["AS_PIGPSLOCAL"] = str(local)
                                    extraData["AS_PIGPSOFFSET"] = str(offset)                                
                                    dateString = utc.strftime("%c")
                                    os.system('sudo date -u --set="{}"'.format(dateString))
                                    result = "Time set to {}".format(dateString)
                                    break
                        
                        if time.time() > timeout:
                            result = "No date returned from gpsd"
                            s.log(1,"ERROR: {}".format(result)) 
                            break
                except Exception as err:
                    result = "No GPS found. Please check gpsd is configured and running - {}".format(err)
                    s.log(1,"ERROR: {}".format(result))                                                                                        
            else:
                result = "Time is synchronised from the internet - Ignoring any gps data"
                s.log(4,"INFO: {}".format(result))
        else:
            result = "Time update disabled"
            s.log(4, f"INFO: {result}")
        
        if warnposition or setposition:                
            try:
                if gpsd is None:
                    gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
                timeout = time.time() + 3
                while True:
                    report = gpsd.next()
                    if report["class"] == 'TPV':
                        mode = getattr(report,'mode',1)
                        lat = getattr(report,'lat',0.0)
                        lon = getattr(report,'lon',0.0)
                        
                        if mode != MODE_NO_FIX:
                            if lat != 0 and lon != 0:
                                
                                if obfuscate:
                                    lat = lat + (obfuscatelatdistance * ONEMETER)
                                    lon = lon + (obfuscatelondistance * ONEMETER)
                                    s.log(4, f"INFO: Offsetting latitude by {obfuscatelatdistance}m and longitude by {obfuscatelondistance}m")
                                discResult, discAllSkyLat, discAllSkyLon, strLat, strLon = compareGPSandAllSky(lat, lon)
                                if discResult:
                                    extraData["AS_PIGPSFIXDISC"] = extradataposdisc
                                
                                if setposition and discResult:
                                    updateData = []
                                    updateData.append({"latitude": strLat})
                                    updateData.append({"longitude": strLon})
                                    s.updateSetting(updateData)
                                    s.log(4, f"INFO: AllSky Lat/Lon updated to {strLat},{strLon} - An AllSky restart will be required for them to take effect")
                                else:
                                    if discResult:
                                        positionResult = f"GPS position differs from AllSky position. AllSky {discAllSkyLat} {discAllSkyLon}, GPS {strLat} {strLon}"
                                    else:
                                        positionResult = f"Lat {lat:.6f} Lon {lon:.6f} - {strLat},{strLon}"
                                    result = result + f". {positionResult}"
                                    s.log(4, f"INFO: {positionResult}")
                                    
                                extraData["AS_PIGPSLATDEC"] = strLat
                                extraData["AS_PIGPSLONDEC"] = strLon
                                extraData["AS_PIGPSLAT"] = deg_to_dms(lat, 'lat')
                                extraData["AS_PIGPSLON"] = deg_to_dms(lon, 'lon')
                                extraData["AS_PIGPSFIX"]["value"] = "Yes"
                                extraData["AS_PIGPSFIX"]["fill"] = "#00ff00"
                                break
                            else:
                                s.log(4, "INFO: No GPS Fix. gpsd returned 0 for both lat and lon")                            
                                break                       
                            
                    if time.time() > timeout:
                        result = "No position returned from gpsd"
                        s.log(1,"ERROR: {}".format(result)) 
                        break                    

            except Exception as e:
                eType, eObject, eTraceback = sys.exc_info()
                result = f"ERROR: Module pigps failed on line {eTraceback.tb_lineno} - {e}"
                s.log(1, result)

        else:
            positionResult = "Position update disabled"
            result = result + ". {}".format(positionResult)
            s.log(4, "INFO: {}".format(positionResult))  
        
        s.saveExtraData(extradatafilenam,extraData)
        s.setLastRun('pigps')
    else:
        result = "Will run in {:.0f} seconds".format(period - diff)
        s.log(4,"INFO: {}".format(result))
    return result

def pigps_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "pigps.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)