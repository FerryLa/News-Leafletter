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

def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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
                article_id = f"{entry.get('title','')}|{entry.get('link','')}"

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

    # 상태 업데이트
    state["seen_ids"] = list(seen_ids)
    _save_state(state)

    return new_articles
