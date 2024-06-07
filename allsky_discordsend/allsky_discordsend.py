'''
allsky_discordsend.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

'''
import allsky_shared as s
import os
import numpy as np
import discord
from discord import SyncWebhook, File
from urllib.parse import urlparse

metaData = {
    "name": "Discord",
    "description": "Posts to a Discord server",
    "version": "v1.0.0",
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
        "dayimageurl": "",
        "daycount": 5,
        "nightimage": "false",
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
        ]                              
    }              
}

def checkSend(key, count, type):
    result = False

    try:
        count = int(count)
    except:
        count = 5

    currentCount = 0
    if s.dbHasKey(key):
        currentCount = s.dbGet(key)
    else:
        s.dbAdd(key, 0)

    currentCount = currentCount + 1
    s.dbUpdate(key, currentCount)

    if currentCount >= count:
        result = True
        s.dbUpdate(key, 0)
    
    s.log(1, "INFO: Sending after {0} current count is {1}, sending {2}".format(count, currentCount, result))
    return result

def validateURL(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sendFile(fileName, sendURL, fileType):
    if validateURL(sendURL):
        if os.path.exists(fileName):
            fileSize = os.path.getsize(fileName)
            if fileSize < 8000000:
                df = discord.File(fileName)
                webhook = SyncWebhook.from_url(sendURL)
                webhook.send(file=df)
                result = 'INFO: {0} file {1} sent to Discord'.format(fileType, fileName)
                s.log(1, result)
            else:
                result = 'ERROR: {0} file {1} is too large to send to Discord. File is {2} bytes'.format(fileType, fileName, fileSize)
                s.log(0, result)
        else:
            result = 'ERROR: {0} file {1} not found'.format(fileType, fileName)
            s.log(0, result)
    else:
        result = 'ERROR: {0} Invalid Discord URL '.format(fileType)
        s.log(0, result + ' ' + sendURL)

    return result

def discordsend(params, event):

    dayimage = params['dayimage']
    dayimageurl = params['dayimageurl']
    daycount = params['daycount']

    nightimage = params['nightimage']
    nightimageurl = params['nightimageurl']
    nightcount = params['nightcount']

    startrails = params['startrails']
    startrailsimageurl = params['startrailsimageurl']

    keogram = params['keogram']
    keogramimageurl = params['keogramimageurl']

    timelapse = params['timelapse']
    timelapseimageurl = params['timelapseimageurl']

    result = 'No files sent to Discord'

    if s.args.event == 'postcapture':
        uploadFile = False
        sendURL = ''
        counter = 5

        if dayimage and s.TOD == 'day':
            uploadFile = True
            sendURL = dayimageurl
            counter = daycount

        if nightimage and s.TOD == 'night':
            uploadFile = True
            sendURL = nightimageurl
            counter = nightcount

        dbKey = 'discord' + s.TOD
        countOk = checkSend(dbKey, counter, s.TOD.title())

        if uploadFile and countOk:
            fileName = s.getEnvironmentVariable('CURRENT_IMAGE')
            result = sendFile(fileName, sendURL, s.TOD.title())

    if s.args.event == 'nightday':
        date = s.getEnvironmentVariable('DATE')
        dateDir = s.getEnvironmentVariable('DATE_DIR')
        fullFileName = s.getSetting('filename')
        filename, fileExtension = os.path.splitext(fullFileName)
        if startrails:
            fileName = os.path.join(dateDir, 'startrails', 'startrails-' + date + fileExtension)
            result = sendFile(fileName, startrailsimageurl, 'Star Trails')

        if keogram:
            fileName = os.path.join(dateDir, 'keogram', 'keogram-' + date + fileExtension)
            result = sendFile(fileName, keogramimageurl, 'Keogram')

        if timelapse:
            fileName = os.path.join(dateDir, 'allsky-' + date + '.mp4')
            result = sendFile(fileName, timelapseimageurl, 'Timelapse')

    return result