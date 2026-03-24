"""
JSON Exporter.
Exports crawl data to JSON format for API integration and further processing.
"""
import json
import os
import logging
from dataclasses import asdict

from seo_spider.core.models import CrawlResult

logger = logging.getLogger("seo_spider.export.json")


class JSONExporter:
    """Export crawl results to JSON."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, result: CrawlResult, filename: str = "crawl_results.json"):
        """Export full crawl results to JSON."""
        path = os.path.join(self.output_dir, filename)

        data = {
            "crawl_info": {
                "start_url": result.start_url,
                "domain": result.domain,
                "start_time": result.crawl_start_time,
                "end_time": result.crawl_end_time,
                "total_urls": result.total_urls_crawled,
                "total_internal": result.total_internal,
                "total_external": result.total_external,
                "subdomains": result.subdomains_found,
            },
            "issues_summary": result.issues,
            "pages": [self._serialize_page(p) for p in result.pages],
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)

        logger.info(f"JSON export complete -> {path}")

    def _serialize_page(self, page) -> dict:
        """Serialize a PageData object to dict."""
        try:
            return asdict(page)
        except Exception:
            # Fallback for non-serializable fields
            return {
                "url": page.url,
                "status_code": page.status_code,
                "title": page.title,
                "meta_description": page.meta_description,
                "word_count": page.word_count,
                "crawl_depth": page.crawl_depth,
                "is_indexable": page.is_indexable,
            }

    def export_summary(self, result: CrawlResult, filename: str = "crawl_summary.json"):
        """Export a lightweight summary without full page data."""
        path = os.path.join(self.output_dir, filename)

        # Status code distribution
        status_dist = {}
        for page in result.pages:
            sc = str(page.status_code)
            status_dist[sc] = status_dist.get(sc, 0) + 1

        # Content type distribution
        content_dist = {}
        for page in result.pages:
            ct = page.content_type.split(';')[0].strip()
            content_dist[ct] = content_dist.get(ct, 0) + 1

        data = {
            "domain": result.domain,
            "total_urls": result.total_urls_crawled,
            "status_distribution": status_dist,
            "content_type_distribution": content_dist,
            "issues": result.issues,
            "subdomains": result.subdomains_found,
            "duplicate_groups_count": len(result.duplicate_groups),
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
