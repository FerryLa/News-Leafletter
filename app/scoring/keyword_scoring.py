# app/scoring/keyword_scoring.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from datetime import datetime, timezone


@dataclass
class ScoredArticle:
    article: dict
    score: int
    matched_keywords: dict[str, int]


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(kw and kw in text for kw in keywords)


def _score_keywords(text: str, kw_scores: dict[str, int]) -> dict[str, int]:
    matched: dict[str, int] = {}
    for kw, w in kw_scores.items():
        if kw and kw in text:
            matched[kw] = matched.get(kw, 0) + w
    return matched


def _split_user_keywords(raw_keywords: list[str]) -> dict[str, int]:
    """
    유저 키워드 규칙:
    - 그냥 "비트코인" -> +1
    - "+비트코인" -> +1
    - "-밈코인" -> -1

    반복하면 가중치 증가:
    - /add 비트코인 (첫번째) -> +1
    - /add 비트코인 (두번째) -> +2
    - /add -밈코인 (첫번째) -> -1
    - /add -밈코인 (두번째) -> -2
    """
    scores: dict[str, int] = {}

    for raw in raw_keywords:
        kw = (raw or "").strip()
        if not kw:
            continue

        if kw.startswith("-"):
            core = kw[1:].strip().lower()
            if core:
                scores[core] = scores.get(core, 0) - 1
        elif kw.startswith("+"):
            core = kw[1:].strip().lower()
            if core:
                scores[core] = scores.get(core, 0) + 1
        else:
            core = kw.lower()
            scores[core] = scores.get(core, 0) + 1

    return scores


def score_article_for_chat(article: dict, chat_id: int) -> ScoredArticle | None:
    """
    한 개 기사에 대해:
    - 유저별 화이트/블랙리스트 체크
    - 유저 키워드 점수 (반복 추가 시 가중치 증가)
    - 테마 키워드 점수 (기간 제한)
    - 분류별 점수
    """
    from app.storage import get_keywords  # 순환 import 방지용 내부 import
    from app.database.db_manager import get_db

    db = get_db()
    scoring_settings = db.get_user_scoring_settings(chat_id)

    text_parts = [
        article.get("title", ""),
        article.get("summary", ""),
        article.get("description", ""),
        article.get("content", ""),
    ]
    text = " ".join(t for t in text_parts if t).lower()

    # 유저별 블랙리스트 체크
    blacklist = scoring_settings["blacklist_keywords"]
    if blacklist and _contains_any(text, blacklist):
        return None

    # 유저별 화이트리스트 체크
    whitelist = scoring_settings["whitelist_keywords"]
    if whitelist and not _contains_any(text, whitelist):
        return None

    matched: dict[str, int] = {}

    # 1. 유저 키워드 스코어링 (가중치 반영)
    raw_user_keywords = get_keywords(chat_id)
    user_scores = _split_user_keywords(raw_user_keywords)
    user_matches = _score_keywords(text, user_scores)
    for k, v in user_matches.items():
        matched[k] = matched.get(k, 0) + v

    # 2. 테마 키워드 스코어링 (기간 제한)
    theme_keywords = scoring_settings["theme_keywords"]
    now = datetime.now(timezone.utc)

    active_themes: dict[str, int] = {}
    for kw, theme_data in theme_keywords.items():
        expire_str = theme_data.get("expire_at", "")
        try:
            expire_date = datetime.fromisoformat(expire_str)
            if now < expire_date:
                active_themes[kw.lower()] = theme_data.get("score", 5)
        except (ValueError, AttributeError):
            pass

    theme_matches = _score_keywords(text, active_themes)
    for k, v in theme_matches.items():
        matched[k] = matched.get(k, 0) + v

    # 3. 분류별 스코어링
    sector_scores = scoring_settings["sector_scores"]
    primary_sector = article.get("primary_sector", "").lower()
    if primary_sector and primary_sector in sector_scores:
        sector_score = sector_scores[primary_sector]
        matched[f"[분류:{primary_sector}]"] = sector_score

    total_score = sum(matched.values())

    return ScoredArticle(article=article, score=total_score, matched_keywords=matched)


def score_and_filter_articles_for_chat(
    articles: list[dict], chat_id: int
) -> list[ScoredArticle]:
    from app.database.db_manager import get_db

    scored: list[ScoredArticle] = []

    for a in articles:
        sa = score_article_for_chat(a, chat_id)
        if sa is not None:
            scored.append(sa)

    # 유저별 최소 스코어 제한 적용
    db = get_db()
    scoring_settings = db.get_user_scoring_settings(chat_id)
    exclude_min_score = scoring_settings.get("exclude_min_score")

    if exclude_min_score is not None:
        scored = [sa for sa in scored if sa.score >= exclude_min_score]

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored
