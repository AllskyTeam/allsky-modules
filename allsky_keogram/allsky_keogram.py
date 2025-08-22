import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import os
import subprocess
import datetime
from pathlib import Path

class ALLSKYKEOGRAM(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Allsky Keogram",
		"description": "Creates a keogram.",
		"version": "v0.0.1",
		"pythonversion": "3.10.0",
		"centersettings": "false",
		"testable": "true",
		"module": "allsky_keogram",    
		"group": "Allsky Core",
		"events": [
			"periodic",
			"nightday"
		],
		"experimental": "true",
		
	   	"arguments": {
			"upload" : "",
			"expand" : "",
			"rotation" : "0",
			"resize": "",
			"font_name" : "Simplex",
			"font_color" : "#ffffff",
			"font_size" : 2,
			"font_thickness" : 2,
			"extra_parameters" : "",
			"input_dir" : "",
			"upload_test" : "",
			"show_labels": "Date and Time"
		},
		"argumentdetails" : {

			"expand" : {
				"required": "false",
				"description": "Expand",
				"help": "Enable to expand keogram to the image width. (Will avoid tall skinny images)",
				"tab": "Main Settings",
				"type": {
					"fieldtype": "checkbox"
				}                
			},
			"rotation" : {
				"required": "false",
				"description": "Rotate",
				"help": "(Optional) Number of degrees to rotate the captured images so the North-South meridian would go straight from top to bottom for building the keogram.  <i>+ for counterclockwise, - for clockwise</i><br><i>Original images will not be rotated.</i><hr>",
				"tab": "Main Settings",
				"type": {
					"fieldtype": "spinner",
					"min": -364,
					"max": 364,
					"step": 1
				}
			},
			"upload" : {
				"required": "false",
				"description": "Upload",
				"help": "Enable to upload the keogram to an Allsky Website and/or remote server.<br><i>Note: Website(s) or remote server must be configured in Allsky Settings.</i>",
				"tab": "Main Settings",
				"type": {
					"fieldtype": "checkbox"
				}               
			},
			"resize": {
				"required": "false",
				"description": "Resize",
				"help": "Resize the uploaded image.  Specify a target percent, width, height, or fixed dimensions. (Even numbers only)<ul><li>Percent of original size (eg '50<code>%</code>)</li><li>Height (eg '720<code>h</code>') <i>Width is auto-scaled</i></li><li>Width (eg '1000<code>w</code>')  <i>Height is auto-scaled</i></li><li>Fixed dimensions in WxH (eg '640<code>x</code>480')</li><li>No resizing ('0' or blank)</li></ul>",
				"tab": "Main Settings"
			},

			"show_labels": {
				"required": "false",
				"description": "Show labels",
				"help": "Choose which marker labels will display on the keogram.<hr>",
				"tab": "Font and Extra Options",
				"type": {
					"fieldtype": "select",
					"values": "Date and Time,Time Only,No Labels"
				}              
			},
			"font_name": {
				"required": "true",
				"description": "Font Name",
				"help": "Font name.",
				"tab": "Font and Extra Options",
				"type": {
					"fieldtype": "select",
					"values": "Simplex,Plain,Duplex,Complex,Complex Small,Triplex,Script Simplex,Script Complex"
				}              
			},
			"font_size": {
				"required": "false",
				"description": "Font Size",
				"help": "Font Size.",
				"tab": "Font and Extra Options",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 0.1
				}           
			},
			"font_thickness": {
				"required": "false",
				"description": "Font thickness",
				"help": "Font Line thickness.",
				"tab": "Font and Extra Options",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 1
				}           
			},
			"font_color": {
				"required": "false",
				"description": "Font Color",
				"help": "Font color.  #ffffff is white.  See the documentation for a description of this field.<br><hr>",
				"tab": "Font and Extra Options"
			},
			"extra_parameters": {
				"required": "false",
				"description": "Extra parameters",
				"tab": "Font and Extra Options",
				"help": "Optional additional keogram creation parameters.<br>Run <code>~/allsky/bin/keogram --help</code> for a list of options or see the documentation."
			},

			"test_notice": {
				"message": "These settings only apply when using the [Test Module] button.",
				"tab": "Testing and Debug",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "warning"
						}
					}
				}
			},			
			"input_dir": {
				"required": "false",
				"description": "Directory of Files",
				"help": "The input directory containing image files from which to create a keogram.  eg 20250801",
				"tab": "Testing and Debug"
			},
			"upload_test" : {
				"required": "false",
				"description": "Upload test keogram",
				"help": "Enable to upload the keogram to configured Allsky websites or remote servers when using the [Test Module] button.",
				"tab": "Testing and Debug",
				"type": {
					"fieldtype": "checkbox"
				}               
			},

			"html": {
				"tab": "Help",
				"source": "local",
				"html": "<blockquote>This help is hard coded into the module's config. This is ok for very short text but not good for longer.</blockquote><p>I think this is goign to be disabled so that help can be consolidated in documentation, which is probably a better idea anyway.  Will see about being able to enter some plain text that is not attached to an entry field.</p>",
				"type": {
					"fieldtype": "html"
				}
			},
			"info_notice": {
				"message": "Note: Info class is blue box.",
				"tab": "Help",
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
			"warn_notice": {
				"message": "Note: Warning class is yellow box.",
				"tab": "Help",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "warning"
						}
					}
				}
			}	
		},
		"enabled": "true",
		"changelog": {
			"v0.0.1" : [
				{
					"author": "Kentner Cottingham",
					"authorurl": "https://github.com/AllSkyTeam",
					"changes": [
						"New for Allsky v2025",
						"New features: Inbuilt label & font settings, Rotation, Image resizing",
						"Supports testing module configuration",
						"test module: Upload currently not working due to sudo permissions thing",
						"resize requires updated allsky_shared.py file"
					]
				}
			]                            
		}                 
	}

	def __execute_script(self, script_path: Path, *args: str) -> tuple[int, str, str]:
		"""
		- If 'script' is executable, run directly (works for binaries).
		- Otherwise, try via bash (for text shell scripts).
		Always return (returncode, stdout, stderr) of primitives.
		"""
		import shutil
		script_str = str(script_path)

		# Ensure output tokens are separate already in *args
		cmd = [script_str, *args]
		if not os.access(script_str, os.X_OK):
			# Fallback to bash only if not executable
			cmd = ["bash", script_str, *args]

		allsky_shared.log(0, f"{cmd}")
		try:
			proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
			if proc.returncode == 0:
				allsky_shared.log(1, f"INFO: Successful: {script_str}")
			else:
				allsky_shared.log(0, f"ERROR: {script_str} - rc={proc.returncode}\nSTDERR:\n{proc.stderr}")
			return proc.returncode, proc.stdout, proc.stderr
		
		except Exception as e:
			return 1, "", str(e)

	# Main Module Function - take the parameters and pass to the keogram script then to upload script. 
	def run(self):
		upload = self.get_param('upload', False, bool)
		expand = self.get_param('expand', False, bool)
		rotation = self.get_param('rotation', 0, int)
		resize = self.get_param('resize',"", str)
		font_name = self.get_param('font_name', "Simplex", str)
		font_color= self.get_param('font_color', "#ffffff", str)
		font_size = self.get_param('font_size', 2, float)
		font_thickness = self.get_param('font_thickness', 3, int)
		extra_params = self.get_param('extra_parameters', "", str)
		show_labels = self.get_param('show_labels',"", str)
		#upload_test = self.get_param('upload_test', False, bool)

		allsky_home = allsky_shared.getEnvironmentVariable("ALLSKY_HOME")
		images_dir = allsky_shared.getEnvironmentVariable("ALLSKY_IMAGES")

		result = ""

		#first validate sizing input by passing bogus info to resize functino to test?
		#test_resize,resize_plan_test = allsky_shared.resize_image("test",resize,start_size=(640,480),return_image=False)
		#w_resize = (resize_plan_test[-2])
		#allsky_shared.log(0, f"test results return new size of {w_resize}")
		#return
	
		# Create keogram by deriving and passing parameters
	 
		# define date as today minus 1.
		#TODO: maybe a better varaible name than kdate?
		kdate = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

		# set input directory and also upload setting
		if self.debugmode:
			upload = self.get_param('upload_test',"", bool)
			user_dir = self.get_param('input_dir', "", str)
			if user_dir:
				input_dir = user_dir if user_dir.startswith("/") else os.path.join(images_dir, user_dir)
				kdate = user_dir
			else:
				input_dir = os.path.join(images_dir, kdate)
		else:
			input_dir = os.path.join(images_dir, kdate)

		output_dir = os.path.join(input_dir, "keogram")
		os.makedirs(output_dir, exist_ok=True)  # safe to ensure it exists (but I think the keogram script creates it)

		#TODO: get extension from allsky settings directly? 
		full_file_name = allsky_shared.getSetting('filename')
		_, file_ext = os.path.splitext(full_file_name)
		ext = file_ext.lstrip('.')

		keo_filename = f"keogram-{kdate}.{ext}"

		keogram_fullpath = os.path.join(output_dir, keo_filename)

		# build info for running the script
		keo_script_path= os.path.join(allsky_home, "bin", "keogram")
		#script = "/home/RazAdmin/allsky/bin/keogram"
		create_params = [
			"-d", input_dir,
			"-e", ext,  # 'jpg' (no leading dot)
			"-o", f"{output_dir}/{keo_filename}",
			"-N", font_name,         # e.g., "Simplex"
			"-S", str(font_size),    # e.g., "2.0"
			"-C", font_color,        # e.g., "#ffffff"
			"-L", str(font_thickness)
		]
		if expand:
			create_params.append("--image-expand")
		if show_labels == "Time Only":
			create_params.append("--no-date")
		if show_labels == "No Labels":
			create_params.append("--no-label")
		if rotation != 0:
			create_params.extend(["--rotate", str(rotation)])

		# NOTE: there is no saftey here if a user adds an extra parameter for one of the input fields inthe module.  like specifying font size twice.
		# if these are entered in UI will need them to be comma separated to use!
		#	create_params.extend(extra_params.split())  # assumes space-separated extra params

		# Execute keogram program
		create_keo_rc, out, err = self.__execute_script(keo_script_path, *create_params)
		if create_keo_rc == 0:		
			#sucessfully created	
			allsky_shared.log(1, f"INFO: Keogram created successfully: {keogram_fullpath}")
			
			#could add stretch here by opening the new keogram file and doing stuff
			#if stretch:
			#	run script for that...

		else:
			allsky_shared.log(0, f"ERROR: Keogram creation failed (rc={create_keo_rc}). See stderr:\n{err}")


		# upload if created and user selected to upload
		if upload and create_keo_rc == 0:
			upload_script_path = os.path.join(allsky_home, "scripts", "upload.sh")
			
			#dont need to redefine.  #keogram_fullpath = os.path.join(output_dir, keo_filename)
			remote_dir = "/keograms"
			uselocalweb = allsky_shared.getSetting("uselocalwebsite")
			useremoteweb = allsky_shared.getSetting("useremotewebsite")
			useremoteserver = allsky_shared.getSetting("useremotewebserver")

			
			# resize
			if resize not in("","0"):			# user entered a resizing value
				tmp_dir=output_dir
				tmp_dir = allsky_shared.get_environment_variable("ALLSKY_TMP")
				#allsky_shared.log(1,tmp_dir)

				keogram_resized,resize_plan = allsky_shared.resize_image(keogram_fullpath,resize)
				allsky_shared.log(1,{resize_plan})
				
				#if keogram_resized is not None:
					#TODO: save resized in tmp and update keogram_fullpath
				# save keogram_resized as tmp dir, keo_filename
				#keo_filename = "test_resized_keo.jpg"
				keogram_tmp_path = os.path.join(tmp_dir, keo_filename)
				keogram_resized.save(keogram_tmp_path)
				keogram_fullpath = keogram_tmp_path
				
			#TODO: delete resized from tmp at end
					
			# local website
			if uselocalweb:
				target = "--local-web"
				remote_dir = os.path.join(allsky_home, "html","allsky", "keograms")
				target_file = keo_filename

				#run upload script
				upload_keo_rc, out, err = self.__execute_script(upload_script_path, target, keogram_fullpath, remote_dir, target_file)
				if upload_keo_rc == 0:
					allsky_shared.log(1, f"INFO: Keogram uploaded successfully: {os.path.join(output_dir, keo_filename)}")
				else:
					allsky_shared.log(0, f"ERROR: Failed to upload keogram to {target} (rc={create_keo_rc}). See stderr:\n{err}")

			if useremoteweb:
				target = "--remote-web"
				remote_dir = allsky_shared.getSetting("remotewebsiteimagedir")+"/keograms"
				target_file = keo_filename
				
				#run upload script
				upload_keo_rc, out, err = self.__execute_script(upload_script_path, target, keogram_fullpath, remote_dir, target_file)
				if upload_keo_rc == 0:
					allsky_shared.log(1, f"INFO: Keogram uploaded successfully: {os.path.join(output_dir, keo_filename)}")
				else:
					allsky_shared.log(0, f"ERROR: Failed to uplaod keogram to {target} (rc={create_keo_rc}). See stderr:\n{err}")

			# remote website need to check "upload with original name?"
			if useremoteserver:
				#target_file = f"keogram.{ext}"
				target = "--remote-server"
				remote_dir = allsky_shared.getSetting("remoteserverimagedir")+"/keograms"
				
				if allsky_shared.getSetting("remoteserverkeogramdestinationname")=="": 
					target_file = keo_filename
				else:
					target_file = allsky_shared.getSetting("remoteserverkeogramdestinationname")

				#run upload script
				upload_keo_rc, out, err = self.__execute_script(upload_script_path, target, keogram_fullpath, remote_dir, target_file)
				if upload_keo_rc == 0:
					allsky_shared.log(1, f"INFO: Keogram uploaded successfully: {os.path.join(output_dir, keo_filename)}")
				else:
					allsky_shared.log(0, f"ERROR: Failed to upload keogram to {target} (rc={create_keo_rc}). See stderr:\n{err}")
		
		# delete temp file if we created it
		if os.path.exists(keogram_tmp_path):
			os.remove(keogram_tmp_path)

		result = "Daily Keogram process complete"
		
		allsky_shared.log(1, f"INFO:  {result}")
		#the end!
		return result
  

def keogram(params, event):
	allsky_keogram = ALLSKYKEOGRAM(params, event)
	result = allsky_keogram.run()

	return result