"""
CSV Exporter — Full Screaming Frog-compatible export.
Generates 22+ CSV files matching all SF tabs.
"""
import csv
import os
import logging
from urllib.parse import quote
from seo_spider.core.models import CrawlResult, PageData

logger = logging.getLogger("seo_spider.export.csv")
ENC = 'utf-8-sig'


def _w(path, headers, rows):
    with open(path, 'w', newline='', encoding=ENC) as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)


class CSVExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _p(self, name):
        return os.path.join(self.output_dir, name)

    def export_all(self, result: CrawlResult):
        self.export_internal(result)
        self.export_external(result)
        self.export_images(result)
        self.export_css(result)
        self.export_javascript_resources(result)
        self.export_hreflang(result)
        self.export_structured_data(result)
        self.export_issues(result)
        self.export_redirects(result)
        self.export_inlinks(result)
        self.export_sitemaps(result)
        # New SF-compatible exports
        self.export_response_codes(result)
        self.export_security(result)
        self.export_content(result)
        self.export_links(result)
        self.export_canonicals(result)
        self.export_directives(result)
        self.export_h1(result)
        self.export_h2(result)
        self.export_meta_keywords(result)
        self.export_pagination(result)
        self.export_url(result)
        self.export_page_titles_duplicate(result)
        self.export_meta_description_duplicate(result)
        self.export_javascript_rendering(result)
        self.export_custom_extraction(result)
        self.export_custom_search(result)
        logger.info(f"All CSV exports complete -> {self.output_dir}")

    # ===== 1. internal_all.csv (63 columns, SF-matching) =====
    def export_internal(self, result: CrawlResult):
        headers = [
            "Address", "Content Type", "Status Code", "Status",
            "Indexability", "Indexability Status",
            "Title 1", "Title 1 Length", "Title 1 Pixel Width",
            "Meta Description 1", "Meta Description 1 Length", "Meta Description 1 Pixel Width",
            "Meta Keywords 1", "Meta Keywords 1 Length",
            "H1-1", "H1-1 Length", "H2-1", "H2-1 Length", "H2-2", "H2-2 Length",
            "Meta Robots 1", "X-Robots-Tag 1", "Meta Refresh 1",
            "Canonical Link Element 1", "rel=\"next\" 1", "rel=\"prev\" 1",
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
                p.canonical_url, p.rel_next, p.rel_prev,
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

    # ===== 2. external_all.csv =====
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

    # ===== 3. images_all.csv =====
    def export_images(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Size (bytes)", "IMG Inlinks",
                    "Indexability", "Indexability Status", "Dimensions",
                    "Alt Text", "Missing Alt Attribute", "Source Page"]
        rows = []
        for p in result.pages:
            for img in p.images:
                dim = f"{img.width}x{img.height}" if img.width and img.height else ""
                rows.append([
                    img.src, "image", img.file_size, "",
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                    dim, img.alt_text, img.is_missing_alt_attribute, p.url,
                ])
        _w(self._p("images_all.csv"), headers, rows)

    # ===== 4. css.csv =====
    def export_css(self, result: CrawlResult):
        headers = ["URL", "Status Code", "Content Type", "File Size", "Source Page"]
        rows = []
        for p in result.pages:
            for css in p.css_resources:
                rows.append([css.url, css.status_code, css.content_type, css.file_size, p.url])
        _w(self._p("css.csv"), headers, rows)

    # ===== 5. javascript.csv (resource list) =====
    def export_javascript_resources(self, result: CrawlResult):
        headers = ["URL", "Status Code", "Content Type", "File Size", "Source Page"]
        rows = []
        for p in result.pages:
            for js in p.js_resources:
                rows.append([js.url, js.status_code, js.content_type, js.file_size, p.url])
        _w(self._p("javascript.csv"), headers, rows)

    # ===== 6. hreflang_all.csv =====
    def export_hreflang(self, result: CrawlResult):
        headers = ["Address", "Title 1", "Occurrences",
                    "HTML hreflang 1", "HTML hreflang 1 URL",
                    "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            if p.hreflang_annotations:
                ann = p.hreflang_annotations[0]
                rows.append([
                    p.url, p.title, len(p.hreflang_annotations),
                    f"{ann.language}-{ann.region}" if ann.region else ann.language,
                    ann.target_url,
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                ])
        _w(self._p("hreflang_all.csv"), headers, rows)

    # ===== 7. structured_data_all.csv =====
    def export_structured_data(self, result: CrawlResult):
        headers = ["Address", "Errors", "Warnings", "Total Types", "Unique Types", "Type-1",
                    "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            if p.structured_data:
                types = [sd.schema_type for sd in p.structured_data]
                errors = sum(len(sd.validation_errors) for sd in p.structured_data)
                warnings = sum(len(sd.validation_warnings) for sd in p.structured_data)
                rows.append([
                    p.url, errors, warnings, len(types), len(set(types)),
                    types[0] if types else '',
                    "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                ])
        _w(self._p("structured_data_all.csv"), headers, rows)

    # ===== 8. issues.csv =====
    def export_issues(self, result: CrawlResult):
        from ..analyzers.issue_detector import IssueDetector
        all_issues = IssueDetector().detect_crawl_issues(result)
        headers = ["URL", "Category", "Severity", "Issue Type", "Description", "Current Value", "Recommendation"]
        rows = []
        for url, issues in all_issues.items():
            for i in issues:
                rows.append([url, i.category, i.severity, i.issue_type, i.description, i.current_value, i.recommendation])
        _w(self._p("issues.csv"), headers, rows)

    # ===== 9. redirects.csv =====
    def export_redirects(self, result: CrawlResult):
        headers = ["Source URL", "Redirect Type", "Redirect Chain", "Final URL", "Chain Length"]
        rows = []
        for p in result.pages:
            if p.is_redirect:
                rows.append([p.url, p.redirect_type, ' -> '.join(p.redirect_chain), p.final_url, len(p.redirect_chain)])
        _w(self._p("redirects.csv"), headers, rows)

    # ===== 10. inlinks.csv =====
    def export_inlinks(self, result: CrawlResult):
        headers = ["Target URL", "Inlink Count", "Source URLs (sample)"]
        rows = []
        for target, sources in sorted(result.inlink_map.items(), key=lambda x: -len(x[1])):
            rows.append([target, len(sources), '; '.join(sources[:10])])
        _w(self._p("inlinks.csv"), headers, rows)

    # ===== 11. sitemaps_all.csv =====
    def export_sitemaps(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status", "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            rows.append([p.url, p.content_type, p.status_code, p.status_text,
                         "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("sitemaps_all.csv"), headers, rows)

    # ===== 12. response_codes_all.csv =====
    def export_response_codes(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status",
                    "Indexability", "Indexability Status", "Inlinks",
                    "Response Time", "Redirect URL", "Redirect Type"]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.inlinks_count, f"{p.response_time:.3f}",
                p.final_url if p.is_redirect else '', p.redirect_type,
            ])
        _w(self._p("response_codes_all.csv"), headers, rows)

    # ===== 13. security_all.csv =====
    def export_security(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status",
                    "HTTPS", "Mixed Content", "HSTS",
                    "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy",
                    "Content-Security-Policy", "Permissions-Policy",
                    "HTTP Version", "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            s = p.security
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                s.is_https, s.has_mixed_content, s.hsts_enabled,
                s.x_frame_options, s.x_content_type_options, s.referrer_policy,
                s.content_security_policy, s.permissions_policy,
                p.http_version,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("security_all.csv"), headers, rows)

    # ===== 14. content_all.csv =====
    def export_content(self, result: CrawlResult):
        headers = ["Address", "Word Count", "Sentence Count", "Average Words Per Sentence",
                    "Flesch Reading Ease Score", "Readability",
                    "Closest Similarity Match", "No. Near Duplicates",
                    "Language", "Hash", "Text Ratio",
                    "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.word_count, p.sentence_count, p.avg_words_per_sentence,
                p.flesch_reading_ease, p.readability,
                p.closest_similarity_match, p.near_duplicate_count,
                p.detected_language or p.html_lang, p.content_hash, p.text_ratio,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
            ])
        _w(self._p("content_all.csv"), headers, rows)

    # ===== 15. links_all.csv =====
    def export_links(self, result: CrawlResult):
        headers = ["Address", "Indexability", "Indexability Status",
                    "Crawl Depth", "Link Score",
                    "Inlinks", "Unique Inlinks", "Unique JS Inlinks", "% of Total",
                    "Outlinks", "Unique Outlinks", "Unique JS Outlinks",
                    "External Outlinks", "Unique External Outlinks", "Unique External JS Outlinks"]
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

    # ===== 16. canonicals_all.csv =====
    def export_canonicals(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "Indexability", "Indexability Status",
                    "Canonical Link Element 1", "HTTP Canonical",
                    "Meta Robots 1", "X-Robots-Tag 1",
                    "rel=\"next\" 1", "rel=\"prev\" 1",
                    "HTTP rel=\"next\" 1", "HTTP rel=\"prev\" 1"]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, 1,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.canonical_url, p.http_canonical,
                p.meta_robots, p.x_robots_tag,
                p.rel_next, p.rel_prev,
                p.http_rel_next, p.http_rel_prev,
            ])
        _w(self._p("canonicals_all.csv"), headers, rows)

    # ===== 17. directives_all.csv =====
    def export_directives(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "Meta Robots 1", "X-Robots-Tag 1",
                    "Meta Refresh 1", "Canonical Link Element 1", "HTTP Canonical"]
        rows = []
        for p in result.pages:
            rows.append([p.url, 1, p.meta_robots, p.x_robots_tag, p.meta_refresh,
                         p.canonical_url, p.http_canonical])
        _w(self._p("directives_all.csv"), headers, rows)

    # ===== 18. h1_all.csv =====
    def export_h1(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "H1-1", "H1-1 Length", "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            h1 = p.headings.h1[0] if p.headings.h1 else ''
            rows.append([p.url, len(p.headings.h1), h1, len(h1),
                         "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("h1_all.csv"), headers, rows)

    # ===== 19. h2_all.csv =====
    def export_h2(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "H2-1", "H2-1 Length", "H2-2", "H2-2 Length",
                    "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            h2_1 = p.headings.h2[0] if p.headings.h2 else ''
            h2_2 = p.headings.h2[1] if len(p.headings.h2) > 1 else ''
            rows.append([p.url, len(p.headings.h2), h2_1, len(h2_1), h2_2, len(h2_2),
                         "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("h2_all.csv"), headers, rows)

    # ===== 20. meta_keywords_all.csv =====
    def export_meta_keywords(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "Meta Keywords 1", "Meta Keywords 1 Length",
                    "Indexability", "Indexability Status"]
        rows = []
        for p in result.pages:
            rows.append([p.url, 1 if p.meta_keywords else 0, p.meta_keywords, p.meta_keywords_length,
                         "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("meta_keywords_all.csv"), headers, rows)

    # ===== 21. pagination_all.csv =====
    def export_pagination(self, result: CrawlResult):
        headers = ["Address", "Indexability", "Indexability Status",
                    "rel=\"next\" 1", "rel=\"prev\" 1",
                    "HTTP rel=\"next\" 1", "HTTP rel=\"prev\" 1",
                    "Canonical Link Element 1", "HTTP Canonical",
                    "Meta Robots 1", "X-Robots-Tag 1"]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.rel_next, p.rel_prev, p.http_rel_next, p.http_rel_prev,
                p.canonical_url, p.http_canonical, p.meta_robots, p.x_robots_tag,
            ])
        _w(self._p("pagination_all.csv"), headers, rows)

    # ===== 22. url_all.csv =====
    def export_url(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status",
                    "Indexability", "Indexability Status",
                    "Hash", "Length", "Canonical Link Element 1", "URL Encoded Address"]
        rows = []
        for p in result.pages:
            rows.append([
                p.url, p.content_type, p.status_code, p.status_text,
                "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status,
                p.content_hash, p.url_length, p.canonical_url, p.url_encoded_address,
            ])
        _w(self._p("url_all.csv"), headers, rows)

    # ===== 23. page_titles_duplicate.csv =====
    def export_page_titles_duplicate(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "Title 1", "Title 1 Length", "Title 1 Pixel Width",
                    "Indexability", "Indexability Status"]
        title_map = {}
        for p in result.pages:
            if p.title:
                title_map.setdefault(p.title, []).append(p)
        rows = []
        for title, pages in title_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append([p.url, len(pages), p.title, p.title_length, p.title_pixel_width,
                                 "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("page_titles_duplicate.csv"), headers, rows)

    # ===== 24. meta_description_duplicate.csv =====
    def export_meta_description_duplicate(self, result: CrawlResult):
        headers = ["Address", "Occurrences", "Meta Description 1", "Meta Description 1 Length",
                    "Meta Description 1 Pixel Width", "Indexability", "Indexability Status"]
        desc_map = {}
        for p in result.pages:
            if p.meta_description:
                desc_map.setdefault(p.meta_description, []).append(p)
        rows = []
        for desc, pages in desc_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append([p.url, len(pages), p.meta_description, p.meta_description_length,
                                 p.meta_description_pixel_width,
                                 "Indexable" if p.is_indexable else "Non-Indexable", p.indexability_status])
        _w(self._p("meta_description_duplicate.csv"), headers, rows)

    # ===== 25. javascript_all.csv (JS rendering comparison) =====
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
            # Only include pages that had JS rendering
            html_wc = p.word_count - p.word_count_change if p.word_count_change else p.word_count
            rows.append([
                p.url, p.status_code, p.status_text,
                html_wc, p.rendered_word_count or p.word_count,
                p.word_count_change, p.js_word_count_pct,
                p.title if not p.rendered_title else p.title,
                p.rendered_title or p.title,
                p.headings.h1[0] if p.headings.h1 else '',
                p.rendered_h1 or (p.headings.h1[0] if p.headings.h1 else ''),
                p.meta_description,
                p.rendered_meta_description or p.meta_description,
                p.canonical_url,
                p.rendered_canonical or p.canonical_url,
                p.unique_inlinks, p.unique_js_inlinks,
                p.unique_outlinks, p.unique_js_outlinks,
                p.unique_external_outlinks, p.unique_external_js_outlinks,
                p.meta_robots,
                p.rendered_meta_robots or p.meta_robots,
            ])
        _w(self._p("javascript_all.csv"), headers, rows)

    # ===== 26. custom_extraction_all.csv =====
    def export_custom_extraction(self, result: CrawlResult):
        headers = ["Address", "Status Code", "Status"]
        # Dynamically add columns based on extraction names
        extraction_names = set()
        for p in result.pages:
            for ce in p.custom_extractions:
                extraction_names.add(ce.name)
        extraction_names = sorted(extraction_names)
        headers.extend(extraction_names)

        rows = []
        for p in result.pages:
            ext_map = {ce.name: ce.value for ce in p.custom_extractions}
            row = [p.url, p.status_code, p.status_text]
            for name in extraction_names:
                row.append(ext_map.get(name, ''))
            rows.append(row)
        _w(self._p("custom_extraction_all.csv"), headers, rows)

    # ===== 27. custom_search_all.csv =====
    def export_custom_search(self, result: CrawlResult):
        headers = ["Address", "Content Type", "Status Code", "Status"]
        search_names = set()
        for p in result.pages:
            for name in p.custom_search_matches:
                search_names.add(name)
        search_names = sorted(search_names)
        headers.extend(search_names)

        rows = []
        for p in result.pages:
            row = [p.url, p.content_type, p.status_code, p.status_text]
            for name in search_names:
                row.append("Contains" if p.custom_search_matches.get(name) else "Does Not Contain")
            rows.append(row)
        _w(self._p("custom_search_all.csv"), headers, rows)
