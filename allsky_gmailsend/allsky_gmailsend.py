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
        "SMTPSERVER": "smtp.gmail.com",
        "SMTPPORT" : "587",
        "EMAILADDRESS": "your_email@gmail.com", 
        "EMAILPASSWORD": "your_app_password",
        "recipientemail": "recipient@example.com",
        "startrails": "false",
        "keogram": "false",
        "timelapse": "false"
    },
    "argumentdetails": {
        "SMTPSERVER" : {
            "required": "true",
            "description": "gmail SMTP server address",
            "help": "",
            "tab": "Gmail Setup",          
        },
        "SMTPPORT" : {
            "required": "true",
            "description": "gmail SMTP server port",
            "help": "",
            "tab": "Gmail Setup"
        },
        "EMAILADDRESS" : {
            "required": "true",
            "description": "sender account email address",
            "help": "",
            "tab": "Gmail Setup"   
        },        
        "EMAILPASSWORD": {
            "required": "true",
            "tab": "Gmail Setup",            
            "description": "App Passsword"
        }, 
        "recipientemail" : {
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

def gmailsend(params, event):
    # Gmail SMTP configuration
    #SMTP_SERVER = "smtp.gmail.com"
    #SMTP_PORT = 587
    #EMAIL_ADDRESS = "kcottingham@gmail.com"  # Replace with your Gmail address
    #EMAIL_PASSWORD = "pbdt dcll qzup cswp"  # Use an App Password (not your actual Gmail password)
    #RECIPIENT_EMAIL = "jkc523@duck.com"  # Replace with recipient email


    # Gmail SMTP configuration
    SMTP_SERVER = params['SMTPSERVER'] #"smtp.gmail.com"
    SMTP_PORT = params['SMTPPORT']
    EMAIL_ADDRESS = params['EMAILADDRESS']         # Replace with your Gmail address
    EMAIL_PASSWORD = params['EMAILPASSWORD']       # Use an App Password (not your actual Gmail password)
    RECIPIENT_EMAIL = params['recipientemail']     # Replace with recipient email

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
        #else:
        #    print(f"Warning: File not found - {file_path}")

    # Send email via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        result = ("Email sent successfully")
    except Exception as e:
        result = (f"Error sending email: {e}")
    
    return result