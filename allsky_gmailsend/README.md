# AllSky Gmail Send Module

|||
| ------------ | ------------ |
| **Status**   | Experimental |
| **Level**    | Intermediate |
| **Runs In**  | endofnight <br>end of day   |
|||

This module allows for automatically emailing nightly startrails, keogram, and timelapse images from a Gmail account each morning. 
Timelapse can be sent in a separate email from the other images if required or desired (eg. due to file size).

**Prerequisites:**
A Google Account with MFA enabled and an app password.

The app password is a 16-digit passcode that gives the script permission to access your Google Account in order to send email.
Please see [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup an App Password.


|**Daily Notification Setup**   | Description  |Notes|
| ------------                  | ------------ |------------ |
| Recipient Email Address       | The address(es) to receive the email notification.  |Required|
| Email Subject Line            | Configurable text for the email subject line |Optional|
| Append date to Subject line   | Select to append Date Stamp to subject line text |Optional|
| Email Message Text            | Configurable text for the message body.  The filenames of any attached files will be appended to this text.|Optional|
||||
| Attach Star Trails            | No / Yes |Optional|
| Attach Keogram                | No / Yes |Optional|
| Attach Timelapse              | No / Yes / Yes - in separate email |Optional|
||||
| **Gmail Sender Account Setup**|||
| Sender email address          | Sending account Gmail address      | Required |
| Sender Google App Password    | From google security settings |Required|
| SMTP Server                   | You should not need to change this|Preset|
| SMTP Port                     | You should not need to change this|Preset|
||||
----------------------

**Notes:**
Gmail has a maximum attachment limit of 25MB.  Please ensure your files will be less that that limit.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.

This should be the last module in your 'selected modules' as it can take a minute or two to complete depending on the strength of your Pi's connection and the size of the files to be attached.
