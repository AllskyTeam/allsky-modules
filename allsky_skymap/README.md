# allsky_skymap

**Sky Map** maps how dark and how transparent the sky is, direction by
direction, for [Allsky](https://github.com/AllskyTeam/allsky). It shows where
the light domes of the towns are, which direction is best for observing, and
how both change over the months.

## What it measures

On clear, moonless images (Sun below -15°, Moon below -3°, at least 80% of the
bright stars seen), for the zenith (above 60°) and eight directions (25° to
60°):

- **Limiting magnitude:** the catalogue stars (Hipparcos, to V = 7.5) are
  projected into the image with the fisheye calibration and looked for. The
  magnitude at which half of them are still seen is the limiting magnitude in
  that direction. The same test next to each star gives the chance of a random
  hit, and that is subtracted first. The limiting magnitude falls where the sky
  is bright (light pollution) or hazy (poor transparency). It is the camera's
  limiting magnitude, not the eye's, so compare it direction by direction and
  night by night.
- **Sky background:** the brightness of the image with the stars filtered out
  (0-255). It shows the light domes directly.

**Trees, roofs and the like** are learnt from the stars themselves. Where stars
brighter than V = 4.5 are almost never seen on clear images, that part of the
sky is blocked and left out. A direction that is much darker than the sky
around it (mostly obstacle) is left out of the map too.

## Results

The measurements are averaged per night and kept for a year. Every 30 minutes
a map is drawn, `skymap.png`, showing the limiting magnitude and the
background of the last night, and `skymap.json` is written with the same data
for all nights, the light domes and the blocked cells.

Here, over three moonless nights in September 2026, the module found:

- A light dome to the north-west, 18% above the median sky: the direction of
  Linz, 19 km away.
- A limiting magnitude of 6.6 to the north, 6.0 at the zenith and 5.4 to the
  west.
- The tree to the south-west, which it left out.
- Between two nights, the zenith background changed from 72 to 42.

For the overlay:

- `AS_SKYMAP_DARKEST`: the best direction, e.g. `N (6.5 mag)`.
- `AS_SKYMAP_DOME`: the brightest light dome, e.g. `NW (+18%)`.

Saved in the Allsky database (table `allsky_skymap`):

- `AS_SKYMAP_LM_ZENITH` and `AS_SKYMAP_LM_MEAN`: the limiting magnitude at the
  zenith and the mean of the eight directions.
- `AS_SKYMAP_BG_ZENITH`: the zenith background.

The module brings charts of these values.

## Installation

Install it from the WebUI's **Module Package Manager** and add **"Sky Map"**
to the **night** flow, before the overlay module. It needs a fisheye
calibration: `calibration.json` in the modules folder, made with the Meteor
Detection module's `tools/calibrate_fisheye.py`. It uses `cv2`, `numpy` and
`pyephem`, and takes about 1.2 s per 4K image on a Raspberry Pi 4, only on
clear, moonless images.

**Publish to the website** copies `skymap.png` and `skymap.json` into the
Website's `skymap` folder and uploads them to a remote website. The remote
folder must exist because the upload does not create folders.

## Data

`stars.json`: Hipparcos (ESA 1997, CDS I/239), stars brighter than V = 7.5.
