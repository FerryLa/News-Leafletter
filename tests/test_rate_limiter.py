"""
테스트: NewsAPI 할당량 관리 시스템
Issue #36: NewsAPI 하루 100회 제한 준수
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.newsapi_rate_limiter import NewsAPIRateLimiter


def test_basic_rate_limiting():
    """기본 레이트 리미팅 테스트"""
    print("\n=== 기본 레이트 리미팅 테스트 ===")

    limiter = NewsAPIRateLimiter(daily_limit=5)  # 테스트용 제한 5회

    print(f"일일 제한: {limiter.daily_limit}회")
    print(f"초기 호출 가능 여부: {limiter.can_call()}")
    print(f"남은 호출 횟수: {limiter.get_remaining_calls()}")

    # 5회 호출
    for i in range(1, 6):
        if limiter.can_call():
            limiter.record_call()
            print(f"  호출 {i}: 성공 (남은 횟수: {limiter.get_remaining_calls()})")
        else:
            print(f"  호출 {i}: 실패 - 할당량 초과")

    # 6번째 호출 시도 (실패해야 함)
    print(f"\n6번째 호출 시도:")
    if limiter.can_call():
        print("  [FAIL] 실패 - 호출이 허용되어서는 안 됨")
    else:
        print("  [PASS] 성공 - 할당량 초과로 차단됨")

    stats = limiter.get_stats()
    print(f"\n통계:")
    print(f"  - 사용: {stats['used']}/{stats['daily_limit']}")
    print(f"  - 남음: {stats['remaining']}")


def test_auto_reset():
    """자동 리셋 테스트"""
    print("\n=== 자동 리셋 테스트 ===")

    limiter = NewsAPIRateLimiter(daily_limit=3)

    # 3회 호출
    for _ in range(3):
        limiter.record_call()

    print(f"호출 후 상태: {limiter.call_count}/{limiter.daily_limit}")
    print(f"호출 가능 여부: {limiter.can_call()}")

    # 강제 리셋 (시간을 과거로 설정하여 테스트)
    limiter.reset_time = datetime.now(timezone.utc) - timedelta(seconds=1)

    # 리셋 확인
    print(f"\n리셋 시간 도달 후:")
    print(f"호출 가능 여부: {limiter.can_call()}")
    print(f"남은 호출 횟수: {limiter.get_remaining_calls()}")

    if limiter.can_call() and limiter.get_remaining_calls() == 3:
        print("[PASS] 자동 리셋 성공")
    else:
        print("[FAIL] 자동 리셋 실패")


def test_concurrent_usage():
    """동시 사용 시뮬레이션"""
    print("\n=== 동시 사용 시뮬레이션 ===")

    limiter = NewsAPIRateLimiter(daily_limit=10)

    # 10개의 요청 시뮬레이션
    success_count = 0
    fail_count = 0

    for i in range(15):  # 제한보다 많이 시도
        if limiter.can_call():
            limiter.record_call()
            success_count += 1
        else:
            fail_count += 1

    print(f"총 시도: 15회")
    print(f"  - 성공: {success_count}회")
    print(f"  - 실패: {fail_count}회 (할당량 초과)")

    if success_count == 10 and fail_count == 5:
        print("[PASS] 동시 사용 테스트 통과")
    else:
        print("[FAIL] 동시 사용 테스트 실패")


def test_stats_accuracy():
    """통계 정확도 테스트"""
    print("\n=== 통계 정확도 테스트 ===")

    limiter = NewsAPIRateLimiter(daily_limit=100)

    # 50회 호출
    for _ in range(50):
        limiter.record_call()

    stats = limiter.get_stats()

    print(f"통계 정보:")
    print(f"  - 일일 제한: {stats['daily_limit']}")
    print(f"  - 사용: {stats['used']}")
    print(f"  - 남음: {stats['remaining']}")
    print(f"  - 리셋 시간: {stats['reset_time']}")

    if stats['used'] == 50 and stats['remaining'] == 50:
        print("[PASS] 통계 정확도 테스트 통과")
    else:
        print("[FAIL] 통계 정확도 테스트 실패")


if __name__ == "__main__":
    print("=" * 60)
    print("Issue #36: NewsAPI 할당량 관리 테스트")
    print("=" * 60)

    test_basic_rate_limiting()
    test_auto_reset()
    test_concurrent_usage()
    test_stats_accuracy()

    print("\n" + "=" * 60)
    print("[SUCCESS] 모든 테스트 완료!")
    print("=" * 60)
