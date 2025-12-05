# app/scoring/keyword_scoring.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# 프로젝트 루트 (News-Leafletter/)
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

ADMIN_KEYWORDS_FILE = DATA_DIR / "admin_keywords.json"
FILTERS_FILE = DATA_DIR / "keyword_filters.json"


@dataclass
class ScoredArticle:
    article: dict
    score: int
    matched_keywords: dict[str, int]


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_admin_keywords() -> dict[str, int]:
    """
    admin_keywords.json 형식:
    {
      "admin": {
        "비트코인": 3,
        "밈코인": -3
      }
    }
    """
    data = _load_json(ADMIN_KEYWORDS_FILE, {})
    admin = data.get("admin", {})
    # key는 소문자로 통일
    return {k.lower(): int(v) for k, v in admin.items()}


def load_filters() -> dict:
    """
    keyword_filters.json 형식 예시:
    {
      "whitelist": ["비트코인", "이더리움"],
      "blacklist": ["광고", "sponsored"],
      "score_rules": {
        "min_score": {
          "enabled": false,
          "value": 10
        },
        "exclude_scores": {
          "enabled": false,
          "values": [-1]
        }
      }
    }
    """
    data = _load_json(FILTERS_FILE, {})

    wl = [s.lower() for s in data.get("whitelist", []) if s]
    bl = [s.lower() for s in data.get("blacklist", []) if s]

    raw_score_rules = data.get("score_rules", {})

    min_conf = raw_score_rules.get("min_score", {})
    excl_conf = raw_score_rules.get("exclude_scores", {})

    score_rules = {
        "min_enabled": bool(min_conf.get("enabled", False)),
        "min_score": min_conf.get("value", None),
        "exclude_enabled": bool(excl_conf.get("enabled", False)),
        "exclude_scores": excl_conf.get("values", []),
    }

    return {
        "whitelist": wl,
        "blacklist": bl,
        "score_rules": score_rules,
    }



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

    # RSS / 뉴스 공통으로 쓸 수 있게 title + summary + description 모두 합침
    text_parts = [
        article.get("title", ""),
        article.get("summary", ""),
        article.get("description", ""),
    ]
    text = " ".join(t for t in text_parts if t).lower()

    admin_kw = load_admin_keywords()
    filters = load_filters()

    # 1) 화이트/블랙리스트 필터링
    wl = filters["whitelist"]
    bl = filters["blacklist"]

    if bl and _contains_any(text, bl):
        # 블랙리스트에 걸리면 바로 탈락
        return None

    if wl and not _contains_any(text, wl):
        # 화이트리스트가 비어있지 않다면, 최소 하나는 포함되어야 함
        return None

    # 2) 어드민 키워드 점수
    admin_matches = _score_keywords(text, admin_kw)

    # 3) 유저 키워드 점수 (+1 / -1)
    raw_user_keywords = get_keywords(chat_id)
    user_pos, user_neg = _split_user_keywords(raw_user_keywords)

    user_pos_matches = _score_keywords(text, user_pos)
    user_neg_matches = _score_keywords(text, user_neg)

    # 4) 총합
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

    # 여기까지 오면:
    # - 블랙리스트 / 화이트리스트는 이미 score_article_for_chat 안에서 처리됨
    # - scored 리스트에는 ScoredArticle(기사, score, matched_keywords)이 들어 있음

    # 🔧 점수 기반 추가 필터 (config로 On/Off)
    filters = load_filters()
    score_rules = filters.get("score_rules", {})

    min_enabled = score_rules.get("min_enabled", False)
    min_score = score_rules.get("min_score", None)

    exclude_enabled = score_rules.get("exclude_enabled", False)
    exclude_scores = set(score_rules.get("exclude_scores", []))

    # 1) 최소 점수 조건
    if min_enabled and min_score is not None:
        scored = [sa for sa in scored if sa.score >= min_score]

    # 2) 특정 점수 제외
    if exclude_enabled and exclude_scores:
        scored = [sa for sa in scored if sa.score not in exclude_scores]

    # 최종 정렬
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored