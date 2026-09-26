# LightGraph

LightGraph is an AllSky module that overlays a light and darkness graph on captured images.

For installation instructions, see the [https://github.com//AllskyTeam/](https://github.com//AllskyTeam/).

## Daily Light Graph

The daily graph covers 24 hours and shows:

- Daylight
- Civil dawn and dusk
- Nautical dawn and dusk
- Astronomical dawn and dusk
- Full darkness

The colors for dawn and dusk are interpolated between the configured light and dark colors.
The graph supports configurable size, position, transparency, colors, hour ticks, hour labels,
and current-time alignment.

The current time can be aligned to the left edge or centered. When centered, the graph covers
12 hours before and 12 hours after the current time.

## Elevation Grid

The optional elevation grid shows Sun and Moon elevation over the same 24-hour period.
It includes configurable position, size, colors, and line thickness. The grid includes hourly
vertical spacing and reference lines for the tropics and polar circles.

## Annual Graph

The optional annual graph displays a full-year calendar with one column for each day. Each day
is filled with the same five color levels used by the daily graph: daylight, civil, nautical,
astronomical, and full darkness.

The annual graph supports:

- Midnight-to-midnight (`0 to 24 hours`) or noon-to-noon (`Previous noon to next noon`) axes
- Time increases upward: midnight is at the bottom in midnight-to-midnight mode
- Vertical labels are shown every six hours (`00` to `24`, or `-12` to `12`)
- A relative `-12` to `+12` hour axis in noon-to-noon mode, with midnight at `0`
- Configurable transparency and position
- Granularity from `1` to `10`
- A current-date vertical marker and current-time horizontal marker
- Configurable `Marker` color, red by default

Granularity `10` uses 15-minute bands. Granularity `1` selects a time interval that produces
bands approximately one pixel high. Intermediate values provide resolutions between those limits.

## Colors

Colors use three space-separated decimal values in Blue/Green/Red (BGR) order, with each value
between 0 and 255. The color picker format is also supported by the module.

## Additional Information

The module uses PyEphem for solar calculations, NumPy for image geometry, and OpenCV for drawing.

Thanks and enjoy!
