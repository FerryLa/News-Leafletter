# storage.py - SQLite 기반으로 리팩토링 (기존 API 유지)
"""
User keyword storage using SQLite database
기존 JSON 기반 API와 호환성 유지
"""
from __future__ import annotations
from typing import List

from app.database.db_manager import get_db


def get_keywords(chat_id: int) -> List[str]:
    """
    특정 chat_id의 모든 키워드 가져오기
    
    Args:
        chat_id: 텔레그램 chat ID
    
    Returns:
        키워드 리스트
    """
    db = get_db()
    return db.get_keywords(chat_id)


def add_keyword(chat_id: int, keyword: str) -> List[str]:
    """
    키워드 추가
    
    Args:
        chat_id: 텔레그램 chat ID
        keyword: 추가할 키워드
    
    Returns:
        업데이트된 전체 키워드 리스트
    """
    db = get_db()
    db.add_keyword(chat_id, keyword)
    return db.get_keywords(chat_id)


def remove_keyword(chat_id: int, keyword: str) -> List[str]:
    """
    키워드 삭제
    
    Args:
        chat_id: 텔레그램 chat ID
        keyword: 삭제할 키워드
    
    Returns:
        업데이트된 전체 키워드 리스트
    """
    db = get_db()
    db.remove_keyword(chat_id, keyword)
    return db.get_keywords(chat_id)


# ==================== 추가 기능 (선택사항) ====================

def clear_all_keywords(chat_id: int) -> int:
    """
    특정 유저의 모든 키워드 삭제
    
    Args:
        chat_id: 텔레그램 chat ID
    
    Returns:
        삭제된 키워드 개수
    """
    db = get_db()
    return db.clear_keywords(chat_id)
