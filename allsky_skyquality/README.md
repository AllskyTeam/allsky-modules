# allsky_skyquality

A **Sky Quality Meter (SQM)** module for [Allsky](https://github.com/AllskyTeam/allsky).

Reports sky brightness in **mag/arcsec²** and writes a rolling history for charting.

## Why exposure/gain normalisation matters

Following [indi-allsky](https://github.com/aaronwmorris/indi-allsky), the base
formula is:

```
mag = offset − 2.5 · log10(signal)
```

The catch: Allsky uses **auto exposure and gain** at night, so the raw mean ADU is
*not* comparable between frames — a darker sky simply gets a longer exposure and
higher gain and lands at a similar ADU. Measuring raw ADU would track the exposure
control loop, not the sky. This module normalises first:

```
signal = mean_ADU / exposure_s / gain_factor
mag    = offset − 2.5 · log10(signal)
gain_factor = 10^(gain / gain_scale)
```

so the reading follows the true sky brightness. A clean night curve then peaks at
astronomical midnight and falls toward dawn.

## Day and night

The sky brightness is measured **day and night**, so its chart shows the whole
24 hours, including twilight: roughly 3–5 mag/arcsec² in daylight and 18–22 at
night. At night the same value is the **SQM** reading, and the module adds:

- the naked-eye limiting magnitude (NELM, Schaefer relation);
- a star count and the **cloud cover** (share of the sky where stars are missing), no sensor needed;
- an aurora index (green glow on the northern horizon).

The Moon's altitude and illumination are recorded with every image, so a bright
reading can be matched to the Moon.

## Installation

Install it from the WebUI's **Module Package Manager**. (For Allsky 2024, copy the
module in by hand — see the
[module's own repository](https://github.com/benhartwich/allsky-skyquality).)

Enable **“Sky Quality Meter”** in the Allsky WebUI for the **day** and **night** flows.
With only the night flow, the charts show the nights only.

## Calibration (do this once)

`offset` is a per-camera constant. Point the module at a night, note the reading at
your darkest hour, and adjust `offset` until it matches a known reference:

- a real SQM device reading, or
- your site's known value (e.g. a rural Bortle 4 sky ≈ 20.8–21.2 mag/arcsec²).

`offset` shifts every reading by the same amount, so one measurement calibrates the
whole scale. `gain_scale` (default 200, suited to ZWO 0.1 dB gain units) only
matters if your gain varies between frames.

## Configuration

| Setting | Default | Meaning |
|---|---|---|
| ROI Mask | — | Optional mask image; white = measure here (best: zenith only) |
| ROI (x1,y1,x2,y2) | — | Explicit rectangle; empty = central FOV |
| Central FOV Divisor | 4 | Central box fraction when no mask/ROI (4 = central quarter) |
| Magnitude Offset | 17.0 | **Calibration constant — tune it** |
| Gain Scale | 200 | Divisor exponent for gain normalisation |
| Count Stars | on | At night, also count stars and estimate the cloud cover |
| Publish to Website | off | Also write a rolling `skyquality.json` for your own website pages |
| History (hours) | 48 | How much history `skyquality.json` keeps |

## Charts and database

Every value is saved in the Allsky database (table `allsky_skyquality`), day and
night, and the module brings four charts for the WebUI's **Charts** page, in the
group **Sky Quality**:

- **Sky Brightness and Moon**: the 24-hour sky brightness with the Moon's altitude;
- **SQM and Limiting Magnitude** (night);
- **Stars and Cloud Cover** (night);
- an **SQM** gauge (16–22 mag/arcsec²).

Pointing at a point of the brightness, SQM or star chart shows that image.
The module's **History** tab shows the same data.

## Output

Variables for the **Overlay Editor** (group *Sky Quality*):

| Variable | Meaning |
|---|---|
| `AS_SKYQUALITY_BRIGHTNESS` | Sky brightness, mag/arcsec² (day and night) |
| `AS_SKYQUALITY_SQM` | SQM, mag/arcsec² (night) |
| `AS_SKYQUALITY_NELM` | Naked-eye limiting magnitude (night) |
| `AS_SKYQUALITY_BORTLE` | Rough Bortle class (night) |
| `AS_SKYQUALITY_STARS` | Star count (night) |
| `AS_SKYQUALITY_CLOUD` | Cloud cover, % (night) |
| `AS_SKYQUALITY_AURORA` | Aurora index (night) |
| `AS_SKYQUALITY_MOONALT`, `AS_SKYQUALITY_MOONILLUM` | Moon altitude (°) and illumination (%) |
| `AS_SKYQUALITY_ADU` | Mean ADU in the measured area |

The names start with `AS_SKYQUALITY_` so they don't clash with the
`allsky_sqm` module's `AS_SQM`. Before v0.3.0 they were `AS_SQM`, `AS_SQM_NELM`
and so on; overlays that used those need the new names.

## Credits

- [Allsky](https://github.com/AllskyTeam/allsky) by Thomas Jacquin and team.
- SQM formula & approach inspired by
  [indi-allsky](https://github.com/aaronwmorris/indi-allsky) by Aaron Morris.
- Built for [astronomy.garden](https://astronomy.garden).

## License

MIT — see the [module's repository](https://github.com/benhartwich/allsky-skyquality).
