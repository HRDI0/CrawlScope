"""
Subdomain discovery module.
Uses multiple methods to discover all subdomains of a target domain:
1. DNS brute force with common subdomain wordlist
2. Certificate Transparency logs (crt.sh)
3. Link analysis during crawling
4. Sitemap parsing
5. DNS zone transfer attempt
"""
import asyncio
import json
import re
import logging
from typing import Optional

import dns.resolver
import dns.zone
import dns.query
import httpx
import tldextract

_tld_extract = tldextract.TLDExtract(suffix_list_urls=None)

logger = logging.getLogger("seo_spider.subdomain")

# Common subdomain prefixes for brute-force discovery
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail",
    "blog", "shop", "store", "app", "api", "dev", "staging",
    "test", "beta", "alpha", "demo", "preview", "sandbox",
    "admin", "portal", "dashboard", "panel", "manage", "cms",
    "cdn", "static", "assets", "media", "img", "images", "files",
    "docs", "doc", "help", "support", "wiki", "kb", "knowledge",
    "forum", "community", "social", "connect", "chat", "talk",
    "status", "monitor", "health", "metrics", "analytics",
    "m", "mobile", "touch",
    "en", "es", "fr", "de", "ja", "ko", "zh", "pt", "ru",
    "news", "press", "events", "careers", "jobs", "about",
    "login", "auth", "sso", "oauth", "id", "account", "accounts",
    "payments", "billing", "checkout", "cart", "order", "orders",
    "search", "go", "redirect", "link", "links", "url",
    "git", "svn", "repo", "code", "ci", "cd", "jenkins", "build",
    "vpn", "remote", "rdp", "ssh", "proxy",
    "ns1", "ns2", "ns3", "dns", "dns1", "dns2",
    "mx", "mx1", "mx2", "relay",
    "db", "database", "sql", "mysql", "postgres", "mongo", "redis",
    "s3", "storage", "backup", "archive",
    "internal", "intranet", "extranet", "corp", "corporate",
    "www1", "www2", "web", "web1", "web2",
    "qa", "uat", "preprod", "pre", "stage",
    "calendar", "meet", "video", "conference",
    "marketplace", "partners", "affiliate",
    "graphql", "rest", "v1", "v2", "v3",
]


class SubdomainDiscovery:
    """Discover all subdomains of a target domain using multiple methods."""

    def __init__(self, domain: str, methods: list[str] = None):
        self.domain = self._clean_domain(domain)
        self.methods = methods or ["dns", "crt_sh", "links"]
        self.discovered: set[str] = set()
        self._resolver = dns.resolver.Resolver()
        self._resolver.timeout = 5
        self._resolver.lifetime = 10

    def _clean_domain(self, domain: str) -> str:
        """Extract the registered domain."""
        ext = _tld_extract(domain)
        return f"{ext.domain}.{ext.suffix}"

    async def discover_all(self) -> set[str]:
        """Run all configured discovery methods and return found subdomains."""
        tasks = []

        if "dns" in self.methods:
            tasks.append(self._dns_bruteforce())
        if "crt_sh" in self.methods:
            tasks.append(self._crt_sh_search())
        if "dns_transfer" in self.methods:
            tasks.append(self._dns_zone_transfer())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, set):
                self.discovered.update(result)
            elif isinstance(result, Exception):
                logger.warning(f"Subdomain discovery error: {result}")

        # Always include the base domain
        self.discovered.add(self.domain)
        self.discovered.add(f"www.{self.domain}")

        logger.info(f"Discovered {len(self.discovered)} subdomains for {self.domain}")
        return self.discovered

    async def _dns_bruteforce(self) -> set[str]:
        """Brute force common subdomain prefixes via DNS resolution."""
        found = set()
        semaphore = asyncio.Semaphore(50)  # Limit concurrent DNS queries

        async def check_subdomain(prefix: str):
            async with semaphore:
                fqdn = f"{prefix}.{self.domain}"
                try:
                    loop = asyncio.get_event_loop()
                    answers = await loop.run_in_executor(
                        None, lambda: self._resolver.resolve(fqdn, 'A')
                    )
                    if answers:
                        found.add(fqdn)
                        logger.debug(f"DNS found: {fqdn}")
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                        dns.resolver.NoNameservers, dns.exception.Timeout):
                    pass
                except Exception as e:
                    logger.debug(f"DNS error for {fqdn}: {e}")

        tasks = [check_subdomain(prefix) for prefix in COMMON_SUBDOMAINS]
        await asyncio.gather(*tasks)

        logger.info(f"DNS brute force found {len(found)} subdomains")
        return found

    async def _crt_sh_search(self) -> set[str]:
        """Query Certificate Transparency logs via crt.sh."""
        found = set()
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for entry in data:
                        name = entry.get("name_value", "")
                        # Handle wildcard certs and multi-line entries
                        for subdomain in name.split("\n"):
                            subdomain = subdomain.strip().lstrip("*.")
                            if subdomain.endswith(self.domain):
                                found.add(subdomain)
        except Exception as e:
            logger.warning(f"crt.sh search failed: {e}")

        logger.info(f"crt.sh found {len(found)} subdomains")
        return found

    async def _dns_zone_transfer(self) -> set[str]:
        """Attempt DNS zone transfer (AXFR) - often blocked but worth trying."""
        found = set()
        try:
            loop = asyncio.get_event_loop()
            ns_records = await loop.run_in_executor(
                None, lambda: self._resolver.resolve(self.domain, 'NS')
            )
            for ns in ns_records:
                ns_host = str(ns).rstrip('.')
                try:
                    zone = await loop.run_in_executor(
                        None,
                        lambda: dns.zone.from_xfr(
                            dns.query.xfr(ns_host, self.domain, timeout=10)
                        )
                    )
                    for name, node in zone.nodes.items():
                        subdomain = f"{name}.{self.domain}"
                        if str(name) != '@':
                            found.add(subdomain)
                except Exception:
                    pass  # Zone transfer usually denied
        except Exception as e:
            logger.debug(f"Zone transfer failed: {e}")

        return found

    def add_from_links(self, urls: list[str]):
        """Add subdomains discovered from crawled links."""
        for url in urls:
            ext = _tld_extract(url)
            full_domain = f"{ext.domain}.{ext.suffix}"
            if full_domain == self.domain and ext.subdomain:
                fqdn = f"{ext.subdomain}.{ext.domain}.{ext.suffix}"
                if fqdn not in self.discovered:
                    self.discovered.add(fqdn)
                    logger.debug(f"Link discovery found: {fqdn}")

    def add_from_sitemap(self, urls: list[str]):
        """Add subdomains discovered from sitemaps."""
        self.add_from_links(urls)

    def get_all_subdomains(self) -> list[str]:
        """Return sorted list of all discovered subdomains."""
        return sorted(self.discovered)
