'''
allsky_sqm.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Portions of this code are from indi-allsky https://github.com/aaronwmorris/indi-allsky

Changelog:
v1.0.1 by Damian Grocholski (Mr-Groch)
- Use of weightedSqmAvg inspired by indi-allsky (https://github.com/aaronwmorris/indi-allsky)
- Added example default formula

'''
import allsky_shared as s
import cv2
import os
import math

metaData = {
    "name": "Sky Quality",
    "description": "Calculates sky quality",
    "module": "allsky_sqm",
    "version": "v1.0.1",
    "events": [
        "night"
    ],
    "experimental": "true",
    "arguments":{
        "mask": "",
        "roi": "",
        "debug": "false",
        "debugimage": "",
        "roifallback": 5,
        "formula": "21.53 + (-0.03817 * weightedSqmAvg)"
    },
    "argumentdetails": {
        "mask" : {
            "required": "false",
            "description": "Mask Path",
            "help": "The name of the image mask. This mask is applied prior to calculating the sky quality",
            "type": {
                "fieldtype": "image"
            }
        },
        "roi": {
            "required": "false",
            "description": "Region of Interest",
            "help": "The area of the image to check for sky quality. Format is x1,y1,x2,y2",
            "type": {
                "fieldtype": "roi"
            }
        },
        "roifallback" : {
            "required": "false",
            "description": "Fallback %",
            "help": "If no ROI is set then this % of the image, from the center will be used",
            "type": {
                "fieldtype": "spinner",
                "min": 1,
                "max": 100,
                "step": 1
            }
        },
        "formula": {
            "required": "false",
            "description": "Adjustment Forumla",
            "help": "Formula to adjust the read mean value, default can be a good starting point. This forumla can use only Pythons inbuilt maths functions and basic mathematical operators. Please see the documentation for more details of the formula variables available"
        },
        "debug" : {
            "required": "false",
            "description": "Enable debug mode",
            "help": "If selected each stage of the detection will generate images in the allsky tmp debug folder",
            "tab": "Debug",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "debugimage" : {
            "required": "false",
            "description": "Debug Image",
            "help": "Image to use for debugging. DO NOT set this unless you know what you are doing",
            "tab": "Debug"
        }
    },
    "enabled": "false"
}

def addInternals(ALLOWED_NAMES):
    internals = {'AS_BIN', 'AS_EXPOSURE_US', 'AS_GAIN', 'AS_MEAN'}
    for internal in internals:
        val = s.getEnvironmentVariable(internal)
        key = internal.replace('AS_', '')
        ALLOWED_NAMES[key] = s.asfloat(val)
    
    return ALLOWED_NAMES

def evaluate(expression, sqmAvg, weightedSqmAvg):

    ALLOWED_NAMES = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    ALLOWED_NAMES = addInternals(ALLOWED_NAMES)
    ALLOWED_NAMES['sqmAvg'] = sqmAvg
    ALLOWED_NAMES['weightedSqmAvg'] = weightedSqmAvg

    code = compile(expression, "<string>", "eval")
    for name in code.co_names:
        if name not in ALLOWED_NAMES:
            raise NameError(f"The use of '{name}' is not allowed")

    return eval(code, {"__builtins__": {}}, ALLOWED_NAMES)


def sqm(params, event):
    mask = params["mask"]
    roi = params["roi"]
    debug = params["debug"]
    formula = params["formula"]
    debugimage = params["debugimage"]
    fallback = int(params["roifallback"])

    if debugimage != "":
        image = cv2.imread(debugimage)
        if image is None:
            image = s.image
            s.log(0, "WARNING: Debug image set to {0} but cannot be found, using latest allsky image".format(debugimage))
        else:
            s.log(0, "WARNING: Using debug image {0}".format(debugimage))
    else:
        image = s.image

    imageMask = None
    if mask != "":
        maskPath = os.path.join(s.getEnvironmentVariable("ALLSKY_OVERLAY"),"images",mask)
        imageMask = cv2.imread(maskPath,cv2.IMREAD_GRAYSCALE)
        if debug:
            s.writeDebugImage(metaData["module"], "image-mask.png", imageMask)

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