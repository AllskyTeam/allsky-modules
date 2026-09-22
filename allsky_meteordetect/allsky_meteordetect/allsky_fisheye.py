"""allsky_fisheye.py — fisheye all-sky projection + geometric meteor radiant matching.

The camera geometry (centre, radial distortion, rotation, handedness) is a fixed,
time-independent property calibrated once with tools/calibrate_fisheye.py against a
plate-solved star field (see calibration.json). This module turns image pixels into
sky directions (altitude/azimuth) and back, and matches a meteor streak to the active
shower whose radiant lies on the streak's great circle.

Radial model (equidistant + cubic distortion):
    t = zenith_angle / 90 ;   r = a1*t + a3*t^3
    x = cx + r*sin(rot + flip*az) ;   y = cy - r*cos(rot + flip*az)

Depends only on numpy (+ json). No ephemeris files: sidereal time is computed from UTC.
"""
import json, math
import numpy as np

# Meteor shower radiants (J2000, degrees). Date windows live in the detector's SHOWERS
# table; here we only need the radiant position to test the geometry.
SHOWER_RADIANTS = {
    "Quadrantids":     (230.0, 49.0),
    "Lyrids":          (271.0, 34.0),
    "Eta Aquariids":   (338.0, -1.0),
    "Delta Aquariids": (340.0, -16.0),
    "Perseids":        (48.0,  58.0),
    "Orionids":        (95.0,  16.0),
    "Leonids":         (152.0, 22.0),
    "Geminids":        (112.0, 33.0),
    "Ursids":          (217.0, 76.0),
}


def load_calibration(path):
    with open(path) as fh:
        return json.load(fh)


def pixel_to_altaz(x, y, c):
    """Image pixel -> (altitude_deg, azimuth_deg from N, E positive per handedness)."""
    dx = x - c["cx"]
    dy = c["cy"] - y
    r = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dx, dy))          # screen angle, 0 = up
    az = ((ang - c["rot_deg"]) * c["flip"]) % 360.0
    # invert r = a1*t + a3*t^3 (monotonic) for t via Newton
    a1, a3 = c["a1"], c["a3"]
    t = min(1.5, r / a1)
    for _ in range(40):
        f = a1*t + a3*t**3 - r
        fp = a1 + 3*a3*t*t
        step = f/fp
        t = min(1.5, max(0.0, t - step))            # clamp: corners beyond the lens circle
        if abs(step) < 1e-7:
            break
    alt = 90.0 - t*90.0
    return alt, az


def altaz_to_pixel(alt, az, c):
    """(altitude_deg, azimuth_deg) -> image pixel (x, y)."""
    t = (90.0 - alt) / 90.0
    r = c["a1"]*t + c["a3"]*t**3
    ang = math.radians(c["rot_deg"] + c["flip"]*az)
    return c["cx"] + r*math.sin(ang), c["cy"] - r*math.cos(ang)


def _julian_day(u):
    """u = (Y, M, D, h, m, s) in UTC -> Julian Day."""
    Y, M, D, h, mi, s = u
    if M <= 2:
        Y -= 1; M += 12
    A = Y // 100; B = 2 - A + A // 4
    day = D + (h + mi/60.0 + s/3600.0) / 24.0
    return (math.floor(365.25*(Y + 4716)) + math.floor(30.6001*(M + 1))
            + day + B - 1524.5)


def local_sidereal_deg(utc, lon_east_deg):
    """Local apparent sidereal time in degrees (good to ~arcsec)."""
    jd = _julian_day(utc)
    d = jd - 2451545.0
    T = d / 36525.0
    gmst = (280.46061837 + 360.98564736629*d + 0.000387933*T*T - T*T*T/38710000.0)
    return (gmst + lon_east_deg) % 360.0


def radec_to_altaz(ra_deg, dec_deg, lst_deg, lat_deg):
    ra = math.radians(ra_deg); dec = math.radians(dec_deg)
    lat = math.radians(lat_deg); ha = math.radians(lst_deg) - ra
    alt = math.asin(math.sin(dec)*math.sin(lat) + math.cos(dec)*math.cos(lat)*math.cos(ha))
    az = math.atan2(math.sin(ha), math.cos(ha)*math.sin(lat) - math.tan(dec)*math.cos(lat))
    return math.degrees(alt), (math.degrees(az) + 180.0) % 360.0


def _unit(alt, az):
    a = math.radians(alt); z = math.radians(az)
    return np.array([math.cos(a)*math.sin(z),      # East
                     math.cos(a)*math.cos(z),      # North
                     math.sin(a)])                 # Up


def match_radiant(p1, p2, c, utc, active_showers, tol_deg=7.0):
    """Match a meteor streak (two pixel endpoints) to an active shower by geometry.

    A meteor moves along a great circle whose backward extension passes through the
    shower radiant. We test which active shower's radiant lies closest to that great
    circle (and is above the horizon). Returns (shower_name, separation_deg) or
    (None, None) for a sporadic / ambiguous meteor.
    """
    lat, lon = c["lat"], c["lon"]
    lst = local_sidereal_deg(utc, lon)
    a1 = pixel_to_altaz(p1[0], p1[1], c)
    a2 = pixel_to_altaz(p2[0], p2[1], c)
    v1, v2 = _unit(*a1), _unit(*a2)
    n = np.cross(v1, v2)
    nn = np.linalg.norm(n)
    if nn < 1e-9:
        return None, None
    n /= nn
    best = (None, 1e9)
    for name in active_showers:
        if name not in SHOWER_RADIANTS:
            continue
        ra, dec = SHOWER_RADIANTS[name]
        ralt, raz = radec_to_altaz(ra, dec, lst, lat)
        if ralt < 0:                                   # radiant below horizon: impossible
            continue
        vr = _unit(ralt, raz)
        sep = abs(math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(vr, n)))))))
        if sep < best[1]:
            best = (name, sep)
    if best[0] is not None and best[1] <= tol_deg:
        return best[0], round(best[1], 2)
    return None, None
