""" allsky_script.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

This module will run a custom script
"""
import allsky_shared as s
import os 
import subprocess

metaData = {
	"name": "AllSKY SQM",
	"description": "Allsky Sky Quality Meter",
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
	    "scriptlocation": ""
	},
	"argumentdetails": {
	    "scriptlocation" : {
	        "required": "true",
	        "description": "File Location",
	        "help": "The location of the script to run"
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

def script(params, event):
	script = params["scriptlocation"]

	if os.path.isfile(script):
	    if os.access(script, os.X_OK):
	        res = subprocess.check_output(script) 
	        result = "Script {0} Executed.".format(script)
	    else:
	        s.log(0,"ERROR: Script {0} is not executable".format(script))
	        result = "Script {0} Is NOT Executeable.".format(script)
	else:
	    s.log(0,"ERROR: cannot access {0}".format(script))
	    result = "Script {0} Not FOund.".format(script)

	if len(image.shape) == 2:
	    grayImage = image
	else:
	    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	if imageMask is not None:
	    if grayImage.shape == imageMask.shape:
	        grayImage = cv2.bitwise_and(src1=grayImage, src2=imageMask)
	        if debug:
	            s.writeDebugImage(metaData["module"], "masked-image.png", grayImage)
	    else:
	        s.log(0,"ERROR: Source image and mask dimensions do not match")

	imageHeight, imageWidth = grayImage.shape[:2]
	try:
	    roiList = roi.split(",")
	    x1 = int(roiList[0])
	    y1 = int(roiList[1])
	    x2 = int(roiList[2])
	    y2 = int(roiList[3])
	except:
	    if len(roi) > 0:
	        s.log(0, "ERROR: SQM ROI is invalid, falling back to {0}% of image".format(fallback))
	    else:
	        s.log(1, "INFO: SQM ROI not set, falling back to {0}% of image".format(fallback))
	    fallbackAdj = (100 / fallback)
	    x1 = int((imageWidth / 2) - (imageWidth / fallbackAdj))
	    y1 = int((imageHeight / 2) - (imageHeight / fallbackAdj))
	    x2 = int((imageWidth / 2) + (imageWidth / fallbackAdj))
	    y2 = int((imageHeight / 2) + (imageHeight / fallbackAdj))

	croppedImage = grayImage[y1:y2, x1:x2]

	if debug:
	    s.writeDebugImage(metaData["module"], "cropped-image.png", croppedImage)

	maxExposure_s = s.asfloat(s.getSetting("nightmaxautoexposure")) / 1000
	exposure_s = s.asfloat(s.getEnvironmentVariable("AS_EXPOSURE_US")) / 1000 / 1000
	maxGain = s.asfloat(s.getSetting("nightmaxautogain"))
	gain = s.asfloat(s.getEnvironmentVariable("AS_GAIN"))

	sqmAvg = cv2.mean(src=croppedImage)[0]
	weightedSqmAvg = (((maxExposure_s - exposure_s) / 10) + 1) * (sqmAvg * (((maxGain - gain) / 10) + 1))

	result = "Final SQM Mean calculated as {0}, weighted {1}".format(sqmAvg, weightedSqmAvg)
	if formula != '':
	    s.log(1,"INFO: SQM Mean calculated as {0}, weighted {1}".format(sqmAvg, weightedSqmAvg))
	    try:
	        sqm = float(evaluate(formula, sqmAvg, weightedSqmAvg))
	        result = "Final SQM calculated as {0}".format(sqm)
	        s.log(1,"INFO: Ran Formula: " + formula)
	        s.log(1,"INFO: " + result)
	    except Exception as e:
	        result = "Error " + str(e)
	        sqm = weightedSqmAvg
	        s.log(0, "ERROR: " + result)
	else:
	    sqm = weightedSqmAvg
	    s.log(1,"INFO: " + result)

	os.environ["AS_SQM"] = str(sqm)

	return result

def rain_cleanup():
	moduleData = {
	    "metaData": metaData,
	    "cleanup": {
	        "files": {},
	        "env": {
	            "AS_SQM"
	        }
	    }
	}
	s.cleanupModule(moduleData)
	return result
