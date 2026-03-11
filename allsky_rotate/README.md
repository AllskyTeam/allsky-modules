# allsky_rotate

Rotates the captured image by a fixed angle **before overlays are applied**, to compensate for a camera that is physically mounted off-axis from polar north (or south). Once corrected, compass directions, cardinal overlays, and star trails will appear correctly oriented in every saved image.

## Important Notes

**Intended use:** This module is designed for fisheye all-sky cameras pointed **straight up** and capturing a large portion of the sky. It is not intended for use with traditional landscape or skyfield-style cameras.

**Module order matters — run this after any masking:** Because rotation shifts the position of the image within the frame, any circular mask applied *before* this module will no longer align correctly with the rotated image. This module must be placed **after** any masking modules in your flow.

**Must be configured in both day and night routines:** This module runs on both the `day` and `night` events. You must add and configure it in both routines independently for rotation to apply consistently across day and night captures.

## Configuration

| Setting | Description |
|---|---|
| **Rotation Angle** | The number of degrees to rotate the image. Positive values rotate **counter-clockwise**, negative values rotate **clockwise**. For example, if your mount is 15° clockwise of north, enter `-15`. |
| **Expand Canvas** | If enabled, the output canvas is enlarged to prevent any part of the rotated image being clipped. For circular fisheye all-sky images this is **not** required and should be left disabled — the sky disk simply spins within the frame. |
| **Background Colour** | The fill colour for any areas exposed by rotation, in `R,G,B` format. Defaults to black (`0,0,0`), which is correct for fisheye images where the corners are already black. |
| **Show North Alignment Line** | Draws a vertical line through the horizontal centre of the image to serve as a north reference. Use this during initial alignment to judge where the celestial pole falls. **Disable once your angle is set** — the line will appear in all saved images and timelapses until turned off. |
| **Alignment Line Colour** | Colour of the alignment line in `R,G,B` format. Defaults to red (`255,0,0`). |
| **Alignment Line Thickness** | Thickness of the alignment line in pixels (1–10). |
| **Star Trail Date** | Date of a star trail image to use as an alignment reference, in `YYYYMMDD` format (e.g. `20250308`). The module will load `~/allsky/images/(date)/startrails/startrails-(date).jpg`, rotate it by the same angle as the live image, and blend it over the live capture. Leave blank to disable. |
| **Star Trail Opacity** | How strongly the star trail is blended over the live image, as a percentage. `100` replaces the live image entirely; `0` hides it. `50–70` is a good range for alignment work. |

## Finding Your Correct Rotation Angle

The easiest method uses a previously captured star trail image. The circular arc of star trails pivots around the celestial pole (Polaris in the northern hemisphere, Sigma Octantis in the southern), making it straightforward to judge alignment visually.

1. Enable **Show North Alignment Line** and enter a recent date in **Star Trail Date**.
2. Set **Star Trail Opacity** to `60–90%` so the trail is clearly visible over the live image.
3. Adjust **Rotation Angle** and observe the result after each capture — the circular arc of the star trails will shift. When the pivot point of the arc sits exactly on the alignment line, your angle is correct.
4. Once happy, clear the **Star Trail Date** field, disable the **Show North Alignment Line** checkbox, and save.

Without a star trail image, you can align by eye using a known reference:

1. Enable **Show North Alignment Line** and capture an image.
2. Note how far off the centre-top the celestial pole (or a known landmark due north/south) appears.
3. Adjust the angle to compensate — if the pole appears 20° clockwise of centre-top, enter `20`.
4. Iterate until the pole sits on the line, then disable the line and save.

## Notes

- The angle follows the standard OpenCV convention: **positive = counter-clockwise, negative = clockwise**. This is the opposite of compass bearing arithmetic, so double-check your direction.
- The star trail overlay is rotated by the same angle as the live image before blending, so both always share the same reference frame as you adjust the angle.
- The alignment line is drawn **after** rotation, so it always appears as a true vertical centre reference regardless of the angle setting.
- If the star trail file for the specified date cannot be found, a warning is written to the log and the module continues normally — no crash, no blank image.
- If the star trail image resolution differs from the live image it will be automatically resized before blending.

## Dependencies

No additional Python packages are required. This module uses only `opencv-python` and `numpy`, which are included with every Allsky installation.

## Changelog

| Version | Changes |
|---|---|
| v1.0.0 | Initial release. Features: image rotation, optional star trail alignment overlay, optional north alignment line. |
