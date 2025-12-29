# 📊 섹터 분류 시스템

News-Leafletter의 섹터 분류 시스템은 뉴스 기사를 자동으로 5개 주요 섹터와 41개 하위 카테고리로 분류합니다.

## 🎯 주요 기능

- ✅ **5개 주요 섹터**: 거시경제, 사회정책, 금융, 산업/기술, 문화/생활
- ✅ **41개 하위 카테고리**: 각 섹터별 세부 분류
- ✅ **키워드 기반 분류**: 신뢰도 점수와 함께 자동 분류
- ✅ **유연한 설정**: config.json으로 간편한 활성화/비활성화

## 📋 섹터 구조

### 1️⃣ 거시경제 (Macro Economy)

**하위 카테고리 (10개)**:
- 국제 무역
- 인플레이션
- 금리 정책
- 전쟁 리스크
- 글로벌 공급망
- 신흥국 경제 동향
- 환율 전쟁
- 에너지 위기
- 보호무역주의
- FTA 재협상

**키워드 예시**: 거시경제, 무역, 금리, 인플레이션, 전쟁, 공급망, 신흥국, 환율, 에너지, 보호무역

### 2️⃣ 사회정책 (Social Policy)

**하위 카테고리 (9개)**:
- 소비 심리
- 부동산 규제
- 총선 공약
- 지역 균형 발전
- 청년 실업률
- 자영업 지원 정책
- 인구 감소 대응
- 지방 소멸 위기
- 공공요금 인상

**키워드 예시**: 사회정책, 복지, 부동산, 선거, 청년실업, 자영업, 인구감소, 공공요금

### 3️⃣ 금융 (Finance)

**하위 카테고리 (8개)**:
- 증시 변동성
- 암호화폐 규제
- 금값 랠리
- 달러 강세
- ESG 투자 확대
- 채권 시장 유동성
- 외환 보유고 감소
- 핀테크 규제 완화

**키워드 예시**: 금융, 주식, 코스피, 암호화폐, 비트코인, 금, 달러, ESG, 채권, 핀테크

### 4️⃣ 산업/기술 (Industry/Technology)

**하위 카테고리 (7개)**:
- AI 혁신
- 반도체 수급난
- 바이오 신약 개발
- 자율주행 상용화
- 우주 산업 클러스터
- 친환경 기술 보조금
- 데이터 주권 강화

**키워드 예시**: AI, 반도체, 바이오, 신약, 자율주행, 전기차, 우주산업, 친환경기술, 데이터주권

### 5️⃣ 문화/생활 (Culture/Lifestyle)

**하위 카테고리 (7개)**:
- K팝 수출
- 게임 산업 규제
- 기후 재해
- 디지털 저작권 분쟁
- 문화유산 보존 정책
- 탄소 중립 캠페인
- 반려동물 산업 성장

**키워드 예시**: K팝, 한류, 게임, 기후, 기후변화, 저작권, 문화유산, 탄소중립, 반려동물

## ⚙️ 설정 방법

`data/config.json` 파일에서 섹터 분류를 설정할 수 있습니다:

```json
{
  "sector_classification": {
    "enabled": true,           // 섹터 분류 활성화 여부
    "min_confidence": 0.1,     // 최소 신뢰도 임계값 (0.0 ~ 1.0)
    "top_subcategories": 3     // 표시할 최대 하위 카테고리 수
  }
}
```

### 설정 옵션

| 옵션 | 설명 | 기본값 | 범위 |
|------|------|--------|------|
| `enabled` | 섹터 분류 활성화 | `true` | true/false |
| `min_confidence` | 분류 최소 신뢰도 | `0.1` | 0.0 ~ 1.0 |
| `top_subcategories` | 표시할 하위 카테고리 수 | `3` | 1 ~ 10 |

## 🔍 사용 예시

### Python 코드에서 사용

```python
from app.classification.sector_classifier import classify_article

# 단일 기사 분류
article = {
    "title": "비트코인 급등, 암호화폐 시장 활성화",
    "description": "가상자산 거래소에서 비트코인 거래량 증가"
}

result = classify_article(article, min_confidence=0.1)

# 결과 확인
if result.primary_sector:
    print(f"주요 섹터: {result.primary_sector.sector_name}")
    print(f"신뢰도: {result.primary_sector.confidence:.2f}")

# 하위 카테고리
for subcat in result.subcategories:
    print(f"- {subcat.subcategory_name} ({subcat.confidence:.2f})")
```

### 출력 예시

```
주요 섹터: 금융
신뢰도: 0.25
- 암호화폐 규제 (0.67)
- 증시 변동성 (0.15)
```

## 📊 통계 및 분석

```python
from app.classification.sector_classifier import (
    classify_articles,
    get_sector_statistics,
    get_subcategory_statistics
)

# 여러 기사 분류
articles = [...]
results = classify_articles(articles)

# 섹터별 통계
sector_stats = get_sector_statistics(results)
# {"금융": 5, "산업/기술": 3, "거시경제": 2}

# 하위 카테고리별 통계
subcat_stats = get_subcategory_statistics(results)
# {"암호화폐 규제": 3, "AI 혁신": 2, ...}
```

## 🧪 테스트

섹터 분류 시스템을 테스트하려면:

```bash
python tests/test_sector_classifier.py
```

테스트 결과 예시:

```
🚀 섹터 분류기 테스트 시작

============================================================
테스트 1: 섹터 정의 확인
============================================================

총 5개 섹터:
  - 거시경제 (macro_economy): 10개 하위 카테고리
  - 사회정책 (social_policy): 9개 하위 카테고리
  - 금융 (finance): 8개 하위 카테고리
  - 산업/기술 (industry_tech): 7개 하위 카테고리
  - 문화/생활 (culture_lifestyle): 7개 하위 카테고리

✅ 섹터 정의 테스트 통과
```

## 🔧 커스터마이징

섹터와 하위 카테고리를 커스터마이징하려면 `app/classification/sector_definitions.py` 파일을 수정하세요:

```python
SECTOR_DEFINITIONS = {
    "custom_sector": {
        "name": "커스텀 섹터",
        "keywords": ["키워드1", "키워드2"],
        "subcategories": {
            "custom_subcat": {
                "name": "커스텀 하위 카테고리",
                "keywords": ["세부키워드1", "세부키워드2"]
            }
        }
    }
}
```

## 📈 성능 특징

- **빠른 분류**: 키워드 매칭 기반으로 실시간 분류
- **확장 가능**: 새로운 섹터/카테고리 추가 용이
- **신뢰도 점수**: 각 분류에 대한 신뢰도 제공
- **다중 섹터**: 하나의 기사가 여러 섹터에 속할 수 있음

## 🎓 분류 알고리즘

1. **텍스트 추출**: 제목, 설명, 본문에서 텍스트 추출
2. **키워드 매칭**: 정의된 키워드와 매칭
3. **신뢰도 계산**: 매칭된 키워드 수 / 전체 키워드 수
4. **임계값 필터링**: min_confidence 이상만 선택
5. **정렬**: 신뢰도 순으로 정렬하여 반환

## 📝 참고사항

- 섹터 분류는 클러스터링 후 각 클러스터의 대표 기사를 기준으로 수행됩니다
- 키워드는 대소문자를 구분하지 않습니다
- 여러 섹터에 동시에 분류될 수 있으며, primary/secondary로 우선순위가 부여됩니다

## 🔗 관련 문서

- [README.md](../README.md): 프로젝트 전체 개요
- [KPI_REPORT.md](KPI_REPORT.md): 성과 지표
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md): DB 마이그레이션

---

**Built with ❤️ by [FerryLa]**

© 2025 News-Leafletter
