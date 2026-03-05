"""
alpacatelescope.py - v0.1.8
A 'Allsky' module to mark the telescope positions via Alpaca API.
Based on the original telescope marker module!
"""
import allsky_shared as s
import numpy as np
import json, cv2, ast
from urllib.request import urlopen

metaData = {
    "name": "Alpaca Telescope",
    "description": "Visualizes telescope position via ASCOM Alpaca Alt/Az data.",
    "module": "alpacatelescope",
    "version": "v0.1.8",
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
        "telescope_default": "(0.0,0.0)"
    },
    "argumentdetails": {
        "telescope_server": { "required": "true", "description": "Alpaca Server URL", "help": "e.g. http://192.168.1.50:11111" },
        "telescope_alt": { "required": "true", "description": "API Path Altitude", "help": "Alpaca endpoint for altitude." },
        "telescope_az": { "required": "true", "description": "API Path Azimuth", "help": "Alpaca endpoint for azimuth." },
        "camera_azimuth": { "description": "Camera North Offset (°)", "help": "Rotation of your camera sensor's north." },
        "center_x": { "description": "Center X (px)", "help": "0 = image center. Use to align zenith." },
        "center_y": { "description": "Center Y (px)", "help": "0 = image center. Use to align zenith." },
        "radius_override": { "description": "Horizon Radius (px)", "help": "Radius from center to 0° altitude." },
        "image_flip": {
            "required": "true",
            "description": "Coordinate Flip",
            "type": { "fieldtype": "select", "values": "None,Horizontal,Vertical,Both", "default": "None" },
            "help": "Matches coordinate math to your image flip settings."
        },
        "telescope_marker_radius": { "description": "Marker Radius (px)", "help": "Size of the telescope marker circle." },
        "telescope_marker_width": { "description": "Marker Thickness (px)", "help": "Line thickness of the marker." },
        "telescope_marker_color": { "description": "Marker Color (B,G,R)", "help": "BGR format, e.g. (0,0,255) for Red." },
        "debug": { 
            "description": "Enable Debug Graphics", 
            "type": { "fieldtype": "checkbox" },
            "help": "Draws horizon (yellow), zenith (cyan) and north line (red)." 
        },
        "extradatafilename": { "description": "Extra Data Filename", "help": "Filename for overlay data (JSON)." },
        "telescope_default": { "description": "Fallback (Alt,Az)", "help": "Default position if server is offline." }
    }
}

def get_alpaca_value(base_url, endpoint):
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
        
        # Parse Settings
        debug = str(params.get('debug', 'false')).lower() == 'true'
        cam_az = float(params.get('camera_azimuth', 0))
        cx = int(float(params.get('center_x', 0)) or w/2)
        cy = int(float(params.get('center_y', 0)) or h/2)
        R = int(float(params.get('radius_override', 0)) or min(w,h)/2)
        flip = params.get('image_flip', 'None')
        
        # Alpaca API calls
        alt = get_alpaca_value(server, params.get('telescope_alt'))
        az = get_alpaca_value(server, params.get('telescope_az'))
        tracking = get_alpaca_value(server, "/api/v1/telescope/0/tracking")
        slewing = get_alpaca_value(server, "/api/v1/telescope/0/slewing")
        at_park = get_alpaca_value(server, "/api/v1/telescope/0/atpark")

        # Status determination
        status = "Idle"
        if tracking: status = "Tracking"
        if slewing: status = "Slewing"
        if at_park: status = "Parked"
        
        # Export for Overlay Manager
        extraData = {
            "AS_TELESCOPEALT": f"{alt:.2f}" if alt is not None else "N/A",
            "AS_TELESCOPEAZ": f"{az:.2f}" if az is not None else "N/A",
            "AS_TELESCOPESTATUS": status
        }
        s.saveExtraData(params.get('extradatafilename', 'alpacatelescope.json'), extraData)

        # Positioning logic
        draw_alt, draw_az = alt, az
        if draw_alt is None or draw_az is None:
            try:
                draw_alt, draw_az = ast.literal_eval(params.get('telescope_default', '(0.0,0.0)'))
            except:
                draw_alt, draw_az = 0.0, 0.0

        # Polar to Cartesian mapping
        az_rad = np.deg2rad((draw_az - cam_az) % 360)
        r_px = ((90.0 - draw_alt) / 90.0) * R
        tx, ty = cx + r_px * np.sin(az_rad), cy - r_px * np.cos(az_rad)

        # Handling image flips for markers and debug graphics
        final_cx, final_cy = cx, cy
        if flip in ["Horizontal", "Both"]:
            tx, final_cx = w - tx, w - cx
        if flip in ["Vertical", "Both"]:
            ty, final_cy = h - ty, h - cy

        # Visual Debug Layer
        if debug:
            # Yellow: Horizon
            cv2.circle(s.image, (int(final_cx), int(final_cy)), int(R), (0, 255, 255), 2)
            # Cyan: Zenith
            cv2.line(s.image, (int(final_cx)-30, int(final_cy)), (int(final_cx)+30, int(final_cy)), (255, 255, 0), 2)
            cv2.line(s.image, (int(final_cx), int(final_cy)-30), (int(final_cx), int(final_cy)+30), (255, 255, 0), 2)
            # Red: North Line (Azimuth 0)
            n_rad = np.deg2rad((0 - cam_az) % 360)
            nx, ny = final_cx + R * np.sin(n_rad), final_cy - R * np.cos(n_rad)
            if flip in ["Horizontal", "Both"]: nx = w - (final_cx + R * np.sin(n_rad))
            if flip in ["Vertical", "Both"]: ny = h - (final_cy - R * np.cos(n_rad))
            cv2.line(s.image, (int(final_cx), int(final_cy)), (int(nx), int(ny)), (0, 0, 255), 3)
            cv2.putText(s.image, "N", (int(nx), int(ny)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)

        # Drawing the actual telescope marker
        m_color = ast.literal_eval(params.get('telescope_marker_color', '(255,0,255)'))
        m_radius = int(params.get('telescope_marker_radius', 30))
        m_width = int(params.get('telescope_marker_width', 5))
        cv2.circle(s.image, (int(tx), int(ty)), m_radius, m_color, m_width)

        return "OK"
    except Exception as e:
        s.log(0, f"ERROR: alpacatelescope: {str(e)}")
        return f"Error: {str(e)}"
