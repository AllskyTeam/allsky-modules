
'''

allsky_uimsgnotify.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

The purpose of this module is to send a notification to the user when a new message is posted into the system messages (e.g., that show on the Allsky WebUI page).
It runs in the periodic pipeline and will:
	1. check the messages.txt file for new messages since the last time it sent a notification
	2. if there are new messages send a notification with the latest message via the user selected channels
	3. Notification can go to email, NTFY.sh, or Pushover.
	4. Variables can be published for use in the Allsky Publish Data module or overlays

'''

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import os
import time
import smtplib
from email.message import EmailMessage
import requests


# GLOBALS
ALLSKYHOME = allsky_shared.get_environment_variable("ALLSKY_HOME", "/home/allsky")
allsky_msg_file = "messages.txt"
allsky_msg_filepath = ALLSKYHOME + "/config/" + allsky_msg_file


class ALLSKYUIMSGNOTIFY(ALLSKYMODULEBASE):
	meta_data = {
		"name": "WebUI Message Notification",
		"description": "Sends notifications when new WebUI messages are posted.  (Push messages, emails, via variables for Allsky Publish Data module or Overlays.)",
		"version": "v1.0.0",
		"pythonversion": "3.10.0",
		"centersettings": "false",
		"testable": "true",
		"module": "allsky_uimsgnotify",    
		"group": "Data Export",
		"events": [
			"periodic"
		],
		"experimental": "true",
		"extradatafilename": "allsky_notify_ui_extradata.json",
		"extradata": {
			"values": {
				"AS_UI_NOTIFY_HAS_NEW_MSG": {
					"name": "${AS_UI_NOTIFY_HAS_NEW_MSG}",
					"format": "",
					"sample": "true",
					"group": "WebUI Message Notifications",
					"description": "Indicates if there is a new message in the Allsky WebUI since last check",
					"type": "bool"
				},
				"AS_UI_NOTIFY_MSG_DATE": {
					"name": "${AS_UI_NOTIFY_MSG_DATE}",
					"format": "",
					"sample": "YYYY/MM/DD 16:47:38",
					"group": "WebUI Message Notifications",
					"description": "Date time of the latest message.",
					"type": "string"
				},
				"AS_UI_NOTIFY_MSG_TXT": {
					"name": "${AS_UI_NOTIFY_MSG_TXT}",
					"format": "",
					"sample": "ERROR: This is a sample message...",
					"group": "WebUI Message Notifications",
					"description": "Text of the latest message.",
					"type": "string"
				},
				"AS_UI_NOTIFY_MSG_OCCURRENCES": {
					"name": "${AS_UI_NOTIFY_MSG_OCCURRENCES}",
					"format": "",
					"sample": "1",
					"group": "WebUI Message Notifications",
					"description": "Occurrences of the latest message.",
					"type": "int"
				},
				"AS_UI_NOTIFY_MSGS_COUNT": {
					"name": "${AS_UI_NOTIFY_MSGS_COUNT}",
					"format": "",
					"sample": "5",
					"group": "WebUI Message Notifications",
					"description": "Total number of messages displayed in WebUI",
					"type": "int"
				}
			}
		},


		"arguments": {
			"notification_title": "Allsky WebUI Message Alert",
			"notification_threshold": 10,

			"publish_vars": "true",
			"send_pushover": "false",
            "send_ntfy": "false",
			"send_email": "false",

			"ntfy_server": "https://ntfy.sh",
            "ntfy_topic": "",

			"pushover_user": "",
			"pushover_token": "",
			"pushover_device":"",
	
			"recipient_email": "",
			"sender_email_address": "", 
			"sender_email_password": "",
			"smtp_server": "smtp.gmail.com",
			"smtp_port": 587,	

			"debug_alert": "false",
			"debug_msg": "Connectivity test message from the Allsky UI Message Notification Module.",
			"debug_sim_msg": "false",
			"debug_ignore_timecheck": "false",
			"debug_reset_db_keys": "false",
			"debug_reset_db_notify_count": "false",
			"debug_reset_db_last_notify": "false"

		},
		"argumentdetails": {

			"publish_vars": {
				"required": "false",
				"description": "Allsky Publish Data",
				"help": "Publish variables for Allsky Publish Data Module, Overlays, etc.",
				"tab": "Notification Channels",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"vars_end_break": {
				"tab": "Notification Channels",
				"source": "local",
				"html": "<BR>",
				"type": {
					"fieldtype": "html"
				}
			},	

			"send_pushover": {
				"required": "false",
				"description": "Pushover",
				"help": "Push message service for iOS, Android, Web/Desktop.",
				"tab": "Notification Channels",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"pushover_user": {
				"required": "false",
				"description": "User Key",
				"help": "Your Pushover User Key",
				"secret": "true",				
				"tab": "Notification Channels",
				"layout" : {
					"row": "PUSHOVER2",
					"title": " ",
					"width": 6
				},
				"filters": {
					"filter": "send_pushover",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"pushover_token": {
				"required": "false",
				"description": "API Token",
				"help": "Your Pushover API Token",
				"secret": "true",				
				"tab": "Notification Channels",
				"layout" : {
					"row": "PUSHOVER2",
					"title": "",
					"width": 6
				},
				"filters": {
					"filter": "send_pushover",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"pushover_end_break": {
				"tab": "Notification Channels",
				"source": "local",
				"html": "<BR>",
				"type": {
					"fieldtype": "html"
				},
				"filters": {
					"filter": "send_pushover",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},	

			"send_ntfy": {
				"required": "false",
				"description": "NTFY.sh",
				"help": "Push message service for iOS, Android, Web/Desktop.",
				"tab": "Notification Channels",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"ntfy_server": {
				"required": "false",
				"description": "NTFY Server",
				"help": "Change only if using a self hosted NTFY server.)",
				"tab": "Notification Channels",
				"layout" : {
					"row": "NTFY2",
					"title": " ",
					"width": 6
				},
				"filters": {
					"filter": "send_ntfy",
					"filtertype": "show",
					"values": [
						"true"
					]
				},          

				"type": {
					"fieldtype": "url"
				}          
			},     
			"ntfy_topic": {
				"required": "false",
				"description": "NTFY Topic",
				"secret": "true",				
				"help": "The feed that you will listen to. It can be anything, but should be unique to you or your use case.",
				"tab": "Notification Channels",
				"layout" : {
					"row": "NTFY2",
					"title": "",
					"width": 6
				},
				"filters": {
					"filter": "send_ntfy",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"ntfy_end_break": {
				"tab": "Notification Channels",
				"source": "local",
				"html": "<br>",
				"type": {
					"fieldtype": "html"
				},	
				"filters": {
					"filter": "send_ntfy",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},

			"send_email": {
				"required": "false",
				"description": "Email",
				"help": "Basic email notification. (SMTP)",
				"tab": "Notification Channels",
				"type": {
					"fieldtype": "checkbox"
				}
			}, 
 			"recipient_email": {
				"required": "false",
				"description": "Recipient Email Address",
				"help": "Separate with a comma if more than one. e.g. AAA@mail.com,BBB@mail.com",
				"tab": "Notification Channels",
				"layout" : {
					"row": "EMAIL2",
					"title": " ",
					"width": 10
				},
				"filters": {
					"filter": "send_email",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"email_info2": {
				"message": "",
				"tab": "Notification Channels",
				"layout" : {
					"row": "EMAIL2",
					"title": " ",
					"width": 1
				},
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "light"
						}
					}
				}
			},
			"smtp_server": {
				"required": "false",
				"description": "Server Address",
				"help": "Only change if not using Gmail",
				"tab": "Notification Channels",
				"layout" : {
					"row": "SMTP",
					"title": " ",
					"width": 6
				},
				"filters": {
					"filter": "send_email",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"smtp_port": {
				"required": "false",
				"description": "Port",
				"help": "Only change if not using Gmail",
				"tab": "Notification Channels",
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
				},
				"filters": {
					"filter": "send_email",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"sender_email_address": {
				"required": "false",
				"secret": "true",
				"description": "SMTP Sender email address",
				"help": "",
				"tab": "Notification Channels",
				"layout" : {
					"row": "EMAIL3",
					"title": " ",
					"width": 6
				},
				"filters": {
					"filter": "send_email",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},        
			"sender_email_password": {
				"required": "false",
				"secret": "true",     
				"description": "SMTP Account Password",
				"help": "SMTP Account password or Google App password if you use MFA.",
				"tab": "Notification Channels",
				"layout" : {
					"row": "EMAIL3",
					"title": "SMTP Sender",
					"width": 6
				},
				"filters": {
					"filter": "send_email",
					"filtertype": "show",
					"values": [
						"true"
					]
				}   
			},        

			"notification_title": {
				"required": "true",
				"description": "Notification Title/Subject",
				"help": "No characters like backslash or quote marks",
				"tab": "Notification Setup"
			},
			"notification_threshold": {
				"required": "false",
				"description": "Max Notification Limit",
				"help": "Stop sending notifications after reaching this limit until the WebUI is cleared.",
				"tab": "Notification Setup",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 100,
					"step": 1
				} 
			},
			
			"debug_alert": {
				"required": "false",
				"description": " ",
				"help": "",
				"tab": "Debug",
				"layout" : {
					"row": "DEBUG",
					"title": "Send Sample Message",
					"width": 2
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debug_msg": {
				"required": "false",
				"description": "Some message text to send for debug or setup",
				"help": "Text for the notification body.",
				"tab": "Debug",
				"layout" : {
					"row": "DEBUG",
					"title": "Send Sample Message",
					"width": 10
				},
				"filters": {
					"filter": "debug_alert",
					"filtertype": "show",
					"values": [
						"true"
					]
				}
			},
			"debug_sim_msg": {
				"required": "false",
				"description": "Sim a WebUI Message",
				"help": "Enable to add a message to Allsky WebUI to test full flow, set variables, etc.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			},			
			"debug_ignore_timecheck": {
				"required": "false",
				"description": "Bypass Time check",
				"help": "Enable to send WebUI message even if not new since the last notification was sent. This is for testing and debug purposes.",
				"tab": "Debug",
				
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debug_reset_db_keys": {
				"required": "false",
				"description": "Reset checks and counts",
				"help": "Enable to reset the notification count and last notify time keys in the database.",
				"tab": "Debug",
				
				"type": {
					"fieldtype": "checkbox"
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

	# Function to send email via Gmail SMTP / TLS
	def __send_email(self, the_email_msg, smtp_server, smtp_port, sender_email_address, sender_email_password):
		try:
			with smtplib.SMTP(smtp_server, smtp_port) as server:
				server.starttls()  # Secure connection
				server.login(sender_email_address, sender_email_password)
				server.send_message(the_email_msg)
			allsky_shared.log(4, f"INFO: Notify Module - Successful send via Email")
			return True
		except Exception as e:
			allsky_shared.log(0, f"ERROR: Notify Module - Error sending email: {e}")
			return False

	def __send_ntfy(self, notification_msg):
		result = False
		ntfy_server = self.get_param('ntfy_server', 'https://ntfy.sh')
		ntfy_topic = self.get_param('ntfy_topic', '')
		ntfy_msg = notification_msg
		
		#now done when parsing the message, but leaving here in case we want to add other replacements in the future
		# replace some HTML as ntfy doesnt support it  eg: <br> with \n for line breaks and &nbsp; with space
		#ntfy_msg = ntfy_msg.replace("&nbsp;", " ")
		#ntfy_msg = ntfy_msg.replace("<br>", "\n\n")	

	
		try:
			response = requests.post(f"{ntfy_server}/{ntfy_topic}",
				headers={
					"Title": self.get_param('notification_title', ''),
					"Priority": "",
					"Tags": "triangular_flag_on_post"
				},
				data=ntfy_msg.encode('utf-8'),
				timeout=10,
			)

			if 200 <= response.status_code < 300:
				result = True
				allsky_shared.log(4, f"INFO: Notify Module - Successful send via NTFY.sh")
			else:
				result = False
				allsky_shared.log(0, f"ERROR: Notify Module - Error sending notification via NTFY.sh: {response.status_code} - {response.text}")
		except requests.exceptions.RequestException as e:
			allsky_shared.log(0, f"ERROR: Notify Module - Failed to send notification via NTFY.sh: {e}")
			return False

		return result

	def __send_pushover(self, notification_msg):
		result = False
		pushover_user = self.get_param('pushover_user', '')
		pushover_token = self.get_param('pushover_token', '')
		pushover_url = "https://api.pushover.net/1/messages.json"

		if not pushover_user or not pushover_token:
			allsky_shared.log(0, "ERROR: Notify Module - Pushover user key or token is missing")
			return False

		payload = {
			"token": pushover_token,
			"user": pushover_user,
			"html": 1,
			"title": self.get_param('notification_title', ''),
			"message": notification_msg,
    	}

		try:
			# Pushover expects application/x-www-form-urlencoded data
			response = requests.post(pushover_url, data=payload, timeout=10)
			response.raise_for_status()  # Raise an exception for HTTP errors

			if response.status_code in (200, 201):
				result = True
				allsky_shared.log(4, f"INFO: Notify Module - Successful send via Pushover")
			else:
				result = False
				allsky_shared.log(0, f"ERROR: Notify Module - Error sending notification via Pushover: {response.status_code} - {response.text}")

		except requests.exceptions.RequestException as e:
			allsky_shared.log(0, f"ERROR: Notify Module - Failed to send notification via Pushover: {e}")
			return False


		return result

	def __parse_message_line(self, message_line):
		timestamp = ""
		occurrences = ""
		message_text = ""

		if not message_line:
			return timestamp, occurrences, message_text

		##if message_line.startswith("\t\t"):
		##	message_line = message_line[2:]	# 

		parts = message_line.rstrip("\r\n").split("\t", 5)  # Split into 6 parts, with the last part being the message text which can contain tabs
		
		#bootstrap_info_format = parts[2].strip()
		timestamp = parts[3].strip()
		occurrences = parts[4].strip()
		message_text = parts[5].strip()

		# replace some HTML as not all clients support it  eg: <br> with \n for line breaks and &nbsp; with space
		message_text = message_text.replace("&nbsp;", " ")
		message_text = message_text.replace("<br>", "\n\n")	

		return timestamp, occurrences, message_text

	def check_for_new_messages(self, key="notifymodule_lastnotify"):	
		result = False
		last_modified_time = 0
		last_notify = 0

		ignore_timecheck = self.get_param('debug_ignore_timecheck', 'false', bool)
		use_debug_notification = self.get_param('debug_alert', 'false', bool)

		# if there is a file, check the date, if no file, then no messages return false
		if os.path.exists(allsky_msg_filepath):
			with open(allsky_msg_filepath, 'r') as f:
				lines = f.readlines()
				if len(lines) > 0:
					last_modified_time = os.path.getmtime(allsky_msg_filepath)
					line_count= len(lines)
					if self.debugmode: print(f"DEBUG: Last modified time of system messages file: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_time))} ({last_modified_time})")
					if self.debugmode and use_debug_notification == True: return True
				else:
					return result
		
		# file exists with data, now check db to see if we've sent a notification since the latest update
		if last_modified_time > 0:	
			if allsky_shared.db_has_key(key):
				last_notify = allsky_shared.db_get(key)
				if self.debugmode: print(f"DEBUG: Last notify time from db: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_notify))} ({last_notify})")
			else:
				allsky_shared.db_add(key, 0)
				if self.debugmode: print("DEBUG: Initializing db to 0")
				last_notify = 0

			if float(last_modified_time) > float(last_notify):
				result = True
				allsky_shared.log(4, f"INFO: Notify Module - New message detected, sending notification")	
			
			if self.debugmode and ignore_timecheck: 
				print(f"DEBUG: Ignoring check on last notify time, sending notification anyway due to debug settings.")
				result = True
			
		
		if result == True:
			allsky_shared.log(4, f"INFO: Notify Module - New system messages detected.")
			if self.debugmode: print(f"DEBUG: Notify Module - New system messages detected.")
		else:
			allsky_shared.log(4, f"INFO: Notify Module - No new system messages detected.")
			if self.debugmode: print(f"DEBUG: Notify Module - No new system messages detected since last notification.")

		return result

	def get_latest_message(self):
		notification_msg = ""

		if os.path.exists(allsky_msg_filepath):
					with open(allsky_msg_filepath, 'r') as f:
						lines = f.readlines()
						if len(lines) > 0:
							result = True
		

		#parse the last message and add it to the notification message body
		last_message_line = next((line for line in reversed(lines) if line.strip()), "")
		msg_time, occurrences, last_message = self.__parse_message_line(last_message_line)
		
		notification_msg += f"{last_message}"
		if int(occurrences) > 1:
			notification_msg +=  "\n\n" + f"({occurrences} occurrences, last on {msg_time})"
		else:
			notification_msg +=  "\n\n" + f"({msg_time})"

		return notification_msg

	def get_notification_count(self, key="notifymodule_notifycount"):
		count = 0

		if allsky_shared.db_has_key(key):
				count = allsky_shared.db_get(key)
				if self.debugmode: print(f"DEBUG: Current notification count from db: {count}")
		else:
			allsky_shared.db_add(key, 0)

		# Reset alert counter when the WebUI messages file is missing or empty.
		if os.path.exists(allsky_msg_filepath):
			with open(allsky_msg_filepath, 'r') as f:
				lines = f.readlines()
				if len(lines) == 0:
					count = 0
					allsky_shared.db_update(key, count)
		else:
			count = 0
			allsky_shared.db_update(key, count)

		return count

	def increment_notification_count(self, key="notifymodule_notifycount"):
		count = self.get_notification_count(key) + 1
		allsky_shared.db_update(key, count)
		if self.debugmode: print(f"DEBUG: Updated notification count in db to: {count}")
		return count

	def _save_extra_data(self, timestamp, occurrences, message_text, mssgs_count=0):
		'''Publish AS_UI_NOTIFY_* variables for the overlay or Allsky Publish Data module etc.'''
		
		try:
			extradata = {}
			extradata = {
				"AS_UI_NOTIFY_HAS_NEW_MSG": "true" if self.check_for_new_messages() else "false",
				"AS_UI_NOTIFY_MSGS_COUNT": int(mssgs_count),

				"AS_UI_NOTIFY_MSG_DATE": timestamp,
				"AS_UI_NOTIFY_MSG_OCCURRENCES": int(occurrences),
				"AS_UI_NOTIFY_MSG_TXT": message_text,
			}
			allsky_shared.save_extra_data(
				self.meta_data['extradatafilename'],
				extradata,
				self.meta_data['module'],
				self.meta_data['extradata'],
				event=self.event
			)
		except Exception as e:
			allsky_shared.log(0, f"ERROR: Notify Module - Failed to save extra data: {e}")
			if self.debugmode: print(f"DEBUG: Notify Module - Failed to save extra data: {e}")


	def reset_db_counts(self, count_key="uimsgnotifymodule_notifycount", time_key="uimsgnotifymodule_lastnotify"):
		allsky_shared.db_delete_key(count_key)
		allsky_shared.db_delete_key(time_key)

		if self.debugmode: print(f"DEBUG: Deleted {count_key} and {time_key} keys from db to reset notification counts and last notify time.")
		return True

	# Main Module Function
	def run(self):
		result = ""
		db_key_notifytime = "uimsgnotifymodule_lastnotify"
		db_key_notifycount = "uimsgnotifymodule_notifycount"
	
		pub_vars = self.get_param('publish_vars', 'false', bool)
		send_ntfy = self.get_param('send_ntfy', 'false', bool)
		send_pushover = self.get_param('send_pushover', 'false', bool)
		send_email = self.get_param('send_email', 'false', bool)

		if self.debugmode:
			# this will reset the tiny db keys so testing or execution can start over
			reset_counts = self.get_param('debug_reset_db_keys', 'false', bool)
			if reset_counts and self.reset_db_counts(db_key_notifycount, db_key_notifytime):
				print("Disable the reset counts toggle before testing again.")
				return "DB counts reset. Disable the reset toggle before testing again."

		# if nothing selected, then log, print a message if in debug, and exit
		if not pub_vars and not send_ntfy and not send_pushover and not send_email:
			if self.debugmode: print("No notification channels selected. Please select at least one channel or disable the module.")
			#	allsky_shared.log(0, "ERROR: Notify Module - No notification channels selected. Please select at least one channel to send notifications or disable the module.")
			#	return "No notification channels selected. Please select at least one channel or disable the module."

		if not pub_vars:
			uimsgnotify_cleanup()
			if self.debugmode: print("DEBUG: Cleaned up module variables.")


		notification_title = self.get_param('notification_title', '', str)

		notification_msg =""
		use_debug_notification = self.get_param('debug_alert', 'false', bool)
		debug_msg = self.get_param('debug_msg', 'Connectivity test message from the Allsky UI Message Notification Module.', str)
		debug_sim_msg = self.get_param('debug_sim_msg', 'false', bool)

		if self.debugmode and debug_sim_msg:
			allsky_shared.add_message("TEST: This is a simulated WEBUI Message from the Notify Module for testing.", "warning")
			print("DEBUG: Logged a simulated message/error to display in WebUI")

		if self.debugmode and use_debug_notification == True:
			# use the test notification text from the debug tab.
			notification_msg = f"{debug_msg}"
		else:
			
			# check notificaiton count if > threshold then send that as a final message instead of the latest message to avoid spamming the user with multiple notifications if there are a lot of messages posted since the last notification was sent.
			notification_count = self.get_notification_count(db_key_notifycount)
			notification_threshold = self.get_param('notification_threshold', 10, int)

			if notification_count > notification_threshold:
				if notification_count == notification_threshold + 1:
					notification_msg = f"Excessive alerts raised! Notifications paused until the messages are cleared from the WebUI.   count: {notification_count}."
				else:	
					return f"Notification count: {notification_count} exceeded threshold {notification_threshold} + 1.  Notifications paused until the messages are cleared from the WebUI.  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}"
			else:
				# Check for new messages in the system messages file, and if there are new messages since last notification, send a notification with the latest message.
				if self.check_for_new_messages(db_key_notifytime):
					# Update extra data immediately when new messages detected
					if os.path.exists(allsky_msg_filepath):
						with open(allsky_msg_filepath, 'r') as f:
							lines = f.readlines()
							if len(lines) > 0:
								mssgs_count= len(lines)
								last_message_line = next((line for line in reversed(lines) if line.strip()), "")
								msg_time, occurrences, last_message = self.__parse_message_line(last_message_line)
								if pub_vars:
									self._save_extra_data(msg_time, occurrences, last_message, mssgs_count)
			

					new_msg = self.get_latest_message()
					notification_msg = new_msg
				else:
					return f"No new messages to notify.  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}"	


		any_send_success = False

		if send_ntfy:
			# verify url and topic are present
			url = self.get_param('ntfy_server', 'https://ntfy.sh', str)
			topic = self.get_param('ntfy_topic', '', str)
			if not url or not topic:
				allsky_shared.log(0, "ERROR: Notify Module - NTFY server or topic not provided. Will not notify via NTFY.sh.")
			else:
				#print("DEBUG: Sending notification via NTFY.sh")
				if self.__send_ntfy(notification_msg):
					any_send_success = True
			
		if send_pushover:
			# verify user and token are present
			user = self.get_param('pushover_user', '', str)
			token = self.get_param('pushover_token', '', str)
			if not user or not token:
				allsky_shared.log(0, "ERROR: Notify Module - Pushover user or token not provided. Will not notify via Pushover.")
			else:
				#print("DEBUG: Sending notification via Pushover")
				if self.__send_pushover(notification_msg):
					any_send_success = True

		if send_email:
			result =False
			# Gmail SMTP configuration and parameters
			smtp_server = self.get_param('smtp_server', 'smtp.gmail.com', str)
			smtp_port = self.get_param('smtp_port', 587, int)
			sender_email_address = self.get_param('sender_email_address', '', str)
			sender_email_password = self.get_param('sender_email_password', '', str)
			recipient_email = self.get_param('recipient_email', '', str)

			# verify sender email, password, server, port, and recipient email are present
			if not sender_email_address or not sender_email_password or not smtp_server or not smtp_port or not recipient_email:
				allsky_shared.log(0, "ERROR: Notify Module - Email configuration incomplete. Will not notify via Email.")
			else:
				# Initia#lize email message details
				msg = EmailMessage()
				msg["From"] = sender_email_address		
				msg["To"] = recipient_email
				msg["Subject"] = notification_title

				# Set the main body content details BEFORE attaching files
				msg.set_content(notification_msg)
				
				# Send the email
				if self.__send_email(msg, smtp_server, smtp_port, sender_email_address, sender_email_password):
					any_send_success = True

		# Update last notify time only after a successful delivery of a real (non-debug) notification.
		if not (self.debugmode and use_debug_notification == True):
			if any_send_success:
				self.increment_notification_count(db_key_notifycount)
				rightnow = time.time()
				if self.debugmode: print(f"DEBUG: Updating last notify time in db to: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rightnow))} ({rightnow})")
				allsky_shared.db_update(db_key_notifytime, rightnow)
			else:
				allsky_shared.log(0, "ERROR: Notify Module - Notification delivery failed on all enabled channels; last notify time not updated so retry can occur.")

		if any_send_success:
			result = "Notification of Allsky WebUI message sent."
			if self.debugmode: print(f"DEBUG: Notify Module - Notification of Allsky WebUI message sent.")
		return result
  
def uimsgnotify(params, event):
	allsky_uimsgnotify = ALLSKYUIMSGNOTIFY(params, event)
	result = allsky_uimsgnotify.run()
	
	allsky_shared.log(4, f"INFO: Notify Module - Finished")

	return result 

def uimsgnotify_cleanup():
	moduleData = {
		"metaData": ALLSKYUIMSGNOTIFY.meta_data,
		"cleanup": {
			"files": {
				ALLSKYUIMSGNOTIFY.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)