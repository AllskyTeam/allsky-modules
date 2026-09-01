# AllSky Startrails Mask Module

|||
| ------------  | ------------   |
| **Status**    | Stable         |
| **Level**     | Beginner       |
| **Runs In**   | Night to Day Transition |
| **Testable**  | Yes |

This module will clean up the nightly startrails output by applying a selectable mask to the image and optionally adding the imaging date onto the final image. It can also upload the modified result after processing.

The module includes test and debug functions including a "Quick Setup Test" option which will create a sample result file so you can validate mask and text placement quickly without actually changing an existing startrails file.

**Prerequisites:**
 - Allsky must be configured to generate Startrails images.
 - Keep at least one day of images on the Pi so prior-night processing can run.
 - Optional: create or select a mask image if you want to hide image areas (for example blurred overlay text or anything else).

### Module Settings:

| Settings                          |               |Default|
| -------------                     | ------------- |------------- |
| Mask final image                  | Select a mask image file to apply to the final startrails image (leave blank for none). | |
| Display imaging date              | Enable date text overlay on the output image. |Yes|
| Display Format                    | Date format string for the overlay text. (no time component, only date).|%Y-%m-%d|
| X Position                        | Horizontal position for the left edge of the date text. |20|
| Y Position                        | Vertical position for the baseline of the date text. |120|
| Font Style                        | Select date text font style. |Duplex|
| Color (HEX)                       | Date text color in HEX (example: #ff0000). |#ff0000|
| Size                              | Date text font size. |3|
| Weight                            | Date text line thickness. |2.5|
| Upload modified image             | Enable to upload the processed startrails image to local/remote destinations. |Yes|
||||
| **Testing - Debug** |||
| Folder to process                 | Optional date folder to process (example: 20250801). Blank uses prior night. | |
| Test Action                | Process Startrails / Process and Upload / Upload Only / Quick Setup Test | |
| | | |



### Notes:
 - If "Upload modified image" is enabled, you can disable the main Allsky Startrails upload option to avoid duplicate uploads.
 - "Quick Setup Test" creates a sample result in images/test/startrails/startrails-test.jpg so you can validate mask and text placement quickly without actually changing an existing startrails file.  (the test folder will be deleted at the end of night if the module is enabled and running)
 - Running other options will overwrite destination files for that date if they exist.

 Much of this module was written by a human, but AI assistance was used while preparing this contribution. The generated code and documentation were reviewed and tested before submission.