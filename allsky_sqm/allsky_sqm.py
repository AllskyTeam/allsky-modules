'''
allsky_sqm.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

Portions of this code are from indi-allsky https://github.com/aaronwmorris/indi-allsky
'''

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import cv2
import os
import math

class ALLSKYSQM(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Sky Quality",
		"description": "Estimate sky quality from captured images",
		"module": "allsky_sqm",
		"version": "v1.0.1",
		"events": [
			"night"
		],
		"experimental": "true",
		"centersettings": "false",
		"testable": "true", 
		"extradatafilename": "allsky_sqm.json",
		"group": "Data Capture",
		"extradata": {
			"values": {
				"AS_SQM": {
					"name": "${SQM}",
					"format": "",
					"sample": "",
					"group": "Environment",
					"description": "Sky Quality",
					"type": "number"
				}
			}                         
		},    
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
				"help": "The name of the image mask. This mask is applied prior to calculating the sky quality.",
				"type": {
					"fieldtype": "image"
				}
			},
			"roi": {
				"required": "false",
				"description": "Region of Interest",
				"help": "The area of the image to check for sky quality. Format is x1,y1,x2,y2.",
				"type": {
					"fieldtype": "roi"
				}
			},
			"roifallback" : {
				"required": "false",
				"description": "Fallback %",
				"help": "If no ROI is set then this % of the image, from the center will be used.",
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
				"help": "Formula to adjust the read mean value, default can be a good starting point. This forumla can use only Pythons inbuilt maths functions and basic mathematical operators. Please see the documentation for more details of the formula variables available."
			},
			"debug" : {
				"required": "false",
				"description": "Enable debug mode",
				"help": "If selected each stage of the detection will generate images in the allsky tmp debug folder.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debugimage" : {
				"required": "false",
				"description": "Debug Image",
				"help": "Image to use for debugging. DO NOT set this unless you know what you are doing.",
				"tab": "Debug"
			}
		},
		"enabled": "false",
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Initial Release",
						"Portions of this code are from indi-allsky https://github.com/aaronwmorris/indi-allsky"
					]
				}
			],
			"v1.0.1" : [
				{
					"author": "Damian Grocholski (Mr-Groch)",
					"authorurl": "https://github.com/Mr-Groch",
					"changes": [
						"Use of weightedSqmAvg inspired by indi-allsky (https://github.com/aaronwmorris/indi-allsky)",
						"Added example default formula"
					]
				}
			]                                                         
		}    
	}
    
	def _add_internals(self, allowed_name):
		internals = {'AS_BIN', 'AS_EXPOSURE_US', 'AS_GAIN', 'AS_MEAN'}
		for internal in internals:
			val = allsky_shared.get_environment_variable(internal)
			key = internal.replace('AS_', '')
			allowed_name[key] = allsky_shared.asfloat(val)
		
		return allowed_name

	def _evaluate(self, expression, sqm_avg, weighted_sqm_avg):

		allowed_name = {
			k: v for k, v in math.__dict__.items() if not k.startswith("__")
		}
		allowed_name = self._add_internals(allowed_name)
		allowed_name['sqmAvg'] = sqm_avg
		allowed_name['weightedSqmAvg'] = weighted_sqm_avg

		code = compile(expression, "<string>", "eval")
		for name in code.co_names:
			if name not in allowed_name:
				raise NameError(f"The use of '{name}' is not allowed")

		return eval(code, {"__builtins__": {}}, allowed_name)

	def run(self):
		extra_data = {}
		mask = self.get_param('mask', '', str, True)
		roi = self.get_param('roi', '', str, True)
		debug = self.get_param('debug', False, bool)
		formula = self.get_param('formula', '', str, True)
		debug_image = self.get_param('debugimage', '', str, True)
		roi_fallback = self.get_param('roifallback', 5, int)
       
		if debug_image != "":
			image = cv2.imread(debug_image)
			if image is None:
				image = allsky_shared.image
				self.log(1, f'WARNING: Debug image set to {debug_image} but cannot be found, using latest allsky image')
			else:
				self.log(1, f'WARNING: Using debug image {debug_image}')
		else:
			image = allsky_shared.image

		image_mask = None
		if mask != "":
			maskPath = os.path.join(allsky_shared.get_environment_variable('ALLSKY_OVERLAY'), 'images', mask)
			image_mask = cv2.imread(maskPath,cv2.IMREAD_GRAYSCALE)
			if debug:
				allsky_shared.write_debug_image(self.meta_data['module'], 'image-mask.png', image_mask)

		if len(image.shape) == 2:
			gray_image = image
		else:
			gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

		if image_mask is not None:
			if gray_image.shape == image_mask.shape:
				gray_image = cv2.bitwise_and(src1=gray_image, src2=image_mask)
				if debug:
					allsky_shared.write_debug_image(self.meta_data['module'], 'masked-image.png', gray_image)
			else:
				self.log(0, 'ERROR in {__file__: Source image and mask dimensions do not match')

		image_height, image_width = gray_image.shape[:2]
		try:
			roi_list = roi.split(',')
			x1 = int(roi_list[0])
			y1 = int(roi_list[1])
			x2 = int(roi_list[2])
			y2 = int(roi_list[3])
		except:
			if len(roi) > 0:
				self.log(0, f'ERROR in {__file__: SQM ROI is invalid, falling back to {roi_fallback}% of image')
			else:
				self.log(4, f'INFO: SQM ROI not set, falling back to {roi_fallback}% of image')
			fallback_adj = (100 / roi_fallback)
			x1 = int((image_width / 2) - (image_width / fallback_adj))
			y1 = int((image_height / 2) - (image_height / fallback_adj))
			x2 = int((image_width / 2) + (image_width / fallback_adj))
			y2 = int((image_height / 2) + (image_height / fallback_adj))

		cropped_image = gray_image[y1:y2, x1:x2]

		if debug:
			allsky_shared.write_debug_image(self.meta_data['module'], 'cropped-image.png', cropped_image)

		max_exposure_s = allsky_shared.asfloat(allsky_shared.get_setting('nightmaxautoexposure')) / 1000
		exposure_s = allsky_shared.asfloat(allsky_shared.get_environment_variable('AS_EXPOSURE_US')) / 1000 / 1000
		max_gain = allsky_shared.asfloat(allsky_shared.get_setting('nightmaxautogain'))
		gain = allsky_shared.asfloat(allsky_shared.get_environment_variable('AS_GAIN'))

		sqm_avg = cv2.mean(src=cropped_image)[0]
		weighted_sqm_avg = (((max_exposure_s - exposure_s) / 10) + 1) * (sqm_avg * (((max_gain - gain) / 10) + 1))

		result = f'Final SQM Mean calculated as {sqm_avg}, weighted {weighted_sqm_avg}'
		if formula != '':
			self.log(4, f'INFO: SQM Mean calculated as {sqm_avg}, weighted {weighted_sqm_avg}')
			try:
				sqm = float(self._evaluate(formula, sqm_avg, weighted_sqm_avg))
				result = f'Final SQM calculated as {sqm}'
				self.log(4, f'INFO: Ran Formula: {formula}')
				self.log(4, f'INFO: {result}')
			except Exception as e:
				result = "Error " + str(e)
				sqm = weighted_sqm_avg
				self.log(0, f'ERROR in {__file__: {result}')
		else:
			sqm = weighted_sqm_avg
			self.log(4, f'INFO: {result}')

		extra_data['AS_SQM'] = sqm
		allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)

		return result

def sqm(params, event):
	allsky_sqm = ALLSKYSQM(params, event)
	result = allsky_sqm.run()

	return result  
    
def sqm_cleanup():
    moduleData = {
        "metaData": ALLSKYSQM.meta_data,
        "cleanup": {
            "files": {},
            "env": {
                ALLSKYSQM.meta_data['extradatafilename']
            }
        }
    }
    allsky_shared.cleanupModule(moduleData)
