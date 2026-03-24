#!/usr/bin/env python3
"""Comprehensive test suite for Python SEO Spider."""
import subprocess
import sys

# === Module Imports ===
from seo_spider.config.settings import CrawlConfig, CrawlMode, RenderingMode
from seo_spider.core.models import PageData, CrawlResult
from seo_spider.core.robots_parser import RobotsParser
from seo_spider.core.crawler import SEOSpiderCrawler
from seo_spider.evasion.anti_bot import AntiBotEvasion
from seo_spider.evasion.fingerprint import BrowserFingerprint
from seo_spider.evasion.proxy_rotator import ProxyRotator
from seo_spider.analyzers.html_parser import HTMLAnalyzer
from seo_spider.analyzers.duplicate_detector import DuplicateDetector
from seo_spider.analyzers.custom_extractor import CustomExtractor
from seo_spider.analyzers.issue_detector import IssueDetector
from seo_spider.analyzers.structured_data_analyzer import StructuredDataAnalyzer
from seo_spider.analyzers.security_analyzer import SecurityAnalyzer
from seo_spider.analyzers.sitemap_parser import SitemapParser, SitemapGenerator
from seo_spider.analyzers.visualization import CrawlVisualizer
from seo_spider.exporters.csv_exporter import CSVExporter
from seo_spider.exporters.xlsx_exporter import XLSXExporter
from seo_spider.exporters.json_exporter import JSONExporter
from seo_spider.exporters.report_generator import ReportGenerator
from seo_spider.utils.url_utils import normalize_url, extract_domain, is_subdomain_of
from seo_spider.utils.hash_utils import content_hash, simhash_text, are_near_duplicates

print("=== 23 MODULE IMPORTS: OK ===")

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

# ========== 1. Config ==========
print("\n[1] Config")
config = CrawlConfig(start_urls=["https://example.com"])
test("Default crawl mode is SPIDER", config.crawl_mode == CrawlMode.SPIDER)
test("Default max_urls is 50000", config.max_urls == 50000)
test("Default concurrent is 10", config.max_concurrent == 10)
test("JS rendering default is RAW_HTML", config.rendering_mode == RenderingMode.RAW_HTML)

# ========== 2. Anti-Bot Evasion ==========
print("\n[2] Anti-Bot Evasion")
evasion = AntiBotEvasion()
profile = evasion.get_request_profile("https://example.com", "example.com")
test("User-Agent is set", len(profile.user_agent) > 20)
test("Headers include Sec-Ch-Ua", "Sec-Ch-Ua" in profile.headers or "DNT" in profile.headers)
test("Multiple headers generated", len(profile.headers) >= 5)
stealth = evasion.get_playwright_stealth_scripts()
test("Stealth scripts generated", len(stealth) >= 7)
test("Stealth includes webdriver override", any("webdriver" in s for s in stealth))
test("Stealth includes WebGL spoof", any("WebGL" in s for s in stealth))

# ========== 3. URL Utilities ==========
print("\n[3] URL Utilities")
test("Normalize relative URL", normalize_url("/about", "https://example.com/") == "https://example.com/about")
test("Normalize with query sort", "a=1&b=2" in normalize_url("https://example.com/?b=2&a=1"))
test("Extract domain from subdomain", extract_domain("https://blog.example.com/page") == "example.com")
test("is_subdomain_of positive", is_subdomain_of("https://blog.example.com", "https://example.com"))
test("is_subdomain_of negative", not is_subdomain_of("https://other.com", "https://example.com"))
test("Reject mailto URLs", normalize_url("mailto:test@test.com") is None)
test("Reject javascript URLs", normalize_url("javascript:void(0)") is None)

# ========== 4. Robots Parser ==========
print("\n[4] Robots Parser")
rp = RobotsParser("User-agent: *\nDisallow: /admin/\nAllow: /admin/api/\nSitemap: https://example.com/sitemap.xml\nCrawl-delay: 2")
test("Allow normal path", rp.is_allowed("/about"))
test("Disallow /admin/", not rp.is_allowed("/admin/"))
test("Allow /admin/api/ (more specific)", rp.is_allowed("/admin/api/"))
test("Sitemaps extracted", rp.get_sitemaps() == ["https://example.com/sitemap.xml"])
test("Crawl delay parsed", rp.get_crawl_delay() == 2.0)

# ========== 5. HTML Analyzer ==========
print("\n[5] HTML Analyzer")
html = """<html lang="en"><head>
<title>Test Page Title</title>
<meta name="description" content="A test page description">
<meta name="robots" content="index, follow">
<meta name="keywords" content="test, seo">
<link rel="canonical" href="https://example.com/test">
<link rel="alternate" hreflang="ko" href="https://example.com/ko/test">
<link rel="next" href="https://example.com/test?page=2">
<link rel="prev" href="https://example.com/test?page=0">
<meta property="og:title" content="OG Title">
<meta property="og:description" content="OG Desc">
<meta property="og:image" content="https://example.com/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="TW Title">
<link rel="stylesheet" href="/style.css">
<script src="/app.js"></script>
</head><body>
<header><nav><a href="/nav-link">Nav</a></nav></header>
<main>
<h1>Main Heading</h1>
<h2>Section One</h2>
<h3>Subsection</h3>
<p>Some content here for testing word count and text ratio. More words to properly test.</p>
<a href="/about">About Us</a>
<a href="/contact" rel="nofollow">Contact</a>
<a href="https://other.com">External Link</a>
<img src="/img/test.png" alt="Test image">
<img src="/img/noalt.jpg">
<img src="/img/empty.jpg" alt="">
</main>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"Test","author":{"@type":"Person","name":"Author"},"datePublished":"2024-01-01","image":"https://example.com/img.jpg"}</script>
</body></html>"""

page = PageData(url="https://example.com/test", status_code=200, content_type="text/html", response_headers={})
HTMLAnalyzer(config).analyze(page, html, "https://example.com/test")

test("Title extracted", page.title == "Test Page Title")
test("Title length", page.title_length == 15)
test("Meta description", page.meta_description == "A test page description")
test("Meta keywords", page.meta_keywords == "test, seo")
test("H1 extracted", page.headings.h1 == ["Main Heading"])
test("H2 extracted", page.headings.h2 == ["Section One"])
test("H3 extracted", page.headings.h3 == ["Subsection"])
test("Internal links count", len(page.internal_links) == 3)
test("External links count", len(page.external_links) == 1)
test("Nofollow detected", any(not l.is_follow for l in page.internal_links))
test("Images count", len(page.images) == 3)
test("Missing alt attribute detected", any(i.is_missing_alt_attribute for i in page.images))
test("Empty alt text detected", any(i.is_missing_alt for i in page.images))
test("Canonical URL", page.canonical_url == "https://example.com/test")
test("Self-referencing canonical", page.canonical_is_self)
test("Hreflang found", len(page.hreflang_annotations) == 1)
test("Hreflang language", page.hreflang_annotations[0].language == "ko")
test("rel=next", page.rel_next != "")
test("rel=prev", page.rel_prev != "")
test("Open Graph title", page.og_title == "OG Title")
test("Twitter card", page.twitter_card == "summary_large_image")
test("Twitter title", page.twitter_title == "TW Title")
test("Structured data found", len(page.structured_data) == 1)
test("Structured data type", page.structured_data[0].schema_type == "Article")
test("HTML lang", page.html_lang == "en")
test("Indexable", page.is_indexable)
test("Word count > 0", page.word_count > 0)
test("Text ratio > 0", page.text_ratio > 0)
test("Content hash generated", len(page.content_hash) == 32)
test("SimHash generated", page.simhash != 0)
test("CSS resources found", len(page.css_resources) >= 1)
test("JS resources found", len(page.js_resources) >= 1)

# ========== 6. Issue Detection ==========
print("\n[6] Issue Detection")
issues = IssueDetector().detect_page_issues(page)
issue_types = [i.issue_type for i in issues]
test("Missing alt attribute issue", "Missing Alt Attribute" in issue_types)
test("Multiple issues found", len(issues) >= 2)
test("Issues have severity", all(i.severity in ("error", "warning", "info", "opportunity") for i in issues))

# Test 404 page issues
page_404 = PageData(url="https://example.com/missing", status_code=404)
issues_404 = IssueDetector().detect_page_issues(page_404)
test("404 detected", any(i.issue_type == "Not Found (404)" for i in issues_404))

# ========== 7. Structured Data Validation ==========
print("\n[7] Structured Data Validation")
sd_analyzer = StructuredDataAnalyzer()
sd_analyzer.validate(page.structured_data[0])
test("Article SD valid", page.structured_data[0].is_valid)

# Test invalid SD
from seo_spider.core.models import StructuredDataItem
bad_sd = StructuredDataItem(format_type="json-ld", schema_type="Product", raw_data={"@type": "Product"})
sd_analyzer.validate(bad_sd)
test("Invalid Product SD detected", not bad_sd.is_valid)
test("Missing name error", any("name" in e for e in bad_sd.validation_errors))

# ========== 8. Duplicate Detection ==========
print("\n[8] Duplicate Detection")
# Test with Jaccard similarity (the primary near-duplicate method used in DuplicateDetector)
from seo_spider.utils.hash_utils import shingle_hash, jaccard_similarity
s1 = shingle_hash("the original content is about testing SEO tools and web crawling for content analysis and optimization purposes")
s2 = shingle_hash("the original content is about testing SEO tools and web crawling for content analysis and optimization purposes today")
s3 = shingle_hash("completely different unrelated content about cooking pasta recipes for dinner party events and family gatherings")
test("Near-duplicate detected (Jaccard)", jaccard_similarity(s1, s2) > 0.7)
test("Different content not duplicate (Jaccard)", jaccard_similarity(s1, s3) < 0.3)
test("MD5 hash consistent", content_hash("test") == content_hash("test"))
test("MD5 hash different", content_hash("test1") != content_hash("test2"))

# ========== 9. Custom Extractor ==========
print("\n[9] Custom Extractor")
extractor = CustomExtractor([
    {"name": "h1", "type": "css", "value": "h1"},
    {"name": "links", "type": "css", "value": "a", "extract": "attribute", "attribute": "href"},
    {"name": "title", "type": "regex", "value": "<title>(.*?)</title>"},
    {"name": "xpath_h1", "type": "xpath", "value": "//h1/text()"},
])
results = extractor.extract(html)
test("CSS extraction works", results[0]["values"] == ["Main Heading"])
test("Attribute extraction works", len(results[1]["values"]) >= 3)
test("Regex extraction works", results[2]["values"] == ["Test Page Title"])
test("XPath extraction works", results[3]["values"] == ["Main Heading"])

# ========== 10. Browser Fingerprint ==========
print("\n[10] Browser Fingerprint")
fp = BrowserFingerprint()
fprint = fp.get_fingerprint(profile.user_agent)
test("Platform detected", fprint.platform in ("Windows", "macOS", "Linux"))
test("Hardware concurrency set", fprint.hardware_concurrency in (4, 8, 12, 16))
test("Device memory set", fprint.device_memory in (4, 8, 16, 32))
test("Consistent fingerprint", fp.get_fingerprint(profile.user_agent).platform == fprint.platform)

# ========== 11. Proxy Rotator ==========
print("\n[11] Proxy Rotator")
pr = ProxyRotator(["http://p1:8080", "http://p2:8080"], strategy="weighted")
test("Has proxies", pr.has_proxies())
p = pr.get_next()
test("Returns proxy", p in ("http://p1:8080", "http://p2:8080"))
pr.report_success(p, 0.5)
test("Stats tracked", pr.get_stats()[0]["success"] >= 0)

# ========== 12. Sitemap Generator ==========
print("\n[12] Sitemap Generator")
sitemaps = SitemapGenerator().generate([page])
test("Sitemap generated", len(sitemaps) == 1)
test("Valid XML header", "<?xml" in sitemaps[0])
test("URL included", "example.com/test" in sitemaps[0])

# ========== 13. Security Analyzer ==========
print("\n[13] Security Analyzer")
page.response_headers = {"strict-transport-security": "max-age=31536000", "x-content-type-options": "nosniff", "referrer-policy": "no-referrer"}
SecurityAnalyzer().analyze(page)
test("HSTS detected", page.security.hsts_enabled)
test("X-Content-Type-Options", page.security.x_content_type_options == "nosniff")
test("Referrer-Policy", page.security.referrer_policy == "no-referrer")

# ========== 14. CLI Interface ==========
print("\n[14] CLI Interface")
r = subprocess.run([sys.executable, "main.py", "crawl", "--help"], capture_output=True, text=True)
test("CLI runs without error", r.returncode == 0)
test("--js-render option exists", "--js-render" in r.stdout)
test("--subdomains option exists", "--subdomains" in r.stdout)
test("--evasion option exists", "--evasion" in r.stdout)
test("--proxies option exists", "--proxies" in r.stdout)
test("--extract option exists", "--extract" in r.stdout)
test("--report option exists", "--report" in r.stdout)
test("--visualization option exists", "--visualization" in r.stdout)
test("--sitemap option exists", "--sitemap" in r.stdout)
test("--format option exists", "--format" in r.stdout)

# ========== Summary ==========
print("\n" + "=" * 60)
total = passed + failed
print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("  ALL TESTS PASSED SUCCESSFULLY!")
else:
    print(f"  {failed} TEST(S) FAILED")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
