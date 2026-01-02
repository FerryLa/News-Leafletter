import asyncio
from app.rss.rss_fetcher import fetch_new_articles_async
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat
from app.clustering.news_clusterer import cluster_scored_articles

async def test():
    print("1. RSS 피드 가져오기...")
    result = await fetch_new_articles_async()
    
    if isinstance(result, tuple):
        articles = result[0]
    else:
        articles = result
    
    print(f"   총 기사: {len(articles)}개")
    
    # 테스트 chat_id (실제 사용자 ID를 넣어야 함)
    # 여기서는 임의의 chat_id를 사용
    test_chat_id = 123456789
    
    print(f"\n2. 스코어링 (chat_id={test_chat_id})...")
    scored = score_and_filter_articles_for_chat(articles, test_chat_id)
    print(f"   스코어링 후: {len(scored)}개")
    
    if scored:
        print(f"   첫 번째 기사 점수: {scored[0].score}")
        print(f"   제목: {scored[0].article.get('title', 'N/A')}")
    else:
        print("   ⚠️  스코어링 후 기사가 없습니다!")
        print("   원인: 키워드가 없거나 모든 기사가 필터링되었을 수 있습니다.")
        return
    
    print(f"\n3. 클러스터링...")
    clustered = cluster_scored_articles(scored)
    print(f"   클러스터 수: {len(clustered)}개")
    
    if clustered:
        print(f"\n4. 첫 번째 클러스터:")
        cluster = clustered[0]
        main = cluster.main_article
        print(f"   대표 기사: {main.article.get('title', 'N/A')}")
        print(f"   점수: {main.score}")
        print(f"   관련 기사 수: {len(cluster.related_articles)}")

asyncio.run(test())
