# rss_fetcher.py - SQLite 기반으로 리팩토링
"""
RSS 피드 수집 및 캐시 관리 (SQLite 기반)
이슈 #21 완전 해결 + 이슈 #32 SQLite 전환
"""
from __future__ import annotations
import asyncio
from typing import List, Dict, Optional, Set
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser

from app.rss.rss_sources import RSS_SOURCES
from app.database.db_manager import get_db

# 성능 최적화: 스레드 풀 재사용
_executor = ThreadPoolExecutor(max_workers=10)


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


def _fetch_single_feed(url: str) -> tuple[List[dict], int, int]:
    """
    단일 RSS 피드를 가져오는 함수 (동기)
    스레드 풀에서 실행됨
    
    Returns:
        (새 기사 목록, 전체 항목 수, 중복 항목 수)
    """
    db = get_db()
    new_articles: List[dict] = []
    total_entries = 0
    duplicate_count = 0
    
    try:
        feed = feedparser.parse(url)
        total_entries = len(feed.entries)
        
        for entry in feed.entries:
            # 정규화된 ID 생성
            article_id = _normalize_article_id(entry)
            
            # 중복 체크 (SQLite)
            if db.is_article_seen(article_id):
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
            
            # DB에 기록
            db.mark_article_seen(article_id, source_url=url, title=title)
            
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
    
    이슈 #21 완전 해결 + 이슈 #32 SQLite 전환:
    - 1. 병렬 처리 (asyncio.gather) ✅
    - 2. 캐시 및 중복 제거 (SQLite 기반) ✅
    
    Args:
        max_articles: 메모리 보호를 위한 최대 기사 수 (기본값: 1000)
        return_stats: True면 통계 정보도 반환
    
    Returns:
        (새로 발견된 기사 목록, 통계 정보 or None)
    """
    start_time = asyncio.get_event_loop().time()
    
    # 통계 초기화
    stats = FetchStatistics(total_feeds=len(RSS_SOURCES))
    
    # 병렬 처리를 위한 태스크 생성
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, _fetch_single_feed, url)
        for url in RSS_SOURCES
    ]
    
    # 모든 피드를 병렬로 가져오기
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 결과 병합 (메모리 보호 포함)
    all_new_articles: list[dict] = []
    article_count = 0
    
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
            
            # 남은 공간만큼만 추가
            remaining_space = max_articles - article_count
            articles_to_add = new_articles[:remaining_space]
            all_new_articles.extend(articles_to_add)
            article_count += len(articles_to_add)
    
    stats.new_articles = len(all_new_articles)
    
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


# ==================== 캐시 관리 유틸리티 ====================

def clear_cache() -> None:
    """RSS 캐시 초기화 (모든 seen_ids 삭제)"""
    db = get_db()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM rss_cache")
    conn.commit()
    
    print("✅ RSS 캐시가 초기화되었습니다.")


def get_cache_info() -> dict:
    """캐시 정보 조회"""
    db = get_db()
    stats = db.get_cache_stats()
    
    # DB 크기 추가
    stats["cache_file_size_kb"] = db.get_db_size() / 1024
    stats["cache_expiry_days"] = 7  # 설정값
    stats["max_stored_ids"] = 10000  # 설정값
    
    return stats


def cleanup_old_rss_cache(days: int = 7) -> int:
    """
    오래된 RSS 캐시 삭제
    
    Args:
        days: N일 이전 데이터 삭제
    
    Returns:
        삭제된 레코드 수
    """
    db = get_db()
    deleted_count = db.cleanup_old_cache(days)
    
    print(f"✅ {deleted_count}개의 오래된 캐시 삭제됨 ({days}일 이전)")
    
    return deleted_count
