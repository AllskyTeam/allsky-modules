# AllSky ADSB module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

## Thanks to the follwoing

hexdb.io - For the aircraft info web service api. Please see https://hexdb.io/
adsbdb.com - For the flight routing information. Please see https://www.adsbdb.com/

This module allows aircraft data to be retrieved from a variety of sources. This scan be useful in detecting which aircraft have
been captured in an image.

If you have an interest in tracking aircraft then setting up a local receiver is a good idea. You can feed the date you capture to the popular online aircraft trackers and, generally, in return they will give you free access to their systems. For example if you feed data to flightradar24 then they will give you a business account. Its important to note that you must be able to feed data 24/7

If you use any of the online sevices available in this module then please consider supporting the sevice by either donating or feeding data.

There are several data sources available

|   Source            | Description             |
|---------------------|--------------|
| **Local**           | A local ADBS receiver
| **Opensky**         | The Opensky network
| **Airplanes Live**  | The Airplanes Live network
| **adsb.fi**         | The adsb.fi network

These datasource typically do not provide details about the actual aircraft type. The 'Aircraft Data' tab provides two options for obtaining additional information about the flight.

The 'data source' option allows either local data or an internet web service to be used. For the internet web service (provided by hexdb.io) there is no additional configuration. For the 'local' option you will need to update the local aicraft database. To do this, from a command line on the pi

cd /opt/allsk/modules/adsb/tools
./update_database

Not all aircraft will be recognised and there may be a few miscoded aircraft in either system, there is no global catalog of jex codes to aircarft so all of this data has been collated by volunteers. 

A second option is available 'Get flight route'. This will attempt to get the route the flight is taking (provided by adsbdb.com). Like the aircraft data above this is all collated by volunteers so may not be 100% accurate.

# Data Sources

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

The only configurable option  is the distance you wish to get data for from your home location. This default to 50 miles but can be changed in the module config upto 250 miles, see 'limit distance'

## adsbfi
Adsb.fi provide free data, with no limits, but also no guarantees of SLA and it may change in the future.

The only configurable option is the distance you wish to get data for from your home location. This default to 50 miles but can be changed in the module config upto 250 miles

## Overlay variables
The module will create an allsky overlay extra data file (allskyadsb.json) containing aircraft sorted by distance. Several variables are available for use in overlays

aircraft_X_hex - The icao code of the aircraft
aircraft_X_text - Short form text of the aircraft
aircraft_X_longtext - Long form text of the aircraft
aircraft_X_type - The type of aircraft (if enabled and the hex code is known)
aircraft_X_owner - The aircraft owner (if enabled and the hex code is known)
aircraft_X_registration - The aircraft registration (if enabled and the hex code is known)
aircraft_X_manufacturer - The manufacturer of the aircraft
aircraft_X_military - Text flag to indicate if the aircraft is military (set to 'Mil'), this is only available when using the local aircraft data set
aircraft_X_short_route - Short version of the aircrafts route if available "ICAO -> ICAO"
aircraft_X_medium_route - Medium version of the aircrafts route if available "City -> City"
aircraft_X_long_route - - Long version of the aircrafts route if available "(City) Airport -> (City) Airport

### Example short form text
WUK78 207°

This has the callsign and azimuth of the aircraft

### Example long form text
WUK78 A321 207° 11Miles FL122  264kts

This has the

- callsign
- Aircraft type (If enabled)
- Azimuth
- Distance
- Flight level
- Speed

## Raw overlay data

The following data is available for the overlay manager

"aircraft_1_hex": "ae5406",
"aircraft_1_type": "V22",
"aircraft_1_owner": null,
"aircraft_1_registration": "08-0050",
"aircraft_1_manufacturer": null,
"aircraft_1_military": "Mil",
"aircraft_1_text": "00000000 127\u00b0",
"aircraft_1_longtext": "00000000 V22 127\u00b0 13Miles LOW  235.0kts",
"aircraft_1_short_route": "MHRO -> MHRO",
"aircraft_1_medium_route": "Roatan -> Roatan",
"aircraft_1_long_route": "(MHRO) Juan Manuel Galvez International Airport -> (MHRO) Juan Manuel Galvez International Airport",
"aircraft_2_hex": "440c17",
"aircraft_2_type": "FA7X",
"aircraft_2_owner": null,
"aircraft_2_registration": "OE-LHA",
"aircraft_2_manufacturer": null,
"aircraft_2_military": "",
"aircraft_2_text": "LDX700 213\u00b0",
"aircraft_2_longtext": "LDX700 FA7X 213\u00b0 17Miles FL097  252kts",
"aircraft_2_short_route": "KMIA -> EGGW",
"aircraft_2_medium_route": "Miami -> London",
"aircraft_2_long_route": "(KMIA) Miami International Airport -> (EGGW) London Luton Airport",

In this example the V22, aircraft 1, has incorrect route information