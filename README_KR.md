# Python SEO Spider

Screaming Frog SEO Spider의 기능을 Python으로 구현한 SEO 크롤링 및 분석 도구입니다. 웹사이트를 크롤링하고, 온페이지 SEO 요소를 분석하며, 기술적 이슈를 탐지하고, Screaming Frog 호환 리포트를 내보낼 수 있습니다.

> **[English README](README.md)**

## 주요 기능

### 크롤링 엔진
- 비동기 HTTP 크롤링 (동시 요청 수, 깊이 제한 설정 가능)
- 서브도메인 자동 발견 및 크로스 서브도메인 크롤링
- robots.txt 준수 (설정으로 오버라이드 가능)
- Playwright 기반 JavaScript 렌더링 (렌더링 전/후 비교)
- HTTP/2 지원
- sitemap.xml 파싱 및 URL 시드 추가

### 봇 탐지 우회
- User-Agent 로테이션 (실제 브라우저 핑거프린트 기반)
- Playwright Stealth 모드
- 요청 딜레이 및 속도 제한 설정
- 프록시 로테이션 지원

### 온페이지 분석
- 타이틀, 메타 설명, 메타 키워드 (길이 + 픽셀 너비)
- H1/H2 헤딩 태그 추출 및 분석
- 단어 수, 문장 수, 텍스트/HTML 비율
- Flesch Reading Ease 가독성 점수 및 등급
- 캐노니컬 태그 (HTML + HTTP 헤더)
- Meta Robots / X-Robots-Tag 지시자
- rel="next"/rel="prev" 페이지네이션 감지
- Hreflang 다국어 주석

### 링크 분석
- 내부/외부 링크 카운팅 (고유 링크 중복 제거)
- 인링크 매핑 및 집계
- 내부 PageRank (Link Score) 계산 (감쇠 계수=0.85, 20회 반복)
- 크롤 깊이 및 폴더 깊이 추적
- 고아 페이지 감지

### 기술적 SEO
- HTTP 상태 코드 모니터링 (2xx/3xx/4xx/5xx)
- 리다이렉트 체인 추적 (유형, 홉 수, 최종 URL)
- 보안 헤더 분석 (HTTPS, HSTS, CSP, X-Frame-Options 등)
- 응답 시간 측정
- 중복 콘텐츠 감지 (해시 기반 + 유사도 기반)
- 중복 타이틀/메타 설명 감지

### JavaScript 렌더링
- Playwright 헤드리스 브라우저 렌더링
- 렌더링 전/후 비교: 타이틀, H1, 메타 설명, 캐노니컬, 단어 수
- JS Word Count % 계산 (JavaScript로 추가된 콘텐츠 비율)
- 렌더링 의존 메타 태그 감지

### 구조화 데이터
- JSON-LD, Microdata, RDFa 추출
- Schema.org 타입 식별
- 유효성 오류/경고 카운팅

### 커스텀 분석
- CSS 선택자/XPath/정규식 기반 커스텀 추출 규칙
- 커스텀 검색 패턴 매칭 (포함/미포함)

### 내보내기 형식

**26개 출력 파일** (23개 CSV + 3개 JSON) (Screaming Frog 호환 형식):

| 파일 | 설명 |
|------|------|
| `internal_all.csv` | 내부 전체 페이지 (61개 컬럼) |
| `url_all.csv` | URL 레벨 데이터 |
| `response_codes_all.csv` | 상태 코드 및 응답 시간 |
| `images_all.csv` | 이미지 출현 (페이지당 1행) |
| `canonicals_all.csv` | 캐노니컬 상태 분석 |
| `directives_all.csv` | Meta Robots 및 지시자 |
| `h1_all.csv` | H1 헤딩 데이터 |
| `h2_all.csv` | H2 헤딩 데이터 |
| `content_all.csv` | 가독성 및 콘텐츠 메트릭 |
| `hreflang_all.csv` | 다국어 주석 |
| `pagination_all.csv` | rel="next"/"prev" 데이터 |
| `structured_data_all.csv` | Schema.org 데이터 |
| `security_all.csv` | HTTPS 및 보안 헤더 |
| `javascript_all.csv` | JS 렌더링 비교 |
| `links_all.csv` | 인링크/아웃링크 분석 |
| `inlinks.csv` | Source→Target 링크 매핑 |
| `redirects.csv` | 리다이렉트 체인 추적 |
| `issues.csv` | 근거를 포함한 SEO 이슈 |
| `external_all.csv` | 외부 URL |
| `page_titles_duplicate.csv` | 중복 타이틀 |
| `meta_description_duplicate.csv` | 중복 메타 설명 |
| `statistics_summary.csv` | 31개 메트릭 (카운팅 단위 포함) |
| `crawl_warnings.csv` | 크롤 경고 로그 |

추가 내보내기:
- **statistics_summary.json** — CSV와 동일한 메트릭 (JSON 형식)
- **run_manifest.json** — 크롤 설정 및 파일 목록
- **run_summary.json** — 상태 분포 및 상위 이슈

### 웹 UI
- Carbon Design System (IBM) 다크 테마 인터페이스
- 4개 탭: 크롤 설정, 결과 대시보드, 페이지 테이블, 세션
- 실시간 크롤 진행 상황 표시
- 상태 코드 분포 차트
- 이슈 패널 (심각도 표시)
- 모든 크롤 옵션 UI 토글/입력으로 설정 가능

## 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/python-seo-spider.git
cd python-seo-spider

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (JS 렌더링용)
playwright install chromium
```

## 빠른 시작

### 웹 UI (권장)

Python SEO Spider를 가장 쉽게 사용하는 방법입니다. 모든 크롤 옵션을 직관적인 그래픽 인터페이스로 조작할 수 있어 CLI 옵션을 외울 필요가 없습니다.

```bash
# 웹 서버 실행
python web_server.py

# 브라우저에서 http://localhost:8090 접속
```

Carbon Design System 다크 테마 대시보드에서 토글과 입력 필드로 모든 크롤 설정을 구성하고, 실시간 진행 상황을 모니터링하며, 차트와 테이블로 결과를 확인하고, 여러 크롤 세션을 관리할 수 있습니다.

### 명령줄 (CLI)

자동화, 스크립팅, CI/CD 파이프라인에 적합합니다. 전체 옵션 목록은 **[CLI 옵션 레퍼런스](CLI_OPTIONS.md)**를 참조하세요.

```bash
# 기본 크롤
python main.py crawl https://example.com

# JS 렌더링, 서브도메인 탐색, 전체 내보내기 포함 전체 감사
python main.py crawl https://example.com --js-render --subdomains --evasion --format all --report

# URL 목록 크롤
python main.py list urls.txt --format xlsx

# 사이트맵 크롤
python main.py sitemap https://example.com/sitemap.xml
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
    rendering_mode="playwright",  # JS 렌더링 활성화
    respect_robots_txt=True,
    concurrent_requests=5,
)

async def main():
    crawler = SEOSpiderCrawler(config)
    result = await crawler.crawl()

    # CSV 내보내기 (27개 파일)
    exporter = CSVExporter("crawl_output/example")
    exporter.export_all(result)

asyncio.run(main())
```

## 출력 구조

```
crawl_output/{domain}/
├── internal_all.csv          # 내부 전체 페이지 (61개 컬럼)
├── url_all.csv               # URL 레벨 데이터
├── response_codes_all.csv    # 상태 코드 및 응답 시간
├── images_all.csv            # 이미지 출현 (페이지당 1행)
├── canonicals_all.csv        # 캐노니컬 상태 분석
├── directives_all.csv        # Meta Robots 및 지시자
├── h1_all.csv                # H1 헤딩 데이터
├── h2_all.csv                # H2 헤딩 데이터
├── content_all.csv           # 가독성 및 콘텐츠 메트릭
├── hreflang_all.csv          # 다국어 주석
├── pagination_all.csv        # rel="next"/"prev" 데이터
├── structured_data_all.csv   # Schema.org 데이터
├── security_all.csv          # HTTPS 및 보안 헤더
├── javascript_all.csv        # JS 렌더링 비교
├── links_all.csv             # 인링크/아웃링크 분석
├── inlinks.csv               # Source→Target 링크 매핑
├── redirects.csv             # 리다이렉트 체인 추적
├── issues.csv                # 근거를 포함한 SEO 이슈
├── external_all.csv          # 외부 URL
├── page_titles_duplicate.csv # 중복 타이틀
├── meta_description_duplicate.csv
├── statistics_summary.csv    # 31개 메트릭 (카운팅 단위 포함)
├── crawl_warnings.csv        # 크롤 경고 로그
├── statistics_summary.json   # CSV와 동일한 메트릭 (JSON)
├── run_manifest.json         # 크롤 설정 및 파일 목록
└── run_summary.json          # 상태 분포 및 상위 이슈
```

## 주요 개선사항 (v2)

- **Screaming Frog 호환 CSV 명명** — 표준 명명 규칙을 따르는 26개 출력 파일
- **확장된 데이터셋** — 포괄적인 SEO 메트릭을 포함한 23개 CSV + 3개 JSON 파일
- **근거 포함 issues.csv** — SEO 이슈에 근거 컬럼 및 source_table 참조로 근본 원인 분석 가능
- **statistics_summary** — 프로그래밍 방식 접근을 위한 메트릭 이름, 값, 카운팅 단위, 범위 포함
- **캐노니컬 상태 분류** — Missing / Self-Referencing / Canonicalised / Canonical to Redirect / Canonical to Non-200
- **리다이렉트 상태 분류** — Redirect Chain / Redirect Loop 감지
- **이미지 출현 기반 카운팅** — 페이지당 1행, Alt 속성 없음 vs Alt 텍스트 없음 구분
- **제목/메타 설명/H1 상태** — 분류 및 전체 페이지 중복 감지
- **근사 중복 감지** — closest_similarity_match 및 near_duplicate_count 채우기로 콘텐츠 중복 제거
- **프로그래밍 방식 접근** — run_manifest.json 및 run_summary.json으로 자동화 및 통합 지원

## 설정

`config_example.yaml`을 복사하여 사용:

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

## 프로젝트 구조

```
python-seo-spider/
├── main.py                    # CLI 진입점
├── web_server.py              # 웹 UI 서버
├── web_ui.html                # Carbon Design System SPA
├── requirements.txt
├── config_example.yaml
├── setup.py
├── test_all.py
├── seo_spider/
│   ├── core/
│   │   ├── models.py          # 데이터 모델 (PageData, CrawlResult, CrawlConfig)
│   │   ├── crawler.py         # 메인 비동기 크롤러 엔진
│   │   ├── robots_parser.py   # robots.txt 처리
│   │   └── subdomain_discovery.py
│   ├── analyzers/
│   │   ├── html_parser.py     # HTML 분석 (타이틀, 메타, 헤딩, 가독성)
│   │   ├── issue_detector.py  # SEO 이슈 탐지
│   │   ├── duplicate_detector.py
│   │   ├── security_analyzer.py
│   │   ├── structured_data_analyzer.py
│   │   ├── sitemap_parser.py
│   │   ├── custom_extractor.py
│   │   └── visualization.py
│   ├── exporters/
│   │   ├── csv_exporter.py    # 27개 Screaming Frog 호환 CSV
│   │   ├── xlsx_exporter.py   # 26시트 Excel 워크북
│   │   ├── json_exporter.py
│   │   └── report_generator.py
│   ├── renderers/
│   │   └── js_renderer.py     # Playwright JS 렌더링
│   ├── evasion/
│   │   ├── anti_bot.py        # 봇 탐지 우회
│   │   ├── fingerprint.py     # 브라우저 핑거프린트 생성
│   │   └── proxy_rotator.py
│   ├── config/
│   │   └── settings.py
│   └── utils/
│       ├── url_utils.py
│       ├── hash_utils.py
│       └── logging_config.py
├── crawl_output/              # 생성된 출력 (gitignore 대상)
├── 산출물_컬럼_명세서.xlsx      # 컬럼 명세서
├── SEO_GEO_분석_가이드.md      # SEO/GEO 분석 가이드
└── SEO_크롤_데이터_분석_방법론.md  # 크롤 데이터 분석 방법론
```

## 문서

- **[CLI_OPTIONS.md](CLI_OPTIONS.md)** — CLI 전체 옵션 레퍼런스 및 사용 예시 (영어/한국어)
- **[산출물_컬럼_명세서.xlsx](산출물_컬럼_명세서.xlsx)** — 27개 CSV 파일, 26개 XLSX 시트, JSON 필드의 전체 컬럼 명세 (한/영)
- **[SEO_GEO_분석_가이드.md](SEO_GEO_분석_가이드.md)** — 크롤 데이터를 활용한 SEO/GEO 제안서 작성 가이드 (시각화 전략, Python 분석 코드 예시 포함)
- **[SEO_크롤_데이터_분석_방법론.md](SEO_크롤_데이터_분석_방법론.md)** — 크롤 데이터 분석 방법론: CSV 컬럼별 정상/비정상 기준, Python+Pandas+Seaborn EDA 코드, Looker Studio·Tableau 대시보드 구축 가이드

## 요구사항

- Python 3.10+
- Playwright (JavaScript 렌더링용)
- 전체 의존성은 `requirements.txt` 참조

## CSV 인코딩

모든 CSV 파일은 UTF-8 BOM (`utf-8-sig`) 인코딩으로 저장됩니다. Windows Excel에서 한글이 정상적으로 표시됩니다.
