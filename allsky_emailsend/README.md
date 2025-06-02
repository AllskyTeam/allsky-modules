# AllSky Email Send Module

|||
| ------------ | ------------   |
| **Status**   | Experimental   |
| **Level**    | Beginner       |
| **Runs In**  | Night to Day Transition<br>Periodic (only for testing)   |


This module allows for automatically emailing nightly startrails, keogram, and timelapse images from a Gmail (or SMTP) account each morning.  Additionally it can create and send a composite startrails+keogram image which is a compressed keogram displayed below the startrails.  The timelapse can be sent in a separate email from the other images if required or desired (eg. due to file size).

**Prerequisites:**
 - For Gmail: An account with MFA enabled and an app password. See [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup an App Password.  _eg a 16-digit passcode used to give the script permission to access your Google Account to send email._
 - Or annother SMTP email server/service

### Settings:
| Daily Notification Setup          |||
| ------------                      | ------------ |------------ |
| To or BCC?                        |Select how emails wil be delivered<br>TO or BCC|Required|
| Recipients                        | The address(es) to receive the email notifications.  |Required|
| Subject                           | Text for email subject line |Optional|
| Append date to Subject            | Select to append Date Stamp to subject line text |Optional|
| Email Message Text                | Enterable plain text for the message body.<br>Filenames of any attached files will be listed below this text.|Optional|
| Attach Images                     | Startrails / Keogram / Startrails and Keogram<br>Startrails Keogram Composite / None |Optional|
| Attach Timelapse                  | No / Yes / Yes - in separate email |Optional|
||||
| **Composite Image Setup**|||
| Padding                           | How much space to add between Startrails and Keogram <br> Default: 50 (0 - 1000)   | Required |
| Keogram Height                    | Keogram is resized to [this height] x [Startrails width] <br> Default: 400 (20 - 2000) |Required  |
| **Sender SMTP Setup**|||
| Sender email address              | Sender account email address      | Required |
| Password / <br>Google App Password| 16-digit passcode from Google security settings<br>(or SMTP Password for other services)|Required|
| SMTP server address               | Server address<br> Default: smtp.gmail.com|Required|
| SMTP server port                  | Server port<br> Default: 587|Required|
| Max attachments size              | Maximum allowed size of all attachments to an email in MB.<br> Default: 25|Required|

----------------------

### Notes:

 - Gmail has a maximum attachment limit of 25MB.  If your files exceed the maximum allowed attachment size limit, then not all files will be attached.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.

 - This module can take a minute or more to complete depending on your Pi, internet connection, size of the files to be attached, etc.  Therefore it may make sense for this to be the last madule to run in your 'selected modules'

 - _Special Thanks to the prior work by Alex Greenland_, I referenced your disordsend module to get myself started with this one!
