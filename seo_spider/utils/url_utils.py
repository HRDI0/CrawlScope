"""
URL normalization and domain utilities.
"""
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode, unquote
import tldextract
import re

# Use snapshot fallback so tldextract works offline / in sandboxed environments
_tld_extract = tldextract.TLDExtract(suffix_list_urls=None)  # uses bundled snapshot


def normalize_url(url: str, base_url: str = None) -> str | None:
    """
    Normalize a URL:
    - Resolve relative URLs against base
    - Lowercase scheme and host
    - Remove default ports
    - Remove fragments
    - Sort query parameters
    - Remove trailing slashes on paths (optional)
    """
    if not url or url.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return None

    # Resolve relative URLs
    if base_url and not url.startswith(('http://', 'https://', '//')):
        url = urljoin(base_url, url)
    elif url.startswith('//'):
        url = 'https:' + url

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    if parsed.scheme not in ('http', 'https'):
        return None

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ''

    # Remove default ports
    port = parsed.port
    if (scheme == 'http' and port == 80) or (scheme == 'https' and port == 443):
        port = None

    netloc = host
    if port:
        netloc = f"{host}:{port}"

    # Decode and normalize path
    path = unquote(parsed.path) or '/'

    # Sort query parameters
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        sorted_params = sorted(params.items())
        query = urlencode(sorted_params, doseq=True)
    else:
        query = ''

    # Remove fragment
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, ''))
    return normalized


def extract_domain(url: str) -> str:
    """Extract registered domain from URL (e.g., 'example.com')."""
    ext = _tld_extract(url)
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain


def extract_subdomain(url: str) -> str:
    """Extract full subdomain from URL (e.g., 'blog.example.com')."""
    ext = _tld_extract(url)
    if ext.subdomain:
        return f"{ext.subdomain}.{ext.domain}.{ext.suffix}"
    return f"{ext.domain}.{ext.suffix}"


def get_fqdn(url: str) -> str:
    """Get fully qualified domain name from URL."""
    parsed = urlparse(url)
    return parsed.hostname.lower() if parsed.hostname else ''


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs share the same registered domain."""
    return extract_domain(url1) == extract_domain(url2)


def is_subdomain_of(url: str, domain: str) -> bool:
    """Check if a URL is a subdomain of the given domain."""
    url_domain = extract_domain(url)
    target_domain = extract_domain(domain)
    return url_domain == target_domain


def get_url_depth(url: str) -> int:
    """Calculate the depth of a URL based on path segments."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return 0
    return len(path.split('/'))


def extract_all_urls_from_text(text: str) -> list[str]:
    """Extract all URLs from raw text using regex."""
    pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]*'
    return re.findall(pattern, text)
