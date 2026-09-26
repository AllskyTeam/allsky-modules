# allsky_lenscheck

**Lens Check**: are the stars still sharp? For
[Allsky](https://github.com/AllskyTeam/allsky).

A camera that is looked after from far away can go blind without anyone
noticing: dew or frost on the dome, or a lens that has slipped out of focus.
The stars then grow into soft discs. This module measures how wide the stars
are on every clear night image, compares it with what is normal for this
camera, and warns when they get wider.

## How it works

1. **Measuring:** the bright catalogue stars (Hipparcos, V < 4) are projected
   into the image with the fisheye calibration. For each one that is seen and
   not saturated, the module measures the width of its image at half its
   height (FWHM). It uses the narrower axis, so a star trailed by a long
   exposure still counts. The median of these widths is the star width of the
   image.
2. **Learning what is normal:** the normal width is learnt from clear, sharp
   images, separately for each exposure time, because a 2 s and a 60 s image
   look different after processing. Only images that look sharp teach it, so a
   slowly fogging dome can't become the new normal. It needs 20 clear images
   per exposure time before it judges.
3. **Judging:** the image is **soft** from 1.3 times the normal width and
   **blurred** from 1.6 times, on two images in a row.
4. **Dew:** if the Dew Heater module, or `AS_TEMP` and `AS_DEW`, shows that the
   temperature is less than 3 °C above the dew point, a blurred image is
   reported as **dew**.

The module only judges images where at least 60% of the bright stars are seen.
Clouds don't make stars wider; they hide them.

## Values

For the overlay and other modules:

- `AS_LENSCHECK_STATE`: `sharp`, `soft`, `blurred`, `dew` or `learning`.
- `AS_LENSCHECK_DEW`: 1 when the stars are blurred and the dome is near the
  dew point, else 0. A heater control can use it.

Saved in the Allsky database (table `allsky_lenscheck`) with a chart:

- `AS_LENSCHECK_FWHM`: the star width in pixels.
- `AS_LENSCHECK_RATIO`: the star width against the normal width.

**Notify URL** (optional): when the image becomes blurred, a short text is
sent with an HTTP POST (e.g. to [ntfy](https://ntfy.sh)), at most once a
night.

## Installation

Install it from the WebUI's **Module Package Manager** and add
**"Lens Check"** to the **night** flow, before the overlay module. It needs a
fisheye calibration: `calibration.json` in the modules folder, made with the
Meteor Detection module's `tools/calibrate_fisheye.py`.

## Tested

On the author's camera, over nine nights in September 2026 (1000 images):

- **Real nights:** 456 clear images were judged. The star width stayed between
  0.70 and 1.19 times normal (99% below 1.14), and no image was flagged.
- **Artificial blur:** there was no dew in that time, so clear images of one
  night were blurred on purpose:

  | Gaussian blur | Star width | Result |
  |---|---|---|
  | σ = 1 px | 1.1× normal | sharp |
  | σ = 1.5 px | 1.2× normal | sharp |
  | σ = 2 px | 1.35× normal | soft |
  | σ = 3 px | 1.66× normal | blurred |

  Real dew usually spreads a star much more. It hasn't been seen by the
  module yet.

While the module is still learning an exposure time (the first 20 clear
images), it takes every image as normal.

## Data

`stars.json`: Hipparcos (ESA 1997, CDS I/239), stars brighter than V = 6.
