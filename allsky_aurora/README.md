# allsky_aurora

An **aurora candidate detector** for [Allsky](https://github.com/AllskyTeam/allsky).

At mid latitudes an aurora shows up as a green glow or arc **low on the polar
horizon**: North in the northern hemisphere, South in the southern. During a
strong storm, red rays may climb above it. This module watches that part of the
sky every night and flags frames that look like an aurora.

## How it tells an aurora from everything else

The green of an aurora is atomic-oxygen emission at 557.7 nm, so the key test is
that the glow is **green above red AND green above blue**:

| Trap | Why it is rejected |
|---|---|
| Moonlit or light-polluted cloud | bright but red-dominant: green is far below red |
| Blue twilight, blue light-pollution dome | green is below blue |
| Airglow | green, but faint and uniform over the whole sky, not a structured arc |
| Stars | removed by a median filter before scoring |

A pixel counts when it is green enough, sits above the smooth background
(structure), and belongs to an extended patch. The **aurora index** is the share
of the band that passes; above **Detection threshold** the frame is flagged.

The module only looks when the Sun is well below the horizon (default -14°),
and skips overcast frames when the **Cloud Forecast** or **Sky Quality Meter**
module runs before it.

> **Scope.** This is a *candidate* detector. An aurora at mid latitudes needs a
> strong geomagnetic storm, so most nights show nothing. Each flagged frame gets
> a thumbnail so you can confirm it by eye.

## Installation

Install it from the WebUI's **Module Package Manager** and add
**"Aurora Detector"** to the **night** flow, before the overlay module (so the
overlay's text and compass aren't in the image). If you use Cloud Forecast or
Sky Quality Meter, put them before this module.

Uses only `cv2`, `numpy` and `pyephem`.

## Where it looks

The band is a sector of the visible fisheye disc toward the pole:

- **With a calibration:** a `calibration.json` made by the Meteor Detection
  module's tools, in the modules folder. The band uses the true optical centre
  and North.
- **Without:** the band uses the image centre and **North in the image**
  (degrees clockwise from the top; the Website's constellation overlay `az` is
  a good value to start with).

**Band inner/outer radius** and **half-width** set the band's size. A mask can
remove trees or buildings. **Enable debug images** writes the band to the tmp
debug folder so you can check it.

## Charts and database

Every scored frame is saved in the Allsky database (table `allsky_aurora`), and
the module brings two charts for the WebUI's **Charts** page, in the group
**Aurora**:

- **Aurora Index**: the index with how much greener than red the glow is;
- **Possible Aurora**: a yes/no indicator.

With the **Space Weather** module's Kp index in the database too, a custom chart
can show both, to see whether the camera saw something when Kp was high.

## Output

| Variable | Meaning |
|---|---|
| `AS_AURORA` | 1 = possible aurora, 0 = no |
| `AS_AURORA_INDEX` | Share of the band that is green, structured and above the background, % |
| `AS_AURORA_GREEN` | How much greener than red the flagged glow is |
| `AS_AURORA_STRUCTURE` | How far the flagged glow is above the smooth background |
| `AS_AURORA_THUMBNAIL` | File name of the thumbnail saved on this frame |

Thumbnails of flagged frames are saved in `images/<day>/aurora/`. With
**Publish to Website** on, a rolling `aurora.json` and the thumbnails are also
written to the website (and uploaded to a remote one), for your own pages.

## Credits

- [Allsky](https://github.com/AllskyTeam/allsky) by Thomas Jacquin and team.
- Built for [astronomy.garden](https://astronomy.garden).
