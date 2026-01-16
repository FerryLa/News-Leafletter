"""
Test script for Issue #61: Apply new classification to sample news
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.classification.gics_sector_definitions import (
    classify_sector_by_keywords,
    classify_themes_by_keywords,
    detect_events_by_keywords,
    get_sector_by_code,
    get_theme_by_code
)

DB_PATH = "data/news_leafletter.db"


# Sample news articles for testing
SAMPLE_NEWS = [
    {
        "title": "삼성전자, 3나노 GAA 공정 기반 AI 반도체 양산 시작",
        "summary": "삼성전자가 세계 최초로 3나노 GAA 공정 기술을 적용한 AI 전용 반도체 양산을 시작했다. 이번 반도체는 기존 대비 성능 30% 향상, 전력 소모 50% 감소를 달성했다."
    },
    {
        "title": "LG에너지솔루션, 미국 배터리 공장 증설 확정",
        "summary": "LG에너지솔루션이 미국 미시간주에 제2공장 건설을 확정했다. 2차전지 수요 급증에 대응하기 위한 조치로, 2026년부터 연간 50GWh 생산 예정이다."
    },
    {
        "title": "HD현대, 자율운항 선박 상용화 본격 추진",
        "summary": "HD현대가 자율운항 기술 자회사 Avikus와 함께 무인선박 상용화를 본격 추진한다. 2025년까지 레벨4 자율운항 선박 10척을 운용할 계획이다."
    },
    {
        "title": "HMM 인수전 치열, 3개 컨소시엄 입찰 예정",
        "summary": "HMM 매각을 둘러싼 인수전이 치열하다. 국내외 3개 컨소시엄이 본입찰에 참여할 예정이며, 최종 인수자는 3월 중 결정될 전망이다."
    },
    {
        "title": "포스코홀딩스, 구조조정으로 비핵심 사업 매각",
        "summary": "포스코홀딩스가 대규모 구조조정에 나섰다. 비철금속 사업부 등 비핵심 사업을 매각하고 2차전지 소재와 수소 사업에 집중할 계획이다."
    },
    {
        "title": "금융당국, 암호화폐 현물 ETF 승인 검토",
        "summary": "금융위원회가 암호화폐 현물 상장지수펀드(ETF) 도입을 검토 중이다. 투자자 보호 장치를 마련한 후 단계적으로 허용할 방침이다."
    },
    {
        "title": "SK하이닉스, HBM3E 메모리 양산 돌입",
        "summary": "SK하이닉스가 차세대 고대역폭 메모리 HBM3E 양산에 돌입했다. AI 서버 수요 급증에 대응하기 위한 조치로, 엔비디아와 우선 공급 계약을 체결했다."
    },
    {
        "title": "넷플릭스, 한국 오리지널 콘텐츠 제작비 2배 확대",
        "summary": "넷플릭스가 2025년 한국 오리지널 콘텐츠 제작에 1조원 이상을 투자한다. K-드라마와 K-예능의 글로벌 인기에 힘입은 결정이다."
    },
    {
        "title": "정부, 로봇 산업 육성 위한 규제 샌드박스 확대",
        "summary": "산업통상자원부가 로봇 산업 육성을 위해 규제 샌드박스를 확대한다. 서비스 로봇과 협동 로봇 분야에 대한 규제를 대폭 완화할 예정이다."
    },
    {
        "title": "한전, 신재생에너지 발전 비중 30% 달성",
        "summary": "한국전력공사가 신재생에너지 발전 비중 30%를 달성했다. 태양광과 풍력 발전소 확대를 통해 탄소중립 목표에 한 걸음 다가섰다."
    }
]


def classify_and_insert_sample_news():
    """샘플 뉴스를 분류하고 DB에 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("Testing New Classification System on Sample News")
    print("=" * 70)

    for idx, news in enumerate(SAMPLE_NEWS, 1):
        title = news["title"]
        summary = news["summary"]
        full_text = f"{title} {summary}"

        print(f"\n[{idx}] {title}")
        print("-" * 70)

        # Classify Sector
        sector_code = classify_sector_by_keywords(full_text)
        if sector_code:
            sector = get_sector_by_code(sector_code)
            print(f"Sector: {sector.name_ko} ({sector_code})")
        else:
            print("Sector: None detected")

        # Classify Themes
        theme_codes = classify_themes_by_keywords(full_text, min_matches=1)
        if theme_codes:
            print(f"Themes: ", end="")
            for theme_code in theme_codes:
                theme = get_theme_by_code(theme_code)
                print(f"{theme.name_ko} ({theme_code})", end=" ")
            print()
        else:
            print("Themes: None detected")

        # Detect Events
        event_codes = detect_events_by_keywords(full_text, min_matches=1)
        if event_codes:
            print(f"Events: {', '.join(event_codes)}")
        else:
            print("Events: None detected")

        # Insert into database
        try:
            # Insert article
            cursor.execute("""
                INSERT INTO articles (article_id, title, summary, url, source_name)
                VALUES (?, ?, ?, ?, ?)
            """, (f"sample_{idx}", title, summary, f"https://example.com/news/{idx}", "Sample News"))

            article_db_id = cursor.lastrowid

            # Insert sector
            if sector_code:
                cursor.execute("SELECT id FROM sectors WHERE sector_code = ?", (sector_code,))
                sector_row = cursor.fetchone()
                if sector_row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO article_sectors (article_id, sector_id, confidence)
                        VALUES (?, ?, 0.9)
                    """, (article_db_id, sector_row[0]))

            # Insert themes
            for theme_code in theme_codes:
                cursor.execute("SELECT id FROM themes WHERE theme_code = ?", (theme_code,))
                theme_row = cursor.fetchone()
                if theme_row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO article_themes (article_id, theme_id, confidence)
                        VALUES (?, ?, 0.85)
                    """, (article_db_id, theme_row[0]))

            # Insert events
            for event_code in event_codes:
                cursor.execute("SELECT id FROM events WHERE event_code = ?", (event_code,))
                event_row = cursor.fetchone()
                if event_row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO article_events (article_id, event_id, relevance_score)
                        VALUES (?, ?, 0.9)
                    """, (article_db_id, event_row[0]))

            conn.commit()
            print("[OK] Saved to database")

        except sqlite3.IntegrityError as e:
            print(f"[SKIP] Already exists or constraint violation: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to save: {e}")

    conn.close()

    print("\n" + "=" * 70)
    print("Classification test completed!")
    print("=" * 70)


def print_classification_statistics():
    """분류 통계 출력"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("Classification Statistics")
    print("=" * 70)

    # Sector statistics
    cursor.execute("""
        SELECT s.sector_name, COUNT(*) as cnt
        FROM article_sectors ase
        JOIN sectors s ON ase.sector_id = s.id
        GROUP BY s.sector_name
        ORDER BY cnt DESC
    """)

    print("\n[Sector Distribution]")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} articles")

    # Theme statistics
    cursor.execute("""
        SELECT t.theme_name, COUNT(*) as cnt
        FROM article_themes at
        JOIN themes t ON at.theme_id = t.id
        GROUP BY t.theme_name
        ORDER BY cnt DESC
    """)

    print("\n[Theme Distribution]")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} articles")

    # Event statistics
    cursor.execute("""
        SELECT e.event_name, COUNT(*) as cnt
        FROM article_events ae
        JOIN events e ON ae.event_id = e.id
        GROUP BY e.event_name
        ORDER BY cnt DESC
    """)

    print("\n[Event Distribution]")
    event_rows = cursor.fetchall()
    if event_rows:
        for row in event_rows:
            print(f"  {row[0]}: {row[1]} articles")
    else:
        print("  No events detected")

    conn.close()


if __name__ == "__main__":
    classify_and_insert_sample_news()
    print_classification_statistics()
