"""
allsky_mlx90614.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky


"""

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import board
import sys
import numpy as np
import adafruit_mlx90640
import cv2
import os
from datetime import datetime
from datetime import timedelta


class ALLSKYMLX90640(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Generate a thermal image",
		"description": "Generate a thermal image from the MLX90640 IR Sensor",
		"module": "allsky_mlx90640",
		"centersettings": "false",
		"version": "v1.0.2",
		"extradatafilename": "allsky_mlx906040.json",
		"group": "Data Sensor",  
		"extradata": {
			"database": {
				"enabled": "True",
				"table": "allsky_ir",
    			"pk": "id",
    			"pk_type": "int",    
				"include_all": "true"
			},       
			"values": {
				"AS_MLX906040MIN": {
					"name": "${MLX906040MIN}",
					"format": "",
					"sample": "",                
					"group": "IR Camera",
					"description": "Min Temperature (in C)",
					"type": "number"
				},
				"AS_MLX906040MAX": {
					"name": "${MLX906040MAX}",
					"format": "",
					"sample": "",                
					"group": "IR Camera",
					"description": "Max Temperature (in C)",
					"type": "number"
				}				
			}                         
		},
		"events": [
			"periodic",
			"day",
			"night"
		],
		"experimental": "true",
		"arguments": {
			"i2caddress": "",
			"imagefilename": "ir.jpg",
			"resize": "1",
			"logdata": "False"
		},
		"argumentdetails": {
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address (0x33) for the mlx90640. NOTE: This value must be hex, i.e., 0x76.",
				"tab": "Sensor",
				"type": {
					"fieldtype": "i2c"
				}         
			},
			"imagefilename": {
				"required": "false",
				"description": "Image filename",
				"tab": "Sensor",
				"help": "The filename to save the image as. NOTE: Does not need the path. The image will be saved in the overlay images folder."
			},
			"resize": {
				"required": "false",
				"description": "Resize Image",
				"help": "Scales the captured image.",
				"tab": "Sensor",           
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 100,
					"step": 1
				}
			},			
			"logdata": {
				"required": "false",
				"description": "Log Data",
				"help": "Log data and images. **WARNING** This will require a lot of additional disk space.",
				"tab": "Logging",
				"type": {"fieldtype": "checkbox"}
			},
			"graph": {
				"required": "false",
				"tab": "History",
				"type": {
					"fieldtype": "graph"
				}
			}   
		},
		"enabled": "false",
		"changelog": {
			"v1.0.0": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.1": [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Added data logging"
				}
			],
			"v1.0.2": [
				{
					"author": "Michel Moriniaux",
					"authorurl": "https://github.com/MichelMoriniaux",
					"changes": "Added RoI"
				}
			]
		}
	}

	_image_file_name = None
	_log_data = None
	_image_path = None
	_image_thumbnail_path = None
	_frame = None
	_i2c_address = ''
	_scale = 1

	def __init__(self, params, event):
		super().__init__(params, event)

		self._image_file_name = self.get_param('imagefilename', 'ir.jpg')
		self._log_data = self.get_param('logdata', False, bool)
		self._i2c_address = self.get_param('i2caddress', '')
		self._scale = self.get_param('resize', 1, int)

		allsky_overlay_folder = allsky_shared.get_environment_variable('ALLSKY_OVERLAY')
		self._image_path = os.path.join(allsky_overlay_folder, 'images', self._image_file_name )
		self._image_thumbnail_path = os.path.join(allsky_overlay_folder, 'imagethumbnails', self._image_file_name )		

	def _get_allsky_date(self):
		datetime_dow = datetime.now()
		dt = datetime_dow - timedelta(hours=12)
		date_string = dt.strftime("%Y%m%d")
		time_string = dt.strftime("%H%M%S")

		return date_string, time_string

	def _get_image(self):
		if self._i2c_address != '':
			try:
				i2c_address_int = int(self._i2c_address, 16)
			except Exception as e:
				eType, eObject, eTraceback = sys.exc_info()
				self.log(0, f'ERROR in {__file__}: Module (mlx906040) _get_image failed on line {eTraceback.tb_lineno} - {e}')

		i2c = board.I2C()
		if self._i2c_address != '':
			mlx = adafruit_mlx90640.MLX90640(i2c, i2c_address_int)
		else:
			mlx = adafruit_mlx90640.MLX90640(i2c)

		mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
		self._frame = np.zeros((24, 32))
		mlx.getFrame(self._frame.ravel())

		# Normalize the data to 0-255 for OpenCV
		frame_normalized = cv2.normalize(self._frame, None, 0, 255, cv2.NORM_MINMAX)
		frame_normalized = frame_normalized.astype(np.uint8)  # Convert to 8-bit

		# Apply a colormap (e.g., COLORMAP_JET or COLORMAP_INFERNO)
		self._raw_image = cv2.applyColorMap(frame_normalized, cv2.COLORMAP_INFERNO)

	def _save_images(self):
		# Resize the image to make it clearer
		temp_image = cv2.resize(self._raw_image, (32*self._scale, 24*self._scale), interpolation=cv2.INTER_CUBIC)
		cv2.imwrite(self._image_path, temp_image)		

		width = self._raw_image.shape[1]
		scale_percent = (90 / width) * 100

		width = int(self._raw_image.shape[1] * scale_percent / 100)
		height = int(self._raw_image.shape[0] * scale_percent / 100)
		dim = (width, height)

		resized = cv2.resize(self._raw_image, dim, interpolation=cv2.INTER_AREA)
		cv2.imwrite(self._image_thumbnail_path, resized)

	def save_extra_data(self):
		min_temp = np.min(self._frame)
		max_temp = np.max(self._frame)
		extra_data = {
			'AS_MLX906040MIN': float(min_temp),
			'AS_MLX906040MAX': float(max_temp)
		}

		allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])

	def run(self):
		self._get_image()
		self._save_images()
		self.save_extra_data()

def mlx90640(params, event):
	allsky_mlx906040 = ALLSKYMLX90640(params, event)
	result = allsky_mlx906040.run()

	return result

def mlx90640_cleanup():
	moduleData = {
		"metaData": ALLSKYMLX90640.meta_data,
		"cleanup": {
			"files": {
				ALLSKYMLX90640.meta_data['extradatafilename']
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)
