#!/usr/bin/env python3

import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes

def gmailsend2():
    # Gmail SMTP configuration
    smtpServer = 'smtp.gmail.com'
    smtpPort = 587
    emailAddress = "kcottingham@gmail.com"
    emailPassword = "pbdt dcll qzup cswp"
    recipientEmail = "jkc523@duck.com"
    subjectText = "some photos"
    subjectDate = True
    messageBody = "text for body"
    startrails = True
    keogram = True
    timelapse = True

    result = "starting"
    
    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

    # Get user's home directory dynamically
    home_dir = os.path.expanduser("~")

    # Initialize emailmessage details
    msg = EmailMessage()
    msg["From"] = emailAddress
    msg["To"] = recipientEmail
    
    if subjectDate:
        msg["Subject"] = f"{subjectText} - {yesterday}"
    else:
        msg["Subject"] = subjectText
    
    #Initial set of message body text
    msg.set_content(messageBody)
    
    # Initialize total attachment size (max is 25MB for gmail)
    total_attachment_size = 0
    max_attachment_size = 25 * 1024 * 1024

    # Function to attach files dynamically
    def attach_file(file_path):
        nonlocal total_attachment_size
        nonlocal messageBody
        
        if os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            maintype, subtype = mime_type.split('/')
  
            file_size = os.path.getsize(file_path)
            if total_attachment_size + file_size > max_attachment_size:
                fileSizeMB = file_size / 1024 / 1024
                messageBody += f"<br>{os.path.basename(file_path)} too large to attach ({fileSizeMB}MB).  Total attachment size exceeds 25MB limit."
                return f"Error: Total attachment size exceeds 25MB limit. File not attached {file_path}\n"
            
            try:
                with open(file_path, "rb") as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))
                    total_attachment_size += file_size
                    fileSizeMB = file_size / 1024 / 1024
                    messageBody += f"<br>{os.path.basename(file_path)}  {fileSizeMB}MB"
                    return f"Attached: {file_path}\n"
            except Exception as e:
                return f"Error attaching file: {e}\n"

    # Check which files to attach
    if startrails:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg")
        result += attach_file(file_path)
     
    if keogram:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
        result += attach_file(file_path)
       
    if timelapse:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        result += attach_file(file_path)

    # Set the main body of the message again with the attachment details    
    # Add an HTML part with the updated body content
    #html_content = f"<html><body><p>{messageBody}</p></body></html>"
    #msg.add_alternative(html_content, subtype='html')

    # Send email via Gmail SMTP / TLS
    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()  # Secure connection
            server.login(emailAddress, emailPassword)
            server.send_message(msg)
            server.quit()
        result = "Email sent successfully"
    except Exception as e:
        result = f"Error sending email: {e}"

    print (result)
    return result
	
gmailsend2()