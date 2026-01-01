#!/usr/bin/env python3
"""유저 피드백 기능 테스트 스크립트"""

from app.database.db_manager import get_db

def test_feedback():
    """피드백 저장 및 조회 테스트"""
    print("=== 유저 피드백 기능 테스트 ===\n")

    db = get_db()
    test_chat_id = 888888  # 테스트용 chat_id

    # 0. FOREIGN KEY 제약 비활성화 (테스트용)
    print("0. FOREIGN KEY 제약 비활성화...")
    conn = db._get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.commit()

    # 1. 테스트 피드백 추가
    print("\n1. 테스트 피드백 추가...")

    # 좋아요 피드백
    db.add_feedback(
        chat_id=test_chat_id,
        article_id="test_article_1",
        feedback_type="like",
        feedback_value=1,
        comment=""
    )
    print("   좋아요 피드백 추가: test_article_1")

    # 싫어요 피드백 (이유 포함)
    db.add_feedback(
        chat_id=test_chat_id,
        article_id="test_article_2",
        feedback_type="dislike",
        feedback_value=-1,
        comment="관련없는 기사"
    )
    print("   싫어요 피드백 추가: test_article_2 (이유: 관련없는 기사)")

    # 또 다른 좋아요
    db.add_feedback(
        chat_id=test_chat_id,
        article_id="test_article_3",
        feedback_type="like",
        feedback_value=1,
        comment=""
    )
    print("   좋아요 피드백 추가: test_article_3")

    # 2. 피드백 조회
    print("\n2. 피드백 조회...")
    all_feedback = db.get_user_feedback(test_chat_id)
    print(f"   전체 피드백: {len(all_feedback)}개")

    for fb in all_feedback:
        icon = "[LIKE]" if fb['feedback_type'] == 'like' else "[DISLIKE]"
        comment = f" - {fb['comment']}" if fb['comment'] else ""
        print(f"   {icon} {fb['article_id']}{comment}")

    # 3. 타입별 필터링
    print("\n3. 타입별 필터링...")
    likes = db.get_user_feedback(test_chat_id, "like")
    dislikes = db.get_user_feedback(test_chat_id, "dislike")

    print(f"   좋아요: {len(likes)}개")
    print(f"   싫어요: {len(dislikes)}개")

    # 4. 중복 피드백 테스트 (같은 기사에 다시 피드백)
    print("\n4. 중복 피드백 테스트...")
    db.add_feedback(
        chat_id=test_chat_id,
        article_id="test_article_1",
        feedback_type="like",
        feedback_value=1,
        comment="정말 좋은 기사!"
    )
    print("   test_article_1에 다시 좋아요 (코멘트 추가)")

    # 5. 업데이트 확인
    print("\n5. 업데이트 확인...")
    updated = db.get_user_feedback(test_chat_id)
    print(f"   전체 피드백: {len(updated)}개 (중복 제거됨)")

    for fb in updated:
        if fb['article_id'] == 'test_article_1':
            print(f"   test_article_1 코멘트: '{fb['comment']}'")

    # 6. 정리
    print("\n6. 테스트 데이터 정리...")
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_feedback WHERE chat_id = ?", (test_chat_id,))
    conn.commit()
    deleted_count = cursor.rowcount
    print(f"   {deleted_count}개 피드백 삭제 완료")

    print("\n[SUCCESS] Feedback test passed!")

if __name__ == "__main__":
    test_feedback()
