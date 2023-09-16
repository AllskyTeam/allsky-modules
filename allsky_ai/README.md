# AllSky AI Module

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Day time, Night time |

This module allows for AllSky to classify the current sky conditions based on Machine Learning.
More info can be found at [allskyai.com](https://www.allskyai.com)

### Release info
* V.1.0 - Trained on ~31.000 curated images

### Todo
* Allow for download if you have a custom trained model for your personal setup

The module contains the following options

| Setting     | Description                                  |
|-------------|----------------------------------------------|
| Camera Type | RGB or MONO                                  |
| Auto Update | Automatically download new version if exists |

## Accessible Variables

```json
{ 'AI_CLASSIFICATION': 'heavy_clouds', 
  'AI_CONFIDENCE': 99.693,
  'AI_INFERENCE': 0.219,
  'AI_UTC': 1693768336}
}
```
