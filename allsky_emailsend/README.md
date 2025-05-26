# AllSky Email Send Module

|||
| ------------ | ------------   |
| **Status**   | Experimental   |
| **Level**    | Beginner       |
| **Runs In**  | Night to Day Transition<br>Periodic (only for testing)   |
|||

This module allows for automatically emailing nightly startrails, keogram, and timelapse images from a Gmail (or SMTP) account each morning. 
Timelapse can be sent in a separate email from the other images if required or desired (eg. due to file size).

**Prerequisites:**

A Google Account with MFA enabled and an app password.  OR an SMTP email server/service

For Gmail, see [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup an App Password.
_An app password is a 16-digit passcode used to give the script permission to access your Google Account in order to send email._

|**Daily Notification Setup**       | Description  |Notes|
| ------------                      | ------------ |------------ |
| To:                               | The address(es) to receive the email notification.  |Required|
| Subject:                          | Configurable text for the email subject line |Optional|
| Append date to Subject line       | Select to append Date Stamp to subject line text |Optional|
| Email Message Text:               | Configurable text for the message body.<br>The filenames of any attached files will be appended to this text.|Optional|
||||
| Attach Star Trails                | No / Yes |Optional|
| Attach Keogram                    | No / Yes |Optional|
| Attach Timelapse                  | No / Yes / Yes - in separate email |Optional|
||||
| **Sender SMTP Setup**|||
| Sender email address              | Sending account Gmail address      | Required |
| Password / Google App Password    | From google security settings |Required|
| SMTP server address               | Preset for Gmail|Required|
| SMTP server port                  | Preset for Gmail|Required|
||||
----------------------

**Notes:**

Gmail has a maximum attachment limit of 25MB.  Please ensure your files will be less that that limit.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.

This module can take a minute or two to complete depending on your Pi's internet connection and the size of the files to be attached.  Therefore it may make sense for this to be the last madule to run in your 'selected modules'


**Special Thanks**

Thanks to Alex Greenland, I took a look at your disordsend module to get myself started with this one!
