#!/usr/bin/env python3
"""
Python SEO Spider - A comprehensive SEO crawling tool.
Replicates all features of Screaming Frog SEO Spider.

Usage:
    python main.py crawl https://example.com
    python main.py crawl https://example.com --js-render --subdomains --evasion
    python main.py crawl https://example.com -o ./output --format xlsx
    python main.py crawl https://example.com --config config.yaml
"""
import asyncio
import sys
import os
import time
import json
import yaml
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seo_spider.config.settings import CrawlConfig, CrawlMode, RenderingMode
from seo_spider.core.crawler import SEOSpiderCrawler
from seo_spider.core.models import CrawlResult
from seo_spider.renderers.js_renderer import JSRenderer
from seo_spider.analyzers.duplicate_detector import DuplicateDetector
from seo_spider.analyzers.issue_detector import IssueDetector
from seo_spider.analyzers.visualization import CrawlVisualizer
from seo_spider.analyzers.structured_data_analyzer import StructuredDataAnalyzer
from seo_spider.analyzers.sitemap_parser import SitemapGenerator
from seo_spider.exporters.csv_exporter import CSVExporter
from seo_spider.exporters.xlsx_exporter import XLSXExporter
from seo_spider.exporters.json_exporter import JSONExporter
from seo_spider.exporters.report_generator import ReportGenerator
from seo_spider.utils.logging_config import setup_logger


logger = setup_logger("seo_spider", "INFO")


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python-seo-spider",
        description="Python SEO Spider - Comprehensive SEO crawling & analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic crawl
  python main.py crawl https://example.com

  # Crawl with JavaScript rendering and subdomain discovery
  python main.py crawl https://example.com --js-render --subdomains

  # Crawl with bot evasion and proxy rotation
  python main.py crawl https://example.com --evasion --proxies proxies.txt

  # Full SEO audit with all exports
  python main.py crawl https://example.com --js-render --subdomains --evasion \\
      --format xlsx --report --visualization --sitemap

  # Crawl from URL list
  python main.py list urls.txt --format csv

  # Crawl from sitemap
  python main.py sitemap https://example.com/sitemap.xml
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # === crawl command ===
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website (spider mode)")
    crawl_parser.add_argument("url", help="Start URL to crawl")

    # Crawl scope
    crawl_parser.add_argument("--max-urls", type=int, default=50000, help="Maximum URLs to crawl (default: 50000)")
    crawl_parser.add_argument("--max-depth", type=int, default=0, help="Maximum crawl depth (0=unlimited)")
    crawl_parser.add_argument("--concurrent", type=int, default=10, help="Max concurrent requests (default: 10)")
    crawl_parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)")
    crawl_parser.add_argument("--delay", type=float, default=0.0, help="Delay between requests in seconds")

    # Subdomain options
    crawl_parser.add_argument("--subdomains", action="store_true", help="Discover and crawl subdomains")
    crawl_parser.add_argument("--subdomain-methods", nargs="+",
                              default=["dns", "crt_sh", "links"],
                              help="Subdomain discovery methods: dns, crt_sh, links, dns_transfer")

    # JavaScript rendering
    crawl_parser.add_argument("--js-render", action="store_true", help="Enable JavaScript rendering (headless Chromium)")
    crawl_parser.add_argument("--js-wait", type=float, default=5.0, help="JS rendering wait time (default: 5s)")
    crawl_parser.add_argument("--js-instances", type=int, default=3, help="Browser instances for JS rendering")
    crawl_parser.add_argument("--block-resources", nargs="*", default=[],
                              help="Block resource types during JS render: image, font, media, stylesheet")

    # Bot evasion
    crawl_parser.add_argument("--evasion", action="store_true", help="Enable bot detection evasion")
    crawl_parser.add_argument("--no-stealth", action="store_true", help="Disable stealth mode in JS renderer")
    crawl_parser.add_argument("--proxies", type=str, help="Path to proxy list file (one per line)")
    crawl_parser.add_argument("--delay-min", type=float, default=0.5, help="Min random delay (default: 0.5s)")
    crawl_parser.add_argument("--delay-max", type=float, default=3.0, help="Max random delay (default: 3.0s)")

    # Scope filters
    crawl_parser.add_argument("--include", nargs="*", default=[], help="Regex patterns to include")
    crawl_parser.add_argument("--exclude", nargs="*", default=[], help="Regex patterns to exclude")
    crawl_parser.add_argument("--no-robots", action="store_true", help="Ignore robots.txt")
    crawl_parser.add_argument("--check-external", action="store_true", help="Check external link status codes")

    # Custom extraction
    crawl_parser.add_argument("--extract", nargs="*", default=[],
                              help="Custom extractions: name:type:pattern (e.g. price:css:.price)")
    crawl_parser.add_argument("--search", nargs="*", default=[],
                              help="Custom searches: name:type:pattern (e.g. phone:regex:\\d{3}-\\d{4})")

    # Output
    crawl_parser.add_argument("-o", "--output", type=str, default="./crawl_output", help="Output directory")
    crawl_parser.add_argument("--format", choices=["csv", "xlsx", "json", "all"], default="csv",
                              help="Export format (default: csv)")
    crawl_parser.add_argument("--report", action="store_true", help="Generate HTML report")
    crawl_parser.add_argument("--visualization", action="store_true", help="Generate site visualization")
    crawl_parser.add_argument("--sitemap", action="store_true", help="Generate XML sitemap")

    # Config file
    crawl_parser.add_argument("--config", type=str, help="Path to YAML config file")

    # === list command ===
    list_parser = subparsers.add_parser("list", help="Crawl URLs from a file")
    list_parser.add_argument("file", help="Path to URL list file (one URL per line)")
    list_parser.add_argument("-o", "--output", type=str, default="./crawl_output")
    list_parser.add_argument("--format", choices=["csv", "xlsx", "json", "all"], default="csv")
    list_parser.add_argument("--js-render", action="store_true")
    list_parser.add_argument("--evasion", action="store_true")

    # === sitemap command ===
    sitemap_parser = subparsers.add_parser("sitemap", help="Crawl URLs from a sitemap")
    sitemap_parser.add_argument("url", help="Sitemap URL")
    sitemap_parser.add_argument("-o", "--output", type=str, default="./crawl_output")
    sitemap_parser.add_argument("--format", choices=["csv", "xlsx", "json", "all"], default="csv")

    return parser


def parse_custom_extractions(extract_args: list) -> list[dict]:
    """Parse custom extraction arguments: name:type:pattern"""
    extractions = []
    for arg in extract_args:
        parts = arg.split(':', 2)
        if len(parts) == 3:
            extractions.append({
                "name": parts[0],
                "type": parts[1],
                "value": parts[2],
            })
    return extractions


def parse_custom_searches(search_args: list) -> list[dict]:
    """Parse custom search arguments: name:type:pattern"""
    searches = []
    for arg in search_args:
        parts = arg.split(':', 2)
        if len(parts) == 3:
            searches.append({
                "name": parts[0],
                "type": parts[1],
                "value": parts[2],
            })
    return searches


def load_proxies(proxy_file: str) -> list[str]:
    """Load proxy list from file."""
    proxies = []
    with open(proxy_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies


def build_config_from_args(args) -> CrawlConfig:
    """Build CrawlConfig from CLI arguments."""
    config = CrawlConfig()

    if args.command == "crawl":
        config.start_urls = [args.url]
        config.crawl_mode = CrawlMode.SPIDER
    elif args.command == "list":
        with open(args.file, 'r') as f:
            config.start_urls = [line.strip() for line in f if line.strip()]
        config.crawl_mode = CrawlMode.LIST
    elif args.command == "sitemap":
        config.start_urls = [args.url]
        config.crawl_mode = CrawlMode.SITEMAP

    # Apply common settings — create domain-based subfolder
    try:
        from urllib.parse import urlparse as _urlparse
        hostname = _urlparse(args.url).hostname or "unknown"
        parts = hostname.replace("www.", "").split(".")
        domain_name = parts[0] if parts else "unknown"
    except Exception:
        domain_name = "unknown"
    config.output_dir = os.path.join(args.output, domain_name)
    config.export_format = args.format

    if args.command == "crawl":
        config.max_urls = args.max_urls
        config.max_depth = args.max_depth
        config.max_concurrent = args.concurrent
        config.request_timeout = args.timeout
        config.delay_between_requests = args.delay

        # Subdomains
        config.crawl_subdomains = args.subdomains
        config.discover_subdomains = args.subdomains
        config.subdomain_discovery_methods = args.subdomain_methods

        # JS Rendering
        if args.js_render:
            config.rendering_mode = RenderingMode.JAVASCRIPT
            config.js_wait_time = args.js_wait
            config.js_browser_instances = args.js_instances
            config.block_resources = args.block_resources or []

        # Bot Evasion
        config.evasion_enabled = args.evasion
        config.use_stealth_mode = not args.no_stealth
        config.delay_min = args.delay_min
        config.delay_max = args.delay_max

        if args.proxies:
            config.proxy_list = load_proxies(args.proxies)
            config.rotate_proxies = True

        # Scope
        config.include_patterns = args.include or []
        config.exclude_patterns = args.exclude or []
        config.respect_robots_txt = not args.no_robots
        config.check_external_links = args.check_external

        # Custom extraction
        config.custom_extractions = parse_custom_extractions(args.extract or [])
        config.custom_searches = parse_custom_searches(args.search or [])

        # Sitemap generation
        config.generate_sitemap = getattr(args, 'sitemap', False)

    return config


def load_yaml_config(config_path: str) -> CrawlConfig:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    config = CrawlConfig()
    for key, value in data.items():
        if hasattr(config, key):
            if key == 'crawl_mode':
                value = CrawlMode(value)
            elif key == 'rendering_mode':
                value = RenderingMode(value)
            setattr(config, key, value)

    return config


async def run_crawl(config: CrawlConfig, args) -> CrawlResult:
    """Execute the crawl with the given configuration."""
    print(f"\n{'='*60}")
    print(f"  Python SEO Spider - Starting Crawl")
    print(f"{'='*60}")
    print(f"  Target: {config.start_urls[0] if config.start_urls else 'N/A'}")
    print(f"  Mode: {config.crawl_mode.value}")
    print(f"  JS Rendering: {'ON' if config.rendering_mode == RenderingMode.JAVASCRIPT else 'OFF'}")
    print(f"  Subdomains: {'ON' if config.crawl_subdomains else 'OFF'}")
    print(f"  Bot Evasion: {'ON' if config.evasion_enabled else 'OFF'}")
    print(f"  Max URLs: {config.max_urls}")
    print(f"  Concurrent: {config.max_concurrent}")
    print(f"{'='*60}\n")

    crawler = SEOSpiderCrawler(config)

    # Set up JS renderer if needed
    js_renderer = None
    if config.rendering_mode == RenderingMode.JAVASCRIPT:
        from evasion.anti_bot import AntiBotEvasion
        evasion = AntiBotEvasion() if config.evasion_enabled else None
        stealth_scripts = evasion.get_playwright_stealth_scripts() if evasion else []

        js_renderer = JSRenderer(
            browser_instances=config.js_browser_instances,
            wait_time=config.js_wait_time,
            ajax_timeout=config.ajax_timeout,
            viewport_width=config.viewport_width,
            viewport_height=config.viewport_height,
            block_resources=config.block_resources,
            stealth_scripts=stealth_scripts if config.use_stealth_mode else [],
        )
        await js_renderer.initialize()
        crawler.set_js_renderer(js_renderer)

    # Progress callback
    start_time = time.time()
    def on_progress(visited, queued, remaining):
        elapsed = time.time() - start_time
        rate = visited / elapsed if elapsed > 0 else 0
        print(f"\r  Crawled: {visited} | Queue: {remaining} | "
              f"Rate: {rate:.1f} URLs/s | Elapsed: {elapsed:.0f}s", end="", flush=True)

    crawler.on_progress(on_progress)

    # Execute crawl
    result = await crawler.crawl()

    if js_renderer:
        await js_renderer.close()

    print(f"\n\n  Crawl complete: {result.total_urls_crawled} URLs crawled")

    return result


def post_process(result: CrawlResult, config: CrawlConfig, args):
    """Run post-crawl analysis and export."""
    output_dir = config.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n  Post-processing...")

    # Duplicate detection
    print("  - Detecting duplicates...")
    dup_detector = DuplicateDetector()
    dup_report = dup_detector.detect_all(result)

    # Issue detection
    print("  - Detecting SEO issues...")
    issue_detector = IssueDetector()
    issue_detector.detect_crawl_issues(result)

    # Structured data validation
    print("  - Validating structured data...")
    sd_analyzer = StructuredDataAnalyzer()
    for page in result.pages:
        for sd in page.structured_data:
            sd_analyzer.validate(sd)

    # Export
    fmt = config.export_format
    print(f"  - Exporting ({fmt})...")

    if fmt in ("csv", "all"):
        exporter = CSVExporter(output_dir)
        exporter.export_all(result)

    if fmt in ("xlsx", "all"):
        exporter = XLSXExporter(output_dir)
        exporter.export(result)

    if fmt in ("json", "all"):
        exporter = JSONExporter(output_dir)
        exporter.export(result)
        exporter.export_summary(result)

    # HTML Report
    if getattr(args, 'report', False) or fmt == "all":
        print("  - Generating HTML report...")
        report_gen = ReportGenerator()
        report_gen.generate_html_report(
            result,
            os.path.join(output_dir, "crawl_report.html"),
        )

    # Visualization
    if getattr(args, 'visualization', False):
        print("  - Generating visualization...")
        viz = CrawlVisualizer()
        viz.export_html_visualization(
            result,
            os.path.join(output_dir, "site_visualization.html"),
        )

    # Sitemap
    if config.generate_sitemap:
        print("  - Generating XML sitemap...")
        generator = SitemapGenerator()
        sitemaps = generator.generate(result.pages)
        for i, xml in enumerate(sitemaps):
            filename = f"sitemap-{i}.xml" if i > 0 else "sitemap.xml"
            path = os.path.join(output_dir, filename)
            with open(path, 'w') as f:
                f.write(xml)

    print(f"\n  All outputs saved to: {output_dir}")
    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  Total URLs:      {result.total_urls_crawled}")
    print(f"  Internal:        {result.total_internal}")
    print(f"  External:        {result.total_external}")
    print(f"  Subdomains:      {len(result.subdomains_found)}")
    print(f"  Issues Found:    {sum(result.issues.values())}")

    if result.issues:
        print(f"\n  Top Issues:")
        for issue, count in sorted(result.issues.items(), key=lambda x: -x[1])[:10]:
            print(f"    {count:>5} | {issue}")

    print(f"{'='*60}\n")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load config from YAML if provided
    if hasattr(args, 'config') and args.config:
        config = load_yaml_config(args.config)
        # Override with CLI args
        if hasattr(args, 'url'):
            config.start_urls = [args.url]
        config.output_dir = args.output
    else:
        config = build_config_from_args(args)

    # Run crawl
    result = asyncio.run(run_crawl(config, args))

    # Post-process and export
    post_process(result, config, args)


if __name__ == "__main__":
    main()
