#!/usr/bin/env python3
"""
Integration test: simulates a realistic crawl result and verifies all outputs.
Runs without network access by constructing PageData objects directly.
"""
import sys, os, json, csv, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seo_spider.core.models import (
    PageData, CrawlResult, LinkData, ImageData, HeadingData,
    ResourceData, StructuredDataItem, HreflangData, SecurityData, PageSpeedData,
)
from seo_spider.config.settings import CrawlConfig
from seo_spider.analyzers.duplicate_detector import DuplicateDetector
from seo_spider.analyzers.issue_detector import IssueDetector
from seo_spider.analyzers.structured_data_analyzer import StructuredDataAnalyzer
from seo_spider.exporters.csv_exporter import CSVExporter
from seo_spider.utils.hash_utils import content_hash, simhash_text
from datetime import datetime

OUTPUT_DIR = "/tmp/crawl_output_test"

def build_test_result() -> CrawlResult:
    """Build a realistic CrawlResult with diverse page types for testing."""
    result = CrawlResult(
        start_url="https://www.example.com/",
        domain="example.com",
        crawl_start_time=datetime.now().isoformat(),
        total_urls_crawled=0,
        total_internal=0,
        total_external=0,
    )

    pages = []

    # === Page 1: Home (200, canonical self, structured data, images, links) ===
    p1 = PageData(
        url="https://www.example.com/",
        final_url="https://www.example.com/",
        status_code=200, status_text="200 OK",
        content_type="text/html; charset=utf-8",
        response_time=0.342, crawl_depth=0,
        crawl_timestamp=datetime.now().isoformat(),
        page_type="HTML", original_status_code=200,
        title="Example Domain - Home Page",
        title_length=29, title_pixel_width=189,
        meta_description="Welcome to Example.com, your trusted source for examples and demos.",
        meta_description_length=67, meta_description_pixel_width=369,
        meta_keywords="example, demo, test", meta_keywords_length=19,
        meta_robots="", x_robots_tag="",
        canonical_url="https://www.example.com/", canonical_is_self=True, canonical_status="Self-Referencing",
        headings=HeadingData(h1=["Welcome to Example.com"], h2=["About Us", "Services"]),
        word_count=450, sentence_count=25, avg_words_per_sentence=18.0,
        flesch_reading_ease=65.2, readability="Fairly Easy", text_ratio=22.5,
        html_lang="en", content_language="en",
        og_title="Example Domain", og_description="Welcome to Example", og_image="https://www.example.com/og.jpg", og_type="website", og_url="https://www.example.com/",
        twitter_card="summary_large_image", twitter_title="Example Domain",
        twitter_description="Welcome to Example", twitter_image="https://www.example.com/tw.jpg",
        folder_depth=0, url_length=26, url_encoded_address="https://www.example.com/",
        is_indexable=True, indexability_status="Indexable",
        security=SecurityData(is_https=True, hsts_enabled=True, x_content_type_options="nosniff",
                              referrer_policy="strict-origin-when-cross-origin"),
        page_speed=PageSpeedData(html_size=15000, response_time=0.342, ttfb=0.15),
        response_headers={"content-type": "text/html", "strict-transport-security": "max-age=31536000"},
    )
    p1.body_text = "Welcome to Example.com " * 20
    p1.content_hash = content_hash(p1.body_text)
    p1.simhash = simhash_text(p1.body_text)

    # Add images
    p1.images = [
        ImageData(src="https://www.example.com/logo.png", alt_text="Example Logo", source_page=p1.url),
        ImageData(src="https://www.example.com/hero.jpg", alt_text="", is_missing_alt=True, source_page=p1.url),
        ImageData(src="https://www.example.com/banner.jpg", is_missing_alt_attribute=True, source_page=p1.url),
        ImageData(src="https://www.example.com/photo.jpg", alt_text="A" * 120, alt_over_100=True, source_page=p1.url),
    ]
    p1.images_count = 4
    p1.images_missing_alt = 1
    p1.images_missing_alt_attribute = 1
    p1.images_with_alt_over_100 = 1

    # Add internal links
    p1.internal_links = [
        LinkData(source_url=p1.url, target_url="https://www.example.com/about", anchor_text="About Us", link_type="hyperlink", is_internal=True, is_follow=True, link_position="navigation"),
        LinkData(source_url=p1.url, target_url="https://www.example.com/services", anchor_text="Services", link_type="hyperlink", is_internal=True, is_follow=True, link_position="navigation"),
        LinkData(source_url=p1.url, target_url="https://www.example.com/blog", anchor_text="Blog", link_type="hyperlink", is_internal=True, is_follow=True, link_position="content"),
        LinkData(source_url=p1.url, target_url="https://www.example.com/contact", anchor_text="Contact", link_type="hyperlink", is_internal=True, is_follow=True, link_position="footer"),
    ]
    p1.external_links = [
        LinkData(source_url=p1.url, target_url="https://twitter.com/example", anchor_text="Twitter", link_type="hyperlink", is_internal=False, is_follow=False, rel_attributes=["nofollow", "noopener"], link_position="footer"),
    ]

    # Structured data
    p1.structured_data = [
        StructuredDataItem(format_type="json-ld", schema_type="WebSite",
            raw_data={"@context": "https://schema.org", "@type": "WebSite", "name": "Example", "url": "https://www.example.com/"}),
        StructuredDataItem(format_type="json-ld", schema_type="Organization",
            raw_data={"@context": "https://schema.org", "@type": "Organization", "name": "Example Corp"}),
    ]

    # Hreflang
    p1.hreflang_annotations = [
        HreflangData(source_url=p1.url, language="en", region="", target_url="https://www.example.com/", is_valid=True),
        HreflangData(source_url=p1.url, language="ko", region="KR", target_url="https://www.example.com/ko/", is_valid=True),
    ]

    # CSS/JS resources
    p1.css_resources = [ResourceData(url="https://www.example.com/style.css", resource_type="css")]
    p1.js_resources = [ResourceData(url="https://www.example.com/app.js", resource_type="javascript")]

    pages.append(p1)

    # === Page 2: About (200, duplicate title with page 5) ===
    p2 = PageData(
        url="https://www.example.com/about",
        final_url="https://www.example.com/about",
        status_code=200, status_text="200 OK",
        content_type="text/html; charset=utf-8",
        response_time=0.523, crawl_depth=1, page_type="HTML", original_status_code=200,
        crawl_timestamp=datetime.now().isoformat(),
        title="About Us - Example Domain",
        title_length=25, title_pixel_width=163,
        meta_description="Learn about Example.com and our mission to provide quality examples.",
        meta_description_length=67, meta_description_pixel_width=369,
        canonical_url="https://www.example.com/about", canonical_is_self=True, canonical_status="Self-Referencing",
        headings=HeadingData(h1=["About Us"], h2=["Our Mission", "Our Team"]),
        word_count=320, sentence_count=18, avg_words_per_sentence=17.8,
        flesch_reading_ease=58.0, readability="Standard", text_ratio=18.3,
        html_lang="en", is_indexable=True, indexability_status="Indexable",
        security=SecurityData(is_https=True, hsts_enabled=True),
        page_speed=PageSpeedData(html_size=12000, response_time=0.523),
        folder_depth=1, url_length=33,
    )
    p2.body_text = "About us content " * 15
    p2.content_hash = content_hash(p2.body_text)
    p2.simhash = simhash_text(p2.body_text)
    p2.images = [ImageData(src="https://www.example.com/team.jpg", alt_text="Our Team", source_page=p2.url)]
    p2.images_count = 1
    p2.internal_links = [
        LinkData(source_url=p2.url, target_url="https://www.example.com/", anchor_text="Home", link_type="hyperlink", is_internal=True, is_follow=True),
    ]
    pages.append(p2)

    # === Page 3: Redirect (301 -> /about) ===
    p3 = PageData(
        url="https://www.example.com/about-us",
        final_url="https://www.example.com/about",
        status_code=200, status_text="301 Moved Permanently",
        content_type="text/html; charset=utf-8",
        response_time=0.8, crawl_depth=1, page_type="Redirect",
        original_status_code=301,
        crawl_timestamp=datetime.now().isoformat(),
        is_redirect=True, redirect_type="301",
        redirect_chain=["https://www.example.com/about-us"],
        redirect_chain_length=1, redirect_status="",
        is_indexable=False, indexability_status="Redirect (301)",
        security=SecurityData(is_https=True),
    )
    pages.append(p3)

    # === Page 4: 404 Page ===
    p4 = PageData(
        url="https://www.example.com/old-page",
        final_url="https://www.example.com/old-page",
        status_code=404, status_text="404 Not Found",
        content_type="text/html; charset=utf-8",
        response_time=0.15, crawl_depth=2, page_type="HTML",
        original_status_code=404,
        crawl_timestamp=datetime.now().isoformat(),
        is_indexable=False, indexability_status="Non-200 Status Code (404)",
        security=SecurityData(is_https=True),
    )
    pages.append(p4)

    # === Page 5: Services (200, duplicate title with about) ===
    p5 = PageData(
        url="https://www.example.com/services",
        final_url="https://www.example.com/services",
        status_code=200, status_text="200 OK",
        content_type="text/html; charset=utf-8",
        response_time=0.41, crawl_depth=1, page_type="HTML", original_status_code=200,
        crawl_timestamp=datetime.now().isoformat(),
        title="About Us - Example Domain",  # DUPLICATE title with p2
        title_length=25, title_pixel_width=163,
        meta_description="Our services include web development, SEO auditing, and more.",
        meta_description_length=62, meta_description_pixel_width=341,
        canonical_url="https://www.example.com/services", canonical_is_self=True, canonical_status="Self-Referencing",
        headings=HeadingData(h1=["Our Services"], h2=["Web Development", "SEO Auditing"]),
        word_count=280, sentence_count=15, avg_words_per_sentence=18.7,
        flesch_reading_ease=52.0, readability="Standard", text_ratio=16.0,
        html_lang="en", is_indexable=True, indexability_status="Indexable",
        security=SecurityData(is_https=True, hsts_enabled=True, x_content_type_options="nosniff"),
        page_speed=PageSpeedData(html_size=10000, response_time=0.41),
        folder_depth=1, url_length=36,
    )
    p5.body_text = "Services content here " * 12
    p5.content_hash = content_hash(p5.body_text)
    p5.simhash = simhash_text(p5.body_text)
    p5.images = [
        ImageData(src="https://www.example.com/seo.png", alt_text="SEO Service", source_page=p5.url),
        ImageData(src="https://www.example.com/dev.png", alt_text="", is_missing_alt=True, source_page=p5.url),
    ]
    p5.images_count = 2
    p5.images_missing_alt = 1
    p5.internal_links = [
        LinkData(source_url=p5.url, target_url="https://www.example.com/", anchor_text="Home", link_type="hyperlink", is_internal=True),
        LinkData(source_url=p5.url, target_url="https://www.example.com/contact", anchor_text="Contact", link_type="hyperlink", is_internal=True),
    ]
    pages.append(p5)

    # === Page 6: Blog (200, missing H1, missing canonical, thin content) ===
    p6 = PageData(
        url="https://www.example.com/blog",
        final_url="https://www.example.com/blog",
        status_code=200, status_text="200 OK",
        content_type="text/html; charset=utf-8",
        response_time=1.2, crawl_depth=1, page_type="HTML", original_status_code=200,
        crawl_timestamp=datetime.now().isoformat(),
        title="Blog",
        title_length=4, title_pixel_width=26,
        meta_description="",  # Missing
        canonical_url="", canonical_status="Missing",
        headings=HeadingData(h1=[], h2=["Latest Posts"]),  # Missing H1
        word_count=85, sentence_count=5, text_ratio=8.0,
        html_lang="en", is_indexable=True, indexability_status="Indexable",
        security=SecurityData(is_https=True),
        page_speed=PageSpeedData(html_size=5000, response_time=1.2),
        folder_depth=1, url_length=32,
    )
    p6.body_text = "Blog posts list " * 5
    p6.content_hash = content_hash(p6.body_text)
    p6.simhash = simhash_text(p6.body_text)
    pages.append(p6)

    # === Page 7: Contact (200, non-self canonical, multiple H1, noindex) ===
    p7 = PageData(
        url="https://www.example.com/contact",
        final_url="https://www.example.com/contact",
        status_code=200, status_text="200 OK",
        content_type="text/html; charset=utf-8",
        response_time=0.35, crawl_depth=1, page_type="HTML", original_status_code=200,
        crawl_timestamp=datetime.now().isoformat(),
        title="Contact Us - Example Domain",
        title_length=27, title_pixel_width=176,
        meta_description="Get in touch with Example.com for support.",
        meta_description_length=43, meta_description_pixel_width=237,
        meta_robots="noindex, nofollow",
        canonical_url="https://www.example.com/about", canonical_is_self=False, canonical_mismatch=True, canonical_status="Canonicalised",
        headings=HeadingData(h1=["Contact Us", "Get In Touch"], h2=["Email", "Phone"]),  # Multiple H1
        word_count=150, sentence_count=8, text_ratio=14.0,
        html_lang="en", is_indexable=False, indexability_status="Noindex in Meta Robots; Canonicalised to different URL",
        security=SecurityData(is_https=True),
        page_speed=PageSpeedData(html_size=8000, response_time=0.35),
        folder_depth=1, url_length=35,
    )
    p7.body_text = "Contact us form " * 8
    p7.content_hash = content_hash(p7.body_text)
    p7.simhash = simhash_text(p7.body_text)

    # Structured data with errors
    p7.structured_data = [
        StructuredDataItem(format_type="json-ld", schema_type="LocalBusiness",
            raw_data={"@context": "https://schema.org", "@type": "LocalBusiness"},
            validation_errors=["Missing required property: name", "Missing required property: address"],
            is_valid=False),
    ]
    pages.append(p7)

    # === Page 8: Redirect chain (302 -> 301 -> final) ===
    p8 = PageData(
        url="https://www.example.com/old-services",
        final_url="https://www.example.com/services",
        status_code=200, status_text="302 Found",
        content_type="text/html",
        response_time=1.5, crawl_depth=2, page_type="Redirect",
        original_status_code=302,
        crawl_timestamp=datetime.now().isoformat(),
        is_redirect=True, redirect_type="302",
        redirect_chain=["https://www.example.com/old-services", "https://www.example.com/services-new"],
        redirect_chain_length=2, redirect_status="Redirect Chain",
        is_indexable=False, indexability_status="Redirect (302)",
        security=SecurityData(is_https=True),
    )
    pages.append(p8)

    # === Set page list ===
    result.pages = pages

    # === Build inlink map ===
    for page in result.pages:
        for link in page.internal_links:
            target = link.target_url
            if target not in result.inlink_map:
                result.inlink_map[target] = []
            result.inlink_map[target].append(page.url)

    total_inlinks = sum(len(v) for v in result.inlink_map.values()) or 1
    for page in result.pages:
        sources = result.inlink_map.get(page.url, [])
        page.inlinks_count = len(sources)
        page.unique_inlinks = len(set(sources))
        page.pct_of_total = round(page.inlinks_count / total_inlinks * 100, 2)
        page.outlinks_count = len(page.internal_links) + len(page.external_links)
        page.unique_outlinks = len(set(l.target_url for l in page.internal_links))
        page.external_outlinks = len(page.external_links)
        page.unique_external_outlinks = len(set(l.target_url for l in page.external_links))

    # Finalize
    result.total_urls_crawled = len(pages)
    result.total_internal = len([p for p in pages if p.status_code == 200])
    result.total_external = 1
    result.crawl_end_time = datetime.now().isoformat()
    result.crawl_warnings = [
        "Robots.txt returned 403",
        "Page https://www.example.com/old-page returned 404",
    ]

    return result


def run_post_process(result: CrawlResult):
    """Run the same post-processing as main.py."""
    from collections import defaultdict

    # Populate status fields
    pages_by_url = {p.url: p for p in result.pages}
    html_pages = [p for p in result.pages if p.status_code == 200 and 'text/html' in p.content_type]

    # Title status & duplicates
    title_map = defaultdict(list)
    for p in html_pages:
        if p.title:
            title_map[p.title.strip().lower()].append(p)
    for p in html_pages:
        if not p.title:
            p.title_status = "Missing"
        elif len(title_map.get(p.title.strip().lower(), [])) > 1:
            p.title_status = "Duplicate"
        elif p.title_length > 60:
            p.title_status = "Over 60 Characters"
        elif p.title_length < 30:
            p.title_status = "Below 30 Characters"
        else:
            p.title_status = "OK"

    # Meta desc status
    desc_map = defaultdict(list)
    for p in html_pages:
        if p.meta_description:
            desc_map[p.meta_description.strip().lower()].append(p)
    for p in html_pages:
        if not p.meta_description:
            p.meta_desc_status = "Missing"
        elif len(desc_map.get(p.meta_description.strip().lower(), [])) > 1:
            p.meta_desc_status = "Duplicate"
        elif p.meta_description_length > 160:
            p.meta_desc_status = "Over 160 Characters"
        elif p.meta_description_length < 70:
            p.meta_desc_status = "Below 70 Characters"
        else:
            p.meta_desc_status = "OK"

    # H1 status
    h1_map = defaultdict(list)
    for p in html_pages:
        if p.headings.h1:
            for h1 in p.headings.h1:
                h1_map[h1.strip().lower()].append(p)
    for p in html_pages:
        if p.headings.missing_h1:
            p.h1_status = "Missing"
        elif p.headings.multiple_h1:
            p.h1_status = "Multiple"
        elif p.headings.h1 and len(h1_map.get(p.headings.h1[0].strip().lower(), [])) > 1:
            p.h1_status = "Duplicate"
        else:
            p.h1_status = "OK"

    # Canonical cross-check
    for p in html_pages:
        if p.canonical_url and p.canonical_status == "Canonicalised":
            target = pages_by_url.get(p.canonical_url)
            if target:
                if target.is_redirect or (300 <= target.status_code < 400):
                    p.canonical_status = "Canonical to Redirect"
                elif target.status_code != 200:
                    p.canonical_status = "Canonical to Non-200"

    # Duplicate detection
    dup_detector = DuplicateDetector()
    dup_detector.detect_all(result)

    # Issue detection
    issue_detector = IssueDetector()
    issue_detector.detect_crawl_issues(result, pages_by_url=pages_by_url)

    # Structured data validation
    sd_analyzer = StructuredDataAnalyzer()
    for page in result.pages:
        for sd in page.structured_data:
            sd_analyzer.validate(sd)


def verify_outputs(output_dir: str):
    """Verify all expected files exist and contain data."""
    print("\n" + "="*60)
    print("  VERIFICATION RESULTS")
    print("="*60)

    expected_csvs = [
        "internal_all.csv", "url_all.csv", "response_codes_all.csv",
        "images_all.csv", "canonicals_all.csv", "directives_all.csv",
        "h1_all.csv", "h2_all.csv", "content_all.csv",
        "hreflang_all.csv", "pagination_all.csv", "structured_data_all.csv",
        "security_all.csv", "javascript_all.csv", "links_all.csv",
        "inlinks.csv", "redirects.csv", "issues.csv",
        "external_all.csv", "page_titles_duplicate.csv", "meta_description_duplicate.csv",
        "statistics_summary.csv", "crawl_warnings.csv",
    ]
    expected_jsons = [
        "statistics_summary.json", "run_manifest.json", "run_summary.json",
    ]

    all_pass = True
    csv_results = {}
    for fname in expected_csvs:
        path = os.path.join(output_dir, fname)
        exists = os.path.exists(path)
        rows = 0
        if exists:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = sum(1 for _ in reader) - 1  # Subtract header
        csv_results[fname] = (exists, rows)
        status = "OK" if exists else "MISSING"
        if not exists:
            all_pass = False
        print(f"  [{status:>7}] {fname:40s} ({rows} rows)" if exists else f"  [{status:>7}] {fname}")

    for fname in expected_jsons:
        path = os.path.join(output_dir, fname)
        exists = os.path.exists(path)
        status = "OK" if exists else "MISSING"
        if not exists:
            all_pass = False
        if exists:
            with open(path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"  [{status:>7}] {fname:40s} ({len(data)} items)")
            elif isinstance(data, dict):
                print(f"  [{status:>7}] {fname:40s} ({len(data)} keys)")
        else:
            print(f"  [{status:>7}] {fname}")

    print("\n" + "-"*60)

    # === Specific content verifications ===
    verifications = []

    # 1. internal_all.csv should have pages
    r = csv_results.get("internal_all.csv", (False, 0))
    verifications.append(("internal_all.csv has rows", r[1] > 0))

    # 2. issues.csv should have issues
    r = csv_results.get("issues.csv", (False, 0))
    verifications.append(("issues.csv has issues", r[1] > 0))

    # 3. images_all.csv should have image occurrences
    r = csv_results.get("images_all.csv", (False, 0))
    verifications.append(("images_all.csv has rows (occurrences)", r[1] > 0))

    # 4. redirects.csv should have redirects
    r = csv_results.get("redirects.csv", (False, 0))
    verifications.append(("redirects.csv has redirects", r[1] > 0))

    # 5. page_titles_duplicate.csv should have duplicates
    r = csv_results.get("page_titles_duplicate.csv", (False, 0))
    verifications.append(("page_titles_duplicate.csv has duplicates", r[1] > 0))

    # 6. statistics_summary.csv should have metrics
    r = csv_results.get("statistics_summary.csv", (False, 0))
    verifications.append(("statistics_summary.csv has metrics", r[1] >= 20))

    # 7. structured_data_all.csv should have rows
    r = csv_results.get("structured_data_all.csv", (False, 0))
    verifications.append(("structured_data_all.csv has rows", r[1] > 0))

    # 8. hreflang_all.csv should have rows
    r = csv_results.get("hreflang_all.csv", (False, 0))
    verifications.append(("hreflang_all.csv has rows", r[1] > 0))

    # 9. canonicals_all.csv should have canonical status column
    path = os.path.join(output_dir, "canonicals_all.csv")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            verifications.append(("canonicals_all.csv has 'Canonical Status' column", "Canonical Status" in headers))

    # 10. issues.csv should have 'Evidence' column
    path = os.path.join(output_dir, "issues.csv")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            verifications.append(("issues.csv has 'Evidence' column", "Evidence" in headers))

    # 11. statistics_summary.json should have proper format
    path = os.path.join(output_dir, "statistics_summary.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            first = data[0]
            has_keys = all(k in first for k in ["metric_name", "metric_value", "counting_unit"])
            verifications.append(("statistics_summary.json has correct format", has_keys))

    # 12. run_manifest.json should have required keys
    path = os.path.join(output_dir, "run_manifest.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        has_keys = all(k in data for k in ["start_url", "domain", "output_files"])
        verifications.append(("run_manifest.json has required keys", has_keys))

    # 13. Verify image counts in statistics
    path = os.path.join(output_dir, "statistics_summary.csv")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            stats = {row["metric_name"]: row["metric_value"] for row in reader}
        total_images = int(stats.get("Total Images", 0))
        verifications.append(("Total Images count is 7 (occurrences)", total_images == 7))
        missing_alt_attr = int(stats.get("Images Missing Alt Attribute", 0))
        verifications.append(("Missing Alt Attribute count is 1", missing_alt_attr == 1))

    print("\n  Content Verifications:")
    for desc, passed in verifications:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"    [{status:>4}] {desc}")

    print("\n" + "="*60)
    if all_pass:
        print("  ALL VERIFICATIONS PASSED")
    else:
        print("  SOME VERIFICATIONS FAILED")
    print("="*60 + "\n")
    return all_pass


def main():
    # Clean output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    print("Building test crawl result...")
    result = build_test_result()

    print("Running post-processing...")
    run_post_process(result)

    print(f"Exporting to {OUTPUT_DIR}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    exporter = CSVExporter(OUTPUT_DIR)
    files = exporter.export_all(result)
    print(f"Generated {len(files)} files")

    # Verify
    passed = verify_outputs(OUTPUT_DIR)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
