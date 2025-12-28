# tests/test_issue_22.py
"""
Issue #22: RSS 중복 필터링 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.db_manager import get_db


def test_issue_22():
    """Issue #22 기능 테스트"""
    
    # 테스트용 DB 생성
    test_db_path = project_root / "data" / "test_issue22.db"
    
    # 기존 테스트 DB 삭제 (깨끗한 상태로 시작)
    if test_db_path.exists():
        test_db_path.unlink()
    
    print("🚀 Issue #22 테스트 시작\n")
    
    # DB 초기화 (마이그레이션 자동 실행됨)
    db = get_db(test_db_path)
    
    # ==================== 테스트 1: 중복 체크 ====================
    print("=== 테스트 1: 중복 체크 ===")
    link1 = "https://example.com/news/1"
    is_dup = db.is_duplicate_by_link(link1)
    print(f"중복 확인 (저장 전): {is_dup}")
    assert is_dup == False, "새 링크는 중복이 아니어야 함"
    print("✅ 통과\n")
    
    # ==================== 테스트 2: 배치 저장 ====================
    print("=== 테스트 2: 배치 저장 ===")
    articles = [
        {"link": link1, "title": "News 1", "id": "news1", "summary": "Summary 1"},
        {"link": "https://example.com/news/2", "title": "News 2", "id": "news2"},
        {"link": link1, "title": "News 1 Duplicate", "id": "news1"},  # 중복
    ]
    
    saved, duplicated = db.save_articles_batch(articles)
    print(f"저장: {saved}개, 중복: {duplicated}개")
    assert saved == 2, "2개가 저장되어야 함"
    assert duplicated == 1, "1개가 중복이어야 함"
    print("✅ 통과\n")
    
    # ==================== 테스트 3: 중복 재확인 ====================
    print("=== 테스트 3: 중복 재확인 ===")
    is_dup_after = db.is_duplicate_by_link(link1)
    print(f"중복 확인 (저장 후): {is_dup_after}")
    assert is_dup_after == True, "저장된 링크는 중복이어야 함"
    print("✅ 통과\n")
    
    # ==================== 테스트 4: 배치 중복 체크 ====================
    print("=== 테스트 4: 배치 중복 체크 ===")
    test_links = [
        "https://example.com/news/1",  # 중복 (이미 저장됨)
        "https://example.com/news/2",  # 중복 (이미 저장됨)
        "https://example.com/news/3",  # 새 링크
        "https://example.com/news/4",  # 새 링크
    ]
    
    duplicate_links = db.get_duplicate_links(test_links)
    print(f"중복 링크: {duplicate_links}")
    assert len(duplicate_links) == 2, "2개가 중복이어야 함"
    assert "https://example.com/news/1" in duplicate_links
    assert "https://example.com/news/2" in duplicate_links
    print("✅ 통과\n")
    
    # ==================== 테스트 5: 통계 확인 ====================
    print("=== 테스트 5: 통계 확인 ===")
    stats = db.get_articles_statistics()
    print(f"전체 기사: {stats['total_articles']}개")
    print(f"오늘 저장: {stats['articles_today']}개")
    assert stats['total_articles'] == 2, "총 2개 저장되어야 함"
    assert stats['articles_today'] == 2, "오늘 2개 저장되어야 함"
    print("✅ 통과\n")
    
    # ==================== 테스트 6: 최근 기사 조회 ====================
    print("=== 테스트 6: 최근 기사 조회 ===")
    recent = db.get_recent_articles(limit=10)
    print(f"최근 기사 수: {len(recent)}")
    assert len(recent) == 2, "2개가 조회되어야 함"
    print(f"첫 번째 기사: {recent[0]['title']}")
    print("✅ 통과\n")
    
    # ==================== 테스트 7: Issue #22 핵심 시나리오 ====================
    print("=== 테스트 7: Issue #22 핵심 시나리오 ===")
    print("동일한 기사를 두 번 수집했을 때 한 번만 저장되는지 확인")
    
    # 같은 기사를 여러 번 수집 (RSS에서 흔한 상황)
    rss_articles = [
        {"link": "https://news.com/article-100", "title": "Breaking News", "id": "100"},
        {"link": "https://news.com/article-100", "title": "Breaking News", "id": "100"},  # 중복
        {"link": "https://news.com/article-100", "title": "Breaking News", "id": "100"},  # 중복
    ]
    
    saved2, dup2 = db.save_articles_batch(rss_articles)
    print(f"저장: {saved2}개, 중복: {dup2}개")
    assert saved2 == 1, "같은 링크는 1번만 저장되어야 함"
    assert dup2 == 2, "나머지 2개는 중복으로 제외되어야 함"
    print("✅ 통과 - Issue #22 요구사항 충족!\n")
    
    # 정리
    db.close()
    
    print("=" * 50)
    print("🎉 모든 테스트 통과!")
    print("=" * 50)


if __name__ == "__main__":
    test_issue_22()