""" allsky_script.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will run a custom script
"""
import allsky_shared as s
import os
import cv2 
import pathlib

metaData = {
    "name": "AllSKY Round Display",
    "description": "Exports an image for use on a round oled display",
    "version": "v1.0.0",    
    "events": [
        "day",
        "night",
        "endofnight",
        "daynight",
        "nightday",
        "periodic"
    ],
    "experimental": "false",    
    "arguments":{
        "roi": "",
        "size": 800
    },
    "argumentdetails": {
        "roi": {
            "required": "true",
            "description": "Image Area",
            "help": "The area of the image to use, will be resized after this is cropped",
            "type": {
                "fieldtype": "roi"
            }
        },
        "size" : {
            "required": "true",
            "description": "Size",
            "help": "width and height of the final image in pixels",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 5000,
                "step": 1
            }
        }      
    }          
}

def writeImage(image, path, quality):
    fileExtension = pathlib.Path(path).suffix

    result = True
    try:
        s.checkAndCreatePath(path)

        if fileExtension == ".jpg":
            cv2.imwrite(path, image, [s.int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            cv2.imwrite(path, image, [s.int(cv2.IMWRITE_PNG_COMPRESSION), quality]) 
    except:
        result = False
    
    return result
  
def esp32round(params, event):
    result = ""
    roi = params["roi"]
    size = s.int(params["size"])
    quality = s.getSetting("quality")
    if quality is not None:
        quality = s.int(quality)
        binning = s.getEnvironmentVariable("AS_BIN")
        
        if binning is None:
            binning = 1
        binning = s.int(binning)

        try:
            roiList = roi.split(",")
            x = s.int(s.int(roiList[0]) / binning)
            y = s.int(s.int(roiList[1]) / binning)
            x1 = s.int(s.int(roiList[2]) / binning)
            y1 = s.int(s.int(roiList[3]) / binning)
        except Exception:
            result = f"Invalid ROI for allsky_round module {e}"
            s.log(1, f"ERROR: {result}")
            return result
            
        try:
            cropped = s.image[y:y1, x:x1]
            resized = cv2.resize(cropped, (size, size), interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            result = f"Falied to crop image {e}"
            s.log(1, f"ERROR: {result}")
            return result
      
        filename = s.getSetting("filename")
        ext = os.path.splitext(filename)[1][1:]
  
        save_dir = s.getEnvironmentVariable("CAPTURE_SAVE_DIR")
        if save_dir is None:
            save_dir = s.getEnvironmentVariable("ALLSKY_CURRENT_DIR")
            
        path = os.path.join(save_dir, f"resized.{ext}")
                    
        if writeImage(resized, path, quality):
            result = f"Image cropped, resized and saved to {path}"
            s.log(1, result)
        else:
            result = f"Failed to save {path}"
            s.log(1, f"ERROR: Failed to save image {path}")

    else:
        result = "Cannot determine the image quality. Intermediate image NOT saved."
        s.log(1, f"ERROR: {result}")
        
    return result