""" allsky_script.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will create a resized image that can be used on a round display
"""
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import cv2 
import pathlib

class ALLSKYESP32ROUND(ALLSKYMODULEBASE):
    
    meta_data = {
        "name": "AllSKY Round Display",
        "description": "Exports an image for use on a round oled display",
        "version": "v1.0.0",    
        "events": [
            "day",
            "night"
        ],
        "experimental": "false",    
        "arguments":{
            "roi": "",
            "size": 720
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
        },
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

    def write_image(self, image, path, quality):
        fileExtension = pathlib.Path(path).suffix

        result = True
        try:
            allsky_shared.checkAndCreatePath(path)

            if fileExtension == ".jpg":
                cv2.imwrite(path, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            else:
                cv2.imwrite(path, image, [int(cv2.IMWRITE_PNG_COMPRESSION), quality]) 
        except:
            result = False
        
        return result
  
    def run(self):
        result = ''
        
        quality = allsky_shared.get_setting("quality")
        size = self.get_param('size', 720, int)  
        roi = self.get_param('roi', '', str)  
            
        if quality is not None:
            quality = int(quality)
            binning = allsky_shared.get_environment_variable('AS_BIN')
            
            if binning is None:
                binning = 1
            binning = int(binning)

            try:
                roiList = roi.split(",")
                x = int(int(roiList[0]) / binning)
                y = int(int(roiList[1]) / binning)
                x1 = int(int(roiList[2]) / binning)
                y1 = int(int(roiList[3]) / binning)
            except Exception:
                result = f"Invalid ROI for allsky_round module {e}"
                allsky_shared.log(1, f"ERROR: {result}")
                return result
                
            try:
                cropped = allsky_shared.image[y:y1, x:x1]
                resized = cv2.resize(cropped, (size, size), interpolation=cv2.INTER_LINEAR)
            except Exception as e:
                result = f"Falied to crop image {e}"
                allsky_shared.log(1, f"ERROR: {result}")
                return result
        
            filename = allsky_shared.getSetting("filename")
            ext = os.path.splitext(filename)[1][1:]
    
            save_dir = allsky_shared.get_environment_variable("CAPTURE_SAVE_DIR")
            if save_dir is None:
                save_dir = allsky_shared.get_environment_variable("ALLSKY_CURRENT_DIR")
                
            path = os.path.join(save_dir, f"resized.{ext}")
                        
            if self.write_image(resized, path, quality):
                result = f"Image cropped, resized and saved to {path}"
                allsky_shared.log(1, result)
            else:
                result = f"Failed to save {path}"
                allsky_shared.log(1, f"ERROR: Failed to save image {path}")
        else:
            result = "Cannot determine the image quality. Intermediate image NOT saved."
            allsky_shared.log(1, f"ERROR: {result}")
            
        return result

def esp32round(params, event):
    module = ALLSKYESP32ROUND(params, event)
    return module.run()