"""
Robots.txt parser and manager.
Mirrors Screaming Frog's robots.txt handling including custom robots.txt testing.
"""
import asyncio
import logging
import re
from urllib.parse import urlparse, urljoin
from typing import Optional
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger("seo_spider.robots")


@dataclass
class RobotsRule:
    """A single robots.txt rule."""
    user_agent: str = "*"
    disallowed: list[str] = field(default_factory=list)
    allowed: list[str] = field(default_factory=list)
    crawl_delay: Optional[float] = None
    sitemaps: list[str] = field(default_factory=list)


class RobotsParser:
    """Parse and evaluate a robots.txt file."""

    def __init__(self, content: str = ""):
        self.content = content
        self.rules: list[RobotsRule] = []
        self.sitemaps: list[str] = []
        self._parse(content)

    def _parse(self, content: str):
        """Parse robots.txt content into rules."""
        if not content:
            return

        current_rule = None
        for line in content.split('\n'):
            line = line.strip()

            # Remove comments
            if '#' in line:
                line = line[:line.index('#')].strip()

            if not line:
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            directive = parts[0].strip().lower()
            value = parts[1].strip()

            if directive == 'user-agent':
                current_rule = RobotsRule(user_agent=value.lower())
                self.rules.append(current_rule)
            elif directive == 'disallow' and current_rule:
                if value:
                    current_rule.disallowed.append(value)
            elif directive == 'allow' and current_rule:
                if value:
                    current_rule.allowed.append(value)
            elif directive == 'crawl-delay' and current_rule:
                try:
                    current_rule.crawl_delay = float(value)
                except ValueError:
                    pass
            elif directive == 'sitemap':
                self.sitemaps.append(value)
                if current_rule:
                    current_rule.sitemaps.append(value)

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """Check if a URL is allowed for a given user agent."""
        path = urlparse(url).path
        if not path:
            path = '/'

        ua_lower = user_agent.lower()

        # Find the most specific matching rule
        matching_rules = []
        for rule in self.rules:
            if rule.user_agent == '*' or rule.user_agent == ua_lower:
                matching_rules.append(rule)

        if not matching_rules:
            return True

        # Check allow rules first (more specific), then disallow
        for rule in matching_rules:
            # Check explicit allows
            for pattern in rule.allowed:
                if self._path_matches(path, pattern):
                    return True

            # Check disallows
            for pattern in rule.disallowed:
                if self._path_matches(path, pattern):
                    return False

        return True

    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if a path matches a robots.txt pattern."""
        if not pattern:
            return False

        # Convert robots.txt pattern to regex
        # * matches any sequence, $ matches end
        regex_pattern = re.escape(pattern)
        regex_pattern = regex_pattern.replace(r'\*', '.*')
        if regex_pattern.endswith(r'\$'):
            regex_pattern = regex_pattern[:-2] + '$'
        else:
            regex_pattern = regex_pattern + '.*'

        regex_pattern = '^' + regex_pattern
        try:
            return bool(re.match(regex_pattern, path))
        except re.error:
            return False

    def get_crawl_delay(self, user_agent: str = "*") -> Optional[float]:
        """Get the crawl delay for a user agent."""
        ua_lower = user_agent.lower()
        for rule in self.rules:
            if rule.user_agent == ua_lower and rule.crawl_delay is not None:
                return rule.crawl_delay
        for rule in self.rules:
            if rule.user_agent == '*' and rule.crawl_delay is not None:
                return rule.crawl_delay
        return None

    def get_sitemaps(self) -> list[str]:
        """Get all sitemap URLs declared in robots.txt."""
        return list(set(self.sitemaps))

    def get_disallowed_paths(self, user_agent: str = "*") -> list[str]:
        """Get all disallowed paths for a user agent."""
        paths = []
        ua_lower = user_agent.lower()
        for rule in self.rules:
            if rule.user_agent in ('*', ua_lower):
                paths.extend(rule.disallowed)
        return paths


class RobotsManager:
    """
    Manage robots.txt files for multiple domains.
    Caches parsed robots.txt per domain.
    """

    def __init__(self, respect_robots: bool = True, custom_user_agent: str = "*"):
        self.respect_robots = respect_robots
        self.custom_user_agent = custom_user_agent
        self._cache: dict[str, RobotsParser] = {}
        self._fetching: dict[str, asyncio.Event] = {}

    async def fetch_and_parse(self, base_url: str, client: httpx.AsyncClient) -> RobotsParser:
        """Fetch and parse robots.txt for a domain."""
        parsed = urlparse(base_url)
        domain_key = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{domain_key}/robots.txt"

        if domain_key in self._cache:
            return self._cache[domain_key]

        # Prevent duplicate fetches
        if domain_key in self._fetching:
            await self._fetching[domain_key].wait()
            return self._cache.get(domain_key, RobotsParser())

        self._fetching[domain_key] = asyncio.Event()

        try:
            response = await client.get(robots_url, timeout=10.0)
            if response.status_code == 200:
                parser = RobotsParser(response.text)
            else:
                parser = RobotsParser()  # No robots.txt = everything allowed
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {robots_url}: {e}")
            parser = RobotsParser()

        self._cache[domain_key] = parser
        self._fetching[domain_key].set()
        return parser

    async def is_allowed(self, url: str, client: httpx.AsyncClient) -> bool:
        """Check if crawling a URL is allowed by robots.txt."""
        if not self.respect_robots:
            return True

        parser = await self.fetch_and_parse(url, client)
        return parser.is_allowed(url, self.custom_user_agent)

    async def get_sitemaps_for_domain(self, base_url: str, client: httpx.AsyncClient) -> list[str]:
        """Get sitemap URLs from robots.txt."""
        parser = await self.fetch_and_parse(base_url, client)
        return parser.get_sitemaps()

    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """Get crawl delay for a domain from cached robots.txt."""
        for key, parser in self._cache.items():
            if domain in key:
                return parser.get_crawl_delay(self.custom_user_agent)
        return None
