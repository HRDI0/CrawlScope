"""
Security Analyzer.
Mirrors Screaming Frog's Security tab functionality.
Checks HTTPS, mixed content, security headers, SSL certificates.
"""
import re
import ssl
import socket
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional

from seo_spider.core.models import PageData, SecurityData

logger = logging.getLogger("seo_spider.security")


class SecurityAnalyzer:
    """Analyze security aspects of a crawled page."""

    def analyze(self, page: PageData):
        """Run all security checks on a page."""
        if not page.response_headers:
            return

        security = SecurityData()
        parsed = urlparse(page.url)
        security.is_https = parsed.scheme == 'https'

        # Security headers
        headers = {k.lower(): v for k, v in page.response_headers.items()}

        security.hsts_enabled = 'strict-transport-security' in headers
        security.x_frame_options = headers.get('x-frame-options', '')
        security.x_content_type_options = headers.get('x-content-type-options', '')
        security.x_xss_protection = headers.get('x-xss-protection', '')
        security.content_security_policy = headers.get('content-security-policy', '')[:200]
        security.referrer_policy = headers.get('referrer-policy', '')
        security.permissions_policy = headers.get('permissions-policy', '')[:200]

        # X-Robots-Tag
        if 'x-robots-tag' in headers:
            page.x_robots_tag = headers['x-robots-tag']

        # Mixed content detection (for HTTPS pages)
        if security.is_https and page.body_text:
            mixed_urls = self._detect_mixed_content(page)
            security.has_mixed_content = len(mixed_urls) > 0
            security.mixed_content_urls = mixed_urls[:20]  # Limit to 20

        page.security = security

    def _detect_mixed_content(self, page: PageData) -> list[str]:
        """Detect HTTP resources loaded on an HTTPS page."""
        mixed = []

        # Check internal links
        for link in page.internal_links:
            if link.target_url.startswith('http://'):
                mixed.append(link.target_url)

        # Check images
        for img in page.images:
            if img.src.startswith('http://'):
                mixed.append(img.src)

        # Check CSS
        for css in page.css_resources:
            if css.url.startswith('http://'):
                mixed.append(css.url)

        # Check JS
        for js in page.js_resources:
            if js.url.startswith('http://'):
                mixed.append(js.url)

        return mixed

    @staticmethod
    async def check_ssl_certificate(hostname: str) -> dict:
        """Check SSL certificate details for a hostname."""
        result = {
            "valid": False,
            "issuer": "",
            "subject": "",
            "not_before": "",
            "not_after": "",
            "days_remaining": 0,
            "error": "",
        }

        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if cert:
                        result["valid"] = True
                        result["issuer"] = str(cert.get('issuer', ''))
                        result["subject"] = str(cert.get('subject', ''))
                        result["not_before"] = cert.get('notBefore', '')
                        result["not_after"] = cert.get('notAfter', '')

                        # Calculate days remaining
                        not_after = cert.get('notAfter', '')
                        if not_after:
                            try:
                                expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                                remaining = (expiry - datetime.utcnow()).days
                                result["days_remaining"] = remaining
                            except Exception:
                                pass
        except Exception as e:
            result["error"] = str(e)

        return result
