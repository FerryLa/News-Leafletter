"""Centralized configuration controller for scoring and runtime settings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_START_MESSAGE = (
    "Leafletter News Bot 입니다.\n"
    "검색할 키워드나 종목/이슈를 보내면 관련 뉴스를 찾아드립니다.\n\n"
    "기능 안내:\n"
    "- 텍스트 입력    : 해당 키워드로 뉴스 검색 (키워드 스코어링 적용)\n"
    "- /add 키워드    : 관심 키워드(+1) 또는 제외 키워드(-1) 추가\n"
    "- /list          : 관심 키워드 목록 보기\n"
    "- /del 키워드    : 관심 키워드 삭제\n"
    "- /scan          : 모든 관심 키워드 뉴스 한 번에 조회\n\n"
    "키워드 스코어링 규칙:\n"
    "- /add 비트코인 뉴스  -> '비트코인 뉴스' +1점\n"
    "- /add -밈코인        -> '밈코인' 포함 기사 -1점\n"
    "검색/알림 결과는 예시처럼 점수와 함께 표시됩니다.\n"
    "  • [+3] 비트코인 ETF 승인 임박\n"
    "  • [-1] 밈코인 단기 급등 기사\n\n"
    "언론사 필터링:\n"
    "- /block 언론사명  : 특정 언론사 기사 차단\n"
    "- /allow 언론사명  : 차단 해제\n"
    "- /sources        : 차단 목록 및 매핑된 언론사 보기\n\n"
    "추가 기능 안내 (RSS):\n"
    "- /rss_now       : RSS에서 새로 들어온 기사 수동 확인\n"
    "- /rss_auto_on   : RSS 자동 알림 시작\n"
    "- /rss_auto_off  : RSS 자동 알림 중지\n\n"
)


class SuperController:
    def __init__(self, config_path: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.data_dir = base_dir / "data"
        self.config_path = config_path or self.data_dir / "config.json"

        self._config: dict[str, Any] = {}
        self._whitelist: list[str] = []
        self._blacklist: list[str] = []
        self._whitelist_enabled: bool = False
        self._blacklist_enabled: bool = False
        self._score_rules: dict[str, Any] = {}
        self._admin_keywords: dict[str, int] = {}
        self._news_page_size: int = 10
        self._rss_auto_interval: int = 10
        self._start_message: str = DEFAULT_START_MESSAGE
        
        # 클러스터링 설정
        self._clustering_config: dict[str, Any] = {}
        self._cluster_keyword_config: dict[str, Any] = {}

        # 섹터 분류 설정
        self._sector_classification_config: dict[str, Any] = {}

        self.reload()

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _normalize_keywords(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return [str(v).lower() for v in values if str(v).strip()]

    def _load_legacy_filters(self) -> dict[str, Any]:
        legacy_path = self.data_dir / "keyword_filters.json"
        return self._read_json(legacy_path, {})

    def _parse_keyword_config(self, raw: Any, fallback: list[str]) -> tuple[bool, list[str]]:
        enabled_default = bool(fallback)
        if isinstance(raw, dict):
            enabled = bool(raw.get("enabled", enabled_default))
            values = raw.get("values", fallback)
        elif isinstance(raw, list):
            enabled = bool(raw) if raw is not None else enabled_default
            values = raw
        else:
            enabled = enabled_default
            values = fallback

        return enabled, self._normalize_keywords(values)

    def _load_legacy_admin_keywords(self) -> dict[str, int]:
        legacy_path = self.data_dir / "admin_keywords.json"
        raw = self._read_json(legacy_path, {})
        admin_block = raw.get("admin", {}) if isinstance(raw, dict) else {}
        return {str(k).lower(): int(v) for k, v in admin_block.items() if str(k).strip()}

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._config = self._read_json(self.config_path, {})

        legacy_filters = self._load_legacy_filters()
        legacy_admin = self._load_legacy_admin_keywords()

        wl_raw = self._config.get("whitelist", legacy_filters.get("whitelist", []))
        bl_raw = self._config.get("blacklist", legacy_filters.get("blacklist", []))
        self._whitelist_enabled, self._whitelist = self._parse_keyword_config(
            wl_raw, legacy_filters.get("whitelist", [])
        )
        self._blacklist_enabled, self._blacklist = self._parse_keyword_config(
            bl_raw, legacy_filters.get("blacklist", [])
        )

        score_rules_conf = self._config.get("score_rules", legacy_filters.get("score_rules", {}))
        min_conf = score_rules_conf.get("min_score", {}) if isinstance(score_rules_conf, dict) else {}
        excl_conf = (
            score_rules_conf.get("exclude_scores", {})
            if isinstance(score_rules_conf, dict)
            else {}
        )
        min_value = min_conf.get("value", None)
        try:
            min_value = int(min_value) if min_value is not None else None
        except (TypeError, ValueError):
            min_value = None

        exclude_values = []
        for v in excl_conf.get("values", []):
            try:
                exclude_values.append(int(v))
            except (TypeError, ValueError):
                continue

        self._score_rules = {
            "min_enabled": bool(min_conf.get("enabled", False)),
            "min_score": min_value,
            "exclude_enabled": bool(excl_conf.get("enabled", False)),
            "exclude_scores": exclude_values,
        }

        raw_admin = self._config.get("admin_keywords") or legacy_admin
        self._admin_keywords = {
            str(k).lower(): int(v) for k, v in raw_admin.items() if str(k).strip()
        }

        news_conf = self._config.get("news", {}) if isinstance(self._config, dict) else {}
        self._news_page_size = int(news_conf.get("page_size", 10))

        rss_conf = self._config.get("rss", {}) if isinstance(self._config, dict) else {}
        self._rss_auto_interval = int(rss_conf.get("auto_interval", 10))

        bot_conf = self._config.get("bot", {}) if isinstance(self._config, dict) else {}
        self._start_message = str(bot_conf.get("start_message", DEFAULT_START_MESSAGE))
        
        # 클러스터링 설정 로드
        clustering_conf = self._config.get("clustering", {})
        self._clustering_config = {
            "enabled": bool(clustering_conf.get("enabled", False)),
            "similarity_threshold": float(clustering_conf.get("similarity_threshold", 0.7)),
            "min_cluster_size": int(clustering_conf.get("min_cluster_size", 2)),
            "max_clusters": int(clustering_conf.get("max_clusters", 10)),
            "vectorizer": clustering_conf.get("vectorizer", {
                "max_features": 1000,
                "ngram_range": [1, 2]
            }),
            "selection": clustering_conf.get("selection", {
                "articles_per_cluster": 2,
                "max_total_articles": 15
            })
        }
        
        # 클러스터 키워드 추출 설정
        keyword_conf = self._config.get("cluster_keywords", {})
        self._cluster_keyword_config = {
            "enabled": bool(keyword_conf.get("enabled", True)),
            "top_n": int(keyword_conf.get("top_n", 3)),
            "min_df": int(keyword_conf.get("min_df", 2))
        }

        # 섹터 분류 설정
        sector_conf = self._config.get("sector_classification", {})
        self._sector_classification_config = {
            "enabled": bool(sector_conf.get("enabled", True)),
            "min_confidence": float(sector_conf.get("min_confidence", 0.1)),
            "top_subcategories": int(sector_conf.get("top_subcategories", 3))
        }

    def get_admin_keywords(self) -> dict[str, int]:
        return dict(self._admin_keywords)

    def get_whitelist(self) -> list[str]:
        return list(self._whitelist)

    def get_blacklist(self) -> list[str]:
        return list(self._blacklist)

    def is_whitelist_enabled(self) -> bool:
        return bool(self._whitelist_enabled)

    def is_blacklist_enabled(self) -> bool:
        return bool(self._blacklist_enabled)

    def get_score_rules(self) -> dict[str, Any]:
        return dict(self._score_rules)

    def get_news_page_size(self) -> int:
        return int(self._news_page_size)

    def get_rss_auto_interval(self) -> int:
        return int(self._rss_auto_interval)

    def get_start_message(self) -> str:
        return self._start_message
    
    def get_clustering_config(self) -> dict[str, Any]:
        """클러스터링 설정 반환"""
        return dict(self._clustering_config)
    
    def get_cluster_keyword_extraction(self) -> dict[str, Any]:
        """클러스터 키워드 추출 설정 반환"""
        return dict(self._cluster_keyword_config)

    def get_sector_classification_config(self) -> dict[str, Any]:
        """섹터 분류 설정 반환"""
        return dict(self._sector_classification_config)


super_controller = SuperController()
