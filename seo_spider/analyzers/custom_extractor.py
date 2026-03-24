"""
Custom Extraction Engine.
Mirrors Screaming Frog's Custom Extraction feature.
Supports XPath, CSS Selectors, and Regex extraction.
"""
import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger("seo_spider.custom_extractor")


class CustomExtractor:
    """
    Extract custom data from HTML pages using configurable rules.

    Extraction types:
    - XPath: Use lxml XPath expressions
    - CSS Selector: Use CSS selectors via BeautifulSoup
    - Regex: Use regular expressions on raw HTML
    """

    def __init__(self, rules: list[dict] = None):
        """
        Initialize with extraction rules.
        Each rule: {"name": str, "type": "xpath|css|regex", "value": str, "extract": "text|html|attribute", "attribute": str}
        """
        self.rules = rules or []

    def extract(self, html: str, url: str = "") -> list[dict]:
        """
        Run all extraction rules against HTML.
        Returns list of {"name": str, "values": list[str]}
        """
        results = []

        for rule in self.rules:
            name = rule.get('name', 'unnamed')
            rule_type = rule.get('type', 'css')
            pattern = rule.get('value', '')
            extract_type = rule.get('extract', 'text')
            attribute = rule.get('attribute', '')

            try:
                if rule_type == 'css':
                    values = self._extract_css(html, pattern, extract_type, attribute)
                elif rule_type == 'xpath':
                    values = self._extract_xpath(html, pattern, extract_type, attribute)
                elif rule_type == 'regex':
                    values = self._extract_regex(html, pattern)
                else:
                    values = []

                results.append({
                    'name': name,
                    'values': values,
                    'count': len(values),
                })
            except Exception as e:
                logger.warning(f"Extraction error for rule '{name}': {e}")
                results.append({
                    'name': name,
                    'values': [],
                    'error': str(e),
                })

        return results

    def _extract_css(self, html: str, selector: str, extract_type: str, attribute: str) -> list[str]:
        """Extract using CSS selectors."""
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        values = []

        for el in elements:
            if extract_type == 'text':
                values.append(el.get_text(strip=True))
            elif extract_type == 'html':
                values.append(str(el))
            elif extract_type == 'attribute' and attribute:
                val = el.get(attribute, '')
                if val:
                    values.append(val)
            else:
                values.append(el.get_text(strip=True))

        return values

    def _extract_xpath(self, html: str, xpath: str, extract_type: str, attribute: str) -> list[str]:
        """Extract using XPath expressions."""
        from lxml import etree

        tree = etree.HTML(html)
        if tree is None:
            return []

        results = tree.xpath(xpath)
        values = []

        for result in results:
            if isinstance(result, str):
                values.append(result)
            elif hasattr(result, 'text'):
                if extract_type == 'html':
                    values.append(etree.tostring(result, encoding='unicode'))
                elif extract_type == 'attribute' and attribute:
                    val = result.get(attribute, '')
                    if val:
                        values.append(val)
                else:
                    text = result.text or ''
                    values.append(text.strip())

        return values

    def _extract_regex(self, html: str, pattern: str) -> list[str]:
        """Extract using regular expressions."""
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        values = []
        for match in matches[:100]:  # Limit to 100 matches
            if isinstance(match, tuple):
                values.append(match[0] if match else '')
            else:
                values.append(match)
        return values

    def add_rule(self, name: str, rule_type: str, value: str, **kwargs):
        """Add a new extraction rule."""
        rule = {
            'name': name,
            'type': rule_type,
            'value': value,
            **kwargs,
        }
        self.rules.append(rule)

    def remove_rule(self, name: str):
        """Remove an extraction rule by name."""
        self.rules = [r for r in self.rules if r.get('name') != name]
