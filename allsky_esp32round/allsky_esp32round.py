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
            "size34": 800,
            "size4": 720,
            "enable34": "False",
			"enable4": "False",
            "filename34": "resized_34",
            "filename4": "resized_4"
        },
        "argumentdetails": {
            "roi": {
                "required": "true",
                "description": "Image Area",
                "help": "The area of the image to use, will be resized after this is cropped. Make sure the ROI selcted is a square",
                "type": {
                    "fieldtype": "roi"
                }
            },
			"enable34" : {
				"required": "false",
				"description": "Enable 3.4 inch display",
				"type": {
					"fieldtype": "checkbox"
				}
			},            
            "size34" : {
                "required": "false",
                "description": "3.4 Inch image size",
                "help": "width and height of the final image in pixels, Default is 800x800 Pixels",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 5000,
                    "step": 1
                },
				"filters": {
					"filter": "enable34",
					"filtertype": "show",
					"values": [
						"enable34"
					]
				}                 
            },
			"filename34": {
				"description": "Filename",
				"help": "The filename for the 3.4inch image. DO NOT include the file extension as this will be added automatically.",
				"filters": {
					"filter": "enable34",
					"filtertype": "show",
					"values": [
						"enable34"
					]
				}    
			},            
			"enable4" : {
				"required": "false",
				"description": "Enable 4 inch display",
				"type": {
					"fieldtype": "checkbox"
				}
			},             
            "size4" : {
                "required": "false",
                "description": "4 Inch image size",
                "help": "width and height of the final image in pixels, Default is 720x720 pixels",
                "type": {
                    "fieldtype": "spinner",
                    "min": 1,
                    "max": 5000,
                    "step": 1
                },
				"filters": {
					"filter": "enable4",
					"filtertype": "show",
					"values": [
						"enable4"
					]
				}                 
            },
			"filename4": {
				"description": "Filename",
				"help": "The filename for the 4inch image. DO NOT include the file extension as this will be added automatically.",
				"filters": {
					"filter": "enable4",
					"filtertype": "show",
					"values": [
						"enable4"
					]
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

    def create_image(self, roi, size, quality, filename):
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
                result = f"Failed to crop image {e}"
                allsky_shared.log(1, f"ERROR: {result}")
                return result
        
            allsky_filename = allsky_shared.getSetting("filename")
            ext = os.path.splitext(allsky_filename)[1][1:]
    
            save_dir = allsky_shared.get_environment_variable("CAPTURE_SAVE_DIR")
            if save_dir is None:
                save_dir = allsky_shared.get_environment_variable("ALLSKY_CURRENT_DIR")
                
            path = os.path.join(save_dir, f"{filename}.{ext}")
                        
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
                              
    def run(self):
        result = ''
        
        quality = allsky_shared.get_setting("quality")
        roi = self.get_param('roi', '', str)  

        enabled34 = self.get_param('enable34', False, bool)
        enabled4 = self.get_param('enable4', False, bool)
        size34 = self.get_param('size', 800, int)  
        size4 = self.get_param('size', 720, int)  
        filename34 = self.get_param('filename34', 'resized_34', str) 
        filename4 = self.get_param('filename4', 'resized_4', str) 
        
        result34 = ''
        result4 = ''
        
        if enabled34:            
            result34 = self.create_image(roi, size34, quality, filename34)
            
        if enabled4:
            result4 = self.create_image(roi, size4, quality, filename4)

        result = ', '.join(x for x in (result34, result4) if x)

        return result

def esp32round(params, event):
    module = ALLSKYESP32ROUND(params, event)
    return module.run()