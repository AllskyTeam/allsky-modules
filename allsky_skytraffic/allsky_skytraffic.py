""" allsky_skytraffic.py

Names the satellites and aircraft that cross the image, for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)

A night image of an all-sky camera is full of moving things: satellites,
aircraft, the odd rocket body.  This module knows where they were while the
image was exposed and puts names to them:

  * Satellites: orbital elements (TLE) from CelesTrak, downloaded once a day and
    kept on disk.  For every night image the position of each satellite is
    computed for the start, middle and end of the exposure with PyEphem, and
    whether it is in sunlight (only a sunlit satellite can leave a trail).
  * Aircraft: optional, from a local ADS-B receiver (readsb / dump1090
    aircraft.json) or a free online feed (adsb.fi, adsb.lol).  Each aircraft is
    moved back to the exposure with its speed and track.
  * The positions are projected into the image with the lens model: the
    fisheye calibration (calibration.json, made with the Meteor Detection
    module's tools) if there is one, else an equidistant fisheye from the image
    centre, the horizon radius and "North in the image".

With that the module
  * names the streaks the Meteor Detection module rejected as "moving"
    (satellite / aircraft), and warns when a saved meteor lies on the track of
    a known satellite or aircraft;
  * checks along each predicted satellite track whether a trail is really in
    the image ("seen"), which counts the satellites the camera records;
  * lists the next bright satellite passes (ISS, Tiangong, the brightest
    satellites and rocket bodies) and ISS / Tiangong transits across the Moon
    or Sun, for the overlay;
  * saves the counts in the Allsky database for the charts it brings along.
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import json
import math
import time
import cv2
import numpy as np


class ALLSKYSKYTRAFFIC(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Sky Traffic",
        "description": "Names the satellites and aircraft crossing the image and lists the next bright passes",
        "version": "v0.1.0",
        "module": "allsky_skytraffic",
        "events": [
            "night",
            "day"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_skytraffic.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_skytraffic",
                "pk": "id",
                "pk_type": "int",
                "include_all": "false",
                "time_of_day_save": {
                    "day": "never",
                    "night": "always",
                    "nightday": "never",
                    "daynight": "never",
                    "periodic": "never"
                }
            },
            "values": {
                "AS_SKYTRAFFIC_SATS": {
                    "name": "${SKYTRAFFIC_SATS}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Sunlit satellites above the horizon during the exposure",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_SEEN": {
                    "name": "${SKYTRAFFIC_SEEN}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Satellites whose trail is in the image",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_SEEN_NAMES": {
                    "name": "${SKYTRAFFIC_SEEN_NAMES}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Names of the satellites whose trail is in the image",
                    "type": "string"
                },
                "AS_SKYTRAFFIC_AIRCRAFT": {
                    "name": "${SKYTRAFFIC_AIRCRAFT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Aircraft in the image during the exposure (needs an ADS-B source)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_NAMED_SATS": {
                    "name": "${SKYTRAFFIC_NAMED_SATS}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Streaks rejected by the Meteor Detection module that were named as satellites",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_NAMED_AIRCRAFT": {
                    "name": "${SKYTRAFFIC_NAMED_AIRCRAFT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Streaks rejected by the Meteor Detection module that were named as aircraft",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_UNNAMED": {
                    "name": "${SKYTRAFFIC_UNNAMED}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Streaks rejected by the Meteor Detection module that no known satellite or aircraft explains",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_NAMES": {
                    "name": "${SKYTRAFFIC_NAMES}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Names given to the rejected streaks",
                    "type": "string"
                },
                "AS_SKYTRAFFIC_METEOR_SUSPECT": {
                    "name": "${SKYTRAFFIC_METEOR_SUSPECT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Saved meteors that lie on the track of a known satellite or aircraft",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYTRAFFIC_NEXT": {
                    "name": "${SKYTRAFFIC_NEXT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Next bright satellite pass, e.g. 'ISS 21:34 67° SW-NE'",
                    "type": "string"
                },
                "AS_SKYTRAFFIC_NEXT_ISS": {
                    "name": "${SKYTRAFFIC_NEXT_ISS}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Next visible pass of the ISS",
                    "type": "string"
                },
                "AS_SKYTRAFFIC_TRANSIT": {
                    "name": "${SKYTRAFFIC_TRANSIT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Traffic",
                    "description": "Next ISS or Tiangong transit across (or close pass by) the Moon or Sun",
                    "type": "string"
                }
            }
        },
        "arguments": {
            "satellites": "true",
            "tle_groups": "active,visual",
            "tle_refresh_hours": "24",
            "aircraft_source": "None",
            "aircraft_url": "",
            "aircraft_radius": "60",
            "site_height": "0",
            "min_altitude": "10",
            "calibration": "calibration.json",
            "north_angle": "0",
            "east_left": "true",
            "horizon_radius": "0",
            "meteor_folder": "",
            "match_tolerance": "0.6",
            "detect_trails": "true",
            "trail_snr": "8",
            "mark_image": "false",
            "passes_hours": "12",
            "pass_min_altitude": "30",
            "transits": "true",
            "publish_web": "false",
            "debug": "false",
            "graph": ""
        },
        "argumentdetails": {
            "satellites": {
                "required": "false",
                "description": "Satellites",
                "help": "Compute where the satellites were during each night image. Needs internet once a day for the orbital elements (CelesTrak).",
                "tab": "Sources",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "tle_groups": {
                "required": "false",
                "description": "Satellite groups",
                "help": "CelesTrak groups to load, separated by commas. 'active' is every working satellite (about 16,000, including Starlink), 'visual' adds the brightest satellites and rocket bodies. Smaller: 'stations,visual,starlink'.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "text"
                }
            },
            "tle_refresh_hours": {
                "required": "false",
                "description": "Refresh the orbital elements every (hours)",
                "help": "How old the downloaded orbital elements may get. CelesTrak asks not to download the same data more often than every 2 hours; once a day keeps the positions accurate to a few kilometres.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 168,
                    "step": 1
                }
            },
            "aircraft_source": {
                "required": "false",
                "description": "Aircraft source",
                "help": "Where the aircraft positions come from. 'Local' is your own ADS-B receiver (readsb, dump1090 or tar1090 aircraft.json, set the URL below). adsb.fi and adsb.lol are free online feeds without a key. The positions are read when the image is processed and moved back to the exposure.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "select",
                    "values": "None,Local,adsb.fi,adsb.lol",
                    "default": "None"
                }
            },
            "aircraft_url": {
                "required": "false",
                "description": "Local ADS-B URL",
                "help": "Only for 'Local': the aircraft.json of your receiver, e.g. http://192.168.1.20/tar1090/data/aircraft.json",
                "tab": "Sources",
                "type": {
                    "fieldtype": "text"
                }
            },
            "aircraft_radius": {
                "required": "false",
                "description": "Aircraft search radius (km)",
                "help": "Only aircraft within this distance are used. An aircraft at 10 km height and 60 km away is 9 degrees above the horizon.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "spinner",
                    "min": 5,
                    "max": 250,
                    "step": 5
                }
            },
            "site_height": {
                "required": "false",
                "description": "Camera height above sea level (m)",
                "help": "Only used for aircraft, whose height comes as height above sea level.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "spinner",
                    "min": -100,
                    "max": 5000,
                    "step": 10
                }
            },
            "min_altitude": {
                "required": "false",
                "description": "Lowest altitude (deg)",
                "help": "Objects lower than this above the horizon are ignored.",
                "tab": "Lens",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 45,
                    "step": 1
                }
            },
            "calibration": {
                "required": "false",
                "description": "Fisheye calibration file",
                "help": "calibration.json in the modules folder, made with the Meteor Detection module's tools (tools/calibrate_fisheye.py). With it the positions are accurate to a fraction of a degree. Without it an equidistant fisheye is assumed from the three settings below.",
                "tab": "Lens",
                "type": {
                    "fieldtype": "text"
                }
            },
            "north_angle": {
                "required": "false",
                "description": "North in the image (deg)",
                "help": "Only without a calibration: where North is, in degrees clockwise from the top of the image (0 = North is up). The Website's constellation overlay 'az' setting is a good value to start with.",
                "tab": "Lens",
                "type": {
                    "fieldtype": "spinner",
                    "min": -180,
                    "max": 360,
                    "step": 1
                }
            },
            "east_left": {
                "required": "false",
                "description": "East is left of North",
                "help": "Only without a calibration: on for a normal view of the sky from below (East is 90 degrees counter-clockwise from North), off for a mirrored image.",
                "tab": "Lens",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "horizon_radius": {
                "required": "false",
                "description": "Horizon radius (pixels)",
                "help": "Only without a calibration: distance from the image centre to the horizon, in pixels of the full image. 0 = half the image height.",
                "tab": "Lens",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 10000,
                    "step": 10
                }
            },
            "meteor_folder": {
                "required": "false",
                "description": "Meteor Detection folder",
                "help": "Where the Meteor Detection module writes meteors.json and meteors_vetoed.json. Empty = its default, the Website's meteors folder.",
                "tab": "Matching",
                "type": {
                    "fieldtype": "text"
                }
            },
            "match_tolerance": {
                "required": "false",
                "description": "Match tolerance (deg)",
                "help": "How far a streak may lie from a predicted track and still get its name. With a calibration the positions are good to about 0.3 degrees. Larger values name more streaks, but also wrongly: Starlink satellites fly in trains along the same track. Without a calibration, raise it to 3-4 degrees.",
                "tab": "Matching",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.3,
                    "max": 10,
                    "step": 0.1
                }
            },
            "detect_trails": {
                "required": "false",
                "description": "Look for the trails",
                "help": "Check along every predicted satellite track whether a trail is in the image (compared with the previous image, so stars cancel). This gives the number of satellites your camera really records.",
                "tab": "Matching",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "trail_snr": {
                "required": "false",
                "description": "Trail threshold",
                "help": "How far above the noise a trail must stand out along the predicted track. Lower finds fainter trails and more false ones.",
                "tab": "Matching",
                "type": {
                    "fieldtype": "spinner",
                    "min": 4,
                    "max": 30,
                    "step": 1
                }
            },
            "mark_image": {
                "required": "false",
                "description": "Mark them in the image",
                "help": "Draw the tracks and names of the satellites that were seen and of the aircraft into the saved image. Put this module AFTER the Meteor Detection module, otherwise the drawn lines look like new streaks to it.",
                "tab": "Matching",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "passes_hours": {
                "required": "false",
                "description": "Look ahead (hours)",
                "help": "How far ahead the next bright passes and transits are computed (once an hour).",
                "tab": "Passes",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 48,
                    "step": 1
                }
            },
            "pass_min_altitude": {
                "required": "false",
                "description": "Lowest culmination (deg)",
                "help": "Only passes that climb at least this high are listed.",
                "tab": "Passes",
                "type": {
                    "fieldtype": "spinner",
                    "min": 10,
                    "max": 80,
                    "step": 5
                }
            },
            "transits": {
                "required": "false",
                "description": "ISS / Tiangong transits",
                "help": "Look for passes of the ISS and Tiangong across (or within a degree of) the Moon and Sun. A transit is only seen from a strip a few kilometres wide, so it is rare at a fixed camera.",
                "tab": "Passes",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to the website",
                "help": "Every 15 minutes, copy the pass list and the logs of the trails seen and named (skytraffic_passes.json, skytraffic_seen.json, skytraffic_named.json) into the Website's skytraffic folder, and upload them to a remote website. The remote 'skytraffic' folder must exist: the upload does not create folders.",
                "tab": "Passes",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "debug": {
                "required": "false",
                "description": "Debug",
                "help": "Write the predicted tracks into a debug image.",
                "tab": "Passes",
                "type": {
                    "fieldtype": "checkbox"
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
            "v0.1.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Satellite positions for every night image from CelesTrak orbital elements (downloaded once a day), projected into the image with the fisheye calibration or an equidistant lens",
                        "Aircraft from a local ADS-B receiver, adsb.fi or adsb.lol, moved back to the exposure",
                        "Names the streaks the Meteor Detection module rejected as moving, and warns when a saved meteor lies on the track of a known satellite or aircraft",
                        "Looks for the trail along every predicted satellite track and counts the satellites the camera records",
                        "Next bright passes and ISS / Tiangong transits of the Moon and Sun for the overlay",
                        "Values are saved in the Allsky database; the module brings charts"
                    ]
                }
            ]
        }
    }

    def run(self):
        try:
            return _run(self)
        except Exception as e:
            _, _, tb = sys.exc_info()
            result = f"Module Sky Traffic failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(s.ALLSKY_TMP, "allsky_skytraffic_state.json")
PREV_FRAME = os.path.join(s.ALLSKY_TMP, "allsky_skytraffic_prev.png")
CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php?GROUP={}&FORMAT=tle"
HEADERS = {"User-Agent": "Allsky-SkyTraffic/0.1 (+https://github.com/AllskyTeam/allsky-modules)"}
BRIGHT_GROUPS = ("stations", "visual")     # the pass list is made from these
STATIONS = ("ISS (ZARYA)", "CSS (TIANHE)")
UNIX_EPOCH = 25567.5                       # ephem.Date('1970/1/1')
KEEP_FRAMES = 8                            # frames kept to match late Meteor Detection results
MIN_TRACK_PX = 60                          # a streak shorter than this is too short to test
WORK_WIDTH = 1600                          # the trail search runs on an image this wide
TRAIL_TOL_DEG = 0.3                        # a trail must lie this close to the track (calibrated lens)
ANGLE_TOL = 8.0                            # streak direction vs track direction (deg)


def _truthy(v):
    """Checkbox args arrive from the flow config as the STRING 'true'/'false'."""
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _edate(t):
    """Unix time -> ephem date."""
    import ephem
    return ephem.Date(t / 86400.0 + UNIX_EPOCH)


def _imageTime():
    """Start of the exposure (AS_TIMESTAMP), else now."""
    try:
        return int(s.get_environment_variable("AS_TIMESTAMP"))
    except (TypeError, ValueError):
        return int(time.time())


def _exposure():
    """Exposure in seconds (AS_EXPOSURE_US), else 1 s."""
    try:
        return max(0.001, int(s.get_environment_variable("AS_EXPOSURE_US")) / 1e6)
    except (TypeError, ValueError):
        return 1.0


def _site():
    return (float(s.convertLatLon(s.getSetting("latitude"))),
            float(s.convertLatLon(s.getSetting("longitude"))))


def _observer(lat, lon, t=None):
    import ephem
    o = ephem.Observer()
    o.lat, o.lon = str(lat), str(lon)
    o.pressure = 0                      # no refraction: satellites are computed geometrically
    if t is not None:
        o.date = _edate(t)
    return o


def _dataDir():
    base = os.environ.get("ALLSKY_MYFILES_DIR") or _MODULE_DIR
    path = os.path.join(base, "skytraffic")
    os.makedirs(path, exist_ok=True)
    return path


def _readState():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {}


def _writeState(st):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh)
    os.replace(tmp, STATE_FILE)


def _compass(az):
    return ("N", "NE", "E", "SE", "S", "SW", "W", "NW")[int(((az % 360) + 22.5) // 45) % 8]


# --- orbital elements --------------------------------------------------------

def _download(groups, refresh_h, st, module):
    """Keep one TLE file per CelesTrak group in the data folder, refreshed every
    refresh_h hours.  A failed download is retried after an hour; the old file
    stays in use."""
    import requests
    folder = _dataDir()
    tried = st.setdefault("tle_tried", {})
    for g in groups:
        path = os.path.join(folder, f"tle-{g}.txt")
        age = time.time() - os.path.getmtime(path) if os.path.isfile(path) else 1e12
        if age < max(2.0, refresh_h) * 3600 or time.time() - tried.get(g, 0) < 3600:
            continue
        tried[g] = time.time()
        try:
            r = requests.get(CELESTRAK.format(g), timeout=30, headers=HEADERS)
            lines = [ln.rstrip() for ln in r.text.splitlines() if ln.strip()]
            if r.status_code != 200 or len(lines) < 3 or not lines[1].startswith("1 "):
                raise ValueError(f"HTTP {r.status_code}: {r.text[:80]!r}")
            with open(path + ".tmp", "w") as fh:
                fh.write("\n".join(lines) + "\n")
            os.replace(path + ".tmp", path)
            module.log(4, f"INFO: Sky Traffic loaded {len(lines) // 3} satellites of group '{g}'")
        except Exception as ex:
            module.log(1, f"WARNING: Sky Traffic could not download the satellite group '{g}': {ex}")


def _satellites(groups):
    """{norad: (name, ephem body)} from the cached TLE files of these groups."""
    import ephem
    sats = {}
    for g in groups:
        path = os.path.join(_dataDir(), f"tle-{g}.txt")
        if not os.path.isfile(path):
            continue
        with open(path) as fh:
            lines = fh.read().splitlines()
        for i in range(0, len(lines) - 2, 3):
            l1, l2 = lines[i + 1], lines[i + 2]
            if not (l1.startswith("1 ") and l2.startswith("2 ")):
                continue
            norad = l1[2:7]
            if norad in sats:
                continue
            try:
                sats[norad] = (lines[i].strip(), ephem.readtle(lines[i].strip(), l1, l2))
            except Exception:
                pass
    return sats


# --- lens --------------------------------------------------------------------

class _Lens:
    """alt/az <-> pixel.  Cubic equidistant fisheye as fitted by the Meteor
    Detection module's calibrate_fisheye.py:
        t = zenith_angle / 90;  r = a1*t + a3*t^3
        x = cx + r*sin(rot + flip*az);  y = cy - r*cos(rot + flip*az)
    Without a calibration a3 = 0 and the rest comes from the settings."""

    def __init__(self, params, shape):
        h, w = shape[:2]
        self.calibrated = False
        c = self._load(params["calibration"].strip())
        if c is not None:
            W, H = float(c.get("W", w)), float(c.get("H", h))
            sx, sy = w / W, h / H
            if abs(sx - sy) < 0.01 * sx:            # resized, not cropped
                self.cx, self.cy = c["cx"] * sx, c["cy"] * sx
                self.a1, self.a3 = c["a1"] * sx, c["a3"] * sx
                self.rot, self.flip = float(c["rot_deg"]), float(c["flip"])
                self.calibrated = True
        if not self.calibrated:
            radius = s.asfloat(params["horizon_radius"]) or h / 2.0
            self.cx, self.cy = w / 2.0, h / 2.0
            self.a1, self.a3 = radius, 0.0
            self.rot = s.asfloat(params["north_angle"])
            self.flip = -1.0 if _truthy(params["east_left"]) else 1.0
        self.horizon = self.a1 + self.a3
        self.px_per_deg = (self.a1 + 3 * self.a3 * 0.25) / 90.0   # scale at 45 deg altitude
        self.w, self.h = w, h

    @staticmethod
    def _load(name):
        if not name:
            return None
        path = name if os.path.isabs(name) else os.path.join(_MODULE_DIR, name)
        try:
            with open(path) as fh:
                c = json.load(fh)
            return c if all(k in c for k in ("cx", "cy", "a1", "a3", "rot_deg", "flip")) else None
        except Exception:
            return None

    def project(self, alt, az):
        t = (90.0 - alt) / 90.0
        r = self.a1 * t + self.a3 * t ** 3
        a = math.radians(self.rot + self.flip * az)
        return self.cx + r * math.sin(a), self.cy - r * math.cos(a)

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and math.hypot(x - self.cx, y - self.cy) < self.horizon


# --- what was in the sky during the exposure -----------------------------------

def _satelliteTracks(sats, lat, lon, t0, exp, lens, min_alt):
    """Sunlit satellites above min_alt during the exposure, as image tracks."""
    obs = _observer(lat, lon)
    n = 7 if exp >= 10 else 3
    times = [t0 + exp * k / (n - 1) for k in range(n)]
    gate = math.radians(min_alt - 1.3 * exp / 2 - 1)      # LEO moves at most ~1.2 deg/s
    tracks, up = [], 0
    for norad, (name, body) in sats.items():
        obs.date = _edate(t0 + exp / 2)
        try:
            body.compute(obs)
        except Exception:
            continue
        if body.alt < gate:
            continue
        pts, lit, alts = [], [], []
        try:
            for t in times:
                obs.date = _edate(t)
                body.compute(obs)
                alt, az = math.degrees(body.alt), math.degrees(body.az)
                alts.append(alt)
                pts.append(lens.project(alt, az))
                lit.append(not body.eclipsed)
        except Exception:
            continue
        vis = [a >= min_alt and l for a, l in zip(alts, lit)]
        if not any(vis):
            continue
        up += 1
        if not any(lens.inside(x, y) for (x, y), v in zip(pts, vis) if v):
            continue
        tracks.append({"name": name, "kind": "satellite", "id": norad,
                       "pts": [[round(x, 1), round(y, 1)] for x, y in pts], "lit": vis,
                       "alt": round(max(alts), 1)})
    return tracks, up


def _fetchAircraft(params, lat, lon):
    """Aircraft list in readsb format and the time of the data."""
    import requests
    src = params["aircraft_source"].strip().lower()
    km = s.asfloat(params["aircraft_radius"])
    nm = max(1, min(250, int(round(km / 1.852))))
    if src == "local":
        url = params["aircraft_url"].strip()
        if not url:
            raise ValueError("no local ADS-B URL set")
    elif src == "adsb.fi":
        url = f"https://opendata.adsb.fi/api/v2/lat/{lat:.4f}/lon/{lon:.4f}/dist/{nm}"
    elif src == "adsb.lol":
        url = f"https://api.adsb.lol/v2/point/{lat:.4f}/{lon:.4f}/{nm}"
    else:
        return [], time.time()
    r = requests.get(url, timeout=8, headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    return d.get("aircraft") or d.get("ac") or [], float(d.get("now") or time.time())


def _aircraftAltAz(lat, lon, h_site, alat, alon, h_ac):
    """Altitude/azimuth of a point from the site: local east/north/up with the
    Earth's curvature (good to a small fraction of a degree within 250 km)."""
    R = 6371000.0
    north = math.radians(alat - lat) * R
    east = math.radians(alon - lon) * R * math.cos(math.radians(lat))
    d = math.hypot(east, north)
    up = h_ac - h_site - d * d / (2 * R)
    return math.degrees(math.atan2(up, d)), math.degrees(math.atan2(east, north)) % 360.0, d


def _aircraftTracks(aircraft, now, lat, lon, h_site, t0, exp, lens, min_alt, radius_m):
    tracks = []
    times = [t0, t0 + exp / 2, t0 + exp]
    for a in aircraft:
        try:
            alat, alon = float(a["lat"]), float(a["lon"])
            h = a.get("alt_geom", a.get("alt_baro"))
            if h in (None, "ground"):
                continue
            h = float(h) * 0.3048
            gs = float(a.get("gs") or 0) * 0.514444
            trk = math.radians(float(a.get("track") or 0))
            tpos = now - float(a.get("seen_pos") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        pts, alts = [], []
        for t in times:
            dist = gs * (t - tpos)
            plat = alat + math.degrees(dist * math.cos(trk) / 6371000.0)
            plon = alon + math.degrees(dist * math.sin(trk) / (6371000.0 * math.cos(math.radians(alat))))
            alt, az, d = _aircraftAltAz(lat, lon, h_site, plat, plon, h)
            if d > radius_m:
                alt = -90.0
            alts.append(alt)
            pts.append(lens.project(max(alt, -5.0), az))
        vis = [x >= min_alt for x in alts]
        if not any(vis) or not any(lens.inside(x, y) for (x, y), v in zip(pts, vis) if v):
            continue
        name = (a.get("flight") or "").strip() or a.get("r") or a.get("hex", "?")
        if a.get("t"):
            name += f" ({a['t']})"
        tracks.append({"name": name, "kind": "aircraft", "id": a.get("hex", ""),
                       "pts": [[round(x, 1), round(y, 1)] for x, y in pts], "lit": vis,
                       "alt": round(max(alts), 1)})
    return tracks


# --- matching streaks to tracks ----------------------------------------------

def _angDiff(a, b):
    """Difference of two undirected line angles in degrees (0..90)."""
    return abs((a - b + 90.0) % 180.0 - 90.0)


def _distance(track, cx, cy, ang, slack):
    """Perpendicular distance of a streak centre from a track, if the streak runs
    along it.  The ends are extended by `slack` (fraction of the track) for the
    timing uncertainty.  Returns (distance, angle difference)."""
    pts = [p for p, v in zip(track["pts"], track["lit"]) if v] or track["pts"]
    if len(pts) < 2:
        return 1e9, 90.0
    best = (1e9, 90.0)
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 < 1e-6:
            continue
        u = ((cx - x1) * dx + (cy - y1) * dy) / L2
        lo = -slack * (len(pts) - 1) if i == 0 else 0.0
        hi = 1.0 + slack * (len(pts) - 1) if i == len(pts) - 2 else 1.0
        if not lo <= u <= hi:
            continue
        d = math.hypot(x1 + u * dx - cx, y1 + u * dy - cy)
        if d < best[0]:
            best = (d, _angDiff(math.degrees(math.atan2(dy, dx)) % 180.0, ang))
    return best


def _identify(tracks, cx, cy, ang, tol_px, ang_tol=ANGLE_TOL):
    """The track a streak belongs to, or None.  A satellite's streak must lie on
    the part of its track it covered during the exposure (the times are exact);
    an aircraft gets more room, its position is extrapolated."""
    best = None
    for tr in tracks:
        d, da = _distance(tr, cx, cy, ang, 0.1 if tr["kind"] == "satellite" else 0.5)
        if d <= tol_px and da <= ang_tol and (best is None or d < best[1]):
            best = (tr, d)
    return best


def _meteorFolder(params):
    folder = params["meteor_folder"].strip()
    if folder:
        return folder
    website = s.getEnvironmentVariable("ALLSKY_WEBSITE") or os.path.join(
        s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "html", "allsky")
    return os.path.join(website, "meteors")


def _stampTime(stamp):
    return time.mktime(time.strptime(stamp, "%Y%m%d%H%M%S"))


def _frameFor(frames, stamp):
    """The stored frame the Meteor Detection module processed at `stamp` (it stamps
    a streak with the time it ran on that frame; both modules run in the same flow)."""
    try:
        t = _stampTime(stamp)
    except ValueError:
        return None
    best = min(frames, key=lambda f: abs(f["run"] - t), default=None)
    return best if best is not None and abs(best["run"] - t) <= 60 else None


def _nameStreaks(params, st, frames, tol_px, module):
    """Name the new 'moving' rejects in meteors_vetoed.json and check the new
    meteors in meteors.json against the stored tracks."""
    folder = _meteorFolder(params)
    named, suspects = [], []
    for fname, key, is_meteor in (("meteors_vetoed.json", "last_vetoed", False),
                                  ("meteors.json", "last_meteor", True)):
        path = os.path.join(folder, fname)
        try:
            with open(path) as fh:
                recs = json.load(fh)
        except Exception:
            continue
        last = st.get(key)
        if last is None:                 # first run: start from now, don't replay the past
            st[key] = max([r.get("time", "") for r in recs] + [""])
            continue
        newest = max(f["run"] for f in frames)
        for r in sorted(recs, key=lambda r: r.get("time", "")):
            stamp = r.get("time", "")
            if stamp <= last:
                continue
            try:
                if _stampTime(stamp) > newest + 60:
                    break                # a frame this module has not processed yet
            except ValueError:
                continue
            st[key] = stamp
            if not is_meteor and r.get("reason") != "moving":
                continue
            frame = _frameFor(frames, stamp)
            if frame is None:
                continue                 # not ours yet: taken before this module started
            cx, cy = r.get("cx"), r.get("cy")
            ang = r.get("angle", r.get("ang"))
            if None in (cx, cy, ang):
                continue
            hit = _identify(frame["tracks"], cx, cy, ang, tol_px)
            rec = {"time": stamp, "cx": cx, "cy": cy, "len": r.get("len", r.get("length")),
                   "reason": "meteor" if is_meteor else "moving"}
            if hit:
                rec.update(name=hit[0]["name"], kind=hit[0]["kind"], dist=round(hit[1], 1))
            if is_meteor:
                if hit:
                    suspects.append(rec)
                    module.log(1, f"WARNING: Sky Traffic: the meteor at {stamp} lies on the track of "
                                  f"{hit[0]['name']} ({hit[0]['kind']}, {hit[1]:.0f} px)")
            else:
                named.append(rec)
    if named or suspects:
        path = os.path.join(_dataDir(), "skytraffic_named.json")
        try:
            with open(path) as fh:
                log = json.load(fh)
        except Exception:
            log = []
        log.extend(named + suspects)
        with open(path, "w") as fh:
            json.dump(log[-1000:], fh)
    return named, suspects


# --- are the trails in the image? --------------------------------------------

def _workImage(img):
    """Grey working copy WORK_WIDTH wide (float32) and its scale."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    sc = min(1.0, WORK_WIDTH / float(g.shape[1]))
    if sc < 1.0:
        g = cv2.resize(g, (int(g.shape[1] * sc), int(g.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    return g, sc


def _trailImage(g, prev_path, max_age):
    """Frame difference with the previous image, so the stars cancel, slightly
    blurred so a 1-2 px trail is sampled.  None without a recent previous image:
    the image alone has too many stars along a track to trust a faint trail."""
    prev = None
    if os.path.isfile(prev_path) and time.time() - os.path.getmtime(prev_path) < max_age:
        prev = cv2.imread(prev_path, cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(prev_path, g)
    if prev is None or prev.shape != g.shape:
        return None
    return cv2.GaussianBlur(g.astype(np.float32) - prev.astype(np.float32), (0, 0), 1.2)


def _trailSeen(d, track, lens, sc, tol_px, snr_min, accept_px):
    """Mean brightness along the lit part of a predicted track, shifted sideways
    in steps of a pixel.  A real trail makes a narrow peak close to offset 0,
    and it does so along the whole track: the peak must also show in at least
    two of the track's three thirds.  A drifting cloud edge is broad or local
    and fails one of the two.
    Returns the offset (full-image px) if seen, else None."""
    pts = np.array([p for p, v in zip(track["pts"], track["lit"]) if v], dtype=np.float64) * sc
    if len(pts) < 2:
        return None
    seg = np.hypot(*np.diff(pts, axis=0).T)
    if seg.sum() < MIN_TRACK_PX * sc * 2:
        return None
    n = int(min(900, max(60, seg.sum())))
    s_ = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s_[-1], n)
    X, Y = np.interp(u, s_, pts[:, 0]), np.interp(u, s_, pts[:, 1])
    dx, dy = np.gradient(X), np.gradient(Y)
    nn = np.hypot(dx, dy) + 1e-9
    nx, ny = -dy / nn, dx / nn
    h, w = d.shape
    cx, cy, R = lens.cx * sc, lens.cy * sc, lens.horizon * sc * 0.97
    span = int(max(12, 4 * tol_px * sc))
    offs = np.arange(-span, span + 1)
    xs = np.rint(X[None, :] + offs[:, None] * nx[None, :]).astype(int)
    ys = np.rint(Y[None, :] + offs[:, None] * ny[None, :]).astype(int)
    ok = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h) & (np.hypot(xs - cx, ys - cy) < R)
    if ok.all(axis=0).sum() < 0.6 * n:
        return None
    keep = ok.all(axis=0)                      # samples inside at every offset
    v = d[ys[:, keep], xs[:, keep]]            # (offsets, samples)

    def peak(block):
        prof = block.mean(axis=1)
        base = float(np.median(prof))
        noise = 1.4826 * float(np.median(np.abs(prof - base))) + 1e-6
        k = int(np.argmax(prof))
        return prof, base, noise, k

    prof, base, noise, k = peak(v)
    height = prof[k] - base
    if height / noise < snr_min or abs(offs[k] / sc) > accept_px:
        return None
    # narrow: 4 px beside the peak it has fallen to about a third
    for j in (k - 4, k + 4):
        if 0 <= j < len(prof) and prof[j] - base > 0.35 * height:
            return None
    # along the whole track: the same offset stands out in two of three thirds
    thirds = np.array_split(np.arange(v.shape[1]), 3)
    good = 0
    for idx in thirds:
        if len(idx) < 10:
            continue
        p3, b3, n3, _ = peak(v[:, idx])
        if (p3[max(0, k - 1):k + 2].max() - b3) / n3 >= snr_min / 2:
            good += 1
    if good < 2:
        return None
    return round(offs[k] / sc, 1)


def _logSeen(t0, seen, lens):
    """Append the trails seen on this image to skytraffic_seen.json (rolling),
    for the night recap and the website."""
    if not seen:
        return
    path = os.path.join(_dataDir(), "skytraffic_seen.json")
    try:
        with open(path) as fh:
            log = json.load(fh)
    except Exception:
        log = []
    stamp = time.strftime("%Y%m%d%H%M%S", time.localtime(t0))
    for tr in seen:
        pts = [p for p, v in zip(tr["pts"], tr["lit"]) if v]
        log.append({"time": stamp, "name": tr["name"], "id": tr["id"], "alt": tr["alt"],
                    "p1": pts[0], "p2": pts[-1]})
    with open(path + ".tmp", "w") as fh:
        json.dump(log[-2000:], fh)
    os.replace(path + ".tmp", path)


PUBLISH_EVERY = 900                        # seconds between website updates


def _publish(st, module):
    """Copy the JSON files to the Website's skytraffic folder and upload them to
    a remote website, at most every PUBLISH_EVERY seconds."""
    import shutil
    import subprocess
    if time.time() - st.get("published", 0) < PUBLISH_EVERY:
        return
    st["published"] = time.time()
    files = [os.path.join(_dataDir(), f) for f in (PASSES_FILE, "skytraffic_seen.json", "skytraffic_named.json")]
    files = [f for f in files if os.path.isfile(f)]
    home = s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky")
    website = s.getEnvironmentVariable("ALLSKY_WEBSITE") or os.path.join(home, "html", "allsky")
    try:
        folder = os.path.join(website, "skytraffic")
        os.makedirs(folder, exist_ok=True)
        for f in files:
            shutil.copy2(f, os.path.join(folder, os.path.basename(f)))
        if str(s.getSetting("useremotewebsite")).lower() in ("true", "1", "yes", "on"):
            uploader = os.path.join(s.getEnvironmentVariable("ALLSKY_SCRIPTS") or os.path.join(home, "scripts"), "upload.sh")
            rdir = ((s.getSetting("remotewebsiteimagedir") or "").rstrip("/") + "/skytraffic").lstrip("/")
            if os.path.isfile(uploader):
                for f in files:
                    subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", f, rdir, os.path.basename(f),
                                      "SkyTraffic"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        module.log(1, f"WARNING: Sky Traffic could not publish to the website: {ex}")


def _mark(img, tracks):
    colours = {"satellite": (80, 255, 80), "aircraft": (0, 165, 255)}
    th = max(1, img.shape[1] // 1500)
    for tr in tracks:
        c = colours[tr["kind"]]
        pts = np.array([p for p, v in zip(tr["pts"], tr["lit"]) if v], dtype=np.int32)
        if len(pts) < 2:
            continue
        cv2.polylines(img, [pts], False, c, th, cv2.LINE_AA)
        x, y = pts[len(pts) // 2]
        cv2.putText(img, tr["name"], (int(x) + 8, int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5 * th, c, th, cv2.LINE_AA)


def _debugImage(module, tracks, seen_ids):
    img = s.image.copy()
    for tr in tracks:
        c = (80, 255, 80) if tr["id"] in seen_ids else (0, 165, 255) if tr["kind"] == "aircraft" else (90, 90, 255)
        pts = np.array(tr["pts"], dtype=np.int32)
        cv2.polylines(img, [pts], False, c, 1, cv2.LINE_AA)
        cv2.putText(img, tr["name"], (int(pts[0][0]) + 4, int(pts[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1)
    s.startModuleDebug(module.meta_data["module"])
    s.writeDebugImage(module.meta_data["module"], "skytraffic-tracks.jpg", img)


# --- next passes and transits --------------------------------------------------

def _passes(params, lat, lon, now):
    """Visible passes of the bright satellites in the next hours, and ISS /
    Tiangong passes close to the Moon or Sun."""
    import ephem
    hours = s.asfloat(params["passes_hours"])
    min_alt = math.radians(s.asfloat(params["pass_min_altitude"]))
    # the brightest satellites, and of the space stations only the station itself
    # (the group also lists its modules and docked craft, which fly with it)
    sats = _satellites(["visual"])
    sats.update({k: v for k, v in _satellites(["stations"]).items() if v[0] in STATIONS})
    obs = _observer(lat, lon, now)
    obs.horizon = "10"
    sun, moon = ephem.Sun(), ephem.Moon()
    end = _edate(now + hours * 3600)
    passes, transits = [], []
    for _norad, (name, body) in sats.items():
        obs.date = _edate(now)
        for _ in range(12):
            try:
                rise_t, rise_az, max_t, max_alt, set_t, set_az = obs.next_pass(body, singlepass=True)
            except Exception:
                break
            if None in (rise_t, max_t, set_t) or rise_t > end:
                break
            if max_alt >= min_alt:
                obs.date = max_t
                body.compute(obs)
                sun.compute(obs)
                if not body.eclipsed and sun.alt < math.radians(-6):
                    passes.append({"name": name, "rise": _unix(rise_t), "max": _unix(max_t),
                                   "set": _unix(set_t), "max_alt": round(math.degrees(max_alt)),
                                   "from": _compass(math.degrees(rise_az)),
                                   "to": _compass(math.degrees(set_az))})
            if _truthy(params["transits"]) and name in STATIONS:
                tr = _closest(obs, body, sun, moon, rise_t, set_t)
                if tr:
                    transits.append(dict(tr, name=name))
            obs.date = set_t + ephem.minute
    passes.sort(key=lambda p: p["max"])
    transits.sort(key=lambda p: p["time"])
    return passes, transits


def _unix(d):
    return round((float(d) - UNIX_EPOCH) * 86400.0)


def _closest(obs, body, sun, moon, rise_t, set_t):
    """Closest approach of a station to the Moon or Sun during one pass (1 s
    steps), if within a degree."""
    import ephem
    best = None
    t = float(rise_t)
    while t <= float(set_t):
        obs.date = t
        body.compute(obs)
        for which, b in (("Moon", moon), ("Sun", sun)):
            b.compute(obs)
            if b.alt <= 0:
                continue
            sep = math.degrees(float(ephem.separation(body, b)))
            if best is None or sep < best["sep"]:
                best = {"body": which, "sep": round(sep, 3), "time": _unix(t),
                        "radius": round(math.degrees(float(b.radius)), 3)}
        t += 1.0 / 86400.0
    return best if best and best["sep"] < 1.0 else None


def _hm(t, seconds=False):
    return time.strftime("%H:%M:%S" if seconds else "%H:%M", time.localtime(t))


def _passTexts(passes, transits, now):
    nxt = next((p for p in passes if p["set"] > now), None)
    iss = next((p for p in passes if p["set"] > now and p["name"] == STATIONS[0]), None)
    tra = next((t for t in transits if t["time"] > now), None)

    def txt(p):
        name = "ISS" if p["name"] == STATIONS[0] else "Tiangong" if p["name"] == STATIONS[1] else p["name"]
        return f"{name} {_hm(p['max'])} {p['max_alt']}° {p['from']}-{p['to']}"
    ttxt = ""
    if tra:
        name = "ISS" if tra["name"] == STATIONS[0] else "Tiangong"
        if tra["sep"] <= tra["radius"]:
            ttxt = f"{name} crosses the {tra['body']} {_hm(tra['time'], True)}"
        else:
            ttxt = f"{name} passes {tra['sep']:.1f}° from the {tra['body']} {_hm(tra['time'], True)}"
    return (txt(nxt) if nxt else ""), (txt(iss) if iss else ""), ttxt


PASSES_FILE = "skytraffic_passes.json"


def _readPasses(lat, lon):
    """The pass list the background job wrote, if it is for this site and fresh."""
    try:
        with open(os.path.join(_dataDir(), PASSES_FILE)) as fh:
            p = json.load(fh)
        if p.get("site") == [lat, lon]:
            return p
    except Exception:
        pass
    return None


def _startPassJob(params, lat, lon, module):
    """Compute the passes in a separate process: it takes several seconds, which
    must not hold up the image.  At most one job runs at a time."""
    import subprocess
    lock = os.path.join(s.ALLSKY_TMP, "allsky_skytraffic_passes.lock")
    if os.path.isfile(lock) and time.time() - os.path.getmtime(lock) < 900:
        return
    with open(lock, "w") as fh:
        fh.write(str(time.time()))
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (os.path.dirname(os.path.abspath(s.__file__)), _MODULE_DIR,
                                                    env.get("PYTHONPATH", "")) if p)
    job = {"lat": lat, "lon": lon, "lock": lock,
           "params": {k: params[k] for k in ("passes_hours", "pass_min_altitude", "transits")}}
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--passes", json.dumps(job)],
                         env=env, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        os.remove(lock)
        module.log(1, f"WARNING: Sky Traffic could not start the pass computation: {ex}")


def _passJob(job):
    """Entry point of the background process."""
    try:
        now = time.time()
        passes, transits = _passes(job["params"], job["lat"], job["lon"], now)
        path = os.path.join(_dataDir(), PASSES_FILE)
        with open(path + ".tmp", "w") as fh:
            json.dump({"computed": round(now), "site": [job["lat"], job["lon"]],
                       "passes": passes, "transits": transits}, fh)
        os.replace(path + ".tmp", path)
    finally:
        try:
            os.remove(job["lock"])
        except OSError:
            pass


def _updatePasses(params, lat, lon, module):
    """Current pass list; starts a new computation once an hour."""
    p = _readPasses(lat, lon)
    if p is None or time.time() - p.get("computed", 0) > 3600:
        _startPassJob(params, lat, lon, module)
    return (p or {}).get("passes", []), (p or {}).get("transits", [])


# --- main --------------------------------------------------------------------

def _run(module):
    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    st = _readState()
    lat, lon = _site()
    use_sats = _truthy(params["satellites"])
    groups = [g.strip() for g in params["tle_groups"].split(",") if g.strip()]
    if use_sats:
        _download(list(dict.fromkeys(groups + list(BRIGHT_GROUPS))), s.asfloat(params["tle_refresh_hours"]), st, module)

    passes, transits = _updatePasses(params, lat, lon, module) if use_sats else ([], [])
    now = time.time()
    nxt, iss, tra = _passTexts(passes, transits, now)
    values = {"AS_SKYTRAFFIC_NEXT": nxt, "AS_SKYTRAFFIC_NEXT_ISS": iss, "AS_SKYTRAFFIC_TRANSIT": tra}

    night = (os.environ.get("DAY_OR_NIGHT") or str(getattr(s, "TOD", ""))).lower() == "night"
    if not night or s.image is None:
        if _truthy(params["publish_web"]):
            _publish(st, module)
        _writeState(st)
        s.saveExtraData(module.meta_data["extradatafilename"], values,
                        module.meta_data["module"], module.meta_data["extradata"], event=module.event)
        return f"Sky Traffic: next pass {nxt or '-'}"

    t0, exp = _imageTime(), _exposure()
    lens = _Lens(params, s.image.shape)
    tol_px = s.asfloat(params["match_tolerance"]) * lens.px_per_deg
    min_alt = s.asfloat(params["min_altitude"])

    tracks, sats_up = [], 0
    if use_sats:
        tracks, sats_up = _satelliteTracks(_satellites(groups), lat, lon, t0, exp, lens, min_alt)
    n_aircraft = 0
    if params["aircraft_source"].strip().lower() not in ("", "none"):
        try:
            aircraft, data_time = _fetchAircraft(params, lat, lon)
            ac = _aircraftTracks(aircraft, data_time, lat, lon, s.asfloat(params["site_height"]),
                                 t0, exp, lens, min_alt, s.asfloat(params["aircraft_radius"]) * 1000.0)
            n_aircraft = len(ac)
            tracks += ac
        except Exception as ex:
            module.log(1, f"WARNING: Sky Traffic could not read the aircraft: {ex}")

    # remember this frame's tracks: the Meteor Detection module reports a streak
    # one frame later, so the names are given when its result shows up
    frames = [f for f in st.get("frames", []) if now - f["run"] < 3 * 3600][-(KEEP_FRAMES - 1):]
    frames.append({"run": now, "t0": t0, "exp": exp, "tracks": tracks})
    st["frames"] = frames
    named, suspects = _nameStreaks(params, st, frames, tol_px, module)

    seen = []
    if use_sats and _truthy(params["detect_trails"]):
        g, sc = _workImage(s.image)
        d = _trailImage(g, PREV_FRAME, max_age=max(600.0, 3 * exp))
        snr = s.asfloat(params["trail_snr"])
        # the offset a real trail had from its track here: 0-5 px on a 3840 px image
        # (0.3 deg); trails found by chance with the wrong times lay 7-26 px off
        accept = TRAIL_TOL_DEG * lens.px_per_deg if lens.calibrated else tol_px
        for tr in tracks if d is not None else []:
            if tr["kind"] == "satellite":
                off = _trailSeen(d, tr, lens, sc, max(tol_px, accept), snr, accept)
                if off is not None:
                    seen.append(tr)
    _logSeen(t0, seen, lens)
    if _truthy(params["publish_web"]):
        _publish(st, module)
    _writeState(st)

    if _truthy(params["debug"]):
        _debugImage(module, tracks, {t["id"] for t in seen})
    if _truthy(params["mark_image"]):
        _mark(s.image, seen + [t for t in tracks if t["kind"] == "aircraft"])

    n_sat = sum(1 for r in named if r.get("kind") == "satellite")
    n_air = sum(1 for r in named if r.get("kind") == "aircraft")
    names = sorted({r["name"] for r in named if r.get("name")})
    values.update({
        "AS_SKYTRAFFIC_SATS": sats_up,
        "AS_SKYTRAFFIC_SEEN": len(seen),
        "AS_SKYTRAFFIC_SEEN_NAMES": ", ".join(t["name"] for t in seen),
        "AS_SKYTRAFFIC_AIRCRAFT": n_aircraft,
        "AS_SKYTRAFFIC_NAMED_SATS": n_sat,
        "AS_SKYTRAFFIC_NAMED_AIRCRAFT": n_air,
        "AS_SKYTRAFFIC_UNNAMED": len(named) - n_sat - n_air,
        "AS_SKYTRAFFIC_NAMES": ", ".join(names),
        "AS_SKYTRAFFIC_METEOR_SUSPECT": len(suspects),
    })
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)

    lens_txt = "calibrated lens" if lens.calibrated else "uncalibrated lens"
    result = (f"Sky Traffic: {sats_up} sunlit satellites up, {len(seen)} trails seen"
              f"{' (' + ', '.join(t['name'] for t in seen) + ')' if seen else ''}, {n_aircraft} aircraft, "
              f"{len(named)} rejected streaks checked ({n_sat} satellites, {n_air} aircraft), "
              f"{lens_txt}; next pass {nxt or '-'}")
    module.log(4, f"INFO: {result}")
    return result


def skytraffic(params, event):
    return ALLSKYSKYTRAFFIC(params, event).run()


def skytraffic_cleanup():
    moduleData = {
        "metaData": ALLSKYSKYTRAFFIC.meta_data,
        "cleanup": {
            "files": {
                ALLSKYSKYTRAFFIC.meta_data["extradatafilename"],
                STATE_FILE,
                PREV_FRAME
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--passes":
    _passJob(json.loads(sys.argv[2]))
