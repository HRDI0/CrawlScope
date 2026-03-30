"""
CSV Exporter — Complete Screaming Frog-compatible export.
Generates 26 CSV files + JSON manifests matching all SF tabs.
"""
import csv
import json
import os
import logging
from urllib.parse import quote
from datetime import datetime
from collections import defaultdict
from seo_spider.core.models import CrawlResult, PageData
from seo_spider.analyzers.issue_detector import IssueDetector

logger = logging.getLogger("seo_spider.export.csv")
ENC = 'utf-8-sig'


def _w(path, headers, rows):
    """Write a CSV file with UTF-8-SIG encoding."""
    with open(path, 'w', newline='', encoding=ENC) as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)


class CSVExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.generated_files = []

    def _p(self, name):
        """Path helper."""
        return os.path.join(self.output_dir, name)

    def _add_file(self, name):
        """Track generated file."""
        self.generated_files.append(name)

    def export_all(self, result: CrawlResult):
        """Export all CSV and JSON files."""
        # Export all CSVs
        self.export_internal(result)
        self.export_url_all(result)
        self.export_response_codes(result)
        self.export_images(result)
        self.export_canonicals(result)
        self.export_directives(result)
        self.export_h1(result)
        self.export_h2(result)
        self.export_content(result)
        self.export_hreflang(result)
        self.export_pagination(result)
        self.export_structured_data(result)
        self.export_security(result)
        self.export_javascript_rendering(result)
        self.export_links(result)
        self.export_inlinks(result)
        self.export_redirects(result)
        self.export_issues(result)
        self.export_external(result)
        self.export_page_titles_duplicate(result)
        self.export_meta_description_duplicate(result)
        self.export_crawl_warnings(result)

        # Generate statistics CSV + JSON files
        self.export_statistics_summary_csv(result)
        self.export_statistics_summary_json(result)
        self.export_run_manifest(result)
        self.export_run_summary(result)

        file_count = len(self.generated_files)
        logger.info(f"All exports complete: {file_count} files -> {self.output_dir}")
        return self.generated_files

    # ===== 1. internal_all.csv (All HTML pages, 61 columns) =====
    def export_internal(self, result: CrawlResult):
        headers = [
            "Address", "Content Type", "Status Code", "Status",
            "Indexability", "Indexability Status",
            "Title 1", "Title 1 Length", "Title 1 Pixel Width",
            "Meta Description 1", "Meta Description 1 Length", "Meta Description 1 Pixel Width",
            "Meta Keywords 1", "Meta Keywords 1 Length",
            "H1-1", "H1-1 Length", "H2-1", "H2-1 Length", "H2-2", "H2-2 Length",
            "Meta Robots 1", "X-Robots-Tag 1", "Meta Refresh 1",
            "Canonical Link Element 1", "Canonical Status", "rel=\"next\" 1", "rel=\"prev\" 1",
            "HTTP rel=\"next\" 1", "HTTP rel=\"prev\" 1",
            "Size (bytes)", "Transferred (bytes)",
            "Word Count", "Sentence Count", "Average Words Per Sentence",
            "Flesch Reading Ease Score", "Readability", "Text Ratio",
            "Crawl Depth", "Folder Depth", "Link Score",
            "Inlinks", "Unique Inlinks", "Unique JS Inlinks", "% of Total",
            "Outlinks", "Unique Outlinks", "Unique JS Outlinks",
            "External Outlinks", "Unique External Outlinks", "Unique External JS Outlinks",
            "Closest Similarity Match", "No. Near Duplicates",
            "Hash", "Response Time", "Last Modified",
            "Redirect URL", "Redirect Type",
            "Cookies", "HTTP Version",
            "URL Encoded Address", "Crawl Timestamp",
            "HTML Lang", "Content Language",
        ]
        rows = []
        for p in result.pages:
            h1_1 = p.headings.h1[0] if p.headings.h1 else ''
            h2_1 = p.headings.h2[0] if p.headings.h2 else ''
            h2_2 = p.headings.h2[1] if len(p.headings.h2) > 1 else ''
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.title, p.title_length, p.title_pixel_width,
                p.meta_description, p.meta_description_length, p.meta_description_pixel_width,
                p.meta_keywords, p.meta_keywords_length,
                h1_1, len(h1_1), h2_1, len(h2_1), h2_2, len(h2_2),
                p.meta_robots, p.x_robots_tag, p.meta_refresh,
                p.canonical_url, p.canonical_status, p.rel_next, p.rel_prev,
                p.http_rel_next, p.http_rel_prev,
                p.page_speed.html_size, p.transferred_bytes,
                p.word_count, p.sentence_count, p.avg_words_per_sentence,
                p.flesch_reading_ease, p.readability, p.text_ratio,
                p.crawl_depth, p.folder_depth, p.link_score,
                p.inlinks_count, p.unique_inlinks, p.unique_js_inlinks, p.pct_of_total,
                p.outlinks_count, p.unique_outlinks, p.unique_js_outlinks,
                p.external_outlinks, p.unique_external_outlinks, p.unique_external_js_outlinks,
                p.closest_similarity_match, p.near_duplicate_count,
                p.content_hash, f"{p.response_time:.3f}", p.last_modified,
                p.final_url if p.is_redirect else '', p.redirect_type,
                p.cookies, p.http_version,
                p.url_encoded_address, p.crawl_timestamp,
                p.html_lang, p.content_language,
            ])
        _w(self._p("internal_all.csv"), headers, rows)
        self._add_file("internal_all.csv")

    # ===== 2. url_all.csv =====
    def export_url_all(self, result: CrawlResult):
        headers = [
            "Address", "Content Type", "Status Code", "Status",
            "Indexability", "Indexability Status",
            "Hash", "URL Length", "Folder Depth",
            "Canonical Link Element 1", "URL Encoded Address"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.content_hash, p.url_length, p.folder_depth,
                p.canonical_url, p.url_encoded_address,
            ])
        _w(self._p("url_all.csv"), headers, rows)
        self._add_file("url_all.csv")

    # ===== 3. response_codes_all.csv =====
    def export_response_codes(self, result: CrawlResult):
        headers = [
            "Address", "Content Type", "Status Code", "Status",
            "Indexability", "Indexability Status",
            "Inlinks", "Response Time", "Redirect URL", "Redirect Type", "Page Type"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.inlinks_count, f"{p.response_time:.3f}",
                p.final_url if p.is_redirect else '', p.redirect_type,
                p.page_type,
            ])
        _w(self._p("response_codes_all.csv"), headers, rows)
        self._add_file("response_codes_all.csv")

    # ===== 4. images_all.csv (ONE ROW PER IMAGE OCCURRENCE) =====
    def export_images(self, result: CrawlResult):
        headers = [
            "Address", "Alt Text", "Alt Text Length",
            "Missing Alt Attribute", "Missing Alt Text", "Alt Over 100 Characters",
            "Image File Size", "Source Page", "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            for img in p.images:
                alt_length = len(img.alt_text) if img.alt_text else 0
                missing_alt_attr = "Yes" if img.is_missing_alt_attribute else "No"
                missing_alt_text = "Yes" if (not img.alt_text and not img.is_missing_alt_attribute) else "No"
                alt_over_100 = "Yes" if img.alt_over_100 else "No"
                rows.append([
                    img.src, img.alt_text, alt_length,
                    missing_alt_attr, missing_alt_text, alt_over_100,
                    img.file_size, p.url,
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                ])
        _w(self._p("images_all.csv"), headers, rows)
        self._add_file("images_all.csv")

    # ===== 5. canonicals_all.csv =====
    def export_canonicals(self, result: CrawlResult):
        headers = [
            "Address", "Canonical Link Element 1", "HTTP Canonical",
            "Canonical Status", "Indexability", "Indexability Status",
            "Meta Robots 1", "X-Robots-Tag 1"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.canonical_url, p.http_canonical,
                p.canonical_status,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.meta_robots, p.x_robots_tag,
            ])
        _w(self._p("canonicals_all.csv"), headers, rows)
        self._add_file("canonicals_all.csv")

    # ===== 6. directives_all.csv =====
    def export_directives(self, result: CrawlResult):
        headers = [
            "Address", "Occurrences",
            "Meta Robots 1", "X-Robots-Tag 1", "Meta Refresh 1",
            "Canonical Link Element 1", "HTTP Canonical",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, 1,
                p.meta_robots, p.x_robots_tag, p.meta_refresh,
                p.canonical_url, p.http_canonical,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("directives_all.csv"), headers, rows)
        self._add_file("directives_all.csv")

    # ===== 7. h1_all.csv =====
    def export_h1(self, result: CrawlResult):
        headers = [
            "Address", "Occurrences",
            "H1-1", "H1-1 Length", "H1-2", "H1-2 Length",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            h1_1 = p.headings.h1[0] if p.headings.h1 else ''
            h1_2 = p.headings.h1[1] if len(p.headings.h1) > 1 else ''
            rows.append([
                p.url, len(p.headings.h1),
                h1_1, len(h1_1), h1_2, len(h1_2),
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("h1_all.csv"), headers, rows)
        self._add_file("h1_all.csv")

    # ===== 8. h2_all.csv =====
    def export_h2(self, result: CrawlResult):
        headers = [
            "Address", "Occurrences",
            "H2-1", "H2-1 Length", "H2-2", "H2-2 Length",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            h2_1 = p.headings.h2[0] if p.headings.h2 else ''
            h2_2 = p.headings.h2[1] if len(p.headings.h2) > 1 else ''
            rows.append([
                p.url, len(p.headings.h2),
                h2_1, len(h2_1), h2_2, len(h2_2),
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("h2_all.csv"), headers, rows)
        self._add_file("h2_all.csv")

    # ===== 9. content_all.csv =====
    def export_content(self, result: CrawlResult):
        headers = [
            "Address", "Word Count", "Sentence Count", "Average Words Per Sentence",
            "Flesch Reading Ease Score", "Readability",
            "Text Ratio", "Closest Similarity Match", "No. Near Duplicates",
            "Language", "Hash",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.word_count, p.sentence_count, p.avg_words_per_sentence,
                p.flesch_reading_ease, p.readability,
                p.text_ratio, p.closest_similarity_match, p.near_duplicate_count,
                p.detected_language or p.html_lang, p.content_hash,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("content_all.csv"), headers, rows)
        self._add_file("content_all.csv")

    # ===== 10. hreflang_all.csv =====
    def export_hreflang(self, result: CrawlResult):
        headers = [
            "Address", "Title 1", "Occurrences",
            "HTML hreflang 1", "HTML hreflang 1 URL",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            if p.hreflang_annotations:
                ann = p.hreflang_annotations[0]
                lang_code = f"{ann.language}-{ann.region}" if ann.region else ann.language
                rows.append([
                    p.url, p.title, len(p.hreflang_annotations),
                    lang_code, ann.target_url,
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                ])
        _w(self._p("hreflang_all.csv"), headers, rows)
        self._add_file("hreflang_all.csv")

    # ===== 11. pagination_all.csv =====
    def export_pagination(self, result: CrawlResult):
        headers = [
            "Address", "Indexability", "Indexability Status",
            "rel=\"next\" 1", "rel=\"prev\" 1",
            "HTTP rel=\"next\" 1", "HTTP rel=\"prev\" 1",
            "Canonical Link Element 1"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.rel_next, p.rel_prev, p.http_rel_next, p.http_rel_prev,
                p.canonical_url,
            ])
        _w(self._p("pagination_all.csv"), headers, rows)
        self._add_file("pagination_all.csv")

    # ===== 12. structured_data_all.csv =====
    def export_structured_data(self, result: CrawlResult):
        headers = [
            "Address", "Format", "Total Types", "Unique Types",
            "Type-1", "Errors", "Warnings",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            if p.structured_data:
                formats = set(sd.format_type for sd in p.structured_data)
                format_str = "; ".join(sorted(formats)) if formats else ""
                types = [sd.schema_type for sd in p.structured_data]
                unique_types = len(set(types))
                errors = sum(len(sd.validation_errors) for sd in p.structured_data)
                warnings = sum(len(sd.validation_warnings) for sd in p.structured_data)
                rows.append([
                    p.url, format_str, len(types), unique_types,
                    types[0] if types else "",
                    errors, warnings,
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                ])
        _w(self._p("structured_data_all.csv"), headers, rows)
        self._add_file("structured_data_all.csv")

    # ===== 13. security_all.csv =====
    def export_security(self, result: CrawlResult):
        headers = [
            "Address", "Content Type", "Status Code", "Status",
            "HTTPS", "Mixed Content", "HSTS",
            "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy",
            "Content-Security-Policy", "Permissions-Policy",
            "Indexability", "Indexability Status"
        ]
        rows = []
        for p in result.pages:
            s = p.security
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                s.is_https, s.has_mixed_content, s.hsts_enabled,
                s.x_frame_options, s.x_content_type_options, s.referrer_policy,
                s.content_security_policy, s.permissions_policy,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("security_all.csv"), headers, rows)
        self._add_file("security_all.csv")

    # ===== 14. javascript_all.csv (JS rendering comparison) =====
    def export_javascript_rendering(self, result: CrawlResult):
        headers = [
            "Address", "Status Code", "Status",
            "HTML Word Count", "Rendered HTML Word Count", "Word Count Change", "JS Word Count %",
            "HTML Title", "Rendered HTML Title",
            "HTML H1", "Rendered HTML H1",
            "HTML Meta Description", "Rendered HTML Meta Description",
            "HTML Canonical", "Rendered HTML Canonical",
            "Unique Inlinks", "Unique JS Inlinks",
            "Unique Outlinks", "Unique JS Outlinks",
            "Unique External Outlinks", "Unique External JS Outlinks",
            "HTML Meta Robots 1", "Rendered HTML Meta Robots 1",
        ]
        rows = []
        for p in result.pages:
            html_wc = p.word_count - p.word_count_change if p.word_count_change else p.word_count
            rows.append([
                p.url, p.status_code, p.status_text,
                html_wc, p.rendered_word_count or p.word_count,
                p.word_count_change, p.js_word_count_pct,
                p.title, p.rendered_title or p.title,
                p.headings.h1[0] if p.headings.h1 else '',
                p.rendered_h1 or (p.headings.h1[0] if p.headings.h1 else ''),
                p.meta_description, p.rendered_meta_description or p.meta_description,
                p.canonical_url, p.rendered_canonical or p.canonical_url,
                p.unique_inlinks, p.unique_js_inlinks,
                p.unique_outlinks, p.unique_js_outlinks,
                p.unique_external_outlinks, p.unique_external_js_outlinks,
                p.meta_robots, p.rendered_meta_robots or p.meta_robots,
            ])
        _w(self._p("javascript_all.csv"), headers, rows)
        self._add_file("javascript_all.csv")

    # ===== 15. links_all.csv =====
    def export_links(self, result: CrawlResult):
        headers = [
            "Address", "Indexability", "Indexability Status",
            "Crawl Depth", "Link Score",
            "Inlinks", "Unique Inlinks", "Unique JS Inlinks", "% of Total",
            "Outlinks", "Unique Outlinks", "Unique JS Outlinks",
            "External Outlinks", "Unique External Outlinks", "Unique External JS Outlinks"
        ]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.crawl_depth, p.link_score,
                p.inlinks_count, p.unique_inlinks, p.unique_js_inlinks, p.pct_of_total,
                p.outlinks_count, p.unique_outlinks, p.unique_js_outlinks,
                p.external_outlinks, p.unique_external_outlinks, p.unique_external_js_outlinks,
            ])
        _w(self._p("links_all.csv"), headers, rows)
        self._add_file("links_all.csv")

    # ===== 16. inlinks.csv =====
    def export_inlinks(self, result: CrawlResult):
        headers = [
            "Source URL", "Target URL", "Anchor Text", "Link Type", "Link Position", "Is Follow", "Status Code"
        ]
        rows = []
        for p in result.pages:
            # Internal links
            for link in p.internal_links:
                rows.append([
                    p.url, link.target_url, link.anchor_text, link.link_type,
                    link.link_position, "Yes" if link.is_follow else "No", link.status_code
                ])
            # External links
            for link in p.external_links:
                rows.append([
                    p.url, link.target_url, link.anchor_text, link.link_type,
                    link.link_position, "Yes" if link.is_follow else "No", link.status_code
                ])
        _w(self._p("inlinks.csv"), headers, rows)
        self._add_file("inlinks.csv")

    # ===== 17. redirects.csv =====
    def export_redirects(self, result: CrawlResult):
        headers = [
            "Source URL", "Status Code", "Redirect Type", "Redirect Chain", "Final URL", "Chain Length", "Redirect Status"
        ]
        rows = []
        for p in result.pages:
            if p.is_redirect:
                chain_str = ' -> '.join(p.redirect_chain) if p.redirect_chain else ''
                rows.append([
                    p.url, p.status_code, p.redirect_type, chain_str,
                    p.final_url, len(p.redirect_chain), p.redirect_status or "Redirect"
                ])
        _w(self._p("redirects.csv"), headers, rows)
        self._add_file("redirects.csv")

    # ===== 18. issues.csv =====
    def export_issues(self, result: CrawlResult):
        headers = [
            "URL", "Category", "Severity", "Issue Type", "Description",
            "Evidence", "Current Value", "Recommendation",
            "Source Table", "Counting Unit"
        ]
        rows = []
        detector = IssueDetector()
        all_issues = detector.detect_crawl_issues(result)
        for url, issues in all_issues.items():
            for issue in issues:
                rows.append([
                    url, issue.category, issue.severity, issue.issue_type,
                    issue.description, issue.evidence, issue.current_value,
                    issue.recommendation, issue.source_table, issue.counting_unit
                ])
        _w(self._p("issues.csv"), headers, rows)
        self._add_file("issues.csv")

    # ===== 19. external_all.csv =====
    def export_external(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status", "Crawl Depth", "Inlinks"]
        rows = []
        ext_inlinks = {}
        for p in result.pages:
            for link in p.external_links:
                ext_inlinks.setdefault(link.target_url, []).append(p.url)
        for url, sources in ext_inlinks.items():
            rows.append([url, '', '', '', '', len(sources)])
        _w(self._p("external_all.csv"), headers, rows)
        self._add_file("external_all.csv")

    # ===== 20. page_titles_duplicate.csv =====
    def export_page_titles_duplicate(self, result: CrawlResult):
        headers = [
            "Address", "Occurrences", "Title 1", "Title 1 Length", "Title 1 Pixel Width",
            "Indexability", "Indexability Status"
        ]
        title_map = {}
        for p in result.pages:
            if p.title:
                title_map.setdefault(p.title, []).append(p)
        rows = []
        for title, pages in title_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append([
                        p.url, len(pages), p.title, p.title_length, p.title_pixel_width,
                        "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status
                    ])
        _w(self._p("page_titles_duplicate.csv"), headers, rows)
        self._add_file("page_titles_duplicate.csv")

    # ===== 21. meta_description_duplicate.csv =====
    def export_meta_description_duplicate(self, result: CrawlResult):
        headers = [
            "Address", "Occurrences", "Meta Description 1", "Meta Description 1 Length",
            "Meta Description 1 Pixel Width", "Indexability", "Indexability Status"
        ]
        desc_map = {}
        for p in result.pages:
            if p.meta_description:
                desc_map.setdefault(p.meta_description, []).append(p)
        rows = []
        for desc, pages in desc_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append([
                        p.url, len(pages), p.meta_description, p.meta_description_length,
                        p.meta_description_pixel_width,
                        "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status
                    ])
        _w(self._p("meta_description_duplicate.csv"), headers, rows)
        self._add_file("meta_description_duplicate.csv")

    # ===== 22. crawl_warnings.csv =====
    def export_crawl_warnings(self, result: CrawlResult):
        headers = ["timestamp", "warning_type", "message", "affected_url"]
        rows = []
        if result.crawl_warnings:
            for warning in result.crawl_warnings:
                # Parse warning if it's a string, otherwise format it
                rows.append([
                    datetime.now().isoformat(), "crawl_warning", str(warning), ""
                ])
        _w(self._p("crawl_warnings.csv"), headers, rows)
        self._add_file("crawl_warnings.csv")

    # ===== 23. statistics_summary.csv =====
    def export_statistics_summary_csv(self, result: CrawlResult):
        """Export statistics summary as CSV."""
        stats = self._compute_statistics(result)
        headers = [
            "metric_name", "metric_value", "counting_unit", "denominator_if_any",
            "scope", "source_tables", "notes"
        ]
        rows = []
        for stat in stats:
            rows.append([
                stat["metric_name"],
                stat["metric_value"],
                stat["counting_unit"],
                stat.get("denominator_if_any", ""),
                stat.get("scope", "crawl"),
                stat.get("source_tables", ""),
                stat.get("notes", "")
            ])
        _w(self._p("statistics_summary.csv"), headers, rows)
        self._add_file("statistics_summary.csv")

    # ===== JSON FILES =====

    # ===== 24. statistics_summary.json =====
    def export_statistics_summary_json(self, result: CrawlResult):
        """Export statistics summary as JSON."""
        stats = self._compute_statistics(result)
        path = self._p("statistics_summary.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        self._add_file("statistics_summary.json")

    # ===== 25. run_manifest.json =====
    def export_run_manifest(self, result: CrawlResult):
        """Export run manifest."""
        manifest = {
            "start_url": result.start_url,
            "domain": result.domain,
            "crawl_start_time": result.crawl_start_time,
            "crawl_end_time": result.crawl_end_time,
            "total_urls_crawled": result.total_urls_crawled,
            "total_internal": result.total_internal,
            "total_external": result.total_external,
            "output_files": sorted(self.generated_files),
            "config_summary": {
                "crawler": "python-seo-spider",
                "version": "1.0",
                "export_format": "screaming_frog_compatible"
            }
        }
        path = self._p("run_manifest.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        self._add_file("run_manifest.json")

    # ===== 26. run_summary.json =====
    def export_run_summary(self, result: CrawlResult):
        """Export run summary."""
        # Status code distribution
        status_dist = defaultdict(int)
        for p in result.pages:
            status_dist[str(p.status_code)] += 1

        # Top issues
        detector = IssueDetector()
        all_issues = detector.detect_crawl_issues(result)
        issue_counts = defaultdict(int)
        for url, issues in all_issues.items():
            for issue in issues:
                issue_counts[issue.issue_type] += 1

        # Calculate crawl duration
        start = datetime.fromisoformat(result.crawl_start_time.replace('Z', '+00:00')) if result.crawl_start_time else datetime.now()
        end = datetime.fromisoformat(result.crawl_end_time.replace('Z', '+00:00')) if result.crawl_end_time else datetime.now()
        duration_seconds = (end - start).total_seconds()

        summary = {
            "domain": result.domain,
            "total_pages": len(result.pages),
            "status_code_distribution": dict(status_dist),
            "top_issues": dict(sorted(issue_counts.items(), key=lambda x: -x[1])[:10]),
            "crawl_duration_seconds": duration_seconds,
            "pages_per_second": len(result.pages) / duration_seconds if duration_seconds > 0 else 0
        }
        path = self._p("run_summary.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        self._add_file("run_summary.json")

    # ===== HELPER METHODS =====

    def _compute_statistics(self, result: CrawlResult) -> list:
        """Compute all statistics metrics."""
        stats = []

        # Count pages by status
        html_pages_200 = [p for p in result.pages if p.content_type and 'html' in p.content_type.lower() and p.status_code == 200]

        # Total URLs
        stats.append({
            "metric_name": "Total URLs Crawled",
            "metric_value": len(result.pages),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Total Internal (HTML 200)
        stats.append({
            "metric_name": "Total Internal URLs",
            "metric_value": len(html_pages_200),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Total External
        stats.append({
            "metric_name": "Total External URLs",
            "metric_value": result.total_external,
            "counting_unit": "url",
            "scope": "crawl",
            "source_tables": "external_all.csv",
        })

        # Redirects
        redirects = [p for p in result.pages if p.is_redirect]
        stats.append({
            "metric_name": "Total Redirects",
            "metric_value": len(redirects),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "redirects.csv",
        })

        # Client errors (4xx)
        client_errors = [p for p in result.pages if 400 <= p.status_code < 500]
        stats.append({
            "metric_name": "Total Client Errors",
            "metric_value": len(client_errors),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "response_codes_all.csv",
        })

        # Server errors (5xx)
        server_errors = [p for p in result.pages if p.status_code >= 500]
        stats.append({
            "metric_name": "Total Server Errors",
            "metric_value": len(server_errors),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "response_codes_all.csv",
        })

        # Total Images (occurrence count)
        total_images = sum(len(p.images) for p in result.pages)
        stats.append({
            "metric_name": "Total Images",
            "metric_value": total_images,
            "counting_unit": "occurrence",
            "scope": "crawl",
            "source_tables": "images_all.csv",
        })

        # Unique Image Assets
        unique_images = set()
        for p in result.pages:
            for img in p.images:
                unique_images.add(img.src)
        stats.append({
            "metric_name": "Unique Image Assets",
            "metric_value": len(unique_images),
            "counting_unit": "asset",
            "scope": "crawl",
            "source_tables": "images_all.csv",
        })

        # Images Missing Alt Attribute
        images_missing_alt_attr = sum(len([img for img in p.images if img.is_missing_alt_attribute]) for p in result.pages)
        stats.append({
            "metric_name": "Images Missing Alt Attribute",
            "metric_value": images_missing_alt_attr,
            "counting_unit": "occurrence",
            "scope": "crawl",
            "source_tables": "images_all.csv",
        })

        # Images Missing Alt Text
        images_missing_alt_text = sum(len([img for img in p.images if not img.alt_text and not img.is_missing_alt_attribute]) for p in result.pages)
        stats.append({
            "metric_name": "Images Missing Alt Text",
            "metric_value": images_missing_alt_text,
            "counting_unit": "occurrence",
            "scope": "crawl",
            "source_tables": "images_all.csv",
        })

        # Images Alt Over 100 Characters
        images_alt_over_100 = sum(len([img for img in p.images if img.alt_over_100]) for p in result.pages)
        stats.append({
            "metric_name": "Images Alt Over 100 Characters",
            "metric_value": images_alt_over_100,
            "counting_unit": "occurrence",
            "scope": "crawl",
            "source_tables": "images_all.csv",
        })

        # Pages with Missing Title
        missing_title = [p for p in result.pages if not p.title]
        stats.append({
            "metric_name": "Pages with Missing Title",
            "metric_value": len(missing_title),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Pages with Duplicate Title
        title_counts = defaultdict(list)
        for p in result.pages:
            if p.title:
                title_counts[p.title].append(p)
        duplicate_titles = [pages for pages in title_counts.values() if len(pages) > 1]
        pages_dup_title = sum(len(pages) for pages in duplicate_titles)
        stats.append({
            "metric_name": "Pages with Duplicate Title",
            "metric_value": pages_dup_title,
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "page_titles_duplicate.csv",
        })

        # Pages with Title Over 60 Characters
        title_over_60 = [p for p in result.pages if p.title_length > 60]
        stats.append({
            "metric_name": "Pages with Title Over 60 Characters",
            "metric_value": len(title_over_60),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Pages with Title Below 30 Characters
        title_below_30 = [p for p in result.pages if p.title_length > 0 and p.title_length < 30]
        stats.append({
            "metric_name": "Pages with Title Below 30 Characters",
            "metric_value": len(title_below_30),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Pages with Missing Meta Description
        missing_desc = [p for p in result.pages if not p.meta_description]
        stats.append({
            "metric_name": "Pages with Missing Meta Description",
            "metric_value": len(missing_desc),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Pages with Duplicate Meta Description
        desc_counts = defaultdict(list)
        for p in result.pages:
            if p.meta_description:
                desc_counts[p.meta_description].append(p)
        duplicate_descs = [pages for pages in desc_counts.values() if len(pages) > 1]
        pages_dup_desc = sum(len(pages) for pages in duplicate_descs)
        stats.append({
            "metric_name": "Pages with Duplicate Meta Description",
            "metric_value": pages_dup_desc,
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "meta_description_duplicate.csv",
        })

        # Pages with Meta Description Over 160 Characters
        desc_over_160 = [p for p in result.pages if p.meta_description_length > 160]
        stats.append({
            "metric_name": "Pages with Meta Description Over 160 Characters",
            "metric_value": len(desc_over_160),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        # Pages with Missing H1
        missing_h1 = [p for p in result.pages if p.headings.missing_h1]
        stats.append({
            "metric_name": "Pages with Missing H1",
            "metric_value": len(missing_h1),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "h1_all.csv",
        })

        # Pages with Multiple H1
        multiple_h1 = [p for p in result.pages if p.headings.multiple_h1]
        stats.append({
            "metric_name": "Pages with Multiple H1",
            "metric_value": len(multiple_h1),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "h1_all.csv",
        })

        # Pages with Missing Canonical
        missing_canonical = [p for p in result.pages if not p.canonical_url]
        stats.append({
            "metric_name": "Pages with Missing Canonical",
            "metric_value": len(missing_canonical),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "canonicals_all.csv",
        })

        # Pages with Self-Referencing Canonical
        self_ref_canonical = [p for p in result.pages if p.canonical_url and p.canonical_is_self]
        stats.append({
            "metric_name": "Pages with Self-Referencing Canonical",
            "metric_value": len(self_ref_canonical),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "canonicals_all.csv",
        })

        # Pages with Non-Self Canonical
        non_self_canonical = [p for p in result.pages if p.canonical_url and not p.canonical_is_self]
        stats.append({
            "metric_name": "Pages with Non-Self Canonical",
            "metric_value": len(non_self_canonical),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "canonicals_all.csv",
        })

        # Pages with Structured Data
        with_schema = [p for p in result.pages if p.structured_data]
        stats.append({
            "metric_name": "Pages with Structured Data",
            "metric_value": len(with_schema),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "structured_data_all.csv",
        })

        # Pages without Structured Data
        without_schema = [p for p in result.pages if not p.structured_data]
        stats.append({
            "metric_name": "Pages without Structured Data",
            "metric_value": len(without_schema),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "structured_data_all.csv",
        })

        # Pages with Hreflang
        with_hreflang = [p for p in result.pages if p.hreflang_annotations]
        stats.append({
            "metric_name": "Pages with Hreflang",
            "metric_value": len(with_hreflang),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "hreflang_all.csv",
        })

        # Average Word Count
        avg_word_count = sum(p.word_count for p in result.pages) / len(result.pages) if result.pages else 0
        stats.append({
            "metric_name": "Average Word Count",
            "metric_value": round(avg_word_count, 2),
            "counting_unit": "words",
            "scope": "crawl",
            "source_tables": "content_all.csv",
        })

        # Average Response Time
        avg_response_time = sum(p.response_time for p in result.pages) / len(result.pages) if result.pages else 0
        stats.append({
            "metric_name": "Average Response Time",
            "metric_value": round(avg_response_time, 3),
            "counting_unit": "seconds",
            "scope": "crawl",
            "source_tables": "response_codes_all.csv",
        })

        # Average Crawl Depth
        avg_crawl_depth = sum(p.crawl_depth for p in result.pages) / len(result.pages) if result.pages else 0
        stats.append({
            "metric_name": "Average Crawl Depth",
            "metric_value": round(avg_crawl_depth, 2),
            "counting_unit": "levels",
            "scope": "crawl",
            "source_tables": "links_all.csv",
        })

        # HTTPS Pages (%)
        https_pages = [p for p in result.pages if p.security.is_https]
        https_pct = (len(https_pages) / len(result.pages) * 100) if result.pages else 0
        stats.append({
            "metric_name": "HTTPS Pages",
            "metric_value": round(https_pct, 1),
            "counting_unit": "%",
            "denominator_if_any": str(len(result.pages)),
            "scope": "crawl",
            "source_tables": "security_all.csv",
        })

        # Non-Indexable Pages
        non_indexable = [p for p in result.pages if not p.is_indexable]
        stats.append({
            "metric_name": "Non-Indexable Pages",
            "metric_value": len(non_indexable),
            "counting_unit": "page",
            "scope": "crawl",
            "source_tables": "internal_all.csv",
        })

        return stats
