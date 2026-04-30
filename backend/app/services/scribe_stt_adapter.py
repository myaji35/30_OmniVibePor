"""
ElevenLabs Scribe STT 어댑터 — ISS-150

browser-use/video-use의 helpers/transcribe.py 로직을 OmniVibe Pro에 맞게 포팅.
word-level timestamp + speaker diarization을 WordTimestamp 배열로 정규화.

ElevenLabs Scribe API 정보:
    엔드포인트: https://api.elevenlabs.io/v1/speech-to-text
    메서드: POST (multipart/form-data)
    헤더: xi-api-key: <ELEVENLABS_API_KEY>
    요청 파라미터:
        - audio: (binary) 오디오 파일
        - model_id: str = "scribe_v1" (기본값)
        - num_speakers: int | None (화자 수 힌트)
        - timestamps_granularity: str = "word" (word|character|none)
        - diarize: bool = True (화자 분리 활성화)
    응답 구조 (추정 — 실제 필드명 변경 시 _parse_response만 수정):
        {
            "text": "전체 텍스트",
            "words": [
                {
                    "text": "단어",
                    "start": 0.0,      # 초(float)
                    "end": 0.5,        # 초(float)
                    "speaker_id": "speaker_0" | null,
                    "type": "word" | "spacing" | "audio_event"
                },
                ...
            ],
            "additional_formats": {...}
        }

Duration Rules (plan §4.3):
    - 2단어씩 UPPERCASE 청킹
    - speaker_id 변경 시 청크 강제 분할
    - 단어 간 gap > 0.5s 시 청크 분할
    - 마지막 청크 end에 1.0s 홀드 추가

인터페이스 호환:
    STTAdapter Protocol을 통해 기존 stt_service.STTService와 교체 가능.
    transcribe(audio_path: Path) -> TranscriptionResult 시그니처 공통.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

import httpx

from app.services.overlay_generator_service import WordTimestamp  # ISS-149 정의 재사용

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# API 상수
# ─────────────────────────────────────────────────────────────────────────────

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
SCRIBE_ENDPOINT = f"{ELEVENLABS_API_BASE}/speech-to-text"

# 청킹 기본값 (plan §4.3)
_DEFAULT_WORDS_PER_CHUNK: int = 2
_DEFAULT_HOLD_SECONDS: float = 1.0
_DEFAULT_GAP_THRESHOLD: float = 0.5  # 단어 사이 gap이 이 값(초) 초과면 분할


# ─────────────────────────────────────────────────────────────────────────────
# 결과 / 청크 dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TranscriptionResult:
    """Scribe STT 어댑터 반환값.

    Attributes:
        words:          word-level WordTimestamp 배열 (초 단위)
        full_text:      전체 텍스트 (공백 결합)
        duration_sec:   오디오 총 길이 (마지막 word.end 기준)
        speaker_count:  감지된 화자 수 (speaker_id 기준)
        raw_response:   디버그용 원시 API 응답 (None 가능)
    """

    words: list[WordTimestamp]
    full_text: str
    duration_sec: float
    speaker_count: int
    raw_response: dict | None = None


@dataclass
class SubtitleChunk:
    """2단어 UPPERCASE 청킹 결과 (plan §4.3 Duration rules).

    Attributes:
        text:       "HELLO WORLD" 형태의 UPPERCASE 결합 텍스트
        start:      첫 번째 단어의 start (초)
        end:        마지막 단어의 end + hold_seconds (초)
        word_count: 포함된 단어 수
    """

    text: str
    start: float
    end: float
    word_count: int


# ─────────────────────────────────────────────────────────────────────────────
# STTAdapter Protocol — stt_service.STTService와 교체 가능 인터페이스
# ─────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class STTAdapter(Protocol):
    """기존 stt_service와 호환되는 어댑터 인터페이스.

    audio_correction_loop.py에서 STTService 대신 ScribeSTTAdapter로
    교체할 때 이 Protocol을 타입 가드로 활용한다.
    """

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """오디오 파일을 TranscriptionResult로 변환."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# ScribeSTTAdapter
# ─────────────────────────────────────────────────────────────────────────────

class ScribeSTTAdapter:
    """ElevenLabs Scribe API 어댑터.

    기존 OpenAI Whisper 어댑터(stt_service.STTService)와 동일한 인터페이스를 제공하여
    Director Agent의 Zero-Fault Audio 루프에서 교체 가능하다.

    사용 예:
        adapter = ScribeSTTAdapter()
        result = await adapter.transcribe(Path("narration.mp3"))
        chunks = adapter.chunk_subtitles(result.words)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        num_speakers: Optional[int] = None,
        model_id: str = "scribe_v1",
        timeout: float = 120.0,
    ) -> None:
        """
        Args:
            api_key:       ElevenLabs API 키. 미제공 시 ELEVENLABS_API_KEY 환경변수 사용.
                           신규 키 발급 금지 — TTS와 동일한 키 재사용.
            num_speakers:  화자 수 힌트 (None이면 자동 감지)
            model_id:      Scribe 모델 ID
            timeout:       httpx 요청 타임아웃(초)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY 미설정 — TTS 키 재사용. 신규 키 발급 금지.\n"
                "backend/.env 또는 환경변수에 ELEVENLABS_API_KEY를 설정하세요."
            )
        self.num_speakers = num_speakers
        self.model_id = model_id
        self.timeout = timeout

    # ── 공개 API ──────────────────────────────────────────────────────────────

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """오디오 파일을 word-level TranscriptionResult로 변환.

        Args:
            audio_path: 처리할 오디오 파일 경로 (mp3/m4a/wav 등)

        Returns:
            TranscriptionResult — words, full_text, duration_sec, speaker_count

        Raises:
            FileNotFoundError: audio_path가 존재하지 않을 때
            httpx.HTTPStatusError: Scribe API 오류 응답
            ValueError: API 키 미설정
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일 없음: {audio_path}")

        logger.info("Scribe STT 시작: %s", audio_path.name)

        data = await self._call_scribe_api(audio_path)
        words = self._parse_response(data)
        full_text = " ".join(w.word for w in words)
        duration_sec = words[-1].end if words else 0.0
        speaker_ids = {w.speaker_id for w in words if w.speaker_id is not None}

        logger.info(
            "Scribe STT 완료: %d words, %.1fs, %d speakers",
            len(words),
            duration_sec,
            len(speaker_ids),
        )

        return TranscriptionResult(
            words=words,
            full_text=full_text,
            duration_sec=duration_sec,
            speaker_count=len(speaker_ids),
            raw_response=data,
        )

    def chunk_subtitles(
        self,
        words: list[WordTimestamp],
        words_per_chunk: int = _DEFAULT_WORDS_PER_CHUNK,
        uppercase: bool = True,
        hold_seconds: float = _DEFAULT_HOLD_SECONDS,
        gap_threshold: float = _DEFAULT_GAP_THRESHOLD,
    ) -> list[SubtitleChunk]:
        """video-use 스타일 2단어 UPPERCASE 청킹.

        분할 조건 (plan §4.3 Duration rules):
            1. words_per_chunk 단어 수 초과
            2. speaker_id 변경 (화자 전환)
            3. 연속 단어 사이 gap > gap_threshold 초

        마지막 청크는 end + hold_seconds (마지막 프레임 홀드).

        Args:
            words:           WordTimestamp 배열
            words_per_chunk: 청크당 최대 단어 수 (기본 2)
            uppercase:       텍스트를 UPPERCASE로 변환할지 여부
            hold_seconds:    마지막 청크 end에 추가할 홀드 시간(초)
            gap_threshold:   단어 사이 gap 분할 기준(초)

        Returns:
            SubtitleChunk 배열
        """
        if not words:
            return []

        chunks: list[SubtitleChunk] = []
        current_group: list[WordTimestamp] = []

        def _flush(is_last: bool = False) -> None:
            """current_group을 SubtitleChunk로 변환하고 비운다."""
            if not current_group:
                return
            text = " ".join(w.word for w in current_group)
            if uppercase:
                text = text.upper()
            raw_end = current_group[-1].end
            final_end = raw_end + hold_seconds if is_last else raw_end
            chunks.append(
                SubtitleChunk(
                    text=text,
                    start=current_group[0].start,
                    end=final_end,
                    word_count=len(current_group),
                )
            )
            current_group.clear()

        for i, word in enumerate(words):
            if current_group:
                prev = current_group[-1]
                speaker_changed = (
                    word.speaker_id is not None
                    and prev.speaker_id is not None
                    and word.speaker_id != prev.speaker_id
                )
                gap_exceeded = (word.start - prev.end) > gap_threshold
                chunk_full = len(current_group) >= words_per_chunk

                if speaker_changed or gap_exceeded or chunk_full:
                    _flush(is_last=False)

            current_group.append(word)

        # 마지막 그룹 플러시 (hold_seconds 적용)
        _flush(is_last=True)

        return chunks

    # ── 내부 메서드 ────────────────────────────────────────────────────────────

    async def _call_scribe_api(self, audio_path: Path) -> dict:
        """ElevenLabs Scribe API를 호출하고 원시 JSON 딕셔너리를 반환.

        필드명 변경 시 이 함수가 아닌 _parse_response를 수정한다.
        """
        form_data: dict = {
            "model_id": self.model_id,
            "timestamps_granularity": "word",
            "diarize": "true",
        }
        if self.num_speakers is not None:
            form_data["num_speakers"] = str(self.num_speakers)

        headers = {"xi-api-key": self.api_key}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with audio_path.open("rb") as f:
                response = await client.post(
                    SCRIBE_ENDPOINT,
                    headers=headers,
                    data=form_data,
                    files={"audio": (audio_path.name, f, "audio/mpeg")},
                )

        response.raise_for_status()
        return response.json()

    def _parse_response(self, data: dict) -> list[WordTimestamp]:
        """Scribe API 응답 딕셔너리를 WordTimestamp 배열로 정규화.

        이 함수만 수정하면 API 응답 필드명 변경에 대응 가능하다.

        ElevenLabs Scribe 응답에서 type == "word" 인 항목만 추출한다.
        spacing/audio_event 항목은 건너뛴다.
        """
        raw_words: list[dict] = data.get("words", [])
        result: list[WordTimestamp] = []

        for item in raw_words:
            # spacing / audio_event 타입은 건너뜀
            word_type = item.get("type", "word")
            if word_type != "word":
                continue

            text: str = item.get("text", "").strip()
            if not text:
                continue

            start: float = float(item.get("start", 0.0))
            end: float = float(item.get("end", start + 0.1))

            # end가 start 이하인 경우 최소 간격 보장
            if end <= start:
                end = start + 0.05

            speaker_id: Optional[str] = item.get("speaker_id") or None
            confidence: Optional[float] = item.get("confidence")
            if confidence is not None:
                confidence = max(0.0, min(1.0, float(confidence)))

            result.append(
                WordTimestamp(
                    word=text,
                    start=start,
                    end=end,
                    speaker_id=speaker_id,
                    confidence=confidence,
                )
            )

        return result
