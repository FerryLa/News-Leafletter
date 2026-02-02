from app.database.db_manager import get_db

db = get_db()
conn = db._get_connection()
cursor = conn.cursor()

# rss_cache 테이블 스키마
cursor.execute("PRAGMA table_info(rss_cache)")
columns = cursor.fetchall()
print("rss_cache 테이블 구조:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 샘플 데이터
cursor.execute("SELECT * FROM rss_cache LIMIT 3")
samples = cursor.fetchall()
print(f"\n샘플 데이터 ({len(samples)}개):")
for sample in samples:
    print(f"  {sample}")

