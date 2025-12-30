# Issue #16: 언론사 필터링 구현 완료

## 개요
사용자가 특정 언론사를 차단하거나 허용할 수 있는 뉴스 소스 필터링 기능을 구현했습니다.

## 구현된 기능

### 1. 데이터베이스 스키마
**파일**: `app/database/db_manager.py`

- `user_preferences` 테이블 추가
  - `chat_id`: 사용자 ID (PRIMARY KEY)
  - `blocked_sources`: 차단된 언론사 목록 (JSON 배열)
  - `allowed_sources`: 허용된 언론사 목록 (JSON 배열)
  - `created_at`, `updated_at`: 타임스탬프

- 마이그레이션 함수: `_migrate_for_issue_16()`

### 2. 데이터베이스 메서드
**파일**: `app/database/db_manager.py` (lines 1176-1360)

- `get_blocked_sources(chat_id)`: 차단된 언론사 목록 조회
- `get_allowed_sources(chat_id)`: 허용된 언론사 목록 조회
- `block_source(chat_id, source)`: 언론사 차단
- `unblock_source(chat_id, source)`: 언론사 차단 해제
- `allow_source(chat_id, source)`: 언론사 허용
- `disallow_source(chat_id, source)`: 언론사 허용 해제

### 3. 도메인-언론사 매핑
**파일**: `app/utils/news_source_mapper.py`

주요 기능:
- `DOMAIN_TO_OUTLET`: 49개 언론사 도메인 매핑
  - 한국 주요 언론사: 조선일보, 중앙일보, KBS, MBC 등
  - 경제지: 매일경제, 한국경제, 파이낸셜뉴스 등
  - 국제 언론: BBC, Reuters, Bloomberg, WSJ 등
  - 암호화폐 전문: CoinDesk, Cointelegraph 등
  - 정부기관: 금융위원회, 한국은행, 금융감독원 등

- `extract_source_from_url(url)`: URL에서 언론사명 추출
  - www. 자동 제거
  - 서브도메인 처리 (예: news.kbs.co.kr → KBS)
  - .co.kr, .go.kr 같은 2단계 도메인 지원
  - 매핑되지 않은 도메인은 그대로 반환

- `get_all_sources()`: 모든 매핑된 언론사 목록 반환

### 4. 텔레그램 봇 커맨드
**파일**: `bot.py` (lines 383-473)

#### `/block <언론사명>`
- 특정 언론사 기사 차단
- 예: `/block 조선일보` 또는 `/block chosun.com`
- 차단 완료 시 전체 차단 목록 표시

#### `/allow <언론사명>`
- 차단 해제
- 예: `/allow 조선일보`
- 남은 차단 목록 표시

#### `/sources`
- 현재 차단된 언론사 목록 표시
- 매핑된 주요 언론사 목록 (처음 20개) 표시

### 5. 필터링 로직
**파일**: `bot.py` (lines 186-212)

- `filter_by_source(news_items, chat_id)`: 기사 목록 필터링
  - 사용자의 차단 목록 조회
  - URL에서 언론사 추출
  - 차단된 언론사 기사 제거

- 적용 위치:
  1. `send_news_with_images()`: 일반 뉴스 전송 시 (line 227)
  2. `rss_auto_loop()`: RSS 자동 알림 시 (line 314)

### 6. 사용자 안내 메시지 업데이트
**파일**: `app/super_controller.py` (lines 24-27)

`/start` 명령어에 언론사 필터링 안내 추가:
```
언론사 필터링 (Issue #16):
- /block 언론사명  : 특정 언론사 기사 차단
- /allow 언론사명  : 차단 해제
- /sources        : 차단 목록 및 매핑된 언론사 보기
```

## 테스트
**파일**: `test_source_filtering.py`

테스트 결과:
- ✅ URL에서 언론사 추출: 6/6 성공
  - 조선일보, KBS, Reuters, CoinDesk, 금융위원회 등
  - 서브도메인 처리 (news.kbs.co.kr → KBS)
  - 매핑되지 않은 도메인 처리
- ✅ 매핑된 언론사 목록: 49개
- ✅ 데이터베이스 작업 (차단/해제) 정상 작동

## 사용 예시

### 1. 언론사 차단
```
사용자: /block 조선일보
봇: 🚫 '조선일보' 차단 완료

차단된 언론사 (1):
• 조선일보
```

### 2. 차단 목록 확인
```
사용자: /sources
봇: 🚫 차단된 언론사 (1):
• 조선일보

📰 매핑된 주요 언론사 (49):
• BBC
• Bloomberg
• CNBC
...
```

### 3. 차단 해제
```
사용자: /allow 조선일보
봇: ✅ '조선일보' 차단 해제 완료

이제 차단된 언론사가 없습니다.
```

## 기술적 특징

1. **JSON 기반 저장**: 차단/허용 목록을 JSON 배열로 저장하여 유연성 확보
2. **Thread-safe**: DatabaseManager의 thread-local 연결 사용
3. **자동 마이그레이션**: 앱 시작 시 테이블 자동 생성
4. **역호환성**: 기존 기능에 영향 없이 새 기능 추가
5. **확장 가능**: 새 언론사 추가는 DOMAIN_TO_OUTLET 딕셔너리만 수정
6. **도메인 정규화**: www, 서브도메인, 2단계 TLD 자동 처리

## 파일 변경 목록

### 신규 파일
- `app/utils/news_source_mapper.py`: 도메인-언론사 매핑
- `app/utils/__init__.py`: utils 모듈 초기화
- `test_source_filtering.py`: 단위 테스트
- `IMPLEMENTATION_ISSUE_16.md`: 구현 문서 (현재 파일)

### 수정 파일
- `app/database/db_manager.py`:
  - `_migrate_for_issue_16()` 추가
  - 언론사 필터링 메서드 6개 추가
- `bot.py`:
  - `filter_by_source()` 함수 추가
  - `/block`, `/allow`, `/sources` 커맨드 핸들러 추가
  - 필터링 로직 통합
- `app/super_controller.py`:
  - `DEFAULT_START_MESSAGE` 업데이트

## 다음 단계 (선택사항)

1. 화이트리스트 모드 구현 (allowed_sources만 허용)
2. 언론사별 통계 (차단된 기사 수 등)
3. 정규표현식 기반 도메인 매칭
4. 언론사 별칭/동의어 지원
5. 차단 기록 로깅

## 완료 체크리스트

- ✅ user_preferences 테이블 생성
- ✅ 데이터베이스 메서드 구현
- ✅ 도메인-언론사 매핑 딕셔너리 (49개 언론사)
- ✅ URL에서 언론사 추출 함수
- ✅ `/block` 커맨드 구현
- ✅ `/allow` 커맨드 구현
- ✅ `/sources` 커맨드 구현
- ✅ 필터링 로직 통합 (send_news_with_images, rss_auto_loop)
- ✅ 단위 테스트 작성 및 통과
- ✅ 사용자 안내 메시지 업데이트

---

**구현 완료일**: 2025-12-29
**Issue**: #16
**Branch**: develop
