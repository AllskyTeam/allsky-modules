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
        "recipient_email": "",
        "subject_text": "Last night's Allsky images",
        "subject_date": "true",
        "message_body": "Attached are last night's Allsky camera images.",
        "startrails": "false",
        "keogram": "false",
        "timelapse": "false",
        "sender_email": "", 
        "sender_password": "",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": "587"
    },
    "argumentdetails": { 
        "recipient_email": {
            "required": "true",
            "description": "Recipient email address",
            "help": "Separate with comma for multiple. Will be sent as a group message to all recipients.",
            "tab": "Daily Notification Setup"             
        },
        "subject_text": {
            "required": "true",
            "description": "Email Subject Line",
            "help": "",
            "tab": "Daily Notification Setup"             
        },
        "subject_date": {
            "required": "false",
            "description": "Append date to Subject line",
            "help": "eg: Last night's Allsky images - 20250401",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }                
        },
        "message_body": {
            "required": "true",
            "description": "Email Message Text",
            "help": "Any message body text you want to include.  use \n for a line break. File names will be listed below this text.",
            "tab": "Daily Notification Setup"             
        },
        "startrails": {
            "required": "false",
            "description": "Attach Star Trails",
            "help": "",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "keogram": {
            "required": "false",
            "description": "Attach Keogram",
            "help": "",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        }, 
        "timelapse": {
            "required": "false",
            "description": "Attach Timelapse",
            "help": "",
            "tab": "Daily Notification Setup",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "sender_email": {
            "required": "true",
            "description": "Sender email address",
            "help": "",
            "tab": "Gmail Sender Account Setup"   
        },        
        "sender_password": {
            "required": "true",        
            "description": "Sender Google App Password",
            "help": "NOT your gmail login password. Get this from your google account's security settings.",
            "tab": "Gmail Sender Account Setup"
        },
        "smtp_server": {
            "required": "true",
            "description": "gmail SMTP server address",
            "help": "Should not need to change this",
            "tab": "Gmail Sender Account Setup"          
        },
        "smtp_port": {
            "required": "true",
            "description": "SMTP server port",
            "help": "Should not need to change this",
            "tab": "Gmail Sender Account Setup"
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
    smtp_server = params['smtp_server']
    smtp_port = params['smtp_port']
    sender_email = params['sender_email']
    sender_password = params['sender_password']
    recipient_email = params['recipient_email']
    subject_text = params['subject_text']
    subject_date = params['subject_date']
    message_body = params['message_body']
    startrails = params['startrails']
    keogram = params['keogram']
    timelapse = params['timelapse']
       
    # Get yesterday's date in YYYYMMDD format
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

    # Get user's home directory dynamically
    home_dir = os.path.expanduser("~")

    # Initialize emailmessage details
    msg = EmailMessage()
    msg["From"] = email_sender_address
    msg["To"] = recipient_email
      
    #message_body = f"{message_body}\n"
    
    if subject_date:
        msg["Subject"] = f"{subject_text} - {yesterday}"
    else:
        msg["Subject"] = subject_text
    
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
        
        message_body += f"\n"       # add a line break before listing files
        
        # First loop: build message_body and filter files
        valid_file_paths.clear()
        for file_path in file_paths:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_size_mb = round(file_size / 1024 / 1024,1)
                total_attachment_size += file_size
                if total_attachment_size > max_attachment_size:
                    message_body += f"\nTotal attachment size exceeds 25MB limit.\n{os.path.basename(file_path)} ({file_size_mb}mb) not attached"
                    result += f"Error: Total attachment size exceeds 25MB limit. File wont be attached: {file_path}\n"
                else:
                    message_body += f"\n{os.path.basename(file_path)}  ({file_size_mb}mb) attached"
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
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        result += "Email sent successfully"
    except Exception as e:
        result += f"Error sending email: {e}"
    
    return result
