#!/usr/bin/env python3
"""
Web API server for Python SEO Spider.
Provides REST endpoints to control the crawler from the Web UI.
"""
import asyncio
import json
import logging
import os
import sys
import time
import traceback
import threading
import uuid
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("web_server")

from seo_spider.config.settings import CrawlConfig, CrawlMode, RenderingMode
from seo_spider.core.crawler import SEOSpiderCrawler
from seo_spider.core.models import CrawlResult
from seo_spider.renderers.js_renderer import JSRenderer
from seo_spider.analyzers.duplicate_detector import DuplicateDetector
from seo_spider.analyzers.issue_detector import IssueDetector
from seo_spider.analyzers.structured_data_analyzer import StructuredDataAnalyzer
from seo_spider.analyzers.sitemap_parser import SitemapGenerator
from seo_spider.exporters.csv_exporter import CSVExporter
from seo_spider.exporters.xlsx_exporter import XLSXExporter
from seo_spider.exporters.json_exporter import JSONExporter
from seo_spider.exporters.report_generator import ReportGenerator

# --- Global state ---
crawl_sessions: dict[str, dict] = {}


def build_config(data: dict) -> CrawlConfig:
    """Build CrawlConfig from JSON request data."""
    config = CrawlConfig()
    config.start_urls = [data.get("url", "")]
    config.max_urls = int(data.get("maxUrls", 5000))
    config.max_depth = int(data.get("maxDepth", 0))
    config.max_concurrent = int(data.get("concurrent", 10))
    config.request_timeout = int(data.get("timeout", 30))

    config.crawl_subdomains = data.get("subdomains", False)
    config.discover_subdomains = data.get("subdomains", False)
    methods = data.get("subdomainMethods", [])
    if methods:
        config.subdomain_discovery_methods = methods

    if data.get("jsRender", False):
        config.rendering_mode = RenderingMode.JAVASCRIPT
        config.js_wait_time = float(data.get("jsWait", 5.0))
        config.js_browser_instances = int(data.get("jsInstances", 3))
        blocked = data.get("blockResources", [])
        if blocked:
            config.block_resources = blocked

    config.evasion_enabled = data.get("evasion", False)
    config.use_stealth_mode = data.get("stealth", True)
    config.delay_min = float(data.get("delayMin", 0.5))
    config.delay_max = float(data.get("delayMax", 3.0))
    config.randomize_delays = data.get("evasion", False)

    config.respect_robots_txt = data.get("respectRobots", True)
    config.check_external_links = data.get("checkExternal", False)

    inc = data.get("includePatterns", "")
    if inc:
        config.include_patterns = [p.strip() for p in inc.split(",") if p.strip()]
    exc = data.get("excludePatterns", "")
    if exc:
        config.exclude_patterns = [p.strip() for p in exc.split(",") if p.strip()]

    config.generate_sitemap = data.get("generateSitemap", False)
    config.export_format = data.get("exportFormat", "csv")

    # Create domain-based output folder (e.g. crawl_output/example)
    url = data.get("url", "")
    try:
        from urllib.parse import urlparse as _urlparse
        hostname = _urlparse(url).hostname or "unknown"
        # Extract main domain name: "www.example.co.kr" -> "example"
        parts = hostname.replace("www.", "").split(".")
        domain_name = parts[0] if parts else "unknown"
    except Exception:
        domain_name = "unknown"
    config.output_dir = os.path.join(os.path.dirname(__file__), "crawl_output", domain_name)

    return config


async def run_crawl_async(session_id: str, config: CrawlConfig):
    """Run a crawl in an async context."""
    session = crawl_sessions[session_id]
    session["status"] = "running"
    session["startTime"] = datetime.now().isoformat()

    logger.info(f"[{session_id}] Crawl starting: {config.start_urls}")

    try:
        crawler = SEOSpiderCrawler(config)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[{session_id}] Failed to create crawler: {e}\n{tb}")
        session["status"] = "error"
        session["error"] = f"Crawler init failed: {e}"
        session["log"].append(tb)
        return

    js_renderer = None
    if config.rendering_mode == RenderingMode.JAVASCRIPT:
        try:
            from seo_spider.evasion.anti_bot import AntiBotEvasion
            evasion = AntiBotEvasion() if config.evasion_enabled else None
            stealth_scripts = evasion.get_playwright_stealth_scripts() if evasion else []
            js_renderer = JSRenderer(
                browser_instances=config.js_browser_instances,
                wait_time=config.js_wait_time,
                block_resources=config.block_resources,
                stealth_scripts=stealth_scripts if config.use_stealth_mode else [],
            )
            await js_renderer.initialize()
            crawler.set_js_renderer(js_renderer)
            logger.info(f"[{session_id}] JS renderer initialized ({config.js_browser_instances} instances)")
        except Exception as e:
            tb = traceback.format_exc()
            logger.warning(f"[{session_id}] JS renderer init failed: {e}\n{tb}")
            session["log"].append(f"JS renderer init failed: {e}\n{tb}")

    start = time.time()

    def on_progress(visited, queued, remaining):
        elapsed = time.time() - start
        rate = visited / elapsed if elapsed > 0 else 0
        session["progress"] = {
            "visited": visited,
            "queued": queued,
            "remaining": remaining,
            "rate": round(rate, 1),
            "elapsed": round(elapsed, 1),
        }

    crawler.on_progress(on_progress)

    try:
        logger.info(f"[{session_id}] Starting crawl...")
        result = await crawler.crawl()
        logger.info(f"[{session_id}] Crawl finished: {result.total_urls_crawled} URLs in {time.time() - start:.1f}s")

        # Post-processing
        logger.info(f"[{session_id}] Running post-processing (duplicates, issues, structured data)...")
        try:
            DuplicateDetector().detect_all(result)
        except Exception as e:
            logger.error(f"[{session_id}] DuplicateDetector error: {e}\n{traceback.format_exc()}")
            session["log"].append(f"DuplicateDetector error: {e}")

        try:
            IssueDetector().detect_crawl_issues(result)
        except Exception as e:
            logger.error(f"[{session_id}] IssueDetector error: {e}\n{traceback.format_exc()}")
            session["log"].append(f"IssueDetector error: {e}")

        try:
            sd_analyzer = StructuredDataAnalyzer()
            for page in result.pages:
                for sd in page.structured_data:
                    sd_analyzer.validate(sd)
        except Exception as e:
            logger.error(f"[{session_id}] StructuredDataAnalyzer error: {e}\n{traceback.format_exc()}")
            session["log"].append(f"StructuredDataAnalyzer error: {e}")

        # Export
        logger.info(f"[{session_id}] Exporting results (format={config.export_format})...")
        try:
            os.makedirs(config.output_dir, exist_ok=True)
            fmt = config.export_format
            if fmt in ("csv", "all"):
                CSVExporter(config.output_dir).export_all(result)
            if fmt in ("xlsx", "all"):
                XLSXExporter(config.output_dir).export(result)
            if fmt in ("json", "all"):
                JSONExporter(config.output_dir).export(result)
                JSONExporter(config.output_dir).export_summary(result)
            ReportGenerator().generate_html_report(result, os.path.join(config.output_dir, "crawl_report.html"))
            if config.generate_sitemap:
                for i, xml in enumerate(SitemapGenerator().generate(result.pages)):
                    with open(os.path.join(config.output_dir, f"sitemap-{i}.xml"), "w") as f:
                        f.write(xml)
            logger.info(f"[{session_id}] Export complete -> {config.output_dir}")
        except Exception as e:
            logger.error(f"[{session_id}] Export error: {e}\n{traceback.format_exc()}")
            session["log"].append(f"Export error: {e}")

        # Build summary for UI
        logger.info(f"[{session_id}] Building UI summary...")
        status_dist = {}
        for p in result.pages:
            sc = str(p.status_code)
            status_dist[sc] = status_dist.get(sc, 0) + 1

        # Safely extract subdomains count
        subdomains = result.subdomains_found if isinstance(result.subdomains_found, list) else []

        session["result"] = {
            "totalUrls": result.total_urls_crawled,
            "internal": result.total_internal,
            "external": result.total_external,
            "subdomains": len(subdomains) if subdomains else 0,
            "subdomainList": subdomains[:100],
            "statusDist": status_dist,
            "issues": dict(sorted(result.issues.items(), key=lambda x: -x[1])[:30]) if result.issues else {},
            "topPages": [
                {
                    "url": p.url,
                    "status": p.status_code,
                    "title": (p.title or "")[:60],
                    "inlinks": p.inlinks_count,
                    "depth": p.crawl_depth,
                }
                for p in sorted(result.pages, key=lambda x: -x.inlinks_count)[:50]
            ],
            "pages": [
                {
                    "url": p.url,
                    "status": p.status_code,
                    "title": (p.title or "")[:80],
                    "metaDesc": (p.meta_description or "")[:100],
                    "wordCount": p.word_count,
                    "h1": (p.headings.h1[0][:60] if p.headings and p.headings.h1 else ""),
                    "canonical": (p.canonical_url or "")[:80],
                    "indexable": p.is_indexable,
                    "depth": p.crawl_depth,
                    "inlinks": p.inlinks_count,
                    "responseTime": round(p.response_time, 3) if p.response_time else 0,
                }
                for p in result.pages[:500]
            ],
        }
        session["status"] = "complete"
        logger.info(f"[{session_id}] Session complete! {result.total_urls_crawled} URLs, {len(status_dist)} status codes")

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[{session_id}] CRAWL ERROR: {e}\n{tb}")
        session["status"] = "error"
        session["error"] = str(e)
        session["log"].append(tb)
    finally:
        if js_renderer:
            try:
                await js_renderer.close()
            except Exception as e:
                logger.warning(f"[{session_id}] JS renderer close error: {e}")
        session["endTime"] = datetime.now().isoformat()


def run_crawl_thread(session_id: str, config: CrawlConfig):
    """Run the async crawl in a new event loop on a thread."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_crawl_async(session_id, config))
        loop.close()
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[{session_id}] THREAD FATAL: {e}\n{tb}")
        if session_id in crawl_sessions:
            crawl_sessions[session_id]["status"] = "error"
            crawl_sessions[session_id]["error"] = str(e)
            crawl_sessions[session_id]["log"].append(tb)


class APIHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the Web UI and API."""

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.serve_file("web_ui.html", "text/html")
        elif parsed.path == "/api/status":
            qs = parse_qs(parsed.query)
            sid = qs.get("id", [""])[0]
            if sid in crawl_sessions:
                self.json_response(crawl_sessions[sid])
            else:
                self.json_response({"error": "Session not found"}, 404)
        elif parsed.path == "/api/sessions":
            summary = {
                sid: {"status": s["status"], "url": s["url"], "startTime": s.get("startTime", "")}
                for sid, s in crawl_sessions.items()
            }
            self.json_response(summary)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/crawl":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}

            url = data.get("url", "").strip()
            if not url:
                self.json_response({"error": "URL is required"}, 400)
                return

            if not url.startswith(("http://", "https://")):
                url = "https://" + url
                data["url"] = url

            config = build_config(data)
            session_id = str(uuid.uuid4())[:8]

            crawl_sessions[session_id] = {
                "id": session_id,
                "url": url,
                "status": "starting",
                "progress": {},
                "result": None,
                "error": None,
                "log": [],
                "startTime": "",
                "endTime": "",
                "config": {
                    "maxUrls": config.max_urls,
                    "jsRender": config.rendering_mode == RenderingMode.JAVASCRIPT,
                    "subdomains": config.crawl_subdomains,
                    "evasion": config.evasion_enabled,
                },
            }

            thread = threading.Thread(target=run_crawl_thread, args=(session_id, config), daemon=True)
            thread.start()

            self.json_response({"sessionId": session_id, "status": "starting"})

        elif parsed.path == "/api/stop":
            self.json_response({"message": "Stop not yet implemented"})
        else:
            self.send_error(404)

    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode("utf-8"))

    def serve_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"File not found: {filename}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Only log errors, not every request
        if args and len(args) >= 1 and isinstance(args[0], str) and args[0].startswith("4"):
            logger.warning(f"HTTP {args[0]} {self.path}")
        # Suppress normal request logging to keep console clean


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8090
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"\n  Python SEO Spider - Web UI")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
