# 직접 스코어링 테스트 (asyncio 없이)
from app.scoring.keyword_scoring import score_article_for_chat

test_article = {
    "title": "비트코인 뉴스",
    "description": "테스트",
    "content": "테스트 내용"
}

chat_id = 5969524053

print("스코어링 테스트...")
try:
    result = score_article_for_chat(test_article, chat_id)
    if result:
        print(f"성공: 점수={result.score}")
    else:
        print("필터링됨 (None 반환)")
except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()
