"""
Report Generator.
Generates comprehensive HTML reports with crawl statistics and issue summaries.
"""
import os
import logging
from datetime import datetime
from collections import Counter

from seo_spider.core.models import CrawlResult

logger = logging.getLogger("seo_spider.report")


class ReportGenerator:
    """Generate HTML crawl reports."""

    def generate_html_report(self, result: CrawlResult, output_path: str):
        """Generate a comprehensive HTML report."""

        # Compute statistics
        status_dist = Counter(p.status_code for p in result.pages)
        indexable = sum(1 for p in result.pages if p.is_indexable)
        non_indexable = sum(1 for p in result.pages if not p.is_indexable)
        avg_word_count = (
            sum(p.word_count for p in result.pages) / len(result.pages)
            if result.pages else 0
        )
        avg_response_time = (
            sum(p.response_time for p in result.pages) / len(result.pages)
            if result.pages else 0
        )

        # Sort issues by count
        sorted_issues = sorted(result.issues.items(), key=lambda x: -x[1])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SEO Crawl Report - {result.domain}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a73e8; margin-bottom: 10px; }}
        h2 {{ color: #333; margin: 30px 0 15px; border-bottom: 2px solid #1a73e8; padding-bottom: 5px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card .number {{ font-size: 2em; font-weight: bold; color: #1a73e8; }}
        .card .label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0; }}
        th {{ background: #1a73e8; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
        .badge-error {{ background: #fce4ec; color: #c62828; }}
        .badge-warning {{ background: #fff3e0; color: #e65100; }}
        .badge-info {{ background: #e3f2fd; color: #1565c0; }}
        .badge-success {{ background: #e8f5e9; color: #2e7d32; }}
        .status-200 {{ color: #2e7d32; }} .status-301 {{ color: #e65100; }}
        .status-404 {{ color: #c62828; }} .status-500 {{ color: #6a1b9a; }}
        .bar {{ height: 20px; border-radius: 3px; margin: 2px 0; }}
        .bar-container {{ background: #eee; border-radius: 3px; overflow: hidden; }}
        footer {{ text-align: center; padding: 30px; color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
<div class="container">
    <h1>SEO Crawl Report</h1>
    <p><strong>Domain:</strong> {result.domain} | <strong>Crawled:</strong> {result.crawl_start_time[:19]} | <strong>Total URLs:</strong> {result.total_urls_crawled}</p>

    <h2>Overview</h2>
    <div class="grid">
        <div class="card"><div class="number">{result.total_urls_crawled}</div><div class="label">Total URLs</div></div>
        <div class="card"><div class="number">{status_dist.get(200, 0)}</div><div class="label">200 OK</div></div>
        <div class="card"><div class="number">{sum(v for k, v in status_dist.items() if 300 <= k < 400)}</div><div class="label">Redirects</div></div>
        <div class="card"><div class="number">{sum(v for k, v in status_dist.items() if 400 <= k < 500)}</div><div class="label">Client Errors</div></div>
        <div class="card"><div class="number">{sum(v for k, v in status_dist.items() if k >= 500)}</div><div class="label">Server Errors</div></div>
        <div class="card"><div class="number">{indexable}</div><div class="label">Indexable</div></div>
        <div class="card"><div class="number">{non_indexable}</div><div class="label">Non-Indexable</div></div>
        <div class="card"><div class="number">{len(result.subdomains_found)}</div><div class="label">Subdomains</div></div>
        <div class="card"><div class="number">{avg_word_count:.0f}</div><div class="label">Avg Word Count</div></div>
        <div class="card"><div class="number">{avg_response_time:.2f}s</div><div class="label">Avg Response Time</div></div>
    </div>

    <h2>Issues ({sum(result.issues.values())} total)</h2>
    <table>
        <tr><th>Issue</th><th>Count</th><th>Severity</th></tr>
        {''.join(f'<tr><td>{issue}</td><td>{count}</td><td>{self._get_severity_badge(issue)}</td></tr>' for issue, count in sorted_issues[:50])}
    </table>

    <h2>Status Code Distribution</h2>
    <table>
        <tr><th>Status Code</th><th>Count</th><th>Percentage</th></tr>
        {''.join(f'<tr><td class="status-{sc}">{sc}</td><td>{count}</td><td>{count/len(result.pages)*100:.1f}%</td></tr>' for sc, count in sorted(status_dist.items()))}
    </table>

    <h2>Subdomains Discovered</h2>
    <table>
        <tr><th>Subdomain</th></tr>
        {''.join(f'<tr><td>{s}</td></tr>' for s in result.subdomains_found[:50])}
    </table>

    <h2>Top Pages by Inlinks</h2>
    <table>
        <tr><th>URL</th><th>Inlinks</th><th>Status</th><th>Title</th></tr>
        {''.join(f'<tr><td>{p.url[:80]}</td><td>{p.inlinks_count}</td><td>{p.status_code}</td><td>{p.title[:50]}</td></tr>' for p in sorted(result.pages, key=lambda x: -x.inlinks_count)[:30])}
    </table>

    <footer>
        Generated by Python SEO Spider | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </footer>
</div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"HTML report generated -> {output_path}")

    def _get_severity_badge(self, issue_name: str) -> str:
        """Determine severity badge for an issue."""
        name_lower = issue_name.lower()
        if any(w in name_lower for w in ['error', 'broken', 'missing', '404', '500']):
            return '<span class="badge badge-error">Error</span>'
        elif any(w in name_lower for w in ['warning', 'over', 'duplicate', 'redirect', 'mixed']):
            return '<span class="badge badge-warning">Warning</span>'
        else:
            return '<span class="badge badge-info">Info</span>'
