#!/usr/bin/env python3
"""이모지 리액션 피드백 기능 테스트 스크립트"""

from app.database.db_manager import get_db
import hashlib

def test_emoji_reaction_feedback():
    """이모지 리액션 피드백 저장 테스트"""
    print("=== 이모지 리액션 피드백 기능 테스트 ===\n")

    db = get_db()
    test_chat_id = 777777  # 테스트용 chat_id

    # 0. FOREIGN KEY 제약 비활성화 (테스트용)
    print("0. FOREIGN KEY 제약 비활성화...")
    conn = db._get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.commit()

    # 1. 테스트 기사 데이터
    print("\n1. 테스트 기사 데이터 준비...")
    test_articles = [
        {
            'title': '비트코인 ETF 승인 임박',
            'url': 'https://example.com/article1',
            'score': 5
        },
        {
            'title': '이더리움 업그레이드 완료',
            'url': 'https://example.com/article2',
            'score': 3
        },
        {
            'title': '밈코인 급등 후 급락',
            'url': 'https://example.com/article3',
            'score': -2
        }
    ]

    # 2. 이모지 리액션 시뮬레이션
    print("\n2. 이모지 리액션 피드백 시뮬레이션...")

    # 👍 리액션 (첫 번째 기사)
    article1_id = hashlib.md5(test_articles[0]['url'].encode()).hexdigest()
    db.add_feedback(
        chat_id=test_chat_id,
        article_id=article1_id,
        feedback_type="like",
        feedback_value=1,
        comment=""
    )
    print(f"   [LIKE] {test_articles[0]['title']}")

    # 👍 리액션 (두 번째 기사)
    article2_id = hashlib.md5(test_articles[1]['url'].encode()).hexdigest()
    db.add_feedback(
        chat_id=test_chat_id,
        article_id=article2_id,
        feedback_type="like",
        feedback_value=1,
        comment=""
    )
    print(f"   [LIKE] {test_articles[1]['title']}")

    # 👎 리액션 (세 번째 기사)
    article3_id = hashlib.md5(test_articles[2]['url'].encode()).hexdigest()
    db.add_feedback(
        chat_id=test_chat_id,
        article_id=article3_id,
        feedback_type="dislike",
        feedback_value=-1,
        comment=""
    )
    print(f"   [DISLIKE] {test_articles[2]['title']}")

    # 3. 피드백 조회
    print("\n3. 저장된 피드백 조회...")
    all_feedback = db.get_user_feedback(test_chat_id)
    print(f"   전체 피드백: {len(all_feedback)}개")

    for fb in all_feedback:
        icon = "[LIKE]" if fb['feedback_type'] == 'like' else "[DISLIKE]"
        print(f"   {icon} article_id: {fb['article_id'][:8]}...")

    # 4. 타입별 통계
    print("\n4. 타입별 통계...")
    likes = db.get_user_feedback(test_chat_id, "like")
    dislikes = db.get_user_feedback(test_chat_id, "dislike")

    print(f"   좋아요: {len(likes)}개")
    print(f"   싫어요: {len(dislikes)}개")

    # 5. 정리
    print("\n5. 테스트 데이터 정리...")
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_feedback WHERE chat_id = ?", (test_chat_id,))
    conn.commit()
    deleted_count = cursor.rowcount
    print(f"   {deleted_count}개 피드백 삭제 완료")

    print("\n[SUCCESS] Emoji reaction feedback test passed!")
    print("\n" + "=" * 60)
    print("실제 텔레그램 봇 테스트 방법:")
    print("1. python bot.py 실행")
    print("2. 텔레그램에서 봇과 대화")
    print("3. 키워드 검색 또는 /scan 실행")
    print("4. 받은 기사 메시지에 좋아요/싫어요 리액션 추가")
    print("5. /feedback 명령어로 피드백 저장 확인")
    print("=" * 60)

if __name__ == "__main__":
    test_emoji_reaction_feedback()
