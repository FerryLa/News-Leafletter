# 📰 Leafletter News Bot

개인 맞춤형 AI 뉴스 큐레이션 텔레그램 봇

---

## 주요 기능

- 키워드 기반 뉴스 자동 수집 및 스코어링
- 50+ 언론사 RSS 실시간 모니터링
- AI 클러스터링 중복 제거
- SQLite 기사 아카이브 및 피드백 시스템

---

## 빠른 시작

```bash
git clone https://github.com/yourusername/News-Leafletter.git
cd News-Leafletter
pip install -r requirements.txt

# config.py에 API 키 입력 후
python bot.py
```

---

## 텔레그램 명령어

| 명령어 | 설명 |
|--------|------|
| `/add 비트코인` | 키워드 추가 (+1점) |
| `/add -밈코인` | 제외 키워드 (-1점) |
| `/list` | 키워드 목록 |
| `/del 비트코인` | 키워드 삭제 |
| `/scan` | 전체 뉴스 조회 |
| `/rss_now` | RSS 수동 확인 |
| `/rss_auto_on/off` | 자동 알림 시작/중지 |

---

## 마일스톤

### ✅ 완료
- [x] **1단계**: RSS 수집/자동화 파이프라인 완성화 (100%)
- [x] **2단계**: 스코어 튜닝 및 텔레그램 응답 UX 개선 (100%)

### 🚧 진행 중
- [ ] **3단계**: 유저 피드백 로깅 (12%)

### 📋 예정
- [ ] **4단계**: ML/임베딩 실험용 데이터 쌓기
- [ ] **5단계**: 추천/클러스터링 모듈 실험
- [ ] **6단계**: 운영 대시보드 & 유료 플랜 준비
- [ ] **7단계**: 보안·저작권·코스트/배포 정책 정리

---

## 설정 관리

`data/config.json`:

```json
{
  "blacklist": {
    "enabled": true,
    "values": ["광고"]
  },
  "admin_keywords": {
    "비트코인": 3,
    "밈코인": -3
  },
  "news": { "page_size": 10 },
  "rss": { "auto_interval": 5 }
}
```

---

## 기술 스택

Python 3.10+, SQLite 3.x, python-telegram-bot, NewsAPI, feedparser, scikit-learn

---

## 폴더 구조

```
News-Leafletter/
├── app/
│   ├── database/       # SQLite 매니저
│   ├── clustering/     # 중복 제거
│   ├── scoring/        # 스코어링
│   ├── rss/            # RSS 수집
│   └── *.py            # 봇 메인 로직
├── data/
│   ├── news_leafletter.db
│   └── config.json
├── tests/
├── docs/
└── README.md
```

---

## 주요 성과

**1-2단계 완료 (RSS 자동화 + UX 개선)**
- RSS 50+ 언론사 자동 수집
- 스코어링 시스템 구축
- 텔레그램 명령어 UX 개선

**3단계 진행 중 (유저 피드백 로깅)**
- SQLite DB 전환: 성능 100배 향상
- 기사 아카이브 시스템 구축
- 속도: 50ms → 0.5ms
- 안정성: 에러율 5% → 0%

자세히: [docs/KPI_REPORT.md](docs/KPI_REPORT.md)

---

## 문서

- [마이그레이션 가이드](docs/MIGRATION_GUIDE.md)
- [SQLite CLI 가이드](docs/SQLITE_CLI_GUIDE.md)

---

© 2024 News-Leafletter | 개인 프로젝트
