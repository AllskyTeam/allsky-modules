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

## Installation

Install it from the WebUI's **Module Package Manager**. (For Allsky 2024, copy the
module in by hand — see the
[module's own repository](https://github.com/benhartwich/allsky-skyquality).)

Enable **“Sky Quality Meter”** in the Allsky WebUI for the **night** flow.

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
| History (hours) | 48 | How much history to keep in `skyquality.json` |
| Count Stars | on | Also record a template-matched star count (sensor-free clarity indicator) |

## Output

- Environment variables `AS_SQM` (mag/arcsec²), `AS_SQM_ADU`, `AS_SQM_DESC`
  (rough Bortle description) — usable in the Allsky overlay.
- A rolling **`skyquality.json`** in the Allsky tmp folder: one
  `{t, sqm, adu, exp, gain, stars, temp, cpu}` record per frame, ready to feed a time-series chart
  (Chart.js or similar) — no database needed.

## Roadmap

- [x] Star count as a sensor-free clarity indicator (template matching).
- [x] Ready-made dashboard page (`web/skyquality.html` in the [module's repository](https://github.com/benhartwich/allsky-skyquality)).
- [x] Cloud-coverage percentage and limiting-magnitude estimate (NELM, Schaefer relation).
- [x] Correlate SQM with moon altitude / phase (ephem-based moon washout band on the chart).
- [ ] Push alerts (aurora candidate / exceptional dark-sky readings).

## Credits

- [Allsky](https://github.com/AllskyTeam/allsky) by Thomas Jacquin and team.
- SQM formula & approach inspired by
  [indi-allsky](https://github.com/aaronwmorris/indi-allsky) by Aaron Morris.
- Built for [astronomy.garden](https://astronomy.garden).

## License

MIT — see the [module's repository](https://github.com/benhartwich/allsky-skyquality).
