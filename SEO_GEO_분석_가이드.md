# SEO/GEO 제안서 데이터 분석 가이드

> Python SEO Spider 크롤 결과(CSV/XLSX)를 활용하여 SEO/GEO 제안서에 활용할 수 있는 분석 방법과 시각화 전략을 안내합니다.

---

## 1. 사이트 건강도 대시보드 (Site Health Overview)

### 사용 파일: `internal_all.csv`, `response_codes_all.csv`, `issues.csv`

**분석 방법:**

- `response_codes_all.csv`에서 Status Code를 그룹화하여 2xx/3xx/4xx/5xx 분포를 계산
- `issues.csv`에서 Severity(Critical/Warning/Info) 기준으로 집계
- `internal_all.csv`에서 Indexability 컬럼으로 색인 가능 vs 불가능 비율 산출

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 도넛 차트 | Status Code 분포 (2xx/3xx/4xx/5xx) | 전체 사이트 응답 상태 한눈에 파악 |
| 가로 막대 그래프 | Issues Severity별 건수 | 긴급도별 이슈 현황 |
| KPI 카드 | 총 URL, 색인 가능 비율, 평균 응답 시간, 총 이슈 수 | 대시보드 상단 요약 |
| 트리맵 | Issue Type별 비중 | 이슈 유형 분포 파악 |

**제안서 활용:**
"현재 사이트의 전체 URL 중 X%만 정상(2xx) 응답하고 있으며, Y개의 Critical 이슈가 발견되었습니다. 이를 개선하면 검색엔진이 크롤 및 색인할 수 있는 페이지가 Z% 증가할 것으로 예상됩니다."

---

## 2. 타이틀/메타 설명 최적화 분석

### 사용 파일: `internal_all.csv`, `page_titles_duplicate.csv`, `meta_description_duplicate.csv`

**분석 방법:**

- `internal_all.csv`에서 Title 1 Length 분포를 히스토그램으로 시각화 (권장: 30~60자)
- Title 1 Pixel Width 기준으로 SERP 잘림(truncation) 여부 분석 (>580px이면 잘림)
- Meta Description 1 Length 분포 분석 (권장: 70~160자)
- `page_titles_duplicate.csv`에서 중복 타이틀 URL 목록 추출
- `meta_description_duplicate.csv`에서 중복 메타 설명 추출
- 누락(빈 값) 비율 계산

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 히스토그램 | Title Length 분포 | 최적 범위 대비 현황 (빨간 영역으로 권장 범위 밖 표시) |
| 히스토그램 | Meta Description Length 분포 | 최적 범위 대비 현황 |
| 스택 막대 | 최적/너무 짧음/너무 긺/누락/중복 비율 | 전체 현황 요약 |
| 표 | 중복 타이틀 TOP 10 (Occurrences 내림차순) | 구체적 수정 대상 제시 |

**제안서 활용:**
"타이틀 태그 중 X%가 권장 길이(30~60자)를 벗어나고 있으며, Y개의 페이지가 동일한 타이틀을 공유하고 있습니다. 각 페이지별 고유한 타이틀을 작성하면 CTR(클릭률)이 개선될 수 있습니다."

---

## 3. 콘텐츠 품질 분석

### 사용 파일: `content_all.csv`, `internal_all.csv`

**분석 방법:**

- Word Count 분포 분석: 콘텐츠 빈약(Thin Content) 페이지 식별 (< 300 단어)
- Flesch Reading Ease Score 분포로 가독성 현황 파악
- Readability 등급별 페이지 수 집계
- Text Ratio(텍스트/HTML 비율) 분석: 낮은 비율 = 코드 대비 콘텐츠 부족
- Near Duplicate 페이지 식별 (No. Near Duplicates > 0)
- Language별 페이지 분포

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 히스토그램 | Word Count 분포 (100단위 구간) | 콘텐츠 양 분포 파악 |
| 파이 차트 | Readability 등급별 비율 | 가독성 현황 요약 |
| 산점도 | Word Count vs Response Time | 콘텐츠 양과 성능 상관관계 |
| 산점도 | Word Count vs Flesch Score | 콘텐츠 양과 가독성 상관관계 |
| 표 | Thin Content 페이지 목록 (Word Count < 300) | 콘텐츠 보강 대상 |
| 표 | 유사 중복 페이지 그룹 | 통합/차별화 대상 |

**제안서 활용:**
"전체 페이지 중 X%가 300단어 미만의 빈약한 콘텐츠를 보유하고 있으며, 이는 검색엔진이 낮은 품질로 판단할 수 있습니다. 또한 Y개 페이지가 유사 중복으로 감지되어 콘텐츠 통합 또는 캐노니컬 처리가 필요합니다."

---

## 4. 사이트 구조/링크 분석

### 사용 파일: `links_all.csv`, `inlinks.csv`, `internal_all.csv`

**분석 방법:**

- Crawl Depth 분포: 3 이상 깊은 페이지 비율 → 접근성 문제
- Link Score(내부 PageRank) 분포: 상위/하위 페이지 식별
- Inlinks 상위 페이지 = 허브 페이지 식별
- Inlinks 0인 페이지 = 고아 페이지(Orphan Pages) 식별
- External Outlinks 분포: 외부 링크 지나치게 많은 페이지 식별
- `inlinks.csv`에서 Inlink Count 내림차순 → 가장 중요한 페이지 순위

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 막대 그래프 | Crawl Depth별 페이지 수 | 사이트 구조 깊이 분포 |
| 히스토그램 | Link Score 분포 | 내부 링크 권위 분포 |
| 산점도 | Inlinks vs Link Score | 인링크와 페이지 가치 상관관계 |
| 네트워크 다이어그램 | 상위 20개 페이지 간 링크 관계 | 사이트 구조 시각화 (고급) |
| 표 | 고아 페이지 목록 (Inlinks = 0) | 내부 링크 추가 대상 |
| 표 | Link Score 상위/하위 20 페이지 | 링크 최적화 대상 |

**제안서 활용:**
"현재 X개의 페이지가 내부 링크를 전혀 받지 못하는 고아 페이지입니다. 이 페이지들은 검색엔진이 발견하기 어렵습니다. 또한 전체 페이지의 Y%가 크롤 깊이 3 이상에 위치해 있어 사이트 구조 개선이 필요합니다."

---

## 5. 기술적 SEO 진단

### 사용 파일: `canonicals_all.csv`, `directives_all.csv`, `redirects.csv`, `security_all.csv`

**분석 방법:**

- `canonicals_all.csv`: Self-referencing canonical 비율, canonical 누락 비율, HTTP vs HTML canonical 불일치
- `directives_all.csv`: noindex 페이지 목록, nofollow 페이지 확인
- `redirects.csv`: 리다이렉트 체인 길이 분석 (2홉 이상 → 성능 저하), 리다이렉트 유형(301 vs 302) 비율
- `security_all.csv`: HTTPS 채택률, 보안 헤더 적용률 (HSTS, CSP, X-Frame-Options 등)

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 스택 막대 | Canonical 상태 (Self/Other/Missing/Mismatch) | 캐노니컬 현황 |
| 파이 차트 | Redirect Type 분포 (301/302/307) | 리다이렉트 유형 비율 |
| 히스토그램 | Redirect Chain Length | 리다이렉트 체인 복잡도 |
| 레이더 차트 | 보안 헤더 적용률 (HSTS, CSP, X-Frame 등) | 보안 현황 한눈에 비교 |
| 표 | 리다이렉트 체인 3홉 이상 목록 | 수정 대상 |

**제안서 활용:**
"X%의 페이지에 캐노니컬 태그가 누락되어 있으며, Y개의 리다이렉트 체인이 3홉 이상입니다. 보안 측면에서는 HSTS가 Z%의 페이지에만 적용되어 있습니다."

---

## 6. 이미지 SEO 분석

### 사용 파일: `images_all.csv`

**분석 방법:**

- Missing Alt Attribute = True인 이미지 비율
- Alt Text 길이 분포 (너무 짧거나/너무 긴 대체 텍스트)
- 이미지 파일 크기 분포 (큰 이미지 = 성능 저하 원인)
- 이미지 형식별 분포 (확장자 기준: jpg/png/webp/svg)

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 도넛 차트 | Alt 텍스트 있음/없음 비율 | 접근성 현황 |
| 히스토그램 | 이미지 파일 크기 분포 | 최적화 필요 이미지 파악 |
| 막대 그래프 | 이미지 형식별 수 | 최신 형식(WebP) 전환 대상 |
| 표 | 큰 이미지 TOP 20 (Size 내림차순) | 최적화 우선순위 |

**제안서 활용:**
"전체 이미지 중 X%에 alt 속성이 누락되어 있어 검색엔진과 스크린리더가 이미지를 이해할 수 없습니다. 또한 Y개의 이미지가 500KB를 초과하여 페이지 로딩 속도를 저하시키고 있습니다."

---

## 7. 국제 SEO (Hreflang) 분석

### 사용 파일: `hreflang_all.csv`

**분석 방법:**

- 언어/지역별 페이지 커버리지 매트릭스
- 반환 태그(return tag) 누락 검사
- hreflang 오류 유형별 집계

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 히트맵 | 언어 x 지역 커버리지 매트릭스 | 다국어 커버리지 현황 |
| 표 | 반환 태그 누락 목록 | 수정 대상 |

---

## 8. 구조화 데이터 분석

### 사용 파일: `structured_data_all.csv`

**분석 방법:**

- Schema.org 타입별 사용 현황
- 오류/경고가 있는 구조화 데이터 비율
- 구조화 데이터가 있는 페이지 vs 없는 페이지 비율

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 막대 그래프 | Schema Type별 사용 수 | 구조화 데이터 활용 현황 |
| 파이 차트 | Valid vs Invalid 비율 | 구조화 데이터 품질 |
| 표 | 오류 있는 페이지 목록 | 수정 대상 |

**제안서 활용:**
"현재 X%의 페이지에만 구조화 데이터가 적용되어 있습니다. 리치 스니펫 노출을 위해 Product, FAQ, Article 등의 스키마 추가를 권장합니다."

---

## 9. JS 렌더링 영향 분석

### 사용 파일: `javascript_all.csv`

**분석 방법:**

- Word Count Change > 0인 페이지: JS에 의존하는 콘텐츠 비율
- JS Word Count %가 높은 페이지: 검색엔진이 놓칠 수 있는 콘텐츠
- HTML Title vs Rendered Title 불일치 페이지
- HTML Meta Description vs Rendered Meta Description 불일치 페이지
- HTML Canonical vs Rendered Canonical 불일치 → 심각한 색인 문제

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 히스토그램 | JS Word Count % 분포 | JS 의존도 분포 |
| 산점도 | HTML Word Count vs Rendered Word Count | 렌더링 전후 콘텐츠 변화 |
| 표 | Title 불일치 페이지 (before/after 비교) | 수정 대상 |
| 표 | JS 의존도 > 50% 페이지 | SSR/Pre-rendering 대상 |

**제안서 활용:**
"X개의 페이지에서 JavaScript 실행 전후 콘텐츠가 크게 변화합니다. 이 페이지들의 핵심 콘텐츠가 JS에 의존하고 있어, 검색엔진 봇이 모든 콘텐츠를 인식하지 못할 수 있습니다. SSR(Server-Side Rendering) 또는 Dynamic Rendering 도입을 권장합니다."

---

## 10. 성능 분석

### 사용 파일: `internal_all.csv`

**분석 방법:**

- Response Time 분포: 느린 페이지(>1초) 비율
- Size(bytes) vs Response Time 상관관계
- Transferred(bytes) 분포: 대용량 페이지 식별

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 히스토그램 | Response Time 분포 (0.1초 구간) | 성능 현황 |
| 산점도 | Page Size vs Response Time | 크기와 속도 상관관계 |
| 표 | 느린 페이지 TOP 20 (Response Time 내림차순) | 최적화 대상 |

---

## 11. GEO (Generative Engine Optimization) 특화 분석

### 사용 파일: `content_all.csv`, `structured_data_all.csv`, `h1_all.csv`, `h2_all.csv`

AI 검색엔진(Google SGE, Bing Chat, Perplexity 등)에 최적화하기 위한 분석:

**분석 방법:**

- **콘텐츠 구조화 점수**: H1/H2 태그 활용률, FAQ 구조화 데이터 적용률 조합
- **답변 적합성**: Word Count 적정 범위(300~2000단어)인 페이지 비율
- **가독성**: Flesch Score가 60 이상(Easy/Fairly Easy)인 비율 → AI가 인용하기 좋은 콘텐츠
- **E-E-A-T 시그널**: 저자 정보, 출처 링크, 구조화 데이터 적용 여부
- **Answer-Ready 콘텐츠**: H2 태그에 질문형 텍스트("~란?", "~방법", "how to" 등) 포함 비율

**시각화 권장:**

| 차트 유형 | 데이터 조합 | 용도 |
|-----------|------------|------|
| 레이더 차트 | GEO 준비도 점수 (구조화, 가독성, 콘텐츠양, 스키마 등) | 종합 GEO 현황 |
| 스택 막대 | 페이지별 GEO 요소 충족 현황 | 개선 대상 식별 |
| 표 | GEO 최적화 체크리스트 (페이지별 O/X) | 구체적 실행 항목 |

**제안서 활용:**
"AI 검색엔진 최적화(GEO) 관점에서, 현재 사이트의 X%만이 답변 인용에 적합한 구조를 갖추고 있습니다. H2 태그 활용률은 Y%, 구조화 데이터 적용률은 Z%입니다. FAQ 스키마 추가, 질문형 소제목 활용, 콘텐츠 가독성 개선으로 AI 검색 노출을 높일 수 있습니다."

---

## 12. 종합 분석 프레임워크: CSV 조합 전략

### 크로스 파일 분석 예시

| 분석 목표 | 조합할 CSV | 결합 키 | 분석 방법 |
|-----------|-----------|---------|-----------|
| 중요 페이지의 기술적 문제 | `links_all.csv` + `issues.csv` | Address/URL | Link Score 상위 페이지에 이슈가 있는지 확인 |
| 콘텐츠 품질 vs 링크 가치 | `content_all.csv` + `links_all.csv` | Address | Word Count와 Link Score 상관관계 분석 |
| 보안 vs 색인 가능성 | `security_all.csv` + `internal_all.csv` | Address | HTTPS 미적용 + Indexable 페이지 식별 |
| JS 렌더링 영향 + 성능 | `javascript_all.csv` + `internal_all.csv` | Address | JS 의존도 높은 페이지의 응답 시간 분석 |
| 중복 콘텐츠 + 캐노니컬 | `page_titles_duplicate.csv` + `canonicals_all.csv` | Address | 중복 타이틀 페이지의 캐노니컬 설정 확인 |
| 이미지 최적화 + 성능 | `images_all.csv` + `internal_all.csv` | Source Page/Address | 이미지 많은 페이지의 응답 시간 상관관계 |

### Python 코드 예시 (Pandas 활용)

```python
import pandas as pd

# 파일 로드
internal = pd.read_csv('crawl_output/example/internal_all.csv')
links = pd.read_csv('crawl_output/example/links_all.csv')
content = pd.read_csv('crawl_output/example/content_all.csv')
issues = pd.read_csv('crawl_output/example/issues.csv')

# 1. 사이트 건강도 요약
health = {
    '총 URL': len(internal),
    '색인 가능': len(internal[internal['Indexability'] == 'Indexable']),
    '2xx 비율': f"{len(internal[internal['Status Code'].between(200,299)]) / len(internal) * 100:.1f}%",
    '평균 응답시간': f"{internal['Response Time'].astype(float).mean():.3f}초",
    '총 이슈': len(issues),
}

# 2. 콘텐츠 품질 분석
thin_content = internal[internal['Word Count'] < 300]
print(f"빈약 콘텐츠 페이지: {len(thin_content)}개 ({len(thin_content)/len(internal)*100:.1f}%)")

# 3. 고아 페이지 식별
orphans = links[links['Inlinks'] == 0]
print(f"고아 페이지: {len(orphans)}개")

# 4. 크로스 분석: 중요 페이지(Link Score 상위)의 이슈
top_pages = links.nlargest(20, 'Link Score')['Address'].tolist()
top_issues = issues[issues['URL'].isin(top_pages)]
print(f"상위 20 페이지의 이슈: {len(top_issues)}개")

# 5. GEO 준비도 점수
geo_score = pd.DataFrame({
    'Address': content['Address'],
    '적정 분량': content['Word Count'].between(300, 2000),
    '좋은 가독성': content['Flesch Reading Ease Score'].astype(float) >= 60,
})
```

---

## 13. 제안서 구성 추천 순서

1. **현황 요약** (사이트 건강도 대시보드) → KPI 카드 + 도넛 차트
2. **기술적 진단** (응답 코드, 리다이렉트, 보안) → 표 + 레이더 차트
3. **온페이지 SEO** (타이틀, 메타, H1/H2) → 히스토그램 + 중복 목록 표
4. **콘텐츠 분석** (분량, 가독성, 중복) → 산점도 + 파이 차트
5. **사이트 구조** (크롤 깊이, 링크 점수, 고아 페이지) → 네트워크 다이어그램 + 표
6. **이미지/리소스** (alt 누락, 큰 파일) → 막대 그래프 + 표
7. **JS 렌더링** (before/after 비교) → 산점도 + 불일치 표
8. **국제 SEO** (hreflang 분석) → 히트맵
9. **GEO 최적화** (AI 검색 대응) → 레이더 차트 + 체크리스트
10. **실행 계획** (우선순위별 개선 항목) → 간트 차트 또는 우선순위 매트릭스

---

## 14. 우선순위 매트릭스 (Impact vs Effort)

크롤 데이터 기반으로 개선 항목의 우선순위를 결정하는 프레임워크:

| 영향도 높음 + 노력 적음 (바로 실행) | 영향도 높음 + 노력 큼 (계획 수립) |
|---|---|
| 누락된 타이틀/메타 설명 추가 | 사이트 구조 재설계 |
| 중복 타이틀 수정 | SSR/Pre-rendering 도입 |
| 301 리다이렉트 체인 정리 | 콘텐츠 전면 재작성 |
| 이미지 alt 태그 추가 | 국제 SEO (hreflang) 설정 |
| 캐노니컬 태그 수정 | 구조화 데이터 전체 적용 |

| 영향도 낮음 + 노력 적음 (여유 시 실행) | 영향도 낮음 + 노력 큼 (후순위) |
|---|---|
| meta keywords 정리 | 전체 URL 구조 변경 |
| 보안 헤더 추가 | 다국어 사이트 구축 |
| HTTP/2 전환 확인 | CMS 마이그레이션 |

---

*이 가이드는 Python SEO Spider의 27개 CSV/26개 XLSX 시트 출력을 기반으로 작성되었습니다.*
