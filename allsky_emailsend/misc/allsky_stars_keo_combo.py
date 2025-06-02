import allsky_shared as s
import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes
from PIL import Image, ImageOps

metaData = {
    "name": "Create combo stars-keo image",
    "description": "Create combo stars-keo image",
    "version": "v1.0",
    "pythonversion": "3.9.0",
    "module": "allsky_stars_keo_combo",    
    "events": [
        "nightday",
        "periodic"
    ],
    "experimental": "false",  
    "arguments": {
        "address_as": "To",
        "recipient_email": "",
        "email_subject_text": "Allsky Startrail-Keogram combo",
        "email_subject_date": "Yes",
        "message_body": "Attached is last night's startrails image combined with the nightly keogram.",
        "img_padding": "50",
        "keogram_height": "400",
        "sender_email_address": "", 
        "sender_email_password": "",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": "587"
    },
    "argumentdetails": { 
        "address_as": {
            "required": "false",
            "description": "To or BCC?",
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
            "help": "Separate with a comma if more than one.  eg. AAA@mail.com,BBB@mail.com",
            "tab": "Daily Notification Setup"             
        },
        "email_subject_text": {
            "required": "true",
            "description": "Subject:",
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
            "description": "Email Message Text:",
            "help": "Any message body text you want to include. No characters like backslash or quote marks. File names are appended below this text.",
            "tab": "Daily Notification Setup"             
        },
        "img_padding": {
            "required": "false",
            "description": "padding between images",
            "help": "",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 20
            }    
        }, 
        "keogram_height": {
            "required": "false",
            "description": "new height for Keogram",
            "help": "",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "spinner",
                "min": 20,
                "max": 1000,
                "step": 20
            }  
        },       
        "sender_email_address": {
            "required": "true",
            "description": "Sender email address",
            "help": "",
            "tab": "Sender SMTP Setup"   
        },        
        "sender_email_password": {
            "required": "true",        
            "description": "Password / Google App Password",
            "help": "For Gmail: get this from your google account's security settings, it is NOT your gmail login password.",
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
            "tab": "Sender SMTP Setup"
        }
    },
    "enabled": "false",
    "changelog": {
        "v1.0": [
            {
                "author": "Kentner Cottingham",
                "authorurl": "https://github.com/NiteRide",
                "changes": "Initial Release"
            }
        ]                                       
    }              
}

# Function to combine the two images
def create_combo_image(output_path, file_path_stars, file_path_keo, keo_height, img_padding):
    result = ""
    try:
        with Image.open(file_path_stars) as stars_img:
            stars_width, stars_height = stars_img.size
            
            with Image.open(file_path_keo) as keo_img:
                keo_img = keo_img.resize((stars_width, keo_height))

            ttl_height = stars_height + img_padding + keo_height

            combined_img = Image.new("RGB", (stars_width, ttl_height), (0, 0, 0))
            combined_img.paste(stars_img, (0, 0))
            combined_img.paste(keo_img, (0, stars_height + img_padding))
            combined_img.save(output_path)
            result += f"Overlay image saved to {output_path}\n"

        return result
    except Exception as e:
        result += f"Error creating combo image: {e}\n"
        return result

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
def stars_keo_combo(params, event):
    # Gmail SMTP configuration and parameters
    smtp_server = params['smtp_server']
    smtp_port = params['smtp_port']
    sender_email_address = params['sender_email_address']
    sender_email_password = params['sender_email_password']
    recipient_email = params['recipient_email']
    email_subject_text = params['email_subject_text']
    email_subject_date = params['email_subject_date']
    message_body = params['message_body']
    keo_height = int(params['keogram_height'])
    img_padding = int(params['img_padding'])
    to_or_bcc = params['address_as']

    result = " "
    send_email = False

    # Get user's home directory
    home_dir = os.path.expanduser("~")

    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    # get image file extension from allsky user settings      
    full_file_name = s.getSetting('filename')
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
    
    # Initialize total attachment size (max is 25MB for gmail)
    max_attachment_size = 25 * 1024 * 1024
    total_attachment_size = 0
 
    stars_exist = False
    keo_exist = False

    # Check for files
    file_path_stars = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}{file_ext}")
    file_path_keo = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}{file_ext}")
    
    if os.path.exists(file_path_stars): stars_exist = True
    if os.path.exists(file_path_keo): keo_exist = True
    
    # path to save
    save_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-keo-{yesterday}{file_ext}")
        
    if stars_exist and keo_exist:
        composite_img = create_combo_image(save_path, file_path_stars, file_path_keo, keo_height, img_padding)
        result += "just tried to create image"
        send_email = True

    if send_email:       
        # Set the main body content details BEFORE attaching files
        msg.set_content(message_body)
        # Attach the valid files
        result += attach_files(msg, save_path)
        # Send the email
        result += send_email_now(msg, smtp_server, smtp_port, sender_email_address, sender_email_password)

    return result