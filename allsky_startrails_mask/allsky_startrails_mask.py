'''
allsky_startrails_mask.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

Used to apply a mask and date text overlay to the startrails image after it has been generated.

'''

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import os
import subprocess
import pwd
import datetime
from pathlib import Path
import cv2
import shutil
import numpy as np

# GLOBALS
ALLSKY_HOME = allsky_shared.getEnvironmentVariable("ALLSKY_HOME")
ALLSKY_IMAGES = allsky_shared.getEnvironmentVariable("ALLSKY_IMAGES", fatal=True)
base_dir = allsky_shared.getSetting("imagepath") or ALLSKY_IMAGES
ALLSKY_CONFIG = allsky_shared.getEnvironmentVariable("ALLSKY_CONFIG", fatal=True)
ALLSKY_TMP = allsky_shared.ALLSKY_TMP
EXT = allsky_shared.get_environment_variable("ALLSKY_EXTENSION", fatal=True)

default_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")	# today minus one

class ALLSKYSTARTRAILSMASK(ALLSKYMODULEBASE):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.process_date = default_date
		self.process_dir = os.path.join(ALLSKY_IMAGES, default_date)

	meta_data = {
		"name": "Startrails Cleanup: Mask and Text Overlay",
		"description": "Cleanup Startrails images by applying a mask and optionally adding the imaging date.",
		"module": "allsky_startrails_mask", 
		"version": "v1.0.0",   
		"centersettings": "false",
		"testable": "true",
		"group": "Image Adjustments",
		"pythonversion": "3.10.0",
		"events": [
			"nightday"
		],
		"experimental": "false",
		"extradatafilename": "",
		
		"arguments": {
			"startrails_mask" : "",
			"date_overlay" : "true",
			"date_format" : "%Y-%m-%d",
			"date_font_name" : "Duplex",
			"date_font_color" : "#ff0000",
			"date_font_size" : "3",
			"date_font_thickness" : "2.5",
			"date_x" : "20",
			"date_y" : "120",
			"startrails_upload": "true",

			"process_date" : "",
			"startrails_test" : ""
		},

		"argumentdetails" : {   
			"startrails_mask" : {
				"required": "false",
				"description": "Mask final image",
				"help": "Select or create a mask to remove items such as blurred overlay text from the final startrails image. (blank for none)",
				"tab": "Settings",
				"type": {
					"fieldtype": "image"
				}
			},

			"date_overlay": {
				"required": "false",
				"description": "Display imaging date",
				"help": "Print date (of the night) on the image.",
				"tab": "Settings",

				"type": {
					"fieldtype": "checkbox"
				}
			},
			"date_format": {
				"required": "false",
				"description": "Display Format",
				"help": "Format of the date overlay (No time component).",
				"tab": "Settings",
				"layout" : {
					"row": "Date",
					"title":"Image Date",
					"width": 3
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"date_x": {
				"required": "false",
				"description": "X Position",
				"help": "X (horizontal) position for left edge of displayed date.",
				"tab": "Settings",
				"layout" : {
					"row": "Date",
					"title":"Position",
					"width": 3
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 10
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}           
			},
			"date_y": {
				"required": "false",
				"description": "Y Position",
				"help": "Y (vertical) position for bottom edge of displayed date.",
				"tab": "Settings",
				"layout" : {
					"row": "Date",
					"title":"Position",
					"width": 3
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 5000,
					"step": 10
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}           
			},

			"date_font_name": {
				"required": "true",
				"description": "Font Style",
				"help": "Select Font",
				"tab": "Settings",
				"layout" : {
					"row": "date font",
					"title":" ",
					"width": 3
				},				
				"type": {
					"fieldtype": "select",
					"values": "Simplex,Plain,Duplex,Complex,Complex Small,Triplex,Script Simplex,Script Complex"
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				} 
			},
			"date_font_color": {
				"required": "false",
				"description": "Color (HEX)",
				"help": "Font color.  #ffffff is white.  See the documentation for a description of this field.<br><hr>",
				"tab": "Settings",
				"layout" : {
					"row": "date font",
					"title":"Font",
					"width": 3
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"date_font_size": {
				"required": "false",
				"description": "Size",
				"help": "Font Size.",
				"tab": "Settings",
				"layout" : {
					"row": "date font",
					"title":"Font",
					"width": 3
				},
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 0.1
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}           
			},
			"date_font_thickness": {
				"required": "false",
				"description": "Weight",
				"help": "Font Line thickness.",
				"tab": "Settings",
				"layout" : {
					"row": "date font",
					"title":"Font",
					"width": 3
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0.5,
					"max": 5,
					"step": 0.1
				},
				"filters": {
					"filter": "date_overlay",
					"filtertype": "show",
					"values": [
						"true"
					]
				}           
			},

			"startrails_upload": {
				"required": "false",
				"description": "Upload modified image",
				"help": "Enable to upload the startrails image to websites and/or remote server when processing is complete.",
				"tab": "Settings",
				
				"type": {
					"fieldtype": "checkbox"
				}
			},

			"settings_notice": {
				"message": "<ul><li>If you select to upload the modified startrails image you can disable the upload startrails option on the Allsky Settings page to prevent double uploads.</li><li>Use options on the [Testing - Debug] tab to validate your setup.</li></ul>",
				"tab": "Settings",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				}
			},

			"process_date": {
				"required": "false",
				"description": "Folder to process",
				"help": "Images folder to process.  eg \"20250801\"  -- Will use the prior nights folder if left blank.",
				"tab": "Testing - Debug"
			},
			"startrails_test" : {
				"required": "false",
				"description": "Test Action",
				"help": "",
				"tab": "Testing - Debug",
				"type": {
					"fieldtype": "select",
					"values": "Process Startrails,Process and Upload,Upload Only,Quick Setup Test"
				}
			},

			"fake_field": {
				"required": "false",
				"description": "Has to be here so alert box is indented in layout/row (filtered to be hidden)",
				"help": "",
				"tab": "Testing - Debug",
				"layout" : {
					"row": "timelapse_testing2",
					"title":" ",
					"width": 0
				},
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "startrails_test",
					"filtertype": "show",
					"values": [
						"BARF!"
					]
				}
			},
			"test_quicktimelapse_notice": {
				"message": "Applies your mask and text overlay settings to a copy of the current Allsky image to validate your setup. Output can be viewed below, or from the images/test folder until removed at the end of each night.<br><p style=\"margin-left: 120px;\"><a href=\"images/test/startrails/startrails-test.jpg\" target=\"_blank\">View Test Image</a></span></p>",
				"tab": "Testing - Debug",
				"layout" : {
					"row": "timelapse_testing2",
					"title":" ",
					"width": 12
				},
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "light"
						}
					}
				},
				"filters": {
					"filter": "startrails_test",
					"filtertype": "show",
					"values": [
						"Quick Setup Test"
					]
				}
			},
			"test_notice": {
				"message": "Using the [Test Module] button:  <ul><li>Choose a folder to process startrails (or leave blank for 'last night')</li><li>Choose to process and or upload the startrails file to your local or remote websites or servers.</li><li>This will overwrite existing files on your pi and/or the destination.</li><li>Or choose 'Quick Setup Test' for a validation of mask and text overlay settings on a sample file.</li></ul>",
				"tab": "Testing - Debug",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				}
			}
		},
		"enabled": "true",
		"changelog": {
			"v1.0.0": [
				{
					"author": "Kentner Cottingham",
					"authorurl": "https://github.com/AllskyTeam",
					"changes": [
						"Initial release",
						"Add mask and date text overlay to Startrails images"
					]
				}
			]
		}
	}

	def _cleanup_test_data(self):
		try:
			test_dir = os.path.join(base_dir, "test")
			if os.path.exists(test_dir):
				shutil.rmtree(test_dir)
				allsky_shared.log(4, "Removed test images folder")
		except Exception as ex:
			allsky_shared.log(1, f"Error removing test images folder: {ex}")

	def _run_script(self, script: Path, *args: str) -> tuple[int, str, str]:

		script_str = str(script)
		
		# Ensure output tokens are separate already in *args
		if os.access(script, os.X_OK):
			cmd = [script_str, *args]
		
		if not os.access(script_str, os.X_OK):
			cmd = ["bash", script_str, *args]		# Fallback to bash if not executable

		# Avoid sudo permission issues in debug runs by executing as ALLSKY_OWNER when available.
		if self.debugmode:
			username = allsky_shared.get_environment_variable("ALLSKY_OWNER")
			if username:
				cmd = ["runuser", "-u", username, "--", script_str, *args]
				if not os.access(script_str, os.X_OK):
					cmd = ["runuser", "-u", username, "--", "bash", script_str, *args]
			else:
				allsky_shared.log(1, "WARNING: ALLSKY_OWNER not set; running script directly in debug mode")

		allsky_shared.log(4, f"DEBUG: Script Args - {cmd}")

		try:
			script_result = subprocess.run(cmd, capture_output=True, text=True, check=False)
			if script_result.returncode == 0:
				allsky_shared.log(3, f"INFO: Successful: {script_str}")
			else:
				allsky_shared.log(0, f"ERROR: {script_str} - rc={script_result.returncode}\nSTDERR:\n{script_result.stderr}")
			return script_result.returncode, script_result.stdout, script_result.stderr
		
		except Exception as e:
			return 1, "", str(e)

	def _set_permissions_to_allskyowner(self, path: Path, flag) -> None:
		"""Set file permissions, with debug logging.

		Args:
			path (Path): Path to the file
			flag (str): "file" or "dir" to determine permissions.
				When "dir" is used, ownership is applied recursively, directories are set to 775,
				and files are set to 664.
		"""
		mode = 0o664 if flag == "file" else 0o775
		
		user = allsky_shared.get_environment_variable("ALLSKY_OWNER")
		uid = pwd.getpwnam(user).pw_uid
		gid = pwd.getpwnam(user).pw_gid

		try:
			if flag == "dir":
				subprocess.run(["sudo", "-n", "chown", "-R", f"{uid}:{gid}", str(path)], check=True)
				subprocess.run(["sudo", "-n", "find", str(path), "-type", "d", "-exec", "chmod", "775", "{}", "+"], check=True)
				subprocess.run(["sudo", "-n", "find", str(path), "-type", "f", "-exec", "chmod", "664", "{}", "+"], check=True)
			else:
				subprocess.run(["sudo", "-n", "chown", f"{uid}:{gid}", str(path)], check=True)
				subprocess.run(["sudo", "-n", "chmod", f"{mode:o}", str(path)], check=True)
			
			allsky_shared.log(4, f"DEBUG: Set permissions for {path} to {oct(mode)} and ownership to {user}")
		except Exception as e:
			allsky_shared.log(0, f"ERROR: Failed to set permissions for {path}: {e}")

	def _hex_to_bgr(self, hex_color):
		s = hex_color.lstrip("#")
		if len(s) == 3:
			s = "".join(ch * 2 for ch in s)
		if len(s) != 6:
			raise ValueError("Invalid hex color")
		r = int(s[0:2], 16)
		g = int(s[2:4], 16)
		b = int(s[4:6], 16)
		return (b, g, r)

	def _add_text(self, image_path):
		'''overlay text on image after applying mask.
		'''
		# array for font mapping to cv2 fonts from date_font_name metadata.
		font_map = {
			"SIMPLEX": cv2.FONT_HERSHEY_SIMPLEX,
			"PLAIN": cv2.FONT_HERSHEY_PLAIN,
			"DUPLEX": cv2.FONT_HERSHEY_DUPLEX,
			"COMPLEX": cv2.FONT_HERSHEY_COMPLEX,
			"COMPLEX SMALL": cv2.FONT_HERSHEY_COMPLEX_SMALL,
			"TRIPLEX": cv2.FONT_HERSHEY_TRIPLEX,
			"SCRIPT SIMPLEX": cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
			"SCRIPT COMPLEX": cv2.FONT_HERSHEY_SCRIPT_COMPLEX
		}

		def put_text_on_image(image, text, position, font, font_size, color, thickness):
			"""Helper function to overlay text on an image."""
			cv2.putText(image, text, position, font, font_size, color, thickness)
			return image

		img = cv2.imread(image_path)

		# add date overlay text to image
		date_overlay=self.get_param("date_overlay", True, bool)
		
		if self.debugmode:
			startrails_test =self.get_param('startrails_test', "None", str)
			if "test" in startrails_test.lower():
				# print 'MASK AND TEXT OVERLAY TEST' in red in center of image
				test_text = "STARTRAILS MASK AND TEXT DEBUG IMAGE"
				test_font = cv2.FONT_HERSHEY_DUPLEX
				test_font_color = (0, 0, 255)  # Red color in BGR
				test_font_size = 4.0
				test_font_thickness = 5
				(text_w, text_h), baseline = cv2.getTextSize(test_text, test_font, test_font_size, test_font_thickness)

				test_x = img.shape[1] // 2 - text_w // 2  # Centered horizontally
				test_y = img.shape[0] // 2 + text_h // 2  # Centered vertically
				
				img = put_text_on_image(img, test_text, (test_x, test_y), test_font, test_font_size, test_font_color, test_font_thickness)
				
				cv2.imwrite(image_path, img)

		if date_overlay:
			date_object = datetime.datetime.strptime(self.process_date, "%Y%m%d")
			date_format = self.get_param("date_format", "%Y-%m-%d", str)
			
			date_text = date_object.strftime(date_format)
			date_font = font_map.get(self.get_param("date_font_name", "SIMPLEX", str).upper(), cv2.FONT_HERSHEY_SIMPLEX)
			date_font_color = self._hex_to_bgr(self.get_param("date_font_color", "#FFFFFF", str))
			date_font_size = self.get_param("date_font_size", 2.0, float)
			date_font_thickness = self.get_param("date_font_thickness", 2, int)
			date_x = self.get_param("date_x", 20, int)
			date_y = self.get_param("date_y", 20, int)
			
			#allsky_shared.log(3, f"INFO: Overlaying text '{overlay_text}' on image.")
			img = put_text_on_image(img, date_text, (date_x, date_y), date_font, date_font_size, date_font_color, date_font_thickness)
			cv2.imwrite(image_path, img)
			allsky_shared.log(4, f"INFO: Text overlay completed.")
	
	def _do_startrails(self):
		
		mask_file = self.get_param('startrails_mask',"", str)
		upload = self.get_param('startrails_upload', False, bool)		# from module settings (overrides allsky website and server settings)

		startrails_test = self.get_param('startrails_test', "", str)
		type = "startrails"
		result = ""
		setup_test = False

		# set input directory and settings
		if self.debugmode:
			process = "process" in startrails_test.lower()
			upload = "upload" in startrails_test.lower()		# returns boolean
			setup_test = "test" in startrails_test.lower()	# returns boolean
		else:
			process = True		# always process when not in debug mode

		output_dir = os.path.join(self.process_dir, "startrails")
		
		stars_image = f"{ALLSKY_IMAGES}/{self.process_date}/startrails/startrails-{self.process_date}.{EXT}"

		if setup_test:
			if not allsky_shared.is_file_readable(stars_image):
				stars_image = (f"{ALLSKY_TMP}/current_images/image.{EXT}\n")
			
			output_dir = os.path.join(ALLSKY_IMAGES, "test", "startrails")		# set test folder as output folder for quick setup test
			process = True
			upload = False
			startrails_filename = f"startrails-test.{EXT}"
			print(f"DEBUG: Quick Setup Test: Creating {output_dir}/{startrails_filename} from {stars_image}")
		else:
			if not allsky_shared.is_file_readable(stars_image):
				allsky_shared.log(0, f"ERROR: Startrails image not found for {self.process_date}.  Please generate startrails first.")
				return f"Startrails image not found for {self.process_date}.  Please generate startrails first."
			
			startrails_filename = f"startrails-{self.process_date}.{EXT}"
	
		startrails_fullpath = os.path.join(output_dir, startrails_filename)
		
		# process startrails
		if process:
			allsky_shared.log(4, f"INFO: Starting Startrails cleanup.")
			allsky_shared.check_and_create_directory(output_dir)  # make dir if not already present

			if mask_file:
				img = cv2.imread(stars_image)
				if img is None:
					allsky_shared.log(0, f"ERROR: unable to read Startrails image for masking: {stars_image}")
				else:
					masked_stars = allsky_shared.mask_image(img, mask_file)
					if masked_stars is not None and masked_stars.any():
						masked_img=cv2.imwrite(startrails_fullpath, masked_stars)
						if masked_img:
							allsky_shared.log(3, f"INFO: Startrails mask applied")
						else:
							allsky_shared.log(0, f"ERROR: unable to save masked Startrails image.")
					else:
						allsky_shared.log(0, f"ERROR: unable to apply Startrails mask.")
			
			date_overlay=self.get_param("date_overlay", True, bool)

			if date_overlay:
				img_with_text = self._add_text(startrails_fullpath)	
				if img_with_text is not None:
					cv2.imwrite(startrails_fullpath, img_with_text)
						
			allsky_shared.log(4, f"INFO: Startrails modified successfully: {startrails_fullpath}")
			
			if self.debugmode:
				# update permissions to ALLSKY_OWNER for output files and directories when in debug mode
				if setup_test: self._set_permissions_to_allskyowner(os.path.join(ALLSKY_IMAGES, "test"), "dir")
				self._set_permissions_to_allskyowner(startrails_fullpath, "file")

			# create local thumbnail & save
			#NOTE: using Allsky thumbnail.sh handles permissions correctly for that sub-process.
			thumb_script = Path(ALLSKY_HOME) / "scripts" / "utilities" / "thumbnail.sh"
			thumb_date = "test" if setup_test else self.process_date
			rc, out, err = self._run_script(
				thumb_script,
				"-t", "startrails",
				"-d", thumb_date,
				"-S", startrails_filename,
				#"-D", startrails_filename,
				"--force",
			)
			if rc != 0:
				allsky_shared.log(0, f"ERROR: Startrails cleanup - thumbnail.sh failed with error: {err}")

		if upload:
			## Use generateForDay.sh --upload as this covers all the upload scenarios for local and remote websites and servers.
			## e.g:  generateForDay.sh --upload --startrails YYYYMMDD
			script_path = os.path.join(ALLSKY_HOME, "scripts", "generateForDay.sh")
			process_dir = self.process_date
			upload_rc, out, err = self._run_script(script_path, "--upload", "--startrails", process_dir)

			if upload_rc == 0:
				allsky_shared.log(4, f"INFO: Startrails Cleanup Module uploaded image successfully")
			else:
				allsky_shared.log(0, f"ERROR: Startrails Cleanup Module failed to upload Startrails (rc={upload_rc}). See stderr:\n{err}")

		result = "Startrails cleanup process complete"
		allsky_shared.log(4, f"INFO:  {result}")
	
		return result

	# Main Module Function
	def run(self):
		self.process_date = default_date
		self.process_dir = os.path.join(ALLSKY_IMAGES, default_date)

		if not self.debugmode: self._cleanup_test_data()	# removes test folder when run under normal mode in Night-Day pipeline

		# set a couple things if running from test button
		if self.debugmode:
			startrails_test =self.get_param('startrails_test', "None", str)

			requested_process_date = self.get_param('process_date', "", str)
			if requested_process_date:
				if requested_process_date.startswith("/"):
					self.process_dir = requested_process_date
					#need to get just the date part for use in scripts
					self.process_date = requested_process_date.split("/")[-1]
				else:
					self.process_date = requested_process_date
					self.process_dir = os.path.join(ALLSKY_IMAGES, self.process_date)
			else:
				self.process_date = default_date
				self.process_dir = os.path.join(ALLSKY_IMAGES, default_date)
		else:
			self.process_date = default_date
			self.process_dir = os.path.join(ALLSKY_IMAGES, default_date)
	
		stars_result = self._do_startrails()
						
		return 

def startrails_mask(params, event):
	allsky_startrails_mask = ALLSKYSTARTRAILSMASK(params, event)
	result = allsky_startrails_mask.run()

	return result 

def startrails_mask_cleanup():
	moduleData = {
		"metaData": ALLSKYSTARTRAILSMASK.meta_data,
		"cleanup": {
			"files": {
				ALLSKYSTARTRAILSMASK.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)