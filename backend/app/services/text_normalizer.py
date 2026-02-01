"""한국어 텍스트 정규화 서비스

숫자를 한글로 변환하여 TTS/STT 일관성 보장:
- 한자어 수사: 일, 이, 삼, 사, 오... (날짜, 금액, 전화번호)
- 고유어 수사: 하나, 둘, 셋, 넷... (개수, 나이, 시간)
"""
import re
import logging
from typing import Dict, Tuple, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class NumberStyle(str, Enum):
    """숫자 읽기 스타일"""
    HANJA = "hanja"  # 한자어: 일, 이, 삼
    NATIVE = "native"  # 고유어: 하나, 둘, 셋
    AUTO = "auto"  # 문맥에 따라 자동


class KoreanTextNormalizer:
    """
    한국어 텍스트 정규화

    숫자를 한글로 변환하여 TTS 생성 시 일관성을 보장합니다.

    Example:
        normalizer = KoreanTextNormalizer()
        normalized, mappings = normalizer.normalize_script(
            "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
        )
        # → "이천이십사년 일월 십오일, 사과 세개를 이천원에 샀습니다."
    """

    # 한자어 수사
    HANJA_UNITS = ["", "십", "백", "천"]
    HANJA_DIGITS = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    HANJA_LARGE = ["", "만", "억", "조", "경"]

    # 고유어 수사
    NATIVE_DIGITS = ["", "하나", "둘", "셋", "넷", "다섯", "여섯", "일곱", "여덟", "아홉"]
    NATIVE_TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"]

    # 단위 변환 (수량 단위)
    COUNTER_UNITS = {
        "개": NumberStyle.NATIVE,
        "명": NumberStyle.NATIVE,
        "마리": NumberStyle.NATIVE,
        "살": NumberStyle.NATIVE,
        "시": NumberStyle.NATIVE,  # 2시 → 두시
        "분": NumberStyle.HANJA,   # 30분 → 삼십분
        "초": NumberStyle.HANJA,
        "원": NumberStyle.HANJA,
        "년": NumberStyle.HANJA,
        "월": NumberStyle.HANJA,
        "일": NumberStyle.HANJA,
    }

    def __init__(self, default_style: NumberStyle = NumberStyle.AUTO):
        """
        Args:
            default_style: 기본 숫자 읽기 스타일
        """
        self.default_style = default_style
        self.logger = logger

    @classmethod
    def number_to_hanja(cls, num: int) -> str:
        """
        숫자를 한자어로 변환

        Args:
            num: 변환할 숫자

        Returns:
            한자어 문자열

        Examples:
            >>> KoreanTextNormalizer.number_to_hanja(1234)
            '일천이백삼십사'
            >>> KoreanTextNormalizer.number_to_hanja(50000)
            '오만'
        """
        if num == 0:
            return "영"

        if num < 0:
            return "마이너스 " + cls.number_to_hanja(-num)

        result = []
        num_str = str(num)

        # 4자리씩 끊어서 처리 (만, 억, 조 단위)
        chunks = []
        temp_num = num
        while temp_num > 0:
            chunks.append(temp_num % 10000)
            temp_num //= 10000

        for i, chunk in enumerate(chunks):
            if chunk == 0:
                continue

            chunk_result = []
            chunk_str = str(chunk)

            # 각 자리수 처리 (왼쪽부터: 천, 백, 십, 일)
            for j, digit_char in enumerate(chunk_str):
                digit = int(digit_char)
                if digit == 0:
                    continue

                pos = len(chunk_str) - j - 1  # 자릿수: 3=천, 2=백, 1=십, 0=일

                # 1은 십, 백, 천 앞에서 생략 (일십 → 십)
                if digit == 1 and pos > 0:
                    chunk_result.append(cls.HANJA_UNITS[pos])
                else:
                    chunk_result.append(cls.HANJA_DIGITS[digit] + cls.HANJA_UNITS[pos])

            if chunk_result:
                # 만, 억, 조 단위 추가
                chunk_text = "".join(chunk_result)
                if i > 0:
                    chunk_text += cls.HANJA_LARGE[i]
                result.insert(0, chunk_text)

        return "".join(result)

    @classmethod
    def number_to_native(cls, num: int) -> str:
        """
        숫자를 고유어로 변환

        Args:
            num: 변환할 숫자 (1-99)

        Returns:
            고유어 문자열

        Examples:
            >>> KoreanTextNormalizer.number_to_native(25)
            '스물다섯'
            >>> KoreanTextNormalizer.number_to_native(3)
            '셋'
        """
        if num == 0:
            return "영"

        if num < 0:
            return "마이너스 " + cls.number_to_native(-num)

        if num >= 100:
            # 100 이상은 한자어 사용
            return cls.number_to_hanja(num)

        tens = num // 10
        ones = num % 10

        result = []
        if tens > 0:
            result.append(cls.NATIVE_TENS[tens])
        if ones > 0:
            result.append(cls.NATIVE_DIGITS[ones])

        return "".join(result)

    def normalize_script(self, script: str) -> Tuple[str, Dict[str, str]]:
        """
        스크립트의 숫자를 한글로 변환

        Args:
            script: 원본 스크립트

        Returns:
            (정규화된 스크립트, 변환 매핑)

        Examples:
            >>> normalizer = KoreanTextNormalizer()
            >>> normalized, mappings = normalizer.normalize_script(
            ...     "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
            ... )
            >>> normalized
            '이천이십사년 일월 십오일, 사과 세개를 이천원에 샀습니다.'
        """
        normalized = script
        mappings = {}

        # 1단계: 마크다운 헤더 및 메타데이터 제거
        # "### 훅 (첫 3초)", "### 본문", "### CTA" 등 제거
        lines = normalized.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # 마크다운 헤더 라인 제거 (### 훅, ## 본문, # 제목 등)
            if re.match(r'^#{1,6}\s+', stripped):
                self.logger.debug(f"Removed markdown header: {stripped}")
                continue

            # 섹션 구분자만 있는 라인 제거 ("훅.", "본문.", "CTA." 등)
            if re.match(r'^(훅|본문|CTA|행동\s*유도|첫\s*\d+초)[\.:]?\s*$', stripped, re.IGNORECASE):
                self.logger.debug(f"Removed section marker: {stripped}")
                continue

            # 메타데이터 라인 제거 ("--- 예상 영상 길이: 2분 30초", "--- 플랫폼: 유튜브" 등)
            if re.match(r'^[-*]{2,}\s*.+[:：]', stripped):
                self.logger.debug(f"Removed metadata line: {stripped}")
                continue

            # 빈 줄이 아니면 추가
            if stripped:
                cleaned_lines.append(stripped)

        # 정리된 텍스트로 재구성 (줄바꿈으로 연결)
        normalized = ' '.join(cleaned_lines)

        # 여러 공백을 하나로 정리
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # 패턴별 처리 (순서 중요!)
        patterns = [
            # 전화번호: 010-1234-5678 (다른 패턴보다 먼저 처리)
            (r'(\d{2,3})-(\d{3,4})-(\d{4})', self._normalize_phone),

            # 연도: 2024년 → 이천이십사년
            (r'(\d{4})년', lambda m: f"{self.number_to_hanja(int(m.group(1)))}년"),

            # 날짜: 1월 15일 → 일월 십오일
            (r'(\d{1,2})월', lambda m: f"{self.number_to_hanja(int(m.group(1)))}월"),
            (r'(\d{1,2})일', lambda m: f"{self.number_to_hanja(int(m.group(1)))}일"),

            # 금액: 2,000원 → 이천원
            (r'([\d,]+)원', lambda m: f"{self.number_to_hanja(int(m.group(1).replace(',', '')))}원"),

            # 퍼센트: 95.5% → 구십오점오퍼센트
            (r'(\d+\.?\d*)%', self._normalize_percentage),

            # 시간: 2시 30분 → 두시 삼십분
            (r'(\d{1,2})시', lambda m: f"{self.number_to_native(int(m.group(1)))}시"),
            (r'(\d{1,2})분', lambda m: f"{self.number_to_hanja(int(m.group(1)))}분"),
            (r'(\d{1,2})초', lambda m: f"{self.number_to_hanja(int(m.group(1)))}초"),

            # 개수: 3개 → 세개
            (r'(\d{1,2})개', lambda m: f"{self.number_to_native(int(m.group(1)))}개"),
            (r'(\d{1,2})명', lambda m: f"{self.number_to_native(int(m.group(1)))}명"),
            (r'(\d{1,2})마리', lambda m: f"{self.number_to_native(int(m.group(1)))}마리"),

            # 나이: 25살 → 스물다섯살
            (r'(\d{1,2})살', lambda m: f"{self.number_to_native(int(m.group(1)))}살"),
            (r'(\d{1,2})세', lambda m: f"{self.number_to_native(int(m.group(1)))}세"),

            # 소수점: 3.14 → 삼점일사
            (r'\b(\d+)\.(\d+)\b', self._normalize_decimal),

            # 일반 숫자: 기본은 한자어
            (r'\b(\d{1,})번', lambda m: f"{self.number_to_hanja(int(m.group(1)))}번"),
            (r'\b(\d{1,})\b', lambda m: self.number_to_hanja(int(m.group(1)))),
        ]

        for pattern, replacer in patterns:
            matches = list(re.finditer(pattern, normalized))
            # 뒤에서부터 치환 (인덱스 변경 방지)
            for match in reversed(matches):
                original = match.group(0)

                try:
                    if callable(replacer):
                        replaced = replacer(match)
                    else:
                        replaced = replacer

                    # 이미 한글로 변환된 경우 스킵
                    if original == replaced:
                        continue

                    mappings[original] = replaced
                    start, end = match.span()
                    normalized = normalized[:start] + replaced + normalized[end:]

                except Exception as e:
                    self.logger.warning(f"Failed to normalize '{original}': {e}")
                    continue

        return normalized, mappings

    def _normalize_phone(self, match) -> str:
        """
        전화번호 정규화

        Examples:
            010-1234-5678 → 공일공 일이삼사 오육칠팔
        """
        parts = [match.group(i) for i in range(1, match.lastindex + 1)]
        result = []

        for part in parts:
            # 각 자리수를 개별로 읽음
            digits = []
            for d in part:
                if d == "0":
                    digits.append("공")
                else:
                    digits.append(self.HANJA_DIGITS[int(d)])
            result.append("".join(digits))

        return " ".join(result)

    def _normalize_percentage(self, match) -> str:
        """
        퍼센트 정규화

        Examples:
            95.5% → 구십오점오퍼센트
        """
        num_str = match.group(1)

        if '.' in num_str:
            # 소수점 있는 경우
            integer, decimal = num_str.split('.')
            result = self.number_to_hanja(int(integer))
            result += "점"
            # 소수점 이하는 각 자리수를 읽음
            for d in decimal:
                result += self.HANJA_DIGITS[int(d)]
            return result + "퍼센트"
        else:
            # 정수인 경우
            return self.number_to_hanja(int(num_str)) + "퍼센트"

    def _normalize_decimal(self, match) -> str:
        """
        소수점 정규화

        Examples:
            3.14 → 삼점일사
        """
        integer = match.group(1)
        decimal = match.group(2)

        result = self.number_to_hanja(int(integer))
        result += "점"

        # 소수점 이하는 각 자리수를 읽음
        for d in decimal:
            result += self.HANJA_DIGITS[int(d)]

        return result


# 싱글톤 인스턴스
_normalizer_instance: Optional[KoreanTextNormalizer] = None


def get_text_normalizer(style: NumberStyle = NumberStyle.AUTO) -> KoreanTextNormalizer:
    """텍스트 정규화 싱글톤 인스턴스"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = KoreanTextNormalizer(default_style=style)
    return _normalizer_instance
