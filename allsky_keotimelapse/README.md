# AllSky Keolapse Timelapse Module

|||
| ------------  | ------------   |
| **Status**    | Stable         |
| **Level**     | Intermediate   |
| **Runs In**   | Night to Day Transition |
| **Testable**  | Yes |

This module creates a daily timelapse with an animated keogram ring (keolapse) that tracks like a clock in sync with the video. 
The output can be created as the main Allsky timelapse (viewed in images and allsky website) or as a separate video file.
There are several settings that allow for customisation of the keolapse including position, size, and colors.  The module also supports upload, setup testing, and optional overlay variables.

**Comments:**
 - It's okay for the resulting keolapse ring to expand beyond the base image.  The frame size will scale/adjust to fit it.
 - Use the Quick Setup Testing feature to figure out your keolapse settings.  Start with a debug image for size, positioning, and colors.  Then try a debug video.  
 - Once you are happy with the settings you can generate a full timelapse for a day/date.
   - *On a Pi 4B processing 1000 images this can take 10 minutes or more depending on the video parameters you choose.*
  

**Prerequisites:**
 - Allsky must be configured to capture nightly images and generate a keogram.
 - Keep at least one day of images on the Pi for prior-night or generate-for-day processing.

### Settings:

| Video Settings                    |               |Default|
| -------------                     | ------------- |------------- |
| Generate Video                    | Enable daily timelapse generation. |Yes|
| Generate Overlay Variables        | Publish AS_KEOLAPSE_* variables for overlays/other modules. |No|
| Save Video As                     | Allsky Timelapse or Separate Video File. |Allsky Timelapse|
| Upload Video                      | Upload generated video using configured destinations. |Yes|
| Upload Thumbnail                  | Upload video thumbnail with the video upload. |Yes|
| Remote Directory                  | Subfolder used when saving as separate file (for example: keolapses). |keolapses|
| **Video Parameters**|||
| Source                            | Use Module Settings or existing Allsky Settings Page values. |Module Settings|
| Output Resolution                 | 720p / 1080p / 4k / Custom / No Resizing. |720p|
| Custom Height                     | Target video height when using Custom resolution. |720|
| FPS (speed)                       | Frames per second for output video. |30|
| Bitrate (kbps)                    | Output video bitrate. |2000|
| Max Length (seconds)              | Module can increase FPS to keep duration under this limit. |60|
| *Advanced Video Settings*         | *Rarely changed*       ||
| Extra Parameters                  | Optional ffmpeg extra parameters. | |
| Encoder Preset                    | compression/speed preset. Slower settings take more time to encode but yield smaller output files. |medium|
| VCODEC                            | Video codec setting. |libx264|
| Pixel Format                      | Output pixel format. |yuv420p|
||||
| **Keolapse Animation** |||
| Overlay on Timelapse              | Enable animated keogram ring overlay. |Yes|
| Keolapse Positioning Mask         | Select or create a circular mask to place the keolapse animation ring.<br>It's okay for the ring to beyond the edges of the image as the frames will be rescaled to fit.<br>(blank uses auto placement). | |
| Ring Height (px)                  | Height of the keogram ring. |175|
| Image Padding (px)                | Minimum spacing to pad outer image edges if the ring pushes the image frame larger out. |5|
| Start Position                    | Initial clock position: Top/Bottom/Left/Right. |Bottom|
| Progress Indicator Color          | Built-in color names or Custom. |Moon Glow|
| Progress Indicator Custom Hex     | Custom hex color for indicator (when Custom is selected). |#f801ae|
| Border Width (px)                 | Width of inner/outer ring borders. |2|
| Border Color                      | Built-in color names or Custom. |Midnight|
| Border Custom Hex                 | Custom hex color for borders (when Custom is selected). |#99a8c4|
||||
| **Testing - Generate for Day** |||
| Folder to process                 | Optional date folder (example: 20250801). Blank uses prior night. | |
| Timelapse / Keolapse Test Mode    | None / Generate / Generate and Upload / Upload Only / Quick Setup Test |None|
| Quick Setup Output Type           | Debug Image or Debug Video for fast validation test. |Debug Image|
| Test Module                       | Runs selected test mode and can act as generate-for-day processing. | |
||||
| **Debug** |||
| Test Button Verbose Output        | Extra output in test results only (not persisted to allsky log). |No|
| Enable Debug Logging              | Detailed module logging for troubleshooting. |No|
| Keep Video Sequence               | Keeps sequence file used for video generation (debug use). |No|

<hr>

### Notes:
 - If creating the keolapse as your main timelapse video, disable 'Generate' for timelapse in the main Allsky settings to avoid duplicate processing (eg creating a timelapse, then creating it again).
 - When **Save Video As** is set to **Separate Video File**, uploads use the remote subdirectory setting and filename pattern for keolapse output.
 - Quick Setup Test uses temporary test data and writes outputs to an `images/test` folder for fast validation.
 - Test modes that generate/upload can overwrite existing destination files for that date.
 - The module can publish these extra-data variables:  `${KEOLAPSE_VIDEO}`, `${KEOLAPSE_DATE}`, `${KEOLAPSE_FRAMES}`, `${KEOLAPSE_DURATION}`.
