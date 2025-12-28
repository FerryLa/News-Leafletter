"""
News sector classification module
Classifies news articles into major sectors and subcategories
"""

from app.classification.sector_classifier import (
    SectorClassifier,
    ClassifiedArticle,
    classify_article,
    classify_articles
)

__all__ = [
    'SectorClassifier',
    'ClassifiedArticle',
    'classify_article',
    'classify_articles'
]
