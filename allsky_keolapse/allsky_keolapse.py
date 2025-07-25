'''
allsky_keolapse.py
Part of allsky postprocess.py modules.
Creates timelapse video with keogram overlay
Inspired by Indi Allsky's keogram timelapse feature. https://github.com/aaronwmorris/indi-allsky
ERIC COMMENTS:
    * log_file will grow without bounds until a reboot. Possible re-create every time a keolapse is created?
      Or better yet, put in the standard allsky log.
    * Use s.LOGLEVEL:
            0 is ERROR - no keolapse will be created
            1 is WARNING - usually means a keolapse WILL be created but may not be ideal
            2 isn't used much
            3 typically to
            4 is debug mode
      0 will also put message in WebUI's "System Messages".
'''
import allsky_shared as s
import os
import cv2
import numpy as np
from datetime import datetime, timedelta
import glob
import shutil
import subprocess

# Use environment variables from allsky_shared for paths
ALLSKY_IMAGES = s.getEnvironmentVariable("ALLSKY_IMAGES", fatal=True)
base_dir = s.getSetting("imagepath") or ALLSKY_IMAGES
ALLSKY_CONFIG = s.getEnvironmentVariable("ALLSKY_CONFIG", fatal=True)
ALLSKY_TMP = s.ALLSKY_TMP
LOG_DIR = os.path.join(ALLSKY_TMP, "logs")
log_file = os.path.join(LOG_DIR, "keolapse_debug.log")
this_module = "allsky_keolapse"

# These globals are set in keolapse()
debug_mode = False
use_timelapse_settings = False
testing_enabled = False
show_circles_only = False

metaData = {
    "note": "metaData structure must remain in this format. DO NOT reformat",
    "name": "Keolapse Generator",
    "description": "Creates timelapse video with keogram ring overlay",
    "version": "v0.8.5",
    "module": "allsky_keolapse",
    "events": [
        "nightday",
        "periodic"
    ],
    "experimental": "true",
    "enabled": "true",
    "arguments": {
        "use_timelapse_settings": "false",
        "video_quality": "medium",
        "framerate": "12",
        "max_length": "120",
        "circle_radius_factor": "0.47",
        "center_x_offset": "0",
        "center_y_offset": "0",
        "keogram_height": "175",
        "resolution": "720p",
        "top_padding": "5",
        "bottom_padding": "5",
        "left_padding": "5",
        "right_padding": "5",
        "circle_padding": "5",
        "edge_padding": "5",
        "enable_testing": "false",
        "debug_mode": "false",
        "show_circles": "false",
        "show_example": "false",
        "show_circles_only": "false",
        "start_position": "12",
        "test_mode": "false",
        "generate_test_data": "false",
        "process_date": ""
    },
    "argumentdetails": {
        "use_timelapse_settings": {
            "required": "false",
            "description": "Use Timelapse Settings",
            "help": "When checked, uses the timelapse settings from the 'Allsky Settings' WebUI page instead of the values below.",
            "tab": "Video",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "video_quality": {
            "required": "true",
            "description": "Video Quality",
            "help": "Output video quality and compression",
            "tab": "Video",
            "type": {
                "fieldtype": "select",
                "values": "low,medium,high"
            }
        },
        "framerate": {
            "required": "true",
            "description": "Framerate",
            "help": "Frames per second in output video. Higher values create smoother but faster videos",
            "tab": "Video",
            "type": {
                "fieldtype": "spinner",
                "min": 5,
                "max": 30,
                "step": 1
            }
        },
        "resolution": {
            "required": "true",
            "description": "Video Resolution",
            "help": "Target resolution of output video. Higher resolutions require more processing time",
            "tab": "Video",
            "type": {
                "fieldtype": "select",
                "values": "720p,1080p,4k"
            }
        },
        "max_length": {
            "required": "true",
            "description": "Maximum Video Length",
            "help": "Target maximum length in seconds. Longer videos require more processing time and storage",
            "tab": "Video",
            "type": {
                "fieldtype": "spinner",
                "min": 30,
                "max": 300,
                "step": 30
            }
        },
        "circle_radius_factor": {
            "required": "true",
            "description": "Circle Radius Factor",
            "help": "Factor to determine circle radius relative to image width (0.1 to 1.0)",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0.1,
                "max": 1.0,
                "step": 0.01
            }
        },
        "center_x_offset": {
            "required": "true",
            "description": "Center X Offset",
            "help": "Offset from image center for circle center X coordinate (in pixels, right/left)",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": -500,
                "max": 500,
                "step": 1
            }
        },
        "center_y_offset": {
            "required": "true",
            "description": "Center Y Offset",
            "help": "Offset from image center for circle center Y coordinate (in pixels, up/down)",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": -500,
                "max": 500,
                "step": 1
            }
        },
        "keogram_height": {
            "required": "true",
            "description": "Keogram Ring Height",
            "help": "Height of keogram ring in pixels",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 50,
                "max": 400,
                "step": 25
            }
        },
        "top_padding": {
            "required": "true",
            "description": "Top Padding",
            "help": "Additional pixels above the sky image. Adjust for balanced appearance",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 500,
                "step": 50
            }
        },
        "bottom_padding": {
            "required": "true",
            "description": "Bottom Padding",
            "help": "Additional pixels below the sky image. Adjust for balanced appearance",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 500,
                "step": 50
            }
        },
        "left_padding": {
            "required": "true",
            "description": "Left Padding",
            "help": "Additional pixels to the left of the sky image. Usually 0",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 500,
                "step": 50
            }
        },
        "right_padding": {
            "required": "true",
            "description": "Right Padding",
            "help": "Additional pixels to the right of the sky image. Usually 0",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 500,
                "step": 50
            }
        },
        "circle_padding": {
            "required": "true",
            "description": "Circle Padding",
            "help": "Spacing between inside sky image and keogram ring, in pixels",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 25,
                "step": 1
            }
        },
        "edge_padding": {
            "required": "true",
            "description": "Edge Padding",
            "help": "Spacing from image edges in pixels",
            "tab": "Image",
            "type": {
                "fieldtype": "spinner",
                "min": 0,
                "max": 25,
                "step": 1
            }
        },
        "start_position": {
            "required": "true",
            "description": "Keogram Start Position",
            "help": "Clock hour position to start keogram (12: top, 3: right, 6: bottom, 9: left)",
            "tab": "Image",
            "type": {
                "fieldtype": "select",
                "values": "12,3,6,9"
            }
        },
        "enable_testing": {
            "required": "false",
            "description": "Enable Testing Mode",
            "help": "Master switch for all testing features. Enable this to use test mode and debug features",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "generate_test_data": {
            "required": "false",
            "description": "Generate Test Data (run once)",
            "help": "Intended to speed up Video testing. Copy one hour of last night's data (11PM-12AM) to '~/allsky/images/test' folder. Uncheck this after generation",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "test_mode": {
            "required": "false",
            "description": "Use Test Data",
            "help": "Use 'test' folder instead of last night's images. Quicker for getting setup!",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "process_date": {
            "required": "false",
            "description": "Older Date to Process (YYYYMMDD)",
            "help": "Optional: Specify a date to process (format: YYYYMMDD). Leave empty to process last night's data (or test data if selected above)",
            "tab": "Testing",
            "type": {
                "fieldtype": "textfield"
            }
        },
        "show_circles": {
            "required": "false",
            "description": "Show Debug Circles",
            "help": "Draw inner and outer keogram ring circles for alignment testing",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "show_circles_only": {
            "required": "false",
            "description": "Debug Circles Only",
            "help": "Draw circles only (no keogram ring) for alignment testing",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "show_example": {
            "required": "false",
            "description": "Create Test Image",
            "help": "Generate single test image with keogram overlay for preview",
            "tab": "Testing",
            "type": {
                "fieldtype": "checkbox"
            }
        },
        "debug_mode": {
            "required": "false",
            "description": "Debug Mode",
            "help": "Enable detailed logging for troubleshooting",
            "tab": "Debug",
            "type": {
                "fieldtype": "checkbox"
            }
        }
    },
    "changelog": {
        "v0.8.5": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": [
                    "Added enable testing mode to control all testing features",
                    "Added logic for Enable Testing feature"
                ]
            }
        ],
        "v0.8.0": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": [
                    "Added ability to show debug circles without keogram ring",
                    "Improved error handling throughout the module",
                    "Fixed inconsistencies in metadata parameters",
                    "Enhanced path handling using environment variables (removed hard-paths)"
                ]
            }
        ],
        "v0.7.1": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": [
                    "Improved circle detection for different image sizes",
                    "Added circle position and radius configuration"
                ]
            }
        ],
        "v0.6.1": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": "Cleanup & Prep for outside testing"
            }
        ]
    }
}

VIDEO_QUALITY = {
    'low':    {'bitrate': '2000k', 'quality': 23},
    'medium': {'bitrate': '4000k', 'quality': 20},
    'high':   {'bitrate': '8000k', 'quality': 17}
}

def debug_log(message, level=1):
    """Enhanced debug logging with multiple levels and debug mode control

    Args:
        message (str): The message to log
        level (int): Log level
    """
    global debug_mode
    try:
        if s.LOGLEVEL < level and not debug_mode:
            return

        # TODO: Only use s.log() have have the invoker add ERROR, WARNING, and INFO to the messages.
        # Then prefix, print(), LOG_DIR, and log_file aren't needed.
        prefix = "ERROR" if level == 0 else "WARNING" if level == 1 else "INFO"

        if level == 0:
            print(f"KEOLAPSE {prefix}: {message}")    # TODO: where does this go?

        # Force s.log() to display in debug mode.
        if debug_mode and level > s.LOGLEVEL:
            level = s.LOGLEVEL

        s.log(level, f"{prefix}: {message}")

        global LOG_DIR, log_file

        # Ensure log directory exists
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        with open(log_file, "a") as f:
            f.write(f"{timestamp} - [{prefix}] {message}\n")

    except Exception as e:
        print(f"KEOLAPSE LOGGING ERROR: {str(e)}")

def get_timelapse_settings():
    """Get timelapse settings from Allsky's settings file"""
    try:
        # Extract relevant timelapse settings
        timelapse_settings = {
            "width": s.getSetting("timelapsewidth"),
            "height": s.getSetting("timelapseheight"),
            "bitrate": s.getSetting("timelapsebitrate"),
            "fps": s.getSetting("timelapsefps"),
            "vcodec": s.getSetting("timelapsevcodec"),
            "pixfmt": s.getSetting("timelapsepixfmt"),
            "fflog": s.getSetting("timelapsefflog")
        }

        debug_log(f"Loaded Allsky's timelapse settings: {timelapse_settings}", level=4)
        return timelapse_settings

    except Exception as e:
        debug_log(f"Unable to load timelapse settings: {str(e)}", level=0)
        return None

def get_target_date(params):
    """Get target date in YYYYMMDD format, using process_date if specified"""
    process_date = params.get("process_date", "").strip()

    if process_date:
        try:
            datetime.strptime(process_date, "%Y%m%d")
            debug_log(f"Using specified date: {process_date}", level=4)
            return process_date
        except ValueError:
            debug_log(f"Invalid date format: {process_date}, using yesterday", level=1)

    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def get_source_directory(params):
    """Get source directory based on test mode and process_date"""

    # Only use test mode if testing is enabled
    global testing_enabled
    test_mode = testing_enabled and str(params.get("test_mode", "false")).lower() == "true"

    source_dir = os.path.join(base_dir, "test" if test_mode else get_target_date(params))

    if not os.path.exists(source_dir):
        debug_log(f"Directory not found: {source_dir}", level=0)
        return None  # Return None to indicate failure

    return source_dir

def get_source_images(params):
    """Get list of source images"""
    try:
        source_dir = get_source_directory(params)
        if source_dir is None:
            debug_log("Cannot proceed without valid source directory", level=0)
            return []

        debug_log(f"Searching for images in: {source_dir}", level=4)

        # Get file extension from environment or default to jpg
        EXTENSION = s.getEnvironmentVariable("EXTENSION", fatal=False) or "jpg"
        image_pattern = os.path.join(source_dir, f"image-*.{EXTENSION}")
        images = sorted(glob.glob(image_pattern))

        if not images:
            debug_log("No images found", level=1)
            return []

        fps = int(params["framerate"])
        estimated_length = len(images) / fps
        minutes = int(estimated_length // 60)
        seconds = int(estimated_length % 60)

        debug_log(f"Found {len(images)} images", level=4)
        debug_log(f"Estimated video length: {minutes}:{seconds:02d} at {fps} fps", level=4)

        return images

    except Exception as e:
        debug_log(f"Failed to get source images: {str(e)}", level=1)
        return []

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_keogram_path(params):
    """Get keogram path based on source directory"""
    source_dir = get_source_directory(params)
    if source_dir is None:
        debug_log("Cannot locate keogram without valid source directory", level=0)
        return None

    keogram_dir = os.path.join(source_dir, "keogram")
    debug_log(f"Searching for keogram in: {keogram_dir}", level=4)

    # If we only want to show debug circles, we don't need a keogram
    global show_circles_only
    if show_circles_only:
        debug_log("Debug circles only mode - no keogram needed", level=4)
        return True

    # Check if keogram directory exists
    if not os.path.exists(keogram_dir):
        debug_log(f"Keogram directory not found: {keogram_dir}", level=1)
        return None

    # Look for keogram files
    keogram_files = glob.glob(os.path.join(keogram_dir, "keogram*.jpg"))
    if keogram_files:
        debug_log(f"Using keogram: {os.path.basename(keogram_files[0])}", level=4)
        return keogram_files[0]

    debug_log("No keogram found", level=1)
    return None

def get_output_path(params, filename):
    """Get path for output file"""
    source_dir = get_source_directory(params)
    if source_dir is None:
        # Create a fallback path in the base directory if source directory doesn't exist
        debug_log("Using fallback output path due to missing source directory", level=1)
        output_dir = ensure_dir(os.path.join(base_dir, "keolapse_output"))
    else:
        output_dir = ensure_dir(os.path.join(source_dir, "keolapse"))

    if filename.startswith("keolapse-") and not filename.startswith("keolapse-test"):
        target_date = get_target_date(params)
        filename = f"keolapse-{target_date}.mp4"

    return os.path.join(output_dir, filename)

def generate_test_data():
    """Generate test data by copying last night's images and keogram"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        source_dir = os.path.join(base_dir, yesterday)
        test_dir = os.path.join(base_dir, "test")

        if not os.path.exists(source_dir):
            debug_log(f"Source directory not found: {source_dir}", level=0)
            return False

        if os.path.exists(test_dir):
            test_images = glob.glob(os.path.join(test_dir, "image-*.jpg"))
            if test_images and test_date_is_current(test_images[0], yesterday):
                debug_log("Test data is current", level=4)
                return True
            shutil.rmtree(test_dir)

        os.makedirs(test_dir)

        # Copy a subset of night images (23:00-00:00)
        night_pattern = os.path.join(source_dir, f"image-{yesterday}23*.jpg")
        night_images = sorted(glob.glob(night_pattern))

        if not night_images:
            debug_log("No night images found", level=3)
            return False

        for img in night_images:
            shutil.copy2(img, os.path.join(test_dir, os.path.basename(img)))

        # Copy keogram if available
        source_keogram = os.path.join(source_dir, "keogram")
        if os.path.exists(source_keogram):
            shutil.copytree(source_keogram, os.path.join(test_dir, "keogram"))

        debug_log(f"Generated test data with {len(night_images)} images", level=3)
        return True

    except Exception as e:
        debug_log(f"Error generating test data: {str(e)}", level=0)
        return False

def test_date_is_current(test_image, target_date):
    """Check if test data matches target date"""
    try:
        test_date = os.path.basename(test_image).split("-")[1][:8]
        return test_date == target_date
    except:
        return False

def cleanup_test_data(event):
    """Clean up test data during nightday transition"""
    if event == "nightday":
        try:
            test_dir = os.path.join(base_dir, "test")
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
                debug_log("Cleaned up test data", level=4)
        except Exception as e:
            debug_log(f"Error cleaning test data: {str(e)}", level=1)

def create_debug_image(images, params):
    """Generate debug test image with keogram overlay"""
    try:
        if not images:
            return False

        mid_idx = len(images) // 2
        test_image = images[mid_idx]

        frame = cv2.imread(test_image)
        if frame is None:
            debug_log(f"Failed to load test image: {test_image}", level=1)
            return False

        original_height, original_width = frame.shape[:2]
        new_width, new_height, scale_factor = calculate_scaled_dimensions(
            params, original_width, original_height)

        generator = KeolapseGenerator(params, scale_factor)

        scaled_frame = cv2.resize(frame, (new_width, new_height),
                                interpolation=cv2.INTER_LANCZOS4)

        # Apply user-specified padding
        top_pad = int(float(params["top_padding"]) * scale_factor)
        bottom_pad = int(float(params["bottom_padding"]) * scale_factor)
        left_pad = int(float(params.get("left_padding", "0")) * scale_factor)
        right_pad = int(float(params.get("right_padding", "0")) * scale_factor)

        padded = cv2.copyMakeBorder(scaled_frame,
                                  top_pad, bottom_pad,
                                  left_pad, right_pad,
                                  cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # This function will now handle any additional expansion needed for the keogram ring
        if not generator.detect_circle(padded):
            return False

        # Check if we're in circles-only mode
        global show_circles_only
        if show_circles_only:
            result = generator.draw_debug_circles(generator.expanded_image.copy())
            output_path = get_output_path(params, "keolapse_debug_circles.jpg")
            cv2.imwrite(output_path, result)
            debug_log(f"Created debug circles image: {output_path}", level=4)
            return True

        # Otherwise, proceed with normal keogram overlay
        keogram_path = get_keogram_path(params)
        if not keogram_path:
            return False

        keogram_data = generator.prepare_keogram(keogram_path)
        if keogram_data[0] is None:
            return False

        # Note that wrap_keogram will use the expanded image if needed
        result = generator.wrap_keogram(padded, keogram_data[0], keogram_data[1],
                                      mid_idx, len(images))

        output_path = get_output_path(params, "keolapse_debug.jpg")
        cv2.imwrite(output_path, result)
        debug_log(f"Created debug image: {output_path}", level=4)

        return True

    except Exception as e:
        debug_log(f"Error creating debug image: {str(e)}", level=1)
        return False

def optimize_video_params(images, params):
    """Optimize video parameters based on input images and target duration"""
    MIN_FPS = 5
    MAX_FPS = 30
    TARGET_DURATION = int(params.get("max_length", "120"))

    current_fps = int(params["framerate"])
    total_frames = len(images)
    current_duration = total_frames / current_fps

    debug_log(f"Initial duration: {current_duration:.1f} seconds", level=4)

    if current_duration <= TARGET_DURATION:
        return images, current_fps

    ideal_frame_count = int(TARGET_DURATION * current_fps)
    skip_interval = max(1, total_frames // ideal_frame_count)
    optimized_images = images[::skip_interval]

    optimized_fps = min(MAX_FPS, max(MIN_FPS,
                       len(optimized_images) / TARGET_DURATION))

    debug_log(f"Optimization results:", level=4)
    debug_log(f"- Original frames: {total_frames}", level=4)
    debug_log(f"- Optimized frames: {len(optimized_images)}", level=4)
    debug_log(f"- Frames kept: 1 in every {skip_interval}", level=4)
    debug_log(f"- Final duration: {len(optimized_images)/optimized_fps:.1f} seconds", level=4)

    return optimized_images, int(optimized_fps)

def should_optimize_video(images, params):
    """Determine if video optimization should be applied"""
    if len(images) < 300:
        return False

    global use_timelapse_settings
    if use_timelapse_settings:
        timelapse_settings = get_timelapse_settings()
        if timelapse_settings:
            fps = int(timelapse_settings["fps"])
        else:
            fps = int(params["framerate"])
    else:
        fps = int(params["framerate"])

    expected_duration = len(images) / fps
    max_length = int(params.get("max_length", "120"))

    return expected_duration > max_length

def calculate_scaled_dimensions(params, original_width, original_height):
    """Calculate scaled dimensions while maintaining aspect ratio"""
    target_res = params["resolution"]
    target_heights = {
        "720p": 720,
        "1080p": 1080,
        "4k": 2160
    }

    target_height = target_heights.get(target_res, 720)

    if original_height < target_height:
        target_height = original_height
        debug_log(f"Maintaining original resolution ({original_height}p)", level=4)

    scale_factor = target_height / original_height
    new_width = int(original_width * scale_factor)

    debug_log(f"Scale factor: {scale_factor:.3f}", level=4)
    debug_log(f"New dimensions: {new_width}x{target_height}", level=4)

    return new_width, target_height, scale_factor

def check_ffmpeg_available():
    """Check if ffmpeg is available on the system"""
    try:
        result = subprocess.run(['which', 'ffmpeg'],
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True
        return False
    except Exception:
        return False

class KeolapseGenerator:
    """Class to handle keogram ring generation and application to images"""
    def __init__(self, params, scale_factor=1.0):
        """Initialize generator with parameters and scale factor"""
        self.params = params
        self.scale_factor = scale_factor
        self.circle_center = None
        self.circle_radius = None
        self.keogram_height = int(float(params["keogram_height"]) * scale_factor)
        self.circle_padding = int(float(params["circle_padding"]) * scale_factor)
        self.edge_padding = int(float(params["edge_padding"]) * scale_factor)
        self.start_position = int(params["start_position"])
        self.angle_offset = {
            12: 90,
            3: 180,
            6: 270,
            9: 0
        }[self.start_position]
        self.circle_radius_factor = float(params["circle_radius_factor"])
        self.center_x_offset = int(float(params["center_x_offset"]) * scale_factor)
        self.center_y_offset = int(float(params["center_y_offset"]) * scale_factor)
        self.expanded_image = None
        self.expansion = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

    def detect_circle(self, image):
        """Detect circle parameters with dynamic scaling and image expansion if needed"""
        try:
            height, width = image.shape[:2]

            # Calculate initial circle center and radius
            center_x = width // 2 + self.center_x_offset
            center_y = height // 2 + self.center_y_offset
            radius = int(min(width, height) * self.circle_radius_factor)

            # Calculate required space for keogram ring
            required_space = radius + self.keogram_height + self.circle_padding

            # Check if we need to expand the image
            expansion_needed = False
            self.expansion = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

            # Check if circle+keogram extends beyond top edge
            if center_y - required_space < 0:
                self.expansion['top'] = abs(center_y - required_space) + self.edge_padding
                expansion_needed = True

            # Check if circle+keogram extends beyond bottom edge
            if center_y + required_space >= height:
                self.expansion['bottom'] = (center_y + required_space) - height + self.edge_padding
                expansion_needed = True

            # Check if circle+keogram extends beyond left edge
            if center_x - required_space < 0:
                self.expansion['left'] = abs(center_x - required_space) + self.edge_padding
                expansion_needed = True

            # Check if circle+keogram extends beyond right edge
            if center_x + required_space >= width:
                self.expansion['right'] = (center_x + required_space) - width + self.edge_padding
                expansion_needed = True

            # Expand image if needed
            if expansion_needed:
                debug_log(f"Expanding image to fit keogram ring: top={self.expansion['top']}, " +
                         f"bottom={self.expansion['bottom']}, left={self.expansion['left']}, " +
                         f"right={self.expansion['right']}", level=4)

                self.expanded_image = cv2.copyMakeBorder(
                    image,
                    self.expansion['top'], self.expansion['bottom'],
                    self.expansion['left'], self.expansion['right'],
                    cv2.BORDER_CONSTANT, value=[0, 0, 0]
                )

                # Adjust center coordinates for expanded image
                center_x += self.expansion['left']
                center_y += self.expansion['top']
            else:
                self.expanded_image = image.copy()

            self.circle_center = (center_x, center_y)
            self.circle_radius = radius

            debug_log(f"Circle detection: center=({center_x}, {center_y}), radius={radius}", level=4)

            return True

        except Exception as e:
            debug_log(f"Error setting circle parameters: {str(e)}", level=0)
            return False

    def prepare_keogram(self, keogram_path):
        """Prepare keogram for overlay with scaling"""
        try:
            # Handle circles-only mode
            if keogram_path is True:  # Special case for circles-only mode
                dummy_img = np.zeros((self.keogram_height, 100, 3), dtype=np.uint8)
                return dummy_img, dummy_img

            keogram = cv2.imread(keogram_path)
            if keogram is None:
                raise Exception(f"Failed to load keogram: {keogram_path}")

            circumference = 2 * np.pi * (self.circle_radius + self.circle_padding)
            new_width = int(circumference)

            keogram_resized = cv2.resize(keogram, (new_width, self.keogram_height),
                                       interpolation=cv2.INTER_LANCZOS4)

            progress = np.zeros_like(keogram_resized)

            hour_width = new_width // 24
            font_scale = max(0.3, 0.5 * self.scale_factor)

            for i in range(24):
                x = i * hour_width
                cv2.line(progress, (x, 0), (x, self.keogram_height),
                        (50, 50, 50), max(1, int(1 * self.scale_factor)))
                cv2.putText(progress, f"{i:02d}",
                           (x + 5, self.keogram_height - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                           (100, 100, 100), max(1, int(1 * self.scale_factor)))

            return keogram_resized, progress

        except Exception as e:
            debug_log(f"Error preparing keogram: {str(e)}", level=0)
            return None, None

    def draw_debug_circles(self, image):
        """Draw debug circles on image without keogram overlay"""
        try:
            result = image.copy()
            height, width = result.shape[:2]

            # Draw inner circle (at circle_radius)
            cv2.circle(result, self.circle_center, self.circle_radius,
                     (0, 255, 0), 2)

            # Draw middle circle (at circle_radius + padding)
            cv2.circle(result, self.circle_center,
                     self.circle_radius + self.circle_padding,
                     (255, 0, 0), 2)

            # Draw outer circle (at circle_radius + padding + keogram_height)
            cv2.circle(result, self.circle_center,
                     self.circle_radius + self.circle_padding + self.keogram_height,
                     (0, 255, 255), 2)

            # Add center marker
            cv2.drawMarker(result, self.circle_center, (255, 0, 255),
                         markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)

            # Add debug text
            debug_text = "DEBUG CIRCLES ONLY MODE"
            font = cv2.FONT_HERSHEY_SIMPLEX
            for i in range(3):
                x = (width // 3) * i + 50
                cv2.putText(result, debug_text, (x, height - 20),
                          font, 1, (0, 0, 255), 2)

            return result

        except Exception as e:
            debug_log(f"Error drawing debug circles: {str(e)}", level=0)
            return image

    def wrap_keogram(self, base_image, keogram, progress_indicator, frame_idx, total_frames):
        """Map keogram around the circular image with corrected angle mapping"""
        try:
            # Use the expanded image (which may be the same as base_image if no expansion needed)
            result = self.expanded_image.copy()
            height, width = result.shape[:2]

            # Check if we should only draw circles and skip keogram
            global show_circles_only
            if show_circles_only:
                return self.draw_debug_circles(result)

            progress_x = int((frame_idx / total_frames) * progress_indicator.shape[1])
            progress_copy = progress_indicator.copy()

            for i in range(4):
                marker_x = max(0, progress_x - i)
                intensity = 255 - (i * 50)
                cv2.line(progress_copy, (marker_x, 0), (marker_x, self.keogram_height),
                        (intensity, intensity, intensity), 2)

            cv2.line(progress_copy, (progress_x, 0), (progress_x, self.keogram_height),
                    (255, 255, 255), 4)

            y, x = np.mgrid[:height, :width]
            dx = x - self.circle_center[0]
            dy = y - self.circle_center[1]

            radius = np.sqrt(dx**2 + dy**2)
            angle = np.degrees(np.arctan2(dy, dx))
            angle = np.where(angle < 0, angle + 360, angle)
            angle = (angle + self.angle_offset) % 360

            ring_mask = (radius > (self.circle_radius + self.circle_padding)) & \
                    (radius < (self.circle_radius + self.circle_padding + self.keogram_height))

            keogram_x = ((angle[ring_mask] / 360) * keogram.shape[1]).astype(int)
            keogram_y = ((radius[ring_mask] - (self.circle_radius + self.circle_padding)) * \
                        self.keogram_height / self.keogram_height).astype(int)

            keogram_x = np.clip(keogram_x, 0, keogram.shape[1] - 1)
            keogram_y = np.clip(keogram_y, 0, keogram.shape[0] - 1)

            combined = cv2.addWeighted(keogram, 0.8, progress_copy, 0.2, 0)
            result[ring_mask] = combined[keogram_y, keogram_x]

            show_circles = str(self.params.get("show_circles", "false")).lower() == "true"
            if show_circles:
                cv2.circle(result, self.circle_center, self.circle_radius,
                        (0, 255, 0), 1) # Inner circle
                cv2.circle(result, self.circle_center, self.circle_radius + self.circle_padding,
                        (255, 0, 0), 1) # Middle circle
                cv2.circle(result, self.circle_center,
                        self.circle_radius + self.circle_padding + self.keogram_height,
                        (0, 255, 255), 1) # Outer circle

            if show_circles or str(self.params.get("show_example", "false")).lower() == "true":
                debug_text = "DEBUG ENABLED"
                font = cv2.FONT_HERSHEY_SIMPLEX
                for i in range(3):
                    x = (result.shape[1] // 3) * i + 50
                    cv2.putText(result, debug_text, (x, height - 20),
                            font, 1, (0, 0, 255), 2)

            return result

        except Exception as e:
            debug_log(f"Error wrapping keogram: {str(e)}", level=0)
            return base_image

def create_video(images, params):
    """Create timelapse video with keogram overlay"""
    if not images:
        debug_log("No images found to process", level=1)
        return False

    try:
        # Check if ffmpeg is available
        if not check_ffmpeg_available():
            debug_log("ERROR: ffmpeg not found. Please install ffmpeg to create videos.", level=0)
            return False

        # Get timelapse settings if enabled.  Only set once.
        global use_timelapse_settings
        timelapse_settings = None

        if use_timelapse_settings:
            timelapse_settings = get_timelapse_settings()
            if timelapse_settings:
                debug_log("Using timelapse settings from Allsky Settings", level=4)
            else:
                # TODO: This should be a fatal error.
                debug_log("Failed to load timelapse settings, using module settings instead", level=1)
                use_timelapse_settings = False

        # Read first frame to get dimensions
        first_frame = cv2.imread(images[0])
        if first_frame is None:
            debug_log(f"Failed to read first image: {os.path.basename(images[0])}", level=0)
            return False

        # Calculate scaled dimensions and scaling factor
        original_height, original_width = first_frame.shape[:2]

        # Determine resolution based on settings
        if use_timelapse_settings and timelapse_settings:
            # If timelapsewidth/height is 0, keep original dimensions
            new_width = timelapse_settings["width"] if timelapse_settings["width"] > 0 else original_width
            new_height = timelapse_settings["height"] if timelapse_settings["height"] > 0 else original_height
            scale_factor = min(new_width / original_width, new_height / original_height)

            # Recalculate to maintain aspect ratio
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)

            debug_log(f"Using timelapse resolution: {new_width}x{new_height}, scale_factor={scale_factor}", level=4)
        else:
            # Use module settings
            new_width, new_height, scale_factor = calculate_scaled_dimensions(
                params, original_width, original_height)

        # Initialize generator with scale factor
        generator = KeolapseGenerator(params, scale_factor)

        # Scale padding values
        top_padding = int(float(params["top_padding"]) * scale_factor)
        bottom_padding = int(float(params["bottom_padding"]) * scale_factor)
        left_padding = int(float(params.get("left_padding", "0")) * scale_factor)
        right_padding = int(float(params.get("right_padding", "0")) * scale_factor)

        # Create a properly scaled sample frame for circle detection
        scaled_frame = cv2.resize(first_frame, (new_width, new_height),
                                interpolation=cv2.INTER_LANCZOS4)
        padded_frame = cv2.copyMakeBorder(
            scaled_frame,
            top_padding, bottom_padding,
            left_padding, right_padding,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0]
        )

        # This will handle any additional expansion needed to fit the keogram ring
        if not generator.detect_circle(padded_frame):
            debug_log("Failed to detect circle parameters", level=0)
            return False

        # Check if we're in circles-only mode
        global show_circles_only
        circles_only = show_circles_only

        if not circles_only:
            # Load and prepare keogram
            keogram_path = get_keogram_path(params)
            if not keogram_path:
                debug_log("No keogram found", level=1)
                return False

            keogram_data = generator.prepare_keogram(keogram_path)
            if keogram_data[0] is None:
                return False
        else:
            # Create dummy keogram data for circles-only mode
            debug_log("Using circles-only mode (no keogram overlay)", level=4)
            dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
            keogram_data = (dummy_img, dummy_img)

        # Get final frame dimensions based on the possibly expanded image
        if generator.expanded_image is not None:
            height, width = generator.expanded_image.shape[:2]
        else:
            height, width = padded_frame.shape[:2]

        debug_log(f"Final frame dimensions: {width}x{height}", level=4)

        # Apply video optimization if needed
        if should_optimize_video(images, params):
            debug_log("Video length exceeds maximum, optimizing...", level=4)
            images, fps = optimize_video_params(images, params)
        else:
            # Set framerate based on settings
            if use_timelapse_settings and timelapse_settings:
                fps = int(timelapse_settings["fps"])
            else:
                fps = int(params["framerate"])

        debug_log(f"Output video dimensions: {width}x{height} @ {fps}fps", level=4)

        # Get quality settings
        if use_timelapse_settings and timelapse_settings:
            # Convert bitrate to quality setting
            bitrate = timelapse_settings["bitrate"]
            if bitrate <= 3000:
                quality_setting = "low"
            elif bitrate <= 6000:
                quality_setting = "medium"
            else:
                quality_setting = "high"

            # Create custom quality parameters based on timelapse settings
            custom_quality = {
                "bitrate": f"{bitrate}k",
                "quality": 23 if quality_setting == "low" else 20 if quality_setting == "medium" else 17
            }
            quality_params = custom_quality
            debug_log(f"Using timelapse quality settings (bitrate: {bitrate}k)", level=4)
        else:
            quality_setting = params.get("video_quality", "medium")
            quality_params = VIDEO_QUALITY.get(quality_setting, VIDEO_QUALITY["medium"])
            debug_log(f"Using video quality: {quality_setting}", level=4)

        debug_log(f"Quality parameters: {quality_params}", level=4)

        # Setup temporary path for initial video
        global test_mode
        is_test = str(params.get("test_mode", "false")).lower() == "true"
        if is_test:
            output_filename = "keolapse-test.mp4"
        else:
            target_date = get_target_date(params)
            output_filename = f"keolapse-{target_date}.mp4"

        output_path = get_output_path(params, output_filename)
        temp_output = output_path.replace(".mp4", "_temp.mp4")

        # Create video writer with x264 codec for better quality control
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

        if not writer.isOpened():
            debug_log(f"Failed to create video writer", level=0)
            return False

        # Process frames
        total_frames = len(images)
        keogram, progress = keogram_data

        # Calculate progress reporting interval
        # TODO: Maybe use 25 instead of 15, and 20 instead of 10??
        progress_interval = max(1, total_frames // (15 if total_frames > 500 else 10))
        start_time = datetime.now()

        for i, img_path in enumerate(images):
            # Progress reporting
            if i % progress_interval == 0:
                progress_pct = (i + 1) / total_frames * 100
                elapsed_time = (datetime.now() - start_time).total_seconds()

                if i > 0:
                    time_per_frame = elapsed_time / i
                    time_remaining = (total_frames - i) * time_per_frame
                    time_str = f"{time_remaining/60:.1f}min" if time_remaining > 60 else f"{time_remaining:.0f}s"
                    debug_log(f"Progress: {progress_pct:.1f}% ({i+1}/{total_frames}) - Est. remaining: {time_str}",
                             level=4)
                else:
                    debug_log(f"Progress: {progress_pct:.1f}% ({i+1}/{total_frames})", level=4)

            # Process frame
            frame = cv2.imread(img_path)
            if frame is None:
                debug_log(f"Failed to read frame: {os.path.basename(img_path)}", level=1)
                continue

            # Scale frame to target resolution
            scaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

            # Add user-specified padding
            padded = cv2.copyMakeBorder(
                scaled,
                top_padding, bottom_padding,
                left_padding, right_padding,
                cv2.BORDER_CONSTANT,
                value=[0, 0, 0]
            )

            # For each frame, we need to detect circle and expand if needed
            # This ensures expansion is consistent for all frames
            if i == 0:
                # For first frame, perform full detection and save expansion values
                generator.detect_circle(padded)
                initial_expansion = generator.expansion.copy()
                initial_circle_center = generator.circle_center
                initial_circle_radius = generator.circle_radius
            else:
                # For subsequent frames, use same expansion as first frame
                # but rebuild the expanded image with the current frame
                if any(initial_expansion.values()):
                    # Apply same expansion as first frame
                    generator.expansion = initial_expansion.copy()
                    generator.expanded_image = cv2.copyMakeBorder(
                        padded,
                        initial_expansion['top'], initial_expansion['bottom'],
                        initial_expansion['left'], initial_expansion['right'],
                        cv2.BORDER_CONSTANT, value=[0, 0, 0]
                    )
                    # Restore circle parameters
                    generator.circle_center = initial_circle_center
                    generator.circle_radius = initial_circle_radius
                else:
                    # No expansion needed
                    generator.expanded_image = padded.copy()

            # Apply appropriate overlay based on mode
            if circles_only:
                result = generator.draw_debug_circles(generator.expanded_image.copy())
            else:
                # Apply keogram overlay (will use expanded image)
                result = generator.wrap_keogram(padded, keogram, progress, i, total_frames)

            writer.write(result)

        writer.release()

        # Re-encode with quality settings using ffmpeg
        try:
            # Determine ffmpeg parameters based on settings
            if use_timelapse_settings and timelapse_settings:
                vcodec = timelapse_settings["vcodec"]
                pixfmt = timelapse_settings["pixfmt"]
                fflog = timelapse_settings["fflog"]

                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_output,
                    '-c:v', vcodec,
                    '-preset', 'medium',
                    '-crf', str(quality_params['quality']),
                    '-b:v', quality_params['bitrate'],
                    '-maxrate', str(int(quality_params['bitrate'].replace('k', '')) * 2) + 'k',
                    '-bufsize', quality_params['bitrate'],
                    '-pix_fmt', pixfmt,
                    '-loglevel', fflog,
                    output_path
                ]
            else:
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_output,
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', str(quality_params['quality']),
                    '-b:v', quality_params['bitrate'],
                    '-maxrate', str(int(quality_params['bitrate'].replace('k', '')) * 2) + 'k',
                    '-bufsize', quality_params['bitrate'],
                    output_path
                ]

            debug_log("Re-encoding video with quality settings...", level=4)
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # Remove temporary file
            if os.path.exists(temp_output):
                os.remove(temp_output)

        except Exception as e:
            debug_log(f"Failed to apply quality settings: {str(e)}", level=1)
            # If re-encoding fails, keep the original file
            if os.path.exists(temp_output):
                os.rename(temp_output, output_path)
                debug_log("Using original encoded video (ffmpeg failed)", level=1)

        # Log completion
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        time_str = f"{total_time/60:.1f} minutes" if total_time > 60 else f"{total_time:.1f} seconds"
        debug_log(f"Video creation completed in {time_str}, start={start_time}, end={end_time}", level=3)

        return True

    except Exception as e:
        debug_log(f"Video creation failed: {str(e)}", level=0)
        return False

def keolapse(params, event):
    """Main entry point for the keolapse module"""
    s.params = params  # Store params in shared module

    global debug_mode, use_timelapse_settings, testing_enabled,show_circles_only
    # Check if testing is enabled
    debug_mode =             str(params.get("debug_mode", "false")).lower() == "true"
    use_timelapse_settings = str(params.get("use_timelapse_settings", "false")).lower() == "true"
    testing_enabled =        str(params.get("enable_testing", "false")).lower() == "true"
    show_circles_only =      str(params.get("show_circles_only", "false")).lower() == "true"

    # Make sure log directory exists
    if not os.path.exists(LOG_DIR):
        ensure_dir(LOG_DIR)

    debug_log("=== Starting Keolapse Module ===", level=3)
    debug_log(f"Base directory: {base_dir}", level=4)
    debug_log(f"Event: {event}", level=4)
    debug_log(f"Module version: {metaData['version']}", level=4)
    debug_log(f"Testing mode: {'Enabled' if testing_enabled else 'Disabled'}", level=4)

    try:
        # Clean up test data during nightday transition
        cleanup_test_data(event)

        # Handle test data generation in periodic mode (before any other testing)
        if testing_enabled and event == "periodic" and str(params.get("generate_test_data", "false")).lower() == "true":
            debug_log("Generating test data...", level=3)
            return "Test data generated successfully" if generate_test_data() else "Failed to generate test data"

        # Get source images (either test or normal depending on settings)
        # This needs to happen BEFORE we try to use images for debug purposes
        images = get_source_images(params)
        if not images:
            source_dir = get_source_directory(params)
            if source_dir is None:
                return "ERROR: Source directory not found - cannot proceed"
            else:
                return "No images found to process"

        # Now that we have images loaded, check if we're in debug/testing mode
        if testing_enabled and event == "periodic" and (
            str(params.get("show_circles", "false")).lower() == "true" or
            str(params.get("show_example", "false")).lower() == "true" or
            show_circles_only
        ):
            debug_log("Creating debug image...", level=3)
            return "Debug image created successfully" if create_debug_image(images, params) else "Failed to create debug image"

        # Normal video creation mode
        debug_log("Creating keolapse video...", level=4)
        return "Video created successfully" if create_video(images, params) else "Failed to create video"

    except Exception as e:
        debug_log(f"Module execution failed: {str(e)}", level=0)
        return f"Error: {str(e)}"
    finally:
        s.params = None  # Clear params from shared module

def keolapse_cleanup():
    """Module cleanup function"""
    try:
        moduleData = {
            "metaData": metaData,
            "cleanup": {
                "files": {},
                "env": {}
            }
        }
        s.cleanupModule(moduleData)
    except Exception as e:
        print(f"KEOLAPSE ERROR during cleanup: {str(e)}", level=0)


