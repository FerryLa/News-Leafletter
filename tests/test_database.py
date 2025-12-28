#!/usr/bin/env python3
"""
SQLite 데이터베이스 시스템 테스트
이슈 #32 검증용
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_database_creation():
    """데이터베이스 생성 및 스키마 테스트"""
    print("=" * 60)
    print("테스트 1: 데이터베이스 생성 및 스키마")
    print("=" * 60)
    
    from app.database.db_manager import DatabaseManager
    
    # 테스트용 DB 생성
    test_db_path = project_root / "data" / "test_news.db"
    if test_db_path.exists():
        test_db_path.unlink()
    
    db = DatabaseManager(test_db_path)
    
    # 테이블 존재 확인
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = [
        'articles',
        'news_history',
        'rss_cache',
        'schema_version',
        'settings',
        'user_feedback',
        'user_keywords'
    ]
    
    print(f"✅ 생성된 테이블: {tables}")
    
    for table in expected_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} (누락됨!)")
    
    db.close()
    print()


def test_keyword_operations():
    """키워드 CRUD 테스트"""
    print("=" * 60)
    print("테스트 2: 키워드 CRUD 작업")
    print("=" * 60)
    
    from app.database.db_manager import DatabaseManager
    
    test_db_path = project_root / "data" / "test_news.db"
    db = DatabaseManager(test_db_path)
    
    chat_id = 12345
    
    # 1. 추가
    print("1️⃣ 키워드 추가 테스트")
    db.add_keyword(chat_id, "비트코인")
    db.add_keyword(chat_id, "이더리움")
    db.add_keyword(chat_id, "-밈코인")
    
    keywords = db.get_keywords(chat_id)
    print(f"  ✅ 추가된 키워드: {keywords}")
    assert len(keywords) == 3, "키워드 개수 오류"
    
    # 2. 중복 추가 방지
    print("2️⃣ 중복 추가 방지 테스트")
    result = db.add_keyword(chat_id, "비트코인")
    assert result == False, "중복 추가가 방지되지 않음"
    print("  ✅ 중복 추가 방지 성공")
    
    # 3. 삭제
    print("3️⃣ 키워드 삭제 테스트")
    db.remove_keyword(chat_id, "-밈코인")
    keywords = db.get_keywords(chat_id)
    print(f"  ✅ 삭제 후 키워드: {keywords}")
    assert len(keywords) == 2, "삭제 오류"
    
    # 4. 전체 삭제
    print("4️⃣ 전체 키워드 삭제 테스트")
    count = db.clear_keywords(chat_id)
    print(f"  ✅ 삭제된 키워드 수: {count}")
    assert count == 2, "전체 삭제 오류"
    
    db.close()
    print()


def test_rss_cache():
    """RSS 캐시 테스트"""
    print("=" * 60)
    print("테스트 3: RSS 캐시 작업")
    print("=" * 60)
    
    from app.database.db_manager import DatabaseManager
    
    test_db_path = project_root / "data" / "test_news.db"
    db = DatabaseManager(test_db_path)
    
    # 1. 기사 등록
    print("1️⃣ 기사 캐시 등록")
    article_id = "test-article-123"
    db.mark_article_seen(article_id, "https://example.com", "테스트 기사")
    
    is_seen = db.is_article_seen(article_id)
    assert is_seen == True, "캐시 등록 실패"
    print(f"  ✅ 기사 등록 확인: {is_seen}")
    
    # 2. 중복 체크
    print("2️⃣ 중복 체크")
    is_seen_again = db.is_article_seen(article_id)
    assert is_seen_again == True, "중복 체크 실패"
    print(f"  ✅ 중복 체크 성공")
    
    # 3. 통계
    print("3️⃣ 캐시 통계")
    stats = db.get_cache_stats()
    print(f"  ✅ 통계: {stats}")
    
    db.close()
    print()


def test_storage_compatibility():
    """기존 storage.py API 호환성 테스트"""
    print("=" * 60)
    print("테스트 4: storage.py API 호환성")
    print("=" * 60)
    
    from app.storage import get_keywords, add_keyword, remove_keyword
    
    chat_id = 67890
    
    # 1. 추가
    print("1️⃣ add_keyword() 테스트")
    keywords = add_keyword(chat_id, "ETF")
    print(f"  ✅ 추가 후: {keywords}")
    
    # 2. 조회
    print("2️⃣ get_keywords() 테스트")
    keywords = get_keywords(chat_id)
    print(f"  ✅ 조회 결과: {keywords}")
    assert "ETF" in keywords, "조회 실패"
    
    # 3. 삭제
    print("3️⃣ remove_keyword() 테스트")
    keywords = remove_keyword(chat_id, "ETF")
    print(f"  ✅ 삭제 후: {keywords}")
    assert "ETF" not in keywords, "삭제 실패"
    
    print()


def test_migration():
    """마이그레이션 테스트 (JSON → SQLite)"""
    print("=" * 60)
    print("테스트 5: JSON → SQLite 마이그레이션")
    print("=" * 60)
    
    # 테스트용 JSON 파일 생성
    import json
    data_dir = project_root / "data"
    
    # 1. 테스트용 watchlist.json 생성
    test_watchlist = {
        "111": ["비트코인", "이더리움"],
        "222": ["-밈코인", "ETF"]
    }
    
    watchlist_path = data_dir / "watchlist_test.json"
    with open(watchlist_path, "w", encoding="utf-8") as f:
        json.dump(test_watchlist, f, ensure_ascii=False, indent=2)
    
    print("1️⃣ 테스트 JSON 파일 생성 완료")
    
    # 2. 마이그레이션 실행 (수동 테스트 필요)
    print("2️⃣ 마이그레이션 실행은 수동으로 진행:")
    print("   $ python app/database/migration.py")
    
    print()


def test_articles_table():
    """기사 저장소 테스트"""
    print("=" * 60)
    print("테스트 6: 기사 저장소 (articles 테이블)")
    print("=" * 60)
    
    from app.database.db_manager import DatabaseManager
    
    test_db_path = project_root / "data" / "test_news.db"
    db = DatabaseManager(test_db_path)
    
    # 1. 기사 저장
    print("1️⃣ 기사 저장 테스트")
    success = db.save_article(
        article_id="test-btc-news-001",
        title="비트코인 10만 달러 돌파",
        url="https://example.com/btc-100k",
        summary="비트코인이 역사상 처음으로 10만 달러를 돌파했습니다.",
        source_name="Crypto News",
        category="cryptocurrency"
    )
    assert success == True, "기사 저장 실패"
    print("  ✅ 기사 저장 성공")
    
    # 2. 기사 조회
    print("2️⃣ 기사 조회 테스트")
    article = db.get_article("test-btc-news-001")
    assert article is not None, "기사 조회 실패"
    assert article["title"] == "비트코인 10만 달러 돌파", "제목 불일치"
    print(f"  ✅ 조회 성공: {article['title']}")
    
    # 3. 중복 저장 방지
    print("3️⃣ 중복 저장 방지 테스트")
    success = db.save_article(
        article_id="test-btc-news-001",
        title="다른 제목",
        url="https://example.com/btc-100k"
    )
    assert success == False, "중복 저장이 방지되지 않음"
    print("  ✅ 중복 저장 방지 성공")
    
    # 4. 검색
    print("4️⃣ 기사 검색 테스트")
    results = db.search_articles(keyword="비트코인", limit=10)
    assert len(results) > 0, "검색 결과 없음"
    print(f"  ✅ 검색 결과: {len(results)}개")
    
    db.close()
    print()


def test_user_feedback():
    """유저 피드백 테스트"""
    print("=" * 60)
    print("테스트 7: 유저 피드백 (user_feedback 테이블)")
    print("=" * 60)
    
    from app.database.db_manager import DatabaseManager
    
    test_db_path = project_root / "data" / "test_news.db"
    db = DatabaseManager(test_db_path)
    
    chat_id = 99999
    article_id = "test-btc-news-001"
    
    # 1. 좋아요 추가
    print("1️⃣ 좋아요 피드백 추가")
    success = db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type="like",
        feedback_value=1
    )
    assert success == True, "피드백 추가 실패"
    print("  ✅ 좋아요 추가 성공")
    
    # 2. 북마크 추가
    print("2️⃣ 북마크 피드백 추가")
    db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type="bookmark",
        feedback_value=1,
        comment="나중에 읽기"
    )
    print("  ✅ 북마크 추가 성공")
    
    # 3. 별점 추가
    print("3️⃣ 별점 피드백 추가")
    db.add_feedback(
        chat_id=chat_id,
        article_id=article_id,
        feedback_type="rating",
        feedback_value=5,
        comment="매우 유용한 기사"
    )
    print("  ✅ 별점 추가 성공")
    
    # 4. 유저 피드백 조회
    print("4️⃣ 유저 피드백 조회")
    feedbacks = db.get_user_feedback(chat_id)
    assert len(feedbacks) == 3, f"피드백 개수 오류: {len(feedbacks)}"
    print(f"  ✅ 피드백 조회 성공: {len(feedbacks)}개")
    
    # 5. 특정 타입만 조회
    print("5️⃣ 북마크만 조회")
    bookmarks = db.get_user_feedback(chat_id, feedback_type="bookmark")
    assert len(bookmarks) == 1, "북마크 조회 실패"
    print(f"  ✅ 북마크 조회 성공: {len(bookmarks)}개")
    
    # 6. 기사별 피드백 통계
    print("6️⃣ 기사 피드백 통계")
    stats = db.get_article_feedback_stats(article_id)
    assert "like" in stats, "통계에 좋아요 없음"
    assert "rating" in stats, "통계에 별점 없음"
    print(f"  ✅ 통계 조회 성공: {stats}")
    
    db.close()
    print()


def cleanup_test_db():
    """테스트 DB 삭제"""
    test_db_path = project_root / "data" / "test_news.db"
    if test_db_path.exists():
        test_db_path.unlink()
        print("🧹 테스트 DB 삭제 완료")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n🚀 SQLite 데이터베이스 시스템 테스트 시작\n")
    
    try:
        test_database_creation()
        test_keyword_operations()
        test_rss_cache()
        test_storage_compatibility()
        test_migration()
        test_articles_table()
        test_user_feedback()
        
        print("=" * 60)
        print("🎉 모든 테스트 통과!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 테스트 DB 정리 여부 확인
        cleanup = input("\n🧹 테스트 DB를 삭제하시겠습니까? (yes/no): ")
        if cleanup.lower() == "yes":
            cleanup_test_db()


if __name__ == "__main__":
    run_all_tests()
