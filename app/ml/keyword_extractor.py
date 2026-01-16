"""
키워드 자동 추출 모듈

TF-IDF 기반으로 제목 + 요약에서 핵심 키워드를 추출합니다.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Tuple
import json
import re


# 한국어 불용어 (stopwords)
KOREAN_STOPWORDS = {
    # 조사
    "이", "가", "을", "를", "은", "는", "에", "와", "과", "의", "으로", "로", "도", "만", "까지", "부터",
    # 어미
    "하다", "되다", "이다", "아니다", "있다", "없다", "같다", "보다",
    # 대명사
    "그", "그것", "그녀", "그들", "저", "저것", "이것", "저것들", "우리", "나", "너",
    # 관사/지시어
    "이", "그", "저", "어느", "어떤",
    # 일반 불용어
    "등", "및", "또한", "하며", "위해", "통해", "대한", "관련", "따른", "위한",
    "것", "수", "때", "년", "월", "일", "시", "분", "초",
    # 뉴스 관련
    "기자", "뉴스", "속보", "단독", "취재", "보도", "발표", "말했다", "밝혔다", "전했다",
}


class KeywordExtractor:
    """TF-IDF 기반 키워드 추출기"""

    def __init__(self, max_keywords: int = 10, min_df: int = 1, max_df: float = 0.9):
        """
        Args:
            max_keywords: 추출할 최대 키워드 수
            min_df: 최소 문서 빈도 (이 값보다 적게 등장하는 단어 제외)
            max_df: 최대 문서 빈도 비율 (너무 많이 등장하는 단어 제외)
        """
        self.max_keywords = max_keywords
        self.min_df = min_df
        self.max_df = max_df
        self.vectorizer = None

    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""

        # 특수문자 제거 (한글, 영문, 숫자만 유지)
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)

        # 다중 공백 제거
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _tokenize(self, text: str) -> List[str]:
        """간단한 토큰화 (공백 기준)"""
        tokens = text.split()

        # 불용어 제거
        tokens = [t for t in tokens if t.lower() not in KOREAN_STOPWORDS]

        # 1글자 단어 제거
        tokens = [t for t in tokens if len(t) > 1]

        return tokens

    def extract_from_single(self, title: str, summary: str = "") -> Dict[str, any]:
        """
        단일 문서에서 키워드 추출 (간단 버전)

        Args:
            title: 제목
            summary: 요약

        Returns:
            {
                "keywords": ["키워드1", "키워드2", ...],
                "scores": [0.85, 0.72, ...]
            }
        """
        # 제목과 요약 결합
        text = f"{title} {summary}".strip()

        # 전처리
        text = self._preprocess_text(text)

        # 토큰화
        tokens = self._tokenize(text)

        if not tokens:
            return {"keywords": [], "scores": []}

        # 단어 빈도 계산 (간단 TF)
        from collections import Counter
        counter = Counter(tokens)

        # 상위 N개 추출
        top_keywords = counter.most_common(self.max_keywords)

        keywords = [kw for kw, _ in top_keywords]
        scores = [count / len(tokens) for _, count in top_keywords]  # 정규화

        return {
            "keywords": keywords,
            "scores": scores
        }

    def extract_from_batch(
        self,
        documents: List[Tuple[str, str]]
    ) -> List[Dict[str, any]]:
        """
        배치 문서에서 키워드 추출 (TF-IDF 사용)

        Args:
            documents: [(title1, summary1), (title2, summary2), ...]

        Returns:
            [
                {"keywords": [...], "scores": [...]},
                ...
            ]
        """
        if not documents:
            return []

        # 제목 + 요약 결합
        texts = [f"{title} {summary}".strip() for title, summary in documents]

        # 전처리
        texts = [self._preprocess_text(t) for t in texts]

        # TF-IDF vectorizer
        try:
            self.vectorizer = TfidfVectorizer(
                tokenizer=self._tokenize,
                min_df=self.min_df,
                max_df=self.max_df,
                lowercase=False  # 한글은 대소문자 구분 없음
            )

            # TF-IDF 행렬 생성
            tfidf_matrix = self.vectorizer.fit_transform(texts)

            # 특성명 (단어 목록)
            feature_names = self.vectorizer.get_feature_names_out()

            # 각 문서별 키워드 추출
            results = []
            for doc_idx in range(len(documents)):
                # 해당 문서의 TF-IDF 점수
                doc_tfidf = tfidf_matrix[doc_idx].toarray()[0]

                # 상위 N개 인덱스
                top_indices = doc_tfidf.argsort()[-self.max_keywords:][::-1]

                # 키워드와 점수
                keywords = [feature_names[i] for i in top_indices if doc_tfidf[i] > 0]
                scores = [float(doc_tfidf[i]) for i in top_indices if doc_tfidf[i] > 0]

                results.append({
                    "keywords": keywords,
                    "scores": scores
                })

            return results

        except Exception as e:
            print(f"⚠️ TF-IDF 추출 실패: {e}")
            # Fallback: 단일 문서 추출
            return [
                self.extract_from_single(title, summary)
                for title, summary in documents
            ]

    def to_json(self, result: Dict[str, any]) -> str:
        """결과를 JSON 문자열로 변환"""
        return json.dumps(result, ensure_ascii=False)

    def from_json(self, json_str: str) -> Dict[str, any]:
        """JSON 문자열을 파싱"""
        try:
            return json.loads(json_str)
        except:
            return {"keywords": [], "scores": []}


# 전역 인스턴스
_extractor = KeywordExtractor(max_keywords=10)


def extract_keywords(title: str, summary: str = "", max_keywords: int = 10) -> Dict[str, any]:
    """
    간편 함수: 키워드 추출

    Args:
        title: 제목
        summary: 요약
        max_keywords: 최대 키워드 수

    Returns:
        {"keywords": [...], "scores": [...]}
    """
    extractor = KeywordExtractor(max_keywords=max_keywords)
    return extractor.extract_from_single(title, summary)


def extract_keywords_to_json(title: str, summary: str = "", max_keywords: int = 10) -> str:
    """
    간편 함수: 키워드 추출 후 JSON 문자열 반환

    Args:
        title: 제목
        summary: 요약
        max_keywords: 최대 키워드 수

    Returns:
        JSON 문자열
    """
    result = extract_keywords(title, summary, max_keywords)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("🔑 키워드 추출 테스트")
    print("=" * 60)

    # 샘플 기사
    samples = [
        ("비트코인 ETF 승인 임박, SEC 최종 검토 단계", "미국 증권거래위원회(SEC)가 비트코인 현물 ETF 승인을 위한 최종 검토 단계에 들어갔다."),
        ("이더리움 2.0 업그레이드 완료, 스테이킹 증가", "이더리움 네트워크가 2.0 업그레이드를 성공적으로 완료하면서 스테이킹 참여자가 급증하고 있다."),
        ("암호화폐 규제 강화, 금융당국 가이드라인 발표", "금융당국이 암호화폐 거래소에 대한 규제 가이드라인을 발표했다."),
    ]

    # 단일 문서 테스트
    print("\n[단일 문서 테스트]")
    for title, summary in samples[:1]:
        result = extract_keywords(title, summary, max_keywords=5)
        print(f"\n제목: {title}")
        print(f"키워드: {result['keywords']}")
        print(f"점수: {[f'{s:.3f}' for s in result['scores']]}")
        print(f"JSON: {extract_keywords_to_json(title, summary, max_keywords=5)}")

    # 배치 테스트
    print("\n\n[배치 테스트]")
    extractor = KeywordExtractor(max_keywords=5)
    results = extractor.extract_from_batch(samples)

    for i, (title, _) in enumerate(samples):
        print(f"\n{i+1}. {title}")
        print(f"   키워드: {results[i]['keywords']}")
        print(f"   점수: {[f'{s:.3f}' for s in results[i]['scores']]}")

    print("\n✅ 테스트 완료!")
