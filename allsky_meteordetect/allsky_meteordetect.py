""" allsky_meteordetect.py

Temporal meteor detection module for Allsky.
https://github.com/AllskyTeam/allsky

Unlike the built-in single-frame detector, this module works on the DIFFERENCE
between consecutive frames (removes stars / static clouds), finds streaks via
connected-components + PCA, and classifies them across neighbouring frames:

    * a streak that continues a PROGRESSING track   -> satellite / aircraft (rejected)
    * a streak that repeats at the SAME location     -> disappearance of an already
                                                        reported meteor (de-duplicated)
    * an isolated, transient streak                  -> meteor candidate (saved)

The saved gallery image keeps the TRUE COLOURS of the meteor untouched; the optional
debug image draws brackets AROUND the streak, never over it, so the meteor's colour
(green = Mg/O, yellow = Na/Fe, ...) is preserved.
"""
import allsky_shared as s
import os
import sys
import re
import json
import time
import shutil
import subprocess
import cv2
import numpy as np

metaData = {
    "name": "Meteor Detection (temporal)",
    "description": "Detects meteors via frame differencing and separates them from satellites/aircraft",
    "version": "v0.5.9",
    "events": [
        "night"
    ],
    "experimental": "false",
    "group": "Image Analysis",
    "centersettings": "false",
    "module": "allsky_meteordetect",
    "extradatafilename": "allsky_meteordetect.json",
    "extradata": {
        "values": {
            "AS_METEORCOUNT": {"name": "${METEORCOUNT}", "format": "", "sample": "", "group": "Meteors", "description": "Meteors confirmed on this frame", "type": "number"},
            "AS_METEORIMAGE": {"name": "${METEORIMAGE}", "format": "", "sample": "", "group": "Meteors", "description": "File name of the meteor image saved on this frame", "type": "string"},
            "AS_METEORIMAGEPATH": {"name": "${METEORIMAGEPATH}", "format": "", "sample": "", "group": "Meteors", "description": "Full path of the meteor image saved on this frame", "type": "string"},
            "AS_METEORIMAGEURL": {"name": "${METEORIMAGEURL}", "format": "", "sample": "", "group": "Meteors", "description": "WebUI URL of that meteor's thumbnail", "type": "string"},
            "AS_METEORMOVING": {"name": "${METEORMOVING}", "format": "", "sample": "", "group": "Meteors", "description": "Streaks rejected as satellites/aircraft on this frame", "type": "number"},
            "AS_METEORVETOED": {"name": "${METEORVETOED}", "format": "", "sample": "", "group": "Meteors", "description": "Streaks rejected by the other filters on this frame", "type": "number"}
        }
    },
    "arguments": {
        "mask": "meteor_mask.png",
        "min_length": "50",
        "diff_thr": "22",
        "min_elong": "5.0",
        "max_area": "6000",
        "cloud_frac": "2.0",
        "edge_feather": "35",
        "dash_filter": "true",
        "dash_runs": "10",
        "dash_min_len": "120",
        "frag_filter": "false",
        "frag_min": "5",
        "frag_min_len": "120",
        "edge_filter": "false",
        "edge_margin": "50",
        "edge_max_elong": "10",
        "edge_min_len": "80",
        "satellite_filter": "true",
        "scint_guard": "true",
        "scint_max": "8",
        "repeat_filter": "true",
        "repeat_k": "3",
        "trail_filter": "true",
        "trail_tol": "12",
        "star_filter": "true",
        "star_radius": "16",
        "star_maglim": "5.0",
        "upload_remote": "true",
        "outputdir": "",
        "save_webui": "true",
        "save_marked": "true",
        "save_vetoed": "true",
        "save_debug": "false",
        "debug": "false"
    },
    "argumentdetails": {
        "mask": {
            "required": "false",
            "description": "Detection Mask",
            "help": "Image mask in the overlay images folder. White = sky to analyse, black = ignore (trees/horizon). Build one with the supplied mask tool.",
            "type": {"fieldtype": "image"}
        },
        "min_length": {
            "required": "true",
            "description": "Min Streak Length (px)",
            "help": "Minimum length of a detected streak in pixels. Short compact blobs near the fisheye edge are defocused stars, not meteors; keep this around 50.",
            "type": {"fieldtype": "spinner", "min": 5, "max": 500, "step": 1}
        },
        "diff_thr": {
            "required": "true",
            "description": "Difference Threshold",
            "help": "Brightness increase over the previous frame for a pixel to count as 'new'. Higher = fewer, brighter detections.",
            "type": {"fieldtype": "spinner", "min": 5, "max": 100, "step": 1}
        },
        "min_elong": {
            "required": "false",
            "description": "Min Elongation",
            "help": "Length/width ratio. Low values pass blobs (defocused stars, cloud); high values require a thin streak. Real meteors here measured >=7; barely-elongated (~4) detections are defocused stars, so keep this around 5.",
            "type": {"fieldtype": "spinner", "min": 1.5, "max": 10, "step": 0.5}
        },
        "max_area": {
            "required": "false",
            "description": "Max Streak Area (px)",
            "help": "Larger connected regions are treated as cloud brightening, not meteors",
            "type": {"fieldtype": "spinner", "min": 500, "max": 50000, "step": 100}
        },
        "cloud_frac": {
            "required": "false",
            "description": "Cloud Skip (%)",
            "help": "If more than this percentage of the sky changed since the last frame the frame is skipped as cloudy",
            "type": {"fieldtype": "spinner", "min": 0.2, "max": 20, "step": 0.1}
        },
        "edge_feather": {
            "required": "false",
            "description": "Mask Edge Feather (px)",
            "help": "Soft fade of the mask edge so the mask boundary itself is not detected as a streak",
            "type": {"fieldtype": "spinner", "min": 0, "max": 151, "step": 2}
        },
        "dash_filter": {
            "required": "false",
            "description": "Reject Dashed Trails",
            "help": "Reject a long streak that is broken into many bright/dark segments along its length. A meteor is one continuous streak; a tumbling satellite or a strobing aircraft leaves a dashed trail. Catches a single-frame satellite/aircraft that the cross-frame filter cannot see.",
            "type": {"fieldtype": "checkbox"}
        },
        "dash_runs": {
            "required": "false",
            "description": "Dash Segments",
            "help": "How many separate bright segments along a streak's axis mark it as a dashed (satellite/aircraft) trail. A real meteor scores <=5 here; a dashed satellite scored 19. Keep at 10 for a wide safety margin.",
            "type": {"fieldtype": "spinner", "min": 4, "max": 40, "step": 1}
        },
        "dash_min_len": {
            "required": "false",
            "description": "Dash Min Length (px)",
            "help": "Only test streaks at least this long for a dashed pattern. Short streaks are exempt so a genuine short meteor is never dash-vetoed (satellite/aircraft trails are long).",
            "type": {"fieldtype": "spinner", "min": 40, "max": 500, "step": 10}
        },
        "frag_filter": {
            "required": "false",
            "description": "Reject Fragmented Trails (arm)",
            "help": "Reject a streak that is only the bright head of a longer DASHED trail whose faint segments were split into separate sub-threshold fragments (a satellite glint the dash veto misses because it measures only the continuous head). Counts diff components lying collinear beyond the streak's ends. OFF by default = shadow mode: the metric is measured and logged (frag-shadow in meteors_vetoed.json, frag_n on each saved meteor) but nothing is vetoed. Before turning it on, check what your real meteors score: here real meteors reached 4, so keep 'Fragment Segments' at 5 or more.",
            "type": {"fieldtype": "checkbox"}
        },
        "frag_min": {
            "required": "false",
            "description": "Fragment Segments",
            "help": "How many collinear diff fragments beyond a streak's ends mark it as the head of a fragmented dashed trail. Real meteors are NOT always 0: over two months of saved detections here they scored up to 4 (stars and noise that happen to lie on the line), while satellite trails scored 3 to 11. At 5 the filter caught the two clearest satellite trails and no real meteor; at 3 it would also have rejected three real meteors.",
            "type": {"fieldtype": "spinner", "min": 2, "max": 20, "step": 1}
        },
        "frag_min_len": {
            "required": "false",
            "description": "Fragment Min Length (px)",
            "help": "Only test streaks at least this long for a collinear fragmented tail. Short streaks are exempt.",
            "type": {"fieldtype": "spinner", "min": 40, "max": 500, "step": 10}
        },
        "edge_filter": {
            "required": "false",
            "description": "Reject Edge Glow (arm)",
            "help": "Reject a long, fat streak whose BOTH ends sit on the border of the detection mask: horizon or lens-rim glow leaking through the feathered edge, which a changing sky turns into a frame difference. Real streaks that reach the border cross it - one end inside - and are thin. OFF by default = shadow mode: matches are logged as edge-shadow in meteors_vetoed.json and every saved meteor records edge_d (its farther end's distance to the border), but nothing is rejected. Here, over two months, it matched 9 detections, all edge glow, and no real streak.",
            "type": {"fieldtype": "checkbox"}
        },
        "edge_margin": {
            "required": "false",
            "description": "Edge Margin (px)",
            "help": "Both ends of a streak closer than this to the mask border count as 'on the border'. Stable here between 50 and 60 px on a 3840 px wide image.",
            "type": {"fieldtype": "spinner", "min": 5, "max": 300, "step": 5}
        },
        "edge_max_elong": {
            "required": "false",
            "description": "Edge Glow Max Elongation",
            "help": "Only streaks fatter than this (length/width below it) can be edge glow. Edge glow here measured 5 to 8; every real streak touching the border measured over 10.",
            "type": {"fieldtype": "spinner", "min": 3, "max": 30, "step": 0.5}
        },
        "edge_min_len": {
            "required": "false",
            "description": "Edge Glow Min Length (px)",
            "help": "Only streaks at least this long can be edge glow. Keeps a short, bright meteor that vanishes behind a tree at the border from being rejected.",
            "type": {"fieldtype": "spinner", "min": 20, "max": 500, "step": 10}
        },
        "satellite_filter": {
            "required": "false",
            "description": "Reject Satellites/Aircraft",
            "help": "Discard streaks that continue a moving track across consecutive frames",
            "type": {"fieldtype": "checkbox"}
        },
        "scint_guard": {
            "required": "false",
            "description": "Scintillation Guard",
            "help": "On very clear nights star twinkling produces many tiny streaks. If a frame has more than 'Scintillation Max' streaks, keep only a clearly dominant one (a real bright meteor) and otherwise skip the frame.",
            "type": {"fieldtype": "checkbox"}
        },
        "scint_max": {
            "required": "false",
            "description": "Scintillation Max",
            "help": "How many streaks in a single frame count as a scintillation-dominated (noisy) frame",
            "type": {"fieldtype": "spinner", "min": 3, "max": 50, "step": 1}
        },
        "repeat_filter": {
            "required": "false",
            "description": "Reject Recurring Positions",
            "help": "Reject a streak whose position keeps producing detections across several frames (scintillation, bloom, a trailed star, a fixed reflection). A real meteor appears once, so it is never caught by this.",
            "type": {"fieldtype": "checkbox"}
        },
        "repeat_k": {
            "required": "false",
            "description": "Recurrence Frames",
            "help": "How many earlier frames must show a detection at the same spot (within ~55 px, last ~25 min) for it to count as a recurring artifact. A meteor gives at most 2, so keep this at 3 or higher.",
            "type": {"fieldtype": "spinner", "min": 2, "max": 10, "step": 1}
        },
        "trail_filter": {
            "required": "false",
            "description": "Reject Star-Trail Orientation",
            "help": "Reject a streak whose orientation matches the local diurnal star-trail direction (computed from the fisheye calibration). Long/bright fireballs are exempt. Needs allsky_fisheye.py + calibration.json; silently skipped otherwise.",
            "type": {"fieldtype": "checkbox"}
        },
        "trail_tol": {
            "required": "false",
            "description": "Star-Trail Tolerance (deg)",
            "help": "How close a streak's angle must be to the local star-trail direction to be rejected. Larger = stricter (rejects more), but risks discarding a real meteor that happens to run parallel to the star trails.",
            "type": {"fieldtype": "spinner", "min": 4, "max": 30, "step": 1}
        },
        "star_filter": {
            "required": "false",
            "description": "Reject Bright-Star Scintillation",
            "help": "Reject a short streak that sits on a catalogue bright star: on clear nights a star twinkles brighter between frames, so the frame difference shows a compact blob at the star's position that mimics a meteor. Long/bright fireballs are exempt. Needs allsky_fisheye.py + calibration.json + stars.json; silently skipped otherwise.",
            "type": {"fieldtype": "checkbox"}
        },
        "star_radius": {
            "required": "false",
            "description": "Star-Match Radius (px)",
            "help": "How close a streak's centre must be to a projected catalogue star to count as that star scintillating. Size it to the calibration accuracy (RMS ~4-6 px) plus a few px of blob offset; too large risks vetoing a real meteor that happens to pass over a star.",
            "type": {"fieldtype": "spinner", "min": 6, "max": 40, "step": 1}
        },
        "star_maglim": {
            "required": "false",
            "description": "Star Magnitude Limit",
            "help": "Only stars brighter than this visual magnitude are used for the veto. Fainter stars rarely brighten enough to trigger a detection, and including them raises the chance of vetoing a real meteor. 5.0 covers the naked-eye bright stars that actually scintillate.",
            "type": {"fieldtype": "spinner", "min": 2.0, "max": 6.0, "step": 0.5}
        },
        "upload_remote": {
            "required": "false",
            "description": "Upload to Remote Website",
            "help": "If the remote website is enabled, upload each meteor image + thumbnail to it (folder 'meteors')",
            "type": {"fieldtype": "checkbox"}
        },
        "outputdir": {
            "required": "false",
            "description": "Output Folder",
            "help": "Where meteor images are written (with a thumbnails/ subfolder). Empty = website meteors folder.",
            "type": {"fieldtype": "text"}
        },
        "save_webui": {
            "required": "false",
            "description": "Browse in the Allsky WebUI",
            "help": "Also file each meteor under images/<day>/meteors/ (image, marked copy and a per-meteor json sidecar, with the thumbnails in the sibling images/<day>/meteorsthumbnails/) so the Allsky WebUI 'Meteors' page can browse it day by day. The website folder above is still written either way — the remote upload and the per-night charts read that one.",
            "type": {"fieldtype": "checkbox"}
        },
        "save_marked": {
            "required": "false",
            "description": "Save Marked Copy",
            "help": "Save a second copy with brackets AROUND the streak (never over it), plus its thumbnail. The gallery image always stays untouched. Needed for the WebUI's 'Use Marked Meteors' option, which links the marked thumbnail without checking that it exists.",
            "type": {"fieldtype": "checkbox"}
        },
        "save_vetoed": {
            "required": "false",
            "description": "Save Rejected-Candidate Crops",
            "help": "Save a small crop around every REJECTED streak (into a 'vetoed/' subfolder) and record it in meteors_vetoed.json. These are the negative examples (aircraft / satellite / artifact) — labelling them on the website builds the training set for a future classifier. Uploaded to the remote 'meteors/vetoed' folder when remote upload is on.",
            "type": {"fieldtype": "checkbox"}
        },
        "save_debug": {
            "required": "false",
            "description": "Save Marked Copy (legacy)",
            "help": "Superseded by 'Save Marked Copy' above; kept so an older saved config still forces the marked copy on.",
            "tab": "Debug",
            "type": {"fieldtype": "checkbox"}
        },
        "debug": {
            "required": "false",
            "description": "Enable stage debug images",
            "help": "Write intermediate images to the allsky tmp debug folder",
            "tab": "Debug",
            "type": {"fieldtype": "checkbox"}
        }
    },
    "changelog": {
        "v0.1.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": "Initial temporal detector (frame diff + PCA streaks + neighbour-frame classification)"
            }
        ],
        "v0.2.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Record meteor peak brightness + date-based active-shower context",
                    "Optional geometric radiant matching via a plate-solved fisheye calibration (allsky_fisheye.py + calibration.json) — attributes each meteor to the shower whose radiant lies on its great circle"
                ]
            }
        ],
        "v0.3.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Recurrence veto: reject a streak whose position keeps firing across several frames (scintillation / bloom / trailed star / fixed reflection). A real meteor appears once, so it is never affected.",
                    "Star-trail veto: reject a streak whose orientation matches the local diurnal star-trail tangent (from the fisheye calibration); long/bright fireballs are exempt.",
                    "Log streak geometry (centroid + endpoints) with each confirmed meteor, and write a rolling meteors_vetoed.json of rejected streaks + reason for tuning/validation."
                ]
            }
        ],
        "v0.4.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Dashed-trail veto: reject a long streak broken into many bright/dark segments along its axis (a tumbling satellite / strobing aircraft). Catches a single-frame satellite pass the cross-frame filter cannot see. Tuned on real data — a dashed satellite scored 19 segments, real meteors <=5.",
                    "Raise default min elongation 4.0 -> 5.0 and min length 40 -> 50: barely-elongated short blobs near the fisheye edge are defocused stars, not meteors. Validated against a clear night where the two real meteors measured elongation 7-8 while the false positives sat right on the old 4.0/40 floors."
                ]
            }
        ],
        "v0.4.1": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Fragmented-trail metric (frag_filter, SHADOW by default): the v0.4.0 dash veto measures only a streak's continuous head, so a satellite glint whose dashed tail is split into separate sub-threshold fragments slips through as a lone bright head. This counts difference components lying collinear (small perpendicular residual) beyond the streak's endpoints — a real meteor has none, the validated 2026-07-13 glint scored 3. Measured on the DIFFERENCE image so static stars cancel and cannot be miscounted as fragments.",
                    "Ships in shadow mode: frag_filter off = the metric is logged (frag-shadow entries in meteors_vetoed.json, frag_n/frag_ext on every saved meteor) but nothing is vetoed. Arm only after real meteors confirm they score 0."
                ]
            }
        ],
        "v0.4.2": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Fix remote upload of meteors.json: the per-hit upload loop reused the image's filename as the remote destination name for all three files, so the log was uploaded UNDER the image name and the remote meteors.json was never refreshed — the remote gallery and per-night chart stayed frozen on the first night ever detected. Each file now keeps its own remote name (image, thumbnail, meteors.json)."
                ]
            }
        ],
        "v0.4.3": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Save rejected-candidate crops (save_vetoed, default on): every vetoed streak — including satellites/aircraft caught by the moving-track filter — is now saved as a small labelling crop in a 'vetoed/' subfolder and recorded (thumb field) in meteors_vetoed.json, then uploaded to the remote 'meteors/vetoed' folder. These are the NEGATIVE examples; labelling them on the website (aircraft / satellite / artifact) builds the training set for a future classifier. The remote 'meteors/vetoed' folder must exist (upload.sh does not create directories)."
                ]
            }
        ],
        "v0.4.4": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Bright-star scintillation veto (star_filter, default on): reject a short streak whose centre sits within star_radius px (default 16) of a projected catalogue star brighter than star_maglim (default 5.0). On clear nights a bright star twinkles brighter between frames, producing a compact frame-difference blob at the star's position that mimics a meteor's appear/vanish signature. The star positions come from a bundled Hipparcos subset (stars.json, Vmag<6) projected with the fisheye calibration for the frame's time; long/bright fireballs (>130 px) are exempt. Silently skipped if allsky_fisheye.py / calibration.json / stars.json are absent. Logged as reason 'star' in meteors_vetoed.json.",
                    "Refined the fisheye calibration against a deep Hipparcos catalogue seeded from the previous fit (RMS ~4 px over 317 stars across 3 clear-night frames); tightened a1, which had pushed mid/edge stars ~15 px outward and would have blunted the star veto."
                ]
            }
        ],
        "v0.5.0": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Allsky WebUI meteor browsing (save_webui, default on): every saved meteor is additionally filed under images/<day>/meteors/ with its thumbnail, marked copy and a per-image json sidecar, which is the layout the WebUI's 'Meteors' page (AllskyTeam/allsky#5227) browses. The website folder is still written unchanged — the remote upload and the per-night charts keep reading the rolling meteors.json there.",
                    "Per-image json sidecar meteors-<stamp>.json next to each image, holding just that image's streaks. Same fields as the rolling log (length, angle, elong, peak, p1, p2, frag_n, frag_ext, showers, radiant), because the WebUI reads them one file at a time rather than scanning a rolling log.",
                    "Marked copy promoted out of Debug (save_marked, default on) and its thumbnail is now written too: the WebUI's 'Use Marked Meteors' option links thumbnails/<name>-marked.jpg without checking that it exists, so a missing one renders as a broken image. save_debug is kept as a legacy alias that still forces the marked copy on.",
                    "The day folder is pinned when a candidate is stashed, not when it is confirmed a frame later, so a meteor caught either side of the DATE_NAME rollover cannot land in the wrong night's folder."
                ]
            },
            {
                "author": "Carlos Gil",
                "authorurl": "https://github.com/ea1ii",
                "changes": [
                    "Original idea and first implementation of saving into images/<day>/meteors/ with a per-image json, in PR #1. This release keeps that layout; it derives the day folder from DATE_NAME rather than from the file name, so a meteor after midnight stays with the night it belongs to."
                ]
            }
        ],
        "v0.5.1": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "WebUI thumbnails move from images/<day>/meteors/thumbnails/ to the sibling images/<day>/meteorsthumbnail/, matching how Allsky 2025 stores keogram and startrails thumbnails (keogramthumbnail/, startrailsthumbnail/) and where the WebUI's Meteors page looks for them. Requested on AllskyTeam/allsky#5227. The website meteors/thumbnails/ folder is unchanged: the website gallery and the remote upload read that one.",
                    "tools/backfill_webui.py files thumbnails into the new folder too, and moves any left in the old one."
                ]
            }
        ],
        "v0.5.2": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "WebUI thumbnail folder renamed to images/<day>/meteorsthumbnails/ (plural, like the day's own thumbnails/), as settled on AllskyTeam/allsky#5227; the WebUI's meteors.php and functions.php read that name. v0.5.1's meteorsthumbnail/ was a guess at the naming.",
                    "tools/backfill_webui.py moves thumbnails from both earlier locations - meteors/thumbnails/ (v0.5.0) and meteorsthumbnail/ (v0.5.1)."
                ]
            }
        ],
        "v0.5.3": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Display name is now 'Meteor Detection (temporal)'. Allsky's built-in allsky_meteor.py is also called 'Meteor Detection', so the Module Manager listed two identical entries and users could not tell which one they had added."
                ]
            }
        ],
        "v0.5.4": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Publish results as real Allsky variables: AS_METEORCOUNT, AS_METEORIMAGE, AS_METEORIMAGEPATH, AS_METEORIMAGEURL, AS_METEORMOVING, AS_METEORVETOED, declared in metaData['extradata'] and written with saveExtraData. Until now they were only environment variables, which reach the overlay of the same frame but not the variable list or MQTT on Allsky 2025. The first four match the built-in meteor module's names, so an overlay or Home Assistant feed built on those keeps working after switching modules. The image values point at the meteor saved on the frame. Works with both saveExtraData signatures (2024 and 2025)."
                ]
            }
        ],
        "v0.5.5": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Performance: streak finding searched the whole 8-megapixel label image once per connected component. A noisy or twinkling sky yields ~1400 components, which cost ~60-70 s per frame on a Pi 4 - delaying every module after this one. It now searches only each component's bounding box: the same pixels in the same order, so results are identical (verified on four real frame pairs), about 240x faster (~0.3 s). Found with the new replay test tool."
                ]
            }
        ],
        "v0.5.6": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Fragment Segments (frag_min) default 3 -> 5. The fragmented-trail veto has run in shadow mode here for two months, recording frag_n on every saved detection. Of 107 saved detections, 11 reached the old threshold of 3; inspected by eye, 7 were satellite trails or artefacts and 3 were real meteors (scores 3, 4, 3). At 5 only the two clearest satellite trails (6 and 11) are caught and no real meteor. The filter stays off by default; this makes turning it on safe."
                ]
            }
        ],
        "v0.5.7": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Edge-glow veto (edge_filter, shadow mode by default): rejects a long (>= 80 px), fat (elongation < 10) streak with BOTH ends within 50 px of the mask border - horizon or lens-rim glow leaking through the feathered edge. About a quarter of the saved detections here touched the border; the real streaks among them cross it with one end inside and are thin (elongation 10 to 47), while the glow bands hug it (elongation 5 to 8). Over two months it matched 9 detections, all inspected and all edge glow, and no real streak; the result is stable between 50 and 60 px and 70 and 80 px minimum length. Every saved meteor now records edge_d, so a user can check their own record before arming it."
                ]
            }
        ],
        "v0.5.8": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Fisheye calibration fixed: the old fit matched stars to their nearest detection in a deep catalogue, which in a dense Milky Way field lets a wrong model look good. It was right only near the zenith (stars at 30 deg altitude 470 px off), so the star-trail veto, bright-star veto and radiant matching were off below about 60 deg. tools/calibrate_fisheye.py now fits only bright stars it can identify beyond doubt, starting from two stars you identify (--star) or an earlier calibration (--seed): 77 stars, 0.28 deg RMS. Re-checked on the saved record: of 30 star-trail vetoes, 2 were real meteors the old calibration threw away (2 more were satellites, caught by luck). If you made a calibration.json with an earlier version, make it again.",
                    "tools/align_overlay.py: computes the Website's constellation overlay settings from the calibration. Here Allsky's default fisheye projection fits the lens to 0.30 deg."
                ]
            }
        ],
        "v0.5.9": [
            {
                "author": "Benjamin Hartwich",
                "authorurl": "https://astronomy.garden",
                "changes": [
                    "Packaged for the allsky-modules repository, so Allsky 2025's Module Package Manager can install it. The bundled files (allsky_fisheye.py, stars.json, tools/) are read from the module's data folder (moduledata/data/allsky_meteordetect) and, as before, from beside the module.",
                    "Your own calibration.json stays beside the module (config/myFiles/modules on Allsky 2025): the package manager replaces the data folder on every update.",
                    "tools/calibrate_fisheye.py: a star must now reach 12 times the image's own noise instead of a fixed brightness, and a fit is judged by its error in degrees, so it also works on smooth, moonlit images from other cameras. --list-stars lists the bright stars that were up, to choose the two for --star.",
                    "tools/align_overlay.py: never uses the repository's calibration.json (the author's camera), refuses a calibration made at another site, and runs without the Website configuration unless --apply is given."
                ]
            }
        ]
    }
}

# Major annual meteor showers: name, (start m,d), (end m,d), peak ZHR. Used for
# date-based shower context (which showers are active) — not geometric radiant matching,
# which would need a calibrated fisheye projection.
SHOWERS = [
    ("Quadrantids",     (12, 28), (1, 12), 110),
    ("Lyrids",          (4, 16),  (4, 25), 18),
    ("Eta Aquariids",   (4, 19),  (5, 28), 50),
    ("Delta Aquariids", (7, 12),  (8, 23), 25),
    ("Perseids",        (7, 17),  (8, 24), 100),
    ("Orionids",        (10, 2),  (11, 7), 20),
    ("Leonids",         (11, 6),  (11, 30), 15),
    ("Geminids",        (12, 4),  (12, 17), 150),
    ("Ursids",          (12, 17), (12, 26), 10),
]


def _activeShowers(stamp):
    """Showers active on the given YYYYMMDDHHMMSS date, brightest first."""
    try:
        val = int(stamp[4:6]) * 100 + int(stamp[6:8])
    except Exception:
        return []
    out = []
    for name, (m1, d1), (m2, d2), zhr in SHOWERS:
        a, b = m1 * 100 + d1, m2 * 100 + d2
        if (a <= val <= b) if a <= b else (val >= a or val <= b):
            out.append((zhr, name))
    return [n for _, n in sorted(out, reverse=True)]


# --- bundled files ---
# The package manager installs the module's support files (allsky_fisheye.py, stars.json,
# tools/) into moduledata/data/<module>/ below the module; a hand-copied module has them
# beside itself. The user's own calibration.json always sits beside the module, because
# the package manager replaces the data folder on every update.
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIRS = (os.path.join(_MODULE_DIR, "moduledata", "data", "allsky_meteordetect"), _MODULE_DIR)


def _dataFile(name):
    """Path of a bundled support file (the last candidate if none exists)."""
    for d in _DATA_DIRS:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            return path
    return os.path.join(_DATA_DIRS[-1], name)


# --- optional geometric radiant matching (needs allsky_fisheye + calibration.json) ---
_calibCache = {"done": False, "mod": None, "calib": None}


def _loadCalib():
    """Lazy-load the fisheye calibration + projection library (both optional)."""
    if not _calibCache["done"]:
        _calibCache["done"] = True
        try:
            lib = os.path.dirname(_dataFile("allsky_fisheye.py"))
            if lib not in sys.path:
                sys.path.insert(0, lib)
            import allsky_fisheye as fe
            p = os.path.join(_MODULE_DIR, "calibration.json")
            _calibCache["calib"] = fe.load_calibration(p)
            _calibCache["mod"] = fe
            s.log(4, "INFO: meteordetect geometric radiant matching enabled")
        except Exception as ex:
            s.log(1, f"INFO: meteordetect radiant matching disabled ({ex})")
    return _calibCache["mod"], _calibCache["calib"]


def _matchRadiant(p1, p2, showers):
    """Geometric shower attribution for a streak (pixel endpoints), or None.
    Uses current UTC (detection is near-real-time, so it matches the frame time)."""
    mod, calib = _loadCalib()
    if not mod or not calib or not showers:
        return None
    try:
        g = time.gmtime()
        u = (g.tm_year, g.tm_mon, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec)
        name, _sep = mod.match_radiant(p1, p2, calib, u, showers)
        return name
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect radiant match failed: {ex}")
        return None


# --- star-trail orientation veto (needs the fisheye calibration) ---
_SIDEREAL_DEG_PER_S = 15.041 / 3600.0

def _trailAngleAt(cx, cy):
    """Local diurnal star-trail tangent orientation at pixel (cx,cy), in image
    degrees [0,180), or None if the calibration is unavailable / point is below
    the horizon. A streak parallel to this is a trailed star, not a meteor.

    The exposure length does not matter for the *direction*: we rotate the star's
    sky vector by a small fixed angle about the celestial pole and read off the
    resulting pixel displacement, which is the tangent to its diurnal circle.
    """
    mod, calib = _loadCalib()
    if not mod or not calib:
        return None
    try:
        alt, az = mod.pixel_to_altaz(cx, cy, calib)
        if alt <= 0.5:
            return None
        v = mod._unit(alt, az)
        P = mod._unit(calib["lat"], 0.0)                 # celestial pole direction
        P = P / (np.linalg.norm(P) + 1e-12)
        th = np.radians(_SIDEREAL_DEG_PER_S * 60.0)      # 60 s of rotation → tangent
        v2 = (v * np.cos(th) + np.cross(P, v) * np.sin(th) + P * float(np.dot(P, v)) * (1 - np.cos(th)))
        alt2 = np.degrees(np.arcsin(max(-1.0, min(1.0, float(v2[2])))))
        az2 = np.degrees(np.arctan2(float(v2[0]), float(v2[1]))) % 360.0
        x1, y1 = mod.altaz_to_pixel(alt, az, calib)
        x2, y2 = mod.altaz_to_pixel(alt2, az2, calib)
        return float(np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180.0)
    except Exception:
        return None


# --- star-catalog scintillation veto (needs the fisheye calibration + star.json) ---
# On a clear night a bright star scintillates: it brightens between two frames, so the
# frame difference shows a short compact blob AT the star's position — the appear/vanish
# signature of a meteor, but sitting exactly on a catalogue star. We project the bright
# stars for the frame's time and reject a short candidate that lands on one.
_starCache = {"done": False, "cat": None}

def _loadStars():
    """Lazy-load the bundled bright-star catalogue [[ra_deg, dec_deg, vmag], ...]."""
    if not _starCache["done"]:
        _starCache["done"] = True
        try:
            p = _dataFile("stars.json")
            _starCache["cat"] = np.asarray(json.load(open(p))["stars"], dtype=float)
        except Exception as ex:
            s.log(1, f"INFO: meteordetect star veto disabled (no catalogue: {ex})")
    return _starCache["cat"]


_starProjCache = {"key": None, "xy": None}

def _brightStarPix(maglim):
    """Projected pixel positions (Nx2) of catalogue stars brighter than `maglim` and
    above the horizon, at the current UTC. Returns None if calibration/catalogue is
    missing. Cached per (minute, maglim): a frame's candidates share one time and the
    stars drift only ~0.25 px/s, far below the veto radius."""
    mod, calib = _loadCalib()
    cat = _loadStars()
    if not mod or not calib or cat is None:
        return None
    g = time.gmtime()
    key = (g.tm_year, g.tm_yday, g.tm_hour, g.tm_min, round(float(maglim), 1))
    if _starProjCache["key"] == key:
        return _starProjCache["xy"]
    try:
        u = (g.tm_year, g.tm_mon, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec)
        lst = mod.local_sidereal_deg(u, calib["lon"])
        lat = calib["lat"]
        xy = []
        for ra, dec, mag in cat:
            if mag > maglim:
                continue
            alt, az = mod.radec_to_altaz(ra, dec, lst, lat)
            if alt < 12.0:                                    # skip horizon/tree mess
                continue
            xy.append(mod.altaz_to_pixel(alt, az, calib))
        arr = np.asarray(xy, dtype=float) if xy else np.empty((0, 2))
        _starProjCache["key"] = key
        _starProjCache["xy"] = arr
        return arr
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect star projection failed: {ex}")
        return None


def _onStar(cx, cy, maglim, radius):
    """Distance to the nearest projected bright star if a star lies within `radius` px
    of pixel (cx,cy) — i.e. the blob is that star scintillating — else None."""
    arr = _brightStarPix(maglim)
    if arr is None or len(arr) == 0:
        return None
    d = np.hypot(arr[:, 0] - cx, arr[:, 1] - cy)
    m = float(d.min())
    return m if m <= radius else None


def _saveVetoThumb(vetoeddir, img_path, stamp, cand):
    """Save a small crop around a REJECTED streak so it can be human-labelled
    (aircraft / satellite / artifact) on the website — the negative examples for a
    future classifier. Crops from the same full frame the meteor image comes from.
    Returns the filename (or None). Never raises."""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None
        h, w = img.shape[:2]
        cx, cy, ln, a = cand["cx"], cand["cy"], cand["len"], np.radians(cand["ang"])
        hx, hy = np.cos(a) * ln / 2.0, np.sin(a) * ln / 2.0
        pad = 180
        x0 = max(0, int(min(cx - hx, cx + hx) - pad)); x1 = min(w, int(max(cx - hx, cx + hx) + pad))
        y0 = max(0, int(min(cy - hy, cy + hy) - pad)); y1 = min(h, int(max(cy - hy, cy + hy) + pad))
        crop = img[y0:y1, x0:x1]
        if crop.size == 0:
            return None
        if crop.shape[1] > 640:
            sc = 640.0 / crop.shape[1]
            crop = cv2.resize(crop, (640, max(1, int(crop.shape[0] * sc))), interpolation=cv2.INTER_AREA)
        os.makedirs(vetoeddir, exist_ok=True)
        fname = f"vetoed-{stamp}-{int(round(cand['cx']))}-{int(round(cand['cy']))}.jpg"
        cv2.imwrite(os.path.join(vetoeddir, fname), crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return fname
    except Exception:
        return None


def _logVetoed(outdir, stamp, cand, reason, detail, thumb=None):
    """Append a rejected streak to a rolling meteors_vetoed.json for tuning/validation.
    `thumb` (if given) is the crop filename so the website can show it for labelling."""
    try:
        path = os.path.join(outdir, "meteors_vetoed.json")
        try:
            log = json.load(open(path)) if os.path.exists(path) else []
        except Exception:
            log = []
        rec = {"time": stamp, "reason": reason, "detail": round(float(detail), 1),
               "cx": round(cand["cx"], 1), "cy": round(cand["cy"], 1),
               "len": round(cand["len"], 1), "elong": round(cand["elong"], 1),
               "ang": round(cand["ang"], 1), "peak": cand.get("peak")}
        if thumb:
            rec["thumb"] = thumb
        log.append(rec)
        json.dump(log[-500:], open(path, "w"), default=float)
    except Exception:
        pass


def _uploadVetoed(outdir, vetoeddir, thumb_fnames):
    """Upload rejected-candidate crops + the vetoed index to the remote website
    (remote <imagedir>/meteors/vetoed/). The remote 'meteors/vetoed' folder must
    already exist — upload.sh does not create directories. Never raises."""
    try:
        if str(s.getSetting("useremotewebsite")).lower() not in ("true", "1", "yes", "on"):
            return
        scripts = s.getEnvironmentVariable("ALLSKY_SCRIPTS") or \
            os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "scripts")
        uploader = os.path.join(scripts, "upload.sh")
        if not os.path.isfile(uploader):
            return
        base = (s.getSetting("remotewebsiteimagedir") or "").rstrip("/")
        mdir = f"{base}/meteors" if base else "meteors"
        vdir = mdir + "/vetoed"
        for fn in thumb_fnames:
            local = os.path.join(vetoeddir, fn)
            if os.path.isfile(local):
                subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", local, vdir, fn, "MeteorVetoed"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vj = os.path.join(outdir, "meteors_vetoed.json")
        if os.path.isfile(vj):
            subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", vj, mdir, "meteors_vetoed.json", "MeteorVetoedLog"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect vetoed upload failed: {ex}")


# --- persistent state between frames (module stays loaded in the postprocess service) ---
_maskCache = {"name": None, "soft": None, "hard": None, "dist": None}
STATE_FILE = os.path.join(s.ALLSKY_TMP, "allsky_meteordetect_state.json")
PREV_FRAME = os.path.join(s.ALLSKY_TMP, "allsky_meteordetect_prev.png")


def _loadMask(maskName, feather, shape):
    """Return (soft float 0..1 mask, hard uint8 mask) matching the frame, cached."""
    if _maskCache["name"] == (maskName, feather) and _maskCache["soft"] is not None \
            and _maskCache["soft"].shape == shape:
        return _maskCache["soft"], _maskCache["hard"]
    hard = None
    if maskName:
        p = os.path.join(s.ALLSKY_OVERLAY, "images", maskName)
        hard = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    if hard is None:
        hard = np.full(shape, 255, np.uint8)
    if hard.shape != shape:
        hard = cv2.resize(hard, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    # soft, feathered edge (indi-allsky lesson: hard edges create false streaks)
    f = s.int(feather)
    if f > 0:
        k = f + (1 - f % 2)  # odd
        soft = cv2.GaussianBlur(hard, (k, k), 0).astype(np.float32) / 255.0
    else:
        soft = hard.astype(np.float32) / 255.0
    _maskCache.update(name=(maskName, feather), soft=soft, hard=hard, dist=None)
    return soft, hard


def _edgeDistance(hard):
    """Distance of every pixel to the nearest masked-out pixel, cached with the mask."""
    if _maskCache.get("dist") is None or _maskCache["dist"].shape != hard.shape:
        _maskCache["dist"] = cv2.distanceTransform((hard > 127).astype(np.uint8), cv2.DIST_L2, 5)
    return _maskCache["dist"]


def _edgeHug(cand, hard):
    """How far the streak's FARTHER end is from the mask edge, in px. Small means both
    ends sit on the border - see the edge-glow check. Never raises."""
    try:
        dist = _edgeDistance(hard)
        h, w = dist.shape
        return max(float(dist[min(max(int(p[1]), 0), h - 1), min(max(int(p[0]), 0), w - 1)])
                   for p in (cand["p1"], cand["p2"]))
    except Exception:
        return float("inf")


def _findStreaks(diff, min_len, min_elong, max_area, diff_thr):
    _, bw = cv2.threshold(diff, diff_thr, 255, cv2.THRESH_BINARY)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    out = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 12 or area > max_area:
            continue
        # Search only the component's bounding box. np.where over the whole label image
        # scanned all 8 megapixels once PER component - about 70 s a frame on a Pi 4 when
        # a noisy or twinkling sky yields ~1400 components. Same pixels, same order.
        x0, y0 = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
        bw_, bh_ = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        ys, xs = np.where(lab[y0:y0 + bh_, x0:x0 + bw_] == i)
        ys = ys + y0
        xs = xs + x0
        pts = np.column_stack((xs, ys)).astype(np.float32)
        if len(pts) < 5:
            continue
        mean, evec, eval_ = cv2.PCACompute2(pts, mean=None)
        l_major = 4.0 * float(np.sqrt(max(eval_[0, 0], 1e-6)))
        l_minor = 4.0 * float(np.sqrt(max(eval_[1, 0], 1e-6)))
        if l_major < min_len:
            continue
        elong = l_major / (l_minor + 1e-6)
        if elong < min_elong:
            continue
        cx, cy = float(mean[0, 0]), float(mean[0, 1])
        dx, dy = float(evec[0][0]), float(evec[0][1])
        ang = float(np.degrees(np.arctan2(dy, dx)) % 180)
        peak = int(diff[ys, xs].max())        # brightness = peak new-light intensity
        # cast everything to native python floats so the state stays JSON-serialisable
        out.append({
            "cx": cx, "cy": cy, "len": float(l_major), "elong": float(elong), "ang": ang,
            "p1": [cx - dx * l_major / 2, cy - dy * l_major / 2],
            "p2": [cx + dx * l_major / 2, cy + dy * l_major / 2],
            "area": int(area), "peak": peak
        })
    return out


def _dashRuns(gray, p1, p2):
    """Count how many separate bright segments lie along a streak's axis.

    A meteor is a single continuous streak (1 run, sometimes 2 if it tapers);
    a tumbling satellite or a strobing aircraft leaves a DASHED trail — many
    bright/dark alternations. Sampling the intensity along the axis (with a
    small perpendicular max so a slight axis mis-fit still lands on the streak),
    then counting rising edges above a level set relative to the streak's own
    peak, gives a clean separator: on this camera a real meteor scores <=5 and
    a dashed satellite scored 19. Validated on the 2026-07-13 detections."""
    p1 = np.asarray(p1, float); p2 = np.asarray(p2, float)
    L = float(np.hypot(*(p2 - p1)))
    if L < 1.0:
        return 0
    n = max(8, int(L))
    d = (p2 - p1) / L
    perp = np.array([-d[1], d[0]])
    h, w = gray.shape
    vals = np.zeros(n + 1, np.float32)
    for i in range(n + 1):
        pt = p1 + d * (L * i / n)
        m = 0.0
        for o in (-3, -2, -1, 0, 1, 2, 3):     # perpendicular window, robust to mis-fit
            q = pt + perp * o
            x = int(round(q[0])); y = int(round(q[1]))
            if 0 <= x < w and 0 <= y < h:
                v = float(gray[y, x])
                if v > m:
                    m = v
        vals[i] = m
    bg = float(np.percentile(vals, 10)); pk = float(vals.max())
    if pk - bg < 8.0:                          # no real contrast -> not dashed
        return 0
    level = bg + 0.30 * (pk - bg)
    on = vals >= level
    return int(np.sum(on[1:] & ~on[:-1])) + (1 if on[0] else 0)


def _collinearFragments(diff, cx, cy, ang, length, diff_thr,
                        perp_tol=8.0, reach_factor=3.0, area_min=6):
    """Count difference components that lie COLLINEAR with a streak but BEYOND
    its endpoints — the dashed continuation of a fragmented satellite/aircraft
    glint whose faint tail was split into separate sub-threshold pieces.

    The v0.4.0 dash veto only samples the streak's own axis (its continuous
    bright head), so a lone bright head with a broken-up tail passes. This
    walks every diff component and keeps those whose centroid sits within
    ``perp_tol`` px of the streak's infinite axis line and past its own extent
    (|axial| > length/2) out to ``reach_factor``x. A real meteor is a single
    streak with nothing collinear beyond it -> 0; the validated 2026-07-13
    satellite glint scored 3. Measured on the DIFFERENCE image so static stars
    (which cancel there) are never miscounted. Returns (count, max_extent_px)."""
    a = np.radians(ang)
    dx, dy = float(np.cos(a)), float(np.sin(a))
    half = length / 2.0
    reach = half * reach_factor
    _, bw = cv2.threshold(diff, diff_thr, 255, cv2.THRESH_BINARY)
    n, _, stats, cent = cv2.connectedComponentsWithStats(bw, 8)
    cnt = 0
    ext = half
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < area_min:
            continue
        px = float(cent[i][0]) - cx
        py = float(cent[i][1]) - cy
        axial = px * dx + py * dy            # signed distance along the axis
        perp = abs(-px * dy + py * dx)       # distance perpendicular to the axis
        if perp <= perp_tol and half < abs(axial) <= reach:
            cnt += 1
            if abs(axial) > ext:
                ext = abs(axial)
    return cnt, float(ext)


def _angDiff(a, b):
    return min(abs(a - b), 180 - abs(a - b))


def _similar(a, b):
    return np.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"]) < 60 and _angDiff(a["ang"], b["ang"]) < 20


def _progressing(a, b):
    dc = np.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"])
    return 25 < dc < 400 and _angDiff(a["ang"], b["ang"]) < 25


def _readState():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {"prev_streaks": []}


def _writeState(st):
    try:
        with open(STATE_FILE, "w") as fh:
            json.dump(st, fh, default=float)
    except Exception as ex:
        s.log(0, f"ERROR: meteordetect could not write state: {ex}")


def _drawBrackets(img, streak, colour=(0, 255, 255)):
    """Draw a rotated bounding bracket AROUND the streak, never over it."""
    p1 = np.array(streak["p1"]); p2 = np.array(streak["p2"])
    d = p2 - p1
    L = np.hypot(*d) + 1e-6
    perp = np.array([-d[1], d[0]]) / L
    pad = 18
    a = p1 - d / L * pad; b = p2 + d / L * pad
    for sgn in (1, -1):
        o = perp * pad * sgn
        ca, cb = a + o, b + o
        cv2.line(img, tuple(ca.astype(int)), tuple((ca + d / L * 22).astype(int)), colour, 2)
        cv2.line(img, tuple(cb.astype(int)), tuple((cb - d / L * 22).astype(int)), colour, 2)


def _safeRemove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _writeJson(path, data):
    try:
        with open(path, "w") as fh:
            json.dump(data, fh, default=float)
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect could not write {os.path.basename(path)}: {ex}")


def _currentDay():
    """Allsky's day-folder name. saveImage.sh exports DATE_NAME immediately before it runs
    flow-runner.py and that name already carries the 12-hour offset, so it stays on the
    evening's date after midnight — which is exactly the folder the images went into."""
    day = str(s.getEnvironmentVariable("DATE_NAME") or "")
    if re.fullmatch(r"\d{8}", day):
        return day
    return time.strftime("%Y%m%d", time.localtime(time.time() - 12 * 3600))


# The WebUI's Meteors page reads a day's meteor thumbnails from a sibling of meteors/,
# plural like the day's own thumbnails/ (not the singular keogramthumbnail/ pattern) -
# settled on AllskyTeam/allsky#5227 and matched by meteors.php and functions.php there.
WEBUI_THUMB_DIR = "meteorsthumbnails"


def _webUIDayDir(day):
    """images/<day>/meteors — the folder the Allsky WebUI 'Meteors' page browses."""
    if not day:
        return None
    images = s.getEnvironmentVariable("ALLSKY_IMAGES") or \
        os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "images")
    return os.path.join(images, day, "meteors")


def _copyToWebUI(day, stamp, fname, outdir, thumbdir, entries, save_marked):
    """Mirror one saved meteor into images/<day>/ for the WebUI browser: the images and
    json into meteors/, the thumbnails into the sibling meteorsthumbnails/.
    Copies the already-encoded files rather than re-encoding them. Never raises."""
    try:
        daydir = _webUIDayDir(day)
        if not daydir:
            return
        os.makedirs(daydir, exist_ok=True)
        daythumbs = os.path.join(os.path.dirname(daydir), WEBUI_THUMB_DIR)
        os.makedirs(daythumbs, exist_ok=True)
        names = [fname]
        if save_marked:
            names.append(f"meteors-{stamp}-marked.jpg")
        for name in names:
            for src, dst in ((os.path.join(outdir, name), os.path.join(daydir, name)),
                             (os.path.join(thumbdir, name), os.path.join(daythumbs, name))):
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
        _writeJson(os.path.join(daydir, f"meteors-{stamp}.json"), entries)
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect could not populate the WebUI folder for {day}: {ex}")


def _publishVariables(count, moving=0, vetoed=0, saved_stamp=None, saved_day=None,
                      save_webui=True, outdir=None):
    """Publish this frame's result as Allsky variables, under the same names Allsky's
    built-in meteor module uses (AS_METEORCOUNT, AS_METEORIMAGE, AS_METEORIMAGEPATH,
    AS_METEORIMAGEURL), so an overlay, MQTT feed or anything else built on those keeps
    working with this module instead. Only what goes through saveExtraData and is
    declared in metaData['extradata'] is published on Allsky 2025; an environment
    variable alone reaches nothing but the overlay of the same frame.

    The image values point at the meteor SAVED on this frame - the built-in points at
    the frame it analysed, but here a meteor is only confirmed one frame later - and
    are empty when nothing was saved. Never raises."""
    image = path = url = ""
    if saved_stamp:
        image = f"meteors-{saved_stamp}.jpg"
        daydir = _webUIDayDir(saved_day) if save_webui else None
        if daydir:
            path = os.path.join(daydir, image)
            url = f"/images/{saved_day}/{WEBUI_THUMB_DIR}/{image}"
        elif outdir:
            path = os.path.join(outdir, image)
    values = {"AS_METEORCOUNT": int(count), "AS_METEORIMAGE": image,
              "AS_METEORIMAGEPATH": path, "AS_METEORIMAGEURL": url,
              "AS_METEORMOVING": int(moving), "AS_METEORVETOED": int(vetoed)}
    for key in ("AS_METEORCOUNT", "AS_METEORMOVING", "AS_METEORVETOED"):
        s.setEnvironmentVariable(key, str(values[key]))
    try:
        try:
            s.saveExtraData(metaData["extradatafilename"], values,
                            metaData["module"], metaData["extradata"])
        except TypeError:           # Allsky 2024: saveExtraData(file_name, extra_data)
            s.saveExtraData(metaData["extradatafilename"], values)
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect could not publish its variables: {ex}")


def _saveMeteor(img_path, stamp, streaks, outdir, thumbdir, save_marked,
                day=None, save_webui=True):
    """Save the pristine true-colour meteor image + thumbnail + json. Returns 1/0.

    Two destinations, because two consumers read different layouts:
      * outdir / thumbdir        - the website folder; the remote upload and the
                                   per-night charts read the rolling meteors.json there
      * images/<day>/meteors/    - what the Allsky WebUI 'Meteors' page browses (thumbnails
                                   in the sibling meteorsthumbnails/); it wants
                                   one json sidecar per image, not a rolling log
    """
    img = cv2.imread(img_path)
    if img is None:
        return 0
    os.makedirs(thumbdir, exist_ok=True)
    fname = f"meteors-{stamp}.jpg"
    cv2.imwrite(os.path.join(outdir, fname), img)                       # GALLERY: untouched colours
    cv2.imwrite(os.path.join(thumbdir, fname),
                cv2.resize(img, (0, 0), fx=0.25, fy=0.25))
    if save_marked:
        marked = img.copy()
        for m in streaks:
            _drawBrackets(marked, m)                                    # brackets AROUND, never over
        marked_name = f"meteors-{stamp}-marked.jpg"
        cv2.imwrite(os.path.join(outdir, marked_name), marked)
        # the WebUI links the marked THUMBNAIL without checking it exists, so write it too
        cv2.imwrite(os.path.join(thumbdir, marked_name),
                    cv2.resize(marked, (0, 0), fx=0.25, fy=0.25))

    showers = _activeShowers(stamp)
    entries = []
    for m in streaks:
        radiant = _matchRadiant(m["p1"], m["p2"], showers)   # geometric attribution
        entries.append({"time": stamp, "file": fname,
                        "length": round(m["len"], 1), "angle": round(m["ang"], 1),
                        "elong": round(m["elong"], 1), "peak": m.get("peak"),
                        "cx": round(m["cx"], 1), "cy": round(m["cy"], 1),
                        "p1": [round(m["p1"][0], 1), round(m["p1"][1], 1)],
                        "p2": [round(m["p2"][0], 1), round(m["p2"][1], 1)],
                        "frag_n": m.get("frag_n", 0), "frag_ext": round(m.get("frag_ext", 0.0), 1),
                        "edge_d": m.get("edge_d"),
                        "showers": showers, "radiant": radiant})

    # per-image sidecar: just this image's streaks, which is what the WebUI browser reads
    _writeJson(os.path.join(outdir, f"meteors-{stamp}.json"), entries)

    logpath = os.path.join(outdir, "meteors.json")
    try:
        log = json.load(open(logpath)) if os.path.exists(logpath) else []
    except Exception:
        log = []
    log.extend(entries)
    _writeJson(logpath, log[-2000:])

    if save_webui:
        _copyToWebUI(day, stamp, fname, outdir, thumbdir, entries, save_marked)
    return 1


def _uploadRemote(outdir, thumbdir, fname):
    """Upload a saved meteor image + thumbnail to the remote website via Allsky's upload.sh.
    Mirrors how keograms are uploaded. Never raises."""
    try:
        if str(s.getSetting("useremotewebsite")).lower() not in ("true", "1", "yes", "on"):
            return
        scripts = s.getEnvironmentVariable("ALLSKY_SCRIPTS") or \
            os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"), "scripts")
        uploader = os.path.join(scripts, "upload.sh")
        if not os.path.isfile(uploader):
            return
        base = (s.getSetting("remotewebsiteimagedir") or "").rstrip("/")
        remote_dir = f"{base}/meteors" if base else "meteors"
        for local, rdir, remote_name, tag in (
            (os.path.join(outdir, fname), remote_dir, fname, "Meteor"),
            (os.path.join(thumbdir, fname), remote_dir + "/thumbnails", fname, "MeteorThumb"),
            # the index that drives the chart + gallery — without it the remote
            # page has the images but no data, so both stay empty. It MUST keep its
            # own name on the remote: passing the image's fname here (the old bug)
            # uploaded the log *under the image name*, so the remote meteors.json
            # was never refreshed and the gallery/chart stayed frozen on one night.
            (os.path.join(outdir, "meteors.json"), remote_dir, "meteors.json", "MeteorLog"),
        ):
            if os.path.isfile(local):
                subprocess.Popen([uploader, "--silent", "--wait", "--remote-web", local, rdir, remote_name, tag],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as ex:
        s.log(1, f"WARNING: meteordetect remote upload failed: {ex}")


def _truthy(v):
    """Checkbox args arrive from the flow config as the STRING 'true'/'false';
    'false' is truthy in Python, so parse booleans explicitly."""
    return v is True or (not isinstance(v, bool) and str(v).strip().lower() in ("true", "1", "yes", "on"))


def meteordetect(params, event):
    if s.image is None:
        return "No image available"

    raining, rainFlag = s.raining()
    if rainFlag:
        _publishVariables(0)
        s.setEnvironmentVariable("AS_METEORCOUNT", "Disabled (rain)")   # overlay text as before
        return "Raining - meteor detection skipped"

    min_len = s.int(params.get("min_length", 50))
    diff_thr = s.int(params.get("diff_thr", 22))
    min_elong = s.asfloat(params.get("min_elong", 5.0))
    max_area = s.int(params.get("max_area", 6000))
    cloud_frac = s.asfloat(params.get("cloud_frac", 2.0)) / 100.0
    feather = params.get("edge_feather", 35)
    # .get() with defaults so a config saved before these options existed still runs
    dash_filter = _truthy(params.get("dash_filter", True))
    dash_runs = s.int(params.get("dash_runs", 10))
    dash_min_len = s.asfloat(params.get("dash_min_len", 120.0))
    frag_filter = _truthy(params.get("frag_filter", False))   # off = shadow (measure + log, no veto)
    frag_min = s.int(params.get("frag_min", 5))
    frag_min_len = s.asfloat(params.get("frag_min_len", 120.0))
    edge_filter = _truthy(params.get("edge_filter", False))   # off = shadow (measure + log, no veto)
    edge_margin = s.asfloat(params.get("edge_margin", 50.0))
    edge_max_elong = s.asfloat(params.get("edge_max_elong", 10.0))
    edge_min_len = s.asfloat(params.get("edge_min_len", 80.0))
    sat_filter = _truthy(params.get("satellite_filter", True))
    scint_guard = _truthy(params.get("scint_guard", True))
    scint_max = s.int(params.get("scint_max", 8))
    repeat_filter = _truthy(params.get("repeat_filter", True))
    repeat_k = s.int(params.get("repeat_k", 3))
    trail_filter = _truthy(params.get("trail_filter", True))
    trail_tol = s.asfloat(params.get("trail_tol", 12.0))
    star_filter = _truthy(params.get("star_filter", True))
    star_radius = s.asfloat(params.get("star_radius", 16.0))
    star_maglim = s.asfloat(params.get("star_maglim", 5.0))
    upload_remote = _truthy(params.get("upload_remote", True))
    save_vetoed = _truthy(params.get("save_vetoed", True))
    save_webui = _truthy(params.get("save_webui", True))
    # save_debug is the old name for the same thing; honour it so an existing config
    # that switched it on keeps getting marked copies.
    save_marked = _truthy(params.get("save_marked", True)) or _truthy(params.get("save_debug", False))
    debug = _truthy(params.get("debug", False))

    outdir = params["outputdir"].strip()
    if not outdir:
        website = s.getEnvironmentVariable("ALLSKY_WEBSITE")
        if not website:
            website = os.path.join(s.getEnvironmentVariable("ALLSKY_HOME") or os.path.expanduser("~/allsky"),
                                   "html", "allsky")
        outdir = os.path.join(website, "meteors")
    thumbdir = os.path.join(outdir, "thumbnails")
    vetoeddir = os.path.join(outdir, "vetoed")

    if debug:
        s.startModuleDebug(metaData["module"])

    gray = cv2.cvtColor(s.image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    soft, hard = _loadMask(params["mask"], feather, gray.shape)

    # previous frame (persisted to disk so it survives restarts)
    prev = cv2.imread(PREV_FRAME, cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(PREV_FRAME, gray.astype(np.uint8))
    if prev is None or prev.shape != gray.shape:
        _publishVariables(0)
        return "First frame stored, need a second frame to compare"

    # frame difference, remove global offset, apply SOFT mask
    diff = cv2.absdiff(gray, prev.astype(np.float32))
    diff = np.clip(diff - float(np.median(diff)), 0, 255)
    diff_m = (diff * soft).astype(np.uint8)
    if debug:
        s.writeDebugImage(metaData["module"], "diff.png", diff_m)

    # cloud gate
    coverage = float((diff_m > diff_thr).mean() / max(1e-6, (hard > 0).mean()))
    if coverage > cloud_frac:
        _publishVariables(0)
        st = _readState(); st["prev_streaks"] = []; _writeState(st)
        return f"Cloudy frame skipped (coverage {coverage*100:.1f}%)"

    streaks = _findStreaks(diff_m, min_len, min_elong, max_area, diff_thr)

    # tag each streak with its dashed-segment count (measured on the true-colour
    # frame the streak was just captured in) so the dashed-trail veto can run when
    # the candidate is confirmed one frame later. Cheap; only long streaks matter.
    if dash_filter:
        for st_ in streaks:
            st_["dash_runs"] = (_dashRuns(gray, st_["p1"], st_["p2"])
                                if st_["len"] >= dash_min_len else 0)

    # tag each long streak with its collinear-fragment count on the DIFFERENCE
    # image (static stars cancel there). Measured always so the shadow metric is
    # gathered even while frag_filter is off; only long streaks are worth testing.
    for st_ in streaks:
        if st_["len"] >= frag_min_len:
            fn, fx = _collinearFragments(diff_m, st_["cx"], st_["cy"],
                                         st_["ang"], st_["len"], diff_thr)
            st_["frag_n"], st_["frag_ext"] = fn, fx
        else:
            st_["frag_n"], st_["frag_ext"] = 0, st_["len"] / 2.0

    # scintillation guard: a clear starry night produces many tiny star-twinkle
    # streaks. If the frame is that noisy, keep only a clearly dominant streak
    # (a genuine bright meteor stands well above the noise), else skip the frame.
    if scint_guard and len(streaks) > scint_max:
        ordered = sorted(streaks, key=lambda st_: st_["len"], reverse=True)
        second = ordered[1]["len"] if len(ordered) > 1 else 0.0
        if ordered[0]["len"] >= 1.6 * second:
            streaks = [ordered[0]]
        else:
            # too noisy to trust: drop pending unconfirmed and skip, like a cloudy frame
            st = _readState()
            for entry in st.get("pending", []):
                _safeRemove(entry["img_path"])
            st["prev_streaks"] = []
            st["pending"] = []
            _writeState(st)
            _publishVariables(0)
            return "Scintillation-dominated frame skipped (clear sky, star twinkle)"

    state = _readState()
    prev_streaks = state.get("prev_streaks", [])
    pending = state.get("pending", [])   # candidates from last frame awaiting confirmation

    # rolling "hot spot" memory for the recurrence veto: [cx, cy, t] of every streak
    # from earlier frames. A trailed star / scintillation / bloom / fixed reflection
    # keeps firing near the same spot; a real meteor appears exactly once, so it can
    # never accumulate here and is never vetoed by recurrence.
    REPEAT_RADIUS, REPEAT_WINDOW_S = 55.0, 1500.0
    now_t = time.time()
    hotspots = [h for h in state.get("hotspots", []) if now_t - h[2] <= REPEAT_WINDOW_S]

    def _recurrence(cand):
        r2 = REPEAT_RADIUS ** 2
        return sum(1 for h in hotspots
                   if (h[0] - cand["cx"]) ** 2 + (h[1] - cand["cy"]) ** 2 <= r2)

    saved, moving, vetoed = 0, 0, 0
    last_saved = (None, None)       # (stamp, day) of the last meteor saved on this frame

    # --- 1) resolve last frame's pending candidates ---
    # A real meteor is present in exactly one frame, so it shows up in TWO consecutive
    # difference images at the SAME location (its appearance, then its disappearance).
    # We confirm a candidate only if the current frame repeats it at the same spot AND
    # it is not a moving track, a recurring position, or aligned with the star trails.
    veto_thumbs = []
    for entry in pending:
        # veto helper: save a labelling crop of the rejected streak (negative example)
        # and log it. Bound the img_path/stamp per iteration so the closure is safe.
        def _veto(cand, reason, detail, _ip=entry.get("img_path"), _stamp=entry["stamp"]):
            t = _saveVetoThumb(vetoeddir, _ip, _stamp, cand) if (save_vetoed and _ip) else None
            if t:
                veto_thumbs.append(t)
            _logVetoed(outdir, _stamp, cand, reason, detail, t)
        keep = []
        for cand in entry["streaks"]:
            if sat_filter and any(_progressing(cur, cand) for cur in streaks):
                moving += 1
                _veto(cand, "moving", 0)
                continue
            if not any(_similar(cur, cand) for cur in streaks):
                continue  # no same-location disappearance -> flicker -> discard
            rec = _recurrence(cand) if repeat_filter else 0
            if repeat_filter and rec >= repeat_k:
                vetoed += 1
                _veto(cand, "repeat", rec)
                continue
            if trail_filter and cand["len"] <= 130.0:          # long/bright fireballs exempt
                ta = _trailAngleAt(cand["cx"], cand["cy"])
                if ta is not None and _angDiff(cand["ang"], ta) <= trail_tol:
                    vetoed += 1
                    _veto(cand, "trail", _angDiff(cand["ang"], ta))
                    continue
            if star_filter and cand["len"] <= 130.0:           # long/bright fireballs exempt
                sd = _onStar(cand["cx"], cand["cy"], star_maglim, star_radius)
                if sd is not None:                             # blob sits on a bright star
                    vetoed += 1
                    _veto(cand, "star", sd)
                    continue
            if dash_filter and cand["len"] >= dash_min_len and cand.get("dash_runs", 0) >= dash_runs:
                vetoed += 1
                _veto(cand, "dashed", cand.get("dash_runs", 0))
                continue
            # fragmented-trail check. Armed (frag_filter on) it vetoes; off it is
            # shadow-only: log a frag-shadow entry for tuning but keep the meteor,
            # so we learn what it WOULD reject without risking a real meteor yet.
            if cand["len"] >= frag_min_len and cand.get("frag_n", 0) >= frag_min:
                if frag_filter:
                    vetoed += 1
                    _veto(cand, "fragmented", cand.get("frag_n", 0))
                    continue
                _veto(cand, "frag-shadow", cand.get("frag_n", 0))
            # edge-glow check: a LONG, FAT streak with BOTH ends on the mask border is the
            # horizon / lens-rim glow leaking through the feathered edge, not a meteor. Real
            # streaks that reach the border cross it - one end inside - and are thin. Over two
            # months here this matched 9 detections, all edge glow, and no real streak.
            cand["edge_d"] = round(_edgeHug(cand, hard), 1)
            if cand["len"] >= edge_min_len and cand.get("elong", 99.0) < edge_max_elong \
                    and cand["edge_d"] < edge_margin:
                if edge_filter:
                    vetoed += 1
                    _veto(cand, "edge-glow", cand["edge_d"])
                    continue
                _veto(cand, "edge-shadow", cand["edge_d"])
            keep.append(cand)
        if keep:
            n = _saveMeteor(entry["img_path"], entry["stamp"], keep,
                            outdir, thumbdir, save_marked,
                            entry.get("day") or _currentDay(), save_webui)
            saved += n
            if n:
                last_saved = (entry["stamp"], entry.get("day") or _currentDay())
            if n and upload_remote:
                _uploadRemote(outdir, thumbdir, f"meteors-{entry['stamp']}.jpg")
        _safeRemove(entry["img_path"])
    if upload_remote and veto_thumbs:
        _uploadVetoed(outdir, vetoeddir, veto_thumbs)

    # --- 2) collect NEW candidates from the current frame (deferred to next frame) ---
    new_cands = []
    for st_ in streaks:
        if sat_filter and any(_progressing(st_, p) for p in prev_streaks):
            moving += 1
            continue
        if any(_similar(st_, p) for p in prev_streaks):
            continue  # disappearance of an already handled streak -> de-dupe
        new_cands.append(st_)

    new_pending = []
    if new_cands:
        stamp = time.strftime("%Y%m%d%H%M%S")
        stash = os.path.join(s.ALLSKY_TMP, f"allsky_meteordetect_pending_{stamp}.jpg")
        cv2.imwrite(stash, s.image)          # stash TRUE-COLOUR frame for later save
        # pin the day folder now: the candidate is only confirmed on a later frame, which
        # may already be in the next DATE_NAME period
        new_pending.append({"img_path": stash, "stamp": stamp,
                            "day": _currentDay(), "streaks": new_cands})

    # remember this frame's streak positions for the recurrence veto (rolling, pruned)
    hotspots.extend([round(st_["cx"], 1), round(st_["cy"], 1), now_t] for st_ in streaks)
    state["hotspots"] = hotspots[-400:]
    state["prev_streaks"] = streaks
    state["pending"] = new_pending
    _writeState(state)

    _publishVariables(saved, moving, vetoed, last_saved[0], last_saved[1], save_webui, outdir)
    result = (f"{saved} meteor(s) confirmed, {moving} moving rejected, "
              f"{vetoed} artifact(s) vetoed, {len(new_cands)} new candidate(s) pending, "
              f"{len(streaks)} streak(s) total")
    s.log(4, f"INFO: {result}")
    return result


def meteordetect_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {STATE_FILE, PREV_FRAME},
            "env": {"AS_METEORCOUNT", "AS_METEORMOVING", "AS_METEORVETOED"}
        }
    }
    s.cleanupModule(moduleData)
