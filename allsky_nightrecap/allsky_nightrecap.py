""" allsky_nightrecap.py

A recap of the night, every morning, for Allsky.
https://github.com/AllskyTeam/allsky

Author:      Benjamin Hartwich (https://astronomy.garden)

At the end of the night this module collects what the other modules found and
makes one picture and one short video of it:

  * when the sky was clear (Target Watch, Cloud Forecast or Sky Quality);
  * the meteors (Meteor Detection), with their showers;
  * the satellite trails found in the images (Sky Traffic);
  * aurora candidates (Aurora Detector);
  * the darkest sky (Sky Quality) and the strongest geomagnetic activity
    (Space Weather).

Every source is optional: what isn't installed is left out.  The recap image,
the video and a JSON summary go into the night's images folder (recap/), and
one line of text is available for the overlay, the website or a notification.
"""
import allsky_shared as s
from allsky_base import ALLSKYMODULEBASE
import os
import sys
import json
import math
import time
import shutil
import subprocess
import cv2
import numpy as np


class ALLSKYNIGHTRECAP(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Night Recap",
        "description": "Every morning one picture and one short video of the night: clear hours, meteors, satellites, aurora",
        "version": "v0.1.0",
        "module": "allsky_nightrecap",
        "events": [
            "nightday"
        ],
        "experimental": "true",
        "centersettings": "false",
        "testable": "true",
        "group": "Image Analysis",
        "extradatafilename": "allsky_nightrecap.json",
        "extradata": {
            "database": {
                "enabled": "True",
                "table": "allsky_nightrecap",
                "pk": "id",
                "pk_type": "int",
                "include_all": "false",
                "time_of_day_save": {
                    "day": "never",
                    "night": "never",
                    "nightday": "always",
                    "daynight": "never",
                    "periodic": "never"
                }
            },
            "values": {
                "AS_NIGHTRECAP_TEXT": {
                    "name": "${NIGHTRECAP_TEXT}",
                    "format": "",
                    "sample": "",
                    "group": "Night Recap",
                    "description": "Last night in one line, e.g. 'Clear 4.5 h, 2 meteors, 12 satellites'",
                    "type": "string"
                },
                "AS_NIGHTRECAP_CLEAR_HOURS": {
                    "name": "${NIGHTRECAP_CLEAR_HOURS}",
                    "format": "",
                    "sample": "",
                    "group": "Night Recap",
                    "description": "Hours of clear sky last night",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_NIGHTRECAP_METEORS": {
                    "name": "${NIGHTRECAP_METEORS}",
                    "format": "",
                    "sample": "",
                    "group": "Night Recap",
                    "description": "Meteors last night",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_NIGHTRECAP_SATELLITES": {
                    "name": "${NIGHTRECAP_SATELLITES}",
                    "format": "",
                    "sample": "",
                    "group": "Night Recap",
                    "description": "Satellite trails found last night",
                    "type": "number",
                    "database": {
                        "include": "true"
                    }
                },
                "AS_NIGHTRECAP_IMAGE": {
                    "name": "${NIGHTRECAP_IMAGE}",
                    "format": "",
                    "sample": "",
                    "group": "Night Recap",
                    "description": "Path of last night's recap image",
                    "type": "string"
                }
            }
        },
        "arguments": {
            "video": "true",
            "seconds_per_event": "2",
            "max_events": "40",
            "clear_above": "70",
            "meteor_folder": "",
            "publish_web": "false",
            "notify_url": ""
        },
        "argumentdetails": {
            "video": {
                "required": "false",
                "description": "Make a video",
                "help": "Besides the recap image, make a short video (H.264, with ffmpeg) that shows the recap and then each event of the night with a caption.",
                "tab": "Recap",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "seconds_per_event": {
                "required": "false",
                "description": "Seconds per event",
                "help": "How long each event is shown in the video.",
                "tab": "Recap",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 10,
                    "step": 1
                }
            },
            "max_events": {
                "required": "false",
                "description": "Most events in the video",
                "help": "Meteors and aurora come first, then the satellites, brightest first.",
                "tab": "Recap",
                "type": {
                    "fieldtype": "spinner",
                    "min": 5,
                    "max": 200,
                    "step": 5
                }
            },
            "clear_above": {
                "required": "false",
                "description": "Clear above (%)",
                "help": "An image counts as clear when at least this much of the sky is clear.",
                "tab": "Recap",
                "type": {
                    "fieldtype": "spinner",
                    "min": 30,
                    "max": 100,
                    "step": 5
                }
            },
            "meteor_folder": {
                "required": "false",
                "description": "Meteor Detection folder",
                "help": "Where the Meteor Detection module writes meteors.json. Empty = its default, the Website's meteors folder.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "text"
                }
            },
            "publish_web": {
                "required": "false",
                "description": "Publish to the website",
                "help": "Copy recap.jpg, recap.mp4 and recap.json into the Website's recap folder, and upload them to a remote website. The remote 'recap' folder must exist.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "checkbox"
                }
            },
            "notify_url": {
                "required": "false",
                "description": "Notify URL",
                "help": "Optional. The one-line recap is sent to this URL with an HTTP POST, e.g. https://ntfy.sh/your-topic.",
                "tab": "Sources",
                "type": {
                    "fieldtype": "text"
                }
            }
        },
        "changelog": {
            "v0.1.0": [
                {
                    "author": "Benjamin Hartwich",
                    "authorurl": "https://astronomy.garden",
                    "changes": [
                        "Recap image and video of the night from the other modules' results: clear hours, meteors, satellite trails, aurora, darkest sky, Kp",
                        "One line for the overlay, the website or a notification"
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
            result = f"Module Night Recap failed on line {tb.tb_lineno} - {e}"
            self.log(0, f"ERROR: {result}")
            return result


W, H = 1920, 1080
BG = (24, 18, 14)
FG = (235, 235, 235)
DIM = (150, 150, 150)
GREEN = (90, 200, 90)
GREY = (80, 80, 80)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _truthy(v):
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def _home():
    return s.get_environment_variable("ALLSKY_HOME") or os.path.expanduser("~/allsky")


def _website():
    return s.get_environment_variable("ALLSKY_WEBSITE") or os.path.join(_home(), "html", "allsky")


def _imagesDir():
    return s.get_environment_variable("ALLSKY_IMAGES") or os.path.join(_home(), "images")


def _stamp(t):
    return time.strftime("%Y%m%d%H%M%S", time.localtime(t))


def _unix(stamp):
    return time.mktime(time.strptime(stamp, "%Y%m%d%H%M%S"))


# --- the night ----------------------------------------------------------------

def _night(now):
    """(start, end, day) of the night that just ended: from the Sun at -6 deg in
    the evening to -6 deg in the morning.  day is the evening's date, the
    images folder the night was saved in."""
    import ephem
    obs = ephem.Observer()
    obs.lat = str(s.convertLatLon(s.getSetting("latitude")))
    obs.lon = str(s.convertLatLon(s.getSetting("longitude")))
    obs.horizon = "-6"
    obs.date = ephem.Date(now / 86400.0 + 25567.5)
    sun = ephem.Sun()
    try:
        rise = obs.previous_rising(sun, use_center=True)
        obs.date = rise
        setting = obs.previous_setting(sun, use_center=True)
        start = (float(setting) - 25567.5) * 86400.0
        end = (float(rise) - 25567.5) * 86400.0
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        end = now
        start = now - 12 * 3600
    if now - end > 6 * 3600:          # run by hand in the evening: take the night before
        end = now
    return start, end, time.strftime("%Y%m%d", time.localtime(start))


# --- sources ------------------------------------------------------------------

def _db():
    try:
        return s.get_database_connection()
    except Exception:
        return None


def _rows(db, table, columns, start, end):
    """[(time, {column: value})] of one module's table within the night."""
    if db is None:
        return []
    try:
        if not db.table_exists(table):
            return []
        have = set(db.get_columns(table) or [])
        cols = [c for c in columns if c in have]
        if not cols:
            return []
        sql = f"SELECT id, {', '.join(cols)} FROM {table} WHERE id >= %s AND id <= %s ORDER BY id"
        return [(int(r["id"]), r) for r in db.fetchall(sql, (int(start), int(end)))]
    except Exception:
        return []


def _clearTimeline(db, start, end, clear_above):
    """[(time, clear %)] from the first module that has data: Target Watch, Cloud
    Forecast, Sky Quality."""
    for table, col, invert in (("allsky_targetwatch", "AS_TARGETWATCH_SKY", False),
                               ("allsky_cloudforecast", "AS_CLOUDFORECAST_COVER", True),
                               ("allsky_skyquality", "AS_SKYQUALITY_CLOUD", True)):
        rows = [(t, r.get(col)) for t, r in _rows(db, table, [col], start, end) if r.get(col) is not None]
        if len(rows) >= 5:
            return [(t, 100.0 - float(v) if invert else float(v)) for t, v in rows], table
    return [], None


def _clearHours(timeline, clear_above):
    """Hours of clear sky, and the longest clear stretch (start, end)."""
    if len(timeline) < 2:
        return 0.0, None
    total, best, run_start = 0.0, None, None
    for (t1, c1), (t2, _c2) in zip(timeline, timeline[1:]):
        gap = min(t2 - t1, 900)                     # a gap in the data counts at most 15 min
        if c1 >= clear_above:
            total += gap
            run_start = t1 if run_start is None else run_start
            if best is None or t1 + gap - run_start > best[1] - best[0]:
                best = (run_start, t1 + gap)
        else:
            run_start = None
    return total / 3600.0, best


def _meteors(params, start, end):
    folder = params["meteor_folder"].strip() or os.path.join(_website(), "meteors")
    try:
        with open(os.path.join(folder, "meteors.json")) as fh:
            recs = json.load(fh)
    except Exception:
        return []
    out = []
    for r in recs:
        try:
            t = _unix(r["time"])
        except (KeyError, ValueError):
            continue
        if start <= t <= end:
            path = os.path.join(folder, r.get("file", ""))
            out.append({"kind": "meteor", "time": t, "file": path if os.path.isfile(path) else None,
                        "label": "Meteor" + (f" ({r['showers'][0]})" if r.get("showers") else ""),
                        "peak": r.get("peak") or 0, "p1": r.get("p1"), "p2": r.get("p2")})
    return out


def _satellites(start, end):
    path = os.path.join(os.environ.get("ALLSKY_MYFILES_DIR") or "", "skytraffic", "skytraffic_seen.json")
    try:
        with open(path) as fh:
            recs = json.load(fh)
    except Exception:
        return []
    out = []
    for r in recs:
        try:
            t = _unix(r["time"])
        except (KeyError, ValueError):
            continue
        if start <= t <= end:
            out.append({"kind": "satellite", "time": t, "label": r.get("name", "satellite"),
                        "p1": r.get("p1"), "p2": r.get("p2"), "alt": r.get("alt", 0)})
    return out


def _aurora(db, start, end):
    rows = _rows(db, "allsky_aurora", ["AS_AURORA", "AS_AURORA_INDEX"], start, end)
    return [{"kind": "aurora", "time": t, "label": f"Aurora? index {float(r.get('AS_AURORA_INDEX') or 0):.1f}%"}
            for t, r in rows if r.get("AS_AURORA") and float(r["AS_AURORA"]) >= 1]


def _extremes(db, start, end):
    out = {}
    sqm = [float(r["AS_SKYQUALITY_SQM"]) for _, r in _rows(db, "allsky_skyquality", ["AS_SKYQUALITY_SQM"], start, end)
           if r.get("AS_SKYQUALITY_SQM") is not None]
    if sqm:
        out["sqm"] = max(sqm)
    kp = [float(r["SWX_KPDATA"]) for _, r in _rows(db, "allsky_spaceweather", ["SWX_KPDATA"], start, end)
          if r.get("SWX_KPDATA") is not None]
    if kp:
        out["kp"] = max(kp)
    return out


def _imageAt(day, t):
    """The night image taken closest before time t (within 10 minutes)."""
    folder = os.path.join(_imagesDir(), day)
    try:
        names = sorted(n for n in os.listdir(folder) if n.startswith("image-") and n.endswith(".jpg"))
    except OSError:
        return None
    best = None
    for n in names:
        try:
            ti = _unix(n[6:20])
        except ValueError:
            continue
        if ti <= t + 5 and t - ti < 600:
            best = n
    return os.path.join(folder, best) if best else None


# --- drawing -----------------------------------------------------------------

def _text(img, txt, org, scale, colour=FG, thick=2):
    cv2.putText(img, txt, org, FONT, scale, colour, thick, cv2.LINE_AA)


def _fit(img, w, h):
    """Scale an image into w x h, centred on black."""
    out = np.zeros((h, w, 3), np.uint8)
    if img is None:
        return out
    sc = min(w / img.shape[1], h / img.shape[0])
    r = cv2.resize(img, (max(1, int(img.shape[1] * sc)), max(1, int(img.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    y0, x0 = (h - r.shape[0]) // 2, (w - r.shape[1]) // 2
    out[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r
    return out


def _crop(ev, day, aspect):
    """A picture of the event: the part of the meteor image or night image
    around the streak, widened to the given width/height ratio."""
    img = cv2.imread(ev["file"]) if ev.get("file") else None
    if img is None:
        path = _imageAt(day, ev["time"])
        img = cv2.imread(path) if path else None
    if img is None or not (ev.get("p1") and ev.get("p2")):
        return img
    h, w = img.shape[:2]
    (x1, y1), (x2, y2) = ev["p1"], ev["p2"]
    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    bw, bh = abs(x2 - x1) + 240, abs(y2 - y1) + 240
    bw, bh = max(bw, bh * aspect), max(bh, bw / aspect)
    bw, bh = min(bw, w), min(bh, h)
    x0 = int(min(max(0, cx - bw / 2), w - bw))
    y0 = int(min(max(0, cy - bh / 2), h - bh))
    return img[y0:y0 + int(bh), x0:x0 + int(bw)]


def _distinct(events):
    """One picture per image: two meteors on the same image are shown once."""
    seen, out = set(), []
    for e in events:
        key = (e["kind"], e.get("file") or round(e["time"]))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def _recapImage(day, start, end, timeline, clear_h, best, events, extremes, clear_above, source):
    img = np.full((H, W, 3), BG, np.uint8)
    d1 = time.strftime("%d %b", time.localtime(start))
    d2 = time.strftime("%d %b %Y", time.localtime(end))
    _text(img, f"The night of {d1} to {d2}", (60, 90), 1.6, FG, 3)

    # tiles
    n_met = sum(1 for e in events if e["kind"] == "meteor")
    n_sat = sum(1 for e in events if e["kind"] == "satellite")
    n_aur = sum(1 for e in events if e["kind"] == "aurora")
    tiles = [(f"{clear_h:.1f} h" if source else "-", "clear sky" if source else "clear sky (no data)"),
             (str(n_met), "meteors"), (str(n_sat), "satellite trails"), (str(n_aur), "aurora images")]
    if "sqm" in extremes:
        tiles.append((f"{extremes['sqm']:.2f}", "darkest sky (mag/arcsec2)"))
    if "kp" in extremes:
        tiles.append((f"{extremes['kp']:.1f}", "highest Kp"))
    tw = (W - 120) // len(tiles)
    for i, (big, small) in enumerate(tiles):
        x = 60 + i * tw
        cv2.rectangle(img, (x, 130), (x + tw - 20, 290), (45, 36, 30), -1)
        _text(img, big, (x + 20, 220), 2.0, FG, 4)
        _text(img, small, (x + 20, 268), 0.8, DIM, 2)

    # clear-sky timeline
    x0, x1, y0, y1 = 60, W - 60, 340, 420
    cv2.rectangle(img, (x0, y0), (x1, y1), GREY, -1)
    span = max(1.0, end - start)
    for (t1, c), (t2, _) in zip(timeline, timeline[1:]):
        if c >= clear_above:
            a = x0 + int((t1 - start) / span * (x1 - x0))
            b = x0 + int((min(t2, t1 + 900) - start) / span * (x1 - x0))
            cv2.rectangle(img, (a, y0), (max(a + 1, b), y1), GREEN, -1)
    for e in events:
        a = x0 + int((e["time"] - start) / span * (x1 - x0))
        colour = {"meteor": (0, 215, 255), "aurora": (120, 255, 120), "satellite": (255, 200, 120)}[e["kind"]]
        cv2.line(img, (a, y0 - 12), (a, y0 - 2), colour, 3)
    t = math.ceil(start / 3600.0) * 3600
    while t < end:
        a = x0 + int((t - start) / span * (x1 - x0))
        cv2.line(img, (a, y1), (a, y1 + 8), DIM, 1)
        _text(img, time.strftime("%H", time.localtime(t)), (a - 12, y1 + 34), 0.7, DIM, 1)
        t += 3600
    label = "clear sky (green)" + (f", longest {time.strftime('%H:%M', time.localtime(best[0]))}-"
                                   f"{time.strftime('%H:%M', time.localtime(best[1]))}" if best else "")
    _text(img, label + "   marks: meteor (yellow), aurora (green), satellite (blue)", (60, 490), 0.75, DIM, 1)

    # pictures: meteors and aurora first, then the satellites
    pics = _distinct([e for e in events if e["kind"] != "satellite"] + [e for e in events if e["kind"] == "satellite"])[:5]
    if pics:
        pw = (W - 120) // 5
        for i, e in enumerate(pics):
            tile = _fit(_crop(e, day, (pw - 20) / 440.0), pw - 20, 440)
            x = 60 + i * pw
            img[530:970, x:x + pw - 20] = tile
            _text(img, e["label"][:24], (x, 1005), 0.7, FG, 2)
            _text(img, time.strftime("%H:%M", time.localtime(e["time"])), (x, 1040), 0.7, DIM, 1)
    else:
        _text(img, "Nothing caught tonight.", (60, 700), 1.2, DIM, 2)
    return img


def _video(path, recap, events, day, seconds, max_events):
    """recap image, then each event with a caption; H.264 with ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    tmp = os.path.join(s.ALLSKY_TMP, "nightrecap_frames")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    frames = [cv2.resize(recap, (1280, 720), interpolation=cv2.INTER_AREA)]
    order = _distinct([e for e in events if e["kind"] != "satellite"] +
                      sorted([e for e in events if e["kind"] == "satellite"], key=lambda e: -e.get("alt", 0)))
    for e in order[:max_events]:
        f = _fit(_crop(e, day, 1280 / 720.0), 1280, 720)
        cv2.rectangle(f, (0, 650), (1280, 720), (0, 0, 0), -1)
        _text(f, f"{time.strftime('%H:%M:%S', time.localtime(e['time']))}  {e['label']}", (20, 698), 1.0, FG, 2)
        frames.append(f)
    for i, f in enumerate(frames):
        cv2.imwrite(os.path.join(tmp, f"f{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-framerate", f"1/{seconds}", "-i", os.path.join(tmp, "f%04d.jpg"),
           "-c:v", "libx264", "-r", "25", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    ok = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600).returncode == 0
    shutil.rmtree(tmp, ignore_errors=True)
    return ok


def _publish(files):
    folder = os.path.join(_website(), "recap")
    os.makedirs(folder, exist_ok=True)
    for f in files:
        shutil.copy2(f, os.path.join(folder, os.path.basename(f)))
    if str(s.getSetting("useremotewebsite")).lower() in ("true", "1", "yes", "on"):
        uploader = os.path.join(s.get_environment_variable("ALLSKY_SCRIPTS") or os.path.join(_home(), "scripts"), "upload.sh")
        rdir = ((s.getSetting("remotewebsiteimagedir") or "").rstrip("/") + "/recap").lstrip("/")
        for f in files:
            if os.path.isfile(uploader):
                subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", f, rdir, os.path.basename(f), "NightRecap"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# --- main --------------------------------------------------------------------

def _run(module):
    params = {k: str(module.get_param(k, v, str)) for k, v in module.meta_data["arguments"].items()}
    clear_above = s.asfloat(params["clear_above"])
    start, end, day = _night(time.time())
    db = _db()
    timeline, source = _clearTimeline(db, start, end, clear_above)
    clear_h, best = _clearHours(timeline, clear_above)
    events = sorted(_meteors(params, start, end) + _aurora(db, start, end) + _satellites(start, end),
                    key=lambda e: e["time"])
    extremes = _extremes(db, start, end)

    n_met = sum(1 for e in events if e["kind"] == "meteor")
    n_sat = sum(1 for e in events if e["kind"] == "satellite")
    n_aur = sum(1 for e in events if e["kind"] == "aurora")
    parts = [f"Clear {clear_h:.1f} h" if source else "No cloud data",
             f"{n_met} meteor{'s' if n_met != 1 else ''}", f"{n_sat} satellite trail{'s' if n_sat != 1 else ''}"]
    if n_aur:
        parts.append(f"aurora on {n_aur} image{'s' if n_aur != 1 else ''}")
    if "sqm" in extremes:
        parts.append(f"darkest {extremes['sqm']:.2f} mag/arcsec²")
    text = time.strftime("%d/", time.localtime(start)) + time.strftime("%d %b: ", time.localtime(end)) + ", ".join(parts)

    folder = os.path.join(_imagesDir(), day, "recap")
    os.makedirs(folder, exist_ok=True)
    recap = _recapImage(day, start, end, timeline, clear_h, best, events, extremes, clear_above, source)
    img_path = os.path.join(folder, "recap.jpg")
    cv2.imwrite(img_path, recap, [cv2.IMWRITE_JPEG_QUALITY, 90])
    files = [img_path]
    if _truthy(params["video"]):
        vid = os.path.join(folder, "recap.mp4")
        if _video(vid, recap, events, day, max(1, s.int(params["seconds_per_event"])), s.int(params["max_events"])):
            files.append(vid)
        else:
            module.log(1, "WARNING: Night Recap could not make the video (is ffmpeg installed?)")
    summary = {"night": day, "start": round(start), "end": round(end), "text": text,
               "clear_hours": round(clear_h, 2), "clear_source": source,
               "longest_clear": [round(best[0]), round(best[1])] if best else None,
               "meteors": n_met, "satellites": n_sat, "aurora": n_aur, "extremes": extremes,
               "events": [{"kind": e["kind"], "time": round(e["time"]), "label": e["label"]} for e in events]}
    js = os.path.join(folder, "recap.json")
    with open(js, "w") as fh:
        json.dump(summary, fh, indent=1)
    files.append(js)
    if _truthy(params["publish_web"]):
        _publish(files)
    url = params["notify_url"].strip()
    if url:
        try:
            import requests
            requests.post(url, data=text.encode("utf-8"), timeout=8)
        except Exception as ex:
            module.log(1, f"WARNING: Night Recap could not send the notification: {ex}")

    s.saveExtraData(module.meta_data["extradatafilename"], {
        "AS_NIGHTRECAP_TEXT": text, "AS_NIGHTRECAP_CLEAR_HOURS": round(clear_h, 1),
        "AS_NIGHTRECAP_METEORS": n_met, "AS_NIGHTRECAP_SATELLITES": n_sat, "AS_NIGHTRECAP_IMAGE": img_path},
        module.meta_data["module"], module.meta_data["extradata"], event=module.event)
    result = f"Night Recap: {text} -> {folder}"
    module.log(4, f"INFO: {result}")
    return result


def nightrecap(params, event):
    return ALLSKYNIGHTRECAP(params, event).run()


def nightrecap_cleanup():
    moduleData = {
        "metaData": ALLSKYNIGHTRECAP.meta_data,
        "cleanup": {
            "files": {
                ALLSKYNIGHTRECAP.meta_data["extradatafilename"]
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
