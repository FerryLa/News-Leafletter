#!/usr/bin/env python3
"""
유저 피드백 조회 스크립트
사용법: python view_feedback.py [chat_id]
"""

import sys
sys.path.insert(0, '.')

from app.database.db_manager import get_db
from datetime import datetime


def view_feedback(chat_id: int = None):
    """피드백 조회 및 통계 출력"""
    db = get_db()

    print("=" * 60)
    print("📊 유저 피드백 조회")
    print("=" * 60)

    if chat_id:
        print(f"\n🔍 Chat ID: {chat_id}")
        view_user_feedback(db, chat_id)
    else:
        # 모든 사용자의 피드백 통계
        view_all_feedback(db)


def view_user_feedback(db, chat_id: int):
    """특정 사용자의 피드백 조회"""

    # 전체 피드백 조회
    all_feedback = db.get_user_feedback(chat_id)

    if not all_feedback:
        print("\n❌ 피드백이 없습니다.")
        return

    print(f"\n📌 전체 피드백: {len(all_feedback)}개")
    print("-" * 60)

    # 타입별 분류
    likes = [fb for fb in all_feedback if fb['feedback_type'] == 'like']
    dislikes = [fb for fb in all_feedback if fb['feedback_type'] == 'dislike']

    print(f"\n✅ 좋아요: {len(likes)}개")
    print(f"❌ 싫어요: {len(dislikes)}개")

    # 최근 피드백 10개 출력
    print("\n" + "=" * 60)
    print("📋 최근 피드백 (최대 10개)")
    print("=" * 60)

    for i, fb in enumerate(all_feedback[:10], 1):
        icon = "👍" if fb['feedback_type'] == 'like' else "👎"
        created_at = fb['created_at']
        article_id = fb['article_id']
        comment = fb.get('comment', '')

        print(f"\n{i}. {icon} [{fb['feedback_type'].upper()}]")
        print(f"   Article ID: {article_id}")
        print(f"   생성 시간: {created_at}")
        if comment:
            print(f"   코멘트: {comment}")


def view_all_feedback(db):
    """모든 사용자의 피드백 통계"""

    conn = db._get_connection()
    cursor = conn.cursor()

    # 전체 통계
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN feedback_type = 'like' THEN 1 END) as likes,
            COUNT(CASE WHEN feedback_type = 'dislike' THEN 1 END) as dislikes
        FROM user_feedback
    """)

    row = cursor.fetchone()
    total = row[0]
    likes = row[1]
    dislikes = row[2]

    if total == 0:
        print("\n❌ 저장된 피드백이 없습니다.")
        return

    print(f"\n📊 전체 통계")
    print("-" * 60)
    print(f"  총 피드백: {total}개")
    print(f"  👍 좋아요: {likes}개 ({likes/total*100:.1f}%)")
    print(f"  👎 싫어요: {dislikes}개 ({dislikes/total*100:.1f}%)")

    # 사용자별 통계
    cursor.execute("""
        SELECT
            chat_id,
            COUNT(*) as total,
            COUNT(CASE WHEN feedback_type = 'like' THEN 1 END) as likes,
            COUNT(CASE WHEN feedback_type = 'dislike' THEN 1 END) as dislikes
        FROM user_feedback
        GROUP BY chat_id
        ORDER BY total DESC
    """)

    users = cursor.fetchall()

    print(f"\n👥 사용자별 통계 ({len(users)}명)")
    print("=" * 60)

    for i, (chat_id, total, likes, dislikes) in enumerate(users, 1):
        print(f"\n{i}. Chat ID: {chat_id}")
        print(f"   총 피드백: {total}개 (👍 {likes} / 👎 {dislikes})")

    # 최근 피드백 10개
    print("\n" + "=" * 60)
    print("📋 최근 전체 피드백 (최대 10개)")
    print("=" * 60)

    cursor.execute("""
        SELECT chat_id, article_id, feedback_type, created_at, comment
        FROM user_feedback
        ORDER BY created_at DESC
        LIMIT 10
    """)

    recent = cursor.fetchall()

    for i, (chat_id, article_id, feedback_type, created_at, comment) in enumerate(recent, 1):
        icon = "👍" if feedback_type == 'like' else "👎"
        print(f"\n{i}. {icon} Chat ID: {chat_id}")
        print(f"   Article ID: {article_id[:16]}...")
        print(f"   생성 시간: {created_at}")
        if comment:
            print(f"   코멘트: {comment}")


def export_feedback_csv(chat_id: int = None, output_file: str = "feedback_export.csv"):
    """피드백을 CSV로 내보내기"""
    import csv

    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    if chat_id:
        cursor.execute("""
            SELECT chat_id, article_id, feedback_type, feedback_value, comment, created_at
            FROM user_feedback
            WHERE chat_id = ?
            ORDER BY created_at DESC
        """, (chat_id,))
    else:
        cursor.execute("""
            SELECT chat_id, article_id, feedback_type, feedback_value, comment, created_at
            FROM user_feedback
            ORDER BY created_at DESC
        """)

    rows = cursor.fetchall()

    if not rows:
        print("\n❌ 내보낼 피드백이 없습니다.")
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Chat ID', 'Article ID', 'Type', 'Value', 'Comment', 'Created At'])
        writer.writerows(rows)

    print(f"\n✅ {len(rows)}개 피드백을 '{output_file}'로 내보냈습니다.")


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        try:
            chat_id = int(sys.argv[1])

            # CSV 내보내기 옵션
            if len(sys.argv) > 2 and sys.argv[2] == '--export':
                output_file = sys.argv[3] if len(sys.argv) > 3 else f"feedback_{chat_id}.csv"
                export_feedback_csv(chat_id, output_file)
            else:
                view_feedback(chat_id)

        except ValueError:
            print("❌ 올바른 chat_id를 입력하세요.")
            print("\n사용법:")
            print("  python view_feedback.py                     # 전체 통계")
            print("  python view_feedback.py [chat_id]           # 특정 사용자 조회")
            print("  python view_feedback.py [chat_id] --export  # CSV로 내보내기")
    else:
        view_feedback()


if __name__ == "__main__":
    main()
