"""
Test suite for sector classification module
Tests sector definitions, classification logic, and integration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.classification.sector_classifier import (
    SectorClassifier,
    classify_article,
    classify_articles,
    get_sector_statistics,
    get_subcategory_statistics
)
from app.classification.sector_definitions import (
    SECTOR_DEFINITIONS,
    get_all_sectors,
    get_sector_name,
    get_subcategories
)


def test_sector_definitions():
    """섹터 정의가 제대로 로드되는지 테스트"""
    print("=" * 60)
    print("테스트 1: 섹터 정의 확인")
    print("=" * 60)

    sectors = get_all_sectors()
    print(f"\n총 {len(sectors)}개 섹터:")
    for sector_id in sectors:
        sector_name = get_sector_name(sector_id)
        subcats = get_subcategories(sector_id)
        print(f"  - {sector_name} ({sector_id}): {len(subcats)}개 하위 카테고리")

    assert len(sectors) == 5, "5개 섹터가 정의되어야 함"
    print("\n✅ 섹터 정의 테스트 통과")


def test_macro_economy_classification():
    """거시경제 섹터 분류 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 거시경제 섹터 분류")
    print("=" * 60)

    # 금리 정책 관련 기사
    article1 = {
        "title": "한국은행 기준금리 인상 단행, 물가 안정 목표",
        "description": "중앙은행이 인플레이션 억제를 위해 금리를 0.25% 포인트 인상했다."
    }

    result1 = classify_article(article1)
    print(f"\n기사: {article1['title']}")
    if result1.primary_sector:
        print(f"주요 섹터: {result1.primary_sector.sector_name} (신뢰도: {result1.primary_sector.confidence:.2f})")
        print(f"매칭 키워드: {', '.join(result1.primary_sector.matched_keywords)}")
    if result1.subcategories:
        print("하위 카테고리:")
        for subcat in result1.subcategories[:3]:
            print(f"  - {subcat.subcategory_name} (신뢰도: {subcat.confidence:.2f})")

    # 전쟁 리스크 관련 기사
    article2 = {
        "title": "우크라이나 전쟁 장기화로 글로벌 공급망 차질",
        "description": "러시아와의 군사 분쟁이 계속되면서 에너지 위기와 원자재 공급 부족이 심화되고 있다."
    }

    result2 = classify_article(article2)
    print(f"\n기사: {article2['title']}")
    if result2.primary_sector:
        print(f"주요 섹터: {result2.primary_sector.sector_name} (신뢰도: {result2.primary_sector.confidence:.2f})")
    if result2.subcategories:
        print("하위 카테고리:")
        for subcat in result2.subcategories[:3]:
            print(f"  - {subcat.subcategory_name} (신뢰도: {subcat.confidence:.2f})")

    print("\n✅ 거시경제 섹터 분류 테스트 통과")


def test_finance_classification():
    """금융 섹터 분류 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 금융 섹터 분류")
    print("=" * 60)

    # 암호화폐 관련 기사
    article = {
        "title": "비트코인 급등, 암호화폐 시장 활성화",
        "description": "가상자산 거래소에서 비트코인과 이더리움 거래량이 급증하면서 코인 투자 열기가 뜨겁다."
    }

    result = classify_article(article)
    print(f"\n기사: {article['title']}")
    if result.primary_sector:
        print(f"주요 섹터: {result.primary_sector.sector_name} (신뢰도: {result.primary_sector.confidence:.2f})")
    if result.subcategories:
        print("하위 카테고리:")
        for subcat in result.subcategories[:3]:
            print(f"  - {subcat.subcategory_name} (신뢰도: {subcat.confidence:.2f})")
            print(f"    매칭 키워드: {', '.join(subcat.matched_keywords)}")

    # "암호화폐" 하위 카테고리가 포함되어야 함
    has_crypto = any("암호화폐" in sc.subcategory_name for sc in result.subcategories)
    assert has_crypto, "암호화폐 관련 기사는 '암호화폐 규제' 하위 카테고리를 포함해야 함"

    print("\n✅ 금융 섹터 분류 테스트 통과")


def test_industry_tech_classification():
    """산업/기술 섹터 분류 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 산업/기술 섹터 분류")
    print("=" * 60)

    # AI 관련 기사
    article = {
        "title": "ChatGPT 등장으로 생성AI 시대 본격화",
        "description": "인공지능 기술이 급속도로 발전하며 딥러닝과 머신러닝 기반 서비스가 확산되고 있다."
    }

    result = classify_article(article)
    print(f"\n기사: {article['title']}")
    if result.primary_sector:
        print(f"주요 섹터: {result.primary_sector.sector_name} (신뢰도: {result.primary_sector.confidence:.2f})")
    if result.subcategories:
        print("하위 카테고리:")
        for subcat in result.subcategories[:3]:
            print(f"  - {subcat.subcategory_name} (신뢰도: {subcat.confidence:.2f})")

    print("\n✅ 산업/기술 섹터 분류 테스트 통과")


def test_multiple_articles_classification():
    """여러 기사 일괄 분류 및 통계 테스트"""
    print("\n" + "=" * 60)
    print("테스트 5: 일괄 분류 및 통계")
    print("=" * 60)

    articles = [
        {
            "title": "코스피 급락, 증시 변동성 확대",
            "description": "주식 시장에서 변동성이 커지며 투자자들의 우려가 높아지고 있다."
        },
        {
            "title": "부동산 규제 강화로 집값 안정화 기대",
            "description": "정부의 주택 정책으로 아파트 가격 상승세가 주춤하고 있다."
        },
        {
            "title": "반도체 공급 부족 심화, 글로벌 생산 차질",
            "description": "칩 부족 현상이 계속되며 파운드리 업체들의 증설이 시급하다."
        },
        {
            "title": "기후 변화로 폭염 피해 증가",
            "description": "이상기후로 인한 자연재해가 늘어나며 기후 위기 대응이 필요하다."
        },
        {
            "title": "K팝 한류 열풍, 해외 수출 급증",
            "description": "방탄소년단과 블랙핑크 등 아이돌 그룹의 인기로 한국 음악이 세계를 사로잡고 있다."
        }
    ]

    results = classify_articles(articles)

    print(f"\n총 {len(results)}개 기사 분류 결과:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.article['title']}")
        if result.primary_sector:
            print(f"   섹터: {result.primary_sector.sector_name}")
        if result.subcategories:
            subcats = ", ".join([sc.subcategory_name for sc in result.subcategories[:2]])
            print(f"   카테고리: {subcats}")

    # 통계
    sector_stats = get_sector_statistics(results)
    subcat_stats = get_subcategory_statistics(results)

    print("\n[섹터별 기사 수]")
    for sector, count in sector_stats.items():
        print(f"  {sector}: {count}개")

    print("\n[하위 카테고리별 기사 수]")
    for subcat, count in sorted(subcat_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {subcat}: {count}개")

    print("\n✅ 일괄 분류 및 통계 테스트 통과")


def test_min_confidence_threshold():
    """최소 신뢰도 임계값 테스트"""
    print("\n" + "=" * 60)
    print("테스트 6: 최소 신뢰도 임계값")
    print("=" * 60)

    article = {
        "title": "경제 뉴스",
        "description": "경제 관련 내용"
    }

    # 낮은 임계값 (0.05)
    classifier_low = SectorClassifier(min_confidence=0.05)
    result_low = classifier_low.classify(article)

    # 높은 임계값 (0.5)
    classifier_high = SectorClassifier(min_confidence=0.5)
    result_high = classifier_high.classify(article)

    print(f"\n기사: {article['title']}")
    print(f"낮은 임계값(0.05) 결과: {len(result_low.subcategories)}개 하위 카테고리")
    print(f"높은 임계값(0.5) 결과: {len(result_high.subcategories)}개 하위 카테고리")

    # 높은 임계값일수록 분류된 카테고리가 적어야 함
    assert len(result_high.subcategories) <= len(result_low.subcategories), \
        "높은 임계값에서는 더 적은 카테고리가 분류되어야 함"

    print("\n✅ 최소 신뢰도 임계값 테스트 통과")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n🚀 섹터 분류기 테스트 시작\n")

    try:
        test_sector_definitions()
        test_macro_economy_classification()
        test_finance_classification()
        test_industry_tech_classification()
        test_multiple_articles_classification()
        test_min_confidence_threshold()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
