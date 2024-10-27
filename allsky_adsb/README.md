# AllSky ADSB module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

This module allows aircraft data to be retrieved from a variety of sources. This scan be useful in detecting which aircraft have
been captured in an image.

If you have an interest in tracking aircraft then setting up a local receiver is a good idea. You can feed the date you capture to the popular online aircraft trackers and, generally, in return they will give you free access to their systems. For example if you feed data to flightradar24 then they will give you a business account. Its important to note that you must be able to feed data 24/7

There are three data sources available

|   Source            | Description             |
|---------------------|--------------|
| **Local**           | A local ADBS receiver
| **Opensky**         | The Opensky network
| **Airplanes Live**  | The Airplane sLive network

## Local
This requires a local ADBS receiver. The setup of this is beyond the scope of this document. There are plenty of resources available online for setting up a local ADSB receiver and feeding tracking sites. Some examples

https://www.flightradar24.com/build-your-own
https://www.adsbexchange.com/ways-to-join-the-exchange/build-your-own/
https://uk.flightaware.com/adsb/piaware/build/

If you have a local ADSB receiver already running then all you need is the url to the raw data. Typically this will look something like

http://192.168.1.28:8080/data/aircraft.json

## Opensky
Opensky is a little more complex to implement for a couple of reasons

1) They have limits on the amount of api request you can make daily
2) They require a bounding box to determine which aircraft to return

### Api limits
For a non registered user the limit is 400 request per day, this equates to roughly every 3 minutes. This is not ideal !

For a registered user the limit is 4000 requests per day, this equates to roughly every 21 seconds. This is probably adequate for most users. So if you wish to use Opensky then create an account and set your username and password in the module config.

If you feed data then the limit is 8000 requests per day, this roughly equates to every 11 seconds which is more than adequate for Allsky. To get this limit will require that you feed data and you should refer to the Opensky website on howto do this.

### Bounding box
Opensky requires a bounding box and will only return aircraft inside this box. There are some resources available online that can help in creating the values for the bounding box. One example is (yes its non ssl !)

http://bboxfinder.com/

## Airplanes Live
Airplanes live provide free data, with no limits, but also no guarantees of SLA and it may change in the future.

The only configurable option for Airplanes Live is the distance you wish to get data for from your home location. This default to 50 miles but can be changed in the module config upto 250 miles

## Overlay variables
The module will create an allsky overlay extra data file (allskyadsb.json) containing aircraft sorted by distance. Several variables are available for use in overlays

aircraft_X_hex - The icao code of the aircraft
aircraft_X_text - Short form text of the aircraft
aircraft_X_longtext - Long form text of the aircraft

### Example short form text
ZY39RM  225°

This has the callsign and azimuth of the aircraft

### Example long form text
EZY39RM  225° 26Miles FL067  222kts

This has the

- callsign
- Azimuth
- Distance
- Flight level
- Speed