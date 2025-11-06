import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

from PIL import Image, ImageOps
import numpy as np
import sys
import os
import time

class ALLSKYLOCALAI(ALLSKYMODULEBASE):
        
    metaData = {
        "name": "Local AI-Based Cloud Detection",
        "description": "Detect clouds using local AI modules",
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
                "help": "The type of module being used.",
                "tab": "Model",            
                "type": {
                    "fieldtype": "select",
                    "values": "Keras"
                }                
            },
            "keras_model_path" : {
                "required": "false",
                "description": "Model Path",
                "help": "Full path to the Keras module file.",
                "tab": "Keras"               
            },
            "keras_labels_path" : {
                "required": "false",
                "description": "Labels Path",
                "help": "Full path to the Keras labels file.",
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

    def is_file_readable(self, filepath):
        return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

    def model_keras(self):
        from keras.models import load_model
        import h5py

        sky_state = ''
        confidence_score = 0

        model_path = params['keras_model_path']
        label_path = params['keras_labels_path']
        
        if is_file_readable(model_path):
            if is_file_readable(label_path):
                
                np.set_printoptions(suppress=True)
                
                start_time = time.time()
                # https://discuss.ai.google.dev/t/cannot-load-h5-model/42465
                f = h5py.File(model_path, mode="r+")
                model_config_string = f.attrs.get('model_config')
                if model_config_string.find('"groups": 1,') != -1:
                    model_config_string = model_config_string.replace('"groups": 1,', '')
                    f.attrs.modify('model_config', model_config_string)
                    f.flush()
                    model_config_string = f.attrs.get('model_config')
                    assert model_config_string.find('"groups": 1,') == -1
                f.close()
                end_time = time.time()
                elapsed_time = end_time - start_time
                s.log(4, f'INFO: Model migration time {elapsed_time:.2f} seconds')
                            
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
                s.log(0, f'ERROR in {__file__}: the Keras label file {label_path} does not exist or is not readable')
        else:
            s.log(0, f'ERROR in {__file__}: the Keras module file {model_path} does not exist or is not readable')
            
        return sky_state, confidence_score
        
        def run(self):
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
            
            s.log(4, f'INFO: Class: {sky_state}.  Confidence Score: {confidence_score}')

            end_time = time.time()
            elapsed_time = end_time - overall_start_time
            result = f'{sky_state} {confidence_score:.3f} took {elapsed_time:.2f} seconds'
            s.log(4, f'INFO: Overall time {elapsed_time:.2f} seconds')
                    
            return result

def localai(params, event):
	allsky_local_ai = ALLSKYLOCALAI(params, event)
	result = allsky_local_ai.run()
 
	return result

def localai_cleanup():
    moduleData = {
        "metaData": ALLSKYLOCALAI.metaData,
        "cleanup": {
            "files": {
                "allskylocalai.json"
            },
            "env": {}
        }
    }
    allsky_shared.cleanupModule(moduleData)
    
    
'''
import tensorflow as tf
from tensorflow.keras import layers, models
from pathlib import Path

# Parameters
image_size = (128, 128)
batch_size = 32
dataset_path = "dataset"  # change this to your actual path

# Load and split the dataset
train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    dataset_path,
    image_size=image_size,
    batch_size=batch_size,
    validation_split=0.2,
    subset="training",
    seed=123
)

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    dataset_path,
    image_size=image_size,
    batch_size=batch_size,
    validation_split=0.2,
    subset="validation",
    seed=123
)

# Cache & prefetch for performance
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# Build model
num_classes = len(train_ds.class_names)
model = models.Sequential([
    layers.Rescaling(1./255, input_shape=(128, 128, 3)),
    layers.Conv2D(16, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(32, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(num_classes)
])

model.compile(
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

# Train model
model.fit(train_ds, validation_data=val_ds, epochs=10)

# Save model
model.save("cloud_classifier_model")
'''

'''
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

# Load model
model = tf.keras.models.load_model("cloud_classifier_model")

# Load class names from training set (optional: hardcode if you prefer)
class_names = ['clear', 'partially_cloudy', 'cloudy', 'raining']

def classify_image(img_path):
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # make batch of 1

    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])
    label = class_names[np.argmax(score)]
    confidence = 100 * np.max(score)

    print(f"{img_path} classified as {label} ({confidence:.2f}%)")

# Example usage
classify_image("test_images/example.jpg")
'''
