"""
테스트: 속보/단독 뉴스 감지 시스템
Issue #36: 단독/속보 뉴스 빠른 전달 시스템
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.scoring.breaking_detector import (
    detect_breaking_keywords,
    is_exclusive_news,
    is_breaking_news,
    get_breaking_score,
)


def test_detect_breaking_keywords():
    """속보 키워드 감지 테스트"""
    print("\n=== 속보 키워드 감지 테스트 ===")

    test_cases = [
        ("[속보] 미국 금리 인상", True, 15),
        ("[단독] 삼성전자 신제품 공개", True, 12),
        ("[긴급] 대통령 긴급 발표", True, 15),
        ("일반 뉴스 제목", False, 0),
        ("Breaking News from US", True, 12),
        ("[전격] 정부 정책 발표", True, 10),
    ]

    for title, expected_found, expected_score in test_cases:
        found, score = detect_breaking_keywords(title)
        status = "[PASS]" if (found == expected_found and score == expected_score) else "[FAIL]"
        print(f"{status} '{title}' -> found={found}, score={score}")


def test_is_exclusive_news():
    """단독 뉴스 판단 테스트"""
    print("\n=== 단독 뉴스 판단 테스트 ===")

    test_cases = [
        ("[단독] 현대차 배터리 자체 생산", True),
        ("[독점] 네이버 블록체인 진출", True),
        ("[속보] 주가 급등", False),
        ("일반 뉴스", False),
        ("단독입수 정부 내부 문건", True),
    ]

    for title, expected in test_cases:
        result = is_exclusive_news(title)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"{status} '{title}' -> {result}")


def test_is_breaking_news():
    """속보 판단 테스트 (단독 제외)"""
    print("\n=== 속보 판단 테스트 ===")

    test_cases = [
        ("[속보] 미국 금리 인상", True),
        ("[긴급] 대통령 발표", True),
        ("[단독] 삼성전자 신제품", False),  # 단독은 속보에서 제외
        ("일반 뉴스", False),
        ("Breaking News", True),
    ]

    for title, expected in test_cases:
        result = is_breaking_news(title)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"{status} '{title}' -> {result}")


def test_get_breaking_score():
    """속보 점수 반환 테스트"""
    print("\n=== 속보 점수 반환 테스트 ===")

    test_cases = [
        ("[속보] 미국 금리 인상", 15),
        ("[단독] 삼성전자 신제품", 12),
        ("[전격] 정부 정책", 10),
        ("일반 뉴스", 0),
    ]

    for title, expected_score in test_cases:
        score = get_breaking_score(title)
        status = "[PASS]" if score == expected_score else "[FAIL]"
        print(f"{status} '{title}' -> {score}점")


def test_clustering_exclusion():
    """단독 뉴스 클러스터링 제외 테스트"""
    print("\n=== 클러스터링 제외 로직 테스트 ===")

    # 가상 기사 생성
    articles = [
        {"title": "[단독] 조선일보 - 삼성전자 AI 칩 개발", "score": 15},
        {"title": "[단독] 중앙일보 - 현대차 배터리 생산", "score": 15},
        {"title": "[속보] 연합뉴스 - 미국 금리 인상", "score": 15},
        {"title": "[속보] KBS - 미국 기준금리 전격 인상", "score": 15},
    ]

    print("\n입력 기사:")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['title']}")

    # 분류
    exclusives = [a for a in articles if is_exclusive_news(a["title"])]
    breaking = [a for a in articles if not is_exclusive_news(a["title"])]

    print(f"\n단독 뉴스 ({len(exclusives)}개) - 클러스터링 제외:")
    for article in exclusives:
        print(f"  - {article['title']}")

    print(f"\n속보 ({len(breaking)}개) - 클러스터링 대상:")
    for article in breaking:
        print(f"  - {article['title']}")

    # 검증
    assert len(exclusives) == 2, "단독 뉴스 2개여야 함"
    assert len(breaking) == 2, "속보 2개여야 함"
    print("\n[PASS] 클러스터링 제외 로직 테스트 통과")


if __name__ == "__main__":
    print("=" * 60)
    print("Issue #36: 속보/단독 뉴스 감지 시스템 테스트")
    print("=" * 60)

    test_detect_breaking_keywords()
    test_is_exclusive_news()
    test_is_breaking_news()
    test_get_breaking_score()
    test_clustering_exclusion()

    print("\n" + "=" * 60)
    print("[SUCCESS] 모든 테스트 완료!")
    print("=" * 60)
