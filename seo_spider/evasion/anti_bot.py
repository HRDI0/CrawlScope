"""
Anti-bot detection evasion system.
Implements multiple strategies to avoid being blocked by WAFs and bot detection systems
like Cloudflare, Akamai Bot Manager, DataDome, PerimeterX, etc.
"""
import random
import time
import asyncio
import hashlib
from typing import Optional
from dataclasses import dataclass, field

from .fingerprint import BrowserFingerprint
from .proxy_rotator import ProxyRotator


# Comprehensive list of real-world User-Agent strings
CHROME_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

FIREFOX_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

EDGE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

ALL_USER_AGENTS = CHROME_USER_AGENTS + FIREFOX_USER_AGENTS + EDGE_USER_AGENTS

# Common Accept-Language headers
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9,ko;q=0.8",
    "en-US,en;q=0.9,ja;q=0.8",
    "en-US,en;q=0.9,de;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8",
    "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
]

# Common referrers to simulate natural traffic
REFERRERS = [
    "https://www.google.com/",
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/",
    "https://search.yahoo.com/",
    "",  # Direct traffic
]

# Common screen resolutions
SCREEN_RESOLUTIONS = [
    (1920, 1080), (2560, 1440), (1366, 768), (1440, 900),
    (1536, 864), (1680, 1050), (1280, 720), (3840, 2160),
]


@dataclass
class RequestProfile:
    """A complete request profile for a single HTTP request."""
    user_agent: str = ""
    headers: dict = field(default_factory=dict)
    proxy: Optional[str] = None
    delay: float = 0.0
    viewport: tuple = (1920, 1080)


class AntiBotEvasion:
    """
    Comprehensive anti-bot evasion system.

    Strategies:
    1. User-Agent rotation with consistent browser fingerprints
    2. Realistic HTTP header generation
    3. Request timing randomization (human-like patterns)
    4. Proxy rotation
    5. Referer spoofing
    6. TLS fingerprint mimicking
    7. Cookie management
    8. Rate limiting with adaptive backoff
    9. Retry-After header respect
    """

    def __init__(
        self,
        rotate_ua: bool = True,
        randomize_delays: bool = True,
        delay_min: float = 0.5,
        delay_max: float = 3.0,
        use_stealth: bool = True,
        proxy_list: list[str] = None,
        spoof_referer: bool = True,
    ):
        self.rotate_ua = rotate_ua
        self.randomize_delays = randomize_delays
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.use_stealth = use_stealth
        self.spoof_referer = spoof_referer

        self._current_ua_idx = 0
        self._request_count = 0
        self._domain_request_counts: dict[str, int] = {}
        self._last_request_time: dict[str, float] = {}
        self._blocked_domains: set = set()
        self._retry_after: dict[str, float] = {}

        self.fingerprint = BrowserFingerprint()
        self.proxy_rotator = ProxyRotator(proxy_list or [])

        # Session-persistent UA (changes every N requests)
        self._session_ua = random.choice(ALL_USER_AGENTS)
        self._ua_change_interval = random.randint(50, 150)

    def get_request_profile(self, url: str, domain: str = "") -> RequestProfile:
        """Generate a complete request profile for a URL."""
        self._request_count += 1

        # Rotate UA periodically (not every request - that's suspicious)
        if self.rotate_ua and self._request_count % self._ua_change_interval == 0:
            self._session_ua = random.choice(ALL_USER_AGENTS)
            self._ua_change_interval = random.randint(50, 150)

        ua = self._session_ua
        headers = self._build_headers(ua, url, domain)
        proxy = self.proxy_rotator.get_next() if self.proxy_rotator.has_proxies() else None
        delay = self._calculate_delay(domain)
        viewport = random.choice(SCREEN_RESOLUTIONS)

        return RequestProfile(
            user_agent=ua,
            headers=headers,
            proxy=proxy,
            delay=delay,
            viewport=viewport,
        )

    def _build_headers(self, ua: str, url: str, domain: str) -> dict:
        """Build realistic HTTP headers matching the User-Agent browser."""
        is_chrome = "Chrome" in ua and "Edg" not in ua
        is_firefox = "Firefox" in ua
        is_edge = "Edg" in ua

        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

        # Browser-specific headers
        if is_chrome or is_edge:
            headers["Sec-Ch-Ua"] = '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'
            headers["Sec-Ch-Ua-Mobile"] = "?0"
            headers["Sec-Ch-Ua-Platform"] = random.choice(['"Windows"', '"macOS"', '"Linux"'])
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"
            headers["Sec-Fetch-User"] = "?1"

        if is_firefox:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            headers["DNT"] = "1"
            headers["Sec-GPC"] = "1"

        # Referer spoofing
        if self.spoof_referer:
            if random.random() < 0.6:  # 60% chance of having a referer
                referer = random.choice(REFERRERS)
                if referer:
                    headers["Referer"] = referer
                    if "google" in referer or "bing" in referer:
                        headers["Sec-Fetch-Site"] = "cross-site"

        # Randomize header order slightly (some bots send headers in consistent order)
        items = list(headers.items())
        # Keep essential headers in place, shuffle optional ones
        essential = {k: v for k, v in items[:3]}
        optional = [(k, v) for k, v in items[3:]]
        random.shuffle(optional)
        headers = {**essential, **dict(optional)}

        return headers

    def _calculate_delay(self, domain: str) -> float:
        """
        Calculate delay before next request.
        Uses variable timing to mimic human browsing patterns.
        """
        if not self.randomize_delays:
            return 0.0

        # Check retry-after
        if domain in self._retry_after:
            retry_time = self._retry_after[domain]
            if time.time() < retry_time:
                return retry_time - time.time()
            else:
                del self._retry_after[domain]

        # Base delay with randomization
        base_delay = random.uniform(self.delay_min, self.delay_max)

        # Add occasional longer pauses (simulating reading time)
        if random.random() < 0.1:  # 10% chance of longer pause
            base_delay += random.uniform(2.0, 8.0)

        # Adaptive: increase delay if we're hitting the same domain a lot
        domain_count = self._domain_request_counts.get(domain, 0)
        if domain_count > 100:
            base_delay *= 1.5
        elif domain_count > 500:
            base_delay *= 2.0

        self._domain_request_counts[domain] = domain_count + 1
        return base_delay

    def handle_response_status(self, domain: str, status_code: int, headers: dict = None):
        """Handle response status codes for adaptive behavior."""
        headers = headers or {}

        if status_code == 429:  # Too Many Requests
            retry_after = headers.get('Retry-After', '60')
            try:
                wait_seconds = int(retry_after)
            except ValueError:
                wait_seconds = 60
            self._retry_after[domain] = time.time() + wait_seconds
            # Also increase delays for this domain
            self.delay_min = min(self.delay_min * 1.5, 10.0)
            self.delay_max = min(self.delay_max * 1.5, 20.0)

        elif status_code == 403:  # Forbidden - possibly blocked
            self._blocked_domains.add(domain)
            # Rotate UA immediately
            self._session_ua = random.choice(ALL_USER_AGENTS)

        elif status_code == 503:  # Service Unavailable
            retry_after = headers.get('Retry-After', '30')
            try:
                wait_seconds = int(retry_after)
            except ValueError:
                wait_seconds = 30
            self._retry_after[domain] = time.time() + wait_seconds

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a domain appears to be blocking us."""
        return domain in self._blocked_domains

    async def wait(self, domain: str):
        """Async wait with the calculated delay."""
        profile = self.get_request_profile("", domain)
        if profile.delay > 0:
            await asyncio.sleep(profile.delay)

    def get_playwright_stealth_scripts(self) -> list[str]:
        """
        Return JavaScript snippets to inject into Playwright pages
        to evade common bot detection techniques.
        """
        return [
            # Override navigator.webdriver
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            # Override navigator.plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ]
            });
            """,
            # Override navigator.languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            """,
            # Fix Chrome runtime
            """
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            """,
            # Override permissions query
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
            # Spoof WebGL vendor and renderer
            """
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.call(this, parameter);
            };
            """,
            # Canvas fingerprint noise
            """
            const toBlob = HTMLCanvasElement.prototype.toBlob;
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            const getImageData = CanvasRenderingContext2D.prototype.getImageData;

            HTMLCanvasElement.prototype.toBlob = function() {
                const context = this.getContext('2d');
                if (context) {
                    const shift = { r: Math.floor(Math.random() * 10) - 5, g: Math.floor(Math.random() * 10) - 5, b: Math.floor(Math.random() * 10) - 5 };
                    const width = this.width, height = this.height;
                    const imageData = context.getImageData(0, 0, width, height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += shift.r;
                        imageData.data[i+1] += shift.g;
                        imageData.data[i+2] += shift.b;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return toBlob.apply(this, arguments);
            };
            """,
            # Disable automation flags
            """
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """,
        ]
