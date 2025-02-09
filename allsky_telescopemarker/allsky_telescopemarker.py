'''
allsky_telescopemarker.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will retrieve the current telescope position from ASCOM Remote Server and mark the current pointing position on the image

'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
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
	"version": "v1.0.1",
	"centersettings": "false",
	"testable": "true",   
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
	    "telescope_marker_radius": {
	        "required": "false",
	        "description": "Telescope marker radius",
	        "help": "Size of the telescope marker in pixels, defaults to 30px"
	    },
	    "telescope_marker_width": {
	        "required": "false",
	        "description": "Telescope marker width",
	        "help": "Size of the telescope marker in pixels, defaults to 5px"
	    },
	    "telescope_marker_color": {
	        "required": "false",
	        "description": "Telescope marker color",
	        "help": "The colour to use for the marker",
	        "type": {
	            "fieldtype": "colour"
	        }          
	    },     
		"observer_position": {
      		"description": "Telescope's position",
			"help": "Define telescope postion, use current Allsky position if left empty",
			"tab": "Telescope",
			"lat": {
				"id": "observer_lat"
			},
			"lon": {
				"id": "observer_lon"				
			},
			"height": {
				"id": "observer_height"				
			},
	        "type": {
	            "fieldtype": "position"
	        }     
		},
	    "image_flip": {
	        "required": "true",
	        "description": "Flip x,y coordinates",
	        "help": "Flip coordinates to match sensor/lens output and AllSky settings",
			"tab": "Allsky",                     
	        "type": {
	            "fieldtype": "select",
	            "values": "None,Horizontal,Vertical,Both",
	            "default": "None"
	        }     
	    },
	    "camera_azimuth": {
	        "required": "false",
	        "description": "Allsky's sensor azimuth orentiation",
			"tab": "Allsky",                     
	        "help": "Define allsky sensor azimuth, use 0° (top is pointing north in circular fisheye image) if left empty"
	    },
	    "margin": {
	        "required": "false",
	        "description": "Allsky's image border",
			"tab": "Allsky",                     
	        "help": "Margin from squared image to horizon fisheye lense in pixels, defaults to 0 px"
	    },
	    "telescope_alt": {
	        "required": "true",
			"tab": "Ascom",          
	        "description": "Telescope server altitude API url",
	        "help": "API query URL of the ASCOM Remote Server for the telescope altitude (https://ascom-standards.org/api/#/Telescope%20Specific%20Methods)",
	        "type": {
	            "fieldtype": "url"
	        }          
	    },
	    "telescope_az": {
	        "required": "true",
			"tab": "Ascom",          
	        "description": "Telescope server altitude API url",
	        "help": "API query URL of the ASCOM Remote Server for the telescope azimuth (https://ascom-standards.org/api/#/Telescope%20Specific%20Methods)",
	        "type": {
	            "fieldtype": "url"
	        }         
	    },
	    "telescope_default": {
	        "required": "false",
			"tab": "Ascom",          
	        "description": "Telescope fallback position",
	        "help": "Default telescope position if ASCOM Remote Server query fails. Defaults to [(0.0,0.0)]"
	    }             
	},
	"changelog": {
	    "v0.1" : [
	        {
	            "author": "Frank Hirsch",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Initial Test"
	        }
	    ],
	    "v1.0.1" : [
	        {
	            "author": "Alex Greenland",
	            "authorurl": "https://github.com/allskyteam",
	            "changes": "Updates for new module system"
	        }
	    ]                                            
	}            
}


class ALLSKYTELESCOPEMARKER(ALLSKYMODULEBASE):
    
	def _get_telescope_position(self, telescope_alt, telescope_az, telescope_default):
		"""
		Read current postion from ASCOM Remote Server
		
		:param telescope_server: Telescope server address
		:param telescope_alt: Telescope altitude position URL
		:param telescope_az: Telescope azimuth position URL
		"""
		
		try:
			# store the response of ra URL 
			response_alt = json.loads(urlopen(telescope_alt, timeout=1).read().decode('utf-8'))['Value']
			# store the response of dec URL 
			response_az = json.loads(urlopen(telescope_az, timeout=1).read().decode('utf-8'))['Value']
			
		except URLError as error:
			# return default position
			return telescope_default
			
		try: 
			# return current postion (ra, dec)
			return response_alt, response_az
		
		except ValueError as e:
			# return default position
			return telescope_default

	def _rotate_azimuth(self, az, camera_azimuth):
		"""
		Rotate the azimuth coordinate by the camera's azimuth orientation.

		:param az: Azimuth in degrees
		:param camera_azimuth: Camera's azimuth orientation in degrees
		:return: Rotated azimuth in degrees
		"""
		return (az - camera_azimuth) % 360

	def _alt_az_to_pixel(self, alt, az, image_width, image_height, margin):
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

	def run(self):
		observer_lat = self.get_param('observer_lat', 0, float) 
		observer_lon = self.get_param('observer_lon', 0, float) 
		observer_height = self.get_param('observer_height', 0, float) 
		
		image_lat = self.get_param('image_lat', 0, float) 
		image_lon = self.get_param('image_lon', 0, float) 
		image_height = self.get_param('image_height', 0, float) 
  
		image_flip = self.get_param('image_flip', 'None', str, True) 
		camera_azimuth = self.get_param('camera_azimuth', 0, float) 
		margin = self.get_param('margin', 0, int) 
  
		telescope_marker_radius = self.get_param('telescope_marker_radius', 30, int) 
		telescope_marker_width = self.get_param('telescope_marker_width', 5, int) 
		telescope_marker_color = self.get_param('telescope_marker_color', '255,0,0', str, True) 
  
		telescope_alt = self.get_param('telescope_alt', '', str, True) 
		telescope_az = self.get_param('telescope_az', '', str, True) 

		telescope_default = self.get_param('telescope_default', '(0.0, 0.0)', str, True) 
		telescope_default = ast.literal_eval(telescope_default)

		alt, az = self._get_telescope_position(telescope_alt, telescope_az, telescope_default)


		# Create observer location and observation time objects
		observer_location = EarthLocation(lat=observer_lat * u.deg, lon=observer_lon * u.deg, height=observer_height * u.m)

		# Adjust the azimuth based on the camera's orientation
		az = self._rotate_azimuth(az, camera_azimuth)

		# Convert Alt/Az to pixel coordinates for the image location
		x, y = self._alt_az_to_pixel(alt, az, allsky_shared.image.shape[1], allsky_shared.image.shape[0], margin)

		# Apply image flip option
		if image_flip == "Horizontal" or image_flip == "Both":
			x = allsky_shared.image.shape[1] - x
		if image_flip == "Vertical" or image_flip == "Both":
			y = allsky_shared.image.shape[0] - y

		# Draw a red circle to mark the position
		allsky_shared.image = cv2.circle(allsky_shared.image, (x - int(telescope_marker_radius/2), y - int(telescope_marker_radius/2)), telescope_marker_radius, telescope_marker_color, telescope_marker_width)
		
		# Save the image with the marked position
		#cv2.imwrite(output_path, s)


def telescopemarker(params, event):
	allsky_telescope_marker = ALLSKYTELESCOPEMARKER(params, event)
	result = allsky_telescope_marker.run()

	return result   