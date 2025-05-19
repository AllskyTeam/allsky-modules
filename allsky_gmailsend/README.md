# AllSky Gmail Send Module

|   |   |
| ------------ | ------------ |
| **Status**   | Experimental |
| **Level**    | Intermediate |
| **Runs In**  | endofnight <br>end of day   |
|||
This module allows for automatically emailing nightly Stratrails and keogram images from a Gmail account. 

**Prerequisites:**
A Google Account with MFA enabled and an app password.

The app password is a 16-digit passcode that gives the script permission to access your Google Account in order to send email.  DO NOT SHARE your App Password.

(App passwords can only be used with accounts that have 2-Step Verification turned on.)

Please see [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup an App Password.


|**Email Notification Settings**| Description  |Notes|
| ------------                | ------------ |------------ |
| Recipient Email Address     | The address to receive the email  |Required|
| Email Subject Line          | Text of the email subject line |Optional|
| Append date to Subject line | Select to append Date Stamp to subject line text |Optional|
| Email Message Text          | Any text you want in the message body.  The filenames of any attached files will be appended to this text.|Optional|
||||
| Star Trails                 | Select to send daily Startrail image|Optional|
| Keogram                     | Select to send daily Keogram image|Optional|
| Timelapse                   | Select to send daily Timelapse video |Optional|
||||
| **Gmail Account Setup**   |||
| Sender email address        | Sending account Gmail address      | Required |
| Google App Password         | From google security settings |Required|
| SMTP Server                 | You should not need to change this|Preset|
| SMTP Port                   | You should not need to change this|Preset|
||||
----------------------

**Notes:**
Gmail has a maximum attachment limit of 25MB.  Please ensure your files will be less that that limit.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.
