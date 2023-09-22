"""

Part of AllSkyAI. To create a custom model or find more info please visit https://www.allskyai.com
Written by Christian Kardach - The Crows Nest Astro
info@allskyai.com

"""
import allsky_shared as s

import os
from tflite_runtime.interpreter import Interpreter
from PIL import Image, ImageOps
import numpy as np
import time
import datetime
import json
import requests
from packaging import version

metaData = {
    "name": "AllSkyAI",
    "description": "Classify the current sky with ML",
    "module": "allsky_ai",
    "version": "v1.0.0",
    "events": [
        "day",
        "night"
    ],
    "experimental": "yes",
    "arguments": {
        "cameraType": "None",
        "autoUpdate": "false"
    },
    "argumentdetails": {
        "autoUpdate": {
            "required": "false",
            "description": "Auto Update",
            "help": "Auto download and update if a new model exists.",
            "tab": "Setup",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "cameraType": {
            "required": "true",
            "description": "Camera Type",
            "help": "The type of sensor that is being used.",
            "tab": "Setup",
            "type": {
                "fieldtype": "select",
                "values": "None,RGB,MONO",
                "default": "RGB"
            }
        }
    },
    "enabled": "false"
}

MODEL_PATH = os.path.join("/opt/allsky/modules", "models")


def check_versions(online_version):
    with open(os.path.join(MODEL_PATH, "version.txt")) as f:
        local_version = f.readlines()[0]

    if version.parse(local_version) < version.parse(online_version):
        return True
    else:
        return False


def download(path_mapping, do_update):
    for url, target in path_mapping.items():
        # If file already exists and we checked auto update
        if os.path.exists(target) and do_update:
            s.log(1, f"AllSkyAI: Updating {url}")
            r = requests.get(url)
            with open(target, 'wb') as f:
                f.write(r.content)

        elif not os.path.exists(target):
            s.log(1, f"AllSkyAI: Downloading {url}")
            r = requests.get(url)
            with open(target, 'wb') as f:
                f.write(r.content)


def precheck_data(camera_type, auto_update):
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH)

    rgb_mapping = {
        "https://allskyai.com/models/rgb/allskyai_rgb.txt": os.path.join(MODEL_PATH, "allskyai_rgb.txt"),
        "https://allskyai.com/models/rgb/allskyai_rgb.tflite": os.path.join(MODEL_PATH, "allskyai_rgb.tflite"),
        "https://allskyai.com/models/rgb/version.txt": os.path.join(MODEL_PATH, "version.txt")
    }

    mono_mapping = {

        "https://allskyai.com/models/grayscale/allskyai_grayscale.txt": os.path.join(MODEL_PATH,
                                                                                     "allskyai_grayscale.txt"),
        "https://allskyai.com/models/grayscale/allskyai_grayscale.tflite": os.path.join(MODEL_PATH,
                                                                                        "allskyai_grayscale.tflite"),
        "https://allskyai.com/models/grayscale/version.txt": os.path.join(MODEL_PATH, "version.txt")
    }

    do_update = False
    if camera_type == "rgb":
        if auto_update:
            r = requests.get("https://allskyai.com/models/rgb/version.txt")
            do_update = check_versions(r.content.decode())

        download(path_mapping=rgb_mapping, do_update=do_update)

    elif camera_type == "mono":
        if auto_update:
            r = requests.get("https://allskyai.com/models/grayscale/version.txt")
            do_update = check_versions(r.content.decode())
        download(path_mapping=mono_mapping, do_update=do_update)


def load_labels(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            result = [line.strip() for line in f.readlines()]
            s.log(1, f"AllSkyAI: Loaded labels: {result}")
            return result
    else:
        s.log(0, f"AllSkyAI Error: Could not locate labels file {filename}")


def get_utc_timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return int(utc_timestamp)


def load_image(img, width, height, color_mode):
    """
    Resize current image, we end up with a height of 512px, then we crop the rest to get a 512x512px image.
    For the grayscale image we need to convert it to a grayscale image since overlays can have color
    For both types we expand the array to have [batch, width, height, channels]
    """
    target_size = 2048, 512
    img = Image.fromarray(img.astype('uint8'), 'RGB')
    img.thumbnail(target_size, Image.Resampling.LANCZOS)

    if color_mode == "mono":
        img = img.convert("L")

    img = np.asarray(img)

    if color_mode == "mono":
        h, w = img.shape
    else:
        h, w, c = img.shape

    x1 = int((w / 2) - 256)
    x2 = int((w / 2) + 256)
    img = img[:, x1:x2]

    # Add batch and grayscale channel. [batch, width, height, channels]
    if color_mode == "mono":
        img = np.expand_dims(img, 0)
        img = np.expand_dims(img, 3)
    else:
        img = np.expand_dims(img, 0)

    return img


def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def set_input_tensor(interpreter, image):
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image


def classify_image(interpreter, image):
    set_input_tensor(interpreter, image)

    interpreter.invoke()
    output_details = interpreter.get_output_details()[0]
    output = np.squeeze(interpreter.get_tensor(output_details['index']))

    label_index = np.argmax(output)
    score = softmax(output)
    confidence = 100 * np.max(score)

    return label_index, confidence


def do_classification(camera_type=None):
    if camera_type == "rgb":
        model_path = os.path.join(MODEL_PATH, "allskyai_rgb.tflite")
        label_path = os.path.join(MODEL_PATH, "allskyai_rgb.txt")
    elif camera_type == "mono":
        model_path = os.path.join(MODEL_PATH, "allskyai_grayscale.tflite")
        label_path = os.path.join(MODEL_PATH, "allskyai_grayscale.txt")

    interpreter = Interpreter(model_path)
    s.log(1, "AllSkyAI: Model Loaded")

    interpreter.allocate_tensors()
    _, height, width, _ = interpreter.get_input_details()[0]['shape']
    s.log(1, f"AllSkyAI: TF Lite input shape:: {height}, {width}")
    s.log(1, f"AllSkyAI: s.image shape: {s.image.shape}")

    # Load an image to be classified.
    img_array = load_image(s.image, width=width, height=height, color_mode=camera_type)

    # Classify the image and check how long it took
    time1 = time.time()

    label_id, confidence = classify_image(interpreter, img_array)

    time2 = time.time()
    classification_time = np.round(time2 - time1, 3)
    s.log(1, f"AllSkyAI: Classificaiton Time = {classification_time} seconds.")

    # Read class labels.
    labels = load_labels(label_path)
    classification_label = labels[label_id]

    s.log(1, f"AllSkyAI: {classification_label}, Confidence: {confidence}%")

    data_json = dict()
    data_json['AI_CLASSIFICATION'] = classification_label
    data_json['AI_CONFIDENCE'] = round(confidence, 3)
    data_json['AI_UTC'] = get_utc_timestamp()
    data_json['AI_INFERENCE'] = classification_time

    return data_json


def ai(params, event):
    # Get the selected camera type, else return error message
    camera_type = params["cameraType"].lower()
    auto_update = params["autoUpdate"]

    if camera_type == "none":
        s.log(0, "ERROR: Camera type not set, check AllSkyAI settings...")
        return "AllSkyAI: Camera type not set"

    # Check if all necessary files exists, else we download the correct ones
    precheck_data(camera_type=camera_type, auto_update=auto_update)

    # Classify the image
    if s.TOD == "day":
        result = do_classification(camera_type=camera_type)

        s.saveExtraData("allskyai.json", result)
        s.log(1, f"AllSkyAI: {json.dumps(result)}")
        return "AllSkyAI sucessfully executed"

    elif s.TOD == "night":
        result = do_classification(camera_type=camera_type)

        s.saveExtraData("allskyai.json", result)
        s.log(1, f"AllSkyAI: {json.dumps(result)}")
        return "AllSkyAI sucessfully executed"

    else:
        return ""

def ai_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": {
                "allskyai.json"
            },
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
