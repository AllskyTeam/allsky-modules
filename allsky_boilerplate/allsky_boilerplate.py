'''
allsky_boilerplate.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


'''
import allsky_shared as s

metaData = {
    "name": "All Sky Boilerplate",
    "description": "Example module for AllSky",
    "module": "allsky_boilerplate",
    "version": "v1.0.0",    
    "events": [
        "day",
        "night",
        "endofnight",
        "daynight",
        "nightday",
        "periodic"
    ],
    "experimental": "false",    
    "arguments":{
        "textfield": "",
        "select": "value1",
        "checkbox": "",        
        "number": "10",
        "gpio": "",
        "image": "",
        "roi": ""
    },
    "argumentdetails": {
        "textfield": {
            "required": "true",
            "description": "Text Field",
            "help": "Example help for the text field",
            "tab": "Field Types"
        },  
        "select" : {
            "required": "false",
            "description": "Select Field",
            "help": "Example help for a select field",
            "tab": "Field Types",
            "type": {
                "fieldtype": "select",
                "values": "None,value1,value2,value3"
            }                
        },
        "checkbox" : {
            "required": "false",
            "description": "Checkbox Field",
            "help": "Example help for the checkbox field",
            "tab": "Field Types",
            "type": {
                "fieldtype": "checkbox"
            }          
        },        
        "number" : {
            "required": "true",
            "description": "Number Field",
            "help": "Example help for the number field",
            "tab": "Field Types",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 1000,
                "step": 1
            }          
        },
        "gpio": {
            "required": "true",
            "description": "GPIO Field",
            "help": "Example help for the GPIO field",
            "tab": "Field Types",
            "type": {
                "fieldtype": "gpio"
            }           
        },
        "image" : {
            "required": "false",
            "description": "Image Field",
            "help": "Example help for the image field",
            "tab": "Field Types",            
            "type": {
                "fieldtype": "image"
            }                
        },
        "roi": {
            "required": "true",
            "description": "Region of Interest field",
            "help": "Help for the region of interest field",
            "tab": "Field Types",            
            "type": {
                "fieldtype": "roi"
            }            
        },
        "textfield1": {
            "required": "true",
            "description": "Text Field1",
            "help": "Example help for the text field in a new tab",
            "tab": "Another Tab"
        }                                                              
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/Mr-Groch",
                "changes": [
                    "Change 1",
                    "Change 2"
                ]
            }
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Change 1",
                    "Change 2"
                ]
            },            
            {
                "author": "Andreas Schminder",
                "authorurl": "https://github.com/Adler6907",
                "changes": "Change 1"
            }
        ]                                
    },
    "businfo": [
        "i2c"
    ],
    "changelog": {
        "v1.0.0" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Change 1",
                    "Change 2",
                    "Change 3"
                ]
            }
        ],
        "v1.0.2" : [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Change 1"
            },            
            {
                "author": "JOhn Doe",
                "authorurl": "https://github.com/allskyteam",
                "changes": [
                    "Change 1",
                    "Change 2",
                    "Change 3"
                ]
            }
        ]                                       
    }                   
}

def boilerplate(params, event):
    ''' Main entry point for the module, this is called by the processing engine. The function
    must have the same name as the module minus the extension and allsky_ i.e.

    allsky_boilerplate.py requires a function called boilerplate

    Two parameters are passed to the function
    params - A list of all parameters, as defined by the 'arguments' entry in the meta data
    event - The event for which the module is being called for i.e. day, night, endofnight etc

    The module must return a string with some text to indicate the result of the function. This text
    is displayed in the module managers debug dialog. This text can be an emptry string but please
    consider making it more meaningful.

    Notes on Modules

    - They Must be fast if run during the day or night events. DO NOT do any long processing in these
      events as it will affect the capture process
    - Consider carefully which events the module should run in. DO NOT just add every event to the module
      as this will confuse the user
    - Provide a requirements.txt file with any Python dependencies. The generic module installer will
      detect this file and install the dependencies
    - Make use if the functions provided in the shared library rather that writing you own. See the main
      documentation for details of the functions available

    Values available from the shared module

    s.args - The arguments passed to the module processor (not normally needed)
    s.LOGLEVEL - The allsky debug level (not normally ndded)
    s.CURRENTIMAGEPATH - The full path to the current image (not normally needed, not available in periodic)
    s.TOD - The time of day (Not available in periodic)
    s.fullFilename - The final image filename i.e. image.jpg (not normally needed, not available in periodic)
    s.image - a numpy array of the current image - Use this for any processing

    Methods available in the shared module

    s.log(level, message) - Logs an entry to the allsky log file if the debug level is above 'level'. Errors are always logged
    s.getEnvironmentVariable(name, fatal=False, error='') - Gets an environment variable, can terminate if ndded
    s.var_dump(variable) - Pretty dump of a variable
    s.getSetting(settingName) - Gets a setting from the camera settings file
    s.writeDebugImage(module, fileName, image) - Writes a debug image    
    s.startModuleDebug(module) - Creates the debug directories for a module
    s.convertPath(path) - Replaces allsky variables in a string
    s.checkAndCreatePath(filePath) - Creates a path for a file
    s.checkAndCreateDirectory(filePath) - Creates a directory
    s.raining() - Only available if the rain module is being used - Returns flags to indicate the rain state
    s.convertLatLon(input) - Converts 52.2N to 52.2 i.e converts to decimal 
    s.setLastRun(module) - Sets the last run time for a module
    s.shouldRun(module, period) - Determines if a module should run based on the period
    s.dbAdd(key, value) - Adds the key/value pair to the internal database
    s.dbUpdate(key, value) - Updates the key/value pair to the internal database
    s.isFileWriteable(fileName) - Determines of the file is writeable
    s.isFileReadable - Determines if the file is readable
    
    See the Allsky documentation for the most uptodate list of avaiable function
    '''

    result = ""

    if s.TOD == "day":
        result = "It's daytime"
        s.log(1,f"INFO: {result}")
    elif s.TOD == "night":
        result = "It's nighttime"
        s.log(1,f"INFO: {result}")
    else:
        result = "I don't know if its day or night!"
        s.log(0,f"ERROR: {result}")

    return result

def boilerplate_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyboiler.json"
            },
            "env": {
                "ALLSKY_BOILERPLATE"
            }
        }
    }
    s.cleanupModule(moduleData)