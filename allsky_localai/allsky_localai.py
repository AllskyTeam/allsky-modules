import allsky_shared as s

from PIL import Image, ImageOps
import numpy as np
import sys
import os
import time
    
metaData = {
    "name": "Local Ai based cloud detection",
    "description": "Detects clouds using local AI modules",
    "module": "allsky_localai",
    "version": "v1.0.0",
    "events": [
        "periodic"
    ],
    "experimental": "false",
    "arguments":{
        "model_type": "keras",
        "keras_model_path": "/opt/allsky/modules/localai/keras_model.h5",
        "keras_labels_path": "/opt/allsky/modules/localai/labels.txt"
    },
    "argumentdetails": {
        "model_type" : {
            "required": "false",
            "description": "Model",
            "help": "The type of module being used",
            "tab": "Model",            
            "type": {
                "fieldtype": "select",
                "values": "Keras"
            }                
        },
        "keras_model_path" : {
            "required": "false",
            "description": "Model Path",
            "help": "Full path to the Keras module file",
            "tab": "Keras"               
        },
        "keras_labels_path" : {
            "required": "false",
            "description": "Labels Path",
            "help": "Full path to the Keras labels file",
            "tab": "Keras"               
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

def is_file_readable(filepath):
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

def model_keras(params):
    from keras.models import load_model
    import h5py

    sky_state = ''
    confidence_score = 0

    model_path = params['keras_model_path']
    label_path = params['keras_labels_path']
    
    if is_file_readable(model_path):
        if is_file_readable(label_path):
            
            np.set_printoptions(suppress=True)
            
            # https://discuss.ai.google.dev/t/cannot-load-h5-model/42465
            f = h5py.File(model_path, mode="r+")
            model_config_string = f.attrs.get('model_config')
            if model_config_string.find('"groups": 1,') != -1:
                model_config_string = model_config_string.replace('"groups": 1,', '')
                f.attrs.modify('model_config', model_config_string)
                f.flush()
                model_config_string = f.attrs.get("model_config")
                assert model_config_string.find('"groups": 1,') == -1
            f.close()
            
            start_time = time.time()
            model = load_model(model_path, compile=False)
            class_names = open(label_path, 'r').readlines()
                
            end_time = time.time()
            elapsed_time = end_time - start_time
            s.log(4, f'INFO: Model loaded in {elapsed_time:.2f} seconds')

            start_time = time.time()
            source_path = os.path.join('/home/pi/allsky/tmp/image.png')
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            #data = np.ndarray(shape=(1, 1700, 1700, 3), dtype=np.float32)
            # Replace this with the path to your image
            image = Image.open(source_path).convert('RGB')
            # resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            #size = (1700, 1700)
            image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
            # turn the image into a numpy array
            image_array = np.asarray(image)
            # Normalize the image
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            # Load the image into the array
            data[0] = normalized_image_array
            # Predicts the model
            prediction = model.predict(data)

            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]
            confidence_score = confidence_score * 100
            sky_state = class_name[2:].strip()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            s.log(4, f'INFO: Prediction took {elapsed_time:.2f} seconds')
        else:
            s.log(0, f'ERROR: the Keras label file {label_path} does not exist or is not readable')
    else:
        s.log(0, f'ERROR: the Keras module file {model_path} does not exist or is not readable')
         
    return sky_state, confidence_score
      
def localai(params, event):
    sky_state = ''
    confidence_score = 0
    result = ''
    extraData = {}
    type = params['model_type'].lower()   
        
    overall_start_time = time.time()
        
    if type == 'keras':
        sky_state, confidence_score = model_keras(params)
    
    extraData['AS_LOCALAI_SKYSTATE'] = sky_state
    extraData['AS_LOCALAI_CONFIDENCE'] = str(confidence_score)
    s.saveExtraData('allskylocalai.json',extraData)
    
    s.log(4, f'INFO: Class: {sky_state}')
    s.log(4, f'INFO: onfidence Score:: {confidence_score}')

    end_time = time.time()
    elapsed_time = end_time - overall_start_time
    result = f'{sky_state} {confidence_score:.3f} took {elapsed_time:.2f} seconds'
    s.log(4, f'INFO: Overall time {elapsed_time:.2f} seconds')
            
    return result

def localai_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskylocalai.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
