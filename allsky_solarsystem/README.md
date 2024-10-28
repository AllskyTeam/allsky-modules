# AllSky Solar System module

|              |              |
|--------------|--------------|
| **Status**   | Experimental |
| **Level**    | Beginner     |
| **Runs In**  | Periodic     |

This module allows data for Solar system objects, planets and Earth satellites,  to be calculated and made available for display on overlays

## Planets
The module config is fairly straightforward, for the Sun, Moon and planets tab simply select the objects you would like calculated and the module will make the following data available in the overlay editor

## The Moon

    "AS_MOON_AZIMUTH": "357",
    "AS_MOON_ELEVATION": "-36.02",
    "AS_MOON_ILLUMINATION": "11.5",
    "AS_MOON_SYMBOL": "W",

## The Sun
    "AS_SUN_DAWN": "20241029 06:14:04",
    "AS_SUN_SUNRISE": "20241029 06:50:27",
    "AS_SUN_NOON": "20241029 11:42:34",
    "AS_SUN_SUNSET": "20241028 16:35:54",
    "AS_SUN_DUSK": "20241028 17:12:07",
    "AS_SUN_AZIMUTH": "307",
    "AS_SUN_ELEVATION": "-40",

## Planets
    "AS_Mercury_ALT": "-36deg 58' 52.9\"",
    "AS_Mercury_ALTD": "-36",
    "AS_Mercury_ALTM": "58",
    "AS_Mercury_ALTS": "52",
    "AS_Mercury_AZ": "285deg 40' 14.5\"",
    "AS_Mercury_AZD": "285",
    "AS_Mercury_AZM": "40",
    "AS_Mercury_AZS": "14",
    "AS_Mercury_RA": "15h 19m 09.98s",
    "AS_Mercury_DEC": "-20deg 05' 17.8\"",
    "AS_Mercury_DISTANCE_KM": "195626327",
    "AS_Mercury_DISTANCE_KM_FORMATTED": "195,626,327",
    "AS_Mercury_DISTANCE_MILES": "121556526",
    "AS_Mercury_DISTANCE_MILES_FORMATTED": "121,556,526",
    "AS_Mercury_VISIBLE": "No",

## Satellites
These are slightly more complex to setup. The satellite tab contains a field where you can enter a comma separated list of Norad ID's and tle groups, for example

25544,amateur <-- This will download Satellite data for ISS (25544 is the Norad id for the ISS) and Satellite data for all amateur radio satellites
25544,amateur, visual <-- will download data for ISS, all amateur radio and brightest satellites

For each satellite the following will be available

    "AS_25544_NAME": "ISS (ZARYA)",
    "AS_25544_ALT": "-14deg 52' 59.3\"",
    "AS_25544_ALTD": "-14",
    "AS_25544_ALTM": "52",
    "AS_25544_ALTS": "59",
    "AS_25544_AZ": "107deg 35' 18.5\"",
    "AS_25544_AZD": "107",
    "AS_25544_AZM": "35",
    "AS_25544_AZS": "18",
    "AS_25544_DISTANCE": "4494.53506453087",
    "AS_25544VISIBLE": "No",

Note that each key contains the norad id.

Also available is a separate list containing the most 'visible' satellites. This is based upon the elevation of a satellite and wether its being lit by the sun. This feature only really works if you are ONLY using the visual group.

    "AS_VISIBLE1_53106_NAME": "GREENCUBE",
    "AS_VISIBLE1_53106_ALT": "28deg 15' 21.5\"",
    "AS_VISIBLE1_53106_ALTD": "28",
    "AS_VISIBLE1_53106_ALTM": "15",
    "AS_VISIBLE1_53106_ALTS": "21",
    "AS_VISIBLE1_53106_AZ": "263deg 36' 41.1\"",
    "AS_VISIBLE1_53106_AZD": "263",
    "AS_VISIBLE1_53106_AZM": "36",
    "AS_VISIBLE1_53106_AZS": "41",
    "AS_VISIBLE1_53106_DISTANCE": "7835.50088580322",
    "AS_VISIBLE2_43700_NAME": "ES'HAIL 2",
    "AS_VISIBLE2_43700_ALT": "25deg 34' 19.0\"",
    "AS_VISIBLE2_43700_ALTD": "25",
    "AS_VISIBLE2_43700_ALTM": "34",
    "AS_VISIBLE2_43700_ALTS": "18",
    "AS_VISIBLE2_43700_AZ": "148deg 51' 30.5\"",
    "AS_VISIBLE2_43700_AZD": "148",
    "AS_VISIBLE2_43700_AZM": "51",
    "AS_VISIBLE2_43700_AZS": "30",
    "AS_VISIBLE2_43700_DISTANCE": "39012.727210743535"
