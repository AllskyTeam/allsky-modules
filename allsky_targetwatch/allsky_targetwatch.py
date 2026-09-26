""" allsky_targetwatch.py

"Is my target clear?" for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)

An all-sky camera sees the whole sky, but what an observer wants to know is
whether the part of the sky with THEIR target is clear: M31 in a clear gap,
Jupiter behind a cloud.  This module answers that for a list of targets on
every night image.

How it measures clear sky
    The bright catalogue stars (Hipparcos, V < 5) are projected into the image
    with the fisheye calibration for the time of the image, and each one is
    looked for: a star counts as seen when the image has a point above 8 times
    the noise within a few pixels of its predicted position.  On a clear night
    here that finds about 60% of the stars; with shifted positions (chance)
    only 2%; under cloud 2% again.  The share of stars seen around a target,
    compared with the share seen on the clear frames of the last nights at that
    altitude, is the target's clear sky in %.

The forecast
    The clouds are followed from image to image with optical flow.  Looking
    upwind of the target on the current clear-sky map tells whether a gap or a
    cloud is coming, and roughly when.

Needs a fisheye calibration (calibration.json, made with the Meteor Detection
module's tools/calibrate_fisheye.py): a star must be found within a few pixels.
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import re
import sys
import json
import math
import time
import cv2
import numpy as np


class ALLSKYTARGETWATCH(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Target Watch",
        "description": "Tells whether the sky around your targets (planets, Messier objects, your own) is clear, and whether clouds or a gap are coming",
        "version": "v0.1.0",
        "module": "allsky_targetwatch",
        "events": [
            "night"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_targetwatch.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_targetwatch",
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
                "AS_TARGETWATCH_SKY": {
                    "name": "${TARGETWATCH_SKY}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Clear sky over the whole sky in %, from the catalogue stars seen",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_TARGETWATCH_SUMMARY": {
                    "name": "${TARGETWATCH_SUMMARY}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "One line for all targets, e.g. 'M31 clear, Jupiter clouds in ~10 min'",
                    "type": "string"
                },
                "AS_TARGETWATCH_T1": {
                    "name": "${TARGETWATCH_T1}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 1: name, state and forecast",
                    "type": "string"
                },
                "AS_TARGETWATCH_T1_CLEAR": {
                    "name": "${TARGETWATCH_T1_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 1: clear sky around it in %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_TARGETWATCH_T2": {
                    "name": "${TARGETWATCH_T2}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 2: name, state and forecast",
                    "type": "string"
                },
                "AS_TARGETWATCH_T2_CLEAR": {
                    "name": "${TARGETWATCH_T2_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 2: clear sky around it in %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_TARGETWATCH_T3": {
                    "name": "${TARGETWATCH_T3}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 3: name, state and forecast",
                    "type": "string"
                },
                "AS_TARGETWATCH_T3_CLEAR": {
                    "name": "${TARGETWATCH_T3_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 3: clear sky around it in %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_TARGETWATCH_T4": {
                    "name": "${TARGETWATCH_T4}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 4: name, state and forecast",
                    "type": "string"
                },
                "AS_TARGETWATCH_T4_CLEAR": {
                    "name": "${TARGETWATCH_T4_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 4: clear sky around it in %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_TARGETWATCH_T5": {
                    "name": "${TARGETWATCH_T5}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 5: name, state and forecast",
                    "type": "string"
                },
                "AS_TARGETWATCH_T5_CLEAR": {
                    "name": "${TARGETWATCH_T5_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Target Watch",
                    "description": "Target 5: clear sky around it in %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                }
            }
        },
        "arguments": {
            "targets": "M31, M42, M45, Jupiter, Saturn",
            "radius": "10",
            "min_altitude": "15",
            "clear_above": "70",
            "cloudy_below": "30",
            "calibration": "calibration.json",
            "forecast": "true",
            "notify_url": "",
            "publish_web": "false",
            "debug": "false",
            "graph": ""
        },
        "argumentdetails": {
            "targets": {
                "required": "false",
                "description": "Targets",
                "help": "Up to 5, separated by commas: the Moon and planets (Moon, Venus, Mars, Jupiter, Saturn, ...), Messier objects (M31, M 42) or their names (Andromeda Galaxy, Pleiades), or your own as Name=RA,Dec with RA in hours or h:m:s and Dec in degrees or d:m:s, e.g. NAN=20:59:17,+44:31:44.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "text"
                }
            },
            "radius": {
                "required": "false",
                "description": "Radius (deg)",
                "help": "The sky within this distance of a target counts. Larger is steadier (more stars) but less sharp. 10 degrees holds about 20 stars.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "spinner",
                    "min": 4,
                    "max": 30,
                    "step": 1
                }
            },
            "min_altitude": {
                "required": "false",
                "description": "Lowest altitude (deg)",
                "help": "A target lower than this is reported as 'low'.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "spinner",
                    "min": 5,
                    "max": 60,
                    "step": 1
                }
            },
            "clear_above": {
                "required": "false",
                "description": "Clear above (%)",
                "help": "A target with at least this much clear sky around it is 'clear'.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "spinner",
                    "min": 30,
                    "max": 100,
                    "step": 5
                }
            },
            "cloudy_below": {
                "required": "false",
                "description": "Cloudy below (%)",
                "help": "A target with less clear sky than this around it is 'cloudy'. Between the two it is 'partly clear'.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 70,
                    "step": 5
                }
            },
            "calibration": {
                "required": "true",
                "description": "Fisheye calibration file",
                "help": "calibration.json in the modules folder, made with the Meteor Detection module's tools/calibrate_fisheye.py. Needed: a star must be found within a few pixels of where it should be.",
                "tab": "Targets",
                "type": {
                    "fieldtype": "text"
                }
            },
            "forecast": {
                "required": "false",
                "description": "Forecast",
                "help": "Follow the clouds from image to image and tell when a cloud or a gap reaches a target (up to 30 minutes ahead).",
                "tab": "Forecast",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "notify_url": {
                "required": "false",
                "description": "Notify URL",
                "help": "Optional. When a target becomes clear (and stays clear on the next image), a short text is sent to this URL with an HTTP POST, at most once an hour per target. Works with ntfy (https://ntfy.sh/your-topic) and anything else that takes a plain text POST.",
                "tab": "Forecast",
                "type": {
                    "fieldtype": "text"
                }
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to the website",
                "help": "Write the state of every target (targetwatch.json) into the Website's targetwatch folder on every image, and upload it to a remote website. The remote 'targetwatch' folder must exist: the upload does not create folders.",
                "tab": "Forecast",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "debug": {
                "required": "false",
                "description": "Debug",
                "help": "Write an image with the stars seen (green) and missed (red) and the target circles.",
                "tab": "Forecast",
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
                        "Clear sky around up to 5 targets (Moon, planets, Messier objects, own coordinates) from the catalogue stars seen there",
                        "Cloud forecast per target from the cloud motion between images",
                        "Optional notification when a target becomes clear",
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
            result = f"Module Target Watch failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIRS = (os.path.join(_MODULE_DIR, "moduledata", "data", "allsky_targetwatch"),
              os.path.join(_MODULE_DIR, "allsky_targetwatch"), _MODULE_DIR)
STATE_FILE = os.path.join(s.ALLSKY_TMP, "allsky_targetwatch_state.json")
PREV_FRAME = os.path.join(s.ALLSKY_TMP, "allsky_targetwatch_prev.png")
MAX_TARGETS = 5
MAG_LIMIT = 5.0             # catalogue stars used
STAR_SNR = 8.0              # a star is seen above this many times the noise
STAR_RADIUS_4K = 4          # search radius (px) on a 3840 px wide image
REF_DEFAULT = 0.6           # share of stars seen on a clear night until learned
REF_FRAMES = 400            # frames the clear-night reference is learned from (~2 nights)
ALT_BANDS = (15, 25, 35, 50, 70, 91)
CHANCE_SHIFTS = ((6, 0), (-6, 0), (0, 6), (0, -6))   # in search radii
MIN_STARS = 8               # a target circle is widened until it holds this many
FLOW_WIDTH = 480            # optical flow runs on an image this wide
PLANETS = ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune")


def _truthy(v):
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _dataFile(name):
    for d in _DATA_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return os.path.join(_DATA_DIRS[-1], name)


def _imageTime():
    try:
        return int(s.get_environment_variable("AS_TIMESTAMP"))
    except (TypeError, ValueError):
        return int(time.time())


def _readState():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {}


def _writeState(st):
    with open(STATE_FILE + ".tmp", "w") as fh:
        json.dump(st, fh)
    os.replace(STATE_FILE + ".tmp", STATE_FILE)


# --- lens (cubic equidistant fisheye, as calibrate_fisheye.py fits it) ----------

def _loadCalib(name, shape):
    path = name if os.path.isabs(name) else os.path.join(_MODULE_DIR, name)
    try:
        with open(path) as fh:
            c = json.load(fh)
    except Exception:
        return None
    if not all(k in c for k in ("cx", "cy", "a1", "a3", "rot_deg", "flip")):
        return None
    h, w = shape[:2]
    sx, sy = w / float(c.get("W", w)), h / float(c.get("H", h))
    if abs(sx - sy) > 0.01 * sx:
        return None                           # cropped image: the calibration doesn't fit
    c = dict(c)
    for k in ("cx", "cy", "a1", "a3"):
        c[k] = c[k] * sx
    return c


def _project(c, alt, az):
    """Arrays of alt/az (deg) -> pixel x, y."""
    t = (90.0 - alt) / 90.0
    r = c["a1"] * t + c["a3"] * t ** 3
    a = np.radians(c["rot_deg"] + c["flip"] * az)
    return c["cx"] + r * np.sin(a), c["cy"] - r * np.cos(a)


def _altaz(ra, dec, lst, lat):
    """RA/Dec arrays (deg) -> altitude, azimuth (deg)."""
    ra, dec, lat = np.radians(ra), np.radians(dec), math.radians(lat)
    ha = math.radians(lst) - ra
    alt = np.arcsin(np.sin(dec) * math.sin(lat) + np.cos(dec) * math.cos(lat) * np.cos(ha))
    az = np.arctan2(np.sin(ha), np.cos(ha) * math.sin(lat) - np.tan(dec) * math.cos(lat))
    return np.degrees(alt), (np.degrees(az) + 180.0) % 360.0


def _unit(alt, az):
    a, z = np.radians(alt), np.radians(az)
    return np.stack([np.cos(a) * np.sin(z), np.cos(a) * np.cos(z), np.sin(a)], axis=-1)


# --- targets -----------------------------------------------------------------

def _parseAngle(txt, hours):
    txt = txt.strip()
    if ":" in txt:
        sign = -1.0 if txt.startswith("-") else 1.0
        parts = [float(p) for p in txt.lstrip("+-").split(":")]
        v = parts[0] + (parts[1] if len(parts) > 1 else 0) / 60.0 + (parts[2] if len(parts) > 2 else 0) / 3600.0
        v *= sign
    else:
        v = float(txt)
    return v * 15.0 if hours else v


def _targets(text):
    """[(label, kind, data)] from the targets setting; unknown names are reported."""
    with open(_dataFile("messier.json")) as fh:
        messier = json.load(fh)["objects"]
    out, unknown = [], []
    for item in [t.strip() for t in text.split(",") if t.strip()]:
        if "=" in item:
            # Name=RA,Dec : the comma between RA and Dec was split off; glue it back below
            out.append([item, "custom", None])
            continue
        if out and out[-1][1] == "custom" and out[-1][2] is None:
            out[-1][0] += "," + item
            out[-1][2] = True
            continue
        m = re.fullmatch(r"(?:m|messier)\s*(\d{1,3})", item, re.I)
        planet = next((p for p in PLANETS if p.lower() == item.lower()), None)
        if planet:
            out.append([planet, "planet", planet])
        elif m and any(o[0] == int(m.group(1)) for o in messier):
            o = next(o for o in messier if o[0] == int(m.group(1)))
            out.append([f"M{o[0]}", "fixed", (o[1], o[2])])
        else:
            o = next((o for o in messier if o[3] and item.lower() in o[3].lower()), None)
            if o:
                out.append([item, "fixed", (o[1], o[2])])
            else:
                unknown.append(item)
    targets = []
    for label, kind, data in out:
        if kind == "custom":
            try:
                name, coords = label.split("=", 1)
                ra, dec = coords.split(",")
                targets.append((name.strip(), "fixed", (_parseAngle(ra, True), _parseAngle(dec, False))))
            except ValueError:
                unknown.append(label)
        else:
            targets.append((label, kind, data))
    return targets[:MAX_TARGETS], unknown


def _targetAltAz(target, lat, lon, t, lst):
    label, kind, data = target
    if kind == "planet":
        import ephem
        obs = ephem.Observer()
        obs.lat, obs.lon = str(lat), str(lon)
        obs.date = ephem.Date(t / 86400.0 + 25567.5)
        body = getattr(ephem, data)()
        body.compute(obs)
        return math.degrees(body.alt), math.degrees(body.az)
    alt, az = _altaz(np.array([data[0]]), np.array([data[1]]), lst, lat)
    return float(alt[0]), float(az[0])


def _lst(t, lon):
    """Local sidereal time in degrees."""
    d = t / 86400.0 + 2440587.5 - 2451545.0
    T = d / 36525.0
    return (280.46061837 + 360.98564736629 * d + 0.000387933 * T * T + lon) % 360.0


# --- which stars are seen ------------------------------------------------------

def _stars():
    with open(_dataFile("stars.json")) as fh:
        st = np.array(json.load(fh)["stars"], dtype=np.float64)
    return st[st[:, 2] <= MAG_LIMIT]


def _seenStars(gray, calib, lat, lst, min_alt):
    """alt, az, x, y, seen for every catalogue star above min_alt inside the image."""
    cat = _stars()
    alt, az = _altaz(cat[:, 0], cat[:, 1], lst, lat)
    up = alt >= min_alt
    alt, az = alt[up], az[up]
    x, y = _project(calib, alt, az)
    h, w = gray.shape
    r = max(2, int(round(STAR_RADIUS_4K * w / 3840.0)))
    inside = (x >= r) & (x < w - r) & (y >= r) & (y < h - r)
    alt, az, x, y = alt[inside], az[inside], x[inside], y[inside]
    g = gray.astype(np.float32)
    hp = g - cv2.medianBlur(gray, 9).astype(np.float32)
    noise = 1.4826 * float(np.median(np.abs(hp - np.median(hp)))) + 1e-3
    peak = cv2.dilate(hp, np.ones((2 * r + 1, 2 * r + 1), np.uint8))   # max within r
    thr = STAR_SNR * noise
    xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
    seen = peak[yi, xi] > thr
    # the same test beside each star: how often cloud texture or noise passes by
    # chance.  Subtracted from the stars seen, so a textured cloud is not "clear".
    chance = np.zeros(len(x))
    for dx, dy in CHANCE_SHIFTS:
        cx_, cy_ = np.clip(xi + int(dx * r), 0, w - 1), np.clip(yi + int(dy * r), 0, h - 1)
        chance += peak[cy_, cx_] > thr
    return alt, az, x, y, seen, chance / len(CHANCE_SHIFTS)


def _visible(seen, chance):
    """Share of stars really seen: seen minus chance, rescaled (0..1)."""
    ps, pc = float(np.mean(seen)), float(np.mean(chance))
    return max(0.0, (ps - pc) / max(1e-3, 1.0 - pc))


def _reference(st, alt, seen, chance, clearish):
    """Share of stars seen on a clear frame, per altitude band, learned as the
    90th percentile of the last REF_FRAMES frames."""
    hist = st.setdefault("ref", [])
    rates = []
    for lo, hi in zip(ALT_BANDS[:-1], ALT_BANDS[1:]):
        m = (alt >= lo) & (alt < hi)
        rates.append(round(_visible(seen[m], chance[m]), 3) if m.sum() >= 10 else None)
    if clearish:
        hist.append(rates)
    del hist[:-REF_FRAMES]
    ref = []
    for i in range(len(ALT_BANDS) - 1):
        v = [r[i] for r in hist if r[i] is not None]
        ref.append(float(np.clip(np.percentile(v, 90), 0.2, 0.95)) if len(v) >= 30 else REF_DEFAULT)
    return ref


def _refAt(ref, alt):
    for i, (lo, hi) in enumerate(zip(ALT_BANDS[:-1], ALT_BANDS[1:])):
        if lo <= alt < hi:
            return ref[i]
    return ref[0]


def _moon(lat, lon, t):
    """Altitude, azimuth and glare radius (deg) of the Moon if it is up: from 5 deg
    at new moon to 20 deg at full moon, measured on moonlit nights here."""
    import ephem
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = ephem.Date(t / 86400.0 + 25567.5)
    m = ephem.Moon(obs)
    if m.alt <= 0:
        return None
    return math.degrees(m.alt), math.degrees(m.az), 5.0 + 15.0 * m.phase / 100.0


def _clearAround(t_alt, t_az, alt, az, seen, chance, ref, radius):
    """Clear sky (%) within radius of a direction (widened up to twice where the
    sky has few bright stars), and the stars it is based on."""
    sep = np.degrees(np.arccos(np.clip(_unit(alt, az) @ _unit(t_alt, t_az), -1, 1)))
    for r in (radius, radius * 1.5, radius * 2):
        m = sep <= r
        if m.sum() >= MIN_STARS:
            break
    n = int(m.sum())
    if n < 5:
        return None, n
    expect = float(np.mean([_refAt(ref, a) for a in alt[m]]))
    return float(min(100.0, 100.0 * _visible(seen[m], chance[m]) / expect)), n


# --- cloud motion ----------------------------------------------------------------

def _flow(gray, st, t0):
    """Median cloud motion (full-image px per second) between the previous image
    and this one, from dense optical flow on a small, blurred copy (stars
    blurred away).  None if there is no recent previous image."""
    sc = FLOW_WIDTH / float(gray.shape[1])
    small = cv2.GaussianBlur(cv2.resize(gray, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA), (0, 0), 2)
    prev = cv2.imread(PREV_FRAME, cv2.IMREAD_GRAYSCALE) if os.path.isfile(PREV_FRAME) else None
    prev_t = st.get("prev_t")
    cv2.imwrite(PREV_FRAME, small)
    st["prev_t"] = t0
    if prev is None or prev.shape != small.shape or not prev_t or not 0 < t0 - prev_t < 900:
        return None
    f = cv2.calcOpticalFlowFarneback(prev, small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    return f / sc / float(t0 - prev_t)


def _forecast(flow, width, calib, t_alt, t_az, alt, az, x, y, seen, chance, ref, radius, now_clear, clear_above, cloudy_below):
    """Look upwind of the target: what the current clear-sky map shows where the
    air over the target will come from in 10, 20, 30 minutes."""
    if flow is None or now_clear is None:
        return ""
    tx, ty = _project(calib, np.array([t_alt]), np.array([t_az]))
    sc = flow.shape[1] / float(width)
    fx0, fy0 = int(np.clip(tx[0] * sc, 0, flow.shape[1] - 1)), int(np.clip(ty[0] * sc, 0, flow.shape[0] - 1))
    win = flow[max(0, fy0 - 20):fy0 + 21, max(0, fx0 - 20):fx0 + 21].reshape(-1, 2)
    v = np.median(win, axis=0)                               # px/s at the target
    if np.hypot(*v) * 600 < 10:                              # under 10 px in 10 min: no motion
        return ""
    for minutes in (10, 20, 30):
        ux, uy = tx[0] - v[0] * minutes * 60, ty[0] - v[1] * minutes * 60
        # the clear sky around the upwind point, using the stars near it in the image
        d = np.hypot(x - ux, y - uy)
        rpx = radius * calib["a1"] / 90.0
        m = d <= rpx
        if m.sum() < 5:
            return ""
        expect = float(np.mean([_refAt(ref, a) for a in alt[m]]))
        c = min(100.0, 100.0 * _visible(seen[m], chance[m]) / expect)
        if now_clear >= clear_above and c < cloudy_below:
            return f"clouds in ~{minutes} min"
        if now_clear < clear_above and c >= clear_above:
            return f"clear in ~{minutes} min"
    return ""


def _moonSeen(gray, calib, t_alt, t_az):
    """The Moon's disc is at its place: a bright, nearly saturated blob."""
    x, y = _project(calib, np.array([t_alt]), np.array([t_az]))
    r = max(3, int(0.7 * calib["a1"] / 90.0))
    x0, y0 = int(x[0]), int(y[0])
    h, w = gray.shape
    patch = gray[max(0, y0 - r):min(h, y0 + r + 1), max(0, x0 - r):min(w, x0 + r + 1)]
    return patch.size > 0 and int(patch.max()) >= 200 and int(patch.max()) > float(np.median(gray)) + 60


def _publish(data, module):
    """targetwatch.json into the Website's targetwatch folder, and to a remote website."""
    import subprocess
    home = s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky")
    website = s.get_environment_variable("ALLSKY_WEBSITE") or os.path.join(home, "html", "allsky")
    try:
        folder = os.path.join(website, "targetwatch")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "targetwatch.json")
        with open(path + ".tmp", "w") as fh:
            json.dump(data, fh)
        os.replace(path + ".tmp", path)
        if str(s.getSetting("useremotewebsite")).lower() in ("true", "1", "yes", "on"):
            uploader = os.path.join(s.get_environment_variable("ALLSKY_SCRIPTS") or os.path.join(home, "scripts"), "upload.sh")
            rdir = ((s.getSetting("remotewebsiteimagedir") or "").rstrip("/") + "/targetwatch").lstrip("/")
            if os.path.isfile(uploader):
                subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", path, rdir, "targetwatch.json",
                                  "TargetWatch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        module.log(1, f"WARNING: Target Watch could not publish to the website: {ex}")


def _notify(url, text, module):
    import requests
    try:
        requests.post(url, data=text.encode("utf-8"), timeout=8)
    except Exception as ex:
        module.log(1, f"WARNING: Target Watch could not send the notification: {ex}")


def _debugImage(module, img, x, y, seen, circles):
    out = img.copy()
    for xi, yi, sn in zip(x, y, seen):
        cv2.circle(out, (int(xi), int(yi)), 6, (0, 255, 0) if sn else (0, 0, 255), 1)
    for (cx, cy, r, label) in circles:
        cv2.circle(out, (int(cx), int(cy)), int(r), (255, 200, 0), 2)
        cv2.putText(out, label, (int(cx + r * 0.7), int(cy - r * 0.7)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
    s.startModuleDebug(module.meta_data["module"])
    s.writeDebugImage(module.meta_data["module"], "targetwatch.jpg", out)


# --- main --------------------------------------------------------------------

def _state_of(clear, clear_above, cloudy_below):
    if clear is None:
        return "unknown"
    return "clear" if clear >= clear_above else "cloudy" if clear < cloudy_below else "partly clear"


def _run(module):
    if s.image is None:
        return "No image available"
    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    calib = _loadCalib(params["calibration"].strip(), s.image.shape)
    if calib is None:
        return "Target Watch needs a fisheye calibration (calibration.json, see the README)"
    lat, lon = float(calib.get("lat", s.convertLatLon(s.getSetting("latitude")))), \
        float(calib.get("lon", s.convertLatLon(s.getSetting("longitude"))))
    t0 = _imageTime()
    lst = _lst(t0, lon)
    min_alt = s.asfloat(params["min_altitude"])
    radius = s.asfloat(params["radius"])
    clear_above, cloudy_below = s.asfloat(params["clear_above"]), s.asfloat(params["cloudy_below"])
    st = _readState()

    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if s.image.ndim == 3 else s.image
    alt, az, x, y, seen, chance = _seenStars(gray, calib, lat, lst, min(10.0, min_alt))
    if len(seen) < 20:
        return "Target Watch: too few catalogue stars in the image - check the calibration"
    # the Moon's glare hides the stars around it: those are no measure of cloud
    moon = _moon(lat, lon, t0)
    if moon is not None:
        m_alt, m_az, glare = moon
        near = np.degrees(np.arccos(np.clip(_unit(alt, az) @ _unit(m_alt, m_az), -1, 1))) < glare
        alt, az, x, y, seen, chance = (a[~near] for a in (alt, az, x, y, seen, chance))
    # learn the clear-night reference only from frames that look clear already
    ref0 = _reference({"ref": list(st.get("ref", []))}, alt, seen, chance, False)
    sky = min(100.0, 100.0 * _visible(seen, chance) / float(np.mean(ref0)))
    ref = _reference(st, alt, seen, chance, sky >= 50)

    flow = _flow(gray, st, t0) if _truthy(params["forecast"]) else None
    targets, unknown = _targets(params["targets"])
    values = {"AS_TARGETWATCH_SKY": round(sky, 1)}
    parts, circles, published = [], [], []
    prev_states = st.get("states", {})
    states = {}
    for i, target in enumerate(targets, start=1):
        label = target[0]
        t_alt, t_az = _targetAltAz(target, lat, lon, t0, lst)
        near_moon = moon is not None and target[2] != "Moon" and float(np.degrees(np.arccos(np.clip(
            _unit(moon[0], moon[1]) @ _unit(t_alt, t_az), -1, 1)))) < moon[2]
        px, py = _project(calib, np.array([t_alt]), np.array([t_az]))
        h, w = gray.shape
        if t_alt < min_alt:
            text, clear = f"{label} low ({t_alt:.0f}°)", None
        elif not (0 <= px[0] < w and 0 <= py[0] < h):
            text, clear = f"{label} outside the image", None
        else:
            clear, n = _clearAround(t_alt, t_az, alt, az, seen, chance, ref, radius)
            if target[1] == "planet" and target[2] == "Moon" and _moonSeen(gray, calib, t_alt, t_az):
                clear = 100.0     # its glare hides the stars around it, but the Moon itself is there
            state = _state_of(clear, clear_above, cloudy_below)
            if near_moon:
                state = "near the Moon" if clear is None else state + " near the Moon"
            fc = _forecast(flow, gray.shape[1], calib, t_alt, t_az, alt, az, x, y, seen, chance, ref, radius, clear,
                           clear_above, cloudy_below) if clear is not None else ""
            text = f"{label} {state}" + (f" ({clear:.0f}%)" if clear is not None else "") + (f", {fc}" if fc else "")
            states[label] = state
            # notify when a target is clear on two images in a row after not being clear
            url = params["notify_url"].strip()
            hist = prev_states.get(label, [])
            if url and state == "clear" and hist[-1:] == ["clear"] and "clear" not in hist[-3:-1]:
                sent = st.setdefault("notified", {})
                if time.time() - sent.get(label, 0) > 3600:
                    sent[label] = time.time()
                    _notify(url, f"{label} is clear ({clear:.0f}% clear sky, {t_alt:.0f}° high)", module)
            cx, cy = _project(calib, np.array([t_alt]), np.array([t_az]))
            circles.append((cx[0], cy[0], radius * calib["a1"] / 90.0, label))
        values[f"AS_TARGETWATCH_T{i}"] = text
        published.append({"name": label, "text": text, "altitude": round(t_alt, 1),
                          "clear": round(clear, 1) if clear is not None else None})
        values[f"AS_TARGETWATCH_T{i}_CLEAR"] = round(clear, 1) if clear is not None else None
        parts.append(text)
    st["states"] = {k: (prev_states.get(k, []) + [v])[-4:] for k, v in states.items()}
    _writeState(st)
    values = {k: v for k, v in values.items() if v is not None}
    values["AS_TARGETWATCH_SUMMARY"] = ", ".join(parts)
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)
    if _truthy(params["debug"]):
        _debugImage(module, s.image, x, y, seen, circles)
    if _truthy(params["publish_web"]):
        _publish({"time": t0, "sky": round(sky, 1), "summary": values["AS_TARGETWATCH_SUMMARY"],
                  "targets": published}, module)

    result = f"Target Watch: sky {sky:.0f}% clear ({int(seen.sum())}/{len(seen)} stars); " + "; ".join(parts)
    if unknown:
        result += f" - unknown target(s): {', '.join(unknown)}"
        module.log(1, f"WARNING: Target Watch does not know {', '.join(unknown)}")
    module.log(4, f"INFO: {result}")
    return result


def targetwatch(params, event):
    return ALLSKYTARGETWATCH(params, event).run()


def targetwatch_cleanup():
    moduleData = {
        "metaData": ALLSKYTARGETWATCH.meta_data,
        "cleanup": {
            "files": {
                ALLSKYTARGETWATCH.meta_data["extradatafilename"],
                STATE_FILE,
                PREV_FRAME
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
