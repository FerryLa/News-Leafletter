# 📰 Leafletter News Bot

개인 맞춤형 AI 뉴스 큐레이션 텔레그램 봇

---

## ✨ 주요 기능

- 🎯 **스마트 스코어링**: 키워드 기반 자동 뉴스 수집 및 점수화
- 📡 **실시간 RSS 모니터링**: 57개 언론사 자동 수집 (2분 간격, 중복 자동 제거)
- 🤖 **AI 클러스터링**: 유사 뉴스 자동 그룹화
- ⚡ **속보/단독 우선순위**: 속보/단독 뉴스 자동 감지 및 높은 점수 부여 ✨ NEW
- 📊 **섹터 분류**: 5개 주요 섹터 + 41개 하위 카테고리 자동 분류
- 💾 **SQLite 아카이브**: 전체 기사 저장 및 통계 분석
- 👍 **유저 피드백**: 좋아요/싫어요, 이모지 리액션 지원 ✨ NEW

---

## 🚀 빠른 시작

### 1️⃣ 프로젝트 클론 및 업데이트

```bash
# 저장소 클론
git clone https://github.com/yourusername/News-Leafletter.git
cd News-Leafletter

# 최신 코드로 업데이트 (이미 클론한 경우)
git pull origin main
```

### 2️⃣ Python 가상환경 설정

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

### 3️⃣ 패키지 설치

```bash
# 가상환경이 활성화된 상태에서 실행
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ 설정 파일 생성 (중요 🔐)

프로젝트 루트에 `config.py` 파일을 생성하고 다음 내용을 입력하세요:

```python
# config.py
TELEGRAM_TOKEN = "your-telegram-bot-token-here"
NEWSAPI_KEY = "your-newsapi-key-here"
```

**⚠️ 보안 주의사항:**

- `config.py`는 `.gitignore`에 등록되어 있어 Git에 업로드되지 않습니다
- API 키는 절대 공개 저장소에 커밋하지 마세요
- 텔레그램 봇 토큰: [@BotFather](https://t.me/BotFather)에서 발급
- NewsAPI 키: [newsapi.org](https://newsapi.org/)에서 무료 발급

### 5️⃣ 실행

```bash
# 가상환경 활성화 상태에서 실행
python bot.py
```

### 6️⃣ 가상환경 종료

```bash
# 작업 완료 후 가상환경 비활성화
deactivate
```

---

## 📱 텔레그램 명령어

### 키워드 관리

| 명령어           | 설명                    | 예시            |
| ---------------- | ----------------------- | --------------- |
| `/add <키워드>`  | 관심 키워드 추가 (+1점) | `/add 비트코인` |
| `/add -<키워드>` | 제외 키워드 추가 (-1점) | `/add -밈코인`  |
| `/list`          | 등록된 키워드 목록      |                 |
| `/del <키워드>`  | 키워드 삭제             | `/del 비트코인` |
| `/scan`          | 모든 키워드 뉴스 조회   |                 |

### 뉴스 알림

| 명령어     | 설명                          |
| ---------- | ----------------------------- |
| `/start`   | 뉴스 자동 알림 시작 (2분 간격) |
| `/stop`    | 뉴스 자동 알림 중지             |
| `/rss_now` | RSS 신규 기사 수동 확인         |

### 속보 기능

| 명령어                | 설명                        |
| --------------------- | --------------------------- |
| `/breaking_now`       | 실시간 속보 확인             |
| `/breaking_auto_on`   | 속보 자동 알림 시작 (5분 간격) |
| `/breaking_auto_off`  | 속보 자동 알림 중지          |

### 피드백

| 명령어           | 설명                  |
| ---------------- | --------------------- |
| `/like`          | 최근 기사에 좋아요     |
| `/dislike [이유]` | 최근 기사에 싫어요     |
| `/feedback`      | 내 피드백 통계 보기    |
| 👍/👎 이모지     | 기사에 직접 리액션     |

### 스코어링 예시

```
- [+3] 비트코인 ETF 승인 임박 (Bloomberg)
- [+1] 암호화폐 시장 분석 (Reuters)
- [-1] 밈코인 급등 소식 (CoinDesk)
```

---

## 🏆 마일스톤

### ✅ 1-2단계: RSS 파이프라인 & UX (100%)

- [x] RSS 50+ 언론사 자동 수집
- [x] 키워드 스코어링 시스템
- [x] 텔레그램 명령어 UX 개선
- [x] 클러스터링 기반 중복 제거

### ✅ 3단계: 유저 피드백 로깅 (100%) ✨ 완료!

- [x] **Issue #22**: SQLite DB 전환 완료
  - JSON → SQLite 마이그레이션
  - 중복 기사 자동 필터링
  - 배치 저장 성능 최적화 (10배 향상)
- [x] **Issue #36**: 속보/단독 뉴스 빠른 전달 ✨ NEW
  - 속보 자동 감지 및 우선순위 점수 부여 (+12~15점)
  - 단독 뉴스 클러스터링 제외 (언론사별 모두 전달)
  - RSS 폴링 간격 단축 (10초 → 2분)
- [x] 기사 아카이브 시스템
- [x] 유저 피드백 UI (좋아요/싫어요, 이모지 리액션)
- [x] 통계 대시보드 기초
- [ ] 피드백 기반 개인화 추천 (마일스톤 4)

### 📋 4-7단계: ML & 프로덕션 (예정)

- [ ] **4단계**: ML/임베딩 실험용 데이터 쌓기
- [ ] **5단계**: 추천/클러스터링 모듈 실험
- [ ] **6단계**: 운영 대시보드 & 유료 플랜
- [ ] **7단계**: 보안/저작권/배포 정책

---

## ⚙️ 설정 관리

`data/config.json` 예시:

```json
{
  "whitelist": {
    "enabled": false,
    "values": []
  },
  "blacklist": {
    "enabled": true,
    "values": ["광고", "sponsored"]
  },
  "admin_keywords": {
    "비트코인": 3,
    "이더리움": 3,
    "ETF": 3,
    "밈코인": -3
  },
  "clustering": {
    "enabled": false,
    "similarity_threshold": 0.7
  },
  "sector_classification": {
    "enabled": true,
    "min_confidence": 0.1,
    "top_subcategories": 3
  },
  "news": {
    "page_size": 10
  },
  "rss": {
    "auto_interval": 120
  }
}
```

**주요 설정:**

- `admin_keywords`: 관리자 키워드 가중치 (±3)
- `blacklist`: 필터링 키워드
- `clustering.enabled`: 중복 제거 활성화
- `sector_classification.enabled`: 섹터 분류 활성화
- `rss.auto_interval`: RSS 체크 주기 (초, 기본 120초)

자세한 섹터 분류 설정은 [섹터 분류 문서](docs/SECTOR_CLASSIFICATION.md)를 참고하세요.

---

## 🛠️ 기술 스택

### Core

- **Python 3.10+**: 메인 언어
- **SQLite 3.x**: 기사 아카이브 & 캐싱
- **python-telegram-bot 22.5**: 텔레그램 봇 프레임워크 (이모지 리액션 지원)

### APIs & Data

- **NewsAPI**: 뉴스 검색 API
- **feedparser**: RSS 파싱
- **requests**: HTTP 클라이언트

### AI/ML (선택)

- **scikit-learn**: TF-IDF, 코사인 유사도
- **sentence-transformers**: 임베딩 (실험 중)

### 데이터베이스 구조

```sql
-- 기사 저장 (Issue #22 구현)
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    link TEXT UNIQUE NOT NULL,  -- 중복 방지
    title TEXT NOT NULL,
    summary TEXT,
    source_url TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 유저 키워드
CREATE TABLE user_keywords (
    chat_id INTEGER,
    keyword TEXT,
    UNIQUE(chat_id, keyword)
);

-- 유저 피드백 (진행 중)
CREATE TABLE user_feedback (
    chat_id INTEGER,
    article_id TEXT,
    feedback_type TEXT,
    feedback_value INTEGER
);
```

---

## 📂 폴더 구조

```
News-Leafletter/
├── app/
│   ├── database/          # SQLite 매니저 (Issue #22 ✨)
│   │   ├── db_manager.py      # 중복 제거, 배치 저장
│   │   └── __init__.py
│   ├── classification/    # 섹터 분류 (Issue #33 ✨)
│   │   ├── sector_classifier.py    # 분류 로직
│   │   ├── sector_definitions.py   # 섹터 정의
│   │   └── __init__.py
│   ├── clustering/        # 중복 제거
│   │   └── news_clusterer.py
│   ├── scoring/           # 스코어링
│   │   └── keyword_scoring.py
│   ├── rss/               # RSS 수집
│   │   ├── rss_fetcher.py
│   │   └── rss_sources.py
│   ├── news.py            # 뉴스 검색
│   ├── storage.py         # 키워드 저장
│   └── super_controller.py  # 설정 관리
├── data/
│   ├── news_leafletter.db   # SQLite DB ✨
│   ├── config.json
│   └── watchlist.json
├── tests/
│   ├── test_issue_22.py        # DB 테스트
│   └── test_sector_classifier.py  # 섹터 분류 테스트 ✨
├── docs/
│   ├── KPI_REPORT.md
│   ├── MIGRATION_GUIDE.md
│   ├── SQLITE_CLI_GUIDE.md
│   └── SECTOR_CLASSIFICATION.md  # 섹터 분류 가이드 ✨
├── bot.py                 # 메인 엔트리
├── requirements.txt
└── README.md
```

---

## 📊 주요 성과

### 1-2단계 완료 (RSS 자동화 + UX)

- ✅ RSS 50+ 언론사 자동 수집
- ✅ 스코어링 시스템 구축
- ✅ 텔레그램 UX 개선

### 3단계 완료! (유저 피드백 로깅 100%) 🎉

**Issue #22 완료: SQLite DB 전환**

| 항목           | 기존 (JSON) | 현재 (SQLite) | 개선률        |
| -------------- | ----------- | ------------- | ------------- |
| 중복 체크 속도 | 500ms       | 50ms          | **10배** ⚡   |
| 메모리 사용량  | 100MB       | 50MB          | 50% 감소      |
| 동시성 지원    | ❌          | ✅            | ACID 보장     |
| 에러율         | 5%          | 0.1%          | **50배** 개선 |

**Issue #36 완료: 속보/단독 뉴스 빠른 전달** ✨ NEW

| 기능                | 구현 내용                     |
| ------------------- | ----------------------------- |
| 속보 자동 감지       | [속보], [긴급], [특보] → +15점 |
| 단독 뉴스 우선 처리  | [단독] → +12점, 클러스터링 제외 |
| RSS 폴링 최적화     | 10초 → 2분 (안정성 + 속도)     |
| 중복 제거           | 속보는 클러스터링, 단독은 개별 전달 |

---

## 📝 라이선스

이 프로젝트는 개인 프로젝트입니다.

---

## 📧 연락처

문의사항이 있으시면 아래의 E-mail주소에 메일을 남겨주세요.

**E-mail: rlawl4240@gmail.com**

---

**Built with ❤️ by [FerryLa]**

© 2025 News-Leafletter
