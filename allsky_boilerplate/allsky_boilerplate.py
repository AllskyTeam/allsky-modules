'''
allsky_boilerplate.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

class ALLSKYBOILERPLATE(ALLSKYMODULEBASE):

	meta_data = {
		"name": "All Sky Boilerplate",
		"description": "Example module for AllSky",
		"module": "allsky_boilerplate",
		"version": "v1.0.3",
		"centersettings": "false",
		"testable": "true",
		"group": "Boilerplate",
		"extradatafilename": "allsky_extradata.json",
		"events": [
			"day",
			"night",
			"daynight",
			"nightday",
			"periodic"
		],
		"deprecation": {
			"fromversion": "v2024.12.06_02",
			"removein": "v2024.12.06_02",
			"notes": "Example message to be displayed when deprecating a module",
			"replacedby": "allsky_power",
			"deprecated": "false"
		}, 
		"experimental": "false",
		"extradata": {
			"values": {
				"AS_BOILERPLATE_VALUE": {
					"name": "${BOILERPLATE_VALUE}",
					"format": "",
					"sample": "",
					"group": "Boilerplate",
					"description": "The ${BOILERPLATE_VALUE$} value",
					"type": "number"
				}
			}                         
		},   
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
				"required": "false",
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
			"ajaxselect": {
				"required": "false",
				"description": "Ajax Select",
				"tab": "Field Types",
				"help": "returns data from an ajax request",
				"type": {
					"fieldtype": "ajaxselect",
					"url": "includes/moduleutil.php?request=Onewire",
					"placeholder": "Select a One Wire device"
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
			"i2c": {
				"required": "false",
				"description": "I2C Address",
				"help": "Example field to select an i2c address",
				"tab": "Field Types",           
				"type": {
					"fieldtype": "i2c"
				}            
			},
			"gpio": {
				"required": "false",
				"description": "GPIO Field",
				"help": "Example help for the GPIO field",
				"tab": "Field Types 2",
				"type": {
					"fieldtype": "gpio"
				}           
			},
			"image" : {
				"required": "false",
				"description": "Image Field",
				"help": "Example help for the image field",
				"tab": "Field Types 2",            
				"type": {
					"fieldtype": "image"
				}                
			},
			"roi": {
				"required": "false",
				"description": "Region of Interest field",
				"help": "Help for the region of interest field",
				"tab": "Field Types 2",            
				"type": {
					"fieldtype": "roi"
				}            
			},
			"variable": {
				"required": "false",
				"description": "Allsky Variable",
				"help": "Allows and Allsky Variable to be selected",
				"tab": "Field Types 2",         
				"type": {
					"fieldtype": "variable",
					"selectmode": "multi"
				}                             
			},
			"position": {
				"description": "Position",
				"help": "Allows lat, lon and altitude to be selected from a map",
				"tab": "Field Types 2",
				"lat": {
					"id": "observer_lat"
				},
				"lon": {
					"id": "observer_lon"				
				},
				"height": {
					"id": "observer_height"				
				},
				"type": {
					"fieldtype": "position"
				}     
			},
			"url": {
				"required": "true",
				"tab": "Field Types 2",          
				"description": "Allows a url to be entered and then checked to see if it can be reached",
				"help": "ASelect a url",
				"type": {
					"fieldtype": "url"
				}          
			},
			"host": {
				"description": "Host",
				"help": "Allows a host and port to be entered",
				"tab": "Field Types 2",
				"url": {
					"id": "influxhost"
				},
				"port": {
					"id": "influxport"				
				},
				"type": {
					"fieldtype": "host"
				}     
			},
			"graph": {
				"required": "false",
				"tab": "Graph",
				"type": {
					"fieldtype": "graph"
				}
			},
			"filterselect" : {
				"required": "false",
				"description": "Select Filter",
				"help": "Select that controls other fields visibility, we call this filters. Try selecting 'value1' or 'value2' to see the effect.",
				"tab": "Filters",
				"type": {
					"fieldtype": "select",
					"values": "None,value1,value2"
				}                
			},			
   			"textfield1": {
				"required": "true",
				"description": "Text Field1",
				"help": "This field is always shown as it has no filters",
				"tab": "Filters"
			},
   			"textfield2": {
				"required": "true",
				"description": "Text Field 2",
				"help": "This field is shown when value1 is selected in the select filter field",
				"tab": "Filters",
				"filters": {
					"filter": "filterselect",
					"filtertype": "show",
					"values": [
						"value1"
					]
				}
			},
			"select2" : {
				"required": "false",
				"description": "Select Field",
				"help": "This field is shown when value1 is selected in the select filter field",
				"tab": "Filters",
				"type": {
					"fieldtype": "select",
					"values": "None,value1,value2,value3"
				},
				"filters": {
					"filter": "filterselect",
					"filtertype": "show",
					"values": [
						"value1"
					]
				}               
			},
			"gpio1": {
				"required": "false",
				"description": "GPIO Field",
				"help": "This field is shown when value2 is selected in the select filter field",
				"tab": "Filters",
				"type": {
					"fieldtype": "gpio"
				},
				"filters": {
					"filter": "filterselect",
					"filtertype": "show",
					"values": [
						"value2"
					]
				}              
			},
			"html": {
				"tab": "Help",
    			"source": "local",
                "html": "<h1>This help text is defined within the module</h1><blockquote>This help is hard coded into the modules config. This is ok for very short text but not good for longer. For longer text use the file option in the field</blockquote><p>Bacon ipsum dolor amet cow chislic strip steak pig pork belly chuck pork doner salami. Pig bresaola kielbasa rump. Jerky beef strip steak jowl beef ribs, kielbasa corned beef fatback cupim pork loin. Swine strip steak tongue turkey pig. Pork belly turducken boudin rump venison.</p><p>Burgdoggen beef pig ribeye, kielbasa biltong filet mignon shank turkey spare ribs ground round meatball sirloin picanha. Brisket t-bone doner, tri-tip jowl ham biltong kielbasa. Fatback chicken kevin tail prosciutto, frankfurter kielbasa capicola rump tri-tip andouille chislic swine pork loin filet mignon. T-bone ribeye spare ribs kevin, sausage turkey short loin short ribs filet mignon tri-tip bresaola. Beef ribs chislic pork, alcatra beef pig ball tip doner jowl shank kevin kielbasa meatloaf spare ribs. Ground round ham tail, flank pastrami kevin jerky.</p>",
				"type": {
					"fieldtype": "html"
				}
			},
			"html1": {
				"tab": "Help 1",
    			"source": "file",
                "file": "help.html",
				"type": {
					"fieldtype": "html"
				}
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
			],
			"v1.0.3" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": [
						"Updated for new module structure",
						"Another change"
					]
				}
			]                             
		},
		"businfo": [
			"i2c"
		]                 
	}

	def run(self):
		result = ""

		if allsky_shared.TOD == "day":
			result = "It's daytime"
			allsky_shared.log(1,f"INFO: {result}")
		elif allsky_shared.TOD == "night":
			result = "It's nighttime"
			allsky_shared.log(1,f"INFO: {result}")
		else:
			result = "I don't know if its day or night!"
			allsky_shared.log(0,f"ERROR: {result}")

		extraData = {}
		extraData["AS_BOILERPLATE_VALUE"] = result
		allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extraData, self.meta_data['module'], self.meta_data['extradata'])
		return result
  
  
def boilerplate(params, event):

	allsky_boilerplate = ALLSKYBOILERPLATE(params, event)
	result = allsky_boilerplate.run()

	return result 

def boilerplate_cleanup():
	moduleData = {
		"metaData": ALLSKYBOILERPLATE.meta_data,
		"cleanup": {
			"files": {
				ALLSKYBOILERPLATE.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)