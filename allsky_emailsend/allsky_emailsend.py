import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import os
import smtplib
import datetime
from email.message import EmailMessage
import mimetypes
from PIL import Image

# GLOBALS
ALLSKY_IMAGES = allsky_shared.getEnvironmentVariable("ALLSKY_IMAGES", fatal=True)
ALLSKY_TMP = allsky_shared.ALLSKY_TMP
EXT = allsky_shared.get_environment_variable("ALLSKY_EXTENSION", fatal=True)

IMAGES_DATE = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")	# today minus one

class ALLSKYEMAILSEND(ALLSKYMODULEBASE):
	meta_data = {
		"name": "Email images via SMTP or Gmail",
		"description": "Email nightly startrails/keogram/timelapse",
		"version": "v1.0.0",
		"pythonversion": "3.10.0",
		"centersettings": "true",
		"testable": "true",
		"module": "allsky_emailsend",    
		"group": "Data Export",
		"extradatafilename": "",
		"events": [
			"nightday"
		],
		"experimental": "false",

		"arguments": {
			"address_as": "To",
			"recipient_email": "",
			"email_subject_text": "Your Allsky nightly images",
			"email_subject_date": "Yes",
			"message_body": "Attached are last night's Allsky camera images.",
			"image_selection": "Startrails Only",
			"timelapse": "No",
			"composite_padding": 50,
			"composite_keogram_height": 400,
			"sender_email_address": "", 
			"sender_email_password": "",
			"smtp_server": "smtp.gmail.com",
			"smtp_port": 587,
			"max_attachment_size_mb": 25
		},
		"argumentdetails": {        
			"address_as": {
				"required": "true",
				"description": "To or BCC",
				"help": "",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "to_cc",
					"title": "Recipient(s)",
					"width": 3
				},
				"type": {
					"fieldtype": "select",
					"values": "To,BCC"
				}              
			},         
			"recipient_email": {
				"required": "true",
				"description": "Email Address(es)",
				"help": "Separate with a comma if more than one. e.g. AAA@mail.com,BBB@mail.com",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "to_cc",
					"title": "Recipient(s)",
					"width": 9
				}
			},
			"email_subject_text": {
				"required": "true",
				"description": "Text",
				"help": "No characters like backslash or quote marks",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "subject",
					"title": "Subject",
					"width": 9
				}
			},
			"email_subject_date": {
				"required": "false",
				"description": "Append date?",
				"help": "eg: Last night's Allsky images - 20250401",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "subject",
					"title": "Subject",
					"width": 3
				},
				"type": {
					"fieldtype": "select",
					"values": "No,Yes"
				}              
			},
			"message_body": {
				"required": "true",
				"description": "Email Message Text",
				"help": "Any message body text you want to include. No characters like backslash or quote marks. File names are appended below this text.",
				"tab": "Daily Notification Setup"             
			},
			"image_selection": {
				"required": "false",
				"description": "Attach Images",
				"help": "Choose which files to attach to the email. 'Composite' will send a single image of Startrails with Keogram below (saved in startrails folder).",
				"tab": "Daily Notification Setup",
				"type": {
					"fieldtype": "select",
					"values": "Startrails Only,Keogram Only,Startrails and Keogram,Startrails Keogram Composite,None"
				}
			},
			"composite_padding": {
				"required": "false",
				"description": "Composite Padding",
				"help": "Black space to add between Startrails and Keogram",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "attach_images",
					"title": "Images",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 500,
					"step": 20
				},
				"filters": {
					"filter": "image_selection",
					"filtertype": "show",
					"values": [
						"Startrails Keogram Composite"
					]
				}
			},
			"composite_keogram_height": {
				"required": "false",
				"description": "Height for Keogram",
				"help": "Keogram will be resized to [this Height] x [Startrails width] below the startarils image",
				"tab": "Daily Notification Setup",
				"layout" : {
					"row": "attach_images",
					"title": "Images",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 20,
					"max": 2000,
					"step": 20
				},
				"filters": {
					"filter": "image_selection",
					"filtertype": "show",
					"values": [
						"Startrails Keogram Composite"
					]
				}  
			},
			"timelapse": {
				"required": "false",
				"description": "Attach Timelapse",
				"help": "",
				"tab": "Daily Notification Setup",
				"type": {
					"fieldtype": "select",
					"values": "No,Yes,Yes - in separate email"
				}
			},

			"sender_email_address": {
				"required": "true",
				"secret": "true",
				"description": "Sender email address",
				"help": "",
				"tab": "Sender SMTP Setup"   
			},        
			"sender_email_password": {
				"required": "true",
				"secret": "true",     
				"description": "Account Password",
				"help": "SMTP Account password or Google App password if you use MFA.",
				"tab": "Sender SMTP Setup"
			},
			"smtp_server": {
				"required": "true",
				"description": "Server Address",
				"help": "Only change if not using Gmail",
				"tab": "Sender SMTP Setup",
				"layout" : {
					"row": "SMTP",
					"title": "SMTP Server",
					"width": 6
				}
			},
			"smtp_port": {
				"required": "true",
				"description": "Port",
				"help": "Only change if not using Gmail",
				"tab": "Sender SMTP Setup",
				"layout" : {
					"row": "SMTP",
					"title": "SMTP Server",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 9999,
					"step": 1
				} 
			},
			"max_attachment_size_mb": {
				"required": "true",
				"description": "Max attachments size",
				"help": "In MB the maximum server allowed size of all attachments to an email.",
				"tab": "Sender SMTP Setup",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 200,
					"step": 1
				}  
			}
		},
		"enabled": "false",
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Kentner Cottingham",
					"authorurl": "https://github.com/NiteRide",
					"changes": [
						"Initial Release"
					]
				}
			]                            
		}                 
	}

	# Function to validate files to attach
	def __validate_files(self, the_file_paths, total_attachment_size, max_attachment_size, message_body, valid_file_paths):
		result = ""
		valid_file_paths.clear()
		for file_path in the_file_paths:
			if os.path.exists(file_path):
				file_size = os.path.getsize(file_path)
				file_size_mb = round(file_size / 1024 / 1024, 1)
				max_limit_mb = round(max_attachment_size / 1024 / 1024, 1)
				total_attachment_size += file_size
				if total_attachment_size > max_attachment_size:
					message_body += f"\n{os.path.basename(file_path)} ({file_size_mb}MB) too large to attach\n{max_limit_mb}MB attachment limit exceeded."
					result += f"Error: Total attachment size exceeds {max_limit_mb}MB limit. File not attached: {file_path}\n"
					allsky_shared.log(1, f"WARNING: Email Send Module - Total attachment size exceeds {max_limit_mb}MB limit.  File not attached: {file_path}")
				else:
					message_body += f"\n{os.path.basename(file_path)} ({file_size_mb}MB)"
					valid_file_paths.append(file_path)
					allsky_shared.log(3, f"DEBUG INFO: Email Send Module - File attached: {os.path.basename(file_path)} ({file_size_mb}MB)")
			else:
				message_body += f"\n{os.path.basename(file_path)} not found."
				result += f"Error: Selected file does not exist: {file_path}\n"
				allsky_shared.log(3, f"DEBUG INFO: Email Send Module - Selected file does not exist: {file_path}")
		return result, total_attachment_size, message_body

	# Function to create composite startrails-keogram image
	def __create_combo_image(self, output_path, file_path_stars, file_path_keo, new_keo_height, img_padding):
		result = ""
		try:
			with Image.open(file_path_stars) as stars_img:
				stars_width, stars_height = stars_img.size
				
				with Image.open(file_path_keo) as keo_img:
					k_width, k_height = keo_img.size
					new_keo_height = min(k_height,new_keo_height)
					keo_img = keo_img.resize((stars_width, new_keo_height))

				ttl_height = stars_height + img_padding + new_keo_height

				combined_img = Image.new("RGB", (stars_width, ttl_height), (0, 0, 0))
				combined_img.paste(stars_img, (0, 0))
				combined_img.paste(keo_img, (0, stars_height + img_padding))
				combined_img.save(output_path, quality=95)
				result += f"Composite image saved to {output_path}\n"
				allsky_shared.log(3, f"DEBUG INFO: Email Send Module - Composite image saved to {output_path}")
			return result
		except Exception as e:
			result += f"Error creating composite image: {e}\n"
			allsky_shared.log(3, f"DEBUG INFO: Email Send Module - Error creating composite image: {e}")
			return result

	# Function to attach valid files to the email
	def __attach_files(self, the_email_msg, attach_files):
		result = ""
		for file_path in attach_files:
			try:
				mime_type, _ = mimetypes.guess_type(file_path)
				maintype, subtype = mime_type.split('/')
				with open(file_path, "rb") as f:
					the_email_msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))
					result += f"Attached: {file_path}\n"
					allsky_shared.log(3, f"DEBUG INFO: Email Send Module - File attached: {file_path}")
			except Exception as e:
				result += f"Error attaching file: {e}\n"
				allsky_shared.log(3, f"ERROR: Email Send Module - Error attaching file: {file_path} - {e}")
		return result

	# Function to send email via Gmail SMTP / TLS
	def __send_email_now(self, the_email_msg, smtp_server, smtp_port, sender_email_address, sender_email_password):
		result = ""
		try:
			with smtplib.SMTP(smtp_server, smtp_port) as server:
				server.starttls()  # Secure connection
				server.login(sender_email_address, sender_email_password)
				server.send_message(the_email_msg)
			result = f"Email sent successfully"
			allsky_shared.log(1, f"INFO: Email Send Module - Email sent successfully.")
		except Exception as e:
			result = f"Error sending email: {e}"
			allsky_shared.log(0, f"ERROR: Email Send Module - Error sending email: {e}")
		return result

	# Main Module Function
	def run(self):
		# Gmail SMTP configuration and parameters
		smtp_server = self.get_param('smtp_server', 'smtp.gmail.com', str)
		smtp_port = self.get_param('smtp_port', 587, int)
		sender_email_address = self.get_param('sender_email_address', '', str)
		sender_email_password = self.get_param('sender_email_password', '', str)
		recipient_email = self.get_param('recipient_email', '', str)
		email_subject_text = self.get_param('email_subject_text', '', str)
		email_subject_date = self.get_param('email_subject_date', '', str)
		message_body = self.get_param('message_body', '', str)
		image_selection = self.get_param('image_selection', '', str)
		composite_padding = self.get_param('composite_padding', 50, int)
		composite_keogram_height = self.get_param('composite_keogram_height', 400, int)
		timelapse = self.get_param('timelapse', 'No', str)
		to_or_bcc = self.get_param('address_as', 'To', str)
		max_attachment_size_mb = self.get_param('max_attachment_size_mb', 25, int)

		startrails = 'No'
		keogram = 'No'
		composite = 'No'
		message_body += f"\n"

		result = ""
		send_email = False

		# Initialize email message details
		msg = EmailMessage()
		msg["From"] = sender_email_address		
		msg[to_or_bcc] = recipient_email

		if email_subject_date == "Yes":
			msg["Subject"] = f"{email_subject_text} - {IMAGES_DATE}"
		else:
			msg["Subject"] = email_subject_text

		match image_selection:
			case "Startrails Only": startrails = "Yes"
			case "Keogram Only": keogram ="Yes"
			case "Startrails and Keogram": 
				startrails ="Yes"
				keogram ="Yes"
			case "Startrails Keogram Composite": composite ="Yes"

		# Initialize total attachment size (max is 25MB for gmail)
		max_attachment_size = (max_attachment_size_mb * 1024 * 1024)
		total_attachment_size = 0

		file_paths_images = []
		file_paths_video = []
		valid_file_paths = []  

		# define file paths to stars/keo/video
		file_path_stars = os.path.join(ALLSKY_IMAGES, IMAGES_DATE, "startrails", f"startrails-{IMAGES_DATE}.{EXT}")
		file_path_keo = os.path.join(ALLSKY_IMAGES, IMAGES_DATE, "keogram", f"keogram-{IMAGES_DATE}.{EXT}")
		file_path_timelapse = os.path.join(ALLSKY_IMAGES, IMAGES_DATE, f"allsky-{IMAGES_DATE}.mp4")
		file_path_composite = os.path.join(ALLSKY_IMAGES, IMAGES_DATE, "startrails", f"startrails-keo-{IMAGES_DATE}.{EXT}")

		# Check user file selections
		if composite =="Yes":
				if os.path.exists(file_path_stars): 
					if os.path.exists(file_path_keo):
						# create composite
						composite_img = self.__create_combo_image(file_path_composite, file_path_stars, file_path_keo, composite_keogram_height, composite_padding)
						# attach composite
						if composite_img:
							file_paths_images.append(file_path_composite)
						send_email = True
					else:
						message_body += f"\nKeogram not found to make composite."
						allsky_shared.log(0, f"ERROR: Email Send Module - Composite not created:  Keogram not found, will attempt to send just Startrails.")
						startrails = "Yes"
				else:
					message_body += f"\nStartrails not found to make composite."
					result += "Composite not created.  Startrails or Keogram not found.\n"
					allsky_shared.log(0, f"ERROR: Email Send Module - Composite not created.  Startrails not found, will attempt to send just Keogram.")
					keogram = "Yes"

		if startrails == "Yes":
			file_paths_images.append(file_path_stars)
			send_email = True
			
		if keogram == "Yes":
			file_paths_images.append(file_path_keo)
			send_email = True

		if timelapse == "Yes":
			file_paths_images.append(file_path_timelapse)
			send_email = True

		if send_email:
			# Validate file paths and file size
			validation_result, total_attachment_size, message_body = self.__validate_files(file_paths_images, total_attachment_size, max_attachment_size, message_body, valid_file_paths)
			result += validation_result
			# Set the main body content details BEFORE attaching files
			msg.set_content(message_body)
			# Attach the valid files
			result += self.__attach_files(msg, valid_file_paths)
			# Send the email
			result += self.__send_email_now(msg, smtp_server, smtp_port, sender_email_address, sender_email_password)

		# If user wants timelapse sent separately
		if timelapse == "Yes - in separate email":
			#file_path = os.path.join(home_dir, f"allsky/images/{IMAGES_DATE}/allsky-{IMAGES_DATE}.mp4")
			file_paths_video.append(file_path_timelapse)

			# Reuse same base message body
			message_body = self.get_param('message_body','',str)
			
			msg_video = EmailMessage()
			msg_video["From"] = sender_email_address
			msg_video[to_or_bcc] = recipient_email
			msg_video["Subject"] = msg["Subject"]
			
			# Validate file paths and file size
			validation_result, total_attachment_size, message_body = self.__validate_files(file_paths_video, total_attachment_size, max_attachment_size, message_body, valid_file_paths)
			result += validation_result
			# Set main body content BEFORE attaching files
			msg_video.set_content(message_body)
			# Attach the valid files
			result += self.__attach_files(msg_video, valid_file_paths)
			# Send the email
			result += self.__send_email_now(msg_video, smtp_server, smtp_port, sender_email_address, sender_email_password)    
		
		return result
  
def emailsend(params, event):
	allsky_emailsend = ALLSKYEMAILSEND(params, event)
	result = allsky_emailsend.run()
	allsky_shared.log(1, f"INFO: Email Send Module - Finished")

	return result 

def emailsend_cleanup():
	moduleData = {
		"metaData": ALLSKYEMAILSEND.meta_data,
		"cleanup": {
			"files": {
				ALLSKYEMAILSEND.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)