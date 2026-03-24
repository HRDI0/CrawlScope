"""
Duplicate Content Detector.
Mirrors Screaming Frog's MD5-based exact duplicate and near-duplicate detection.
"""
import logging
from typing import Optional
from collections import defaultdict

from seo_spider.core.models import PageData, CrawlResult
from seo_spider.utils.hash_utils import (
    content_hash, simhash_text, are_near_duplicates,
    shingle_hash, jaccard_similarity,
)

logger = logging.getLogger("seo_spider.duplicate")


class DuplicateDetector:
    """
    Detect duplicate and near-duplicate content across crawled pages.

    Detection methods:
    1. Exact duplicate (MD5 hash of body text)
    2. Exact duplicate page titles
    3. Exact duplicate meta descriptions
    4. Near-duplicate content (SimHash)
    5. Near-duplicate content (Jaccard similarity with shingling)
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def detect_all(self, result: CrawlResult) -> dict:
        """
        Run all duplicate detection methods.
        Returns a comprehensive report.
        """
        report = {
            "exact_duplicates": self.find_exact_duplicates(result.pages),
            "duplicate_titles": self.find_duplicate_titles(result.pages),
            "duplicate_descriptions": self.find_duplicate_descriptions(result.pages),
            "near_duplicates": self.find_near_duplicates(result.pages),
            "duplicate_h1s": self.find_duplicate_h1s(result.pages),
        }

        # Update the result object
        result.duplicate_groups = report["exact_duplicates"]

        # Count issues
        result.issues["Duplicate Page"] = sum(
            len(urls) - 1 for urls in report["exact_duplicates"].values()
        )
        result.issues["Duplicate Title"] = sum(
            len(urls) - 1 for urls in report["duplicate_titles"].values()
        )
        result.issues["Duplicate Meta Description"] = sum(
            len(urls) - 1 for urls in report["duplicate_descriptions"].values()
        )
        result.issues["Near-Duplicate Content"] = len(report["near_duplicates"])
        result.issues["Duplicate H1"] = sum(
            len(urls) - 1 for urls in report["duplicate_h1s"].values()
        )

        return report

    def find_exact_duplicates(self, pages: list[PageData]) -> dict[str, list[str]]:
        """Find pages with exactly the same content (MD5 hash match)."""
        hash_groups: dict[str, list[str]] = defaultdict(list)

        for page in pages:
            if page.content_hash and page.status_code == 200:
                hash_groups[page.content_hash].append(page.url)

        # Only return groups with duplicates
        return {
            h: urls for h, urls in hash_groups.items()
            if len(urls) > 1
        }

    def find_duplicate_titles(self, pages: list[PageData]) -> dict[str, list[str]]:
        """Find pages with identical page titles."""
        title_groups: dict[str, list[str]] = defaultdict(list)

        for page in pages:
            if page.title and page.status_code == 200:
                title_groups[page.title.strip().lower()].append(page.url)

        return {
            t: urls for t, urls in title_groups.items()
            if len(urls) > 1
        }

    def find_duplicate_descriptions(self, pages: list[PageData]) -> dict[str, list[str]]:
        """Find pages with identical meta descriptions."""
        desc_groups: dict[str, list[str]] = defaultdict(list)

        for page in pages:
            if page.meta_description and page.status_code == 200:
                desc_groups[page.meta_description.strip().lower()].append(page.url)

        return {
            d: urls for d, urls in desc_groups.items()
            if len(urls) > 1
        }

    def find_duplicate_h1s(self, pages: list[PageData]) -> dict[str, list[str]]:
        """Find pages with identical H1 headings."""
        h1_groups: dict[str, list[str]] = defaultdict(list)

        for page in pages:
            if page.headings.h1 and page.status_code == 200:
                for h1 in page.headings.h1:
                    h1_groups[h1.strip().lower()].append(page.url)

        return {
            h: urls for h, urls in h1_groups.items()
            if len(urls) > 1
        }

    def find_near_duplicates(self, pages: list[PageData]) -> list[tuple[str, str, float]]:
        """
        Find near-duplicate pages using SimHash comparison.
        Returns list of (url1, url2, similarity_score) tuples.
        """
        near_dupes = []
        valid_pages = [p for p in pages if p.simhash and p.status_code == 200]

        # Compare all pairs (O(n^2) but necessary for accuracy)
        for i in range(len(valid_pages)):
            for j in range(i + 1, len(valid_pages)):
                p1, p2 = valid_pages[i], valid_pages[j]

                # Skip if same content hash (already an exact duplicate)
                if p1.content_hash == p2.content_hash:
                    continue

                if are_near_duplicates(p1.simhash, p2.simhash, threshold=5):
                    # Verify with Jaccard similarity for accuracy
                    if p1.body_text and p2.body_text:
                        s1 = shingle_hash(p1.body_text)
                        s2 = shingle_hash(p2.body_text)
                        similarity = jaccard_similarity(s1, s2)
                        if similarity >= self.similarity_threshold:
                            near_dupes.append((p1.url, p2.url, similarity))

        return near_dupes
