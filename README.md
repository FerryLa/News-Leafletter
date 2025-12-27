# 📰 Leafletter News Bot

개인 맞춤형 AI 뉴스 큐레이션 텔레그램 봇

---

## ✨ 주요 기능

- 🎯 **스마트 스코어링**: 키워드 기반 자동 뉴스 수집 및 점수화
- 📡 **실시간 RSS 모니터링**: 50+ 언론사 자동 수집 (중복 자동 제거)
- 🤖 **AI 클러스터링**: 유사 뉴스 자동 그룹화
- 💾 **SQLite 아카이브**: 전체 기사 저장 및 통계 분석
- 👍 **유저 피드백**: 피드백 로깅 시스템 (진행 중)

---

## 🚀 빠른 시작
```bash
# 1. 클론
git clone https://github.com/yourusername/News-Leafletter.git
cd News-Leafletter

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 설정 파일 생성
# config.py에 API 키 입력:
# - TELEGRAM_TOKEN
# - NEWSAPI_KEY

# 4. 실행
python bot.py
```

---

## 📱 텔레그램 명령어

### 키워드 관리
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/add <키워드>` | 관심 키워드 추가 (+1점) | `/add 비트코인` |
| `/add -<키워드>` | 제외 키워드 추가 (-1점) | `/add -밈코인` |
| `/list` | 등록된 키워드 목록 | |
| `/del <키워드>` | 키워드 삭제 | `/del 비트코인` |
| `/scan` | 모든 키워드 뉴스 조회 | |

### RSS 기능
| 명령어 | 설명 |
|--------|------|
| `/rss_now` | RSS 신규 기사 수동 확인 |
| `/rss_auto_on` | 자동 알림 시작 (5초 간격) |
| `/rss_auto_off` | 자동 알림 중지 |

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

### ✅ 3단계: 유저 피드백 로깅 (35%)
- [x] **Issue #22**: SQLite DB 전환 완료 ✨ NEW
  - JSON → SQLite 마이그레이션
  - 중복 기사 자동 필터링
  - 배치 저장 성능 최적화 (10배 향상)
- [x] 기사 아카이브 시스템
- [x] 통계 대시보드 기초
- [ ] 유저 피드백 UI (북마크, 좋아요/싫어요)
- [ ] 피드백 기반 개인화 추천

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
  "news": {
    "page_size": 10
  },
  "rss": {
    "auto_interval": 5
  }
}
```

**주요 설정:**
- `admin_keywords`: 관리자 키워드 가중치 (±3)
- `blacklist`: 필터링 키워드
- `clustering.enabled`: 중복 제거 활성화
- `rss.auto_interval`: RSS 체크 주기 (초)

---

## 🛠️ 기술 스택

### Core
- **Python 3.10+**: 메인 언어
- **SQLite 3.x**: 기사 아카이브 & 캐싱
- **python-telegram-bot 20.x**: 텔레그램 봇 프레임워크

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
│   └── test_issue_22.py   # DB 테스트
├── docs/
│   ├── KPI_REPORT.md
│   ├── MIGRATION_GUIDE.md
│   └── SQLITE_CLI_GUIDE.md
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

### 3단계 진행 중 (유저 피드백 로깅 35%)
**🎉 Issue #22 완료: SQLite DB 전환**

| 항목 | 기존 (JSON) | 현재 (SQLite) | 개선률 |
|------|-------------|---------------|--------|
| 중복 체크 속도 | 500ms | 50ms | **10배** ⚡ |
| 메모리 사용량 | 100MB | 50MB | 50% 감소 |
| 동시성 지원 | ❌ | ✅ | ACID 보장 |
| 에러율 | 5% | 0.1% | **50배** 개선 |
| 저장 용량 | 무제한 | 자동 정리 | 효율적 |


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