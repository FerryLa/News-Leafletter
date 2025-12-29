"""
JSON to SQLite Migration Tool
기존 JSON 파일들을 SQLite 데이터베이스로 마이그레이션
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.database.db_manager import DatabaseManager


class DataMigrator:
    """JSON → SQLite 마이그레이션 도구"""
    
    def __init__(self, db: DatabaseManager, data_dir: Path):
        self.db = db
        self.data_dir = Path(data_dir)
    
    def migrate_all(self, backup: bool = True) -> Dict[str, Any]:
        """
        모든 JSON 데이터를 SQLite로 마이그레이션
        
        Args:
            backup: True면 JSON 파일을 .backup으로 백업
        
        Returns:
            마이그레이션 통계
        """
        stats = {
            "watchlist": 0,
            "rss_cache": 0,
            "errors": []
        }
        
        print("=" * 60)
        print("🚀 JSON → SQLite 마이그레이션 시작")
        print("=" * 60)
        
        # 1. watchlist.json 마이그레이션
        try:
            keywords_count = self._migrate_watchlist()
            stats["watchlist"] = keywords_count
            print(f"✅ watchlist.json: {keywords_count}개 키워드 마이그레이션 완료")
        except Exception as e:
            stats["errors"].append(f"watchlist 마이그레이션 실패: {e}")
            print(f"❌ watchlist.json 마이그레이션 실패: {e}")
        
        # 2. rss_state.json 마이그레이션
        try:
            cache_count = self._migrate_rss_state()
            stats["rss_cache"] = cache_count
            print(f"✅ rss_state.json: {cache_count}개 캐시 마이그레이션 완료")
        except Exception as e:
            stats["errors"].append(f"rss_state 마이그레이션 실패: {e}")
            print(f"❌ rss_state.json 마이그레이션 실패: {e}")
        
        # 3. 백업 (선택사항)
        if backup:
            self._backup_json_files()
            print("💾 JSON 파일 백업 완료")
        
        print("=" * 60)
        print("🎉 마이그레이션 완료!")
        print("=" * 60)
        
        return stats
    
    def _migrate_watchlist(self) -> int:
        """
        watchlist.json → user_keywords 테이블
        
        Returns:
            마이그레이션된 키워드 개수
        """
        watchlist_path = self.data_dir / "watchlist.json"
        
        if not watchlist_path.exists():
            print("⚠️  watchlist.json이 없습니다. 스킵합니다.")
            return 0
        
        # JSON 로드
        with open(watchlist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 데이터 구조: {"chat_id": ["keyword1", "keyword2", ...], ...}
        total_keywords = 0
        
        with self.db.transaction():
            for chat_id_str, keywords in data.items():
                try:
                    chat_id = int(chat_id_str)
                except ValueError:
                    print(f"⚠️  잘못된 chat_id: {chat_id_str}")
                    continue
                
                for keyword in keywords:
                    self.db.add_keyword(chat_id, keyword)
                    total_keywords += 1
        
        return total_keywords
    
    def _migrate_rss_state(self) -> int:
        """
        rss_state.json → rss_cache 테이블
        
        Returns:
            마이그레이션된 캐시 개수
        """
        rss_state_path = self.data_dir / "rss_state.json"
        
        if not rss_state_path.exists():
            print("⚠️  rss_state.json이 없습니다. 스킵합니다.")
            return 0
        
        # JSON 로드
        with open(rss_state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 데이터 구조: {"seen_ids": [...], "timestamps": {...}}
        seen_ids = data.get("seen_ids", [])
        timestamps = data.get("timestamps", {})
        
        total_cached = 0
        
        with self.db.transaction():
            for article_id in seen_ids:
                # timestamps에서 first_seen 가져오기
                timestamp = timestamps.get(article_id)
                
                # SQLite에 삽입
                conn = self.db._get_connection()
                cursor = conn.cursor()
                
                if timestamp:
                    # 타임스탬프가 있으면 사용
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO rss_cache (article_id, first_seen)
                        VALUES (?, ?)
                        """,
                        (article_id, timestamp)
                    )
                else:
                    # 없으면 현재 시각 사용
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO rss_cache (article_id)
                        VALUES (?)
                        """,
                        (article_id,)
                    )
                
                total_cached += 1
        
        return total_cached
    
    def _backup_json_files(self) -> None:
        """JSON 파일들을 .backup으로 백업"""
        json_files = [
            "watchlist.json",
            "rss_state.json"
        ]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for filename in json_files:
            json_path = self.data_dir / filename
            if json_path.exists():
                backup_path = self.data_dir / f"{filename}.{timestamp}.backup"
                json_path.rename(backup_path)
                print(f"  📁 {filename} → {backup_path.name}")
    
    def verify_migration(self) -> Dict[str, Any]:
        """
        마이그레이션 결과 검증
        
        Returns:
            검증 통계
        """
        print("\n" + "=" * 60)
        print("🔍 마이그레이션 검증 중...")
        print("=" * 60)
        
        stats = {}
        
        # 1. 키워드 개수 확인
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user_keywords")
        keyword_count = cursor.fetchone()[0]
        stats["total_keywords"] = keyword_count
        print(f"✅ 총 키워드: {keyword_count}개")
        
        cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM user_keywords")
        user_count = cursor.fetchone()[0]
        stats["total_users"] = user_count
        print(f"✅ 총 유저: {user_count}명")
        
        # 2. RSS 캐시 개수 확인
        cursor.execute("SELECT COUNT(*) FROM rss_cache")
        cache_count = cursor.fetchone()[0]
        stats["total_cache"] = cache_count
        print(f"✅ 총 RSS 캐시: {cache_count}개")
        
        # 3. DB 크기 확인
        db_size = self.db.get_db_size() / 1024  # KB
        stats["db_size_kb"] = db_size
        print(f"✅ DB 크기: {db_size:.2f} KB")
        
        print("=" * 60)
        
        return stats


def migrate_json_to_sqlite(
    data_dir: Path | str,
    db_path: Path | str | None = None,
    backup: bool = True
) -> Dict[str, Any]:
    """
    JSON 데이터를 SQLite로 마이그레이션하는 헬퍼 함수
    
    Args:
        data_dir: data 디렉토리 경로
        db_path: SQLite DB 경로 (None이면 기본 경로)
        backup: JSON 파일 백업 여부
    
    Returns:
        마이그레이션 통계
    """
    from app.database.db_manager import get_db
    
    # DB 인스턴스 생성
    db = get_db(db_path)
    
    # 마이그레이터 생성 및 실행
    migrator = DataMigrator(db, Path(data_dir))
    stats = migrator.migrate_all(backup=backup)
    
    # 검증
    verification = migrator.verify_migration()
    stats["verification"] = verification
    
    return stats


if __name__ == "__main__":
    """CLI에서 직접 실행 가능"""
    import sys
    
    # 프로젝트 루트 기준 경로
    base_dir = Path(__file__).resolve().parents[2]
    data_dir = base_dir / "data"
    
    print("\n🔧 News-Leafletter 마이그레이션 도구")
    print(f"📂 데이터 디렉토리: {data_dir}")
    
    # 확인 메시지
    confirm = input("\n⚠️  JSON 파일을 SQLite로 마이그레이션하시겠습니까? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ 취소되었습니다.")
        sys.exit(0)
    
    # 마이그레이션 실행
    try:
        stats = migrate_json_to_sqlite(data_dir, backup=True)
        
        print("\n✅ 마이그레이션 성공!")
        print(f"📊 통계: {stats}")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
