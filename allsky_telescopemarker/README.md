# Telescope Position Marker Module
This module marks the current position of your telescope in Allsky images. Each time the module starts it will refresh the current telescope postion allowing you to track your observing conditions in real time.

It does require ASCOM Remote Server with a connected telescope to retrieve the alt/az from.
If you wish to test you can setup a simulated ASCOM telescope in the remote server or define a fallback location for your telescope (ASCOM Remote Server not accessible or response is not a valid JSON object).

For details how to setup ASCOM Remote server and API documenation see:
[ASCOM Remote Server](https://download.ascom-standards.org/docs/RemoteInstConf.pdf)
[ASCOM Alpaca Device API](https://ascom-standards.org/api/#/Telescope%20Specific%20Methods)

The minimum requirements to get it working are:
* You are using a fisheye lense with at least 180° field of view.
* The Allsky image is square.  You will likely need to crop the image.

In the module settings there are configuration options for:
* Define individual latitude/longitude/altitude for telescope and allsky camera.
* Set azimuth rotation if your sensor is not pointing north.
* Customize size and color of the marker.
* Define x,y coordinate flip to map image orientation.

![Sample Allsky image](165_parked_fisheye_image.jpg)

### Release info
### V0.1
* Initial release developed based on Allsky v2023.05.01_04 and ASCOM Remote Server v6.7.1
