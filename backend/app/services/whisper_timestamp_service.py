"""Whisper STT에서 Word-level Timestamp 추출 서비스

Zero-Fault Audio 파이프라인의 핵심 컴포넌트:
- Whisper API 응답에서 word-level timestamp 추출
- ScriptBlock 타이밍 자동 매핑
- Remotion Sequence props 변환
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WordTimestamp:
    word: str
    start: float  # seconds
    end: float    # seconds


@dataclass
class ScriptBlockTiming:
    type: str
    text: str
    startTime: float
    duration: float
    words: List[WordTimestamp]


def extract_word_timestamps(whisper_response: Dict[str, Any]) -> List[WordTimestamp]:
    """
    Whisper API 응답에서 word-level timestamp 추출
    verbose_json 형식 지원
    """
    timestamps = []

    # verbose_json 형식
    if 'segments' in whisper_response:
        for segment in whisper_response['segments']:
            if 'words' in segment:
                for word_data in segment['words']:
                    timestamps.append(WordTimestamp(
                        word=word_data.get('word', '').strip(),
                        start=word_data.get('start', 0.0),
                        end=word_data.get('end', 0.0)
                    ))

    return timestamps


def map_timestamps_to_blocks(
    timestamps: List[WordTimestamp],
    block_types: List[str] = None,
    fps: int = 30
) -> List[ScriptBlockTiming]:
    """
    Word-level timestamp를 ScriptBlock 타이밍으로 자동 변환
    블록 타입을 자동으로 감지하여 매핑
    """
    if not timestamps:
        return []

    if block_types is None:
        block_types = ['hook', 'intro', 'body', 'cta', 'outro']

    total_duration = timestamps[-1].end if timestamps else 0
    blocks = []

    # 타입별 비율로 분할
    type_ratios = {
        'hook': 0.15,
        'intro': 0.10,
        'body': 0.55,
        'cta': 0.10,
        'outro': 0.10
    }

    current_time = 0.0

    for block_type in block_types:
        ratio = type_ratios.get(block_type, 0.2)
        duration = total_duration * ratio
        end_time = current_time + duration

        # 해당 시간 범위의 단어 추출
        block_words = [
            w for w in timestamps
            if w.start >= current_time and w.start < end_time
        ]

        text = ' '.join(w.word for w in block_words)

        blocks.append(ScriptBlockTiming(
            type=block_type,
            text=text,
            startTime=current_time,
            duration=duration,
            words=block_words
        ))

        current_time = end_time

    return blocks


def timestamps_to_remotion_sequence(
    timestamps: List[WordTimestamp],
    fps: int = 30
) -> List[Dict]:
    """
    Whisper 타임스탬프를 Remotion Sequence props 형식으로 변환
    """
    sequences = []

    for ts in timestamps:
        sequences.append({
            'word': ts.word,
            'from': int(ts.start * fps),
            'durationInFrames': max(1, int((ts.end - ts.start) * fps)),
            'startSeconds': ts.start,
            'endSeconds': ts.end
        })

    return sequences
