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
import datetime
import json
import requests
import time


# Disable Numpy warnings
np.seterr(all="ignore")

metaData = {
    "name": "AllSkyAI",
    "description": "Classify the current sky with ML. More info https://www.allskyai.com",
    "module": "allsky_ai",
    "version": "v1.0.5",
    "events": [
        "day",
        "night"
    ],
    "experimental": "yes",
    "arguments": {
        "camera_type": "None",
        "auto_update": "False",
        "contribute": "False",
        "use_account": "False",
        "account_auto_update": "False",
        "allsky_id": "",
        "access_token": "",
        "disable_upload": "False",
        "upload_frequency": "600"
    },
    "argumentdetails": {
        "auto_update": {
            "required": "false",
            "description": "Auto Update",
            "help": "Auto download and update if a new model exists.",
            "tab": "Setup",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "camera_type": {
            "required": "true",
            "description": "Camera Type",
            "help": "The type of sensor that is being used.",
            "tab": "Setup",
            "type": {
                "fieldtype": "select",
                "values": "None,RGB,MONO",
                "default": "RGB"
            }
        },
        "contribute": {
            "required": "false",
            "description": "Contribute",
            "help": "Contribute by uploading an image every 10th minute. This will be used to build a better generic model for everyone! * Only applicable unless you have an account",
            "tab": "Contribute",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "use_account": {
            "required": "false",
            "description": "Use AllSkyAI Account",
            "help": "If you have an AllSkyAI account you can enter details and uploaded images will be registred to your account",
            "tab": "AllSkyAI",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "account_auto_update": {
            "required": "false",
            "description": "Auto Update Model",
            "help": "",
            "tab": "AllSkyAI",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "allsky_id": {
            "required": "false",
            "description": "AllSkyAI ID",
            "help": "AllSkyAI ID if you have a registered AllSkyAI account.",
            "tab": "AllSkyAI"
        },
        "access_token": {
            "required": "false",
            "description": "Access Code",
            "help": "Access code, also found on AllSkyAI website",
            "tab": "AllSkyAI"
        },
        "disable_upload": {
            "required": "false",
            "description": "Disable Upload",
            "help": "Will turn upload off",
            "tab": "AllSkyAI",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "upload_frequency" : {
            "required": "true",
            "description": "Upload Frequency",
            "help": "How often should an image be uploaded",
            "tab": "AllSkyAI",
            "type": {
                "fieldtype": "spinner",
                "min": 10,
                "max": 6000,
                "step": 1
            }          
        }
    },
    "enabled": "false"
}

MODEL_PATH = "/opt/allsky/modules/models"
API = "https://www.allskyai.com/api/v1/allsky"
DEBUG = False


# -------------------------------------------------------------------------------------
# Inference
# -------------------------------------------------------------------------------------

def get_utc_timestamp():
    dt = datetime.datetime.now(datetime.timezone.utc)
    utc_time = dt.replace(tzinfo=datetime.timezone.utc)
    utc_timestamp = utc_time.timestamp()
    return int(utc_timestamp)


def load_labels(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            result = [line.strip() for line in f.readlines()]
            s.log(1, f"AllSkyAI: Loaded labels: {result}")
            return result
    else:
        s.log(0, f"AllSkyAI Error: Could not locate labels file {filename}")


def load_image(width, height, color_mode):
    """
    Resize current image, so we end up with a height of 512px, then we crop the rest to get a 512x512px image.
    For the grayscale image we need to convert it to a grayscale image since overlays can have color
    For both types we expand the array to have [batch, width, height, channels]
    PIL image defined as [with, height]
    Numpy shape defined as [height, width]
    """
    rgb = s.image[..., ::-1].copy()
    img = Image.fromarray(rgb)
    if width == height:
        target_size = 2048, 512
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
    else:
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    w, h = img.size
    if DEBUG:
        s.log(0, f"AllSkyAI: Rezied image - w:{w}, h:{h}")

    if color_mode == "mono":
        img = img.convert("L")

    img = np.asarray(img)
    if DEBUG:
        s.log(0, f"AllSkyAI: Numpy image = {img.shape}")

    if width == height:
        x1 = int((w / 2) - 256)
        x2 = int((w / 2) + 256)
        img = img[:, x1:x2]

    if DEBUG:
        save_img = Image.fromarray(img.astype('uint8'), 'RGB')
        save_img.save(os.path.join(MODEL_PATH, "test_out.jpg"))

    img = np.asarray(img, dtype=np.float32)

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
    model_path = os.path.join(MODEL_PATH, "allskyai.tflite")
    label_path = os.path.join(MODEL_PATH, "allskyai.txt")

    # Result dict, if this did not run an empty dict will be returned
    data_json = dict()

    if not os.path.exists(model_path) or not os.path.exists(label_path):
        s.log(1, "Could not run inference, model or label file does not exists")
        return data_json

    interpreter = Interpreter(model_path)
    s.log(1, "AllSkyAI: Model Loaded")

    interpreter.allocate_tensors()
    _, height, width, _ = interpreter.get_input_details()[0]['shape']
    s.log(1, f"AllSkyAI: TF Lite input shape: {height}, {width}")

    # Load an image to be classified.
    img_array = load_image(width=width, height=height, color_mode=camera_type)

    # Classify the image.
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

def empty_json():
    data_json = dict()
    data_json['AI_CLASSIFICATION'] = "None"
    data_json['AI_CONFIDENCE'] = 0.00
    data_json['AI_UTC'] = "None"
    data_json['AI_INFERENCE'] = 0.00
    
    return data_json
# -------------------------------------------------------------------------------------
# API Functions
# -------------------------------------------------------------------------------------

def check_versions(server_version):

    # V1.0 had a version file with single line content of v.1.0.0
    # if we can't parse the data then treat it as invalid and try to download it again
    with open(os.path.join(MODEL_PATH, "version.txt")) as f:
        try:
            local_version = int(f.readlines()[0])
        except:
            s.log(1, f"AllSkyAI: Invalid version file, trying to download again")
            return True

    # Check if we can convert timestamp to datetime, else we return with an error message
    server_version = int(server_version)
    try:
        local_version = datetime.datetime.fromtimestamp(local_version / 1000.0)
        s.log(1, f"AllSkyAI: Local Version - {local_version}")
    except:
        s.log(1, f"AllSkyAI Error: Could not convert local model version")
        return False

    try:
        server_version = datetime.datetime.fromtimestamp(server_version / 1000.0)
        s.log(1, f"AllSkyAI: Server Version - {server_version}")
    except:
        s.log(1, f"AllSkyAI Error: Could not convert server model version")
        return False

    if server_version > local_version:
        return True
    else:
        return False


def upload_image(allsky_id, access_token):
    target_size = 3096, 1024
    tmp_path = os.path.join(MODEL_PATH, "tmp.jpg")

    # Convert BRG to RGB
    rgb = s.image[..., ::-1].copy()
    img = Image.fromarray(rgb)
    img.thumbnail(target_size, Image.Resampling.LANCZOS)
    img.save(os.path.join(MODEL_PATH, "tmp.jpg"))

    url = API + '/upload'
    headers = {"AllSkyAI-Id": allsky_id, "AllSkyAI-Access-Token": access_token}
    with open(tmp_path, 'rb') as img:
        name_img = os.path.basename(tmp_path)
        files = {'image': (name_img, img, 'image/jpg')}
        with requests.Session() as sess:
            r = sess.post(url, files=files, headers=headers)
            if r.status_code == 200:
                s.log(1, "AllSkyAI: Uploaded image to AllSkyAI")
            else:
                s.log(1, "AllSkyAI: Could not upload image to AllSkyAI")


def download_general_model(camera_type):
    mapping = {
        API + "/getGeneralLabels?cameraType=" + camera_type: os.path.join(MODEL_PATH, "allskyai.txt"),
        API + "/getGeneralModel?cameraType=" + camera_type: os.path.join(MODEL_PATH, "allskyai.tflite"),
        API + "/getGeneralModelVersion?cameraType=" + camera_type: os.path.join(MODEL_PATH, "version.txt")
    }

    for url, target in mapping.items():
        try:
            s.log(1, f"AllSkyAI: Downloading {url}")
            r = requests.get(url)
            if r.status_code == 200:
                with open(target, 'wb') as f:
                    f.write(r.content)
            else:
                s.log(0, f"AllSkyAI Error: {r.content}")
        except:
            s.log(0, f"AllSkyAI download error")


def download_user_model(allsky_id, access_token):
    mapping = {
        API + "/getUserLabels?allsky_id=" + allsky_id + "&access_token=" + access_token: os.path.join(MODEL_PATH,
                                                                                                      "allskyai.txt"),
        API + "/getUserModel?allsky_id=" + allsky_id + "&access_token=" + access_token: os.path.join(MODEL_PATH,
                                                                                                     "allskyai.tflite"),
        API + "/getUserVersion?allsky_id=" + allsky_id + "&access_token=" + access_token: os.path.join(MODEL_PATH,
                                                                                                       "version.txt")
    }

    for url, target in mapping.items():
        try:
            s.log(1, f"AllSkyAI: Downloading {url}")
            r = requests.get(url)
            if r.status_code == 200:
                with open(target, 'wb') as f:
                    f.write(r.content)
            else:
                s.log(0, f"AllSkyAI Error: {r.content.decode()}")
        except:
            s.log(0, f"AllSkyAI: Download error")


def general_model_precheck(camera_type, auto_update):
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH)

    # If version file doesn't exist, download all files
    if not os.path.exists(os.path.join(MODEL_PATH, "version.txt")):
        s.log(1, f"AllSkyAI: Downloading general model for {camera_type}")
        download_general_model(camera_type=camera_type)
        return

    if auto_update:
        r = requests.get(API + "/getGeneralModelVersion?cameraType=" + camera_type)
        update = check_versions(r.content.decode())
        if update:
            download_general_model(camera_type=camera_type)


def user_account_precheck(camera_type, account_auto_update, allsky_id, access_token):
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_PATH)

    # If version file doesn't exist, download all files
    if not os.path.exists(os.path.join(MODEL_PATH, "version.txt")):
        s.log(1, f"AllSkyAI: Downloading model for {allsky_id}")
        download_user_model(allsky_id=allsky_id, access_token=access_token)
        return

    if account_auto_update:
        r = requests.get(API + "/getUserVersion?allsky_id=" + allsky_id + "&accessToken=" + access_token)
        update = check_versions(r.content.decode())
        if update:
            download_user_model(allsky_id=allsky_id, access_token=access_token)


# -------------------------------------------------------------------------------------

def current_milli_time():
    return round(time.time() * 1000)


def check_time_elapsed(allsky_id, access_token, upload_frequency, disable_upload):
    if disable_upload:
        s.log(1, f"AllSkyAI - Upload disabled")
        return

    elif time.time() - (s.dbGet("allskyai_last_publish") / 1000) > upload_frequency:
        s.log(1, f"AllSkyAI - Uploading image")
        upload_image(allsky_id, access_token)
        s.dbUpdate("allskyai_last_publish", current_milli_time())

# -------------------------------------------------------------------------------------

def run(camera_type,
        contribute,
        auto_update,
        use_account,
        account_auto_update,
        allsky_id,
        access_token,
        disable_upload,
        upload_frequency
        ):
    if use_account:
        s.log(1, "Using AllSkyAI account")
        if not allsky_id:
            return "No AllSkyAI ID supplied"

        if not access_token:
            return "No AllSkyAI Access Token supplied"

        user_account_precheck(camera_type=camera_type, account_auto_update=account_auto_update, allsky_id=allsky_id,
                              access_token=access_token)

    else:
        general_model_precheck(camera_type=camera_type, auto_update=auto_update)

    # Run prediction
    result = do_classification(camera_type=camera_type)

    if bool(result):
        s.saveExtraData("allskyai.json", result)
        s.log(1, f"AllSkyAI: {json.dumps(result)}")
    else:
        result = empty_json()
        s.saveExtraData("allskyai.json", result)
        s.log(1, f"AllSkyAI: {json.dumps(result)}")

    # Check elapsed time. We will only upload an image every 10 minutes
    if use_account:
        if not s.dbHasKey("allskyai_last_publish"):
            s.dbAdd("allskyai_last_publish", current_milli_time())
        else:
            check_time_elapsed(allsky_id=allsky_id, access_token=access_token, upload_frequency=upload_frequency, disable_upload=disable_upload)

    elif contribute:
        if not s.dbHasKey("allskyai_last_publish"):
            s.dbAdd("allskyai_last_publish", current_milli_time())
        else:
            check_time_elapsed(allsky_id=allsky_id, access_token=access_token, upload_frequency=600, disable_upload=False)


# -------------------------------------------------------------------------------------

def ai(params, event):
    # Get the selected camera type, else return error message
    camera_type = params["camera_type"].lower()
    contribute = params["contribute"]
    auto_update = params["auto_update"]
    use_account = params["use_account"]
    account_auto_update = params["account_auto_update"]
    allsky_id = params["allsky_id"]
    access_token = params["access_token"]
    disable_upload = params["disable_upload"]
    upload_frequency = int(params["upload_frequency"])

    if camera_type == "none":
        s.log(0, "ERROR: Camera type not set, check AllSkyAI settings...")
        return "AllSkyAI: Camera type not set"

    result = ""
    if s.TOD == "day":
        run(camera_type=camera_type,
            contribute=contribute,
            auto_update=auto_update,
            use_account=use_account,
            account_auto_update=account_auto_update,
            allsky_id=allsky_id,
            access_token=access_token,
            disable_upload=disable_upload,
            upload_frequency=upload_frequency
            )
    elif s.TOD == "night":
        run(camera_type=camera_type,
            contribute=contribute,
            auto_update=auto_update,
            use_account=use_account,
            account_auto_update=account_auto_update,
            allsky_id=allsky_id,
            access_token=access_token,
            disable_upload=disable_upload,
            upload_frequency=upload_frequency
            )

    return "AllSkyAI executed!"


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
