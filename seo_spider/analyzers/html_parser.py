"""
HTML Parser and On-Page SEO Analyzer.
Extracts all SEO-relevant data from HTML, mirroring Screaming Frog's analysis tabs.
"""
import re
import logging
from typing import Optional
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, Comment

from seo_spider.core.models import (
    PageData, LinkData, ImageData, HeadingData, ResourceData,
    HreflangData, StructuredDataItem, CustomExtractionResult,
)
from seo_spider.config.settings import CrawlConfig
from seo_spider.utils.url_utils import normalize_url, extract_domain, is_subdomain_of
from seo_spider.utils.hash_utils import content_hash, simhash_text

logger = logging.getLogger("seo_spider.html_parser")


class HTMLAnalyzer:
    """
    Comprehensive HTML analyzer that extracts all SEO-relevant data.
    Processes a single page's HTML and populates the PageData model.
    """

    def __init__(self, config: CrawlConfig):
        self.config = config
        self._base_domain = extract_domain(config.start_urls[0]) if config.start_urls else ""

    def analyze(self, page: PageData, html: str, url: str):
        """Run all analysis on HTML content and populate PageData."""
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            soup = BeautifulSoup(html, 'html.parser')

        # Title
        self._extract_title(page, soup)

        # Meta tags
        self._extract_meta(page, soup)

        # Headings
        if self.config.extract_headings:
            self._extract_headings(page, soup)

        # Links
        if self.config.extract_links:
            self._extract_links(page, soup, url)

        # Images
        if self.config.extract_images:
            self._extract_images(page, soup, url)

        # Resources (CSS, JS)
        self._extract_resources(page, soup, url)

        # Structured Data (MUST be before _analyze_content which destroys script tags)
        if self.config.extract_structured_data:
            self._extract_structured_data(page, soup)

        # Content analysis (destroys script/style tags for text extraction)
        self._analyze_content(page, soup, html)

        # Canonical
        if self.config.extract_canonicals:
            self._extract_canonical(page, soup, url)

        # Set canonical status if not already set
        if not page.canonical_status:
            if not page.canonical_url and not page.http_canonical:
                page.canonical_status = "Missing"

        # Hreflang
        if self.config.extract_hreflang:
            self._extract_hreflang(page, soup, url)

        # Pagination
        if self.config.extract_pagination:
            self._extract_pagination(page, soup, url)

        # Open Graph
        self._extract_open_graph(page, soup)

        # Twitter Card
        self._extract_twitter_card(page, soup)

        # HTML lang
        self._extract_html_lang(page, soup)

        # Meta Robots / Indexability
        self._analyze_indexability(page, soup)

        # Custom extractions
        if self.config.custom_extractions:
            self._run_custom_extractions(page, soup, html)

        # Custom searches
        if self.config.custom_searches:
            self._run_custom_searches(page, html)

    def _extract_title(self, page: PageData, soup: BeautifulSoup):
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            page.title = title_tag.get_text(strip=True)
            page.title_length = len(page.title)
            # Estimate pixel width (approx 6px per character for common fonts)
            page.title_pixel_width = int(page.title_length * 6.5)

    def _extract_meta(self, page: PageData, soup: BeautifulSoup):
        """Extract meta tags."""
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)})
        if meta_desc:
            page.meta_description = meta_desc.get('content', '')
            page.meta_description_length = len(page.meta_description)

        # Meta description pixel width
        page.meta_description_pixel_width = int(page.meta_description_length * 5.5) if page.meta_description_length else 0

        # Meta keywords
        meta_kw = soup.find('meta', attrs={'name': re.compile(r'^keywords$', re.I)})
        if meta_kw:
            page.meta_keywords = meta_kw.get('content', '')
            page.meta_keywords_length = len(page.meta_keywords)

        # Meta robots
        meta_robots = soup.find('meta', attrs={'name': re.compile(r'^robots$', re.I)})
        if meta_robots:
            page.meta_robots = meta_robots.get('content', '')

        # Meta refresh
        meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'^refresh$', re.I)})
        if meta_refresh:
            page.meta_refresh = meta_refresh.get('content', '')

        # Charset
        meta_charset = soup.find('meta', attrs={'charset': True})
        if meta_charset:
            page.charset = meta_charset.get('charset', '')
        else:
            meta_ct = soup.find('meta', attrs={'http-equiv': re.compile(r'^content-type$', re.I)})
            if meta_ct:
                content = meta_ct.get('content', '')
                if 'charset=' in content:
                    page.charset = content.split('charset=')[-1].strip()

        # Content-Language
        meta_lang = soup.find('meta', attrs={'http-equiv': re.compile(r'^content-language$', re.I)})
        if meta_lang:
            page.content_language = meta_lang.get('content', '')

    def _extract_headings(self, page: PageData, soup: BeautifulSoup):
        """Extract all heading tags."""
        headings = HeadingData()
        for level in range(1, 7):
            tag = f'h{level}'
            elements = soup.find_all(tag)
            texts = [el.get_text(strip=True) for el in elements]
            setattr(headings, tag, texts)
        page.headings = headings

    def _extract_links(self, page: PageData, soup: BeautifulSoup, base_url: str):
        """Extract all links and classify as internal/external."""
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            normalized = normalize_url(href, base_url)
            if not normalized:
                continue

            rel = a_tag.get('rel', [])
            if isinstance(rel, str):
                rel = rel.split()

            anchor_text = a_tag.get_text(strip=True)
            is_follow = 'nofollow' not in rel

            # Determine position
            position = self._determine_link_position(a_tag)

            link = LinkData(
                source_url=base_url,
                target_url=normalized,
                anchor_text=anchor_text[:200],  # Truncate long anchors
                link_type="hyperlink",
                is_follow=is_follow,
                rel_attributes=rel,
                link_position=position,
            )

            if is_subdomain_of(normalized, self._base_domain):
                link.is_internal = True
                page.internal_links.append(link)
            else:
                link.is_internal = False
                page.external_links.append(link)

    def _determine_link_position(self, tag) -> str:
        """Determine where a link is positioned in the page structure."""
        parent = tag.parent
        while parent:
            name = parent.name or ''
            if name in ('header', 'nav'):
                return 'navigation'
            elif name == 'footer':
                return 'footer'
            elif name in ('aside',):
                return 'sidebar'
            elif name in ('main', 'article', 'section'):
                return 'content'
            parent = parent.parent
        return 'content'

    def _extract_images(self, page: PageData, soup: BeautifulSoup, base_url: str):
        """Extract all images and analyze alt text."""
        for img in soup.find_all('img'):
            src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
            if not src:
                continue

            normalized_src = normalize_url(src, base_url) or src
            alt = img.get('alt')

            image = ImageData(
                src=normalized_src,
                alt_text=alt if alt is not None else '',
                title=img.get('title', ''),
                width=self._parse_int(img.get('width')),
                height=self._parse_int(img.get('height')),
                is_missing_alt_attribute=(alt is None),
                is_missing_alt=(alt is not None and alt.strip() == ''),
                alt_over_100=(len(alt) > 100 if alt else False),
                source_page=base_url,
            )
            page.images.append(image)

        page.images_count = len(page.images)
        page.images_missing_alt = sum(
            1 for img in page.images
            if img.is_missing_alt
        )
        page.images_missing_alt_attribute = sum(
            1 for img in page.images if img.is_missing_alt_attribute
        )
        page.images_with_alt_over_100 = sum(
            1 for img in page.images if img.alt_over_100
        )

    def _extract_resources(self, page: PageData, soup: BeautifulSoup, base_url: str):
        """Extract CSS and JavaScript resources."""
        # CSS
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href', '')
            if href:
                page.css_resources.append(ResourceData(
                    url=normalize_url(href, base_url) or href,
                    resource_type="css",
                    content_type="text/css",
                ))

        for style in soup.find_all('style'):
            # Inline styles with @import
            text = style.get_text()
            imports = re.findall(r'@import\s+url\(["\']?([^"\']+)["\']?\)', text)
            for imp in imports:
                page.css_resources.append(ResourceData(
                    url=normalize_url(imp, base_url) or imp,
                    resource_type="css",
                    content_type="text/css",
                ))

        # JavaScript
        for script in soup.find_all('script', src=True):
            src = script.get('src', '')
            if src:
                page.js_resources.append(ResourceData(
                    url=normalize_url(src, base_url) or src,
                    resource_type="javascript",
                    content_type="application/javascript",
                ))

    def _analyze_content(self, page: PageData, soup: BeautifulSoup, html: str):
        """Analyze text content: word count, readability, text ratio, duplicate detection."""
        # Remove script and style elements
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()

        page.body_text = text[:5000]
        words = text.split() if text else []
        page.word_count = len(words)

        # Sentence analysis
        sentences = re.split(r'[.!?。]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]
        page.sentence_count = len(sentences)
        page.avg_words_per_sentence = round(page.word_count / page.sentence_count, 1) if page.sentence_count > 0 else 0

        # Flesch Reading Ease (works for English; approximate for other languages)
        syllable_count = self._count_syllables(text)
        if page.sentence_count > 0 and page.word_count > 0:
            page.flesch_reading_ease = round(
                206.835
                - 1.015 * (page.word_count / page.sentence_count)
                - 84.6 * (syllable_count / page.word_count),
                1
            )
        else:
            page.flesch_reading_ease = 0.0

        if page.flesch_reading_ease >= 80:
            page.readability = "Easy"
        elif page.flesch_reading_ease >= 60:
            page.readability = "Fairly Easy"
        elif page.flesch_reading_ease >= 40:
            page.readability = "Standard"
        elif page.flesch_reading_ease >= 20:
            page.readability = "Fairly Difficult"
        else:
            page.readability = "Difficult"

        # Language detection (simple heuristic)
        page.detected_language = page.html_lang or ""

        # Text to HTML ratio
        html_size = len(html)
        text_size = len(text)
        page.text_ratio = round((text_size / html_size * 100), 2) if html_size > 0 else 0

        # Duplicate detection
        if self.config.detect_duplicates and text:
            page.content_hash = content_hash(text)
            page.simhash = simhash_text(text)

    @staticmethod
    def _count_syllables(text: str) -> int:
        """Approximate syllable count for English text."""
        text = text.lower()
        words = re.findall(r'[a-z]+', text)
        count = 0
        for word in words:
            vowels = re.findall(r'[aeiouy]+', word)
            syl = max(1, len(vowels))
            if word.endswith('e') and len(vowels) > 1:
                syl -= 1
            count += syl
        # For non-Latin text (Korean, etc.), estimate 1 syllable per character
        non_latin = re.findall(r'[^\x00-\x7F]', text)
        count += len(non_latin)
        return max(count, 1)

    def _extract_canonical(self, page: PageData, soup: BeautifulSoup, url: str):
        """Extract canonical URL."""
        canonical = soup.find('link', rel='canonical')
        if canonical:
            href = canonical.get('href', '')
            normalized = normalize_url(href, url) or href
            page.canonical_url = normalized
            page.canonical_is_self = (normalized == url or normalized == page.final_url)
            page.canonical_mismatch = not page.canonical_is_self

        # Set canonical_status
        if not page.canonical_url and not page.http_canonical:
            page.canonical_status = "Missing"
        elif page.canonical_is_self:
            page.canonical_status = "Self-Referencing"
        else:
            page.canonical_status = "Canonicalised"

    def _extract_hreflang(self, page: PageData, soup: BeautifulSoup, url: str):
        """Extract hreflang annotations."""
        for link in soup.find_all('link', rel='alternate'):
            hreflang = link.get('hreflang')
            if hreflang:
                href = link.get('href', '')
                normalized = normalize_url(href, url) or href

                # Parse language-region
                parts = hreflang.split('-')
                language = parts[0] if parts else ''
                region = parts[1] if len(parts) > 1 else ''

                annotation = HreflangData(
                    source_url=url,
                    language=language,
                    region=region,
                    target_url=normalized,
                )

                # Validate
                issues = []
                if not language:
                    issues.append("Missing language code")
                if len(language) != 2 and language != 'x-default':
                    issues.append(f"Invalid language code: {language}")
                if region and len(region) != 2:
                    issues.append(f"Invalid region code: {region}")
                if not href:
                    issues.append("Missing href")

                annotation.issues = issues
                annotation.is_valid = len(issues) == 0
                page.hreflang_annotations.append(annotation)

    def _extract_pagination(self, page: PageData, soup: BeautifulSoup, url: str):
        """Extract rel=next and rel=prev pagination links."""
        next_link = soup.find('link', rel='next')
        if next_link:
            href = next_link.get('href', '')
            page.rel_next = normalize_url(href, url) or href

        prev_link = soup.find('link', rel='prev')
        if prev_link:
            href = prev_link.get('href', '')
            page.rel_prev = normalize_url(href, url) or href

    def _extract_open_graph(self, page: PageData, soup: BeautifulSoup):
        """Extract Open Graph meta tags."""
        og_mapping = {
            'og:title': 'og_title',
            'og:description': 'og_description',
            'og:image': 'og_image',
            'og:type': 'og_type',
            'og:url': 'og_url',
        }
        for og_prop, attr_name in og_mapping.items():
            meta = soup.find('meta', property=og_prop)
            if meta:
                setattr(page, attr_name, meta.get('content', ''))

    def _extract_twitter_card(self, page: PageData, soup: BeautifulSoup):
        """Extract Twitter Card meta tags."""
        tc_mapping = {
            'twitter:card': 'twitter_card',
            'twitter:title': 'twitter_title',
            'twitter:description': 'twitter_description',
            'twitter:image': 'twitter_image',
        }
        for tc_name, attr_name in tc_mapping.items():
            meta = soup.find('meta', attrs={'name': tc_name})
            if not meta:
                meta = soup.find('meta', property=tc_name)
            if meta:
                setattr(page, attr_name, meta.get('content', ''))

    def _extract_structured_data(self, page: PageData, soup: BeautifulSoup):
        """Extract JSON-LD structured data."""
        import json
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '{}')
                schema_type = ''
                if isinstance(data, dict):
                    schema_type = data.get('@type', '')
                elif isinstance(data, list) and data:
                    schema_type = data[0].get('@type', '') if isinstance(data[0], dict) else ''

                item = StructuredDataItem(
                    format_type="json-ld",
                    schema_type=schema_type,
                    raw_data=data if isinstance(data, dict) else {"@graph": data},
                )
                page.structured_data.append(item)
            except json.JSONDecodeError:
                page.structured_data.append(StructuredDataItem(
                    format_type="json-ld",
                    validation_errors=["Invalid JSON-LD"],
                    is_valid=False,
                ))

    def _extract_html_lang(self, page: PageData, soup: BeautifulSoup):
        """Extract HTML lang attribute."""
        html_tag = soup.find('html')
        if html_tag:
            page.html_lang = html_tag.get('lang', '')

    def _analyze_indexability(self, page: PageData, soup: BeautifulSoup):
        """Determine if a page is indexable based on meta robots and other signals."""
        robots_content = page.meta_robots.lower() if page.meta_robots else ''
        x_robots = page.x_robots_tag.lower() if page.x_robots_tag else ''

        # Check X-Robots-Tag from headers
        if 'x-robots-tag' in page.response_headers:
            page.x_robots_tag = page.response_headers['x-robots-tag']
            x_robots = page.x_robots_tag.lower()

        reasons = []
        if 'noindex' in robots_content:
            reasons.append("Noindex in Meta Robots")
        if 'noindex' in x_robots:
            reasons.append("Noindex in X-Robots-Tag")
        if page.status_code != 200:
            reasons.append(f"Non-200 Status Code ({page.status_code})")
        if page.canonical_url and page.canonical_mismatch:
            reasons.append("Canonicalised to different URL")

        if reasons:
            page.is_indexable = False
            page.indexability_status = "; ".join(reasons)
        else:
            page.is_indexable = True
            page.indexability_status = "Indexable"

    def _run_custom_extractions(self, page: PageData, soup: BeautifulSoup, html: str):
        """Run custom extraction rules (XPath, CSS Selector, Regex)."""
        for rule in self.config.custom_extractions:
            name = rule.get('name', '')
            extraction_type = rule.get('type', '')
            pattern = rule.get('value', '')

            value = ''
            try:
                if extraction_type == 'css':
                    elements = soup.select(pattern)
                    value = ' | '.join(el.get_text(strip=True) for el in elements)
                elif extraction_type == 'xpath':
                    from lxml import etree
                    tree = etree.HTML(html)
                    results = tree.xpath(pattern)
                    if results:
                        value = ' | '.join(
                            r.text if hasattr(r, 'text') and r.text else str(r)
                            for r in results
                        )
                elif extraction_type == 'regex':
                    matches = re.findall(pattern, html)
                    value = ' | '.join(matches[:10])
            except Exception as e:
                value = f"Error: {e}"

            page.custom_extractions.append(CustomExtractionResult(
                name=name,
                value=value,
                extraction_type=extraction_type,
            ))

    def _run_custom_searches(self, page: PageData, html: str):
        """Run custom search patterns against page content."""
        for search in self.config.custom_searches:
            name = search.get('name', '')
            search_type = search.get('type', 'contains')
            pattern = search.get('value', '')

            matched = False
            try:
                if search_type == 'contains':
                    matched = pattern.lower() in html.lower()
                elif search_type == 'regex':
                    matched = bool(re.search(pattern, html, re.IGNORECASE))
                elif search_type == 'not_contains':
                    matched = pattern.lower() not in html.lower()
            except Exception:
                pass

            page.custom_search_matches[name] = matched

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse an integer value."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
