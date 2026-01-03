import asyncio
import sys
from app.rss.rss_fetcher import fetch_new_articles_async

async def test():
    print("1. RSS 피드 가져오기 시작...")
    try:
        result = await asyncio.wait_for(fetch_new_articles_async(), timeout=30.0)
        
        if isinstance(result, tuple):
            articles, stats = result
            print(f"   성공: {len(articles)}개 기사")
            if stats:
                print(f"   통계: {stats}")
        else:
            articles = result
            print(f"   성공: {len(articles)}개 기사")
        
        if not articles:
            print("\n⚠️  새 기사가 0개입니다!")
            print("   원인: RSS 피드가 응답하지 않거나, 모든 기사가 이미 캐시됨")
        else:
            print(f"\n첫 3개 기사:")
            for i, a in enumerate(articles[:3], 1):
                print(f"   {i}. {a.get('title', 'N/A')[:60]}")
    except asyncio.TimeoutError:
        print("   ❌ 타임아웃! RSS 피드가 응답하지 않습니다.")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
