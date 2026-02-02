"""
속보/단독 뉴스 감지 테스트
Issue #36: 단독/속보 뉴스 빠른 전달 시스템
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scoring.breaking_detector import (
    detect_breaking_keywords,
    is_exclusive_news,
    is_breaking_news,
    get_breaking_score
)


def test_breaking_detection():
    """속보 감지 테스트"""
    print("=" * 60)
    print("속보/단독 뉴스 감지 테스트")
    print("=" * 60)

    test_cases = [
        # (제목, 예상 is_breaking, 예상 is_exclusive, 예상 점수)
        ("[긴급속보] 미국 금리 인상", True, False, 15),
        ("[속보] 비트코인 급락", True, False, 15),
        ("[특보] 한국은행 금리 동결", True, False, 15),
        ("[단독] 삼성전자 AI 칩 개발", False, True, 12),
        ("[단독입수] 네이버 블록체인 사업 진출", False, True, 12),
        ("Breaking: Bitcoin hits new high", True, False, 12),
        ("[전격] 정부 규제 완화", True, False, 10),
        ("일반 뉴스 제목", False, False, 0),
        ("비트코인 시장 분석", False, False, 0),
    ]

    print("\n1. 속보/단독 키워드 감지 테스트")
    print("-" * 60)

    passed = 0
    failed = 0

    for title, expected_breaking, expected_exclusive, expected_score in test_cases:
        is_breaking, score = detect_breaking_keywords(title)
        actual_is_breaking = is_breaking_news(title)
        actual_is_exclusive = is_exclusive_news(title)

        # 검증
        score_ok = score == expected_score
        breaking_ok = actual_is_breaking == expected_breaking
        exclusive_ok = actual_is_exclusive == expected_exclusive

        if score_ok and breaking_ok and exclusive_ok:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"\n제목: {title}")
        print(f"  예상: 속보={expected_breaking}, 단독={expected_exclusive}, 점수={expected_score}")
        print(f"  실제: 속보={actual_is_breaking}, 단독={actual_is_exclusive}, 점수={score}")
        print(f"  결과: {status}")

    print("\n" + "=" * 60)
    print(f"테스트 결과: {passed}개 통과, {failed}개 실패")
    print("=" * 60)

    return failed == 0


def test_scoring_integration():
    """스코어링 시스템 통합 테스트"""
    print("\n\n" + "=" * 60)
    print("스코어링 시스템 통합 테스트")
    print("=" * 60)

    from app.scoring.keyword_scoring import score_article_for_chat

    # 테스트용 기사 데이터
    test_articles = [
        {
            "title": "[속보] 비트코인 ETF 승인",
            "description": "미국 SEC가 비트코인 현물 ETF를 승인했습니다.",
            "expected_min_score": 15  # 속보 점수만
        },
        {
            "title": "[단독] 삼성전자, AI 반도체 개발 성공",
            "description": "삼성전자가 차세대 AI 반도체 개발에 성공했습니다.",
            "expected_min_score": 12  # 단독 점수만
        },
        {
            "title": "일반 비트코인 뉴스",
            "description": "비트코인 가격이 상승했습니다.",
            "expected_min_score": 0  # 속보/단독 없음
        }
    ]

    print("\n속보/단독 점수가 자동으로 추가되는지 확인:")
    print("-" * 60)

    # 테스트용 chat_id (실제 DB에 없어도 됨)
    test_chat_id = 99999

    for idx, article in enumerate(test_articles, 1):
        print(f"\n[테스트 {idx}] {article['title']}")

        scored = score_article_for_chat(article, test_chat_id)

        if scored is None:
            print("  - 필터링됨 (블랙리스트/화이트리스트)")
            continue

        print(f"  - 총 점수: {scored.score}점")
        print(f"  - 매칭된 키워드: {scored.matched_keywords}")

        # 속보/단독 점수 확인
        if "[속보/단독]" in scored.matched_keywords:
            breaking_score = scored.matched_keywords["[속보/단독]"]
            print(f"  - 속보/단독 자동 점수: +{breaking_score}점")

        # 최소 점수 검증
        expected = article["expected_min_score"]
        if scored.score >= expected:
            print(f"  - 결과: PASS (예상 최소 {expected}점 이상)")
        else:
            print(f"  - 결과: FAIL (예상 최소 {expected}점, 실제 {scored.score}점)")

    print("\n" + "=" * 60)


def test_clustering_logic():
    """클러스터링 로직 테스트 (단독 뉴스 제외)"""
    print("\n\n" + "=" * 60)
    print("클러스터링 로직 테스트")
    print("=" * 60)

    from app.scoring.keyword_scoring import ScoredArticle
    from app.clustering.news_clusterer import cluster_scored_articles

    # 테스트 기사 생성
    test_articles = [
        ScoredArticle(
            article={"title": "[단독] 기사 1", "description": "단독 뉴스 1"},
            score=15,
            matched_keywords={"[속보/단독]": 12}
        ),
        ScoredArticle(
            article={"title": "[단독] 기사 2", "description": "단독 뉴스 2"},
            score=14,
            matched_keywords={"[속보/단독]": 12}
        ),
        ScoredArticle(
            article={"title": "[속보] 비트코인 급락", "description": "비트코인이 급락했습니다"},
            score=18,
            matched_keywords={"[속보/단독]": 15}
        ),
        ScoredArticle(
            article={"title": "[속보] 암호화폐 시장 패닉", "description": "암호화폐 시장에 패닉이 왔습니다"},
            score=17,
            matched_keywords={"[속보/단독]": 15}
        ),
        ScoredArticle(
            article={"title": "일반 뉴스 1", "description": "일반적인 뉴스입니다"},
            score=5,
            matched_keywords={}
        ),
    ]

    print("\n테스트 기사 목록:")
    for idx, sa in enumerate(test_articles, 1):
        print(f"  {idx}. {sa.article['title']} (점수: {sa.score})")

    print("\n클러스터링 실행...")
    clustered = cluster_scored_articles(test_articles)

    print(f"\n클러스터링 결과: 총 {len(clustered)}개 클러스터")
    print("-" * 60)

    exclusive_count = 0
    clustered_count = 0

    for idx, cluster in enumerate(clustered, 1):
        title = cluster.main_article.article['title']
        is_exclusive = "[단독]" in title
        is_breaking = "[속보]" in title

        if is_exclusive:
            exclusive_count += 1
            print(f"\n클러스터 {idx}: {title}")
            print(f"  - 유형: 단독 뉴스 (클러스터링 제외)")
            print(f"  - 관련 기사 수: {len(cluster.related_articles)} (단독은 0이어야 함)")
            print(f"  - 점수: {cluster.avg_score}")
        elif is_breaking:
            clustered_count += 1
            print(f"\n클러스터 {idx}: {title}")
            print(f"  - 유형: 속보 뉴스 (클러스터링 적용)")
            print(f"  - 관련 기사 수: {len(cluster.related_articles)}")
            print(f"  - 점수: {cluster.avg_score}")
        else:
            print(f"\n클러스터 {idx}: {title}")
            print(f"  - 유형: 일반 뉴스")
            print(f"  - 관련 기사 수: {len(cluster.related_articles)}")

    print("\n" + "=" * 60)
    print(f"단독 뉴스: {exclusive_count}개 (개별 전달)")
    print(f"속보/일반 뉴스: {clustered_count}개 (클러스터링 적용)")
    print("=" * 60)


if __name__ == "__main__":
    print("\n\n")
    print("=" * 60)
    print("  Issue #36: Breaking/Exclusive News Fast Delivery Test")
    print("=" * 60)
    print("\n")

    # 테스트 실행
    test1_ok = test_breaking_detection()
    test_scoring_integration()
    test_clustering_logic()

    print("\n\n" + "=" * 60)
    if test1_ok:
        print("모든 기본 테스트 통과!")
    else:
        print("일부 테스트 실패")
    print("=" * 60)
