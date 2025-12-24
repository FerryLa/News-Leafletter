# test_rss_cache.py - RSS 캐시 시스템 테스트 및 사용 예시

"""
이슈 #21-2 캐시 및 중복 제거 사용 가이드
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# tests 폴더에서 실행해도 app 모듈을 찾을 수 있도록
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.rss.rss_fetcher import (
    fetch_new_articles,
    print_fetch_statistics,
    get_cache_info,
    clear_cache,
)


def example_1_basic_usage():
    """기본 사용법 (통계 없이)"""
    print("=" * 60)
    print("예시 1: 기본 사용법")
    print("=" * 60)
    
    # 기존 방식과 동일 (호환성 유지)
    articles, _ = fetch_new_articles()
    
    print(f"✅ 새로 발견된 기사: {len(articles)}개")
    
    if articles:
        print("\n첫 번째 기사:")
        print(f"  제목: {articles[0]['title']}")
        print(f"  링크: {articles[0]['link']}")


def example_2_with_statistics():
    """통계 정보와 함께 사용"""
    print("\n" + "=" * 60)
    print("예시 2: 통계 정보 활용")
    print("=" * 60)
    
    # return_stats=True로 통계 받기
    articles, stats = fetch_new_articles(return_stats=True)
    
    # 통계 출력
    print_fetch_statistics(stats)
    
    # 중복 제거 효율 계산
    if stats.total_entries > 0:
        efficiency = (stats.duplicate_articles / stats.total_entries) * 100
        print(f"📈 중복 제거 효율: {efficiency:.1f}%")


def example_3_cache_management():
    """캐시 관리"""
    print("\n" + "=" * 60)
    print("예시 3: 캐시 정보 조회")
    print("=" * 60)
    
    # 캐시 정보 조회
    cache_info = get_cache_info()
    
    print("📦 캐시 현황:")
    print(f"  - 총 캐시된 ID: {cache_info['total_cached_ids']}개")
    print(f"  - 타임스탬프 있는 항목: {cache_info['with_timestamp']}개")
    print(f"  - 만료 예정 항목: {cache_info['expired_items']}개")
    print(f"  - 캐시 파일 크기: {cache_info['cache_file_size_kb']:.2f} KB")
    print(f"  - 캐시 만료 기간: {cache_info['cache_expiry_days']}일")
    print(f"  - 최대 저장 ID: {cache_info['max_stored_ids']}개")


def example_4_memory_limit():
    """메모리 제한 사용"""
    print("\n" + "=" * 60)
    print("예시 4: 메모리 제한 설정")
    print("=" * 60)
    
    # 최대 100개만 가져오기 (메모리 절약)
    articles, stats = fetch_new_articles(
        max_articles=100,
        return_stats=True
    )
    
    print(f"✅ 수집된 기사: {len(articles)}개 (최대 100개 제한)")
    print(f"⚠️ 무시된 기사: {stats.new_articles - len(articles)}개")


def example_5_cache_reset():
    """캐시 초기화 (주의: 데이터 삭제됨!)"""
    print("\n" + "=" * 60)
    print("예시 5: 캐시 초기화")
    print("=" * 60)
    
    # 사용자 확인
    confirm = input("⚠️ 캐시를 초기화하시겠습니까? (yes/no): ")
    
    if confirm.lower() == "yes":
        clear_cache()
        print("✅ 캐시가 초기화되었습니다.")
        print("💡 다음 수집 시 모든 기사가 '새 기사'로 인식됩니다.")
    else:
        print("❌ 취소되었습니다.")


def example_6_bot_integration():
    """텔레그램 봇 통합 예시"""
    print("\n" + "=" * 60)
    print("예시 6: 텔레그램 봇 통합")
    print("=" * 60)
    
    print("""
# bot.py에서 사용하는 방법:

from app.rss.rss_fetcher import fetch_new_articles, print_fetch_statistics

async def rss_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    await update.message.reply_text("📡 RSS 확인 중...")
    
    # 통계와 함께 기사 가져오기
    articles, stats = fetch_new_articles(return_stats=True)
    
    if not articles:
        await update.message.reply_text("새로운 기사가 없습니다.")
        return
    
    # 통계 정보 전송 (선택사항)
    stats_msg = (
        f"📊 수집 결과\\n"
        f"• 새 기사: {stats.new_articles}개\\n"
        f"• 중복 제거: {stats.duplicate_articles}개\\n"
        f"• 처리 시간: {stats.fetch_time:.1f}초"
    )
    await update.message.reply_text(stats_msg)
    
    # 기사 전송...
    """)


def run_all_examples():
    """모든 예시 실행"""
    try:
        example_1_basic_usage()
        example_2_with_statistics()
        example_3_cache_management()
        example_4_memory_limit()
        
        print("\n" + "=" * 60)
        print("🎉 모든 예시 실행 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 RSS 캐시 시스템 테스트 시작\n")
    
    # 개별 예시 실행
    # example_1_basic_usage()
    # example_2_with_statistics()
    # example_3_cache_management()
    
    # 모든 예시 실행
    run_all_examples()
    
    # 캐시 초기화 (필요시)
    # example_5_cache_reset()
