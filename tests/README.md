# Tests Directory

News-Leafletter 프로젝트의 테스트 및 검증 파일들을 관리하는 디렉토리입니다.

## 폴더 구조

```
tests/
├── unit/              # 단위 테스트
│   ├── test_scoring.py
│   ├── test_database.py
│   └── ...
├── integration/       # 통합 테스트
│   └── (여러 컴포넌트 연동 테스트)
├── check/            # 시스템 상태 확인 스크립트
│   ├── check_db_schema.py
│   ├── check_cache_data.py
│   └── ...
└── debug/            # 디버그 및 로깅
    ├── run_bot_debug.py
    ├── run_bot_with_logging.py
    └── *.log
```

## 각 폴더 설명

### 📁 unit/
개별 함수나 클래스의 기능을 독립적으로 테스트하는 단위 테스트 파일들

**주요 테스트:**
- 스코어링 기능
- 데이터베이스 CRUD
- RSS 피드 처리
- 키워드 관리
- 섹터 분류

### 📁 integration/
여러 컴포넌트가 함께 동작하는 것을 테스트하는 통합 테스트 파일들

**테스트 예시:**
- RSS 수집 → 스코어링 → 알림 전체 프로세스
- 봇 명령어 → 데이터베이스 → 응답 워크플로우

### 📁 check/
시스템 상태를 확인하고 검증하는 스크립트들

**용도:**
- 데이터베이스 스키마 확인
- 캐시 데이터 검증
- 기능 동작 확인
- 버그 수정 후 검증

### 📁 debug/
디버깅과 로깅을 위한 파일들

**포함 내용:**
- 디버그 모드 실행 스크립트
- 로그 파일들
- 트러블슈팅 도구

## 실행 방법

### 단위 테스트
```bash
# 특정 테스트 실행
python tests/unit/test_scoring.py

# 가상환경에서 실행
.venv/Scripts/python tests/unit/test_scoring.py
```

### 시스템 확인
```bash
# 데이터베이스 스키마 확인
python tests/check/check_db_schema.py

# 캐시 데이터 확인
python tests/check/check_cache_data.py
```

### 디버그 모드 실행
```bash
# 디버그 모드로 봇 실행
python tests/debug/run_bot_debug.py

# 로깅 활성화
python tests/debug/run_bot_with_logging.py
```

## 테스트 작성 가이드

### 단위 테스트 작성
1. `tests/unit/` 폴더에 `test_*.py` 형식으로 파일 생성
2. 테스트할 기능을 명확하게 분리
3. 각 테스트는 독립적으로 실행 가능해야 함

### 통합 테스트 작성
1. `tests/integration/` 폴더에 파일 생성
2. 여러 컴포넌트의 상호작용 테스트
3. 실제 사용 시나리오를 반영

## 파일 정리

로그 파일과 임시 파일은 주기적으로 정리:
```bash
# 로그 파일 삭제
rm tests/debug/*.log
rm tests/debug/*.txt
```
