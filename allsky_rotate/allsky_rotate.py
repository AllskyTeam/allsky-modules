"""
allsky_rotate.py - Rotate the allsky image before overlays are applied.

Designed for use with fisheye all-sky cameras pointed straight up. Rotates
the captured image to compensate for a camera mounted off-axis from polar
north, ensuring overlays and cardinal directions land on a correctly oriented
image. Optionally blends a star trail reference image to assist with alignment.
"""

import os
import cv2
import numpy as np
import allsky_shared as s

metaData = {
    "name": "Image Rotation",
    "description": "Rotates the captured image by a fixed angle before overlays are applied. Use to compensate for a camera that is not aligned with polar north.",
    "module": "allsky_rotate",
    "version": "1.0.0",
    "events": [
        "day",
        "night"
    ],
    "experimental": "false",
    "arguments": {
        "angle": "0",
        "expand": "false",
        "background": "0,0,0",
        "alignmentline": "false",
        "linecolour": "255,0,0",
        "linethickness": "1",
        "startraildate": "",
        "startrailopacity": "50"
    },
    "argumentdetails": {
        "angle": {
            "required": "true",
            "description": "Rotation angle in degrees. Positive values rotate counter-clockwise, negative values rotate clockwise.",
            "help": "Enter the number of degrees to rotate the image. For example, -90 rotates 90° clockwise.",
            "type": {
                "fieldtype": "spinner",
                "min": -359,
                "max": 359,
                "step": 1
            }
        },
        "expand": {
            "required": "false",
            "description": "Expand canvas to fit rotated image",
            "help": "If enabled, the output image will be enlarged so no corners are clipped. If disabled, the output image retains the original dimensions (corners will be filled with the background colour). For circular fisheye images, leave this disabled.",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "background": {
            "required": "false",
            "description": "Background fill colour (R,G,B)",
            "help": "Colour used to fill the corners exposed by rotation, in R,G,B format. Default is black (0,0,0).",
            "type": {
                "fieldtype": "text"
            }
        },
        "alignmentline": {
            "required": "false",
            "description": "Show north alignment line",
            "help": "Draws a vertical line through the centre of the image to help align the camera with the north star. Disable this once your camera is correctly aligned.",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "linecolour": {
            "required": "false",
            "description": "Alignment line colour (R,G,B)",
            "help": "Colour of the alignment line in R,G,B format. Default is red (255,0,0).",
            "type": {
                "fieldtype": "text"
            }
        },
        "linethickness": {
            "required": "false",
            "description": "Alignment line thickness (pixels)",
            "help": "Thickness of the alignment line in pixels.",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 10,
                "step": 1
            }
        },
        "startraildate": {
            "required": "false",
            "description": "Star trail date (YYYYMMDD)",
            "help": "Date of the star trail image to use as an alignment reference, in YYYYMMDD format (e.g. 20250308). The image will be loaded from ~/allsky/images/(date)/startrails/startrails-(date).jpg, rotated by the same angle, and blended over the live image. Leave blank to disable.",
            "type": {
                "fieldtype": "text"
            }
        },
        "startrailopacity": {
            "required": "false",
            "description": "Star trail overlay opacity (%)",
            "help": "How strongly the star trail image is blended over the live image, as a percentage. 100 replaces the live image entirely; 0 hides the star trail. 50 is a good starting point.",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 100,
                "step": 5
            }
        }
    },
    "enabled": "false"
}


def _to_bool(value):
    """Safely coerce a string or bool param to a Python bool."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def _parse_bgr(colour_str: str):
    """Parse a 'R,G,B' string into a (B, G, R) tuple for OpenCV."""
    try:
        parts = [int(v.strip()) for v in colour_str.split(",")]
        if len(parts) == 3:
            r, g, b = parts
            return (b, g, r)
    except (ValueError, AttributeError):
        pass
    return (0, 0, 0)  # default: black


def _rotate_image(image, angle, expand, bg_color):
    """Rotate an OpenCV image by angle degrees. Returns the rotated image."""
    h, w = image.shape[:2]
    cx, cy = w / 2.0, h / 2.0

    rotation_matrix = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)

    if expand:
        cos_a = abs(rotation_matrix[0, 0])
        sin_a = abs(rotation_matrix[0, 1])
        new_w = int(h * sin_a + w * cos_a)
        new_h = int(h * cos_a + w * sin_a)
        rotation_matrix[0, 2] += (new_w / 2.0) - cx
        rotation_matrix[1, 2] += (new_h / 2.0) - cy
        out_w, out_h = new_w, new_h
    else:
        out_w, out_h = w, h

    return cv2.warpAffine(
        image,
        rotation_matrix,
        (out_w, out_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=bg_color
    )


def _load_startrail(date_str: str):
    """
    Locate and load a star trail image for the given YYYYMMDD date string.
    Returns an OpenCV image or None if not found.
    """
    date_str = date_str.strip()
    if not date_str:
        return None

    home = os.path.expanduser("~")
    path = os.path.join(
        home, "allsky", "images", date_str,
        "startrails", f"startrails-{date_str}.jpg"
    )

    if not os.path.isfile(path):
        s.log(1, f"WARNING: allsky_rotate - star trail image not found: {path}")
        return None

    trail = cv2.imread(path)
    if trail is None:
        s.log(1, f"WARNING: allsky_rotate - failed to read star trail image: {path}")
        return None

    s.log(4, f"INFO: allsky_rotate - loaded star trail: {path}")
    return trail


def rotate(params, event):
    """Rotate s.image by the configured angle, optionally blending a star trail
    reference image and drawing a north alignment line."""

    # ── Parameter parsing ──────────────────────────────────────────────────
    try:
        angle = float(params.get("angle", 0))
    except (ValueError, TypeError):
        s.log(1, "INFO: allsky_rotate - invalid angle, skipping rotation")
        return

    expand          = _to_bool(params.get("expand", False))
    bg_color        = _parse_bgr(params.get("background", "0,0,0"))
    alignment_line  = _to_bool(params.get("alignmentline", False))
    line_colour     = _parse_bgr(params.get("linecolour", "255,0,0"))
    startrail_date  = params.get("startraildate", "").strip()

    try:
        line_thickness = int(params.get("linethickness", 1))
    except (ValueError, TypeError):
        line_thickness = 1

    try:
        startrail_opacity = max(0, min(100, int(params.get("startrailopacity", 50)))) / 100.0
    except (ValueError, TypeError):
        startrail_opacity = 0.5

    # ── Image check ────────────────────────────────────────────────────────
    image = s.image
    if image is None:
        s.log(0, "ERROR: allsky_rotate - s.image is None, cannot continue")
        return

    # ── Image rotation ─────────────────────────────────────────────────────
    if angle != 0:
        image = _rotate_image(image, angle, expand, bg_color)
        direction = "CCW" if angle > 0 else "CW"
        s.log(4, f"INFO: allsky_rotate - rotated {abs(angle):.1f}° {direction} "
                 f"({'expanded' if expand else 'same size'})")
    else:
        s.log(4, "INFO: allsky_rotate - angle is 0, skipping rotation")

    # ── Star trail overlay ─────────────────────────────────────────────────
    if startrail_date:
        trail = _load_startrail(startrail_date)

        if trail is not None:
            # Rotate the trail by the same angle so both images share the same frame
            if angle != 0:
                trail = _rotate_image(trail, angle, expand, bg_color)

            # Resize trail to match live image if dimensions differ
            h, w = image.shape[:2]
            th, tw = trail.shape[:2]
            if (th, tw) != (h, w):
                trail = cv2.resize(trail, (w, h), interpolation=cv2.INTER_LINEAR)
                s.log(4, f"INFO: allsky_rotate - star trail resized from {tw}x{th} to {w}x{h}")

            # Ensure both images are the same channel depth before blending
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            if len(trail.shape) == 2:
                trail = cv2.cvtColor(trail, cv2.COLOR_GRAY2BGR)

            image = cv2.addWeighted(trail, startrail_opacity, image, 1.0 - startrail_opacity, 0)
            s.log(4, f"INFO: allsky_rotate - star trail blended at {int(startrail_opacity * 100)}% opacity")

    # ── North alignment line ───────────────────────────────────────────────
    if alignment_line:
        h, w = image.shape[:2]
        cx = w // 2
        cv2.line(image, (cx, 0), (cx, h), line_colour, line_thickness)
        s.log(4, "INFO: allsky_rotate - alignment line drawn")

    s.image = image
