# Unit Tests

단위 테스트 파일들이 위치한 폴더입니다.

## 파일 목록

- `test_scoring.py` - 스코어링 기능 테스트
- `test_scoring_simple.py` - 간단한 스코어링 테스트
- `test_direct_scoring.py` - 직접 스코어링 테스트
- `test_user_keywords.py` - 사용자 키워드 관리 테스트
- `test_rss.py` - RSS 피드 테스트
- `test_rss_cache.py` - RSS 캐시 테스트
- `test_new_articles.py` - 새 기사 탐지 테스트
- `test_simple.py` - 기본 기능 테스트
- `test_database.py` - 데이터베이스 테스트
- `test_issue_22.py` - Issue #22 관련 테스트
- `test_issue_34.py` - Issue #34 관련 테스트
- `test_source_filtering.py` - 언론사 필터링 테스트
- `test_sector_classifier.py` - 섹터 분류 테스트
- `test_breaking_detector.py` - 속보 탐지 테스트
- `test_bot_import.py` - 봇 임포트 테스트
- `test_emoji_reactions.py` - 이모지 반응 테스트
- `test_feedback.py` - 피드백 기능 테스트
- `test_handler_import.py` - 핸들러 임포트 테스트
- `test_migration.py` - 마이그레이션 테스트

## 실행 방법

```bash
# 특정 테스트 실행
python tests/unit/test_scoring.py

# 가상환경에서 실행
.venv/Scripts/python tests/unit/test_scoring.py
```
