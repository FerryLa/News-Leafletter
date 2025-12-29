"""
Sector and subcategory definitions for news classification
Based on 5 major sectors with detailed subcategories
"""

from typing import Dict, List


# 섹터 정의 구조
# {
#     "sector_id": {
#         "name": "섹터명",
#         "keywords": ["섹터 키워드들"],
#         "subcategories": {
#             "subcategory_id": {
#                 "name": "하위 카테고리명",
#                 "keywords": ["하위 카테고리 키워드들"]
#             }
#         }
#     }
# }

SECTOR_DEFINITIONS: Dict[str, Dict] = {
    "macro_economy": {
        "name": "거시경제",
        "keywords": [
            "거시경제", "세계경제", "글로벌경제", "경제성장", "경기", "gdp",
            "무역", "수출", "수입", "관세", "보호무역"
        ],
        "subcategories": {
            "international_trade": {
                "name": "국제 무역",
                "keywords": [
                    "국제무역", "무역전쟁", "무역협정", "수출입", "관세",
                    "통관", "무역수지", "무역적자", "무역흑자", "wto"
                ]
            },
            "inflation": {
                "name": "인플레이션",
                "keywords": [
                    "인플레이션", "물가", "소비자물가", "물가상승", "디플레이션",
                    "cpi", "물가지수", "인플레", "물가안정"
                ]
            },
            "interest_rate": {
                "name": "금리 정책",
                "keywords": [
                    "금리", "기준금리", "금리인상", "금리인하", "통화정책",
                    "연준", "fed", "한국은행", "중앙은행", "금리동결"
                ]
            },
            "war_risk": {
                "name": "전쟁 리스크",
                "keywords": [
                    "전쟁", "분쟁", "군사", "무력충돌", "지정학", "안보",
                    "우크라이나", "러시아", "대만", "중동", "테러"
                ]
            },
            "supply_chain": {
                "name": "글로벌 공급망",
                "keywords": [
                    "공급망", "서플라이체인", "물류", "반도체공급", "원자재공급",
                    "공급부족", "공급망재편", "리쇼어링", "니어쇼어링"
                ]
            },
            "emerging_markets": {
                "name": "신흥국 경제 동향",
                "keywords": [
                    "신흥국", "이머징마켓", "개도국", "브릭스", "brics",
                    "동남아시아", "인도경제", "베트남경제", "중국경제"
                ]
            },
            "currency_war": {
                "name": "환율 전쟁",
                "keywords": [
                    "환율전쟁", "환율조작", "위안화", "엔화", "환율정책",
                    "통화가치", "평가절하", "평가절상"
                ]
            },
            "energy_crisis": {
                "name": "에너지 위기",
                "keywords": [
                    "에너지위기", "유가", "석유", "천연가스", "lng", "원유",
                    "오펙", "opec", "에너지안보", "전력난", "가스공급"
                ]
            },
            "protectionism": {
                "name": "보호무역주의",
                "keywords": [
                    "보호무역", "자국우선", "수입규제", "반덤핑", "세이프가드",
                    "미국우선주의", "무역장벽"
                ]
            },
            "fta": {
                "name": "FTA 재협상",
                "keywords": [
                    "fta", "자유무역협정", "통상협상", "무역협정", "rcep",
                    "한미fta", "재협상", "쿼드", "인도태평양경제프레임워크"
                ]
            }
        }
    },

    "social_policy": {
        "name": "사회정책",
        "keywords": [
            "사회정책", "복지", "정부정책", "사회", "국민",
            "정책", "제도", "법안", "개혁"
        ],
        "subcategories": {
            "consumer_sentiment": {
                "name": "소비 심리",
                "keywords": [
                    "소비심리", "소비자신뢰", "소비지출", "민간소비", "내수",
                    "소비위축", "소비회복", "가계소비"
                ]
            },
            "real_estate": {
                "name": "부동산 규제",
                "keywords": [
                    "부동산", "주택", "아파트", "집값", "주택가격", "전세",
                    "월세", "dtl", "ltv", "담보대출", "주택규제", "분양"
                ]
            },
            "election": {
                "name": "총선 공약",
                "keywords": [
                    "총선", "대선", "선거", "공약", "정치", "여당", "야당",
                    "국회의원", "대통령", "정당"
                ]
            },
            "regional_balance": {
                "name": "지역 균형 발전",
                "keywords": [
                    "지역균형", "균형발전", "수도권", "비수도권", "지방분권",
                    "지역개발", "혁신도시", "기업도시"
                ]
            },
            "youth_unemployment": {
                "name": "청년 실업률",
                "keywords": [
                    "청년실업", "청년고용", "취업난", "구직", "일자리",
                    "청년정책", "청년수당", "청년지원"
                ]
            },
            "small_business": {
                "name": "자영업 지원 정책",
                "keywords": [
                    "자영업", "소상공인", "중소기업", "소기업", "창업",
                    "자영업지원", "소상공인지원", "임대료", "상생"
                ]
            },
            "population_decline": {
                "name": "인구 감소 대응",
                "keywords": [
                    "인구감소", "저출산", "고령화", "출산율", "인구절벽",
                    "인구정책", "육아지원", "보육", "출산장려"
                ]
            },
            "regional_extinction": {
                "name": "지방 소멸 위기",
                "keywords": [
                    "지방소멸", "인구유출", "농촌인구", "지방위기",
                    "소멸위험지역", "지역소멸"
                ]
            },
            "public_utility": {
                "name": "공공요금 인상",
                "keywords": [
                    "공공요금", "전기료", "가스요금", "수도요금", "요금인상",
                    "공공요금인상", "통신비", "교통비"
                ]
            }
        }
    },

    "finance": {
        "name": "금융",
        "keywords": [
            "금융", "투자", "시장", "자산", "주가", "코스피", "나스닥",
            "증시", "펀드", "채권", "외환", "달러"
        ],
        "subcategories": {
            "stock_volatility": {
                "name": "증시 변동성",
                "keywords": [
                    "증시", "주식", "코스피", "코스닥", "나스닥", "s&p500",
                    "다우존스", "변동성", "급락", "급등", "증시폭락"
                ]
            },
            "crypto_regulation": {
                "name": "암호화폐 규제",
                "keywords": [
                    "암호화폐", "가상자산", "비트코인", "이더리움", "코인",
                    "암호화폐규제", "가상자산법", "거래소", "코인거래"
                ]
            },
            "gold_rally": {
                "name": "금값 랠리",
                "keywords": [
                    "금", "금값", "금시세", "골드", "금투자", "금가격",
                    "안전자산", "금매입"
                ]
            },
            "dollar_strength": {
                "name": "달러 강세",
                "keywords": [
                    "달러", "달러강세", "달러약세", "달러화", "환율",
                    "원달러환율", "달러인덱스", "기축통화"
                ]
            },
            "esg_investment": {
                "name": "ESG 투자 확대",
                "keywords": [
                    "esg", "지속가능", "친환경투자", "사회책임투자", "녹색금융",
                    "esg경영", "탄소중립", "그린본드"
                ]
            },
            "bond_market": {
                "name": "채권 시장 유동성",
                "keywords": [
                    "채권", "국채", "회사채", "채권시장", "채권금리",
                    "장기금리", "단기금리", "채권수익률"
                ]
            },
            "forex_reserves": {
                "name": "외환 보유고 감소",
                "keywords": [
                    "외환보유고", "외환보유액", "외환준비금", "외화보유",
                    "달러보유고", "외환위기"
                ]
            },
            "fintech": {
                "name": "핀테크 규제 완화",
                "keywords": [
                    "핀테크", "금융기술", "디지털금융", "간편결제", "모바일뱅킹",
                    "인터넷전문은행", "오픈뱅킹", "금융혁신"
                ]
            }
        }
    },

    "industry_tech": {
        "name": "산업/기술",
        "keywords": [
            "산업", "기술", "혁신", "개발", "제조", "생산",
            "it", "반도체", "ai", "바이오"
        ],
        "subcategories": {
            "ai_innovation": {
                "name": "AI 혁신",
                "keywords": [
                    "인공지능", "ai", "머신러닝", "딥러닝", "chatgpt",
                    "llm", "생성ai", "ai기술", "ai반도체"
                ]
            },
            "semiconductor": {
                "name": "반도체 수급난",
                "keywords": [
                    "반도체", "칩", "파운드리", "메모리반도체", "시스템반도체",
                    "반도체공급", "칩부족", "tsmc", "삼성전자반도체"
                ]
            },
            "bio_pharma": {
                "name": "바이오 신약 개발",
                "keywords": [
                    "바이오", "신약", "제약", "임상시험", "의약품", "치료제",
                    "백신", "항암제", "바이오기술", "유전자치료"
                ]
            },
            "autonomous_driving": {
                "name": "자율주행 상용화",
                "keywords": [
                    "자율주행", "무인차", "자동차기술", "전기차", "ev",
                    "배터리", "2차전지", "모빌리티"
                ]
            },
            "space_industry": {
                "name": "우주 산업 클러스터",
                "keywords": [
                    "우주산업", "위성", "로켓", "우주개발", "누리호",
                    "발사체", "우주탐사", "항공우주"
                ]
            },
            "green_tech": {
                "name": "친환경 기술 보조금",
                "keywords": [
                    "친환경기술", "녹색기술", "재생에너지", "태양광", "풍력",
                    "수소", "수소경제", "그린뉴딜", "탄소감축"
                ]
            },
            "data_sovereignty": {
                "name": "데이터 주권 강화",
                "keywords": [
                    "데이터주권", "개인정보", "정보보호", "데이터법", "gdpr",
                    "개인정보보호", "데이터경제", "마이데이터"
                ]
            }
        }
    },

    "culture_lifestyle": {
        "name": "문화/생활",
        "keywords": [
            "문화", "생활", "사회", "트렌드", "일상",
            "엔터테인먼트", "여가", "환경"
        ],
        "subcategories": {
            "kpop_export": {
                "name": "K팝 수출",
                "keywords": [
                    "k팝", "kpop", "한류", "케이팝", "아이돌", "한국음악",
                    "방탄소년단", "bts", "블랙핑크", "케이콘텐츠"
                ]
            },
            "game_regulation": {
                "name": "게임 산업 규제",
                "keywords": [
                    "게임", "게임산업", "게임규제", "셧다운제", "게임중독",
                    "e스포츠", "게임개발", "모바일게임"
                ]
            },
            "climate_disaster": {
                "name": "기후 재해",
                "keywords": [
                    "기후", "기후변화", "온난화", "폭염", "폭우", "태풍",
                    "자연재해", "이상기후", "기후위기", "홍수"
                ]
            },
            "digital_copyright": {
                "name": "디지털 저작권 분쟁",
                "keywords": [
                    "저작권", "지적재산권", "저작권분쟁", "불법복제", "웹툰",
                    "ott", "스트리밍", "음원", "콘텐츠저작권"
                ]
            },
            "cultural_heritage": {
                "name": "문화유산 보존 정책",
                "keywords": [
                    "문화유산", "문화재", "유네스코", "세계유산", "전통문화",
                    "문화재보호", "무형문화재", "문화재복원"
                ]
            },
            "carbon_neutral": {
                "name": "탄소 중립 캠페인",
                "keywords": [
                    "탄소중립", "넷제로", "탄소배출", "온실가스", "탄소감축",
                    "탄소제로", "기후행동", "탄소세"
                ]
            },
            "pet_industry": {
                "name": "반려동물 산업 성장",
                "keywords": [
                    "반려동물", "펫", "애완동물", "펫산업", "반려견", "반려묘",
                    "펫케어", "동물복지", "펫푸드"
                ]
            }
        }
    }
}


def get_all_sectors() -> List[str]:
    """모든 섹터 ID 목록 반환"""
    return list(SECTOR_DEFINITIONS.keys())


def get_sector_name(sector_id: str) -> str:
    """섹터 ID로 섹터명 반환"""
    return SECTOR_DEFINITIONS.get(sector_id, {}).get("name", "")


def get_sector_keywords(sector_id: str) -> List[str]:
    """섹터 ID로 섹터 키워드 반환"""
    return SECTOR_DEFINITIONS.get(sector_id, {}).get("keywords", [])


def get_subcategories(sector_id: str) -> Dict[str, Dict]:
    """섹터 ID로 하위 카테고리 반환"""
    return SECTOR_DEFINITIONS.get(sector_id, {}).get("subcategories", {})


def get_subcategory_name(sector_id: str, subcategory_id: str) -> str:
    """하위 카테고리 ID로 카테고리명 반환"""
    subcats = get_subcategories(sector_id)
    return subcats.get(subcategory_id, {}).get("name", "")


def get_subcategory_keywords(sector_id: str, subcategory_id: str) -> List[str]:
    """하위 카테고리 ID로 키워드 반환"""
    subcats = get_subcategories(sector_id)
    return subcats.get(subcategory_id, {}).get("keywords", [])
