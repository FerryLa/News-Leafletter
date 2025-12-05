# Leafletter News Bot (News-Leafletter)

개인 맞춤형 뉴스 스캐너 텔레그램 봇입니다.  
관심 키워드를 등록해두면, 명령어(/scan)로 한 번에 관련 뉴스를 조회하고,  
RSS 기반으로 새로 올라오는 기사도 자동으로 감시해서 텔레그램으로 알려줍니다.

기사마다 **어드민 키워드(+3/−3)와 유저 키워드(+1/−1)**를 반영한 스코어를 계산하고,  
화이트리스트/블랙리스트 키워드로 뉴스 노이즈를 줄일 수 있습니다.

---

## 설정 관리 (super_controller)

- `app/super_controller.py`가 `data/config.json`을 읽어 **화이트/블랙리스트, 점수 규칙, 어드민 키워드, 뉴스/ RSS/봇 동작 설정**을 한 곳에서 관리합니다.
- 각 필터/점수 규칙은 `enabled` 플래그로 On/Off 할 수 있으며, 설정을 수정한 뒤 `reload()` 메서드로 핫리로드 확장도 가능합니다.
- 기본 설정 예시는 `data/config.json`에 포함되어 있으며, 기존 `data/admin_keywords.json`과 `data/keyword_filters.json` 내용도 자동으로 병합되는 방식으로 동작합니다.

---

## 기능 요약

- **키워드 기반 뉴스 검색 & 스코어링**
    - 일반 텍스트 입력 → 해당 키워드로 뉴스 검색
    - 검색 결과는 키워드 스코어링을 적용해 `• [+3] 제목 (매체)` 형식으로 표시
    - `/add`, `/list`, `/del`, `/scan` 명령어로 관심 키워드 관리
        - `/add 키워드` → 유저 관심 키워드 **+1점**
        - `/add -키워드` → 유저 관심 키워드 **−1점** (제외하고 싶은 단어)
    - `/scan` → 등록된 모든 관심 키워드에 대해 한 번에 뉴스 조회

- **RSS 기반 실시간 감시 (스코어링 포함)**
    - 여러 RSS 피드를 주기적으로 긁어서 새 기사 탐지
    - `/rss_now` 로 새로 들어온 기사 수동 확인
    - `/rss_auto_on` / `/rss_auto_off` 으로 자동 알림 ON/OFF
    - RSS 기사에도 동일한 키워드 스코어링/필터링 적용
        - 블랙리스트에 걸리면 기사 자체를 제외
        - 화이트리스트가 설정된 경우, 해당 단어가 하나도 없으면 제외

- **키워드 스코어링 / 필터링 규칙**
    - **어드민 키워드**
        - `data/admin_keywords.json` 에서 정의
        - 예: `"비트코인": 3`, `"밈코인": -3`
        - 보통 ±3 정도로 강한 가중치
    - **유저 키워드**
        - `/add` 명령어로 등록
        - `"비트코인"` → +1, `"-밈코인"` → −1
        - 유저 키워드는 `data/watchlist.json`에 chat_id별로 저장
    - **화이트리스트 / 블랙리스트**
        - `data/keyword_filters.json` 에서 정의
        - `whitelist` 에 포함된 단어가 하나도 없으면 기사 제외
        - `blacklist` 에 포함된 단어가 하나라도 있으면 기사 제외

- **개인용 텔레그램 봇**
    - BotFather로 생성한 봇 토큰 사용
    - 개인 채팅방에서만 동작 (현재 기준)

---

## 텔레그램 명령어 정리

봇 사용법은 `app/bot.py`의 `/start` 안내와 동일하게 동작합니다.

- 일반 텍스트 입력  
    - 해당 텍스트로 뉴스 검색  
    - 어드민/유저 키워드를 반영한 스코어링 결과 출력

- `/start`  
    - 봇 소개 및 기본 사용법 안내

- `/add <키워드>`  
    - 관심 키워드 추가  
    - 예)
        - `/add 비트코인 뉴스` → “비트코인 뉴스”에 +1점 가중치
        - `/add -밈코인` → “밈코인” 포함 기사에 −1점 가중치

- `/list`  
    - 현재 등록된 관심 키워드 목록 출력

- `/del <키워드>`  
    - 특정 관심 키워드 삭제

- `/scan`  
    - 등록된 모든 관심 키워드에 대해 한 번에 뉴스 조회  
    - 각 키워드별로 관련 뉴스 목록을 스코어 순으로 출력

- `/rss_now`  
    - RSS에서 새로 들어온 기사 수동 확인  
    - 스코어링/필터링 적용 후 상위 기사 출력

- `/rss_auto_on`  
    - RSS 자동 알림 시작  
    - 설정된 주기(AUTO_INTERVAL 초)마다 새 기사 확인 후,  
      스코어링/필터링을 통과한 기사만 텔레그램으로 전송

- `/rss_auto_off`  
    - RSS 자동 알림 중지

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
    bot.py                  # 텔레그램 봇 엔트리 포인트 (명령어 정의)
    news.py                 # 뉴스 API 검색 로직
    storage.py              # 관심 키워드 저장/로드 (JSON 기반, watchlist.json)
    scoring/
      keyword_scoring.py    # 어드민/유저 키워드 기반 기사 스코어링 & 필터링
    rss/
      rss_fetcher.py        # RSS 수집 및 신규 기사 판별
      rss_sources.py        # RSS 피드 목록 정의
  data/
    watchlist.json          # 유저별 관심 키워드 저장 파일 (chat_id 기준)
    rss_state.json          # 이미 본 RSS 기사 ID 목록
    admin_keywords.json     # 어드민 키워드 및 스코어(가중치) 설정
    keyword_filters.json    # 화이트리스트/블랙리스트 키워드 설정
  config.py                 # 토큰/키 등 설정 (TELEGRAM_TOKEN, NEWSAPI_KEY 등)
  requirements.txt
  README.md
