import random
from typing import Any, Literal
from pydantic import BaseModel

_CHROME_BUILDS = ["140.0.0.0", "141.0.0.0", "142.0.0.0", "143.0.0.0", "144.0.0.0", "145.0.0.0", "146.0.0.0"]
_ANDROID_BUILDS = ["13", "14", "15"]
_ANDROID_MODELS = ["SM-S908B", "SM-A546B", "Pixel 7", "Pixel 8", "SM-G991B"]
_IOS_VERSIONS = ["16_6", "17_0", "17_4", "18_0"]

_WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{build} Safari/537.36"
_MAC_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{build} Safari/537.36"
_LINUX_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{build} Safari/537.36"
_ANDROID_UA = "Mozilla/5.0 (Linux; Android {android}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{build} Mobile Safari/537.36"
_IOS_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS {ios} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
_UA_BY_OS = {"win": _WIN_UA, "mac": _MAC_UA, "linux": _LINUX_UA}

_WIN_RENDERERS = [
    "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 6600 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
]
_MAC_RENDERERS = [
    "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)",
    "ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)",
    "ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    "ANGLE (Intel, Intel(R) Iris(TM) Plus Graphics OpenGL Engine, OpenGL 4.1)",
]
_LINUX_RENDERERS = ["ANGLE (Intel, Mesa Intel(R) UHD Graphics 620 (KBL GT2), OpenGL 4.6)", "ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.6)"]
_ANDROID_RENDERERS = ["Adreno (TM) 730", "Adreno (TM) 660", "Mali-G78 MP14"]
_IOS_RENDERERS = ["Apple GPU"]

_RENDERERS_BY_OS = {"win": _WIN_RENDERERS, "mac": _MAC_RENDERERS, "linux": _LINUX_RENDERERS, "android": _ANDROID_RENDERERS, "ios": _IOS_RENDERERS}
_VENDOR_BY_OS = {"win": "Google Inc. (NVIDIA)", "mac": "Google Inc. (Apple)", "linux": "Google Inc. (Intel)", "android": "Qualcomm", "ios": "Apple Inc."}
_RESOLUTIONS_BY_OS = {"win": ["1920_1080", "2560_1440", "1680_1050", "1440_900"], "mac": ["2560_1600", "2880_1800", "1920_1200", "1440_900"], "linux": ["1920_1080", "2560_1440", "1280_1024"]}

def _rand_ua(os: str) -> str:
    if os == "android": return _ANDROID_UA.format(android=random.choice(_ANDROID_BUILDS), model=random.choice(_ANDROID_MODELS), build=random.choice(_CHROME_BUILDS))
    if os == "ios": return _IOS_UA.format(ios=random.choice(_IOS_VERSIONS))
    return _UA_BY_OS.get(os, _WIN_UA).format(build=random.choice(_CHROME_BUILDS))

def _rand_renderer(os: str) -> str: return random.choice(_RENDERERS_BY_OS.get(os, _WIN_RENDERERS))
def _rand_resolution(os: str) -> str: return random.choice(_RESOLUTIONS_BY_OS.get(os, ["1920_1080", "2560_1440", "1680_1050", "1440_900"]))

class WebGLConfig(BaseModel):
    model_config = {"frozen": True}
    unmasked_vendor: str = ""
    unmasked_renderer: str = ""

class Fingerprint(BaseModel):
    model_config = {"frozen": True}

    os: Literal["win", "mac", "linux", "android", "ios"] = "win"
    ua: str = ""
    screen_resolution: str = ""
    automatic_timezone: str = "1"
    timezone: str = ""
    language: list[str] = []
    location: str = "ask"
    webrtc: str = "disabled"
    do_not_track: str = "default"
    interface_language: list[str] = []
    webgpu: str = "webgl"
    canvas: str = "1"
    webgl: str = "1"
    webgl_image: str = "1"
    audio: str = "1"
    media_devices: str = "1"
    client_rects: str = "1"
    speech_voices: str = "1"
    hardware_concurrency: str = "8"
    device_memory: str = "8"
    fonts: str | list[str] = "default"
    font_type: str = "default"
    flash: str = "block"
    scan_port_type: str = "1"
    webgl_config: WebGLConfig = WebGLConfig()

    @classmethod
    def random(cls, os: Literal["win", "mac", "linux", "android", "ios"] = "win", **kwargs: Any) -> "Fingerprint":
        return cls(os=os, ua=_rand_ua(os), screen_resolution=_rand_resolution(os),
                   webgl_config=WebGLConfig(unmasked_vendor=_VENDOR_BY_OS.get(os, "Google Inc. (NVIDIA)"),
                                            unmasked_renderer=_rand_renderer(os)), **kwargs)

    def to_api(self) -> dict[str, Any]:
        ua = self.ua or _rand_ua(self.os)
        res = self.screen_resolution or _rand_resolution(self.os)
        vendor = self.webgl_config.unmasked_vendor or _VENDOR_BY_OS.get(self.os, "Google Inc. (NVIDIA)")
        renderer = self.webgl_config.unmasked_renderer or _rand_renderer(self.os)
        cfg: dict[str, Any] = {
            "os": self.os, "ua": ua, "automatic_timezone": self.automatic_timezone,
            "language": self.language, "location": self.location, "webrtc": self.webrtc,
            "do_not_track": self.do_not_track, "interface_language": self.interface_language,
            "webgpu": self.webgpu, "screen_resolution": res, "canvas": self.canvas,
            "webgl": self.webgl, "webgl_image": self.webgl_image, "audio": self.audio,
            "media_devices": self.media_devices, "client_rects": self.client_rects,
            "speech_voices": self.speech_voices, "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory, "flash": self.flash, "scan_port_type": self.scan_port_type,
            "webgl_config": {"unmasked_vendor": vendor, "unmasked_renderer": renderer},
        }
        if self.automatic_timezone == "0" and self.timezone: cfg["timezone"] = self.timezone
        if self.font_type != "default": cfg["font_type"] = self.font_type
        if self.fonts != "default": cfg["fonts"] = self.fonts if isinstance(self.fonts, list) else [self.fonts]
        return cfg

DEFAULT_FINGERPRINT = Fingerprint()
WIN_FINGERPRINT     = Fingerprint(os="win")
MAC_FINGERPRINT     = Fingerprint(os="mac")
LINUX_FINGERPRINT   = Fingerprint(os="linux")
ANDROID_FINGERPRINT = Fingerprint(os="android")
IOS_FINGERPRINT     = Fingerprint(os="ios")
