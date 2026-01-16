"""
Migration script for Issue #61: Sector-Theme-Event 3-tier classification structure

Migrates from 5-sector to GICS-based 11-sector structure with separate theme and event tables.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/news_leafletter.db"


def create_new_tables(conn: sqlite3.Connection):
    """Create new tables for sector-theme-event structure"""
    cursor = conn.cursor()

    # 1. Create sectors table (11 GICS-based sectors)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sector_code TEXT UNIQUE NOT NULL,
            sector_name TEXT NOT NULL,
            sector_name_en TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Create themes table (flexible, expandable)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_code TEXT UNIQUE NOT NULL,
            theme_name TEXT NOT NULL,
            theme_name_en TEXT NOT NULL,
            description TEXT,
            keywords TEXT,  -- JSON array of keywords
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Create events table (specific incidents)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_code TEXT UNIQUE NOT NULL,
            event_name TEXT NOT NULL,
            event_name_en TEXT,
            description TEXT,
            start_date DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Create article_sectors junction table (one sector per article)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_sectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            sector_id INTEGER NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (sector_id) REFERENCES sectors(id) ON DELETE CASCADE,
            UNIQUE(article_id)  -- One sector per article
        )
    """)

    # 5. Create article_themes junction table (multiple themes per article)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            theme_id INTEGER NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
            UNIQUE(article_id, theme_id)  -- Prevent duplicates
        )
    """)

    # 6. Create article_events junction table (multiple events per article)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            relevance_score REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            UNIQUE(article_id, event_id)  -- Prevent duplicates
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_sectors_article ON article_sectors(article_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_sectors_sector ON article_sectors(sector_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_themes_article ON article_themes(article_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_themes_theme ON article_themes(theme_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_events_article ON article_events(article_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_events_event ON article_events(event_id)")

    conn.commit()
    print("[OK] Created new tables: sectors, themes, events, article_sectors, article_themes, article_events")


def insert_gics_sectors(conn: sqlite3.Connection):
    """Insert 11 GICS-based sectors"""
    cursor = conn.cursor()

    sectors = [
        ("ENERGY", "에너지", "Energy", "석유, 가스, 신재생 에너지 등"),
        ("MATERIALS", "소재", "Materials", "화학, 금속, 광업, 건설자재 등"),
        ("INDUSTRIALS", "산업재", "Industrials", "기계, 운송, 건설, 항공우주/방위 등"),
        ("IT", "IT", "Information Technology", "소프트웨어, 하드웨어, 반도체, IT서비스 등"),
        ("COMMUNICATION", "커뮤니케이션", "Communication Services", "통신, 미디어, 엔터테인먼트 등"),
        ("FINANCIALS", "금융", "Financials", "은행, 증권, 보험, 부동산금융 등"),
        ("HEALTHCARE", "헬스케어", "Healthcare", "제약, 바이오, 의료기기, 헬스케어서비스 등"),
        ("CONSUMER", "소비재", "Consumer Discretionary & Staples", "유통, 자동차, 의류, 식음료, 생필품 등"),
        ("UTILITIES", "유틸리티", "Utilities", "전력, 가스, 수도 등 공공서비스"),
        ("REAL_ESTATE", "부동산", "Real Estate", "부동산 개발, 운영, 리츠 등"),
        ("PUBLIC_POLICY", "정책·공공", "Public Policy & Government", "정부정책, 공공부문, 규제 등")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO sectors (sector_code, sector_name, sector_name_en, description)
        VALUES (?, ?, ?, ?)
    """, sectors)

    conn.commit()
    print(f"[OK] Inserted {len(sectors)} GICS-based sectors")


def insert_initial_themes(conn: sqlite3.Connection):
    """Insert initial themes (expandable)"""
    cursor = conn.cursor()

    themes = [
        ("SEMICONDUCTOR", "반도체", "Semiconductor", "반도체 제조, 설계, 장비", '["반도체", "칩", "웨이퍼", "파운드리"]'),
        ("BATTERY", "2차전지", "Secondary Battery", "전기차 배터리, ESS", '["배터리", "2차전지", "리튬", "양극재", "음극재"]'),
        ("AI", "AI", "Artificial Intelligence", "인공지능, 머신러닝, LLM", '["AI", "인공지능", "머신러닝", "딥러닝", "ChatGPT"]'),
        ("AUTONOMOUS", "자율운항", "Autonomous Navigation", "자율주행, 무인선박, 드론", '["자율주행", "자율운항", "무인선박", "드론"]'),
        ("ROBOTICS", "로봇", "Robotics", "산업로봇, 서비스로봇", '["로봇", "로보틱스", "자동화"]'),
        ("GREEN", "친환경", "Green/ESG", "ESG, 탄소중립, 재생에너지", '["친환경", "ESG", "탄소중립", "재생에너지", "태양광", "풍력"]'),
        ("LNG", "LNG", "LNG/Natural Gas", "액화천연가스, 가스공급", '["LNG", "천연가스", "액화천연가스"]'),
        ("CONTENT", "콘텐츠", "Content/Media", "K-pop, OTT, 게임, 웹툰", '["K팝", "OTT", "게임", "웹툰", "콘텐츠"]'),
        ("PLATFORM", "플랫폼", "Platform Economy", "이커머스, 배달, 공유경제", '["플랫폼", "이커머스", "배달앱", "공유경제"]'),
        ("DEFENSE", "방산", "Defense Industry", "방위산업, 무기수출", '["방산", "방위산업", "무기", "군사"]')
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO themes (theme_code, theme_name, theme_name_en, description, keywords)
        VALUES (?, ?, ?, ?, ?)
    """, themes)

    conn.commit()
    print(f"[OK] Inserted {len(themes)} initial themes")


def insert_sample_events(conn: sqlite3.Connection):
    """Insert sample events for demonstration"""
    cursor = conn.cursor()

    events = [
        ("HMM_ACQUISITION", "HMM 인수전", "HMM Acquisition Battle",
         "HMM 인수를 둘러싼 국내외 기업들의 경쟁", "2024-01-01", None),
        ("HD_HYUNDAI_AUTONOMOUS", "HD현대-자율운항 협력", "HD Hyundai Autonomous Navigation Partnership",
         "HD현대 그룹의 자율운항 기술 개발 및 협력", "2024-01-01", None),
        ("POSCO_RESTRUCTURE", "포스코 구조조정", "POSCO Restructuring",
         "포스코 그룹의 사업 구조조정 및 재편", "2024-01-01", None)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO events (event_code, event_name, event_name_en, description, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, events)

    conn.commit()
    print(f"[OK] Inserted {len(events)} sample events")


def migrate_existing_data(conn: sqlite3.Connection):
    """Migrate existing sector classifications to new structure"""
    cursor = conn.cursor()

    # Mapping from old sector names to new sector codes
    sector_mapping = {
        "거시경제": "PUBLIC_POLICY",  # Macro economy -> Public Policy
        "사회정책": "PUBLIC_POLICY",  # Social policy -> Public Policy
        "금융": "FINANCIALS",
        "산업/기술": "IT",  # Default to IT, but should be analyzed per article
        "문화/생활": "CONSUMER"
    }

    # Get all articles with primary_sector
    cursor.execute("""
        SELECT id, primary_sector
        FROM articles
        WHERE primary_sector IS NOT NULL AND primary_sector != ''
    """)

    articles = cursor.fetchall()
    migrated = 0

    for article_id, old_sector in articles:
        if old_sector in sector_mapping:
            new_sector_code = sector_mapping[old_sector]

            # Get new sector_id
            cursor.execute("SELECT id FROM sectors WHERE sector_code = ?", (new_sector_code,))
            sector_row = cursor.fetchone()

            if sector_row:
                sector_id = sector_row[0]

                # Insert into article_sectors
                cursor.execute("""
                    INSERT OR IGNORE INTO article_sectors (article_id, sector_id, confidence)
                    VALUES (?, ?, 0.8)
                """, (article_id, sector_id))

                migrated += 1

    conn.commit()
    print(f"[OK] Migrated {migrated} articles to new sector structure")


def add_migration_flag(conn: sqlite3.Connection):
    """Add flag to articles table to track migration"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN sector_migrated BOOLEAN DEFAULT 0
        """)
        conn.commit()
        print("[OK] Added sector_migrated flag to articles table")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("[INFO]  sector_migrated column already exists")
        else:
            raise


def main():
    """Main migration function"""
    print("[START] Issue #61 Migration: Sector-Theme-Event Structure")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    try:
        # Step 1: Create new tables
        create_new_tables(conn)

        # Step 2: Insert GICS sectors
        insert_gics_sectors(conn)

        # Step 3: Insert initial themes
        insert_initial_themes(conn)

        # Step 4: Insert sample events
        insert_sample_events(conn)

        # Step 5: Migrate existing data
        migrate_existing_data(conn)

        # Step 6: Add migration flag
        add_migration_flag(conn)

        print("=" * 70)
        print("[OK] Migration completed successfully!")
        print("\n[SUMMARY] Summary:")

        # Print statistics
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sectors")
        print(f"  - Sectors: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM themes")
        print(f"  - Themes: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM events")
        print(f"  - Events: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM article_sectors")
        print(f"  - Article-Sector links: {cursor.fetchone()[0]}")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
