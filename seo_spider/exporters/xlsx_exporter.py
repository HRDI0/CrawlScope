"""
XLSX Exporter — Full Screaming Frog-compatible Excel export.
Generates multi-sheet Excel workbook matching all SF tabs.
"""
import os
import logging
from typing import Optional

from seo_spider.core.models import CrawlResult

logger = logging.getLogger("seo_spider.export.xlsx")


class XLSXExporter:
    """Export crawl results to a multi-sheet Excel file."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export(self, result: CrawlResult, filename: str = "crawl_report.xlsx"):
        """Export full crawl data to Excel with all SF-compatible tabs."""
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas required for XLSX export: pip install pandas openpyxl")
            return

        path = os.path.join(self.output_dir, filename)

        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            self._write_internal(result, writer)
            self._write_external(result, writer)
            self._write_images(result, writer)
            self._write_css(result, writer)
            self._write_javascript_resources(result, writer)
            self._write_hreflang(result, writer)
            self._write_structured_data(result, writer)
            self._write_response_codes(result, writer)
            self._write_security(result, writer)
            self._write_content(result, writer)
            self._write_links(result, writer)
            self._write_canonicals(result, writer)
            self._write_directives(result, writer)
            self._write_h1(result, writer)
            self._write_h2(result, writer)
            self._write_meta_keywords(result, writer)
            self._write_pagination(result, writer)
            self._write_url(result, writer)
            self._write_page_titles_dup(result, writer)
            self._write_meta_desc_dup(result, writer)
            self._write_javascript_rendering(result, writer)
            self._write_redirects(result, writer)
            self._write_inlinks(result, writer)
            self._write_issues(result, writer)
            self._write_overview(result, writer)
            self._write_subdomains(result, writer)

        logger.info(f"XLSX export complete -> {path}")

    # ===== 1. Internal (63 columns) =====
    def _write_internal(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            h1_1 = p.headings.h1[0] if p.headings.h1 else ''
            h2_1 = p.headings.h2[0] if p.headings.h2 else ''
            h2_2 = p.headings.h2[1] if len(p.headings.h2) > 1 else ''
            rows.append({
                "Address": p.url,
                "Content Type": p.content_type,
                "Status Code": p.status_code,
                "Status": p.status_text,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                "Title 1": p.title,
                "Title 1 Length": p.title_length,
                "Title 1 Pixel Width": p.title_pixel_width,
                "Meta Description 1": p.meta_description,
                "Meta Description 1 Length": p.meta_description_length,
                "Meta Description 1 Pixel Width": p.meta_description_pixel_width,
                "Meta Keywords 1": p.meta_keywords,
                "Meta Keywords 1 Length": p.meta_keywords_length,
                "H1-1": h1_1,
                "H1-1 Length": len(h1_1),
                "H2-1": h2_1,
                "H2-1 Length": len(h2_1),
                "H2-2": h2_2,
                "H2-2 Length": len(h2_2),
                "Meta Robots 1": p.meta_robots,
                "X-Robots-Tag 1": p.x_robots_tag,
                "Meta Refresh 1": p.meta_refresh,
                "Canonical Link Element 1": p.canonical_url,
                'rel="next" 1': p.rel_next,
                'rel="prev" 1': p.rel_prev,
                'HTTP rel="next" 1': p.http_rel_next,
                'HTTP rel="prev" 1': p.http_rel_prev,
                "Size (bytes)": p.page_speed.html_size,
                "Transferred (bytes)": p.transferred_bytes,
                "Word Count": p.word_count,
                "Sentence Count": p.sentence_count,
                "Average Words Per Sentence": p.avg_words_per_sentence,
                "Flesch Reading Ease Score": p.flesch_reading_ease,
                "Readability": p.readability,
                "Text Ratio": p.text_ratio,
                "Crawl Depth": p.crawl_depth,
                "Folder Depth": p.folder_depth,
                "Link Score": p.link_score,
                "Inlinks": p.inlinks_count,
                "Unique Inlinks": p.unique_inlinks,
                "Unique JS Inlinks": p.unique_js_inlinks,
                "% of Total": p.pct_of_total,
                "Outlinks": p.outlinks_count,
                "Unique Outlinks": p.unique_outlinks,
                "Unique JS Outlinks": p.unique_js_outlinks,
                "External Outlinks": p.external_outlinks,
                "Unique External Outlinks": p.unique_external_outlinks,
                "Unique External JS Outlinks": p.unique_external_js_outlinks,
                "Closest Similarity Match": p.closest_similarity_match,
                "No. Near Duplicates": p.near_duplicate_count,
                "Hash": p.content_hash,
                "Response Time": round(p.response_time, 3),
                "Last Modified": p.last_modified,
                "Redirect URL": p.final_url if p.is_redirect else '',
                "Redirect Type": p.redirect_type,
                "Cookies": p.cookies,
                "HTTP Version": p.http_version,
                "URL Encoded Address": p.url_encoded_address,
                "Crawl Timestamp": p.crawl_timestamp,
                "HTML Lang": p.html_lang,
                "Content Language": p.content_language,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Internal", index=False)

    # ===== 2. External =====
    def _write_external(self, result, writer):
        import pandas as pd
        ext_inlinks = {}
        for p in result.pages:
            for link in p.external_links:
                ext_inlinks.setdefault(link.target_url, []).append(p.url)
        rows = [{"Address": url, "Content Type": '', "Status Code": '', "Status": '',
                 "Crawl Depth": '', "Inlinks": len(sources)}
                for url, sources in ext_inlinks.items()]
        pd.DataFrame(rows).to_excel(writer, sheet_name="External", index=False)

    # ===== 3. Images =====
    def _write_images(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            for img in p.images:
                dim = f"{img.width}x{img.height}" if img.width and img.height else ""
                rows.append({
                    "Address": img.src, "Content Type": "image",
                    "Size (bytes)": img.file_size, "IMG Inlinks": "",
                    "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                    "Indexability Status": p.indexability_status,
                    "Dimensions": dim, "Alt Text": img.alt_text,
                    "Missing Alt Attribute": img.is_missing_alt_attribute,
                    "Source Page": p.url,
                })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Images", index=False)

    # ===== 4. CSS =====
    def _write_css(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            for css in p.css_resources:
                rows.append({"URL": css.url, "Status Code": css.status_code,
                             "Content Type": css.content_type, "File Size": css.file_size,
                             "Source Page": p.url})
        pd.DataFrame(rows).to_excel(writer, sheet_name="CSS", index=False)

    # ===== 5. JavaScript Resources =====
    def _write_javascript_resources(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            for js in p.js_resources:
                rows.append({"URL": js.url, "Status Code": js.status_code,
                             "Content Type": js.content_type, "File Size": js.file_size,
                             "Source Page": p.url})
        pd.DataFrame(rows).to_excel(writer, sheet_name="JavaScript Res", index=False)

    # ===== 6. Hreflang =====
    def _write_hreflang(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            if p.hreflang_annotations:
                ann = p.hreflang_annotations[0]
                rows.append({
                    "Address": p.url, "Title 1": p.title,
                    "Occurrences": len(p.hreflang_annotations),
                    "HTML hreflang 1": f"{ann.language}-{ann.region}" if ann.region else ann.language,
                    "HTML hreflang 1 URL": ann.target_url,
                    "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                    "Indexability Status": p.indexability_status,
                })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Hreflang", index=False)

    # ===== 7. Structured Data =====
    def _write_structured_data(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            if p.structured_data:
                types = [sd.schema_type for sd in p.structured_data]
                errors = sum(len(sd.validation_errors) for sd in p.structured_data)
                warnings = sum(len(sd.validation_warnings) for sd in p.structured_data)
                rows.append({
                    "Address": p.url, "Errors": errors, "Warnings": warnings,
                    "Total Types": len(types), "Unique Types": len(set(types)),
                    "Type-1": types[0] if types else '',
                    "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                    "Indexability Status": p.indexability_status,
                })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Structured Data", index=False)

    # ===== 8. Response Codes =====
    def _write_response_codes(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url, "Content Type": p.content_type,
                "Status Code": p.status_code, "Status": p.status_text,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                "Inlinks": p.inlinks_count,
                "Response Time": round(p.response_time, 3),
                "Redirect URL": p.final_url if p.is_redirect else '',
                "Redirect Type": p.redirect_type,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Response Codes", index=False)

    # ===== 9. Security =====
    def _write_security(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            s = p.security
            rows.append({
                "Address": p.url, "Content Type": p.content_type,
                "Status Code": p.status_code, "Status": p.status_text,
                "HTTPS": s.is_https, "Mixed Content": s.has_mixed_content,
                "HSTS": s.hsts_enabled,
                "X-Frame-Options": s.x_frame_options,
                "X-Content-Type-Options": s.x_content_type_options,
                "Referrer-Policy": s.referrer_policy,
                "Content-Security-Policy": s.content_security_policy,
                "Permissions-Policy": s.permissions_policy,
                "HTTP Version": p.http_version,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Security", index=False)

    # ===== 10. Content =====
    def _write_content(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url, "Word Count": p.word_count,
                "Sentence Count": p.sentence_count,
                "Average Words Per Sentence": p.avg_words_per_sentence,
                "Flesch Reading Ease Score": p.flesch_reading_ease,
                "Readability": p.readability,
                "Closest Similarity Match": p.closest_similarity_match,
                "No. Near Duplicates": p.near_duplicate_count,
                "Language": p.detected_language or p.html_lang,
                "Hash": p.content_hash, "Text Ratio": p.text_ratio,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Content", index=False)

    # ===== 11. Links =====
    def _write_links(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                "Crawl Depth": p.crawl_depth, "Link Score": p.link_score,
                "Inlinks": p.inlinks_count, "Unique Inlinks": p.unique_inlinks,
                "Unique JS Inlinks": p.unique_js_inlinks, "% of Total": p.pct_of_total,
                "Outlinks": p.outlinks_count, "Unique Outlinks": p.unique_outlinks,
                "Unique JS Outlinks": p.unique_js_outlinks,
                "External Outlinks": p.external_outlinks,
                "Unique External Outlinks": p.unique_external_outlinks,
                "Unique External JS Outlinks": p.unique_external_js_outlinks,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Links", index=False)

    # ===== 12. Canonicals =====
    def _write_canonicals(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url, "Occurrences": 1,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                "Canonical Link Element 1": p.canonical_url,
                "HTTP Canonical": p.http_canonical,
                "Meta Robots 1": p.meta_robots, "X-Robots-Tag 1": p.x_robots_tag,
                'rel="next" 1': p.rel_next, 'rel="prev" 1': p.rel_prev,
                'HTTP rel="next" 1': p.http_rel_next, 'HTTP rel="prev" 1': p.http_rel_prev,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Canonicals", index=False)

    # ===== 13. Directives =====
    def _write_directives(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url, "Occurrences": 1,
                "Meta Robots 1": p.meta_robots, "X-Robots-Tag 1": p.x_robots_tag,
                "Meta Refresh 1": p.meta_refresh,
                "Canonical Link Element 1": p.canonical_url,
                "HTTP Canonical": p.http_canonical,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Directives", index=False)

    # ===== 14. H1 =====
    def _write_h1(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            h1 = p.headings.h1[0] if p.headings.h1 else ''
            rows.append({
                "Address": p.url, "Occurrences": len(p.headings.h1),
                "H1-1": h1, "H1-1 Length": len(h1),
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="H1", index=False)

    # ===== 15. H2 =====
    def _write_h2(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            h2_1 = p.headings.h2[0] if p.headings.h2 else ''
            h2_2 = p.headings.h2[1] if len(p.headings.h2) > 1 else ''
            rows.append({
                "Address": p.url, "Occurrences": len(p.headings.h2),
                "H2-1": h2_1, "H2-1 Length": len(h2_1),
                "H2-2": h2_2, "H2-2 Length": len(h2_2),
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="H2", index=False)

    # ===== 16. Meta Keywords =====
    def _write_meta_keywords(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url,
                "Occurrences": 1 if p.meta_keywords else 0,
                "Meta Keywords 1": p.meta_keywords,
                "Meta Keywords 1 Length": p.meta_keywords_length,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Meta Keywords", index=False)

    # ===== 17. Pagination =====
    def _write_pagination(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                'rel="next" 1': p.rel_next, 'rel="prev" 1': p.rel_prev,
                'HTTP rel="next" 1': p.http_rel_next, 'HTTP rel="prev" 1': p.http_rel_prev,
                "Canonical Link Element 1": p.canonical_url,
                "HTTP Canonical": p.http_canonical,
                "Meta Robots 1": p.meta_robots, "X-Robots-Tag 1": p.x_robots_tag,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Pagination", index=False)

    # ===== 18. URL =====
    def _write_url(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            rows.append({
                "Address": p.url, "Content Type": p.content_type,
                "Status Code": p.status_code, "Status": p.status_text,
                "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                "Indexability Status": p.indexability_status,
                "Hash": p.content_hash, "Length": p.url_length,
                "Canonical Link Element 1": p.canonical_url,
                "URL Encoded Address": p.url_encoded_address,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="URL", index=False)

    # ===== 19. Page Titles Duplicate =====
    def _write_page_titles_dup(self, result, writer):
        import pandas as pd
        title_map = {}
        for p in result.pages:
            if p.title:
                title_map.setdefault(p.title, []).append(p)
        rows = []
        for title, pages in title_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append({
                        "Address": p.url, "Occurrences": len(pages),
                        "Title 1": p.title, "Title 1 Length": p.title_length,
                        "Title 1 Pixel Width": p.title_pixel_width,
                        "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                        "Indexability Status": p.indexability_status,
                    })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Titles Duplicate", index=False)

    # ===== 20. Meta Description Duplicate =====
    def _write_meta_desc_dup(self, result, writer):
        import pandas as pd
        desc_map = {}
        for p in result.pages:
            if p.meta_description:
                desc_map.setdefault(p.meta_description, []).append(p)
        rows = []
        for desc, pages in desc_map.items():
            if len(pages) > 1:
                for p in pages:
                    rows.append({
                        "Address": p.url, "Occurrences": len(pages),
                        "Meta Description 1": p.meta_description,
                        "Meta Description 1 Length": p.meta_description_length,
                        "Meta Description 1 Pixel Width": p.meta_description_pixel_width,
                        "Indexability": "Indexable" if p.is_indexable else "Non-Indexable",
                        "Indexability Status": p.indexability_status,
                    })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Meta Desc Duplicate", index=False)

    # ===== 21. JavaScript Rendering =====
    def _write_javascript_rendering(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            html_wc = p.word_count - p.word_count_change if p.word_count_change else p.word_count
            rows.append({
                "Address": p.url, "Status Code": p.status_code, "Status": p.status_text,
                "HTML Word Count": html_wc,
                "Rendered HTML Word Count": p.rendered_word_count or p.word_count,
                "Word Count Change": p.word_count_change,
                "JS Word Count %": p.js_word_count_pct,
                "HTML Title": p.title,
                "Rendered HTML Title": p.rendered_title or p.title,
                "HTML H1": p.headings.h1[0] if p.headings.h1 else '',
                "Rendered HTML H1": p.rendered_h1 or (p.headings.h1[0] if p.headings.h1 else ''),
                "HTML Meta Description": p.meta_description,
                "Rendered HTML Meta Description": p.rendered_meta_description or p.meta_description,
                "HTML Canonical": p.canonical_url,
                "Rendered HTML Canonical": p.rendered_canonical or p.canonical_url,
                "Unique Inlinks": p.unique_inlinks, "Unique JS Inlinks": p.unique_js_inlinks,
                "Unique Outlinks": p.unique_outlinks, "Unique JS Outlinks": p.unique_js_outlinks,
                "Unique External Outlinks": p.unique_external_outlinks,
                "Unique External JS Outlinks": p.unique_external_js_outlinks,
                "HTML Meta Robots 1": p.meta_robots,
                "Rendered HTML Meta Robots 1": p.rendered_meta_robots or p.meta_robots,
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="JS Rendering", index=False)

    # ===== 22. Redirects =====
    def _write_redirects(self, result, writer):
        import pandas as pd
        rows = []
        for p in result.pages:
            if p.is_redirect:
                rows.append({
                    "Source URL": p.url, "Redirect Type": p.redirect_type,
                    "Redirect Chain": ' -> '.join(p.redirect_chain),
                    "Final URL": p.final_url, "Chain Length": len(p.redirect_chain),
                })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Redirects", index=False)

    # ===== 23. Inlinks =====
    def _write_inlinks(self, result, writer):
        import pandas as pd
        rows = []
        for target, sources in sorted(result.inlink_map.items(), key=lambda x: -len(x[1])):
            rows.append({
                "Target URL": target, "Inlink Count": len(sources),
                "Source URLs (sample)": '; '.join(sources[:10]),
            })
        pd.DataFrame(rows).to_excel(writer, sheet_name="Inlinks", index=False)

    # ===== 24. Issues =====
    def _write_issues(self, result, writer):
        import pandas as pd
        try:
            from ..analyzers.issue_detector import IssueDetector
            all_issues = IssueDetector().detect_crawl_issues(result)
            rows = []
            for url, issues in all_issues.items():
                for i in issues:
                    rows.append({
                        "URL": url, "Category": i.category,
                        "Severity": i.severity, "Issue Type": i.issue_type,
                        "Description": i.description, "Current Value": i.current_value,
                        "Recommendation": i.recommendation,
                    })
            pd.DataFrame(rows).to_excel(writer, sheet_name="Issues", index=False)
        except Exception as e:
            logger.warning(f"Could not generate Issues sheet: {e}")
            pd.DataFrame().to_excel(writer, sheet_name="Issues", index=False)

    # ===== 25. Overview =====
    def _write_overview(self, result, writer):
        import pandas as pd
        overview = {
            "Metric": [
                "Domain", "Total URLs Crawled", "Internal URLs", "External URLs",
                "Subdomains Found", "Crawl Start", "Crawl End",
            ],
            "Value": [
                result.domain, result.total_urls_crawled,
                result.total_internal, result.total_external,
                len(result.subdomains_found),
                result.crawl_start_time, result.crawl_end_time,
            ],
        }
        for issue, count in sorted(result.issues.items(), key=lambda x: -x[1]):
            overview["Metric"].append(issue)
            overview["Value"].append(count)
        pd.DataFrame(overview).to_excel(writer, sheet_name="Overview", index=False)

    # ===== 26. Subdomains =====
    def _write_subdomains(self, result, writer):
        import pandas as pd
        rows = [{"Subdomain": s} for s in result.subdomains_found]
        pd.DataFrame(rows).to_excel(writer, sheet_name="Subdomains", index=False)
