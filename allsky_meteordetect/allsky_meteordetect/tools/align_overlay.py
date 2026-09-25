#!/usr/bin/env python3
"""Align the Allsky Website's constellation overlay from a plate-solved calibration.

Aligning the overlay is otherwise trial and error: guess overlayWidth/Height, nudge
overlayOffsetLeft/Top, rotate with az, reload, repeat. Allsky's own documentation calls
it "a trial-and-error effort that takes time". This computes all five values - plus the
best-fitting projection - from the fisheye calibration that tools/calibrate_fisheye.py
fitted against real stars, so centre and rotation are as good as the plate solve.

How it maps. The overlay is drawn by virtualsky on a canvas overlayWidth x
overlayHeight, placed overlayOffsetLeft/Top from the image's top-left, in page pixels
for an image shown imageWidth wide. Its zenith-centred projections are
    polar    r = R * z / 90deg                 (equidistant)
    fisheye  r = R * sin(z/2) / sin(45deg)     (equisolid, Allsky's default)
    ortho    r = R * sin(z)
with R = overlayHeight / 2, rotated by az_off = az - 180. The calibration's centre and
rotation carry over exactly; its radial law (r = a1*t + a3*t^3, t = z/90) generally
matches none of the three, so the radius is a least-squares fit over the sky the camera
actually sees, and the tool reports the error that remains. That error is a limit of
virtualsky's projections, not of the calibration.

Usage:
    tools/align_overlay.py                          # compute and print, change nothing
    tools/align_overlay.py --preview FRAME.jpg      # also draw where the overlay puts stars
    tools/align_overlay.py --apply                  # write into the local Website's config
    tools/align_overlay.py --config ~/allsky/config/remote_configuration.json --apply
"""

import argparse
import json
import math
import os
import shutil
import sys
import time

import numpy as np

PROJECTIONS = {
    "polar": lambda z: z / (math.pi / 2),
    "fisheye": lambda z: np.sin(z / 2) / 0.70710678,
    "ortho": lambda z: np.sin(z),
}
KEYS = ("projection", "overlayWidth", "overlayHeight", "overlayOffsetLeft", "overlayOffsetTop", "az")


def _here(*parts):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), *parts)


def _fit(calib, fisheye, image_w, image_h, design_w, mask_path=None, step=24):
    """Best radius per projection over the visible sky. Returns {name: (R, rms, p95, max)}."""
    s = design_w / float(image_w)
    visible = None
    if mask_path and os.path.isfile(mask_path):
        import cv2
        m = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if m is not None:
            if m.shape != (image_h, image_w):
                m = cv2.resize(m, (image_w, image_h), interpolation=cv2.INTER_NEAREST)
            visible = m > 127
    xs, ys = np.meshgrid(np.arange(0, image_w, step), np.arange(0, image_h, step))
    xs, ys = xs.ravel(), ys.ravel()
    if visible is not None:
        keep = visible[ys, xs]
        xs, ys = xs[keep], ys[keep]
    alt = np.array([fisheye.pixel_to_altaz(x, y, calib)[0] for x, y in zip(xs, ys)])
    keep = alt > 0                              # sky only, whatever the mask says
    xs, ys, alt = xs[keep], ys[keep], alt[keep]
    z = np.radians(90.0 - alt)
    r_img = np.hypot(xs - calib["cx"], ys - calib["cy"])
    t = z / (math.pi / 2)
    px_per_deg = (calib["a1"] + 3 * calib["a3"] * t ** 2) / 90.0
    out = {}
    for name, f in PROJECTIONS.items():
        k = f(z)
        R = float(np.dot(k, r_img * s) / np.dot(k, k))
        err = np.abs((R * k / s - r_img) / px_per_deg)
        out[name] = (R, float(np.sqrt(np.mean(err ** 2))), float(np.percentile(err, 95)), float(err.max()))
    return out, float(np.degrees(z).max()), len(xs)


def _checkSite(calib, home):
    """Refuse a calibration made somewhere else: it would give confident, wrong settings."""
    try:
        st = json.load(open(os.path.join(home, "config", "settings.json")))
    except Exception:
        return
    import re
    def num(v):
        m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*([NSEWnsew]?)\s*", str(v or ""))
        if not m:
            return None
        x = float(m.group(1))
        return -x if m.group(2).upper() in ("S", "W") else x
    lat, lon = num(st.get("latitude")), num(st.get("longitude"))
    if lat is None or lon is None or "lat" not in calib:
        return
    if abs(lat - calib["lat"]) > 0.5 or abs(lon - calib["lon"]) > 0.5:
        sys.exit(f"ERROR: this calibration was made at {calib['lat']:.2f}, {calib['lon']:.2f}, but Allsky is "
                 f"set to {lat:.2f}, {lon:.2f}. It belongs to another camera - make your own with "
                 "tools/calibrate_fisheye.py.")


def _settings(calib, R, projection, design_w, image_w):
    s = design_w / float(image_w)
    if calib.get("flip", -1) != -1:
        sys.exit("ERROR: this calibration has east on the RIGHT (flip=+1); virtualsky always draws "
                 "east on the left, so no overlay setting can match it. Flip the image in Allsky instead.")
    return {
        "projection": projection,
        "overlayWidth": int(round(2 * R)),
        "overlayHeight": int(round(2 * R)),
        "overlayOffsetLeft": int(round(calib["cx"] * s - R)),
        "overlayOffsetTop": int(round(calib["cy"] * s - R)),
        "az": round((calib["rot_deg"] + 180.0) % 360.0, 1),
    }


def _preview(calib, fisheye, st, design_w, frame, out_path, maglim=3.2, min_alt=15.0):
    """Mark catalogue stars where the calibration puts them (green circle = the real star)
    and where virtualsky will draw them with these settings (yellow cross)."""
    import cv2
    img = cv2.imread(frame)
    if img is None:
        sys.exit(f"ERROR: cannot read {frame}")
    H, W = img.shape[:2]
    s = design_w / float(W)
    R = st["overlayHeight"] / 2.0
    cxd, cyd = st["overlayOffsetLeft"] + st["overlayWidth"] / 2.0, st["overlayOffsetTop"] + R
    az_off = st["az"] - 180.0
    f = PROJECTIONS[st["projection"]]
    stamp = "".join(ch for ch in os.path.basename(frame) if ch.isdigit())[-14:]
    epoch = time.mktime(time.strptime(stamp, "%Y%m%d%H%M%S"))
    g = time.gmtime(epoch)
    lst = fisheye.local_sidereal_deg((g.tm_year, g.tm_mon, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec), calib["lon"])
    stars = json.load(open(_here("stars.json")))["stars"]
    n = 0
    for ra, dec, mag in stars:
        if mag > maglim:
            continue
        alt, az = fisheye.radec_to_altaz(ra, dec, lst, calib["lat"])
        if alt < min_alt:
            continue
        x0, y0 = fisheye.altaz_to_pixel(alt, az, calib)
        if not (0 <= x0 < W and 0 <= y0 < H):
            continue
        a = math.radians(az - az_off)
        r = R * float(f(math.radians(90.0 - alt)))
        xv, yv = (cxd - r * math.sin(a)) / s, (cyd - r * math.cos(a)) / s
        cv2.circle(img, (int(x0), int(y0)), 26, (0, 255, 0), 3)
        cv2.drawMarker(img, (int(xv), int(yv)), (0, 255, 255), cv2.MARKER_CROSS, 40, 4)
        cv2.line(img, (int(x0), int(y0)), (int(xv), int(yv)), (0, 255, 255), 2)
        n += 1
    cv2.putText(img, "green = star (plate solve)   yellow = constellation overlay with these settings",
                (40, H - 60), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.imwrite(out_path, cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    return n


def main():
    home = os.environ.get("ALLSKY_HOME") or os.path.expanduser("~/allsky")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calibration", default=None,
                    help="calibration.json (default: next to the installed module, else the repository's)")
    ap.add_argument("--config", default=os.path.join(home, "html", "allsky", "configuration.json"),
                    help="Website configuration.json to align (default: the local Website)")
    ap.add_argument("--mask", default=os.path.join(home, "config", "overlay", "images", "meteor_mask.png"),
                    help="mask of the visible sky, to fit only where there are stars to see")
    ap.add_argument("--projection", choices=sorted(PROJECTIONS), help="force a projection (default: best fit)")
    ap.add_argument("--preview", metavar="FRAME", help="draw the result onto a night frame")
    ap.add_argument("--apply", action="store_true", help="write the values into --config (with a backup)")
    args = ap.parse_args()

    calib_path = args.calibration
    if not calib_path:
        # only an INSTALLED calibration: the repository's calibration.json is the author's
        # camera, and using it for yours would give confident, wrong settings
        for cand in (os.path.join(home, "config", "myFiles", "modules", "calibration.json"),
                     os.path.join(home, "scripts", "modules", "calibration.json")):
            if os.path.isfile(cand):
                calib_path = cand
                break
    if not calib_path:
        sys.exit("ERROR: no calibration found - make one with tools/calibrate_fisheye.py and pass it "
                 "with --calibration")
    calib = json.load(open(calib_path))
    _checkSite(calib, home)
    sys.path.insert(0, os.path.dirname(os.path.abspath(calib_path)))
    sys.path.insert(0, _here())
    import allsky_fisheye as fisheye

    if os.path.isfile(args.config):
        doc = json.load(open(args.config))
    elif args.apply:
        sys.exit(f"ERROR: no Website configuration at {args.config} - pass --config")
    else:
        print(f"note: no Website configuration at {args.config}; assuming Allsky's default imageWidth 900")
        doc = {"config": {}}
    cfg = doc.get("config", doc)
    design_w = float(cfg.get("imageWidth") or 900)
    image_w, image_h = int(calib.get("W", 3840)), int(calib.get("H", 2160))

    fits, zmax, nsamp = _fit(calib, fisheye, image_w, image_h, design_w, args.mask)
    best = args.projection or min(fits, key=lambda k: fits[k][1])
    st = _settings(calib, fits[best][0], best, design_w, image_w)

    print(f"calibration : {calib_path}  (rms {calib.get('rms_deg', '?')} deg over {calib.get('n_stars', '?')} stars)")
    print(f"website     : {args.config}  (imageWidth {design_w:g})")
    print(f"visible sky : up to {zmax:.0f} deg from the zenith ({nsamp} sample points)\n")
    print("projection  radius   error rms   95%     max")
    for name, (R, rms, p95, mx) in sorted(fits.items(), key=lambda kv: kv[1][1]):
        mark = "  <- best" if name == best else ""
        print(f"  {name:9} {R:7.1f}   {rms:5.2f}    {p95:5.2f}  {mx:5.2f} deg{mark}")
    print("\nSettings:")
    for k in KEYS:
        print(f"  {k:18} {st[k]!r:>10}   (now {cfg.get(k)!r})")
    print(f"\nExpect stars to sit within about {fits[best][2]:.1f} deg of the overlay over most of the sky "
          f"(worst {fits[best][3]:.1f} deg near the edge). Centre and rotation come from the plate solve; "
          "the rest is the difference between your lens and virtualsky's projection.")

    if args.preview:
        out = os.path.splitext(os.path.basename(args.preview))[0] + "-overlay-check.jpg"
        n = _preview(calib, fisheye, st, design_w, args.preview, out)
        print(f"\npreview     : {out}  ({n} stars; green circle = real star, yellow cross = overlay)")

    if args.apply:
        backup = args.config + time.strftime(".bak-overlay-%Y%m%d-%H%M%S")
        shutil.copy2(args.config, backup)
        cfg.update(st)
        with open(args.config, "w") as fh:
            json.dump(doc, fh, indent=4)
            fh.write("\n")
        print(f"\nwritten     : {args.config}\nbackup      : {backup}")
        print("Reload the Website and switch the constellation overlay on to check it.")
    else:
        print("\nNothing written. Add --apply to write these values.")


if __name__ == "__main__":
    main()
