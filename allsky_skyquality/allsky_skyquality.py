""" allsky_skyquality.py

Sky Quality Meter (SQM) module for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)
Home / docs: https://github.com/benhartwich/allsky-skyquality
             (ready-made charting dashboard and full README live there)

Note: this is an advanced alternative to the bundled allsky_sqm module. Where
allsky_sqm reports a raw ROI mean, this reports calibrated mag/arcsec2 with
exposure/gain normalisation plus sensor-free star-count, cloud and aurora indices.

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

`offset` must be calibrated once against a real SQM device (or a known dark-sky
reading). The measured values are written to a rolling `skyquality.json` so a
time-series chart can be built later.
"""
import allsky_shared as s
import os
import json
import math
import time
import subprocess
import cv2
import numpy as np

metaData = {
    "name": "Sky Quality Meter",
    "description": "Measures sky brightness in mag/arcsec2 (exposure/gain normalised)",
    "version": "v0.1.0",
    "events": [
        "night"
    ],
    "experimental": "false",
    "module": "allsky_skyquality",
    "arguments": {
        "mask": "",
        "roi": "",
        "fov_div": "4",
        "offset": "17.0",
        "gain_scale": "200.0",
        "history_hours": "48",
        "count_stars": "true",
        "publish_web": "true",
        "debug": "false"
    },
    "argumentdetails": {
        "mask": {
            "required": "false",
            "description": "ROI Mask",
            "help": "Optional mask image (overlay images folder). White = measure here. Overrides ROI/FOV. Use a zenith-only mask for best results.",
            "type": {"fieldtype": "image"}
        },
        "roi": {
            "required": "false",
            "description": "ROI (x1,y1,x2,y2)",
            "help": "Explicit rectangle to measure. Empty = central region from 'Central FOV'.",
            "type": {"fieldtype": "text"}
        },
        "fov_div": {
            "required": "false",
            "description": "Central FOV Divisor",
            "help": "If no mask/ROI is set, measure a central box of this fraction (4 = central quarter, like indi-allsky)",
            "type": {"fieldtype": "spinner", "min": 2, "max": 20, "step": 1}
        },
        "offset": {
            "required": "true",
            "description": "Magnitude Offset (calibrate!)",
            "help": "Additive calibration constant. Adjust until the reading matches a known SQM value for your camera/exposure.",
            "type": {"fieldtype": "spinner", "min": 0, "max": 30, "step": 0.1}
        },
        "gain_scale": {
            "required": "false",
            "description": "Gain Scale",
            "help": "Divisor exponent for gain normalisation: gain_factor = 10^(gain/scale). 200 suits ZWO 0.1dB gain units; gain 0 => factor 1.",
            "type": {"fieldtype": "spinner", "min": 20, "max": 1000, "step": 10}
        },
        "history_hours": {
            "required": "false",
            "description": "History (hours)",
            "help": "How much history to keep in skyquality.json for charting",
            "type": {"fieldtype": "spinner", "min": 1, "max": 240, "step": 1}
        },
        "count_stars": {
            "required": "false",
            "description": "Count Stars",
            "help": "Also count visible stars (template matching) — a sensor-free clarity/cloud indicator recorded alongside the SQM value",
            "type": {"fieldtype": "checkbox"}
        },
        "publish_web": {
            "required": "false",
            "description": "Publish to Website",
            "help": "Copy skyquality.json into the website data/ folder (and upload to the remote website if enabled) so the dashboard can read it",
            "type": {"fieldtype": "checkbox"}
        },
        "debug": {
            "required": "false",
            "description": "Enable debug images",
            "help": "Write the ROI image to the allsky tmp debug folder",
            "tab": "Debug",
            "type": {"fieldtype": "checkbox"}
        }
    },
    "enabled": "false",
    "changelog": {
        "v0.1.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://github.com/benhartwich",
                "changes": "Initial exposure/gain-normalised SQM in mag/arcsec2 + rolling json for charts"
            }
        ]
    }
}

_maskCache = {"name": None, "mask": None}


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
        if s.getSetting("useremotewebsite") != "true":
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


def _appendHistory(record, hours, publish_web):
    # keep the authoritative copy in tmp, publish a copy to the website data/ folder
    path = os.path.join(s.ALLSKY_TMP, "skyquality.json")
    try:
        data = json.load(open(path)) if os.path.exists(path) else []
    except Exception:
        data = []
    data.append(record)
    cutoff = record["t"] - hours * 3600
    data = [d for d in data if d.get("t", 0) >= cutoff][-5000:]
    try:
        json.dump(data, open(path, "w"))
    except Exception as ex:
        s.log(1, f"WARNING: skyquality could not write history: {ex}")
        return
    if publish_web:
        try:
            ddir = _websiteDataDir()
            os.makedirs(ddir, exist_ok=True)
            webpath = os.path.join(ddir, "skyquality.json")
            json.dump(data, open(webpath, "w"))
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
    (O I 557.7 nm); this is a candidate index, not a certainty."""
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return 0.0
    y0, y1 = int(ys.min()), int(ys.max())
    band = mask.copy()
    band[y0 + int(0.20 * (y1 - y0)):, :] = 0        # keep only the top (north) 20%
    if int((band > 0).sum()) < 50:
        return 0.0
    b, g, r = cv2.split(bgr.astype(np.int16))
    green_excess = (g - b)[band > 0]
    return round(max(0.0, float(green_excess.mean())), 1)


def skyquality(params, event):
    if s.image is None:
        return "No image available"

    offset = s.asfloat(params.get("offset", 17.0))
    gain_scale = s.asfloat(params.get("gain_scale", 200.0))
    debug = params.get("debug", False)

    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY) if len(s.image.shape) == 3 else s.image
    mask = _roiMask(params, gray.shape[:2])
    if debug:
        s.startModuleDebug(metaData["module"])
        s.writeDebugImage(metaData["module"], "sqm-roi.png",
                          cv2.bitwise_and(gray, gray, mask=mask))

    mean_adu = float(cv2.mean(gray, mask=mask)[0])

    # exposure (us -> s) and gain from the capture environment
    exp_us = s.asfloat(s.getEnvironmentVariable("AS_EXPOSURE_US"))
    exposure_s = (exp_us / 1e6) if exp_us and exp_us > 0 else 1.0
    gain = s.asfloat(s.getEnvironmentVariable("AS_GAIN"))
    if gain is None:
        gain = 0.0
    gain_factor = 10.0 ** (gain / gain_scale) if gain_scale > 0 else 1.0

    signal = mean_adu / exposure_s / gain_factor
    if signal <= 0:
        s.setEnvironmentVariable("AS_SQM", "0")
        return "Signal is zero, cannot compute SQM"

    sqm = offset - 2.5 * math.log10(signal)

    # extra sensor-free metrics (like indi-allsky): stars, cloud cover, aurora, temps
    def _flt(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    stars = cloud = None
    if params.get("count_stars", True):
        stars = _countStars(_starPoints(gray, mask, 0.65))
        cloud = _cloudPct(mask, _starPoints(gray, mask, 0.55), cell=80)
    aurora = _auroraIndex(s.image, mask) if len(s.image.shape) == 3 else None
    temp = _flt(s.getEnvironmentVariable("AS_TEMPERATURE_C"))
    cpu = _flt(s.getEnvironmentVariable("AS_CPUTEMP_C"))

    s.setEnvironmentVariable("AS_SQM", f"{sqm:.2f}")
    s.setEnvironmentVariable("AS_SQM_ADU", f"{mean_adu:.1f}")
    s.setEnvironmentVariable("AS_SQM_DESC", _bortle(sqm))
    if stars is not None:
        s.setEnvironmentVariable("AS_SQM_STARS", str(stars))
    if cloud is not None:
        s.setEnvironmentVariable("AS_SQM_CLOUD", str(cloud))
    if aurora is not None:
        s.setEnvironmentVariable("AS_SQM_AURORA", str(aurora))

    rec = {
        "t": int(time.time()),
        "sqm": round(sqm, 2),
        "adu": round(mean_adu, 1),
        "exp": round(exposure_s, 3),
        "gain": round(gain, 1),
    }
    for k, v in (("stars", stars), ("cloud", cloud), ("aurora", aurora),
                 ("temp", None if temp is None else round(temp, 1)),
                 ("cpu", None if cpu is None else round(cpu, 1))):
        if v is not None:
            rec[k] = v
    _appendHistory(rec, s.int(params.get("history_hours", 48)), params.get("publish_web", True))

    extra = (f", {stars} stars" if stars is not None else "") + \
            (f", {cloud}% cloud" if cloud is not None else "")
    result = f"SQM {sqm:.2f} mag/arcsec2 (ADU {mean_adu:.1f}, exp {exposure_s:.2f}s){extra} — Bortle {_bortle(sqm)}"
    s.log(4, f"INFO: {result}")
    return result


def skyquality_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {os.path.join(s.ALLSKY_TMP, "skyquality.json")},
            "env": {"AS_SQM", "AS_SQM_ADU", "AS_SQM_DESC", "AS_SQM_STARS",
                    "AS_SQM_CLOUD", "AS_SQM_AURORA"}
        }
    }
    s.cleanupModule(moduleData)
