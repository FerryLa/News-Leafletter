"""
Simple news clustering module for News-Leafletter
Clusters scored articles by similarity to reduce noise and group related news
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.super_controller import super_controller
from app.scoring.keyword_scoring import ScoredArticle


@dataclass
class ClusteredNews:
    """클러스터링된 뉴스 그룹"""
    cluster_id: int
    main_article: ScoredArticle  # 대표 기사 (highest score)
    related_articles: List[ScoredArticle]  # 관련 기사들
    cluster_keywords: List[str]  # 클러스터 키워드
    total_count: int  # 전체 기사 수
    avg_score: float  # 평균 스코어
    # 섹터 분류 정보
    primary_sector: Optional[str] = None  # 주요 섹터
    secondary_sector: Optional[str] = None  # 부 섹터
    subcategories: List[str] = None  # 하위 카테고리들

    def __post_init__(self):
        """초기화 후 처리"""
        if self.subcategories is None:
            self.subcategories = []


class NewsClusterer:
    """간단한 뉴스 클러스터링 클래스"""
    
    def __init__(self):
        self.config = super_controller.get_clustering_config()
    
    def is_enabled(self) -> bool:
        """클러스터링 활성화 여부"""
        return self.config.get("enabled", False)
    
    def cluster(self, scored_articles: List[ScoredArticle]) -> List[ClusteredNews]:
        """
        스코어링된 기사를 클러스터링
        
        Args:
            scored_articles: 스코어링된 기사 리스트
        
        Returns:
            클러스터링된 뉴스 그룹 리스트
        """
        if not self.is_enabled():
            # 클러스터링 비활성화 시 각 기사를 개별 클러스터로
            return self._format_without_clustering(scored_articles)
        
        if len(scored_articles) < 2:
            # 기사가 너무 적으면 클러스터링 불필요
            return self._format_without_clustering(scored_articles)
        
        try:
            # 1. 텍스트 추출
            texts = self._extract_texts(scored_articles)
            
            # 2. TF-IDF 벡터화
            vectorizer_config = self.config["vectorizer"]
            vectorizer = TfidfVectorizer(
                max_features=vectorizer_config["max_features"],
                ngram_range=tuple(vectorizer_config["ngram_range"]),
                min_df=1
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 3. 유사도 계산
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 4. 간단한 클러스터링 (threshold 기반)
            clusters = self._simple_clustering(similarity_matrix, scored_articles)
            
            # 5. 클러스터 키워드 추출
            clustered_results = self._finalize_clusters(
                clusters, 
                texts, 
                vectorizer
            )
            
            return clustered_results
            
        except Exception as e:
            print(f"클러스터링 중 오류 발생: {e}")
            return self._format_without_clustering(scored_articles)
    
    def _extract_texts(self, scored_articles: List[ScoredArticle]) -> List[str]:
        """기사에서 텍스트 추출"""
        texts = []
        for sa in scored_articles:
            article = sa.article
            parts = [
                article.get("title", ""),
                article.get("description", ""),
                article.get("summary", ""),
            ]
            text = " ".join(p for p in parts if p)
            texts.append(text.lower())
        return texts
    
    def _simple_clustering(
        self, 
        similarity_matrix: np.ndarray,
        scored_articles: List[ScoredArticle]
    ) -> Dict[int, List[int]]:
        """
        단순 threshold 기반 클러스터링
        유사도가 threshold 이상인 기사들을 같은 클러스터로 묶음
        """
        threshold = self.config["similarity_threshold"]
        n_articles = len(scored_articles)
        
        # 클러스터 할당 (-1: 미할당)
        cluster_assignments = [-1] * n_articles
        current_cluster_id = 0
        
        for i in range(n_articles):
            if cluster_assignments[i] != -1:
                continue  # 이미 할당됨
            
            # 새 클러스터 생성
            cluster_assignments[i] = current_cluster_id
            
            # i번 기사와 유사한 기사들 찾기
            for j in range(i + 1, n_articles):
                if cluster_assignments[j] != -1:
                    continue
                
                if similarity_matrix[i][j] >= threshold:
                    cluster_assignments[j] = current_cluster_id
            
            current_cluster_id += 1
        
        # 클러스터별로 기사 인덱스 그룹화
        clusters: Dict[int, List[int]] = {}
        for idx, cluster_id in enumerate(cluster_assignments):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(idx)
        
        return clusters
    
    def _finalize_clusters(
        self,
        clusters: Dict[int, List[int]],
        texts: List[str],
        vectorizer: TfidfVectorizer
    ) -> List[ClusteredNews]:
        """클러스터 정보 완성"""
        from app.scoring.keyword_scoring import ScoredArticle
        
        results = []
        
        for cluster_id, indices in clusters.items():
            # 해당 클러스터의 기사들
            cluster_articles = [self._articles[i] for i in indices]
            
            # 스코어 순 정렬
            cluster_articles.sort(key=lambda x: x.score, reverse=True)
            
            # 평균 스코어
            avg_score = np.mean([a.score for a in cluster_articles])
            
            # 클러스터 키워드 추출
            cluster_texts = [texts[i] for i in indices]
            keywords = self._extract_keywords(cluster_texts, vectorizer)
            
            # 대표 기사와 관련 기사 분리
            selection_config = self.config["selection"]
            articles_per_cluster = selection_config["articles_per_cluster"]
            
            main_article = cluster_articles[0]
            related = cluster_articles[1:articles_per_cluster]
            
            results.append(ClusteredNews(
                cluster_id=cluster_id,
                main_article=main_article,
                related_articles=related,
                cluster_keywords=keywords,
                total_count=len(cluster_articles),
                avg_score=float(avg_score)
            ))
        
        # 평균 스코어로 정렬
        results.sort(key=lambda x: x.avg_score, reverse=True)
        
        # 최대 기사 수 제한
        max_total = selection_config["max_total_articles"]
        article_count = 0
        filtered_results = []
        
        for cluster in results:
            if article_count >= max_total:
                break
            filtered_results.append(cluster)
            article_count += 1 + len(cluster.related_articles)
        
        return filtered_results
    
    def _extract_keywords(
        self, 
        texts: List[str], 
        vectorizer: TfidfVectorizer
    ) -> List[str]:
        """클러스터의 주요 키워드 추출"""
        keyword_config = super_controller.get_cluster_keyword_extraction()
        
        if not keyword_config.get("enabled", True):
            return []
        
        if len(texts) < keyword_config.get("min_df", 2):
            return []
        
        try:
            # 간단한 빈도 기반 키워드
            from collections import Counter
            
            all_words = []
            for text in texts:
                words = text.split()
                # 2글자 이상, 의미있는 단어만
                all_words.extend([
                    w for w in words 
                    if len(w) > 1 and w.isalnum()
                ])
            
            word_counts = Counter(all_words)
            top_n = keyword_config.get("top_n", 3)
            
            # 상위 N개
            top_words = [word for word, count in word_counts.most_common(top_n)]
            return top_words
            
        except Exception:
            return []
    
    def _format_without_clustering(
        self, 
        scored_articles: List[ScoredArticle]
    ) -> List[ClusteredNews]:
        """클러스터링 없이 각 기사를 개별 클러스터로"""
        selection_config = self.config.get("selection", {})
        max_total = selection_config.get("max_total_articles", 15)
        
        results = []
        for idx, sa in enumerate(scored_articles[:max_total]):
            results.append(ClusteredNews(
                cluster_id=idx,
                main_article=sa,
                related_articles=[],
                cluster_keywords=[],
                total_count=1,
                avg_score=float(sa.score)
            ))
        
        return results


# 전역 변수로 기사 저장 (임시)
_clusterer_instance = None
_articles_cache = []


def cluster_scored_articles(scored_articles: List[ScoredArticle]) -> List[ClusteredNews]:
    """
    스코어링된 기사를 클러스터링하는 편의 함수
    섹터 분류도 함께 수행

    Issue #36: 단독 뉴스는 클러스터링 제외 (언론사별 모두 전달)

    Args:
        scored_articles: ScoredArticle 리스트

    Returns:
        ClusteredNews 리스트 (섹터 정보 포함)
    """
    from app.scoring.breaking_detector import is_exclusive_news

    global _clusterer_instance, _articles_cache

    if _clusterer_instance is None:
        _clusterer_instance = NewsClusterer()

    # Issue #36: 단독 뉴스와 일반 뉴스 분리
    exclusive_articles = []
    regular_articles = []

    for sa in scored_articles:
        title = sa.article.get("title", "")
        if is_exclusive_news(title):
            # 단독 뉴스는 클러스터링 제외
            exclusive_articles.append(sa)
        else:
            # 일반 뉴스(속보 포함)는 클러스터링
            regular_articles.append(sa)

    # 기사 캐시 (클러스터링 중 접근용)
    _articles_cache = regular_articles
    _clusterer_instance._articles = regular_articles

    # 일반 뉴스만 클러스터링 수행
    clustered = _clusterer_instance.cluster(regular_articles)

    # 단독 뉴스를 개별 클러스터로 추가
    for idx, sa in enumerate(exclusive_articles):
        clustered.append(ClusteredNews(
            cluster_id=len(clustered) + idx,
            main_article=sa,
            related_articles=[],
            cluster_keywords=["단독"],
            total_count=1,
            avg_score=float(sa.score)
        ))

    # 섹터 분류 활성화 여부 확인
    sector_config = super_controller.get_sector_classification_config()
    if not sector_config.get("enabled", True):
        return clustered

    # 각 클러스터에 섹터 분류 추가
    try:
        from app.classification.sector_classifier import classify_article

        for cluster in clustered:
            # 대표 기사로 섹터 분류
            classified = classify_article(
                cluster.main_article.article,
                min_confidence=sector_config.get("min_confidence", 0.1)
            )

            # 섹터 정보 추가
            if classified.primary_sector:
                cluster.primary_sector = classified.primary_sector.sector_name
            if classified.secondary_sector:
                cluster.secondary_sector = classified.secondary_sector.sector_name

            # 상위 N개 하위 카테고리만 추가
            top_n = sector_config.get("top_subcategories", 3)
            cluster.subcategories = [
                sc.subcategory_name for sc in classified.subcategories[:top_n]
            ]

            # Issue #34: 대표 기사의 원본 딕셔너리에 섹터 정보 추가 (DB 저장용)
            cluster.main_article.article["primary_sector"] = cluster.primary_sector or "other"
            cluster.main_article.article["secondary_sector"] = cluster.secondary_sector
            cluster.main_article.article["subcategories"] = cluster.subcategories

            # 관련 기사들에도 동일한 섹터 정보 추가
            for related in cluster.related_articles:
                related.article["primary_sector"] = cluster.primary_sector or "other"
                related.article["secondary_sector"] = cluster.secondary_sector
                related.article["subcategories"] = cluster.subcategories

    except Exception as e:
        print(f"섹터 분류 중 오류 발생: {e}")
        # 오류가 발생해도 클러스터링 결과는 반환

    return clustered
