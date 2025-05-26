# AllSky Email Send Module

|||
| ------------ | ------------   |
| **Status**   | Experimental   |
| **Level**    | Beginner       |
| **Runs In**  | Night to Day Transition<br>Periodic (only for testing)   |


This module allows for automatically emailing nightly startrails, keogram, and timelapse images from a Gmail (or SMTP) account each morning. 
Timelapse can be sent in a separate email from the other images if required or desired (eg. due to file size).

**Prerequisites:**
 - A Google Account with MFA enabled and an app password.  OR an SMTP email server/service

 - For Gmail, see [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup an App Password.  _eg a 16-digit passcode used to give the script permission to access your Google Account to send email._

### Settings:
| Daily Notification Setup       |||
| ------------                      | ------------ |------------ |
| To:                               | The address(es) to receive the email notification.  |Required|
| Subject:                          | Configurable text for the email subject line |Optional|
| Append date to Subject line       | Select to append Date Stamp to subject line text |Optional|
| Email Message Text:               | Configurable text for the message body.<br>The filenames of any attached files will be appended to this text.|Optional|
| Attach Star Trails                | No / Yes |Optional|
| Attach Keogram                    | No / Yes |Optional|
| Attach Timelapse                  | No / Yes / Yes - in separate email |Optional|
||||
| **Sender SMTP Setup**|||
| Sender email address              | Sending account email address      | Required |
| Password / <br>Google App Password    |16-digit passcode from Google security settings<br> (or SMTP Password for other services)|Required|
| SMTP server address               | Preset for Gmail|Required|
| SMTP server port                  | Preset for Gmail|Required|

----------------------

### Notes:

 - Gmail has a maximum attachment limit of 25MB.  If your files exceed that limit then not all files will be attached.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.

 - This module can take a minute or two to complete depending on your Pi's internet connection and the size of the files to be attached.  Therefore it may make sense for this to be the last madule to run in your 'selected modules'


 - _Special Thanks to the prior work by Alex Greenland_, I referenced your disordsend module to get myself started with this one!
