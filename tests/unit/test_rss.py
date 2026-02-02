import asyncio
from app.rss.rss_fetcher import fetch_new_articles_async

async def test():
    print("RSS 피드 테스트 시작...")
    result = await fetch_new_articles_async()
    
    if isinstance(result, tuple):
        articles, stats = result
        print(f"새 기사: {len(articles)}개")
        print(f"통계: {stats}")
        if articles:
            print("\n첫 번째 기사:")
            print(f"  제목: {articles[0].get('title', 'N/A')}")
            print(f"  링크: {articles[0].get('link', 'N/A')}")
    else:
        articles = result
        print(f"새 기사: {len(articles)}개")
        if articles:
            print("\n첫 번째 기사:")
            print(f"  제목: {articles[0].get('title', 'N/A')}")
            print(f"  링크: {articles[0].get('link', 'N/A')}")

asyncio.run(test())
