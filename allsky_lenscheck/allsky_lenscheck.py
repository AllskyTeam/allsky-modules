""" allsky_lenscheck.py

Is the lens (or dome) still sharp?  For Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)

A camera that is looked after from far away can go blind without anyone
noticing: dew or frost on the dome, a lens that has slipped out of focus.  The
stars then grow into soft discs.  This module measures how wide the stars are
on every clear night image and compares it with what is normal for this camera
at this exposure time.

How
    The bright catalogue stars (Hipparcos, V < 4) are projected into the image
    with the fisheye calibration.  For each one that is seen and not saturated,
    the width of its image at half its height is measured (the narrower axis,
    so that a star trailed by a long exposure still counts).  The median is
    the star width (FWHM) of the image.  The normal width is learnt on clear
    images, separately for each exposure time (a 2 s and a 60 s image look
    different after processing).

    A width 1.3 times the normal width is "soft", 1.6 times "blurred".  If the
    Dew Heater module (or a temperature/humidity module) reports that the dome
    is close to the dew point, a blurred image is reported as dew.
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


class ALLSKYLENSCHECK(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Lens Check",
        "description": "Measures how sharp the stars are and warns of dew, frost or a lens out of focus",
        "version": "v0.1.0",
        "module": "allsky_lenscheck",
        "events": [
            "night"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_lenscheck.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_lenscheck",
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
                "AS_LENSCHECK_FWHM": {
                    "name": "${LENSCHECK_FWHM}",
                    "format": "",
                    "sample": "",
                    "group": "Lens Check",
                    "description": "Star width (FWHM) in pixels",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_LENSCHECK_RATIO": {
                    "name": "${LENSCHECK_RATIO}",
                    "format": "",
                    "sample": "",
                    "group": "Lens Check",
                    "description": "Star width compared with the normal width (1.0 = normal)",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_LENSCHECK_STATE": {
                    "name": "${LENSCHECK_STATE}",
                    "format": "",
                    "sample": "",
                    "group": "Lens Check",
                    "description": "sharp, soft, blurred, dew or learning",
                    "type": "string"
                },
                "AS_LENSCHECK_DEW": {
                    "name": "${LENSCHECK_DEW}",
                    "format": "",
                    "sample": "",
                    "group": "Lens Check",
                    "description": "1 when the stars are blurred and the dome is near the dew point, else 0",
                    "type": "bool",
                    "database": {
                        "include": "true"
                    }
                }
            }
        },
        "arguments": {
            "calibration": "calibration.json",
            "soft_ratio": "1.3",
            "blurred_ratio": "1.6",
            "dew_margin": "3",
            "notify_url": "",
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
            "soft_ratio": {
                "required": "false",
                "description": "Soft from",
                "help": "Star width compared with the normal width from which the image is 'soft'. Over nine clear nights here, single images varied up to 1.2 times the normal width.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1.1,
                    "max": 3,
                    "step": 0.05
                }
            },
            "blurred_ratio": {
                "required": "false",
                "description": "Blurred from",
                "help": "From this ratio, on two images in a row, the image is 'blurred' and a notification is sent.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1.2,
                    "max": 4,
                    "step": 0.05
                }
            },
            "dew_margin": {
                "required": "false",
                "description": "Dew margin (°C)",
                "help": "If the temperature is less than this above the dew point (from the Dew Heater module, or AS_TEMP and AS_DEW), a blurred image is reported as dew.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 10,
                    "step": 0.5
                }
            },
            "notify_url": {
                "required": "false",
                "description": "Notify URL",
                "help": "Optional. When the image becomes blurred, a short text is sent to this URL with an HTTP POST (e.g. https://ntfy.sh/your-topic), at most once a night.",
                "tab": "Settings",
                "type": {
                    "fieldtype": "text"
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
                        "Star width (FWHM) of the bright catalogue stars on every clear night image, compared with the normal width learnt per exposure time",
                        "Soft / blurred / dew state, a dew flag other modules can use, optional notification",
                        "Values are saved in the Allsky database; the module brings a chart"
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
            result = f"Module Lens Check failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIRS = (os.path.join(_MODULE_DIR, "moduledata", "data", "allsky_lenscheck"),
              os.path.join(_MODULE_DIR, "allsky_lenscheck"), _MODULE_DIR)
MAG_LIMIT = 4.0
MIN_ALT = 25.0
HW = 10                     # half window for measuring a star (px, 4K image)
CLEAR_MIN = 0.6             # share of the bright stars seen for a usable image
MIN_STARS = 8
BASE_FRAMES = 200           # clear images the normal width is learnt from, per exposure bin
BASE_MIN = 20               # images needed before the width is judged


def _truthy(v):
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _dataFile(name):
    for d in _DATA_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return os.path.join(_DATA_DIRS[-1], name)


def _stateFile():
    folder = os.path.join(os.environ.get("ALLSKY_MYFILES_DIR") or _MODULE_DIR, "lenscheck")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "lenscheck_state.json")


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


def _env(name):
    try:
        return s.get_environment_variable(name)
    except Exception:
        return None


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


def _stars(calib, t):
    with open(_dataFile("stars.json")) as fh:
        cat = np.array(json.load(fh)["stars"], dtype=np.float64)
    cat = cat[cat[:, 2] < MAG_LIMIT]
    d = t / 86400.0 + 2440587.5 - 2451545.0
    lst = (280.46061837 + 360.98564736629 * d + calib["lon"]) % 360.0
    ra, dec, lat = np.radians(cat[:, 0]), np.radians(cat[:, 1]), math.radians(calib["lat"])
    ha = math.radians(lst) - ra
    alt = np.degrees(np.arcsin(np.sin(dec) * math.sin(lat) + np.cos(dec) * math.cos(lat) * np.cos(ha)))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * math.sin(lat) - np.tan(dec) * math.cos(lat))) + 180) % 360
    up = alt > MIN_ALT
    tt = (90.0 - alt[up]) / 90.0
    r = calib["a1"] * tt + calib["a3"] * tt ** 3
    a = np.radians(calib["rot_deg"] + calib["flip"] * az[up])
    return calib["cx"] + r * np.sin(a), calib["cy"] - r * np.cos(a)


def _measure(gray, x, y):
    """Share of the stars seen, and the median narrow-axis FWHM of the seen,
    unsaturated ones (None with too few)."""
    h, w = gray.shape
    hw = max(5, int(round(HW * w / 3840.0)))
    ok = (x > hw + 5) & (x < w - hw - 5) & (y > hw + 5) & (y < h - hw - 5)
    x, y = np.rint(x[ok]).astype(int), np.rint(y[ok]).astype(int)
    hp = gray.astype(np.float32) - cv2.medianBlur(gray, 31).astype(np.float32)
    noise = 1.4826 * float(np.median(np.abs(hp - np.median(hp)))) + 1e-3
    seen, widths = 0, []
    for xi, yi in zip(x, y):
        win = hp[yi - 4:yi + 5, xi - 4:xi + 5]
        if win.max() < 8 * noise:
            continue
        seen += 1
        dy, dx = np.unravel_index(np.argmax(win), win.shape)
        cx, cy = xi - 4 + dx, yi - 4 + dy
        if gray[cy, cx] >= 250:
            continue                              # saturated: its width says nothing
        p = hp[cy - hw:cy + hw + 1, cx - hw:cx + hw + 1]
        _n, lab = cv2.connectedComponents((p >= 0.5 * p[hw, hw]).astype(np.uint8))
        blob = lab == lab[hw, hw]
        if blob[0].any() or blob[-1].any() or blob[:, 0].any() or blob[:, -1].any():
            continue                              # runs into a neighbour or the window edge
        yy, xx = np.nonzero(blob)
        if len(xx) < 4:
            continue
        ev = np.linalg.eigvalsh(np.cov(np.stack([xx, yy]).astype(float)) + np.eye(2) / 12.0)
        widths.append(4.0 * math.sqrt(ev[0]))     # a uniform disc of diameter D: variance D^2/16
    frac = seen / float(max(1, len(x)))
    return frac, (float(np.median(widths)) if len(widths) >= MIN_STARS else None), len(widths)


def _expBin(exp_s):
    """Exposure time bin: 1 s, 2 s, 4 s, ... (processing differs by exposure)."""
    return str(int(round(math.log2(max(0.001, exp_s)))))


def _dewMargin():
    """Temperature minus dew point in °C, from the Dew Heater module or
    AS_TEMP / AS_DEW, else None."""
    for fname, key in (("allsky_dew.json", "AS_DEWCONTROLMARGIN"),):
        try:
            d = s.load_extra_data_file(fname)
            if d and key in d:
                v = d[key]
                return float(v.get("value") if isinstance(v, dict) else v)
        except Exception:
            pass
    try:
        t, dp = s.get_allsky_variable("AS_TEMP"), s.get_allsky_variable("AS_DEW")
        if t not in (None, "") and dp not in (None, ""):
            return float(t) - float(dp)
    except Exception:
        pass
    return None


def _run(module):
    if s.image is None:
        return "No image available"
    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    calib = _loadCalib(params["calibration"].strip(), s.image.shape)
    if calib is None:
        return "Lens Check needs a fisheye calibration (calibration.json, see the README)"
    try:
        t0 = int(_env("AS_TIMESTAMP"))
    except (TypeError, ValueError):
        t0 = int(time.time())
    try:
        exp = int(_env("AS_EXPOSURE_US")) / 1e6
    except (TypeError, ValueError):
        exp = 1.0

    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if s.image.ndim == 3 else s.image
    x, y = _stars(calib, t0)
    frac, fwhm, n = _measure(gray, x, y)
    if frac < CLEAR_MIN or fwhm is None:
        return f"Lens Check: not clear enough to judge ({100 * frac:.0f}% of the bright stars seen)"

    path = _stateFile()
    st = _load(path, {})
    base = st.setdefault("base", {})
    hist = base.setdefault(_expBin(exp), [])
    normal = float(np.median(hist)) if len(hist) >= BASE_MIN else None
    ratio = fwhm / normal if normal else None

    soft, blurred = s.asfloat(params["soft_ratio"]), s.asfloat(params["blurred_ratio"])
    recent = st.setdefault("recent", [])
    recent.append(round(ratio, 3) if ratio else None)
    del recent[:-3]
    if ratio is None:
        state = "learning"
    elif ratio >= blurred and len(recent) >= 2 and recent[-2] is not None and recent[-2] >= blurred:
        state = "blurred"
    elif ratio >= soft:
        state = "soft"
    else:
        state = "sharp"
    # only sharp-looking images teach the normal width, so a slow fogging can't creep in
    if ratio is None or ratio < soft:
        hist.append(round(fwhm, 3))
        del hist[:-BASE_FRAMES]

    margin = _dewMargin()
    dew = state == "blurred" and margin is not None and margin < s.asfloat(params["dew_margin"])
    if dew:
        state = "dew"
    url = params["notify_url"].strip()
    night = time.strftime("%Y%m%d", time.localtime(t0 - 12 * 3600))
    if url and state in ("blurred", "dew") and st.get("notified") != night:
        st["notified"] = night
        text = (f"Allsky: the stars are {ratio:.1f} times wider than normal"
                + (f" and the dome is {margin:.1f} °C above the dew point - dew?" if dew else " - dew, frost or focus?"))
        try:
            import requests
            requests.post(url, data=text.encode("utf-8"), timeout=8)
        except Exception as ex:
            module.log(1, f"WARNING: Lens Check could not send the notification: {ex}")
    _save(path, st)

    values = {"AS_LENSCHECK_FWHM": round(fwhm, 2), "AS_LENSCHECK_STATE": state, "AS_LENSCHECK_DEW": 1 if dew else 0}
    if ratio is not None:
        values["AS_LENSCHECK_RATIO"] = round(ratio, 2)
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)
    result = (f"Lens Check: {state}, star width {fwhm:.2f} px"
              + (f" = {ratio:.2f} x normal" if ratio else f" (learning, {len(hist)}/{BASE_MIN} images)")
              + f", {n} stars measured")
    module.log(4 if state in ("sharp", "learning") else 1, f"INFO: {result}")
    return result


def lenscheck(params, event):
    return ALLSKYLENSCHECK(params, event).run()


def lenscheck_cleanup():
    moduleData = {
        "metaData": ALLSKYLENSCHECK.meta_data,
        "cleanup": {
            "files": {
                ALLSKYLENSCHECK.meta_data["extradatafilename"]
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
