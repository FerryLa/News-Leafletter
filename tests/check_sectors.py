"""
최근 저장된 기사의 섹터 정보 확인
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.db_manager import get_db
import json


def check_recent_sectors(limit=10):
    """최근 기사의 섹터 정보 확인"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    print("=" * 80)
    print(f"최근 저장된 기사 {limit}개의 섹터 정보")
    print("=" * 80)

    cursor.execute("""
        SELECT
            title,
            primary_sector,
            secondary_sector,
            subcategories,
            fetched_at
        FROM articles
        ORDER BY fetched_at DESC
        LIMIT ?
    """, (limit,))

    for i, row in enumerate(cursor.fetchall(), 1):
        title, primary, secondary, subcats, fetched = row

        # subcategories JSON 파싱
        if subcats:
            try:
                subcats = json.loads(subcats)
                subcats_str = ", ".join(subcats)
            except:
                subcats_str = subcats
        else:
            subcats_str = "없음"

        print(f"\n[{i}] {title}")
        print(f"    주요 섹터: {primary or '없음'}")
        print(f"    부 섹터: {secondary or '없음'}")
        print(f"    하위 카테고리: {subcats_str}")
        print(f"    저장 시간: {fetched}")


def check_sector_statistics():
    """섹터별 통계"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("섹터별 기사 통계")
    print("=" * 80)

    cursor.execute("""
        SELECT
            primary_sector,
            COUNT(*) as count
        FROM articles
        GROUP BY primary_sector
        ORDER BY count DESC
    """)

    total = 0
    for row in cursor.fetchall():
        sector, count = row
        total += count
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{sector:15s} : {count:5d}개")

    print(f"\n{'총계':15s} : {total:5d}개")


def check_sector_samples(sector_name, limit=5):
    """특정 섹터의 샘플 기사"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print(f"'{sector_name}' 섹터 샘플 기사 {limit}개")
    print("=" * 80)

    cursor.execute("""
        SELECT
            title,
            subcategories,
            fetched_at
        FROM articles
        WHERE primary_sector = ?
        ORDER BY fetched_at DESC
        LIMIT ?
    """, (sector_name, limit))

    rows = cursor.fetchall()
    if not rows:
        print(f"\n'{sector_name}' 섹터의 기사가 없습니다.")
        return

    for i, row in enumerate(rows, 1):
        title, subcats, fetched = row

        if subcats:
            try:
                subcats = json.loads(subcats)
                subcats_str = ", ".join(subcats)
            except:
                subcats_str = subcats
        else:
            subcats_str = "없음"

        print(f"\n[{i}] {title}")
        print(f"    카테고리: {subcats_str}")
        print(f"    저장 시간: {fetched}")


if __name__ == "__main__":
    # 최근 기사 확인
    check_recent_sectors(10)

    # 섹터별 통계
    check_sector_statistics()

    # 각 섹터별 샘플
    for sector in ["금융", "산업/기술", "거시경제", "사회정책", "문화/생활"]:
        check_sector_samples(sector, 3)
