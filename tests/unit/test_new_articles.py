from app.database.db_manager import get_db
import hashlib

# RSS 캐시를 임시로 클리어하여 테스트
db = get_db()
conn = db._get_connection()
cursor = conn.cursor()

# 캐시된 기사 중 일부 삭제 (최근 1개만 남기고 나머지 삭제)
cursor.execute("SELECT article_id FROM rss_cache ORDER BY first_seen DESC LIMIT 1 OFFSET 1")
to_delete = cursor.fetchall()

if to_delete:
    print(f"캐시에서 {len(to_delete)}개 기사 삭제...")
    for row in to_delete[:100]:  # 최대 100개만 삭제
        cursor.execute("DELETE FROM rss_cache WHERE article_id = ?", (row[0],))
    conn.commit()
    print("완료!")
else:
    print("삭제할 캐시가 없습니다.")

# 현재 캐시 상태
cursor.execute("SELECT COUNT(*) FROM rss_cache")
count = cursor.fetchone()[0]
print(f"\n현재 캐시: {count}개")

