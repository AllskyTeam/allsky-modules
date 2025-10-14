import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import cv2
import numpy as np
import discord
from discord import SyncWebhook, File
from urllib.parse import urlparse
from io import BytesIO

class ALLSKYDISCORD(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Post Image to Discord",
		"description": "Post an image to a Discord server",
		"version": "v1.0.3",
		"pythonversion": "3.9.0",
		"centersettings": "false",
		"testable": "true", 
		"module": "allsky_discordsend",
		"group": "Data Export", 
		"events": [
			"day",
			"night",
			"nightday"
		],
		"experimental": "false",    
		"arguments":{
			"dayimage": "false",
			"dayimageannotated" : "true",
			"dayimageurl": "",
			"daycount": 5,
			"nightimage": "false",
			"nightimageannotated" : "true",
			"nightimageurl": "",
			"nightcount": 5,
			"startrails": "false",
			"startrailsimageurl": "",
			"keogram": "false",
			"keogramimageurl": "",
			"timelapse": "false",
			"timelapseimageurl": ""
		},
		"argumentdetails": {
			"dayimage" : {
				"required": "false",
				"description": "Post Day time Images",
				"help": "Post daytime images to the Discord Server.",
				"tab": "Day Time",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"dayimageannotated" : {
				"description": "Send Annotated Image",
				"help": "Send the image after the overlay has been added. This module must be after the Overlay module in the flow.",
				"tab": "Day Time",
				"type": {
					"fieldtype": "checkbox"
				}          
			},        
			"daycount" : {
				"required": "false",
				"description": "Daytime Count",
				"help": "Send every (this number) frames to Discord. This is to prevent flooding the Discord channels.",
				"tab": "Day Time",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 100,
					"step": 1
				}
			},        
			"dayimageurl": {
				"required": "false",
				"tab": "Day Time",            
				"description": "The webhook URL for day time images"
			}, 
			"nightimage" : {
				"required": "false",
				"description": "Post Night time Images",
				"help": "Post nighttime images to the Discord Server.",
				"tab": "Night Time",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"nightimageannotated" : {
				"description": "Send Annotated Image",
				"help": "Send the image after the overlay has been added. This module must be after the Overlay module in the flow.",
				"tab": "Night Time",
				"type": {
					"fieldtype": "checkbox"
				}          
			},          
			"nightcount" : {
				"required": "false",
				"description": "Nighttime Count",
				"help": "Send every (this number) frame to Discord. This is to prevent flooding the Discord channels.",
				"tab": "Night Time",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 100,
					"step": 1
				}
			},         
			"nightimageurl": {
				"required": "false",
				"tab": "Night Time",           
				"description": "The webhook url for night time images"
			},  

			"startrails" : {
				"required": "false",
				"description": "Post Star Trails Images",
				"help": "Post Startrails images to the Discord Server.",
				"tab": "Star Trails",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"startrailsimageurl": {
				"required": "false",
				"tab": "Star Trails",           
				"description": "The webhook url for Star Trails images"
			},  

			"keogram" : {
				"required": "false",
				"description": "Post Keograms Images",
				"help": "Post Keogram images to the Discord Server.",
				"tab": "Keograms",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"keogramimageurl": {
				"required": "false",
				"tab": "Keograms",           
				"description": "The webhook URL for Keograms"
			},  

			"timelapse" : {
				"required": "false",
				"description": "Post Timelapse videos",
				"help": "Post Timelapse videos to the Discord Server.",
				"tab": "Timelapse",
				"type": {
					"fieldtype": "checkbox"
				}          
			},
			"timelapseimageurl": {
				"required": "false",
				"tab": "Timelapse",           
				"description": "The webhook url for Timelapses"
			}      
		},
		"enabled": "false",
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			],
			"v1.0.1" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Issue #161 - Send annotated image"
				}
			],
			"v1.0.3" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Updated for new module systen"
				}
			]                                        
		}              
	}

	def __cv2_discord_file(self, img, file_name):
		img_encode = cv2.imencode('.png', img)[1]
		data_encode = np.array(img_encode)
		byte_encode = data_encode.tobytes()
		byte_image = BytesIO(byte_encode)
		image = discord.File(byte_image, filename=os.path.basename(file_name))
		return image

	def __check_send(self, key, count, tod):
		result = False

		if not self.debugmode:
			try:
				count = int(count)
			# pylint: disable=broad-exception-caught
			except Exception:
				count = 5

			current_count = 0
			if allsky_shared.dbHasKey(key):
				current_count = allsky_shared.dbGet(key)
			else:
				allsky_shared.dbAdd(key, 0)

			current_count = current_count + 1
			allsky_shared.dbUpdate(key, current_count)

			if current_count >= count:
				result = True
				allsky_shared.dbUpdate(key, 0)

			self.log(4, f'INFO: {tod} - Sending after {count} current count is {current_count}, sending {result}')
		else:
			result = True

		return result

	def __validate_url(self, url):
		try:
			result = urlparse(url)
			return all([result.scheme, result.netloc])
		# pylint: disable=broad-exception-caught
		except Exception:
			return False

	def __send_file(self, file_name, sendURL, fileType, use_annotated):
		if self.__validate_url(sendURL):
			if os.path.exists(file_name):
				file_size = os.path.getsize(file_name)
				if file_size < 8000000:
					if use_annotated:
						discord_file = self.__cv2_discord_file(allsky_shared.image, file_name)
					else:
						discord_file = discord.File(file_name)
					webhook = SyncWebhook.from_url(sendURL)
					webhook.send(file=discord_file)
					result = f'{fileType} file {file_name} sent to Discord'
					self.log(4 ,f'INFO: {result}')
				else:
					result = f'{fileType} file {file_name} is too large to send to Discord. File is {file_size} bytes'
					self.log(0, f'ERROR in {__file__}: {result}')
			else:
				result = f'{fileType} file ="{file_name}" not found'
				self.log(0, f'ERROR in {__file__}: {result}')
		else:
			result = f'{fileType} Invalid Discord URL {sendURL}'
			self.log(0, f'ERROR in {__file__}: {result}')

		return result

	def run(self):

		day_image = self.get_param('dayimage', False, bool)  
		day_image_annotated = self.get_param('dayimageannotated', False, bool)  
		day_image_url = self.get_param('dayimageurl', '', str)  
		day_count = self.get_param('daycount', 5, int)  
  
		night_image = self.get_param('nightimage', False, bool)  
		night_image_annotated = self.get_param('nightimageannotated', False, bool)  
		night_image_url = self.get_param('nightimageurl', '', str)  
		night_count = self.get_param('nightcount', 5, int)  

		startrails = self.get_param('startrails', False, bool)  
		startrails_image_url = self.get_param('startrailsimageurl', '', str)  
  
		keogram = self.get_param('keogram', False, bool)  
		keogram_image_url = self.get_param('keogramimageurl', '', str)  

		timelapse = self.get_param('timelapse', False, bool)  
		timelapse_image_url = self.get_param('timelapseimageurl', '', str)  


		result = 'No files sent to Discord'

		if self.event == 'postcapture':
			upload_file = False
			send_url = ''
			counter = 5

			if day_image and allsky_shared.TOD == 'day':
				upload_file = True
				send_url = day_image_url
				counter = day_count
				use_annotated = day_image_annotated

			if night_image and allsky_shared.TOD == 'night':
				upload_file = True
				send_url = night_image_url
				counter = night_count
				use_annotated = night_image_annotated

			db_key = 'discord' + allsky_shared.TOD
			count_ok = self.__check_send(db_key, counter, allsky_shared.TOD.title())

			if upload_file and (count_ok or self.debugmode):
				if self.debugmode:
					allsky_tmp = allsky_shared.getEnvironmentVariable('ALLSKY_TMP', False, self.debugmode)					
					image_file_name = allsky_shared.getEnvironmentVariable('FULL_FILENAME', False, self.debugmode)
					file_name = os.path.join(allsky_tmp, image_file_name)
					allsky_shared.image = cv2.imread(file_name)     
					original_height, original_width = allsky_shared.image.shape[:2]
					new_width = 512
					aspect_ratio = original_height / original_width
					new_height = int(new_width * aspect_ratio)
					allsky_shared.image = cv2.resize(allsky_shared.image, (new_width, new_height), interpolation=cv2.INTER_AREA)
				else:
					file_name = allsky_shared.getEnvironmentVariable('CURRENT_IMAGE')

				result = self.__send_file(file_name, send_url, allsky_shared.TOD.title(), use_annotated)

		if self.event == 'nightday':
			date = allsky_shared.getEnvironmentVariable('DATE')
			date_dir = allsky_shared.getEnvironmentVariable('DATE_DIR')
			full_file_name = allsky_shared.getSetting('filename')
			_, file_extension = os.path.splitext(full_file_name)
			if startrails:
				file_name = os.path.join(date_dir, 'startrails', 'startrails-' + date + file_extension)
				result = self.__sendFile(file_name, startrails_image_url, 'Star Trails', False)

			if keogram:
				file_name = os.path.join(date_dir, 'keogram', 'keogram-' + date + file_extension)
				result = self.__sendFile(file_name, keogram_image_url, 'Keogram', False)

			if timelapse:
				file_name = os.path.join(date_dir, 'allsky-' + date + '.mp4')
				result = self.__sendFile(file_name, timelapse_image_url, 'Timelapse', False)

		return result

def discordsend(params, event):
	allsky_discord = ALLSKYDISCORD(params, event)
	result = allsky_discord.run()

	return result        
