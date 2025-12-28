"""
Sector classification module for news articles
Classifies articles into major sectors and subcategories based on keywords
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import Counter

from app.classification.sector_definitions import (
    SECTOR_DEFINITIONS,
    get_all_sectors,
    get_sector_keywords,
    get_subcategories,
    get_subcategory_keywords
)


@dataclass
class SectorMatch:
    """섹터 매칭 결과"""
    sector_id: str
    sector_name: str
    confidence: float
    matched_keywords: List[str]


@dataclass
class SubcategoryMatch:
    """하위 카테고리 매칭 결과"""
    subcategory_id: str
    subcategory_name: str
    confidence: float
    matched_keywords: List[str]


@dataclass
class ClassifiedArticle:
    """분류된 기사"""
    article: dict
    primary_sector: Optional[SectorMatch]
    secondary_sector: Optional[SectorMatch]
    subcategories: List[SubcategoryMatch]
    classification_score: float


class SectorClassifier:
    """뉴스 기사 섹터 분류기"""

    def __init__(self, min_confidence: float = 0.1):
        """
        Args:
            min_confidence: 최소 신뢰도 임계값 (0.0 ~ 1.0)
        """
        self.min_confidence = min_confidence
        self.sector_definitions = SECTOR_DEFINITIONS

    def classify(self, article: dict) -> ClassifiedArticle:
        """
        기사를 분석하여 섹터 및 하위 카테고리로 분류

        Args:
            article: 뉴스 기사 딕셔너리

        Returns:
            ClassifiedArticle: 분류 결과
        """
        # 1. 텍스트 추출 및 전처리
        text = self._extract_text(article)

        # 2. 섹터 분류
        sector_matches = self._classify_sectors(text)

        # 3. 하위 카테고리 분류
        subcategory_matches = self._classify_subcategories(text, sector_matches)

        # 4. 결과 구성
        primary_sector = sector_matches[0] if sector_matches else None
        secondary_sector = sector_matches[1] if len(sector_matches) > 1 else None

        # 분류 스코어 계산 (primary sector의 confidence)
        classification_score = primary_sector.confidence if primary_sector else 0.0

        return ClassifiedArticle(
            article=article,
            primary_sector=primary_sector,
            secondary_sector=secondary_sector,
            subcategories=subcategory_matches,
            classification_score=classification_score
        )

    def _extract_text(self, article: dict) -> str:
        """기사에서 텍스트 추출"""
        parts = [
            article.get("title", ""),
            article.get("description", ""),
            article.get("summary", ""),
            article.get("content", "")
        ]
        return " ".join(p for p in parts if p).lower()

    def _classify_sectors(self, text: str) -> List[SectorMatch]:
        """
        텍스트를 분석하여 섹터 분류

        Args:
            text: 분석할 텍스트 (소문자 변환됨)

        Returns:
            List[SectorMatch]: 신뢰도 순으로 정렬된 섹터 매칭 결과
        """
        sector_scores = {}
        sector_keywords_matched = {}

        for sector_id in get_all_sectors():
            keywords = get_sector_keywords(sector_id)
            matched = []

            for keyword in keywords:
                if keyword and keyword.lower() in text:
                    matched.append(keyword)

            if matched:
                sector_scores[sector_id] = len(matched)
                sector_keywords_matched[sector_id] = matched

        # 신뢰도 계산 (매칭된 키워드 수 / 전체 키워드 수)
        matches = []
        for sector_id, score in sector_scores.items():
            total_keywords = len(get_sector_keywords(sector_id))
            confidence = score / total_keywords if total_keywords > 0 else 0.0

            if confidence >= self.min_confidence:
                sector_name = SECTOR_DEFINITIONS[sector_id]["name"]
                matches.append(SectorMatch(
                    sector_id=sector_id,
                    sector_name=sector_name,
                    confidence=confidence,
                    matched_keywords=sector_keywords_matched[sector_id]
                ))

        # 신뢰도 순으로 정렬
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def _classify_subcategories(
        self,
        text: str,
        sector_matches: List[SectorMatch]
    ) -> List[SubcategoryMatch]:
        """
        텍스트를 분석하여 하위 카테고리 분류
        우선순위가 높은 섹터의 하위 카테고리부터 검사

        Args:
            text: 분석할 텍스트
            sector_matches: 매칭된 섹터 목록

        Returns:
            List[SubcategoryMatch]: 신뢰도 순으로 정렬된 하위 카테고리 매칭 결과
        """
        subcategory_scores = {}
        subcategory_keywords_matched = {}
        subcategory_to_sector = {}

        # 매칭된 섹터들의 하위 카테고리 검사
        sectors_to_check = [sm.sector_id for sm in sector_matches] if sector_matches else get_all_sectors()

        for sector_id in sectors_to_check:
            subcategories = get_subcategories(sector_id)

            for subcat_id, subcat_data in subcategories.items():
                keywords = subcat_data.get("keywords", [])
                matched = []

                for keyword in keywords:
                    if keyword and keyword.lower() in text:
                        matched.append(keyword)

                if matched:
                    full_id = f"{sector_id}.{subcat_id}"
                    subcategory_scores[full_id] = len(matched)
                    subcategory_keywords_matched[full_id] = matched
                    subcategory_to_sector[full_id] = sector_id

        # 신뢰도 계산
        matches = []
        for full_id, score in subcategory_scores.items():
            sector_id = subcategory_to_sector[full_id]
            subcat_id = full_id.split(".", 1)[1]

            subcategories = get_subcategories(sector_id)
            total_keywords = len(subcategories[subcat_id].get("keywords", []))
            confidence = score / total_keywords if total_keywords > 0 else 0.0

            if confidence >= self.min_confidence:
                subcat_name = subcategories[subcat_id]["name"]
                matches.append(SubcategoryMatch(
                    subcategory_id=full_id,
                    subcategory_name=subcat_name,
                    confidence=confidence,
                    matched_keywords=subcategory_keywords_matched[full_id]
                ))

        # 신뢰도 순으로 정렬
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches


# 전역 분류기 인스턴스
_classifier_instance: Optional[SectorClassifier] = None


def get_classifier(min_confidence: float = 0.1) -> SectorClassifier:
    """
    전역 분류기 인스턴스 반환

    Args:
        min_confidence: 최소 신뢰도 임계값

    Returns:
        SectorClassifier: 분류기 인스턴스
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SectorClassifier(min_confidence=min_confidence)
    return _classifier_instance


def classify_article(article: dict, min_confidence: float = 0.1) -> ClassifiedArticle:
    """
    단일 기사 분류 편의 함수

    Args:
        article: 뉴스 기사 딕셔너리
        min_confidence: 최소 신뢰도 임계값

    Returns:
        ClassifiedArticle: 분류 결과
    """
    classifier = get_classifier(min_confidence)
    return classifier.classify(article)


def classify_articles(
    articles: List[dict],
    min_confidence: float = 0.1
) -> List[ClassifiedArticle]:
    """
    여러 기사 일괄 분류 편의 함수

    Args:
        articles: 뉴스 기사 딕셔너리 리스트
        min_confidence: 최소 신뢰도 임계값

    Returns:
        List[ClassifiedArticle]: 분류 결과 리스트
    """
    classifier = get_classifier(min_confidence)
    return [classifier.classify(article) for article in articles]


def get_sector_statistics(classified_articles: List[ClassifiedArticle]) -> Dict[str, int]:
    """
    분류된 기사들의 섹터 통계

    Args:
        classified_articles: 분류된 기사 리스트

    Returns:
        Dict[str, int]: 섹터별 기사 수
    """
    sector_counts = Counter()

    for ca in classified_articles:
        if ca.primary_sector:
            sector_counts[ca.primary_sector.sector_name] += 1

    return dict(sector_counts)


def get_subcategory_statistics(classified_articles: List[ClassifiedArticle]) -> Dict[str, int]:
    """
    분류된 기사들의 하위 카테고리 통계

    Args:
        classified_articles: 분류된 기사 리스트

    Returns:
        Dict[str, int]: 하위 카테고리별 기사 수
    """
    subcat_counts = Counter()

    for ca in classified_articles:
        for subcat in ca.subcategories:
            subcat_counts[subcat.subcategory_name] += 1

    return dict(subcat_counts)
