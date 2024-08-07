'''
allsky_telescopemarker.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve the current telescope position from ASCOM Remote Server and mark the current pointing position on the image

'''
import allsky_shared as s
import numpy as np
from astropy.coordinates import EarthLocation
from astropy import units as u
import json, cv2, ast
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from socket import timeout

metaData = {
    "name": "Telescope postion marker",
    "description": "Mark the current telescope postion retreived from ASCOM Remote Server in the image",
    "module": "allsky_telescopemarker",
    "version": "v0.1",   
    "events": [
        "night",
        "day"
    ],
    "experimental": "true", 
    "arguments":{
        "observer_lat": "48.58",
        "observer_lon": "8.0",
        "observer_height": "130",
        "image_lat": "48.58",
        "image_lon": "8.0",
        "image_height": "132",
        "image_flip": "None",
        "camera_azimuth": "160.0",
        "margin": "60",
        "telescope_marker_radius": "30",
        "telescope_marker_width": "5",
        "telescope_marker_color": "(0,0,255)",
        "telescope_server": "http://192.168.178.109:11111",
        "telescope_alt": "/api/v1/telescope/0/altitude",
        "telescope_az": "/api/v1/telescope/0/azimuth",
        "telescope_default": "(0.0,0.0)"
    },
    "argumentdetails": {
        "observer_lat": {
            "required": "false",
            "description": "Telescope's latitude",
            "help": "Define telescope postion, use current Allsky latitude if left empty"
        },
        "observer_lon": {
            "required": "false",
            "description": "Telescope's itude",
            "help": "Define telescope postion, use current Allsky itude if left empty"
        },
        "observer_height": {
            "required": "false",
            "description": "Telescope's altitude [m]",
            "help": "Define telescope altutude, use 0 if left empty"
        },
        "image_lat": {
            "required": "false",
            "description": "Allsky's latitude",
            "help": "Define allsky postion, use current Allsky latitude if left empty"
        },
        "image_lon": {
            "required": "false",
            "description": "Allsky's itude",
            "help": "Define allsky postion, use current Allsky itude if left empty"
        },
        "image_height": {
            "required": "false",
            "description": "Allsky's altitude [m]",
            "help": "Define allsky altutude, use 0m if left empty"
        },
        "image_flip": {
            "required": "true",
            "description": "Flip x,y coordinates",
            "help": "Flip coordinates to match sensor/lens output and AllSky settings",            
            "type": {
                "fieldtype": "select",
                "values": "None,Horizontal,Vertical,Both",
                "default": "None"
            }     
        },
        "camera_azimuth": {
            "required": "false",
            "description": "Allsky's sensor azimuth orentiation [°]",
            "help": "Define allsky sensor azimuth, use 0° (top is pointing north in circular fisheye image) if left empty"
        },
        "margin": {
            "required": "false",
            "description": "Allsky's image border [px]",
            "help": "Margin from squared image to horizon fisheye lense, use 0 px if left empty"
        },
        "telescope_marker_radius": {
            "required": "false",
            "description": "Telescope marker radius [px]",
            "help": "Size of the telescope marker, use 30px if left empty"
        },
        "telescope_marker_width": {
            "required": "false",
            "description": "Telescope marker width [px]",
            "help": "Size of the telescope marker, use 5px if left empty"
        },
        "telescope_marker_color": {
            "required": "false",
            "description": "Telescope marker color [(r,g,b)]",
            "help": "RGB tuple of the telescope marker color, use red (0,0,255) if left empty"
        },
        "telescope_server": {
            "required": "true",
            "description": "Telescope server address [URL]",
            "help": "HTTP base URL of the ASCOM Remote Server"
        },
        "telescope_alt": {
            "required": "true",
            "description": "Telescope server altitude API url [path]",
            "help": "API query URL of the ASCOM Remote Server for the telescope altitude (https://ascom-standards.org/api/#/Telescope%20Specific%20Methods)"
        },
        "telescope_az": {
            "required": "true",
            "description": "Telescope server altitude API url [path]",
            "help": "API query URL of the ASCOM Remote Server for the telescope azimuth (https://ascom-standards.org/api/#/Telescope%20Specific%20Methods)"
        },
        "telescope_default": {
            "required": "false",
            "description": "Telescope fallback position [(0.0,0.0)]",
            "help": "Default telescope position if ASCOM Remote Server query fails"
        }             
    },
    "changelog": {
        "v0.1" : [
            {
                "author": "Frank Hirsch",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Test"
            }
        ]                                        
    }            
}


def get_telescope_position(telescope_server, telescope_alt, telescope_az, telescope_default):
    """
    Read current postion from ASCOM Remote Server
    
    :param telescope_server: Telescope server address
    :param telescope_alt: Telescope altitude position URL
    :param telescope_az: Telescope azimuth position URL
    """
    
    try:
        # store the response of ra URL 
        response_alt = json.loads(urlopen(telescope_server + telescope_alt, timeout=1).read().decode('utf-8'))['Value']
        # store the response of dec URL 
        response_az = json.loads(urlopen(telescope_server + telescope_az, timeout=1).read().decode('utf-8'))['Value']
        
    except URLError as error:
        # return default position
        return telescope_default
        
    try: 
        # return current postion (ra, dec)
        return response_alt, response_az
    
    except ValueError as e:
        # return default position
        return telescope_default

def rotate_azimuth(az, camera_azimuth):
    """
    Rotate the azimuth coordinate by the camera's azimuth orientation.

    :param az: Azimuth in degrees
    :param camera_azimuth: Camera's azimuth orientation in degrees
    :return: Rotated azimuth in degrees
    """
    return (az - camera_azimuth) % 360

def alt_az_to_pixel(alt, az, image_width, image_height, margin):
    """
    Convert altitude and azimuth to pixel coordinates on a fisheye image.

    :param alt: Altitude in degrees
    :param az: Azimuth in degrees
    :param image_width: Width of the image in pixels
    :param image_height: Height of the image in pixels
    :param margin: Additional margin around the image in pixels
    :return: (x, y) pixel coordinates
    """
    # Convert degrees to radians
    alt_rad = np.deg2rad(alt)
    az_rad = np.deg2rad(az)

    # Compute the radius of the fisheye projection
    radius = (min(image_width, image_height) - 2 * margin) / 2

    # Fisheye projection equations
    x = image_width / 2 + radius * np.sin(az_rad) * np.cos(alt_rad)
    y = image_height / 2 - radius * np.cos(az_rad) * np.cos(alt_rad)

    return int(x), int(y)

def mark_telescope_position(s, alt, az, observer_lat, observer_lon, observer_height, image_lat, image_lon, image_height, image_flip, camera_azimuth, margin, telescope_marker_radius, telescope_marker_color, telescope_marker_width):
    """
    Mark the position of the telescope on the fisheye image based on RA and Dec.

    :param ra: Right ascension in degrees
    :param dec: Declination in degrees
    :param observer_lat: Latitude of the observer
    :param observer_lon: Longitude of the observer
    :param observer_height: Height of the observer in meters
    :param image_lat: Latitude of the fisheye image location
    :param image_lon: Longitude of the fisheye image location
    :param image_height: Height of the fisheye image location in meters
    :param camera_azimuth: Azimuth orientation of the camera in degrees
    :param margin: Additional margin around the image in pixels
    """

    # Create observer location and observation time objects
    observer_location = EarthLocation(lat=observer_lat * u.deg, lon=observer_lon * u.deg, height=observer_height * u.m)

    # Adjust the azimuth based on the camera's orientation
    az = rotate_azimuth(az, camera_azimuth)

    # Convert Alt/Az to pixel coordinates for the image location
    x, y = alt_az_to_pixel(alt, az, s.image.shape[1], s.image.shape[0], margin)

    # Apply image flip option
    if image_flip == "Horizontal" or image_flip == "Both":
        x = s.image.shape[1] - x
    if image_flip == "Vertical" or image_flip == "Both":
        y = s.image.shape[0] - y

    # Draw a red circle to mark the position
    s.image = cv2.circle(s.image, (x - int(telescope_marker_radius/2), y - int(telescope_marker_radius/2)), telescope_marker_radius, telescope_marker_color, telescope_marker_width)
    
    # Save the image with the marked position
    #cv2.imwrite(output_path, s)

def telescopemarker(params, event):
    observer_lat = float(params['observer_lat'])
    observer_lon = float(params['observer_lon'])
    observer_height = float(params['observer_height'])
    image_lat = float(params['image_lat'])
    image_lon = float(params['image_lon'])
    image_height = float(params['image_height'])
    image_flip = params['image_flip']
    camera_azimuth = float(params['camera_azimuth'])
    margin = int(params['margin'])
    telescope_marker_radius = int(params['telescope_marker_radius'])
    telescope_marker_width = int(params['telescope_marker_width'])
    telescope_marker_color = ast.literal_eval(params['telescope_marker_color'])
    telescope_server = params['telescope_server']
    telescope_alt = params['telescope_alt']
    telescope_az = params['telescope_az']
    telescope_default = ast.literal_eval(params['telescope_default'])

    alt, az = get_telescope_position(telescope_server, telescope_alt, telescope_az, telescope_default)
    mark_telescope_position(s, alt, az, observer_lat, observer_lon, observer_height, image_lat, image_lon, image_height, image_flip, camera_azimuth, margin, telescope_marker_radius, telescope_marker_color, telescope_marker_width)

