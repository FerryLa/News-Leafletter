# rss_fetcher.py - 이슈 #21 완전 해결: 비동기 병렬 처리 + 메모리 보호 + 향상된 캐시
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import asyncio
from typing import List, Dict, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import feedparser

from app.rss.rss_sources import RSS_SOURCES

# 프로젝트 루트 기준으로 data/rss_state.json 경로 계산
BASE_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = BASE_DIR / "data" / "rss_state.json"

MAX_STORED_IDS = 10000  # 최근 10,000개 기사 ID만 기록
CACHE_EXPIRY_DAYS = 7    # 7일 이상 된 기사는 캐시에서 제거

# 성능 최적화: 스레드 풀 재사용
_executor = ThreadPoolExecutor(max_workers=10)

# 메모리 캐시: 빠른 중복 체크용
_memory_cache: Optional[Set[str]] = None


@dataclass
class FetchStatistics:
    """RSS 수집 통계"""
    total_feeds: int = 0
    successful_feeds: int = 0
    failed_feeds: int = 0
    total_entries: int = 0
    new_articles: int = 0
    duplicate_articles: int = 0
    fetch_time: float = 0.0


def _load_state() -> dict:
    """상태 파일 로드"""
    if not STATE_FILE.exists():
        return {"seen_ids": [], "timestamps": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"seen_ids": [], "timestamps": {}}


def _save_state(state: dict) -> None:
    """
    state 딕셔너리를 디스크에 저장
    - seen_ids: 이미 본 기사 ID 목록
    - timestamps: 각 ID의 첫 발견 시간
    """
    seen_ids: set[str] = set(state.get("seen_ids", []))
    timestamps: dict = state.get("timestamps", {})
    
    # 만료된 항목 제거 (7일 이상 된 기사)
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRY_DAYS)
    cutoff_iso = cutoff_time.isoformat()
    
    # 타임스탬프가 있는 항목 중 만료된 것 제거
    expired_ids = [
        article_id for article_id, timestamp in timestamps.items()
        if timestamp < cutoff_iso
    ]
    
    for article_id in expired_ids:
        seen_ids.discard(article_id)
        timestamps.pop(article_id, None)
    
    # 크기 제한 (MAX_STORED_IDS)
    ids_list = list(seen_ids)
    if len(ids_list) > MAX_STORED_IDS:
        # 오래된 것부터 제거 (타임스탬프 없는 것 우선)
        ids_with_time = [(aid, timestamps.get(aid, "0")) for aid in ids_list]
        ids_with_time.sort(key=lambda x: x[1])
        
        # 최근 MAX_STORED_IDS개만 유지
        keep_ids = [aid for aid, _ in ids_with_time[-MAX_STORED_IDS:]]
        ids_list = keep_ids
        
        # 제거된 ID의 타임스탬프도 삭제
        timestamps = {aid: timestamps[aid] for aid in keep_ids if aid in timestamps}
    
    state["seen_ids"] = ids_list
    state["timestamps"] = timestamps
    
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _normalize_article_id(entry: dict) -> str:
    """
    기사 ID 정규화 (중복 제거 강화)
    
    우선순위:
    1. guid (Global Unique ID)
    2. id (entry.id)
    3. link (URL)
    4. title + link 조합 (fallback)
    """
    # 1순위: guid
    guid = entry.get("guid")
    if guid:
        # guid가 딕셔너리인 경우 처리
        if isinstance(guid, dict):
            guid = guid.get("value") or guid.get("guid")
        if guid and isinstance(guid, str):
            return guid.strip().lower()
    
    # 2순위: id
    article_id = entry.get("id")
    if article_id:
        return str(article_id).strip().lower()
    
    # 3순위: link
    link = entry.get("link")
    if link:
        return str(link).strip().lower()
    
    # 4순위: title + link 조합 (fallback)
    title = entry.get("title", "")
    link = entry.get("link", "")
    return f"{title}|{link}".strip().lower()


def _is_duplicate(article_id: str, seen_ids: Set[str]) -> bool:
    """
    중복 체크 (메모리 캐시 + 디스크 캐시)
    
    Args:
        article_id: 정규화된 기사 ID
        seen_ids: 이미 본 ID 집합
    
    Returns:
        True if 중복, False if 새 기사
    """
    global _memory_cache
    
    # 메모리 캐시 초기화 (첫 호출 시)
    if _memory_cache is None:
        _memory_cache = set(seen_ids)
    
    # 메모리 캐시에서 먼저 확인 (O(1) 속도)
    if article_id in _memory_cache:
        return True
    
    # 디스크 캐시에서도 확인 (메모리 캐시 누락 대비)
    if article_id in seen_ids:
        _memory_cache.add(article_id)  # 메모리 캐시 동기화
        return True
    
    return False


def _fetch_single_feed(url: str, seen_ids: set[str]) -> tuple[List[dict], int, int]:
    """
    단일 RSS 피드를 가져오는 함수 (동기)
    스레드 풀에서 실행됨
    
    Returns:
        (새 기사 목록, 전체 항목 수, 중복 항목 수)
    """
    new_articles: List[dict] = []
    total_entries = 0
    duplicate_count = 0
    
    try:
        feed = feedparser.parse(url)
        total_entries = len(feed.entries)
        
        for entry in feed.entries:
            # 정규화된 ID 생성
            article_id = _normalize_article_id(entry)
            
            # 중복 체크
            if _is_duplicate(article_id, seen_ids):
                duplicate_count += 1
                continue
            
            # 새 기사 발견
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
    
    return new_articles, total_entries, duplicate_count


async def fetch_new_articles_async(
    max_articles: int = 1000,
    return_stats: bool = False
) -> tuple[list[dict], Optional[FetchStatistics]]:
    """
    모든 RSS 소스를 **비동기 병렬**로 처리하여 성능 향상
    
    이슈 #21 완전 해결:
    - 1. 병렬 처리 (asyncio.gather) ✅
    - 2. 캐시 및 중복 제거 (메모리 + 디스크) ✅
    
    Args:
        max_articles: 메모리 보호를 위한 최대 기사 수 (기본값: 1000)
        return_stats: True면 통계 정보도 반환
    
    Returns:
        (새로 발견된 기사 목록, 통계 정보 or None)
    """
    start_time = asyncio.get_event_loop().time()
    
    # 상태 로드
    state = _load_state()
    seen_ids: set[str] = set(state.get("seen_ids", []))
    timestamps: dict = state.get("timestamps", {})
    
    # 통계 초기화
    stats = FetchStatistics(total_feeds=len(RSS_SOURCES))
    
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
    current_time = datetime.now(timezone.utc).isoformat()
    
    for result in results:
        if isinstance(result, Exception):
            stats.failed_feeds += 1
            continue
        
        if isinstance(result, tuple):
            new_articles, total_entries, duplicate_count = result
            
            stats.successful_feeds += 1
            stats.total_entries += total_entries
            stats.duplicate_articles += duplicate_count
            
            # 메모리 보호: 최대 제한 체크
            if article_count >= max_articles:
                print(f"⚠️ 기사 수 제한 도달: {max_articles}개 (추가 기사 무시됨)")
                break
            
            # seen_ids 및 타임스탬프 업데이트
            for article in new_articles:
                seen_ids.add(article["id"])
                timestamps[article["id"]] = current_time
            
            # 남은 공간만큼만 추가
            remaining_space = max_articles - article_count
            articles_to_add = new_articles[:remaining_space]
            all_new_articles.extend(articles_to_add)
            article_count += len(articles_to_add)
    
    stats.new_articles = len(all_new_articles)
    
    # 상태 저장 (seen_ids + timestamps)
    state["seen_ids"] = list(seen_ids)
    state["timestamps"] = timestamps
    _save_state(state)
    
    # 통계 완성
    stats.fetch_time = asyncio.get_event_loop().time() - start_time
    
    if return_stats:
        return all_new_articles, stats
    else:
        return all_new_articles, None


def fetch_new_articles(
    max_articles: int = 1000,
    return_stats: bool = False
) -> tuple[list[dict], Optional[FetchStatistics]]:
    """
    동기 래퍼 함수 (기존 코드 호환성 유지)
    
    Args:
        max_articles: 최대 기사 수 제한 (기본값: 1000)
        return_stats: True면 통계 정보도 반환
    
    Returns:
        (새로 발견된 기사 목록, 통계 정보 or None)
    """
    try:
        # 현재 실행 중인 이벤트 루프 확인
        loop = asyncio.get_running_loop()
        # 이미 루프가 실행 중이면 nest_asyncio 사용 또는 에러 발생
        raise RuntimeError(
            "fetch_new_articles()는 비동기 컨텍스트에서 직접 호출할 수 없습니다. "
            "대신 fetch_new_articles_async()를 사용하세요."
        )
    except RuntimeError:
        # 실행 중인 루프가 없으면 정상 처리
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            fetch_new_articles_async(max_articles, return_stats)
        )


def print_fetch_statistics(stats: FetchStatistics) -> None:
    """통계 정보 출력 (디버깅용)"""
    print("\n" + "="*50)
    print("📊 RSS 수집 통계")
    print("="*50)
    print(f"총 피드 수: {stats.total_feeds}")
    print(f"성공: {stats.successful_feeds} / 실패: {stats.failed_feeds}")
    print(f"총 항목 수: {stats.total_entries}")
    print(f"새 기사: {stats.new_articles}")
    print(f"중복 제거: {stats.duplicate_articles}")
    print(f"처리 시간: {stats.fetch_time:.2f}초")
    print("="*50 + "\n")


# 캐시 초기화 함수 (필요시 사용)
def clear_cache() -> None:
    """메모리 캐시 및 디스크 캐시 초기화"""
    global _memory_cache
    _memory_cache = None
    
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    
    print("✅ 캐시가 초기화되었습니다.")


def get_cache_info() -> dict:
    """캐시 정보 조회"""
    state = _load_state()
    seen_ids = state.get("seen_ids", [])
    timestamps = state.get("timestamps", {})
    
    # 오래된 항목 수 계산
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=CACHE_EXPIRY_DAYS)
    cutoff_iso = cutoff_time.isoformat()
    old_count = sum(1 for ts in timestamps.values() if ts < cutoff_iso)
    
    return {
        "total_cached_ids": len(seen_ids),
        "with_timestamp": len(timestamps),
        "expired_items": old_count,
        "cache_file_size_kb": STATE_FILE.stat().st_size / 1024 if STATE_FILE.exists() else 0,
        "cache_expiry_days": CACHE_EXPIRY_DAYS,
        "max_stored_ids": MAX_STORED_IDS,
    }
