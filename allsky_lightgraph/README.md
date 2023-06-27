# LightGraph 
LightGraph AllSky module 

LightGraph is a AllSky module that overlays on the image captured a graph displaying lightness and darkeness for the day (see below, for what a 'day' means).

![LighGraph sample](https://cgastrophoto.co.uk/lightgraph/lightgraph_sample.JPG)

The display consists of a rectangle covering 24 hours filled with different colors corresponding to: daylight, night, civil dawn and dush, nautical dawn and dusk, and astronomical dawn and dusk.

For instructrions to install, check https://github.com/thomasjacquin/allsky wiki.

# Features and Options

## Position and Size
4 parameters allow to position the graph according to your needs. One extra paramenter allows to set horizontal position to center. If centered is activated, the the horizontal position is ignored.

If horizontal size is set too big the graph will be as wide as the picture.
If the sum of hotizontal position and width (vertical position and heigh) is bigger than the image width (height) the graph will be aligned to the right (bottom) of the image.

## Colors

There are settings for frame color, lights time color and darkness time color. For each of the theree there are two options: daytime and night, so best contrasting colors can be selected for day and night. Format is 3 space separated decimal values (0 to 255) in BGR order.

Color for dawn and dusk are a simple interpolation between lightness and darkness colors.

Transparecy can also be selected.

## Hour marks

Hourly tickmarks can be displayed. Hour numbers as well. If hour tickmarcks are disabled, hour numbers setting will be ignored.

Text scale can also be selected. If the text is so big as to overlap at a given graph width, only every other hour number will be deisplayed.

Two thin lines mark sun transit (noon) and anti-transit (midnight).

## Now Time

A small cursor points to the current time. The user can select left or center alignment.

If left is selected the the display covers 24 hours starting the current time.
If center is selected then the display covers from 12 hours before current time util 12 hours after current time.

# Elevation Grid

An extra feature had been added: a chart showing Sun and Moon elevation.

It shares the timebase with the light graph. But has an specific set of parameters for: enabling/didabling this feature, position, size and colors.
Vertical grid spacing is every hour. Horizontal grid matches tropics and 
por circles latitudes.

# Additional feature

At the moment, and for my convenience the script exports these variables:
AS_SUN_ALT, AS_SUN_AZ
AS_MOON_TRANSIT, AS_MOON_ANTITRANSIT, AS_MOONRISE, AS_MOONSET
AS_SUN_NOON, AS_SUN_MIDNIGHT

They will be removed when AllSky supplies this data.

Thanks and enjoy!
