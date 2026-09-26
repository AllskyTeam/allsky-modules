# allsky_nightrecap

**Night Recap**: every morning, one picture and one short video of the night,
for [Allsky](https://github.com/AllskyTeam/allsky).

At the end of the night the module collects what the other modules found:

| Source module | What it adds |
|---|---|
| Target Watch, Cloud Forecast or Sky Quality | when the sky was clear, the hours of clear sky, the longest clear stretch |
| Meteor Detection | the meteors, with their showers |
| Sky Traffic | the satellite trails found in the images |
| Aurora Detector | images flagged as a possible aurora |
| Sky Quality | the darkest sky (mag/arcsec²) |
| Space Weather | the highest Kp |

Every source is optional: what isn't installed is left out. Clear sky is taken
from the first of Target Watch, Cloud Forecast and Sky Quality that has data
for the night.

## What it makes

In the night's images folder, `recap/`:

- `recap.jpg`: the night at a glance. It shows tiles with the numbers, a
  timeline with the clear sky in green and a mark for every event, and
  pictures of the first five events cut around the streak.
- `recap.mp4`: the recap, then each event with its time and name (H.264,
  made with ffmpeg).
- `recap.json`: the same as data.

One line of text, for the overlay (`AS_NIGHTRECAP_TEXT`), the website or a
notification:

```
17/18 Sep: Clear 4.5 h, 8 meteors, 9 satellite trails
```

The clear hours, meteors and satellite trails of each night are saved in the
Allsky database (table `allsky_nightrecap`), and the **Nights** chart shows
them night by night.

## Installation

Install it from the WebUI's **Module Package Manager** and add
**"Night Recap"** to the **night to day** flow. The night is taken from sunset
to sunrise (Sun at -6°). Uses `cv2`, `numpy`, `pyephem`, and `ffmpeg` for the
video, which Allsky already has.

**Publish to the website** copies the three files into the Website's `recap`
folder and uploads them to a remote website. The remote folder must exist.
**Notify URL** sends the one-line recap with an HTTP POST, e.g. to
[ntfy](https://ntfy.sh).
