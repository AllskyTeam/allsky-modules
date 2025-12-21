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

import allsky_shared as s
import cv2
import numpy as np

metaData = {
    "name": "Image Tuning",
    "description": "Advanced control: Saturation, Contrast, Gamma, Sharpening, and Denoise",
    "module": "allsky_imagetuning",
    "version": "v2.1.0",
    "events": [
        "night",
        "day"
    ],
    "experimental": "false",
    "arguments":{
        "level": "0",
        "contrast": "1.0",
        "gamma": "1.0",
        "sharpness": "0",
        "denoise": "0",
        "auto_anchor": "false"
    },
    "argumentdetails": {
        "level" : {
            "required": "false",
            "description": "Saturation",
            "help": "0 is neutral. -10 is B&W. 10 is max color.",
            "type": {
                "fieldtype": "spinner",
                "min": -10,
                "max": 10,
                "step": 0.1
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
            }
        },
        "auto_anchor" : {
            "required": "false",
            "description": "Smart Contrast",
            "help": "Automatically adjusts brightness when changing Contrast.",
            "type": {
                "fieldtype": "checkbox"
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
        ]
    }
}

def imagetuning(params, event):
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
    if not hasattr(s, 'image') or s.image is None:
        s.log(0, "ERROR: No image found")
        return "No image found"

    try:
        # Parse arguments safely
        sat_level = float(params.get("level", 0))
        contrast_level = float(params.get("contrast", 1.0))
        gamma_level = float(params.get("gamma", 1.0))
        sharpness_level = int(params.get("sharpness", 0))
        denoise_level = int(params.get("denoise", 0))
        
        # Handle checkbox parameter
        anchor_param = params.get("auto_anchor", "false")
        if isinstance(anchor_param, bool):
            auto_anchor = anchor_param
        else:
            auto_anchor = str(anchor_param).lower() == "true"

        # Enforce limits
        sat_level = max(-10.0, min(10.0, sat_level))
        contrast_level = max(0.0, min(5.0, contrast_level))
        gamma_level = max(0.1, min(5.0, gamma_level))
        
    except ValueError as e:
        s.log(0, f"ERROR: Invalid parameters - {e}")
        return "Invalid parameters"

    # Step 0: Apply Noise Reduction (First step)
    if denoise_level > 0:
        try:
            # Bilateral Filter: Preserves edges (stars) while smoothing flat areas (noise)
            # d: Diameter of each pixel neighborhood (keep small for speed)
            # sigma: Filter strength. Higher = more blurring of noise.
            d = 5 
            sigma = denoise_level * 15 
            s.image = cv2.bilateralFilter(s.image, d, sigma, sigma)
            result.append(f"Denoise {denoise_level}")
        except Exception as e:
            s.log(0, f"ERROR: Denoise failed: {e}")

    # Step 1: Apply Saturation
    sat_multiplier = 1.0 + (sat_level / 10.0)
    if sat_multiplier != 1.0:
        if len(s.image.shape) == 3 and s.image.shape[2] == 3:
            try:
                hsv = cv2.cvtColor(s.image, cv2.COLOR_BGR2HSV).astype(np.float32)
                h_ch, s_ch, v_ch = cv2.split(hsv)
                s_ch = np.clip(s_ch * sat_multiplier, 0, 255)
                hsv = cv2.merge([h_ch, s_ch, v_ch]).astype(np.uint8)
                s.image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                result.append(f"Sat x{sat_multiplier:.1f}")
            except Exception as e:
                s.log(0, f"ERROR: Saturation adjustment failed: {e}")

    # Step 2: Apply Gamma Correction
    if gamma_level != 1.0:
        try:
            invGamma = 1.0 / gamma_level
            table = np.array([((i / 255.0) ** invGamma) * 255
                for i in np.arange(0, 256)]).astype("uint8")
            s.image = cv2.LUT(s.image, table)
            result.append(f"Gamma {gamma_level:.1f}")
        except Exception as e:
            s.log(0, f"ERROR: Gamma correction failed: {e}")

    # Step 3: Apply Contrast
    if contrast_level != 1.0:
        try:
            beta = 0
            if auto_anchor:
                mean_brightness = np.mean(s.image)
                beta = mean_brightness * (1.0 - contrast_level)
            
            s.image = cv2.convertScaleAbs(s.image, alpha=contrast_level, beta=beta)
            result.append(f"Cont x{contrast_level:.1f}")
        except Exception as e:
            s.log(0, f"ERROR: Contrast adjustment failed: {e}")

    # Step 4: Apply Sharpening (Last step)
    if sharpness_level > 0:
        try:
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(s.image, -1, kernel)
            alpha = sharpness_level * 0.2
            s.image = cv2.addWeighted(sharpened, alpha, s.image, 1 - alpha, 0)
            result.append(f"Sharp {sharpness_level}")
        except Exception as e:
            s.log(0, f"ERROR: Sharpening failed: {e}")

    # Build result message
    if not result:
        msg = "No adjustments made"
    else:
        msg = ", ".join(result)

    s.log(4, f"INFO: {msg}")
    return msg

def imagetuning_cleanup():
    '''
    Cleanup function called when module is removed or disabled.
    Currently no cleanup needed for this module.
    '''
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {},
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
