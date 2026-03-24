"""
Core SEO Spider Crawler Engine.
Breadth-first crawling with async I/O, matching Screaming Frog's crawl behavior.
"""
import asyncio
import time
import logging
from collections import deque
from urllib.parse import urlparse, urljoin
from typing import Optional, Callable
from datetime import datetime

import httpx

from .models import PageData, CrawlResult, LinkData
from .robots_parser import RobotsManager
from .subdomain_discovery import SubdomainDiscovery
from seo_spider.config.settings import CrawlConfig, RenderingMode, CrawlMode
from seo_spider.evasion.anti_bot import AntiBotEvasion
from seo_spider.utils.url_utils import normalize_url, extract_domain, is_subdomain_of, get_fqdn
from seo_spider.utils.logging_config import setup_logger

logger = setup_logger("seo_spider.crawler")


class SEOSpiderCrawler:
    """
    Main crawler engine. Orchestrates the entire crawl process.

    Features:
    - Breadth-first crawling (like Screaming Frog)
    - Subdomain discovery and crawling
    - Respects robots.txt
    - Async concurrent crawling
    - Bot evasion integration
    - JavaScript rendering integration (via JSRenderer)
    - Configurable scope and filters
    """

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.result = CrawlResult()

        # URL management
        self._queue: deque[tuple[str, int]] = deque()  # (url, depth)
        self._visited: set[str] = set()
        self._queued: set[str] = set()
        self._external_urls: set[str] = set()

        # Domain tracking
        self._base_domain: str = ""
        self._allowed_domains: set[str] = set()

        # Modules
        self._robots = RobotsManager(
            respect_robots=config.respect_robots_txt,
        )
        self._evasion = AntiBotEvasion(
            rotate_ua=config.rotate_user_agents,
            randomize_delays=config.randomize_delays,
            delay_min=config.delay_min,
            delay_max=config.delay_max,
            use_stealth=config.use_stealth_mode,
            proxy_list=config.proxy_list,
            spoof_referer=config.spoof_referer,
        ) if config.evasion_enabled else None

        self._subdomain_discovery: Optional[SubdomainDiscovery] = None
        self._js_renderer = None  # Set externally if JS rendering is needed

        # Callbacks
        self._on_page_crawled: Optional[Callable] = None
        self._on_progress: Optional[Callable] = None

        # Semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(config.max_concurrent)

        # Statistics
        self._start_time: float = 0
        self._pages_per_second: float = 0

    def set_js_renderer(self, renderer):
        """Set the JavaScript renderer for JS rendering mode."""
        self._js_renderer = renderer

    def on_page_crawled(self, callback: Callable):
        """Register a callback for when a page is crawled."""
        self._on_page_crawled = callback

    def on_progress(self, callback: Callable):
        """Register a progress callback."""
        self._on_progress = callback

    async def crawl(self) -> CrawlResult:
        """Execute the full crawl process."""
        self._start_time = time.time()
        self.result.crawl_start_time = datetime.now().isoformat()

        if not self.config.start_urls:
            logger.error("No start URLs configured")
            return self.result

        start_url = self.config.start_urls[0]
        self._base_domain = extract_domain(start_url)
        self.result.start_url = start_url
        self.result.domain = self._base_domain

        logger.info(f"Starting crawl of {self._base_domain}")

        # Phase 1: Subdomain discovery
        if self.config.crawl_subdomains and self.config.discover_subdomains:
            await self._discover_subdomains()

        # Phase 2: Seed the queue
        await self._seed_queue()

        # Phase 3: Main crawl loop
        async with httpx.AsyncClient(
            follow_redirects=False,  # We handle redirects manually
            timeout=httpx.Timeout(self.config.request_timeout),
            verify=True,
            http2=True,
        ) as client:
            # Fetch robots.txt first
            await self._robots.fetch_and_parse(start_url, client)

            # Discover sitemaps from robots.txt
            sitemaps = await self._robots.get_sitemaps_for_domain(start_url, client)
            if sitemaps:
                sitemap_urls = await self._parse_sitemaps(sitemaps, client)
                for url in sitemap_urls:
                    self._enqueue(url, 0)
                if self._subdomain_discovery:
                    self._subdomain_discovery.add_from_sitemap(sitemap_urls)

            # Main BFS crawl
            await self._bfs_crawl(client)

        # Phase 4: Check external links if configured
        if self.config.check_external_links:
            await self._check_external_links()

        # Finalize
        self.result.crawl_end_time = datetime.now().isoformat()
        self.result.total_urls_crawled = len(self._visited)
        self.result.total_internal = len([p for p in self.result.pages if not p.is_error])
        self.result.total_external = len(self._external_urls)

        # Build inlink map
        self._build_inlink_map()

        elapsed = time.time() - self._start_time
        logger.info(
            f"Crawl complete: {self.result.total_urls_crawled} URLs in {elapsed:.1f}s "
            f"({self.result.total_urls_crawled / elapsed:.1f} URLs/s)"
        )

        return self.result

    async def _discover_subdomains(self):
        """Run subdomain discovery."""
        logger.info(f"Discovering subdomains for {self._base_domain}")
        self._subdomain_discovery = SubdomainDiscovery(
            self._base_domain,
            methods=self.config.subdomain_discovery_methods,
        )
        subdomains = await self._subdomain_discovery.discover_all()
        self._allowed_domains = subdomains
        self.result.subdomains_found = sorted(subdomains)
        logger.info(f"Found {len(subdomains)} subdomains: {', '.join(sorted(subdomains)[:10])}...")

    async def _seed_queue(self):
        """Seed the crawl queue with start URLs."""
        for url in self.config.start_urls:
            normalized = normalize_url(url)
            if normalized:
                self._enqueue(normalized, 0)

    def _enqueue(self, url: str, depth: int):
        """Add a URL to the crawl queue."""
        if url in self._queued or url in self._visited:
            return
        if self.config.max_urls and len(self._queued) >= self.config.max_urls:
            return
        if self.config.max_depth and depth > self.config.max_depth:
            return

        # Check scope
        if not self._is_in_scope(url):
            self._external_urls.add(url)
            return

        # Check include/exclude patterns
        if not self._matches_filters(url):
            return

        self._queued.add(url)
        self._queue.append((url, depth))

    def _is_in_scope(self, url: str) -> bool:
        """Check if a URL is within crawl scope."""
        url_domain = extract_domain(url)

        if url_domain != self._base_domain:
            return False

        if self.config.crawl_subdomains:
            return is_subdomain_of(url, self._base_domain)

        # If not crawling subdomains, only allow the exact start domain
        start_host = get_fqdn(self.config.start_urls[0])
        url_host = get_fqdn(url)
        return url_host == start_host

    def _matches_filters(self, url: str) -> bool:
        """Check if URL matches include/exclude patterns."""
        import re

        if self.config.include_patterns:
            if not any(re.search(p, url) for p in self.config.include_patterns):
                return False

        if self.config.exclude_patterns:
            if any(re.search(p, url) for p in self.config.exclude_patterns):
                return False

        return True

    async def _bfs_crawl(self, client: httpx.AsyncClient):
        """Breadth-first crawling with concurrent workers."""
        tasks = set()

        while self._queue or tasks:
            # Fill up to max_concurrent tasks
            while self._queue and len(tasks) < self.config.max_concurrent:
                url, depth = self._queue.popleft()
                if url in self._visited:
                    continue
                task = asyncio.create_task(self._crawl_url(url, depth, client))
                tasks.add(task)

            if not tasks:
                break

            # Wait for at least one task to complete
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                try:
                    page_data = await task
                    if page_data:
                        self.result.pages.append(page_data)

                        # Discover new URLs from links
                        self._process_discovered_links(page_data)

                        # Update progress
                        if self._on_page_crawled:
                            self._on_page_crawled(page_data)

                        if self._on_progress:
                            self._on_progress(
                                len(self._visited),
                                len(self._queued),
                                len(self._queue),
                            )
                except Exception as e:
                    logger.error(f"Task error: {e}")

    async def _crawl_url(self, url: str, depth: int, client: httpx.AsyncClient) -> Optional[PageData]:
        """Crawl a single URL and return PageData."""
        async with self._semaphore:
            if url in self._visited:
                return None

            self._visited.add(url)

            # Check robots.txt
            if self.config.respect_robots_txt:
                allowed = await self._robots.is_allowed(url, client)
                if not allowed:
                    logger.debug(f"Blocked by robots.txt: {url}")
                    page = PageData(url=url, crawl_depth=depth)
                    page.indexability_status = "Blocked by Robots.txt"
                    page.is_indexable = False
                    return page

            # Apply evasion delays
            if self._evasion:
                domain = get_fqdn(url)
                await self._evasion.wait(domain)

            # Build request
            headers = {}
            if self._evasion:
                profile = self._evasion.get_request_profile(url, get_fqdn(url))
                headers = profile.headers

            page = PageData(
                url=url,
                crawl_depth=depth,
                crawl_timestamp=datetime.now().isoformat(),
            )

            try:
                start_time = time.time()

                # Follow redirects manually to track the chain
                redirect_chain = []
                current_url = url
                final_response = None

                for _ in range(self.config.max_redirects + 1):
                    response = await client.get(
                        current_url,
                        headers=headers,
                        follow_redirects=False,
                    )

                    if response.is_redirect:
                        redirect_chain.append(current_url)
                        location = response.headers.get('location', '')
                        current_url = normalize_url(location, current_url) or location
                        page.is_redirect = True
                        page.redirect_type = str(response.status_code)
                    else:
                        final_response = response
                        break
                else:
                    # Too many redirects
                    page.crawl_error = "Redirect loop detected"
                    page.is_error = True
                    return page

                if not final_response:
                    page.crawl_error = "No final response after redirects"
                    page.is_error = True
                    return page

                response_time = time.time() - start_time
                page.response_time = response_time
                page.status_code = final_response.status_code
                page.status_text = str(final_response.status_code)
                page.final_url = str(final_response.url)
                page.redirect_chain = redirect_chain
                page.content_type = final_response.headers.get('content-type', '')
                page.response_headers = dict(final_response.headers)
                page.charset = self._extract_charset(final_response)

                # Populate new fields from headers
                page.http_version = str(final_response.http_version) if hasattr(final_response, 'http_version') else ""
                page.last_modified = final_response.headers.get('last-modified', '')
                page.cookies = '; '.join(f"{k}={v}" for k, v in final_response.cookies.items()) if final_response.cookies else ''
                page.transferred_bytes = len(final_response.content) if final_response.content else 0

                # HTTP Canonical
                link_header = final_response.headers.get('link', '')
                if 'rel="canonical"' in link_header:
                    import re as _re
                    m = _re.search(r'<([^>]+)>;\s*rel="canonical"', link_header)
                    if m:
                        page.http_canonical = m.group(1)

                # HTTP rel-next/prev
                if 'rel="next"' in link_header:
                    import re as _re
                    m = _re.search(r'<([^>]+)>;\s*rel="next"', link_header)
                    if m:
                        page.http_rel_next = m.group(1)
                if 'rel="prev"' in link_header:
                    import re as _re
                    m = _re.search(r'<([^>]+)>;\s*rel="prev"', link_header)
                    if m:
                        page.http_rel_prev = m.group(1)

                # X-Robots-Tag from header
                if 'x-robots-tag' in final_response.headers:
                    page.x_robots_tag = final_response.headers['x-robots-tag']

                # URL properties
                from urllib.parse import quote, urlparse as _urlparse
                parsed = _urlparse(url)
                page.folder_depth = len([s for s in parsed.path.split('/') if s])
                page.url_length = len(url)
                page.url_encoded_address = quote(url, safe=':/?#[]@!$&\'()*+,;=-._~')

                # Handle evasion response
                if self._evasion:
                    domain = get_fqdn(url)
                    self._evasion.handle_response_status(
                        domain, final_response.status_code,
                        dict(final_response.headers)
                    )

                # Only parse HTML content
                if 'text/html' in page.content_type:
                    raw_html = final_response.text
                    html_content = raw_html

                    # JavaScript rendering if configured — store before/after
                    if (self.config.rendering_mode == RenderingMode.JAVASCRIPT
                            and self._js_renderer):
                        # First parse raw HTML to get pre-render values
                        from ..analyzers.html_parser import HTMLAnalyzer
                        pre_analyzer = HTMLAnalyzer(self.config)
                        pre_page = PageData(url=url)
                        pre_analyzer.analyze(pre_page, raw_html, url)

                        try:
                            rendered_html = await self._js_renderer.render(url)
                            if rendered_html:
                                html_content = rendered_html
                                # Store rendered comparison data after main analysis
                                page._pre_render = pre_page
                        except Exception as e:
                            logger.warning(f"JS rendering failed for {url}: {e}")

                    # Parse HTML and extract data
                    from ..analyzers.html_parser import HTMLAnalyzer
                    analyzer = HTMLAnalyzer(self.config)
                    analyzer.analyze(page, html_content, url)

                    # Populate JS rendering comparison if applicable
                    if hasattr(page, '_pre_render') and page._pre_render:
                        pre = page._pre_render
                        page.rendered_title = page.title
                        page.rendered_h1 = page.headings.h1[0] if page.headings.h1 else ""
                        page.rendered_meta_description = page.meta_description
                        page.rendered_canonical = page.canonical_url
                        page.rendered_meta_robots = page.meta_robots
                        page.rendered_word_count = page.word_count
                        # Overwrite main fields with raw HTML values, keep rendered in rendered_ fields
                        page.word_count_change = page.word_count - pre.word_count
                        page.js_word_count_pct = round(
                            (page.word_count_change / pre.word_count * 100) if pre.word_count > 0 else 0, 1
                        )
                        del page._pre_render

                    page.page_speed.html_size = len(final_response.content)
                    page.page_speed.response_time = response_time
                    page.page_speed.ttfb = response_time  # Simplified

                # Security analysis
                from ..analyzers.security_analyzer import SecurityAnalyzer
                sec_analyzer = SecurityAnalyzer()
                sec_analyzer.analyze(page)

            except httpx.TimeoutException:
                page.crawl_error = "Request timeout"
                page.is_error = True
                page.status_code = 0
            except httpx.ConnectError as e:
                page.crawl_error = f"Connection error: {e}"
                page.is_error = True
                page.status_code = 0
            except Exception as e:
                page.crawl_error = f"Error: {str(e)}"
                page.is_error = True
                logger.error(f"Error crawling {url}: {e}")

            return page

    def _process_discovered_links(self, page: PageData):
        """Extract and enqueue new URLs from a crawled page."""
        next_depth = page.crawl_depth + 1

        for link in page.internal_links:
            normalized = normalize_url(link.target_url, page.url)
            if normalized:
                self._enqueue(normalized, next_depth)

                # Feed to subdomain discovery
                if self._subdomain_discovery:
                    self._subdomain_discovery.add_from_links([normalized])

        for link in page.external_links:
            normalized = normalize_url(link.target_url, page.url)
            if normalized:
                self._external_urls.add(normalized)

    async def _parse_sitemaps(self, sitemap_urls: list[str], client: httpx.AsyncClient) -> list[str]:
        """Parse XML sitemaps and extract URLs."""
        from ..analyzers.sitemap_parser import SitemapParser
        parser = SitemapParser()
        all_urls = []

        for sitemap_url in sitemap_urls:
            try:
                urls = await parser.parse_sitemap(sitemap_url, client)
                all_urls.extend(urls)
            except Exception as e:
                logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")

        logger.info(f"Found {len(all_urls)} URLs in sitemaps")
        return all_urls

    async def _check_external_links(self):
        """Check status codes of external links."""
        logger.info(f"Checking {len(self._external_urls)} external links")
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            follow_redirects=True,
            verify=True,
        ) as client:
            semaphore = asyncio.Semaphore(20)

            async def check_url(url: str):
                async with semaphore:
                    try:
                        if self._evasion:
                            await asyncio.sleep(0.5)
                        response = await client.head(url)
                        return url, response.status_code
                    except Exception:
                        return url, 0

            tasks = [check_url(url) for url in list(self._external_urls)[:1000]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, tuple):
                    url, status = result
                    # Update any links pointing to this URL
                    for page in self.result.pages:
                        for link in page.external_links:
                            if normalize_url(link.target_url, page.url) == url:
                                link.status_code = status

    def _build_inlink_map(self):
        """Build a map of inlinks and compute link metrics."""
        for page in self.result.pages:
            for link in page.internal_links:
                target = normalize_url(link.target_url, page.url)
                if target:
                    if target not in self.result.inlink_map:
                        self.result.inlink_map[target] = []
                    self.result.inlink_map[target].append(page.url)

        total_inlinks = sum(len(v) for v in self.result.inlink_map.values()) or 1

        # Update inlink/outlink counts on pages
        for page in self.result.pages:
            sources = self.result.inlink_map.get(page.url, [])
            page.inlinks_count = len(sources)
            page.unique_inlinks = len(set(sources))
            page.pct_of_total = round(page.inlinks_count / total_inlinks * 100, 2)

            page.outlinks_count = len(page.internal_links) + len(page.external_links)
            page.unique_outlinks = len(set(l.target_url for l in page.internal_links))
            page.external_outlinks = len(page.external_links)
            page.unique_external_outlinks = len(set(l.target_url for l in page.external_links))

        # Compute Link Score (simplified PageRank, 20 iterations)
        pages_by_url = {p.url: p for p in self.result.pages}
        n = len(pages_by_url)
        if n > 0:
            scores = {url: 1.0 / n for url in pages_by_url}
            damping = 0.85
            for _ in range(20):
                new_scores = {}
                for url in pages_by_url:
                    rank = (1 - damping) / n
                    for source_url in self.result.inlink_map.get(url, []):
                        if source_url in pages_by_url:
                            src_page = pages_by_url[source_url]
                            out_count = src_page.outlinks_count or 1
                            rank += damping * scores.get(source_url, 0) / out_count
                    new_scores[url] = rank
                scores = new_scores
            # Normalize to 0-100
            max_score = max(scores.values()) if scores else 1
            for url, page in pages_by_url.items():
                page.link_score = round(scores.get(url, 0) / max_score * 100, 2) if max_score > 0 else 0

    def _extract_charset(self, response) -> str:
        """Extract character encoding from response."""
        content_type = response.headers.get('content-type', '')
        if 'charset=' in content_type:
            return content_type.split('charset=')[-1].strip().rstrip(';')
        return response.encoding or 'utf-8'
