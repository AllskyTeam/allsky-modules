# allsky_cloudforecast

A **day + night cloud cover and clear-sky nowcast** module for
[Allsky](https://github.com/AllskyTeam/allsky).

It estimates how cloudy the sky is directly from the all-sky image, around the
clock, and turns the recent trend into a short-term nowcast: *clearing*,
*clouding over* or *stable*. No sensor is needed.

## Two methods, chosen automatically

| Time | Method | Idea |
|---|---|---|
| **Day** | Red/Blue Ratio (RBR) | Clear sky is blue (low R/B); cloud is white/grey (R≈B, high R/B). A sky pixel counts as cloud when R/B exceeds a threshold. This is the standard sky-imager meteorology method. Blown-out pixels (the Sun) are ignored. |
| **Night** | Star deficit | A clear sky is dotted with stars everywhere; cloud blanks them out. Cloud cover = share of the sky grid with no detected stars. |

Day or night picks the method, so a single number tracks cloud cover through
the whole 24 hours.

## Nowcast

The last ~45 minutes of cloud cover are fitted with a straight line:

- falling → **clearing** (with an estimated "clear within ~N min")
- rising → **clouding over** (with "overcast in ~N min")
- flat → **stable**

Only same-method points are used, so the day↔night switch never creates a spurious
jump, and a minimum time span is required before a trend is reported.

With **Cloud-Motion Nowcast** on, the cloud drift between frames is measured
(optical flow) and the cloud field upwind of the zenith is moved along it, which
gives a directional nowcast such as "zenith clouding over in ~15 min". It is most
reliable by day and falls back to the trend when the motion is unclear.

> **Scope.** This is a persistence/trend extrapolation, reliable for roughly the
> next 30–60 minutes, not a weather forecast.

## Installation

Install it from the WebUI's **Module Package Manager** and enable
**"Cloud Forecast"** for **both** the day and night flows. With only one of
them, the charts show only that part of the day.

Uses only `cv2` + `numpy` (already in Allsky's requirements).

## Configuration

| Setting | Default | Meaning |
|---|---|---|
| Sky Mask | — | White = sky to analyse, black = ignore (trees, buildings, horizon). Without a mask the whole image is used, so a mask gives much better numbers. |
| Daytime R/B Cloud Threshold | `0.88` | R/B above which a daytime pixel is cloud (clear ≈ 0.5–0.6) |
| Clear Below (%) | `20` | Cloud cover below this = clear sky |
| Overcast Above (%) | `65` | Cloud cover above this = overcast |
| Nowcast Window (min) | `45` | History window the trend is fitted over |
| Cloud-Motion Nowcast | on | Also use the cloud motion between frames |
| Optical-Flow Downscale | `4` | Resolution of the motion measurement (higher = faster, coarser) |
| Publish to Website | off | Also write a rolling `cloud.json` for your own website pages |
| History (hours) | `48` | How much history `cloud.json` keeps |

The daytime threshold and the clear/overcast bands are site-dependent (light
pollution, horizon glow); tune them once against a clear and an overcast frame.

## Charts and database

Every value is saved in the Allsky database (table `allsky_cloudforecast`), day
and night, and the module brings three charts for the WebUI's **Charts** page, in
the group **Cloud Forecast**:

- **Cloud Cover**: the cloud cover with the cover expected in 30 minutes;
- **Clear Sky**: a clear / not clear indicator;
- a **Cloud Cover** gauge (0–100 %).

Pointing at a point of the cloud cover shows that image. The module's
**History** tab shows the same data.

## Output

Variables for the **Overlay Editor** (group *Cloud Forecast*):

| Variable | Meaning |
|---|---|
| `AS_CLOUDFORECAST_COVER` | Cloud cover, % |
| `AS_CLOUDFORECAST_CLEAR` | 1 = clear, 0 = not clear |
| `AS_CLOUDFORECAST_STATE` | clear, partly cloudy or overcast |
| `AS_CLOUDFORECAST_PRED30` | Cloud cover expected in 30 minutes, % |
| `AS_CLOUDFORECAST_TREND` | clearing, clouding over or stable |
| `AS_CLOUDFORECAST_NOWCAST` | The nowcast as text, e.g. "clouding over — overcast in ~20 min" |
| `AS_CLOUDFORECAST_METHOD` | rbr (day) or stars (night) |

## Credits

- [Allsky](https://github.com/AllskyTeam/allsky) by Thomas Jacquin and team.
- Built for [astronomy.garden](https://astronomy.garden).
