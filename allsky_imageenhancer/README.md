# Allsky Image Enhancer Module

Image enhancement module for AllSky providing control over image quality parameters.

## Description

The Image Enhancer module provides five tools to improve your AllSky images:

1. **Saturation Control** - Adjust color intensity from black & white to vibrant colors
2. **Contrast Enhancement** - Increase separation between light and dark areas
3. **Gamma Correction** - Brighten dark areas (lift shadows) without blowing out highlights
4. **Sharpening** - Enhance edge details to make stars and features more defined
5. **Noise Reduction** - Remove grain and noise while preserving important details like stars

## Features

- **Smart Processing Order** - Applies enhancements in the correct sequence for best results
- **Edge-Preserving Denoising** - Uses bilateral filtering to smooth noise while keeping stars sharp
- **Smart Contrast** - auto-anchoring maintains overall brightness when adjusting contrast

## Parameters

### Saturation (level)
- **Range:** -10 to 10
- **Default:** 0 (neutral)
- **Description:** Controls color intensity
  - **-10:** Black & White
  - **0:** Original colors
  - **10:** Maximum color saturation
- **Use Case:** Enhance nebulae, auroras, or reduce color noise in low-light images

### Contrast (contrast)
- **Range:** 0 to 5
- **Default:** 1.0 (neutral)
- **Description:** Controls separation between light and dark areas
  - **1.0:** Original contrast
  - **> 1.0:** Increases contrast
  - **< 1.0:** Decreases contrast
- **Use Case:** Make stars stand out more against the sky background

### Gamma (gamma)
- **Range:** 0.1 to 5.0
- **Default:** 1.0 (neutral)
- **Description:** Brightness control that preserves highlights
  - **1.0:** Original brightness
  - **> 1.0:** Brightens dark areas (lifts shadows)
  - **< 1.0:** Darkens the image
- **Use Case:** Reveal faint stars and detail in dark night skies

### Sharpness (sharpness)
- **Range:** 0 to 5
- **Default:** 0 (off)
- **Description:** Edge enhancement strength
  - **0:** No sharpening
  - **1:** Mild sharpening
  - **5:** Very strong sharpening
- **Use Case:** Make stars appear more defined and crisp
- **Note:** Apply sparingly to avoid introducing artifacts

### Noise Reduction (denoise)
- **Range:** 0 to 5
- **Default:** 0 (off)
- **Description:** Removes grain and noise
  - **0:** No denoising
  - **1-2:** Light denoising (preserves faint stars)
  - **3-5:** Strong denoising (may blur faint stars)
- **Use Case:** Clean up noisy images from high ISO settings
- **Note:** Uses bilateral filtering to preserve edges

### Smart Contrast (auto_anchor)
- **Type:** Checkbox
- **Default:** Off (false)
- **Description:** Automatically adjusts brightness when changing contrast
- **Effect:** Maintains overall image brightness when contrast is increased/decreased
- **Use Case:** Enable when you want to adjust contrast without making the image too bright or dark

## Processing Order

The module applies enhancements in this specific order for optimal results:

1. **Noise Reduction** - Clean the image first
2. **Saturation** - Adjust color intensity
3. **Gamma** - Correct brightness
4. **Contrast** - Enhance separation
5. **Sharpening** - Final detail enhancement

## Usage Examples

### Example 1: Night Sky Enhancement
For typical night sky images with stars:
- Saturation: 2
- Contrast: 1.2
- Gamma: 1.3
- Sharpness: 1
- Denoise: 1
- Smart Contrast: On

### Example 2: Aurora/Nebula Enhancement
For colorful phenomena:
- Saturation: 5
- Contrast: 1.3
- Gamma: 1.1
- Sharpness: 2
- Denoise: 0
- Smart Contrast: On

### Example 3: Noise Reduction for High ISO
For very noisy images:
- Saturation: 0
- Contrast: 1.1
- Gamma: 1.0
- Sharpness: 0
- Denoise: 3
- Smart Contrast: Off

### Example 4: Daytime Enhancement
For daytime cloud images:
- Saturation: 1
- Contrast: 1.15
- Gamma: 1.0
- Sharpness: 2
- Denoise: 0
- Smart Contrast: On

## Installation

This module requires OpenCV and NumPy. Dependencies are automatically installed via the `requirements.txt` file when using the AllSky module installer.

## Tips and Best Practices

1. **Start Small** - Begin with subtle adjustments and increase gradually
2. **Denoise First** - If using noise reduction, the module applies it first automatically
3. **Watch for Artifacts** - Too much sharpening can introduce halos around bright objects
4. **Balance Adjustments** - Heavy denoising may require less sharpening
5. **Use Smart Contrast** - Enable auto_anchor when adjusting contrast to maintain brightness
6. **Test Different Times** - Settings that work at night may not work during the day

## Events

This module runs during:
- **night** - Nighttime image processing
- **day** - Daytime image processing

## Version History

### v2.1.0
- Added Noise Reduction (Bilateral Filter) for edge-preserving denoising
- Improved parameter validation and error handling
- Enhanced documentation

## Author

GitHub: [chvvkumar](https://github.com/chvvkumar)
