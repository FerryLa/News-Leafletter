import asyncio
from app.rss.rss_fetcher import fetch_new_articles_async
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat

async def test():
    result = await fetch_new_articles_async()
    if isinstance(result, tuple):
        articles = result[0]
    else:
        articles = result
    
    print(f"1. RSS: {len(articles)}개")
    
    chat_id = 5969524053
    
    print(f"2. 스코어링 시작...")
    try:
        scored = score_and_filter_articles_for_chat(articles, chat_id)
        print(f"   완료: {len(scored)}개")
    except Exception as e:
        print(f"   오류: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
