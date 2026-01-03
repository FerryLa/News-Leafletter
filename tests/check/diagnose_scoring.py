import asyncio
from app.rss.rss_fetcher import fetch_new_articles_async
from app.scoring.keyword_scoring import score_and_filter_articles_for_chat

async def test():
    result = await fetch_new_articles_async()
    if isinstance(result, tuple):
        articles = result[0]
    else:
        articles = result
    
    print(f"RSS 기사: {len(articles)}개\n")
    
    # 실제 사용자 ID
    chat_id = 5969524053
    
    print(f"스코어링 (chat_id={chat_id})...")
    scored = score_and_filter_articles_for_chat(articles, chat_id)
    print(f"스코어링 후: {len(scored)}개\n")
    
    if scored:
        print("상위 기사:")
        for i, sa in enumerate(scored[:5], 1):
            print(f"{i}. [{sa.score:+}] {sa.article.get('title', 'N/A')[:50]}")
    else:
        print("⚠️  스코어링 후 기사가 0개!")
        print("\n원인 확인:")
        
        # 키워드 확인
        from app.database.db_manager import get_db
        db = get_db()
        keywords = db.get_keywords_with_scores(chat_id)
        print(f"1. 등록된 키워드: {len(keywords)}개")
        
        # 스코어링 설정 확인
        settings = db.get_user_scoring_settings(chat_id)
        print(f"2. 최소 점수 제한: {settings.get('exclude_min_score')}")
        print(f"3. 블랙리스트: {settings.get('blacklist_keywords')}")
        print(f"4. 화이트리스트: {settings.get('whitelist_keywords')}")

asyncio.run(test())
