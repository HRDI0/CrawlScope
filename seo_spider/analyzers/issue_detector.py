"""
SEO Issue Detector.
Mirrors Screaming Frog's 300+ issue detection covering all SEO categories.
"""
import logging
from typing import Optional
from dataclasses import dataclass, field

from seo_spider.core.models import PageData, CrawlResult

logger = logging.getLogger("seo_spider.issues")


@dataclass
class SEOIssue:
    """Represents a detected SEO issue."""
    category: str = ""        # Title, Meta Description, H1, Links, Images, etc.
    severity: str = "warning" # error, warning, info, opportunity
    issue_type: str = ""      # e.g., "Missing Title", "Title Too Long"
    description: str = ""
    url: str = ""
    current_value: str = ""
    recommendation: str = ""
    evidence: str = ""        # concrete proof of the issue (e.g., actual URL, actual value)
    source_table: str = ""    # which CSV this issue relates to (e.g., "internal_all.csv")
    counting_unit: str = ""   # what's being counted: "page", "image", "link", etc.


class IssueDetector:
    """
    Detect 300+ SEO issues across all categories.
    Mirrors Screaming Frog's Overview tab issue detection.
    """

    def detect_page_issues(self, page: PageData, pages_by_url: dict = None) -> list[SEOIssue]:
        """Detect all issues for a single page.

        Args:
            page: PageData object to check
            pages_by_url: Optional dict mapping URLs to PageData for cross-checks
        """
        issues = []

        if page.status_code != 200:
            issues.extend(self._check_status_issues(page))
            return issues  # Skip content checks for non-200 pages

        issues.extend(self._check_title_issues(page))
        issues.extend(self._check_meta_description_issues(page))
        issues.extend(self._check_h1_issues(page))
        issues.extend(self._check_heading_issues(page))
        issues.extend(self._check_content_issues(page))
        issues.extend(self._check_image_issues(page))
        issues.extend(self._check_link_issues(page))
        issues.extend(self._check_canonical_issues(page, pages_by_url))
        issues.extend(self._check_hreflang_issues(page))
        issues.extend(self._check_indexability_issues(page))
        issues.extend(self._check_security_issues(page))
        issues.extend(self._check_structured_data_issues(page))
        issues.extend(self._check_og_twitter_issues(page))
        issues.extend(self._check_performance_issues(page))
        issues.extend(self._check_pagination_issues(page))

        return issues

    def detect_crawl_issues(self, result: CrawlResult, pages_by_url: dict = None) -> dict[str, list[SEOIssue]]:
        """Detect all issues across the entire crawl.

        Args:
            result: CrawlResult object containing all pages
            pages_by_url: Optional dict mapping URLs to PageData for cross-checking canonicals
        """
        all_issues: dict[str, list[SEOIssue]] = {}

        # Build pages_by_url if not provided
        if pages_by_url is None:
            pages_by_url = {page.url: page for page in result.pages}

        # Per-page checks
        for page in result.pages:
            page_issues = self.detect_page_issues(page, pages_by_url)
            if page_issues:
                all_issues[page.url] = page_issues

        # Cross-page duplicate checks for titles, meta descriptions, and h1s
        cross_page_issues = self._check_cross_page_duplicates(result.pages)
        for url, issues in cross_page_issues.items():
            if url in all_issues:
                all_issues[url].extend(issues)
            else:
                all_issues[url] = issues

        # Aggregate issue counts
        issue_counts = {}
        for url, issues in all_issues.items():
            for issue in issues:
                key = f"{issue.category}: {issue.issue_type}"
                issue_counts[key] = issue_counts.get(key, 0) + 1

        result.issues.update(issue_counts)
        return all_issues

    def _check_status_issues(self, page: PageData) -> list[SEOIssue]:
        """Check HTTP status code issues."""
        issues = []
        sc = page.status_code

        if sc == 0:
            issues.append(SEOIssue(
                category="Response Codes", severity="error",
                issue_type="Connection Error", url=page.url,
                description=page.crawl_error or "Failed to connect",
                evidence=page.url,
                source_table="response_codes_all.csv",
                counting_unit="page",
            ))
        elif 300 <= sc < 400:
            issues.append(SEOIssue(
                category="Response Codes", severity="warning",
                issue_type=f"Redirect ({sc})", url=page.url,
                description=f"Page redirects with status {sc}",
                current_value=f"Redirects to: {page.final_url}",
                evidence=page.final_url or page.url,
                source_table="redirects.csv",
                counting_unit="page",
            ))
        elif sc == 404:
            issues.append(SEOIssue(
                category="Response Codes", severity="error",
                issue_type="Not Found (404)", url=page.url,
                evidence=page.url,
                source_table="response_codes_all.csv",
                counting_unit="page",
            ))
        elif sc == 410:
            issues.append(SEOIssue(
                category="Response Codes", severity="warning",
                issue_type="Gone (410)", url=page.url,
                evidence=page.url,
                source_table="response_codes_all.csv",
                counting_unit="page",
            ))
        elif 400 <= sc < 500:
            issues.append(SEOIssue(
                category="Response Codes", severity="error",
                issue_type=f"Client Error ({sc})", url=page.url,
                evidence=page.url,
                source_table="response_codes_all.csv",
                counting_unit="page",
            ))
        elif 500 <= sc < 600:
            issues.append(SEOIssue(
                category="Response Codes", severity="error",
                issue_type=f"Server Error ({sc})", url=page.url,
                evidence=page.url,
                source_table="response_codes_all.csv",
                counting_unit="page",
            ))

        # Redirect chain
        if len(page.redirect_chain) > 1:
            issues.append(SEOIssue(
                category="Response Codes", severity="warning",
                issue_type="Redirect Chain",
                url=page.url,
                description=f"Redirect chain with {len(page.redirect_chain)} hops",
                current_value=" -> ".join(page.redirect_chain[:5]),
                evidence=" -> ".join(page.redirect_chain),
                source_table="redirects.csv",
                counting_unit="page",
            ))

        # Redirect loop
        if page.crawl_error and "loop" in page.crawl_error.lower():
            issues.append(SEOIssue(
                category="Response Codes", severity="error",
                issue_type="Redirect Loop",
                url=page.url,
                description=page.crawl_error,
                evidence=page.url,
                source_table="redirects.csv",
                counting_unit="page",
            ))

        return issues

    def _check_title_issues(self, page: PageData) -> list[SEOIssue]:
        """Check page title issues."""
        issues = []

        if not page.title:
            issues.append(SEOIssue(
                category="Page Titles", severity="error",
                issue_type="Missing", url=page.url,
                recommendation="Add a unique, descriptive title tag",
                evidence=page.url,
                source_table="internal_all.csv",
                counting_unit="page",
            ))
        else:
            if page.title_length < 30:
                issues.append(SEOIssue(
                    category="Page Titles", severity="warning",
                    issue_type="Below 30 Characters", url=page.url,
                    current_value=f"{page.title_length} chars: {page.title[:50]}",
                    recommendation="Title should be 30-60 characters",
                    evidence=page.title,
                    source_table="internal_all.csv",
                    counting_unit="page",
                ))
            elif page.title_length > 60:
                issues.append(SEOIssue(
                    category="Page Titles", severity="warning",
                    issue_type="Over 60 Characters", url=page.url,
                    current_value=f"{page.title_length} chars",
                    recommendation="Title may be truncated in SERPs",
                    evidence=page.title,
                    source_table="internal_all.csv",
                    counting_unit="page",
                ))
            if page.title_pixel_width > 580:
                issues.append(SEOIssue(
                    category="Page Titles", severity="warning",
                    issue_type="Over 580 Pixels", url=page.url,
                    current_value=f"{page.title_pixel_width}px estimated",
                    evidence=page.title,
                    source_table="internal_all.csv",
                    counting_unit="page",
                ))

        return issues

    def _check_meta_description_issues(self, page: PageData) -> list[SEOIssue]:
        """Check meta description issues."""
        issues = []

        if not page.meta_description:
            issues.append(SEOIssue(
                category="Meta Description", severity="warning",
                issue_type="Missing", url=page.url,
                recommendation="Add a unique meta description (120-160 chars)",
                evidence=page.url,
                source_table="internal_all.csv",
                counting_unit="page",
            ))
        else:
            if page.meta_description_length < 70:
                issues.append(SEOIssue(
                    category="Meta Description", severity="info",
                    issue_type="Below 70 Characters", url=page.url,
                    current_value=f"{page.meta_description_length} chars",
                    evidence=page.meta_description,
                    source_table="internal_all.csv",
                    counting_unit="page",
                ))
            elif page.meta_description_length > 160:
                issues.append(SEOIssue(
                    category="Meta Description", severity="warning",
                    issue_type="Over 160 Characters", url=page.url,
                    current_value=f"{page.meta_description_length} chars",
                    recommendation="Description may be truncated in SERPs",
                    evidence=page.meta_description,
                    source_table="internal_all.csv",
                    counting_unit="page",
                ))

        return issues

    def _check_h1_issues(self, page: PageData) -> list[SEOIssue]:
        """Check H1 heading issues."""
        issues = []

        if page.headings.missing_h1:
            issues.append(SEOIssue(
                category="H1", severity="warning",
                issue_type="Missing", url=page.url,
                recommendation="Add a single H1 heading to the page",
                evidence=page.url,
                source_table="h1_all.csv",
                counting_unit="page",
            ))
        elif page.headings.multiple_h1:
            h1_texts = " | ".join(page.headings.h1)
            issues.append(SEOIssue(
                category="H1", severity="warning",
                issue_type="Multiple", url=page.url,
                current_value=f"{page.headings.h1_count} H1 tags found",
                recommendation="Use only one H1 per page",
                evidence=h1_texts,
                source_table="h1_all.csv",
                counting_unit="page",
            ))

        # Check for duplicate h1s
        if len(page.headings.h1) != len(set(page.headings.h1)):
            duplicate_h1 = [h for h in page.headings.h1 if page.headings.h1.count(h) > 1][0]
            issues.append(SEOIssue(
                category="H1", severity="warning",
                issue_type="Duplicate", url=page.url,
                current_value=f"Duplicate H1 found",
                evidence=duplicate_h1,
                source_table="h1_all.csv",
                counting_unit="page",
            ))

        for h1 in page.headings.h1:
            if len(h1) > 70:
                issues.append(SEOIssue(
                    category="H1", severity="info",
                    issue_type="Over 70 Characters", url=page.url,
                    current_value=f"{len(h1)} chars",
                    evidence=h1,
                    source_table="h1_all.csv",
                    counting_unit="page",
                ))

        return issues

    def _check_heading_issues(self, page: PageData) -> list[SEOIssue]:
        """Check heading hierarchy issues."""
        issues = []

        # Check if H2 exists but no H1
        if not page.headings.h1 and page.headings.h2:
            issues.append(SEOIssue(
                category="Headings", severity="warning",
                issue_type="H2 Without H1", url=page.url,
            ))

        # Check heading order (no H3 before H2, etc.)
        levels_found = []
        for level in range(1, 7):
            if getattr(page.headings, f'h{level}'):
                levels_found.append(level)
        for i in range(1, len(levels_found)):
            if levels_found[i] - levels_found[i-1] > 1:
                issues.append(SEOIssue(
                    category="Headings", severity="info",
                    issue_type="Non-Sequential Heading Order", url=page.url,
                    description=f"Jumps from H{levels_found[i-1]} to H{levels_found[i]}",
                ))

        return issues

    def _check_content_issues(self, page: PageData) -> list[SEOIssue]:
        """Check content-related issues."""
        issues = []

        if page.word_count < 100:
            issues.append(SEOIssue(
                category="Content", severity="warning",
                issue_type="Low Content (Under 100 Words)", url=page.url,
                current_value=f"{page.word_count} words",
                recommendation="Add more substantial content",
            ))
        elif page.word_count < 200:
            issues.append(SEOIssue(
                category="Content", severity="info",
                issue_type="Thin Content (Under 200 Words)", url=page.url,
                current_value=f"{page.word_count} words",
            ))

        if page.text_ratio < 10:
            issues.append(SEOIssue(
                category="Content", severity="info",
                issue_type="Low Text Ratio", url=page.url,
                current_value=f"{page.text_ratio}%",
                description="Text to HTML ratio below 10%",
            ))

        return issues

    def _check_image_issues(self, page: PageData) -> list[SEOIssue]:
        """Check image-related issues."""
        issues = []

        for img in page.images:
            if img.is_missing_alt_attribute:
                issues.append(SEOIssue(
                    category="Images", severity="warning",
                    issue_type="Missing Alt Attribute", url=page.url,
                    current_value=img.src[:100],
                    evidence=img.src,
                    source_table="images_all.csv",
                    counting_unit="image",
                ))
            elif img.is_missing_alt:
                issues.append(SEOIssue(
                    category="Images", severity="info",
                    issue_type="Missing Alt Text", url=page.url,
                    current_value=img.src[:100],
                    evidence=img.src,
                    source_table="images_all.csv",
                    counting_unit="image",
                ))
            if img.alt_over_100:
                issues.append(SEOIssue(
                    category="Images", severity="info",
                    issue_type="Alt Text Over 100 Characters", url=page.url,
                    current_value=f"{len(img.alt_text)} chars",
                    evidence=img.alt_text,
                    source_table="images_all.csv",
                    counting_unit="image",
                ))

        return issues

    def _check_link_issues(self, page: PageData) -> list[SEOIssue]:
        """Check link-related issues."""
        issues = []

        # Check for broken internal links
        for link in page.internal_links:
            if link.status_code == 404:
                issues.append(SEOIssue(
                    category="Links", severity="error",
                    issue_type="Broken Internal Link (404)", url=page.url,
                    current_value=link.target_url[:100],
                ))
            elif link.status_code >= 500:
                issues.append(SEOIssue(
                    category="Links", severity="error",
                    issue_type="Internal Link Server Error", url=page.url,
                    current_value=f"{link.target_url[:80]} ({link.status_code})",
                ))

        # Check for broken external links
        for link in page.external_links:
            if link.status_code == 404:
                issues.append(SEOIssue(
                    category="Links", severity="warning",
                    issue_type="Broken External Link (404)", url=page.url,
                    current_value=link.target_url[:100],
                ))

        # Orphan pages (no inlinks)
        if page.inlinks_count == 0 and page.crawl_depth > 0:
            issues.append(SEOIssue(
                category="Links", severity="warning",
                issue_type="Orphan Page", url=page.url,
                description="No internal pages link to this URL",
            ))

        return issues

    def _check_canonical_issues(self, page: PageData, pages_by_url: dict = None) -> list[SEOIssue]:
        """Check canonical-related issues.

        Distinguishes:
        - Canonical Missing (no canonical tag)
        - Self-Referencing Canonical (canonical points to itself)
        - Non-Self Canonical (canonical points elsewhere)
        - Canonical to Redirect (canonical points to a URL in redirect list)
        - Canonical to Non-200 (canonical target has non-200 status)
        """
        issues = []

        if not page.canonical_url:
            issues.append(SEOIssue(
                category="Canonicals", severity="info",
                issue_type="Canonical Missing", url=page.url,
                evidence=page.url,
                source_table="canonicals_all.csv",
                counting_unit="page",
            ))
        else:
            # Check if self-referencing
            if page.canonical_url == page.url:
                issues.append(SEOIssue(
                    category="Canonicals", severity="info",
                    issue_type="Self-Referencing Canonical", url=page.url,
                    current_value=page.canonical_url[:100],
                    evidence=page.canonical_url,
                    source_table="canonicals_all.csv",
                    counting_unit="page",
                ))
            else:
                # Check if canonical points to a redirect
                if pages_by_url and page.canonical_url in pages_by_url:
                    canonical_page = pages_by_url[page.canonical_url]
                    if 300 <= canonical_page.status_code < 400:
                        issues.append(SEOIssue(
                            category="Canonicals", severity="warning",
                            issue_type="Canonical to Redirect", url=page.url,
                            current_value=page.canonical_url[:100],
                            evidence=page.canonical_url,
                            source_table="canonicals_all.csv",
                            counting_unit="page",
                        ))
                    elif canonical_page.status_code != 200:
                        issues.append(SEOIssue(
                            category="Canonicals", severity="warning",
                            issue_type="Canonical to Non-200", url=page.url,
                            current_value=f"{page.canonical_url[:100]} (status: {canonical_page.status_code})",
                            evidence=page.canonical_url,
                            source_table="canonicals_all.csv",
                            counting_unit="page",
                        ))
                    else:
                        # Non-self canonical to a valid page
                        issues.append(SEOIssue(
                            category="Canonicals", severity="warning",
                            issue_type="Non-Self Canonical", url=page.url,
                            current_value=page.canonical_url[:100],
                            evidence=page.canonical_url,
                            source_table="canonicals_all.csv",
                            counting_unit="page",
                        ))
                else:
                    # Non-self canonical, target not in crawl
                    issues.append(SEOIssue(
                        category="Canonicals", severity="warning",
                        issue_type="Non-Self Canonical", url=page.url,
                        current_value=page.canonical_url[:100],
                        evidence=page.canonical_url,
                        source_table="canonicals_all.csv",
                        counting_unit="page",
                    ))

        return issues

    def _check_hreflang_issues(self, page: PageData) -> list[SEOIssue]:
        """Check hreflang issues."""
        issues = []

        for ann in page.hreflang_annotations:
            if not ann.is_valid:
                for issue_text in ann.issues:
                    issues.append(SEOIssue(
                        category="Hreflang", severity="warning",
                        issue_type=issue_text, url=page.url,
                        current_value=f"{ann.language}-{ann.region}: {ann.target_url[:50]}",
                    ))
            if not ann.has_return_tag:
                issues.append(SEOIssue(
                    category="Hreflang", severity="warning",
                    issue_type="Missing Return Tag", url=page.url,
                    current_value=f"Target: {ann.target_url[:80]}",
                ))

        return issues

    def _check_indexability_issues(self, page: PageData) -> list[SEOIssue]:
        """Check indexability issues."""
        issues = []

        if not page.is_indexable and page.status_code == 200:
            issues.append(SEOIssue(
                category="Indexability", severity="warning",
                issue_type="Non-Indexable", url=page.url,
                current_value=page.indexability_status,
            ))

        if page.meta_robots and 'nofollow' in page.meta_robots.lower():
            issues.append(SEOIssue(
                category="Indexability", severity="info",
                issue_type="Nofollow in Meta Robots", url=page.url,
            ))

        return issues

    def _check_security_issues(self, page: PageData) -> list[SEOIssue]:
        """Check security issues."""
        issues = []

        if not page.security.is_https:
            issues.append(SEOIssue(
                category="Security", severity="warning",
                issue_type="HTTP (Not HTTPS)", url=page.url,
            ))

        if page.security.has_mixed_content:
            issues.append(SEOIssue(
                category="Security", severity="warning",
                issue_type="Mixed Content", url=page.url,
                current_value=f"{len(page.security.mixed_content_urls)} insecure resources",
            ))

        if page.security.is_https and not page.security.hsts_enabled:
            issues.append(SEOIssue(
                category="Security", severity="info",
                issue_type="Missing HSTS Header", url=page.url,
            ))

        if not page.security.x_content_type_options:
            issues.append(SEOIssue(
                category="Security", severity="info",
                issue_type="Missing X-Content-Type-Options", url=page.url,
            ))

        return issues

    def _check_structured_data_issues(self, page: PageData) -> list[SEOIssue]:
        """Check structured data issues."""
        issues = []

        if not page.structured_data:
            issues.append(SEOIssue(
                category="Structured Data", severity="info",
                issue_type="No Structured Data", url=page.url,
                recommendation="Consider adding JSON-LD structured data",
                evidence=page.url,
                source_table="structured_data_all.csv",
                counting_unit="page",
            ))
        else:
            for sd in page.structured_data:
                sd_type = getattr(sd, 'schema_type', 'Unknown')
                if not sd.is_valid:
                    for err in sd.validation_errors:
                        issues.append(SEOIssue(
                            category="Structured Data", severity="error",
                            issue_type=f"Validation Error: {err}", url=page.url,
                            evidence=sd_type,
                            source_table="structured_data_all.csv",
                            counting_unit="page",
                        ))
                for warn in sd.validation_warnings:
                    issues.append(SEOIssue(
                        category="Structured Data", severity="warning",
                        issue_type=f"Validation Warning: {warn}", url=page.url,
                        evidence=sd_type,
                        source_table="structured_data_all.csv",
                        counting_unit="page",
                    ))

        return issues

    def _check_og_twitter_issues(self, page: PageData) -> list[SEOIssue]:
        """Check Open Graph and Twitter Card issues."""
        issues = []

        if not page.og_title:
            issues.append(SEOIssue(
                category="Social", severity="info",
                issue_type="Missing og:title", url=page.url,
            ))
        if not page.og_description:
            issues.append(SEOIssue(
                category="Social", severity="info",
                issue_type="Missing og:description", url=page.url,
            ))
        if not page.og_image:
            issues.append(SEOIssue(
                category="Social", severity="info",
                issue_type="Missing og:image", url=page.url,
            ))
        if not page.twitter_card:
            issues.append(SEOIssue(
                category="Social", severity="info",
                issue_type="Missing Twitter Card", url=page.url,
            ))

        return issues

    def _check_performance_issues(self, page: PageData) -> list[SEOIssue]:
        """Check performance issues."""
        issues = []

        if page.response_time > 3.0:
            issues.append(SEOIssue(
                category="Performance", severity="warning",
                issue_type="Slow Response Time", url=page.url,
                current_value=f"{page.response_time:.2f}s",
                recommendation="Response time should be under 3 seconds",
            ))
        elif page.response_time > 1.0:
            issues.append(SEOIssue(
                category="Performance", severity="info",
                issue_type="Response Time Over 1s", url=page.url,
                current_value=f"{page.response_time:.2f}s",
            ))

        if page.page_speed.html_size > 200_000:
            issues.append(SEOIssue(
                category="Performance", severity="warning",
                issue_type="Large HTML Size", url=page.url,
                current_value=f"{page.page_speed.html_size / 1024:.0f} KB",
            ))

        return issues

    def _check_cross_page_duplicates(self, pages: list[PageData]) -> dict[str, list[SEOIssue]]:
        """Check for duplicate titles, meta descriptions, and h1s across pages.

        For each duplicate group, creates issues for every page in the group.

        Args:
            pages: List of PageData objects to check for duplicates

        Returns:
            Dictionary mapping URLs to lists of duplicate issues
        """
        all_issues: dict[str, list[SEOIssue]] = {}

        # Filter pages with status 200 only
        valid_pages = [p for p in pages if p.status_code == 200]

        # Check for duplicate titles
        title_groups: dict[str, list[str]] = {}
        for page in valid_pages:
            if page.title:
                if page.title not in title_groups:
                    title_groups[page.title] = []
                title_groups[page.title].append(page.url)

        for title, urls in title_groups.items():
            if len(urls) > 1:
                for url in urls:
                    if url not in all_issues:
                        all_issues[url] = []
                    all_issues[url].append(SEOIssue(
                        category="Page Titles", severity="warning",
                        issue_type="Duplicate", url=url,
                        current_value=f"Duplicate title across {len(urls)} pages",
                        recommendation="Each page should have a unique title",
                        evidence=title,
                        source_table="internal_all.csv",
                        counting_unit="page",
                    ))

        # Check for duplicate meta descriptions
        desc_groups: dict[str, list[str]] = {}
        for page in valid_pages:
            if page.meta_description:
                if page.meta_description not in desc_groups:
                    desc_groups[page.meta_description] = []
                desc_groups[page.meta_description].append(page.url)

        for desc, urls in desc_groups.items():
            if len(urls) > 1:
                for url in urls:
                    if url not in all_issues:
                        all_issues[url] = []
                    all_issues[url].append(SEOIssue(
                        category="Meta Description", severity="warning",
                        issue_type="Duplicate", url=url,
                        current_value=f"Duplicate description across {len(urls)} pages",
                        recommendation="Each page should have a unique description",
                        evidence=desc,
                        source_table="internal_all.csv",
                        counting_unit="page",
                    ))

        # Check for duplicate h1s
        h1_groups: dict[str, list[str]] = {}
        for page in valid_pages:
            for h1 in page.headings.h1:
                if h1 not in h1_groups:
                    h1_groups[h1] = []
                h1_groups[h1].append(page.url)

        for h1, urls in h1_groups.items():
            if len(urls) > 1:
                for url in urls:
                    if url not in all_issues:
                        all_issues[url] = []
                    all_issues[url].append(SEOIssue(
                        category="H1", severity="warning",
                        issue_type="Duplicate", url=url,
                        current_value=f"Duplicate H1 across {len(urls)} pages",
                        recommendation="Each page should have a unique H1",
                        evidence=h1,
                        source_table="h1_all.csv",
                        counting_unit="page",
                    ))

        return all_issues

    def _check_pagination_issues(self, page: PageData) -> list[SEOIssue]:
        """Check pagination issues."""
        issues = []

        if page.rel_next and page.rel_prev:
            pass  # Properly paginated
        elif page.rel_next and not page.rel_prev:
            # First page of paginated series - OK
            pass
        elif not page.rel_next and page.rel_prev:
            # Last page of paginated series - OK
            pass

        return issues
