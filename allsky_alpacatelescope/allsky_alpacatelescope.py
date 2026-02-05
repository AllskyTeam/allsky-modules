"""
alpacatelescope.py - v0.1.5
A module for 'Allsky' to visualize telescope positions via ASCOM Alpaca.
Supports non-square sensors, provides advanced calibration graphics,
and exports real-time status to the Allsky Overlay Manager.

Original logic based on 'allsky_telescopemarker'.
"""
import allsky_shared as s
import numpy as np
import json, cv2, ast
from urllib.request import urlopen

metaData = {
    "name": "Alpaca Telescope",
    "description": "Visualizes telescope position and exports status via ASCOM Alpaca API.",
    "module": "alpacatelescope",
    "version": "v0.1.5",
    "events": ["night", "day"],
    "experimental": "false",
    "arguments":{
        "telescope_server": "http://192.168.178.213:11111",
        "telescope_alt": "/api/v1/telescope/0/altitude",
        "telescope_az": "/api/v1/telescope/0/azimuth",
        "camera_azimuth": "0",
        "center_x": "0",
        "center_y": "0",
        "radius_override": "0",
        "image_flip": "None",
        "telescope_marker_radius": "30",
        "telescope_marker_width": "5",
        "telescope_marker_color": "(255,0,255)",
        "debug": "false",
        "extradatafilename": "alpacatelescope.json",
        "telescope_default": "(0.0,0.0)",
        "observer_lat": "",
        "observer_lon": "",
        "observer_height": ""
    },
    "argumentdetails": {
        "telescope_server": { "required": "true", "description": "Alpaca Server URL", "help": "e.g. http://192.168.1.50:11111" },
        "camera_azimuth": { "description": "Camera North Offset (°)", "help": "Rotation of your camera's north in degrees." },
        "center_x": { "description": "Manual Center X (px)", "help": "0 = image center. Adjust for non-square sensors." },
        "center_y": { "description": "Manual Center Y (px)", "help": "0 = image center. Adjust for non-square sensors." },
        "radius_override": { "description": "Horizon Radius (px)", "help": "Radius from center to 0° altitude." },
        "image_flip": {
            "required": "true",
            "description": "Coordinate Flip",
            "type": { "fieldtype": "select", "values": "None,Horizontal,Vertical,Both", "default": "None" }
        },
        "debug": { "description": "Enable Debug Graphics", "type": { "fieldtype": "checkbox" }, "help": "Draws horizon, zenith and north line." },
        "telescope_marker_color": { "description": "Marker Color (B,G,R)", "help": "BGR format, e.g., (255,0,255) for Magenta." },
        "extradatafilename": { "description": "Extra Data Filename", "help": "Default: alpacatelescope.json" }
    }
}

def get_alpaca_value(base_url, endpoint):
    """ Helper to fetch JSON data from Alpaca API """
    url = f"{base_url}/{endpoint.lstrip('/')}"
    try:
        with urlopen(url, timeout=1.5) as r:
            data = json.loads(r.read().decode('utf-8'))
            if data.get('ErrorNumber') == 0:
                return data.get('Value')
    except Exception:
        return None
    return None

def alpacatelescope(params, event):
    try:
        if s.image is None: return "No Image"
        h, w = s.image.shape[:2]
        server = params.get('telescope_server', '').rstrip('/')
        
        # 1. Parse Settings
        debug = str(params.get('debug', 'false')).lower() == 'true'
        cam_az = float(params.get('camera_azimuth', 0))
        cx = int(float(params.get('center_x', 0)) or w/2)
        cy = int(float(params.get('center_y', 0)) or h/2)
        R = int(float(params.get('radius_override', 0)) or min(w,h)/2)
        flip = params.get('image_flip', 'None')
        
        # 2. Fetch Alpaca Data
        alt = get_alpaca_value(server, params.get('telescope_alt'))
        az = get_alpaca_value(server, params.get('telescope_az'))
        tracking = get_alpaca_value(server, "/api/v1/telescope/0/tracking")
        slewing = get_alpaca_value(server, "/api/v1/telescope/0/slewing")
        at_park = get_alpaca_value(server, "/api/v1/telescope/0/atpark")

        # 3. Status Logic & Export
        status = "Idle"
        if tracking: status = "Tracking"
        if slewing: status = "Slewing"
        if at_park: status = "Parked"
        
        extraData = {
            "AS_TELESCOPEALT": f"{alt:.2f}" if alt is not None else "N/A",
            "AS_TELESCOPEAZ": f"{az:.2f}" if az is not None else "N/A",
            "AS_TELESCOPESTATUS": status,
            "AS_TELESCOPETRACKING": "Yes" if tracking else "No",
            "AS_OBSERVER_LAT": params.get('observer_lat', 'N/A'),
            "AS_OBSERVER_LON": params.get('observer_lon', 'N/A')
        }
        s.saveExtraData(params.get('extradatafilename', 'alpacatelescope.json'), extraData)

        # 4. Calculation (Fallback if server offline)
        draw_alt, draw_az = alt, az
        if draw_alt is None or draw_az is None:
            draw_alt, draw_az = ast.literal_eval(params.get('telescope_default', '(0.0,0.0)'))

        # Map Az/Alt to Image Coordinates (Fisheye Projection)
        az_rad = np.deg2rad((draw_az - cam_az) % 360)
        r_px = ((90.0 - draw_alt) / 90.0) * R
        tx, ty = cx + r_px * np.sin(az_rad), cy - r_px * np.cos(az_rad)

        # Apply Image Flips to calculated points
        final_cx, final_cy = cx, cy
        if flip in ["Horizontal", "Both"]:
            tx, final_cx = w - tx, w - cx
        if flip in ["Vertical", "Both"]:
            ty, final_cy = h - ty, h - cy

        # 5. Drawing - Debug Layer
        if debug:
            # Draw Horizon Circle
            cv2.circle(s.image, (int(final_cx), int(final_cy)), int(R), (0, 255, 255), 2)
            # Draw Zenith Cross
            cv2.line(s.image, (int(final_cx)-20, int(final_cy)), (int(final_cx)+20, int(final_cy)), (255, 255, 0), 2)
            cv2.line(s.image, (int(final_cx), int(final_cy)-20), (int(final_cx), int(final_cy)+20), (255, 255, 0), 2)
            # Draw North Indicator
            n_rad = np.deg2rad((0 - cam_az) % 360)
            nx, ny = final_cx + R * np.sin(n_rad), final_cy - R * np.cos(n_rad)
            if flip in ["Horizontal", "Both"]: nx = w - (final_cx + R * np.sin(n_rad))
            if flip in ["Vertical", "Both"]: ny = h - (final_cy - R * np.cos(n_rad))
            cv2.line(s.image, (int(final_cx), int(final_cy)), (int(nx), int(ny)), (0, 0, 255), 3)
            cv2.putText(s.image, "N", (int(nx), int(ny)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 6. Drawing - Telescope Marker
        m_color = ast.literal_eval(params.get('telescope_marker_color', '(255,0,255)'))
        m_rad = int(params.get('telescope_marker_radius', 30))
        m_width = int(params.get('telescope_marker_width', 5))
        cv2.circle(s.image, (int(tx), int(ty)), m_rad, m_color, m_width)

        return "OK"
    except Exception as e:
        s.log(0, f"ERROR: alpacatelescope: {str(e)}")
        return f"Error: {str(e)}"
