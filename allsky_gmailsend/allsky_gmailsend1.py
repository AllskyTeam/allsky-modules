import allsky_shared as s

import smtplib
import os
import datetime
from email.message import EmailMessage


metaData = {
    "name": "Send with Gmail",
    "description": "emails nightly images to email recipients.",
    "version": "v0.1",
    "pythonversion": "3.9.0",
    "module": "allsky_gmailsend",    
    "events": [
        "periodic",
        "nightday",
        "daynight"
    ],
    "experimental": "false",
    
    "arguments":{
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT" : 587,
        "EMAIL_ADDRESS": "your_email@gmail.com", 
        "EMAIL_PASSWORD": "your_app_password",  # Use an App Password (not your actual Gmail password)
        "RECIPIENT_EMAIL": "recipient@example.com",
        "startrails": "false",
        "keogram": "false",
        "timelapse": "false"
    },
    "argumentdetails": {
        "SMTP_SERVER" : {
            "required": "true",
            "description": "gmail SMTP server address",
            "help": "",
            "tab": "Gmail Setup",
            
        },
        "SMTP_PORT" : {
            "required": "true",
            "description": "gmail SMTP server port",
            "help": "",
            "tab": "Gmail Setup"
        },
        "EMAIL_ADDRESS" : {
            "required": "true",
            "description": "sender account email address",
            "help": "",
            "tab": "Gmail Setup"   
        },        
        "EMAIL_PASSWORD": {
            "required": "true",
            "tab": "Gmail Setup",            
            "description": "App Passsword"
        }, 
        "RECIPIENT_EMAIL" : {
            "required": "TRUE",
            "description": "recipient email adressess",
            "help": "",
            "tab": "Gmail Setup"             
        },
        "startrails" : {
            "required": "false",
            "description": "Post Star Trails Images",
            "help": "Post Star Trails images to the Discord Server",
            "tab": "Gmail Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "keogram" : {
            "required": "false",
            "description": "Post Keograms Images",
            "help": "Post Keograms images to the Discord Server",
            "tab": "Gmail Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "timelapse" : {
            "required": "false",
            "description": "Post Timelapse videos",
            "help": "Post Timelapse videos to the Discord Server",
            "tab": "Gmail Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }
    },
    
    "enabled": "false",
    
    "changelog": {
        "v0.1" : [
            {
                "author": "Kentner Cottingham",
                "authorurl": "https://github.com/NiteRide",
                "changes": "Initial Release"
            }
        ]                                       
    }              
}

# Gmail SMTP configuration
SMTP_SERVER = params['SMTP_SERVER'] #"smtp.gmail.com"
SMTP_PORT = params['SMTP_PORT']
EMAIL_ADDRESS = params['EMAIL_ADDRESS']         # Replace with your Gmail address
EMAIL_PASSWORD = params['EMAIL_PASSWORD']       # Use an App Password (not your actual Gmail password)
RECIPIENT_EMAIL = params['RECIPIENT_EMAIL']     # Replace with recipient email

# Get yesterday's date in YYYYMMDD format
yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

# Get user's home directory dynamically
home_dir = os.path.expanduser("~")

# Define file paths relative to the user's home directory
file_paths = [
    os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg"),
    os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
]

# Create email message
msg = EmailMessage()
msg["Subject"] = f"Last night’s startrails and keogram: {yesterday}"
msg["From"] = EMAIL_ADDRESS
msg["To"] = RECIPIENT_EMAIL
msg.set_content(f"Attached are the Allsky images from last night: \n{os.path.basename(file_paths[0])}\n{os.path.basename(file_paths[1])}")

# Attach files
for file_path in file_paths:
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=os.path.basename(file_path))
    else:
        print(f"Warning: File not found - {file_path}")

# Send email via Gmail SMTP
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Secure connection
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")