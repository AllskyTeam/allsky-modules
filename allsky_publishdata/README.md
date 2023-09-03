# AllSky Publish Data Module

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Day time, Night time |

This module allows for AllSky data and variables to be published to an external client such as Redis, MQTT or regular
POST

Following clients are supported

- REDIS
- MQTT
- Requests (POST)

The module contains the following options

| Setting              | Description                                 |
|----------------------|---------------------------------------------|
| Extra Data To Export | Comma separated ENV variables               |
| Redis Host           | Server/Host running the Redis server        |
| Redis Port           | Default port                                |
| Redis Topic          | Which topic should the data be published to |
| Redis Password       | (Optional) If Redis requires a password     |
| MQTT Host            | Server/Host running the Redis server        |
| MQTT Port            | Default port                                |
| MQTT Topic           | Which topic should the data be published to |
| MQTT Username        | (Optional) If MQTT requires a username      |
| MQTT Password        | (Optional) If MQTT requires a password      |
| POST Endpoint        | Endpoint to post the data to                |


