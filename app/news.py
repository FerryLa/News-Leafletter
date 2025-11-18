# news.py
import requests
from config import NEWSAPI_KEY


def search_news(query: str) -> str:
    """
    입력된 query로 뉴스 검색 후
    제목 + URL 리스트를 문자열로 반환
    """
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "ko",          # 한국어 뉴스 위주. 필요하면 'en'으로 바꿔도 됨
        "sortBy": "publishedAt",
        "pageSize": 5,
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

    lines = []
    for a in articles:
        title = a.get("title", "제목 없음")
        url = a.get("url", "")
        source = (a.get("source") or {}).get("name", "")
        # 보기 좋게 포맷
        lines.append(f"• {title} ({source})\n{url}")

    return "\n\n".join(lines)
