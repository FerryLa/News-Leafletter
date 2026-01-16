# Issue #61: Sector-Theme-Event 3단 분류 체계 구축 완료

> **마일스톤 4 - Day 0**: 머신러닝 전 산업 섹터 분류 체계 정립

---

## 개요 (Overview)

본 이슈는 **머신러닝 기반 뉴스·데이터 분류를 위해 산업(Sector)–테마(Theme)–사건(Event) 3단 구조의 표준 분류 체계를 정의**하는 것을 목표로 했습니다.

기존의 단순 섹터 분류(5대 섹터 + 41개 하위 카테고리)는 산업 간 경계 붕괴, 테마 중심 투자 확산, 사건 기반 분석 증가로 인해 한계를 보였습니다. 이를 개선하기 위해 **GICS(Global Industry Classification Standard)를 기반으로 한 현대적 분류 체계**를 도입했습니다.

---

## 완료 항목 (Completed Tasks)

### ✅ 1. 산업(Sector) 11개 Select 옵션 DB 반영

**데이터베이스 테이블:**
```sql
CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    sector_code TEXT UNIQUE NOT NULL,
    sector_name TEXT NOT NULL,
    sector_name_en TEXT NOT NULL,
    description TEXT
);
```

**GICS 기반 11개 섹터:**
1. 에너지 (ENERGY)
2. 소재 (MATERIALS)
3. 산업재 (INDUSTRIALS)
4. IT (IT)
5. 커뮤니케이션 (COMMUNICATION)
6. 금융 (FINANCIALS)
7. 헬스케어 (HEALTHCARE)
8. 소비재 (CONSUMER)
9. 유틸리티 (UTILITIES)
10. 부동산 (REAL_ESTATE)
11. 정책·공공 (PUBLIC_POLICY)

**특징:**
- 고정 분류 (확장성 최소, 안정성 우선)
- 기사당 1개의 섹터만 할당 (Single-label)
- GICS 표준을 따라 국제적 호환성 확보

---

### ✅ 2. 테마(Theme) Multi-select DB 생성

**데이터베이스 테이블:**
```sql
CREATE TABLE themes (
    id INTEGER PRIMARY KEY,
    theme_code TEXT UNIQUE NOT NULL,
    theme_name TEXT NOT NULL,
    theme_name_en TEXT NOT NULL,
    description TEXT,
    keywords TEXT,  -- JSON 배열
    is_active BOOLEAN DEFAULT 1
);
```

**초기 10개 테마:**
1. 반도체 (SEMICONDUCTOR)
2. 2차전지 (BATTERY)
3. AI (AI)
4. 자율운항 (AUTONOMOUS)
5. 로봇 (ROBOTICS)
6. 친환경 (GREEN)
7. LNG (LNG)
8. 콘텐츠 (CONTENT)
9. 플랫폼 (PLATFORM)
10. 방산 (DEFENSE)

**특징:**
- 유동 분류 (신규 테마 추가 용이)
- 기사당 여러 테마 할당 가능 (Multi-label)
- `is_active` 플래그로 테마 활성화/비활성화 관리

---

### ✅ 3. 사건(Event) 전용 DB 및 Relation 연결

**데이터베이스 테이블:**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_code TEXT UNIQUE NOT NULL,
    event_name TEXT NOT NULL,
    event_name_en TEXT,
    description TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT 1
);
```

**샘플 이벤트 3개:**
1. HMM 인수전 (HMM_ACQUISITION)
2. HD현대-자율운항 협력 (HD_HYUNDAI_AUTONOMOUS)
3. 포스코 구조조정 (POSCO_RESTRUCTURE)

**특징:**
- 개별 이슈 단위로 관리
- 시작일/종료일 추적 (시간적 맥락 보존)
- 기사당 여러 이벤트 연결 가능 (N:M Relation)

---

### ✅ 4. Junction Tables (연결 테이블) 구현

#### Article-Sector (1:1 관계)
```sql
CREATE TABLE article_sectors (
    article_id INTEGER,
    sector_id INTEGER,
    confidence REAL DEFAULT 1.0,
    UNIQUE(article_id)  -- 기사당 1개 섹터만
);
```

#### Article-Themes (N:M 관계)
```sql
CREATE TABLE article_themes (
    article_id INTEGER,
    theme_id INTEGER,
    confidence REAL DEFAULT 1.0,
    UNIQUE(article_id, theme_id)
);
```

#### Article-Events (N:M 관계)
```sql
CREATE TABLE article_events (
    article_id INTEGER,
    event_id INTEGER,
    relevance_score REAL DEFAULT 1.0,
    UNIQUE(article_id, event_id)
);
```

---

### ✅ 5. 샘플 뉴스 10건에 신규 분류 체계 적용

**테스트 결과:**
```
[샘플 뉴스 분류 통계]

[Sector Distribution]
  에너지: 2 articles
  커뮤니케이션: 1 articles
  정책·공공: 1 articles
  금융: 1 articles
  소재: 1 articles
  IT: 1 articles

[Theme Distribution]
  반도체: 2 articles
  AI: 2 articles
  2차전지: 2 articles
  콘텐츠: 1 articles
  친환경: 1 articles
  자율운항: 1 articles
  로봇: 1 articles

[Event Distribution]
  포스코 구조조정: 1 articles
  HMM 인수전: 1 articles
  HD현대-자율운항 협력: 1 articles
```

**성공적으로 분류된 예시:**
1. "삼성전자 3나노 AI 반도체" → Sector: IT, Themes: [반도체, AI]
2. "LG에너지솔루션 배터리 공장" → Sector: 에너지, Themes: [2차전지]
3. "HD현대 자율운항 선박" → Sector: None, Themes: [자율운항], Events: [HD현대-자율운항 협력]
4. "HMM 인수전 치열" → Events: [HMM 인수전]

---

### ✅ 6. 머신러닝 학습용 라벨 구조 문서화

**문서 위치:** `docs/ML_LABEL_STRUCTURE.md`

**주요 내용:**
- Sector: Single-label Classification (11 classes)
- Theme: Multi-label Classification (10+ classes, expandable)
- Event: Named Entity Recognition (NER) or Relation Extraction
- 학습 데이터 추출 쿼리
- 라벨 인코딩 방법
- 모델 학습 파이프라인 예시
- 라벨 품질 관리 가이드

---

### ✅ 7. 뉴스레터 Issue 템플릿에 분류 항목 반영

**문서 위치:** `docs/NEWSLETTER_TEMPLATE.md`

**템플릿 구조:**
```markdown
## 분류 (Classification)

### 산업 (Sector) - 1개만 선택
- [ ] 에너지 (ENERGY)
- [ ] 소재 (MATERIALS)
- [x] IT (IT)
...

### 테마 (Themes) - 다중 선택 가능
- [x] 반도체 (SEMICONDUCTOR)
- [x] AI (AI)
...

### 사건 (Events) - 해당되는 경우만
- [ ] HMM 인수전 (HMM_ACQUISITION)
...
```

---

## 구현 파일 (Implementation Files)

### 1. 마이그레이션 스크립트
- **파일:** `scripts/migrate_sector_structure.py`
- **기능:**
  - 새로운 sectors, themes, events 테이블 생성
  - Junction tables (article_sectors, article_themes, article_events) 생성
  - GICS 기반 11개 섹터 삽입
  - 초기 10개 테마 삽입
  - 샘플 이벤트 3개 삽입
  - 기존 데이터 마이그레이션

### 2. 분류 정의 모듈
- **파일:** `app/classification/gics_sector_definitions.py`
- **기능:**
  - GICS 기반 11개 섹터 정의 (키워드 포함)
  - 10개 테마 정의 (키워드 포함)
  - 샘플 이벤트 정의
  - 키워드 기반 자동 분류 함수
  - 유틸리티 함수 (조회, 검색 등)

### 3. 테스트 스크립트
- **파일:** `scripts/test_new_classification.py`
- **기능:**
  - 10개 샘플 뉴스에 자동 분류 적용
  - DB에 저장
  - 분류 통계 출력

### 4. 문서
- **파일:** `docs/ML_LABEL_STRUCTURE.md`
  - 머신러닝 학습용 라벨 구조 설명
- **파일:** `docs/NEWSLETTER_TEMPLATE.md`
  - 뉴스레터 작성 템플릿

---

## 개선 사항 (Improvements)

| 항목 | 기존 (5-Sector) | 개선 (Sector-Theme-Event) |
|------|-----------------|---------------------------|
| **산업 분류** | 5개 (모호한 경계) | 11개 (GICS 기반 명확) |
| **테마 관리** | 41개 하위 카테고리 혼재 | 10개 독립 테마, 확장 가능 |
| **사건 추적** | 없음 | 별도 Events 테이블로 관리 |
| **ML 학습** | 라벨 의미 모호 | Single/Multi-label 명확 |
| **확장성** | 카테고리 폭증 위험 | 역할별 분리로 안정적 |
| **시간 추적** | 불가능 | 이벤트 시작/종료일 기록 |

---

## 기대 효과 (Expected Impact)

### 1. 머신러닝 분류 정확도 향상
- 산업 vs 테마 vs 사건의 역할 분리
- 각 차원별 독립적 학습 가능
- Single-label (Sector) + Multi-label (Theme) 조합

### 2. 뉴스레터 콘텐츠 구조화
- 동일 사건의 흐름 추적 가능 (Event 테이블)
- 테마별 트렌드 분석 용이
- 섹터별 비중 조절 가능

### 3. 장기 데이터 자산화
- 시간이 지나도 분류 체계 붕괴 없음
- 과거 데이터를 신규 모델로 재분류 가능
- GICS 표준 준수로 국제적 호환성

### 4. 분석·필터·통계 활용성 증가
- 섹터별/테마별/이벤트별 교차 분석
- 신뢰도 점수 기반 품질 관리
- 키워드 확장 및 자동 분류 개선

---

## 다음 단계 (Next Steps)

### 마일스톤 4 - Day 1~5

1. **키워드 확장**
   - 실제 RSS 데이터 분석
   - TF-IDF 기반 자동 키워드 추출
   - 분류 정확도 개선

2. **자동 분류 시스템 통합**
   - RSS 수집 파이프라인에 분류 로직 추가
   - 신뢰도 낮은 기사 수동 라벨링 큐 구축

3. **ML 모델 실험**
   - Baseline: TF-IDF + Logistic Regression
   - Advanced: KoBERT/KoELECTRA 파인튜닝
   - 평가 지표 설정 및 벤치마크

4. **Active Learning 도입**
   - 모델 예측 신뢰도 기반 샘플링
   - 인간 피드백 반영 자동화

5. **뉴스레터 템플릿 확대**
   - GitHub Issues 템플릿 적용
   - 텔레그램 봇 응답 포맷 업데이트

---

## 실행 방법 (How to Run)

### 1. 마이그레이션 실행
```bash
python scripts/migrate_sector_structure.py
```

### 2. 샘플 분류 테스트
```bash
python scripts/test_new_classification.py
```

### 3. Python에서 사용
```python
from app.classification.gics_sector_definitions import (
    classify_sector_by_keywords,
    classify_themes_by_keywords,
    detect_events_by_keywords
)

text = "삼성전자가 최신 AI 반도체를 공개했다"

sector = classify_sector_by_keywords(text)  # "IT"
themes = classify_themes_by_keywords(text)  # ["SEMICONDUCTOR", "AI"]
events = detect_events_by_keywords(text)    # []
```

### 4. SQL로 조회
```sql
-- 섹터별 기사 수
SELECT s.sector_name, COUNT(*) as cnt
FROM article_sectors ase
JOIN sectors s ON ase.sector_id = s.id
GROUP BY s.sector_name;

-- 테마별 기사 수
SELECT t.theme_name, COUNT(*) as cnt
FROM article_themes at
JOIN themes t ON at.theme_id = t.id
GROUP BY t.theme_name;

-- 이벤트별 기사 수
SELECT e.event_name, COUNT(*) as cnt
FROM article_events ae
JOIN events e ON ae.event_id = e.id
GROUP BY e.event_name;
```

---

## 최종 요약 (Summary)

본 이슈는 **"분류를 줄이는 작업이 아니라, 역할을 나누는 작업"**입니다.

- **Sector (산업)**: 뼈대 역할 - 고정된 11개 GICS 기반 분류
- **Theme (테마)**: 방향 역할 - 확장 가능한 기술/트렌드 분류
- **Event (사건)**: 서사 역할 - 특정 시점의 개별 이슈 추적

이 구조는 머신러닝과 리서치 모두에 장기적으로 안정적인 기반을 제공합니다.

---

## 체크리스트 (Definition of Done)

- [x] 산업(Sector) Select 옵션 11개 확정 및 DB 반영
- [x] 테마(Theme) Multi-select 또는 별도 DB 생성
- [x] 사건(Event) 전용 DB 생성 및 Relation 연결
- [x] 샘플 뉴스/기사 10건 이상에 신규 분류 체계 적용
- [x] 머신러닝 학습용 라벨 구조 문서화
- [x] 뉴스레터 Issue 템플릿에 분류 항목 반영

---

**Issue Status:** ✅ COMPLETED

**Completed Date:** 2025-01-16

**Built with ❤️ by [FerryLa]**

© 2025 News-Leafletter
