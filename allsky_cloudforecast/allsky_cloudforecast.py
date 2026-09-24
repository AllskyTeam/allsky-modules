""" allsky_cloudforecast.py

Clear-sky / cloud nowcast module for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)
Home / docs: https://github.com/benhartwich/allsky-cloudforecast

Estimates cloud cover from the all-sky image DAY and NIGHT, and turns the recent
trend into a short-term nowcast ("clearing", "clouding over", "stable").

Two complementary measurements, chosen automatically by day or night:

  * Day   - Red/Blue Ratio (RBR): clear sky is blue (low R/B), cloud is white/grey
            (R~=B, high R/B). The standard method used by sky-imager meteorology.
  * Night - star deficit: a clear sky is dotted with stars everywhere; cloud blanks
            them out (template-matched star count on a coarse grid).

The values are saved in the Allsky database for the charts the module brings
along.  The nowcast is a persistence/trend extrapolation of the last ~45 min,
optionally refined by the cloud motion between frames (optical flow) - good for
~30-60 min, not a weather forecast.

Uses only cv2 + numpy (already in the Allsky venv).
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import json
import time
import math
import subprocess
import cv2
import numpy as np


class ALLSKYCLOUDFORECAST(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Cloud Forecast",
        "description": "Cloud cover from the image day and night (red/blue ratio by day, missing stars at night), with a short-term nowcast and charts",
        "version": "v0.3.0",
        "module": "allsky_cloudforecast",
        "events": [
            "day",
            "night"
        ],
        "experimental": "false",
        "centersettings": "false",
        "testable": "false",
        "group": "Image Analysis",
        "extradatafilename": "allsky_cloudforecast.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_cloudforecast",
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
                "AS_CLOUDFORECAST_COVER": {
                    "name": "${CLOUDFORECAST_COVER}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Cloud cover, %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_CLOUDFORECAST_CLEAR": {
                    "name": "${CLOUDFORECAST_CLEAR}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Clear sky, 1 = clear, 0 = not clear",
                    "type": "bool",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_CLOUDFORECAST_STATE": {
                    "name": "${CLOUDFORECAST_STATE}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Sky state: clear, partly cloudy or overcast",
                    "type": "string",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_CLOUDFORECAST_PRED30": {
                    "name": "${CLOUDFORECAST_PRED30}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Cloud cover expected in 30 minutes, %",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_CLOUDFORECAST_TREND": {
                    "name": "${CLOUDFORECAST_TREND}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Trend: clearing, clouding over or stable",
                    "type": "string",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_CLOUDFORECAST_NOWCAST": {
                    "name": "${CLOUDFORECAST_NOWCAST}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Nowcast, e.g. 'clouding over, overcast in ~20 min'",
                    "type": "string"
                },
                "AS_CLOUDFORECAST_METHOD": {
                    "name": "${CLOUDFORECAST_METHOD}",
                    "format": "",
                    "sample": "",
                    "group": "Cloud Forecast",
                    "description": "Method: rbr (day) or stars (night)",
                    "type": "string"
                }
            }
        },
        "arguments": {
            "mask": "",
            "rbr_thr": "0.88",
            "clear_pct": "20",
            "overcast_pct": "65",
            "trend_min": "45",
            "motion_nowcast": "true",
            "flow_downscale": "4",
            "history_hours": "48",
            "publish_web": "false",
            "debug": "false"
        },
        "argumentdetails": {
            "mask": {
                "required": "false",
                "description": "Sky Mask",
                "help": "Mask image (overlay images folder). White = sky to analyse, black = ignore (trees, buildings, horizon). Without a mask the whole image is used.",
                "type": {
                    "fieldtype": "image"
                }
            },
            "rbr_thr": {
                "required": "false",
                "description": "Daytime R/B Cloud Threshold",
                "help": "A sky pixel counts as cloud (daytime) when Red/Blue exceeds this. Clear sky ~0.5-0.6, cloud >0.85.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.6,
                    "max": 1.3,
                    "step": 0.01
                }
            },
            "clear_pct": {
                "required": "false",
                "description": "Clear Below (%)",
                "help": "Cloud cover below this counts as a clear sky",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 50,
                    "step": 1
                }
            },
            "overcast_pct": {
                "required": "false",
                "description": "Overcast Above (%)",
                "help": "Cloud cover above this counts as overcast",
                "type": {
                    "fieldtype": "spinner",
                    "min": 40,
                    "max": 95,
                    "step": 1
                }
            },
            "trend_min": {
                "required": "false",
                "description": "Nowcast Window (min)",
                "help": "How many minutes of recent history the trend/nowcast is fitted over",
                "type": {
                    "fieldtype": "spinner",
                    "min": 15,
                    "max": 180,
                    "step": 5
                }
            },
            "motion_nowcast": {
                "required": "false",
                "description": "Cloud-Motion Nowcast",
                "help": "Track cloud motion between frames (optical flow) and advect it over the zenith — a directional nowcast (“clouds from the SW, zenith clouding over in ~15 min”). Most reliable by day. Falls back to the trend nowcast when motion is unclear.",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "flow_downscale": {
                "required": "false",
                "description": "Optical-Flow Downscale",
                "help": "Downscale factor for the optical-flow computation (higher = faster, coarser). 4 = quarter resolution.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 2,
                    "max": 8,
                    "step": 1
                }
            },
            "history_hours": {
                "required": "false",
                "description": "History (hours)",
                "help": "How much history cloud.json keeps (the nowcast uses the last few minutes of it)",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 240,
                    "step": 1
                },
                "tab": "Website"
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to Website",
                "help": "Also write cloud.json into the website folder (and upload it to the remote website if enabled), for your own website pages. The WebUI charts don't need this.",
                "type": {
                    "fieldtype": "checkbox"
                },
                "tab": "Website"
            },
            "debug": {
                "required": "false",
                "description": "Enable debug images",
                "help": "Write the cloud-mask image to the allsky tmp debug folder",
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
                    "authorurl": "https://github.com/benhartwich",
                    "changes": "Initial day (RBR) + night (star deficit) cloud cover with a trend-based clear-sky nowcast and dashboard json"
                }
            ],
            "v0.2.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://github.com/benhartwich",
                    "changes": [
                        "Cloud-motion nowcast: dense optical flow between frames estimates cloud drift; the cloud field is advected over the zenith (upwind sampling) to predict clouding-over / clearing with a time estimate",
                        "Motion direction is reported as a compass bearing via the fisheye calibration when available"
                    ]
                }
            ],
            "v0.2.1": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://github.com/benhartwich",
                    "changes": "Use s.TOD (not the postprocess event, which is 'postcapture') to pick the day/night method — fixes the RBR/star-deficit choice"
                }
            ],
            "v0.3.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://github.com/benhartwich",
                    "changes": [
                        "Class-based module for Allsky v2025",
                        "Values are saved in the Allsky database, day and night, and the module brings charts: cloud cover with the 30-minute forecast, a clear/not clear indicator and a cloud cover gauge",
                        "Values are available in the Overlay Editor, named AS_CLOUDFORECAST_*",
                        "No mask by default; publishing cloud.json to the website is off by default, since the WebUI charts don't need it"
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
            result = f"Module Cloud Forecast failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


_maskCache = {"name": None, "mask": None}
_starTemplate = None
_calibCache = {"done": False, "zen": None}
PREV_FLOW = os.path.join(s.ALLSKY_TMP, "allsky_cloudforecast_prev.png")
PREV_META = os.path.join(s.ALLSKY_TMP, "allsky_cloudforecast_prevmeta.json")
HISTORY = os.path.join(s.ALLSKY_TMP, "cloud.json")
_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _imageTime():
    """When the image was taken (AS_TIMESTAMP), else now."""
    taken = s.get_environment_variable("AS_TIMESTAMP")
    try:
        return int(taken)
    except (TypeError, ValueError):
        return int(time.time())


def _compass(az):
    return _COMPASS[int((az % 360) / 22.5 + 0.5) % 16]


def _truthy(v):
    """Checkbox args arrive from the flow config as the STRING 'true'/'false';
    'false' is truthy in Python, so parse booleans explicitly."""
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _mask(name, shape):
    name = (name or "").strip()
    if not name:
        return np.full(shape, 255, np.uint8)
    if _maskCache["name"] == name and _maskCache["mask"] is not None \
            and _maskCache["mask"].shape == shape:
        return _maskCache["mask"]
    p = os.path.join(s.ALLSKY_OVERLAY, "images", name)
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if m is None:
        m = np.full(shape, 255, np.uint8)
    elif m.shape != shape:
        m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    _maskCache.update(name=name, mask=m)
    return m


def _cloudDay(bgr, mask, rbr_thr):
    """Daytime cloud fraction via Red/Blue ratio. Overexposed (sun) pixels excluded."""
    b, g, r = cv2.split(bgr.astype(np.float32))
    rbr = r / (b + 1.0)
    sat = (r > 250) & (g > 250) & (b > 250)          # sun / blown highlights
    sky = (mask > 127) & ~sat
    n = int(sky.sum())
    if n < 1000:
        return None, None
    cloud = (rbr > rbr_thr) & sky
    frac = round(100.0 * int(cloud.sum()) / n, 1)
    return frac, (cloud.astype(np.uint8) * 255)


def _starPoints(gray, mask, thr=0.55):
    global _starTemplate
    if _starTemplate is None:
        t = np.zeros((15, 15), np.uint8)
        cv2.circle(t, (7, 7), 3, 255, cv2.FILLED)
        _starTemplate = cv2.blur(t, (2, 2))
    img = cv2.bitwise_and(gray, gray, mask=mask)
    try:
        res = cv2.matchTemplate(img, _starTemplate, cv2.TM_CCOEFF_NORMED)
    except Exception:
        return []
    ys, xs = np.where(res >= thr)
    return list(zip(xs.tolist(), ys.tolist()))


def _cloudNight(gray, mask, cell=80):
    """Night cloud fraction = share of the sky grid with no detected stars."""
    pts = _starPoints(gray, mask)
    h, w = mask.shape
    gw, gh = max(1, w // cell), max(1, h // cell)
    maskC = cv2.resize(mask, (gw, gh), interpolation=cv2.INTER_AREA)
    sky_cells = maskC > 127
    total = int(sky_cells.sum())
    if total == 0:
        return None
    star_grid = np.zeros((gh, gw), bool)
    for x, y in pts:
        star_grid[min(gh - 1, y * gh // h), min(gw - 1, x * gw // w)] = True
    clear = int((sky_cells & star_grid).sum())
    return round(100.0 * (1.0 - clear / total), 1)


def _state(cloud, clear_pct, overcast_pct):
    if cloud is None:
        return "unknown"
    if cloud < clear_pct:
        return "clear"
    if cloud > overcast_pct:
        return "overcast"
    return "partly cloudy"


def _nowcast(history, now_t, now_cloud, trend_min, clear_pct, overcast_pct, method):
    """Linear trend over the last trend_min minutes -> (trend, predicted_30, text).
    Only same-method points are used so the day<->night method switch does not create
    a spurious jump, and a minimum time span is required to avoid a degenerate slope."""
    cutoff = now_t - trend_min * 60
    pts = [(d["t"], d["cloud"]) for d in history
           if d.get("t", 0) >= cutoff and d.get("cloud") is not None
           and d.get("method") == method]
    pts.append((now_t, now_cloud))
    span_min = (now_t - min(t for t, _ in pts)) / 60.0
    if len(pts) < 3 or span_min < max(10.0, trend_min * 0.3):
        return "unknown", None, "building history"
    tm = np.array([(t - now_t) / 60.0 for t, _ in pts])     # minutes, <=0
    cl = np.array([c for _, c in pts], float)
    slope = float(np.polyfit(tm, cl, 1)[0])                  # %/min
    pred = float(np.clip(now_cloud + slope * 30.0, 0, 100))
    if slope < -0.4:
        trend = "clearing"
    elif slope > 0.4:
        trend = "clouding over"
    else:
        trend = "stable"
    # short verbal nowcast
    if trend == "clearing" and now_cloud >= clear_pct:
        mins = (now_cloud - clear_pct) / max(1e-3, -slope)
        text = f"clearing — likely clear within ~{int(round(mins/5)*5)} min" if mins < 180 else "slowly clearing"
    elif trend == "clouding over" and now_cloud <= overcast_pct:
        mins = (overcast_pct - now_cloud) / max(1e-3, slope)
        text = f"clouding over — overcast in ~{int(round(mins/5)*5)} min" if mins < 180 else "slowly clouding over"
    else:
        text = f"{_state(now_cloud, clear_pct, overcast_pct)}, {trend}"
    return trend, round(pred, 1), text


def _websiteDir():
    website = s.getEnvironmentVariable("ALLSKY_WEBSITE")
    if not website:
        website = os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"),
                               "html", "allsky")
    return website


def _uploadRemote(local, fname):
    try:
        if str(s.getSetting("useremotewebsite")).lower() not in ("true", "1", "yes", "on"):
            return
        scripts = s.getEnvironmentVariable("ALLSKY_SCRIPTS") or \
            os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "scripts")
        uploader = os.path.join(scripts, "upload.sh")
        if not os.path.isfile(uploader) or not os.path.isfile(local):
            return
        rdir = (s.getSetting("remotewebsiteimagedir") or "").rstrip("/")
        subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", local, rdir, fname, "CloudForecast"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        s.log(1, f"WARNING: cloudforecast remote upload failed: {ex}")


def _loadHistory():
    try:
        with open(HISTORY) as f:
            return json.load(f)
    except Exception:
        return []


def _appendHistory(record, hours, publish_web):
    """Add the record to the rolling cloud.json in tmp, which the trend nowcast
    uses, and optionally publish a copy to the website (and the remote website)."""
    data = _loadHistory()
    data.append(record)
    cutoff = record["t"] - hours * 3600
    data = [d for d in data if d.get("t", 0) >= cutoff][-6000:]
    try:
        with open(HISTORY, "w") as f:
            json.dump(data, f)
    except Exception as ex:
        s.log(1, f"WARNING: cloudforecast could not write history: {ex}")
        return data
    if publish_web:
        try:
            ddir = _websiteDir()
            os.makedirs(ddir, exist_ok=True)
            webpath = os.path.join(ddir, "cloud.json")
            with open(webpath, "w") as f:
                json.dump(data, f)
            _uploadRemote(webpath, "cloud.json")
        except Exception as ex:
            s.log(1, f"WARNING: cloudforecast could not publish: {ex}")
    return data


def _zenithCalib(H, W):
    """(cx, cy, fisheye_module_or_None, calibration_or_None). Zenith = optical centre
    from the fisheye calibration if present, else the image centre."""
    if not _calibCache["done"]:
        _calibCache["done"] = True
        try:
            import allsky_fisheye as fe
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")
            _calibCache["zen"] = (fe.load_calibration(p), fe)
        except Exception:
            _calibCache["zen"] = None
    if _calibCache["zen"]:
        calib, fe = _calibCache["zen"]
        return calib["cx"], calib["cy"], fe, calib
    return W / 2.0, H / 2.0, None, None


def _cloudFieldSmall(bgr, gray, mask, event, rbr_thr, sw, sh):
    """A downscaled 0/1 cloud field for advection (day: RBR, night: star deficit)."""
    msmall = cv2.resize(mask, (sw, sh), interpolation=cv2.INTER_AREA)
    sky = msmall > 127
    if event == "day":
        bs = cv2.resize(bgr, (sw, sh), interpolation=cv2.INTER_AREA).astype(np.float32)
        b, g, r = cv2.split(bs)
        field = ((r / (b + 1.0) > rbr_thr) & sky).astype(np.float32)
    else:
        H, W = gray.shape
        cell = 80
        gw, gh = max(1, W // cell), max(1, H // cell)
        star = np.zeros((gh, gw), bool)
        for x, y in _starPoints(gray, mask):
            star[min(gh - 1, y * gh // H), min(gw - 1, x * gw // W)] = True
        field = cv2.resize((~star).astype(np.float32), (sw, sh), interpolation=cv2.INTER_LINEAR)
        field = field * sky
    return field, sky


def _flowNowcast(gray, bgr, mask, event, method, rbr_thr, clear_pct, overcast_pct, downscale):
    """Optical-flow advection nowcast over the zenith. Returns a dict or None (no usable
    previous frame). verdict ∈ {clouding over, clearing, holding, calm, unclear}."""
    H, W = gray.shape
    sw, sh = W // downscale, H // downscale
    small = cv2.resize(gray, (sw, sh), interpolation=cv2.INTER_AREA)
    prev = cv2.imread(PREV_FLOW, cv2.IMREAD_GRAYSCALE)
    try:
        with open(PREV_META) as f:
            meta = json.load(f)
    except Exception:
        meta = {}
    now = _imageTime()
    cv2.imwrite(PREV_FLOW, small)
    try:
        with open(PREV_META, "w") as f:
            json.dump({"t": now, "method": method}, f)
    except Exception:
        pass
    if prev is None or prev.shape != small.shape:
        return None
    dt = now - meta.get("t", 0)
    if meta.get("method") != method or dt < 8 or dt > 360:   # skip transitions / stale gaps
        return None

    flow = cv2.calcOpticalFlowFarneback(prev, small, None, 0.5, 3, 20, 3, 5, 1.2, 0)
    field, sky = _cloudFieldSmall(bgr, gray, mask, event, rbr_thr, sw, sh)
    fx, fy = flow[..., 0], flow[..., 1]
    mag = np.hypot(fx, fy)
    sig = sky & (mag > 0.6)
    if int(sig.sum()) < max(30, 0.01 * int(sky.sum())):
        return {"verdict": "calm", "confidence": 0.0, "from_az": None,
                "speed_deg_min": 0.0, "horizon_min": None, "text": "cloud motion calm"}
    ux, uy = fx[sig] / mag[sig], fy[sig] / mag[sig]
    coh = float(np.hypot(ux.mean(), uy.mean()))               # 0..1 directional coherence
    per_min = 60.0 / dt
    vmx, vmy = float(np.median(fx[sig])) * per_min, float(np.median(fy[sig])) * per_min
    if coh < 0.3:
        return {"verdict": "unclear", "confidence": round(coh, 2), "from_az": None,
                "speed_deg_min": 0.0, "horizon_min": None, "text": "cloud motion unclear"}

    cx, cy, fe, calib = _zenithCalib(H, W)
    zx, zy = cx / downscale, cy / downscale

    def sample(px, py, rad=3):
        x0, x1 = max(0, int(px - rad)), min(sw, int(px + rad + 1))
        y0, y1 = max(0, int(py - rad)), min(sh, int(py + rad + 1))
        if x1 <= x0 or y1 <= y0:
            return None
        return float(field[y0:y1, x0:x1].mean())

    cur = sample(zx, zy)
    verdict, horizon = "holding", None
    for t in range(3, 41):
        val = sample(zx - vmx * t, zy - vmy * t)              # what is upwind now reaches zenith at +t
        if val is None:
            break
        if cur is not None and cur <= 0.5 and val > 0.5:
            verdict, horizon = "clouding over", t; break
        if cur is not None and cur > 0.5 and val <= 0.5:
            verdict, horizon = "clearing", t; break

    from_az = None
    if fe and calib:
        try:
            norm = math.hypot(vmx, vmy) or 1.0
            fxp, fyp = cx - vmx / norm * 250.0, cy - vmy / norm * 250.0   # upwind point (full px)
            _alt, from_az = fe.pixel_to_altaz(fxp, fyp, calib)
            from_az = round(from_az, 0)
        except Exception:
            from_az = None
    a1 = calib["a1"] if calib else 1250.0
    speed_deg = round(math.hypot(vmx, vmy) * downscale * 90.0 / a1, 2)

    frm = f"from the {_compass(from_az)} " if from_az is not None else ""
    if verdict == "clouding over":
        text = f"clouds {frm}— zenith clouding over in ~{horizon} min"
    elif verdict == "clearing":
        text = f"clouds {frm}— zenith clearing in ~{horizon} min"
    else:
        text = (f"clouds drifting {frm}".strip() + " — zenith holding") if from_az is not None \
            else "cloud motion steady — zenith holding"
    return {"verdict": verdict, "confidence": round(coh, 2), "from_az": from_az,
            "speed_deg_min": speed_deg, "horizon_min": horizon, "text": text}


def _measure(module):
    if s.image is None:
        return "No image available"

    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    rbr_thr = s.asfloat(params["rbr_thr"])
    clear_pct = s.asfloat(params["clear_pct"])
    overcast_pct = s.asfloat(params["overcast_pct"])
    trend_min = s.int(params["trend_min"])
    debug = _truthy(params["debug"])

    # The flow runner passes the event "postcapture"; day or night is in s.TOD
    # (or DAY_OR_NIGHT).
    tod = str(getattr(s, "TOD", "") or s.get_environment_variable("DAY_OR_NIGHT") or "night").lower()

    shape = s.image.shape[:2]
    mask = _mask(params["mask"], shape)
    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if len(s.image.shape) == 3 else s.image

    if tod == "day":
        cloud, cmask = _cloudDay(s.image, mask, rbr_thr)
        method = "rbr"
    else:
        cloud = _cloudNight(gray, mask)
        cmask = None
        method = "stars"

    if cloud is None:
        return "Could not measure cloud cover"
    if debug and cmask is not None:
        s.startModuleDebug(module.meta_data["module"])
        s.writeDebugImage(module.meta_data["module"], "cloudmask.png", cmask)

    now = _imageTime()
    state = _state(cloud, clear_pct, overcast_pct)
    trend, pred30, text = _nowcast(_loadHistory(), now, cloud, trend_min, clear_pct, overcast_pct, method)

    motion = None
    if _truthy(params["motion_nowcast"]):
        try:
            motion = _flowNowcast(gray, s.image, mask, tod, method, rbr_thr,
                                  clear_pct, overcast_pct, max(2, s.int(params["flow_downscale"])))
        except Exception as ex:
            s.log(1, f"WARNING: cloudforecast motion nowcast failed: {ex}")
    # prefer the directional motion nowcast when it has a confident verdict
    if motion and motion.get("verdict") in ("clouding over", "clearing"):
        text = motion["text"]
    elif motion and motion.get("verdict") == "holding" and trend == "stable":
        text = motion["text"]

    rec = {"t": now, "cloud": cloud, "method": method, "state": state,
           "trend": trend, "pred30": pred30, "nowcast": text}
    if motion:
        rec["motion"] = motion
    _appendHistory(rec, s.int(params["history_hours"]), _truthy(params["publish_web"]))

    values = {
        "AS_CLOUDFORECAST_COVER": cloud,
        "AS_CLOUDFORECAST_CLEAR": 1 if state == "clear" else 0,
        "AS_CLOUDFORECAST_STATE": state,
        "AS_CLOUDFORECAST_TREND": trend,
        "AS_CLOUDFORECAST_NOWCAST": text,
        "AS_CLOUDFORECAST_METHOD": method,
    }
    if pred30 is not None:
        values["AS_CLOUDFORECAST_PRED30"] = pred30
    s.saveExtraData(module.meta_data["extradatafilename"], values,
                    module.meta_data["module"], module.meta_data["extradata"], event=module.event)

    result = f"Cloud {cloud:.0f}% ({method}) — {state}; {text}"
    module.log(4, f"INFO: {result}")
    return result


def cloudforecast(params, event):
    return ALLSKYCLOUDFORECAST(params, event).run()


def cloudforecast_cleanup():
    moduleData = {
        "metaData": ALLSKYCLOUDFORECAST.meta_data,
        "cleanup": {
            "files": {
                ALLSKYCLOUDFORECAST.meta_data["extradatafilename"],
                HISTORY, PREV_FLOW, PREV_META
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
