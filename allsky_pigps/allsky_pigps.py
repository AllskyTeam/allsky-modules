'''
allsky_pigps.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import os
import time
import datetime
import subprocess
import gps
from datetime import timedelta
    
metaData = {
    "name": "AllSKY GPS",
    "description": "Sets date/time and position from an attached GPS",
    "version": "v1.0.0",    
    "events": [
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "setposition": "True",
        "settime": "True",
        "timeperiod": "60"
    },
    "argumentdetails": {
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
        }
    }          
}

def checkTimeSyncRunning():
    result = False
    status = subprocess.check_output("timedatectl status | grep System", shell=True).decode("utf-8")
    status = status.splitlines()
    status = status[0].lower()
    if status.find(" yes") > -1:
        result = True
        
    return result

       
def pigps(params, event):
    
    setposition = params['setposition']
    settime = params['settime']
    period = int(params['timeperiod'])
    shouldRun, diff = s.shouldRun('pigps', period)
    result = ""
    
    if shouldRun:
        if not checkTimeSyncRunning():
            try:
                gpsd = gps.gps(mode=gps.WATCH_ENABLE)
                timeout = time.time() + 5
                while True:
                    gpsd.next()
                    if gpsd.utc != None and gpsd.utc != '':
                        if settime:
                            s.log(4,"INFO: Got UTC date info {} from gpsd in {:.2f} seconds".format(gpsd.utc, timeout - time.time())) 
                            offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
                            offset = offset / 60 / 60 * -1
                            
                            year = int(gpsd.utc[0:4])
                            month = int(gpsd.utc[5:7])
                            day = int(gpsd.utc[8:10])
                            
                            hour = int(gpsd.utc[11:13])
                            min = int(gpsd.utc[14:16])
                            sec = int(gpsd.utc[17:19])
                
                            utc = datetime.datetime(year, month, day, hour, min, sec, 0)
                            s.log(4,"INFO: Offset calculated as {}".format(offset)) 
                            s.log(4,"INFO: UTC date/time created as {}".format(utc)) 
                            local = utc - timedelta(hours=offset)
                            s.log(4,"INFO: Local date/time created as {}".format(local))
                            dateString = utc.strftime("%c")
                            s.log(4,"INFO: executing {}".format('sudo date -u --set="{}"'.format(dateString)))
                            os.system('sudo date -u --set="{}"'.format(dateString))
                            result = "Time set to {}".format(dateString)
                        else:
                            result = "Time update disabled"
                            s.log(4, "INFO: {}".format(result))                        
                            
                        if setposition:
                            if ((gps.isfinite(gpsd.fix.latitude) and gps.isfinite(gpsd.fix.longitude))):
                                lat = gpsd.fix.latitude
                                lon = gpsd.fix.longitude
                                
                                if (lat < 0):
                                    strLat = "{}S".format(lat)
                                else:
                                    strLat = "{}N".format(lat)

                                if (lon < 0):
                                    strLon = "{}W".format(lon)
                                else:
                                    strLon = "{}E".format(lon)
                                
                                updateData = []
                                updateData.append({"latitude": strLat})
                                updateData.append({"longitude": strLon})
                                s.updateSetting(updateData)
                                positionResult = "Lat {:.6f} Lon {:.6f} - {},{}".format(lat, lon, strLat, strLon)
                                result = result + ". {}".format(positionResult)
                                s.log(4, "INFO: {}".format(positionResult))
                            else:
                                s.log(4, "INFO: Lat n/a Lon n/a")
                        else:
                            positionResult = "Position update disabled"
                            result = result + ". {}".format(positionResult)
                            s.log(4, "INFO: {}".format(positionResult))                        
                        break
                    if time.time() > timeout:
                        result = "Invalid date returned from gpsd"
                        s.log(1,"ERROR: {}".format(result)) 
                        break
            except Exception as err:
                result = "No GPS found. Please check gpsd is configured and running - {}".format(err)
                s.log(1,"ERROR: {}".format(result))
        else:
            result = "Time is synchronised from the internet - Ignoring any gps data"
            s.log(4,"INFO: {}".format(result))
        
        s.setLastRun('pigps')
    else:
        result = "Will run in {:.0f} seconds".format(period - diff)
        s.log(4,"INFO: {}".format(result))
    return result