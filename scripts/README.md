# Scripts Directory

유틸리티 스크립트들을 관리하는 디렉토리입니다.

## 파일 목록

### view_feedback.py
유저 피드백을 조회하고 통계를 확인하는 스크립트

**사용법:**
```bash
# 전체 피드백 통계
python scripts/view_feedback.py

# 특정 사용자 피드백 조회
python scripts/view_feedback.py [chat_id]

# CSV로 내보내기
python scripts/view_feedback.py [chat_id] --export [output_file.csv]
```

**예시:**
```bash
# 전체 통계 확인
python scripts/view_feedback.py

# chat_id 12345의 피드백 조회
python scripts/view_feedback.py 12345

# CSV로 내보내기
python scripts/view_feedback.py 12345 --export my_feedback.csv
```

### clear_rss_cache.py
RSS 캐시를 정리하는 스크립트

**사용법:**
```bash
# RSS 캐시 전체 삭제
python scripts/clear_rss_cache.py
```

**용도:**
- 오래된 RSS 캐시 삭제
- 중복 기사 필터링 초기화
- 데이터베이스 공간 확보

## 실행 환경

모든 스크립트는 프로젝트 루트에서 실행해야 합니다:

```bash
# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 스크립트 실행
python scripts/view_feedback.py
```

## 새로운 스크립트 추가

유틸리티 스크립트를 추가할 때는:
1. 이 폴더에 파일 생성
2. 명확한 파일명 사용 (동사_명사.py)
3. 스크립트 상단에 docstring으로 용도 설명
4. 이 README에 사용법 추가

## 스크립트 작성 가이드

```python
#!/usr/bin/env python3
"""
스크립트 설명
사용법: python scripts/script_name.py [arguments]
"""

import sys
sys.path.insert(0, '.')

# 나머지 코드...
```
