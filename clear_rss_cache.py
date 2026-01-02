from app.database.db_manager import get_db

db = get_db()
conn = db._get_connection()

# RSS 캐시 완전 삭제 (테스트용)
print("RSS 캐시를 삭제합니다...")
conn.execute("DELETE FROM rss_cache")
conn.commit()

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM rss_cache")
count = cursor.fetchone()[0]
print(f"현재 캐시: {count}개")
print("\n이제 /rss_now를 실행하면 새 기사가 나타날 것입니다.")

