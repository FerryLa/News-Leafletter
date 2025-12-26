# news.py
import requests
from config import NEWSAPI_KEY
from app.super_controller import super_controller


def search_news(query: str, chat_id: int | None = None) -> str:
    """
    입력된 query로 뉴스 검색 후
    스코어링 및 클러스터링 적용하여 반환
    (텍스트 형태로 반환 - 호환성 유지)
    """
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "ko",
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

    # chat_id가 없으면 기존 방식 (스코어링 없음)
    if chat_id is None:
        lines = []
        for a in articles[:5]:
            title = a.get("title", "제목 없음")
            url_ = a.get("url", "")
            source = (a.get("source") or {}).get("name", "")
            lines.append(f"• {title} ({source})\n{url_}")
        return "\n\n".join(lines)

    # chat_id가 있으면 스코어링 + 클러스터링
    from app.scoring.keyword_scoring import score_and_filter_articles_for_chat
    from app.clustering.news_clusterer import cluster_scored_articles

    # 1. 스코어링 및 필터링
    scored = score_and_filter_articles_for_chat(articles, chat_id)
    if not scored:
        return "필터/스코어 기준에 맞는 기사가 없습니다."

    # 2. 클러스터링 (활성화 여부는 내부에서 판단)
    clustered = cluster_scored_articles(scored)
    
    # 3. 기존 포맷으로 변환 (한 줄씩)
    lines = []
    for cluster in clustered:
        # 대표 기사만 표시
        main = cluster.main_article
        article = main.article
        
        title = article.get("title", "제목 없음")
        url_ = article.get("url", article.get("link", ""))
        source = (article.get("source") or {}).get("name", "")
        score = main.score
        
        lines.append(f"• [{score:+}] {title} ({source})\n{url_}")
    
    return "\n\n".join(lines)


def get_news_with_images(query: str, chat_id: int | None = None) -> list:
    """
    뉴스를 검색하고 이미지 URL과 함께 리스트로 반환
    (봇에서 개별 메시지로 전송하기 위함)
    
    Returns:
        [
            {
                'title': str,
                'url': str,
                'image_url': str,
                'source': str,
                'score': int
            },
            ...
        ]
    """
    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "ko",
        "sortBy": "publishedAt",
        "pageSize": super_controller.get_news_page_size(),
        "apiKey": NEWSAPI_KEY,
    }

    try:
        res = requests.get(url, params=params, timeout=10)
    except Exception:
        return []

    try:
        data = res.json()
    except Exception:
        return []

    if data.get("status") != "ok":
        return []

    articles = data.get("articles", [])
    if not articles:
        return []

    # chat_id가 없으면 스코어링 없이 반환
    if chat_id is None:
        results = []
        for a in articles[:5]:
            results.append({
                'title': a.get("title", "제목 없음"),
                'url': a.get("url", ""),
                'image_url': a.get("urlToImage", ""),
                'source': (a.get("source") or {}).get("name", ""),
                'score': 0
            })
        return results

    # chat_id가 있으면 스코어링 + 클러스터링
    from app.scoring.keyword_scoring import score_and_filter_articles_for_chat
    from app.clustering.news_clusterer import cluster_scored_articles

    # 1. 스코어링 및 필터링
    scored = score_and_filter_articles_for_chat(articles, chat_id)
    if not scored:
        return []

    # 2. 클러스터링
    clustered = cluster_scored_articles(scored)
    
    # 3. 이미지 URL과 함께 반환
    results = []
    for cluster in clustered:
        main = cluster.main_article
        article = main.article
        
        results.append({
            'title': article.get("title", "제목 없음"),
            'url': article.get("url", article.get("link", "")),
            'image_url': article.get("urlToImage", ""),
            'source': (article.get("source") or {}).get("name", ""),
            'score': main.score
        })
    
    return results
