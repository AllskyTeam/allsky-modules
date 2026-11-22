# SharedSky module for Allsky

`allsky_sharedsky` connects an [Allsky](https://github.com/AllskyTeam/allsky) camera to
[SharedSky](https://allskyhub.org/mitmachen), the free network that measures meteors and
fireballs together with other all-sky cameras: their height, path and, for fireballs, where
pieces may have fallen.

Everything goes out over HTTPS from the camera. There is no FTP, MQTT or open port.

## What it sends

- **The camera's data** (name, place, image size, whether the clock is synchronised). It
  sends this on the first image, again when something changes, and every 6 hours.
- **A small image** (at most 640 px and 300 kB) about once a minute. The hub keeps one
  every 5 minutes.
- **A full frame, now and then.** The hub asks for one on a clear night to work out the
  camera's orientation from the stars. You don't calibrate anything.
- **Every meteor the [Meteor Detection (temporal)](https://github.com/AllskyTeam/allsky-modules/tree/master/allsky_meteordetect)
  module saved**, with its full frame and the two ends of its track. Meteors that other
  cameras saw at the same time are measured together.

Your images stay yours. The hub shows them only where you allow it, and always with the
station's name. Measurements (times, tracks, trajectories) are shared under CC BY 4.0 with
the station's name.

## Setup

1. Create a free account at <https://allskyhub.org> and choose **Kamera verbinden**
   (connect a camera), software *andere oder eigene Software* (other software). The hub
   shows a **station ID** and a **secret**, once.
2. Install **SharedSky** with the Allsky Module Manager.
3. In the WebUI, add **SharedSky** to the day and night flows:
   - Put it **after Meteor Detection (temporal)** in the night flow.
   - Put it **before the Overlay** module, so the hub gets the image without text.
4. Enter the station ID and the secret. Optionally, enter the camera's elevation in metres;
   it helps with meteor heights.
5. Press **Test**. The module then sends everything to the hub's test mode, which checks
   each field and stores nothing. The answer shows what the hub understood.

Latitude and longitude come from Allsky's settings. The station name comes from Allsky's
*Location*, unless you give one.

## Settings

| Setting | Default | |
|---|---|---|
| Station ID, Secret | | from *Kamera verbinden*; the secret is kept in Allsky's `env.json` |
| Name | Allsky's location | the station's name in the network |
| Elevation (m) | empty | height above sea level |
| Lens focal length (mm) | empty | optional, the hub fits the lens itself |
| Image every (s) | 60 | how often the small image goes out |
| Send meteors | on | the meteors of the Meteor Detection (temporal) module |
| Meteor folder | the website's `meteors` | where that module saves its images |

## Files

`~/allsky/config/sharedsky/` holds `state.json` (what was sent) and `orientation.json`.

`orientation.json` is the orientation the hub worked out from the stars:

- `north_deg` is the image direction of north, 0 = up, clockwise.
- `mirrored` is the usual case of a camera looking up.
- `lens` holds the fitted fisheye lens.

`sky_to_pixel(orientation, alt, az)` in the module turns a direction in the sky into a pixel
of the image. You can use it for an overlay of constellations or of the cardinal points.

## Notes

- If the hub can't be reached, Allsky keeps capturing. The module logs a warning, and only
  three failures in a row become a WebUI message. Meteors not sent yet go out with the next
  images, up to 24 hours later.
- Meteors from before the first run are not sent.
- A meteor image of another size than the frame the module sees is skipped. This happens
  when the meteor module runs after a resize or crop, and the track would not fit the
  orientation.
- The API is open and documented: <https://allskyhub.org/entwickler/connect>.

## Licence

MIT, like Allsky. Source: <https://github.com/benhartwich/allskyhub>.
