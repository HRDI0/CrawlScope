"""
Data models for crawl results.
Mirrors all the data columns/tabs available in Screaming Frog.
"""
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class LinkData:
    """Represents a link found on a page."""
    source_url: str = ""
    target_url: str = ""
    anchor_text: str = ""
    link_type: str = ""         # hyperlink, image, css, js, canonical, hreflang, etc.
    is_internal: bool = True
    is_follow: bool = True
    rel_attributes: list[str] = field(default_factory=list)
    status_code: int = 0
    link_position: str = ""     # header, nav, content, footer, sidebar


@dataclass
class ImageData:
    """Represents an image found on a page."""
    src: str = ""
    alt_text: str = ""
    title: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: int = 0
    status_code: int = 0
    is_missing_alt: bool = False
    is_missing_alt_attribute: bool = False
    alt_over_100: bool = False


@dataclass
class HeadingData:
    """Represents heading structure on a page."""
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    h4: list[str] = field(default_factory=list)
    h5: list[str] = field(default_factory=list)
    h6: list[str] = field(default_factory=list)

    @property
    def h1_count(self) -> int:
        return len(self.h1)

    @property
    def missing_h1(self) -> bool:
        return self.h1_count == 0

    @property
    def multiple_h1(self) -> bool:
        return self.h1_count > 1


@dataclass
class ResourceData:
    """Represents a CSS/JS/other resource."""
    url: str = ""
    resource_type: str = ""     # css, javascript, font, media, other
    status_code: int = 0
    file_size: int = 0
    content_type: str = ""


@dataclass
class StructuredDataItem:
    """Represents a structured data item found on a page."""
    format_type: str = ""       # json-ld, microdata, rdfa
    schema_type: str = ""       # e.g., "Article", "Product", "Organization"
    raw_data: dict = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    is_valid: bool = True


@dataclass
class HreflangData:
    """Represents hreflang annotations."""
    source_url: str = ""
    language: str = ""
    region: str = ""
    target_url: str = ""
    has_return_tag: bool = False
    is_valid: bool = True
    issues: list[str] = field(default_factory=list)


@dataclass
class SecurityData:
    """Security-related data for a page."""
    is_https: bool = False
    has_mixed_content: bool = False
    mixed_content_urls: list[str] = field(default_factory=list)
    ssl_certificate_valid: bool = True
    ssl_expiry_date: Optional[str] = None
    hsts_enabled: bool = False
    x_frame_options: str = ""
    x_content_type_options: str = ""
    x_xss_protection: str = ""
    content_security_policy: str = ""
    referrer_policy: str = ""
    permissions_policy: str = ""


@dataclass
class PageSpeedData:
    """Page performance metrics."""
    total_size: int = 0         # bytes
    html_size: int = 0
    css_size: int = 0
    js_size: int = 0
    image_size: int = 0
    response_time: float = 0.0  # seconds
    ttfb: float = 0.0           # Time to First Byte
    total_requests: int = 0


@dataclass
class CustomExtractionResult:
    """Result from a custom extraction rule."""
    name: str = ""
    value: str = ""
    extraction_type: str = ""   # xpath, css, regex


@dataclass
class PageData:
    """
    Complete data for a crawled page.
    This is the primary data structure - equivalent to a row in Screaming Frog's main table.
    """
    # === Basic Info ===
    url: str = ""
    final_url: str = ""         # After redirects
    status_code: int = 0
    status_text: str = ""
    content_type: str = ""
    response_time: float = 0.0
    crawl_depth: int = 0
    crawl_timestamp: str = ""

    # === Redirects ===
    is_redirect: bool = False
    redirect_chain: list[str] = field(default_factory=list)
    redirect_type: str = ""     # 301, 302, 303, 307, 308, meta-refresh, js

    # === Title ===
    title: str = ""
    title_length: int = 0
    title_pixel_width: int = 0  # Estimated pixel width

    # === Meta Description ===
    meta_description: str = ""
    meta_description_length: int = 0
    meta_description_pixel_width: int = 0

    # === Meta Keywords ===
    meta_keywords: str = ""
    meta_keywords_length: int = 0

    # === Meta Robots ===
    meta_robots: str = ""
    x_robots_tag: str = ""
    meta_refresh: str = ""
    is_indexable: bool = True
    indexability_status: str = "Indexable"

    # === Canonical ===
    canonical_url: str = ""
    http_canonical: str = ""
    canonical_is_self: bool = False
    canonical_mismatch: bool = False

    # === Headings ===
    headings: HeadingData = field(default_factory=HeadingData)

    # === Content ===
    word_count: int = 0
    sentence_count: int = 0
    avg_words_per_sentence: float = 0.0
    flesch_reading_ease: float = 0.0
    readability: str = ""       # "Easy", "Standard", "Difficult", etc.
    text_ratio: float = 0.0     # Text to HTML ratio
    content_hash: str = ""      # MD5 for duplicate detection
    simhash: int = 0            # SimHash for near-duplicate detection
    body_text: str = ""         # Extracted visible text (truncated)
    detected_language: str = ""

    # === Links ===
    internal_links: list[LinkData] = field(default_factory=list)
    external_links: list[LinkData] = field(default_factory=list)
    inlinks_count: int = 0      # Pages linking TO this page
    unique_inlinks: int = 0
    unique_js_inlinks: int = 0
    outlinks_count: int = 0
    unique_outlinks: int = 0
    unique_js_outlinks: int = 0
    external_outlinks: int = 0
    unique_external_outlinks: int = 0
    unique_external_js_outlinks: int = 0
    pct_of_total: float = 0.0   # % of total inlinks
    link_score: float = 0.0     # Internal PageRank approximation

    # === Images ===
    images: list[ImageData] = field(default_factory=list)
    images_count: int = 0
    images_missing_alt: int = 0

    # === Resources ===
    css_resources: list[ResourceData] = field(default_factory=list)
    js_resources: list[ResourceData] = field(default_factory=list)
    other_resources: list[ResourceData] = field(default_factory=list)

    # === Structured Data ===
    structured_data: list[StructuredDataItem] = field(default_factory=list)

    # === Hreflang ===
    hreflang_annotations: list[HreflangData] = field(default_factory=list)

    # === Pagination ===
    rel_next: str = ""
    rel_prev: str = ""
    http_rel_next: str = ""
    http_rel_prev: str = ""

    # === Open Graph ===
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = ""
    og_url: str = ""

    # === Twitter Card ===
    twitter_card: str = ""
    twitter_title: str = ""
    twitter_description: str = ""
    twitter_image: str = ""

    # === Security ===
    security: SecurityData = field(default_factory=SecurityData)

    # === Performance ===
    page_speed: PageSpeedData = field(default_factory=PageSpeedData)

    # === Custom Extractions ===
    custom_extractions: list[CustomExtractionResult] = field(default_factory=list)

    # === Custom Search Matches ===
    custom_search_matches: dict[str, bool] = field(default_factory=dict)

    # === Language ===
    html_lang: str = ""
    content_language: str = ""

    # === Encoding ===
    charset: str = ""

    # === HTTP Headers ===
    response_headers: dict[str, str] = field(default_factory=dict)
    http_version: str = ""
    last_modified: str = ""
    cookies: str = ""

    # === URL Properties ===
    folder_depth: int = 0       # Number of path segments
    url_length: int = 0
    url_encoded_address: str = ""

    # === Transfer ===
    transferred_bytes: int = 0

    # === Near Duplicates ===
    closest_similarity_match: str = ""
    near_duplicate_count: int = 0

    # === JS Rendering Comparison ===
    rendered_title: str = ""
    rendered_h1: str = ""
    rendered_meta_description: str = ""
    rendered_canonical: str = ""
    rendered_meta_robots: str = ""
    rendered_word_count: int = 0
    word_count_change: int = 0
    js_word_count_pct: float = 0.0

    # === Errors ===
    crawl_error: str = ""
    is_error: bool = False


@dataclass
class CrawlResult:
    """Complete crawl result containing all pages and summary data."""
    start_url: str = ""
    domain: str = ""
    crawl_start_time: str = ""
    crawl_end_time: str = ""
    total_urls_crawled: int = 0
    total_internal: int = 0
    total_external: int = 0

    pages: list[PageData] = field(default_factory=list)
    subdomains_found: list[str] = field(default_factory=list)

    # Issue summary counts
    issues: dict[str, int] = field(default_factory=dict)

    # Duplicate tracking
    duplicate_groups: dict[str, list[str]] = field(default_factory=dict)

    # Inlink map: target_url -> [source_urls]
    inlink_map: dict[str, list[str]] = field(default_factory=dict)

    def get_pages_by_status(self, status: int) -> list[PageData]:
        return [p for p in self.pages if p.status_code == status]

    def get_pages_with_issues(self) -> list[PageData]:
        return [p for p in self.pages if p.is_error or p.crawl_error]
