from datetime import datetime, timedelta
import os, sys, json
import allsky_shared as s

# --- NCNN backend & image utils ---
import ncnn
import numpy as np
from PIL import Image
import requests  # for first-time download and update

metaData = {
    "name": "YOLO Rain Detector",
    "description": "Detects raindrops using NCNN-converted YOLO model and updates overlay.",
    "module": "raindetector",
    "version": "v1.0.0",
    "events": ["day", "night"],
    "enabled": "false",
    "changelog": {
        "v1.0.0": [
            {
                "author": "Muchen Han",
                "authorurl": "https://github.com/MCH0202",
                "changes": "Switch to NCNN inference with identical state logic (cooldown/window/overlay)."
            }
        ]
    }
}

# ---------------- NCNN + Model paths & runtime constants ----------------
MODEL_DIR          = "/opt/allsky/modules/yolo_model"
MODEL_PARAM_PATH   = f"{MODEL_DIR}/model.ncnn.param"
MODEL_BIN_PATH     = f"{MODEL_DIR}/model.ncnn.bin"
MODEL_VERSION_PATH = f"{MODEL_DIR}/version.txt"

MODEL_PARAM_URL    = "https://github.com/MCH0202/allsky-raindetector-model/releases/download/live/model.ncnn.param"
MODEL_BIN_URL      = "https://github.com/MCH0202/allsky-raindetector-model/releases/download/live/model.ncnn.bin"
VERSION_URL        = "https://github.com/MCH0202/allsky-raindetector-model/releases/download/live/version.txt"

#NCNN loading
NCNN_PARAM      = MODEL_PARAM_PATH
NCNN_BIN        = MODEL_BIN_PATH

NCNN_IMG_SZ     = 1440
NCNN_CONF_THRES = 0.20
NCNN_IOU_THRES  = 0.50
NCNN_THREADS    = 4
USE_VULKAN      = False

# ---------------- Ensure model exists & update if a new version is available ----------------
try:
    if not os.path.isdir(MODEL_DIR):
        os.makedirs(MODEL_DIR, exist_ok=True)

    # Read local version (best-effort)
    local_ver = None
    if os.path.isfile(MODEL_VERSION_PATH):
        try:
            with open(MODEL_VERSION_PATH, "r", encoding="utf-8") as f:
                local_ver = f.read().strip()
        except Exception:
            local_ver = None

    # Fetch remote version (if fail still run with local files)
    remote_ver = None
    try:
        vr = requests.get(VERSION_URL, timeout=8)
        if vr.status_code == 200 and 0 < len(vr.text) < 64:
            remote_ver = vr.text.strip()
    except Exception:
        remote_ver = None

    # Decide if need to (re)download
    missing_files = (not os.path.isfile(MODEL_PARAM_PATH)) or (not os.path.isfile(MODEL_BIN_PATH))
    version_changed = (remote_ver is not None) and (remote_ver != local_ver)
    need_download = missing_files or version_changed

    if need_download:
        print("[NCNN] Fetching model artifacts...")

        # Download .param
        r = requests.get(MODEL_PARAM_URL, timeout=30)
        if r.status_code != 200 or len(r.content) < 100:
            raise RuntimeError(f"param download failed (code={r.status_code}, size={len(r.content)})")
        with open(MODEL_PARAM_PATH, "wb") as f:
            f.write(r.content)

        # Download .bin
        r = requests.get(MODEL_BIN_URL, timeout=60)
        if r.status_code != 200 or len(r.content) < 1000:
            raise RuntimeError(f"bin download failed (code={r.status_code}, size={len(r.content)})")
        with open(MODEL_BIN_PATH, "wb") as f:
            f.write(r.content)

        # Basic validation
        if os.path.getsize(MODEL_PARAM_PATH) < 100 or os.path.getsize(MODEL_BIN_PATH) < 1000:
            raise RuntimeError("downloaded files look invalid (too small).")

        # Persist remote version if available
        if remote_ver:
            with open(MODEL_VERSION_PATH, "w", encoding="utf-8") as f:
                f.write(remote_ver)

except Exception as e:
    print(f"[NCNN] model setup/update failed: {e}")

# ---------------- Preload NCNN model at import ----------------
_preloaded_net = None
try:
    net = ncnn.Net()
    net.opt.use_vulkan_compute = USE_VULKAN
    net.opt.num_threads = NCNN_THREADS
    r1 = net.load_param(NCNN_PARAM)
    r2 = net.load_model(NCNN_BIN)
    if r1 == 0 and r2 == 0:
        _preloaded_net = net
    else:
        print(f"[NCNN] preload failed: param_ret={r1}, model_ret={r2}, param={NCNN_PARAM}, bin={NCNN_BIN}")
        _preloaded_net = None
except Exception as e:
    print(f"[NCNN] preload exception: {e}")
    _preloaded_net = None


def raindetector(params, event):
    """
    Single entrypoint for Allsky flow.
    Loads image from s.CURRENTIMAGEPATH, runs NCNN inference,
    and updates overlay with rain detection state.
    """
    # --- Use preloaded net if available; otherwise try once more ---
    if _preloaded_net is not None:
        _net = _preloaded_net
    else:
        _net = ncnn.Net()
        _net.opt.use_vulkan_compute = USE_VULKAN
        _net.opt.num_threads = NCNN_THREADS
        r1 = _net.load_param(NCNN_PARAM)
        r2 = _net.load_model(NCNN_BIN)
        if r1 != 0 or r2 != 0:
            print(f"[NCNN] on-demand load failed: param_ret={r1}, model_ret={r2}, param={NCNN_PARAM}, bin={NCNN_BIN}")
            return

    # ---- Original constants ----
    RAIN_RESET_INTERVAL = timedelta(minutes=180)
    WINDOW_DURATION = timedelta(minutes=3)

    # ---- Status persistence path ----
    status_path = os.path.join(s.getEnvironmentVariable("ALLSKY_CONFIG"), "overlay", "extra", "yolo_status.json")

    # ---- Input image ----
    image_path = s.CURRENTIMAGEPATH
    print("CURRENT_IMAGE =", image_path)
    if not image_path or not os.path.isfile(image_path):
        print("Error: CURRENT_IMAGE not found.")
        return

    now = datetime.now()
    status = {}
    in_cooldown = False

    if os.path.exists(status_path):
        try:
            with open(status_path) as f:
                status = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read status.json - {e}")
            status = {}

    cooldown_until_str = status.get("cooldown_until")
    first_raindrop_time_str = status.get("first_raindrop_time")
    detection_history = status.get("detection_history", [])

    if cooldown_until_str:
        try:
            cooldown_until = datetime.fromisoformat(cooldown_until_str)
            if now < cooldown_until:
                in_cooldown = True
        except Exception as e:
            print(f"Warning: Failed to parse cooldown_until: {e}")

    if in_cooldown:
        # Show previously recorded first drop time during cooldown
        try:
            dt_obj = datetime.fromisoformat(first_raindrop_time_str)
            display_time = dt_obj.strftime("%d %b %Y, %H:%M")
        except Exception:
            display_time = first_raindrop_time_str or "Unknown"

        overlay_data = {
            "YOLO_RAINDROP_DETECTED": True,
            "YOLO_FIRST_RAINDROP_TIME": display_time
        }

    else:
        # ===================== NCNN INFERENCE BLOCK =====================
        # Read image
        im = Image.open(image_path).convert("RGB")
        W, H = im.size

        # Letterbox to square NCNN_IMG_SZ (keep ratio, pad 114,114,114)
        r = min(NCNN_IMG_SZ / H, NCNN_IMG_SZ / W)
        new_w, new_h = int(round(W * r)), int(round(H * r))
        resized = im.resize((new_w, new_h), Image.BILINEAR)
        pad_x = (NCNN_IMG_SZ - new_w) // 2
        pad_y = (NCNN_IMG_SZ - new_h) // 2
        canvas = Image.new("RGB", (NCNN_IMG_SZ, NCNN_IMG_SZ), (114, 114, 114))
        canvas.paste(resized, (pad_x, pad_y))
        rgb = np.array(canvas)  # HWC, uint8, RGB

        # Forward: in0 -> out0 ; normalize to [0,1]
        ex = _net.create_extractor()
        mat_in = ncnn.Mat.from_pixels(
            rgb, ncnn.Mat.PixelType.PIXEL_RGB, NCNN_IMG_SZ, NCNN_IMG_SZ
        )
        mat_in.substract_mean_normalize([0.0, 0.0, 0.0], [1/255., 1/255., 1/255.])
        if ex.input("in0", mat_in) != 0:
            print("[NCNN] ex.input failed")
            return

        out = ncnn.Mat()
        ret = ex.extract("out0", out)
        if ret != 0:
            print(f"[NCNN] ex.extract failed ret={ret}")
            return

        # Parse output: assume (5, N) or (N, 5) as [x, y, w, h, conf] for a single class
        arr = np.array(out)
        boxes_len = 0

        if arr.ndim == 2:
            if arr.shape[0] == 5:
                arr = arr.T  # -> (N, 5)
            if arr.shape[1] >= 5:
                conf = arr[:, 4]
                mask = conf > NCNN_CONF_THRES
                arr = arr[mask]
                if arr.size:
                    # xywh -> xyxy in 1440×1440
                    xywh = arr[:, :4]
                    xyxy = np.empty_like(xywh)
                    xyxy[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
                    xyxy[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
                    xyxy[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
                    xyxy[:, 3] = xywh[:, 1] + xywh[:, 3] / 2

                    # simple NMS
                    scores = conf[mask]
                    idxs = np.argsort(scores)[::-1]
                    keep = []
                    while idxs.size > 0:
                        i = idxs[0]; keep.append(i)
                        if idxs.size == 1:
                            break
                        xx1 = np.maximum(xyxy[i, 0], xyxy[idxs[1:], 0])
                        yy1 = np.maximum(xyxy[i, 1], xyxy[idxs[1:], 1])
                        xx2 = np.minimum(xyxy[i, 2], xyxy[idxs[1:], 2])
                        yy2 = np.minimum(xyxy[i, 3], xyxy[idxs[1:], 3])
                        inter = np.maximum(0, xx2-xx1) * np.maximum(0, yy2-yy1)
                        area_i = (xyxy[i, 2]-xyxy[i, 0]) * (xyxy[i, 3]-xyxy[i, 1])
                        area   = (xyxy[idxs[1:], 2]-xyxy[idxs[1:], 0]) * (xyxy[idxs[1:], 3]-xyxy[idxs[1:], 1])
                        iou = inter / (area_i + area - inter + 1e-9)
                        idxs = idxs[1:][iou < NCNN_IOU_THRES]
                    boxes_len = len(keep)

        # ===============================================================

        cutoff = now - timedelta(minutes=3)
        detection_history = [t for t in detection_history if datetime.fromisoformat(t) >= cutoff]

        if boxes_len > 0:
            detection_history.append(now.isoformat())

            if len(detection_history) >= 3:
                is_new_rain = True
                if first_raindrop_time_str:
                    try:
                        prev_time = datetime.fromisoformat(first_raindrop_time_str)
                        if (now - prev_time) < timedelta(minutes=180):
                            is_new_rain = False
                    except Exception as e:
                        print(f"Warning: Failed to parse first_raindrop_time: {e}")

                if is_new_rain:
                    first_raindrop_time_str = detection_history[0]

                cooldown_until = (now + timedelta(hours=1)).isoformat()
                display_time = datetime.fromisoformat(first_raindrop_time_str).strftime("%d %b %Y, %H:%M")

                overlay_data = {
                    "YOLO_RAINDROP_DETECTED": True,
                    "YOLO_FIRST_RAINDROP_TIME": display_time
                }

                status = {
                    "cooldown_until": cooldown_until,
                    "first_raindrop_time": first_raindrop_time_str,
                    "detection_history": detection_history
                }

                with open(status_path, "w") as f:
                    json.dump(status, f, indent=2)
            else:
                overlay_data = {
                    "YOLO_RAINDROP_DETECTED": "pending",
                    "YOLO_FIRST_RAINDROP_TIME": ""
                }
                status["detection_history"] = detection_history
                with open(status_path, "w") as f:
                    json.dump(status, f, indent=2)
        else:
            if len(detection_history) == 1:
                first_time = datetime.fromisoformat(detection_history[0])
                if now - first_time > timedelta(minutes=3):
                    detection_history = []
                    overlay_data = {
                        "YOLO_RAINDROP_DETECTED": False,
                        "YOLO_FIRST_RAINDROP_TIME": "N/A"
                    }
                else:
                    overlay_data = {
                        "YOLO_RAINDROP_DETECTED": "pending",
                        "YOLO_FIRST_RAINDROP_TIME": ""
                    }
                    status["detection_history"] = detection_history
                    with open(status_path, "w") as f:
                        json.dump(status, f, indent=2)
            else:
                overlay_data = {
                    "YOLO_RAINDROP_DETECTED": False,
                    "YOLO_FIRST_RAINDROP_TIME": "N/A"
                }

    # ---- Overlay output ----
    extraData = {
        "AS_YOLORAINDETECTED": {"value": overlay_data["YOLO_RAINDROP_DETECTED"], "expires": 7200},
        "AS_YOLOFIRSTDROP": {"value": overlay_data["YOLO_FIRST_RAINDROP_TIME"], "expires": 7200}
    }
    s.saveExtraData("yolo_rain.json", extraData)
    print("NCNN inference complete.")
