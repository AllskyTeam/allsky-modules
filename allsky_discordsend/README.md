# Post Image to Discord Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Daytime Capture, Nighttime Capture, Night to Day Transition  |


This module allows images to be sent to a Discord server using webhooks. Please see [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks "Discord Webhooks") for details on how to create webhooks.

|  Setting | Description  |
| ------------ | ------------ |
| Post Daytime Images | Enable to send any daytime captured images to the Discord server. NOTE: The 'Day Time URL' must also be set.  |
| Daytime Count | Select the frequency with which daytime images are sent to the Discord server. |
| Daytime | The webhook URL for the daytime images. |
|||
| Post Nighttime Images | Enable to send any nighttime captured images to the Discord server. NOTE: The 'Nighttime URL' must also be set.  |
| Nightime Count | Select the frequency with which nighttime images are sent to the Discord server. |
| Nighttime | The webhook URL for the nighttime images. |
|||
| Post Startrails Images | Select to send Startrails images to the Discord server. |
| Startrails | The webhook URL for the Startrails image. |
|||
| Post Keogram Images | Select to send Keogram images to the Discord server. |
| Keogram | The webhook URL for the Keogram image.
|||
| Post Timelapse Videos | Select to send timelapse videos to the Discord server. |
| Timelapse | The webhook URL for the Timelapse video. |


**NOTE:** There are limits when sending data to a Discord server. Please see [Discord Rate Limits](https://discord.com/developers/docs/topics/rate-limits "Discord Rate Limits") for detailed info.
- Do not send images too frequently.
- The maximum file size is 8Mb so you will have to modify the timelapse creation options to ensure the file is under the 8Mb limit.
