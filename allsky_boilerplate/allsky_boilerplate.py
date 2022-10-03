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
        }                                                        
    },
    "enabled": "false"            
}

def boilerplate(params, event):
    result = ""

    return result