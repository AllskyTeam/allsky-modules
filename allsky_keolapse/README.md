# AllSky Keolapse Module Setup Guide
**PERIODIC module mode highly suggested**

## Introduction

The Keolapse module creates timelapse videos with a circular keogram overlay surrounding your allsky camera image. This guide will help you set up and optimize the module for your specific camera installation.

## Installation

The module is included in the AllSky Modules distribution. Enable it through the AllSky Module Manager:

1. Navigate to **Module Manager**
2. Find "Keolapse Generator" in the list
   * In 'Night to Day Transition' or 'Periodic'.
3. Click **Enable**
4. Configure the module parameters (detailed below)
5. Click **Save**

## Basic Configuration

### Video Settings

| Setting | Description | Recommended |
|---------|-------------|-------------|
| Use Timelapse Settings | Uses AllSky's main timelapse settings | Disabled initially |
| Video Quality | Output quality/compression | Medium |
| Framerate | Frames per second | 12-15 |
| Max Length | Maximum video length in seconds | 120 |
| Resolution | Target output resolution | 720p initially |

### Image Settings

| Setting | Description | Recommended |
|---------|-------------|-------------|
| Top/Bottom Padding | Pixels above/below the sky image | 5 initially |
| Left/Right Padding | Pixels to sides of sky image | 5 initially |
| Keogram Height | Height of the keogram ring | 175 initially |
| Circle Padding | Space between image and keogram | 5 initially |
| Edge Padding | Spacing from image edges | 5 |
| Start Position | Keogram start position | 12 (top) |

## Alignment Configuration

The most critical aspect is positioning the keogram ring correctly around your sky image. These settings control the positioning:

| Setting | Description | Default |
|---------|-------------|---------|
| Circle Radius Factor | Size of circle relative to image width | 0.47 |
| Center X Offset | Horizontal center adjustment in pixels | 0 |
| Center Y Offset | Vertical center adjustment in pixels | 0 |

## Using Test Mode

Test mode lets you quickly experiment with settings without processing full nights of data:

1. Enable **Test Mode** in the Testing tab
2. If you haven't generated test data yet, also enable **Generate Test Data**
3. Run the module once with periodic event to create test data
4. Disable **Generate Test Data** after creation (important!)
5. Keep **Test Mode** enabled while experimenting
**Tip: To run the testing faster, disable the module, save in the manager, then re-enable & save.**

### Alignment Testing Process

1. Enable **Show Circles Only** in the Testing tab
2. Run the module with periodic event
3. Examine the debug image in your images/test/keolapse folder
4. Adjust Circle Radius Factor and X/Y Offsets as needed
5. Repeat until the circles align properly with your sky image

## Debugging Guide

### Understanding the Debug Circles

The debug mode displays three colored circles:
- **Blue (inner)**: The boundary where the keogram inner edge will be placed - directly controlled by the Circle Radius Factor
- **Yellow (outer)**: Where the keogram outer edge will be (Blue circle + Keogram Height)
- **Pink cross**: The center point of the circles - controlled by X/Y Offset values

### Adjustment Tips

1. **If your all-sky camera image isn't centered**:
   - Adjust Center X/Y Offset values to move circles
   - Positive X values move right, negative left
   - Positive Y values move down, negative up

2. **If the circles are too large or small**:
   - Decrease Circle Radius Factor to make circles smaller
   - Increase Circle Radius Factor to make circles larger

3. **If your image has a mask or isn't fully circular**:
   - Adjust the radius factor to fit just inside the visible sky portion
   - Use Circle Padding to add space between sky and keogram

## Example Workflow

1. Enable Test Mode and Generate Test Data
2. Run module once to create test data
3. Disable Generate Test Data
4. Enable Show Circles Only
5. Run module again to create debug image
6. Check alignment and adjust settings as needed
7. When alignment looks good, disable Show Circles Only
8. Run module again to create a test video with keogram
9. Fine-tune settings as needed
10. Disable Test Mode when satisfied
11. The module will now run automatically on nightday transitions

## Troubleshooting

- **No output file created**: Check the logs at `/home/pi/allsky/tmp/logs/keolapse_debug.log`
- **Missing keogram**: Ensure the Keogram is enabled in the AllSky Settings page
- **Poor alignment**: Use Show Circles Only mode to refine positioning
- **Video quality issues**: Try a higher quality setting or adjust resolution

## Advanced Usage

- Use Process Date to create videos for previous dates
- Adjust Top/Bottom Padding for better visual balance
- Experiment with different Start Position values for keogram orientation

Remember that creating videos is processor-intensive. If your Raspberry Pi seems sluggish during video creation, consider optimizing your settings or scheduling the module to run at less busy times.
