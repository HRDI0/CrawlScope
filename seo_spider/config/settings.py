"""
Crawl configuration - mirrors Screaming Frog's Configuration menu.
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CrawlMode(Enum):
    SPIDER = "spider"           # BFS link discovery
    LIST = "list"               # Crawl from URL list
    SITEMAP = "sitemap"         # Crawl from sitemap


class RenderingMode(Enum):
    RAW_HTML = "raw_html"       # Parse raw HTML only
    JAVASCRIPT = "javascript"   # Full JS rendering via headless browser


class StorageMode(Enum):
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class CrawlConfig:
    """Complete crawl configuration matching Screaming Frog's options."""

    # === General ===
    start_urls: list[str] = field(default_factory=list)
    crawl_mode: CrawlMode = CrawlMode.SPIDER
    max_urls: int = 50000
    max_depth: int = 0                # 0 = unlimited
    max_concurrent: int = 10
    request_timeout: int = 30
    delay_between_requests: float = 0.0    # seconds
    respect_robots_txt: bool = True
    respect_nofollow: bool = True
    respect_canonical: bool = True
    follow_redirects: bool = True
    max_redirects: int = 5

    # === Subdomain Crawling ===
    crawl_subdomains: bool = True
    discover_subdomains: bool = True
    subdomain_discovery_methods: list[str] = field(
        default_factory=lambda: ["dns", "crt_sh", "links", "sitemap"]
    )

    # === JavaScript Rendering ===
    rendering_mode: RenderingMode = RenderingMode.RAW_HTML
    js_wait_time: float = 5.0          # seconds to wait for JS
    js_browser_instances: int = 3
    block_resources: list[str] = field(
        default_factory=lambda: []     # e.g. ["image", "font", "media"]
    )
    ajax_timeout: float = 10.0
    viewport_width: int = 1920
    viewport_height: int = 1080

    # === Bot Evasion ===
    evasion_enabled: bool = True
    rotate_user_agents: bool = True
    randomize_delays: bool = True
    delay_min: float = 0.5
    delay_max: float = 3.0
    use_stealth_mode: bool = True
    rotate_proxies: bool = False
    proxy_list: list[str] = field(default_factory=list)
    spoof_referer: bool = True
    randomize_headers: bool = True
    mimic_browser_fingerprint: bool = True
    honor_retry_after: bool = True
    max_retries: int = 3

    # === Scope ===
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    crawl_external: bool = False       # check status codes of external links
    check_external_links: bool = True
    allowed_protocols: list[str] = field(
        default_factory=lambda: ["http", "https"]
    )

    # === Content ===
    extract_headings: bool = True
    extract_meta: bool = True
    extract_images: bool = True
    extract_links: bool = True
    extract_structured_data: bool = True
    extract_hreflang: bool = True
    extract_canonicals: bool = True
    extract_pagination: bool = True
    calculate_word_count: bool = True
    calculate_text_ratio: bool = True
    detect_duplicates: bool = True

    # === Custom Extraction ===
    custom_extractions: list[dict] = field(default_factory=list)
    # Format: [{"name": "price", "type": "xpath|css|regex", "value": "..."}]

    # === Custom Search ===
    custom_searches: list[dict] = field(default_factory=list)
    # Format: [{"name": "phone", "type": "contains|regex", "value": "..."}]

    # === Security ===
    check_ssl: bool = True
    check_mixed_content: bool = True
    check_http_security_headers: bool = True

    # === Sitemap ===
    generate_sitemap: bool = True
    sitemap_include_images: bool = False
    sitemap_include_lastmod: bool = True
    sitemap_include_priority: bool = False
    sitemap_include_changefreq: bool = False

    # === Storage ===
    storage_mode: StorageMode = StorageMode.HYBRID
    output_dir: str = "./crawl_output"

    # === Export ===
    export_format: str = "csv"         # csv, xlsx, json
    export_internal: bool = True
    export_external: bool = True
    export_images: bool = True
    export_css: bool = True
    export_js: bool = True


def default_config(start_url: str, **overrides) -> CrawlConfig:
    """Create a default configuration for a given URL."""
    config = CrawlConfig(start_urls=[start_url])
    for key, val in overrides.items():
        if hasattr(config, key):
            setattr(config, key, val)
    return config
