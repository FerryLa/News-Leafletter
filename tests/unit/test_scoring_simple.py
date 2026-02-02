import asyncio
from app.rss.rss_fetcher import fetch_new_articles_async
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat

async def test():
    print("1. RSS 기사 가져오기...")
    result = await fetch_new_articles_async()
    
    if isinstance(result, tuple):
        articles = result[0]
    else:
        articles = result
    
    print(f"   총 기사: {len(articles)}개")
    
    # 실제 사용자 ID
    test_chat_id = 5969524053
    
    print(f"\n2. 스코어링 (chat_id={test_chat_id})...")
    scored = score_and_filter_articles_for_chat(articles, test_chat_id)
    print(f"   스코어링 후: {len(scored)}개")
    
    if scored:
        print(f"\n   상위 5개 기사:")
        for i, sa in enumerate(scored[:5], 1):
            print(f"   {i}. [{sa.score:+}] {sa.article.get('title', 'N/A')[:60]}...")
    else:
        print("   ⚠️  스코어링 후 기사가 없습니다!")

asyncio.run(test())
