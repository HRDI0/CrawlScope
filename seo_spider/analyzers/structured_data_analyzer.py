"""
Structured Data Analyzer.
Validates JSON-LD, Microdata, and RDFa against Schema.org specifications.
Mirrors Screaming Frog's structured data validation.
"""
import json
import re
import logging
from typing import Optional

from seo_spider.core.models import StructuredDataItem

logger = logging.getLogger("seo_spider.structured_data")

# Common Schema.org types and their required properties
SCHEMA_REQUIRED_PROPERTIES = {
    "Article": ["headline", "author", "datePublished", "image"],
    "NewsArticle": ["headline", "author", "datePublished", "image"],
    "BlogPosting": ["headline", "author", "datePublished"],
    "Product": ["name", "image"],
    "Review": ["itemReviewed", "author"],
    "AggregateRating": ["ratingValue", "reviewCount"],
    "Organization": ["name"],
    "LocalBusiness": ["name", "address"],
    "Person": ["name"],
    "Event": ["name", "startDate", "location"],
    "Recipe": ["name", "image", "author"],
    "FAQPage": ["mainEntity"],
    "HowTo": ["name", "step"],
    "BreadcrumbList": ["itemListElement"],
    "WebSite": ["name", "url"],
    "WebPage": ["name"],
    "ImageObject": ["contentUrl"],
    "VideoObject": ["name", "uploadDate", "thumbnailUrl"],
    "SoftwareApplication": ["name", "operatingSystem"],
    "Course": ["name", "provider"],
    "JobPosting": ["title", "datePosted", "description", "hiringOrganization"],
    "Dataset": ["name", "description"],
}

# Google recommended properties for rich results
GOOGLE_RECOMMENDED = {
    "Article": ["dateModified", "mainEntityOfPage"],
    "Product": ["description", "offers", "aggregateRating", "review"],
    "LocalBusiness": ["telephone", "openingHours", "geo"],
    "Event": ["endDate", "description", "image", "offers"],
    "Recipe": ["cookTime", "prepTime", "nutrition", "recipeIngredient"],
    "FAQPage": [],
    "BreadcrumbList": [],
    "JobPosting": ["baseSalary", "employmentType", "jobLocation"],
}


class StructuredDataAnalyzer:
    """Validate and analyze structured data items."""

    def validate(self, item: StructuredDataItem) -> StructuredDataItem:
        """Validate a structured data item against Schema.org and Google requirements."""
        errors = []
        warnings = []

        data = item.raw_data
        schema_type = item.schema_type

        if not schema_type:
            errors.append("Missing @type property")
            item.validation_errors = errors
            item.is_valid = False
            return item

        # Check @context
        context = data.get('@context', '')
        if not context:
            errors.append("Missing @context property")
        elif 'schema.org' not in str(context):
            warnings.append(f"Non-standard @context: {context}")

        # Check required properties
        required = SCHEMA_REQUIRED_PROPERTIES.get(schema_type, [])
        for prop in required:
            if prop not in data:
                errors.append(f"Missing required property: {prop}")
            elif not data[prop]:
                errors.append(f"Empty required property: {prop}")

        # Check Google recommended properties
        recommended = GOOGLE_RECOMMENDED.get(schema_type, [])
        for prop in recommended:
            if prop not in data:
                warnings.append(f"Missing recommended property: {prop}")

        # Validate specific types
        if schema_type in ('Article', 'NewsArticle', 'BlogPosting'):
            self._validate_article(data, errors, warnings)
        elif schema_type == 'Product':
            self._validate_product(data, errors, warnings)
        elif schema_type == 'BreadcrumbList':
            self._validate_breadcrumb(data, errors, warnings)
        elif schema_type == 'FAQPage':
            self._validate_faq(data, errors, warnings)

        item.validation_errors = errors
        item.validation_warnings = warnings
        item.is_valid = len(errors) == 0
        return item

    def _validate_article(self, data: dict, errors: list, warnings: list):
        """Validate Article-type structured data."""
        # Check datePublished format
        date_pub = data.get('datePublished', '')
        if date_pub and not self._is_valid_date(str(date_pub)):
            errors.append(f"Invalid datePublished format: {date_pub}")

        # Check author
        author = data.get('author')
        if author:
            if isinstance(author, dict):
                if '@type' not in author:
                    warnings.append("Author missing @type")
                if 'name' not in author:
                    errors.append("Author missing name")
            elif isinstance(author, str):
                warnings.append("Author should be a Person or Organization object, not a string")

        # Check image
        image = data.get('image')
        if image:
            if isinstance(image, str) and not image.startswith(('http://', 'https://')):
                warnings.append("Image URL should be absolute")

    def _validate_product(self, data: dict, errors: list, warnings: list):
        """Validate Product-type structured data."""
        offers = data.get('offers')
        if offers:
            if isinstance(offers, dict):
                if 'price' not in offers and 'lowPrice' not in offers:
                    warnings.append("Offers missing price")
                if 'priceCurrency' not in offers:
                    warnings.append("Offers missing priceCurrency")
                if 'availability' not in offers:
                    warnings.append("Offers missing availability")

    def _validate_breadcrumb(self, data: dict, errors: list, warnings: list):
        """Validate BreadcrumbList structured data."""
        items = data.get('itemListElement', [])
        if not items:
            errors.append("BreadcrumbList has no items")
            return

        for i, item in enumerate(items):
            if isinstance(item, dict):
                if 'position' not in item:
                    errors.append(f"Breadcrumb item {i} missing position")
                if 'name' not in item and 'item' not in item:
                    errors.append(f"Breadcrumb item {i} missing name or item")

    def _validate_faq(self, data: dict, errors: list, warnings: list):
        """Validate FAQPage structured data."""
        entities = data.get('mainEntity', [])
        if not entities:
            errors.append("FAQPage has no mainEntity items")
            return

        if not isinstance(entities, list):
            entities = [entities]

        for i, entity in enumerate(entities):
            if isinstance(entity, dict):
                if entity.get('@type') != 'Question':
                    errors.append(f"FAQ item {i} @type should be 'Question'")
                if 'name' not in entity:
                    errors.append(f"FAQ item {i} missing question (name)")
                accepted = entity.get('acceptedAnswer', {})
                if not accepted:
                    errors.append(f"FAQ item {i} missing acceptedAnswer")
                elif isinstance(accepted, dict) and 'text' not in accepted:
                    errors.append(f"FAQ item {i} acceptedAnswer missing text")

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if a date string is in a valid ISO 8601 format."""
        iso_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
        ]
        return any(re.match(p, date_str) for p in iso_patterns)

    def validate_all(self, items: list[StructuredDataItem]) -> list[StructuredDataItem]:
        """Validate a list of structured data items."""
        return [self.validate(item) for item in items]
