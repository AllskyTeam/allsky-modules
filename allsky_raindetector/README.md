# AllSky Raindetector

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Day time, Night time |

This module allows AllSky to detect raindrops on the camera lens using a YOLO model converted to the **NCNN** format. It is designed for lightweight and fast inference on Raspberry Pi, while preserving the same detection logic used in the PyTorch/Ultralytics version.


## Accessible Variables

```json
{ "AS_YOLORAINDETECTED": true, 
  "AS_YOLOFIRSTDROP": "18 Aug 2025, 14:32" }
```

- `AS_YOLORAINDETECTED` → `true`, `false`, or `pending`  
- `AS_YOLOFIRSTDROP` → First raindrop timestamp

### Release info
### V1.0.0
* Initial release of NCNN-based YOLO Rain Detector
* Preloaded NCNN model for faster inference
* Added sliding window + cooldown logic
* Overlay integration with `AS_YOLORAINDETECTED` and `AS_YOLOFIRSTDROP`
