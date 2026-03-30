# SEO 크롤 데이터 분석 방법론

> Python SEO Spider가 생성하는 23개 CSV + 3개 JSON 파일의 모든 컬럼에 대한 의미, 정상/이상 기준, 그리고 Looker Studio · Tableau · Python(Pandas+Seaborn) 환경에서의 시각화 및 EDA 방법을 상세히 안내합니다.

---

## 목차

1. [분석 환경 세팅](#1-분석-환경-세팅)
2. [internal_all.csv — 핵심 종합 데이터](#2-internal_allcsv--핵심-종합-데이터)
3. [response_codes_all.csv — HTTP 상태 코드 분석](#3-response_codes_allcsv--http-상태-코드-분석)
4. [content_all.csv — 콘텐츠 품질 분석](#4-content_allcsv--콘텐츠-품질-분석)
5. [links_all.csv — 링크 구조 분석](#5-links_allcsv--링크-구조-분석)
6. [security_all.csv — 보안 분석](#6-security_allcsv--보안-분석)
7. [canonicals_all.csv — 캐노니컬 분석](#7-canonicals_allcsv--캐노니컬-분석)
8. [directives_all.csv — 크롤 지시자 분석](#8-directives_allcsv--크롤-지시자-분석)
9. [h1_all.csv / h2_all.csv — 헤딩 태그 분석](#9-h1_allcsv--h2_allcsv--헤딩-태그-분석)
10. [page_titles_duplicate.csv / meta_description_duplicate.csv — 중복 분석](#10-중복-타이틀--메타-설명-분석)
11. [javascript_all.csv — JS 렌더링 분석](#11-javascript_allcsv--js-렌더링-분석)
12. [images_all.csv — 이미지 분석](#12-images_allcsv--이미지-분석)
13. [redirects.csv — 리다이렉트 분석](#13-redirectscsv--리다이렉트-분석)
14. [issues.csv — SEO 이슈 분석](#14-issuescsv--seo-이슈-분석)
15. [external_all.csv / inlinks.csv — 외부 링크 및 인링크 분석](#15-외부-링크-및-인링크-분석)
16. [structured_data_all.csv — 구조화 데이터 분석](#16-structured_data_allcsv--구조화-데이터-분석)
17. [hreflang_all.csv — 다국어 분석](#17-hreflang_allcsv--다국어-분석)
18. [url_all.csv / pagination_all.csv / meta_keywords_all.csv — 기타](#18-기타-csv-분석)
19. [crawl_warnings.csv — 크롤 경고](#19-crawl_warningscsv--크롤-경고)
20. [statistics_summary.csv / JSON — 통계 요약](#20-statistics_summarycsv--json--통계-요약)
21. [run_manifest.json / run_summary.json — 실행 메타데이터](#21-run_manifestjson--run_summaryjson--실행-메타데이터)
22. [크로스 파일 종합 분석](#22-크로스-파일-종합-분석)
23. [Looker Studio 대시보드 구축 가이드](#23-looker-studio-대시보드-구축-가이드)
24. [Tableau 대시보드 구축 가이드](#24-tableau-대시보드-구축-가이드)

---

## 1. 분석 환경 세팅

### Python 환경

```python
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams

# 한글 폰트 설정 (Windows)
rcParams['font.family'] = 'Malgun Gothic'
# macOS: rcParams['font.family'] = 'AppleGothic'
# Linux: rcParams['font.family'] = 'NanumGothic'
rcParams['axes.unicode_minus'] = False

# Seaborn 테마
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)

# 공통 색상 팔레트
STATUS_COLORS = {'2xx': '#2ca02c', '3xx': '#ff7f0e', '4xx': '#d62728', '5xx': '#7f7f7f'}
SEVERITY_COLORS = {'Critical': '#d62728', 'Warning': '#ff7f0e', 'Info': '#1f77b4'}
BOOL_COLORS = {True: '#2ca02c', False: '#d62728'}
```

### 데이터 로드 함수

```python
def load_crawl_data(domain_folder: str) -> dict:
    """크롤 결과 CSV 전체를 dict로 로드"""
    import os
    data = {}
    csv_files = [
        'internal_all', 'external_all', 'images_all', 'css', 'javascript',
        'hreflang_all', 'structured_data_all', 'issues', 'redirects', 'inlinks',
        'sitemaps_all', 'response_codes_all', 'security_all', 'content_all',
        'links_all', 'canonicals_all', 'directives_all', 'h1_all', 'h2_all',
        'meta_keywords_all', 'pagination_all', 'url_all',
        'page_titles_duplicate', 'meta_description_duplicate',
        'javascript_all', 'custom_extraction_all', 'custom_search_all',
        'crawl_warnings', 'statistics_summary',
    ]
    for name in csv_files:
        path = os.path.join(domain_folder, f"{name}.csv")
        if os.path.exists(path):
            data[name] = pd.read_csv(path, encoding='utf-8-sig')
    return data

# 사용 예시
data = load_crawl_data('crawl_output/example')
internal = data['internal_all']
```

---

## 2. internal_all.csv — 핵심 종합 데이터

가장 중요한 파일입니다. 크롤된 모든 내부 페이지의 67개 컬럼 데이터를 담고 있으며, 대부분의 분석이 이 파일에서 시작됩니다.

> **v2 신규 컬럼**: `Canonical Status`, `Title Status`, `Meta Description Status`, `H1 Status`, `Page Type`, `Original Status Code`, `Redirect Status`, `Redirect Chain Length`, `Images Missing Alt Attribute`, `Images with Alt Over 100`

### 컬럼별 의미 · 정상/이상 기준

#### 기본 정보

| 컬럼 | 의미 | 정상 | 이상/문제 |
|------|------|------|----------|
| `Address` | 페이지 URL | - | - |
| `Content Type` | HTTP Content-Type 헤더 | `text/html; charset=utf-8` | 빈 값, `application/octet-stream` (서버 설정 오류) |
| `Status Code` | HTTP 응답 코드 | `200` | `404`(깨진 링크), `500`(서버 오류), `301/302`(리다이렉트) |
| `Status` | 상태 코드 설명 | `OK` | `Not Found`, `Internal Server Error` |
| `Indexability` | 검색엔진 색인 가능 여부 | `Indexable` | `Non-Indexable` (의도하지 않은 경우 문제) |
| `Indexability Status` | 색인 불가 사유 | `Indexable` | `noindex`, `Canonicalised`, `Blocked by robots.txt` |

#### 타이틀 태그

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Title 1` | 페이지 타이틀 | 고유하고 페이지 내용을 설명 | 빈 값(누락), 다른 페이지와 동일(중복), "Untitled"(기본값) |
| `Title 1 Length` | 타이틀 문자 수 | **30~60자** | <30자(너무 짧음), >60자(SERP에서 잘릴 수 있음) |
| `Title 1 Pixel Width` | SERP 표시 예상 픽셀 | **< 580px** | >580px (Google SERP에서 말줄임 처리됨) |

#### 메타 설명

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Meta Description 1` | 메타 디스크립션 | 고유하고 매력적인 설명 | 빈 값(누락), 중복 |
| `Meta Description 1 Length` | 메타 설명 문자 수 | **70~160자** | <70자(너무 짧음), >160자(잘림) |
| `Meta Description 1 Pixel Width` | SERP 표시 예상 픽셀 | **< 920px** | >920px (SERP에서 잘림) |

#### 메타 키워드

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Meta Keywords 1` | meta keywords 값 | 비어있어도 무방 (SEO 영향 없음) | 과도한 키워드 스터핑 |
| `Meta Keywords 1 Length` | 키워드 문자 수 | 0 또는 적절한 수준 | >200자 (키워드 스터핑 의심) |

#### 헤딩 태그

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `H1-1` | 첫 번째 H1 텍스트 | 페이지당 정확히 1개, 고유 | 빈 값(H1 누락), 타이틀과 완전 동일 |
| `H1-1 Length` | H1 문자 수 | **20~70자** | 0(누락), >70자(너무 긺) |
| `H2-1`, `H2-2` | 첫/두 번째 H2 | 있으면 좋음 | 빈 값이어도 치명적이진 않음 |

#### 지시자 (Directives)

| 컬럼 | 의미 | 정상 | 이상/문제 |
|------|------|------|----------|
| `Meta Robots 1` | meta robots 값 | `index, follow` 또는 빈 값 | 의도치 않은 `noindex`, `nofollow` |
| `X-Robots-Tag 1` | HTTP X-Robots-Tag 헤더 | 빈 값 (설정 안 함) | 의도치 않은 `noindex` |
| `Meta Refresh 1` | meta refresh 태그 | 빈 값 (미사용) | 사용 시 SEO 부정적 — 301 리다이렉트로 대체해야 |
| `Canonical Link Element 1` | rel=canonical URL | 자기 자신(self-referencing) 또는 정규 URL | 빈 값(누락), 잘못된 URL, 다른 도메인으로 지정 |
| `rel="next" 1` / `rel="prev" 1` | 페이지네이션 | 페이지네이션 있으면 설정 | 불완전한 체인 |
| `HTTP rel="next" 1` / `HTTP rel="prev" 1` | HTTP Link 헤더 | HTML 태그와 일치 | HTML과 HTTP 불일치 |

#### 콘텐츠 품질

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Word Count` | 본문 단어 수 | **300~3000** (페이지 유형에 따라 다름) | <200 (Thin Content), >10000 (과도) |
| `Sentence Count` | 문장 수 | 문맥에 따라 | 0 (콘텐츠 없음) |
| `Average Words Per Sentence` | 문장당 평균 단어 | **15~25** | >30 (가독성 저하) |
| `Flesch Reading Ease Score` | 가독성 점수 (0~100) | **60~80** (일반 웹콘텐츠) | <30 (매우 어려움), >90 (지나치게 단순) |
| `Readability` | 가독성 등급 | `Easy`, `Fairly Easy`, `Standard` | `Difficult`, `Fairly Difficult` |
| `Text Ratio` | 텍스트/HTML 비율 (%) | **> 10%** | <10% (코드 대비 콘텐츠 부족), <5% (심각) |

#### 크기 · 성능

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Size (bytes)` | HTML 문서 크기 | **< 100KB** | >200KB (큰 페이지), >500KB (매우 큼) |
| `Transferred (bytes)` | 네트워크 전송 크기 | Size보다 작음 (gzip) | Size와 동일 (압축 미적용) |
| `Response Time` | HTTP 응답 시간 (초) | **< 0.5초** | 0.5~1.0초 (느림), >1.0초 (매우 느림), >3초 (심각) |

#### 사이트 구조

| 컬럼 | 의미 | 정상 범위 | 이상/문제 |
|------|------|----------|----------|
| `Crawl Depth` | 시작 URL부터 클릭 수 | **0~3** | >3 (깊음), >5 (매우 깊음 — 접근성 문제) |
| `Folder Depth` | URL 경로 세그먼트 수 | **1~4** | >5 (URL 구조 복잡) |
| `Link Score` | 내부 PageRank (0~100) | 상위 페이지: >50 | 0 (인링크 없음), <1 (고아 페이지) |

#### 링크 메트릭

| 컬럼 | 의미 | 정상 | 이상/문제 |
|------|------|------|----------|
| `Inlinks` | 인링크 수 (이 페이지를 가리키는) | **> 1** | 0 (고아 페이지 — 검색엔진이 발견 못함) |
| `Unique Inlinks` | 고유 소스 인링크 | > 0 | 0 |
| `% of Total` | 전체 인링크 중 비율 | 고르게 분배 | 한 페이지에 >30% 집중 (과도) |
| `Outlinks` | 발신 링크 수 | 적정 수준 | >100 (과도 — 링크 가치 희석) |
| `External Outlinks` | 외부 링크 수 | 적정 수준 | 페이지당 >50 (과도) |

#### 기타

| 컬럼 | 의미 | 정상 | 이상/문제 |
|------|------|------|----------|
| `Hash` | 콘텐츠 MD5 해시 | 고유 | 다른 URL과 동일 해시 → 중복 콘텐츠 |
| `Last Modified` | Last-Modified 헤더 | 최근 날짜 | 매우 오래됨 또는 빈 값 |
| `Redirect URL` | 리다이렉트 대상 | 빈 값 (리다이렉트 아님) | 값이 있으면 이 페이지는 리다이렉트 |
| `Redirect Type` | 301/302/307 등 | `301` (영구) | `302` (임시 — 영구면 301로 변경) |
| `HTTP Version` | HTTP 프로토콜 버전 | `HTTP/2` | `HTTP/1.1` (HTTP/2 미지원) |
| `URL Encoded Address` | 퍼센트 인코딩 URL | URL과 동일 | 한글 등 비ASCII 문자 포함 시 인코딩 |
| `HTML Lang` | html lang 속성 | 올바른 언어 코드 (`ko`, `en`) | 빈 값 또는 잘못된 코드 |

### Python EDA: internal_all.csv 종합 분석

```python
internal = data['internal_all']

# ============================================================
# 1. 기본 통계 요약
# ============================================================
print(f"총 URL 수: {len(internal)}")
print(f"색인 가능: {(internal['Indexability'] == 'Indexable').sum()} ({(internal['Indexability'] == 'Indexable').mean()*100:.1f}%)")
print(f"평균 응답 시간: {internal['Response Time'].astype(float).mean():.3f}초")
print(f"평균 단어 수: {internal['Word Count'].mean():.0f}")

# ============================================================
# 2. 타이틀 길이 분포 + 최적 구간 표시
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# 타이틀 길이
ax = axes[0]
title_len = internal['Title 1 Length'].dropna()
ax.hist(title_len, bins=40, color='#4C72B0', edgecolor='white', alpha=0.8)
ax.axvspan(30, 60, alpha=0.15, color='green', label='최적 범위 (30~60)')
ax.axvline(30, color='green', linestyle='--', alpha=0.5)
ax.axvline(60, color='green', linestyle='--', alpha=0.5)
ax.set_xlabel('Title Length (문자 수)')
ax.set_ylabel('페이지 수')
ax.set_title('타이틀 길이 분포')
ax.legend()

# 메타 설명 길이
ax = axes[1]
desc_len = internal['Meta Description 1 Length'].dropna()
ax.hist(desc_len, bins=40, color='#DD8452', edgecolor='white', alpha=0.8)
ax.axvspan(70, 160, alpha=0.15, color='green', label='최적 범위 (70~160)')
ax.axvline(70, color='green', linestyle='--', alpha=0.5)
ax.axvline(160, color='green', linestyle='--', alpha=0.5)
ax.set_xlabel('Meta Description Length (문자 수)')
ax.set_ylabel('페이지 수')
ax.set_title('메타 설명 길이 분포')
ax.legend()

plt.tight_layout()
plt.savefig('title_meta_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 3. 타이틀/메타 설명 현황 요약 (파이 차트)
# ============================================================
def classify_title(row):
    if pd.isna(row['Title 1']) or row['Title 1'] == '':
        return '누락'
    elif row['Title 1 Length'] < 30:
        return '너무 짧음 (<30자)'
    elif row['Title 1 Length'] > 60:
        return '너무 긺 (>60자)'
    else:
        return '최적'

internal['title_status'] = internal.apply(classify_title, axis=1)

fig, ax = plt.subplots(figsize=(7, 7))
colors = {'최적': '#2ca02c', '너무 짧음 (<30자)': '#ff7f0e', '너무 긺 (>60자)': '#d62728', '누락': '#7f7f7f'}
counts = internal['title_status'].value_counts()
ax.pie(counts, labels=counts.index, autopct='%1.1f%%',
       colors=[colors.get(x, '#999') for x in counts.index], startangle=140)
ax.set_title('타이틀 태그 현황')
plt.savefig('title_status_pie.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 4. 응답 시간 분포 (로그 스케일)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 5))
resp_time = internal['Response Time'].astype(float)
ax.hist(resp_time, bins=50, color='#55A868', edgecolor='white', alpha=0.8)
ax.axvline(0.5, color='orange', linestyle='--', label='경고 (0.5초)')
ax.axvline(1.0, color='red', linestyle='--', label='위험 (1.0초)')
ax.set_xlabel('Response Time (초)')
ax.set_ylabel('페이지 수')
ax.set_title('응답 시간 분포')
ax.legend()
plt.savefig('response_time_dist.png', dpi=150, bbox_inches='tight')
plt.show()

# 느린 페이지 TOP 20
slow_pages = internal.nlargest(20, 'Response Time')[['Address', 'Response Time', 'Status Code', 'Word Count']]
print("\n=== 느린 페이지 TOP 20 ===")
print(slow_pages.to_string(index=False))

# ============================================================
# 5. 크롤 깊이 분포
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
depth_counts = internal['Crawl Depth'].value_counts().sort_index()
bars = ax.bar(depth_counts.index.astype(str), depth_counts.values, color='#4C72B0', edgecolor='white')
for i, bar in enumerate(bars):
    if depth_counts.index[i] > 3:
        bar.set_color('#d62728')  # 깊이 4 이상은 빨간색
ax.set_xlabel('Crawl Depth')
ax.set_ylabel('페이지 수')
ax.set_title('크롤 깊이 분포 (4 이상 = 빨간색)')
plt.savefig('crawl_depth_dist.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 6. Word Count vs Response Time 산점도
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(
    internal['Word Count'],
    internal['Response Time'].astype(float),
    c=internal['Crawl Depth'],
    cmap='YlOrRd',
    alpha=0.6,
    s=20,
)
plt.colorbar(scatter, label='Crawl Depth')
ax.set_xlabel('Word Count')
ax.set_ylabel('Response Time (초)')
ax.set_title('콘텐츠 양 vs 응답 시간 (색상 = 크롤 깊이)')
ax.axhline(0.5, color='orange', linestyle='--', alpha=0.5)
ax.axhline(1.0, color='red', linestyle='--', alpha=0.5)
plt.savefig('wordcount_vs_response.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 7. 색인 가능성 요약
# ============================================================
idx_summary = internal.groupby(['Indexability', 'Indexability Status']).size().reset_index(name='Count')
idx_summary = idx_summary.sort_values('Count', ascending=False)
print("\n=== 색인 가능성 요약 ===")
print(idx_summary.to_string(index=False))
```

---

## 3. response_codes_all.csv — HTTP 상태 코드 분석

### 컬럼별 정상/이상 기준

| 컬럼 | 정상 | 문제 |
|------|------|------|
| `Status Code` | `200` | `301/302`(리다이렉트), `403`(접근거부), `404`(깨진링크), `500`(서버오류) |
| `Response Time` | <0.5초 | >1.0초 |
| `Redirect URL` | 빈 값 | 값이 있으면 리다이렉트 발생 |

### 상태 코드 분류 기준

| 코드 범위 | 의미 | SEO 영향 |
|-----------|------|---------|
| **2xx** | 성공 | 정상 — 검색엔진이 콘텐츠를 수집 가능 |
| **3xx** | 리다이렉트 | 301은 양호, 302는 주의 (링크 가치 전달 미보장) |
| **4xx** | 클라이언트 오류 | 심각 — 깨진 링크, 크롤 예산 낭비 |
| **5xx** | 서버 오류 | 심각 — 검색엔진이 페이지를 포기할 수 있음 |

### Python EDA

```python
resp = data['response_codes_all']

# 상태 코드 그룹 생성
resp['Status Group'] = resp['Status Code'].astype(str).str[0] + 'xx'

# ============================================================
# 1. 상태 코드 그룹 분포 (도넛 차트)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 도넛 차트
ax = axes[0]
group_counts = resp['Status Group'].value_counts()
colors_map = {'2xx': '#2ca02c', '3xx': '#ff7f0e', '4xx': '#d62728', '5xx': '#7f7f7f', '1xx': '#aec7e8'}
pie_colors = [colors_map.get(g, '#999') for g in group_counts.index]
wedges, texts, autotexts = ax.pie(
    group_counts, labels=group_counts.index, autopct='%1.1f%%',
    colors=pie_colors, startangle=90, pctdistance=0.75,
)
centre_circle = plt.Circle((0, 0), 0.50, fc='white')
ax.add_artist(centre_circle)
ax.set_title('HTTP 상태 코드 분포')

# 개별 코드 TOP 10
ax = axes[1]
code_counts = resp['Status Code'].value_counts().head(10)
bars = ax.barh(code_counts.index.astype(str), code_counts.values, color='#4C72B0')
ax.set_xlabel('페이지 수')
ax.set_title('상태 코드 TOP 10')
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('status_code_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. 상태 코드별 평균 응답 시간
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
avg_rt = resp.groupby('Status Code')['Response Time'].mean().sort_values(ascending=False).head(10)
ax.barh(avg_rt.index.astype(str), avg_rt.values, color='#DD8452')
ax.set_xlabel('평균 Response Time (초)')
ax.set_title('상태 코드별 평균 응답 시간')
ax.invert_yaxis()
plt.savefig('status_avg_response.png', dpi=150, bbox_inches='tight')
plt.show()

# 4xx/5xx 문제 페이지 목록
problem_pages = resp[resp['Status Code'] >= 400][['Address', 'Status Code', 'Status', 'Inlinks']]
problem_pages = problem_pages.sort_values('Inlinks', ascending=False)
print(f"\n=== 4xx/5xx 오류 페이지: {len(problem_pages)}개 ===")
print(problem_pages.head(20).to_string(index=False))
```

---

## 4. content_all.csv — 콘텐츠 품질 분석

### 컬럼별 정상/이상 기준

| 컬럼 | 정상 범위 | 이상/문제 |
|------|----------|----------|
| `Word Count` | **300~3000** | <200 (Thin Content — 검색엔진 품질 판단 부정적) |
| `Sentence Count` | > 5 | 0~2 (내용 부실) |
| `Average Words Per Sentence` | **15~25** | >30 (가독성 저하), <8 (비정상적으로 짧음) |
| `Flesch Reading Ease Score` | **60~80** | <30 (매우 어려움), >90 (너무 단순) |
| `Readability` | `Easy` ~ `Standard` | `Difficult` |
| `Text Ratio` | **> 10%** | <10% (HTML 대비 텍스트 부족) |
| `Closest Similarity Match` | 빈 값 | URL이 있으면 유사 콘텐츠 존재 |
| `No. Near Duplicates` | 0 | >0 (유사 중복 감지) |

### Flesch Reading Ease 점수 해석

| 점수 | 등급 | 의미 |
|------|------|------|
| 90~100 | Very Easy | 초등학교 수준 — 웹에서는 이상적이지만 전문 콘텐츠에는 부적합 |
| 80~90 | Easy | 쉬운 영어 — 일반 웹콘텐츠에 좋음 |
| 70~80 | Fairly Easy | 비교적 쉬움 — 대부분의 독자가 이해 |
| 60~70 | Standard | 표준 — 일반 웹콘텐츠 적정 수준 |
| 50~60 | Fairly Difficult | 다소 어려움 — 주의 필요 |
| 30~50 | Difficult | 어려움 — 학술/법률 수준 |
| 0~30 | Very Difficult | 매우 어려움 — 전문가 대상 |

### Python EDA

```python
content = data['content_all']

# ============================================================
# 1. 콘텐츠 양 분포 (히스토그램 + KDE)
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Word Count
ax = axes[0][0]
wc = content['Word Count'].clip(upper=5000)
sns.histplot(wc, bins=50, kde=True, ax=ax, color='#4C72B0')
ax.axvline(200, color='red', linestyle='--', label='Thin Content 기준 (200)')
ax.axvline(300, color='orange', linestyle='--', label='최소 권장 (300)')
ax.set_title('Word Count 분포')
ax.legend()

# Flesch Score
ax = axes[0][1]
flesch = content['Flesch Reading Ease Score'].astype(float).dropna()
sns.histplot(flesch, bins=30, kde=True, ax=ax, color='#55A868')
ax.axvspan(60, 80, alpha=0.15, color='green', label='최적 범위')
ax.set_title('Flesch Reading Ease Score 분포')
ax.legend()

# Text Ratio
ax = axes[1][0]
tr = content['Text Ratio'].astype(float).dropna()
sns.histplot(tr, bins=40, kde=True, ax=ax, color='#DD8452')
ax.axvline(10, color='red', linestyle='--', label='최소 기준 (10%)')
ax.set_title('Text Ratio 분포 (%)')
ax.legend()

# Readability 등급 분포
ax = axes[1][1]
readability_order = ['Easy', 'Fairly Easy', 'Standard', 'Fairly Difficult', 'Difficult']
read_counts = content['Readability'].value_counts()
read_counts = read_counts.reindex(readability_order).dropna()
colors_read = ['#2ca02c', '#98df8a', '#ffbb78', '#ff7f0e', '#d62728']
ax.barh(read_counts.index, read_counts.values, color=colors_read[:len(read_counts)])
ax.set_title('가독성 등급 분포')
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('content_quality_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. Thin Content 페이지 식별
# ============================================================
thin = content[content['Word Count'] < 200]
print(f"\n=== Thin Content 페이지 (<200 단어): {len(thin)}개 ({len(thin)/len(content)*100:.1f}%) ===")
print(thin[['Address', 'Word Count', 'Text Ratio', 'Readability']].head(20).to_string(index=False))

# ============================================================
# 3. Word Count vs Flesch Score 산점도
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(
    content['Word Count'].clip(upper=5000),
    content['Flesch Reading Ease Score'].astype(float),
    c=content['Text Ratio'].astype(float),
    cmap='RdYlGn',
    alpha=0.6, s=20,
)
plt.colorbar(scatter, label='Text Ratio (%)')
ax.set_xlabel('Word Count')
ax.set_ylabel('Flesch Reading Ease Score')
ax.set_title('콘텐츠 양 vs 가독성 (색상 = Text Ratio)')
ax.axhline(60, color='green', linestyle='--', alpha=0.3, label='최적 하한 (60)')
ax.axvline(300, color='red', linestyle='--', alpha=0.3, label='최소 단어 (300)')
ax.legend()
plt.savefig('wordcount_vs_flesch.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 4. 유사 중복 페이지
# ============================================================
near_dup = content[content['No. Near Duplicates'].fillna(0).astype(int) > 0]
print(f"\n=== 유사 중복 감지 페이지: {len(near_dup)}개 ===")
if len(near_dup) > 0:
    print(near_dup[['Address', 'Closest Similarity Match', 'No. Near Duplicates']].to_string(index=False))
```

---

## 5. links_all.csv — 링크 구조 분석

### 컬럼별 정상/이상 기준

| 컬럼 | 정상 | 문제 |
|------|------|------|
| `Crawl Depth` | 0~3 | >3 (중요 페이지인데 깊음) |
| `Link Score` | 분포에 따라 상대적 | 0 (고아 페이지) |
| `Inlinks` | > 0 | 0 (고아 페이지) |
| `Unique Inlinks` | > 0 | 0 |
| `% of Total` | 고르게 분배 | >30% (한 페이지에 과도 집중) |
| `Outlinks` | 적정 수준 (10~50) | >100 (과도 — Google은 페이지당 합리적 수의 링크 권장) |
| `External Outlinks` | 적정 수준 | 페이지당 >50 (과도) |

### Python EDA

```python
links = data['links_all']

# ============================================================
# 1. Link Score 분포 (로그 스케일)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
ls = links['Link Score'].astype(float).dropna()
sns.histplot(ls, bins=50, kde=True, ax=ax, color='#C44E52')
ax.set_title('Link Score 분포 (내부 PageRank)')
ax.set_xlabel('Link Score (0~100)')

ax = axes[1]
inlinks = links['Inlinks'].astype(int)
sns.histplot(inlinks.clip(upper=inlinks.quantile(0.95)), bins=40, kde=True, ax=ax, color='#4C72B0')
ax.set_title('인링크 수 분포 (상위 95%)')
ax.set_xlabel('Inlinks')

plt.tight_layout()
plt.savefig('link_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. 고아 페이지 감지 (Inlinks = 0)
# ============================================================
orphans = links[links['Inlinks'].astype(int) == 0]
print(f"\n=== 고아 페이지 (Inlinks = 0): {len(orphans)}개 ===")
print(orphans[['Address', 'Crawl Depth', 'Link Score', 'Outlinks']].head(20).to_string(index=False))

# ============================================================
# 3. Link Score TOP 20 / BOTTOM 20
# ============================================================
print("\n=== Link Score 상위 20 페이지 ===")
print(links.nlargest(20, 'Link Score')[['Address', 'Link Score', 'Inlinks', 'Crawl Depth']].to_string(index=False))

print("\n=== Link Score 하위 20 페이지 (0 제외) ===")
low = links[links['Link Score'].astype(float) > 0].nsmallest(20, 'Link Score')
print(low[['Address', 'Link Score', 'Inlinks', 'Crawl Depth']].to_string(index=False))

# ============================================================
# 4. Inlinks vs Link Score 산점도
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(links['Inlinks'].astype(int), links['Link Score'].astype(float),
           alpha=0.5, s=15, c=links['Crawl Depth'].astype(int), cmap='viridis_r')
ax.set_xlabel('Inlinks')
ax.set_ylabel('Link Score')
ax.set_title('인링크 수 vs Link Score')
plt.colorbar(ax.collections[0], label='Crawl Depth')
plt.savefig('inlinks_vs_linkscore.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 5. 과도한 아웃링크 페이지
# ============================================================
excessive_out = links[links['Outlinks'].astype(int) > 100]
print(f"\n=== 과도한 아웃링크 (>100): {len(excessive_out)}개 ===")
if len(excessive_out) > 0:
    print(excessive_out[['Address', 'Outlinks', 'External Outlinks', 'Link Score']].to_string(index=False))
```

---

## 6. security_all.csv — 보안 분석

### 컬럼별 정상/이상 기준

| 컬럼 | 정상 | 문제 |
|------|------|------|
| `HTTPS` | `True` | `False` (HTTP만 사용 — Google 순위 신호에 부정적) |
| `Mixed Content` | `False` | `True` (HTTPS 페이지에서 HTTP 리소스 로드) |
| `HSTS` | `True` | `False` (HTTP → HTTPS 강제 전환 미설정) |
| `X-Frame-Options` | `DENY` 또는 `SAMEORIGIN` | 빈 값 (클릭재킹 취약) |
| `X-Content-Type-Options` | `nosniff` | 빈 값 (MIME 스니핑 취약) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` 등 | 빈 값 (레퍼러 정보 노출) |
| `Content-Security-Policy` | 설정됨 | 빈 값 (XSS 취약) |
| `HTTP Version` | `HTTP/2` | `HTTP/1.1` (성능 저하) |

### Python EDA

```python
security = data['security_all']

# ============================================================
# 1. 보안 헤더 적용률 (레이더 차트)
# ============================================================
total = len(security)
metrics = {
    'HTTPS': (security['HTTPS'].astype(str).str.lower() == 'true').sum() / total * 100,
    'HSTS': (security['HSTS'].astype(str).str.lower() == 'true').sum() / total * 100,
    'X-Frame-Options': (security['X-Frame-Options'].notna() & (security['X-Frame-Options'] != '')).sum() / total * 100,
    'X-Content-Type': (security['X-Content-Type-Options'].notna() & (security['X-Content-Type-Options'] != '')).sum() / total * 100,
    'Referrer-Policy': (security['Referrer-Policy'].notna() & (security['Referrer-Policy'] != '')).sum() / total * 100,
    'CSP': (security['Content-Security-Policy'].notna() & (security['Content-Security-Policy'] != '')).sum() / total * 100,
}

# 레이더 차트
labels = list(metrics.keys())
values = list(metrics.values())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
values += values[:1]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.fill(angles, values, color='#4C72B0', alpha=0.25)
ax.plot(angles, values, color='#4C72B0', linewidth=2)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=10)
ax.set_ylim(0, 100)
ax.set_title('보안 헤더 적용률 (%)', size=14, pad=20)
for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
    ax.text(angle, value + 3, f'{value:.0f}%', ha='center', size=9)
plt.savefig('security_radar.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. Mixed Content 페이지
# ============================================================
mixed = security[security['Mixed Content'].astype(str).str.lower() == 'true']
print(f"\n=== Mixed Content 페이지: {len(mixed)}개 ===")
if len(mixed) > 0:
    print(mixed[['Address', 'HTTPS', 'Mixed Content']].head(20).to_string(index=False))
```

---

## 7. canonicals_all.csv — 캐노니컬 분석

### 캐노니컬 상태 분류 (5단계)

> v2에서 `Canonical Status` 컬럼이 CSV에 직접 포함됩니다. 별도 Python 분류 불필요.

| 상태 | 설명 | SEO 영향 |
|------|------|---------|
| **Missing** | canonical 태그 없음 | 경고 — 중복 콘텐츠 위험 |
| **Self-Referencing** | canonical이 자기 자신 | 정상 — 권장되는 설정 |
| **Canonicalised** | 다른 URL을 canonical로 지정 | 정상 (의도적) 또는 문제 (잘못 지정) |
| **Canonical to Redirect** | canonical 대상이 리다이렉트 응답 | 심각 — canonical 대상을 최종 URL로 변경해야 함 |
| **Canonical to Non-200** | canonical 대상이 200이 아닌 응답 (404/500 등) | 심각 — 즉시 수정 필요 |

### Python EDA

```python
canonicals = data['canonicals_all']

# v2: Canonical Status 컬럼이 이미 5단계로 분류되어 있음
fig, ax = plt.subplots(figsize=(10, 6))
status_counts = canonicals['Canonical Status'].value_counts()
colors_can = {
    'Self-Referencing': '#2ca02c',
    'Canonicalised': '#ff7f0e',
    'Missing': '#d62728',
    'Canonical to Redirect': '#9467bd',
    'Canonical to Non-200': '#8c564b',
}
ax.barh(status_counts.index, status_counts.values,
        color=[colors_can.get(x, '#999') for x in status_counts.index])
ax.set_xlabel('페이지 수')
ax.set_title('캐노니컬 태그 상태 (5단계 분류)')
for i, (v, label) in enumerate(zip(status_counts.values, status_counts.index)):
    ax.text(v + 0.5, i, str(v), va='center')
plt.savefig('canonical_status.png', dpi=150, bbox_inches='tight')
plt.show()

# 위험 캐노니컬 상세
dangerous = canonicals[canonicals['Canonical Status'].isin(['Canonical to Redirect', 'Canonical to Non-200'])]
if len(dangerous) > 0:
    print(f"\n⚠️ 위험 캐노니컬 {len(dangerous)}건:")
    print(dangerous[['Address', 'Canonical Link Element 1', 'Canonical Status']].to_string(index=False))

print(f"\n=== 캐노니컬 요약 ===")
for status, count in status_counts.items():
    print(f"  {status}: {count}개 ({count/len(canonicals)*100:.1f}%)")
```

---

## 8. directives_all.csv — 크롤 지시자 분석

### 주의해야 할 지시자

| 지시자 | 의미 | 정상 | 문제 |
|--------|------|------|------|
| `index, follow` | 색인 허용, 링크 추적 | 기본값 — 정상 | - |
| `noindex` | 색인 차단 | 의도적이면 정상 | 중요 페이지에 실수로 적용된 경우 |
| `nofollow` | 링크 추적 차단 | 특수 페이지에 의도적 사용 | 내부 링크에 사용 — Link Juice 낭비 |
| `none` | noindex + nofollow | 매우 제한적 사용 | 잘못 적용된 경우 심각 |
| `noarchive` | 캐시 차단 | 특정 상황에서 정상 | 불필요한 경우 제거 권장 |

### Python EDA

```python
directives = data['directives_all']

# noindex 페이지 식별
noindex = directives[
    directives['Meta Robots 1'].str.contains('noindex', case=False, na=False) |
    directives['X-Robots-Tag 1'].str.contains('noindex', case=False, na=False)
]
print(f"=== noindex 페이지: {len(noindex)}개 ({len(noindex)/len(directives)*100:.1f}%) ===")
print(noindex[['Address', 'Meta Robots 1', 'X-Robots-Tag 1']].head(20).to_string(index=False))

# meta refresh 사용 페이지 (비권장)
meta_refresh = directives[directives['Meta Refresh 1'].notna() & (directives['Meta Refresh 1'] != '')]
if len(meta_refresh) > 0:
    print(f"\n=== Meta Refresh 사용 페이지 (301으로 대체 권장): {len(meta_refresh)}개 ===")
    print(meta_refresh[['Address', 'Meta Refresh 1']].to_string(index=False))
```

---

## 9. h1_all.csv / h2_all.csv — 헤딩 태그 분석

### 정상/이상 기준

| 상태 | 기준 | SEO 영향 |
|------|------|---------|
| H1 누락 | `H1-1`이 빈 값 | 경고 — 페이지의 주제를 검색엔진에 전달 못함 |
| H1 다수 | `Occurrences` > 1 | 경고 — HTML5에서는 허용되지만 SEO 관점에서 1개 권장 |
| H1 과도하게 긴 | `H1-1 Length` > 70자 | 주의 — 간결하게 작성 권장 |
| H2 부재 | `H2-1`이 빈 값 | 정보 — 콘텐츠 구조가 부실할 수 있음 |

### Python EDA

```python
h1 = data['h1_all']
h2 = data['h2_all']

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# H1 Occurrences 분포
ax = axes[0]
h1_occ = h1['Occurrences'].value_counts().sort_index()
colors_h1 = ['#2ca02c' if x == 1 else '#ff7f0e' if x == 0 else '#d62728' for x in h1_occ.index]
ax.bar(h1_occ.index.astype(str), h1_occ.values, color=colors_h1)
ax.set_xlabel('H1 태그 수')
ax.set_ylabel('페이지 수')
ax.set_title('페이지당 H1 태그 수 (1개 = 정상)')

# H1 길이 분포
ax = axes[1]
h1_len = h1['H1-1 Length'].dropna()
ax.hist(h1_len[h1_len > 0], bins=30, color='#4C72B0', edgecolor='white')
ax.axvline(70, color='red', linestyle='--', label='권장 최대 (70자)')
ax.set_xlabel('H1 길이 (문자 수)')
ax.set_ylabel('페이지 수')
ax.set_title('H1 길이 분포')
ax.legend()

# H2 Occurrences 분포
ax = axes[2]
h2_occ = h2['Occurrences'].value_counts().sort_index().head(10)
ax.bar(h2_occ.index.astype(str), h2_occ.values, color='#DD8452')
ax.set_xlabel('H2 태그 수')
ax.set_ylabel('페이지 수')
ax.set_title('페이지당 H2 태그 수')

plt.tight_layout()
plt.savefig('heading_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# H1 누락 페이지
missing_h1 = h1[h1['Occurrences'] == 0]
print(f"\n=== H1 누락 페이지: {len(missing_h1)}개 ===")
print(missing_h1[['Address', 'Indexability']].head(20).to_string(index=False))

# 복수 H1 페이지
multi_h1 = h1[h1['Occurrences'] > 1]
print(f"\n=== 복수 H1 페이지: {len(multi_h1)}개 ===")
print(multi_h1[['Address', 'Occurrences', 'H1-1']].head(20).to_string(index=False))
```

---

## 10. 중복 타이틀 / 메타 설명 분석

### page_titles_duplicate.csv / meta_description_duplicate.csv

이 파일들에는 **2개 이상의 페이지가 동일한 타이틀/메타 설명을 사용하는 경우**만 포함됩니다.

| 컬럼 | 의미 |
|------|------|
| `Occurrences` | 같은 값을 공유하는 페이지 수 |
| `Title 1` / `Meta Description 1` | 중복된 값 |

### 왜 문제인가

- 검색엔진이 각 페이지를 구분하기 어려움
- SERP에서 사용자가 클릭할 페이지를 선택하기 어려움
- 크롤 예산 낭비 가능

### Python EDA

```python
dup_titles = data.get('page_titles_duplicate', pd.DataFrame())
dup_desc = data.get('meta_description_duplicate', pd.DataFrame())

if len(dup_titles) > 0:
    # 중복 타이틀 그룹별 요약
    dup_summary = dup_titles.groupby('Title 1').agg(
        Pages=('Address', 'count'),
        URLs=('Address', lambda x: list(x)[:5]),  # 샘플 5개
    ).sort_values('Pages', ascending=False)

    print(f"=== 중복 타이틀 그룹: {len(dup_summary)}개, 영향 페이지: {len(dup_titles)}개 ===")
    for title, row in dup_summary.head(10).iterrows():
        print(f"\n  [{row['Pages']}개 페이지] \"{title[:80]}\"")
        for url in row['URLs']:
            print(f"    - {url}")

    # 시각화: 중복 그룹 크기 분포
    fig, ax = plt.subplots(figsize=(10, 5))
    occ = dup_titles.groupby('Title 1')['Address'].count().value_counts().sort_index()
    ax.bar(occ.index.astype(str), occ.values, color='#C44E52')
    ax.set_xlabel('중복 페이지 수')
    ax.set_ylabel('그룹 수')
    ax.set_title('타이틀 중복 그룹 크기 분포')
    plt.savefig('dup_title_groups.png', dpi=150, bbox_inches='tight')
    plt.show()
```

---

## 11. javascript_all.csv — JS 렌더링 분석

### 컬럼별 의미 및 판단 기준

| 컬럼 | 의미 | 정상 | 문제 |
|------|------|------|------|
| `HTML Word Count` | 렌더링 전 단어 수 | 렌더링 후와 비슷 | 렌더링 후보다 매우 적음 |
| `Rendered HTML Word Count` | 렌더링 후 단어 수 | HTML Word Count와 비슷 | 크게 증가 (JS 의존) |
| `Word Count Change` | 렌더링 전후 단어 차이 | 0 또는 적음 | 큰 양수 (JS 의존 콘텐츠) |
| `JS Word Count %` | JS로 추가된 비율 | **< 20%** | >50% (핵심 콘텐츠가 JS에 의존) |
| `HTML Title` vs `Rendered HTML Title` | 렌더링 전후 타이틀 | 동일 | 다름 (JS가 타이틀 변경) |
| `HTML H1` vs `Rendered HTML H1` | 렌더링 전후 H1 | 동일 | 다름 (JS가 H1 생성) |
| `HTML Canonical` vs `Rendered HTML Canonical` | 렌더링 전후 canonical | 동일 | **다름 (심각한 색인 문제 가능)** |

### Python EDA

```python
js = data.get('javascript_all', pd.DataFrame())

if len(js) > 0:
    # ============================================================
    # 1. JS 의존도 분포
    # ============================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    js_pct = js['JS Word Count %'].astype(float).fillna(0)
    sns.histplot(js_pct, bins=30, kde=True, ax=ax, color='#9467bd')
    ax.axvline(20, color='orange', linestyle='--', label='주의 (20%)')
    ax.axvline(50, color='red', linestyle='--', label='위험 (50%)')
    ax.set_title('JS Word Count % 분포')
    ax.set_xlabel('JS로 추가된 단어 비율 (%)')
    ax.legend()

    # HTML vs Rendered Word Count 산점도
    ax = axes[1]
    ax.scatter(js['HTML Word Count'].astype(int),
               js['Rendered HTML Word Count'].astype(int),
               alpha=0.5, s=15, c='#4C72B0')
    # 대각선 (변화 없음)
    max_val = max(js['HTML Word Count'].astype(int).max(), js['Rendered HTML Word Count'].astype(int).max())
    ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='변화 없음')
    ax.set_xlabel('HTML Word Count (렌더링 전)')
    ax.set_ylabel('Rendered HTML Word Count (렌더링 후)')
    ax.set_title('렌더링 전 vs 후 단어 수')
    ax.legend()

    plt.tight_layout()
    plt.savefig('js_rendering_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

    # ============================================================
    # 2. 메타 태그 불일치 감지
    # ============================================================
    title_diff = js[js['HTML Title'] != js['Rendered HTML Title']]
    h1_diff = js[js['HTML H1'] != js['Rendered HTML H1']]
    canon_diff = js[js['HTML Canonical'] != js['Rendered HTML Canonical']]
    robots_diff = js[js['HTML Meta Robots 1'] != js['Rendered HTML Meta Robots 1']]

    print("=== JS 렌더링 전후 불일치 ===")
    print(f"  Title 불일치: {len(title_diff)}개")
    print(f"  H1 불일치: {len(h1_diff)}개")
    print(f"  Canonical 불일치: {len(canon_diff)}개 {'⚠️ 심각!' if len(canon_diff) > 0 else '✓'}")
    print(f"  Meta Robots 불일치: {len(robots_diff)}개 {'⚠️ 심각!' if len(robots_diff) > 0 else '✓'}")

    # JS 의존도 높은 페이지
    high_js = js[js['JS Word Count %'].astype(float) > 50]
    print(f"\n=== JS 의존도 > 50% 페이지: {len(high_js)}개 ===")
    print(high_js[['Address', 'HTML Word Count', 'Rendered HTML Word Count', 'JS Word Count %']].head(20).to_string(index=False))
```

---

## 12. images_all.csv — 이미지 분석

### 정상/이상 기준

| 항목 | 정상 | 문제 |
|------|------|------|
| Alt Text | 이미지를 설명하는 텍스트 | 빈 값 (접근성 + SEO 문제) |
| Missing Alt Attribute | `False` | `True` (alt 속성 자체가 없음) |
| Size (bytes) | < 200KB | > 500KB (페이지 로딩 속도 저하) |
| Dimensions | 적절한 크기 | 빈 값 (크기 미지정 — CLS 유발) |

### Python EDA

```python
images = data['images_all']

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Alt 텍스트 현황
ax = axes[0]
alt_status = {
    'Alt 있음': (images['Missing Alt Attribute'].astype(str) == 'False').sum(),
    'Alt 누락': (images['Missing Alt Attribute'].astype(str) == 'True').sum(),
}
ax.pie(alt_status.values(), labels=alt_status.keys(), autopct='%1.1f%%',
       colors=['#2ca02c', '#d62728'], startangle=140)
ax.set_title(f'이미지 Alt 텍스트 현황 (총 {len(images)}개)')

# 이미지 크기 분포
ax = axes[1]
sizes = images['Size (bytes)'].astype(float).dropna()
sizes_kb = sizes / 1024
sns.histplot(sizes_kb.clip(upper=1000), bins=40, ax=ax, color='#DD8452')
ax.axvline(200, color='orange', linestyle='--', label='권장 최대 (200KB)')
ax.axvline(500, color='red', linestyle='--', label='위험 (500KB)')
ax.set_xlabel('이미지 크기 (KB)')
ax.set_title('이미지 파일 크기 분포')
ax.legend()

# 형식별 분포
ax = axes[2]
images['extension'] = images['Address'].str.extract(r'\.(\w{3,4})(?:\?|$)', expand=False).str.lower()
ext_counts = images['extension'].value_counts().head(8)
ax.barh(ext_counts.index, ext_counts.values, color='#55A868')
ax.set_xlabel('이미지 수')
ax.set_title('이미지 형식별 분포')
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('image_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# 큰 이미지 TOP 20
large_imgs = images.nlargest(20, 'Size (bytes)')
large_imgs['Size (KB)'] = (large_imgs['Size (bytes)'].astype(float) / 1024).round(1)
print("\n=== 큰 이미지 TOP 20 ===")
print(large_imgs[['Address', 'Size (KB)', 'Alt Text', 'Source Page']].to_string(index=False))
```

---

## 13. redirects.csv — 리다이렉트 분석

### 정상/이상 기준

| 항목 | 정상 | 문제 |
|------|------|------|
| Redirect Type | `301` (영구 리다이렉트) | `302` (임시 — 영구이면 301으로 변경) |
| Chain Length | 1 (직접 리다이렉트) | **2~3** (체인 — 성능 저하), **>3** (과도 — 심각) |
| Redirect Status | 빈 값 (단일 리다이렉트) | `Redirect Chain` (다중 홉), `Redirect Loop` (무한 루프 — 즉시 수정) |
| Final URL | 내부 페이지 | 외부 도메인 (의도하지 않은 경우 문제) |

> **v2 신규 컬럼**: `Status Code` (원본 응답 코드), `Redirect Status` (빈값/Redirect Chain/Redirect Loop)

### Python EDA

```python
redirects = data.get('redirects', pd.DataFrame())

if len(redirects) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 리다이렉트 유형 분포
    ax = axes[0]
    type_counts = redirects['Redirect Type'].value_counts()
    colors_redir = {'301': '#2ca02c', '302': '#ff7f0e', '307': '#d62728'}
    ax.bar(type_counts.index.astype(str), type_counts.values,
           color=[colors_redir.get(str(x), '#999') for x in type_counts.index])
    ax.set_title('리다이렉트 유형 분포')
    ax.set_ylabel('페이지 수')

    # 체인 길이 분포
    ax = axes[1]
    chain_counts = redirects['Chain Length'].value_counts().sort_index()
    colors_chain = ['#2ca02c' if x == 1 else '#ff7f0e' if x <= 3 else '#d62728' for x in chain_counts.index]
    ax.bar(chain_counts.index.astype(str), chain_counts.values, color=colors_chain)
    ax.set_title('리다이렉트 체인 길이 (3 이상 = 빨간색)')
    ax.set_xlabel('체인 길이 (홉)')
    ax.set_ylabel('페이지 수')

    plt.tight_layout()
    plt.savefig('redirect_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()

    # 긴 리다이렉트 체인
    long_chains = redirects[redirects['Chain Length'] >= 3]
    print(f"\n=== 리다이렉트 체인 3홉 이상: {len(long_chains)}개 ===")
    print(long_chains[['Source URL', 'Redirect Type', 'Chain Length', 'Final URL']].to_string(index=False))
```

---

## 14. issues.csv — SEO 이슈 분석

### Severity 수준

| Severity | 의미 | 우선순위 |
|----------|------|---------|
| `Critical` | 색인/크롤링 차단, 심각한 기술적 문제 | 즉시 해결 |
| `Warning` | SEO 성능에 부정적 영향 | 빠른 시일 내 해결 |
| `Info` | 개선 권고사항 | 여유 있을 때 해결 |

### Python EDA

```python
issues = data['issues']

# ============================================================
# 1. Severity별 / Category별 이슈 수
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Severity
ax = axes[0]
sev_counts = issues['Severity'].value_counts()
sev_order = ['Critical', 'Warning', 'Info']
sev_counts = sev_counts.reindex(sev_order).dropna()
colors_sev = ['#d62728', '#ff7f0e', '#1f77b4']
ax.barh(sev_counts.index, sev_counts.values, color=colors_sev[:len(sev_counts)])
ax.set_xlabel('이슈 수')
ax.set_title('Severity별 이슈 수')
for i, v in enumerate(sev_counts.values):
    ax.text(v + 0.5, i, str(v), va='center')

# Category
ax = axes[1]
cat_counts = issues['Category'].value_counts().head(10)
ax.barh(cat_counts.index, cat_counts.values, color='#4C72B0')
ax.set_xlabel('이슈 수')
ax.set_title('Category별 이슈 수 (TOP 10)')
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('issues_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# 2. Issue Type별 상세
# ============================================================
fig, ax = plt.subplots(figsize=(12, 8))
type_sev = issues.groupby(['Issue Type', 'Severity']).size().unstack(fill_value=0)
type_sev = type_sev.reindex(columns=['Critical', 'Warning', 'Info'])
type_sev['total'] = type_sev.sum(axis=1)
type_sev = type_sev.sort_values('total', ascending=True).tail(20)
type_sev.drop('total', axis=1).plot(kind='barh', stacked=True, ax=ax,
    color=['#d62728', '#ff7f0e', '#1f77b4'])
ax.set_xlabel('이슈 수')
ax.set_title('Issue Type별 이슈 (Severity 스택)')
ax.legend(title='Severity')
plt.savefig('issue_types_stacked.png', dpi=150, bbox_inches='tight')
plt.show()

# Critical 이슈 목록
critical = issues[issues['Severity'] == 'Critical']
print(f"\n=== Critical 이슈: {len(critical)}개 ===")
print(critical[['URL', 'Issue Type', 'Description', 'Recommendation']].to_string(index=False))
```

---

## 15. 외부 링크 및 인링크 분석

### external_all.csv

| 컬럼 | 의미 | 주의사항 |
|------|------|---------|
| `Address` | 외부 URL | - |
| `Inlinks` | 이 외부 URL을 가리키는 내부 페이지 수 | 높을수록 중요한 외부 사이트 |

### inlinks.csv

| 컬럼 | 의미 | 주의사항 |
|------|------|---------|
| `Target URL` | 인링크를 받는 URL | - |
| `Inlink Count` | 인링크 총 수 | 많을수록 사이트 내 중요도 높음 |

### Python EDA

```python
inlinks = data['inlinks']

# 인링크 분포 (로그 스케일)
fig, ax = plt.subplots(figsize=(12, 5))
il = inlinks['Inlink Count'].astype(int).sort_values(ascending=False)
ax.bar(range(min(50, len(il))), il.head(50).values, color='#4C72B0')
ax.set_xlabel('페이지 순위')
ax.set_ylabel('인링크 수')
ax.set_title('인링크 수 TOP 50 페이지')
plt.savefig('inlinks_top50.png', dpi=150, bbox_inches='tight')
plt.show()

# 인링크 TOP 20
print("=== 가장 많은 인링크를 받는 페이지 TOP 20 ===")
print(inlinks.nlargest(20, 'Inlink Count')[['Target URL', 'Inlink Count']].to_string(index=False))
```

---

## 16. structured_data_all.csv — 구조화 데이터 분석

### 정상/이상 기준

| 항목 | 정상 | 문제 |
|------|------|------|
| Errors | 0 | >0 (구조화 데이터 오류 — Google에서 무시될 수 있음) |
| Warnings | 0 | >0 (개선 권고) |
| Type-1 | Product, Article, FAQ 등 적절한 타입 | 빈 값 또는 비관련 타입 |

### Python EDA

```python
sd = data.get('structured_data_all', pd.DataFrame())

if len(sd) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 스키마 타입 분포
    ax = axes[0]
    type_counts = sd['Type-1'].value_counts().head(10)
    ax.barh(type_counts.index, type_counts.values, color='#55A868')
    ax.set_title('Schema.org 타입 분포')
    ax.invert_yaxis()

    # 오류/경고 현황
    ax = axes[1]
    has_errors = (sd['Errors'].astype(int) > 0).sum()
    has_warnings = (sd['Warnings'].astype(int) > 0).sum()
    valid = len(sd) - has_errors
    ax.bar(['Valid', 'Errors', 'Warnings'],
           [valid, has_errors, has_warnings],
           color=['#2ca02c', '#d62728', '#ff7f0e'])
    ax.set_title('구조화 데이터 유효성')
    ax.set_ylabel('페이지 수')

    plt.tight_layout()
    plt.savefig('structured_data_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
```

---

## 17. hreflang_all.csv — 다국어 분석

### 정상/이상 기준

| 항목 | 정상 | 문제 |
|------|------|------|
| hreflang 설정 | 모든 언어 버전 페이지에 상호 참조 | 반환 태그(return tag) 누락 |
| Occurrences | 언어 버전 수와 일치 | 불일치 (일부 누락) |

---

## 18. 기타 CSV 분석

### url_all.csv

| 컬럼 | 정상 | 문제 |
|------|------|------|
| `Length` | **< 100자** | >100자 (긴 URL — SEO 부정적), >200자 (매우 긺) |
| `Hash` | 고유 | 다른 URL과 동일 (중복 콘텐츠) |

### pagination_all.csv

| 확인 사항 | 정상 | 문제 |
|-----------|------|------|
| rel=next/prev 체인 | 완전한 순방향/역방향 체인 | 끊어진 체인 (prev 없이 next만 있거나 반대) |
| canonical과 관계 | 각 페이지가 self-canonical | 모든 페이지네이션이 첫 페이지를 canonical로 지정 (비권장) |

### meta_keywords_all.csv

Google은 meta keywords를 무시하지만, 키워드 스터핑 감지에 활용할 수 있습니다.

| 항목 | 정상 | 문제 |
|------|------|------|
| `Meta Keywords 1 Length` | 0 (미사용) 또는 < 100자 | > 200자 (키워드 스터핑 의심) |

---

## 19. crawl_warnings.csv — 크롤 경고

> **v2 신규 파일**. 크롤 중 발생한 경고(robots.txt 차단, 타임아웃, 비정상 응답 등)를 기록합니다.

### 컬럼 설명

| 컬럼 | 의미 | 예시 |
|------|------|------|
| `timestamp` | 경고 발생 시각 (ISO 8601) | `2024-01-15T14:30:00` |
| `warning_type` | 경고 분류 | `crawl_warning` |
| `message` | 경고 상세 내용 | `Robots.txt blocked URL` |
| `affected_url` | 관련 URL | `https://example.com/blocked` |

### Python EDA

```python
warnings = data.get('crawl_warnings', pd.DataFrame())
if len(warnings) > 0:
    print(f"총 크롤 경고: {len(warnings)}건")
    print(warnings['warning_type'].value_counts())
```

---

## 20. statistics_summary.csv / JSON — 통계 요약

> **v2 신규 파일**. 크롤 전체의 31개 핵심 지표를 표준화된 형식으로 제공합니다. CSV와 JSON 두 형식으로 동시 생성됩니다.

### 컬럼 설명

| 컬럼 | 의미 | 예시 |
|------|------|------|
| `metric_name` | 지표명 | `Total URLs Crawled` |
| `metric_value` | 수치 값 | `1500` |
| `counting_unit` | 집계 단위 | `page` / `url` / `occurrence` / `asset` / `second` |
| `denominator_if_any` | 비율 분모 (해당 시) | `Total URLs Crawled` |
| `scope` | 지표 범위 | `crawl` |
| `source_tables` | 산출 근거 CSV | `internal_all.csv` |
| `notes` | 추가 설명 | |

### 주요 지표 (31개)

카테고리별 지표: Total URLs Crawled, Total Internal URLs, Total External URLs, Total Redirects, Total Client Errors (4xx), Total Server Errors (5xx), Total Images (occurrence), Unique Image Assets, Images Missing Alt Attribute, Images Missing Alt Text, Images with Alt Over 100, Pages with Title, Pages with Missing Title, Pages with Duplicate Title, Pages with Title Over 60, Pages with Title Below 30, Pages with Meta Description, Pages with Missing Meta Description, Pages with Duplicate Meta Description, Pages with Meta Description Over 160, Pages with Meta Description Below 70, Pages with H1, Pages with Missing H1, Pages with Multiple H1, Canonical Self-Referencing, Canonical Missing, Canonical to Redirect, Canonical to Non-200, Average Response Time, Total Indexable, Total Non-Indexable

### Python EDA

```python
stats = data.get('statistics_summary', pd.DataFrame())
if len(stats) > 0:
    print("=== 크롤 통계 요약 ===")
    for _, row in stats.iterrows():
        print(f"  {row['metric_name']}: {row['metric_value']} ({row['counting_unit']})")

    # JSON 버전 로드 (더 유연한 처리)
    import json
    with open('crawl_output/example/statistics_summary.json', encoding='utf-8') as f:
        stats_json = json.load(f)
```

---

## 21. run_manifest.json / run_summary.json — 실행 메타데이터

> **v2 신규 파일**. 크롤 실행의 메타 정보와 요약 통계를 JSON으로 제공합니다.

### run_manifest.json 필드

| 필드 | 의미 |
|------|------|
| `start_url` | 크롤 시작 URL |
| `domain` | 대상 도메인 |
| `crawl_start_time` / `crawl_end_time` | 크롤 시작/종료 시각 |
| `total_urls_crawled` | 총 크롤 URL 수 |
| `total_internal` / `total_external` | 내부/외부 URL 수 |
| `output_files` | 생성된 파일 목록 |
| `config_summary` | 크롤러 설정 요약 |

### run_summary.json 필드

| 필드 | 의미 |
|------|------|
| `domain` | 도메인 |
| `total_pages` | 총 페이지 수 |
| `status_code_distribution` | 상태 코드별 분포 (객체) |
| `top_issues` | 주요 이슈 TOP 10 (객체) |
| `crawl_duration_seconds` | 크롤 소요 시간 (초) |
| `pages_per_second` | 초당 크롤 속도 |

### Python 활용

```python
import json

with open('crawl_output/example/run_manifest.json', encoding='utf-8') as f:
    manifest = json.load(f)
print(f"크롤 대상: {manifest['domain']}, 생성 파일: {len(manifest['output_files'])}개")

with open('crawl_output/example/run_summary.json', encoding='utf-8') as f:
    summary = json.load(f)
print(f"크롤 속도: {summary['pages_per_second']:.1f} pages/sec")
print(f"상태 코드 분포: {summary['status_code_distribution']}")
```

---

## 22. 크로스 파일 종합 분석

### 종합 SEO 점수 계산

```python
def calculate_seo_scores(data: dict) -> pd.DataFrame:
    """각 페이지의 SEO 점수를 0~100으로 계산"""
    internal = data['internal_all']
    scores = pd.DataFrame({'Address': internal['Address']})

    # 1. 기술 점수 (30점 만점)
    scores['tech_score'] = 0
    scores.loc[internal['Status Code'] == 200, 'tech_score'] += 10
    scores.loc[internal['Indexability'] == 'Indexable', 'tech_score'] += 10
    scores.loc[internal['Response Time'].astype(float) < 0.5, 'tech_score'] += 5
    scores.loc[internal['Response Time'].astype(float) < 1.0, 'tech_score'] += 5

    # 2. 온페이지 점수 (40점 만점)
    scores['onpage_score'] = 0
    # 타이틀
    tl = internal['Title 1 Length']
    scores.loc[tl.between(30, 60), 'onpage_score'] += 8
    scores.loc[(tl > 0) & (~tl.between(30, 60)), 'onpage_score'] += 3
    # 메타 설명
    dl = internal['Meta Description 1 Length']
    scores.loc[dl.between(70, 160), 'onpage_score'] += 8
    scores.loc[(dl > 0) & (~dl.between(70, 160)), 'onpage_score'] += 3
    # H1
    h1_len = internal['H1-1 Length']
    scores.loc[h1_len > 0, 'onpage_score'] += 6
    # 콘텐츠
    wc = internal['Word Count']
    scores.loc[wc >= 300, 'onpage_score'] += 8
    scores.loc[(wc > 0) & (wc < 300), 'onpage_score'] += 3
    # 캐노니컬
    scores.loc[internal['Canonical Link Element 1'].notna() & (internal['Canonical Link Element 1'] != ''), 'onpage_score'] += 5
    # 텍스트 비율
    scores.loc[internal['Text Ratio'].astype(float) > 10, 'onpage_score'] += 5

    # 3. 링크 점수 (30점 만점)
    scores['link_score_raw'] = 0
    inlinks = internal['Inlinks'].astype(int)
    scores.loc[inlinks > 0, 'link_score_raw'] += 10
    scores.loc[inlinks > 5, 'link_score_raw'] += 5
    depth = internal['Crawl Depth'].astype(int)
    scores.loc[depth <= 3, 'link_score_raw'] += 10
    scores.loc[(depth > 3) & (depth <= 5), 'link_score_raw'] += 5
    ls = internal['Link Score'].astype(float)
    scores.loc[ls > 10, 'link_score_raw'] += 5

    # 종합
    scores['total_score'] = scores['tech_score'] + scores['onpage_score'] + scores['link_score_raw']

    return scores

scores = calculate_seo_scores(data)

# 점수 분포 시각화
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for ax, col, title, color in zip(
    axes.flat,
    ['total_score', 'tech_score', 'onpage_score', 'link_score_raw'],
    ['종합 SEO 점수 (0~100)', '기술 점수 (0~30)', '온페이지 점수 (0~40)', '링크 점수 (0~30)'],
    ['#4C72B0', '#55A868', '#DD8452', '#C44E52'],
):
    sns.histplot(scores[col], bins=20, kde=True, ax=ax, color=color)
    ax.axvline(scores[col].mean(), color='red', linestyle='--',
               label=f'평균: {scores[col].mean():.1f}')
    ax.set_title(title)
    ax.legend()

plt.tight_layout()
plt.savefig('seo_scores_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

# 점수 낮은 페이지 TOP 20
print("\n=== SEO 점수 하위 20 페이지 ===")
print(scores.nsmallest(20, 'total_score').to_string(index=False))
```

### 상관관계 히트맵

```python
# 주요 수치 컬럼 상관관계
internal = data['internal_all']
numeric_cols = [
    'Status Code', 'Title 1 Length', 'Meta Description 1 Length',
    'H1-1 Length', 'Word Count', 'Sentence Count', 'Flesch Reading Ease Score',
    'Text Ratio', 'Crawl Depth', 'Link Score', 'Inlinks', 'Outlinks',
    'Response Time',
]
corr_data = internal[numeric_cols].apply(pd.to_numeric, errors='coerce')
corr_matrix = corr_data.corr()

fig, ax = plt.subplots(figsize=(14, 11))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f',
            cmap='RdBu_r', center=0, ax=ax, vmin=-1, vmax=1,
            square=True, linewidths=0.5)
ax.set_title('SEO 메트릭 상관관계 히트맵', size=14, pad=15)
plt.savefig('correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## 23. Looker Studio 대시보드 구축 가이드

### 데이터 소스 연결

1. Google Sheets에 CSV 업로드 (또는 BigQuery)
2. Looker Studio에서 "데이터 소스 추가" → Google Sheets 선택
3. 각 CSV를 별도 데이터 소스로 추가
4. `Address` 컬럼으로 데이터 소스 간 블렌딩(Blending) 설정

### 추천 대시보드 페이지 구성

#### 페이지 1: 사이트 건강도 개요

| 차트 | 데이터 소스 | 차원(Dimension) | 측정항목(Metric) | 차트 유형 |
|------|-----------|----------------|-----------------|----------|
| 총 URL KPI 카드 | `internal_all` | - | `Record Count` | 스코어카드 |
| 색인 가능 비율 | `internal_all` | - | `COUNT_D(CASE WHEN Indexability="Indexable" THEN Address END) / Record Count` | 스코어카드 (%) |
| 평균 응답 시간 | `internal_all` | - | `AVG(Response Time)` | 스코어카드 |
| 상태 코드 분포 | `response_codes_all` | 수식 필드: `LEFT(CAST(Status Code AS TEXT), 1) & "xx"` | `Record Count` | 도넛 차트 |
| Issue Severity 분포 | `issues` | `Severity` | `Record Count` | 가로 막대 |
| Issue Type TOP 15 | `issues` | `Issue Type` | `Record Count` | 가로 막대 (정렬: 내림차순) |

#### 페이지 2: 온페이지 SEO

| 차트 | 데이터 소스 | 설정 | 차트 유형 |
|------|-----------|------|----------|
| 타이틀 길이 분포 | `internal_all` | 차원: 구간 필드 (10자 단위), 측정: Count | 막대 그래프 |
| 메타 설명 길이 분포 | `internal_all` | 차원: 구간 필드 (10자 단위), 측정: Count | 막대 그래프 |
| H1 현황 요약 | `h1_all` | 차원: 수식 `CASE WHEN Occurrences=0 THEN "누락" WHEN Occurrences=1 THEN "정상" ELSE "복수" END` | 파이 차트 |
| 중복 타이틀 표 | `page_titles_duplicate` | 차원: Title 1, Occurrences, Address | 표 |

#### 페이지 3: 콘텐츠 품질

| 차트 | 데이터 소스 | 설정 | 차트 유형 |
|------|-----------|------|----------|
| Word Count 분포 | `content_all` | 구간 필드 (100 단위) | 막대 그래프 |
| Readability 등급 | `content_all` | 차원: Readability | 파이 차트 |
| Flesch Score vs Word Count | `content_all` | X: Word Count, Y: Flesch Score | 산점도 |
| Thin Content 표 | `content_all` (필터: Word Count < 200) | Address, Word Count, Readability | 표 |

#### 페이지 4: 사이트 구조 · 링크

| 차트 | 데이터 소스 | 설정 | 차트 유형 |
|------|-----------|------|----------|
| 크롤 깊이 분포 | `links_all` | 차원: Crawl Depth | 막대 그래프 |
| Link Score 분포 | `links_all` | 구간 필드 (10 단위) | 막대 그래프 |
| 고아 페이지 표 | `links_all` (필터: Inlinks = 0) | Address, Outlinks | 표 |
| Inlinks TOP 20 표 | `inlinks` (정렬: 내림차순, 행 제한 20) | Target URL, Inlink Count | 표 |

#### 페이지 5: 기술적 SEO

| 차트 | 데이터 소스 | 설정 | 차트 유형 |
|------|-----------|------|----------|
| 보안 헤더 적용률 | `security_all` | 각 헤더 컬럼에 대해 `COUNTIF(!='')/COUNT` | 막대 그래프 |
| 캐노니컬 상태 | `canonicals_all` | 수식 필드로 상태 분류 | 파이 차트 |
| 리다이렉트 유형 | `redirects` | 차원: Redirect Type | 파이 차트 |
| 체인 길이 분포 | `redirects` | 차원: Chain Length | 막대 그래프 |

### Looker Studio 수식 필드 예시

```
# 상태 코드 그룹
CASE
  WHEN Status Code >= 200 AND Status Code < 300 THEN "2xx Success"
  WHEN Status Code >= 300 AND Status Code < 400 THEN "3xx Redirect"
  WHEN Status Code >= 400 AND Status Code < 500 THEN "4xx Client Error"
  WHEN Status Code >= 500 THEN "5xx Server Error"
  ELSE "Other"
END

# 타이틀 상태 분류
CASE
  WHEN Title 1 IS NULL OR Title 1 = "" THEN "누락"
  WHEN Title 1 Length < 30 THEN "너무 짧음"
  WHEN Title 1 Length > 60 THEN "너무 긺"
  ELSE "최적"
END

# 응답 시간 등급
CASE
  WHEN Response Time < 0.5 THEN "Fast"
  WHEN Response Time < 1.0 THEN "Moderate"
  WHEN Response Time < 3.0 THEN "Slow"
  ELSE "Very Slow"
END
```

---

## 24. Tableau 대시보드 구축 가이드

### 데이터 연결

1. Tableau Desktop에서 "텍스트 파일"로 CSV 연결
2. 여러 CSV를 `Address` 컬럼으로 관계(Relationship) 설정
3. 또는 Union으로 결합

### 추천 대시보드 구성

#### 시트 1: Site Health Scorecard

```
Columns: [Measure Names]
Rows: [Measure Values]
Measures:
  - COUNTD([Address]) → "총 URL"
  - SUM(IF [Indexability]="Indexable" THEN 1 ELSE 0 END) / COUNTD([Address]) → "색인 비율"
  - AVG([Response Time]) → "평균 응답시간"
  - COUNTD(IF [Status Code] >= 400 THEN [Address] END) → "오류 페이지"
```

#### 시트 2: 상태 코드 분포 (TreeMap)

```
Mark Type: Square
Color: [Status Group] (Calculated Field: LEFT(STR([Status Code]), 1) + "xx")
Size: COUNTD([Address])
Label: [Status Code], COUNTD([Address])
```

#### 시트 3: 타이틀 · 메타 길이 분포 (Histogram)

```
Columns: BIN([Title 1 Length], 5)   -- 5자 단위 구간
Rows: COUNTD([Address])
Reference Line: 30 (최소), 60 (최대)  -- 최적 범위
Color: IF [Title 1 Length] >= 30 AND [Title 1 Length] <= 60 THEN "최적" ELSE "범위 밖" END
```

#### 시트 4: 콘텐츠 품질 산점도

```
Columns: [Word Count]
Rows: [Flesch Reading Ease Score]
Color: [Readability]
Size: [Text Ratio]
Detail: [Address]
Reference Line (Y축): 60 (최적 하한)
Reference Line (X축): 300 (최소 단어)
```

#### 시트 5: 링크 구조 버블 차트

```
Columns: [Inlinks]
Rows: [Link Score]
Size: [Outlinks]
Color: [Crawl Depth]
Detail: [Address]
```

#### 시트 6: 응답 시간 히트맵

```
Columns: [Crawl Depth]
Rows: [Status Code Group]
Color: AVG([Response Time])
Color Palette: Red-Green Diverging (reversed)
```

### Tableau 계산 필드 예시

```
// 상태 코드 그룹
[Status Group] = LEFT(STR([Status Code]), 1) + "xx"

// 타이틀 상태
[Title Status] =
  IF ISNULL([Title 1]) OR [Title 1] = "" THEN "누락"
  ELSEIF [Title 1 Length] < 30 THEN "너무 짧음"
  ELSEIF [Title 1 Length] > 60 THEN "너무 긺"
  ELSE "최적"
  END

// Thin Content 여부
[Is Thin Content] = [Word Count] < 200

// 고아 페이지 여부
[Is Orphan Page] = [Inlinks] = 0

// 응답 시간 등급
[Speed Grade] =
  IF [Response Time] < 0.5 THEN "Fast"
  ELSEIF [Response Time] < 1.0 THEN "Moderate"
  ELSEIF [Response Time] < 3.0 THEN "Slow"
  ELSE "Very Slow"
  END

// SEO 간이 점수
[SEO Quick Score] =
  (IF [Status Code] = 200 THEN 20 ELSE 0 END) +
  (IF [Title 1 Length] BETWEEN 30 AND 60 THEN 15 ELSE IF [Title 1 Length] > 0 THEN 5 ELSE 0 END END) +
  (IF [Meta Description 1 Length] BETWEEN 70 AND 160 THEN 15 ELSE IF [Meta Description 1 Length] > 0 THEN 5 ELSE 0 END END) +
  (IF [H1-1 Length] > 0 THEN 10 ELSE 0 END) +
  (IF [Word Count] >= 300 THEN 15 ELSE IF [Word Count] > 0 THEN 5 ELSE 0 END END) +
  (IF [Inlinks] > 0 THEN 10 ELSE 0 END) +
  (IF [Response Time] < 0.5 THEN 10 ELSE IF [Response Time] < 1.0 THEN 5 ELSE 0 END END) +
  (IF [Crawl Depth] <= 3 THEN 5 ELSE 0 END)
```

### Tableau 대시보드 레이아웃 예시

```
┌──────────────────────────────────────────────────────────┐
│  [KPI 카드]  총URL | 색인비율 | 평균응답 | 오류수 | 이슈수    │
├──────────────────────┬───────────────────────────────────┤
│  상태 코드 분포       │  Issue Type TOP 15                │
│  (도넛/트리맵)        │  (가로 막대)                       │
├──────────────────────┼───────────────────────────────────┤
│  타이틀 길이 분포     │  콘텐츠 양 vs 가독성 산점도         │
│  (히스토그램)         │                                    │
├──────────────────────┼───────────────────────────────────┤
│  크롤 깊이 분포       │  Link Score vs Inlinks            │
│  (막대 그래프)        │  (버블 차트)                       │
└──────────────────────┴───────────────────────────────────┘
```

---

*이 문서는 Python SEO Spider v2의 23개 CSV + 3개 JSON 출력을 기반으로 작성되었습니다. 각 분석 코드는 `crawl_output/{도메인}/` 폴더의 파일을 대상으로 합니다.*
