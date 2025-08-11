# AllSky Email Send Module

|||
| ------------ | ------------   |
| **Status**   | Stable         |
| **Level**    | Beginner       |
| **Runs In**  | Night to Day Transition<br>Periodic (Enable only for testing!)   |


This module allows for automatically emailing nightly startrails, keogram, and timelapse images from a Gmail (or SMTP) account each morning.  Additionally it can create and send a composite startrails+keogram image which is a compressed keogram displayed below the startrails.  The timelapse can be sent in a separate email from the other images if required or desired (eg. due to file size).

**Prerequisites:**
 - Gmail or annother SMTP email server/service
 - Allsky must be configured to generate Startrails, Keogram, and/or Timeplapse and to store at least one day of images on the Pi.

### Settings:

| Daily Notification Setup          |               |Default|
| -------------                     | ------------- |------------- |
| To or BCC                         | Select how emails will be addressed    |To|
| Recipients                        | The address(es) to receive the email notifications.  ||
| Subject                           | Text for email subject line ||
| Append date to Subject            | Select to append Date Stamp to subject line text |Yes|
| Email Message Text                | Enterable plain text for the message body.<br>Filenames of any attached files will be listed below this text.||
| Attach Images                     | Startrails / Keogram / Startrails and Keogram<br>Startrails Keogram Composite / None |Startrails Only|
| Padding                           | How much space to add between Startrails and Keogram     | 50 |
| Keogram Height                    | Keogram is resized to [This height] x [Startrails width] | 400 |
| Attach Timelapse                  | No / Yes / Yes - in separate email |No|
||||
| **Sender SMTP Setup**|||
| Sender email address              | Sender account email address      |  |
| Account Password                  | SMTP Account password or 16-digit passcode from Google security settings||
| SMTP server address               | Server address |smtp.gmail.com|
| SMTP server port                  | Server port|587|
| Max attachments size              | Maximum allowed size of all attachments to an email in MB.|25|
||||
 **Test**           |||
 |The "test button" supports triggering an email, _but will not attach images_.  Use to verify server/credentials/recipient/email body text, etc.||
<hr>

### Notes:
 - For Gmail with MFA enabled you need an app password (not your regular login password). See [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup.  _eg a 16-digit passcode used to give the script permission to access your Google Account to send email._

 - Gmail has a maximum attachment limit of 25MB.  If your files exceed the maximum allowed attachment size limit, then not all files will be attached.  You may have to modify timelapse creation options if that file is too large and you wish to send it via email.

 - This module can take a minute or more to complete depending on your Pi, internet connection, size of the files to be attached, etc.  Therefore it may make sense for this to be the last madule to run in your 'selected modules'

 - _Special thanks to prior work by Alex Greenland_, I referenced your disordsend module to get myself started with this one!

<hr>

### Screenshots of module setup:
|Configuration Tab        |Example|
| ------------            | ------------   |
|Sender SMTP Settings     |![image](https://github.com/user-attachments/assets/81adc966-de5a-4a3f-a454-b5d8d94477d4)|
|Daily Notification Setup |![image](https://github.com/user-attachments/assets/6d68e309-5533-496a-9e95-e42141764a15)|
|Composite Image Setup    |![image](https://github.com/user-attachments/assets/f1f4a0cf-df06-4ee7-9237-0a4904e60ca7)|



