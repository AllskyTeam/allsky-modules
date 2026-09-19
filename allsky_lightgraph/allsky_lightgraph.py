'''
allsky_lightgraph.py
Part of allsky prostprocess.py modules.
https://github.com/AllskyTeam/allsky

This module draws a 24-hour long graph showing:
	sunrise and sunset
	dawn and dusk  (civil, nautical and astronomical)
	sun transit (noon) and anti-transit (midnight)
and optionally an annual graph of astronomical darkness.
Expected parameters:
	Size and positioning
	Coloring and transparency
	Reference point (now on the center or on the left)
'''
import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE
import os
import ephem
import datetime
import cv2
import numpy as np
from math import degrees

class ALLSKYLIGHTGRAPH(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Light Graph",
		"description": "Draw a 24-hour light graph on the overlay",
		"events": [
			"night",
			"day"
		],
		"experimental": "false",
		"centersettings": "false",	
		"version": "v0.7",
		"module": "allsky_lightgraph",
		"group": "Image Adjustments",
		"changelog": {
			"v0.6": [
				{
					"author": "Carlos Gil",
					"authorurl": "https://github.com/ea1ii",
					"changes": "Previous release"
				},
				{
					"author": "AllskyTeam",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Partially migrated to new module format"
				}
			],
			"v0.7": [
				{
					"author": "Carlos Gil",
					"authorurl": "https://github.com/ea1ii",
					"changes": [
						"Removed code for publihing variables (no longer needed)",
						"Added Thickness parameter for elevation graph lines",
						"Added option to draw annual darkness graph"
					]
				}
			]
		},
		"arguments": {
			"border_color": "30 190 40",
			"light_color": "240 240 240",
			"dark_color": "10 10 10",
			"width": 800,
			"height": 25,
			"alpha": 1.0,
			"horiz_pos": 10,
			"vert_pos": 940,
			"horiz_center": "true",
			"hour_ticks": "true",
			"hour_nums": "true",
			"hour_txt_size": 0.5,
			"text_color": "30 190 40",
			"now_point": "Center",
			"draw_elev": "true",
			"elev_color": "30 190 40",
			"sun_color": "85 205 235",
			"moon_color": "230 200 95",
			"elev_horiz_pos": 750,
			"elev_vert_pos": 10,
			"elev_width": 300,
			"elev_height": 100,
			"elev_thickness": 2,
			"draw_annual": "false",
			"annual_color": "30 190 40",
			"Marker": "0 0 255",
			"annual_alpha": 0.75,
			"annual_axis": "Previous noon to next noon",
			"annual_granularity": 10,
			"annual_width": 500,
			"annual_height": 150,
			"annual_horiz_pos": 260,
			"annual_vert_pos": 100,
			"debug": "False"
		},
		"argumentdetails": {
			"border_color": {
				"required": "true",
				"description": "Border color",
				"help": "BGR format.",
				"tab": "Colors",
				"type": {
					"fieldtype": "colour"
				}
			},
			"light_color": {
				"required": "true",
				"description": "Fill color for light time",
				"help": "BGR format.",
				"tab": "Colors",
				"type": {
					"fieldtype": "colour"
				}
			},
			"dark_color": {
				"required": "true",
				"description": "Fill color for dark time",
				"help": "BGR format.",
				"tab": "Colors",
				"type": {
					"fieldtype": "colour"
				}
			},
			"width": {
				"required": "true",
				"description": "Width",
				"help": "Total with for the graph.",
				"type": {
					"fieldtype": "spinner",
					"min": 500,
					"max": 2000,
					"step": 1
				}
			},
			"height": {
				"required": "true",
				"description": "Height",
				"help": "Total height for the graph.",
				"type": {
					"fieldtype": "spinner",
					"min": 5,
					"max": 2000,
					"step": 1
				}
			},
			"alpha": {
				"required": "true",
				"description": "Transparency",
				"help": "From 0 (invisible) to 1 (opaque).",
				"tab": "Colors",
				"type": {
					"fieldtype": "spinner",
					"min": 0.10,
					"max": 1.00,
					"step": 0.05
				}
			},
			"horiz_pos": {
				"required": "true",
				"description": "Left border position in px",
				"help": "Ignored if centered.",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"vert_pos": {
				"required": "true",
				"description": "Top border position in px",
				"help": "",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"horiz_center": {
				"required": "false",
				"description": "Horizontal center align",
				"help": "",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"hour_ticks": {
				"required": "false",
				"description": "Visible hour tickmarks",
				"help": "",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"hour_nums": {
				"required": "false",
				"description": "Visible hour numbers",
				"help": "Might decrease frquency if too compact.",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"hour_txt_size": {
				"required": "true",
				"description": "Hour text font scale",
				"help": "Hours to be skipped over if too big and close",
				"type": {
					"fieldtype": "spinner",
					"min": 0.1,
					"max": 2.0,
					"step": 0.1
				}
			},	 
			"text_color": {
				"required": "true",
				"description": "Color for text",
				"help": "BGR format.",
				"tab": "Colors",
				"type": {
					"fieldtype": "colour"
				}
			},
			"now_point": {
				"required": "true",
				"description": "Now is aligned to the center or to the left",
				"help": "",
				"type": {
					"fieldtype": "select",
					"values": "Center, Left"
				}
			},
			"draw_elev": {
				"required": "false",
				"description": "Draw elevation chart",
				"help": "",
				"tab": "Elevation",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"elev_color": {
				"required": "true",
				"description": "Elevation border color",
				"help": "BGR format.",
				"tab": "Elevation",
				"type": {
					"fieldtype": "colour"
				}
			},
			"sun_color": {
				"required": "true",
				"description": "Sun color",
				"help": "BGR format.",
				"tab": "Elevation",
				"type": {
					"fieldtype": "colour"
				}
			},
			"moon_color": {
				"required": "true",
				"description": "Moon color",
				"help": "BGR format.",
				"tab": "Elevation",
				"type": {
					"fieldtype": "colour"
				}
			},
			"elev_width": {
				"required": "true",
				"description": "Width",
				"help": "Total with for the graph",
				"tab": "Elevation",
				"type": {
					"fieldtype": "spinner",
					"min": 200,
					"max": 2000,
					"step": 1
				}
			},
			"elev_height": {
				"required": "true",
				"description": "Height",
				"help": "Total height for the graph.",
				"tab": "Elevation",
				"type": {
					"fieldtype": "spinner",
					"min": 200,
					"max": 2000,
					"step": 1
				}
			},
			"elev_horiz_pos": {
				"required": "true",
				"description": "Left border position in px",
				"help": "",
				"tab": "Elevation",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"elev_vert_pos": {
				"required": "true",
				"description": "Top border position in px",
				"tab": "Elevation",
				"help": "",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"elev_thickness": {
				"required": "true",
				"description": "Thickness",
				"help": "Thickness for the elevation graph.",
				"default": 2,
				"tab": "Elevation",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 5,
					"step": 1
				}
			},			
			"draw_annual": {
				"required": "false",
				"description": "Draw annual darkness graph",
				"help": "Shows astronomical-dark hours for each day of the year.",
				"tab": "Annual",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"annual_color": {
				"required": "true",
				"description": "Annual graph border color",
				"help": "BGR format. The graph uses the main graph colors for its bands.",
				"tab": "Annual",
				"type": {
					"fieldtype": "colour"
				}
			},
			"Marker": {
				"required": "true",
				"description": "Current date and time marker color",
				"help": "BGR format. Draws a vertical date line and horizontal time line.",
				"tab": "Annual",
				"type": {
					"fieldtype": "colour"
				}
			},
			"annual_alpha": {
				"required": "true",
				"description": "Annual graph transparency",
				"help": "From 0 (invisible) to 1 (opaque).",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 0.10,
					"max": 1.00,
					"step": 0.05
				}
			},
			"annual_axis": {
				"required": "true",
				"description": "Annual graph time axis",
				"help": "Choose a midnight-to-midnight or previous-noon-to-next-noon day.",
				"tab": "Annual",
				"type": {
					"fieldtype": "select",
					"values": "0 to 24 hours, Previous noon to next noon"
				}
			},
			"annual_granularity": {
				"required": "true",
				"description": "Annual graph granularity",
				"help": "10 uses 15-minute bands. 1 makes bands approximately one pixel high.",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 1
				}
			},
			"annual_width": {
				"required": "true",
				"description": "Width",
				"help": "Total width for the annual graph.",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 200,
					"max": 2000,
					"step": 1
				}
			},
			"annual_height": {
				"required": "true",
				"description": "Height",
				"help": "Total height for the annual graph.",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 80,
					"max": 1000,
					"step": 1
				}
			},
			"annual_horiz_pos": {
				"required": "true",
				"description": "Left border position in px",
				"help": "",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"annual_vert_pos": {
				"required": "true",
				"description": "Top border position in px",
				"help": "",
				"tab": "Annual",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 2000,
					"step": 1
				}
			},
			"debug": {
				"required": "false",
				"description": "Enable debug mode",
				"help": "If selected image will not be updated but stored in allsky tmp debug folder.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			}
		}
	}

	border_color = light_color = dark_color = text_color =None
	day2civil_color = civil2nauti_color = nauti2astro_color = None
	elev_color = sun_solor = moon_color = None
	elev_thickness = 2
	latitude = longitude = 0
	graph_X = graph_Y = graph_width = graph_height = 0
	elev_X = elev_Y =                   elev_width = elev_height = 0
	annual_X = annual_Y = annual_width = annual_height = 0
	annual_sample_count = 96
	npoints = res = 0
	startTime = finishTime = nowTime = datetime.datetime.now()
	startTimeUTC = finishTimeUTC = nowTimeUTC = datetime.datetime.utcnow()
	midnight = noon = None
	location = None
	timeArray = []
	sunPath = moonPath = []
	annual_bands = []

	def __init__(self, debug, params, event):
		super().__init__(params, event)
		self.get_params(debug, params)
		self.set_size(debug, params)
		self.set_time(debug, params)
		self.calculations(debug, params)
		if params["draw_elev"] == True:
			self.elev_thickness = int(params["elev_thickness"])
			self.calSunMoon(params)
		if params["draw_annual"] == True:
			self.calAnnualDarkness(params)

	def _readColor(self, input):
		if input.count(' ') >= 2:
			result = tuple(int(item) for item in input.split(' '))  # Legacy GBR values
		else:
			temp_result = tuple(int(item) for item in input.split(','))  # RGB to BGR for new colour picker
			result = (temp_result[2], temp_result[1], temp_result[0])

		return result
	
	def _scaleColor(self, val1, val2, fraction):
		return tuple(sum(x) * fraction for x in zip(val1, val2))

	def get_params(self, debug, params):
		self.border_color = self._readColor(params["border_color"])
		self.light_color = self._readColor(params["light_color"])
		self.dark_color = self._readColor(params["dark_color"])
		self.text_color = self._readColor(params["text_color"])

		self.day2civil_color = self._scaleColor(self.light_color, self.dark_color, 0.75)
		self.civil2nauti_color = self._scaleColor(self.light_color, self.dark_color, 0.50)
		self.nauti2astro_color = self._scaleColor(self.light_color, self.dark_color, 0.25)

		self.latitude, self.longitude = allsky_shared.get_lat_lon()

		if params["draw_elev"] == True:
			self.elev_color = self._readColor(params["elev_color"])
			self.sun_color = self._readColor(params["sun_color"])
			self.moon_color = self._readColor(params["moon_color"])
			# self.elev_thickness = int(params["elev_thickness"])

		if params["draw_annual"] == True:
			self.annual_color = self._readColor(params["annual_color"])
			self.annual_marker = self._readColor(params["Marker"])
				
	def set_size(self, debug, params):
		self.image_width = allsky_shared.image.shape[1]
		self.image_height = allsky_shared.image.shape[0]
		self.graph_width = int(params["width"])
		self.graph_height = int(params["height"])
		self.graph_X = int(params["horiz_pos"])
		self.graph_Y = int(params["vert_pos"])
		center = params["horiz_center"]

		if self.graph_width > self.image_width:
			self.graph_width = self.image_width
			self.graph_X = 0
			if debug:
				self.log(1, "Width truncated")

		if center:
			self.graph_X = int((self.image_width - self.graph_width) / 2)
		elif (self.graph_X + self.graph_width) > self.image_width:
			self.graph_X = self.image_width - self.graph_width
			if debug:
				self.log(1,"X adjusted")

		if self.graph_height > self.image_height / 5:
			self.graph_height = int(self.image_height / 5)
		if (self.graph_Y + self.graph_height) > self.image_height:
			self.graph_Y = self.image_height - self.graph_height
			if debug:
				self.log(1,"Y adjusted")
		if self.graph_Y < 10:
			self.graph_Y = 10
			if debug:
				self.log(1,"Y adjusted")

		if params["draw_elev"] == True:
			self.elev_width = int(params["elev_width"])
			self.elev_height = int(params["elev_height"])
			self.elev_X = int(params["elev_horiz_pos"])
			self.elev_Y = int(params["elev_vert_pos"])
			if self.elev_width > self.image_width:
				self.elev_width = int(self.image_width / 4)
			if self.elev_height > self.image_height:
				self.elev_height = int(self.image_height / 4)
			if (self.elev_X + self.elev_width) > self.image_width:
				self.elev_X = self.image_width - self.elev_width
			if (self.elev_Y + self.elev_height) > self.image_height:
				self.elev_Y = self.image_height - self.elev_height           	 

		if params["draw_annual"] == True:
			self.annual_width = min(int(params["annual_width"]), self.image_width)
			self.annual_height = min(int(params["annual_height"]), self.image_height)
			self.annual_X = int(params["annual_horiz_pos"])
			self.annual_Y = int(params["annual_vert_pos"])
			if self.annual_X + self.annual_width > self.image_width:
				self.annual_X = self.image_width - self.annual_width
			if self.annual_Y + self.annual_height > self.image_height:
				self.annual_Y = self.image_height - self.annual_height
			self.annual_X = max(0, self.annual_X)
			self.annual_Y = max(0, self.annual_Y)

	def set_time(self, debug, params):

		if params["now_point"] == "Center":
			self.startTime = self.nowTime - datetime.timedelta(hours=12)
			self.finishTime = self.nowTime + datetime.timedelta(hours=12)
			self.startTimeUTC = self.nowTimeUTC - datetime.timedelta(hours=12)
			self.finishTimeUTC = self.nowTimeUTC + datetime.timedelta(hours=12)
		else:
			self.startTime = self.nowTime
			self.finishTime = self.nowTime + datetime.timedelta(hours=24)
			self.startTimeUTC = self.nowTimeUTC
			self.finishTimeUTC = self.nowTimeUTC + datetime.timedelta(hours=24)

	def _convertLatLon(self, input):
		# convert latitude or longitude to ephem format
		v = input
		g = int(v)
		v = v - g
		m = int(v * 60)
		v = v * 60 - m
		se = v * 60
		res = str(g) + ':' + str(m) + ':' + str(se)

		return res

	def calculations(self, debug, params):
		self.location = ephem.Observer()
		self.location.lat = self._convertLatLon(self.latitude)
		self.location.lon = self._convertLatLon(self.longitude)
		self.location.date = ephem.Date(self.nowTimeUTC)

		ss = ephem.Sun()

		# store in an array all next risings and settings, and transits
		self.location.horizon = '-18:0'
		try:
			raise_astro1 = self.location.next_rising(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(raise_astro1, "DawnAstro")]
		except:
			pass
		try:
			set_astro1 = self.location.next_setting(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(set_astro1, "DuskAstro")]
		except:
			pass
		self.location.horizon = '-12:0'
		try:
			raise_nauti1 = self.location.next_rising(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(raise_nauti1, "DawnNauti")]
		except:
			pass
		try:
			set_nauti1 = self.location.next_setting(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(set_nauti1, "DuskNauti")]
		except:
			pass
		self.location.horizon = '-6:0'
		try:
			raise_civil1 = self.location.next_rising(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(raise_civil1, "DawnCivil")]
		except:
			pass
		try:
			set_civil1 = self.location.next_setting(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(set_civil1, "DuskCivil")]
		except:
			pass
		self.location.horizon = '0:0'
		try:
			raise1 = self.location.next_rising(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(raise1, "Sunrise")]
		except:
			pass
		try:
			set1 = self.location.next_setting(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(set1, "Sunset")]
		except:
			pass

		try:
			transit1 = self.location.next_transit(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(transit1, "Noon")]
		except:
			pass
		try:
			anti_transit1 = self.location.next_antitransit(ephem.Sun()).datetime()
			self.timeArray = self.timeArray + [(anti_transit1, "Midnight")]
		except:
			pass
		
		# of centered, add all previous risings and settings and transits
		if params["now_point"] == "Center":
			self.location.horizon ='-18:0'
			try:
				raise_astro2 = self.location.previous_rising(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(raise_astro2, "DawnAstro")]
			except:
				pass
			try:
				set_astro2 = self.location.previous_setting(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(set_astro2, "DuskAstro")]
			except:
				pass
			self.location.horizon ='-12:0'
			try:
				raise_nauti2 = self.location.previous_rising(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(raise_nauti2, "DawnNauti")]
			except:
				pass
			try:
				set_nauti2 = self.location.previous_setting(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(set_nauti2, "DuskNauti")]
			except:
				pass
			self.location.horizon ='-6:0'
			try:
				raise_civil2 = self.location.previous_rising(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(raise_civil2, "DawnCivil")]
			except:
				pass
			try:
				set_civil2 = self.location.previous_setting(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(set_civil2, "DuskCivil")]
			except:
				pass
			self.location.horizon ='0:0'
			try:
				raise2 = self.location.previous_rising(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(raise2, "Sunrise")]
			except:
				pass
			try:
				set2 = self.location.previous_setting(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(set2, "Sunset")]
			except:
				pass

			try:
				transit2 = self.location.previous_transit(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(transit2, "Noon")]
			except:
				pass
			try:
				anti_transit2 = self.location.previous_antitransit(ephem.Sun()).datetime()
				self.timeArray = self.timeArray + [(anti_transit2, "Midnight")]
			except:
				pass

		# sort all events
		self.timeArray.sort()

		# filter out events before start time or after end time
		while (self.timeArray[0])[0] < self.startTimeUTC:
			self.timeArray = self.timeArray[1:]

		while (self.timeArray[-1])[0] > self.finishTimeUTC:
			self.timeArray = self.timeArray[:-1]

		# add start and end time events
		self.timeArray = [(self.startTimeUTC, "Start")] + self.timeArray + [(self.finishTimeUTC, "Finish")]

		ss = ephem.Sun()
		ss.compute(self.location)
		sun_elev = ss.alt

		# add to each element datetime scaled to rectangle X coordinate
		for i in range(len(self.timeArray)):
			self.timeArray[i] = self.timeArray[i] + (int((self.timeArray[i][0] - self.startTimeUTC).total_seconds() / (self.finishTimeUTC - self.startTimeUTC).total_seconds() * self.graph_width),)

		# remove and store separately the transits as the do not trigger a color change, but draw a single line
		for moment in self.timeArray:
			if moment[1] == "Noon":
				self.noon = moment
				self.timeArray.remove(moment)
			if moment[1] == "Midnight":
				self.midnight = moment
				self.timeArray.remove(moment)
		for moment in self.timeArray: # not sure yey if an extra check is really necessary, probably not
			if moment[1] == "Noon":
				self.noon = moment
				self.timeArray.remove(moment)
			if moment[1] == "Midnight":
				self.midnight = moment
				self.timeArray.remove(moment)     

	def calSunMoon(self, params):
		k = 3  # k is the precission for moon-solar plot in pixels
		self.npoints = int(self.elev_width / k) + 1
		self.res = self.elev_width / self.npoints
		delta_t = 24.0 * 3600.0 / self.npoints
		sun = ephem.Sun()
		moon = ephem.Moon()
		for x in range(self.npoints + 1):
			xt = self.startTimeUTC + datetime.timedelta(seconds=x * delta_t)
			self.location.date = ephem.Date(xt)
			sun.compute(self.location)
			self.sunPath = self.sunPath + [(x * self.res, int(degrees(sun.alt) / 90.0 * self.elev_height / 2.0))]
			moon.compute(self.location)
			self.moonPath = self.moonPath + [(x * self.res, int(degrees(moon.alt) / 90.0 * self.elev_height / 2.0))]

	def calAnnualDarkness(self, params):
		self.annual_bands = []
		granularity = max(1, min(10, int(params.get("annual_granularity", 10))))
		pixel_samples = max(2, self.annual_height - 22)
		self.annual_sample_count = int(round(pixel_samples +
			(granularity - 1) * (96 - pixel_samples) / 9.0))
		self.annual_sample_count = max(2, self.annual_sample_count)
		if self.annual_sample_count % 2:
			self.annual_sample_count += 1
		start = datetime.datetime(self.nowTime.year, 1, 1)
		noon_to_noon = self._annualNoonToNoon(params)
		end = datetime.datetime(self.nowTime.year + 1, 1, 1)
		days = (end - start).days
		sun = ephem.Sun()
		for day in range(days):
			date = start + datetime.timedelta(days=day)
			bands = []
			sample_minutes = 1440.0 / self.annual_sample_count
			for sample in range(self.annual_sample_count):
				moment = date + datetime.timedelta(minutes=(sample + 0.5) * sample_minutes)
				self.location.date = ephem.Date(moment)
				sun.compute(self.location)
				altitude = degrees(sun.alt)
				if altitude < -18.0:
					band = 0
				elif altitude < -12.0:
					band = 1
				elif altitude < -6.0:
					band = 2
				elif altitude < 0.0:
					band = 3
				else:
					band = 4
				bands.append(band)
			if noon_to_noon:
				half_day = self.annual_sample_count // 2
				bands = bands[half_day:] + bands[:half_day]
			self.annual_bands.append(bands)

	def _annualNoonToNoon(self, params):
		axis = str(params.get("annual_axis", "0 to 24 hours")).strip().lower()
		return "noon" in axis

	def _azMidDarkness(self, dt1, dt2):
		tdelta = (dt2 - dt1).total_seconds()
		tmid = dt1 + datetime.timedelta(seconds=tdelta/2)
		loc = self.location
		loc.date = ephem.Date(tmid.strftime("%Y/%m/%d %H:%M:%S"))
		sun = ephem.Sun()
		sun.compute(loc)
		a = degrees(sun.alt)
		if a < -18.0:
			drk = 0 # night
		elif a < -12.0:
			drk = 1 # astronomical
		elif a < -6.0:
			drk = 2 # nautical
		elif a < 0.0:
			drk = 3 # civil
		else:
			drk = 4 # day

		return drk

	def draw(self, params):
		alpha = float(params["alpha"])
		textSize = float(params["hour_txt_size"])
		
		canvas = allsky_shared.image
		if alpha < 1.0:
			canvas = allsky_shared.image.copy() # if transparency, work on a copy
		else:
			canvas = allsky_shared.image

		# dark areas
		for i in range(len(self.timeArray)-1):
			# print (self._timeArray[i][0].strftime("%Y-%m-%d %H:%M:%S"), " to ",self._timeArray[i+1][0].strftime("%Y-%m-%d %H:%M:%S"), "(", self._timeArray[i][1], " to ",self._timeArray[i+1][1])
			drk = self._azMidDarkness(self.timeArray[i][0], self.timeArray[i + 1][0])
			if drk == 0:
				col = self.dark_color
			elif drk == 1:
				col = self.nauti2astro_color
			elif drk == 2:
				col = self.civil2nauti_color
			elif drk == 3:
				col = self.day2civil_color
			else:
				col = self.light_color

			cv2.rectangle(img=canvas, \
				pt1=(self.graph_X + self.timeArray[i][2], self.graph_Y), \
				pt2=(self.graph_X + self.timeArray[i + 1][2], self.graph_Y + self.graph_height), \
				color=col, thickness=cv2.FILLED)

		# transits
		if self.noon:
			cv2.line(img=canvas, pt1=(self.graph_X + self.noon[2], self.graph_Y), \
				pt2=(self.graph_X + self.noon[2], self.graph_Y + self.graph_height), color=self.dark_color)

		if self.midnight:
			cv2.line(img=canvas, pt1=(self.graph_X + self.midnight[2], self.graph_Y), \
				pt2=(self.graph_X + self.midnight[2], self.graph_Y + self.graph_height), color=self.light_color)

		# box
		cv2.rectangle(img=canvas, pt1=(self.graph_X, self.graph_Y), \
			pt2=(self.graph_X + self.graph_width, self.graph_Y + self.graph_height), \
			thickness=2, color=self.border_color)    

		# hour ticks
		if params["hour_ticks"] is True:
			tickSize = int(self.graph_height / 5)
			firstIntHourTime = self.startTime.replace(second=0, minute=0, microsecond=0)  # everything is calculated in UTC, but this is local
			startingX = -(self.startTime - firstIntHourTime).total_seconds() / 3600.0 / 24.0 * self.graph_width + self.graph_X
			hourdeltaPx = self.graph_width / 24.0

			yy = self.graph_Y
			font = cv2.FONT_HERSHEY_SIMPLEX
			onlyHour = firstIntHourTime.hour
			skipHour = False               
			for i in range(26):
				xPos = int(startingX + i * hourdeltaPx)
				if xPos > self.graph_X and xPos < self.graph_X + self.graph_width:
					cv2.line(img=canvas, pt1=(xPos, self.graph_Y), pt2=(xPos, self.graph_Y - tickSize), thickness=2, color=self.border_color)
					if params["hour_nums"] == True:
						textSz = cv2.getTextSize(str(onlyHour).zfill(2), font, textSize, 1)[0]
						textX = xPos - int(textSz[0] / 2.0)
						if skipHour:
							skipHour = False
						elif textSz[0] > hourdeltaPx:
							skipHour = True
						if not skipHour:
							cv2.putText(canvas, str(onlyHour).zfill(2), (textX, self.graph_Y - tickSize - 1), font, textSize, self.text_color, 1, cv2.LINE_AA)
				onlyHour = onlyHour + 1
				if onlyHour == 24:
					onlyHour = 0

		# now mark
		if params["now_point"] == "Center":
			startingX = int(self.graph_X + self.graph_width / 2.0)
		else:
			startingX = self.graph_X
		
		tri = np.array([[startingX, self.graph_Y + 8], [startingX - 5, self.graph_Y], [startingX + 5, self.graph_Y]])
		cv2.fillPoly(img=canvas, pts=[tri], color=self.border_color)
		tri = np.array([[startingX, self.graph_Y + self.graph_height - 8], [startingX - 5, self.graph_Y + self.graph_height], [startingX + 5, self.graph_Y + self.graph_height]])
		cv2.fillPoly(img=canvas, pts=[tri], color=self.border_color)

		#elev chart
		if params["draw_elev"] is True:
			# box
			cv2.rectangle(img=canvas, pt1=(self.elev_X, self.elev_Y), \
				pt2=(self.elev_X + self.elev_width, self.elev_Y + self.elev_height), \
				thickness=1, color=self.elev_color)
			cv2.line(img=canvas, pt1=(self.elev_X, self.elev_Y + int(self.elev_height / 2)), \
								pt2=(self.elev_X + self.elev_width, self.elev_Y + int(self.elev_height / 2)), thickness=2, color=self.elev_color)
			TROPIC = 23.5
			POLAR = 66.5
			cv2.line(img=canvas, pt1=(self.elev_X, self.elev_Y + int(self.elev_height / 2 - POLAR * self.elev_height / 180.0)), \
								pt2=(self.elev_X + self.elev_width, self.elev_Y + int(self.elev_height / 2 - POLAR * self.elev_height / 180.0)), thickness=1, color=self.elev_color)
			cv2.line(img=canvas, pt1=(self.elev_X, self.elev_Y + int(self.elev_height / 2 - TROPIC * self.elev_height / 180.0)), \
								pt2=(self.elev_X + self.elev_width, self.elev_Y + int(self.elev_height / 2 - TROPIC * self.elev_height / 180.0)), thickness=1, color=self.elev_color)
			cv2.line(img=canvas, pt1=(self.elev_X, self.elev_Y + int(self.elev_height / 2 + POLAR * self.elev_height / 180.0)), \
								pt2=(self.elev_X + self.elev_width, self.elev_Y + int(self.elev_height / 2 + POLAR * self.elev_height / 180.0)), thickness=1, color=self.elev_color)
			cv2.line(img=canvas, pt1=(self.elev_X, self.elev_Y + int(self.elev_height / 2 + TROPIC * self.elev_height / 180.0)), \
								pt2=(self.elev_X + self.elev_width, self.elev_Y + int(self.elev_height / 2 + TROPIC * self.elev_height / 180.0)), thickness=1, color=self.elev_color)
			
			# hours
			startingX = (firstIntHourTime - self.startTime).total_seconds() / 3600.0 / 24.0 * self.elev_width + self.elev_X
			hourdeltaPx = self.elev_width / 24.0
			
			onlyHour = firstIntHourTime.hour               
			for i in range(25):
				xPos = int(startingX + i * hourdeltaPx)
				if xPos > self.elev_X and xPos < self.elev_X + self.elev_width:
					cv2.line(img=canvas, pt1=(xPos, self.elev_Y), pt2=(xPos, self.elev_Y + self.elev_height), thickness=1, color=self.elev_color)
				onlyHour = onlyHour + 1
				if onlyHour == 24:
					onlyHour = 0

			# mark
			if params["now_point"] == "Center":
				startingX = self.elev_X+ int(self.elev_width / 2)
			else:
				startingX = self.elev_X 
			cv2.line(img=canvas, pt1=(startingX, self.elev_Y), pt2=(startingX, self.elev_Y + self.elev_height), thickness=2, color=self.elev_color)

			# paths
			for i in range(len(self.sunPath) - 1):
				cv2.line(img=canvas, \
					pt1=(self.elev_X + int(i * self.res), \
						self.elev_Y + int(self.elev_height / 2.0) - self.sunPath[i][1]), \
					pt2=(self.elev_X + int((i + 1) * self.res), \
						self.elev_Y + int(self.elev_height / 2.0) - self.sunPath[i + 1][1]), \
					thickness=self.elev_thickness, color=self.sun_color)
				cv2.line(img=canvas, \
					pt1=(self.elev_X + int(i * self.res), \
						self.elev_Y + int(self.elev_height / 2.0) - self.moonPath[i][1]), \
					pt2=(self.elev_X + int((i + 1) * self.res), \
						self.elev_Y + int(self.elev_height / 2.0) - self.moonPath[i + 1][1]), \
					thickness=self.elev_thickness, color=self.moon_color)

		if params["draw_annual"] is True:
			annual_canvas = canvas.copy()
			left = self.annual_X + 4
			top = self.annual_Y + 4
			right = self.annual_X + self.annual_width - 4
			bottom = self.annual_Y + self.annual_height - 18
			band_colors = (self.dark_color, self.nauti2astro_color,
				self.civil2nauti_color, self.day2civil_color, self.light_color)
			if right > left and bottom > top and self.annual_bands:
				plot_width = right - left
				plot_height = bottom - top
				annual_text_size = 0.25 * self.annual_height / 150.0
				n_days = len(self.annual_bands)
				for day, bands in enumerate(self.annual_bands):
					x1 = left + int(day * plot_width / n_days)
					x2 = left + int((day + 1) * plot_width / n_days)
					x2 = max(x1 + 1, x2)
					n_samples = len(bands)
					for sample, band in enumerate(bands):
						y1 = top + int(sample * plot_height / n_samples)
						y2 = top + int((sample + 1) * plot_height / n_samples)
						cv2.rectangle(annual_canvas, (x1, y1), (x2, y2),
							band_colors[band], cv2.FILLED)

				for month in range(12):
					month_start = (datetime.datetime(self.nowTime.year, month + 1, 1) -
						datetime.datetime(self.nowTime.year, 1, 1)).days
					x = left + int(month_start * plot_width / n_days)
					cv2.putText(annual_canvas, datetime.date(2000, month + 1, 1).strftime("%b")[0].upper(),
						(x, self.annual_Y + self.annual_height - 4), cv2.FONT_HERSHEY_SIMPLEX,
						annual_text_size, self.annual_color, 1, cv2.LINE_AA)

				cv2.rectangle(annual_canvas, (self.annual_X, self.annual_Y),
					(self.annual_X + self.annual_width, self.annual_Y + self.annual_height),
					self.annual_color, 1)

				day_of_year = self.nowTime.timetuple().tm_yday - 1
				date_x = left + int((day_of_year + 0.5) * plot_width / n_days)
				time_fraction = (
					self.nowTime.hour * 3600 +
					self.nowTime.minute * 60 +
					self.nowTime.second
				) / 86400.0
				time_y = top + int(time_fraction * plot_height)
				cv2.line(annual_canvas, (date_x, top), (date_x, bottom), self.annual_marker, 2)
				cv2.line(annual_canvas, (left, time_y), (right, time_y), self.annual_marker, 2)
			annual_alpha = float(params["annual_alpha"])
			canvas = cv2.addWeighted(annual_canvas, annual_alpha, canvas, 1 - annual_alpha, 0)

		if alpha < 1.0:
			tmpcanv = cv2.addWeighted(canvas, alpha, allsky_shared.image, 1 - alpha, 0)
			allsky_shared.image = tmpcanv
		else:
			allsky_shared.image = canvas

def lightgraph(params, event):
	allsky_shared.startModuleDebug("allsky_lightgraph")

	debug = params["debug"]
	drawer = ALLSKYLIGHTGRAPH(debug, params, event)

	drawer.draw(params)
	result ="Light Graph Complete"

	allsky_shared.log(4, "INFO {0}".format(result))
	return result
