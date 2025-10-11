# Light Graph Module

LightGraph is a Allsky module that overlays on an image a graph displaying lightness and darkeness for the day (see below, for what a 'day' means).

![LighGraph sample](https://cgastrophoto.co.uk/lightgraph/lightgraph_sample.JPG)

The display consists of a rectangle covering 24 hours filled with different colors corresponding to: daylight, night, civil dawn and dusk, nautical dawn and dusk, and astronomical dawn and dusk.

# Features and Options

## Position and Size
4 parameters allow you to position the graph according to your needs. One extra paramenter allows you to set the horizontal position to center. If centered is activated, the the horizontal position is ignored.

If horizontal size is set too big the graph will be as wide as the picture.
If the sum of hotizontal position and width (vertical position and height) is bigger than the image width (height) the graph will be aligned to the right (bottom) of the image.

## Colors
There are settings for frame color and light and darkness time colors. For each of the three there are two options: daytime and night, so best contrasting colors can be selected for day and night. Format is 3 space-separated decimal values (0 to 255) in Blue/Green/Red (BGR) order.

Color for dawn and dusk are a simple interpolation between lightness and darkness colors.

Transparency can also be selected.

## Hour marks
Hourly tickmarks can be displayed. Hour numbers as well. If hour tickmarcks are disabled, hour numbers setting will be ignored.

Text scale can also be selected. If the text is so big as to overlap at a given graph width, only every other hour number will be displayed.

Two thin lines mark sun transit (noon) and anti-transit (midnight).

## Now Time
A small cursor points to the current time. You can select left or center alignment.

If left is selected then the display covers 24 hours starting with the current time.
If center is selected then the display covers from 12 hours before current time util 12 hours after current time.

# Elevation Grid

An extra feature had been added: a chart showing Sun and Moon elevation.

It shares the timebase with the light graph but has a specific set of parameters: enabling/didabling this feature, position, size and colors.
Vertical grid spacing is every hour. Horizontal grid matches tropics and polar circles latitudes.
