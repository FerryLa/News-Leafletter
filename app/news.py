# news.py
import requests
from config import NEWSAPI_KEY
from app.super_controller import super_controller


def search_news(query: str, chat_id: int | None = None) -> str:
    """
    입력된 query로 뉴스 검색 후
    제목 + URL 리스트를 문자열로 반환
    """
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "ko",          # 한국어 뉴스 위주. 필요하면 'en'으로 바꿔도 됨
        "sortBy": "publishedAt",
        "pageSize": super_controller.get_news_page_size(),
        "apiKey": NEWSAPI_KEY,
    }

    try:
        res = requests.get(url, params=params, timeout=10)
    except Exception:
        return "뉴스 API 요청 중 오류가 발생했습니다."

    try:
        data = res.json()
    except Exception:
        return "뉴스 API 응답 파싱 중 오류가 발생했습니다."

    # 에러 메시지 처리
    if data.get("status") != "ok":
        msg = data.get("message", "알 수 없는 오류")
        return f"뉴스 API에서 오류를 반환했습니다:\n{msg}"

    articles = data.get("articles", [])
    if not articles:
        return "관련 기사를 찾지 못했어요."

    # ⚙ chat_id가 없으면 기존 방식 그대로 (일반 텍스트 검색용)
    # 일반 텍스트 검색(/scan 말고 그냥 메시지 치는 경우) → chat_id=None → 기존 로직 유지
    if chat_id is None:
        lines = []
        for a in articles[:5]:
            title = a.get("title", "제목 없음")
            url_ = a.get("url", "")
            source = (a.get("source") or {}).get("name", "")
            lines.append(f"• {title} ({source})\n{url_}")
        return "\n\n".join(lines)

    # ⚙ chat_id가 있으면 스코어링 사용
    from app.scoring.keyword_scoring import score_and_filter_articles_for_chat

    scored = score_and_filter_articles_for_chat(articles, chat_id)
    if not scored:
        return "필터/스코어 기준에 맞는 기사가 없습니다."

    lines = []
    for sa in scored[:5]:
        a = sa.article
        title = a.get("title", "제목 없음")
        url_ = a.get("url", "")
        source = (a.get("source") or {}).get("name", "")
        score = sa.score
        lines.append(f"• [{score:+}] {title} ({source})\n{url_}")

    return "\n\n".join(lines)
