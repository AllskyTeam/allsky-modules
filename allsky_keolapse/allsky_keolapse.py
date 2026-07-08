'''
allsky_keolapse.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

Creates a timelapse video with the night's keogram wrapped as a ring
around the circular sky image, with a progress sweep showing the
current position in the night.

Inspired by Indi Allsky's keogram timelapse feature.
https://github.com/aaronwmorris/indi-allsky
'''
import os
import glob
import shutil
import subprocess
from datetime import datetime, timedelta

import cv2
import numpy as np

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

VIDEO_QUALITY = {
	'low': {'bitrate': '2000k', 'quality': 23},
	'medium': {'bitrate': '4000k', 'quality': 20},
	'high': {'bitrate': '8000k', 'quality': 17}
}


class KEOLAPSEGENERATOR:
	'''Handles keogram ring generation and application to images.

	Receives the parent module instance so it can use the module's typed
	settings and logging.
	'''

	def __init__(self, module, scale_factor=1.0):
		self.module = module
		self.scale_factor = scale_factor
		self.circle_center = None
		self.circle_radius = None
		self.keogram_height = int(module.keogram_height * scale_factor)
		self.circle_padding = int(module.circle_padding * scale_factor)
		self.edge_padding = int(module.edge_padding * scale_factor)
		self.start_position = module.start_position
		self.angle_offset = {
			12: 90,
			3: 180,
			6: 270,
			9: 0
		}.get(self.start_position, 90)
		self.circle_radius_factor = module.circle_radius_factor
		self.center_x_offset = int(module.center_x_offset * scale_factor)
		self.center_y_offset = int(module.center_y_offset * scale_factor)
		self.expanded_image = None
		self.expansion = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

	def detect_circle(self, image):
		'''Set circle parameters with dynamic scaling, expanding the image if needed.'''
		try:
			height, width = image.shape[:2]

			center_x = width // 2 + self.center_x_offset
			center_y = height // 2 + self.center_y_offset
			radius = int(min(width, height) * self.circle_radius_factor)

			required_space = radius + self.keogram_height + self.circle_padding

			expansion_needed = False
			self.expansion = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

			if center_y - required_space < 0:
				self.expansion['top'] = abs(center_y - required_space) + self.edge_padding
				expansion_needed = True

			if center_y + required_space >= height:
				self.expansion['bottom'] = (center_y + required_space) - height + self.edge_padding
				expansion_needed = True

			if center_x - required_space < 0:
				self.expansion['left'] = abs(center_x - required_space) + self.edge_padding
				expansion_needed = True

			if center_x + required_space >= width:
				self.expansion['right'] = (center_x + required_space) - width + self.edge_padding
				expansion_needed = True

			if expansion_needed:
				self.module.klog(
					1,
					f"Expanding image to fit keogram ring: top={self.expansion['top']}, "
					f"bottom={self.expansion['bottom']}, left={self.expansion['left']}, "
					f"right={self.expansion['right']}"
				)

				self.expanded_image = cv2.copyMakeBorder(
					image,
					self.expansion['top'], self.expansion['bottom'],
					self.expansion['left'], self.expansion['right'],
					cv2.BORDER_CONSTANT, value=[0, 0, 0]
				)

				center_x += self.expansion['left']
				center_y += self.expansion['top']
			else:
				self.expanded_image = image.copy()

			self.circle_center = (center_x, center_y)
			self.circle_radius = radius

			self.module.klog(2, f'Circle detection: center=({center_x}, {center_y}), radius={radius}', debug_only=True)

			return True

		except Exception as e:
			self.module.klog(0, f'ERROR: setting circle parameters failed: {e}')
			return False

	def prepare_keogram(self, keogram_path):
		'''Prepare keogram for overlay with scaling. Returns (keogram, progress) or (None, None).'''
		try:
			if keogram_path is True:  # circles-only mode, no keogram needed
				dummy_img = np.zeros((self.keogram_height, 100, 3), dtype=np.uint8)
				return dummy_img, dummy_img

			keogram = cv2.imread(keogram_path)
			if keogram is None:
				raise Exception(f'Failed to load keogram: {keogram_path}')

			circumference = 2 * np.pi * (self.circle_radius + self.circle_padding)
			new_width = int(circumference)

			keogram_resized = cv2.resize(
				keogram, (new_width, self.keogram_height),
				interpolation=cv2.INTER_LANCZOS4
			)

			progress = np.zeros_like(keogram_resized)

			hour_width = new_width // 24
			font_scale = max(0.3, 0.5 * self.scale_factor)

			for i in range(24):
				x = i * hour_width
				cv2.line(
					progress, (x, 0), (x, self.keogram_height),
					(50, 50, 50), max(1, int(1 * self.scale_factor))
				)
				cv2.putText(
					progress, f'{i:02d}',
					(x + 5, self.keogram_height - 5),
					cv2.FONT_HERSHEY_SIMPLEX, font_scale,
					(100, 100, 100), max(1, int(1 * self.scale_factor))
				)

			return keogram_resized, progress

		except Exception as e:
			self.module.klog(0, f'ERROR: preparing keogram failed: {e}')
			return None, None

	def draw_debug_circles(self, image):
		'''Draw debug circles on image without keogram overlay.'''
		try:
			result = image.copy()
			height, width = result.shape[:2]

			# Inner circle (at circle_radius)
			cv2.circle(result, self.circle_center, self.circle_radius, (0, 255, 0), 2)

			# Middle circle (at circle_radius + padding)
			cv2.circle(
				result, self.circle_center,
				self.circle_radius + self.circle_padding,
				(255, 0, 0), 2
			)

			# Outer circle (at circle_radius + padding + keogram_height)
			cv2.circle(
				result, self.circle_center,
				self.circle_radius + self.circle_padding + self.keogram_height,
				(0, 255, 255), 2
			)

			cv2.drawMarker(
				result, self.circle_center, (255, 0, 255),
				markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2
			)

			debug_text = 'DEBUG CIRCLES ONLY MODE'
			font = cv2.FONT_HERSHEY_SIMPLEX
			for i in range(3):
				x = (width // 3) * i + 50
				cv2.putText(result, debug_text, (x, height - 20), font, 1, (0, 0, 255), 2)

			return result

		except Exception as e:
			self.module.klog(0, f'ERROR: drawing debug circles failed: {e}')
			return image

	def wrap_keogram(self, base_image, keogram, progress_indicator, frame_idx, total_frames):
		'''Map keogram around the circular image with corrected angle mapping.'''
		try:
			# Use the expanded image (may equal base_image if no expansion was needed)
			result = self.expanded_image.copy()
			height, width = result.shape[:2]

			if self.module.show_circles_only:
				return self.draw_debug_circles(result)

			progress_x = int((frame_idx / total_frames) * progress_indicator.shape[1])
			progress_copy = progress_indicator.copy()

			for i in range(4):
				marker_x = max(0, progress_x - i)
				intensity = 255 - (i * 50)
				cv2.line(
					progress_copy, (marker_x, 0), (marker_x, self.keogram_height),
					(intensity, intensity, intensity), 2
				)

			cv2.line(
				progress_copy, (progress_x, 0), (progress_x, self.keogram_height),
				(255, 255, 255), 4
			)

			y, x = np.mgrid[:height, :width]
			dx = x - self.circle_center[0]
			dy = y - self.circle_center[1]

			radius = np.sqrt(dx ** 2 + dy ** 2)
			angle = np.degrees(np.arctan2(dy, dx))
			angle = np.where(angle < 0, angle + 360, angle)
			angle = (angle + self.angle_offset) % 360

			ring_mask = (radius > (self.circle_radius + self.circle_padding)) & \
				(radius < (self.circle_radius + self.circle_padding + self.keogram_height))

			keogram_x = ((angle[ring_mask] / 360) * keogram.shape[1]).astype(int)
			keogram_y = (radius[ring_mask] - (self.circle_radius + self.circle_padding)).astype(int)

			keogram_x = np.clip(keogram_x, 0, keogram.shape[1] - 1)
			keogram_y = np.clip(keogram_y, 0, keogram.shape[0] - 1)

			combined = cv2.addWeighted(keogram, 0.8, progress_copy, 0.2, 0)
			result[ring_mask] = combined[keogram_y, keogram_x]

			if self.module.show_circles:
				cv2.circle(result, self.circle_center, self.circle_radius, (0, 255, 0), 1)
				cv2.circle(
					result, self.circle_center,
					self.circle_radius + self.circle_padding, (255, 0, 0), 1
				)
				cv2.circle(
					result, self.circle_center,
					self.circle_radius + self.circle_padding + self.keogram_height,
					(0, 255, 255), 1
				)

			if self.module.show_circles or self.module.show_example:
				debug_text = 'DEBUG ENABLED'
				font = cv2.FONT_HERSHEY_SIMPLEX
				for i in range(3):
					x = (result.shape[1] // 3) * i + 50
					cv2.putText(result, debug_text, (x, height - 20), font, 1, (0, 0, 255), 2)

			return result

		except Exception as e:
			self.module.klog(0, f'ERROR: wrapping keogram failed: {e}')
			return base_image


class ALLSKYKEOLAPSE(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Keolapse Generator",
		"description": "Creates a timelapse video with the keogram wrapped as a ring around the sky image",
		"module": "allsky_keolapse",
		"version": "v0.9.3",
		"pythonversion": "3.10.0",
		"centersettings": "false",
		"testable": "true",
		"group": "Video",
		"events": [
			"nightday",
			"periodic"
		],
		"experimental": "true",
		"enabled": "false",
		"extradatafilename": "allsky_keolapse.json",
		"extradata": {
			"values": {
				"AS_KEOLAPSE_VIDEO": {
					"name": "${KEOLAPSE_VIDEO}",
					"format": "",
					"sample": "",
					"group": "Keolapse",
					"description": "Full path of the last keolapse video created",
					"type": "string"
				},
				"AS_KEOLAPSE_DATE": {
					"name": "${KEOLAPSE_DATE}",
					"format": "",
					"sample": "",
					"group": "Keolapse",
					"description": "Date (YYYYMMDD) of the last keolapse video created",
					"type": "string"
				},
				"AS_KEOLAPSE_FRAMES": {
					"name": "${KEOLAPSE_FRAMES}",
					"format": "{dp=0}",
					"sample": "",
					"group": "Keolapse",
					"description": "Number of frames in the last keolapse video",
					"type": "number"
				},
				"AS_KEOLAPSE_DURATION": {
					"name": "${KEOLAPSE_DURATION}",
					"format": "{dp=1}",
					"sample": "",
					"group": "Keolapse",
					"description": "Duration in seconds of the last keolapse video",
					"type": "number"
				}
			}
		},
		"arguments": {
			"use_timelapse_settings": "false",
			"video_quality": "medium",
			"framerate": "12",
			"max_length": "120",
			"upload": "false",
			"upload_subdir": "keolapses",
			"upload_thumbnail": "true",
			"thumbnail_width": "100",
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
			"start_position": "12",
			"enable_testing": "false",
			"generate_test_data": "false",
			"test_mode": "false",
			"process_date": "",
			"show_circles": "false",
			"show_circles_only": "false",
			"show_example": "false",
			"upload_test": "false",
			"debug_mode": "false"
		},
		"argumentdetails": {
			"use_timelapse_settings": {
				"required": "false",
				"description": "Use Timelapse Settings",
				"help": "When checked, uses the timelapse settings (width, height, FPS, bitrate, codec, pixel format) from the main Allsky Settings instead of the values below.",
				"tab": "Video",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"video_quality": {
				"required": "true",
				"description": "Video Quality",
				"help": "Output video quality and compression.",
				"tab": "Video",
				"type": {
					"fieldtype": "select",
					"values": "low,medium,high"
				}
			},
			"framerate": {
				"required": "true",
				"description": "Framerate",
				"help": "Frames per second in output video. Higher values create smoother but faster videos.",
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
				"help": "Target resolution of output video. Higher resolutions require more processing time.",
				"tab": "Video",
				"type": {
					"fieldtype": "select",
					"values": "720p,1080p,4k"
				}
			},
			"max_length": {
				"required": "true",
				"description": "Maximum Video Length",
				"help": "Target maximum length in seconds. Longer videos require more processing time and storage.",
				"tab": "Video",
				"type": {
					"fieldtype": "spinner",
					"min": 30,
					"max": 300,
					"step": 30
				}
			},
			"upload": {
				"required": "false",
				"description": "Upload",
				"help": "Enable to upload the keolapse video to a local/remote Allsky Website and/or remote server, into the subdirectory named below.<br><i>Note: Website(s) or remote server must be configured in Allsky Settings. For remote uploads the subdirectory must already exist on the server.</i>",
				"tab": "Video",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"upload_subdir": {
				"required": "false",
				"description": "Upload Subdirectory",
				"help": "Subdirectory under the website/server image directory to upload keolapse videos into (e.g. <code>keolapses</code>). Keeps keolapse videos separate from the regular timelapse <code>videos</code> directory. The uploaded file keeps its dated name (keolapse-YYYYMMDD.mp4). For remote (sftp/scp/ftp) uploads this directory must already exist on the server.",
				"tab": "Video"
			},
			"upload_thumbnail": {
				"required": "false",
				"description": "Create &amp; Upload Thumbnail",
				"help": "Create a JPEG thumbnail from the video and upload it to a <code>thumbnails</code> subdirectory of the upload directory (e.g. <code>keolapses/thumbnails/keolapse-YYYYMMDD.jpg</code>). Website galleries that pair each video with a thumbnail need this; without it the gallery page may not display the video. For remote uploads the <code>thumbnails</code> directory must already exist on the server.",
				"tab": "Video",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"thumbnail_width": {
				"required": "false",
				"description": "Thumbnail Width",
				"help": "Width in pixels of the generated thumbnail (height scales to keep aspect ratio). Match your website's thumbnail size (Allsky default is 100).",
				"tab": "Video",
				"type": {
					"fieldtype": "spinner",
					"min": 50,
					"max": 400,
					"step": 10
				}
			},
			"alignment_ui": {
				"tab": "Image",
				"source": "file",
				"file": "alignment.html",
				"type": {
					"fieldtype": "html"
				}
			},
			"circle_radius_factor": {
				"required": "true",
				"description": "Circle Radius Factor",
				"help": "Factor to determine circle radius relative to the smaller image dimension (0.1 to 1.0). Usually set with the alignment tool above.",
				"tab": "Image",
				"type": {
					"fieldtype": "spinner",
					"min": 0.1,
					"max": 1.0,
					"step": 0.0001
				}
			},
			"center_x_offset": {
				"required": "true",
				"description": "Center X Offset",
				"help": "Offset from image center for circle center X coordinate (in pixels, right/left).",
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
				"help": "Offset from image center for circle center Y coordinate (in pixels, up/down).",
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
				"help": "Height of keogram ring in pixels.",
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
				"help": "Additional pixels above the sky image. Adjust for balanced appearance.",
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
				"help": "Additional pixels below the sky image. Adjust for balanced appearance.",
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
				"help": "Additional pixels to the left of the sky image. Usually 0.",
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
				"help": "Additional pixels to the right of the sky image. Usually 0.",
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
				"help": "Spacing between inside sky image and keogram ring, in pixels.",
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
				"help": "Spacing from image edges in pixels.",
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
				"help": "Clock hour position to start keogram (12: top, 3: right, 6: bottom, 9: left).",
				"tab": "Image",
				"type": {
					"fieldtype": "select",
					"values": "12,3,6,9"
				}
			},
			"enable_testing": {
				"required": "false",
				"description": "Enable Testing Mode",
				"help": "Master switch for all testing features. Enable this to use test mode and debug features.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"generate_test_data": {
				"required": "false",
				"description": "Generate Test Data (run once)",
				"help": "Intended to speed up video testing. Copies one hour of last night's data (11PM-12AM) to the <code>test</code> folder under the Allsky images directory. Uncheck this after generation.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"test_mode": {
				"required": "false",
				"description": "Use Test Data",
				"help": "Use the test folder instead of last night's image folder. Quicker for getting set up!",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"process_date": {
				"required": "false",
				"description": "Older Date to Process (YYYYMMDD)",
				"help": "Optional: Specify a date to process (format: YYYYMMDD). Leave empty to process last night's data (or test data if selected above).",
				"tab": "Testing"
			},
			"show_circles": {
				"required": "false",
				"description": "Show Debug Circles",
				"help": "Draw inner and outer keogram ring circles for alignment testing.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"show_circles_only": {
				"required": "false",
				"description": "Debug Circles Only",
				"help": "Draw circles only (no keogram ring) for alignment testing.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"show_example": {
				"required": "false",
				"description": "Create Test Image",
				"help": "Generate single test image with keogram overlay for preview.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"upload_test": {
				"required": "false",
				"description": "Upload test video",
				"help": "Enable to upload the keolapse video to configured Allsky Websites or remote servers when using the [Test Module] button.",
				"tab": "Testing",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"debug_mode": {
				"required": "false",
				"description": "Debug Mode",
				"help": "Enable detailed logging for troubleshooting. Also writes a log to <code>tmp/logs/keolapse_debug.log</code>.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			}
		},
		"businfo": [],
		"changelog": {
			"v0.9.3": [
				{
					"author": "Andy Felong",
					"authorurl": "https://github.com/AndyOfLinux",
					"changes": [
						"Added interactive circle alignment tool to the Image tab: the current capture image is shown with the keogram ring circles overlaid; drag or use arrow keys to move the centre, drag the handle / mouse wheel / +- keys to resize",
						"Alignment tool includes black mask display modes (disc or surround) with adjustable opacity for fine alignment against the sky image",
						"On-screen nudge buttons (centre arrows, radius +/-) with Shift-click for 10 px steps and hold-to-repeat, for mouse and touch use",
						"Circle Radius Factor spinner step reduced from 0.01 to 0.0001 for pixel-level radius control"
					]
				}
			],
			"v0.9.2": [
				{
					"author": "Andy Felong",
					"authorurl": "https://github.com/AndyOfLinux",
					"changes": [
						"Create a JPEG thumbnail from the video and upload it to a 'thumbnails' subdirectory (keolapse-YYYYMMDD.jpg), matching the Allsky website gallery convention",
						"Added 'Create & Upload Thumbnail' (default on) and 'Thumbnail Width' (default 100) settings",
						"Refactored upload into a reusable helper shared by the video and thumbnail uploads"
					]
				}
			],
			"v0.9.1": [
				{
					"author": "Andy Felong",
					"authorurl": "https://github.com/AndyOfLinux",
					"changes": [
						"Fixed upload overwriting the regular timelapse video: keolapse now uploads into its own subdirectory (default 'keolapses') with its dated filename instead of the videos directory / timelapse destination name",
						"Added 'Upload Subdirectory' setting (default 'keolapses')",
						"Corrected remote-server setting name (useremoteserver)",
						"Local website upload subdirectory is created automatically; clearer error when a remote subdirectory is missing"
					]
				}
			],
			"v0.9.0": [
				{
					"author": "Andy Felong",
					"authorurl": "https://github.com/AndyOfLinux",
					"changes": [
						"Refactored to Allsky v2025 module architecture (ALLSKYMODULEBASE class)",
						"Core timelapse settings now read via allsky_shared.getSetting() instead of parsing settings.json",
						"Image extension derived from the Allsky 'filename' setting instead of EXTENSION env var",
						"Replaced hardcoded upload script with standard Allsky upload.sh (local/remote website, remote server)",
						"Periodic event now only runs when testing is enabled (prevents accidental video generation every periodic cycle)",
						"Publishes AS_KEOLAPSE_* overlay variables (video path, date, frames, duration)",
						"Supports the WebUI [Test Module] button"
					]
				}
			],
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

	def __init__(self, params, event):
		super().__init__(params, event)

		# Core Allsky environment
		self._allsky_home = allsky_shared.getEnvironmentVariable('ALLSKY_HOME', fatal=True)
		self._images_dir = allsky_shared.getEnvironmentVariable('ALLSKY_IMAGES', fatal=True)
		self._tmp_dir = allsky_shared.getEnvironmentVariable('ALLSKY_TMP', fatal=True)
		self._log_dir = os.path.join(self._tmp_dir, 'logs')
		self._log_file = os.path.join(self._log_dir, 'keolapse_debug.log')

		# Image extension from the core 'filename' setting (e.g. image.jpg -> jpg)
		full_file_name = allsky_shared.getSetting('filename') or 'image.jpg'
		_, file_ext = os.path.splitext(full_file_name)
		self._extension = file_ext.lstrip('.') or 'jpg'

		# Video settings
		self.use_timelapse_settings = self._get_bool('use_timelapse_settings', False)
		self.video_quality = self.get_param('video_quality', 'medium', str, True)
		self.framerate = self.get_param('framerate', 12, int)
		self.max_length = self.get_param('max_length', 120, int)
		self.resolution = self.get_param('resolution', '720p', str, True)
		self.upload = self._get_bool('upload', False)
		self.upload_subdir = (self.get_param('upload_subdir', 'keolapses', str) or 'keolapses').strip().strip('/')
		self.upload_thumbnail = self._get_bool('upload_thumbnail', True)
		self.thumbnail_width = self.get_param('thumbnail_width', 100, int)

		# Image / ring settings
		self.circle_radius_factor = self.get_param('circle_radius_factor', 0.47, float)
		self.center_x_offset = self.get_param('center_x_offset', 0, int)
		self.center_y_offset = self.get_param('center_y_offset', 0, int)
		self.keogram_height = self.get_param('keogram_height', 175, int)
		self.top_padding = self.get_param('top_padding', 5, int)
		self.bottom_padding = self.get_param('bottom_padding', 5, int)
		self.left_padding = self.get_param('left_padding', 5, int)
		self.right_padding = self.get_param('right_padding', 5, int)
		self.circle_padding = self.get_param('circle_padding', 5, int)
		self.edge_padding = self.get_param('edge_padding', 5, int)
		self.start_position = self.get_param('start_position', 12, int)

		# Testing / debug settings
		self.enable_testing = self._get_bool('enable_testing', False)
		self.generate_test_data_flag = self.enable_testing and self._get_bool('generate_test_data', False)
		self.test_mode = self.enable_testing and self._get_bool('test_mode', False)
		self.process_date = self.get_param('process_date', '', str).strip()
		self.show_circles = self.enable_testing and self._get_bool('show_circles', False)
		self.show_circles_only = self.enable_testing and self._get_bool('show_circles_only', False)
		self.show_example = self.enable_testing and self._get_bool('show_example', False)
		self.upload_test = self._get_bool('upload_test', False)
		self.debug_mode_param = self._get_bool('debug_mode', False)

	def _get_bool(self, param, default):
		'''Boolean parameter, safe for both JSON booleans and "true"/"false" strings.'''
		value = self.params.get(param, default)
		if isinstance(value, bool):
			return value
		return str(value).strip().lower() in ('true', '1', 'yes', 'on')

	@staticmethod
	def _setting_bool(name):
		'''Truthiness of a core Allsky setting (handles bools, 1/0 and "true" strings).'''
		value = allsky_shared.getSetting(name)
		if isinstance(value, bool):
			return value
		if value is None:
			return False
		return str(value).strip().lower() in ('true', '1', 'yes', 'on')

	@staticmethod
	def _setting_int(name, default):
		try:
			return int(allsky_shared.getSetting(name))
		except (TypeError, ValueError):
			return default

	@staticmethod
	def _setting_str(name, default):
		value = allsky_shared.getSetting(name)
		if value is None or str(value).strip() == '':
			return default
		return str(value)

	def klog(self, level, message, debug_only=False):
		'''Module logging. Goes to the Allsky log; optionally mirrored to a debug file.'''
		if debug_only and not self.debug_mode_param:
			return

		self.log(level, f'KEOLAPSE: {message}')

		if not self.debug_mode_param:
			return

		try:
			os.makedirs(self._log_dir, exist_ok=True)
			prefix = 'ERROR' if level == 0 else 'INFO' if level == 1 else 'DEBUG'
			timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
			with open(self._log_file, 'a', encoding='utf-8') as f:
				f.write(f'{timestamp} - [{prefix}] {message}\n')
		except Exception as e:
			print(f'KEOLAPSE LOGGING ERROR: {e}')

	def _get_core_timelapse_settings(self):
		'''Core Allsky timelapse settings via allsky_shared.getSetting().'''
		settings = {
			'width': self._setting_int('timelapsewidth', 0),
			'height': self._setting_int('timelapseheight', 0),
			'bitrate': self._setting_int('timelapsebitrate', 5000),
			'fps': self._setting_int('timelapsefps', 12),
			'vcodec': self._setting_str('timelapsevcodec', 'libx264'),
			'pixfmt': self._setting_str('timelapsepixfmt', 'yuv420p'),
			'fflog': self._setting_str('timelapsefflog', 'warning')
		}
		self.klog(1, f'Loaded core timelapse settings: {settings}')
		return settings

	def _get_target_date(self):
		'''Target date in YYYYMMDD format, using process_date if specified.'''
		if self.process_date:
			try:
				datetime.strptime(self.process_date, '%Y%m%d')
				self.klog(1, f'Using specified date: {self.process_date}')
				return self.process_date
			except ValueError:
				self.klog(0, f'ERROR: Invalid date format: {self.process_date}, using yesterday')

		return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

	def _get_source_directory(self):
		'''Source directory based on test mode and process_date.'''
		source_dir = os.path.join(self._images_dir, 'test' if self.test_mode else self._get_target_date())

		if not os.path.exists(source_dir):
			self.klog(0, f'ERROR: Directory not found: {source_dir}')
			return None

		return source_dir

	def _get_source_images(self):
		'''Sorted list of source image paths.'''
		try:
			source_dir = self._get_source_directory()
			if source_dir is None:
				self.klog(0, 'ERROR: Cannot proceed without valid source directory')
				return []

			self.klog(2, f'Searching for images in: {source_dir}', debug_only=True)

			image_pattern = os.path.join(source_dir, f'image-*.{self._extension}')
			images = sorted(glob.glob(image_pattern))

			if not images:
				self.klog(0, f'ERROR: No images found matching {image_pattern}')
				return []

			estimated_length = len(images) / self.framerate
			minutes = int(estimated_length // 60)
			seconds = int(estimated_length % 60)

			self.klog(1, f'Found {len(images)} images')
			self.klog(1, f'Estimated video length: {minutes}:{seconds:02d} at {self.framerate} fps')

			return images

		except Exception as e:
			self.klog(0, f'ERROR: Failed to get source images: {e}')
			return []

	@staticmethod
	def _ensure_dir(path):
		os.makedirs(path, exist_ok=True)
		return path

	def _get_keogram_path(self):
		'''Path to the keogram for the source directory (or True in circles-only mode).'''
		source_dir = self._get_source_directory()
		if source_dir is None:
			self.klog(0, 'ERROR: Cannot locate keogram without valid source directory')
			return None

		if self.show_circles_only:
			self.klog(1, 'Debug circles only mode - no keogram needed')
			return True

		keogram_dir = os.path.join(source_dir, 'keogram')
		self.klog(2, f'Searching for keogram in: {keogram_dir}', debug_only=True)

		if not os.path.exists(keogram_dir):
			self.klog(0, f'ERROR: Keogram directory not found: {keogram_dir}')
			return None

		# Prefer the configured image extension; fall back to any common type
		for pattern in (f'keogram*.{self._extension}', 'keogram*.jpg', 'keogram*.png'):
			keogram_files = sorted(glob.glob(os.path.join(keogram_dir, pattern)))
			if keogram_files:
				self.klog(1, f'Using keogram: {os.path.basename(keogram_files[0])}')
				return keogram_files[0]

		self.klog(0, 'ERROR: No keogram found')
		return None

	def _get_output_path(self, filename):
		'''Full path for an output file, ensuring the directory exists.'''
		source_dir = self._get_source_directory()
		if source_dir is None:
			self.klog(0, 'ERROR: Using fallback output path due to missing source directory')
			output_dir = self._ensure_dir(os.path.join(self._images_dir, 'keolapse_output'))
		else:
			output_dir = self._ensure_dir(os.path.join(source_dir, 'keolapse'))

		if filename.startswith('keolapse-') and not filename.startswith('keolapse-test'):
			filename = f'keolapse-{self._get_target_date()}.mp4'

		return os.path.join(output_dir, filename)

	def _generate_test_data(self):
		'''Generate test data by copying last night's images and keogram.'''
		try:
			yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
			source_dir = os.path.join(self._images_dir, yesterday)
			test_dir = os.path.join(self._images_dir, 'test')

			if not os.path.exists(source_dir):
				self.klog(0, f'ERROR: Source directory not found: {source_dir}')
				return False

			if os.path.exists(test_dir):
				test_images = glob.glob(os.path.join(test_dir, f'image-*.{self._extension}'))
				if test_images and self._test_date_is_current(test_images[0], yesterday):
					self.klog(1, 'Test data is current')
					return True
				shutil.rmtree(test_dir)

			os.makedirs(test_dir)

			# Copy a subset of night images (23:00-00:00)
			night_pattern = os.path.join(source_dir, f'image-{yesterday}23*.{self._extension}')
			night_images = sorted(glob.glob(night_pattern))

			if not night_images:
				self.klog(0, 'ERROR: No night images found')
				return False

			for img in night_images:
				shutil.copy2(img, os.path.join(test_dir, os.path.basename(img)))

			source_keogram = os.path.join(source_dir, 'keogram')
			if os.path.exists(source_keogram):
				shutil.copytree(source_keogram, os.path.join(test_dir, 'keogram'))

			self.klog(1, f'Generated test data with {len(night_images)} images')
			return True

		except Exception as e:
			self.klog(0, f'ERROR: generating test data failed: {e}')
			return False

	@staticmethod
	def _test_date_is_current(test_image, target_date):
		'''Check if test data matches target date.'''
		try:
			test_date = os.path.basename(test_image).split('-')[1][:8]
			return test_date == target_date
		except Exception:
			return False

	def _cleanup_test_data(self):
		'''Clean up test data during nightday transition.'''
		if self.event == 'nightday':
			try:
				test_dir = os.path.join(self._images_dir, 'test')
				if os.path.exists(test_dir):
					shutil.rmtree(test_dir)
					self.klog(1, 'Cleaned up test data')
			except Exception as e:
				self.klog(0, f'ERROR: cleaning test data failed: {e}')

	def _create_debug_image(self, images):
		'''Generate debug test image with keogram overlay.'''
		try:
			if not images:
				return False

			mid_idx = len(images) // 2
			test_image = images[mid_idx]

			frame = cv2.imread(test_image)
			if frame is None:
				self.klog(0, f'ERROR: Failed to load test image: {test_image}')
				return False

			original_height, original_width = frame.shape[:2]
			new_width, new_height, scale_factor = self._calculate_scaled_dimensions(
				original_width, original_height)

			generator = KEOLAPSEGENERATOR(self, scale_factor)

			scaled_frame = cv2.resize(
				frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

			top_pad = int(self.top_padding * scale_factor)
			bottom_pad = int(self.bottom_padding * scale_factor)
			left_pad = int(self.left_padding * scale_factor)
			right_pad = int(self.right_padding * scale_factor)

			padded = cv2.copyMakeBorder(
				scaled_frame,
				top_pad, bottom_pad,
				left_pad, right_pad,
				cv2.BORDER_CONSTANT, value=[0, 0, 0]
			)

			if not generator.detect_circle(padded):
				return False

			if self.show_circles_only:
				result = generator.draw_debug_circles(generator.expanded_image.copy())
				output_path = self._get_output_path('keolapse_debug_circles.jpg')
				cv2.imwrite(output_path, result)
				self.klog(1, f'Created debug circles image: {output_path}')
				return True

			keogram_path = self._get_keogram_path()
			if not keogram_path:
				return False

			keogram_data = generator.prepare_keogram(keogram_path)
			if keogram_data[0] is None:
				return False

			result = generator.wrap_keogram(
				padded, keogram_data[0], keogram_data[1], mid_idx, len(images))

			output_path = self._get_output_path('keolapse_debug.jpg')
			cv2.imwrite(output_path, result)
			self.klog(1, f'Created debug image: {output_path}')

			return True

		except Exception as e:
			self.klog(0, f'ERROR: creating debug image failed: {e}')
			return False

	def _optimize_video_params(self, images, fps):
		'''Reduce frame count / adjust fps to hit the target duration.'''
		MIN_FPS = 5
		MAX_FPS = 30
		target_duration = self.max_length

		total_frames = len(images)
		current_duration = total_frames / fps

		self.klog(2, f'Initial duration: {current_duration:.1f} seconds', debug_only=True)

		if current_duration <= target_duration:
			return images, fps

		ideal_frame_count = int(target_duration * fps)
		skip_interval = max(1, total_frames // ideal_frame_count)
		optimized_images = images[::skip_interval]

		optimized_fps = min(MAX_FPS, max(MIN_FPS, len(optimized_images) / target_duration))

		self.klog(1, 'Optimization results:')
		self.klog(1, f'- Original frames: {total_frames}')
		self.klog(1, f'- Optimized frames: {len(optimized_images)}')
		self.klog(2, f'- Frames kept: 1 in every {skip_interval}', debug_only=True)
		self.klog(1, f'- Final duration: {len(optimized_images) / optimized_fps:.1f} seconds')

		return optimized_images, int(optimized_fps)

	def _should_optimize_video(self, images, fps):
		'''Determine if video optimization should be applied.'''
		if len(images) < 300:
			return False

		expected_duration = len(images) / fps
		return expected_duration > self.max_length

	def _calculate_scaled_dimensions(self, original_width, original_height):
		'''Calculate scaled dimensions while maintaining aspect ratio.'''
		target_heights = {
			'720p': 720,
			'1080p': 1080,
			'4k': 2160
		}

		target_height = target_heights.get(self.resolution, 720)

		if original_height < target_height:
			target_height = original_height
			self.klog(1, f'Maintaining original resolution ({original_height}p)')

		scale_factor = target_height / original_height
		new_width = int(original_width * scale_factor)

		self.klog(2, f'Scale factor: {scale_factor:.3f}', debug_only=True)
		self.klog(2, f'New dimensions: {new_width}x{target_height}', debug_only=True)

		return new_width, target_height, scale_factor

	@staticmethod
	def _check_ffmpeg_available():
		try:
			result = subprocess.run(
				['which', 'ffmpeg'], capture_output=True, text=True, check=False)
			return result.returncode == 0
		except Exception:
			return False

	def _create_video(self, images):
		'''Create the keolapse video.

		Returns (success, output_path, frame_count, fps).
		'''
		if not images:
			self.klog(0, 'ERROR: No images found to process')
			return False, None, 0, 0

		try:
			if not self._check_ffmpeg_available():
				self.klog(0, 'ERROR: ffmpeg not found. Please install ffmpeg to create videos.')
				return False, None, 0, 0

			timelapse_settings = None
			use_timelapse_settings = self.use_timelapse_settings
			if use_timelapse_settings:
				timelapse_settings = self._get_core_timelapse_settings()
				self.klog(1, 'Using timelapse settings from Allsky Settings')

			first_frame = cv2.imread(images[0])
			if first_frame is None:
				self.klog(0, f'ERROR: Failed to read first image: {os.path.basename(images[0])}')
				return False, None, 0, 0

			original_height, original_width = first_frame.shape[:2]

			if use_timelapse_settings and timelapse_settings:
				# If timelapsewidth/height is 0, keep original dimensions
				new_width = timelapse_settings['width'] if timelapse_settings['width'] > 0 else original_width
				new_height = timelapse_settings['height'] if timelapse_settings['height'] > 0 else original_height
				scale_factor = min(new_width / original_width, new_height / original_height)

				# Recalculate to maintain aspect ratio
				new_width = int(original_width * scale_factor)
				new_height = int(original_height * scale_factor)

				self.klog(1, f'Using timelapse resolution: {new_width}x{new_height}')
			else:
				new_width, new_height, scale_factor = self._calculate_scaled_dimensions(
					original_width, original_height)

			generator = KEOLAPSEGENERATOR(self, scale_factor)

			top_padding = int(self.top_padding * scale_factor)
			bottom_padding = int(self.bottom_padding * scale_factor)
			left_padding = int(self.left_padding * scale_factor)
			right_padding = int(self.right_padding * scale_factor)

			scaled_frame = cv2.resize(
				first_frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
			padded_frame = cv2.copyMakeBorder(
				scaled_frame,
				top_padding, bottom_padding,
				left_padding, right_padding,
				cv2.BORDER_CONSTANT,
				value=[0, 0, 0]
			)

			if not generator.detect_circle(padded_frame):
				self.klog(0, 'ERROR: Failed to detect circle parameters')
				return False, None, 0, 0

			if not self.show_circles_only:
				keogram_path = self._get_keogram_path()
				if not keogram_path:
					self.klog(0, 'ERROR: No keogram found')
					return False, None, 0, 0

				keogram_data = generator.prepare_keogram(keogram_path)
				if keogram_data[0] is None:
					return False, None, 0, 0
			else:
				self.klog(1, 'Using circles-only mode (no keogram overlay)')
				dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
				keogram_data = (dummy_img, dummy_img)

			if generator.expanded_image is not None:
				height, width = generator.expanded_image.shape[:2]
			else:
				height, width = padded_frame.shape[:2]

			self.klog(1, f'Final frame dimensions: {width}x{height}')

			# Framerate based on settings
			if use_timelapse_settings and timelapse_settings:
				fps = timelapse_settings['fps']
			else:
				fps = self.framerate

			# Apply video optimization if needed
			if self._should_optimize_video(images, fps):
				self.klog(1, 'Video length exceeds maximum, optimizing...')
				images, fps = self._optimize_video_params(images, fps)

			self.klog(1, f'Output video dimensions: {width}x{height} @ {fps}fps')

			# Quality settings
			if use_timelapse_settings and timelapse_settings:
				bitrate = timelapse_settings['bitrate']
				if bitrate <= 3000:
					crf = 23
				elif bitrate <= 6000:
					crf = 20
				else:
					crf = 17
				quality_params = {'bitrate': f'{bitrate}k', 'quality': crf}
				self.klog(1, f'Using timelapse quality settings (bitrate: {bitrate}k)')
			else:
				quality_params = VIDEO_QUALITY.get(self.video_quality, VIDEO_QUALITY['medium'])
				self.klog(1, f'Using video quality: {self.video_quality}')

			self.klog(2, f'Quality parameters: {quality_params}', debug_only=True)

			# Output paths
			if self.test_mode:
				output_filename = 'keolapse-test.mp4'
			else:
				output_filename = f'keolapse-{self._get_target_date()}.mp4'

			output_path = self._get_output_path(output_filename)
			temp_output = output_path.replace('.mp4', '_temp.mp4')

			fourcc = cv2.VideoWriter_fourcc(*'mp4v')
			writer = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

			if not writer.isOpened():
				self.klog(0, 'ERROR: Failed to create video writer')
				return False, None, 0, 0

			total_frames = len(images)
			keogram, progress = keogram_data

			progress_interval = max(1, total_frames // (15 if total_frames > 500 else 10))
			start_time = datetime.now()

			initial_expansion = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}
			initial_circle_center = None
			initial_circle_radius = None

			for i, img_path in enumerate(images):
				if i % progress_interval == 0:
					progress_pct = (i + 1) / total_frames * 100
					elapsed_time = (datetime.now() - start_time).total_seconds()

					if i > 0:
						time_per_frame = elapsed_time / i
						time_remaining = (total_frames - i) * time_per_frame
						time_str = f'{time_remaining / 60:.1f}min' if time_remaining > 60 else f'{time_remaining:.0f}s'
						self.klog(1, f'Progress: {progress_pct:.1f}% ({i + 1}/{total_frames}) - Est. remaining: {time_str}')
					else:
						self.klog(1, f'Progress: {progress_pct:.1f}% ({i + 1}/{total_frames})')

				frame = cv2.imread(img_path)
				if frame is None:
					self.klog(2, f'Failed to read frame: {os.path.basename(img_path)}', debug_only=True)
					continue

				scaled = cv2.resize(
					frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

				padded = cv2.copyMakeBorder(
					scaled,
					top_padding, bottom_padding,
					left_padding, right_padding,
					cv2.BORDER_CONSTANT,
					value=[0, 0, 0]
				)

				if i == 0:
					# First frame: full detection, save expansion values
					generator.detect_circle(padded)
					initial_expansion = generator.expansion.copy()
					initial_circle_center = generator.circle_center
					initial_circle_radius = generator.circle_radius
				else:
					# Subsequent frames: reuse first frame's expansion
					if any(initial_expansion.values()):
						generator.expansion = initial_expansion.copy()
						generator.expanded_image = cv2.copyMakeBorder(
							padded,
							initial_expansion['top'], initial_expansion['bottom'],
							initial_expansion['left'], initial_expansion['right'],
							cv2.BORDER_CONSTANT, value=[0, 0, 0]
						)
						generator.circle_center = initial_circle_center
						generator.circle_radius = initial_circle_radius
					else:
						generator.expanded_image = padded.copy()

				if self.show_circles_only:
					result = generator.draw_debug_circles(generator.expanded_image.copy())
				else:
					result = generator.wrap_keogram(padded, keogram, progress, i, total_frames)

				writer.write(result)

			writer.release()

			# Re-encode with quality settings using ffmpeg
			try:
				if use_timelapse_settings and timelapse_settings:
					vcodec = timelapse_settings['vcodec']
					pixfmt = timelapse_settings['pixfmt']
					fflog = timelapse_settings['fflog']

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
						'-pix_fmt', 'yuv420p',
						output_path
					]

				self.klog(1, 'Re-encoding video with quality settings...')
				subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

				if os.path.exists(temp_output):
					os.remove(temp_output)

			except Exception as e:
				self.klog(0, f'ERROR: Failed to apply quality settings: {e}')
				# If re-encoding fails, keep the original file
				if os.path.exists(temp_output):
					os.rename(temp_output, output_path)
					self.klog(0, 'Using original encoded video (ffmpeg failed)')

			total_time = (datetime.now() - start_time).total_seconds()
			time_str = f'{total_time / 60:.1f} minutes' if total_time > 60 else f'{total_time:.1f} seconds'
			self.klog(1, f'Video creation completed in {time_str}')

			return True, output_path, total_frames, fps

		except Exception as e:
			self.klog(0, f'ERROR: Video creation failed: {e}')
			return False, None, 0, 0

	def _execute_script(self, script_path, *args):
		'''Run a script or binary, returning (returncode, stdout, stderr).'''
		cmd = [str(script_path), *args]
		if not os.access(str(script_path), os.X_OK):
			cmd = ['bash', str(script_path), *args]

		self.klog(2, f'Executing: {cmd}', debug_only=True)
		try:
			proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
			return proc.returncode, proc.stdout, proc.stderr
		except Exception as e:
			return 1, '', str(e)

	@staticmethod
	def _join_remote_dir(base, subdir):
		'''Join a remote image dir and subdir into a clean absolute-style path.

		upload.sh uses the directory argument verbatim as the destination
		(e.g. "cd '<dir>'" for sftp), so we just normalise slashes and append
		the keolapse subdirectory. We deliberately do not use os.path.join,
		since the remote server may use a different path separator convention
		than the Pi.
		'''
		base = (base or '').rstrip('/')
		subdir = (subdir or '').strip('/')
		if not base:
			return subdir
		return f'{base}/{subdir}' if subdir else base

	def _build_upload_targets(self, subdir):
		'''Build the list of (flag, destination_dir) for each enabled upload target.

		subdir is appended to each destination's image directory. For the local
		website the directory is created here; remote directories must already
		exist on the server (upload.sh will not create them).
		'''
		targets = []

		# Local Allsky Website (on the Pi) - we can create the directory.
		if self._setting_bool('uselocalwebsite'):
			local_dir = os.path.join(self._allsky_home, 'html', 'allsky', subdir)
			try:
				os.makedirs(local_dir, exist_ok=True)
			except Exception as e:
				self.klog(0, f'ERROR: could not create local website dir {local_dir}: {e}')
			targets.append(('--local-web', local_dir))

		# Remote Allsky Website (sftp/scp/ftp/etc via upload.sh).
		if self._setting_bool('useremotewebsite'):
			remote_dir = self._join_remote_dir(
				self._setting_str('remotewebsiteimagedir', ''), subdir)
			targets.append(('--remote-web', remote_dir))

		# Remote server (note: the core setting is "useremoteserver").
		if self._setting_bool('useremoteserver') or self._setting_bool('useremotewebserver'):
			remote_dir = self._join_remote_dir(
				self._setting_str('remoteserverimagedir', ''), subdir)
			targets.append(('--remote-server', remote_dir))

		return targets

	def _upload_one(self, file_path, file_name, subdir, label):
		'''Upload a single file to each enabled destination under subdir.

		Returns a short status string summarising each destination.
		'''
		upload_script = os.path.join(self._allsky_home, 'scripts', 'upload.sh')
		targets = self._build_upload_targets(subdir)

		if not targets:
			self.klog(1, f'{label} upload requested but no Allsky Website or remote server is enabled in Allsky Settings')
			return 'no upload targets configured'

		messages = []
		for target, remote_dir in targets:
			rc, _out, err = self._execute_script(
				upload_script, target, file_path, remote_dir, file_name)
			if rc == 0:
				self.klog(1, f'{label} uploaded successfully via {target} to {remote_dir}/{file_name}')
				messages.append(f'{target} ok')
			else:
				err_text = (err or '').strip()
				# sftp/scp fail this way when the subdir is missing on the server.
				if 'cd' in err_text.lower() or 'no such file' in err_text.lower():
					self.klog(0,
						f"ERROR: {label} upload via {target} failed (rc={rc}). The '{subdir}' "
						f"directory may not exist on the destination: {remote_dir}. "
						f"Create it once on the server, then retry. STDERR:\n{err_text}")
				else:
					self.klog(0, f'ERROR: Failed to upload {label} via {target} (rc={rc}). STDERR:\n{err_text}')
				messages.append(f'{target} failed')

		return ', '.join(messages)

	def _upload_video(self, video_path, file_name):
		'''Upload the keolapse video into upload_subdir of each enabled destination.

		Uploaded with its dated filename (keolapse-YYYYMMDD.mp4) so it never
		collides with the regular timelapse video.
		'''
		return self._upload_one(video_path, file_name, self.upload_subdir, 'Keolapse video')

	def _create_thumbnail(self, video_path):
		'''Extract a single representative frame from the video as a JPEG thumbnail.

		The thumbnail matches the Allsky website convention: same dated stem as
		the video but with a .jpg extension, scaled to thumbnail_width. Returns
		the local thumbnail path, or None on failure.
		'''
		try:
			if not self._check_ffmpeg_available():
				self.klog(0, 'ERROR: ffmpeg not found, cannot create thumbnail')
				return None

			thumb_path = os.path.splitext(video_path)[0] + '.jpg'
			width = max(10, int(self.thumbnail_width))

			# Seek a little into the video for a representative (non-black) frame.
			cmd = [
				'ffmpeg', '-y',
				'-ss', '2',
				'-i', video_path,
				'-frames:v', '1',
				'-update', '1',
				'-vf', f'scale={width}:-1',
				thumb_path
			]
			proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

			if proc.returncode != 0 or not os.path.exists(thumb_path):
				# Retry from the first frame if the seek landed past the end.
				cmd_retry = [
					'ffmpeg', '-y',
					'-i', video_path,
					'-frames:v', '1',
					'-update', '1',
					'-vf', f'scale={width}:-1',
					thumb_path
				]
				proc = subprocess.run(cmd_retry, capture_output=True, text=True, check=False)

			if not os.path.exists(thumb_path):
				self.klog(0, f'ERROR: thumbnail not created. ffmpeg STDERR:\n{(proc.stderr or "").strip()}')
				return None

			self.klog(1, f'Created thumbnail: {thumb_path} (width {width})')
			return thumb_path

		except Exception as e:
			self.klog(0, f'ERROR: creating thumbnail failed: {e}')
			return None

	def _upload_thumbnail(self, thumb_path):
		'''Upload the thumbnail into the thumbnails/ subdirectory of upload_subdir.'''
		thumb_subdir = self._join_remote_dir(self.upload_subdir, 'thumbnails')
		return self._upload_one(
			thumb_path, os.path.basename(thumb_path), thumb_subdir, 'Keolapse thumbnail')

	def _save_extra_data(self, output_path, frames, fps):
		'''Publish AS_KEOLAPSE_* variables for the overlay system.'''
		try:
			extra_data = {
				'AS_KEOLAPSE_VIDEO': output_path,
				'AS_KEOLAPSE_DATE': self._get_target_date(),
				'AS_KEOLAPSE_FRAMES': frames,
				'AS_KEOLAPSE_DURATION': round(frames / fps, 1) if fps else 0
			}
			allsky_shared.save_extra_data(
				self.meta_data['extradatafilename'],
				extra_data,
				self.meta_data['module'],
				self.meta_data['extradata'],
				event=self.event
			)
		except Exception as e:
			self.klog(0, f'ERROR: saving extra data failed: {e}')

	def run(self):
		self.klog(1, '=== Starting Keolapse Module ===')
		self.klog(2, f'Images directory: {self._images_dir}', debug_only=True)
		self.klog(2, f'Event: {self.event}', debug_only=True)
		self.klog(1, f"Module version: {self.meta_data['version']}")
		self.klog(1, f"Testing mode: {'Enabled' if self.enable_testing else 'Disabled'}")

		try:
			# Guard: full video generation in the periodic flow only makes sense
			# while testing. Otherwise a video would be regenerated every periodic
			# cycle. Normal generation happens on the nightday event (or via the
			# WebUI [Test Module] button).
			if self.event == 'periodic' and not (self.enable_testing or self.debugmode):
				result = 'Skipped: periodic event with testing disabled (video is generated on the nightday event)'
				self.klog(4, result)
				return result

			self._cleanup_test_data()

			# Test data generation (before any other testing feature)
			if self.generate_test_data_flag and self.event in ('periodic', ''):
				self.klog(1, 'Generating test data...')
				return 'Test data generated successfully' if self._generate_test_data() else 'ERROR: Failed to generate test data'

			images = self._get_source_images()
			if not images:
				if self._get_source_directory() is None:
					return 'ERROR: Source directory not found - cannot proceed'
				return 'ERROR: No images found to process'

			# Debug image / alignment modes
			if (self.show_circles or self.show_example or self.show_circles_only) \
					and self.event in ('periodic', ''):
				self.klog(1, 'Creating debug image...')
				return 'Debug image created successfully' if self._create_debug_image(images) else 'ERROR: Failed to create debug image'

			# Normal video creation
			self.klog(1, 'Creating keolapse video...')
			success, output_path, frames, fps = self._create_video(images)

			if not success:
				return 'ERROR: Failed to create video'

			self._save_extra_data(output_path, frames, fps)

			result = f'Video created successfully: {output_path}'

			# Create a thumbnail so website galleries that pair each video with a
			# thumbnail (e.g. <subdir>/thumbnails/keolapse-YYYYMMDD.jpg) display it.
			thumb_path = None
			if self.upload_thumbnail:
				thumb_path = self._create_thumbnail(output_path)

			# Upload handling: in [Test Module] runs only upload when upload_test
			# is enabled; in normal runs honor the upload setting.
			do_upload = self.upload_test if self.debugmode else self.upload
			if do_upload:
				upload_result = self._upload_video(output_path, os.path.basename(output_path))
				result = f'{result} (upload: {upload_result})'
				if self.upload_thumbnail and thumb_path:
					thumb_result = self._upload_thumbnail(thumb_path)
					result = f'{result} (thumbnail: {thumb_result})'

			return result

		except Exception as e:
			self.klog(0, f'ERROR: Module execution failed: {e}')
			return f'ERROR: {e}'


def keolapse(params, event):
	allsky_keolapse = ALLSKYKEOLAPSE(params, event)
	result = allsky_keolapse.run()

	return result


def keolapse_cleanup():
	moduleData = {
		"metaData": ALLSKYKEOLAPSE.meta_data,
		"cleanup": {
			"files": {
				ALLSKYKEOLAPSE.meta_data["extradatafilename"]
			},
			"env": {}
		}
	}
	allsky_shared.cleanupModule(moduleData)
