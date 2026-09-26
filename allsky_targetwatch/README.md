# allsky_targetwatch

**Target Watch**: is my target clear? For
[Allsky](https://github.com/AllskyTeam/allsky).

An all-sky camera sees the whole sky. An observer wants to know whether the
part of the sky with their target is clear: M31 in a clear gap, Jupiter behind
a cloud. This module answers that on every night image for up to five targets,
and says when a cloud or a gap is coming:

```
M31 clear (100%), Vega clear (100%), clouds in ~10 min, Deneb cloudy (9%), clear in ~20 min
```

## How it measures clear sky

The bright catalogue stars (Hipparcos, V < 5) are projected into the image with
the fisheye calibration for the time of the image, and the module looks for
each of them. A star counts as seen if the image has a point 8 times above the
noise within a few pixels of where it should be.

The same test next to every star measures how often cloud texture or noise
passes by chance, and that rate is subtracted. The share of stars really seen
around a target is compared with the share seen on the clear images of the
last nights at that altitude. The result is the **clear sky in %**.

Measured on the author's camera:

- **Clear image:** 62% of the stars are found. The same test at shifted
  positions finds 2%.
- **Overcast image:** 2%, against 1% by chance.

The Moon's glare hides the stars around it, from 5° at new moon to 20° at full
moon, so those stars aren't counted. A target inside the glare is reported as
"near the Moon".

## The forecast

The clouds are followed from image to image with optical flow. The module then
reads the current clear-sky map upwind of each target, where the air over the
target will come from in 10, 20 and 30 minutes.

On one night with passing clouds here:

- **"Clouds in ~N min":** came true 21 times out of 22. Without a forecast, a
  clear target clouded over within 30 minutes in 24% of cases.
- **"Clear in ~N min":** came true 5 times out of 8, against 16% without.

It forecasts only some of the changes, about one in five, but when it says
something it is usually right. One night is not much: check it on your own
sky.

## Targets

Up to 5, separated by commas:

- **The Moon and planets:** `Moon`, `Venus`, `Mars`, `Jupiter`, `Saturn`, ...
- **Messier objects:** `M31`, `M 42`, or their names: `Andromeda Galaxy`,
  `Pleiades`, `Orion Nebula`.
- **Your own**, as `Name=RA,Dec`, with RA in hours or h:m:s and Dec in degrees
  or d:m:s, e.g. `NAN=20:59:17,+44:31:44`.

A target lower than **Lowest altitude** is reported as low, one outside the
image (a cropped sensor) as outside the image.

## Installation

Install it from the WebUI's **Module Package Manager** and add
**"Target Watch"** to the **night** flow. It needs a fisheye calibration:
`calibration.json` in the modules folder, made with the Meteor Detection
module's `tools/calibrate_fisheye.py`. A star must be found within a few
pixels, which no uncalibrated lens model reaches.

It uses `cv2`, `numpy`, `pyephem` and `requests`, which Allsky already has, and
takes about 1.2 s per 4K image on a Raspberry Pi 4.

## Notification

**Notify URL** (optional): when a target becomes clear and stays clear on the
next image, the module sends a short text such as `M31 is clear (100% clear
sky, 74° high)` with an HTTP POST. It sends at most one per target per hour.
This works with [ntfy](https://ntfy.sh) (`https://ntfy.sh/your-topic`) and
anything else that takes a plain-text POST.

## Values and charts

For the overlay:

- `AS_TARGETWATCH_SUMMARY`: one line for all targets.
- `AS_TARGETWATCH_T1` ... `AS_TARGETWATCH_T5`: each target on its own.

Saved in the Allsky database (table `allsky_targetwatch`):

- `AS_TARGETWATCH_SKY`: clear sky over the whole sky, in %.
- `AS_TARGETWATCH_T1_CLEAR` ... `AS_TARGETWATCH_T5_CLEAR`: clear sky at each
  target, in %.

The module brings a chart of clear sky at the targets and a clear-sky gauge.

## Data

- `stars.json`: Hipparcos (ESA 1997, CDS I/239), stars brighter than V = 6.
- `messier.json`: Messier object positions from
  [OpenNGC](https://github.com/mattiaverga/OpenNGC) by Mattia Verga, licensed
  [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/).
