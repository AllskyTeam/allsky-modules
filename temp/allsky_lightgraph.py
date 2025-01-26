'''
allsky_lightgraph.py
Part of allsky prostprocess.py modules.
https:// github.com/.........
This modules draw a 24hrs long graph showing:
	sunrise and sunset
	dawn and dusk  (civil, nautical and astronomical)
	sun transit (noon) and anti-transit (midnight)
Expected parameters:
	Size and positioning
	Coloring and transparency
	Reference point (now on the center or on the left)
'''
import allsky_shared as s
import os
import ephem
import datetime
import cv2
import numpy as np
from math import degrees

metaData = {
	"name": "Light Graph",
	"description": "Draws a 24hrs light graph",
	"events": [
	    "night",
	    "day"
	],
	"experimental": "false",
	"version": "v0.6",
	"module": "allsky_lightgraph",
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
	    "debug": "False"
	},
	"argumentdetails": {
	    "border_color": {
	        "required": "true",
	        "description": "Border color",
	        "help": "BGR format",
	        "tab": "Colors",
	        "type": {
	            "fieldtype": ""
	        }
	    },
	    "light_color": {
	        "required": "true",
	        "description": "Fill color for light time",
	        "help": "BGR format",
	        "tab": "Colors",
	        "type": {
	            "fieldtype": ""
	        }
	    },
	    "dark_color": {
	        "required": "true",
	        "description": "Fill color for dark time",
	        "help": "BGR format",
	        "tab": "Colors",
	        "type": {
	            "fieldtype": ""
	        }
	    },
	    "width": {
	        "required": "true",
	        "description": "Width",
	        "help": "Total with for the graph",
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
	        "help": "Total height for the graph",
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
	        "help": "From 0 (invisible) to 1 (opaque)",
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
	        "help": "Ignored if centered",
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
	        "help": "Might decrease frquency if too compact",
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
	        "help": "BGR format",
	        "tab": "Colors",
	        "type": {
	            "fieldtype": ""
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
	        "help": "BGR format",
	        "tab": "Elevation",
	        "type": {
	            "fieldtype": ""
	        }
	    },
	    "sun_color": {
	        "required": "true",
	        "description": "Sun color",
	        "help": "BGR format",
	        "tab": "Elevation",
	        "type": {
	            "fieldtype": ""
	        }
	    },
	    "moon_color": {
	        "required": "true",
	        "description": "Moon color",
	        "help": "BGR format",
	        "tab": "Elevation",
	        "type": {
	            "fieldtype": ""
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
	        "help": "Total height for the graph",
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
	   "debug": {
	        "required": "false",
	        "description": "Enable debug mode",
	        "help": "If selected image will not be updated but stored in allsky tmp debug folder",
	        "tab": "Debug",
	        "type": {
	            "fieldtype": "checkbox"
	        }
	    }

	}
}

class lGraph():

	border_color = light_color = dark_color = text_color =None
	day2civil_color = civil2nauti_color = nauti2astro_color = None
	elev_color = sun_solor = moon_color = None
	latitude = longitude = 0
	graph_X = graph_Y = graph_width = graph_height = 0
	elev_X = elev_Y = elev_width = elev_height = 0
	npoints = res = 0
	startTime = finishTime = nowTime = datetime.datetime.now()
	startTimeUTC = finishTimeUTC = nowTimeUTC = datetime.datetime.utcnow()
	midnight = noon = None
	location = None
	timeArray = []
	sunPath = moonPath = []

	def _readColor(self, input):
	    return tuple(int(item) for item in input.split(' '))

	def _scaleColor(self, val1, val2, fraction):
	    return tuple(sum(x) * fraction for x in zip(val1,val2))

	def get_params(self, debug, params):
	    self.border_color = self._readColor(params["border_color"])
	    self.light_color = self._readColor(params["light_color"])
	    self.dark_color = self._readColor(params["dark_color"])
	    self.text_color = self._readColor(params["text_color"])

	    self.day2civil_color = self._scaleColor(self.light_color, self.dark_color, 0.75)
	    self.civil2nauti_color = self._scaleColor(self.light_color, self.dark_color, 0.50)
	    self.nauti2astro_color = self._scaleColor(self.light_color, self.dark_color, 0.25)

	    self.latitude = s.convertLatLon(s.getSetting("latitude"))
	    self.longitude = s.convertLatLon(s.getSetting("longitude"))

	    if params["draw_elev"] == True:
	        self.elev_color = self._readColor(params["elev_color"])
	        self.sun_color = self._readColor(params["sun_color"])
	        self.moon_color = self._readColor(params["moon_color"])
	            
	def set_size(self, debug, params):
	    self.image_width = s.image.shape[1]
	    self.image_height = s.image.shape[0]
	    self.graph_width = int(params["width"])
	    self.graph_height = int(params["height"])
	    self.graph_X = int(params["horiz_pos"])
	    self.graph_Y = int(params["vert_pos"])
	    center = params["horiz_center"]

	    if self.graph_width > self.image_width:
	        self.graph_width = self.image_width
	        self.graph_X = 0
	        if debug:
	            s.log(1,"Width truncated")
	    
	    if center:
	        self.graph_X = int((self.image_width - self.graph_width) / 2)
	    elif (self.graph_X + self.graph_width) > self.image_width:
	        self.graph_X = self.image_width - self.graph_width
	        if debug:
	            s.log(1,"X adjusted")

	    if self.graph_height > self.image_height / 5:
	        self.graph_height = int(self.image_height / 5)
	    if (self.graph_Y + self.graph_height) > self.image_height:
	        self.graph_Y = self.image_height - self.graph_height
	        if debug:
	            s.log(1,"Y adjusted")
	    if self.graph_Y < 10:
	        self.graph_Y = 10
	        if debug:
	            s.log(1,"Y adjusted")

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
	    self.location.horizon ='-18:0'
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
	    self.location.horizon ='-12:0'
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
	    self.location.horizon ='-6:0'
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
	    self.location.horizon ='0:0'
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
	    k = 3 # k is the precission for moon-solar plot in pixels
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

	def draw (self, params):
	    alpha = float(params["alpha"])
	    textSize = float(params["hour_txt_size"])
	    
	    canvas = s.image
	    if alpha < 1.0:
	        canvas = s.image.copy() # if transparency, work on a copy
	    else:
	        canvas = s.image

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
	    if params["hour_ticks"] == True:
	        tickSize = int(self.graph_height / 5)
	        firstIntHourTime = self.startTime.replace(second=0, minute=0, microsecond=0) # everything is calculated in UTC, but this is local
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
	    if params["draw_elev"] == True:
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
	        yy = self.elev_Y
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
	                thickness=1, color=self.sun_color)
	            cv2.line(img=canvas, \
	                pt1=(self.elev_X + int(i * self.res), \
	                    self.elev_Y + int(self.elev_height / 2.0) - self.moonPath[i][1]), \
	                pt2=(self.elev_X + int((i + 1) * self.res), \
	                    self.elev_Y + int(self.elev_height / 2.0) - self.moonPath[i + 1][1]), \
	                thickness=1, color=self.moon_color)

	    if alpha < 1.0:
	        tmpcanv = cv2.addWeighted(canvas, alpha, s.image, 1 - alpha, 0)
	        s.image = tmpcanv
	    else:
	        s.image = canvas

	def exportData(self):
	    # this is temporary until allsky exports all relevant datetimes
	    sun = ephem.Sun()

	    t = datetime.datetime.utcnow()
	    self.location.horizon = 0

	    self.location.date = ephem.Date(t)

	    sun.compute(self.location)
	    sun_alt = "{:.3f}".format(degrees(sun.alt))
	    sun_az = "{:.3f}".format(degrees(sun.az))

	    self.location.date = ephem.Date(self.startTime)

	    moon = ephem.Moon()
	    moon.compute(self.location)
	    moon_trans = ephem.localtime(self.location.next_transit(ephem.Moon())).time().strftime("%H:%M")
	    moon_atran = ephem.localtime(self.location.next_antitransit(ephem.Moon())).time().strftime("%H:%M")
	    moon_rise = ephem.localtime(self.location.next_rising(ephem.Moon())).time().strftime("%H:%M")
	    moon_set = ephem.localtime(self.location.next_setting(ephem.Moon())).time().strftime("%H:%M")
	    
	    sun.compute(self.location)
	    sun_trans = ephem.localtime(self.location.next_transit(ephem.Sun())).time().strftime("%H:%M")
	    sun_atran = ephem.localtime(self.location.next_antitransit(ephem.Sun())).time().strftime("%H:%M")
	    
	    #age = moon.age()

	    os.environ["AS_SUN_ALT"] = str(sun_alt)
	    os.environ["AS_SUN_AZ"] = str(sun_az)

	    os.environ["AS_MOON_TRANSIT"] = str(moon_trans)
	    os.environ["AS_MOON_ANTITRANSIT"] = str(moon_atran)
	    os.environ["AS_MOONRISE"] = str(moon_rise)
	    os.environ["AS_MOONSET"] = str(moon_set)

	    os.environ["AS_SUN_NOON"] = str(sun_trans)
	    os.environ["AS_SUN_MIDNIGHT"] = str(sun_atran)


	def __init__(self, debug, params):
	    self.get_params(debug, params)
	    self.set_size(debug, params)
	    self.set_time(debug, params)
	    self.calculations(debug, params)
	    if params["draw_elev"] == True:
	        self.calSunMoon(params)

def lightgraph(params, event):
	s.startModuleDebug("allsky_lightgraph")

	debug = params["debug"]
	drawer = lGraph(debug, params)
	drawer.exportData()
	drawer.draw(params)
	result ="Light Graph Complete"
	
	s.log(1, "INFO {0}".format(result))
	return result
