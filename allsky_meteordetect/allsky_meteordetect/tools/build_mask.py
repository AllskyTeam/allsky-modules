#!/usr/bin/env python3
"""build_mask.py — generate a detection mask for allsky_meteordetect.

The mask marks which part of the all-sky frame is usable sky (white = analyse)
and which part is a permanent obstruction such as trees, a building or the lens
vignette (black = ignore).

Method: obstructions like trees are *persistently dark silhouettes* against the
sky. For every pixel we measure, across many DAYTIME frames, how often it is
markedly darker than the sky (referenced to the bright image centre). Sky is
rarely dark, trees are almost always dark — a far more robust separator than
brightness or texture alone. The illuminated fisheye disk is found via a circle
fit; small enclosed holes (overlay text, birds) are filled, large obstructions
are kept as holes, and a safety margin is eroded for branches that sway.

Example:
    python3 build_mask.py \
        --images ~/allsky/images \
        --nights 20260703 20260704 20260705 \
        --out meteor_mask.png

Then copy meteor_mask.png into your Allsky overlay images folder
(config/overlay/images/) and select it as the module's "Detection Mask".

A building or wall can be as bright as the sky, so it isn't dark.  But averaged over
many frames the sky is smooth, while buildings, trees and poles keep sharp edges.
So the tool also fills the sky outward from the image centre, stopping at those
edges: whatever that doesn't reach and that touches the edge of the sky (where
obstructions rise from the horizon) is an obstruction too.  Turn this off with
--no-edges.
"""
import argparse
import glob
import os
import sys

import cv2
import numpy as np


def daytime(fn, lo, hi):
    base = os.path.basename(fn)          # image-YYYYMMDDHHMMSS.jpg: the hour is at 14-15
    try:
        hh = int(base[14:16])
    except Exception:
        return False
    return lo <= hh <= hi


def gather(images_dir, nights, lo, hi, per_night):
    files = []
    for n in nights:
        cand = sorted(glob.glob(os.path.join(images_dir, n, "image-*.jpg")))
        day = [f for f in cand if daytime(f, lo, hi)]
        if len(day) > per_night:
            idx = np.linspace(0, len(day) - 1, per_night).astype(int)
            day = [day[i] for i in idx]
        files += day
    return files


def edge_obstructions(mean, circ, k_edge, min_len_frac, near_frac=0.04, min_area_frac=0.002, work_width=1280):
    """Obstructions found by their outlines: fill the sky outward from the image centre
    without crossing a persistent edge.  What isn't reached and comes near the edge of
    the disk is an obstruction.  Works at a fixed width, so it behaves the same for
    every camera.  Returns (obstruction mask, edge mask) at full size."""
    FH, FW = mean.shape
    if FW > work_width:
        size = (work_width, int(round(FH * work_width / FW)))
        obs, edges = edge_obstructions(cv2.resize(mean.astype(np.float32), size, interpolation=cv2.INTER_AREA),
                                       cv2.resize(circ, size, interpolation=cv2.INTER_NEAREST),
                                       k_edge, min_len_frac, near_frac, min_area_frac, work_width)
        return (cv2.resize(obs, (FW, FH), interpolation=cv2.INTER_NEAREST),
                cv2.resize(edges, (FW, FH), interpolation=cv2.INTER_NEAREST))
    H, W = mean.shape
    m = mean.astype(np.float32) + 1.0
    flat = m / cv2.GaussianBlur(m, (0, 0), W / 40)          # take out the sky's smooth gradient
    g = cv2.GaussianBlur(flat, (0, 0), max(1.0, W / 1200))
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    centre = grad[int(H * .3):int(H * .7), int(W * .3):int(W * .7)]
    edges = ((grad > k_edge * float(np.median(centre))) & (circ > 0)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(edges, 8)
    long_ = np.zeros_like(edges)
    for i in range(1, n):                                   # long structures only, not text or noise
        if max(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]) >= min_len_frac * W:
            long_[lab == i] = 1
    r = max(1, int(W / 500))
    barrier = cv2.dilate(long_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    free = ((circ > 0) & (barrier == 0)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(free, 4)
    sky_id = lab[H // 2, W // 2]
    rim = (circ > 0) & (cv2.erode(circ, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 3, 2 * r + 3))) == 0)
    rim[0, :] = rim[-1, :] = True                          # a disk larger than the frame ends at the frame
    rim[:, 0] = rim[:, -1] = True
    # Obstructions rise from the horizon, but their own outline often runs along the
    # frame too, so "near the edge" rather than "touching it".
    d = max(3, int(near_frac * W))
    rim = cv2.dilate(rim.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1))) > 0
    # Everything the fill didn't reach, outlines included, in connected pieces: a
    # building's faces and outlines form one piece.  A piece is an obstruction if it
    # comes near the edge (where obstructions rise from the horizon) and encloses a
    # real area: overlay text near the edge is only thin strokes.
    notsky = ((circ > 0) & (lab != sky_id)).astype(np.uint8)
    pn, plab, pst, _ = cv2.connectedComponentsWithStats(notsky, 8)
    min_area = min_area_frac * float((circ > 0).sum())
    obstruction = np.zeros((H, W), np.uint8)
    for i in range(1, pn):
        piece = plab == i
        if not (rim & piece).any():
            continue                                        # inside the sky: a cloud, not an obstruction
        if (piece & (barrier == 0)).sum() < min_area:
            continue                                        # only strokes: text, a wire
        obstruction[piece] = 255
    return obstruction, long_


def build(args):
    files = gather(args.images, args.nights, args.day_start, args.day_end, args.per_night)
    if not files:
        sys.exit("No daytime images found — check --images / --nights / --day-start/--day-end")
    print(f"{len(files)} daytime frames for the stack")

    acc = darkacc = None
    H = W = None
    used = 0
    for f in files:
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        if acc is None:
            H, W = img.shape
            acc = np.zeros((H, W), np.float64)
            darkacc = np.zeros((H, W), np.float64)
        if img.shape != (H, W):
            continue
        fimg = img.astype(np.float64)
        acc += fimg
        cbox = fimg[int(H * 0.30):int(H * 0.70), int(W * 0.30):int(W * 0.70)]
        ref = np.median(cbox)                       # sky reference (centre is always sky)
        darkacc += (fimg < args.dark_ratio * ref).astype(np.float64)
        used += 1
    if used == 0:
        sys.exit("Could not read any images")
    mean = acc / used
    darkfrac = darkacc / used
    meanu8 = mean.astype(np.uint8)
    print(f"{used} frames stacked, {W}x{H}")

    # 1) fisheye disk (illuminated area vs black corners)
    _, disk = cv2.threshold(meanu8, 25, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    disk = cv2.morphologyEx(disk, cv2.MORPH_CLOSE, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(disk, 8)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    blob = np.where(labels == largest, 255, 0).astype(np.uint8)
    cnts, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    (cx, cy), R = cv2.minEnclosingCircle(max(cnts, key=cv2.contourArea))
    R *= args.disk_shrink
    print(f"Fisheye circle: centre=({cx:.0f},{cy:.0f}) R={R:.0f}")
    circ = np.zeros((H, W), np.uint8)
    cv2.circle(circ, (int(cx), int(cy)), int(R), 255, -1)

    # 2) obstruction = persistently dark
    tree = (darkfrac > args.dark_thr).astype(np.uint8) * 255
    tree = cv2.morphologyEx(tree, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    if not args.no_edges:
        outlined, _ = edge_obstructions(mean, circ, args.edge_k, args.edge_len)
        print(f"Outlined obstructions: {100.0 * (outlined > 0).sum() / max(1, (circ > 0).sum()):.1f}% of the disk")
        tree = cv2.bitwise_or(tree, outlined)
    sky = cv2.bitwise_and(circ, cv2.bitwise_not(tree))

    # 3) tidy: largest component, fill only SMALL holes, safety erode
    sky = cv2.morphologyEx(sky, cv2.MORPH_OPEN,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(sky, 8)
    mask = (np.where(labels == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])), 255, 0)
            .astype(np.uint8)) if n > 1 else sky
    circ_area = max(1, int((circ > 0).sum()))
    inv = cv2.bitwise_not(mask)
    nh, labh, sth, _ = cv2.connectedComponentsWithStats(inv, 8)
    fill = np.zeros_like(mask)
    for i in range(1, nh):
        x, y, w, h, area = sth[i]
        border = (x == 0 or y == 0 or x + w == W or y + h == H)
        if (not border) and area < args.hole_frac * circ_area:
            fill[labh == i] = 255
    mask = mask | fill
    e = max(3, int(args.erode_frac * min(H, W)))
    mask = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (e, e)))

    pct = 100.0 * (mask > 0).sum() / circ_area
    print(f"Usable sky: {pct:.1f}% of the fisheye disk")
    cv2.imwrite(args.out, mask)
    print(f"Wrote {args.out}")

    if args.preview:
        prev = cv2.cvtColor(meanu8, cv2.COLOR_GRAY2BGR)
        ov = prev.copy(); ov[mask == 0] = (0, 0, 130)
        prev = cv2.addWeighted(ov, 0.5, prev, 0.5, 0)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(prev, cnts, -1, (0, 255, 0), 5)
        cv2.imwrite(args.preview, cv2.resize(prev, (1280, int(round(1280 * H / W)))))
        print(f"Wrote preview {args.preview}")


def main():
    p = argparse.ArgumentParser(description="Build an Allsky detection mask from daytime images")
    p.add_argument("--images", required=True, help="Allsky images directory (contains per-night folders)")
    p.add_argument("--nights", required=True, nargs="+", help="Night folder names, e.g. 20260703 20260704")
    p.add_argument("--out", default="meteor_mask.png", help="Output mask path")
    p.add_argument("--preview", default="", help="Optional preview image path")
    p.add_argument("--day-start", type=int, default=10, help="First daytime hour to sample (default 10)")
    p.add_argument("--day-end", type=int, default=15, help="Last daytime hour to sample (default 15)")
    p.add_argument("--per-night", type=int, default=15, help="Max frames sampled per night")
    p.add_argument("--dark-ratio", type=float, default=0.55, help="Pixel is 'dark' below this fraction of sky reference")
    p.add_argument("--dark-thr", type=float, default=0.35, help="Dark-frequency above this => obstruction")
    p.add_argument("--disk-shrink", type=float, default=0.95, help="Shrink fisheye radius to drop the vignette ring")
    p.add_argument("--hole-frac", type=float, default=0.01, help="Fill enclosed holes smaller than this fraction of the disk")
    p.add_argument("--erode-frac", type=float, default=0.012, help="Safety erosion as fraction of frame size")
    p.add_argument("--no-edges", action="store_true",
                   help="Don't look for obstructions by their outlines (only by being dark)")
    p.add_argument("--edge-k", type=float, default=5.0, help="An edge is this many times the sky's typical gradient")
    p.add_argument("--edge-len", type=float, default=0.03, help="Edges shorter than this fraction of the width are ignored")
    build(p.parse_args())


if __name__ == "__main__":
    main()
