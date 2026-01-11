import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

class ALLSKYEXAMPLE(ALLSKYMODULEBASE):

  meta_data = {
    "name": "Allsky Example Module",
    "description": "A simple example module for Allsky.",
    "module": "allsky_example",    
    "version": "v1.0.0",
    "group": "Data Capture",
    "events": [
      "periodic",
      "day",
      "night"
    ],
    "enabled": "false",    
    "experimental": "true",
    "testable": "true",  
    "centersettings": "false",
    "extradatafilename": "allsky_example.json", 
    "extradata": {
      "values": {
        "AS_EXAMPLE": {
          "name": "${EXAMPLE}",
          "format": "{dp=0|per}",
          "sample": "",                   
          "group": "User",
          "description": "My Example Value",
          "type": "number"
        },
        "AS_EXAMPLE1": {
          "name": "${EXAMPLE1}",
          "format": "{dp=2}",
          "sample": "",                   
          "group": "User",
          "description": "My Example Value 2",
          "type": "number"
        }        
      }      
    },
    "arguments":{
      "filename": ""
    },
    "argumentdetails": {
      "filename": {
        "required": "true",
        "description": "Filename",
        "help": "The location of the json file to read data from"
      }                
    },
    "businfo": [
    ],
    "changelog": {
      "v1.0.0" : [
        {
          "author": "Alex Greenland",
          "authorurl": "https://github.com/allskyteam",
          "changes": "Initial Release"
        }
      ] 
    }
  }

  def run(self):
    result = ""

    file_name = self.get_param("filename", "", str, True) 
    
    json_data = allsky_shared.load_json_file(file_name)
      
    if json_data:
      if "example" in json_data and "example1" in json_data:
        extra_data = {}
        extra_data["AS_EXAMPLE"] = json_data["example"]
        extra_data["AS_EXAMPLE1"] = json_data["example1"]
        allsky_shared.save_extra_data(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'])
        result = f"INFO: Data read from {file_name} and variable AS_EXAMPLE created"
      else:
        result = f"ERROR: The 'example' and 'example1' values are missing from the json file"
        
    else:
      result = f"ERROR: File {file_name} does not contain valid JSON."

    self.log(4, result)
    
    return result
  
def example(params, event):
        allsky_example = ALLSKYEXAMPLE(params, event)
        result = allsky_example.run()

        return result    
    
def example_cleanup():   
        moduleData = {
            "metaData": ALLSKYEXAMPLE.meta_data,
            "cleanup": {
                "files": {
                    ALLSKYEXAMPLE.meta_data['extradatafilename']
                },
                "env": {}
            }
        }
        allsky_shared.cleanupModule(moduleData)