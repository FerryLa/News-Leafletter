"""
GICS-based Sector-Theme-Event Definitions for Issue #61

This module defines the new 3-tier classification structure:
1. Sector (고정 분류) - GICS-based 11 sectors
2. Theme (유동 분류) - Expandable technology/trend themes
3. Event (개별 이슈) - Specific incidents with temporal context
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


# ===== SECTOR DEFINITIONS (GICS-BASED) =====

@dataclass
class SectorDefinition:
    """산업(Sector) 정의"""
    code: str
    name_ko: str
    name_en: str
    description: str
    keywords: List[str]


GICS_SECTORS: List[SectorDefinition] = [
    SectorDefinition(
        code="ENERGY",
        name_ko="에너지",
        name_en="Energy",
        description="석유, 가스, 신재생 에너지 등",
        keywords=["석유", "원유", "가스", "천연가스", "lng", "에너지", "유가", "opec",
                 "신재생에너지", "태양광", "풍력", "수소", "배터리"]
    ),
    SectorDefinition(
        code="MATERIALS",
        name_ko="소재",
        name_en="Materials",
        description="화학, 금속, 광업, 건설자재 등",
        keywords=["철강", "포스코", "화학", "소재", "금속", "알루미늄", "구리",
                 "시멘트", "유리", "광업", "원자재", "건설자재"]
    ),
    SectorDefinition(
        code="INDUSTRIALS",
        name_ko="산업재",
        name_en="Industrials",
        description="기계, 운송, 건설, 항공우주/방위 등",
        keywords=["기계", "중공업", "조선", "건설", "플랜트", "항공", "방산",
                 "물류", "운송", "철도", "항공우주", "방위산업"]
    ),
    SectorDefinition(
        code="IT",
        name_ko="IT",
        name_en="Information Technology",
        description="소프트웨어, 하드웨어, 반도체, IT서비스 등",
        keywords=["it", "정보기술", "소프트웨어", "sw", "하드웨어", "hw",
                 "반도체", "칩", "컴퓨터", "스마트폰", "전자", "반도체장비"]
    ),
    SectorDefinition(
        code="COMMUNICATION",
        name_ko="커뮤니케이션",
        name_en="Communication Services",
        description="통신, 미디어, 엔터테인먼트 등",
        keywords=["통신", "5g", "6g", "이동통신", "kt", "skt", "lg유플러스",
                 "미디어", "방송", "엔터테인먼트", "콘텐츠", "ott"]
    ),
    SectorDefinition(
        code="FINANCIALS",
        name_ko="금융",
        name_en="Financials",
        description="은행, 증권, 보험, 부동산금융 등",
        keywords=["금융", "은행", "증권", "보험", "자산운용", "투자", "펀드",
                 "금융서비스", "핀테크", "카드", "신용", "대출"]
    ),
    SectorDefinition(
        code="HEALTHCARE",
        name_ko="헬스케어",
        name_en="Healthcare",
        description="제약, 바이오, 의료기기, 헬스케어서비스 등",
        keywords=["제약", "바이오", "의약품", "신약", "임상", "병원",
                 "의료", "의료기기", "헬스케어", "건강", "치료"]
    ),
    SectorDefinition(
        code="CONSUMER",
        name_ko="소비재",
        name_en="Consumer Discretionary & Staples",
        description="유통, 자동차, 의류, 식음료, 생필품 등",
        keywords=["유통", "리테일", "이커머스", "쇼핑", "자동차", "전기차", "ev",
                 "의류", "패션", "식음료", "음식", "음료", "생필품", "소비재"]
    ),
    SectorDefinition(
        code="UTILITIES",
        name_ko="유틸리티",
        name_en="Utilities",
        description="전력, 가스, 수도 등 공공서비스",
        keywords=["전력", "전기", "발전", "송전", "배전", "가스공급", "상하수도",
                 "수도", "공공서비스", "인프라"]
    ),
    SectorDefinition(
        code="REAL_ESTATE",
        name_ko="부동산",
        name_en="Real Estate",
        description="부동산 개발, 운영, 리츠 등",
        keywords=["부동산", "건설", "주택", "아파트", "상업용부동산", "오피스",
                 "리츠", "reit", "부동산개발", "임대"]
    ),
    SectorDefinition(
        code="PUBLIC_POLICY",
        name_ko="정책·공공",
        name_en="Public Policy & Government",
        description="정부정책, 공공부문, 규제 등",
        keywords=["정책", "정부", "공공", "규제", "법안", "제도", "행정",
                 "정치", "국회", "선거", "정당", "복지", "사회정책"]
    )
]


# ===== THEME DEFINITIONS (EXPANDABLE) =====

@dataclass
class ThemeDefinition:
    """테마(Theme) 정의"""
    code: str
    name_ko: str
    name_en: str
    description: str
    keywords: List[str]
    is_active: bool = True


THEMES: List[ThemeDefinition] = [
    ThemeDefinition(
        code="SEMICONDUCTOR",
        name_ko="반도체",
        name_en="Semiconductor",
        description="반도체 제조, 설계, 장비",
        keywords=["반도체", "칩", "웨이퍼", "파운드리", "메모리", "낸드", "d램",
                 "시스템반도체", "반도체장비", "tsmc", "삼성전자"]
    ),
    ThemeDefinition(
        code="BATTERY",
        name_ko="2차전지",
        name_en="Secondary Battery",
        description="전기차 배터리, ESS",
        keywords=["배터리", "2차전지", "리튬", "양극재", "음극재", "전해질",
                 "배터리셀", "ess", "에너지저장", "전기차배터리"]
    ),
    ThemeDefinition(
        code="AI",
        name_ko="AI",
        name_en="Artificial Intelligence",
        description="인공지능, 머신러닝, LLM",
        keywords=["ai", "인공지능", "머신러닝", "딥러닝", "chatgpt", "gpt",
                 "llm", "생성ai", "ai반도체", "ai칩"]
    ),
    ThemeDefinition(
        code="AUTONOMOUS",
        name_ko="자율운항",
        name_en="Autonomous Navigation",
        description="자율주행, 무인선박, 드론",
        keywords=["자율주행", "자율운항", "무인선박", "자율운행", "무인차량",
                 "드론", "무인기", "adas", "레벨4"]
    ),
    ThemeDefinition(
        code="ROBOTICS",
        name_ko="로봇",
        name_en="Robotics",
        description="산업로봇, 서비스로봇",
        keywords=["로봇", "로보틱스", "산업로봇", "서비스로봇", "협동로봇",
                 "자동화", "스마트팩토리", "무인화"]
    ),
    ThemeDefinition(
        code="GREEN",
        name_ko="친환경",
        name_en="Green/ESG",
        description="ESG, 탄소중립, 재생에너지",
        keywords=["친환경", "esg", "탄소중립", "탄소배출", "넷제로", "그린",
                 "재생에너지", "지속가능", "환경", "온실가스"]
    ),
    ThemeDefinition(
        code="LNG",
        name_ko="LNG",
        name_en="LNG/Natural Gas",
        description="액화천연가스, 가스공급",
        keywords=["lng", "천연가스", "액화천연가스", "가스터빈", "가스선",
                 "lng선", "가스저장", "가스발전"]
    ),
    ThemeDefinition(
        code="CONTENT",
        name_ko="콘텐츠",
        name_en="Content/Media",
        description="K-pop, OTT, 게임, 웹툰",
        keywords=["k팝", "kpop", "한류", "ott", "넷플릭스", "게임", "웹툰",
                 "콘텐츠", "엔터", "아이돌", "드라마", "영화"]
    ),
    ThemeDefinition(
        code="PLATFORM",
        name_ko="플랫폼",
        name_en="Platform Economy",
        description="이커머스, 배달, 공유경제",
        keywords=["플랫폼", "이커머스", "배달앱", "쿠팡", "네이버", "카카오",
                 "공유경제", "마켓플레이스", "온라인쇼핑"]
    ),
    ThemeDefinition(
        code="DEFENSE",
        name_ko="방산",
        name_en="Defense Industry",
        description="방위산업, 무기수출",
        keywords=["방산", "방위산업", "무기", "군사", "무기수출", "전투기",
                 "함정", "k방산", "방산수출"]
    )
]


# ===== EVENT DEFINITIONS (SPECIFIC INCIDENTS) =====

@dataclass
class EventDefinition:
    """사건(Event) 정의"""
    code: str
    name_ko: str
    name_en: str
    description: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    keywords: List[str] = None
    is_active: bool = True


# Sample events (these will be managed dynamically in DB)
SAMPLE_EVENTS: List[EventDefinition] = [
    EventDefinition(
        code="HMM_ACQUISITION",
        name_ko="HMM 인수전",
        name_en="HMM Acquisition Battle",
        description="HMM 인수를 둘러싼 국내외 기업들의 경쟁",
        keywords=["hmm", "hmm인수", "해운사인수", "산업은행"]
    ),
    EventDefinition(
        code="HD_HYUNDAI_AUTONOMOUS",
        name_ko="HD현대-자율운항 협력",
        name_en="HD Hyundai Autonomous Navigation Partnership",
        description="HD현대 그룹의 자율운항 기술 개발 및 협력",
        keywords=["hd현대", "자율운항", "avikus", "에이비커스", "무인선박"]
    ),
    EventDefinition(
        code="POSCO_RESTRUCTURE",
        name_ko="포스코 구조조정",
        name_en="POSCO Restructuring",
        description="포스코 그룹의 사업 구조조정 및 재편",
        keywords=["포스코", "구조조정", "포스코홀딩스", "포스코인터내셔널"]
    )
]


# ===== UTILITY FUNCTIONS =====

def get_sector_by_code(code: str) -> Optional[SectorDefinition]:
    """섹터 코드로 섹터 정의 조회"""
    for sector in GICS_SECTORS:
        if sector.code == code:
            return sector
    return None


def get_theme_by_code(code: str) -> Optional[ThemeDefinition]:
    """테마 코드로 테마 정의 조회"""
    for theme in THEMES:
        if theme.code == code:
            return theme
    return None


def get_event_by_code(code: str) -> Optional[EventDefinition]:
    """이벤트 코드로 이벤트 정의 조회"""
    for event in SAMPLE_EVENTS:
        if event.code == code:
            return event
    return None


def get_all_sector_codes() -> List[str]:
    """모든 섹터 코드 반환"""
    return [sector.code for sector in GICS_SECTORS]


def get_all_theme_codes() -> List[str]:
    """모든 활성 테마 코드 반환"""
    return [theme.code for theme in THEMES if theme.is_active]


def get_sector_keywords_map() -> Dict[str, List[str]]:
    """섹터별 키워드 맵 반환"""
    return {sector.code: sector.keywords for sector in GICS_SECTORS}


def get_theme_keywords_map() -> Dict[str, List[str]]:
    """테마별 키워드 맵 반환"""
    return {theme.code: theme.keywords for theme in THEMES if theme.is_active}


# ===== CLASSIFICATION HELPERS =====

def classify_sector_by_keywords(text: str) -> Optional[str]:
    """키워드 기반 섹터 분류 (가장 많이 매칭된 섹터 반환)"""
    text_lower = text.lower()

    sector_scores = {}
    for sector in GICS_SECTORS:
        score = sum(1 for keyword in sector.keywords if keyword.lower() in text_lower)
        if score > 0:
            sector_scores[sector.code] = score

    if sector_scores:
        return max(sector_scores, key=sector_scores.get)
    return None


def classify_themes_by_keywords(text: str, min_matches: int = 1) -> List[str]:
    """키워드 기반 테마 분류 (매칭된 모든 테마 반환)"""
    text_lower = text.lower()

    matched_themes = []
    for theme in THEMES:
        if not theme.is_active:
            continue

        matches = sum(1 for keyword in theme.keywords if keyword.lower() in text_lower)
        if matches >= min_matches:
            matched_themes.append(theme.code)

    return matched_themes


def detect_events_by_keywords(text: str, min_matches: int = 1) -> List[str]:
    """키워드 기반 이벤트 감지"""
    text_lower = text.lower()

    detected_events = []
    for event in SAMPLE_EVENTS:
        if not event.is_active or not event.keywords:
            continue

        matches = sum(1 for keyword in event.keywords if keyword.lower() in text_lower)
        if matches >= min_matches:
            detected_events.append(event.code)

    return detected_events


if __name__ == "__main__":
    # Test the classification
    print("=== GICS Sector Definitions ===")
    for sector in GICS_SECTORS:
        print(f"{sector.code}: {sector.name_ko} ({sector.name_en})")

    print("\n=== Theme Definitions ===")
    for theme in THEMES:
        print(f"{theme.code}: {theme.name_ko} ({theme.name_en})")

    print("\n=== Sample Events ===")
    for event in SAMPLE_EVENTS:
        print(f"{event.code}: {event.name_ko}")

    # Test classification
    sample_text = "삼성전자가 최신 AI 반도체를 공개하며 HMM 인수전에도 관심을 보이고 있다"
    print(f"\n=== Classification Test ===")
    print(f"Text: {sample_text}")
    print(f"Sector: {classify_sector_by_keywords(sample_text)}")
    print(f"Themes: {classify_themes_by_keywords(sample_text)}")
    print(f"Events: {detect_events_by_keywords(sample_text)}")
