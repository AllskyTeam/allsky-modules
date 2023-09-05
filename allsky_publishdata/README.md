# AllSky Publish Data Module

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Day time, Night time |

This module allows for AllSky data and variables to be published to an external client such as Redis, MQTT or regular
POST. Also reads additional data from the `ALLSKY_EXTRA` folder and includes it in the message data.

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

## Example output
`Connected to MQTT Broker!
Channel: allsky/meta
`

```json
{'ALLSKY_VERSION': 'v2023.05.01_02',
 'CAMERA_TYPE': 'RPi',
 'CURRENT_IMAGE': '/home/chris/allsky/tmp/image-20230903211208.jpg',
 'DAY_OR_NIGHT': 'NIGHT',
 'FULL_FILENAME': 'image.jpg',
 'allskyai': {'AI_CLASSIFICATION': 'heavy_clouds',
              'AI_CONFIDENCE': 99.693,
              'AI_INFERENCE': 0.219,
              'AI_UTC': 1693768336},
 'utc': 1693768336}
```


