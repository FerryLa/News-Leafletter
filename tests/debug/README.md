# Debug & Logging

디버그 및 로깅 관련 파일들이 위치한 폴더입니다.

## 파일 목록

### 스크립트
- `run_bot_debug.py` - 디버그 모드로 봇 실행
- `run_bot_with_logging.py` - 로깅을 활성화한 봇 실행

### 로그 파일
- `bot_log.txt` - 봇 실행 로그
- `bot_clean.log` - 정리된 로그 파일

## 실행 방법

```bash
# 디버그 모드로 봇 실행
python tests/debug/run_bot_debug.py

# 로깅 활성화하여 봇 실행
python tests/debug/run_bot_with_logging.py

# 가상환경에서 실행
.venv/Scripts/python tests/debug/run_bot_debug.py
```

## 용도

- **디버깅**: 봇의 상세한 동작을 추적하고 문제를 진단
- **로깅**: 실행 중 발생하는 이벤트를 기록
- **트러블슈팅**: 오류 발생 시 원인 파악

## 로그 파일 관리

로그 파일은 주기적으로 정리하는 것을 권장합니다:
```bash
# 오래된 로그 파일 삭제
rm tests/debug/*.log
rm tests/debug/*.txt
```
