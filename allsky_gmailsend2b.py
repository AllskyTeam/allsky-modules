import allsky_shared as s
import smtplib
import os
import datetime
from email.message import EmailMessage
import mimetypes

metaData = {
    "name": "Send with Gmail 2",
    "description": "emails nightly images to email recipients",
    "version": "v0.1",
    "pythonversion": "3.9.0",
    "module": "allsky_gmailsend2",    
    "events": [
        "nightday",
        "periodic"
    ],
    "experimental": "false",  
    "arguments": {
        "recipientEmail": "recipient@example.com",
        "subjectText": "Last night's Allsky images",
        "subjectDate": "true",
        "message_body": "Attached are last night's Allsky camera images.",
        "startrails": "false",
        "keogram": "false",
        "timelapse": "false",
        "emailAddress": "your_email@gmail.com", 
        "emailPassword": "your_app_password",
        "smtpServer": "smtp.gmail.com",
        "smtpPort": "587"
    },
    "argumentdetails": { 
        "recipientEmail": {
            "required": "true",
            "description": "Recipient email addresses",
            "help": "only enter one email address",
            "tab": "Notification Setup"             
        },
        "subjectText": {
            "required": "true",
            "description": "Email Subject Line",
            "help": "",
            "tab": "Notification Setup"             
        },
        "subjectDate": {
            "required": "false",
            "description": "Append date to Subject line",
            "help": "eg: Last night's Allsky images - 20250401",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }                
        },
        "message_body": {
            "required": "true",
            "description": "Email Message Text",
            "help": "Any message body text you want to include. File names will be appended to this text.",
            "tab": "Notification Setup"             
        },
        "startrails": {
            "required": "false",
            "description": "Attach Star Trails",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "keogram": {
            "required": "false",
            "description": "Attach Keogram",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "timelapse": {
            "required": "false",
            "description": "Attach Timelapse",
            "help": "",
            "tab": "Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "emailAddress": {
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
        "smtpServer": {
            "required": "true",
            "description": "gmail SMTP server address",
            "help": "you should not need to change this",
            "tab": "Gmail Account Setup"          
        },
        "smtpPort": {
            "required": "true",
            "description": "SMTP server port",
            "help": "you should not need to change this",
            "tab": "Gmail Account Setup"
        }
    },
    "enabled": "false",
    "changelog": {
        "v0.1": [
            {
                "author": "Kentner Cottingham",
                "authorurl": "https://github.com/NiteRide",
                "changes": "Initial Release"
            }
        ]                                       
    }              
}

def gmailsend2(params, event):
    # Gmail SMTP configuration and parameters
    smtpServer = params['smtpServer']
    smtpPort = params['smtpPort']
    emailAddress = params['emailAddress']
    emailPassword = params['emailPassword']
    recipientEmail = params['recipientEmail']
    subjectText = params['subjectText']
    subjectDate = params['subjectDate']
    message_body = params['message_body']
    startrails = params['startrails']
    keogram = params['keogram']
    timelapse = params['timelapse']
    
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
    
    # Initialize total attachment size (max is 25MB for gmail)
    total_attachment_size = 0
    max_attachment_size = 25 * 1024 * 1024
    file_paths = []
    valid_file_paths = []

    # Function to validate and attach files dynamically
    def check_files(file_paths):
        nonlocal total_attachment_size
        nonlocal message_body
        nonlocal valid_file_paths
        nonlocal result
    
        # First loop: build message_body and filter files
        valid_file_paths.clear()
        for file_path in file_paths:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_sizeMb = file_size / 1024 / 1024
                total_attachment_size += file_size
                if total_attachment_size + file_size > max_attachment_size:
                    message_body += f"\n{os.path.basename(file_path)} too large to attach: {file_sizeMb}mb"
                    result += f"Error: Total attachment size exceeds 25MB limit. File not attached: {file_path}\n"
                else:
                    message_body += f"\n{os.path.basename(file_path)}  {file_sizeMb}mb"
                    valid_file_paths.append(file_path)
            else:
                result += f"Error: File does not exist: {file_path}\n"
        return result
        
    def attach_files(attach_files):
        nonlocal valid_file_paths
        nonlocal result

        # Second loop: attach valid files
        for file_path in attach_files:
            try:
                mime_type, _ = mimetypes.guess_type(file_path)
                maintype, subtype = mime_type.split('/')
                with open(file_path, "rb") as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(file_path))
                    result += f"Attached: {file_path}\n"
            except Exception as e:
                result += f"Error attaching file: {e}\n"
        return result

    # Check user file selections
    if startrails:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/startrails/startrails-{yesterday}.jpg")
        file_paths.append(file_path)
        
    if keogram:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/keogram/keogram-{yesterday}.jpg")
        file_paths.append(file_path)
        
    if timelapse:
        file_path = os.path.join(home_dir, f"allsky/images/{yesterday}/allsky-{yesterday}.mp4")
        file_paths.append(file_path)
    
    # validate file paths and file size
    result +=check_files(file_paths)
    
    # Set the main body content with the attachment details BEFORE attaching files
    msg.set_content(message_body)
    
    #attach the valid files
    result += attach_files(valid_file_paths)

    # Send email via Gmail SMTP / TLS
    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()  # Secure connection
            server.login(emailAddress, emailPassword)
            server.send_message(msg)
        result = "Email sent successfully"
    except Exception as e:
        result = f"Error sending email: {e}"
    
    return result
