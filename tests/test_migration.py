#!/usr/bin/env python3
"""DB 마이그레이션 테스트 스크립트"""

from app.database.db_manager import get_db

def test_migration():
    """키워드 점수 컬럼 마이그레이션 테스트"""
    print("=== DB 마이그레이션 테스트 ===\n")

    db = get_db()

    # 1. 기존 데이터 확인
    print("1. 현재 DB 구조 확인...")
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(user_keywords)")
    columns = cursor.fetchall()

    print("   user_keywords 테이블 컬럼:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")

    # 2. 테스트 데이터 추가
    print("\n2. 테스트 데이터 추가...")
    test_chat_id = 999999  # 테스트용 chat_id

    # 기존 데이터 삭제
    db.clear_keywords(test_chat_id)

    # 새로운 방식으로 추가
    db.add_keyword(test_chat_id, "비트코인", 2)
    db.add_keyword(test_chat_id, "기재정정", 3)
    db.add_keyword(test_chat_id, "밈코인", -2)

    print("   추가 완료: 비트코인 +2, 기재정정 +3, 밈코인 -2")

    # 3. 결과 확인
    print("\n3. 결과 확인...")
    keywords = db.get_keywords_with_scores(test_chat_id)

    print(f"   저장된 키워드 ({len(keywords)}):")
    for kw, score in keywords.items():
        print(f"   - {kw}: {score:+}점")

    # 4. 업데이트 테스트
    print("\n4. 업데이트 테스트...")
    db.add_keyword(test_chat_id, "비트코인", 5)
    print("   비트코인 점수를 +5로 업데이트")

    keywords = db.get_keywords_with_scores(test_chat_id)
    print(f"   업데이트 후 비트코인 점수: {keywords.get('비트코인', 0):+}점")

    # 5. 정리
    print("\n5. 테스트 데이터 정리...")
    db.clear_keywords(test_chat_id)
    print("   정리 완료")

    print("\n[SUCCESS] Migration test passed!")

if __name__ == "__main__":
    test_migration()
