"""
XML Sitemap Parser and Generator.
Mirrors Screaming Frog's sitemap discovery, parsing, and generation capabilities.
"""
import logging
import re
from typing import Optional
from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

from seo_spider.core.models import PageData

logger = logging.getLogger("seo_spider.sitemap")

SITEMAP_NS = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1',
    'xhtml': 'http://www.w3.org/1999/xhtml',
}


class SitemapParser:
    """Parse XML sitemaps and sitemap index files."""

    async def parse_sitemap(self, url: str, client: httpx.AsyncClient) -> list[str]:
        """
        Parse a sitemap URL and return all URLs found.
        Handles both sitemap index files and regular sitemaps.
        """
        all_urls = []

        try:
            response = await client.get(url, timeout=30.0)
            if response.status_code != 200:
                logger.warning(f"Sitemap returned {response.status_code}: {url}")
                return []

            content = response.text

            # Detect if it's a sitemap index
            if '<sitemapindex' in content:
                urls = await self._parse_sitemap_index(content, client)
                all_urls.extend(urls)
            else:
                urls = self._parse_urlset(content)
                all_urls.extend(urls)

        except Exception as e:
            logger.warning(f"Failed to parse sitemap {url}: {e}")

        logger.info(f"Parsed sitemap {url}: {len(all_urls)} URLs found")
        return all_urls

    async def _parse_sitemap_index(self, content: str, client: httpx.AsyncClient) -> list[str]:
        """Parse a sitemap index file and recursively parse child sitemaps."""
        all_urls = []

        try:
            root = ET.fromstring(content)
            sitemap_elements = root.findall('.//sm:sitemap/sm:loc', SITEMAP_NS)
            if not sitemap_elements:
                sitemap_elements = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')

            for elem in sitemap_elements:
                child_url = elem.text.strip() if elem.text else ''
                if child_url:
                    child_urls = await self.parse_sitemap(child_url, client)
                    all_urls.extend(child_urls)

        except ET.ParseError as e:
            logger.warning(f"XML parse error in sitemap index: {e}")

        return all_urls

    def _parse_urlset(self, content: str) -> list[str]:
        """Parse a standard sitemap urlset."""
        urls = []

        try:
            root = ET.fromstring(content)
            loc_elements = root.findall('.//sm:url/sm:loc', SITEMAP_NS)
            if not loc_elements:
                loc_elements = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')

            for elem in loc_elements:
                url = elem.text.strip() if elem.text else ''
                if url:
                    urls.append(url)

        except ET.ParseError as e:
            logger.warning(f"XML parse error in sitemap: {e}")
            # Fallback: extract URLs with regex
            urls = re.findall(r'<loc>\s*(https?://[^<]+)\s*</loc>', content)

        return urls


class SitemapGenerator:
    """
    Generate XML sitemaps from crawl results.
    Mirrors Screaming Frog's sitemap generation feature.
    """

    def generate(
        self,
        pages: list[PageData],
        include_images: bool = False,
        include_lastmod: bool = True,
        include_priority: bool = False,
        include_changefreq: bool = False,
        max_urls_per_sitemap: int = 50000,
    ) -> list[str]:
        """
        Generate XML sitemap(s) from crawled pages.
        Returns a list of XML strings (one per sitemap file).
        Only includes 200 OK HTML pages by default.
        """
        # Filter pages
        eligible = [
            p for p in pages
            if p.status_code == 200
            and p.is_indexable
            and 'text/html' in p.content_type
        ]

        if not eligible:
            return []

        sitemaps = []
        for i in range(0, len(eligible), max_urls_per_sitemap):
            batch = eligible[i:i + max_urls_per_sitemap]
            xml = self._build_sitemap_xml(
                batch, include_images, include_lastmod,
                include_priority, include_changefreq,
            )
            sitemaps.append(xml)

        # Generate sitemap index if multiple sitemaps
        if len(sitemaps) > 1:
            index_xml = self._build_sitemap_index(len(sitemaps))
            sitemaps.insert(0, index_xml)

        return sitemaps

    def _build_sitemap_xml(
        self, pages: list[PageData],
        include_images: bool,
        include_lastmod: bool,
        include_priority: bool,
        include_changefreq: bool,
    ) -> str:
        """Build a single sitemap XML string."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
        ]

        if include_images:
            lines.append(
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            )
        else:
            lines.append(
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            )

        for page in pages:
            url = page.canonical_url if page.canonical_is_self else page.url
            lines.append('  <url>')
            lines.append(f'    <loc>{self._escape_xml(url)}</loc>')

            if include_lastmod and page.crawl_timestamp:
                date = page.crawl_timestamp[:10]  # YYYY-MM-DD
                lines.append(f'    <lastmod>{date}</lastmod>')

            if include_changefreq:
                freq = self._estimate_changefreq(page)
                lines.append(f'    <changefreq>{freq}</changefreq>')

            if include_priority:
                priority = self._estimate_priority(page)
                lines.append(f'    <priority>{priority}</priority>')

            if include_images:
                for img in page.images[:1000]:
                    if img.src:
                        lines.append('    <image:image>')
                        lines.append(f'      <image:loc>{self._escape_xml(img.src)}</image:loc>')
                        if img.alt_text:
                            lines.append(f'      <image:caption>{self._escape_xml(img.alt_text)}</image:caption>')
                        if img.title:
                            lines.append(f'      <image:title>{self._escape_xml(img.title)}</image:title>')
                        lines.append('    </image:image>')

            lines.append('  </url>')

        lines.append('</urlset>')
        return '\n'.join(lines)

    def _build_sitemap_index(self, count: int) -> str:
        """Build a sitemap index XML string."""
        today = datetime.now().strftime('%Y-%m-%d')
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for i in range(count):
            lines.append('  <sitemap>')
            lines.append(f'    <loc>sitemap-{i + 1}.xml</loc>')
            lines.append(f'    <lastmod>{today}</lastmod>')
            lines.append('  </sitemap>')
        lines.append('</sitemapindex>')
        return '\n'.join(lines)

    def _estimate_changefreq(self, page: PageData) -> str:
        """Estimate change frequency based on URL patterns."""
        url = page.url.lower()
        if '/' == url.rstrip('/').split('/')[-1] or url.count('/') <= 3:
            return 'daily'
        elif 'blog' in url or 'news' in url:
            return 'weekly'
        else:
            return 'monthly'

    def _estimate_priority(self, page: PageData) -> str:
        """Estimate priority based on crawl depth and inlinks."""
        if page.crawl_depth == 0:
            return '1.0'
        elif page.crawl_depth == 1:
            return '0.8'
        elif page.crawl_depth == 2:
            return '0.6'
        else:
            return '0.5'

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters."""
        return (
            text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace("'", '&apos;')
            .replace('"', '&quot;')
        )
