"""
텍스트 처리 헬퍼 함수들
"""
import re
from typing import List, Dict, Any


def normalize_script(text: str) -> str:
    """
    스크립트 정규화 (TTS가 읽지 말아야 할 메타데이터 제거)
    """
    # Markdown 헤더 제거
    text = re.sub(r'#{1,6}\s+', '', text)

    # 괄호 주석 제거
    text = re.sub(r'\[.*?\]', '', text)

    # 특수문자 정리
    text = re.sub(r'[•\-\*]', '', text)

    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def calculate_duration(text: str, language: str = "ko") -> int:
    """
    텍스트를 음성으로 읽을 때 소요 시간 계산 (초 단위)
    """
    if not text.strip():
        return 0

    # 언어별 평균 읽기 속도 (문자/초)
    speed_map = {
        "ko": 8,   # 한국어: 초당 약 8자
        "en": 15,  # 영어: 초당 약 15자
        "ja": 10   # 일본어: 초당 약 10자
    }

    speed = speed_map.get(language, 10)
    char_count = len(text.strip())

    duration = char_count / speed
    return int(duration) + 1


def extract_keywords(text: str, language: str = "ko", top_n: int = 5) -> List[str]:
    """
    텍스트에서 핵심 키워드 추출
    """
    # 한국어 불용어
    stopwords_ko = {
        "이", "그", "저", "것", "수", "등", "및", "에", "의", "가", "을", "를",
        "은", "는", "이것", "그것", "저것", "매우", "아주", "정말", "너무", "조금"
    }

    # 단어 분리
    words = re.findall(r'\b\w+\b', text)

    # 불용어 제거
    keywords = []
    for word in words:
        if len(word) > 1 and word not in stopwords_ko:
            keywords.append(word)

    # 중복 제거 및 상위 N개 반환
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:top_n]


def split_into_blocks(
    text: str,
    method: str = "paragraph",
    max_duration: int = 10
) -> List[Dict[str, Any]]:
    """
    스크립트를 의미 단위 블록으로 분할
    """
    blocks = []

    if method == "paragraph":
        paragraphs = text.split('\n\n')

        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            duration = calculate_duration(para)

            if i == 0:
                block_type = "hook"
            elif i == len(paragraphs) - 1:
                block_type = "cta"
            else:
                block_type = "body"

            blocks.append({
                "text": para,
                "duration": duration,
                "type": block_type
            })

    elif method == "duration":
        sentences = re.split(r'[.!?]\s+', text)
        current_block = ""
        current_duration = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_duration = calculate_duration(sentence)

            if current_duration + sentence_duration > max_duration and current_block:
                blocks.append({
                    "text": current_block.strip(),
                    "duration": current_duration,
                    "type": "body"
                })
                current_block = sentence + ". "
                current_duration = sentence_duration
            else:
                current_block += sentence + ". "
                current_duration += sentence_duration

        if current_block:
            blocks.append({
                "text": current_block.strip(),
                "duration": current_duration,
                "type": "cta" if len(blocks) > 0 else "hook"
            })

    return blocks
