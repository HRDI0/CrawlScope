# Python SEO Spider

A full-featured SEO crawling and analysis tool built in Python, inspired by Screaming Frog SEO Spider. Crawl websites, analyze on-page SEO factors, detect technical issues, and export Screaming Frog-compatible reports.

> **[한국어 README](README_KR.md)**

## Features

### Crawling Engine
- Async HTTP crawling with configurable concurrency and depth limits
- Subdomain discovery and cross-subdomain crawling
- Robots.txt compliance with configurable override
- JavaScript rendering via Playwright (before/after comparison)
- HTTP/2 support
- Sitemap.xml parsing and URL seeding

### Bot Detection Evasion
- Rotating User-Agent headers with realistic browser fingerprints
- Playwright Stealth mode for JS-rendered pages
- Configurable request delays and rate limiting
- Proxy rotation support

### On-Page Analysis
- Title tags, meta descriptions, meta keywords (length + pixel width)
- H1/H2 heading extraction and analysis
- Word count, sentence count, text-to-HTML ratio
- Flesch Reading Ease score and readability grading
- Canonical tags (HTML + HTTP header)
- Meta robots / X-Robots-Tag directives
- rel="next"/rel="prev" pagination detection
- Hreflang annotations

### Link Analysis
- Internal/external link counting with unique deduplication
- Inlink mapping and aggregation
- Internal PageRank (Link Score) calculation (damping=0.85, 20 iterations)
- Crawl depth and folder depth tracking
- Orphan page detection

### Technical SEO
- HTTP status code monitoring (2xx/3xx/4xx/5xx)
- Redirect chain tracking (type, hops, final URL)
- Security header analysis (HTTPS, HSTS, CSP, X-Frame-Options, etc.)
- Response time measurement
- Duplicate content detection (hash-based + near-duplicate similarity)
- Duplicate title and meta description detection

### JavaScript Rendering
- Playwright-based headless browser rendering
- Before/after comparison: title, H1, meta description, canonical, word count
- JS Word Count % calculation (content added by JavaScript)
- Detection of rendering-dependent meta tags

### Structured Data
- JSON-LD, Microdata, RDFa extraction
- Schema.org type identification
- Validation error/warning counting

### Custom Analysis
- Custom CSS/XPath/Regex extraction rules
- Custom search pattern matching (Contains/Does Not Contain)

### Export Formats

**27 CSV files** matching Screaming Frog format:

| File | Description |
|------|-------------|
| `internal_all.csv` | All internal pages (63 columns) |
| `external_all.csv` | External link aggregation |
| `images_all.csv` | Image analysis with alt text and dimensions |
| `css.csv` | CSS resources |
| `javascript.csv` | JavaScript resources |
| `hreflang_all.csv` | Hreflang annotations |
| `structured_data_all.csv` | Structured data types and validation |
| `response_codes_all.csv` | HTTP response code analysis |
| `security_all.csv` | Security headers |
| `content_all.csv` | Content quality and readability |
| `links_all.csv` | Link structure and Link Score |
| `canonicals_all.csv` | Canonical tag analysis |
| `directives_all.csv` | Crawl directives (robots, canonical) |
| `h1_all.csv` | H1 tag analysis |
| `h2_all.csv` | H2 tag analysis |
| `meta_keywords_all.csv` | Meta keywords |
| `pagination_all.csv` | Pagination (rel next/prev) |
| `url_all.csv` | URL structure analysis |
| `page_titles_duplicate.csv` | Duplicate page titles |
| `meta_description_duplicate.csv` | Duplicate meta descriptions |
| `javascript_all.csv` | JS rendering before/after comparison |
| `custom_extraction_all.csv` | Custom extraction results |
| `custom_search_all.csv` | Custom search matches |
| `issues.csv` | SEO issues with severity |
| `redirects.csv` | Redirect chains |
| `inlinks.csv` | Inlink aggregation |
| `sitemaps_all.csv` | Sitemap URLs |

Also exports:
- **XLSX** — Multi-sheet Excel workbook (26 sheets) with all the above
- **JSON** — Full crawl results + summary

### Web UI
- Carbon Design System (IBM) styled dark-theme interface
- 4-tab layout: Crawl settings, Results dashboard, Pages table, Sessions
- Real-time crawl progress polling
- Status code distribution chart
- Issues panel with severity indicators
- All crawl options configurable via UI toggles and inputs

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/python-seo-spider.git
cd python-seo-spider

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for JS rendering)
playwright install chromium
```

## Quick Start

### Command Line

```bash
# Basic crawl
python main.py https://example.com

# With options
python main.py https://example.com --max-pages 500 --depth 5 --js-rendering
```

### Web UI

```bash
# Start the web server
python web_server.py

# Open http://localhost:8000 in your browser
```

### Python API

```python
import asyncio
from seo_spider.core.crawler import SEOSpiderCrawler
from seo_spider.core.models import CrawlConfig
from seo_spider.exporters.csv_exporter import CSVExporter

config = CrawlConfig(
    start_url="https://example.com",
    max_pages=100,
    max_depth=3,
    rendering_mode="playwright",  # Enable JS rendering
    respect_robots_txt=True,
    concurrent_requests=5,
)

async def main():
    crawler = SEOSpiderCrawler(config)
    result = await crawler.crawl()

    # Export to CSV (27 files)
    exporter = CSVExporter("crawl_output/example")
    exporter.export_all(result)

asyncio.run(main())
```

## Output Structure

```
crawl_output/
└── example/              # Domain-based folder
    ├── internal_all.csv
    ├── external_all.csv
    ├── content_all.csv
    ├── links_all.csv
    ├── security_all.csv
    ├── javascript_all.csv
    ├── ... (27 CSV files total)
    ├── crawl_report.xlsx
    └── crawl_results.json
```

## Configuration

Copy `config_example.yaml` and customize:

```yaml
crawl:
  start_url: "https://example.com"
  max_pages: 1000
  max_depth: 10
  concurrent_requests: 5
  request_delay: 0.5
  respect_robots_txt: true

rendering:
  mode: "playwright"          # none | playwright
  wait_for: "networkidle"
  timeout: 30000

evasion:
  rotate_user_agent: true
  stealth_mode: true

export:
  formats: ["csv", "xlsx", "json"]
  output_dir: "crawl_output"
```

## Project Structure

```
python-seo-spider/
├── main.py                    # CLI entry point
├── web_server.py              # Web UI server
├── web_ui.html                # Carbon Design System SPA
├── requirements.txt
├── config_example.yaml
├── setup.py
├── test_all.py
├── seo_spider/
│   ├── core/
│   │   ├── models.py          # Data models (PageData, CrawlResult, CrawlConfig)
│   │   ├── crawler.py         # Main async crawler engine
│   │   ├── robots_parser.py   # Robots.txt handling
│   │   └── subdomain_discovery.py
│   ├── analyzers/
│   │   ├── html_parser.py     # HTML analysis (titles, meta, headings, readability)
│   │   ├── issue_detector.py  # SEO issue detection
│   │   ├── duplicate_detector.py
│   │   ├── security_analyzer.py
│   │   ├── structured_data_analyzer.py
│   │   ├── sitemap_parser.py
│   │   ├── custom_extractor.py
│   │   └── visualization.py
│   ├── exporters/
│   │   ├── csv_exporter.py    # 27 Screaming Frog-compatible CSVs
│   │   ├── xlsx_exporter.py   # 26-sheet Excel workbook
│   │   ├── json_exporter.py
│   │   └── report_generator.py
│   ├── renderers/
│   │   └── js_renderer.py     # Playwright JS rendering
│   ├── evasion/
│   │   ├── anti_bot.py        # Bot detection evasion
│   │   ├── fingerprint.py     # Browser fingerprint generation
│   │   └── proxy_rotator.py
│   ├── config/
│   │   └── settings.py
│   └── utils/
│       ├── url_utils.py
│       ├── hash_utils.py
│       └── logging_config.py
├── crawl_output/              # Generated output (gitignored)
├── 산출물_컬럼_명세서.xlsx      # Column specification document
└── SEO_GEO_분석_가이드.md      # SEO/GEO analysis guide
```

## Documentation

- **[산출물_컬럼_명세서.xlsx](산출물_컬럼_명세서.xlsx)** — Complete column specification for all 27 CSV files, 26 XLSX sheets, and JSON fields (Korean/English)
- **[SEO_GEO_분석_가이드.md](SEO_GEO_분석_가이드.md)** — Guide for using crawl data in SEO/GEO proposals with visualization strategies and Python analysis code examples

## Requirements

- Python 3.10+
- Playwright (for JavaScript rendering)
- See `requirements.txt` for full dependency list

## License

MIT
