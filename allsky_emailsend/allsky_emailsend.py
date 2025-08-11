import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import os
import smtplib
import datetime
from email.message import EmailMessage
import mimetypes
from PIL import Image

class ALLSKYEMAILSEND(ALLSKYMODULEBASE):

    meta_data = {
        "name": "Email images via SMTP or Gmail",
        "description": "Email nightly images to recipients",
        "version": "v1.0.0",
        "pythonversion": "3.10.0",
        "centersettings": "false",
        "testable": "true",
        "module": "allsky_emailsend",    
        "group": "Data Export",
        "events": [
            "nightday",
            "periodic"
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
                "type": {
                    "fieldtype": "select",
                    "values": "To,BCC"
                }              
            },         
            "recipient_email": {
                "required": "true",
                "description": "Recipients",
                "secret": "true",
                "help": "Separate with a comma if more than one.  eg. AAA@mail.com,BBB@mail.com",
                "tab": "Daily Notification Setup"             
            },
            "email_subject_text": {
                "required": "true",
                "description": "Subject",
                "help": "No characters like backslash or quote marks",
                "tab": "Daily Notification Setup"             
            },
            "email_subject_date": {
                "required": "false",
                "description": "Append date to Subject line",
                "help": "eg: Last night's Allsky images - 20250401",
                "tab": "Daily Notification Setup",
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
                "help": "<li>Only sends images if Allsky is configured to create them and save at least one day on the Pi.<li>Selecting Composite will send a single image of Startrails with Keogram displayed below.",
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
                "description": "SMTP server address",
                "help": "Only change if not using Gmail",
                "tab": "Sender SMTP Setup"          
            },
            "smtp_port": {
                "required": "true",
                "description": "SMTP server port",
                "help": "Only change if not using Gmail",
                "tab": "Sender SMTP Setup",
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
                        "Refactored for Allsky v2025",
                        "Added Filters and Help"
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
                total_attachment_size += file_size
                if total_attachment_size > max_attachment_size:
                    message_body += f"\n{os.path.basename(file_path)} too large to attach: ({file_size_mb}mb)"
                    result += f"Error: Total attachment size exceeds {max_attachment_size}MB limit. File not attached: {file_path}\n"
                else:
                    message_body += f"\n{os.path.basename(file_path)}  ({file_size_mb}mb)"
                    valid_file_paths.append(file_path)
            else:
                result += f"Error: File does not exist: {file_path}\n"
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

            return result
        except Exception as e:
            result += f"Error creating composite image: {e}\n"
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
            except Exception as e:
                result += f"Error attaching file: {e}\n"
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
        except Exception as e:
            result = f"Error sending email: {e}"
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

        result = ""
        send_email = False

        # Get user's home directory
        #TODO use allsky_shared in lieu of this
        home_dir = os.path.expanduser("~")

        # Get yesterday's date in YYYYMMDD format
        # TODO (maybe) - overkill to add a testing tab for user to specify a folder instead of last nights date for folder
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        
        # get image file extension from allsky user settings      
        full_file_name = allsky_shared.getSetting('filename')
        _, file_ext = os.path.splitext(full_file_name)

        # Initialize email message details
        msg = EmailMessage()
        msg["From"] = sender_email_address
        match to_or_bcc:
            case "To": msg["To"] = recipient_email
            case "BCC": msg["BCC"] = recipient_email
        if email_subject_date == "Yes":
            msg["Subject"] = f"{email_subject_text} - {yesterday}"
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

        # there has to be a better way to get these paths using allsky variables?
        # TODO use allsky_shared in lieu of this
        file_path_stars = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}{file_ext}")
        file_path_keo = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}{file_ext}")
        file_path_timelapse = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        
        # maybe should use temp folder instead?
        file_path_composite = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-keo-{yesterday}{file_ext}")

        # Check user file selections
        if composite =="Yes":
                if os.path.exists(file_path_stars) and os.path.exists(file_path_keo):
                    # create composite
                    composite_img = self.__create_combo_image(file_path_composite, file_path_stars, file_path_keo, composite_keogram_height, composite_padding)
                    # attach composite
                    if composite_img:
                        file_paths_images.append(file_path_composite)
                    send_email = True
                else:
                    result += "Composite not created.  Startrails or Keogram not found.\n"

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
            file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
            file_paths_video.append(file_path)

            # Reuse same base message body
            message_body = self.get_param('message_body','',str)
            
            msg_video = EmailMessage()
            msg_video["From"] = sender_email_address
            msg_video["To"] = recipient_email
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

    return result 

