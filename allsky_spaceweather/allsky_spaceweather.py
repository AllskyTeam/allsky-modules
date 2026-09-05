#TODO Events
'''
allsky_spaceweather.py

Part of allsky postprocess.py modules for Thomas Jacquin's AllSky.
https://github.com/AllskyTeam/allsky

This module retrieves space weather data from NOAA SWPC APIs and processes it for AllSky Overlays
'''
import allsky_shared as s
import sys
import requests
import json
import ephem
import pytz
import datetime

# A selected rtsw/ record older than this means the feed has stalled, or that the
# file ordering has changed again. Either way the values are not current and the
# module says so rather than rendering them silently.
RTSW_MAX_AGE_SECONDS = 1800


metaData = {
        "name": "Space Weather",
        "description": "Retrieve space weather data from NOAA SWPC",
        "docs": "docs/allsky_modules/extra/space_weather.html",    
        "module": "allsky_spaceweather",
        "version": "v1.0.2",
        "centersettings": "false",
        "testable": "true", 
        "extradatafilename": "spaceweather.json",
        "group": "Data Capture", 
        "events": [
                "day",
                "night",
                "periodic"
        ],
        "extradata": {
                "values": {
                        "SWX_SWIND_SPEED": {
                                "name": "${SWIND_SPEED}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "Solar wind speed",
                                "type": "number"
                        },
                        "SWX_SWIND_DENSITY": {
                                "name": "${SWIND_DENSITY}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "Solar wind density",
                                "type": "number"
                        },
                        "SWX_SWIND_TEMP": {
                                "name": "${SWIND_TEMP}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "Solar wind temperature",
                                "type": "number"
                        },
                        "SWX_KPDATA": {
                                "name": "${KPDATA}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "KP Data",
                                "type": "number"
                        },
                        "SWX_BZDATA": {
                                "name": "${BZDATA}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "BZ Data",
                                "type": "number"
                        },
                        "SWX_S_ANGLE": {
                                "name": "${S_ANGLE}",
                                "format": "",
                                "sample": "",
                                "group": "Space",
                                "description": "Sun Angle",
                                "type": "number"
                        }
                }                         
        }, 
        "arguments": {
                "latitude": "",
                "longitude": "",
                "period": 300,
                "filename": "spaceweather.json"
        },
        "argumentdetails": {
                "period": {
                        "required": "true",
                        "description": "Update Period",
                        "help": "How often to fetch new data (in seconds). 300 seconds minimum (5 minutes) to avoid overloading the API.",
                        "type": {
                                "fieldtype": "spinner",
                                "min": 300,
                                "max": 3000,
                                "step": 60
                        }
                }
        },
        "changelog": {
                "v1.0.0": [
                        {
                                "author": "Jim Cauthen",
                                "authorurl": "https://github.com/jcauthen78/",
                                "changes": "Initial Release"
                        }
                ],
                "v1.0.1": [
                        {
                                "author": "Alex Greenland",
                                "authorurl": "https://github.com/allskyteam",
                                "changes": "Updates for new module system"
                        }
                ],
                "v1.0.2": [
                        {
                                "author": "Jim Cauthen",
                                "authorurl": "https://github.com/jcauthen78/",
                                "changes": "Fixed NOAA API format handling (list-of-lists vs list-of-dicts), added per-endpoint error handling and HTTP status checks"
                        }
                ]     
        }
}

class ALLSKYSPACEWEATHER:

        def __init__(self, params, event):
                self.params = params
                self.event = event
   

        def get_param(self, param, default, target_type=str, use_default_if_blank=False):
                result = default
                try:
                        result = self.params[param]
                except (ValueError, KeyError):
                        pass

                try:
                        result = target_type(result)
                except (ValueError, TypeError):
                        result = default

                return result
 
        # ---------------------------------------------------------------------------
        # Helper: extract a value from a NOAA API record that may be either a list
        # (old format: [time_tag, val1, val2, ...]) or a dict (new format:
        # {"time_tag": "...", "Kp": "...", ...}).
        # ---------------------------------------------------------------------------
        def _get_record_value(self, record, index_or_key, key_name=None):
                        """
                        Retrieve a value from a NOAA API record.

                        Handles both formats:
                                - list-of-lists:  record[index_or_key]
                                - list-of-dicts:  record[key_name]  (falls back to index_or_key if key_name is None)

                        Args:
                                        record:       A single data row (list or dict)
                                        index_or_key: Integer index for list format, or string key for dict format
                                        key_name:     Explicit dict key to use when record is a dict. If None,
                                                                                                index_or_key is used directly (works when it's a string).
                        Returns:
                                        The raw value (usually a string) from the record.
                        """
                        if isinstance(record, dict):
                                        # Dict format – use the explicit key name if provided
                                        k = key_name if key_name is not None else index_or_key
                                        return record[k]
                        else:
                                        # List format – use the integer index
                                        return record[index_or_key]

        def _safe_float_conversion(self, data, default='xxx'):
                        """Safely convert string to float with default value"""
                        try:
                                        return float(data)
                        except (TypeError, ValueError):
                                        return default

        def _fetch_json(self, url, label=""):
                        """
                        Fetch JSON from a NOAA SWPC endpoint with HTTP status checking.

                        Args:
                                        url:   The API URL
                                        label: Human-readable label for log messages
                        Returns:
                                        Parsed JSON data (list or dict), or None on failure.
                        """
                        response = requests.get(url, timeout=30)
                        if response.status_code != 200:
                                        s.log(0, f"ERROR: {label} API returned HTTP {response.status_code}")
                                        return None
                        try:
                                        data = json.loads(response.content)
                        except json.JSONDecodeError as e:
                                        s.log(0, f"ERROR: {label} API returned invalid JSON: {e}")
                                        return None
                        # Sanity check: must be a non-empty list
                        if not isinstance(data, list) or len(data) < 2:
                                        s.log(0, f"ERROR: {label} API returned unexpected data structure")
                                        return None
                        return data

        def _record_age_seconds(self, record):
                        """
                        Age of a record's time_tag in seconds, or None if it cannot be parsed.

                        The rtsw/ time_tag is naive UTC and sometimes carries fractional
                        seconds ("2026-08-31T11:08:06" or "...:06.123"), so only the first
                        19 characters are parsed.
                        """
                        try:
                                        tag = datetime.datetime.strptime(record["time_tag"][:19], "%Y-%m-%dT%H:%M:%S")
                        except (KeyError, TypeError, ValueError):
                                        return None
                        now = datetime.datetime.now(tz=pytz.UTC).replace(tzinfo=None)
                        return (now - tag).total_seconds()

        def _select_rtsw_record(self, data, label=""):
                        """
                        Select the newest operational record from a NOAA RTSW product.

                        The json/rtsw/ files that replaced the retired products/solar-wind/
                        feeds differ from them in two ways that positional indexing cannot
                        survive:

                          * they are ordered NEWEST FIRST over a rolling 24 hour window, so
                                data[-1] is the OLDEST record in the file, about 24 hours stale,
                                and
                          * records from three spacecraft (SOLAR1, IMAP and ACE) interleave
                                in one file, each carrying a boolean "active", so no fixed
                                position identifies the operational one. data[0] is frequently
                                an inactive IMAP or ACE record.

                        So select explicitly: filter on active, then take the highest
                        time_tag.

                        Args:
                                        data:  Parsed rtsw/ payload, or None if the fetch failed.
                                        label: Human-readable label for log messages.
                        Returns:
                                        The newest active record (dict), or None if there is none.
                        """
                        if data is None:
                                        return None

                        active = [record for record in data
                                        if isinstance(record, dict) and record.get("active") and record.get("time_tag")]
                        if not active:
                                        s.log(0, f"ERROR: {label} API returned no active spacecraft records")
                                        return None

                        newest = max(active, key=lambda record: record["time_tag"])
                        age = self._record_age_seconds(newest)
                        if age is None or age > RTSW_MAX_AGE_SECONDS:
                                        s.log(1, f"WARNING: {label} newest active record is not current "
                                                        f"({newest.get('time_tag')} from {newest.get('source')})")
                        return newest

        def _process_solar_wind_data(self, record):
                        """Process one solar wind record and return formatted values with colors"""
                        # --- The record is already selected; _get_record_value reads its fields ---
                        last = record
                        density = self._safe_float_conversion(self._get_record_value(last, 1, "proton_density"))
                        speed = self._safe_float_conversion(self._get_record_value(last, 2, "proton_speed"))
                        temp = self._safe_float_conversion(self._get_record_value(last, 3, "proton_temperature"))
                        temp_fmt = format(temp, ',').rstrip('0').rstrip('.') if temp != 'xxx' else temp


                        # Color determination logic
                        density_color = "#10e310"  # default green
                        if isinstance(density, float):
                                        if density > 6:
                                                        density_color = "#10e310"  # green
                                        elif 2 <= density <= 6:
                                                        density_color = "#ffec00"  # yellow
                                        else:
                                                        density_color = "#f56b6b"  # red

                        speed_color = "#10e310"  # default green
                        if isinstance(speed, float):
                                        if speed > 550:
                                                        speed_color = "#f56b6b"  # red
                                        elif 500 <= speed <= 550:
                                                        speed_color = "#ffec00"  # yellow
                                        else:
                                                        speed_color = "#10e310"  # green

                        temp_color = "#808080"  # default gray
                        if isinstance(temp, float):
                                        if temp >= 500001:
                                                        temp_color = "#f56b6b"  # red
                                        elif temp >= 300001:
                                                        temp_color = "#ffec00"  # yellow
                                        elif temp >= 100001:
                                                        temp_color = "#10e310"  # green
                                        elif temp >= 50000:
                                                        temp_color = "#ffec00"  # yellow
                                        else:
                                                        temp_color = "#f56b6b"  # red

                        return {
                                        "speed": {"value": speed, "color": speed_color},
                                        "density": {"value": density, "color": density_color},
                                        "temp": {"value": temp_fmt, "color": temp_color}
                        }


        def run(self):
                """Main entry point for the module"""
                result = ""

                # API endpoints
                urls = {
                                "wind": "https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json",
                                "kp": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                                "bz": "https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json"
                }

                try:
                        # Get period from params, enforce minimum of 300 seconds
                        period = self.get_param('period', 300, int)
                        module = metaData['module']

                        shouldRun, diff = s.shouldRun(module, period)
                        if shouldRun:
                                # Calculate sun angle
                                utcnow = datetime.datetime.now(tz=pytz.UTC)
                                dtUtc = utcnow.replace(microsecond=0, tzinfo=None)

                                lat = s.getSetting('latitude')
                                lat = s.convertLatLon(lat)
                                lon = s.getSetting('longitude')
                                lon = s.convertLatLon(lon)

                                obs = ephem.Observer()
                                obs.lat = lat
                                obs.long = lon
                                obs.date = dtUtc.strftime('%Y-%m-%d %H:%M:%S')

                                sun = ephem.Sun(obs)
                                sun.compute(obs)
                                sun_angle = round(float(sun.alt) * 57.2957795, 1)

                                # Initialize data dictionary
                                space_weather_data = {
                                                "SWX_S_ANGLE": {
                                                                "value": sun_angle,
                                                                "expires": 0
                                                }
                                }

                                # ---------------------------------------------------------------
                                # Fetch and process solar wind data
                                # ---------------------------------------------------------------
                                wind_data = self._fetch_json(urls["wind"], "Solar Wind")
                                wind_record = self._select_rtsw_record(wind_data, "Solar Wind")
                                if wind_record is not None:
                                                try:
                                                                solar_wind = self._process_solar_wind_data(wind_record)
                                                                space_weather_data.update({
                                                                                "SWX_SWIND_SPEED": {
                                                                                                "value": solar_wind["speed"]["value"],
                                                                                                "fill": solar_wind["speed"]["color"],
                                                                                                "expires": 0
                                                                                },
                                                                                "SWX_SWIND_DENSITY": {
                                                                                                "value": solar_wind["density"]["value"],
                                                                                                "fill": solar_wind["density"]["color"],
                                                                                                "expires": 0
                                                                                },
                                                                                "SWX_SWIND_TEMP": {
                                                                                                "value": solar_wind["temp"]["value"],
                                                                                                "fill": solar_wind["temp"]["color"],
                                                                                                "expires": 0
                                                                                }
                                                                })
                                                except Exception as e:
                                                                s.log(0, f"ERROR: Failed to process solar wind data: {e}")

                                # ---------------------------------------------------------------
                                # Fetch and process Kp index
                                # ---------------------------------------------------------------
                                kp_data = self._fetch_json(urls["kp"], "Kp Index")
                                if kp_data is not None:
                                                try:
                                                                last_kp = kp_data[-1]
                                                                # Handle both list and dict formats for Kp value
                                                                kp_value = float(self._get_record_value(last_kp, 1, "Kp"))
                                                                kp_color = "#10e310"  # default green
                                                                if kp_value > 5:
                                                                                kp_color = "#f56b6b"  # red
                                                                elif kp_value >= 4:
                                                                                kp_color = "#ffec00"  # yellow

                                                                space_weather_data["SWX_KPDATA"] = {
                                                                                "value": kp_value,
                                                                                "fill": kp_color,
                                                                                "expires": 0
                                                                }
                                                except Exception as e:
                                                                s.log(0, f"ERROR: Failed to process Kp data: {e}")

                                # ---------------------------------------------------------------
                                # Fetch and process Bz data
                                # ---------------------------------------------------------------
                                bz_data = self._fetch_json(urls["bz"], "Bz")
                                bz_record = self._select_rtsw_record(bz_data, "Bz")
                                if bz_record is not None:
                                                try:
                                                                last_bz = bz_record
                                                                # Handle both list and dict formats for Bz value
                                                                bz_value = float(self._get_record_value(last_bz, 3, "bz_gsm"))
                                                                bz_color = "#10e310"  # default green
                                                                if bz_value <= -15:
                                                                                bz_color = "#f56b6b"  # red
                                                                elif bz_value <= -6:
                                                                                bz_color = "#ffec00"  # yellow

                                                                space_weather_data["SWX_BZDATA"] = {
                                                                                "value": bz_value,
                                                                                "fill": bz_color,
                                                                                "expires": 0
                                                                }
                                                except Exception as e:
                                                                s.log(0, f"ERROR: Failed to process Bz data: {e}")

                                # Save whatever was collected. One endpoint failing must not discard
                                # the fields that succeeded, or the whole file freezes.
                                s.saveExtraData(metaData['extradatafilename'], space_weather_data)
                                result = f"Space weather data successfully written to {metaData['extradatafilename']}"
                                s.log(1, f"INFO: {result}")
                                s.setLastRun(module)

                        else:
                                        result = f"Last run {diff} seconds ago. Running every {period} seconds"
                                        s.log(1, f"INFO: {result}")

                except Exception as e:
                                eType, eObject, eTraceback = sys.exc_info()
                                result = f"Module spaceweather failed on line {eTraceback.tb_lineno} - {e}"
                                s.log(0, f"ERROR: {result}")

                return result

def spaceweather(params, event):
        allsky_space_weather = ALLSKYSPACEWEATHER(params, event)
        result = allsky_space_weather.run()
 
        return result

def spaceweather_cleanup():
        """Cleanup function for the module"""
        moduleData = {
            "metaData": ALLSKYSPACEWEATHER.meta_data,
            "cleanup": {
                "files": {
                    ALLSKYSPACEWEATHER.meta_data['extradatafilename']
                },
                "env": {}
            }
        }
        s.cleanupModule(moduleData)
