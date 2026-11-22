"""
allsky_sharedsky.py

Part of allsky postprocess.py modules.
https://github.com/AllskyTeam/allsky

Sends this camera's images and meteors to SharedSky (https://allskyhub.org), the network
that measures meteors and fireballs together with other cameras: the camera's data on
start and on changes, a small image about once a minute (the full frame when the hub asks
for one to work out the camera's orientation from the stars) and every meteor that the
Meteor Detection (temporal) module saved, with its track. Everything goes out over HTTPS;
no FTP, MQTT or open port is needed.

The open API is connect/v1 (https://allskyhub.org/entwickler/connect, SPEC §10.2 and §10.4
of https://github.com/benhartwich/allskyhub).
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
import subprocess
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, ClassVar

import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

HUB = "https://allskyhub.org"
API = "/api/connect/v1"
THUMB_SIDE = 640  # the longest side of a thumbnail (SPEC §10.2)
THUMB_MAX = 300 * 1024
FRAME_MAX = 8 * 1024 * 1024
STATION_EVERY = 6 * 3600  # PUT /station again after this: its answer brings the orientation
CLOCK_EVERY = 600  # how long the clock check is kept
METEORS_BACK = 24 * 3600  # meteors not sent yet are looked for this far back
KEEP_SENT = 3 * 86400
EVENTS_PER_RUN = 3  # the rest follow with the next images
TIMEOUT = (5, 20)  # connect, read: the flow waits for this module
METEOR_SIDECAR = re.compile(r"meteors-(\d{14})\.json")

# (status, JSON answer); status 0 when the hub could not be reached.
Answer = tuple[int, dict[str, Any]]
Transport = Callable[..., Answer]


def requests_transport(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
) -> Answer:
    """One request with requests, which Allsky installs; ``OSError`` when unreachable."""
    import requests  # only on the camera, never in the tests

    r = requests.request(method, url, headers=headers, json=json_body, files=files, timeout=TIMEOUT)
    try:
        body = r.json()
    except ValueError:
        body = {}
    return r.status_code, body if isinstance(body, dict) else {}


def iso(unix: float) -> str:
    utc = dt.timezone.utc  # noqa: UP017 - dt.UTC needs Python 3.11, older Pis have 3.9
    return dt.datetime.fromtimestamp(unix, utc).isoformat(timespec="milliseconds")


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    """Width and height from a JPEG's frame header, without decoding it."""
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = int.from_bytes(data[i + 2 : i + 4], "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(data[i + 5 : i + 7], "big")
            width = int.from_bytes(data[i + 7 : i + 9], "big")
            return width, height
        i += 2 + length
    return None


def clock_synced() -> bool:
    """Whether systemd says the clock is synchronised (NTP or GPS via chrony)."""
    try:
        out = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.stdout.strip() == "yes"


def encode_jpeg(image: Any, longest: int | None, limit: int) -> bytes | None:
    """The image as a JPEG of at most ``limit`` bytes, scaled down to ``longest``."""
    import cv2  # Allsky's own

    h, w = image.shape[:2]
    if longest and max(w, h) > longest:
        f = longest / max(w, h)
        image = cv2.resize(image, (round(w * f), round(h * f)), interpolation=cv2.INTER_AREA)
    for quality in (85, 70, 55, 40):
        ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if ok and len(buf) <= limit:
            return buf.tobytes()
    return None


def sky_to_pixel(
    orientation: dict[str, Any] | None, alt: float, az: float, width: int | None = None
) -> tuple[float, float] | None:
    """Where the hub's orientation (``orientation.json``, SPEC §4.8) puts a direction in the
    image: altitude and azimuth in degrees (azimuth from north over east) to pixels of the
    full frame, or of an image ``width`` wide (a resized copy). None without a lens, e.g.
    for an overlay of constellations or the cardinal points."""
    lens = (orientation or {}).get("lens")
    if not lens or not lens.get("width"):
        return None
    tx, ty = float(lens["tilt_east_deg"]), float(lens["tilt_north_deg"])
    tau = math.radians(math.hypot(tx, ty))
    if tau > 1e-14:  # the axis leans: turn the direction into the camera's frame
        phi = math.atan2(tx, ty)
        a, z = math.radians(alt), math.radians(az)
        v = (math.cos(a) * math.sin(z), math.cos(a) * math.cos(z), math.sin(a))
        ax, ay = math.sin(tau) * math.sin(phi), math.sin(tau) * math.cos(phi)
        n = math.hypot(ax, ay)
        k = (ay / n, -ax / n, 0.0)  # axis x up, normalised
        kv = (k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0])
        kd = k[0] * v[0] + k[1] * v[1] + k[2] * v[2]
        c, s = math.cos(tau), math.sin(tau)
        w = [v[i] * c + kv[i] * s + k[i] * kd * (1 - c) for i in range(3)]
        alt = math.degrees(math.asin(max(-1.0, min(1.0, w[2]))))
        az = math.degrees(math.atan2(w[0], w[1])) % 360.0
    t = (90.0 - alt) / 90.0
    r = float(lens["a1"]) * t + float(lens["a3"]) * t**3
    north = float(orientation["north_deg"])  # type: ignore[index]
    ang = math.radians(north - az if orientation.get("mirrored") else north + az)  # type: ignore[union-attr]
    f = width / float(lens["width"]) if width else 1.0
    return (float(lens["cx"]) + r * math.sin(ang)) * f, (float(lens["cy"]) - r * math.cos(ang)) * f


def station_body(
    *,
    name: str,
    latitude: float,
    longitude: float,
    elevation_m: float | None,
    version: str | None,
    focal_mm: float | None,
    width: int,
    height: int,
    synced: bool,
) -> dict[str, Any]:
    """``PUT /station`` (SPEC §10.2): the full frame is the image as this module sees it."""
    return {
        "name": name[:100],
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation_m,
        "software": "Allsky",
        "software_version": (version or "")[:40] or None,
        "lens": {"focal_mm": focal_mm} if focal_mm else None,
        "width": width,
        "height": height,
        "clock_synced": synced,
    }


def frame_metadata(
    *,
    start: float,
    exposure_s: float,
    gain: float | None,
    night: bool,
    synced: bool,
    stars: int | None,
) -> dict[str, Any]:
    """``POST /frames`` metadata; ``time`` is the middle of the exposure."""
    return {
        "time": iso(start + exposure_s / 2),
        "exposure_s": exposure_s,
        "gain": gain,
        "night": night,
        "clock_synced": synced,
        "stars": stars,
        "sky_brightness": None,
    }


def meteors(
    folder: Path,
    since: float,
    sent: dict[str, float],
    exposure_at: Callable[[int], float | None],
    synced: bool,
) -> Iterator[tuple[str, dict[str, Any], Path]]:
    """The meteors the Meteor Detection (temporal) module saved and this module did not send
    yet, oldest first: (key, ``POST /events`` metadata, the meteor's full frame). The module
    writes ``meteors-<start of the exposure, local time>.json`` beside the image with the
    two ends of each streak; one event per streak."""
    try:
        sidecars = sorted(p for p in folder.iterdir() if METEOR_SIDECAR.fullmatch(p.name))
    except OSError:
        return
    for sidecar in sidecars:
        try:
            if sidecar.stat().st_mtime < since:
                continue
            entries = json.loads(sidecar.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(entries, list):
            continue
        stamp = METEOR_SIDECAR.fullmatch(sidecar.name).group(1)  # type: ignore[union-attr]
        start = int(time.mktime(time.strptime(stamp, "%Y%m%d%H%M%S")))
        # The hour repeated when the clocks go back: mktime may be an hour off, the frame
        # this module saw tells which. Unknown (the module did not run): the exposure is 0.
        exposure = 0.0
        for guess in (start, start - 3600, start + 3600):
            found = exposure_at(guess)
            if found is not None:
                start, exposure = guess, found
                break
        for n, entry in enumerate(entries):
            key = f"{stamp}:{n}"
            if key in sent or not isinstance(entry, dict):
                continue
            try:
                track = [[float(v) for v in entry["p1"]], [float(v) for v in entry["p2"]]]
            except (KeyError, TypeError, ValueError):
                continue
            image = folder / str(entry.get("file") or f"meteors-{stamp}.jpg")
            meta = {
                "kind": "meteor",
                "start": iso(start),
                "end": iso(start + exposure),
                "track": track,
                "clock_synced": synced,
            }
            yield key, meta, image


class Hub:
    """The few calls of connect/v1; ``test`` sends to its test mode, which stores nothing."""

    def __init__(
        self, base: str, station_id: str, secret: str, transport: Transport, test: bool
    ) -> None:
        self.url = base.rstrip("/") + API + ("/test" if test else "")
        self.headers = {"Authorization": f"Bearer {station_id}:{secret}"}
        self.transport = transport

    def _send(self, method: str, path: str, **kwargs: Any) -> Answer:
        try:
            return self.transport(method, self.url + path, headers=self.headers, **kwargs)
        except OSError:
            return 0, {}

    def station(self, body: dict[str, Any]) -> Answer:
        return self._send("PUT", "/station", json_body=body)

    def _multipart(self, path: str, meta: dict[str, Any], image: bytes) -> Answer:
        files = {
            "metadata": ("metadata.json", json.dumps(meta).encode(), "application/json"),
            "image": ("image.jpg", image, "image/jpeg"),
        }
        return self._send("POST", path, files=files)

    def frame(self, meta: dict[str, Any], image: bytes) -> Answer:
        return self._multipart("/frames", meta, image)

    def event(self, meta: dict[str, Any], image: bytes) -> Answer:
        return self._multipart("/events", meta, image)


class ALLSKYSHAREDSKY(ALLSKYMODULEBASE):
    meta_data: ClassVar[dict[str, Any]] = {
        "name": "SharedSky",
        "description": "Send images and meteors to SharedSky, measured with other cameras",
        "module": "allsky_sharedsky",
        "version": "v1.0.0",
        "centersettings": "false",
        "testable": "true",
        "group": "Data Export",
        "events": ["day", "night"],
        "experimental": "true",
        "arguments": {
            "stationid": "",
            "secret": "",
            "name": "",
            "elevation": "",
            "focal": "",
            "interval": "60",
            "meteors": "true",
            "meteorfolder": "",
            "hub": HUB,
        },
        "argumentdetails": {
            "stationid": {
                "required": "true",
                "description": "Station ID",
                "help": "The 26 characters shown when you connected the camera at https://allskyhub.org (Kamera verbinden).",
                "tab": "SharedSky",
            },
            "secret": {
                "required": "true",
                "description": "Secret",
                "help": "The 64 characters shown once with the station ID. A new one can be made on the station's page.",
                "tab": "SharedSky",
                "secret": "true",
            },
            "name": {
                "required": "false",
                "description": "Name",
                "help": "The station's name in the network. Empty: Allsky's location.",
                "tab": "SharedSky",
            },
            "elevation": {
                "required": "false",
                "description": "Elevation (m)",
                "help": "The camera's height above sea level, for measuring meteor heights.",
                "tab": "SharedSky",
                "type": {"fieldtype": "spinner", "min": -500, "max": 9000, "step": 1},
            },
            "focal": {
                "required": "false",
                "description": "Lens focal length (mm)",
                "help": "Optional. The hub works out the lens from the stars itself.",
                "tab": "SharedSky",
            },
            "interval": {
                "required": "false",
                "description": "Image every (s)",
                "help": "How often a small image is sent. The hub keeps one every 5 minutes.",
                "tab": "SharedSky",
                "type": {"fieldtype": "spinner", "min": 30, "max": 600, "step": 10},
            },
            "meteors": {
                "required": "false",
                "description": "Send meteors",
                "help": "Send the meteors the Meteor Detection (temporal) module saved, with their track. Put this module after it in the night flow.",
                "tab": "Meteors",
                "type": {"fieldtype": "checkbox"},
            },
            "meteorfolder": {
                "required": "false",
                "description": "Meteor folder",
                "help": "Where the meteor module saves its images. Empty: its default, the website's meteors folder.",
                "tab": "Meteors",
            },
            "hub": {
                "required": "false",
                "description": "Hub",
                "help": "Leave as it is.",
                "tab": "Advanced",
            },
        },
        "enabled": "false",
        "changelog": {
            "v1.0.0": [
                {
                    "author": "Benjamin Hartwich (Agent assisted)",
                    "authorurl": "https://github.com/benhartwich/",
                    "changes": "Initial release",
                }
            ]
        },
    }

    transport: Transport = staticmethod(requests_transport)
    encode: Callable[[Any, int | None, int], bytes | None] = staticmethod(encode_jpeg)
    clock: Callable[[], bool] = staticmethod(clock_synced)

    # --- Allsky's values ---

    def _env(self, name: str) -> str:
        return str(allsky_shared.get_environment_variable(name) or "").strip()

    def _number(self, name: str) -> float | None:
        try:
            return float(self._env(name))
        except ValueError:
            return None

    def _variable(self, name: str) -> int | None:
        getter = getattr(allsky_shared, "get_allsky_variable", None)
        try:
            return int(float(getter(name))) if getter else None
        except (TypeError, ValueError):
            return None

    def _float_param(self, name: str) -> float | None:
        try:
            return float(self.get_param(name, "", str, True))
        except ValueError:
            return None

    def _meteor_folder(self) -> Path:
        folder = self.get_param("meteorfolder", "", str, True).strip()
        if folder:
            return Path(folder)
        website = self._env("ALLSKY_WEBSITE")
        if website:
            return Path(website) / "meteors"
        return Path(allsky_shared.ALLSKYPATH) / "html" / "allsky" / "meteors"

    def _state_dir(self) -> Path:
        return Path(allsky_shared.ALLSKYPATH) / "config" / "sharedsky"

    def _load(self) -> dict[str, Any]:
        try:
            state = json.loads((self._state_dir() / "state.json").read_text())
        except (OSError, ValueError):
            state = {}
        return state if isinstance(state, dict) else {}

    def _save(self, state: dict[str, Any]) -> None:
        if self.debug_mode:
            return
        folder = self._state_dir()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            tmp = folder / "state.json.tmp"
            tmp.write_text(json.dumps(state))
            tmp.replace(folder / "state.json")
        except OSError as e:
            self.log(1, f"WARNING: SharedSky could not save its state: {e}")

    def _keep_orientation(self, state: dict[str, Any], orientation: Any) -> None:
        """The hub's orientation (SPEC §4.8, §6.3) for other modules (an overlay)."""
        if orientation == state.get("orientation") or self.debug_mode:
            return
        state["orientation"] = orientation
        try:
            self._state_dir().mkdir(parents=True, exist_ok=True)
            (self._state_dir() / "orientation.json").write_text(json.dumps(orientation))
        except OSError:
            return
        if orientation:
            self.log(1, "INFO: SharedSky worked out the camera's orientation from the stars.")

    # --- answers ---

    def _ok(self, what: str, status: int, answer: dict[str, Any], secret: str) -> bool:
        if status == 200:
            ok = getattr(allsky_shared, "network_ok", None)
            if ok:
                ok("sharedsky")
            if self.debug_mode:
                print(f"{what}: {json.dumps(answer)}")
            return True
        code = answer.get("error", "")
        if status == 401:
            self.log(
                0,
                "ERROR: SharedSky does not know this station ID and secret. Copy them again from the station's page.",
            )
        elif status in (400, 413):
            field = f" ({answer['field']})" if answer.get("field") else ""
            self.log(0, f"ERROR: SharedSky refused the {what}: {code}{field}")
        else:
            message = (
                f"SharedSky could not take the {what} (HTTP {status or 'no connection'} {code})"
            )
            failure = getattr(allsky_shared, "network_failure", None)
            if failure:
                failure("sharedsky", message, secrets=secret)
            else:
                self.log(1, f"WARNING: {message}")
        return False

    # --- the run ---

    def run(self) -> str:
        station_id = self.get_param("stationid", "", str, True).strip()
        secret = self.get_param("secret", "", str, True).strip()
        if not station_id or not secret:
            self.log(0, "ERROR: SharedSky needs the station ID and the secret.")
            return "No station ID or secret"
        image = allsky_shared.image
        if image is None:
            return "No image available"
        latitude, longitude = allsky_shared.get_lat_lon()
        if latitude is None or longitude is None:
            self.log(
                0, "ERROR: SharedSky needs the camera's latitude and longitude in the settings."
            )
            return "No location"

        now = time.time()
        state = self._load()
        state.setdefault("since", now)  # meteors from before the first run stay home
        height, width = image.shape[:2]
        checked_at, synced = state.get("clock") or (0, False)
        if now - checked_at >= CLOCK_EVERY:
            synced = self.clock()
            state["clock"] = [now, synced]
        start = self._number("AS_TIMESTAMP") or now
        exposure = (self._number("AS_EXPOSURE_US") or 0) / 1e6
        exposures = {
            k: v for k, v in (state.get("exposures") or {}).items() if now - float(k) < KEEP_SENT
        }
        exposures[str(int(start))] = exposure
        state["exposures"] = exposures
        hub = Hub(
            self.get_param("hub", HUB, str, True),
            station_id,
            secret,
            self.transport,
            self.debug_mode,
        )
        done: list[str] = []

        name = self.get_param("name", "", str, True).strip()
        body = station_body(
            name=name or str(allsky_shared.get_setting("location") or "") or "Allsky",
            latitude=latitude,
            longitude=longitude,
            elevation_m=self._float_param("elevation"),
            version=self._env("ALLSKY_VERSION"),
            focal_mm=self._float_param("focal"),
            width=width,
            height=height,
            synced=synced,
        )
        again = now - state.get("station_at", 0) >= STATION_EVERY
        if body != state.get("station") or again or self.debug_mode:
            status, answer = hub.station(body)
            if not self._ok("station", status, answer, secret):
                self._save(state)
                return "Station not sent"
            state.update(station=body, station_at=now, full=bool(answer.get("want_full_frame")))
            self._keep_orientation(state, answer.get("orientation"))
            done.append("station")

        interval = max(30.0, self._float_param("interval") or 60.0)
        night = self.event == "night" or str(getattr(allsky_shared, "TOD", "")) == "night"
        if state.get("full") or now - state.get("frame_at", 0) >= interval or self.debug_mode:
            full = bool(state.get("full"))
            jpeg = self.encode(
                image, None if full else THUMB_SIDE, FRAME_MAX if full else THUMB_MAX
            )
            if jpeg is not None:
                meta = frame_metadata(
                    start=start,
                    exposure_s=exposure,
                    gain=self._number("AS_GAIN"),
                    night=night,
                    synced=synced,
                    stars=self._variable("AS_STARCOUNT"),
                )
                status, answer = hub.frame(meta, jpeg)
                if self._ok("full frame" if full else "image", status, answer, secret):
                    state.update(frame_at=now, full=bool(answer.get("want_full_frame")))
                    done.append("full frame" if full else "image")

        if self.get_param("meteors", True, bool):
            sent = {k: v for k, v in (state.get("sent") or {}).items() if now - v < KEEP_SENT}
            since = max(float(state["since"]), now - METEORS_BACK)
            found = meteors(
                self._meteor_folder(), since, sent, lambda t: exposures.get(str(t)), synced
            )
            count = 0
            for key, meta, path in found:
                if count >= EVENTS_PER_RUN:
                    break
                count += 1
                try:
                    data = path.read_bytes()
                except OSError:
                    sent[key] = now
                    continue
                if jpeg_size(data) != (width, height):
                    # Saved at another size than this module sees (resize or crop after
                    # the meteor module): the track would not fit the hub's orientation.
                    self.log(
                        1,
                        f"WARNING: SharedSky skips the meteor {path.name}: it is not {width} x {height}. Put the meteor module and this one at the same place in the flow.",
                    )
                    sent[key] = now
                    continue
                status, answer = hub.event(meta, data)
                if self._ok("meteor", status, answer, secret):
                    sent[key] = now
                    done.append("meteor")
                elif status in (400, 413):
                    sent[key] = now  # it would be refused again
                else:
                    break  # the hub is away: next time
            state["sent"] = sent

        self._save(state)
        result = f"Sent {', '.join(done)}" if done else "Nothing to send"
        self.log(4, f"INFO: SharedSky: {result}")
        return result


def sharedsky(params: dict[str, Any], event: str) -> str:
    return ALLSKYSHAREDSKY(params, event).run()


def sharedsky_cleanup() -> None:
    module_data = {
        "metaData": ALLSKYSHAREDSKY.meta_data,
        "cleanup": {"files": {}, "env": {}},
    }
    allsky_shared.cleanupModule(module_data)
