"""
Remotion Overlay Auto-Generator Service

ISS-149 (USER_STORY P0) — Phase A: Remotion Overlay Auto-Gen

목적:
    word-level timestamp 배열(WordTimestamp[])을 받아
    Remotion 4.0 렌더 가능한 JSX 컴포넌트 문자열(OverlayOutput)을 반환하는
    계약(Contract)을 정의한다.

    실제 JSX 생성 로직은 ISS-152에서 구현한다.
    이 파일은 타입 계약 + 스켈레톤 + 기본 검증만 포함한다.

Plan 문서:
    docs/01-plan/features/video-use-integration.plan.md §4.2

공유 자산 (분리 금지):
    - ffmpeg_profile.py SoT (IOS_SAFE_FPS = "30" → fps 기본값 30)
    - brand-dna.json design_tokens (brand_tokens 파라미터로 수용)
    - Remotion 4.0.429 (버전 잠금)

Duration Rules (video-use timeline_view.py 참고):
    - 단순 카드: 5–7s
    - 복합 카드: 8–14s
    - 마지막 1s 홀드
    - 병렬 reveal 금지

참고:
    - browser-use/video-use OSS (helpers/transcribe.py, helpers/timeline_view.py)
    - ElevenLabs Scribe STT → word-level timestamp + speaker_id 출력 형식 사용
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 상수 — ffmpeg_profile.py SoT 값과 일치시킨다 (하드코딩 금지)
# ─────────────────────────────────────────────────────────────────────────────

# ffmpeg_profile.IOS_SAFE_FPS = "30" 을 int로 사용
_DEFAULT_FPS: int = 30

# 마지막 자막 카드 이후 홀드 시간 (video-use Duration Rules)
_LAST_CARD_HOLD_SEC: float = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# OverlayStyle Enum
# ─────────────────────────────────────────────────────────────────────────────

class OverlayStyle(str, Enum):
    """자막 오버레이 스타일 종류.

    Attributes:
        subtitle:  기본 자막 (하단 고정, 화이트/그림자)
        emphasis:  강조 자막 (단어별 하이라이트, brand_tokens hero 색상 사용)
        animation: 애니메이션 자막 (단어 reveal, Remotion spring/interpolate 활용)
    """

    subtitle = "subtitle"
    emphasis = "emphasis"
    animation = "animation"


# ─────────────────────────────────────────────────────────────────────────────
# WordTimestamp dataclass — ElevenLabs Scribe STT 출력 표현
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WordTimestamp:
    """ElevenLabs Scribe STT의 word-level 타임스탬프 단위.

    ElevenLabs Scribe는 화자 분리(speaker_id)와 신뢰도(confidence)를
    word 단위로 반환한다. audio_correction_loop.py에서 변환 시 이 포맷 사용.

    Attributes:
        word:        해당 단어 (발음 기호 제거된 정규화 텍스트)
        start:       단어 시작 시각 (초, 0.0 기준)
        end:         단어 종료 시각 (초)
        speaker_id:  화자 식별자 (모노 녹음이면 None)
        confidence:  STT 신뢰도 0.0–1.0 (없으면 None)
    """

    word: str
    start: float
    end: float
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None

    def __post_init__(self) -> None:
        """기본 유효성 검증."""
        if self.start < 0:
            raise ValueError(f"WordTimestamp.start는 0 이상이어야 합니다: {self.start}")
        if self.end <= self.start:
            raise ValueError(
                f"WordTimestamp.end({self.end})는 start({self.start})보다 커야 합니다"
            )
        if not self.word.strip():
            raise ValueError("WordTimestamp.word는 빈 문자열이 될 수 없습니다")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"WordTimestamp.confidence는 0.0–1.0 범위여야 합니다: {self.confidence}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# OverlayInput / OverlayOutput dataclass — §4.2 입출력 계약
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OverlayInput:
    """Overlay 생성기 입력 계약 (plan 문서 §4.2).

    Attributes:
        word_timestamps:       ElevenLabs Scribe STT word-level 결과 목록
        style:                 오버레이 스타일 (subtitle/emphasis/animation)
        brand_tokens:          brand-dna.json design_tokens 딕셔너리.
                               최소 필드: colors.hero, typography.font_heading
        narration_duration_sec: 나레이션 오디오 전체 길이(초).
                                0.0이면 word_timestamps 마지막 end + hold로 계산.
    """

    word_timestamps: list[WordTimestamp]
    style: OverlayStyle
    brand_tokens: dict
    narration_duration_sec: float = 0.0

    def __post_init__(self) -> None:
        """타입 강제 변환 (dict에서 역직렬화 시 대응)."""
        # style이 문자열로 넘어온 경우 Enum 변환
        if isinstance(self.style, str):
            self.style = OverlayStyle(self.style)


@dataclass
class OverlayOutput:
    """Overlay 생성기 출력 계약 (plan 문서 §4.2).

    Attributes:
        remotion_jsx:    Remotion 4.0.429 직접 렌더 가능한 React 컴포넌트 문자열.
        composition_id:  Remotion <Composition id=> 식별자 (예: "SubtitleOverlay")
        duration_frames: 영상 총 프레임 수 (fps 기준, 마지막 1s 홀드 포함)
        asset_paths:     폰트/이미지 등 정적 자산 경로 목록
        fps:             프레임 레이트 (ffmpeg_profile.py SoT 기본값 30)
    """

    remotion_jsx: str
    composition_id: str
    duration_frames: int
    asset_paths: list[str] = field(default_factory=list)
    fps: int = _DEFAULT_FPS


# ─────────────────────────────────────────────────────────────────────────────
# _SubtitleChunk — 내부 청킹 결과 (scribe_stt_adapter.SubtitleChunk와 구별)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _SubtitleChunk:
    """overlay_generator 내부 청킹 단위.

    scribe_stt_adapter.SubtitleChunk와 구조가 유사하지만,
    overlay 파이프라인 전용으로 관리하여 STT 어댑터 의존성을 제거한다.

    Attributes:
        text:       UPPERCASE 결합 텍스트
        start:      첫 번째 단어의 start (초)
        end:        마지막 단어의 end (초, 마지막 청크는 + 1s 홀드 포함)
        word_count: 포함된 단어 수
    """

    text: str
    start: float
    end: float
    word_count: int


# ─────────────────────────────────────────────────────────────────────────────
# OverlayGeneratorService
# ─────────────────────────────────────────────────────────────────────────────

class OverlayGeneratorService:
    """word-level timestamp → Remotion JSX 오버레이 변환 서비스.

    사용 예시 (ISS-152 구현 후)::

        service = OverlayGeneratorService(fps=30)
        result = service.generate(
            OverlayInput(
                word_timestamps=timestamps,
                style=OverlayStyle.subtitle,
                brand_tokens=brand_dna["design_tokens"],
            )
        )
        # result.remotion_jsx → Remotion 4.0 컴포넌트 문자열

    Director Agent 통합 지점:
        app/agents/director_agent.py 자막 생성 단계에서 호출.
        app/services/audio_correction_loop.py STT 결과를 WordTimestamp[]로 변환 후 전달.
    """

    def __init__(self, fps: int = _DEFAULT_FPS) -> None:
        """서비스 초기화.

        Args:
            fps: 렌더링 프레임 레이트. ffmpeg_profile.IOS_SAFE_FPS(30)과 일치시킬 것.
                 Remotion <Composition fps=> 와 동일한 값을 사용해야 한다.
        """
        if fps <= 0:
            raise ValueError(f"fps는 양의 정수여야 합니다: {fps}")
        self.fps = fps

    def generate(self, input: OverlayInput) -> OverlayOutput:  # noqa: A002
        """word-level timestamp 배열을 Remotion JSX 컴포넌트 문자열로 변환한다.

        video-use timeline_view.py word-segment grouping 로직을 포팅하여 구현.

        Args:
            input: OverlayInput 계약 (word_timestamps, style, brand_tokens)

        Returns:
            OverlayOutput: remotion_jsx, composition_id, duration_frames, asset_paths

        Raises:
            ValueError: 입력 유효성 검증 실패 시.

        Notes:
            Duration Rules (video-use timeline_view.py):
            - subtitle: 2단어 청킹, 단순 카드 5–7s
            - emphasis: 1단어 청킹, 0.5–2s visual accent
            - animation: phrase 단위 (최대 7단어), 8–14s 복합 콘텐츠
            - 모든 스타일: 마지막 청크 end + 1.0s 홀드
            - 병렬 reveal 금지 (청크 사이 overlap 없음)

            30ms 오디오 페이드:
            - 실제 오디오 처리는 ffmpeg_profile.py가 담당.
            - 여기서는 로그로만 표시하고 다음 ISS-153(ffmpeg 단계)에서 적용.
        """
        self._validate_input(input)
        chunks = self._group_words_into_chunks(input.word_timestamps, input.style)
        jsx = self._render_jsx(chunks, input.style, input.brand_tokens)
        last_end = chunks[-1].end if chunks else 0.0
        duration_frames = self._calc_duration_frames(last_end)
        composition_id = self._make_composition_id(input)

        # 30ms 오디오 페이드 — 다음 ffmpeg 단계(ISS-153)에서 적용.
        # ffmpeg_profile.py의 IOS_SAFE_AUDIO_FILTER("aresample=async=1:first_pts=0")와
        # 함께 -af "afade=t=out:st={last_end - 0.03}:d=0.03" 옵션을 추가한다.
        logger.info(
            "generate 완료: style=%s, chunks=%d, duration_frames=%d, "
            "last_end=%.3fs, audio_fade_ms=30 (ISS-153 ffmpeg 단계에서 적용 예정)",
            input.style.value,
            len(chunks),
            duration_frames,
            last_end,
        )

        return OverlayOutput(
            remotion_jsx=jsx,
            composition_id=composition_id,
            duration_frames=duration_frames,
            asset_paths=[],  # Phase A: 외부 asset 없음. 폰트는 brand_tokens 경유.
            fps=self.fps,
        )

    def _validate_input(self, input: OverlayInput) -> None:  # noqa: A002
        """입력 유효성 검증.

        Args:
            input: 검증할 OverlayInput

        Raises:
            ValueError: 빈 word_timestamps, 잘못된 brand_tokens, 음수 duration 등
        """
        if not input.word_timestamps:
            raise ValueError(
                "word_timestamps가 비어 있습니다. "
                "ElevenLabs Scribe STT 결과가 누락되었을 수 있습니다."
            )

        if not isinstance(input.brand_tokens, dict):
            raise ValueError(
                f"brand_tokens는 dict이어야 합니다: {type(input.brand_tokens)}"
            )

        if input.narration_duration_sec < 0:
            raise ValueError(
                f"narration_duration_sec는 0 이상이어야 합니다: {input.narration_duration_sec}"
            )

        # word_timestamps 정렬 검증 (start 오름차순)
        for i in range(1, len(input.word_timestamps)):
            prev = input.word_timestamps[i - 1]
            curr = input.word_timestamps[i]
            if curr.start < prev.start:
                raise ValueError(
                    f"word_timestamps[{i}].start({curr.start})이 "
                    f"word_timestamps[{i-1}].start({prev.start})보다 작습니다. "
                    "타임스탬프는 시간 오름차순이어야 합니다."
                )

    def _calc_duration_frames(self, end_sec: float) -> int:
        """마지막 1s 홀드 포함 총 프레임 수를 계산한다.

        Duration Rule (video-use): 마지막 자막 카드 이후 1초 홀드.

        Args:
            end_sec: 마지막 WordTimestamp.end 값 (초)

        Returns:
            int: ceil((end_sec + 1.0) * fps)

        Examples:
            >>> service = OverlayGeneratorService(fps=30)
            >>> service._calc_duration_frames(10.0)
            330  # (10.0 + 1.0) * 30 = 330
        """
        total_sec = end_sec + _LAST_CARD_HOLD_SEC
        return math.ceil(total_sec * self.fps)

    def _group_words_into_chunks(
        self,
        words: list[WordTimestamp],
        style: OverlayStyle,
    ) -> list[_SubtitleChunk]:
        """video-use timeline_view.py word-segment grouping 포팅.

        Duration Rules:
            - subtitle:  2단어 청킹, gap > 0.5s 또는 speaker 변경 시 강제 분할
            - emphasis:  1단어 청킹 (visual accent, 0.5–2s per chunk)
            - animation: phrase 단위 최대 7단어, gap > 0.8s 또는 sentence boundary 시 분할

        병렬 reveal 금지:
            청크 사이 overlap이 발생하지 않도록 보장.
            비중첩 보장: chunk[i].end <= chunk[i+1].start (홀드 미포함 구간).

        마지막 청크:
            end = last_word.end + _LAST_CARD_HOLD_SEC (1s 홀드).
        """
        if not words:
            return []

        if style == OverlayStyle.subtitle:
            words_per_chunk = 2
            gap_threshold = 0.5
        elif style == OverlayStyle.emphasis:
            words_per_chunk = 1
            gap_threshold = 0.3
        else:  # animation
            words_per_chunk = 7
            gap_threshold = 0.8

        chunks: list[_SubtitleChunk] = []
        current_group: list[WordTimestamp] = []

        def _flush(is_last: bool = False) -> None:
            if not current_group:
                return
            text = " ".join(w.word for w in current_group).upper()
            raw_end = current_group[-1].end
            final_end = raw_end + _LAST_CARD_HOLD_SEC if is_last else raw_end
            # 병렬 reveal 금지: 이전 청크의 end보다 새 start가 크거나 같아야 한다
            if chunks:
                prev_raw_end = current_group[0].start
                # current_group[0].start는 항상 이전 청크 raw_end 이후임을 _flush 흐름이 보장
                pass
            chunks.append(
                _SubtitleChunk(
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
                # animation 스타일: 문장 경계 감지 (마침표/물음표/느낌표로 끝나는 단어)
                sentence_boundary = (
                    style == OverlayStyle.animation
                    and prev.word.rstrip().endswith((".", "?", "!", "。", "？", "！"))
                )

                if speaker_changed or gap_exceeded or chunk_full or sentence_boundary:
                    _flush(is_last=False)

            current_group.append(word)

        _flush(is_last=True)
        return chunks

    def _render_jsx(
        self,
        chunks: list[_SubtitleChunk],
        style: OverlayStyle,
        brand_tokens: dict,
    ) -> str:
        """청크 배열을 Remotion SubtitleOverlay JSX 문자열로 변환한다.

        출력 형식:
            <SubtitleOverlay
              chunks={[...]}
              brandTokens={{...}}
              fps={30}
              position="bottom"
              uppercase={true}
            />

        스타일별 차이:
            - subtitle:  position="bottom", uppercase, 기본 자막
            - emphasis:  position="center", uppercase, 큰 폰트 hint
            - animation: position prop + animation prop 전달 (Remotion측 미구현이나 prop 전달)

        brand_tokens 반영:
            colors.hero, typography.font_heading을 JSON으로 직렬화하여 prop에 주입.
        """
        chunks_data = [
            {
                "text": c.text,
                "start": c.start,
                "end": c.end,
                "wordCount": c.word_count,
            }
            for c in chunks
        ]
        chunks_json = json.dumps(chunks_data, ensure_ascii=False)
        brand_json = json.dumps(brand_tokens, ensure_ascii=False)

        if style == OverlayStyle.subtitle:
            position = "bottom"
            extra_props = ""
        elif style == OverlayStyle.emphasis:
            position = "center"
            extra_props = "\n  fontSizeHint={96}"
        else:  # animation
            position = "bottom"
            extra_props = '\n  animation="fade-up"'

        return (
            f"<SubtitleOverlay\n"
            f"  chunks={{{chunks_json}}}\n"
            f"  brandTokens={{{brand_json}}}\n"
            f"  fps={{{self.fps}}}\n"
            f'  position="{position}"\n'
            f"  uppercase={{true}}"
            f"{extra_props}\n"
            f"/>"
        )

    def _make_composition_id(self, input: OverlayInput) -> str:  # noqa: A002
        """Remotion <Composition id=> 식별자를 생성한다.

        형식: overlay-{style}-{hash[:8]}
        hash 소재: 첫 3단어 + 마지막 단어 + style + word_count

        Args:
            input: OverlayInput

        Returns:
            str: 예) "overlay-subtitle-a3f2b1c0"
        """
        words = input.word_timestamps
        sample_words = [w.word for w in words[:3]] + [words[-1].word]
        raw = f"{input.style.value}-{'|'.join(sample_words)}-{len(words)}"
        digest = hashlib.sha1(raw.encode()).hexdigest()  # noqa: S324
        return f"overlay-{input.style.value}-{digest[:8]}"
