"""
Phase A 통합 테스트 — ISS-153

검증 항목:
    - DirectorAgent.generate_overlay_from_stt 메서드 존재
    - mock WordTimestamp 5개 → OverlayOutput 정상 반환
    - 빈 입력 → ValueError
    - subtitle 스타일 정상 동작
    - _normalize_to_word_timestamps(scribe) 정상 동작
    - E2E smoke: STT mock → overlay_generator → JSX 비어있지 않음 + composition_id 검증

외부 API 호출: 모두 mock (ELEVENLABS_API_KEY, OPENAI_API_KEY 의존 없음)
"""
import pytest
from unittest.mock import MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# 공통 fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_word_timestamps():
    """5개 WordTimestamp 샘플."""
    from app.services.overlay_generator_service import WordTimestamp
    return [
        WordTimestamp(word="안녕하세요", start=0.0, end=0.5),
        WordTimestamp(word="저는", start=0.6, end=0.9),
        WordTimestamp(word="OmniVibe", start=1.0, end=1.5),
        WordTimestamp(word="입니다", start=1.6, end=2.0),
        WordTimestamp(word="감사합니다", start=2.2, end=2.8),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# test_director_overlay_method_exists
# ─────────────────────────────────────────────────────────────────────────────

def test_director_overlay_method_exists():
    """DirectorAgent에 generate_overlay_from_stt 메서드가 존재해야 한다."""
    from app.agents.director_agent import DirectorAgent
    assert hasattr(DirectorAgent, "generate_overlay_from_stt"), (
        "DirectorAgent에 generate_overlay_from_stt 메서드가 없습니다"
    )
    assert callable(getattr(DirectorAgent, "generate_overlay_from_stt")), (
        "generate_overlay_from_stt가 callable이 아닙니다"
    )


# ─────────────────────────────────────────────────────────────────────────────
# test_director_overlay_with_5_words
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_director_overlay_with_5_words(sample_word_timestamps):
    """mock WordTimestamp 5개 → OverlayOutput 정상 반환."""
    from app.agents.director_agent import DirectorAgent
    from app.services.overlay_generator_service import OverlayOutput

    agent = DirectorAgent()
    output = await agent.generate_overlay_from_stt(sample_word_timestamps)

    assert isinstance(output, OverlayOutput), (
        f"반환 타입 오류: {type(output)}"
    )
    assert output.remotion_jsx.strip(), "remotion_jsx가 비어 있습니다"
    assert output.duration_frames > 0, (
        f"duration_frames가 0 이하: {output.duration_frames}"
    )
    assert output.composition_id.startswith("overlay-"), (
        f"composition_id 형식 오류: {output.composition_id}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# test_director_overlay_empty_raises
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_director_overlay_empty_raises():
    """빈 word_timestamps → ValueError를 발생시켜야 한다."""
    from app.agents.director_agent import DirectorAgent

    agent = DirectorAgent()
    with pytest.raises(ValueError, match="word_timestamps"):
        await agent.generate_overlay_from_stt([])


# ─────────────────────────────────────────────────────────────────────────────
# test_director_overlay_style_subtitle
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_director_overlay_style_subtitle(sample_word_timestamps):
    """subtitle 스타일로 명시적 호출 시 position='bottom' JSX 포함."""
    from app.agents.director_agent import DirectorAgent
    from app.services.overlay_generator_service import OverlayStyle

    agent = DirectorAgent()
    output = await agent.generate_overlay_from_stt(
        sample_word_timestamps,
        style=OverlayStyle.subtitle,
        brand_tokens={"colors": {"hero": "#00A1E0"}},
    )

    assert 'position="bottom"' in output.remotion_jsx, (
        f"subtitle 스타일에 position=\"bottom\"이 없습니다:\n{output.remotion_jsx}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# test_audio_correction_loop_normalize_scribe
# ─────────────────────────────────────────────────────────────────────────────

def test_audio_correction_loop_normalize_scribe(sample_word_timestamps):
    """_normalize_to_word_timestamps(scribe): TranscriptionResult mock → WordTimestamp 배열."""
    from app.services.audio_correction_loop import _normalize_to_word_timestamps
    from app.services.overlay_generator_service import WordTimestamp

    # ScribeSTTAdapter.transcribe() 반환값을 mock으로 흉내
    mock_result = MagicMock()
    mock_result.words = sample_word_timestamps

    result = _normalize_to_word_timestamps(mock_result, source="scribe")

    assert isinstance(result, list), f"결과가 list가 아닙니다: {type(result)}"
    assert len(result) == 5, f"단어 수 불일치: {len(result)}"
    assert all(isinstance(w, WordTimestamp) for w in result), (
        "결과 원소가 WordTimestamp가 아닌 것이 있습니다"
    )


def test_audio_correction_loop_normalize_whisper_raises():
    """_normalize_to_word_timestamps(whisper): NotImplementedError 발생."""
    from app.services.audio_correction_loop import _normalize_to_word_timestamps

    mock_result = MagicMock()
    with pytest.raises(NotImplementedError):
        _normalize_to_word_timestamps(mock_result, source="whisper")


def test_audio_correction_loop_normalize_invalid_source_raises():
    """_normalize_to_word_timestamps(invalid): ValueError 발생."""
    from app.services.audio_correction_loop import _normalize_to_word_timestamps

    mock_result = MagicMock()
    with pytest.raises(ValueError, match="지원하지 않는 source"):
        _normalize_to_word_timestamps(mock_result, source="unknown")


def test_audio_correction_loop_normalize_missing_words_raises():
    """_normalize_to_word_timestamps(scribe): words 속성 없으면 ValueError."""
    from app.services.audio_correction_loop import _normalize_to_word_timestamps

    mock_result = MagicMock(spec=[])  # words 속성 없음
    with pytest.raises(ValueError, match="stt_result.words가 없습니다"):
        _normalize_to_word_timestamps(mock_result, source="scribe")


# ─────────────────────────────────────────────────────────────────────────────
# test_phase_a_e2e_pipeline_smoke
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phase_a_e2e_pipeline_smoke():
    """Phase A E2E smoke: STT mock → overlay_generator → JSX 비어있지 않음.

    외부 API 호출 없이 파이프라인 흐름을 검증한다.
    """
    from app.services.overlay_generator_service import WordTimestamp
    from app.services.audio_correction_loop import _normalize_to_word_timestamps
    from app.agents.director_agent import DirectorAgent

    # 1. Scribe STT 결과 mock (30초 샘플 오디오 시뮬레이션)
    mock_words = [
        WordTimestamp(word="OmniVibe", start=0.0, end=0.7),
        WordTimestamp(word="Pro는", start=0.8, end=1.2),
        WordTimestamp(word="AI", start=1.3, end=1.5),
        WordTimestamp(word="기반", start=1.6, end=2.0),
        WordTimestamp(word="영상", start=2.1, end=2.5),
        WordTimestamp(word="자동화", start=2.6, end=3.2),
        WordTimestamp(word="플랫폼입니다", start=3.3, end=4.0),
    ]

    mock_transcription = MagicMock()
    mock_transcription.words = mock_words

    # 2. STT 결과 정규화 (scribe 어댑터)
    word_timestamps = _normalize_to_word_timestamps(mock_transcription, source="scribe")
    assert len(word_timestamps) == 7, f"정규화 단어 수 오류: {len(word_timestamps)}"

    # 3. Director Agent overlay 생성
    agent = DirectorAgent()
    output = await agent.generate_overlay_from_stt(
        word_timestamps,
        brand_tokens={"colors": {"hero": "#22D3EE"}, "typography": {"font_heading": "Pretendard"}},
        narration_duration_sec=4.0,
    )

    # 4. 결과 검증
    assert output.remotion_jsx.strip(), "remotion_jsx가 비어 있습니다"
    assert "<SubtitleOverlay" in output.remotion_jsx, (
        "SubtitleOverlay 컴포넌트가 JSX에 없습니다"
    )

    # composition_id 형식: overlay-{style}-{hash[:8]}
    parts = output.composition_id.split("-")
    assert len(parts) == 3, (
        f"composition_id 형식 오류 (overlay-style-hash 기대): {output.composition_id}"
    )
    assert parts[0] == "overlay", f"composition_id prefix 오류: {output.composition_id}"
    assert len(parts[2]) == 8, (
        f"composition_id hash 길이 오류 (8자리 기대): {output.composition_id}"
    )

    # duration_frames > 0 + fps == 30 (ffmpeg_profile SoT)
    assert output.duration_frames > 0
    assert output.fps == 30, (
        f"fps가 30이 아닙니다 (ffmpeg_profile SoT 위반): {output.fps}"
    )

    print(f"\n[Phase A E2E Smoke] PASS")
    print(f"  composition_id : {output.composition_id}")
    print(f"  duration_frames: {output.duration_frames}")
    print(f"  fps            : {output.fps}")
    print(f"  jsx_lines      : {len(output.remotion_jsx.splitlines())}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase A 체크리스트 검증
# ─────────────────────────────────────────────────────────────────────────────

def test_phase_a_checklist_ffmpeg_sot():
    """Phase A 체크리스트: ffmpeg_profile.py가 직접 ffmpeg 호출 0건."""
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "subprocess.run.*ffmpeg", "app/"],
        capture_output=True, text=True,
        cwd="/Volumes/E_SSD/02_GitHub.nosync/0030_OmniVibePro/backend"
    )
    # overlay_generator 파일에서 직접 ffmpeg 호출 없어야 함
    hits = [
        line for line in result.stdout.splitlines()
        if "overlay_generator" in line
    ]
    assert len(hits) == 0, (
        f"overlay_generator_service.py에서 ffmpeg 직접 호출 감지:\n"
        + "\n".join(hits)
    )


def test_phase_a_checklist_ios_fps():
    """Phase A 체크리스트: OverlayGeneratorService의 기본 fps == 30 (iOS SoT)."""
    from app.services.overlay_generator_service import OverlayGeneratorService
    service = OverlayGeneratorService()
    assert service.fps == 30, (
        f"OverlayGeneratorService 기본 fps가 30이 아닙니다: {service.fps}"
    )


def test_phase_a_checklist_last_hold():
    """Phase A 체크리스트: 마지막 청크 1s 홀드 적용 확인 (duration_frames)."""
    from app.services.overlay_generator_service import (
        OverlayGeneratorService,
        OverlayInput,
        OverlayStyle,
        WordTimestamp,
    )
    import math

    words = [
        WordTimestamp(word="테스트", start=0.0, end=1.0),
    ]
    service = OverlayGeneratorService(fps=30)
    output = service.generate(OverlayInput(
        word_timestamps=words,
        style=OverlayStyle.subtitle,
        brand_tokens={},
    ))
    # 마지막 word.end = 1.0
    # _flush(is_last=True): chunk.end = 1.0 + 1.0 = 2.0 (홀드 적용)
    # _calc_duration_frames(2.0): ceil((2.0 + 1.0) * 30) = 90
    expected_frames = math.ceil((1.0 + 1.0 + 1.0) * 30)
    assert output.duration_frames == expected_frames, (
        f"1s 홀드 적용 실패: expected={expected_frames}, actual={output.duration_frames}"
    )
