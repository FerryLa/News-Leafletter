from app.database.db_manager import get_db
from datetime import datetime, timedelta, timezone

db = get_db()
conn = db._get_connection()
cursor = conn.cursor()

# 전체 캐시
cursor.execute("SELECT COUNT(*) FROM rss_cache")
total_count = cursor.fetchone()[0]
print(f"전체 캐시: {total_count}개")

# 최근 캐시 (first_seen 기준)
yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
cursor.execute(
    "SELECT COUNT(*) FROM rss_cache WHERE first_seen > ?",
    (yesterday.isoformat(),)
)
recent_count = cursor.fetchone()[0]
print(f"최근 24시간 내 캐시: {recent_count}개")

# 가장 최근 캐시 5개
cursor.execute("SELECT article_id, title, first_seen FROM rss_cache ORDER BY first_seen DESC LIMIT 5")
recent = cursor.fetchall()
print(f"\n가장 최근 캐시 5개:")
for article_id, title, first_seen in recent:
    print(f"  {first_seen}: {title[:50]}...")

