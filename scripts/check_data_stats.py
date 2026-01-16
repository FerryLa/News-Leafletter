#!/usr/bin/env python3
"""
데이터 수집 통계 확인 스크립트

전체 기사 수, 섹터별/도메인별 분포, 누락 필드 비율, 키워드 추출 완료율 등을 확인합니다.
"""

import sys
sys.path.insert(0, '.')

from app.database.db_manager import get_db
from collections import Counter
import json


def check_data_stats(source_filter: str = None):
    """데이터 통계 확인"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("📊 데이터 수집 통계")
    print("=" * 70)

    # 필터 조건
    where_clause = ""
    params = []
    if source_filter:
        where_clause = "WHERE source_name = ?"
        params = [source_filter]
        print(f"\n🔍 필터: source_name = '{source_filter}'")

    # 1. 전체 기사 수
    query = f"SELECT COUNT(*) FROM articles {where_clause}"
    cursor.execute(query, params)
    total = cursor.fetchone()[0]

    print(f"\n📈 전체 통계")
    print(f"   전체 기사: {total:,}개")

    if total == 0:
        print("\n⚠️ 데이터가 없습니다. RSS 수집을 먼저 실행하세요.")
        print("   명령어: /rss_now (텔레그램) 또는 봇 실행")
        return

    # 2. 섹터별 분포
    print(f"\n📊 섹터별 분포")
    query = f"""
        SELECT primary_sector, COUNT(*) as count
        FROM articles {where_clause}
        GROUP BY primary_sector
        ORDER BY count DESC
    """
    cursor.execute(query, params)
    sector_dist = cursor.fetchall()

    for sector, count in sector_dist[:10]:  # 상위 10개
        sector_name = sector or "미분류"
        percentage = count / total * 100
        bar = "█" * int(percentage / 2)
        print(f"   {sector_name:15s}: {count:4d}개 ({percentage:5.1f}%) {bar}")

    # 3. 도메인(언론사)별 분포
    print(f"\n📰 도메인(언론사)별 분포 (Top 10)")
    query = f"""
        SELECT source_name, COUNT(*) as count
        FROM articles {where_clause}
        GROUP BY source_name
        ORDER BY count DESC
        LIMIT 10
    """
    cursor.execute(query, params)
    source_dist = cursor.fetchall()

    for source, count in source_dist:
        source_name = source or "알 수 없음"
        percentage = count / total * 100
        print(f"   {source_name:30s}: {count:4d}개 ({percentage:5.1f}%)")

    # 4. 누락 필드 비율
    print(f"\n⚠️ 누락 필드 비율")

    fields = {
        'title': 'SELECT COUNT(*) FROM articles {} WHERE title IS NULL OR title = \'\'',
        'summary': 'SELECT COUNT(*) FROM articles {} WHERE summary IS NULL OR summary = \'\'',
        'content': 'SELECT COUNT(*) FROM articles {} WHERE content IS NULL OR content = \'\'',
        'published_at': 'SELECT COUNT(*) FROM articles {} WHERE published_at IS NULL',
        'source_name': 'SELECT COUNT(*) FROM articles {} WHERE source_name IS NULL OR source_name = \'\'',
    }

    for field, query_template in fields.items():
        query = query_template.format(where_clause)
        cursor.execute(query, params)
        null_count = cursor.fetchone()[0]
        null_percentage = null_count / total * 100
        status = "✅" if null_percentage < 10 else "⚠️" if null_percentage < 30 else "❌"
        print(f"   {status} {field:15s}: {null_count:4d}개 ({null_percentage:5.1f}%)")

    # 5. ML 관련 컬럼 완성도
    print(f"\n🤖 ML 관련 컬럼 완성도")

    # content_length
    query = f"SELECT COUNT(*) FROM articles {where_clause} AND content_length IS NOT NULL" if where_clause else "SELECT COUNT(*) FROM articles WHERE content_length IS NOT NULL"
    cursor.execute(query, params if where_clause else [])
    content_length_count = cursor.fetchone()[0]
    content_length_pct = content_length_count / total * 100

    # keyword_extracted
    query = f"SELECT COUNT(*) FROM articles {where_clause} AND keyword_extracted IS NOT NULL" if where_clause else "SELECT COUNT(*) FROM articles WHERE keyword_extracted IS NOT NULL"
    cursor.execute(query, params if where_clause else [])
    keyword_count = cursor.fetchone()[0]
    keyword_pct = keyword_count / total * 100

    # sentiment_score
    query = f"SELECT COUNT(*) FROM articles {where_clause} AND sentiment_score IS NOT NULL" if where_clause else "SELECT COUNT(*) FROM articles WHERE sentiment_score IS NOT NULL"
    cursor.execute(query, params if where_clause else [])
    sentiment_count = cursor.fetchone()[0]
    sentiment_pct = sentiment_count / total * 100

    print(f"   content_length:     {content_length_count:4d}개 ({content_length_pct:5.1f}%)")
    print(f"   keyword_extracted:  {keyword_count:4d}개 ({keyword_pct:5.1f}%)")
    print(f"   sentiment_score:    {sentiment_count:4d}개 ({sentiment_pct:5.1f}%)")

    # 6. 시간별 수집량 (최근 7일)
    print(f"\n📅 일별 수집량 (최근 7일)")
    query = f"""
        SELECT DATE(fetched_at) as date, COUNT(*) as count
        FROM articles {where_clause}
        WHERE fetched_at >= datetime('now', '-7 days')
        GROUP BY DATE(fetched_at)
        ORDER BY date DESC
    """
    cursor.execute(query, params)
    daily_dist = cursor.fetchall()

    if daily_dist:
        for date, count in daily_dist:
            print(f"   {date}: {count:4d}개")
    else:
        print("   (최근 7일 데이터 없음)")

    # 7. 평균 content_length
    query = f"SELECT AVG(content_length) FROM articles {where_clause} AND content_length IS NOT NULL" if where_clause else "SELECT AVG(content_length) FROM articles WHERE content_length IS NOT NULL"
    cursor.execute(query, params if where_clause else [])
    avg_length = cursor.fetchone()[0]

    if avg_length:
        print(f"\n📏 평균 content_length: {avg_length:,.0f}자")

    # 8. 키워드 추출 샘플
    if keyword_count > 0:
        print(f"\n🔑 키워드 추출 샘플 (최근 3개)")
        query = f"""
            SELECT title, keyword_extracted
            FROM articles {where_clause}
            WHERE keyword_extracted IS NOT NULL
            ORDER BY fetched_at DESC
            LIMIT 3
        """ if where_clause else """
            SELECT title, keyword_extracted
            FROM articles
            WHERE keyword_extracted IS NOT NULL
            ORDER BY fetched_at DESC
            LIMIT 3
        """
        cursor.execute(query, params if where_clause else [])
        samples = cursor.fetchall()

        for i, (title, kw_json) in enumerate(samples, 1):
            try:
                kw_data = json.loads(kw_json)
                keywords = kw_data.get('keywords', [])
                print(f"\n   {i}. {title[:50]}...")
                print(f"      키워드: {', '.join(keywords[:5])}")
            except:
                print(f"\n   {i}. {title[:50]}...")
                print(f"      키워드: (파싱 실패)")

    # 9. 품질 점수 계산
    print(f"\n" + "=" * 70)
    print(f"🎯 데이터 품질 점수")
    print("=" * 70)

    quality_score = 0

    # 기사 수 (최대 20점)
    if total >= 1000:
        quality_score += 20
    elif total >= 500:
        quality_score += 15
    elif total >= 100:
        quality_score += 10
    else:
        quality_score += max(0, total // 10)

    # content 누락률 (최대 20점)
    query = f"SELECT COUNT(*) FROM articles {where_clause} WHERE content IS NOT NULL AND content != ''"
    cursor.execute(query, params)
    content_exists = cursor.fetchone()[0]
    content_ratio = content_exists / total if total > 0 else 0
    quality_score += int(content_ratio * 20)

    # content_length 완성도 (최대 20점)
    quality_score += int(content_length_pct / 100 * 20)

    # keyword_extracted 완성도 (최대 20점)
    quality_score += int(keyword_pct / 100 * 20)

    # 섹터 분류 완성도 (최대 20점)
    query = f"SELECT COUNT(*) FROM articles {where_clause} WHERE primary_sector IS NOT NULL AND primary_sector != '' AND primary_sector != 'other'"
    cursor.execute(query, params)
    sector_classified = cursor.fetchone()[0]
    sector_ratio = sector_classified / total if total > 0 else 0
    quality_score += int(sector_ratio * 20)

    print(f"\n   총점: {quality_score}/100점")

    if quality_score >= 90:
        grade = "S (최고 품질)"
    elif quality_score >= 80:
        grade = "A (우수)"
    elif quality_score >= 70:
        grade = "B (양호)"
    elif quality_score >= 60:
        grade = "C (보통)"
    else:
        grade = "D (개선 필요)"

    print(f"   등급: {grade}")

    print("\n" + "=" * 70)
    print("✅ 통계 확인 완료!")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="데이터 수집 통계 확인")
    parser.add_argument("--source", type=str, help="특정 source_name 필터")

    args = parser.parse_args()

    try:
        check_data_stats(source_filter=args.source)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
