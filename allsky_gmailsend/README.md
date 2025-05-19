# AllSky Gmail Send Module

|   |   |
| ------------ | ------------ |
| **Status**   | Experimental |
| **Level**    | Intermediate |
| **Runs In**  | endofnight   |


This module allows for automatically emailing nightly Stratrails and keogram images from a Gmail account. 

**Prerequisites:**
A Google Account and a Google App Password. 

Please see [LINK TEXT](https://www.google.com) for details on how to setup an App Password.


|**Notification Settings**    | Description  |Notes|
| ------------                | ------------ |------------ |
| Recipient Email Address     | The person to receive the email.  |Required|
| Email Subject Line          | Text of the email subject line |Optional|
| Append date to Subject line | Select to append Date Stamp to subject line text |Optional|
| Email Message Text          | Any text you want in the message body.  The filenames of any attached files will be appended to this text.|Optional|
|Files to Attach              | Checkboxes to select for: Startrails, Keogram, Timelapse|Optional|
||||
| Star Trails                 | Select to send Star Trail images to the discord server |Optional|
| Keogram                     | Select to send Keogram image|Optional|
| Timelapse                   | Select to send timelapse video |Optional|
||||
| **Sender Account Config**   |||
| Sender email address        |     | Required |
||||
|SMTP Server|you should not need to change this|Preset|
|SMTP Port|you should not need to change this|Preset|
----------------------

**Notes:**
Gmail has a maximum attachment limit of 25MB.  Please ensure your files will be less that that limit.
You may have to modify timelapse creation options if that file is too large and you wish to send it via email.
