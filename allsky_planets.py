import allsky_shared as s
import os
import math
from skyfield.api import load, wgs84, Loader
from skyfield.api import N, S, E, W
from skyfield import almanac
# from astropy import units as u

metaData = {
    "name": "Planets AltAZ degrees",
    "description": "Export Planets AltAZ degrees",
    "events": [
        "night",
        "day"
    ],
    "experimental": "true",
    "module": "allsky_planets",
    "arguments": {
    },
    "argumentdetails": {
    }
}

_enableSkyfield = True
try:
    _eph = load('de421.bsp')
except Exception as err:
    _enableSkyfield = False
_observerLat = s.getSetting('latitude')
_observerLon = s.getSetting('longitude')

def _convertLatLon(input):
    """ lat and lon can either be a positive or negative float, or end with N, S, E,or W. """
    """ If in  N, S, E, W format, 0.2E becomes -0.2 """
    nsew = 1 if input[-1] in ['N', 'S', 'E', 'W'] else 0
    if nsew:
        multiplier = 1 if input[-1] in ['N', 'E'] else -1
        ret = multiplier * sum(s.float(x) / 60 ** n for n, x in enumerate(input[:-1].split('-')))
    else:
        ret = float(input)
    return ret

def planets(params, event):

    if _enableSkyfield:
        planets = {
            'MERCURY BARYCENTER',
            'VENUS BARYCENTER',
            'MARS BARYCENTER',
            'JUPITER BARYCENTER',
            'SATURN BARYCENTER',
        }
        ts = load.timescale()
        t = ts.now()
        earth = _eph['earth']

        home = earth + wgs84.latlon(_convertLatLon(_observerLat), _convertLatLon(_observerLon))

        for planetId in planets:
            planet = _eph[planetId]
            astrometric = home.at(t).observe(planet)
            alt, az, d = astrometric.apparent().altaz()
            side = "W"
            if az.degrees <= 180:
                side = "E"

            os.environ['AS_' + planetId.replace(' BARYCENTER','') + 'ALTdeg'] = str(round(alt.degrees,1))
            os.environ['AS_' + planetId.replace(' BARYCENTER','') + 'AZdeg'] = str(round(az.degrees,1))
            os.environ['AS_' + planetId.replace(' BARYCENTER','') + 'AZSide'] = str(side)
    else:
        s.log(4, 'INFO: Planets module error.')
        
    result ="planets altaz data written"
    s.log(1, "INFO {0}".format(result))
    
    return result
