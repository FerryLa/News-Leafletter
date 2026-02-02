# Issue #37: 피드백 및 속보 기능 재구현

## 📌 개요
Issue #36에서 구현한 텔레그램 피드백 및 속보 기능이 심각한 버그를 유발하여 롤백되었습니다.
이번 이슈에서는 안정성을 우선으로 하여 해당 기능들을 재검토하고 재구현합니다.

## 🐛 Issue #36에서 발생한 문제들

### 1. **봇 시작 실패 (치명적)**
- **원인**: Windows cp949 인코딩 환경에서 한글 이모지 출력 불가
- **오류**: `bot.py:1589` - `UnicodeEncodeError`
- **영향**: 봇이 전혀 실행되지 않음

### 2. **봇 인스턴스 충돌**
- **오류**: `Conflict: terminated by other getUpdates request`
- **원인**: 여러 봇 프로세스가 동시에 실행되어 텔레그램 API 충돌
- **영향**: 명령어 응답 없음

### 3. **뉴스 전송 중단**
- **증상**: `/rss_now` 실행 시 "📡 RSS 확인 중..." 이후 무응답
- **원인**:
  - 클러스터링/섹터 분류 과정에서 타임아웃 발생 가능성
  - RSS fetcher 응답 지연
- **영향**: 사용자가 뉴스를 전혀 받지 못함

## 🎯 재구현 목표

### Phase 1: 안정성 우선 (v1.0)
- [ ] Windows 환경 호환성 보장
  - [ ] 모든 출력 메시지를 ASCII 또는 UTF-8로 제한
  - [ ] 한글 이모지 사용 금지 또는 안전한 대체
- [ ] 봇 인스턴스 관리 개선
  - [ ] PID 파일로 중복 실행 방지
  - [ ] Graceful shutdown 구현
- [ ] 성능 최적화
  - [ ] 클러스터링 타임아웃 설정 (최대 30초)
  - [ ] RSS fetcher 비동기 최적화
  - [ ] 섹터 분류 비활성화 옵션 제공

### Phase 2: 기능 재구현 (v2.0)
- [ ] **피드백 기능**
  - [ ] `/like`, `/dislike` 명령어
  - [ ] `/feedback` 통계 보기
  - [ ] 이모지 리액션 (선택적, Windows 환경에서 안전성 검증 후)
  - [ ] DB 저장 및 통계 분석

- [ ] **속보 기능**
  - [ ] `/breaking_now` - 실시간 속보 확인
  - [ ] `/breaking_auto_on/off` - 속보 자동 알림
  - [ ] NewsAPI top-headlines 통합
  - [ ] 속보 자동 감지 (제목 키워드 기반)

### Phase 3: 테스트 및 검증 (v3.0)
- [ ] 단위 테스트 작성
  - [ ] 피드백 저장/조회 테스트
  - [ ] 속보 감지 로직 테스트
  - [ ] 인코딩 호환성 테스트
- [ ] 통합 테스트
  - [ ] Windows/Linux 환경 모두 검증
  - [ ] 24시간 안정성 테스트
  - [ ] 메모리 누수 확인
- [ ] 에러 핸들링
  - [ ] 모든 async 함수에 try-except 추가
  - [ ] 사용자 친화적 에러 메시지
  - [ ] 로깅 시스템 강화

## 🔧 기술적 개선사항

### 1. 인코딩 문제 해결
```python
# ❌ 기존 (오류 발생)
print("⚠️ MessageReactionHandler를 사용할 수 없습니다.")

# ✅ 개선안 1: ASCII 출력
print("WARNING: MessageReactionHandler not available.")

# ✅ 개선안 2: UTF-8 강제
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 2. 봇 인스턴스 관리
```python
# PID 파일로 중복 실행 방지
import os
import sys

PID_FILE = 'bot.pid'

def check_already_running():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            old_pid = int(f.read())
        if psutil.pid_exists(old_pid):
            print(f"Bot already running (PID: {old_pid})")
            sys.exit(1)

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
```

### 3. 타임아웃 설정
```python
# RSS fetcher 타임아웃
async def fetch_with_timeout():
    try:
        return await asyncio.wait_for(
            fetch_new_articles_async(),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.warning("RSS fetch timeout")
        return []
```

## 📋 체크리스트

### 필수 사항
- [ ] Windows 10/11 환경에서 정상 작동 확인
- [ ] `/rss_now` 명령어 5초 이내 응답
- [ ] 24시간 연속 실행 시 메모리 누수 없음
- [ ] 모든 텔레그램 명령어 응답률 99% 이상

### 선택 사항
- [ ] Linux 환경 호환성
- [ ] Docker 이미지 제공
- [ ] 성능 모니터링 대시보드

## 🚀 배포 계획

1. **Phase 1 완료 후** → develop 브랜치 병합
2. **Phase 2 완료 후** → 베타 테스트 (1주일)
3. **Phase 3 완료 후** → main 브랜치 병합 및 릴리스 v2.0

## 📚 참고 자료

- Issue #36: 텔레그램 피드백 기능 추가 (롤백됨)
- Commit `b1cf8a5`: [FEAT] 텔레그램 피드백 기능 추가
- Commit `2f1912c`: [REVERT] Issue #36 롤백

---

**우선순위**: 🔴 High (Critical)
**담당자**: @FerryLa
**예상 소요 시간**: 2-3주
**관련 이슈**: #36
