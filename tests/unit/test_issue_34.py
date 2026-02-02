"""
Test suite for Issue #34: DB에 섹터 정보 저장
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.db_manager import DatabaseManager
import tempfile
import os


def test_sector_migration():
    """섹터 컬럼 마이그레이션 테스트"""
    print("=" * 60)
    print("테스트 1: 섹터 컬럼 마이그레이션")
    print("=" * 60)

    # 임시 DB 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    try:
        db = DatabaseManager(db_path)

        # 컬럼 확인
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}

        print(f"\narticles 테이블 컬럼:")
        for col in sorted(columns):
            print(f"  - {col}")

        assert "primary_sector" in columns, "primary_sector 컬럼이 없음"
        assert "secondary_sector" in columns, "secondary_sector 컬럼이 없음"
        assert "subcategories" in columns, "subcategories 컬럼이 없음"

        # 인덱스 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_articles_primary_sector'
        """)
        assert cursor.fetchone() is not None, "primary_sector 인덱스가 없음"

        print("\n✅ 테스트 통과!")

    finally:
        db.close()
        os.unlink(db_path)


def test_save_article_with_sector():
    """섹터 정보 포함 기사 저장 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 섹터 정보 포함 기사 저장")
    print("=" * 60)

    # 임시 DB 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    try:
        db = DatabaseManager(db_path)

        # 섹터 정보 포함 기사
        articles = [
            {
                "link": "https://example.com/news/1",
                "title": "비트코인 급등",
                "id": "news1",
                "summary": "암호화폐 시장 활성화",
                "primary_sector": "금융",
                "secondary_sector": None,
                "subcategories": ["암호화폐 규제", "증시 변동성"]
            },
            {
                "link": "https://example.com/news/2",
                "title": "AI 혁신 가속화",
                "id": "news2",
                "summary": "ChatGPT 출시",
                "primary_sector": "산업/기술",
                "secondary_sector": "거시경제",
                "subcategories": ["AI 혁신"]
            },
            {
                "link": "https://example.com/news/3",
                "title": "일반 뉴스",
                "id": "news3",
                "summary": "기타 내용"
                # 섹터 정보 없음 -> 'other'로 저장되어야 함
            }
        ]

        saved, duplicated = db.save_articles_batch(articles)
        print(f"\n저장: {saved}개, 중복: {duplicated}개")

        assert saved == 3, "3개가 저장되어야 함"

        # DB에서 조회
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, primary_sector, secondary_sector, subcategories
            FROM articles
            ORDER BY id
        """)

        print("\n[저장된 데이터]")
        for row in cursor.fetchall():
            print(f"제목: {row[0]}")
            print(f"  주요 섹터: {row[1]}")
            print(f"  부 섹터: {row[2]}")
            print(f"  하위 카테고리: {row[3]}")
            print()

        # 검증
        cursor.execute("SELECT primary_sector FROM articles WHERE article_id = 'news1'")
        assert cursor.fetchone()[0] == "금융", "news1의 섹터가 잘못됨"

        cursor.execute("SELECT primary_sector FROM articles WHERE article_id = 'news2'")
        assert cursor.fetchone()[0] == "산업/기술", "news2의 섹터가 잘못됨"

        cursor.execute("SELECT primary_sector FROM articles WHERE article_id = 'news3'")
        assert cursor.fetchone()[0] == "other", "news3의 기본값이 잘못됨"

        print("✅ 테스트 통과!")

    finally:
        db.close()
        os.unlink(db_path)


def test_sector_query():
    """섹터별 조회 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 섹터별 조회")
    print("=" * 60)

    # 임시 DB 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name

    try:
        db = DatabaseManager(db_path)

        # 다양한 섹터의 기사 저장
        articles = [
            {"link": f"https://example.com/news/{i}", "title": f"금융 뉴스 {i}",
             "id": f"finance{i}", "primary_sector": "금융"}
            for i in range(1, 6)
        ]
        articles += [
            {"link": f"https://example.com/news/tech{i}", "title": f"기술 뉴스 {i}",
             "id": f"tech{i}", "primary_sector": "산업/기술"}
            for i in range(1, 4)
        ]

        db.save_articles_batch(articles)

        # 섹터별 통계
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT primary_sector, COUNT(*) as count
            FROM articles
            GROUP BY primary_sector
            ORDER BY count DESC
        """)

        print("\n[섹터별 통계]")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}개")

        # 특정 섹터 조회
        cursor.execute("""
            SELECT title FROM articles
            WHERE primary_sector = '금융'
            ORDER BY title
        """)

        finance_articles = cursor.fetchall()
        print(f"\n[금융 섹터 기사] ({len(finance_articles)}개)")
        for article in finance_articles:
            print(f"  - {article[0]}")

        assert len(finance_articles) == 5, "금융 섹터 기사가 5개여야 함"

        print("\n✅ 테스트 통과!")

    finally:
        db.close()
        os.unlink(db_path)


def run_all_tests():
    """모든 테스트 실행"""
    print("\n🚀 Issue #34 테스트 시작\n")

    try:
        test_sector_migration()
        test_save_article_with_sector()
        test_sector_query()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        print("\nIssue #34 완료:")
        print("✓ articles 테이블에 sector 컬럼 추가")
        print("✓ 인덱스 생성 확인")
        print("✓ 기사 저장 시 섹터 자동 저장")
        print("✓ 섹터별 조회 가능")
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
