"""
SQLite Database Manager for News-Leafletter
Centralized database management with transaction support and connection pooling
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from contextlib import contextmanager
import threading
import json
from typing import List, Dict, Any, Optional, Tuple  # ← Tuple 확인


class DatabaseManager:
    """
    SQLite 데이터베이스 매니저
    
    Features:
    - Thread-safe 연결 관리
    - 자동 스키마 마이그레이션
    - 트랜잭션 지원
    - 컨텍스트 매니저 지원
    """
    
    # 스키마 버전 (마이그레이션 추적용)
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # 초기화
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Thread-safe 연결 가져오기"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # WAL 모드 활성화 (동시성 향상)
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저
        
        Usage:
            with db.transaction():
                db.add_keyword(chat_id, keyword)
                db.add_keyword(chat_id, keyword2)
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _initialize_database(self) -> None:
        """데이터베이스 초기화 및 스키마 생성"""
        conn = self._get_connection()
        
        # 스키마 생성
        conn.executescript("""
            -- 유저 관심 키워드
            CREATE TABLE IF NOT EXISTS user_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, keyword)
            );
            CREATE INDEX IF NOT EXISTS idx_user_keywords_chat 
                ON user_keywords(chat_id);
            
            -- RSS 캐시 (중복 제거용)
            CREATE TABLE IF NOT EXISTS rss_cache (
                article_id TEXT PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_url TEXT,
                title TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_rss_cache_first_seen 
                ON rss_cache(first_seen);
            
            -- 뉴스 전송 히스토리 (분석/통계용)
            CREATE TABLE IF NOT EXISTS news_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                article_url TEXT,
                article_id TEXT,
                title TEXT,
                score INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_news_history_chat 
                ON news_history(chat_id);
            CREATE INDEX IF NOT EXISTS idx_news_history_sent 
                ON news_history(sent_at);
            
            -- 기사 저장소 (전체 기사 아카이브)
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                source_name TEXT,
                source_url TEXT,
                published_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_url TEXT,
                author TEXT,
                category TEXT,
                language TEXT DEFAULT 'ko'
            );
            CREATE INDEX IF NOT EXISTS idx_articles_article_id 
                ON articles(article_id);
            CREATE INDEX IF NOT EXISTS idx_articles_published 
                ON articles(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_source 
                ON articles(source_name);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url 
                ON articles(url);
            
            -- 유저 피드백 (좋아요/싫어요, 북마크 등)
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                article_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                feedback_value INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(article_id),
                UNIQUE(chat_id, article_id, feedback_type)
            );
            CREATE INDEX IF NOT EXISTS idx_user_feedback_chat 
                ON user_feedback(chat_id);
            CREATE INDEX IF NOT EXISTS idx_user_feedback_article 
                ON user_feedback(article_id);
            CREATE INDEX IF NOT EXISTS idx_user_feedback_type 
                ON user_feedback(feedback_type);
            
            -- 설정 (키-값 저장소)
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- 스키마 버전 관리
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        
        # 스키마 버전 확인 및 업데이트
        self._update_schema_version()

        # ✅ Issue #22: link 컬럼 마이그레이션 (여기 추가!)
        self._migrate_for_issue_22()
    
    def _update_schema_version(self) -> None:
        """스키마 버전 업데이트"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        current_version = row[0] if row[0] is not None else 0
        
        if current_version < self.SCHEMA_VERSION:
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,)
            )
            conn.commit()
    
    def _migrate_for_issue_22(self) -> None:
        """
        Issue #22: RSS 중복 필터링을 위한 스키마 마이그레이션
        
        - articles 테이블에 link 컬럼 추가
        - link 컬럼에 UNIQUE 인덱스 생성
        - 기존 url 데이터를 link로 복사
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. link 컬럼 존재 여부 확인
            cursor.execute("PRAGMA table_info(articles)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'link' not in columns:
                print("🔧 [Issue #22] articles 테이블 마이그레이션 시작...")
                
                # 2. link 컬럼 추가
                conn.execute("ALTER TABLE articles ADD COLUMN link TEXT")
                print("   ✓ link 컬럼 추가 완료")
                
                # 3. 기존 url 값을 link로 복사
                conn.execute("UPDATE articles SET link = url WHERE link IS NULL")
                print("   ✓ 기존 url 데이터를 link로 복사 완료")
                
                # 4. link 컬럼에 UNIQUE 인덱스 생성
                try:
                    conn.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_link_unique
                        ON articles(link)
                    """)
                    print("   ✓ link 컬럼 UNIQUE 인덱스 생성 완료")
                except sqlite3.IntegrityError as e:
                    print(f"   ⚠ UNIQUE 인덱스 생성 실패 (중복 데이터 존재): {e}")
                
                conn.commit()
                print("✅ [Issue #22] 마이그레이션 완료!")
            else:
                # link 컬럼이 이미 존재하면 인덱스만 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name='idx_articles_link_unique'
                """)
                if not cursor.fetchone():
                    try:
                        conn.execute("""
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_link_unique
                            ON articles(link)
                        """)
                        conn.commit()
                        print("✅ [Issue #22] link 인덱스 생성 완료")
                    except sqlite3.IntegrityError:
                        pass
        
        except Exception as e:
            print(f"❌ [Issue #22] 마이그레이션 실패: {e}")
            conn.rollback()


    # ==================== 유저 키워드 관련 ====================
    
    def get_keywords(self, chat_id: int) -> List[str]:
        """특정 chat_id의 모든 키워드 가져오기"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT keyword FROM user_keywords WHERE chat_id = ? ORDER BY created_at",
            (chat_id,)
        )
        
        return [row[0] for row in cursor.fetchall()]
    
    def add_keyword(self, chat_id: int, keyword: str) -> bool:
        """
        키워드 추가
        
        Returns:
            True if 새로 추가됨, False if 이미 존재함
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO user_keywords (chat_id, keyword) VALUES (?, ?)",
                (chat_id, keyword)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # UNIQUE 제약 위반 (이미 존재)
            return False
    
    def remove_keyword(self, chat_id: int, keyword: str) -> bool:
        """
        키워드 삭제
        
        Returns:
            True if 삭제됨, False if 존재하지 않음
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM user_keywords WHERE chat_id = ? AND keyword = ?",
            (chat_id, keyword)
        )
        conn.commit()
        
        return cursor.rowcount > 0
    
    def clear_keywords(self, chat_id: int) -> int:
        """
        특정 chat_id의 모든 키워드 삭제
        
        Returns:
            삭제된 키워드 개수
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM user_keywords WHERE chat_id = ?",
            (chat_id,)
        )
        conn.commit()
        
        return cursor.rowcount
    
    # ==================== RSS 캐시 관련 ====================
    
    def is_article_seen(self, article_id: str) -> bool:
        """기사가 이미 본 것인지 확인"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM rss_cache WHERE article_id = ?",
            (article_id,)
        )
        
        return cursor.fetchone() is not None
    
    def mark_article_seen(
        self, 
        article_id: str, 
        source_url: str = "", 
        title: str = ""
    ) -> None:
        """기사를 '본 것'으로 표시"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT OR IGNORE INTO rss_cache (article_id, source_url, title)
            VALUES (?, ?, ?)
            """,
            (article_id, source_url, title)
        )
        conn.commit()
    
    def get_seen_article_ids(self, limit: int = 10000) -> List[str]:
        """
        최근 본 기사 ID 목록 가져오기
        
        Args:
            limit: 최대 개수 (기본값: 10000)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT article_id 
            FROM rss_cache 
            ORDER BY first_seen DESC 
            LIMIT ?
            """,
            (limit,)
        )
        
        return [row[0] for row in cursor.fetchall()]
    
    def cleanup_old_cache(self, days: int = 7) -> int:
        """
        오래된 캐시 삭제
        
        Args:
            days: 며칠 이전 데이터를 삭제할지
        
        Returns:
            삭제된 레코드 수
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            DELETE FROM rss_cache 
            WHERE first_seen < datetime('now', '-' || ? || ' days')
            """,
            (days,)
        )
        conn.commit()
        
        return cursor.rowcount
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 전체 캐시 수
        cursor.execute("SELECT COUNT(*) FROM rss_cache")
        total = cursor.fetchone()[0]
        
        # 오늘 추가된 수
        cursor.execute(
            """
            SELECT COUNT(*) FROM rss_cache 
            WHERE DATE(first_seen) = DATE('now')
            """
        )
        today = cursor.fetchone()[0]
        
        # 가장 오래된 캐시
        cursor.execute("SELECT MIN(first_seen) FROM rss_cache")
        oldest = cursor.fetchone()[0]
        
        return {
            "total_cached": total,
            "cached_today": today,
            "oldest_cache": oldest,
        }
    
    # ==================== 뉴스 히스토리 관련 ====================
    
    def log_news_sent(
        self,
        chat_id: int,
        article_url: str,
        article_id: str = "",
        title: str = "",
        score: int = 0
    ) -> None:
        """뉴스 전송 기록 저장"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO news_history 
            (chat_id, article_url, article_id, title, score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, article_url, article_id, title, score)
        )
        conn.commit()
    
    def get_news_history(
        self,
        chat_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """특정 유저의 뉴스 수신 히스토리"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT article_url, title, score, sent_at
            FROM news_history
            WHERE chat_id = ?
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (chat_id, limit)
        )
        
        return [
            {
                "url": row[0],
                "title": row[1],
                "score": row[2],
                "sent_at": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    def get_popular_news(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        최근 N일간 가장 많이 전송된 뉴스
        
        Args:
            days: 기간 (일)
            limit: 결과 개수
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                title,
                article_url,
                COUNT(*) as send_count,
                AVG(score) as avg_score
            FROM news_history
            WHERE sent_at >= datetime('now', '-' || ? || ' days')
            GROUP BY article_url
            ORDER BY send_count DESC, avg_score DESC
            LIMIT ?
            """,
            (days, limit)
        )
        
        return [
            {
                "title": row[0],
                "url": row[1],
                "send_count": row[2],
                "avg_score": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    # ==================== 설정 관련 ====================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row is None:
            return default
        
        # JSON 파싱 시도
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return row[0]
    
    def set_setting(self, key: str, value: Any) -> None:
        """설정값 저장"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # JSON 직렬화
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (key, value)
        )
        conn.commit()
    
    def delete_setting(self, key: str) -> bool:
        """설정 삭제"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ==================== 유틸리티 ====================
    
    def vacuum(self) -> None:
        """데이터베이스 최적화 (공간 회수)"""
        conn = self._get_connection()
        conn.execute("VACUUM")
        conn.commit()
    
    def get_db_size(self) -> int:
        """데이터베이스 파일 크기 (bytes)"""
        return self.db_path.stat().st_size if self.db_path.exists() else 0
    
    # ==================== 기사 저장소 관련 ====================
    
    def save_article(
        self,
        article_id: str,
        title: str,
        url: str,
        summary: str = "",
        content: str = "",
        source_name: str = "",
        source_url: str = "",
        published_at: str = "",
        image_url: str = "",
        author: str = "",
        category: str = "",
        language: str = "ko"
    ) -> bool:
        """
        기사 저장 (아카이브용)
        
        Returns:
            True if 새로 저장됨, False if 이미 존재함
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO articles 
                (article_id, title, url, summary, content, source_name, 
                 source_url, published_at, image_url, author, category, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (article_id, title, url, summary, content, source_name,
                 source_url, published_at or None, image_url, author, category, language)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # UNIQUE 제약 위반 (이미 존재)
            return False
    
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """article_id로 기사 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT article_id, title, url, summary, content, source_name,
                   source_url, published_at, fetched_at, image_url, author,
                   category, language
            FROM articles
            WHERE article_id = ?
            """,
            (article_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "article_id": row[0],
            "title": row[1],
            "url": row[2],
            "summary": row[3],
            "content": row[4],
            "source_name": row[5],
            "source_url": row[6],
            "published_at": row[7],
            "fetched_at": row[8],
            "image_url": row[9],
            "author": row[10],
            "category": row[11],
            "language": row[12]
        }
    
    def search_articles(
        self,
        keyword: str = "",
        source_name: str = "",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """기사 검색"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if keyword:
            query += " AND (title LIKE ? OR summary LIKE ? OR content LIKE ?)"
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])
        
        if source_name:
            query += " AND source_name = ?"
            params.append(source_name)
        
        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "article_id": row[1],
                "title": row[2],
                "url": row[3],
                "summary": row[4],
                "source_name": row[6],
                "published_at": row[8]
            })
        
        return results
    
    # ==================== 유저 피드백 관련 ====================
    
    def add_feedback(
        self,
        chat_id: int,
        article_id: str,
        feedback_type: str,
        feedback_value: int = 0,
        comment: str = ""
    ) -> bool:
        """
        유저 피드백 추가
        
        Args:
            chat_id: 텔레그램 chat ID
            article_id: 기사 ID
            feedback_type: 피드백 타입 (like, dislike, bookmark, rating 등)
            feedback_value: 피드백 값 (예: 별점 1-5)
            comment: 추가 코멘트
        
        Returns:
            True if 성공
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_feedback
                (chat_id, article_id, feedback_type, feedback_value, comment)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, article_id, feedback_type, feedback_value, comment)
            )
            conn.commit()
            return True
        except Exception:
            return False
    
    def get_user_feedback(
        self,
        chat_id: int,
        feedback_type: str = ""
    ) -> List[Dict[str, Any]]:
        """특정 유저의 피드백 조회"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if feedback_type:
            cursor.execute(
                """
                SELECT article_id, feedback_type, feedback_value, comment, created_at
                FROM user_feedback
                WHERE chat_id = ? AND feedback_type = ?
                ORDER BY created_at DESC
                """,
                (chat_id, feedback_type)
            )
        else:
            cursor.execute(
                """
                SELECT article_id, feedback_type, feedback_value, comment, created_at
                FROM user_feedback
                WHERE chat_id = ?
                ORDER BY created_at DESC
                """,
                (chat_id,)
            )
        
        return [
            {
                "article_id": row[0],
                "feedback_type": row[1],
                "feedback_value": row[2],
                "comment": row[3],
                "created_at": row[4]
            }
            for row in cursor.fetchall()
        ]
    
    def get_article_feedback_stats(self, article_id: str) -> Dict[str, Any]:
        """특정 기사의 피드백 통계"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                feedback_type,
                COUNT(*) as count,
                AVG(feedback_value) as avg_value
            FROM user_feedback
            WHERE article_id = ?
            GROUP BY feedback_type
            """,
            (article_id,)
        )
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                "count": row[1],
                "avg_value": row[2]
            }
        
        return stats
    
   # ==================== Issue #22: RSS 중복 필터링 ====================

    def is_duplicate_by_link(self, link: str) -> bool:
        """
        Issue #22: link로 중복 기사 확인
        
        Args:
            link: 기사 링크 URL
        
        Returns:
            True if 중복 (이미 존재), False if 새 기사
        """
        if not link:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM articles WHERE link = ? LIMIT 1",
            (link,)
        )
        
        return cursor.fetchone() is not None

    def get_duplicate_links(self, links: List[str]) -> set[str]:
        """
        Issue #22: 배치로 중복 링크 찾기 (성능 최적화)
        
        Args:
            links: 체크할 링크 목록
        
        Returns:
            중복된 링크의 set (이미 DB에 존재하는 링크들)
        """
        if not links:
            return set()
        
        # 빈 문자열 필터링
        valid_links = [link for link in links if link]
        if not valid_links:
            return set()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # IN 쿼리로 한 번에 체크
        placeholders = ",".join("?" * len(valid_links))
        query = f"SELECT link FROM articles WHERE link IN ({placeholders})"
        
        cursor.execute(query, tuple(valid_links))
        
        return {row[0] for row in cursor.fetchall()}

    def save_articles_batch(
        self,
        articles: List[Dict[str, Any]],
        skip_duplicates: bool = True
    ) -> Tuple[int, int]:
        """
        Issue #22: 중복 제외하고 기사 배치 저장
        
        Args:
            articles: 저장할 기사 목록
            skip_duplicates: True면 중복 건너뛰기, False면 에러 발생
        
        Returns:
            (저장된 개수, 중복으로 제외된 개수)
        """
        if not articles:
            return (0, 0)
        
        # 1. 중복 체크
        new_articles = articles
        duplicated_count = 0
        
        if skip_duplicates:
            links = [a.get("link") or a.get("url", "") for a in articles]
            duplicate_links = self.get_duplicate_links(links)
            
            new_articles = [
                a for a in articles 
                if (a.get("link") or a.get("url", "")) not in duplicate_links
            ]
            
            duplicated_count = len(articles) - len(new_articles)
        
        # 2. 배치 저장
        conn = self._get_connection()
        cursor = conn.cursor()
        
        saved_count = 0
        
        for article in new_articles:
            try:
                # 필수 필드 추출
                link = article.get("link") or article.get("url", "")
                title = article.get("title", "")
                
                if not link or not title:
                    continue
                
                # 선택 필드 추출
                article_id = article.get("id") or article.get("article_id", "")
                summary = article.get("summary", "")
                source_url = article.get("source_url", "")
                published_at = article.get("published_raw") or article.get("published_at")
                fetched_at = article.get("fetched_at")
                
                # INSERT
                cursor.execute(
                    """
                    INSERT INTO articles 
                    (article_id, link, title, url, summary, source_url, 
                     published_at, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article_id,
                        link,
                        title,
                        link,
                        summary,
                        source_url,
                        published_at,
                        fetched_at or datetime.now(timezone.utc).isoformat()
                    )
                )
                
                saved_count += 1
                
            except sqlite3.IntegrityError as e:
                if skip_duplicates:
                    duplicated_count += 1
                else:
                    raise
            except Exception as e:
                print(f"⚠️ 기사 저장 실패: {e}")
                continue
        
        conn.commit()
        
        return (saved_count, duplicated_count)

    def get_recent_articles(
        self,
        limit: int = 100,
        source_name: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Issue #22: 최근 저장된 기사 조회
        
        Args:
            limit: 최대 개수
            source_name: 특정 출처만 조회 (선택)
        
        Returns:
            기사 목록 (최신순)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if source_name:
            cursor.execute(
                """
                SELECT article_id, link, title, summary, source_name, 
                       published_at, fetched_at
                FROM articles
                WHERE source_name = ?
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (source_name, limit)
            )
        else:
            cursor.execute(
                """
                SELECT article_id, link, title, summary, source_name, 
                       published_at, fetched_at
                FROM articles
                ORDER BY fetched_at DESC
                LIMIT ?
                """,
                (limit,)
            )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "article_id": row[0],
                "link": row[1],
                "title": row[2],
                "summary": row[3],
                "source_name": row[4],
                "published_at": row[5],
                "fetched_at": row[6]
            })
        
        return results

    def get_articles_statistics(self) -> Dict[str, Any]:
        """
        Issue #22: 기사 저장소 통계
        
        Returns:
            통계 정보 딕셔너리
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 전체 기사 수
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        
        # 오늘 저장된 기사 수
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE DATE(fetched_at) = DATE('now')
        """)
        today = cursor.fetchone()[0]
        
        # 출처별 기사 수 (상위 5개)
        cursor.execute("""
            SELECT source_name, COUNT(*) as count
            FROM articles
            WHERE source_name IS NOT NULL AND source_name != ''
            GROUP BY source_name
            ORDER BY count DESC
            LIMIT 5
        """)
        top_sources = [
            {"source": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]
        
        return {
            "total_articles": total,
            "articles_today": today,
            "top_sources": top_sources
        }

    def close(self) -> None:
        """연결 종료"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()


# ==================== 싱글톤 인스턴스 ====================

_db_instance: Optional[DatabaseManager] = None


def get_db(db_path: Optional[Path | str] = None) -> DatabaseManager:
    """
    DatabaseManager 싱글톤 인스턴스 가져오기
    
    Args:
        db_path: DB 경로 (None이면 기본 경로 사용)
    """
    global _db_instance
    
    if _db_instance is None:
        if db_path is None:
            # 기본 경로: data/news_leafletter.db
            base_dir = Path(__file__).resolve().parents[2]
            db_path = base_dir / "data" / "news_leafletter.db"
        
        _db_instance = DatabaseManager(db_path)
    
    return _db_instance
