"""STT 라우터 — Scribe 우선, Whisper fallback (ISS-164, Phase B Gate G3-c).

ElevenLabs Scribe API가 실패(타임아웃/401/429/5xx/빈 결과)하거나
비활성화 상태일 때 자동으로 OpenAI Whisper로 전환한다.
단일 벤더 의존 해소 + 가용성 보장.

사용:
    router = STTRouter()
    out = await router.transcribe(Path("narration.mp3"))
    print(out.backend_used, out.fallback_triggered)
    # TranscriptionResult는 out.result에서 접근
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from app.services.scribe_stt_adapter import (
    ScribeSTTAdapter,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 공개 타입
# ─────────────────────────────────────────────────────────────────────────────

class STTBackend(str, Enum):
    """사용된 STT 백엔드 식별자."""

    SCRIBE = "scribe"
    WHISPER = "whisper"


@runtime_checkable
class STTBackendProtocol(Protocol):
    """STT 백엔드 공통 인터페이스 (duck-typing 가드 용도).

    STTRouter에 주입되는 모든 어댑터는 이 메서드 시그니처를 충족해야 한다.
    """

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """오디오 파일을 TranscriptionResult로 변환."""
        ...


@dataclass
class STTRouterResult:
    """STT 라우터 반환값.

    Attributes:
        result:            TranscriptionResult — words, full_text, duration_sec 등
        backend_used:      실제 응답을 처리한 백엔드 (SCRIBE | WHISPER)
        fallback_triggered: True이면 primary 실패 후 fallback 경로를 사용했음
        primary_error:     primary 백엔드 실패 메시지 (fallback이 없으면 None)
    """

    result: TranscriptionResult
    backend_used: STTBackend
    fallback_triggered: bool
    primary_error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# STTRouter
# ─────────────────────────────────────────────────────────────────────────────

class STTRouter:
    """Scribe → Whisper 자동 fallback 라우터.

    prefer=STTBackend.SCRIBE (기본값)이면 Scribe를 먼저 시도하고
    실패 시 Whisper로 전환한다. prefer=STTBackend.WHISPER로 설정하면
    역순으로 동작한다.

    어댑터 lazy 초기화:
        scribe_adapter / whisper_adapter를 None으로 두면 실제 호출 직전에
        기본 구현체(ScribeSTTAdapter / WhisperAdapter)를 생성한다.
        테스트에서는 두 파라미터에 FakeAdapter를 주입하여 외부 API 없이 검증.

    예외 처리:
        primary 백엔드에서 발생하는 모든 예외(httpx 오류, ValueError,
        RuntimeError 포함)를 잡아 secondary로 전환한다.
        secondary까지 실패하면 예외를 그대로 전파한다.
    """

    def __init__(
        self,
        scribe_adapter: Optional[STTBackendProtocol] = None,
        whisper_adapter: Optional[STTBackendProtocol] = None,
        prefer: STTBackend = STTBackend.SCRIBE,
    ) -> None:
        self.prefer = prefer
        self._scribe = scribe_adapter
        self._whisper = whisper_adapter

    # ── 내부: lazy 초기화 ────────────────────────────────────────────────────

    def _ensure_scribe(self) -> STTBackendProtocol:
        if self._scribe is None:
            self._scribe = ScribeSTTAdapter()
        return self._scribe

    def _ensure_whisper(self) -> STTBackendProtocol:
        if self._whisper is None:
            from app.services.stt_service import STTService  # 지연 import (순환 방지)

            self._whisper = WhisperAdapter(STTService())
        return self._whisper

    # ── 공개 API ─────────────────────────────────────────────────────────────

    async def transcribe(self, audio_path: Path) -> STTRouterResult:
        """primary STT 시도 → 실패 시 secondary로 자동 전환.

        fallback 조건:
          - ValueError (API 키 미설정)
          - httpx.HTTPStatusError, httpx.TimeoutException
          - RuntimeError (빈 words 등 후처리 에러)
          - 기타 모든 Exception

        Args:
            audio_path: 처리할 오디오 파일 경로

        Returns:
            STTRouterResult (result, backend_used, fallback_triggered, primary_error)

        Raises:
            Exception: primary + secondary 모두 실패한 경우 secondary 예외 전파
        """
        audio_path = Path(audio_path)

        if self.prefer == STTBackend.SCRIBE:
            primary_tag = STTBackend.SCRIBE
            secondary_tag = STTBackend.WHISPER
            primary_get = self._ensure_scribe
            secondary_get = self._ensure_whisper
        else:
            primary_tag = STTBackend.WHISPER
            secondary_tag = STTBackend.SCRIBE
            primary_get = self._ensure_whisper
            secondary_get = self._ensure_scribe

        # ── Primary 시도 ──────────────────────────────────────────────────────
        primary_error: Optional[str] = None
        try:
            adapter = primary_get()
            result = await adapter.transcribe(audio_path)
            if not result.words:
                raise RuntimeError(
                    f"{primary_tag.value} 응답에 words 없음 (빈 결과). fallback 전환."
                )
            logger.debug(
                "[stt_router] %s 성공 (%d words)",
                primary_tag.value,
                len(result.words),
            )
            return STTRouterResult(
                result=result,
                backend_used=primary_tag,
                fallback_triggered=False,
            )
        except Exception as exc:
            primary_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "[stt_router] %s 실패 → %s fallback. 원인: %s",
                primary_tag.value,
                secondary_tag.value,
                primary_error,
            )

        # ── Secondary (fallback) ──────────────────────────────────────────────
        adapter = secondary_get()
        result = await adapter.transcribe(audio_path)
        logger.info(
            "[stt_router] fallback %s 성공 (%d words)",
            secondary_tag.value,
            len(result.words),
        )
        return STTRouterResult(
            result=result,
            backend_used=secondary_tag,
            fallback_triggered=True,
            primary_error=primary_error,
        )


# ─────────────────────────────────────────────────────────────────────────────
# WhisperAdapter — 기존 STTService → STTBackendProtocol 브릿지
# ─────────────────────────────────────────────────────────────────────────────

class WhisperAdapter:
    """OpenAI Whisper 어댑터 — 기존 STTService를 STTBackendProtocol에 맞게 래핑.

    현재 상태: 골격만 구현 (NotImplementedError).
    STTService.transcribe()는 str을 반환하므로 word-level TranscriptionResult
    변환이 추가로 필요하다. 후속 ISS에서 구현 예정.

    참고:
        stt_service.STTService.transcribe_with_timestamps() 를 활용하면
        segment-level 타임스탬프를 얻을 수 있다. 단어 단위 분해는 후속 작업.
    """

    def __init__(self, service: object) -> None:
        self.service = service

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Whisper STT → TranscriptionResult 변환.

        Raises:
            NotImplementedError: 후속 ISS에서 완성 예정.
                STTService.transcribe_with_timestamps() 결과를
                segment → WordTimestamp 배열로 변환하는 로직 필요.
        """
        raise NotImplementedError(
            "WhisperAdapter.transcribe — STTService 시그니처 확인 후 후속 ISS에서 구현. "
            "현재는 fallback path 골격만 검증 목적으로 존재."
        )
