"""
JavaScript Rendering Engine using Playwright (headless Chromium).
Mirrors Screaming Frog's JavaScript rendering via its built-in Chromium WRS.

Supports:
- Full page rendering with JS execution
- AJAX/XHR waiting
- Dynamic content extraction
- SPA frameworks (React, Angular, Vue.js)
- Resource blocking (images, fonts, media)
- Stealth mode integration for anti-bot evasion
"""
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("seo_spider.renderer")


class JSRenderer:
    """
    Headless Chromium-based JavaScript renderer.

    Uses Playwright to render pages in a real browser environment,
    executing JavaScript to capture dynamically generated content and links.
    """

    def __init__(
        self,
        browser_instances: int = 3,
        wait_time: float = 5.0,
        ajax_timeout: float = 10.0,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        block_resources: list[str] = None,
        stealth_scripts: list[str] = None,
        user_agent: str = None,
    ):
        self.browser_instances = browser_instances
        self.wait_time = wait_time
        self.ajax_timeout = ajax_timeout
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.block_resources = block_resources or []
        self.stealth_scripts = stealth_scripts or []
        self.user_agent = user_agent

        self._browser = None
        self._context_pool: list = []
        self._semaphore = asyncio.Semaphore(browser_instances)
        self._initialized = False

    async def initialize(self):
        """Initialize Playwright and launch browser."""
        if self._initialized:
            return

        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()

            # Launch Chromium with stealth-friendly settings
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--start-maximized',
                ],
            )

            # Pre-create browser contexts (connection pool)
            for _ in range(self.browser_instances):
                context = await self._create_context()
                self._context_pool.append(context)

            self._initialized = True
            logger.info(f"JS Renderer initialized with {self.browser_instances} browser instances")

        except ImportError:
            logger.error(
                "Playwright not installed. Install with: "
                "pip install playwright && playwright install chromium"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize JS renderer: {e}")
            raise

    async def _create_context(self):
        """Create a new browser context with stealth settings."""
        context_options = {
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "java_script_enabled": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
        }

        if self.user_agent:
            context_options["user_agent"] = self.user_agent

        context = await self._browser.new_context(**context_options)

        # Inject stealth scripts
        for script in self.stealth_scripts:
            await context.add_init_script(script)

        # Default stealth: override navigator.webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = { runtime: {} };
        """)

        return context

    @asynccontextmanager
    async def _get_context(self):
        """Get a browser context from the pool."""
        async with self._semaphore:
            if self._context_pool:
                context = self._context_pool.pop()
            else:
                context = await self._create_context()
            try:
                yield context
            finally:
                self._context_pool.append(context)

    async def render(self, url: str) -> Optional[str]:
        """
        Render a page with JavaScript and return the rendered HTML.

        Process:
        1. Navigate to URL
        2. Wait for network idle
        3. Wait additional time for JS execution
        4. Wait for AJAX requests to complete
        5. Return rendered DOM HTML
        """
        if not self._initialized:
            await self.initialize()

        async with self._get_context() as context:
            page = await context.new_page()

            try:
                # Set up resource blocking
                if self.block_resources:
                    await page.route("**/*", self._route_handler)

                # Navigate to URL
                response = await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=int(self.ajax_timeout * 1000),
                )

                if not response:
                    logger.warning(f"No response for {url}")
                    return None

                # Wait for additional JavaScript execution
                await self._wait_for_content(page)

                # Get the rendered HTML
                rendered_html = await page.content()

                logger.debug(f"Rendered {url} - {len(rendered_html)} bytes")
                return rendered_html

            except Exception as e:
                logger.warning(f"Rendering failed for {url}: {e}")
                return None
            finally:
                await page.close()

    async def render_batch(self, urls: list[str]) -> dict[str, Optional[str]]:
        """Render multiple URLs concurrently."""
        if not self._initialized:
            await self.initialize()

        tasks = {url: self.render(url) for url in urls}
        results = {}

        for url, coro in tasks.items():
            try:
                results[url] = await coro
            except Exception as e:
                logger.error(f"Batch render error for {url}: {e}")
                results[url] = None

        return results

    async def render_and_extract(self, url: str) -> dict:
        """
        Render a page and extract both HTML and JavaScript-generated content.
        Returns rendered HTML plus any dynamically loaded data.
        """
        if not self._initialized:
            await self.initialize()

        async with self._get_context() as context:
            page = await context.new_page()

            try:
                # Capture network requests for resource analysis
                requests_log = []

                async def log_request(request):
                    requests_log.append({
                        "url": request.url,
                        "method": request.method,
                        "resource_type": request.resource_type,
                    })

                page.on("request", log_request)

                if self.block_resources:
                    await page.route("**/*", self._route_handler)

                response = await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=int(self.ajax_timeout * 1000),
                )

                await self._wait_for_content(page)

                # Extract comprehensive data
                rendered_html = await page.content()

                # Extract all links via JS (catches dynamically added links)
                js_links = await page.evaluate("""
                    () => {
                        const links = [];
                        document.querySelectorAll('a[href]').forEach(a => {
                            links.push({
                                href: a.href,
                                text: a.textContent.trim(),
                                rel: a.rel,
                                target: a.target,
                            });
                        });
                        return links;
                    }
                """)

                # Extract meta tags via JS
                js_meta = await page.evaluate("""
                    () => {
                        const meta = {};
                        document.querySelectorAll('meta').forEach(m => {
                            const name = m.getAttribute('name') || m.getAttribute('property') || '';
                            const content = m.getAttribute('content') || '';
                            if (name) meta[name] = content;
                        });
                        meta.title = document.title;
                        return meta;
                    }
                """)

                # Extract structured data via JS
                js_structured_data = await page.evaluate("""
                    () => {
                        const data = [];
                        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
                            try {
                                data.push(JSON.parse(s.textContent));
                            } catch(e) {}
                        });
                        return data;
                    }
                """)

                return {
                    "html": rendered_html,
                    "links": js_links,
                    "meta": js_meta,
                    "structured_data": js_structured_data,
                    "network_requests": requests_log,
                    "status_code": response.status if response else 0,
                }

            except Exception as e:
                logger.warning(f"Render and extract failed for {url}: {e}")
                return {"html": None, "links": [], "meta": {}, "structured_data": [], "network_requests": []}
            finally:
                await page.close()

    async def _wait_for_content(self, page):
        """
        Wait for JavaScript content to fully load.
        Uses multiple strategies:
        1. Network idle
        2. DOM content loaded
        3. Custom wait time
        4. Wait for specific selectors (SPA frameworks)
        """
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle", timeout=int(self.ajax_timeout * 1000))
        except Exception:
            pass

        # Additional wait for late-loading JS
        if self.wait_time > 0:
            await asyncio.sleep(self.wait_time)

        # Try to wait for common SPA framework indicators
        spa_selectors = [
            "[data-reactroot]",      # React
            "[ng-version]",          # Angular
            "[data-v-]",             # Vue.js
            "#__next",               # Next.js
            "#__nuxt",               # Nuxt.js
            "[data-gatsby]",         # Gatsby
        ]

        for selector in spa_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Found SPA indicator, wait a bit more for hydration
                    await asyncio.sleep(1.0)
                    break
            except Exception:
                pass

    async def _route_handler(self, route):
        """Handle resource blocking based on configuration."""
        resource_type = route.request.resource_type

        if resource_type in self.block_resources:
            await route.abort()
        else:
            await route.continue_()

    async def get_page_screenshot(self, url: str, output_path: str):
        """Take a screenshot of a rendered page."""
        if not self._initialized:
            await self.initialize()

        async with self._get_context() as context:
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="networkidle")
                await self._wait_for_content(page)
                await page.screenshot(path=output_path, full_page=True)
            finally:
                await page.close()

    async def close(self):
        """Clean up browser resources."""
        if self._browser:
            for context in self._context_pool:
                await context.close()
            await self._browser.close()
            await self._playwright.stop()
            self._initialized = False
            logger.info("JS Renderer closed")
