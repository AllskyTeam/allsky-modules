"""
allsky_mlx90614.py

Part of allsky postprocess.py modules.
https://github.com/thomasjacquin/allsky


"""

import allsky_shared as s
import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import datetime as dt
import cv2
import cmapy
import os
from scipy import ndimage
from datetime import datetime
from datetime import timedelta
import csv

metaData = {
    "name": "All Sky MLX90640",
    "description": "Generates a thermal image from the sensor",
    "module": "allsky_mlx90640",
    "version": "v1.0.2",
    "events": ["periodic"],
    "experimental": "true",
    "arguments": {
        "i2caddress": "",
        "imagefilename": "ir.jpg",
        "logdata": "False",
        "roi": ""
    },
    "argumentdetails": {
        "i2caddress": {
            "required": "false",
            "description": "I2C Address",
            "help": "Override the standard i2c address (0x33) for the mlx90640. NOTE: This value must be hex i.e. 0x76",
            "tab": "Sensor"
        },
        "imagefilename": {
            "required": "false",
            "description": "Image filename",
            "tab": "Image",
            "help": "The filename to save the image as. NOTE: Does not need the path. The image will be saved in the overlay images folder"
        },
        "logdata": {
            "required": "false",
            "description": "Log Data",
            "help": "Log data and images. **WARNING** This will require a lot of additional disk space",
            "tab": "Logging",
            "type": {"fieldtype": "checkbox"}
        },
        "roi": {
            "required": "false",
            "description": "Region of Interest for temperature calculations",
            "help": "Define a region of interest, format X,Y,L,H",
            "tab": "Image"
        }
    },
    "enabled": "false",
    "changelog": {
        "v1.0.0": [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Initial Release"
            }
        ],
        "v1.0.1": [
            {
                "author": "Alex Greenland",
                "authorurl": "https://github.com/allskyteam",
                "changes": "Added data logging"
            }
        ],
        "v1.0.2": [
            {
                "author": "Michel Moriniaux",
                "authorurl": "https://github.com/MichelMoriniaux",
                "changes": "Added RoI"
            }
        ]
    }
}


class pithermalcam:
    # See https://gitlab.com/cvejarano-oss/cmapy/-/blob/master/docs/colorize_all_examples.md to for options that can be put in this list
    _colormap_list = [
        "jet",
        "bwr",
        "seismic",
        "coolwarm",
        "PiYG_r",
        "tab10",
        "tab20",
        "gnuplot2",
        "brg",
    ]
    _interpolation_list = [
        cv2.INTER_NEAREST,
        cv2.INTER_LINEAR,
        cv2.INTER_AREA,
        cv2.INTER_CUBIC,
        cv2.INTER_LANCZOS4,
        5,
        6,
    ]
    _interpolation_list_name = [
        "Nearest",
        "Inter Linear",
        "Inter Area",
        "Inter Cubic",
        "Inter Lanczos4",
        "Pure Scipy",
        "Scipy/CV2 Mixed",
    ]
    _current_frame_processed = False  # Tracks if the current processed image matches the current raw image
    i2c = None
    mlx = None
    _temp_min = None
    _temp_max = None
    _raw_image = None
    _image = None
    _file_saved_notification_start = None
    _displaying_onscreen = False
    _exit_requested = False

    def __init__(self, use_f: bool = True, filter_image: bool = False, image_width: int = 1200,
                 image_height: int = 900, output_folder: str = "/home/pi/pithermalcam/saved_snapshots/",):
        self.use_f = use_f
        self.filter_image = filter_image
        self.image_width = image_width
        self.image_height = image_height
        self.output_folder = output_folder

        self._colormap_index = 0
        self._interpolation_index = 3
        self._setup_therm_cam()
        self._t0 = time.time()
        # self.update_image_frame()

    def __del__(self):
        pass

    def _setup_therm_cam(self):
        """Initialize the thermal camera"""
        # Setup camera
        self.i2c = busio.I2C(board.SCL, board.SDA)  # setup I2C
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)  # begin MLX90640 with I2C comm
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ  # set refresh rate
        time.sleep(0.1)

    def _c_to_f(self, temp: float):
        """Convert temperature from C to F"""
        return (9.0 / 5.0) * temp + 32.0

    def _sub_frame(self, frame, region=None):
        pixel = 0
        sub_frame = np.zeros((int(region[2]) * int(region[3]),))

        for h in range(region[3]):
            for w in range(region[2]):
                sub_frame[pixel] = frame[(region[1] + h)*32 + (region[0] + w)]
                pixel += 1
        return sub_frame

    def get_mean_temp(self, region=None):
        """
        Get mean temp of entire field of view. Return both temp C and temp F.
        """
        frame = np.zeros((24 * 32,))  # setup array for storing all 768 temperatures
        while True:
            try:
                self.mlx.getFrame(frame)  # read MLX temperatures into frame var
                break
            except ValueError:
                continue  # if error, just read again

        if region:
            frame = self._sub_frame(frame, region)
        temp_c = np.mean(frame)
        temp_f = self._c_to_f(temp_c)

        max = np.max(frame)
        min = np.min(frame)

        return temp_c, temp_f, min, max

    def _pull_raw_image(self):
        """Get one pull of the raw image data, converting temp units if necessary"""
        # Get image
        self._raw_image = np.zeros((24 * 32,))
        try:
            self.mlx.getFrame(self._raw_image)  # read mlx90640
            self._temp_min = np.min(self._raw_image)
            self._temp_max = np.max(self._raw_image)
            self._raw_image = self._temps_to_rescaled_uints(self._raw_image, self._temp_min, self._temp_max)
            self._current_frame_processed = False  # Note that the newly updated raw frame has not been processed
        except ValueError:
            print("Math error; continuing...")
            self._raw_image = np.zeros((24 * 32,))  # If something went wrong, make sure the raw image has numbers
        except OSError:
            print("IO Error; continuing...")
            self._raw_image = np.zeros((24 * 32,))  # If something went wrong, make sure the raw image has numbers

    def _process_raw_image(self):
        """Process the raw temp data to a colored image. Filter if necessary"""
        # Image processing
        # Can't apply colormap before ndimage, so reversed in first two options, even though it seems slower
        if self._interpolation_index == 5:  # Scale via scipy only - slowest but seems higher quality
            self._image = ndimage.zoom(self._raw_image, 25)  # interpolate with scipy
            self._image = cv2.applyColorMap(self._image, cmapy.cmap(self._colormap_list[self._colormap_index]))
        elif self._interpolation_index == 6:  # Scale partially via scipy and partially via cv2 - mix of speed and quality
            self._image = ndimage.zoom(self._raw_image, 10)  # interpolate with scipy
            self._image = cv2.applyColorMap(self._image, cmapy.cmap(self._colormap_list[self._colormap_index]))
            self._image = cv2.resize(self._image, (800, 600), interpolation=cv2.INTER_CUBIC)
        else:
            self._image = cv2.applyColorMap(self._raw_image, cmapy.cmap(self._colormap_list[self._colormap_index]))
            self._image = cv2.resize(self._image, (800, 600), interpolation=self._interpolation_list[self._interpolation_index])
        self._image = cv2.flip(self._image, 1)
        if self.filter_image:
            self._image = cv2.bilateralFilter(self._image, 15, 80, 80)

    def _add_image_text(self):
        """Set image text content"""
        if self.use_f:
            temp_min = self._c_to_f(self._temp_min)
            temp_max = self._c_to_f(self._temp_max)
            text = f"Tmin={temp_min:+.1f}F - Tmax={temp_max:+.1f}F - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}"
        else:
            text = f"Tmin={self._temp_min:+.1f}C - Tmax={self._temp_max:+.1f}C - FPS={1/(time.time() - self._t0):.1f} - Interpolation: {self._interpolation_list_name[self._interpolation_index]} - Colormap: {self._colormap_list[self._colormap_index]} - Filtered: {self.filter_image}"
        cv2.putText(self._image, text, (30, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255),1)
        self._t0 = time.time()  # Update time to this pull

        # For a brief period after saving, display saved notification
        if self._file_saved_notification_start is not None and (time.monotonic() - self._file_saved_notification_start) < 1:
            cv2.putText(self._image, "Snapshot Saved!", (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    def add_customized_text(self, text):
        """Add custom text to the center of the image, used mostly to notify user that server is off."""
        cv2.putText(self._image, text, (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        time.sleep(0.1)

    def _show_processed_image(self):
        """Resize image window and display it"""
        cv2.namedWindow("Thermal Image", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Thermal Image", self.image_width, self.image_height)
        cv2.imshow("Thermal Image", self._image)

    def display_next_frame_onscreen(self):
        """Display the camera live to the display"""
        # Display shortcuts reminder to user on first run
        if not self._displaying_onscreen:
            self._print_shortcuts_keys()
            self._displaying_onscreen = True
        self.update_image_frame()
        self._show_processed_image()
        self._set_click_keyboard_events()

    def change_colormap(self, forward: bool = True):
        """Cycle colormap. Forward by default, backwards if param set to false."""
        if forward:
            self._colormap_index += 1
            if self._colormap_index == len(self._colormap_list):
                self._colormap_index = 0
        else:
            self._colormap_index -= 1
            if self._colormap_index < 0:
                self._colormap_index = len(self._colormap_list) - 1

    def change_interpolation(self, forward: bool = True):
        """Cycle interpolation. Forward by default, backwards if param set to false."""
        if forward:
            self._interpolation_index += 1
            if self._interpolation_index == len(self._interpolation_list):
                self._interpolation_index = 0
        else:
            self._interpolation_index -= 1
            if self._interpolation_index < 0:
                self._interpolation_index = len(self._interpolation_list) - 1

    def update_image_frame(self, annotate=False):
        """Pull raw temperature data, process it to an image, and update image text"""
        self._pull_raw_image()
        self._process_raw_image()
        if annotate:
            self._add_image_text()
        self._current_frame_processed = True
        return self._image

    def update_raw_image_only(self):
        """Update only raw data without any further image processing or text updating"""
        self._pull_raw_image

    def get_current_raw_image_frame(self):
        """Return the current raw image"""
        self._pull_raw_image
        return self._raw_image

    def get_current_image_frame(self):
        """Get the processed image"""
        # If the current raw image hasn't been procssed, process and return it
        if not self._current_frame_processed:
            self._process_raw_image()
            self._add_image_text()
            self._current_frame_processed = True
        return self._image

    def save_image(self):
        """Save the current frame as a snapshot to the output folder."""
        fname = self.output_folder + "pic_" + dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        cv2.imwrite(fname, self._image)
        self._file_saved_notification_start = time.monotonic()
        print("Thermal Image ", fname)

    def _temps_to_rescaled_uints(self, f, Tmin, Tmax):
        """Function to convert temperatures to pixels on image"""
        f = np.nan_to_num(f)
        norm = np.uint8((f - Tmin) * 255 / (Tmax - Tmin))
        norm.shape = (24, 32)
        return norm


def getAllskyDate():
    dtNow = datetime.now()
    dt = dtNow - timedelta(hours=12)
    dateStr = dt.strftime("%Y%m%d")
    timeStr = dt.strftime("%H%M%S")

    return dateStr, timeStr


def mlx90640(params, event):
    imageFileName = params["imagefilename"]
    logData = params["logdata"]
    roi = params["roi"]
    imagePath = os.path.join(os.environ["ALLSKY_OVERLAY"], "images", imageFileName)
    imageThumbnailPath = os.path.join(os.environ["ALLSKY_OVERLAY"], "imagethumbnails", imageFileName)

    region = None
    if roi:
        region = list(map(int, roi.split(',')))
        if len(region) != 4:
            region = None

    extradatafilename = "mlx90640.json"
    cam = pithermalcam()
    img = cam.update_image_frame()
    cv2.imwrite(imagePath, img)

    width = img.shape[1]
    scale_percent = (90 / width) * 100

    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)

    # resize image
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    cv2.imwrite(imageThumbnailPath, resized)

    temp_c, temp_f, min, max = cam.get_mean_temp(region)
    extraData = {}
    extraData["AS_MLX90640_C"] = str(round(temp_c, 2))
    extraData["AS_MLX90640_f"] = str(round(temp_f, 2))
    extraData["AS_MLX90640MAX_C"] = str(round(max, 2))
    extraData["AS_MLX90640MIN_C"] = str(round(min, 2))

    s.saveExtraData(extradatafilename, extraData)

    if logData:
        dateStr, timeStr = getAllskyDate()
        allskyHome = os.environ["ALLSKY_HOME"]
        irDir = os.path.join(allskyHome, "config", "overlay", "ir", dateStr)
        fileName, fileExtension = os.path.splitext(imageFileName)
        irImageName = os.path.join(irDir, f"{dateStr}{timeStr}{fileExtension}")
        dataFileName = os.path.join(irDir, f"{dateStr}.csv")

        s.checkAndCreateDirectory(irDir)

        if not os.path.isfile(dataFileName):
            attr = "w"
        else:
            attr = "a"

        fh = open(dataFileName, attr)
        writer = csv.writer(fh)

        if attr == "w":
            writer.writerow(["date", "time", "min", "max", "mean"])

        writer.writerow(
            [
                dateStr,
                timeStr,
                extraData["AS_MLX90640MIN_C"],
                extraData["AS_MLX90640MAX_C"],
                extraData["AS_MLX90640_C"],
            ]
        )

        fh.close()

        cv2.imwrite(irImageName, resized)
