#!/usr/bin/env python3

import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes

def gmailsend2():
    # Gmail SMTP configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email_address = "kcottingham@gmail.com"
    sender_email_password = "pbdt dcll qzup cswp"
    recipient_email = "jkc523@duck.com"
    email_subject_text = "some photos"
    email_subject_date = True
    message_body = "text for body"
    startrails = "Yes"
    keogram = "Yes"
    timelapse = "Yes - in separate email"

    result = ""
    send_email = False

    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

    # Get user's home directory dynamically
    home_dir = os.path.expanduser("~")

    # Initialize emailmessage details
    msg = EmailMessage()
    msg["From"] = sender_email_address
    msg["To"] = recipient_email
    
    if email_subject_date == "Yes":
        msg["Subject"] = f"{email_subject_text} - {yesterday}"
    else:
        msg["Subject"] = email_subject_text
    
    # Initialize total attachment size (max is 25MB for gmail)
    total_attachment_size = 0
    max_attachment_size = 25 * 1024 * 1024
    file_paths = []
    file_paths_video = []
    valid_file_paths = []

    def validate_files(the_file_paths):
        # Function to validate files
        nonlocal total_attachment_size
        nonlocal message_body
        nonlocal valid_file_paths
        nonlocal result
    
        # build message_body and filter files
        valid_file_paths.clear()
        for file_path in the_file_paths:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_size_mb = round(file_size / 1024 / 1024,1)
                total_attachment_size += file_size
                if total_attachment_size > max_attachment_size:
                    message_body += f"\n{os.path.basename(file_path)} too large to attach: ({file_size_mb}mb)"
                    result += f"Error: Total attachment size exceeds 25MB limit. File not attached: {file_path}\n"
                else:
                    message_body += f"\n{os.path.basename(file_path)}  ({file_size_mb}mb)"
                    valid_file_paths.append(file_path)
            else:
                result += f"Error: File does not exist: {file_path}\n"
        return result
        
    def attach_files(the_email_msg, attach_files):
        # Function to attach files to the email
        nonlocal result

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

    def send_email_now(the_email_msg):
        # Function to send email via Gmail SMTP / TLS
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(sender_email_address, sender_email_password)
                server.send_message(the_email_msg)
            result = "Email sent successfully"
        except Exception as e:
            result = f"Error sending email: {e}"
        return result

    # Check user file selections
    if startrails == "Yes":
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg")
        file_paths.append(file_path)
        send_email = True
        
    if keogram == "Yes":
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
        file_paths.append(file_path)
        send_email = True

    if timelapse == "Yes":
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        file_paths.append(file_path)
        send_email = True

    if send_email:
        # validate file paths and file size
        result += validate_files(file_paths)
        # Set the main body content details BEFORE attaching files
        msg.set_content(message_body)
        #attach the valid files
        result += attach_files(msg, valid_file_paths)
        # send the email
        result += send_email_now(msg)

    # if user wants timelapse sent separately
    if timelapse == "Yes - in separate email":
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        file_paths_video.append(file_path)

        # reuse same base message body
        message_body = params['message_body']
        
        msg_video = EmailMessage()
        msg_video["From"] = sender_email_address
        msg_video["To"] = recipient_email
        msg_video["Subject"] = msg["Subject"]
        
        # validate file paths and file size
        result +=validate_files(file_paths_video)
        # Set main body content BEFORE attaching files
        msg_video.set_content(message_body)
        #attach the valid files
        result += attach_files(msg_video, valid_file_paths)
        # send the email
        result += send_email_now(msg_video)    
    
    return result
	
gmailsend2()