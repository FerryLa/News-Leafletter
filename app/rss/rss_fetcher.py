# rss_fetcher.py - 이슈 #21 해결: 비동기 병렬 처리 + 메모리 보호
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

import feedparser

from app.rss.rss_sources import RSS_SOURCES

# 프로젝트 루트 기준으로 data/rss_state.json 경로 계산
BASE_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = BASE_DIR / "data" / "rss_state.json"

MAX_STORED_IDS = 10000  # 최근 10,000개 기사 ID만 기록

# 성능 최적화: 스레드 풀 재사용
_executor = ThreadPoolExecutor(max_workers=10)


def _load_state() -> dict:
    """상태 파일 로드"""
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
    MAX_STORED_IDS 개수까지만 유지한 뒤 파일에 저장.
    """
    seen_ids: set[str] = set(state.get("seen_ids", []))
    ids_list = list(seen_ids)

    if len(ids_list) > MAX_STORED_IDS:
        ids_list = ids_list[-MAX_STORED_IDS:]

    state["seen_ids"] = ids_list

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump({"seen_ids": ids_list}, f, ensure_ascii=False, indent=2)


def _fetch_single_feed(url: str, seen_ids: set[str]) -> List[dict]:
    """
    단일 RSS 피드를 가져오는 함수 (동기)
    스레드 풀에서 실행됨
    """
    new_articles: List[dict] = []
    
    try:
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            article_id = entry.get("id") or entry.get("guid") or entry.get("link")
            if not article_id:
                article_id = f"{entry.get('title', '')}|{entry.get('link', '')}"

            if article_id in seen_ids:
                continue

            published = entry.get("published") or entry.get("updated") or ""
            link = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", "")

            new_articles.append({
                "id": article_id,
                "title": title,
                "link": link,
                "summary": summary,
                "published_raw": published,
                "source_url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as e:
        # 개별 피드 실패는 전체를 막지 않음
        print(f"Failed to fetch {url}: {e}")
    
    return new_articles


async def fetch_new_articles_async(max_articles: int = 1000) -> list[dict]:
    """
    모든 RSS 소스를 **비동기 병렬**로 처리하여 성능 향상
    
    이슈 #21 해결: 반응속도 최적화
    
    Args:
        max_articles: 메모리 보호를 위한 최대 기사 수 (기본값: 1000)
                     극단적으로 많은 기사가 수집될 경우 메모리 부족 방지
    
    Returns:
        새로 발견된 기사 목록 (최대 max_articles개)
    """
    state = _load_state()
    seen_ids: set[str] = set(state.get("seen_ids", []))
    
    # 병렬 처리를 위한 태스크 생성
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, _fetch_single_feed, url, seen_ids)
        for url in RSS_SOURCES
    ]
    
    # 모든 피드를 병렬로 가져오기
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 병합 (메모리 보호 포함)
    all_new_articles: list[dict] = []
    article_count = 0
    
    for result in results:
        if isinstance(result, list):
            # 메모리 보호: 최대 제한 체크
            if article_count >= max_articles:
                print(f"⚠️ 기사 수 제한 도달: {max_articles}개 (추가 기사 무시됨)")
                break
            
            # seen_ids 업데이트
            for article in result:
                seen_ids.add(article["id"])
            
            # 남은 공간만큼만 추가
            remaining_space = max_articles - article_count
            articles_to_add = result[:remaining_space]
            all_new_articles.extend(articles_to_add)
            article_count += len(articles_to_add)
    
    # 상태 저장 (seen_ids만 디스크에 저장)
    seen_list = list(seen_ids)
    if len(seen_list) > MAX_STORED_IDS:
        seen_list = seen_list[-MAX_STORED_IDS:]
    
    state["seen_ids"] = seen_list
    _save_state(state)
    
    return all_new_articles


def fetch_new_articles(max_articles: int = 1000) -> list[dict]:
    """
    동기 래퍼 함수 (기존 코드 호환성 유지)
    
    Args:
        max_articles: 최대 기사 수 제한 (기본값: 1000)
    
    Returns:
        새로 발견된 기사 목록
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(fetch_new_articles_async(max_articles))
