"""
NewsAPI 할당량 관리 모듈
Issue #36: 하루 100회 제한 준수를 위한 레이트 리미터
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


class NewsAPIRateLimiter:
    """NewsAPI 호출 제한 관리"""

    def __init__(self, daily_limit: int = 100):
        """
        Args:
            daily_limit: 하루 최대 호출 횟수 (기본 100)
        """
        self.daily_limit = daily_limit
        self.call_count = 0
        self.reset_time: Optional[datetime] = None
        self._reset_limiter()

    def _reset_limiter(self):
        """리미터 초기화 (하루 시작)"""
        now = datetime.now(timezone.utc)
        # 다음 날 00:00 UTC 계산
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.reset_time = tomorrow
        self.call_count = 0

    def _check_reset(self):
        """시간이 지나면 자동 리셋"""
        now = datetime.now(timezone.utc)
        if self.reset_time and now >= self.reset_time:
            self._reset_limiter()

    def can_call(self) -> bool:
        """
        API 호출 가능 여부 확인

        Returns:
            True if 호출 가능 (제한 내)
        """
        self._check_reset()
        return self.call_count < self.daily_limit

    def record_call(self):
        """API 호출 기록"""
        self._check_reset()
        self.call_count += 1

    def get_remaining_calls(self) -> int:
        """남은 호출 횟수 반환"""
        self._check_reset()
        return max(0, self.daily_limit - self.call_count)

    def get_reset_time(self) -> Optional[datetime]:
        """리셋 시간 반환"""
        return self.reset_time

    def get_stats(self) -> dict:
        """통계 정보 반환"""
        self._check_reset()
        return {
            "daily_limit": self.daily_limit,
            "used": self.call_count,
            "remaining": self.get_remaining_calls(),
            "reset_time": self.reset_time.isoformat() if self.reset_time else None,
        }


# 전역 인스턴스 (싱글톤)
_rate_limiter: Optional[NewsAPIRateLimiter] = None


def get_rate_limiter(daily_limit: int = 100) -> NewsAPIRateLimiter:
    """
    전역 레이트 리미터 인스턴스 반환

    Args:
        daily_limit: 하루 최대 호출 횟수

    Returns:
        NewsAPIRateLimiter 인스턴스
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = NewsAPIRateLimiter(daily_limit)
    return _rate_limiter
