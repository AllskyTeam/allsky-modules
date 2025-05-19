#!/usr/bin/env python3

#import allsky_shared as s
import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes

def gmailsend(params, event):
    # Gmail SMTP configuration
    smtpServer = 'smtp.gmail.com'
    smtpPort = 587
    emailAddress = "kcottingham@gmail.com"
    emailPassword = "pbdt dcll qzup cswp"
    recipientEmail = "jkc523@duck.com"
    subjectText = "some photos"
    subjectDate = true
    messageBody = "text for body"
    startrails = true
    keogram = true
    timelapse = true
    
    result = "starting"
    
    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y%m%d")

    # Get user's home directory dynamically
    home_dir = os.path.expanduser("~")

    # Create email message
    msg = EmailMessage()
    msg["From"] = emailAddress
    msg["To"] = recipientEmail
    
    if subjectDate:
        msg["Subject"] = (subjectText + f" - {yesterday}")     
    else: 
        msg["Subject"] = subjectText
    
    # Initialize total attachment size
    total_attachment_size = 0
    max_attachment_size = 25 * 1024 * 1024  # 25MB in bytes

    # Function to attach files dynamically
    def attach_file(file_path):
        nonlocal total_attachment_size
        
        if os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            maintype, subtype = mime_type.split('/')
            
            file_size = os.path.getsize(file_path)
            
            if total_attachment_size + file_size > max_attachment_size:
                messageBody += f"\n{os.path.basename(file_path)} too large to attach: ({file_size}).")
                return f"Error: Total attachment size exceeds 25MB limit. File not attached: {file_path}\n"
            
            try:
                with open(file_path, "rb") as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))
                messageBody += f"\n{os.path.basename(file_path)} attached: ({file_size})")
                total_attachment_size += file_size
                return f"Attached: {file_path}\n"
            except Exception as e:
                return f"Error attaching file: {e}\n"

    # Attach Files    
    if startrails:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg")
        result += attach_file(file_path)
   
    if keogram:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
        result += attach_file(file_path)
    
    if timelapse:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        result += attach_file(file_path)
    
    # Set final message body text (including reference to attachments)
    msg.set_content(messageBody)

    # Send email via Gmail SMTP
    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()  # Secure connection
            server.login(emailAddress, emailPassword)
            server.send_message(msg)
            server.quit()
        result = "Email sent successfully"
    except Exception as e:
        result = f"Error sending email: {e}"
    
    return result
	
gmailsend()