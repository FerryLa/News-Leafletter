# Leafletter News Bot (News-Leafletter)

개인 맞춤형 뉴스 스캐너 텔레그램 봇입니다.  
관심 키워드를 등록해두면, 명령어(/scan)로 한 번에 관련 뉴스를 조회하고,  
RSS 기반으로 새로 올라오는 기사도 자동으로 감시해서 텔레그램으로 알려줍니다.

---

## 기능 요약

- **키워드 기반 뉴스 검색**
    - 일반 텍스트 입력 → 해당 키워드로 뉴스 검색
    - `/add` `/list` `/del` `/scan` 명령어로 관심 키워드 관리
- **RSS 기반 실시간 감시**
    - 여러 RSS 피드를 주기적으로 긁어서 새 기사 탐지
    - `/rss_now` 로 수동 확인
    - `/rss_auto_on` / `/rss_auto_off` 으로 자동 알림 ON/OFF
- **개인용 텔레그램 봇**
    - BotFather로 생성한 봇 토큰 사용
    - 개인 채팅방에서만 동작 (현재 기준)

---

## 기술 스택

- Python 3.10+
- [python-telegram-bot 20.x](https://docs.python-telegram-bot.org/)
- `requests` (뉴스 API 호출)
- `feedparser` (RSS 파싱)
- 추후 예정
    - `pandas`, `numpy` (CSV/JSON 분석)
    - `scikit-learn`, `sentence-transformers` (대전환 이벤트 감지용 간단 ML/임베딩)

---

## 폴더 구조

```text
News-Leafletter/
  app/
    bot.py              # 텔레그램 봇 엔트리 포인트
    news.py             # 뉴스 API 검색 로직
    storage.py          # 관심 키워드 저장/로드 (JSON 기반)
    rss/
      rss_fetcher.py    # RSS 수집 및 신규 기사 판별
      rss_sources.py    # RSS 피드 목록 정의
  data/
    watchlist.json      # 유저별 관심 키워드 저장 파일
    rss_state.json      # 이미 본 RSS 기사 ID 목록
  config.py             # 토큰/키 등 설정
  requirements.txt
  README.md
