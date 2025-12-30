"""
뉴스 URL에서 언론사를 추출하는 유틸리티
Issue #16: 언론사 필터링
"""
from urllib.parse import urlparse
from typing import Optional


# 도메인 -> 언론사명 매핑
DOMAIN_TO_OUTLET = {
    # 주요 종합 일간지
    "chosun.com": "조선일보",
    "joongang.co.kr": "중앙일보",
    "donga.com": "동아일보",
    "hani.co.kr": "한겨레",
    "khan.co.kr": "경향신문",

    # 방송사
    "kbs.co.kr": "KBS",
    "mbc.co.kr": "MBC",
    "sbs.co.kr": "SBS",
    "jtbc.co.kr": "JTBC",
    "ytn.co.kr": "YTN",

    # 경제지
    "mk.co.kr": "매일경제",
    "hankyung.com": "한국경제",
    "sedaily.com": "서울경제",
    "fnnews.com": "파이낸셜뉴스",
    "mt.co.kr": "머니투데이",
    "edaily.co.kr": "이데일리",
    "asiae.co.kr": "아시아경제",
    "etnews.com": "전자신문",

    # 통신사
    "yna.co.kr": "연합뉴스",
    "yonhapnewstv.co.kr": "연합뉴스TV",
    "newsis.com": "뉴시스",

    # IT/테크
    "zdnet.co.kr": "지디넷코리아",
    "bloter.net": "블로터",
    "ddaily.co.kr": "디지털데일리",

    # 국제 언론
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "reuters.com": "Reuters",
    "nytimes.com": "The New York Times",
    "wsj.com": "The Wall Street Journal",
    "bloomberg.com": "Bloomberg",
    "ft.com": "Financial Times",
    "economist.com": "The Economist",
    "theguardian.com": "The Guardian",
    "washingtonpost.com": "The Washington Post",
    "cnn.com": "CNN",
    "cnbc.com": "CNBC",

    # 암호화폐 전문
    "coindesk.com": "CoinDesk",
    "cointelegraph.com": "Cointelegraph",
    "cryptonews.com": "CryptoNews",

    # 정부/공공기관
    "fsc.go.kr": "금융위원회",
    "fss.or.kr": "금융감독원",
    "bok.or.kr": "한국은행",
    "dart.fss.or.kr": "전자공시시스템",
    "krx.co.kr": "한국거래소",
    "kostat.go.kr": "통계청",

    # 기타 뉴스
    "ohmynews.com": "오마이뉴스",
    "pressian.com": "프레시안",
    "nocutnews.co.kr": "노컷뉴스",
    "newspim.com": "뉴스핌",
    "newstapa.org": "뉴스타파",
}


def extract_source_from_url(url: str) -> Optional[str]:
    """
    URL에서 언론사명을 추출합니다.

    Args:
        url: 뉴스 기사 URL

    Returns:
        언론사명 (매핑되지 않은 경우 도메인 반환, 실패 시 None)

    Examples:
        >>> extract_source_from_url("https://www.chosun.com/economy/2024/...")
        "조선일보"
        >>> extract_source_from_url("https://news.naver.com/...")
        "news.naver.com"
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # www. 제거
        if domain.startswith("www."):
            domain = domain[4:]

        # 매핑된 언론사 반환
        if domain in DOMAIN_TO_OUTLET:
            return DOMAIN_TO_OUTLET[domain]

        # 서브도메인이 있는 경우 상위 도메인으로 재시도
        # 예: news.chosun.com -> chosun.com
        # 예: news.kbs.co.kr -> kbs.co.kr
        parts = domain.split(".")

        # .co.kr, .go.kr 같은 2단계 도메인 처리
        if len(parts) >= 3:
            # 마지막 3개 부분 확인 (예: kbs.co.kr)
            parent_domain_3 = ".".join(parts[-3:])
            if parent_domain_3 in DOMAIN_TO_OUTLET:
                return DOMAIN_TO_OUTLET[parent_domain_3]

        # 일반 도메인 처리 (예: chosun.com)
        if len(parts) >= 2:
            parent_domain_2 = ".".join(parts[-2:])
            if parent_domain_2 in DOMAIN_TO_OUTLET:
                return DOMAIN_TO_OUTLET[parent_domain_2]

        # 매핑되지 않은 경우 도메인 그대로 반환
        return domain

    except Exception as e:
        print(f"URL 파싱 실패: {url}, 에러: {e}")
        return None


def get_all_sources() -> list[str]:
    """모든 매핑된 언론사 목록을 반환합니다."""
    return sorted(set(DOMAIN_TO_OUTLET.values()))
