"""
Allsky S3 uploader module (SkyVault-friendly)

- Runs on 'day' and 'night' events; position before/after overlays to control source.
- Uses 'periodic' to flush a lightweight retry cache.
- S3 key layout: <prefixBase>/YYYY-MM-DD/HH/<filename>
- Dependencies: boto3 (via dependencies/allsky_s3upload/requirements.txt)
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

import allsky_shared as s

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception as e:
    s.log(4, f"ERROR: allsky_s3upload missing dependency boto3: {e}")
    raise

# NOTE: metaData must be valid Python AND JSON-parsable by the installer.
metaData = {
    "name": "S3 Upload (SkyVault)",
    "description": "Uploads images to Amazon S3 with retry cache. Place before or after overlays to control source.",
    "module": "allsky_s3upload",
    "version": "v1.0.0",
    "pythonversion": "3",
    "events": ["day", "night", "periodic"],
    "arguments": {
        "awsAccessKeyId": "",
        "awsSecretAccessKey": "",
        "awsRegion": "eu-north-1",
        "s3Bucket": "",
        "prefixBase": "allsky",
        "storageClass": "STANDARD_IA",
        "periodicFlushSeconds": "60",
        "maxAttempts": "5",
        "backoffSeconds": "1"
    },
    "argumentdetails": {
        "awsAccessKeyId": {
            "required": "true",
            "description": "AWS Access Key ID",
            "help": "Use a least-privilege IAM user scoped to your bucket/prefix.",
            "tab": "AWS",
            "type": "text"
        },
        "awsSecretAccessKey": {
            "required": "true",
            "description": "AWS Secret Access Key",
            "help": "Stored in module params; prefer a restricted IAM user.",
            "tab": "AWS",
            "type": "password"
        },
        "awsRegion": {
            "required": "true",
            "description": "AWS Region",
            "help": "e.g. eu-north-1",
            "tab": "AWS",
            "type": "text"
        },
        "s3Bucket": {
            "required": "true",
            "description": "S3 Bucket",
            "help": "Your SkyVault user bucket name.",
            "tab": "S3",
            "type": "text"
        },
        "prefixBase": {
            "required": "false",
            "description": "S3 Key Prefix Base",
            "help": "Final key: <prefixBase>/YYYY-MM-DD/HH/<filename>",
            "tab": "S3",
            "type": "text"
        },
        "storageClass": {
            "required": "false",
            "description": "Storage Class",
            "help": "STANDARD, STANDARD_IA, ONEZONE_IA, INTELLIGENT_TIERING, or GLACIER_IR.",
            "tab": "S3",
            "type": "select",
            "values": ["STANDARD", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER_IR"]
        },
        "periodicFlushSeconds": {
            "required": "false",
            "description": "Periodic Flush (seconds)",
            "help": "Minimum interval between periodic runs. Used to flush retry cache.",
            "tab": "Advanced",
            "type": "number",
            "min": 10,
            "max": 3600,
            "step": 10
        },
        "maxAttempts": {
            "required": "false",
            "description": "Max Attempts",
            "help": "Per-file attempts per invocation before re-queuing.",
            "tab": "Advanced",
            "type": "number",
            "min": 1,
            "max": 10,
            "step": 1
        },
        "backoffSeconds": {
            "required": "false",
            "description": "Backoff Base (seconds)",
            "help": "Exponential backoff base delay (capped).",
            "tab": "Advanced",
            "type": "number",
            "min": 1,
            "max": 10,
            "step": 1
        }
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0": [
            {
                "author": "Titan Astro S.L.",
                "authorurl": "https://titanastro.com",
                "changes": [
                    "Initial release with day/night hooks, periodic retry flush, and prefix-based key layout."
                ]
            }
        ]
    }
}

# ---------- Internal helpers ----------

MODULE_NAME = "s3upload"
CACHE_DIR = "/opt/allsky/modules/cache/allsky_s3upload"
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_now_parts():
    now = datetime.now(timezone.utc)  # UTC for stable partitioning
    yyyy_mm_dd = now.strftime("%Y-%m-%d")
    hh = now.strftime("%H")
    return yyyy_mm_dd, hh

def _build_s3_key(prefix_base, filename):
    date_part, hour_part = _get_now_parts()
    prefix_base = (prefix_base or "").strip().strip("/")
    if prefix_base:
        return f"{prefix_base}/{date_part}/{hour_part}/{filename}"
    else:
        return f"{date_part}/{hour_part}/{filename}"

def _new_s3_client(params):
    return boto3.client(
        "s3",
        region_name=(params.get("awsRegion") or "").strip(),
        aws_access_key_id=(params.get("awsAccessKeyId") or "").strip(),
        aws_secret_access_key=(params.get("awsSecretAccessKey") or "").strip(),
    )

def _backoff_sleep(base, attempt):
    try:
        base = int(base)
    except Exception:
        base = 1
    delay = base * (2 ** attempt)
    if delay > base * 8:
        delay = base * 8
    time.sleep(delay)

def _int_param(params, key, default):
    try:
        return int(str(params.get(key, default)).strip())
    except Exception:
        return int(default)

def _put_with_retries(s3, bucket, key, file_path, storage_class, max_attempts, backoff_base):
    attempt = 0
    while True:
        try:
            s3.upload_file(
                Filename=file_path,
                Bucket=bucket,
                Key=key,
                ExtraArgs={"StorageClass": storage_class}
            )
            return True
        except (BotoCoreError, ClientError) as e:
            attempt += 1
            s.log(2, f"WARNING: S3 put failed ({attempt}/{max_attempts}) for {file_path} -> s3://{bucket}/{key}: {e}")
            if attempt >= max_attempts:
                return False
            _backoff_sleep(backoff_base, attempt)

def _cache_add(file_path, key):
    rec = {"file": file_path, "key": key, "ts": int(time.time())}
    fname = f"{int(time.time()*1000)}_{os.path.basename(file_path)}.json"
    out = os.path.join(CACHE_DIR, fname)
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rec, f, separators=(",", ":"))
        s.log(1, f"INFO: queued for retry: {file_path} -> {key}")
    except Exception as e:
        s.log(3, f"ERROR: failed to write retry cache for {file_path}: {e}")

def _cache_list():
    try:
        for name in sorted(os.listdir(CACHE_DIR)):
            if name.endswith(".json"):
                yield os.path.join(CACHE_DIR, name)
    except Exception as e:
        s.log(3, f"ERROR: listing cache failed: {e}")

def _cache_flush(params):
    bucket = (params.get("s3Bucket") or "").strip()
    if not bucket:
        return "no-bucket"
    storage_class = (params.get("storageClass") or "STANDARD_IA").strip()
    max_attempts = _int_param(params, "maxAttempts", 5)
    backoff_base = _int_param(params, "backoffSeconds", 1)

    s3 = _new_s3_client(params)
    flushed = 0
    for recfile in _cache_list():
        try:
            with open(recfile, "r", encoding="utf-8") as f:
                rec = json.load(f)
            file_path = rec.get("file", "")
            key = rec.get("key", "")
            if not (file_path and key) or not os.path.exists(file_path):
                s.log(2, f"WARNING: dropping cache entry (missing file or key): {recfile}")
                os.remove(recfile)
                continue
            ok = _put_with_retries(s3, bucket, key, file_path, storage_class, max_attempts, backoff_base)
            if ok:
                os.remove(recfile)
                flushed += 1
        except Exception as e:
            s.log(2, f"WARNING: cache flush error on {recfile}: {e}")
    if flushed:
        s.log(1, f"INFO: flushed {flushed} cached upload(s)")
    return f"flushed:{flushed}"

def _make_temp_from_simage():
    """
    If s.image exists (i.e., the current processed frame in memory), write it to a
    temporary JPG and return that path. Prefer OpenCV if present; otherwise PIL.
    Returns (temp_path or None).
    """
    simg = getattr(s, "image", None)
    if simg is None:
        return None
    tmp_path = f"/tmp/s3upload_{int(time.time()*1000)}.jpg"
    # Try OpenCV first
    try:
        import cv2  # type: ignore
        # If image is grayscale, imencode still handles it; if BGR, keep as-is.
        ok, buf = cv2.imencode(".jpg", simg)
        if ok:
            with open(tmp_path, "wb") as f:
                f.write(buf.tobytes())
            return tmp_path
    except Exception as e:
        s.log(2, f"INFO: cv2 not available or failed to encode, trying PIL: {e}")
    # Try PIL as fallback
    try:
        from PIL import Image  # type: ignore
        import numpy as np
        arr = simg
        if len(arr.shape) == 3 and arr.shape[2] == 3:
            # Heuristic: many pipelines use BGR; convert to RGB for PIL
            try:
                arr = arr[:, :, ::-1]
            except Exception:
                pass
        Image.fromarray(arr).save(tmp_path, format="JPEG", quality=90)
        return tmp_path
    except Exception as e:
        s.log(2, f"INFO: PIL not available or failed to encode; will fall back to file on disk: {e}")
    return None

def _upload_current(params):
    # If we are positioned before 'Save image', the processed pixels live in s.image.
    # Try to materialize that to a temp JPG first; otherwise fall back to on-disk file.
    temp_from_mem = _make_temp_from_simage()
    delete_after = temp_from_mem is not None
    source_path = temp_from_mem
    # Always resolve the ORIGINAL capture filename to keep image-<timestamp>.<ext> in S3.
    current_path = getattr(s, "CURRENTIMAGEPATH", None)
    if current_path is None:
        # Fallback some builds expose s.fullFilename
        original_name = (getattr(s, "fullFilename", "") or "").strip()
    else:
        original_name = os.path.basename(current_path)
    if not original_name:
        # Ultimate fallback if nothing is available
        original_name = os.path.basename(source_path) if source_path else "image.jpg"

    if source_path is None:
        # No in-memory image available; upload the file on disk.
        if current_path is None:
            return "no-current"
        if not os.path.exists(current_path):
            s.log(2, f"WARNING: current image not found: {current_path}")
            return "missing-current"
        source_path = current_path

    bucket = (params.get("s3Bucket") or "").strip()
    if not bucket:
        s.log(3, "ERROR: s3Bucket is empty in module params.")
        return "no-bucket"
    prefix_base = (params.get("prefixBase") or "allsky").strip()
    storage_class = (params.get("storageClass") or "STANDARD_IA").strip()
    max_attempts = _int_param(params, "maxAttempts", 5)
    backoff_base = _int_param(params, "backoffSeconds", 1)

    # Use the original capture filename for the S3 object key.
    key = _build_s3_key(prefix_base, original_name)

    s3 = _new_s3_client(params)
    ok = _put_with_retries(s3, bucket, key, source_path, storage_class, max_attempts, backoff_base)
    if ok:
        s.log(1, f"INFO: uploaded {source_path} -> s3://{bucket}/{key}")
        # Clean up temp artifact if we wrote one
        if delete_after:
            try:
                os.remove(source_path)
            except Exception:
                pass
        return "uploaded"
    else:
        _cache_add(source_path, key)
        return "queued"

def s3upload(params, event):
    try:
        if event == "periodic":
            period = _int_param(params, "periodicFlushSeconds", 60)
            if not s.shouldRun("s3upload", period):
                return "skip-periodic"
            result = _cache_flush(params)
            s.setLastRun("s3upload")
            return result

        # For 'day' and 'night', always run when the module is enabled & ordered.
        _cache_flush(params)
        return _upload_current(params)

    except Exception as e:
        eType, eObject, eTraceback = sys.exc_info()
        result = f"ERROR: Module s3upload failed on line {getattr(eTraceback, 'tb_lineno', '?')} - {e}"
        s.log(4, result)
        return result

def s3upload_cleanup():
    moduleData = {
        "metaData": metaData,
        "cleanup": {
            "files": set(),
            "env": {}
        }
    }
    s.cleanupModule(moduleData)
