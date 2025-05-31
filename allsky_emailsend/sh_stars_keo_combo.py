#!/usr/bin/env python

import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes
from PIL import Image, ImageOps

# Function to combine the two images
def create_combo_image(output_path, file_path_stars, file_path_keo, keo_height, padding):
    try:
        with Image.open(file_path_stars) as stars_img:
            stars_width, stars_height = stars_img.size
            
            with Image.open(file_path_keo) as keo_img:
                keo_img = keo_img.resize((stars_width, keo_height))

            ttl_height = stars_height + padding + keo_height
            combined_img = Image.new("RGB", (stars_width, ttl_height), (0, 0, 0))
            combined_img.paste(stars_img, (0, 0))
            combined_img.paste(keo_img, (0, (stars_height + padding)))
            combined_img.save(output_path)
            print(f"Overlay image saved to {output_path}")

        return output_path
    except Exception as e:
        print(f"Error creating combo image: {e}")
        return None

# Function to attach valid files to the email
def attach_files(the_email_msg, file_path):
    result = ""
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
def send_email_now(the_email_msg, smtp_server, smtp_port, sender_email_address, sender_email_password):
    result = ""
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(sender_email_address, sender_email_password)
            server.send_message(the_email_msg)
        result = "\nEmail sent successfully"
    except Exception as e:
        result = f"\nError sending email: {e}"
    return result

# Main Module Function
def allsky_stars_keo_combo():

    # Gmail SMTP configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email_address = "kcottingham@gmail.com"
    sender_email_password = "pbdt dcll qzup cswp"
    recipient_email = "jkc523@duck.com"
    email_subject_text = "somea combo image"
    email_subject_date = "Yes"
    message_body = "text for body"
    keo_height = 300
    padding = 100
        

    result = ""
    send_email = False

    # Get user's home directory
    home_dir = os.path.expanduser("~")

    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    # get image file extension from allsky user settings      
    file_ext = ".jpg"

    # Initialize email message details
    msg = EmailMessage()
    msg["From"] = sender_email_address
    msg["To"] = recipient_email
    
    if email_subject_date == "Yes":
        msg["Subject"] = f"{email_subject_text} - {yesterday}"
    else:
        msg["Subject"] = email_subject_text
    
    # Initialize total attachment size (max is 25MB for gmail)
    max_attachment_size = 25 * 1024 * 1024
    total_attachment_size = 0
 
    stars_exist = False
    keo_exist = False

    stars_width = 0
    keo_height = 300
    padding =100

    # Check for files
    file_path_stars = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}{file_ext}")
    file_path_keo = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}{file_ext}")
    
    if os.path.exists(file_path_stars): stars_exist = True
    if os.path.exists(file_path_keo): keo_exist = True
    # path to save
    save_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-keo-{yesterday}{file_ext}")
    
    
    if stars_exist and keo_exist:
        composite_img = create_combo_image(save_path,file_path_stars,file_path_keo,keo_height,padding)
        result += "just tried to create image"
        send_email = True

    if send_email:
        # Validate file paths and file size
        #validation_result, total_attachment_size, message_body = validate_files(file_paths_images, total_attachment_size, max_attachment_size, message_body, valid_file_paths)
        #result += validation_result
        
        # Set the main body content details BEFORE attaching files
        msg.set_content(message_body)
        # Attach the valid files
        result += attach_files(msg, composite_img)
        # Send the email
        result += send_email_now(msg, smtp_server, smtp_port, sender_email_address, sender_email_password)

    return result

    print(result)

allsky_stars_keo_combo()