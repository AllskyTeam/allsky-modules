""" allsky_skyquality.py

Sky Quality Meter (SQM) module for Allsky.
https://github.com/AllskyTeam/allsky

Reports sky brightness in **mag/arcsec²**, following the approach used by
indi-allsky:

    mag = offset − 2.5 · log10(signal)

The important difference to a naive ADU measurement: Allsky uses AUTO exposure
and gain at night, so the raw mean ADU is NOT comparable between frames (a darker
sky simply gets a longer exposure / higher gain and ends up at a similar ADU).
This module therefore normalises the mean ADU by exposure time and gain first, so
the result tracks the true sky brightness instead of the exposure control loop:

    signal = mean_ADU / exposure_s / gain_factor
    mag    = offset − 2.5 · log10(signal)

The sky brightness is measured day and night, so its chart shows the whole
24 hours including twilight.  At night the same value is the SQM reading, and
the naked-eye limiting magnitude, star count, cloud cover and aurora index are
added.  Everything is saved in the Allsky database for the charts the module
brings along, and optionally in a rolling `skyquality.json` for a website.

`offset` must be calibrated once against a real SQM device (or a known dark-sky
reading).
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import json
import math
import time
import subprocess
import cv2
import numpy as np


class ALLSKYSKYQUALITY(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Sky Quality Meter",
        "description": "Sky brightness in mag/arcsec2 day and night, with SQM, limiting magnitude, stars and cloud cover at night, and charts",
        "version": "v0.3.0",
        "module": "allsky_skyquality",
        "events": [
            "day",
            "night"
        ],
        "experimental": "false",
        "centersettings": "false",
        "testable": "false",
        "group": "Data Capture",
        "extradatafilename": "allsky_skyquality.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_skyquality",
                "pk": "id",
                "pk_type": "int",
                "include_all": "false",
                "time_of_day_save": {
                    "day": "always",
                    "night": "always",
                    "nightday": "never",
                    "daynight": "never",
                    "periodic": "never"
                }
            },
            "values": {
                "AS_SKYQUALITY_BRIGHTNESS": {
                    "name": "${SKYQUALITY_BRIGHTNESS}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Sky brightness, mag/arcsec2 (day and night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_SQM": {
                    "name": "${SKYQUALITY_SQM}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "SQM, mag/arcsec2 (night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_NELM": {
                    "name": "${SKYQUALITY_NELM}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Naked-eye limiting magnitude (night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_BORTLE": {
                    "name": "${SKYQUALITY_BORTLE}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Bortle class (night)",
                    "type": "string"
                },
                "AS_SKYQUALITY_STARS": {
                    "name": "${SKYQUALITY_STARS}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Star count (night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_CLOUD": {
                    "name": "${SKYQUALITY_CLOUD}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Cloud cover, % (night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_AURORA": {
                    "name": "${SKYQUALITY_AURORA}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Aurora index (night)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_MOONALT": {
                    "name": "${SKYQUALITY_MOONALT}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Moon altitude, degrees",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_MOONILLUM": {
                    "name": "${SKYQUALITY_MOONILLUM}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Moon illumination, %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_SKYQUALITY_ADU": {
                    "name": "${SKYQUALITY_ADU}",
                    "format": "",
                    "sample": "",
                    "group": "Sky Quality",
                    "description": "Mean ADU in the measured area",
                    "type": "number"
                }
            }
        },
        "arguments": {
            "mask": "",
            "roi": "",
            "fov_div": "4",
            "offset": "17.0",
            "gain_scale": "200.0",
            "count_stars": "true",
            "history_hours": "48",
            "publish_web": "false",
            "debug": "false"
        },
        "argumentdetails": {
            "mask": {
                "required": "false",
                "description": "ROI Mask",
                "help": "Optional mask image (overlay images folder). White = measure here. Overrides ROI/FOV. Use a zenith-only mask for best results.",
                "type": {
                    "fieldtype": "image"
                }
            },
            "roi": {
                "required": "false",
                "description": "ROI (x1,y1,x2,y2)",
                "help": "Explicit rectangle to measure. Empty = central region from 'Central FOV'.",
                "type": {
                    "fieldtype": "text"
                }
            },
            "fov_div": {
                "required": "false",
                "description": "Central FOV Divisor",
                "help": "If no mask/ROI is set, measure a central box of this fraction (4 = central quarter, like indi-allsky)",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 20,
                    "step": 1
                }
            },
            "offset": {
                "required": "true",
                "description": "Magnitude Offset (calibrate!)",
                "help": "Additive calibration constant. Adjust until the reading matches a known SQM value for your camera/exposure.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 30,
                    "step": 0.1
                }
            },
            "gain_scale": {
                "required": "false",
                "description": "Gain Scale",
                "help": "Divisor exponent for gain normalisation: gain_factor = 10^(gain/scale). 200 suits ZWO 0.1dB gain units; gain 0 => factor 1.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 20,
                    "max": 1000,
                    "step": 10
                }
            },
            "count_stars": {
                "required": "false",
                "description": "Count Stars",
                "help": "At night, also count visible stars and estimate the cloud cover from where stars are missing (template matching, no sensor needed)",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "history_hours": {
                "required": "false",
                "description": "History (hours)",
                "help": "How much history to keep in skyquality.json",
                "tab": "Website",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 240,
                    "step": 1
                }
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to Website",
                "help": "Also write a rolling skyquality.json into the website folder (and upload it to the remote website if enabled), for your own website pages. The WebUI charts don't need this.",
                "tab": "Website",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "debug": {
                "required": "false",
                "description": "Enable debug images",
                "help": "Write the ROI image to the allsky tmp debug folder",
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
                    "changes": [
                        "Initial exposure/gain-normalised SQM in mag/arcsec2 + rolling json for charts",
                        "Star count (template matching), camera and CPU temperature",
                        "Cloud/haze index (star-deficit grid) and aurora candidate index (green excess on the north horizon)"
                    ]
                }
            ],
            "v0.2.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Record naked-eye limiting magnitude (NELM) derived from SQM",
                        "Record Moon altitude + illumination (ephem, falls back to Allsky overlay values) for moon-correlation charts"
                    ]
                }
            ],
            "v0.2.1": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Checkbox settings are parsed properly: they arrive as the string 'false', which Python treats as true, so debug and the other checkboxes were always on. Remote upload now reads useremotewebsite as the boolean it is",
                        "Aurora index: green must exceed red as well as blue. Moonlit or light-polluted cloud is red-dominant and was counted as aurora by the green-over-blue test"
                    ]
                }
            ],
            "v0.3.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Runs day and night: the sky brightness is measured around the clock, SQM, limiting magnitude, stars, cloud cover and aurora index at night",
                        "Values are saved in the Allsky database, and the module brings charts: sky brightness over 24 hours, SQM and limiting magnitude, stars and cloud cover, and an SQM gauge",
                        "Values are available in the Overlay Editor",
                        "Variables are now named AS_SKYQUALITY_*, so they don't clash with the allsky_sqm module's AS_SQM",
                        "Publishing skyquality.json to the website is now off by default, since the WebUI charts don't need it"
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
            result = f"Module Sky Quality Meter failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_maskCache = {"name": None, "mask": None}


def _truthy(v):
    """Checkbox args arrive from the flow config as the STRING 'true'/'false';
    'false' is truthy in Python, so parse booleans explicitly."""
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _bortle(mag):
    """Rough Bortle class / description from mag/arcsec2 (indicative only)."""
    table = [
        (21.9, "1 – excellent dark sky"),
        (21.7, "2 – typical dark sky"),
        (21.5, "3 – rural sky"),
        (20.4, "4 – rural/suburban"),
        (19.1, "5 – suburban"),
        (18.0, "6 – bright suburban"),
        (17.0, "7 – suburban/urban"),
        (-99, "8-9 – city sky"),
    ]
    for lim, desc in table:
        if mag >= lim:
            return desc
    return "unknown"


def _roiMask(params, shape):
    """Return a uint8 mask for the region to measure."""
    maskName = params["mask"].strip()
    roi = params["roi"].strip()
    if maskName:
        if _maskCache["name"] == maskName and _maskCache["mask"] is not None \
                and _maskCache["mask"].shape == shape:
            return _maskCache["mask"]
        p = os.path.join(s.ALLSKY_OVERLAY, "images", maskName)
        m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if m is not None:
            if m.shape != shape:
                m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
            _maskCache.update(name=maskName, mask=m)
            return m
    h, w = shape
    m = np.zeros(shape, np.uint8)
    if roi:
        try:
            x1, y1, x2, y2 = [s.int(v) for v in roi.split(",")]
            cv2.rectangle(m, (x1, y1), (x2, y2), 255, -1)
            return m
        except Exception:
            s.log(1, "WARNING: skyquality ROI invalid, using central FOV")
    div = max(2, s.int(params["fov_div"]))
    cx, cy = w // 2, h // 2
    bw, bh = w // div, h // div
    cv2.rectangle(m, (cx - bw, cy - bh), (cx + bw, cy + bh), 255, -1)
    return m


def _websiteDataDir():
    # website root — the standard Allsky website folder that already exists on the
    # remote (no sub-directory to create); skyquality.json sits next to skyquality.html
    website = s.getEnvironmentVariable("ALLSKY_WEBSITE")
    if not website:
        website = os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"),
                               "html", "allsky")
    return website


def _uploadRemote(local, fname):
    """Upload skyquality.json to the remote website root. Never raises."""
    try:
        if str(s.getSetting("useremotewebsite")).lower() not in ("true", "1", "yes", "on"):
            return
        scripts = s.getEnvironmentVariable("ALLSKY_SCRIPTS") or \
            os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "scripts")
        uploader = os.path.join(scripts, "upload.sh")
        if not os.path.isfile(uploader) or not os.path.isfile(local):
            return
        rdir = (s.getSetting("remotewebsiteimagedir") or "").rstrip("/")
        subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", local, rdir, fname, "SkyQuality"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        s.log(1, f"WARNING: skyquality remote upload failed: {ex}")


def _appendHistory(record, hours):
    """Add the record to the rolling skyquality.json in tmp and publish a copy to
    the website folder (and the remote website, if enabled)."""
    path = os.path.join(s.ALLSKY_TMP, "skyquality.json")
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
    except Exception as ex:
        s.log(1, f"WARNING: skyquality could not write history: {ex}")
        return
    try:
        ddir = _websiteDataDir()
        os.makedirs(ddir, exist_ok=True)
        webpath = os.path.join(ddir, "skyquality.json")
        with open(webpath, "w") as f:
            json.dump(data, f)
        _uploadRemote(webpath, "skyquality.json")
    except Exception as ex:
        s.log(1, f"WARNING: skyquality could not publish to website: {ex}")


_starTemplate = None


def _starPoints(gray, mask, thr=0.65):
    """Template-match star-like points (indi-allsky method). Returns list of (x, y)."""
    global _starTemplate
    if _starTemplate is None:
        t = np.zeros((15, 15), np.uint8)
        cv2.circle(t, (7, 7), 3, 255, cv2.FILLED)
        _starTemplate = cv2.blur(t, (2, 2))
    img = cv2.bitwise_and(gray, gray, mask=mask) if mask is not None else gray
    try:
        res = cv2.matchTemplate(img, _starTemplate, cv2.TM_CCOEFF_NORMED)
    except Exception:
        return []
    ys, xs = np.where(res >= thr)
    return list(zip(xs.tolist(), ys.tolist()))


def _countStars(points):
    """Star count with 10px grid dedup."""
    seen = set()
    for x, y in points:
        seen.add((x // 10, y // 10))
    return len(seen)


def _cloudPct(mask, points, cell=48):
    """Cloud/haze index: fraction of the sky (coarse grid) that has NO stars.
    Clear sky is dotted with stars everywhere; cloud/overcast blanks them out."""
    h, w = mask.shape
    gw, gh = max(1, w // cell), max(1, h // cell)
    maskC = cv2.resize(mask, (gw, gh), interpolation=cv2.INTER_AREA)
    sky_cells = maskC > 127
    total = int(sky_cells.sum())
    if total == 0:
        return None
    star_grid = np.zeros((gh, gw), bool)
    for x, y in points:
        gx, gy = min(gw - 1, x * gw // w), min(gh - 1, y * gh // h)
        star_grid[gy, gx] = True
    clear_cells = int((sky_cells & star_grid).sum())
    return round(100.0 * (1.0 - clear_cells / total), 1)


def _auroraIndex(bgr, mask):
    """Green-excess glow low on the NORTH horizon (image is North-up). Aurora is green
    (O I 557.7 nm); this is a candidate index, not a certainty.

    Green must be above BOTH red and blue (min of the two excesses): moonlit or
    light-polluted cloud is RED-dominant (green far below red), so requiring green
    over red as well rejects the warm cloud that a green-over-blue-only test flags
    as false aurora. See the dedicated allsky_aurora module for detection."""
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return 0.0
    y0, y1 = int(ys.min()), int(ys.max())
    band = mask.copy()
    band[y0 + int(0.20 * (y1 - y0)):, :] = 0        # keep only the top (north) 20%
    if int((band > 0).sum()) < 50:
        return 0.0
    b, g, r = cv2.split(bgr.astype(np.int16))
    green_excess = np.minimum(g - r, g - b)[band > 0]   # green over red AND blue
    return round(max(0.0, float(green_excess.mean())), 1)


def _limitingMag(sqm):
    """Naked-eye limiting magnitude (NELM) from zenithal SQM, using the standard
    Schaefer relation (as used by Unihedron):
        NELM = 7.93 − 5·log10(10^(4.316 − SQM/5) + 1)
    A pure function of SQM — no field-of-view calibration needed."""
    try:
        return round(7.93 - 5.0 * math.log10(10.0 ** (4.316 - sqm / 5.0) + 1.0), 2)
    except Exception:
        return None


def _moon():
    """(altitude_deg, illumination_pct) of the Moon when the image was taken.
    Prefers Allsky's overlay values if present, otherwise computes them with
    ephem from the configured lat/lon.  Returns (None, None) if neither is
    available."""
    alt_s = s.get_environment_variable("AS_MOON_ELEVATION")
    ill_s = s.get_environment_variable("AS_MOON_ILLUMINATION")
    if alt_s not in (None, "") and ill_s not in (None, ""):
        try:
            return round(float(alt_s), 1), round(float(ill_s), 0)
        except (TypeError, ValueError):
            pass
    try:
        import ephem
        from datetime import datetime, timezone
        obs = ephem.Observer()
        obs.lat = str(s.convertLatLon(s.getSetting("latitude")))
        obs.lon = str(s.convertLatLon(s.getSetting("longitude")))
        taken = s.get_environment_variable("AS_TIMESTAMP")
        when = datetime.fromtimestamp(int(taken), timezone.utc) if taken else datetime.now(timezone.utc)
        obs.date = ephem.Date(when.replace(tzinfo=None))
        m = ephem.Moon(obs)
        return round(math.degrees(float(m.alt)), 1), round(float(m.phase), 0)
    except Exception:
        return None, None


def _measure(module):
    if s.image is None:
        return "No image available"

    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    # The flow runner passes the event "postcapture"; day or night is in DAY_OR_NIGHT.
    night = str(s.get_environment_variable("DAY_OR_NIGHT") or "").upper() == "NIGHT"
    offset = s.asfloat(params["offset"])
    gain_scale = s.asfloat(params["gain_scale"])
    debug = _truthy(params["debug"])

    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if len(s.image.shape) == 3 else s.image
    mask = _roiMask(params, gray.shape[:2])
    if debug:
        s.startModuleDebug(module.meta_data["module"])
        s.writeDebugImage(module.meta_data["module"], "sqm-roi.png",
                          cv2.bitwise_and(gray, gray, mask=mask))

    mean_adu = float(cv2.mean(gray, mask=mask)[0])

    # exposure (us -> s) and gain from the capture environment
    exp_us = s.asfloat(s.get_environment_variable("AS_EXPOSURE_US"))
    exposure_s = (exp_us / 1e6) if exp_us and exp_us > 0 else 1.0
    gain = s.asfloat(s.get_environment_variable("AS_GAIN")) or 0.0
    gain_factor = 10.0 ** (gain / gain_scale) if gain_scale > 0 else 1.0

    signal = mean_adu / exposure_s / gain_factor
    if signal <= 0:
        return "Signal is zero, cannot compute the sky brightness"
    brightness = offset - 2.5 * math.log10(signal)
    moon_alt, moon_ill = _moon()

    values = {
        "AS_SKYQUALITY_BRIGHTNESS": round(brightness, 2),
        "AS_SKYQUALITY_ADU": round(mean_adu, 1),
    }
    if moon_alt is not None:
        values["AS_SKYQUALITY_MOONALT"] = moon_alt
        values["AS_SKYQUALITY_MOONILLUM"] = moon_ill

    # SQM and everything based on stars only make sense at night.
    stars = cloud = aurora = nelm = None
    if night:
        nelm = _limitingMag(brightness)
        values["AS_SKYQUALITY_SQM"] = round(brightness, 2)
        values["AS_SKYQUALITY_BORTLE"] = _bortle(brightness)
        if nelm is not None:
            values["AS_SKYQUALITY_NELM"] = nelm
        if _truthy(params["count_stars"]):
            stars = _countStars(_starPoints(gray, mask, 0.65))
            cloud = _cloudPct(mask, _starPoints(gray, mask, 0.55), cell=80)
            values["AS_SKYQUALITY_STARS"] = stars
            if cloud is not None:
                values["AS_SKYQUALITY_CLOUD"] = cloud
        if len(s.image.shape) == 3:
            aurora = _auroraIndex(s.image, mask)
            values["AS_SKYQUALITY_AURORA"] = aurora

    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)

    if _truthy(params["publish_web"]):
        def _flt(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        temp = _flt(s.get_environment_variable("AS_TEMPERATURE_C"))
        cpu = _flt(s.get_environment_variable("AS_CPUTEMP_C"))
        rec = {
            "t": int(time.time()),
            "brightness": round(brightness, 2),
            "adu": round(mean_adu, 1),
            "exp": round(exposure_s, 3),
            "gain": round(gain, 1),
        }
        if night:
            rec["sqm"] = round(brightness, 2)
        for k, v in (("mlim", nelm), ("stars", stars), ("cloud", cloud), ("aurora", aurora),
                     ("moon_alt", moon_alt), ("moon_ill", moon_ill),
                     ("temp", None if temp is None else round(temp, 1)),
                     ("cpu", None if cpu is None else round(cpu, 1))):
            if v is not None:
                rec[k] = v
        _appendHistory(rec, s.int(params["history_hours"]))

    if night:
        extra = (f", {stars} stars" if stars is not None else "") + \
                (f", {cloud}% cloud" if cloud is not None else "")
        result = f"SQM {brightness:.2f} mag/arcsec2 (ADU {mean_adu:.1f}, exp {exposure_s:.2f}s){extra} — Bortle {_bortle(brightness)}"
    else:
        result = f"Sky brightness {brightness:.2f} mag/arcsec2 (ADU {mean_adu:.1f}, exp {exposure_s:.4f}s)"
    module.log(4, f"INFO: {result}")
    return result


def skyquality(params, event):
    return ALLSKYSKYQUALITY(params, event).run()


def skyquality_cleanup():
    moduleData = {
        "metaData": ALLSKYSKYQUALITY.meta_data,
        "cleanup": {
            "files": {
                ALLSKYSKYQUALITY.meta_data["extradatafilename"],
                os.path.join(s.ALLSKY_TMP, "skyquality.json")
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
