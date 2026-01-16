#!/usr/bin/env python3
"""
마일스톤 4 - Day 1: ML 학습용 컬럼 추가 마이그레이션

추가 컬럼:
- content_length: 본문 길이 (INTEGER)
- keyword_extracted: 자동 추출 키워드 (JSON TEXT)
- sentiment_score: 감성 분석 점수 (REAL, 선택 사항)
"""

import sys
sys.path.insert(0, '.')

from app.database.db_manager import get_db
import json


def migrate_ml_columns():
    """ML 학습용 컬럼 추가"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("🚀 ML 학습용 컬럼 마이그레이션 시작")
    print("=" * 60)

    # 1. 기존 컬럼 확인
    cursor.execute("PRAGMA table_info(articles)")
    columns = {row[1] for row in cursor.fetchall()}

    print(f"\n✅ 현재 컬럼 수: {len(columns)}")
    print(f"   컬럼 목록: {', '.join(sorted(columns))}")

    # 2. content_length 컬럼 추가
    if 'content_length' not in columns:
        print("\n📊 content_length 컬럼 추가 중...")
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN content_length INTEGER")
            conn.commit()
            print("   ✅ content_length 컬럼 추가 완료")
        except Exception as e:
            print(f"   ⚠️ content_length 추가 실패: {e}")
    else:
        print("\n✅ content_length 컬럼 이미 존재")

    # 3. keyword_extracted 컬럼 추가
    if 'keyword_extracted' not in columns:
        print("\n🔑 keyword_extracted 컬럼 추가 중...")
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN keyword_extracted TEXT")
            conn.commit()
            print("   ✅ keyword_extracted 컬럼 추가 완료")
        except Exception as e:
            print(f"   ⚠️ keyword_extracted 추가 실패: {e}")
    else:
        print("\n✅ keyword_extracted 컬럼 이미 존재")

    # 4. sentiment_score 컬럼 추가 (선택 사항)
    if 'sentiment_score' not in columns:
        print("\n😊 sentiment_score 컬럼 추가 중...")
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_score REAL")
            conn.commit()
            print("   ✅ sentiment_score 컬럼 추가 완료")
        except Exception as e:
            print(f"   ⚠️ sentiment_score 추가 실패: {e}")
    else:
        print("\n✅ sentiment_score 컬럼 이미 존재")

    # 5. 기존 데이터 content_length 계산
    print("\n📐 기존 데이터 content_length 계산 중...")
    cursor.execute("""
        SELECT article_id, content
        FROM articles
        WHERE content IS NOT NULL AND content_length IS NULL
    """)
    rows = cursor.fetchall()

    if rows:
        print(f"   처리할 기사: {len(rows)}개")
        updated = 0
        for article_id, content in rows:
            length = len(content) if content else 0
            cursor.execute(
                "UPDATE articles SET content_length = ? WHERE article_id = ?",
                (length, article_id)
            )
            updated += 1

        conn.commit()
        print(f"   ✅ {updated}개 기사 content_length 업데이트 완료")
    else:
        print("   ℹ️ 업데이트할 기사 없음")

    # 6. 최종 확인
    print("\n" + "=" * 60)
    print("📊 마이그레이션 완료 - 최종 상태")
    print("=" * 60)

    cursor.execute("PRAGMA table_info(articles)")
    final_columns = [row[1] for row in cursor.fetchall()]

    print(f"\n✅ 최종 컬럼 수: {len(final_columns)}")

    # ML 관련 컬럼 확인
    ml_columns = ['content_length', 'keyword_extracted', 'sentiment_score']
    print(f"\n🤖 ML 관련 컬럼:")
    for col in ml_columns:
        status = "✅" if col in final_columns else "❌"
        print(f"   {status} {col}")

    # 통계
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_length IS NOT NULL")
    with_length = cursor.fetchone()[0]

    print(f"\n📈 데이터 통계:")
    print(f"   전체 기사: {total}개")
    print(f"   content_length 있음: {with_length}개")

    if total > 0:
        print(f"   완성도: {with_length/total*100:.1f}%")

    print("\n✅ 마이그레이션 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        migrate_ml_columns()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
