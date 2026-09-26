""" allsky_skymap.py

A map of the night sky's darkness and transparency, direction by direction,
for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)

On clear, moonless images the module measures, for the zenith and eight
directions:

  * the limiting magnitude: the catalogue stars (Hipparcos, to V = 7.5) are
    projected into the image with the fisheye calibration and looked for; the
    magnitude at which half of them are still seen (after subtracting the
    chance of a random hit) is the limiting magnitude in that direction.  It
    falls where the sky is bright (light pollution) or hazy (poor
    transparency);
  * the sky background: the brightness of the image with the stars filtered
    out, which shows the light domes of towns directly.

Trees, roofs and the like are learnt from the stars themselves: where bright
stars are never seen on clear images, the sky is blocked, and that part is
left out.  The results are averaged per night, kept for a year and drawn as a
map.

Needs a fisheye calibration (calibration.json, made with the Meteor Detection
module's tools/calibrate_fisheye.py).
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


class ALLSKYSKYMAP(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Sky Map",
        "description": "Limiting magnitude and sky brightness direction by direction: light domes, dark directions and transparency",
        "version": "v0.1.0",
        "module": "allsky_skymap",
        "events": [
            "night"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_skymap.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_skymap",
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
                "AS_SKYMAP_LM_ZENITH": {
                    "name": "${SKYMAP_LM_ZENITH}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Limiting magnitude at the zenith (stars seen by the camera)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYMAP_LM_MEAN": {
                    "name": "${SKYMAP_LM_MEAN}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Limiting magnitude, mean of the eight directions",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYMAP_BG_ZENITH": {
                    "name": "${SKYMAP_BG_ZENITH}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Sky background at the zenith (image brightness without stars, 0-255)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYMAP_DARKEST": {
                    "name": "${SKYMAP_DARKEST}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Direction with the faintest stars seen, e.g. 'N (6.8 mag)'",
                    "type": "string"
                },
                "AS_SKYMAP_DOME": {
                    "name": "${SKYMAP_DOME}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Brightest light dome, e.g. 'NE (+45%)'",
                    "type": "string"
                },
                "AS_SKYMAP_MAP": {
                    "name": "${SKYMAP_MAP}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Map",
                    "description": "Path of the map image",
                    "type": "string"
                }
            }
        },
        "arguments": {
            "calibration": "calibration.json",
            "sun_max": "-15",
            "moon_max": "-3",
            "clear_min": "80",
            "min_altitude": "25",
            "map_minutes": "30",
            "publish_web": "false",
            "graph": ""
        },
        "argumentdetails": {
            "calibration": {
                "required": "true",
                "description": "Fisheye calibration file",
                "help": "calibration.json in the modules folder, made with the Meteor Detection module's tools/calibrate_fisheye.py.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "text"
                }
            },
            "sun_max": {
                "required": "false",
                "description": "Sun below (deg)",
                "help": "Only measure when the Sun is at least this far below the horizon.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": -30,
                    "max": -6,
                    "step": 1
                }
            },
            "moon_max": {
                "required": "false",
                "description": "Moon below (deg)",
                "help": "Only measure when the Moon is at least this far below the horizon; moonlight brightens the whole sky.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": -20,
                    "max": 90,
                    "step": 1
                }
            },
            "clear_min": {
                "required": "false",
                "description": "Clear sky (%)",
                "help": "Only measure when at least this share of the bright stars (V < 3) is seen, i.e. the sky is clear.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 50,
                    "max": 100,
                    "step": 5
                }
            },
            "min_altitude": {
                "required": "false",
                "description": "Lowest altitude (deg)",
                "help": "The directions are measured from this altitude up to 60 degrees; above 60 degrees is the zenith.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 10,
                    "max": 45,
                    "step": 5
                }
            },
            "map_minutes": {
                "required": "false",
                "description": "Redraw the map every (minutes)",
                "help": "How often the map image is drawn.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 5,
                    "max": 240,
                    "step": 5
                }
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to the website",
                "help": "Copy skymap.png and skymap.json into the Website's skymap folder and upload them to a remote website (the remote folder must exist).",
                "tab": "Settings",
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
                        "Limiting magnitude and sky background for the zenith and eight directions on clear, moonless images",
                        "Blocked parts of the sky (trees, roofs) learnt from the stars",
                        "Nightly averages kept for a year and drawn as a map; light domes and the darkest direction for the overlay",
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
            result = f"Module Sky Map failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIRS = (os.path.join(_MODULE_DIR, "moduledata", "data", "allsky_skymap"),
              os.path.join(_MODULE_DIR, "allsky_skymap"), _MODULE_DIR)
SECTORS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
ZENITH = 8                  # region index of the zenith cap (above 60 deg)
ZENITH_ALT = 60.0
STAR_SNR = 8.0
STAR_RADIUS_4K = 4
BRIGHT = 3.0                # stars used for the clear-sky test
LEARN = 4.5                 # stars used to learn the blocked parts of the sky
CELL_ALT, CELL_AZ = 5, 10   # blocked-sky map cells (deg)
BLOCK_MIN_FRAMES = 10       # star sightings needed before a cell can be called blocked
BLOCK_SEEN = 0.2            # bright stars seen in less than this share -> blocked
KEEP_NIGHTS = 366


def _truthy(v):
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _dataFile(name):
    for d in _DATA_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return os.path.join(_DATA_DIRS[-1], name)


def _store():
    path = os.path.join(os.environ.get("ALLSKY_MYFILES_DIR") or _MODULE_DIR, "skymap")
    os.makedirs(path, exist_ok=True)
    return path


def _imageTime():
    try:
        return int(s.get_environment_variable("AS_TIMESTAMP"))
    except (TypeError, ValueError):
        return int(time.time())


def _load(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return default


def _save(path, data):
    with open(path + ".tmp", "w") as fh:
        json.dump(data, fh)
    os.replace(path + ".tmp", path)


# --- geometry -------------------------------------------------------------------

def _loadCalib(name, shape):
    path = name if os.path.isabs(name) else os.path.join(_MODULE_DIR, name)
    c = _load(path, None)
    if not c or not all(k in c for k in ("cx", "cy", "a1", "a3", "rot_deg", "flip")):
        return None
    h, w = shape[:2]
    sx, sy = w / float(c.get("W", w)), h / float(c.get("H", h))
    if abs(sx - sy) > 0.01 * sx:
        return None
    c = dict(c)
    for k in ("cx", "cy", "a1", "a3"):
        c[k] *= sx
    return c


def _project(c, alt, az):
    t = (90.0 - alt) / 90.0
    r = c["a1"] * t + c["a3"] * t ** 3
    a = np.radians(c["rot_deg"] + c["flip"] * az)
    return c["cx"] + r * np.sin(a), c["cy"] - r * np.cos(a)


def _lst(t, lon):
    d = t / 86400.0 + 2440587.5 - 2451545.0
    T = d / 36525.0
    return (280.46061837 + 360.98564736629 * d + 0.000387933 * T * T + lon) % 360.0


def _altaz(ra, dec, lst, lat):
    ra, dec, lat = np.radians(ra), np.radians(dec), math.radians(lat)
    ha = math.radians(lst) - ra
    alt = np.arcsin(np.sin(dec) * math.sin(lat) + np.cos(dec) * math.cos(lat) * np.cos(ha))
    az = np.arctan2(np.sin(ha), np.cos(ha) * math.sin(lat) - np.tan(dec) * math.cos(lat))
    return np.degrees(alt), (np.degrees(az) + 180.0) % 360.0


def _region(alt, az):
    return np.where(alt >= ZENITH_ALT, ZENITH, ((az + 22.5) // 45).astype(int) % 8)


def _sunMoon(lat, lon, t):
    import ephem
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = ephem.Date(t / 86400.0 + 25567.5)
    return math.degrees(ephem.Sun(obs).alt), math.degrees(ephem.Moon(obs).alt)


# --- measuring ---------------------------------------------------------------

def _stars():
    with open(_dataFile("stars.json")) as fh:
        return np.array(json.load(fh)["stars"], dtype=np.float64)


def _look(gray, calib, lat, lst, min_alt):
    """Catalogue stars above min_alt: alt, az, mag, seen, chance."""
    cat = _stars()
    alt, az = _altaz(cat[:, 0], cat[:, 1], lst, lat)
    m = alt >= min_alt
    alt, az, mag = alt[m], az[m], cat[m, 2]
    x, y = _project(calib, alt, az)
    h, w = gray.shape
    r = max(2, int(round(STAR_RADIUS_4K * w / 3840.0)))
    k = 3 * r
    ok = (x >= k) & (x < w - k) & (y >= k) & (y < h - k)
    alt, az, mag, x, y = alt[ok], az[ok], mag[ok], x[ok], y[ok]
    bg = cv2.medianBlur(gray, 31)
    hp = gray.astype(np.float32) - bg.astype(np.float32)
    noise = 1.4826 * float(np.median(np.abs(hp - np.median(hp)))) + 1e-3
    peak = cv2.dilate(hp, np.ones((2 * r + 1, 2 * r + 1), np.uint8))
    thr = STAR_SNR * noise
    xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
    seen = peak[yi, xi] > thr
    chance = np.mean([peak[yi + dy, xi + dx] > thr for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k))], axis=0)
    return alt, az, mag, seen, chance, bg


def _limitingMag(mag, seen, chance):
    """Magnitude where the chance-corrected share of stars seen falls to 50%
    (0.5 mag bins, interpolated).  None with too few stars."""
    prev = None
    for lo in np.arange(1.0, 7.51, 0.5):
        m = (mag >= lo) & (mag < lo + 0.5)
        if m.sum() < 4:
            continue
        ps, pc = float(seen[m].mean()), float(chance[m].mean())
        f = max(0.0, (ps - pc) / max(1e-3, 1.0 - pc))
        if f < 0.5:
            if prev is None:
                return round(float(lo), 2)
            pl, fl = prev
            return round(float(pl + 0.25 + (fl - 0.5) / max(1e-3, fl - f) * 0.5), 2)
        prev = (lo, f)
    return 7.5 if prev is not None else None


def _learnBlocked(st, alt, az, mag, seen):
    """Count, per cell, how often the bright stars in it are seen on clear images."""
    cells = st.setdefault("cells", {})
    ia, iz = (alt // CELL_ALT).astype(int), (az // CELL_AZ).astype(int)
    for a, z, m, sn in zip(ia, iz, mag, seen):
        if m >= LEARN:
            continue
        c = cells.setdefault(f"{a}:{z}", [0, 0])
        c[0] += 1
        c[1] += int(sn)


def _blocked(st, alt, az):
    """For each star: does it lie in a cell where bright stars are (almost)
    never seen on clear images, i.e. behind a tree or roof?"""
    cells = st.get("cells", {})
    ia, iz = (alt // CELL_ALT).astype(int), (az // CELL_AZ).astype(int)
    out = np.zeros(len(alt), bool)
    for i, (a, z) in enumerate(zip(ia, iz)):
        c = cells.get(f"{a}:{z}")
        out[i] = c is not None and c[0] >= BLOCK_MIN_FRAMES and c[1] / c[0] < BLOCK_SEEN
    return out


def _background(bg, calib, blockedCells, min_alt):
    """Median sky background per region, from points on an alt/az grid (stars
    filtered out, blocked cells left out)."""
    ga, gz = np.meshgrid(np.arange(min_alt + 1, 90, 3.0), np.arange(0, 360, 5.0))
    ga, gz = ga.ravel(), gz.ravel()
    keep = np.array([f"{int(a // CELL_ALT)}:{int(z // CELL_AZ)}" not in blockedCells for a, z in zip(ga, gz)])
    ga, gz = ga[keep], gz[keep]
    x, y = _project(calib, ga, gz)
    h, w = bg.shape
    ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    reg = _region(ga[ok], gz[ok])
    val = bg[y[ok].astype(int), x[ok].astype(int)].astype(float)
    return [float(np.median(val[reg == k])) if (reg == k).sum() >= 5 else None for k in range(9)]


# --- nightly averages and the map ------------------------------------------------

def _nightKey(t):
    return time.strftime("%Y%m%d", time.localtime(t - 12 * 3600))


def _addToNight(store, t, lm, bg):
    nights = store.setdefault("nights", {})
    n = nights.setdefault(_nightKey(t), {"frames": 0, "lm": [[] for _ in range(9)], "bg": [[] for _ in range(9)]})
    n["frames"] += 1
    for k in range(9):
        if lm[k] is not None:
            n["lm"][k].append(lm[k])
        if bg[k] is not None:
            n["bg"][k].append(round(bg[k], 1))
    for key in sorted(nights)[:-KEEP_NIGHTS]:
        del nights[key]


def _summary(store, nights=None):
    """Median limiting magnitude and background per region over the given
    nights (all if None)."""
    keys = sorted(store.get("nights", {}))
    if nights:
        keys = keys[-nights:]
    lm, bg = [], []
    for k in range(9):
        v = [x for key in keys for x in store["nights"][key]["lm"][k]]
        b = [x for key in keys for x in store["nights"][key]["bg"][k]]
        lm.append(round(float(np.median(v)), 2) if v else None)
        bg.append(round(float(np.median(b)), 1) if b else None)
    for k in _obstructed(bg):
        lm[k] = bg[k] = None
    return lm, bg, len(keys)


def _obstructed(bg):
    """Directions much darker than the sky around them: mostly trees or a roof,
    not sky.  Their values are left out of the summary."""
    vals = [v for v in bg[:8] if v is not None]
    if len(vals) < 3:
        return set()
    med = float(np.median(vals))
    return {k for k in range(8) if bg[k] is not None and bg[k] < 0.5 * med}


def _domes(bg):
    """Directions whose background is clearly above the median direction:
    the light domes of towns."""
    skip = _obstructed(bg)
    vals = [(bg[k], k) for k in range(8) if bg[k] is not None and k not in skip]
    if len(vals) < 3:
        return []
    med = float(np.median([v for v, _ in vals]))
    out = [(SECTORS[k], round(100.0 * (v - med) / max(1.0, med))) for v, k in vals if v > med * 1.1]
    return sorted(out, key=lambda d: -d[1])


def _drawMap(path, lm_last, bg_last, lm_all, bg_all, n_all, night):
    """Two polar maps (limiting magnitude, background) for the last night and
    for all nights."""
    W, H = 1600, 900
    img = np.full((H, W, 3), (24, 18, 14), np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    def colour(v, lo, hi, invert=False):
        f = 0.0 if v is None else float(np.clip((v - lo) / (hi - lo), 0, 1))
        f = 1 - f if invert else f
        c = cv2.applyColorMap(np.array([[int(f * 255)]], np.uint8), cv2.COLORMAP_VIRIDIS)[0, 0]
        return (60, 60, 60) if v is None else tuple(int(x) for x in c)

    def polar(cx, cy, R, vals, lo, hi, invert, fmt, title):
        # sector k is centred at -90 - 45k degrees: North up, East left
        for k in range(8):
            a0 = -90 - k * 45 - 22.5
            cv2.ellipse(img, (cx, cy), (R, R), 0, a0, a0 + 45, colour(vals[k], lo, hi, invert), -1)
            cv2.ellipse(img, (cx, cy), (R, R), 0, a0, a0 + 45, (24, 18, 14), 2)
        cv2.circle(img, (cx, cy), int(R / 3), colour(vals[ZENITH], lo, hi, invert), -1)
        cv2.circle(img, (cx, cy), int(R / 3), (24, 18, 14), 2)
        for k in range(8):
            ang = math.radians(-90 - k * 45)
            tx, ty = cx + int(0.68 * R * math.cos(ang)), cy + int(0.68 * R * math.sin(ang))
            txt = fmt(vals[k]) if vals[k] is not None else "-"
            cv2.putText(img, txt, (tx - 30, ty + 8), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            lx, ly = cx + int((R + 22) * math.cos(ang)), cy + int((R + 22) * math.sin(ang))
            cv2.putText(img, SECTORS[k], (lx - 12, ly + 8), font, 0.7, (200, 200, 200), 2, cv2.LINE_AA)
        cv2.putText(img, fmt(vals[ZENITH]) if vals[ZENITH] is not None else "-", (cx - 30, cy + 8), font, 0.7,
                    (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, title, (cx - R, cy - R - 40), font, 0.8, (235, 235, 235), 2, cv2.LINE_AA)

    # the map is seen from below, like the sky: East on the left
    R = 250
    polar(330, 360, R, lm_last, 4.0, 7.0, False, lambda v: f"{v:.1f}", f"Limiting mag. night {night}")
    polar(1000, 360, R, bg_last, 20, 150, True, lambda v: f"{v:.0f}", "Sky background, same night")
    cv2.putText(img, f"All {n_all} nights: limiting magnitude zenith {lm_all[ZENITH] or '-'}, "
                     f"background zenith {bg_all[ZENITH] or '-'}", (60, 700), font, 0.8, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.putText(img, "Brighter colour = darker sky / fainter stars seen. Seen from below: East is left of North.",
                (60, 750), font, 0.7, (160, 160, 160), 1, cv2.LINE_AA)
    cv2.imwrite(path, img)


# --- main --------------------------------------------------------------------

def _run(module):
    if s.image is None:
        return "No image available"
    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    calib = _loadCalib(params["calibration"].strip(), s.image.shape)
    if calib is None:
        return "Sky Map needs a fisheye calibration (calibration.json, see the README)"
    lat, lon = float(calib["lat"]), float(calib["lon"])
    t0 = _imageTime()
    sun, moon = _sunMoon(lat, lon, t0)
    if sun > s.asfloat(params["sun_max"]):
        return f"Sky Map: not dark enough (Sun {sun:.0f}°)"
    if moon > s.asfloat(params["moon_max"]):
        return f"Sky Map: the Moon is up ({moon:.0f}°)"

    min_alt = s.asfloat(params["min_altitude"])
    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if s.image.ndim == 3 else s.image
    alt, az, mag, seen, chance, bg = _look(gray, calib, lat, _lst(t0, lon), min_alt)
    bright = mag < BRIGHT
    if bright.sum() < 20:
        return "Sky Map: too few catalogue stars in the image - check the calibration"
    store_path = os.path.join(_store(), "skymap_data.json")
    store = _load(store_path, {})
    blocked = _blocked(store, alt, az)
    clear = 100.0 * float(seen[bright & ~blocked].mean())
    if clear < s.asfloat(params["clear_min"]):
        return f"Sky Map: not clear ({clear:.0f}% of the bright stars seen)"
    _learnBlocked(store, alt, az, mag, seen)          # only from clear images
    blocked = _blocked(store, alt, az)
    use = ~blocked
    reg = _region(alt, az)
    lm = [(_limitingMag(mag[use & (reg == k)], seen[use & (reg == k)], chance[use & (reg == k)])
           if (use & (reg == k)).sum() >= 15 else None) for k in range(9)]
    blocked_cells = {c for c, v in store.get("cells", {}).items() if v[0] >= BLOCK_MIN_FRAMES and v[1] / v[0] < BLOCK_SEEN}
    bgv = _background(bg, calib, blocked_cells, min_alt)
    _addToNight(store, t0, lm, bgv)
    _save(store_path, store)

    lm_last, bg_last, _ = _summary(store, 1)
    lm_all, bg_all, n_all = _summary(store)
    dirs = [(lm_all[k], SECTORS[k]) for k in range(8) if lm_all[k] is not None]
    darkest = max(dirs) if dirs else None
    domes = _domes(bg_all)
    map_path = os.path.join(_store(), "skymap.png")
    if not os.path.isfile(map_path) or time.time() - os.path.getmtime(map_path) > 60 * s.asfloat(params["map_minutes"]):
        _drawMap(map_path, lm_last, bg_last, lm_all, bg_all, n_all, _nightKey(t0))
        summary = {"night": _nightKey(t0), "nights": n_all, "sectors": list(SECTORS) + ["zenith"],
                   "lm_last_night": lm_last, "bg_last_night": bg_last, "lm_all": lm_all, "bg_all": bg_all,
                   "light_domes": domes, "blocked_cells": sorted(blocked_cells)}
        _save(os.path.join(_store(), "skymap.json"), summary)
        if _truthy(params["publish_web"]):
            _publish([map_path, os.path.join(_store(), "skymap.json")])

    lm_dirs = [v for v in lm[:8] if v is not None]
    values = {"AS_SKYMAP_LM_ZENITH": lm[ZENITH], "AS_SKYMAP_LM_MEAN": round(float(np.mean(lm_dirs)), 2) if lm_dirs else None,
              "AS_SKYMAP_BG_ZENITH": round(bgv[ZENITH], 1) if bgv[ZENITH] is not None else None,
              "AS_SKYMAP_DARKEST": f"{darkest[1]} ({darkest[0]:.1f} mag)" if darkest else "",
              "AS_SKYMAP_DOME": f"{domes[0][0]} (+{domes[0][1]}%)" if domes else "",
              "AS_SKYMAP_MAP": map_path}
    values = {k: v for k, v in values.items() if v is not None}
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)
    txt = " ".join(f"{(SECTORS + ('Z',))[k]}:{lm[k]:.1f}" if lm[k] is not None else f"{(SECTORS + ('Z',))[k]}:-" for k in range(9))
    result = f"Sky Map: limiting magnitude {txt}; {int(blocked.sum())} stars behind obstacles"
    module.log(4, f"INFO: {result}")
    return result


def _publish(files):
    import shutil
    import subprocess
    home = s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky")
    website = s.get_environment_variable("ALLSKY_WEBSITE") or os.path.join(home, "html", "allsky")
    folder = os.path.join(website, "skymap")
    os.makedirs(folder, exist_ok=True)
    for f in files:
        shutil.copy2(f, os.path.join(folder, os.path.basename(f)))
    if str(s.getSetting("useremotewebsite")).lower() in ("true", "1", "yes", "on"):
        uploader = os.path.join(s.get_environment_variable("ALLSKY_SCRIPTS") or os.path.join(home, "scripts"), "upload.sh")
        rdir = ((s.getSetting("remotewebsiteimagedir") or "").rstrip("/") + "/skymap").lstrip("/")
        for f in files:
            if os.path.isfile(uploader):
                subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", f, rdir, os.path.basename(f), "SkyMap"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def skymap(params, event):
    return ALLSKYSKYMAP(params, event).run()


def skymap_cleanup():
    moduleData = {
        "metaData": ALLSKYSKYMAP.meta_data,
        "cleanup": {
            "files": {
                ALLSKYSKYMAP.meta_data["extradatafilename"]
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
