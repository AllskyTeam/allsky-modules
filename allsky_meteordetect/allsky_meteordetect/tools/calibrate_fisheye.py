#!/usr/bin/env python3
"""Plate-solve an all-sky camera's lens from clear night frames -> calibration.json.

Start from two bright stars you identified in the first frame (--star, twice) - the
reliable way - or from an earlier calibration (--seed), or let it search blind
(experimental). It computes where the catalogue's bright stars stood at each frame's time
and place, and fits a radial lens model by least squares against the stars it can
identify beyond doubt: the brightest point in a shrinking window around each prediction,
taken only when it clearly outshines everything else in that window:

    t = zenith_angle / 90deg ;   r = a1*t + a3*t^3      (a3 = 0: equidistant)
    x = cx + r*sin(rot + flip*az) ;   y = cy - r*cos(rot + flip*az)

Several frames (different hours or nights) are fitted together, which spreads the
stars over more of the sky.

Needs only what Allsky installs (numpy, OpenCV, SciPy) plus allsky_fisheye.py and
stars.json from this repository. Location comes from Allsky's settings, the time from
the frame's file name (Allsky names frames in the Pi's local time).

Usage:
    tools/calibrate_fisheye.py FRAME --list-stars              # which bright stars are up
    tools/calibrate_fisheye.py FRAME --star vega 2828 1213 --star altair 2527 1976
    tools/calibrate_fisheye.py FRAME1 FRAME2 --seed calibration.json --out calibration.json --preview check.jpg
    tools/calibrate_fisheye.py FRAME                      # blind, experimental
"""

import argparse
import json
import math
import os
import re
import sys
import time

import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import allsky_fisheye as F                                    # noqa: E402


# --- inputs ------------------------------------------------------------------------

def _parseLatLon(value):
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*([NSEWnsew]?)\s*", str(value or ""))
    if not m:
        return None
    v = float(m.group(1))
    return -abs(v) if m.group(2).upper() in ("S", "W") else v


def _location(args):
    lat, lon = args.lat, args.lon
    if lat is None or lon is None:
        home = os.environ.get("ALLSKY_HOME") or os.path.expanduser("~/allsky")
        try:
            st = json.load(open(os.path.join(home, "config", "settings.json")))
            lat = lat if lat is not None else st.get("latitude")
            lon = lon if lon is not None else st.get("longitude")
        except Exception:
            pass
    lat, lon = _parseLatLon(lat), _parseLatLon(lon)
    if lat is None or lon is None:
        sys.exit("ERROR: no location - pass --lat/--lon or run where Allsky's settings.json is")
    return lat, lon


def _frameUtc(path):
    """File name 'image-YYYYMMDDHHMMSS' is local time; the system's zone (and DST) decides."""
    m = re.search(r"(\d{14})", os.path.basename(path))
    if not m:
        sys.exit(f"ERROR: no YYYYMMDDHHMMSS timestamp in {path}")
    g = time.gmtime(time.mktime(time.strptime(m.group(1), "%Y%m%d%H%M%S")))
    return (g.tm_year, g.tm_mon, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec)


def _catalogue(utc, lat, lon, maglim, min_alt=8.0):
    """Catalogue stars above min_alt as arrays (alt, az, mag)."""
    stars = json.load(open(os.path.join(HERE, "stars.json")))["stars"]
    lst = F.local_sidereal_deg(utc, lon)
    rows = []
    for ra, dec, mag in stars:
        if mag > maglim:
            continue
        alt, az = F.radec_to_altaz(ra, dec, lst, lat)
        if alt >= min_alt:
            rows.append((alt, az, mag))
    return np.array(rows, dtype=float)


def _skyRegion(gray):
    """Where the lens actually images sky: the large glowing disk, with the dark frame
    corners - and the overlay text that sits on them - left out. Found on a heavily
    smoothed copy, where thin text strokes vanish into the black corners."""
    h, w = gray.shape
    smooth = cv2.GaussianBlur(gray, (0, 0), max(8, w / 150))
    level = 0.35 * float(np.median(smooth[h // 3:2 * h // 3, w // 3:2 * w // 3]))
    sky = (smooth > max(6.0, level)).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(sky, 8)
    if n > 1:
        sky = (lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    margin = max(3, int(w * 0.006))
    return cv2.erode(sky, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * margin + 1,) * 2)) > 0


def _detect(gray, max_n, static=None):
    """Stars as local brightness maxima, brightest first, as an (n, 2) array.

    Local maxima rather than thresholded areas: in a star-rich Milky Way frame any
    threshold low enough for faint stars merges the field into large irregular patches.
    Brightness is the peak above the LOCAL background, which saturated bright stars
    still win. And a star always sits on glowing sky - overlay text sits on the black
    frame corners, a gap between branches is ringed by dark tree - so a maximum only
    counts where the smoothed background is at least half the typical sky level."""
    h, w = gray.shape
    g = gray.astype(np.float32)
    local = cv2.GaussianBlur(g, (0, 0), max(3.0, w / 700))
    diff = cv2.GaussianBlur(g, (0, 0), 1.2) - local                   # star contrast
    wide = cv2.GaussianBlur(g, (0, 0), max(10.0, w / 150))           # sky background
    sky = _skyRegion(gray)
    sky_level = float(np.median(wide[sky])) if sky.any() else float(np.median(wide))
    k = max(5, int(w / 550) | 1)
    peaks = (diff == cv2.dilate(diff, np.ones((k, k), np.uint8))) & (diff > 12.0) \
        & sky & (wide > 0.5 * sky_level)
    ys, xs = np.nonzero(peaks)
    pts = np.column_stack([xs, ys]).astype(float)
    # Rank by contrast through a wider aperture: a long exposure clips every star's peak
    # at the same value, but a bright star keeps a wider halo than a faint one.
    halo = cv2.GaussianBlur(g, (0, 0), max(2.0, w / 960)) - cv2.GaussianBlur(g, (0, 0), max(8.0, w / 240))
    strength = halo[ys, xs]
    if static is not None and len(static) and len(pts):
        # Anything at the same pixel in a frame taken half an hour apart is not a star:
        # the sky has turned by ~7 degrees in between, overlay text and hot pixels have not.
        d, _ = cKDTree(static).query(pts)
        keep = d > max(2.0, w / 1300)
        pts, strength = pts[keep], strength[keep]
    order = np.argsort(-strength)[:max_n]
    return pts[order]


def _companion(path, minutes=30, window=15):
    """Another frame of the same night, about `minutes` away, from the same folder."""
    m = re.search(r"(\d{14})", os.path.basename(path))
    t0 = time.mktime(time.strptime(m.group(1), "%Y%m%d%H%M%S"))
    best = None
    for name in os.listdir(os.path.dirname(os.path.abspath(path))):
        mm = re.fullmatch(r"image-(\d{14})\.(jpg|jpeg|png)", name, re.I)
        if not mm:
            continue
        dt = abs(time.mktime(time.strptime(mm.group(1), "%Y%m%d%H%M%S")) - t0) / 60.0
        if abs(dt - minutes) <= window and (best is None or abs(dt - minutes) < best[0]):
            best = (abs(dt - minutes), os.path.join(os.path.dirname(os.path.abspath(path)), name))
    return best[1] if best else None


# --- model ---------------------------------------------------------------------------

def _project(alt, az, p, flip):
    cx, cy, a1, a3, rot = p
    t = (90.0 - alt) / 90.0
    r = a1 * t + a3 * t ** 3
    ang = np.radians(rot + flip * az)
    return cx + r * np.sin(ang), cy - r * np.cos(ang)


def _hypotheses(cat, dets, W, H, n_blobs=24, n_stars=24, keep=40):
    """Blind search the way astrometry does it: two star <-> blob correspondences fix
    centre, scale and rotation exactly. In complex numbers the equidistant model is a
    similarity,  P = C + A*S,  with S = t*exp(i*flip*az), t = zenith_angle/90deg,
    A = -i*R*exp(i*rot). So every pair of bright blobs against every pair of bright
    catalogue stars gives one (C, A); each is scored by how many other bright stars
    then land on a blob. Returns the best distinct hypotheses (score, cx, cy, R, rot, flip)."""
    score_cat = cat[(cat[:, 2] <= 3.0) & (cat[:, 0] >= 12)]
    pick = cat[(cat[:, 2] <= 3.5) & (cat[:, 0] >= 15)]
    pick = pick[np.argsort(pick[:, 2])][:n_stars]
    blobs = dets[:n_blobs]
    tree = cKDTree(dets[:150])
    thr = 0.008 * W
    P = blobs[:, 0] + 1j * blobs[:, 1]
    found = []
    for flip in (1.0, -1.0):
        S = (90.0 - pick[:, 0]) / 90.0 * np.exp(1j * np.radians(flip * pick[:, 1]))
        Sall = (90.0 - score_cat[:, 0]) / 90.0 * np.exp(1j * np.radians(flip * score_cat[:, 1]))
        for a in range(len(S)):
            for b in range(a + 1, len(S)):
                dS = S[a] - S[b]
                if abs(dS) < 0.05:
                    continue
                for i in range(len(P)):
                    for j in range(len(P)):
                        if i == j:
                            continue
                        A = (P[i] - P[j]) / dS
                        R = abs(A)
                        if not (0.15 * min(W, H) < R < 4.0 * max(W, H)):
                            continue
                        C = P[i] - A * S[a]
                        if not (-0.2 * W < C.real < 1.2 * W and -0.2 * H < C.imag < 1.2 * H):
                            continue
                        Q = C + A * Sall
                        inside = (Q.real >= 0) & (Q.real < W) & (Q.imag >= 0) & (Q.imag < H)
                        if inside.sum() < 6:
                            continue
                        d, _ = tree.query(np.column_stack([Q.real[inside], Q.imag[inside]]))
                        sc = int((d < thr).sum())
                        if sc >= 6:
                            rot = (math.degrees(np.angle(A)) + 90.0) % 360.0
                            found.append((sc, C.real, C.imag, R, rot, flip))
    found.sort(reverse=True)
    distinct = []
    for h in found:
        if all(abs(h[1] - d[1]) > 0.02 * W or abs(h[2] - d[2]) > 0.02 * W or abs(h[3] / d[3] - 1) > 0.05
               or abs((h[4] - d[4] + 180) % 360 - 180) > 3 or h[5] != d[5] for d in distinct):
            distinct.append(h)
        if len(distinct) >= keep:
            break
    return distinct


def _haloMap(gray):
    g = gray.astype(np.float32); w = g.shape[1]
    return cv2.GaussianBlur(g, (0, 0), max(2.0, w / 960)) - cv2.GaussianBlur(g, (0, 0), max(8.0, w / 240))


_NOISE = {}


def _threshold(stars, sky):
    """How bright a star must stand out: 12 times the star map's noise over the sky,
    so it adapts to smooth moonlit images as well as grainy dark ones."""
    key = id(stars)
    if key not in _NOISE:
        v = stars[sky][::7]
        _NOISE[key] = max(3.0, 12.0 * 1.4826 * float(np.median(np.abs(v - np.median(v)))))
    return _NOISE[key]


def _brightPairs(frames, p, flip, radius, dominance=1.35):
    """(alt, az, x, y) for every bright catalogue star whose search window holds ONE clear
    winner: the brightest point there, at least `dominance` times the runner-up.
    Nearest-neighbour matching against a deep catalogue is what went wrong before: in a
    dense Milky Way field a wrong model still finds hundreds of neighbours within a few
    pixels, and the small residual hides it. Bright stars are too sparse to be confused."""
    out = []
    for cat, halo, sky in frames:
        H, W = halo.shape
        x, y = _project(cat[:, 0], cat[:, 1], p, flip)
        r = int(radius)
        for (alt, az, _), px, py in zip(cat, x, y):
            x0, y0, x1, y1 = int(px) - r, int(py) - r, int(px) + r + 1, int(py) + r + 1
            if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                continue
            win = halo[y0:y1, x0:x1].copy()
            win[~sky[y0:y1, x0:x1]] = -1e9
            j = np.unravel_index(np.argmax(win), win.shape)
            best = win[j]
            if best < _threshold(halo, sky):
                continue
            yy, xx = np.ogrid[:win.shape[0], :win.shape[1]]
            win[(yy - j[0]) ** 2 + (xx - j[1]) ** 2 < 36] = -1e9
            if best < dominance * max(float(win.max()), 1.0):
                continue
            out.append((alt, az, x0 + j[1], y0 + j[0]))
    return np.array(out)


def _fitPairs(pairs, p0, flip, free_a3):
    def resid(q):
        pp = (q[0], q[1], q[2], q[3] if free_a3 else p0[3], q[4])
        x, y = _project(pairs[:, 0], pairs[:, 1], pp, flip)
        return np.concatenate([x - pairs[:, 2], y - pairs[:, 3]])
    q = list(least_squares(resid, np.asarray(p0, float), loss="soft_l1", f_scale=6.0).x)
    if not free_a3:
        q[3] = p0[3]
    return q


def _refine(frames, p, flip, W, verbose=False):
    """Shrink the search window step by step; the cubic term is freed once the
    equidistant part has settled. Returns (params, pairs) or (None, pairs)."""
    s = W / 3840.0
    p = list(p)
    pairs = np.empty((0, 4))
    for it, rad in enumerate((100, 80, 62, 48, 38, 30, 24, 20)):
        pairs = _brightPairs(frames, p, flip, rad * s)
        if len(pairs) < 8:
            return None, pairs
        p = _fitPairs(pairs, p, flip, free_a3=(it >= 2))
        if verbose:
            x, y = _project(pairs[:, 0], pairs[:, 1], p, flip)
            e = np.hypot(x - pairs[:, 2], y - pairs[:, 3])
            print(f"  window {rad * s:5.0f} px: {len(pairs):3} bright stars, RMS {np.sqrt(np.mean(e ** 2)):5.1f} px")
    return p, pairs


def _stats(pairs, p, flip):
    """RMS residual in px and in degrees (each pair at its own plate scale)."""
    x, y = _project(pairs[:, 0], pairs[:, 1], p, flip)
    e = np.hypot(x - pairs[:, 2], y - pairs[:, 3])
    t_ = (90.0 - pairs[:, 0]) / 90.0
    deg = e / ((p[2] + 3 * p[3] * t_ ** 2) / 90.0)
    return float(np.sqrt(np.mean(e ** 2))), float(np.sqrt(np.mean(deg ** 2))), len(e)


# Bright stars a user can identify and click on, for the two-star start: RA, Dec (J2000).
NAMED = {
    "sirius": (101.287, -16.716), "canopus": (95.988, -52.696), "arcturus": (213.915, 19.182),
    "vega": (279.234, 38.784), "capella": (79.172, 45.998), "rigel": (78.634, -8.202),
    "procyon": (114.825, 5.225), "betelgeuse": (88.793, 7.407), "altair": (297.696, 8.868),
    "aldebaran": (68.980, 16.509), "antares": (247.352, -26.432), "spica": (201.298, -11.161),
    "pollux": (116.329, 28.026), "fomalhaut": (344.413, -29.622), "deneb": (310.358, 45.280),
    "regulus": (152.093, 11.967), "castor": (113.650, 31.888), "polaris": (37.955, 89.264),
    "dubhe": (165.932, 61.751), "alkaid": (206.885, 49.313), "mirfak": (51.081, 49.861),
    "alpheratz": (2.097, 29.090), "hamal": (31.793, 23.463), "alphecca": (233.672, 26.715),
}


def _seedFromStars(stars, utc, lat, lon, flip):
    """Two clicked stars fix centre, scale and rotation: P = C + A*S (see _hypotheses)."""
    lst = F.local_sidereal_deg(utc, lon)
    (n1, x1, y1), (n2, x2, y2) = stars
    S = []
    for n in (n1, n2):
        ra, dec = NAMED[n.lower()]
        alt, az = F.radec_to_altaz(ra, dec, lst, lat)
        if alt < 5:
            sys.exit(f"ERROR: {n} was below the horizon at this frame's time")
        S.append((90.0 - alt) / 90.0 * np.exp(1j * math.radians(flip * az)))
    A = (complex(x1, y1) - complex(x2, y2)) / (S[0] - S[1])
    C = complex(x1, y1) - A * S[0]
    return [C.real, C.imag, abs(A), 0.0, (math.degrees(np.angle(A)) + 90.0) % 360.0]


# --- main ------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames", nargs="+", help="clear night frames named image-YYYYMMDDHHMMSS.jpg")
    ap.add_argument("--star", nargs=3, action="append", metavar=("NAME", "X", "Y"),
                    help="a bright star you identified in the FIRST frame and its pixel position; give "
                         "it twice. Known names: " + ", ".join(sorted(NAMED)))
    ap.add_argument("--seed", help="start from an existing calibration.json instead")
    ap.add_argument("--lat", help="latitude, e.g. 48.136N (default: Allsky settings)")
    ap.add_argument("--lon", help="longitude, e.g. 14.39E (default: Allsky settings)")
    ap.add_argument("--out", help="write calibration.json here")
    ap.add_argument("--preview", help="write a check image of the first frame here")
    ap.add_argument("-v", "--verbose", action="store_true", help="show each refinement step")
    ap.add_argument("--list-stars", action="store_true",
                    help="list the named bright stars above the horizon at the first frame's time, "
                         "to choose two for --star, and stop")
    args = ap.parse_args()
    lat, lon = _location(args)
    if args.list_stars:
        utc = _frameUtc(args.frames[0])
        lst = F.local_sidereal_deg(utc, lon)
        compass = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
        rows = []
        for name, (ra, dec) in NAMED.items():
            alt, az = F.radec_to_altaz(ra, dec, lst, lat)
            if alt >= 20:
                rows.append((alt, az, name))
        print(f"Bright stars at least 20 deg up at {os.path.basename(args.frames[0])} "
              f"({lat:.2f}, {lon:.2f}). Pick two far apart, not too low:")
        for alt, az, name in sorted(rows, reverse=True):
            print(f"  {name:11} altitude {alt:4.0f} deg   azimuth {az:4.0f} deg ({compass[int((az + 22.5) % 360 // 45)]})")
        print("Then read each one's pixel position in an image viewer and run with "
              "--star NAME X Y --star NAME X Y.")
        return
    started = time.time()

    frames, utcs, size, blind = [], [], None, None
    for path in args.frames:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            sys.exit(f"ERROR: cannot read {path}")
        if size and img.shape != size:
            sys.exit("ERROR: all frames must have the same size")
        size = img.shape
        utc = _frameUtc(path)
        cat = _catalogue(utc, lat, lon, maglim=3.0, min_alt=15.0)
        frames.append((cat, _haloMap(img), _skyRegion(img)))
        utcs.append(utc)
        print(f"{os.path.basename(path)}: {len(cat)} bright catalogue stars above 15 deg")
        if blind is None and not args.star and not args.seed:
            comp, static = _companion(path), None
            if comp is not None:
                cimg = cv2.imread(comp, cv2.IMREAD_GRAYSCALE)
                if cimg is not None and cimg.shape == size:
                    static = _detect(cimg, 3000)
            blind = (_catalogue(utc, lat, lon, maglim=4.0), _detect(img, 550, static=static))
    H, W = size

    # A starting point: two identified stars, an earlier calibration, or a blind search.
    if args.star:
        if len(args.star) != 2:
            sys.exit("ERROR: give --star exactly twice")
        for n, _, _ in args.star:
            if n.lower() not in NAMED:
                sys.exit(f"ERROR: unknown star {n!r}; known: {', '.join(sorted(NAMED))}")
        stars = [(n, float(x), float(y)) for n, x, y in args.star]
        starts = [(_seedFromStars(stars, utcs[0], lat, lon, f), f) for f in (-1.0, 1.0)]
        print("start: two identified stars")
    elif args.seed:
        c = json.load(open(args.seed))
        starts = [([c["cx"], c["cy"], c["a1"], c.get("a3", 0.0), c["rot_deg"]], float(c["flip"]))]
        print(f"start: {args.seed}")
    else:
        hyps = _hypotheses(blind[0], blind[1], W, H)
        starts = [([cx, cy, R, 0.0, rot], flip) for _, cx, cy, R, rot, flip in hyps]
        print(f"start: blind search, {len(starts)} candidates "
              "(experimental - two identified stars are far more reliable)")

    best = None
    for seed, flip in starts:
        p, pairs = _refine(frames, seed, flip, W, verbose=args.verbose)
        if p is None:
            continue
        rms_deg = _stats(pairs, p, flip)[1]
        if rms_deg < 0.75 and (best is None or len(pairs) > len(best[1])):   # degrees: lens scales vary
            best = (p, pairs, flip)
    if best is None:
        sys.exit("ERROR: no consistent solution - use clear frames, or identify two bright stars with --star")
    p, pairs, flip = best
    rms_px, rms_deg, n = _stats(pairs, p, flip)
    print(f"solution: {n} bright stars, RMS {rms_px:.2f} px = {rms_deg:.3f} deg; centre {p[0]:.1f},{p[1]:.1f}, "
          f"rotation {p[4] % 360:.2f} deg, {'east left' if flip < 0 else 'east right'}")

    calib = {
        "model": "cubic_equidistant",
        "cx": round(p[0], 3), "cy": round(p[1], 3), "a1": round(p[2], 4), "a3": round(p[3], 4),
        "R_horizon": round(p[2] + p[3], 2), "rot_deg": round(p[4] % 360, 4), "flip": int(flip),
        "rms_px": round(rms_px, 2), "rms_deg": round(rms_deg, 3), "n_stars": n,
        "method": "bright unambiguous stars, shrinking search windows",
        "frame_utc": "%04d-%02d-%02d %02d:%02d:%02d" % tuple(utcs[0][:6]),
        "calibrated_from": [os.path.basename(f) for f in args.frames],
        "lat": lat, "lon": lon, "W": W, "H": H,
    }
    print("\n" + json.dumps(calib, indent=2))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(calib, fh, indent=2)
            fh.write("\n")
        print(f"\nwritten: {args.out}")

    if args.preview:
        img = cv2.imread(args.frames[0])
        cat = frames[0][0]
        x, y = _project(cat[:, 0], cat[:, 1], p, flip)
        s = W / 3840.0
        for px, py in zip(x, y):
            cv2.circle(img, (int(px), int(py)), int(24 * s), (0, 255, 0), 3)
        for _, _, dx, dy in _brightPairs(frames[:1], p, flip, 20 * s):
            cv2.drawMarker(img, (int(dx), int(dy)), (0, 255, 255), cv2.MARKER_TILTED_CROSS, int(20 * s), 2)
        cv2.drawMarker(img, (int(p[0]), int(p[1])), (255, 0, 255), cv2.MARKER_CROSS, int(60 * s), 3)
        cv2.imwrite(args.preview, img)
        print(f"preview: {args.preview}  (green = catalogue star, yellow = star it matched, magenta = zenith)")
    print(f"done in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
