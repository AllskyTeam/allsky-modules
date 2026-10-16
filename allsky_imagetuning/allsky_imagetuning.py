'''
allsky_imagetuning.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky

Advanced image enhancement module providing control over:
- Saturation
- Contrast
- Gamma (Brightness)
- Sharpening
- Noise Reduction (Denoising)
'''

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import cv2
import numpy as np

class IMAGETUNING(ALLSKYMODULEBASE):
    
    meta_data = {
        "name": "Image Tuning",
        "description": "Advanced control: Saturation, Contrast, Gamma, Sharpening, and Denoise",
        "module": "allsky_imagetuning",
        "version": "v2.1.1",
        "events": [
            "night",
            "day"
        ],
        "experimental": "false",
        "arguments":{
            "enablesaturation": "false",
            "enablecontrast": "false",
            "enablegamma": "false",
            "enablesharpness": "false",
            "enabledenoise": "false",
            "level": "0",
            "contrast": "1.0",
            "gamma": "1.0",
            "sharpness": "0",
            "denoise": "0",
            "auto_anchor": "false"
        },
        "argumentdetails": {
			"enablesaturation" : {
				"required": "false",
				"description": "Enable Saturation",
				"help": "Enable saturation level of the image.",
				"layout": {
					"row": "saturation",
					"title": "Saturation",
					"label": "Enable",
					"width": 4
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},            
            "level" : {
                "required": "false",
                "description": "Saturation",
                "help": "0 is neutral. -10 is B&W. 10 is max color.",
				"layout": {
					"row": "saturation",
					"title": "Saturation",
					"label": "Level",
					"width": 4
				},                
                "type": {
                    "fieldtype": "spinner",
                    "min": -10,
                    "max": 10,
                    "step": 0.1
                },
				"filters": {
					"filter": "enablesaturation",
					"filtertype": "show"
				}                
            },
            
            
			"enablecontrast" : {
				"required": "false",
				"description": "Enable Contrast",
				"help": "Enable contrast changes for the image.",
				"layout": {
					"row": "contrastt",
					"title": "Contrast",
					"label": "Enable",
					"width": 4
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},              
            "contrast" : {
                "required": "false",
                "description": "Contrast",
                "help": "1.0 is neutral. Higher values increase separation between light and dark.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 5,
                    "step": 0.01
                },
				"layout": {
					"row": "contrastt",
					"title": "Contrast",
					"label": "Level",
					"width": 4
				},
				"filters": {
					"filter": "enablecontrast",
					"filtertype": "show"
				}                    
            },
            "auto_anchor" : {
                "required": "false",
                "description": "Smart Contrast",
                "help": "Automatically adjusts brightness when changing Contrast.",
                "type": {
                    "fieldtype": "checkbox"
                },
				"layout": {
					"row": "contrastt",
					"title": "Contrast",
					"label": "Smart Contrast",
					"width": 4
				},
				"filters": {
					"filter": "enablecontrast",
					"filtertype": "show"
				}                  
            },
            
            
            
            
			"enablegamma" : {
				"required": "false",
				"description": "Enable Gamma corrction",
				"help": "Enable Gamma correction",
				"layout": {
					"row": "gammaa",
					"title": "Gamma (Brightness)",
					"label": "Enable",
					"width": 4
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},             
            "gamma" : {
                "required": "false",
                "description": "Gamma (Brightness)",
                "help": "1.0 is neutral. Values > 1.0 lift shadows (brighten dark areas).",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0.1,
                    "max": 5.0,
                    "step": 0.1
                },
				"layout": {
					"row": "gammaa",
					"title": "Gamma (Brightness)",
					"label": "Level",
					"width": 4
				},
				"filters": {
					"filter": "enablegamma",
					"filtertype": "show"
				}                 
            },
            
            
			"enablesharpness" : {
				"required": "false",
				"description": "Enable Sharpening",
				"help": "Enable sharpening of the image.",
				"layout": {
					"row": "sharpnesss",
					"title": "Sharpening",
					"label": "Enable",
					"width": 4
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},             
            "sharpness" : {
                "required": "false",
                "description": "Sharpening",
                "help": "0 is off. 1 is mild, 5 is very strong. Enhances edges.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 5,
                    "step": 1
                },
				"layout": {
					"row": "sharpnesss",
					"title": "Sharpness",
					"label": "Level",
					"width": 4
				},
				"filters": {
					"filter": "enablesharpness",
					"filtertype": "show"
				}                
            },
            
			"enabledenoise" : {
				"required": "false",
				"description": "Enable Noise Reduction",
				"help": "Enable noise reduction of the image.",
				"layout": {
					"row": "denoises",
					"title": "Noise Reduction",
					"label": "Enable",
					"width": 4
				},
				"type": {
					"fieldtype": "checkbox"
				}
			},             
            "denoise" : {
                "required": "false",
                "description": "Noise Reduction",
                "help": "0 is off. Removes grain. Higher values smooth more but may blur faint stars.",
                "type": {
                    "fieldtype": "spinner",
                    "min": 0,
                    "max": 5,
                    "step": 1
                },
				"layout": {
					"row": "denoises",
					"title": "Noise Reduction",
					"label": "Level",
					"width": 4
				},
				"filters": {
					"filter": "enabledenoise",
					"filtertype": "show"
				}                  
            }
        },
        "enabled": "false",
        "changelog": {
            "v2.1.0" : [
                {
                    "author": "chvvkumar",
                    "authorurl": "https://github.com/chvvkumar",
                    "changes": "Added Noise Reduction (Bilateral Filter)"
                }
            ],
            "v2.1.1" : [
                {
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
                    "changes": "Migrated to new module system"
                }
            ]            
        }
    }

    def run(self):
        '''
        Main entry point for the image tuning module.
        
        This module applies various image enhancements including:
        - Noise Reduction (first step to clean the image)
        - Saturation adjustment
        - Gamma correction (brightness)
        - Contrast enhancement with optional smart anchoring
        - Sharpening (final step to enhance details)
        
        Parameters:
        - params: Dictionary of module parameters
        - event: The event triggering this module (day/night)
        
        Returns:
        - String describing the enhancements applied
        '''
        
        result = []
        
        # Check if image is available
        if not hasattr(allsky_shared, 'image') or allsky_shared.image is None:
            allsky_shared.log(0, "ERROR: No image found")
            return "No image found"

        try:
            # Parse arguments safely
            sat_level = self.get_param('level', 0, float)
            contrast_level = self.get_param('contrast', 1.0, float)
            gamma_level = self.get_param('gamma', 1.0, float)
            gamma_level = self.get_param('gamma', 1.0, float)            
            sharpness_level = self.get_param('sharpness', 0, int)
            denoise_level = self.get_param('denoise', 0, int)
            auto_anchor = self.get_param('auto_anchor', 'false', bool)

            enable_saturation = self.get_param('enablesaturation', 'false', bool)
            enable_contrast = self.get_param('enablecontrast', 'false', bool)
            enable_gamma = self.get_param('enablegamma', 'false', bool)
            enable_sharpness = self.get_param('enablesharpness', 'false', bool)
            enable_denoise = self.get_param('enabledenoise', 'false', bool)
                  
            # Enforce limits
            sat_level = max(-10.0, min(10.0, sat_level))
            contrast_level = max(0.0, min(5.0, contrast_level))
            gamma_level = max(0.1, min(5.0, gamma_level))
            
        except ValueError as e:
            allsky_shared.log(0, f"ERROR: Invalid parameters - {e}")
            return "Invalid parameters"

        # Step 0: Apply Noise Reduction (First step)
        if enable_denoise:
            if denoise_level > 0:
                try:
                    # Bilateral Filter: Preserves edges (stars) while smoothing flat areas (noise)
                    # d: Diameter of each pixel neighborhood (keep small for speed)
                    # sigma: Filter strength. Higher = more blurring of noise.
                    d = 5 
                    sigma = denoise_level * 15 
                    allsky_shared.image = cv2.bilateralFilter(allsky_shared.image, d, sigma, sigma)
                    result.append(f"Denoise {denoise_level}")
                except Exception as e:
                    allsky_shared.log(0, f"ERROR: Denoise failed: {e}")

        # Step 1: Apply Saturation
        if enable_saturation:
            sat_multiplier = 1.0 + (sat_level / 10.0)
            if sat_multiplier != 1.0:
                if len(allsky_shared.image.shape) == 3 and allsky_shared.image.shape[2] == 3:
                    try:
                        hsv = cv2.cvtColor(allsky_shared.image, cv2.COLOR_BGR2HSV).astype(np.float32)
                        h_ch, s_ch, v_ch = cv2.split(hsv)
                        s_ch = np.clip(s_ch * sat_multiplier, 0, 255)
                        hsv = cv2.merge([h_ch, s_ch, v_ch]).astype(np.uint8)
                        allsky_shared.image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                        result.append(f"Sat x{sat_multiplier:.2f}")
                    except Exception as e:
                        allsky_shared.log(0, f"ERROR: Saturation adjustment failed: {e}")

        # Step 2: Apply Gamma Correction
        if enable_gamma:
            if gamma_level != 1.0:
                try:
                    invGamma = 1.0 / gamma_level
                    table = np.array([((i / 255.0) ** invGamma) * 255
                        for i in np.arange(0, 256)]).astype("uint8")
                    allsky_shared.image = cv2.LUT(allsky_shared.image, table)
                    result.append(f"Gamma {gamma_level:.1f}")
                except Exception as e:
                    allsky_shared.log(0, f"ERROR: Gamma correction failed: {e}")

        # Step 3: Apply Contrast
        if enable_contrast:
            if contrast_level != 1.0:
                try:
                    beta = 0
                    if auto_anchor:
                        mean_brightness = np.mean(allsky_shared.image)
                        beta = mean_brightness * (1.0 - contrast_level)
                    
                    allsky_shared.image = cv2.convertScaleAbs(allsky_shared.image, alpha=contrast_level, beta=beta)
                    result.append(f"Cont x{contrast_level:.2f}")
                except Exception as e:
                    allsky_shared.log(0, f"ERROR: Contrast adjustment failed: {e}")

        # Step 4: Apply Sharpening (Last step)
        if enable_sharpness:
            if sharpness_level > 0:
                try:
                    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                    sharpened = cv2.filter2D(allsky_shared.image, -1, kernel)
                    alpha = sharpness_level * 0.2
                    allsky_shared.image = cv2.addWeighted(sharpened, alpha, allsky_shared.image, 1 - alpha, 0)
                    result.append(f"Sharp {sharpness_level}")
                except Exception as e:
                    allsky_shared.log(0, f"ERROR: Sharpening failed: {e}")

        # Build result message
        if not result:
            msg = "No adjustments made"
        else:
            msg = ", ".join(result)

        allsky_shared.log(4, f"INFO: {msg}")
        return msg

def imagetuning(params, event):
    allsky_imagetuning = IMAGETUNING(params, event)
    result = allsky_imagetuning.run()

    return result

def imagetuning_cleanup():
    moduleData = {
        "metaData": IMAGETUNING.meta_data,
        "cleanup": {
            "files": {
            },
            "env": {}
        }
    }
    allsky_shared.cleanupModule(moduleData)
