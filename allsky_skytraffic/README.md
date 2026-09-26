# allsky_skytraffic

**Sky Traffic** names the satellites and aircraft that cross the image, for
[Allsky](https://github.com/AllskyTeam/allsky).

A night image is full of moving things: satellites, aircraft, rocket bodies.
This module knows where each of them was while the image was exposed:

- **Satellites:** orbital elements (TLE) from [CelesTrak](https://celestrak.org),
  downloaded once a day and kept on disk. For every night image the module
  computes each satellite's position at the start, middle and end of the
  exposure with PyEphem, and whether it was in sunlight. Only a sunlit
  satellite can leave a trail.
- **Aircraft** (optional): from your own ADS-B receiver (readsb, dump1090 or
  tar1090 `aircraft.json`) or a free online feed (adsb.fi, adsb.lol). Each
  aircraft is moved back to the exposure with its speed and track.

It puts these positions into the image with the lens model and then:

1. **Names the streaks the Meteor Detection module rejected as "moving".**
   A satellite or aircraft streak gets its name, e.g. `MIDORI II (ADEOS-II)` or
   `AUA18PU (E195)`. A saved meteor that lies on the track of a known
   satellite or aircraft is logged as a warning.
2. **Looks for the trail along every predicted satellite track.** It compares
   each image with the previous one, so the stars cancel. This counts the
   satellites your camera really records, and which ones they were.
3. **Lists the next bright passes** of the ISS, Tiangong and the brightest
   satellites and rocket bodies. It also finds ISS and Tiangong passes across,
   or within a degree of, the Moon or Sun.

## Installation

Install it from the WebUI's **Module Package Manager** and add **"Sky Traffic"**
to the **night** flow. To name the Meteor Detection module's rejected streaks,
put it after that module. Add it to the **day** flow too if you want the next
pass in the overlay before dark.

It needs `pyephem`, `requests`, `cv2` and `numpy`, which Allsky already has. It
needs internet access once a day for the orbital elements. The online aircraft
feeds are read with every night image.

## The lens

The positions are only as good as the lens model:

- **With a calibration** (recommended): `calibration.json` in the modules
  folder, made with the Meteor Detection module's `tools/calibrate_fisheye.py`.
  Positions are then accurate to about 0.3°. If the image is resized, the
  calibration is scaled to match. If the image is cropped, it can't be used.
- **Without one:** the module assumes an equidistant fisheye centred in the
  image, set with **North in the image**, **East is left of North** and
  **Horizon radius**. Raise **Match tolerance** to 3-4° then.

**Debug** writes the predicted tracks into a debug image (green: trail seen,
red: satellite not seen, orange: aircraft). Use it to check the lens settings
against a bright satellite.

## Values

For the overlay:

| Variable | |
|---|---|
| `AS_SKYTRAFFIC_NEXT` | next bright pass, e.g. `ISS 19:50 46° W-SE` |
| `AS_SKYTRAFFIC_NEXT_ISS` | next visible ISS pass |
| `AS_SKYTRAFFIC_TRANSIT` | next ISS / Tiangong transit or close pass by the Moon or Sun |
| `AS_SKYTRAFFIC_SEEN_NAMES` | satellites whose trail is in this image |
| `AS_SKYTRAFFIC_NAMES` | names given to rejected streaks |

Saved in the Allsky database (table `allsky_skytraffic`) for every night image:

- `AS_SKYTRAFFIC_SATS`: sunlit satellites up.
- `AS_SKYTRAFFIC_SEEN`: trails seen.
- `AS_SKYTRAFFIC_AIRCRAFT`: aircraft in the image.
- `AS_SKYTRAFFIC_NAMED_SATS`, `AS_SKYTRAFFIC_NAMED_AIRCRAFT` and
  `AS_SKYTRAFFIC_UNNAMED`: rejected streaks that were named as satellites or
  aircraft, or not named.
- `AS_SKYTRAFFIC_METEOR_SUSPECT`: meteors on a known track.

The module brings three charts: satellites up against trails seen, named
streaks, and aircraft.

Files in `config/myFiles/skytraffic/`:

- `tle-<group>.txt`: the orbital elements.
- `skytraffic_passes.json`: the pass list, recomputed hourly in the background.
- `skytraffic_named.json`: every named streak, with time, position, name and
  distance from the track.
- `skytraffic_seen.json`: every satellite trail found in an image, with time,
  name and the ends of the trail in the image.

## On the website

**Publish to the website** copies `skytraffic_passes.json`,
`skytraffic_seen.json` and `skytraffic_named.json` into the Website's
`skytraffic` folder every 15 minutes, and uploads them to a remote website.
The remote folder must exist because the upload does not create folders.

## Tested

On the author's camera, one night (299 images, 42-90 s exposures):

- **Trails:** it found 9 satellite trails, among them MIDORI II, CZ-8A R/B,
  COSMOS 2151 and FENGYUN 3C, all within 5 px of the predicted track. The same
  night with the time shifted by 10 minutes found none.
- **Moving streaks:** none of the 12 streaks the Meteor Detection module
  rejected as moving matched a satellite. They are most likely aircraft: the
  camera is 20 km from an airport.
- **Aircraft**, one evening (85 images, 19:46–22:05), with adsb.fi positions logged every 15 s:
  - 9 aircraft trails in the images lay within 15 px of their predicted tracks. With the aircraft data shifted by 2 minutes, none did.
  - The Meteor Detection module had saved a "meteor" at 20:03. Sky Traffic flagged it as lying on the track of the aircraft NSZ3748, 12 px away, which checked by eye was right. With the shifted data it wasn't flagged.
  - The 6 streaks rejected as moving that evening were drifting cloud and contrail structures. None of them was named, with or without the shift.
  - Positions from adsb.fi agree with adsb.fi's own direction and distance to 0.3°.

## Limits

- An all-sky camera with long exposures records only the brighter satellites.
  A faint Starlink is spread over hundreds of pixels. Most satellites that are
  up leave no visible trail.
- Satellites that aren't in the loaded groups can't be named: debris,
  classified satellites, and objects launched in the last hours. The
  **visual** group adds the bright rocket bodies.
- Aircraft positions from an online feed are a few seconds old and are moved to
  the exposure in a straight line. A turning aircraft near an airport can be
  off by more than the tolerance.
- Starlink satellites fly in trains along the same track. If the image time is
  off by minutes, another satellite of the train lies on the streak and gives
  it the wrong name. Keep the clock synchronised (NTP) and the tolerance small.
- The orbital elements are fetched at most every 2 hours, as CelesTrak asks.
