import allsky_shared as s
import smtplib
import os
import datetime
from email.message import EmailMessage

metaData = {
    "name": "Send with Gmail",
    "description": "emails nightly images to email recipients",
    "version": "v0.1",
    "pythonversion": "3.9.0",
    "module": "allsky_gmailsend",    
    "events": [
        "nightday",
        "periodic"
    ],
    "experimental": "false",  
    "arguments":{
        "recipientEmail": "recipient@example.com",
        "subjectText":"Last night's Allsky images",
        "subjectDate":"true",
        "messageBody":"Attached are last night's Allsky camera images.",
        "startrails": "false",
        "keogram": "false",
        "timelapse": "false",
        "emailAddress": "your_email@gmail.com", 
        "emailPassword": "your_app_password",
        "smtpServer": "smtp.gmail.com",
        "smtpPort" : "587"
    },
    "argumentdetails": { 
        "recipientEmail" : {
            "required": "true",
            "description": "Recipient email adresess",
            "help": "only enter one email address",
            "tab": "Notification Setup"             
        },
        "subjectText" : {
            "required": "true",
            "description": "Email Subject Line",
            "help": "",
            "tab": "Notification Setup"             
        },
        "subjectDate" : {
            "required": "false",
            "description": "Append date to Subject line",
            "help": "eg: Last night's Allsky images - 20250401",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }                
        },
        "messageBody" : {
            "required": "true",
            "description": "Email Message Text",
            "help": "Any message body text you want to include.  File names will be appended to this text.",
            "tab": "Notification Setup"             
        },
        "startrails" : {
            "required": "false",
            "description": "Attach Star Trails",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "keogram" : {
            "required": "false",
            "description": "Attach Keogram",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "timelapse" : {
            "required": "false",
            "description": "Attach Timelapse",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "emailAddress" : {
            "required": "true",
            "description": "Sender email address",
            "help": "",
            "tab": "Gmail Account Setup"   
        },        
        "emailPassword": {
            "required": "true",        
            "description": "Sender Google App Password",
            "help": "(NOT your gmail login password. Get this from your google account's security settings.",
            "tab": "Gmail Account Setup"
        },
        "smtpServer" : {
            "required": "true",
            "description": "gmail SMTP server address",
            "help": "you should not need to change this",
            "tab": "Gmail Account Setup"          
        },
        "smtpPort" : {
            "required": "true",
            "description": "SMTP server port",
            "help": "you should not need to change this",
            "tab": "Gmail Account Setup"
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
    smtpServer = params['smtpServer']
    smtpPort = params['smtpPort']
    emailAddress = params['emailAddress']
    emailPassword = params['emailPassword']
    recipientEmail = params['recipientEmail']
    subjectText = params['subjectText']
    subjectDate = params['subjectDate']
    messageBody = params['messageBody']
    startrails = params['startrails']
    keogram = params['keogram']
    timelapse = params['timelapse']
    
    result = "starting"
    
    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

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
    
    msg.set_content(
        f"{messageBody}"
    )
    
    # Attach Files as required
    if startrails:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg")
        if os.path.exists(file_path):
            msg.set_content(msg.get_content() + f"\n{os.path.basename(file_path)}")
            with open(file_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=os.path.basename(file_path))          
               
    if keogram:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
        if os.path.exists(file_path):
            msg.set_content(msg.get_content() + f"\n{os.path.basename(file_path)}")
            with open(file_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=os.path.basename(file_path))          

    # Send email via Gmail SMTP
    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()  # Secure connection
            server.login(emailAddress, emailPassword)
            server.send_message(msg)
        result = "Email sent successfully"
    except Exception as e:
        result = f"Error sending email: {e}"
    
    return result