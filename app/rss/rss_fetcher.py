# rss_fetcher.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

import feedparser

from app.rss.rss_sources import RSS_SOURCES

# 프로젝트 루트 기준으로 data/rss_state.json 경로 계산
BASE_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = BASE_DIR / "data" / "rss_state.json"

MAX_IDS = 10000  # 최근 10,000개 기사만 기록
MAX_SEEN_IDS = MAX_IDS  # 동일 값 사용 (이름만 다르게 쓰고 싶으면 이렇게 매핑)


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    """
    state 딕셔너리에서 seen_ids를 가져와서,
    MAX_IDS 개수까지만 유지한 뒤 파일에 저장.
    """
    # state 안에 저장된 seen_ids 가져오기 (없으면 빈 리스트)
    seen_ids: set[str] = set(state.get("seen_ids", []))

    # set → 리스트로 변환 후 뒤에서 MAX_IDS개만 유지
    ids_list = list(seen_ids)

    if len(ids_list) > MAX_IDS:
        ids_list = ids_list[-MAX_IDS:]
        seen_ids.clear()
        seen_ids.update(ids_list)

    # 최종 값 다시 state에 반영
    state["seen_ids"] = ids_list

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump({"seen_ids": ids_list}, f, ensure_ascii=False, indent=2)


def fetch_new_articles() -> list[dict]:
    """
    모든 RSS 소스를 돌면서,
    이전에 본 적 없는 새 기사만 리스트로 반환.
    """
    state = _load_state()
    seen_ids: set[str] = set(state.get("seen_ids", []))

    new_articles: list[dict] = []

    for url in RSS_SOURCES:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            # 각 기사를 식별할 수 있는 값 (guid 또는 link 위주)
            article_id = entry.get("id") or entry.get("guid") or entry.get("link")
            if not article_id:
                # 그래도 최소한 제목+링크 조합으로 fallback
                article_id = f"{entry.get('title', '')}|{entry.get('link', '')}"

            if article_id in seen_ids:
                continue  # 이미 본 기사

            seen_ids.add(article_id)

            published = entry.get("published") or entry.get("updated") or ""
            link = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", "")

            new_articles.append(
                {
                    "id": article_id,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published_raw": published,
                    "source_url": url,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    # 상태 업데이트 (너무 커지지 않게 개수 제한)
    seen_list = list(seen_ids)

    if len(seen_list) > MAX_SEEN_IDS:
        # 뒤쪽 최근 MAX_SEEN_IDS개만 남기고 앞부분 버리기
        seen_list = seen_list[-MAX_SEEN_IDS:]
        seen_ids = set(seen_list)

    state["seen_ids"] = seen_list
    _save_state(state)

    return new_articles
