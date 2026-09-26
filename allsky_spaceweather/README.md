# Space Weather Module

This module retrieves real-time space weather data from NOAA's Space Weather Prediction Center (SWPC) APIs and integrates it with your Allsky system. It provides data about solar wind conditions, geomagnetic activity (Kp index), and other space weather parameters useful for astronomical observation.

## Features

- Retrieves real-time space weather data including:
  - Solar wind speed, density, and temperature
  - Geomagnetic activity (Kp index)
  - Magnetic field (Bz) component
  - Solar elevation angle for your location
- Color-coded status indicators for each parameter
- Configurable update frequency
- Outputs data in JSON format for easy integration with AllSky overlays

## Configuration

The module requires the following configuration parameters:

| Parameter  | Description | Example |
|------------|-------------|----------|
| Latitude   | Your observation latitude (supports N/S suffix) | 43.61N or 43.61 |
| Longitude  | Your observation longitude (supports E/W suffix or negative values) | 116.20W or -116.20 |
| Period     | Update frequency in seconds (minimum 300) | 300 |
| Filename   | Output JSON filename | spaceweather.json |

## Output Data

The module generates a JSON file containing the following data:

```json
{
  "SWX_SWIND_SPEED": {
    "value": 425.3,
    "fill": "#10e310",
    "expires": 0
  },
  "SWX_SWIND_DENSITY": {
    "value": 5.2,
    "fill": "#ffec00",
    "expires": 0
  },
  "SWX_KPDATA": {
    "value": 3.0,
    "fill": "#10e310",
    "expires": 0
  }
  // ... additional parameters
}
```

### Color Codes

The module uses color coding to indicate parameter status:
- 🟢 Green (#10e310): Normal conditions
- 🟡 Yellow (#ffec00): Elevated activity
- 🔴 Red (#f56b6b): High activity/potential alert conditions

## Charts and Database

The solar wind speed, density and temperature, the Kp index and Bz are saved in
the Allsky database (table `allsky_spaceweather`) every time new data is fetched,
day and night, and also from the periodic flow. The module brings four charts for
the WebUI's **Charts** page, in the group **Space Weather**:

- **Kp Index** (0–9)
- **Bz (Interplanetary Magnetic Field)**
- **Solar Wind**: speed and density
- a **Kp Index** gauge (green below 4, yellow 4–5, red above 5)

To get charts without gaps, add the module to the periodic flow as well, so it
keeps fetching when no images are taken. The module's **History** tab shows the
same data.

## Parameter Thresholds

### Solar Wind Speed
- 🟢 < 500 km/s
- 🟡 500-550 km/s
- 🔴 > 550 km/s

### Solar Wind Density
- 🔴 < 2 n/cm³
- 🟡 2-6 n/cm³
- 🟢 > 6 n/cm³

### Kp Index
- 🟢 < 4
- 🟡 4-5
- 🔴 > 5

### Bz Component
- 🟢 > -6 nT
- 🟡 -6 to -15 nT
- 🔴 ≤ -15 nT

## Data Sources

This module uses the following NOAA SWPC APIs:
- Solar Wind: https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json
- Kp Index: https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json
- Magnetic Field: https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json

## Requirements

- Python 3.x
- Allsky system
- Internet connection for API access
- Required Python packages:
  - ephem
  - pytz
  - requests
  - beautifulsoup4

## Notes

- The minimum update period is set to 300 seconds to prevent overwhelming the NOAA APIs.
- Coordinate inputs are flexible and support both decimal degrees and cardinal directions.
- The module automatically handles spaces in coordinate inputs.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

[MIT License](LICENSE)

## Contributing Notes

AI assistance was used while preparing this contribution. The generated code and
documentation were reviewed and tested before submission.

## Acknowledgments

- Data provided by NOAA Space Weather Prediction Center.
- Built for the AllSky camera system (https://github.com/AllskyTeam/allsky).
