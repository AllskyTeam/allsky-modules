This module marks the current position of your telescope in your allsky-image.
It will get the current positon via ALAPACA Network connection from your telescope system.

This module is heavily inspired and based on the original telescopemarker by frankhirsch!

It is modified to have more features and fixes the main limitation, as the aspect ration can be anything, not only 1:1.

Main features:
- Draws a circle around the current positon
- Saves Alt/Az, usable in Overlay Editor as ${AS_TELESCOPEALT} + ${AS_TELESCOPEAZ}
- Saves current status of the Telescop, usable in Overlay Editor as ${AS_TELESCOPESTATUS} (Home, Parked, Tracking, Idle, N/A if no network Connection)
- Debug mode helps with orientation (Draws North + Horizont)
- customization of the marker (size, color)
