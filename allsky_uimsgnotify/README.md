# AllSky WebUI Messages Notification Module

||| 
| ------------  | ------------   |
| **Level**     | Beginner       |
| **Runs In**   | Periodic       |
| **Testable**  | Yes            |

This module watches the Allsky WebUI system messages file and sends the latest WebUI message as a notification when new messages are detected.  It was designed to alert those who need to know right away when an error occurs or for those who don't check the WebUI regularly but want to know when an error message occurs.

Notifications can be sent via Pushover, ntfy.sh, and/or Email (SMTP). Values can also be published to variables the Allsky Publish Data module or overlays.  You can enable as many options as you want.

- **Allsky Publish Data** enables the use of variables which can be consumed by the Allsky Publish Data module to send to MQTT/Redis/etc.  These variables can also be used in overlays.
  - Use the Module Package Manager in Allsky to install the Allsky Publish Data module
- **Pushover** is an established push notification service/app that can send notifications to iOS, Android, and Desktop/Web.  Free to try with a small one-time purchase to continue.
  - Visit [pushover.net/](https://pushover.net/) to learn about this service and 'create an application' key/token
- **NTFY.sh** is a free open source notification service/app that can send notifications to iOS, Android, and Desktop/Web.  Not quite as slick as Pushover, but works well.
  - Visit [NTFY.sh](https://ntfy.sh/) to learn about this service
- **Email** is a basic email notification via an  SMTP capable account or server (Gmail or other).
  - For Gmail with MFA enabled you need an app password (not your regular login password). See [Sign in with app passwords](https://support.google.com/accounts/answer/185833?hl=en) for details on how to setup. eg a 16-digit passcode used to give the module permission to access your Google Account to send email.

The [Test Module] button can be used to verify  setup with a test notification, simulate a new WEBUI Message, or otherwise test your setup with various debug options.

### Settings:

| **Notification Channels**        |               |Default|
| -------------                    | ------------- |------------- |
| Allsky Publish Data              | Publish values for overlays and Allsky Publish Data module. |true|
| Pushover                         | Enable push notifications via Pushover. |false|
| User Key                         | Your Pushover User Key. ||
| API Token                        | Your Pushover API Token. ||
| NTFY.sh                          | Enable push notifications via ntfy.sh. |false|
| NTFY Server                      | ntfy server URL (change only for self-hosted ntfy). |https://ntfy.sh|
| NTFY Topic                       | ntfy topic/feed to publish to. ||
| Email                            | Enable email notifications via SMTP. |false|
| Recipient Email Address          | Recipient address(es), comma-separated for multiple recipients. ||
| Server Address                   | SMTP server address. |smtp.gmail.com|
| Port                             | SMTP port. |587|
| SMTP Sender email address        | Sender account email address. ||
| SMTP Account Password            | SMTP account password (or app password when required). ||
||||
| **Notification Setup**           |||
| Notification Title/Subject       | Title/Subject used for outgoing notifications. |Allsky WebUI Message Alert|
| Max Notification Limit           | Stop sending notifications after this threshold is met until you review them and clear them in the WebUI |10|
||||
| **Debug / Test**                 |||
| Send Sample Message              | Sends a sample message instead of the latest WebUI message. |false|
| Sim a WebUI Message              | Adds a simulated warning message to the WebUI to verify notification flow. |false|
| Bypass Time check                | Notification of latest WebUI message reagrdless of timestamp detected. |false|
| Reset checks and counts          | Resets module DB keys that track notifications count and last notify time. Debug only. |false|
||||





### Accessible Variables:

When 'Allsky Publish Data' is enabled, this module publishes:
 |Variable          |type   |comments|
 |------------------|-------|--------|
 |`${AS_UI_NOTIFY_HAS_NEW_MSG}`      |bool   |true or false if there is a new message since last check|
 |`${AS_UI_NOTIFY_MSG_DATE}`         |str    |timestamp from message e.g. June 22, 06:30 AM|
 |`${AS_UI_NOTIFY_MSG_TXT}`          |str    |literal text of message|
 |`${AS_UI_NOTIFY_MSG_OCCURRENCES}`  |int    |occurrence count of message|
 |`${AS_UI_NOTIFY_MSGS_COUNT}`       |int    |count of messages displaying in WebUI|

### Notes:
 - Notification send time and count are tracked in module DB keys, so only new messages are sent under normal operation.
 - Once notification count exceeds the configured max limit, notifications are paused until WebUI messages are cleared.
 - If all enabled channels fail delivery, the "last notify" timestamp is not updated so the module can retry on the next run.
 - The notification text is the literal WebUI message, so some may include hyperlinks that are only accessible from the WebUI
