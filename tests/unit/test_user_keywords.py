from app.database.db_manager import get_db

# DB에서 실제 사용자 목록 확인
db = get_db()
conn = db._get_connection()
cursor = conn.cursor()

# 사용자 키워드 확인
cursor.execute("SELECT DISTINCT chat_id FROM user_keywords LIMIT 10")
users = cursor.fetchall()

print("등록된 사용자:")
for user in users:
    chat_id = user[0]
    keywords = db.get_keywords_with_scores(chat_id)
    print(f"\n  Chat ID: {chat_id}")
    print(f"  키워드: {keywords}")

# 최근 피드백 확인
cursor.execute("SELECT COUNT(*) FROM user_feedback")
feedback_count = cursor.fetchone()[0]
print(f"\n전체 피드백 수: {feedback_count}")

# RSS 캐시 확인
cursor.execute("SELECT COUNT(*) FROM rss_cache")
cache_count = cursor.fetchone()[0]
print(f"RSS 캐시 수: {cache_count}")

