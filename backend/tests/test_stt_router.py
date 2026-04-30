"""STT 라우터 단위 테스트 — ISS-164, Phase B Gate G3-c.

실제 API 호출 없음 (FakeAdapter 주입).
asyncio_mode=auto (pytest.ini 설정) — @pytest.mark.anyio 불필요.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.stt_router import (
    STTBackend,
    STTRouter,
    STTRouterResult,
    WhisperAdapter,
)
from app.services.scribe_stt_adapter import TranscriptionResult
from app.services.overlay_generator_service import WordTimestamp

# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼 / FakeAdapter
# ─────────────────────────────────────────────────────────────────────────────

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "scribe_response_sample.json"


def _make_result(word_count: int = 4) -> TranscriptionResult:
    """테스트용 TranscriptionResult 생성."""
    words = [
        WordTimestamp(
            word=f"word{i}",
            start=float(i),
            end=float(i) + 0.5,
            speaker_id="speaker_0",
        )
        for i in range(word_count)
    ]
    return TranscriptionResult(
        words=words,
        full_text=" ".join(w.word for w in words),
        duration_sec=float(word_count),
        speaker_count=1,
        raw_response=None,
    )


class FakeAdapter:
    """외부 API 없이 동작하는 테스트용 어댑터."""

    def __init__(
        self,
        result: TranscriptionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.called = False
        self.last_path: Path | None = None

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        self.called = True
        self.last_path = audio_path
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


@pytest.fixture
def fake_audio(tmp_path: Path) -> Path:
    """더미 오디오 파일 (내용 무관, 경로 존재만 필요)."""
    p = tmp_path / "test_audio.wav"
    p.write_bytes(b"FAKE_AUDIO")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# STTRouter 핵심 시나리오
# ─────────────────────────────────────────────────────────────────────────────

class TestSTTRouterScribeSuccess:
    """Scribe 성공 경로."""

    async def test_returns_scribe_result(self, fake_audio: Path) -> None:
        """Scribe 성공 시 SCRIBE 백엔드로 결과 반환."""
        scribe = FakeAdapter(result=_make_result(4))
        whisper = FakeAdapter()
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        out = await router.transcribe(fake_audio)

        assert isinstance(out, STTRouterResult)
        assert out.backend_used == STTBackend.SCRIBE
        assert out.fallback_triggered is False
        assert out.primary_error is None
        assert len(out.result.words) == 4

    async def test_scribe_called_whisper_not_called(self, fake_audio: Path) -> None:
        """Scribe 성공 시 Whisper는 호출되지 않아야 한다."""
        scribe = FakeAdapter(result=_make_result())
        whisper = FakeAdapter()
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        await router.transcribe(fake_audio)

        assert scribe.called is True
        assert whisper.called is False

    async def test_audio_path_passed_to_adapter(self, fake_audio: Path) -> None:
        """어댑터에 정확한 경로가 전달되어야 한다."""
        scribe = FakeAdapter(result=_make_result())
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=FakeAdapter())

        await router.transcribe(fake_audio)

        assert scribe.last_path == fake_audio


class TestSTTRouterFallback:
    """Scribe 실패 → Whisper fallback 경로."""

    async def test_scribe_error_falls_back_to_whisper(self, fake_audio: Path) -> None:
        """Scribe RuntimeError → Whisper fallback 동작."""
        scribe = FakeAdapter(error=RuntimeError("Scribe 5xx"))
        whisper = FakeAdapter(result=_make_result(3))
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        out = await router.transcribe(fake_audio)

        assert out.backend_used == STTBackend.WHISPER
        assert out.fallback_triggered is True
        assert "RuntimeError" in (out.primary_error or "")
        assert scribe.called is True
        assert whisper.called is True

    async def test_scribe_empty_words_falls_back(self, fake_audio: Path) -> None:
        """Scribe가 빈 words 반환 시 fallback 전환 (RuntimeError로 처리)."""
        scribe = FakeAdapter(result=_make_result(word_count=0))
        whisper = FakeAdapter(result=_make_result(2))
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        out = await router.transcribe(fake_audio)

        assert out.backend_used == STTBackend.WHISPER
        assert out.fallback_triggered is True
        assert out.primary_error is not None

    async def test_value_error_falls_back(self, fake_audio: Path) -> None:
        """API 키 없음(ValueError) 발생 시에도 fallback 전환."""
        scribe = FakeAdapter(error=ValueError("ELEVENLABS_API_KEY 미설정"))
        whisper = FakeAdapter(result=_make_result())
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        out = await router.transcribe(fake_audio)

        assert out.backend_used == STTBackend.WHISPER
        assert out.fallback_triggered is True

    async def test_fallback_result_has_words(self, fake_audio: Path) -> None:
        """fallback 결과도 정상 TranscriptionResult여야 한다."""
        scribe = FakeAdapter(error=RuntimeError("timeout"))
        whisper = FakeAdapter(result=_make_result(5))
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        out = await router.transcribe(fake_audio)

        assert len(out.result.words) == 5
        assert out.result.full_text != ""


class TestSTTRouterPreferWhisper:
    """prefer=WHISPER 모드."""

    async def test_prefer_whisper_skips_scribe(self, fake_audio: Path) -> None:
        """prefer=WHISPER 시 Whisper 먼저 호출, Scribe는 호출되지 않음."""
        scribe = FakeAdapter()
        whisper = FakeAdapter(result=_make_result())
        router = STTRouter(
            scribe_adapter=scribe,
            whisper_adapter=whisper,
            prefer=STTBackend.WHISPER,
        )

        out = await router.transcribe(fake_audio)

        assert out.backend_used == STTBackend.WHISPER
        assert out.fallback_triggered is False
        assert whisper.called is True
        assert scribe.called is False

    async def test_prefer_whisper_falls_back_to_scribe(self, fake_audio: Path) -> None:
        """prefer=WHISPER에서 Whisper 실패 시 Scribe로 fallback."""
        scribe = FakeAdapter(result=_make_result())
        whisper = FakeAdapter(error=RuntimeError("Whisper down"))
        router = STTRouter(
            scribe_adapter=scribe,
            whisper_adapter=whisper,
            prefer=STTBackend.WHISPER,
        )

        out = await router.transcribe(fake_audio)

        assert out.backend_used == STTBackend.SCRIBE
        assert out.fallback_triggered is True


class TestSTTRouterBothFail:
    """Primary + Secondary 모두 실패."""

    async def test_both_fail_propagates_secondary_error(self, fake_audio: Path) -> None:
        """primary + secondary 모두 실패 시 secondary 예외 전파."""
        scribe = FakeAdapter(error=RuntimeError("scribe down"))
        whisper = FakeAdapter(error=RuntimeError("whisper also down"))
        router = STTRouter(scribe_adapter=scribe, whisper_adapter=whisper)

        with pytest.raises(RuntimeError, match="whisper also down"):
            await router.transcribe(fake_audio)


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처 형식 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestScribeFixture:
    """scribe_response_sample.json 형식이 Scribe API 응답 스키마와 일치하는지 검증."""

    def test_fixture_file_exists(self) -> None:
        """픽스처 파일이 존재해야 한다."""
        assert FIXTURE_PATH.exists(), f"픽스처 파일 없음: {FIXTURE_PATH}"

    def test_fixture_has_required_top_level_keys(self) -> None:
        """최상위 필수 키 존재 여부."""
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        assert "words" in data, "words 키 없음"
        assert "language_code" in data, "language_code 키 없음"
        assert "text" in data, "text 키 없음"

    def test_fixture_has_word_type_entries(self) -> None:
        """words 배열에 type == 'word' 항목이 최소 1개 이상이어야 한다."""
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        word_entries = [w for w in data["words"] if w.get("type") == "word"]
        assert len(word_entries) >= 1, "type='word' 항목이 없음"

    def test_fixture_word_fields(self) -> None:
        """word 타입 항목은 text/start/end/speaker_id를 가져야 한다."""
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for item in data["words"]:
            if item.get("type") != "word":
                continue
            assert "text" in item, f"text 없음: {item}"
            assert "start" in item, f"start 없음: {item}"
            assert "end" in item, f"end 없음: {item}"
            assert item["end"] >= item["start"], "end < start 오류"

    def test_fixture_source_metadata(self) -> None:
        """_source 메타 필드가 curated 또는 live_api임을 명시해야 한다."""
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        source = data.get("_source", "")
        assert source in ("manually_curated_per_docs", "live_api"), (
            f"_source 값이 유효하지 않음: {source!r}"
        )

    def test_fixture_parseable_by_scribe_adapter(self) -> None:
        """픽스처가 ScribeSTTAdapter._parse_response()로 파싱 가능해야 한다."""
        from app.services.scribe_stt_adapter import ScribeSTTAdapter

        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        adapter = ScribeSTTAdapter(api_key="test-key")
        words = adapter._parse_response(data)

        assert isinstance(words, list), "파싱 결과가 리스트가 아님"
        assert len(words) >= 1, "파싱된 단어가 없음"
        for w in words:
            from app.services.overlay_generator_service import WordTimestamp
            assert isinstance(w, WordTimestamp)


# ─────────────────────────────────────────────────────────────────────────────
# WhisperAdapter 골격 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestWhisperAdapterSkeleton:
    """WhisperAdapter가 NotImplementedError를 올바르게 발생시키는지 확인."""

    async def test_whisper_adapter_not_implemented(self, fake_audio: Path) -> None:
        """WhisperAdapter.transcribe()는 현재 NotImplementedError 발생 (후속 ISS 예정)."""
        adapter = WhisperAdapter(service=object())

        with pytest.raises(NotImplementedError):
            await adapter.transcribe(fake_audio)
