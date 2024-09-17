import allsky_shared as s
import os
import cv2
import numpy as np
import discord
from discord import SyncWebhook, File
from urllib.parse import urlparse
from io import BytesIO

metaData = {
    "name": "Discord",
    "description": "Posts to a Discord server",
    "version": "v1.0.1",
    "pythonversion": "3.9.0",
    "module": "allsky_discordsend",    
    "events": [
        "day",
        "night",
        "nightday"
    ],
    "experimental": "false",    
    "arguments":{
        "dayimage": "false",
        "dayimageannotated" : "true",
        "dayimageurl": "",
        "daycount": 5,
        "nightimage": "false",
        "nightimageannotated" : "true",
        "nightimageurl": "",
        "nightcount": 5,
        "startrails": "false",
        "startrailsimageurl": "",
        "keogram": "false",
        "keogramimageurl": "",
        "timelapse": "false",
        "timelapseimageurl": ""
    },
    "argumentdetails": {
        "dayimage" : {
            "required": "false",
            "description": "Post Day time Images",
            "help": "Post daytime images to the Discord Server",
            "tab": "Day Time",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "dayimageannotated" : {
            "description": "Send Annotated Image",
            "help": "Send the image after the overlay has been added. The discord module must ba after the overlay module in the flow",
            "tab": "Day Time",
            "type": {
                "fieldtype": "checkbox"
            }          
        },        
        "daycount" : {
            "required": "false",
            "description": "Daytime Count",
            "help": "Send every (this number) frame to Discord. This is to prevent flooding the discord channels",
            "tab": "Day Time",            
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }
        },        
        "dayimageurl": {
            "required": "false",
            "tab": "Day Time",            
            "description": "The webhook url for day time images"
        }, 
        "nightimage" : {
            "required": "false",
            "description": "Post Night time Images",
            "help": "Post Nighttime images to the Discord Server",
            "tab": "Night Time",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "nightimageannotated" : {
            "description": "Send Annotated Image",
            "help": "Send the image after the overlay has been added. The discord module must ba after the overlay module in the flow",
            "tab": "Night Time",
            "type": {
                "fieldtype": "checkbox"
            }          
        },          
        "nightcount" : {
            "required": "false",
            "description": "Nighttime Count",
            "help": "Send every (this number) frame to Discord. This is to prevent flooding the discord channels",
            "tab": "Night Time",            
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }
        },         
        "nightimageurl": {
            "required": "false",
            "tab": "Night Time",           
            "description": "The webhook url for night time images"
        },  

        "startrails" : {
            "required": "false",
            "description": "Post Star Trails Images",
            "help": "Post Star Trails images to the Discord Server",
            "tab": "Star Trails",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "startrailsimageurl": {
            "required": "false",
            "tab": "Star Trails",           
            "description": "The webhook url for Star Trails images"
        },  


        "keogram" : {
            "required": "false",
            "description": "Post Keograms Images",
            "help": "Post Keograms images to the Discord Server",
            "tab": "Keograms",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "keogramimageurl": {
            "required": "false",
            "tab": "Keograms",           
            "description": "The webhook url for Star Keograms"
        },  

        "timelapse" : {
            "required": "false",
            "description": "Post Timelapse videos",
            "help": "Post Timelapse videos to the Discord Server",
            "tab": "Timelapse",
            "type": {
                "fieldtype": "checkbox"
            }          
        },
        "timelapseimageurl": {
            "required": "false",
            "tab": "Timelapse",           
            "description": "The webhook url for Timelapses"
        }      
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Issue #161 - Send annotated image"
            }
        ]                                       
    }              
}

def cv2_discord_file(img, file_name):
    img_encode = cv2.imencode('.png', img)[1]
    data_encode = np.array(img_encode)
    byte_encode = data_encode.tobytes()
    byte_image = BytesIO(byte_encode)
    image=discord.File(byte_image, filename=os.path.basename(file_name))
    return image

def check_send(key, count, tod):
    result = False

    try:
        count = int(count)
    # pylint: disable=broad-exception-caught
    except Exception:
        count = 5

    current_count = 0
    if s.dbHasKey(key):
        current_count = s.dbGet(key)
    else:
        s.dbAdd(key, 0)

    current_count = current_count + 1
    s.dbUpdate(key, current_count)

    if current_count >= count:
        result = True
        s.dbUpdate(key, 0)

    s.log(4, f'INFO: {tod} - Sending after {count} current count is {current_count}, sending {result}')
    return result

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    # pylint: disable=broad-exception-caught
    except Exception:
        return False

def sendFile(fileName, sendURL, fileType, use_annotated):
    if validate_url(sendURL):
        if os.path.exists(fileName):
            file_size = os.path.getsize(fileName)
            if file_size < 8000000:
                if use_annotated:
                    discord_file = cv2_discord_file(s.image, fileName)
                else:
                    discord_file = discord.File(fileName)
                webhook = SyncWebhook.from_url(sendURL)
                webhook.send(file=discord_file)
                result = f'INFO: {fileType} file {fileName} sent to Discord'
                s.log(4, result)
            else:
                result = f'ERROR: {fileType} file {fileName} is too large to send to Discord. File is {file_size} bytes'
                s.log(0, result)
        else:
            result = f'ERROR: {fileType} file {fileName} not found'
            s.log(0, result)
    else:
        result = f'ERROR: {fileType} Invalid Discord URL '
        s.log(0, f'{result} {sendURL}')

    return result

def discordsend(params, event):

    day_image = params['dayimage']
    day_image_annotated = params['dayimageannotated']
    day_image_url = params['dayimageurl']
    day_count = params['daycount']

    night_image = params['nightimage']
    night_image_annotated = params['nightimageannotated']
    night_image_url = params['nightimageurl']
    night_count = params['nightcount']

    startrails = params['startrails']
    startrails_image_url = params['startrailsimageurl']

    keogram = params['keogram']
    timelapse_image_url = params['keogramimageurl']

    timelapse = params['timelapse']
    timelapse_image_url = params['timelapseimageurl']

    result = 'No files sent to Discord'

    if event == 'postcapture':
        upload_file = False
        send_url = ''
        counter = 5

        if day_image and s.TOD == 'day':
            upload_file = True
            send_url = day_image_url
            counter = day_count
            use_annotated = day_image_annotated

        if night_image and s.TOD == 'night':
            upload_file = True
            send_url = night_image_url
            counter = night_count
            use_annotated = night_image_annotated

        db_key = 'discord' + s.TOD
        count_ok = check_send(db_key, counter, s.TOD.title())

        if upload_file and count_ok:
            file_name = s.getEnvironmentVariable('CURRENT_IMAGE')
            result = sendFile(file_name, send_url, s.TOD.title(), use_annotated)

    if event == 'nightday':
        date = s.getEnvironmentVariable('DATE')
        date_dir = s.getEnvironmentVariable('DATE_DIR')
        full_file_name = s.getSetting('filename')
        _, file_extension = os.path.splitext(full_file_name)
        if startrails:
            file_name = os.path.join(date_dir, 'startrails', 'startrails-' + date + file_extension)
            result = sendFile(file_name, startrails_image_url, 'Star Trails', False)

        if keogram:
            file_name = os.path.join(date_dir, 'keogram', 'keogram-' + date + file_extension)
            result = sendFile(file_name, timelapse_image_url, 'Keogram', False)

        if timelapse:
            file_name = os.path.join(date_dir, 'allsky-' + date + '.mp4')
            result = sendFile(file_name, timelapse_image_url, 'Timelapse', False)

    return result