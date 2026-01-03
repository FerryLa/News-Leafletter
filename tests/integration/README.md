# Integration Tests

통합 테스트 파일들이 위치한 폴더입니다.

## 용도

여러 컴포넌트가 함께 동작하는 것을 테스트하는 파일들을 여기에 배치합니다.

예시:
- 봇 전체 워크플로우 테스트
- API + 데이터베이스 통합 테스트
- RSS 피드 수집부터 알림까지 전체 프로세스 테스트

## 실행 방법

```bash
# 통합 테스트 실행
python tests/integration/test_full_workflow.py

# 가상환경에서 실행
.venv/Scripts/python tests/integration/test_full_workflow.py
```

## 단위 테스트와의 차이

- **단위 테스트** (unit): 개별 함수나 클래스의 기능을 독립적으로 테스트
- **통합 테스트** (integration): 여러 컴포넌트가 연동되어 동작하는 것을 테스트
