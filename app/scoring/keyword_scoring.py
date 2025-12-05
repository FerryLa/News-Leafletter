# app/scoring/keyword_scoring.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.super_controller import super_controller


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


def _split_user_keywords(raw_keywords: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    """
    유저 키워드 규칙:
    - 그냥 "비트코인" -> +1
    - "-밈코인" 처럼 앞에 - 붙이면 -> -1
    """
    pos: dict[str, int] = {}
    neg: dict[str, int] = {}

    for raw in raw_keywords:
        kw = (raw or "").strip()
        if not kw:
            continue

        if kw.startswith("-"):
            core = kw[1:].strip().lower()
            if core:
                neg[core] = -1
        else:
            pos[kw.lower()] = 1

    return pos, neg


def score_article_for_chat(article: dict, chat_id: int) -> ScoredArticle | None:
    """
    한 개 기사에 대해:
    - 화이트/블랙리스트 체크
    - 어드민 키워드 점수 (보통 ±3)
    - 유저 키워드 점수 (±1)
    """
    from app.storage import get_keywords  # 순환 import 방지용 내부 import

    text_parts = [
        article.get("title", ""),
        article.get("summary", ""),
        article.get("description", ""),
        article.get("content", ""),
    ]
    text = " ".join(t for t in text_parts if t).lower()

    admin_kw = super_controller.get_admin_keywords()

    wl_enabled = super_controller.is_whitelist_enabled()
    wl = super_controller.get_whitelist()
    bl_enabled = super_controller.is_blacklist_enabled()
    bl = super_controller.get_blacklist()

    if bl_enabled and bl and _contains_any(text, bl):
        return None

    if wl_enabled and wl and not _contains_any(text, wl):
        return None

    admin_matches = _score_keywords(text, admin_kw)

    raw_user_keywords = get_keywords(chat_id)
    user_pos, user_neg = _split_user_keywords(raw_user_keywords)

    user_pos_matches = _score_keywords(text, user_pos)
    user_neg_matches = _score_keywords(text, user_neg)

    matched: dict[str, int] = {}
    for d in (admin_matches, user_pos_matches, user_neg_matches):
        for k, v in d.items():
            matched[k] = matched.get(k, 0) + v

    total_score = sum(matched.values())

    return ScoredArticle(article=article, score=total_score, matched_keywords=matched)


def score_and_filter_articles_for_chat(
    articles: list[dict], chat_id: int
) -> list[ScoredArticle]:
    scored: list[ScoredArticle] = []

    for a in articles:
        sa = score_article_for_chat(a, chat_id)
        if sa is not None:
            scored.append(sa)

    score_rules = super_controller.get_score_rules()

    min_enabled = score_rules.get("min_enabled", False)
    min_score = score_rules.get("min_score", None)

    exclude_enabled = score_rules.get("exclude_enabled", False)
    exclude_scores = set(score_rules.get("exclude_scores", []))

    if min_enabled and min_score is not None:
        scored = [sa for sa in scored if sa.score >= min_score]

    if exclude_enabled and exclude_scores:
        scored = [sa for sa in scored if sa.score not in exclude_scores]

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored
