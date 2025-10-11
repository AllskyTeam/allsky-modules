# Import JSON Data Module

|             |                      |
|-------------|----------------------|
| **Status**  | Experimental         |
| **Level**   | Beginner             |
| **Runs In** | Periodic |

This module allows for Allsky to download JSON data from a URL and convert it into variables for the overlay editor. The data format must be a single JSON object containing key/value data only.

The module contains the following options:

| Setting             | Description                                                                   |
|---------------------|-------------------------------------------------------------------------------|
| Read Every          | Read data every x seconds from the provided URL.                              |
| JSON Data URL       | The URL to retrieve the data from.                                            |
| Variable Prefix     | The prefix to add to the data. Not normally required.                         |
| Extra Data Filename | The name of the extra data filename. This should not normally be changed.     |

## Accessible Variables

Whatever the JSON URL provided !

### V.1.0.0
* Initial release
