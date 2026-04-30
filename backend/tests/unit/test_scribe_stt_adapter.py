"""
ScribeSTTAdapter 단위 테스트 — ISS-150

실제 ElevenLabs API 호출 없음 (mock 전용).
모든 테스트는 ELEVENLABS_API_KEY 환경변수 없이 실행 가능.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.scribe_stt_adapter import (
    ScribeSTTAdapter,
    SubtitleChunk,
    TranscriptionResult,
)
from app.services.overlay_generator_service import WordTimestamp


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def adapter(monkeypatch: pytest.MonkeyPatch) -> ScribeSTTAdapter:
    """ELEVENLABS_API_KEY 환경변수를 주입하여 어댑터 초기화."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-fixture")
    return ScribeSTTAdapter()


@pytest.fixture
def sample_words() -> list[WordTimestamp]:
    """4개 단어, 2명 화자 샘플."""
    return [
        WordTimestamp(word="Hello",   start=0.0, end=0.4, speaker_id="spk_0"),
        WordTimestamp(word="World",   start=0.5, end=0.9, speaker_id="spk_0"),
        WordTimestamp(word="Nice",    start=1.0, end=1.4, speaker_id="spk_1"),
        WordTimestamp(word="to",      start=1.5, end=1.7, speaker_id="spk_1"),
    ]


@pytest.fixture
def mock_scribe_response() -> dict:
    """Scribe API mock 응답 딕셔너리."""
    return {
        "text": "Hello World",
        "words": [
            {"text": "Hello", "start": 0.0, "end": 0.4, "type": "word", "speaker_id": "spk_0", "confidence": 0.99},
            {"text": " ",     "start": 0.4, "end": 0.5, "type": "spacing"},
            {"text": "World", "start": 0.5, "end": 0.9, "type": "word", "speaker_id": "spk_0", "confidence": 0.95},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 초기화 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestInit:
    def test_init_without_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API 키 없으면 ValueError."""
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
            ScribeSTTAdapter()

    def test_init_with_env_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """환경변수로 초기화 성공."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "env-key-123")
        a = ScribeSTTAdapter()
        assert a.api_key == "env-key-123"

    def test_init_with_explicit_key(self) -> None:
        """명시적 api_key 파라미터 우선."""
        a = ScribeSTTAdapter(api_key="explicit-key")
        assert a.api_key == "explicit-key"

    def test_init_with_num_speakers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """num_speakers 파라미터 저장."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
        a = ScribeSTTAdapter(num_speakers=2)
        assert a.num_speakers == 2


# ─────────────────────────────────────────────────────────────────────────────
# _parse_response 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestParseResponse:
    def test_parse_response_normalizes(
        self, adapter: ScribeSTTAdapter, mock_scribe_response: dict
    ) -> None:
        """mock dict → WordTimestamp 배열 변환 — spacing 타입 제외."""
        words = adapter._parse_response(mock_scribe_response)
        assert len(words) == 2
        assert words[0].word == "Hello"
        assert words[1].word == "World"

    def test_parse_response_seconds(
        self, adapter: ScribeSTTAdapter, mock_scribe_response: dict
    ) -> None:
        """start/end가 초(float) 단위로 저장된다."""
        words = adapter._parse_response(mock_scribe_response)
        assert words[0].start == pytest.approx(0.0)
        assert words[0].end == pytest.approx(0.4)

    def test_parse_response_speaker_id(
        self, adapter: ScribeSTTAdapter, mock_scribe_response: dict
    ) -> None:
        """speaker_id가 올바르게 매핑된다."""
        words = adapter._parse_response(mock_scribe_response)
        assert words[0].speaker_id == "spk_0"

    def test_parse_response_confidence(
        self, adapter: ScribeSTTAdapter, mock_scribe_response: dict
    ) -> None:
        """confidence가 0.0–1.0 범위로 정규화된다."""
        words = adapter._parse_response(mock_scribe_response)
        assert words[0].confidence == pytest.approx(0.99)

    def test_parse_response_skips_spacing(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """type=spacing 항목은 WordTimestamp에 포함하지 않는다."""
        data = {
            "words": [
                {"text": "Hi",    "start": 0.0, "end": 0.3, "type": "word"},
                {"text": " ",     "start": 0.3, "end": 0.4, "type": "spacing"},
                {"text": "there", "start": 0.4, "end": 0.7, "type": "word"},
            ]
        }
        words = adapter._parse_response(data)
        assert len(words) == 2
        assert words[0].word == "Hi"
        assert words[1].word == "there"

    def test_parse_response_end_le_start_corrected(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """end <= start 인 경우 최소 간격 0.05s로 보정된다."""
        data = {
            "words": [
                {"text": "oops", "start": 1.0, "end": 0.5, "type": "word"},
            ]
        }
        words = adapter._parse_response(data)
        assert words[0].end > words[0].start

    def test_parse_response_empty_text_skipped(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """빈 text 항목은 건너뛴다."""
        data = {
            "words": [
                {"text": "",   "start": 0.0, "end": 0.1, "type": "word"},
                {"text": "OK", "start": 0.2, "end": 0.4, "type": "word"},
            ]
        }
        words = adapter._parse_response(data)
        assert len(words) == 1
        assert words[0].word == "OK"


# ─────────────────────────────────────────────────────────────────────────────
# chunk_subtitles 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestChunkSubtitles:
    def test_chunk_subtitles_2words(
        self, adapter: ScribeSTTAdapter, sample_words: list[WordTimestamp]
    ) -> None:
        """2단어씩 묶인다 (speaker_id 변경 전까지)."""
        chunks = adapter.chunk_subtitles(sample_words, words_per_chunk=2)
        # spk_0 두 단어 → 1청크, spk_1 두 단어 → 1청크 (speaker_break으로 분할)
        assert len(chunks) >= 2

    def test_chunk_subtitles_uppercase(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """uppercase=True 시 텍스트가 대문자로 변환된다."""
        words = [
            WordTimestamp(word="hello", start=0.0, end=0.4),
            WordTimestamp(word="world", start=0.5, end=0.9),
        ]
        chunks = adapter.chunk_subtitles(words, uppercase=True)
        assert chunks[0].text == "HELLO WORLD"

    def test_chunk_subtitles_no_uppercase(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """uppercase=False 시 원본 대소문자 유지."""
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.4),
        ]
        chunks = adapter.chunk_subtitles(words, uppercase=False)
        assert chunks[0].text == "Hello"

    def test_chunk_subtitles_speaker_break(
        self, adapter: ScribeSTTAdapter, sample_words: list[WordTimestamp]
    ) -> None:
        """speaker_id 변경 시 청크가 강제 분할된다."""
        # sample_words: spk_0(Hello, World) / spk_1(Nice, to)
        chunks = adapter.chunk_subtitles(sample_words, words_per_chunk=4)  # 단어 수 여유
        texts = [c.text for c in chunks]
        # spk_0 묶음과 spk_1 묶음이 분리되어야 한다
        assert any("HELLO" in t and "WORLD" in t for t in texts)
        assert any("NICE" in t and "TO" in t for t in texts)

    def test_chunk_subtitles_gap_break(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """단어 간 gap > gap_threshold 시 청크 분할."""
        words = [
            WordTimestamp(word="one",   start=0.0, end=0.3),
            WordTimestamp(word="two",   start=1.0, end=1.3),  # gap = 0.7s > 0.5
            WordTimestamp(word="three", start=1.4, end=1.7),
        ]
        chunks = adapter.chunk_subtitles(words, words_per_chunk=3, gap_threshold=0.5)
        # "one"은 단독 청크, "two three"는 다음 청크
        assert len(chunks) == 2
        assert "ONE" in chunks[0].text
        assert "TWO" in chunks[1].text

    def test_chunk_subtitles_last_hold(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """마지막 청크의 end에 hold_seconds(1.0s)가 추가된다."""
        words = [
            WordTimestamp(word="final", start=2.0, end=2.5),
        ]
        chunks = adapter.chunk_subtitles(words, hold_seconds=1.0)
        assert chunks[-1].end == pytest.approx(2.5 + 1.0)

    def test_chunk_subtitles_empty_words(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """빈 words 배열이면 빈 리스트 반환."""
        assert adapter.chunk_subtitles([]) == []

    def test_chunk_subtitles_word_count_field(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """SubtitleChunk.word_count가 실제 단어 수와 일치한다."""
        words = [
            WordTimestamp(word="a", start=0.0, end=0.2),
            WordTimestamp(word="b", start=0.3, end=0.5),
        ]
        chunks = adapter.chunk_subtitles(words, words_per_chunk=2)
        assert chunks[0].word_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# transcribe (mock httpx) 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestTranscribe:
    @pytest.mark.anyio
    async def test_transcribe_returns_result(
        self,
        adapter: ScribeSTTAdapter,
        mock_scribe_response: dict,
        tmp_path: Path,
    ) -> None:
        """mock httpx로 transcribe() 전체 흐름 검증."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake-audio-data")

        mock_response = MagicMock()
        mock_response.json.return_value = mock_scribe_response
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.scribe_stt_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await adapter.transcribe(audio_file)

        assert isinstance(result, TranscriptionResult)
        assert len(result.words) == 2
        assert result.full_text == "Hello World"
        assert result.speaker_count == 1  # 모두 spk_0
        assert result.duration_sec == pytest.approx(0.9)

    @pytest.mark.anyio
    async def test_transcribe_file_not_found(
        self, adapter: ScribeSTTAdapter
    ) -> None:
        """존재하지 않는 파일이면 FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await adapter.transcribe(Path("/nonexistent/audio.mp3"))
