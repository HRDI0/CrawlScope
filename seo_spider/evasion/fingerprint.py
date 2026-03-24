"""
Browser fingerprint management.
Generates consistent browser fingerprints that match User-Agent strings.
"""
import random
import hashlib
from dataclasses import dataclass


@dataclass
class FingerprintProfile:
    """A complete browser fingerprint."""
    platform: str
    vendor: str
    renderer: str
    screen_width: int
    screen_height: int
    color_depth: int
    timezone_offset: int
    language: str
    hardware_concurrency: int
    device_memory: int
    max_touch_points: int
    do_not_track: str


# Realistic WebGL renderers per platform
WEBGL_RENDERERS = {
    "Windows": [
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
    ],
    "macOS": [
        ("Apple", "Apple M1"),
        ("Apple", "Apple M2"),
        ("Apple", "Apple M1 Pro"),
        ("Intel Inc.", "Intel Iris Plus Graphics 645"),
    ],
    "Linux": [
        ("Mesa", "Mesa Intel(R) UHD Graphics 630 (CFL GT2)"),
        ("X.Org", "AMD Radeon RX 580 (polaris10, LLVM 15.0.7, DRM 3.49)"),
    ],
}

TIMEZONES = [-480, -420, -360, -300, -240, 0, 60, 120, 180, 330, 540, 600]


class BrowserFingerprint:
    """Generate consistent, realistic browser fingerprints."""

    def __init__(self):
        self._profiles: dict[str, FingerprintProfile] = {}

    def get_fingerprint(self, user_agent: str) -> FingerprintProfile:
        """Get or create a consistent fingerprint for a given User-Agent."""
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        if ua_hash in self._profiles:
            return self._profiles[ua_hash]

        # Determine platform from UA
        if "Windows" in user_agent:
            platform = "Windows"
        elif "Macintosh" in user_agent or "Mac OS" in user_agent:
            platform = "macOS"
        else:
            platform = "Linux"

        renderer_data = random.choice(WEBGL_RENDERERS.get(platform, WEBGL_RENDERERS["Windows"]))

        resolutions = [
            (1920, 1080), (2560, 1440), (1366, 768),
            (1440, 900), (3840, 2160), (1536, 864),
        ]
        res = random.choice(resolutions)

        profile = FingerprintProfile(
            platform=platform,
            vendor=renderer_data[0],
            renderer=renderer_data[1],
            screen_width=res[0],
            screen_height=res[1],
            color_depth=24,
            timezone_offset=random.choice(TIMEZONES),
            language="en-US",
            hardware_concurrency=random.choice([4, 8, 12, 16]),
            device_memory=random.choice([4, 8, 16, 32]),
            max_touch_points=0,
            do_not_track="1" if "Firefox" in user_agent else "unspecified",
        )

        self._profiles[ua_hash] = profile
        return profile

    def get_stealth_js(self, profile: FingerprintProfile) -> str:
        """Generate JavaScript to set the fingerprint in a headless browser."""
        return f"""
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{profile.platform}'
        }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {profile.hardware_concurrency}
        }});
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {profile.device_memory}
        }});
        Object.defineProperty(screen, 'width', {{
            get: () => {profile.screen_width}
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {profile.screen_height}
        }});
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {profile.color_depth}
        }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => {profile.max_touch_points}
        }});
        """
