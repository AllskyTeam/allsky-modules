""" allsky_aurora.py

Aurora (northern / southern lights) candidate detector for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)
Home / docs: https://github.com/benhartwich/allsky-aurora

At mid latitudes an aurora shows up as a green glow or arc LOW on the polar
horizon (North in the northern hemisphere, South in the southern), sometimes with
red rays above it during a strong geomagnetic storm.  The green is atomic-oxygen
emission at 557.7 nm, so the most telling property of an aurora, compared with
everything else that brightens that part of the sky at night, is that it is
GREEN: green above red AND green above blue.

That double test is what makes this robust.  The traps at night are:
  * moonlit / light-polluted cloud: bright but RED-dominant (sodium or moon
    light), green far BELOW red, so it is rejected;
  * blue twilight or a blue light-pollution dome: green below blue, rejected;
  * airglow: really green, but faint, uniform and all-sky rather than a
    structured arc low on the polar horizon; the band + structure test
    suppresses it.

The module only looks when the Sun is well below the horizon, builds a band low
on the polar horizon (from a fisheye calibration if there is one, else from the
image centre and "North in the image"), and scores it for a green, structured,
above-background glow.

Scope: this is a *candidate* detector.  An aurora at mid latitudes is rare (it
needs a strong storm).  The module computes a green index, flags likely frames,
and saves a thumbnail of the band so a human can confirm.  The values go into
the Allsky database for the charts it brings along.
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import re
import sys
import json
import math
import time
import subprocess
import cv2
import numpy as np


class ALLSKYAURORA(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Aurora Detector",
        "description": "Flags a possible aurora: a green (over red and blue), structured glow low on the polar horizon, only when it is dark",
        "version": "v0.2.0",
        "module": "allsky_aurora",
        "events": [
            "night"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_aurora.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_aurora",
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
                "AS_AURORA": {
                    "name": "${AURORA}",
                    "format": "",
                    "sample": "",
                    "group": "Aurora",
                    "description": "Possible aurora, 1 = yes, 0 = no",
                    "type": "bool",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_AURORA_INDEX": {
                    "name": "${AURORA_INDEX}",
                    "format": "",
                    "sample": "",
                    "group": "Aurora",
                    "description": "Aurora index: % of the band that is green, structured and above the background",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_AURORA_GREEN": {
                    "name": "${AURORA_GREEN}",
                    "format": "",
                    "sample": "",
                    "group": "Aurora",
                    "description": "How much greener than red the flagged glow is",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_AURORA_STRUCTURE": {
                    "name": "${AURORA_STRUCTURE}",
                    "format": "",
                    "sample": "",
                    "group": "Aurora",
                    "description": "How far the flagged glow is above the smooth background",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_AURORA_THUMBNAIL": {
                    "name": "${AURORA_THUMBNAIL}",
                    "format": "",
                    "sample": "",
                    "group": "Aurora",
                    "description": "File name of the candidate thumbnail saved on this frame",
                    "type": "string"
                }
            }
        },
        "arguments": {
            "sun_max": "-14",
            "r_inner": "0.60",
            "r_outer": "0.98",
            "az_half": "70",
            "green_over_red": "8",
            "green_over_blue": "6",
            "residual_thr": "6",
            "dark_floor": "24",
            "bright_ceil": "252",
            "edge_erode": "8",
            "min_index": "0.6",
            "cloud_max": "85",
            "work_width": "720",
            "mask": "",
            "calibration": "calibration.json",
            "pole_angle": "0",
            "save_thumbnail": "true",
            "history_hours": "72",
            "publish_web": "false",
            "debug": "false"
        },
        "argumentdetails": {
            "sun_max": {
                "required": "false",
                "description": "Sun altitude — darkness limit (deg)",
                "help": "Only look while the Sun is at or below this altitude. Aurora needs a dark sky; in twilight the green test is unreliable. Negative number (default -14).",
                "type": {
                    "fieldtype": "spinner",
                    "min": -18,
                    "max": -6,
                    "step": 1
                }
            },
            "r_inner": {
                "required": "false",
                "description": "ROI band — inner radius (fraction of disc)",
                "help": "Inner edge of the arc as a fraction of the visible fisheye-disc radius (0 = centre/zenith, 1 = disc edge). 0.60 keeps it off the zenith.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.0,
                    "max": 0.9,
                    "step": 0.05
                }
            },
            "r_outer": {
                "required": "false",
                "description": "ROI band — outer radius (fraction of disc)",
                "help": "Outer edge of the arc as a fraction of the disc radius. 0.98 reaches almost to the disc edge, the lowest altitude the lens sees, where an aurora appears first.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.5,
                    "max": 1.0,
                    "step": 0.02
                }
            },
            "az_half": {
                "required": "false",
                "description": "ROI band — half-width around the pole direction (deg)",
                "help": "Angular half-width of the arc either side of North (South in the southern hemisphere). 70 = a 140 deg arc.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 30,
                    "max": 120,
                    "step": 5
                }
            },
            "green_over_red": {
                "required": "false",
                "description": "Min green excess over red (G-R)",
                "help": "An aurora pixel must have green clearly above red. This is the key filter: moonlit / light-polluted cloud is RED-dominant (G-R strongly negative) and is rejected here. Higher = stricter.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 40,
                    "step": 1
                }
            },
            "green_over_blue": {
                "required": "false",
                "description": "Min green excess over blue (G-B)",
                "help": "Green must also be above blue, rejecting a blue twilight sky or a blue light-pollution dome. Higher = stricter.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 40,
                    "step": 1
                }
            },
            "residual_thr": {
                "required": "false",
                "description": "Min brightness residual",
                "help": "How far above the smoothed background a feature must sit, so a smooth uniform green airglow is separated from a structured arc/rays. Higher = stricter.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 40,
                    "step": 1
                }
            },
            "dark_floor": {
                "required": "false",
                "description": "Dark floor (brightness)",
                "help": "Pixels dimmer than this are treated as empty dark sky, never aurora. In a dark image the limit is lowered to 80% of the band's median brightness.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 120,
                    "step": 2
                }
            },
            "bright_ceil": {
                "required": "false",
                "description": "Bright ceiling (saturation)",
                "help": "Pixels brighter than this are treated as blown-out / burnt-in overlay graphics, never aurora. Run this module BEFORE allsky_overlay so the compass/text are not in the image.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 150,
                    "max": 255,
                    "step": 5
                }
            },
            "edge_erode": {
                "required": "false",
                "description": "Edge erosion (px)",
                "help": "Shrink the in-band region inward by this many pixels (at analysis scale) to remove the bright/dark boundary at the vignette rim and treeline, which would otherwise read as false structure.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 25,
                    "step": 1
                }
            },
            "min_index": {
                "required": "false",
                "description": "Detection threshold (% of band)",
                "help": "Flag an aurora candidate when at least this percentage of the northern band is green + structured + above background.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.1,
                    "max": 20,
                    "step": 0.1
                }
            },
            "cloud_max": {
                "required": "false",
                "description": "Max cloud cover (%)",
                "help": "Skip when the cloud cover from the Cloud Forecast or Sky Quality Meter module (if one runs before this module) is above this; a fully overcast sky can't show an aurora. Ignored if neither runs.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 20,
                    "max": 100,
                    "step": 5
                }
            },
            "work_width": {
                "required": "false",
                "description": "Analysis width (px)",
                "help": "The band crop is downscaled to this width for speed. 720 is plenty on a 4K frame.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 320,
                    "max": 1920,
                    "step": 40
                }
            },
            "mask": {
                "required": "false",
                "description": "Sky mask (optional)",
                "help": "Optional mask image (overlay images folder). Black = ignore (e.g. trees on the northern horizon). Intersected with the band.",
                "type": {
                    "fieldtype": "image"
                }
            },
            "calibration": {
                "required": "false",
                "description": "Fisheye calibration file",
                "help": "Optional fisheye calibration (calibration.json, as made by the Meteor Detection module's tools) in the modules folder. With it, the band uses the true optical centre and North; without it, the image centre and 'North in the image'.",
                "type": {
                    "fieldtype": "text"
                }
            },
            "pole_angle": {
                "required": "false",
                "description": "North in the image (deg)",
                "help": "Only used without a calibration: where North is in the image, in degrees clockwise from the top (0 = North is up). The Website's constellation overlay 'az' setting is a good value to start with.",
                "type": {
                    "fieldtype": "spinner",
                    "min": -180,
                    "max": 180,
                    "step": 1
                }
            },
            "save_thumbnail": {
                "required": "false",
                "description": "Save candidate thumbnail",
                "help": "When a candidate is flagged, save a colour crop of the band in the day's images folder (aurora/), so you can confirm it by eye.",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "history_hours": {
                "required": "false",
                "description": "History (hours)",
                "help": "How much history aurora.json keeps.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 336,
                    "step": 1
                },
                "tab": "Website"
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to Website",
                "help": "Also write a rolling aurora.json (and the thumbnails) into the website folder and upload them to the remote website if enabled, for your own website pages. The WebUI charts don't need this.",
                "type": {
                    "fieldtype": "checkbox"
                },
                "tab": "Website"
            },
            "debug": {
                "required": "false",
                "description": "Enable debug images",
                "help": "Write the band ROI and candidate mask to the allsky tmp debug folder.",
                "tab": "Debug",
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
                    "changes": "Initial darkness-gated northern-band aurora candidate detector: green-over-red AND green-over-blue, structured above background, coherent blobs; rolling json + thumbnail for confirmation. The green-over-red test rejects the moonlit/light-polluted red cloud that fools a green-over-blue-only index."
                }
            ],
            "v0.2.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Class-based module for Allsky v2025",
                        "Works in both hemispheres: in the southern hemisphere the band looks South",
                        "Without a calibration, 'North in the image' sets the direction; a calibration.json made by the Meteor Detection module's tools is used when present",
                        "Values are saved in the Allsky database and the module brings charts: aurora index and a 'possible aurora' indicator",
                        "Values are available in the Overlay Editor (AS_AURORA, AS_AURORA_INDEX, AS_AURORA_GREEN, AS_AURORA_STRUCTURE)",
                        "The cloud gate reads the Cloud Forecast or Sky Quality Meter module's cloud cover",
                        "The darkness gate uses the time the image was taken",
                        "Candidate thumbnails go into the day's images folder (aurora/) instead of tmp; publishing to the website is off by default"
                    ]
                }
            ]
        }
    }

    def run(self):
        try:
            return _measure(self)
        except Exception as e:
            _, _, tb = sys.exc_info()
            result = f"Module Aurora Detector failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_maskCache = {"name": None, "mask": None}
_calibCache = {"name": None, "calib": None}
CLOUD_MAX_AGE = 900     # seconds; an older cloud value from another module is ignored


def _truthy(v):
    """Checkbox args arrive from the flow config as the STRING 'true'/'false';
    'false' is truthy in Python, so parse booleans explicitly."""
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _imageTime():
    """When the image was taken (AS_TIMESTAMP), else now."""
    try:
        return int(s.get_environment_variable("AS_TIMESTAMP"))
    except (TypeError, ValueError):
        return int(time.time())


def _latitude():
    try:
        return float(s.convertLatLon(s.getSetting("latitude")))
    except Exception:
        return None


# --- Sun position -----------------------------------------------------------

def _sunAlt():
    """Sun altitude in degrees when the image was taken, via ephem. None if it
    can't be computed (then the module does NOT gate on darkness)."""
    try:
        import ephem
        from datetime import datetime, timezone
        obs = ephem.Observer()
        obs.lat = str(s.convertLatLon(s.getSetting("latitude")))
        obs.lon = str(s.convertLatLon(s.getSetting("longitude")))
        obs.date = ephem.Date(datetime.fromtimestamp(_imageTime(), timezone.utc).replace(tzinfo=None))
        sun = ephem.Sun()
        sun.compute(obs)
        return math.degrees(float(sun.alt))
    except Exception:
        return None


# --- Cloud cover from another module ------------------------------------------

def _cloudCover():
    """Cloud cover in % from the Cloud Forecast or Sky Quality Meter module, if
    one of them wrote it in the last CLOUD_MAX_AGE seconds, else None."""
    for fname, key in (("allsky_cloudforecast.json", "AS_CLOUDFORECAST_COVER"),
                       ("allsky_skyquality.json", "AS_SKYQUALITY_CLOUD")):
        try:
            data = s.load_extra_data_file(fname)
            if not data or key not in data:
                continue
            fresh = False
            for d in s.get_extra_dir() or []:
                p = os.path.join(d, fname) if d else None
                if p and os.path.isfile(p) and time.time() - os.path.getmtime(p) < CLOUD_MAX_AGE:
                    fresh = True
            if not fresh:
                continue
            v = data[key]
            return float(v.get("value") if isinstance(v, dict) else v)
        except Exception:
            continue
    return None


# --- Region of interest -----------------------------------------------------

def _loadCalib(name):
    """calibration.json in the modules folder (beside this module), as made by the
    Meteor Detection module's tools.  None if there is none."""
    if not name:
        return None
    if _calibCache["name"] == name and _calibCache["calib"] is not None:
        return _calibCache["calib"]
    path = name if os.path.isabs(name) else os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    try:
        with open(path) as fh:
            c = json.load(fh)
        if "cx" not in c or "cy" not in c:
            raise ValueError("not a fisheye calibration")
        _calibCache.update(name=name, calib=c)
        return c
    except Exception:
        _calibCache.update(name=name, calib=None)
        return None


def _bandMask(shape, params, calib, south):
    """uint8 mask of an arc toward the pole within the visible fisheye disc.

    Rather than project (alt,az), which on a zoomed lens can land outside the
    visible disc, the arc is built geometrically as a sector of the visible disc:
      * disc centre from the calibration (optical centre), else the image centre;
      * disc radius = the largest circle that fits the frame;
      * North from the calibration's rotation, else from 'North in the image';
        in the southern hemisphere the arc points the opposite way (South).
    A pixel is kept if its distance from the centre is r_inner..r_outer of the disc
    radius AND its bearing is within az_half of the pole direction."""
    h, w = shape
    if calib is not None:
        cx, cy = float(calib["cx"]), float(calib["cy"])
        rot = math.radians(float(calib.get("rot_deg", 0.0)))
    else:
        cx, cy = w / 2.0, h / 2.0
        rot = math.radians(s.asfloat(params.get("pole_angle", 0)) or 0.0)
    if south:
        rot += math.pi
    R = min(cx, cy, w - cx, h - cy)                 # inscribed disc radius
    r_inner = s.asfloat(params.get("r_inner", 0.60)) * R
    r_outer = s.asfloat(params.get("r_outer", 0.98)) * R
    az_half = s.asfloat(params.get("az_half", 70))

    yy, xx = np.mgrid[0:h, 0:w]
    dx = xx - cx
    dy = cy - yy                                     # up-positive
    rho = np.hypot(dx, dy)
    nx, ny = math.sin(rot), math.cos(rot)           # pole unit vector
    with np.errstate(invalid="ignore", divide="ignore"):
        cosang = (dx * nx + dy * ny) / np.maximum(rho, 1e-6)
    ang = np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))
    keep = (rho >= r_inner) & (rho <= r_outer) & (ang <= az_half)
    return (keep.astype(np.uint8)) * 255


def _userMask(params, shape):
    """Optional tree/horizon mask (white = keep). Cached."""
    name = params.get("mask", "").strip()
    if not name:
        return None
    if _maskCache["name"] == name and _maskCache["mask"] is not None \
            and _maskCache["mask"].shape == shape:
        return _maskCache["mask"]
    p = os.path.join(s.ALLSKY_OVERLAY, "images", name)
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    if m.shape != shape:
        m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    _maskCache.update(name=name, mask=m)
    return m


# --- Detection --------------------------------------------------------------

def _detect(bgr, band, params):
    """Score the northern band for aurora. Returns a dict of metrics + a candidate
    flag. Aurora pixels are GREEN (above red AND blue), STRUCTURED (above the
    smooth background) and coherent (extended blobs, not single specks)."""
    ys, xs = np.where(band > 0)
    if len(ys) < 50:
        return None
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    crop = bgr[y0:y1, x0:x1]
    bmask = band[y0:y1, x0:x1]

    work_w = max(160, s.int(params.get("work_width", 720)))
    ch, cw = crop.shape[:2]
    if cw > work_w:
        scale = work_w / float(cw)
        crop = cv2.resize(crop, (work_w, max(1, int(ch * scale))), interpolation=cv2.INTER_AREA)
        bmask = cv2.resize(bmask, (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_NEAREST)
    inb = bmask > 127
    if int(inb.sum()) < 50:
        return None

    # suppress stars: bright point sources would otherwise read as tiny "aurora".
    # A median filter removes points while preserving extended structure.
    crop = cv2.medianBlur(crop, 5)

    b, g, r = cv2.split(crop.astype(np.int16))
    val = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)

    gor_thr = s.asfloat(params.get("green_over_red", 8))
    gob_thr = s.asfloat(params.get("green_over_blue", 6))
    res_thr = s.asfloat(params.get("residual_thr", 6))
    floor = s.asfloat(params.get("dark_floor", 24))
    ceil = s.asfloat(params.get("bright_ceil", 252))
    erode_px = max(1, s.int(params.get("edge_erode", 8)))

    # The floor is relative to the band's own brightness too, so a dark image
    # (no stretch, short exposure) isn't all "empty sky".
    if int(inb.sum()):
        floor = min(floor, 0.8 * float(np.median(val[inb])))

    # INTERIOR sky only: erode the valid, lit, in-band region inward to kill the
    # bright/dark boundary at the vignette rim / treeline (false structure).
    valid = (inb & (val > floor) & (val < ceil)).astype(np.uint8) * 255
    valid = cv2.erode(valid, np.ones((2 * erode_px + 1, 2 * erode_px + 1), np.uint8))
    interior = valid > 0
    n_int = int(interior.sum())
    if n_int < 50:
        return None

    # remove the smooth background glow -> keep structured brightening only
    k = max(31, (crop.shape[1] // 12) | 1)
    background = cv2.GaussianBlur(val, (k, k), 0)
    residual = val - background

    green_over_red = g - r                      # THE discriminator vs red cloud
    green_over_blue = g - b                      # vs blue twilight / LP dome

    cand = interior & (green_over_red > gor_thr) & (green_over_blue > gob_thr) \
        & (residual > res_thr)
    cand_u8 = cv2.morphologyEx(cand.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    # keep only coherent, EXTENDED blobs (a real arc/rays are patchy/banded, not
    # single specks — those would be residual stars or hot pixels)
    keep = np.zeros_like(cand_u8)
    n_blobs = 0
    if int(cand_u8.sum()):
        num, labels, stats, _ = cv2.connectedComponentsWithStats(cand_u8, 8)
        min_blob = max(25, n_int // 150)
        for i in range(1, num):
            if stats[i, cv2.CC_STAT_AREA] >= min_blob:
                keep[labels == i] = 255
                n_blobs += 1
    kept = keep > 0
    n_cand = int(kept.sum())
    index = 100.0 * n_cand / n_int
    green_mean = float(green_over_red[kept].mean()) if n_cand else 0.0
    structure = float(residual[kept].mean()) if n_cand else 0.0

    min_index = s.asfloat(params.get("min_index", 0.6))
    candidate = (index >= min_index) and (n_blobs >= 1)

    return {
        "index": round(index, 2),
        "green": round(green_mean, 1),
        "structure": round(structure, 1),
        "blobs": n_blobs,
        "candidate": bool(candidate),
        "crop_box": (x0, y0, x1, y1),
        "cand_mask": keep,
    }


# --- Saving -------------------------------------------------------------------

def _currentDay():
    """Allsky's day-folder name (DATE_NAME), which stays on the evening's date
    after midnight."""
    day = str(s.get_environment_variable("DATE_NAME") or "")
    if re.fullmatch(r"\d{8}", day):
        return day
    return time.strftime("%Y%m%d", time.localtime(_imageTime() - 12 * 3600))


def _websiteDataDir():
    website = s.get_environment_variable("ALLSKY_WEBSITE")
    if not website:
        website = os.path.join(s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky"),
                               "html", "allsky")
    return website


def _uploadRemote(local, fname, subdir=""):
    """Upload a file to the remote website (optionally into a subdir, e.g. 'aurora').
    The subdir must already exist on the server. Never raises."""
    try:
        if str(s.getSetting("useremotewebsite")).lower() not in ("true", "1", "yes", "on"):
            return
        scripts = s.get_environment_variable("ALLSKY_SCRIPTS") or \
            os.path.join(s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "scripts")
        uploader = os.path.join(scripts, "upload.sh")
        if not os.path.isfile(uploader) or not os.path.isfile(local):
            return
        rdir = (s.getSetting("remotewebsiteimagedir") or "").rstrip("/")
        if subdir:
            rdir = f"{rdir}/{subdir.strip('/')}"
        subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", local, rdir, fname, "Aurora"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        s.log(1, f"WARNING: aurora remote upload failed: {ex}")


def _appendHistory(record, hours):
    """Rolling aurora.json in tmp, published to the website. Never raises."""
    path = os.path.join(s.ALLSKY_TMP, "aurora.json")
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        data = []
    data.append(record)
    cutoff = record["t"] - hours * 3600
    data = [d for d in data if d.get("t", 0) >= cutoff][-5000:]
    try:
        with open(path, "w") as f:
            json.dump(data, f)
        ddir = _websiteDataDir()
        os.makedirs(ddir, exist_ok=True)
        webpath = os.path.join(ddir, "aurora.json")
        with open(webpath, "w") as f:
            json.dump(data, f)
        _uploadRemote(webpath, "aurora.json")
    except Exception as ex:
        s.log(1, f"WARNING: aurora could not publish to website: {ex}")


def _saveThumb(bgr, box, publish_web):
    """Save a colour crop of the band in images/<day>/aurora/ for human
    confirmation, and optionally publish it to the website."""
    try:
        x0, y0, x1, y1 = box
        pad = 20
        h, w = bgr.shape[:2]
        crop = bgr[max(0, y0 - pad):min(h, y1 + pad), max(0, x0 - pad):min(w, x1 + pad)]
        if crop.size == 0:
            return None
        fname = time.strftime("aurora-%Y%m%d%H%M%S.jpg", time.localtime(_imageTime()))
        images = s.get_environment_variable("ALLSKY_IMAGES") or \
            os.path.join(s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "images")
        daydir = os.path.join(images, _currentDay(), "aurora")
        os.makedirs(daydir, exist_ok=True)
        cv2.imwrite(os.path.join(daydir, fname), crop, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if publish_web:
            wdir = os.path.join(_websiteDataDir(), "aurora")
            os.makedirs(wdir, exist_ok=True)
            webthumb = os.path.join(wdir, fname)
            cv2.imwrite(webthumb, crop, [cv2.IMWRITE_JPEG_QUALITY, 88])
            _uploadRemote(webthumb, fname, subdir="aurora")
        return fname
    except Exception as ex:
        s.log(1, f"WARNING: aurora could not save thumbnail: {ex}")
        return None


def _measure(module):
    if s.image is None:
        return "No image available"
    if len(s.image.shape) != 3:
        return "Aurora needs a colour image"

    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    debug = _truthy(params["debug"])

    # --- darkness gate ---
    sun_alt = _sunAlt()
    sun_max = s.asfloat(params["sun_max"])
    if sun_alt is not None and sun_alt > sun_max:
        return f"Aurora: not dark enough (sun {sun_alt:.1f} deg, need <= {sun_max}) — skipped"

    # --- cloud gate (only if another module measured the cloud cover) ---
    cloud = _cloudCover()
    cloud_max = s.asfloat(params["cloud_max"])
    if cloud is not None and cloud > cloud_max:
        return f"Aurora: overcast ({cloud:.0f}% cloud > {cloud_max}%) — skipped"

    lat = _latitude()
    south = lat is not None and lat < 0
    calib = _loadCalib(params["calibration"].strip())
    shape = s.image.shape[:2]
    band = _bandMask(shape, params, calib, south)
    umask = _userMask(params, shape)
    if umask is not None:
        band = cv2.bitwise_and(band, umask)

    if debug:
        s.startModuleDebug(module.meta_data["module"])
        s.writeDebugImage(module.meta_data["module"], "aurora-band.png",
                          cv2.bitwise_and(s.image, s.image, mask=band))

    det = _detect(s.image, band, params)
    if det is None:
        return "Aurora: band empty or too small — nothing to score"

    if debug:
        s.writeDebugImage(module.meta_data["module"], "aurora-candidate.png", det["cand_mask"])

    publish_web = _truthy(params["publish_web"])
    thumb = None
    if det["candidate"] and _truthy(params["save_thumbnail"]):
        thumb = _saveThumb(s.image, det["crop_box"], publish_web)

    values = {
        "AS_AURORA": 1 if det["candidate"] else 0,
        "AS_AURORA_INDEX": det["index"],
        "AS_AURORA_GREEN": det["green"],
        "AS_AURORA_STRUCTURE": det["structure"],
        "AS_AURORA_THUMBNAIL": thumb or "",
    }
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)

    if publish_web:
        rec = {"t": _imageTime(), "index": det["index"], "green": det["green"],
               "structure": det["structure"], "blobs": det["blobs"],
               "aurora": det["candidate"], "calib": calib is not None}
        if sun_alt is not None:
            rec["sun_alt"] = round(sun_alt, 1)
        if thumb:
            rec["thumb"] = thumb
        _appendHistory(rec, s.int(params["history_hours"]))

    pole = "southern" if south else "northern"
    if det["candidate"]:
        result = (f"POSSIBLE AURORA — index {det['index']:.1f}% of the {pole} band, "
                  f"{det['blobs']} patches, green +{det['green']:.0f} over red, "
                  f"structure {det['structure']:.0f}")
        module.log(1, f"INFO: {result}")
    else:
        result = f"Aurora: clear — green index {det['index']:.2f}% (watching the {pole} horizon)"
        module.log(4, f"INFO: {result}")
    return result


def aurora(params, event):
    return ALLSKYAURORA(params, event).run()


def aurora_cleanup():
    moduleData = {
        "metaData": ALLSKYAURORA.meta_data,
        "cleanup": {
            "files": {
                ALLSKYAURORA.meta_data["extradatafilename"],
                os.path.join(s.ALLSKY_TMP, "aurora.json")
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
