#!/usr/bin/env python3
"""Replay a saved night through the meteor detector -- a test mode.

Meteors are rare and clear nights rarer, so "is it working, are my thresholds right"
otherwise means waiting weeks for an answer (see AllskyTeam/allsky discussion #4281:
"Is there a way to run a test?"). This runs the detector over the images Allsky
already saved for one night, frame by frame, and reports what it would have confirmed
and what it rejected, and why.

It runs the INSTALLED module -- the same code and the same fisheye calibration that
run live -- inside a private sandbox. Nothing live is touched: no detector state, no
settings, no website, no uploads, no overlay variables.

Usage:
    tools/replay_night.py 20260917
    tools/replay_night.py 20260917 --set min_length=60 --set diff_thr=25
    tools/replay_night.py 20260917 --compare     # vs. what was saved live that night

Settings come from your night flow, so the replay uses exactly what you configured;
--set overrides single values for an experiment without changing anything.

Two differences to a live night:
  * It replays the images Allsky SAVED, which already carry the overlay. Live, the
    module sees the frame before the overlay module runs (when it sits right after
    Load Image). Text that changes every frame inside the detection mask can show up
    as an extra candidate here that never appears live.
  * The detector's memory of recurring hot spots starts empty, as on a new install.
"""

import argparse
import glob
import importlib.util
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import types
from collections import Counter
from datetime import datetime, timedelta

import cv2

MODULE = "allsky_meteordetect"
FRAME_RE = re.compile(r"^image-(\d{14})\.(jpg|jpeg|png)$", re.I)
METEOR_RE = re.compile(r"^meteors-(\d{14})\.(jpg|png)$", re.I)
SKIP_PREFIXES = ("Cloudy frame", "Scintillation", "First frame", "Raining", "No image")


# --- the detector's view of time ---------------------------------------------------

class FrameClock:
    """Stands in for the time module inside the detector, so 'now' is the frame's
    capture time: the pending-candidate stamps, the recurrence memory and - above all -
    the sky projection used by the star vetoes follow the night being replayed rather
    than the moment the replay runs."""

    def __init__(self):
        self.t = time.time()

    def time(self):
        return self.t

    def gmtime(self, secs=None):
        return time.gmtime(self.t if secs is None else secs)

    def localtime(self, secs=None):
        return time.localtime(self.t if secs is None else secs)

    def strftime(self, fmt, tt=None):
        return time.strftime(fmt, self.localtime() if tt is None else tt)

    def __getattr__(self, name):
        return getattr(time, name)


def _epoch(stamp):
    """Allsky names files in local time."""
    return time.mktime(time.strptime(stamp, "%Y%m%d%H%M%S"))


# --- day / night, the way Allsky decides it -----------------------------------------

def _parseLatLon(value):
    """'48.136010N' / '14.389510E' / '-33.9' -> float, or None."""
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*([NSEWnsew]?)\s*", str(value or ""))
    if not m:
        return None
    v = float(m.group(1))
    return -abs(v) if m.group(2).upper() in ("S", "W") else v


def _sunElevation(lat, lon, t):
    """Solar elevation in degrees (NOAA approximation, good to a fraction of a degree)."""
    g = time.gmtime(t)
    hour = g.tm_hour + g.tm_min / 60 + g.tm_sec / 3600
    gamma = 2 * math.pi / 365 * (g.tm_yday - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
    ha = math.radians((hour * 60 + eqtime + 4 * lon) / 4 - 180)
    la = math.radians(lat)
    cosz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1.0, min(1.0, cosz))))


# --- setup -----------------------------------------------------------------------------

def _findModule(home, explicit):
    """The module file that actually runs live: Allsky 2025 searches config/myFiles
    first, then scripts/. The repository copy next to this tool is the last resort."""
    if explicit:
        return os.path.abspath(explicit)
    repo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), MODULE + ".py")
    for path in (os.path.join(home, "config", "myFiles", "modules", MODULE + ".py"),
                 os.path.join(home, "scripts", "modules", MODULE + ".py"),
                 repo):
        if os.path.isfile(path):
            return path
    sys.exit(f"ERROR: {MODULE}.py not found; pass --module")


def _flowArguments(home):
    """This module's arguments as configured in the night flow ({} if not found)."""
    path = os.path.join(home, "config", "modules", "postprocessing_night.json")
    try:
        flow = json.load(open(path))
    except Exception:
        return {}
    for entry in flow.values():
        if isinstance(entry, dict) and str(entry.get("module", "")).startswith(MODULE):
            return dict(entry.get("metadata", {}).get("arguments", {}))
    return {}


def _loadDetector(home, module_path, sandbox):
    """Import allsky_shared and the module with every path that WRITES pointed into the
    sandbox, and everything that reaches outside - uploads, overlay variables, rain
    check - replaced. Paths that are only READ (settings, mask, calibration) stay real."""
    os.environ.setdefault("ALLSKY_HOME", home)
    os.environ.setdefault("ALLSKY_SCRIPTS", os.path.join(home, "scripts"))
    os.environ.setdefault("ALLSKY_OVERLAY", os.path.join(home, "config", "overlay"))
    os.environ.setdefault("SETTINGS_FILE", os.path.join(home, "config", "settings.json"))
    os.environ["ALLSKY_TMP"] = os.path.join(sandbox, "tmp")
    os.environ["ALLSKY_IMAGES"] = os.path.join(sandbox, "images")
    os.environ["ALLSKY_EXTRA"] = os.path.join(sandbox, "extra")
    for d in ("tmp", "images", "extra", "website/meteors/thumbnails"):
        os.makedirs(os.path.join(sandbox, d), exist_ok=True)

    sys.path.insert(0, os.path.join(home, "scripts", "modules"))   # allsky_shared
    sys.path.insert(0, os.path.dirname(module_path))               # allsky_fisheye beside it
    import allsky_shared as s                                      # noqa: E402

    spec = importlib.util.spec_from_file_location(MODULE, module_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if not m.STATE_FILE.startswith(sandbox):
        sys.exit(f"ERROR: detector state would go to {m.STATE_FILE}, not the sandbox - aborting")

    published = {}
    s.raining = lambda *a, **k: (False, False)
    s.saveExtraData = lambda file_name, extra_data, *a, **k: published.update(extra_data)
    s.writeDebugImage = lambda *a, **k: None
    s.startModuleDebug = lambda *a, **k: None
    m._uploadRemote = lambda *a, **k: None
    m._uploadVetoed = lambda *a, **k: None

    def _blocked(*a, **k):
        raise RuntimeError("process launch blocked during replay")
    m.subprocess = types.SimpleNamespace(Popen=_blocked, run=_blocked,
                                         DEVNULL=None, PIPE=None, STDOUT=None)
    clock = FrameClock()
    m.time = clock
    return s, m, clock, published


def _nightFrames(folder, night_only, lat, lon, angle):
    frames = []
    for name in sorted(os.listdir(folder)):
        mm = FRAME_RE.match(name)
        if not mm:
            continue
        stamp = mm.group(1)
        if night_only and _sunElevation(lat, lon, _epoch(stamp)) >= angle:
            continue
        frames.append((stamp, os.path.join(folder, name)))
    return frames


def _liveStamps(home, night, outputdir):
    """Meteors the live module saved for this night, from the website folder (every
    version writes there), assigned to nights the way Allsky assigns images."""
    website = outputdir or os.path.join(os.environ.get("ALLSKY_WEBSITE")
                                        or os.path.join(home, "html", "allsky"), "meteors")
    stamps = []
    for name in (os.listdir(website) if os.path.isdir(website) else []):
        mm = METEOR_RE.match(name)
        if mm:
            stamp = mm.group(1)
            evening = (datetime.strptime(stamp, "%Y%m%d%H%M%S") - timedelta(hours=12)).strftime("%Y%m%d")
            if evening == night:
                stamps.append(stamp)
    return sorted(stamps)


def _hms(stamp):
    return f"{stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]}"


# --- main ------------------------------------------------------------------------------

def main():
    home = os.environ.get("ALLSKY_HOME") or os.path.expanduser("~/allsky")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("night", help="night folder name (YYYYMMDD, the evening's date) or a path to it")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override one module setting for this replay; repeatable")
    ap.add_argument("--module", help=f"{MODULE}.py to test (default: the installed one)")
    ap.add_argument("--out", help="keep results here (default: a new temporary folder)")
    ap.add_argument("--all", action="store_true",
                    help="replay every frame, not only those Allsky would process as night")
    ap.add_argument("--compare", action="store_true",
                    help="compare with the meteors the live module saved for this night")
    ap.add_argument("--verbose", action="store_true", help="print every frame and the module's log")
    args = ap.parse_args()

    folder = args.night if os.sep in args.night else os.path.join(
        os.environ.get("ALLSKY_IMAGES") or os.path.join(home, "images"), args.night)
    folder = os.path.abspath(folder)
    night = os.path.basename(folder.rstrip(os.sep))
    if not os.path.isdir(folder):
        sys.exit(f"ERROR: no such night folder: {folder}")

    module_path = _findModule(home, args.module)
    sandbox = os.path.abspath(args.out) if args.out else tempfile.mkdtemp(prefix=f"meteor-replay-{night}-")
    os.makedirs(sandbox, exist_ok=True)

    s, m, clock, published = _loadDetector(home, module_path, sandbox)
    logs = []
    s.log = lambda level, msg, *a, **k: (logs.append(msg), args.verbose and print("   log:", msg))

    params = dict(m.metaData["arguments"])
    params.update(_flowArguments(home))
    live_outputdir = (params.get("outputdir") or "").strip()
    for item in args.set:
        key, sep, value = item.partition("=")
        if not sep or key not in m.metaData["arguments"]:
            sys.exit(f"ERROR: --set {item!r}: unknown setting (known: {', '.join(sorted(m.metaData['arguments']))})")
        params[key] = value
    params.update(upload_remote="false", outputdir=os.path.join(sandbox, "website", "meteors"),
                  save_webui="true", save_marked="true", save_vetoed="true", debug="false")

    lat = _parseLatLon(s.getSetting("latitude"))
    lon = _parseLatLon(s.getSetting("longitude"))
    angle = float(s.getSetting("angle") if s.getSetting("angle") is not None else -6)
    night_only = not args.all and lat is not None and lon is not None
    frames = _nightFrames(folder, night_only, lat, lon, angle)
    if not frames:
        sys.exit("No frames to replay" + (" (none below the day/night angle; try --all)" if night_only else ""))

    version = m.metaData.get("version", "?")
    print(f"module   : {module_path}  ({version})")
    print(f"night    : {folder}")
    print(f"frames   : {len(frames)}" + (f" night frames (sun below {angle:g} deg)" if night_only else " (all)")
          + f", {_hms(frames[0][0])} - {_hms(frames[-1][0])}")
    if args.set:
        print("settings : " + ", ".join(args.set))
    print(f"sandbox  : {sandbox}\n")

    os.environ["DATE_NAME"] = night
    outcomes = Counter()
    started = time.time()
    for i, (stamp, path) in enumerate(frames, 1):
        clock.t = _epoch(stamp)
        s.image = cv2.imread(path)
        result = m.meteordetect(params, "postcapture")
        kind = next((p for p in SKIP_PREFIXES if str(result).startswith(p)), "analysed")
        outcomes[kind] += 1
        found = published.get("AS_METEORCOUNT", 0)
        if args.verbose or found:
            print(f"  {_hms(stamp)}  {result}")
        if not args.verbose and i % 50 == 0:
            rate = i / max(1e-6, time.time() - started)
            print(f"  ... {i}/{len(frames)} frames ({rate:.1f}/s)", flush=True)

    # --- report ---------------------------------------------------------------------
    daydir = os.path.join(sandbox, "images", night, "meteors")
    found = []
    for name in sorted(os.listdir(daydir) if os.path.isdir(daydir) else []):
        mm = METEOR_RE.match(name)
        if mm:
            try:
                streaks = json.load(open(os.path.join(daydir, f"meteors-{mm.group(1)}.json")))
            except Exception:
                streaks = []
            found.append((mm.group(1), streaks))

    print(f"\nframes analysed : {outcomes['analysed']}")
    for kind in SKIP_PREFIXES:
        if outcomes[kind]:
            print(f"  skipped       : {outcomes[kind]:4}  {kind.lower()}")
    print(f"\nMETEORS CONFIRMED: {len(found)}")
    for stamp, streaks in found:
        detail = "; ".join(f"len {x.get('length')} px, elong {x.get('elong')}, peak {x.get('peak')}"
                           for x in streaks) or "no metadata"
        print(f"  {_hms(stamp)}  {detail}")

    try:
        vetoed = json.load(open(os.path.join(sandbox, "website", "meteors", "meteors_vetoed.json")))
    except Exception:
        vetoed = []
    tonight = [v for v in vetoed if str(v.get("time", "")) >= frames[0][0]]
    reasons = Counter(v.get("reason", "?") for v in tonight)
    print(f"\nREJECTED: {sum(reasons.values())}" + (f"  ({', '.join(f'{r} {n}' for r, n in reasons.most_common())})"
                                                if reasons else ""))

    if args.compare:
        # The two stamps mean different things. Here it is the frame's capture START
        # (its file name); live it is the wall clock when the module processed that frame,
        # i.e. after the whole exposure plus the processing. So a live stamp belongs to the
        # latest replay stamp BEFORE it, at most one maximum exposure plus a processing
        # margin earlier. Matched one-to-one.
        max_exp = float(s.getSetting("nightmaxautoexposure") or 90000) / 1000.0
        window = max_exp + 150.0
        live = _liveStamps(home, night, live_outputdir)
        mine = [st for st, _ in found]
        free, pairs, only_live = list(mine), [], []
        for ls in live:
            cands = [st for st in free if 0 <= _epoch(ls) - _epoch(st) <= window]
            if cands:
                st = max(cands)
                free.remove(st)
                pairs.append((st, ls))
            else:
                only_live.append(ls)
        print(f"\nCOMPARE with the live night ({len(live)} saved live):")
        print(f"  found by both      : {len(pairs)}  "
              + "  ".join(f"{_hms(st)}~{_hms(ls)}" for st, ls in pairs))
        print(f"  only saved live    : {len(only_live)}  " + " ".join(_hms(x) for x in only_live))
        print(f"  only in the replay : {len(free)}  " + " ".join(_hms(x) for x in free))
        print(f"  (replay = frame capture time, live = when it was processed; paired when the live"
              f" stamp is 0-{int(window)} s later)")

    print(f"\nLook at the results - the marked copies show what was detected:")
    print(f"  {daydir}")
    print(f"  rejected crops: {os.path.join(sandbox, 'website', 'meteors', 'vetoed')}")
    print(f"Done in {time.time() - started:.0f} s. Delete the sandbox when finished:  rm -rf {sandbox}")


if __name__ == "__main__":
    main()
