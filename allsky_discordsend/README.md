# AllSky Discord Module

|   |   |
| ------------ | ------------ |
| **Status**  | Experimental  |
| **Level**  | Experienced  |
| **Runs In**  | Day time, Night time, endofnight  |


This module allows images to be sent to a discord server using webhooks. Please see [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks "Discord Webhooks") for details on how to create webhooks

|  Setting | Description  |
| ------------ | ------------ |
| Post Day time Images | Enable to send any daytime captured images to the Discord server. NOTE: The 'Day Time URL' must also be set  |
| Daytime Count | Select the frequency with which daytime images are sent to the Discord server |
| Day Time | The webhook URL for the daytime images |
|||
| Post Night time Images | Enable to send any night time captured images to the Discord server. NOTE: The 'Night Time URL' must also be set  |
| Nightime Count | Select the frequency with which night time images are sent to the Discord server |
| Night Time | The webhook URL for the night time images |
|||
| Post Star Trails Images | Select to send Star Trail images to the discord server |
| Star Trails | The webhook URL for the star trail images |
|||
| Post Keograms Images | Select to send Keogram images to the discord server |
| Keograms | The webhook URL for the Keogram images
|||
| Post Timelapse videos | Select to send timelapse videos to the discord server |
| Timelapse | The webhook for the timelapse video |


**NOTE:** There are limits when sending data to a Discord server. Please see [Discord Rate Limits](https://discord.com/developers/docs/topics/rate-limits "Discord Rate Limits") for detailed info
- Do not send images too frequently.
- The maximum file size is 8Mb so you will have to modify the timelapse creation options to ensure the file is under the 8Mb limit
