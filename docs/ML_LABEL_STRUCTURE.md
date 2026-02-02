# 머신러닝 학습용 라벨 구조 (Issue #61)

> **마일스톤 4 - Day 0**: 머신러닝 전 산업 섹터 분류 체계 정립

이 문서는 News-Leafletter의 새로운 **Sector-Theme-Event 3단 분류 체계**를 머신러닝 학습에 어떻게 활용할 수 있는지 설명합니다.

---

## 1. 개요 (Overview)

기존의 5개 섹터 + 41개 하위 카테고리 구조는 **산업·테마·사건이 혼재**되어 있어 머신러닝 모델이 학습하기에 모호했습니다.

새로운 구조는 **역할을 명확히 분리**하여 모델이 각 차원을 독립적으로 학습할 수 있도록 설계되었습니다:

- **Sector (산업)**: 고정된 11개 GICS 기반 산업 분류 → **단일 라벨 (Single-label)**
- **Theme (테마)**: 확장 가능한 기술/트렌드 분류 → **다중 라벨 (Multi-label)**
- **Event (사건)**: 특정 시점의 개별 이슈 → **관계형 엔티티 (Relation)**

---

## 2. 데이터 구조

### 2.1 데이터베이스 스키마

#### Sectors (산업)
```sql
CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    sector_code TEXT UNIQUE NOT NULL,      -- 예: "IT", "ENERGY"
    sector_name TEXT NOT NULL,             -- 예: "IT", "에너지"
    sector_name_en TEXT NOT NULL,          -- 예: "Information Technology"
    description TEXT
);
```

**특징:**
- 11개 고정 섹터 (GICS 기반)
- 확장성 낮음 (안정성 우선)
- 기사당 **1개의 섹터만** 할당

#### Themes (테마)
```sql
CREATE TABLE themes (
    id INTEGER PRIMARY KEY,
    theme_code TEXT UNIQUE NOT NULL,       -- 예: "AI", "SEMICONDUCTOR"
    theme_name TEXT NOT NULL,              -- 예: "AI", "반도체"
    theme_name_en TEXT NOT NULL,
    description TEXT,
    keywords TEXT,                          -- JSON 배열
    is_active BOOLEAN DEFAULT 1
);
```

**특징:**
- 확장 가능 (신규 테마 추가 용이)
- 기사당 **여러 테마** 할당 가능
- 트렌드에 따라 테마 활성화/비활성화 가능

#### Events (사건)
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_code TEXT UNIQUE NOT NULL,       -- 예: "HMM_ACQUISITION"
    event_name TEXT NOT NULL,              -- 예: "HMM 인수전"
    event_name_en TEXT,
    description TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT 1
);
```

**특징:**
- 특정 시점의 이슈 (시작일/종료일 존재)
- 기사당 **여러 이벤트** 연결 가능
- 이벤트 종료 후 `is_active=0` 처리

#### Junction Tables (연결 테이블)
```sql
-- 기사 ↔ 섹터 (1:1)
CREATE TABLE article_sectors (
    article_id INTEGER,
    sector_id INTEGER,
    confidence REAL DEFAULT 1.0,
    UNIQUE(article_id)  -- 기사당 1개 섹터만
);

-- 기사 ↔ 테마 (N:M)
CREATE TABLE article_themes (
    article_id INTEGER,
    theme_id INTEGER,
    confidence REAL DEFAULT 1.0,
    UNIQUE(article_id, theme_id)
);

-- 기사 ↔ 이벤트 (N:M)
CREATE TABLE article_events (
    article_id INTEGER,
    event_id INTEGER,
    relevance_score REAL DEFAULT 1.0,
    UNIQUE(article_id, event_id)
);
```

---

## 3. 머신러닝 라벨 형식

### 3.1 Sector Classification (단일 라벨 분류)

**Task Type:** Multi-class Classification (11 classes)

**Input:**
```python
{
    "text": "삼성전자가 3나노 AI 반도체 양산을 시작했다...",
    "title": "삼성전자, 3나노 GAA 공정 기반 AI 반도체 양산 시작"
}
```

**Label:**
```python
{
    "sector": "IT",  # 단일 선택
    "confidence": 0.95
}
```

**Classes (11):**
```
ENERGY, MATERIALS, INDUSTRIALS, IT, COMMUNICATION,
FINANCIALS, HEALTHCARE, CONSUMER, UTILITIES,
REAL_ESTATE, PUBLIC_POLICY
```

**학습 데이터 추출 쿼리:**
```sql
SELECT
    a.id,
    a.title,
    a.summary,
    s.sector_code as label,
    ase.confidence
FROM articles a
JOIN article_sectors ase ON a.id = ase.article_id
JOIN sectors s ON ase.sector_id = s.id
WHERE ase.confidence > 0.7;
```

---

### 3.2 Theme Classification (다중 라벨 분류)

**Task Type:** Multi-label Classification (10+ themes, expandable)

**Input:**
```python
{
    "text": "삼성전자가 3나노 AI 반도체 양산을 시작했다...",
    "title": "삼성전자, 3나노 GAA 공정 기반 AI 반도체 양산 시작"
}
```

**Label:**
```python
{
    "themes": ["SEMICONDUCTOR", "AI"],  # 다중 선택
    "confidences": [0.92, 0.88]
}
```

**Classes (10+):**
```
SEMICONDUCTOR, BATTERY, AI, AUTONOMOUS, ROBOTICS,
GREEN, LNG, CONTENT, PLATFORM, DEFENSE
(신규 테마 추가 가능)
```

**학습 데이터 추출 쿼리:**
```sql
SELECT
    a.id,
    a.title,
    a.summary,
    GROUP_CONCAT(t.theme_code) as labels,
    GROUP_CONCAT(at.confidence) as confidences
FROM articles a
JOIN article_themes at ON a.id = at.article_id
JOIN themes t ON at.theme_id = t.id
WHERE at.confidence > 0.7
GROUP BY a.id;
```

---

### 3.3 Event Detection (개체명 인식)

**Task Type:** Named Entity Recognition (NER) or Relation Extraction

**Input:**
```python
{
    "text": "HMM 매각을 둘러싼 인수전이 치열하다...",
    "title": "HMM 인수전 치열, 3개 컨소시엄 입찰 예정"
}
```

**Label:**
```python
{
    "events": ["HMM_ACQUISITION"],
    "relevance_scores": [0.95]
}
```

**Classes (Dynamic):**
```
HMM_ACQUISITION, HD_HYUNDAI_AUTONOMOUS, POSCO_RESTRUCTURE, ...
(이벤트는 동적으로 추가/종료됨)
```

**학습 데이터 추출 쿼리:**
```sql
SELECT
    a.id,
    a.title,
    a.summary,
    GROUP_CONCAT(e.event_code) as labels,
    GROUP_CONCAT(ae.relevance_score) as scores
FROM articles a
JOIN article_events ae ON a.id = ae.article_id
JOIN events e ON ae.event_id = e.id
WHERE ae.relevance_score > 0.7
GROUP BY a.id;
```

---

## 4. 학습 파이프라인

### 4.1 데이터 준비

```python
import sqlite3
import pandas as pd

def load_training_data():
    conn = sqlite3.connect('data/news_leafletter.db')

    # Sector 학습 데이터
    sector_df = pd.read_sql("""
        SELECT
            a.title || ' ' || a.summary as text,
            s.sector_code as label
        FROM articles a
        JOIN article_sectors ase ON a.id = ase.article_id
        JOIN sectors s ON ase.sector_id = s.id
        WHERE ase.confidence > 0.7
    """, conn)

    # Theme 학습 데이터
    theme_df = pd.read_sql("""
        SELECT
            a.id,
            a.title || ' ' || a.summary as text,
            GROUP_CONCAT(t.theme_code) as labels
        FROM articles a
        JOIN article_themes at ON a.id = at.article_id
        JOIN themes t ON at.theme_id = t.id
        WHERE at.confidence > 0.7
        GROUP BY a.id
    """, conn)

    conn.close()
    return sector_df, theme_df
```

### 4.2 라벨 인코딩

#### Sector (단일 라벨)
```python
from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
y_sector = label_encoder.fit_transform(sector_df['label'])

# 클래스: ['COMMUNICATION', 'CONSUMER', 'ENERGY', 'FINANCIALS', ...]
```

#### Theme (다중 라벨)
```python
from sklearn.preprocessing import MultiLabelBinarizer

# labels: "SEMICONDUCTOR,AI" -> ["SEMICONDUCTOR", "AI"]
theme_df['labels'] = theme_df['labels'].str.split(',')

mlb = MultiLabelBinarizer()
y_theme = mlb.fit_transform(theme_df['labels'])

# 출력: [[1, 1, 0, 0, ...], [0, 1, 0, 1, ...], ...]
```

### 4.3 모델 학습 예시

#### Sector Classification (scikit-learn)
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# 파이프라인 구성
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000)),
    ('clf', LogisticRegression(multi_class='multinomial', max_iter=1000))
])

# 학습
pipeline.fit(X_train, y_train)

# 예측
predictions = pipeline.predict(X_test)
```

#### Theme Classification (Transformers)
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.utils.data import DataLoader

# 모델 로드
model = AutoModelForSequenceClassification.from_pretrained(
    "klue/roberta-base",
    num_labels=len(mlb.classes_),
    problem_type="multi_label_classification"
)

tokenizer = AutoTokenizer.from_pretrained("klue/roberta-base")

# 학습 (multi-label)
# ...
```

---

## 5. 라벨 품질 관리

### 5.1 신뢰도 점수 (Confidence Score)

모든 라벨에는 `confidence` 또는 `relevance_score`가 포함됩니다:

- **0.9 ~ 1.0**: 매우 확실한 분류 (키워드 다수 매칭)
- **0.7 ~ 0.9**: 신뢰할 만한 분류 (키워드 일부 매칭)
- **< 0.7**: 불확실한 분류 (학습 데이터에서 제외 권장)

### 5.2 라벨 검증

```sql
-- 라벨이 없는 기사 찾기
SELECT id, title FROM articles
WHERE id NOT IN (SELECT article_id FROM article_sectors);

-- 신뢰도가 낮은 라벨 찾기
SELECT a.id, a.title, s.sector_name, ase.confidence
FROM articles a
JOIN article_sectors ase ON a.id = ase.article_id
JOIN sectors s ON ase.sector_id = s.id
WHERE ase.confidence < 0.7;
```

### 5.3 라벨 분포 확인

```sql
-- Sector 분포
SELECT s.sector_name, COUNT(*) as cnt
FROM article_sectors ase
JOIN sectors s ON ase.sector_id = s.id
GROUP BY s.sector_name
ORDER BY cnt DESC;

-- Theme 분포
SELECT t.theme_name, COUNT(*) as cnt
FROM article_themes at
JOIN themes t ON at.theme_id = t.id
GROUP BY t.theme_name
ORDER BY cnt DESC;
```

---

## 6. 장점 및 기대 효과

### 6.1 명확한 역할 분리

| 차원 | 역할 | 특징 | ML 태스크 |
|------|------|------|-----------|
| **Sector** | 뼈대 | 고정, 안정적 | Single-label Classification |
| **Theme** | 방향 | 유동, 확장 가능 | Multi-label Classification |
| **Event** | 서사 | 시간 제한적 | NER / Relation Extraction |

### 6.2 확장성

- **Sector**: 변경 최소 (안정성 보장)
- **Theme**: 신규 테마 추가 용이 (기존 모델 재학습 불필요)
- **Event**: 동적 관리 (종료된 이벤트 자동 비활성화)

### 6.3 설명 가능성 (Explainability)

- 분류 결과가 명확함: "IT 섹터, AI·반도체 테마, HMM 인수전 이벤트"
- 각 차원별 신뢰도 점수 제공
- 키워드 기반 분류로 해석 가능

### 6.4 데이터 자산화

- 시간이 지나도 분류 체계 붕괴 없음
- 과거 데이터를 신규 모델로 재분류 가능
- 섹터별/테마별/이벤트별 교차 분석 가능

---

## 7. 다음 단계 (Next Steps)

### 마일스톤 4 - Day 1~5

1. **데이터 수집 자동화**
   - RSS 수집 시 자동 분류 적용
   - 신뢰도가 낮은 기사는 수동 라벨링 큐에 추가

2. **키워드 확장**
   - 실제 기사 데이터 분석을 통한 키워드 확장
   - TF-IDF 기반 자동 키워드 추출

3. **모델 실험**
   - Baseline: TF-IDF + Logistic Regression
   - Advanced: KoBERT, KoELECTRA 등 Transformer 모델

4. **평가 지표 설정**
   - Sector: Accuracy, F1-score (macro)
   - Theme: Hamming Loss, F1-score (micro/macro)
   - Event: Precision, Recall, F1-score

5. **Active Learning**
   - 모델 예측 신뢰도가 낮은 샘플 우선 라벨링
   - 인간 피드백 반영하여 모델 개선

---

## 8. 참고 자료

- **GICS (Global Industry Classification Standard)**: https://www.msci.com/gics
- **Multi-label Classification**: https://scikit-learn.org/stable/modules/multiclass.html
- **Transformers for Korean NLP**: https://github.com/KLUE-benchmark/KLUE

---

**Built with ❤️ by [FerryLa]**

© 2025 News-Leafletter
