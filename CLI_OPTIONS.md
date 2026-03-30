# CLI Options Reference / CLI 옵션 레퍼런스

> Python SEO Spider supports three commands: `crawl`, `list`, and `sitemap`.
>
> Python SEO Spider는 `crawl`, `list`, `sitemap` 세 가지 명령을 지원합니다.

---

## Commands / 명령어

### `crawl` — Spider Mode / 스파이더 모드

Starting from a single URL, follow links and crawl the entire site.

하나의 URL에서 시작하여 링크를 따라 전체 사이트를 크롤링합니다.

```bash
python main.py crawl <URL> [options]
```

### `list` — URL List Mode / URL 목록 모드

Crawl a specific set of URLs from a text file (one URL per line).

텍스트 파일에 있는 URL 목록을 크롤링합니다 (한 줄에 하나의 URL).

```bash
python main.py list <file> [options]
```

### `sitemap` — Sitemap Mode / 사이트맵 모드

Parse a sitemap XML and crawl all URLs found in it.

사이트맵 XML을 파싱하여 발견된 모든 URL을 크롤링합니다.

```bash
python main.py sitemap <sitemap_url> [options]
```

---

## `crawl` Command Options / `crawl` 명령 옵션

### Crawl Scope / 크롤 범위

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `url` | *(required)* | Start URL to crawl | 크롤 시작 URL |
| `--max-urls N` | `50000` | Maximum number of URLs to crawl | 최대 크롤 URL 수 |
| `--max-depth N` | `0` | Maximum crawl depth (0 = unlimited) | 최대 크롤 깊이 (0 = 무제한) |
| `--concurrent N` | `10` | Maximum concurrent requests | 최대 동시 요청 수 |
| `--timeout N` | `30` | Request timeout in seconds | 요청 타임아웃 (초) |
| `--delay N` | `0.0` | Fixed delay between requests (seconds) | 요청 간 고정 딜레이 (초) |

### Subdomain Discovery / 서브도메인 탐색

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--subdomains` | off | Enable subdomain discovery and crawling | 서브도메인 자동 발견 및 크롤링 활성화 |
| `--subdomain-methods M [M ...]` | `dns crt_sh links` | Discovery methods to use | 서브도메인 탐색 방법 선택 |

Available methods / 사용 가능한 방법:

| Method | Description (EN) | 설명 (KR) |
|--------|-----------------|-----------|
| `dns` | DNS record lookup | DNS 레코드 조회 |
| `crt_sh` | Certificate Transparency log search (crt.sh) | 인증서 투명성 로그 검색 (crt.sh) |
| `links` | Discover subdomains from crawled links | 크롤된 링크에서 서브도메인 발견 |
| `dns_transfer` | DNS zone transfer attempt | DNS 존 전송 시도 |

### JavaScript Rendering / JavaScript 렌더링

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--js-render` | off | Enable JavaScript rendering (headless Chromium via Playwright) | JS 렌더링 활성화 (Playwright 헤드리스 Chromium) |
| `--js-wait N` | `5.0` | Wait time after page load for JS execution (seconds) | 페이지 로드 후 JS 실행 대기 시간 (초) |
| `--js-instances N` | `3` | Number of browser instances for parallel rendering | 병렬 렌더링용 브라우저 인스턴스 수 |
| `--block-resources R [R ...]` | *(none)* | Block resource types during rendering | 렌더링 시 차단할 리소스 유형 |

Blockable resource types / 차단 가능 리소스 유형: `image`, `font`, `media`, `stylesheet`

### Bot Detection Evasion / 봇 탐지 우회

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--evasion` | off | Enable bot detection evasion | 봇 탐지 우회 활성화 |
| `--no-stealth` | off | Disable Playwright stealth mode | Playwright 스텔스 모드 비활성화 |
| `--proxies FILE` | *(none)* | Path to proxy list file (one proxy per line) | 프록시 목록 파일 경로 (한 줄에 하나) |
| `--delay-min N` | `0.5` | Minimum random delay between requests (seconds) | 최소 랜덤 딜레이 (초) |
| `--delay-max N` | `3.0` | Maximum random delay between requests (seconds) | 최대 랜덤 딜레이 (초) |

Proxy file format / 프록시 파일 형식:
```
http://proxy1.example.com:8080
http://user:pass@proxy2.example.com:3128
socks5://proxy3.example.com:1080
# Lines starting with # are ignored / #으로 시작하는 줄은 무시됩니다
```

### Scope Filters / 범위 필터

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--include P [P ...]` | *(none)* | Regex patterns — only crawl matching URLs | 정규식 패턴 — 매칭되는 URL만 크롤 |
| `--exclude P [P ...]` | *(none)* | Regex patterns — skip matching URLs | 정규식 패턴 — 매칭되는 URL 제외 |
| `--no-robots` | off | Ignore robots.txt restrictions | robots.txt 제한 무시 |
| `--check-external` | off | Check HTTP status of external links | 외부 링크의 HTTP 상태 코드 확인 |

Filter examples / 필터 예시:
```bash
# Only crawl /blog/ pages / /blog/ 페이지만 크롤
python main.py crawl https://example.com --include "/blog/"

# Exclude image and PDF URLs / 이미지와 PDF URL 제외
python main.py crawl https://example.com --exclude "\.(jpg|png|gif|pdf)$"

# Combine include and exclude / 포함과 제외 조합
python main.py crawl https://example.com --include "/products/" --exclude "/products/archive/"
```

### Custom Extraction / 커스텀 추출

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--extract RULE [RULE ...]` | *(none)* | Custom extraction rules (format: `name:type:pattern`) | 커스텀 추출 규칙 (형식: `이름:유형:패턴`) |
| `--search RULE [RULE ...]` | *(none)* | Custom search rules (format: `name:type:pattern`) | 커스텀 검색 규칙 (형식: `이름:유형:패턴`) |

Extraction types / 추출 유형: `css` (CSS selector), `xpath` (XPath), `regex` (Regular Expression)

Examples / 예시:
```bash
# Extract product prices using CSS selector / CSS 선택자로 상품 가격 추출
python main.py crawl https://shop.example.com --extract "price:css:.product-price"

# Extract dates using XPath / XPath로 날짜 추출
python main.py crawl https://example.com --extract "date:xpath://time/@datetime"

# Search for phone numbers using regex / 정규식으로 전화번호 검색
python main.py crawl https://example.com --search "phone:regex:\d{2,3}-\d{3,4}-\d{4}"

# Multiple extractions / 복수 추출
python main.py crawl https://example.com \
    --extract "price:css:.price" "author:css:.author-name" \
    --search "email:regex:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
```

### Output / 출력

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `-o`, `--output DIR` | `./crawl_output` | Output directory (domain subfolder auto-created) | 출력 디렉토리 (도메인 하위 폴더 자동 생성) |
| `--format FORMAT` | `csv` | Export format: `csv`, `xlsx`, `json`, `all` | 내보내기 형식: `csv`, `xlsx`, `json`, `all` |
| `--report` | off | Generate HTML report | HTML 리포트 생성 |
| `--visualization` | off | Generate site structure visualization | 사이트 구조 시각화 생성 |
| `--sitemap` | off | Generate XML sitemap from crawled URLs | 크롤된 URL로 XML 사이트맵 생성 |

Output formats / 출력 형식:

| Format | Files Generated | 생성 파일 |
|--------|----------------|-----------|
| `csv` | 23 CSV + 3 JSON files (Screaming Frog compatible) | 23개 CSV + 3개 JSON 파일 (Screaming Frog 호환) |
| `xlsx` | 1 Excel workbook with 26 sheets | 26개 시트의 Excel 워크북 1개 |
| `json` | crawl_results.json + crawl_summary.json | crawl_results.json + crawl_summary.json |
| `all` | All of the above + HTML report | 위 모든 형식 + HTML 리포트 |

**v2 CSV 출력 파일 목록 (26개)**:
`internal_all.csv`, `url_all.csv`, `response_codes_all.csv`, `images_all.csv`, `canonicals_all.csv`, `directives_all.csv`, `h1_all.csv`, `h2_all.csv`, `content_all.csv`, `hreflang_all.csv`, `pagination_all.csv`, `structured_data_all.csv`, `security_all.csv`, `javascript_all.csv`, `links_all.csv`, `inlinks.csv`, `redirects.csv`, `issues.csv`, `external_all.csv`, `page_titles_duplicate.csv`, `meta_description_duplicate.csv`, `crawl_warnings.csv`, `statistics_summary.csv`, `statistics_summary.json`, `run_manifest.json`, `run_summary.json`

### Configuration File / 설정 파일

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `--config FILE` | *(none)* | Path to YAML configuration file (overrides CLI options) | YAML 설정 파일 경로 (CLI 옵션보다 우선) |

---

## `list` Command Options / `list` 명령 옵션

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `file` | *(required)* | Path to URL list file (one URL per line) | URL 목록 파일 경로 (한 줄에 하나) |
| `-o`, `--output DIR` | `./crawl_output` | Output directory | 출력 디렉토리 |
| `--format FORMAT` | `csv` | Export format: `csv`, `xlsx`, `json`, `all` | 내보내기 형식 |
| `--js-render` | off | Enable JavaScript rendering | JS 렌더링 활성화 |
| `--evasion` | off | Enable bot detection evasion | 봇 탐지 우회 활성화 |

---

## `sitemap` Command Options / `sitemap` 명령 옵션

| Option | Default | Description (EN) | 설명 (KR) |
|--------|---------|-----------------|-----------|
| `url` | *(required)* | Sitemap XML URL | 사이트맵 XML URL |
| `-o`, `--output DIR` | `./crawl_output` | Output directory | 출력 디렉토리 |
| `--format FORMAT` | `csv` | Export format: `csv`, `xlsx`, `json`, `all` | 내보내기 형식 |

---

## Web Server / 웹 서버

```bash
python web_server.py [port]
```

| Argument | Default | Description (EN) | 설명 (KR) |
|----------|---------|-----------------|-----------|
| `port` | `8090` | HTTP server port number | HTTP 서버 포트 번호 |

The Web UI provides all the same options as the CLI through a graphical interface. See [README.md](README.md) for details.

웹 UI는 CLI와 동일한 모든 옵션을 그래픽 인터페이스로 제공합니다. 자세한 내용은 [README_KR.md](README_KR.md)를 참조하세요.

---

## Usage Examples / 사용 예시

### Basic Crawl / 기본 크롤

```bash
python main.py crawl https://example.com
```

### Full SEO Audit / 전체 SEO 감사

```bash
python main.py crawl https://example.com \
    --max-urls 10000 \
    --max-depth 10 \
    --concurrent 15 \
    --js-render \
    --js-instances 5 \
    --subdomains \
    --evasion \
    --check-external \
    --format all \
    --report \
    --visualization \
    --sitemap \
    -o ./audit_output
```

### Fast Crawl (No JS) / 빠른 크롤 (JS 없이)

```bash
python main.py crawl https://example.com \
    --max-urls 500 \
    --concurrent 20 \
    --timeout 10 \
    --format csv
```

### Stealth Crawl with Proxies / 프록시 스텔스 크롤

```bash
python main.py crawl https://example.com \
    --evasion \
    --proxies proxies.txt \
    --delay-min 1.0 \
    --delay-max 5.0 \
    --js-render \
    --block-resources image font media
```

### Crawl Specific Section / 특정 섹션만 크롤

```bash
python main.py crawl https://example.com \
    --include "/blog/" "/news/" \
    --exclude "/blog/tag/" "/blog/author/" \
    --max-depth 5
```

### Custom Data Extraction / 커스텀 데이터 추출

```bash
python main.py crawl https://shop.example.com \
    --extract "price:css:.product-price" "sku:xpath://span[@class='sku']/text()" \
    --search "phone:regex:\d{2,3}-\d{3,4}-\d{4}" "email:regex:[^\s]+@[^\s]+" \
    --format all
```

### Crawl from URL List / URL 목록 크롤

```bash
# urls.txt:
# https://example.com/page1
# https://example.com/page2
# https://example.com/page3

python main.py list urls.txt --js-render --format xlsx
```

### Crawl from Sitemap / 사이트맵 크롤

```bash
python main.py sitemap https://example.com/sitemap.xml --format all
```
