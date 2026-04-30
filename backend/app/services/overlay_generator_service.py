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

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
                         ISS-152에서 실제 JSX를 채운다. 현재는 빈 문자열.
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

        Args:
            input: OverlayInput 계약 (word_timestamps, style, brand_tokens)

        Returns:
            OverlayOutput: remotion_jsx, composition_id, duration_frames, asset_paths

        Raises:
            NotImplementedError: ISS-152에서 구현 예정.
            ValueError: 입력 유효성 검증 실패 시.

        Notes:
            ISS-152 구현 시 다음 로직이 여기 들어간다:
            1. _validate_input() 호출
            2. word_timestamps를 청킹 (video-use timeline_view.py grouping 참고)
            3. OverlayStyle에 따라 Remotion Spring/interpolate 표현식 생성
            4. brand_tokens의 colors.hero, typography.font_heading 적용
            5. JSX 문자열 조립 → OverlayOutput 반환
        """
        self._validate_input(input)
        raise NotImplementedError(
            "ISS-152에서 구현 예정. "
            "현재는 스켈레톤 계약만 정의되어 있습니다."
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
