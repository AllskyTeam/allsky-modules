'''
allsky_pistatus.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import sys
import os
import shutil
from vcgencmd import Vcgencmd

metaData = {
    "name": "Reads Pi Status",
    "description": "Reads Pi Data",
    "version": "v1.0.0",    
    "events": [
        "day",
        "night",
        "periodic"
    ],
    "experimental": "true",    
    "arguments":{
        "period": 60
    },
    "argumentdetails": {
        "period" : {
            "required": "true",
            "description": "Read Every",
            "help": "Reads data every x seconds.",                
            "type": {
                "fieldtype": "spinner",
                "min": 60,
                "max": 1440,
                "step": 1
            }          
        }                   
    },
    "enabled": "false"            
}

tstats = {
    '0': 'Under-voltage detected',
    '1': 'Arm frequency capped',
    '2': 'Currently throttled',
    '3': 'Soft temperature limit active',
    '16': 'Under-voltage has occurred',
    '17': 'Arm frequency capping has occurred',
    '18': 'Throttling has occurred',
    '19': 'Soft temperature limit has occurred'
}

def formatSize(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.2fG" % (G)
        else:
            return "%.2fM" % (M)
    else:
        return "%.2fkb" % (kb)

def pistatus(params, event): 
    usage = shutil.disk_usage("/")
    size = formatSize(usage[0])
    used = formatSize(usage[1])
    free = formatSize(usage[2])

    os.environ['AS_DISKSIZE'] = str(size)
    os.environ['AS_DISKUSAGE'] = str(used)
    os.environ['AS_DISKFREE'] = str(free)

    vcgm = Vcgencmd()
    temp = vcgm.measure_temp();

    os.environ['AS_CPUTEMP'] = str(temp)

    throttled = vcgm.get_throttled()
    os.environ['AS_THROTTLEDBINARY'] = str(throttled['raw_data'])
    text = []
    for bit in tstats:
        key = 'AS_TSTAT' + bit
        os.environ[key] = str(throttled['breakdown'][bit])
        if throttled['breakdown'][bit]:
            textKey = key + 'TEXT'
            os.environ[textKey] = tstats[bit]
            text.append(tstats[bit])

    tstatText = ", ".join(text)
    os.environ['AS_TSTATSUMARYTEXT'] = tstatText

    return "PI Status Data Written"