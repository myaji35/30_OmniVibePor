"""DurationCalculator - 텍스트 → 음성 시간 예측

REALPLAN.md Phase 3.1 구현

기능:
- 텍스트 길이 → 예상 오디오 시간 계산
- 언어별 읽기 속도 설정
- 구두점 휴지 고려
- 학습 데이터 기반 보정
"""

import re
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """지원 언어"""
    KO = "ko"  # 한국어
    EN = "en"  # 영어
    JA = "ja"  # 일본어
    ZH = "zh"  # 중국어


class DurationCalculator:
    """텍스트 → 음성 시간 예측 계산기"""

    # 언어별 기본 읽기 속도 (분당 글자/단어 수)
    READING_SPEEDS = {
        Language.KO: 200,  # 한국어: 분당 200자
        Language.EN: 150,  # 영어: 분당 150단어
        Language.JA: 180,  # 일본어: 분당 180자
        Language.ZH: 220,  # 중국어: 분당 220자
    }

    # 구두점별 휴지 시간 (초)
    PAUSE_DURATIONS = {
        '.': 0.5,   # 마침표
        '。': 0.5,  # 한글 마침표
        '?': 0.5,   # 물음표
        '!': 0.5,   # 느낌표
        ',': 0.3,   # 쉼표
        '、': 0.3,  # 한글 쉼표
        ';': 0.3,   # 세미콜론
        ':': 0.2,   # 콜론
        '\n': 0.4,  # 줄바꿈
    }

    def __init__(self, language: Language = Language.KO):
        """
        Args:
            language: 텍스트 언어
        """
        self.language = language
        self.base_speed = self.READING_SPEEDS[language]
        self.correction_factor = 1.0  # 학습 데이터 기반 보정 계수

    def calculate(self, text: str) -> Dict[str, float]:
        """
        텍스트의 예상 오디오 시간 계산

        Args:
            text: 입력 텍스트

        Returns:
            {
                'duration': 예상 시간 (초),
                'base_duration': 기본 읽기 시간 (초),
                'pause_duration': 구두점 휴지 시간 (초),
                'word_count': 글자/단어 수,
                'correction_factor': 보정 계수
            }
        """
        if not text or not text.strip():
            return {
                'duration': 0.0,
                'base_duration': 0.0,
                'pause_duration': 0.0,
                'word_count': 0,
                'correction_factor': self.correction_factor
            }

        # 1. 글자/단어 수 계산
        word_count = self._count_words(text)

        # 2. 기본 읽기 시간 (초)
        base_duration = (word_count / self.base_speed) * 60

        # 3. 구두점 휴지 시간 (초)
        pause_duration = self._calculate_pause_duration(text)

        # 4. 총 예상 시간 (보정 계수 적용)
        total_duration = (base_duration + pause_duration) * self.correction_factor

        result = {
            'duration': round(total_duration, 1),
            'base_duration': round(base_duration, 1),
            'pause_duration': round(pause_duration, 1),
            'word_count': word_count,
            'correction_factor': self.correction_factor
        }

        logger.debug(f"Duration calculation: {result}")
        return result

    def _count_words(self, text: str) -> int:
        """
        언어별 글자/단어 수 계산

        Args:
            text: 입력 텍스트

        Returns:
            글자/단어 수
        """
        # 공백 및 특수문자 제거
        cleaned = text.strip()

        if self.language == Language.EN:
            # 영어: 단어 수
            words = re.findall(r'\b\w+\b', cleaned)
            return len(words)
        else:
            # 한국어/일본어/중국어: 글자 수 (공백 제외)
            chars = re.sub(r'\s+', '', cleaned)
            # 구두점 제외
            chars = re.sub(r'[.,;:!?。、]', '', chars)
            return len(chars)

    def _calculate_pause_duration(self, text: str) -> float:
        """
        구두점 휴지 시간 계산

        Args:
            text: 입력 텍스트

        Returns:
            총 휴지 시간 (초)
        """
        total_pause = 0.0

        for char in text:
            if char in self.PAUSE_DURATIONS:
                total_pause += self.PAUSE_DURATIONS[char]

        return total_pause

    def update_correction_factor(self, predicted: float, actual: float):
        """
        학습 데이터 기반 보정 계수 업데이트

        Args:
            predicted: 예측 시간 (초)
            actual: 실제 TTS 시간 (초)
        """
        if predicted <= 0 or actual <= 0:
            return

        # 실제 시간 / 예측 시간 = 보정 계수
        new_factor = actual / predicted

        # 이동 평균으로 부드럽게 업데이트 (alpha = 0.1)
        self.correction_factor = 0.9 * self.correction_factor + 0.1 * new_factor

        logger.info(
            f"Updated correction factor: {self.correction_factor:.3f} "
            f"(predicted: {predicted:.1f}s, actual: {actual:.1f}s)"
        )

    def estimate_for_target_duration(
        self,
        target_duration: float,
        margin: float = 0.1
    ) -> Dict[str, int]:
        """
        목표 시간에 맞는 글자 수 범위 계산

        Args:
            target_duration: 목표 시간 (초)
            margin: 오차 범위 (기본: 10%)

        Returns:
            {
                'min_words': 최소 글자/단어 수,
                'max_words': 최대 글자/단어 수,
                'target_words': 목표 글자/단어 수
            }
        """
        # 목표 시간 범위
        min_duration = target_duration * (1 - margin)
        max_duration = target_duration * (1 + margin)

        # 평균 휴지 비율 (전체 시간의 약 15%)
        avg_pause_ratio = 0.15

        # 기본 읽기 시간 = 총 시간 * (1 - 휴지 비율) / 보정 계수
        base_min = (min_duration * (1 - avg_pause_ratio)) / self.correction_factor
        base_max = (max_duration * (1 - avg_pause_ratio)) / self.correction_factor

        # 글자/단어 수 = (기본 읽기 시간 / 60) * 읽기 속도
        min_words = int((base_min / 60) * self.base_speed)
        max_words = int((base_max / 60) * self.base_speed)
        target_words = int(((target_duration * (1 - avg_pause_ratio)) / self.correction_factor / 60) * self.base_speed)

        return {
            'min_words': min_words,
            'max_words': max_words,
            'target_words': target_words
        }


# ==================== 싱글톤 인스턴스 ====================

_calculator_instances: Dict[Language, DurationCalculator] = {}


def get_duration_calculator(language: Language = Language.KO) -> DurationCalculator:
    """
    DurationCalculator 싱글톤 인스턴스 (언어별)

    Args:
        language: 텍스트 언어

    Returns:
        DurationCalculator 인스턴스
    """
    if language not in _calculator_instances:
        _calculator_instances[language] = DurationCalculator(language)

    return _calculator_instances[language]


# ==================== Utility Functions ====================

def calculate_duration(text: str, language: str = "ko") -> float:
    """
    간편 함수: 텍스트 → 예상 시간 (초)

    Args:
        text: 입력 텍스트
        language: 언어 코드 (ko, en, ja, zh)

    Returns:
        예상 시간 (초)
    """
    lang = Language(language)
    calculator = get_duration_calculator(lang)
    result = calculator.calculate(text)
    return result['duration']


def estimate_word_count(target_duration: float, language: str = "ko") -> int:
    """
    간편 함수: 목표 시간 → 필요 글자/단어 수

    Args:
        target_duration: 목표 시간 (초)
        language: 언어 코드

    Returns:
        목표 글자/단어 수
    """
    lang = Language(language)
    calculator = get_duration_calculator(lang)
    result = calculator.estimate_for_target_duration(target_duration)
    return result['target_words']
