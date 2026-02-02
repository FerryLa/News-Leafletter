"""
속보/단독 뉴스 감지 모듈
Issue #36: 단독/속보 뉴스 빠른 전달 시스템
"""

from typing import Tuple


# 속보 키워드 정의 (우선순위별)
BREAKING_KEYWORDS = {
    # 최고 긴급도
    "[긴급]": 15,
    "[속보]": 15,
    "[특보]": 15,
    "긴급속보": 15,

    # 단독 뉴스
    "[단독]": 12,
    "Breaking": 12,
    "BREAKING": 12,
    "단독입수": 12,

    # 긴급 이벤트
    "[전격]": 10,
    "[독점]": 10,
    "전격발표": 10,
}


def detect_breaking_keywords(title: str) -> Tuple[bool, int]:
    """
    제목에서 속보 키워드 감지

    Args:
        title: 기사 제목

    Returns:
        (is_breaking, priority_score)
        - is_breaking: 속보 여부
        - priority_score: 우선순위 점수 (0~15)
    """
    if not title:
        return (False, 0)

    # 가장 높은 점수를 반환 (여러 키워드 포함 시)
    max_score = 0
    found = False

    for keyword, score in BREAKING_KEYWORDS.items():
        if keyword in title:
            found = True
            max_score = max(max_score, score)

    return (found, max_score)


def is_exclusive_news(title: str) -> bool:
    """
    단독 뉴스 여부 판단

    Args:
        title: 기사 제목

    Returns:
        True if 단독 뉴스
    """
    exclusive_keywords = ["[단독]", "단독입수", "[독점]"]

    for keyword in exclusive_keywords:
        if keyword in title:
            return True

    return False


def is_breaking_news(title: str) -> bool:
    """
    속보 여부 판단 (단독 제외)

    Args:
        title: 기사 제목

    Returns:
        True if 속보 (단독 뉴스는 False)
    """
    if is_exclusive_news(title):
        return False

    breaking_keywords = ["[긴급]", "[속보]", "[특보]", "긴급속보", "Breaking", "BREAKING", "[전격]", "전격발표"]

    for keyword in breaking_keywords:
        if keyword in title:
            return True

    return False


def get_breaking_score(title: str) -> int:
    """
    속보 점수 반환 (간편 함수)

    Args:
        title: 기사 제목

    Returns:
        속보 점수 (0~15)
    """
    _, score = detect_breaking_keywords(title)
    return score
