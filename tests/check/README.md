# Check Scripts

시스템 상태 확인 및 검증 스크립트들이 위치한 폴더입니다.

## 파일 목록

### 시스템 상태 확인
- `check_db_schema.py` - 데이터베이스 스키마 확인
- `check_cache_data.py` - 캐시 데이터 확인
- `check_clustering.py` - 클러스터링 동작 확인
- `check_sectors.py` - 섹터 분류 확인

### 진단 스크립트
- `diagnose_rss.py` - RSS 피드 문제 진단
- `diagnose_scoring.py` - 스코어링 시스템 진단

### 검증 스크립트
- `verify_handler_fix.py` - 핸들러 수정 검증

## 실행 방법

```bash
# 데이터베이스 스키마 확인
python tests/check/check_db_schema.py

# 캐시 데이터 확인
python tests/check/check_cache_data.py

# 가상환경에서 실행
.venv/Scripts/python tests/check/check_db_schema.py
```

## 용도

이 스크립트들은 주로 다음과 같은 목적으로 사용됩니다:
- 데이터베이스 상태 확인
- 캐시 및 저장된 데이터 검증
- 기능 동작 확인
- 버그 수정 후 검증
