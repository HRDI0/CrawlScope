# Python SEO Spider v2 — 핵심 변경점 요약

---

## 1. `seo_spider/core/models.py` — 데이터 모델 확장

**PageData 신규 필드 (10개):**

| 필드 | 타입 | 설명 |
|------|------|------|
| `original_status_code` | int | 리다이렉트 전 최초 HTTP 응답 코드 |
| `page_type` | str | 콘텐츠 유형 분류 (HTML/Image/CSS/JS/PDF/Redirect/Other) |
| `redirect_status` | str | ""/Redirect Chain/Redirect Loop |
| `redirect_chain_length` | int | 리다이렉트 홉 수 |
| `title_status` | str | Missing/Duplicate/Over 60/Below 30/OK |
| `meta_desc_status` | str | Missing/Duplicate/Over 160/Below 70/OK |
| `canonical_status` | str | Missing/Self-Referencing/Canonicalised/Canonical to Redirect/Canonical to Non-200 |
| `h1_status` | str | Missing/Multiple/Duplicate/OK |
| `images_missing_alt_attribute` | int | alt 속성 자체가 없는 이미지 수 |
| `images_with_alt_over_100` | int | alt 100자 초과 이미지 수 |

**ImageData 신규 필드:**
- `source_page: str` — 이미지가 발견된 페이지 URL
- `is_missing_alt_attribute: bool` — alt 속성 자체 누락 (alt="" 와 구분)
- `alt_over_100: bool` — alt 텍스트 100자 초과

**CrawlResult 신규 필드:**
- `crawl_warnings: list[str]` — 크롤 중 경고 목록
- `sitemap_urls: list[str]` — 사이트맵 URL 목록

---

## 2. `seo_spider/exporters/csv_exporter.py` — 전체 재작성

**26개 파일 출력 (23 CSV + 3 JSON):**

| # | 파일 | 변경 유형 |
|---|------|----------|
| 1-21 | 기존 CSV 파일들 | 컬럼 추가/수정 |
| 22 | `crawl_warnings.csv` | **신규** — 크롤 경고 기록 |
| 23 | `statistics_summary.csv` | **신규** — 31개 핵심 지표 |
| 24 | `statistics_summary.json` | **신규** — 통계 JSON 버전 |
| 25 | `run_manifest.json` | **신규** — 실행 메타데이터 |
| 26 | `run_summary.json` | **신규** — 실행 요약 |

**주요 변경:**
- `images_all.csv`: 1행=1 이미지 출현(occurrence) 방식으로 변경, `Missing Alt Attribute` / `Missing Alt Text` / `Alt Over 100 Characters` 3가지 분리
- `canonicals_all.csv`: `Canonical Status` 컬럼 추가 (5단계 분류)
- `redirects.csv`: `Status Code`, `Redirect Status` 컬럼 추가
- `issues.csv`: `Evidence`, `Source Table`, `Counting Unit` 3개 컬럼 추가 (7→10 컬럼)
- `inlinks.csv`: Source→Target 개별 행 방식으로 변경 (7개 컬럼)
- `response_codes_all.csv`: `Page Type` 컬럼 추가
- `_compute_statistics()`: 31개 지표를 metric_name/metric_value/counting_unit/denominator_if_any/scope/source_tables 구조로 산출
- JSON 파일은 `encoding='utf-8'` (BOM 없음), CSV는 `encoding='utf-8-sig'` (BOM 포함)

---

## 3. `seo_spider/analyzers/issue_detector.py` — 증거 기반 이슈 탐지

**SEOIssue 신규 필드:**
- `evidence: str` — 이슈 발견 근거 (실제 값)
- `source_table: str` — 관련 CSV 파일명
- `counting_unit: str` — 이슈 집계 단위

**주요 메서드 변경:**
- `detect_page_issues(page, pages_by_url=None)` — cross-page 참조 딕셔너리 선택 전달
- `detect_crawl_issues(result, pages_by_url=None)` — `_check_cross_page_duplicates()` 호출
- `_check_canonical_issues(page, pages_by_url)` — 5단계 캐노니컬 분류 (Canonical to Redirect / Canonical to Non-200 교차 검증)
- `_check_cross_page_duplicates(pages)` — defaultdict로 title/meta_description/h1 그룹핑 후 중복 이슈 생성

---

## 4. `seo_spider/analyzers/html_parser.py` — 이미지/캐노니컬 강화

- `_extract_images()`: `source_page=base_url` 설정, `is_missing_alt_attribute`와 `alt_over_100` 별도 분류
- `_extract_canonical()`: `canonical_status`를 Missing / Self-Referencing / Canonicalised 3단계 설정
- `analyze()`: 캐노니컬 추출 후 canonical_status가 미설정이면 "Missing"으로 기본값

---

## 5. `seo_spider/core/crawler.py` — 리다이렉트/페이지 유형 추적

- **리다이렉트 루프 감지**: `redirect_status = "Redirect Loop"`, `original_status_code` 보존
- **리다이렉트 체인**: `redirect_chain_length = len(redirect_chain)`, 2홉 이상이면 `redirect_status = "Redirect Chain"`
- **페이지 유형 자동 분류**: Content-Type 헤더 기반으로 HTML/Image/CSS/JavaScript/PDF/Redirect/Other 판별

---

## 6. `main.py` — 후처리(post-process) 함수 추가

**`_populate_status_fields(pages_by_url)` 함수 신규:**
- **Title Status**: defaultdict 그룹핑 → Missing/Duplicate/Over 60 Characters/Below 30 Characters/OK
- **Meta Description Status**: 동일 패턴 → Missing/Duplicate/Over 160/Below 70/OK
- **H1 Status**: Missing/Multiple/Duplicate/OK
- **Canonical 교차 검증**: canonical_status가 "Canonicalised"인 경우 대상 URL의 상태 코드 확인 → Canonical to Redirect / Canonical to Non-200 재분류
- **근사 중복(Near-Duplicate)**: SimHash 해밍 거리 ≤ 5로 `closest_similarity_match`, `near_duplicate_count` 산출
- `post_process()`에서 `_populate_status_fields()` 호출, `pages_by_url`을 IssueDetector에 전달

---

## 7. `test_integration.py` — 통합 테스트 추가

- 8개 시뮬레이션 페이지 (200/301/404/302 등 다양한 시나리오)
- 후처리 → 26개 파일 내보내기 → 14개 콘텐츠 검증
- 모든 검증 통과 확인
