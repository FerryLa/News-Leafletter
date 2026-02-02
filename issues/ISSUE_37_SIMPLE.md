# Issue #37: 피드백/속보 기능 롤백 - 봇 작동 중단 문제

## 문제
Issue #36 (텔레그램 피드백 기능) 병합 후 봇이 완전히 작동 중단

### 증상
- Windows 인코딩 오류로 봇 시작 불가 (`UnicodeEncodeError`)
- 텔레그램 봇 인스턴스 충돌 (`Conflict: terminated by other getUpdates`)
- `/rss_now` 명령어 무응답 - 뉴스가 전혀 나오지 않음

## 해결
- 커밋 `4d0ae85`로 롤백 (피드백 기능 이전 버전)
- 피드백/속보 기능 제거하여 안정성 복구

## 제거된 기능
- `/like`, `/dislike`, `/feedback` (피드백)
- `/breaking_now`, `/breaking_auto_on` (속보)
- 이모지 리액션

## 다음 단계
- 안정성 우선 재구현 필요
- Windows/Linux 환경 모두 호환 보장
- 충분한 테스트 후 재배포

**Priority**: Critical
**Status**: Fixed (롤백 완료)
**Related**: #36
