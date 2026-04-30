"""
overlay_generator_service.py 기본 import 및 계약 테스트

ISS-149 (USER_STORY P0) — Acceptance Criteria #7

검증 항목:
    - 모듈 import 가능
    - OverlayInput / OverlayOutput dataclass 생성
    - generate() 호출 시 NotImplementedError
    - 빈 word_timestamps 거부 (_validate_input)
"""
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# test_import — AC #7: 모듈 import 테스트
# ─────────────────────────────────────────────────────────────────────────────

def test_import():
    """overlay_generator_service 모듈의 모든 공개 심볼이 import 가능해야 한다."""
    from app.services.overlay_generator_service import (  # noqa: F401
        OverlayGeneratorService,
        OverlayInput,
        OverlayOutput,
        OverlayStyle,
        WordTimestamp,
    )


# ─────────────────────────────────────────────────────────────────────────────
# test_dataclass_construction — AC #2: dataclass 생성 가능
# ─────────────────────────────────────────────────────────────────────────────

def test_word_timestamp_construction():
    """WordTimestamp dataclass가 유효한 인수로 생성 가능해야 한다."""
    from app.services.overlay_generator_service import WordTimestamp

    wt = WordTimestamp(word="안녕", start=0.0, end=0.5)
    assert wt.word == "안녕"
    assert wt.start == 0.0
    assert wt.end == 0.5
    assert wt.speaker_id is None
    assert wt.confidence is None


def test_word_timestamp_with_optional_fields():
    """WordTimestamp의 선택 필드(speaker_id, confidence)가 정상 설정되어야 한다."""
    from app.services.overlay_generator_service import WordTimestamp

    wt = WordTimestamp(
        word="hello",
        start=1.0,
        end=1.4,
        speaker_id="speaker_0",
        confidence=0.98,
    )
    assert wt.speaker_id == "speaker_0"
    assert wt.confidence == 0.98


def test_word_timestamp_invalid_end_before_start():
    """end <= start이면 ValueError가 발생해야 한다."""
    from app.services.overlay_generator_service import WordTimestamp

    with pytest.raises(ValueError, match="end"):
        WordTimestamp(word="test", start=1.0, end=0.5)


def test_overlay_input_construction():
    """OverlayInput dataclass가 유효한 인수로 생성 가능해야 한다."""
    from app.services.overlay_generator_service import (
        OverlayInput,
        OverlayStyle,
        WordTimestamp,
    )

    timestamps = [
        WordTimestamp(word="오늘은", start=0.0, end=0.5),
        WordTimestamp(word="좋은", start=0.5, end=0.9),
        WordTimestamp(word="날씨입니다", start=0.9, end=1.5),
    ]
    inp = OverlayInput(
        word_timestamps=timestamps,
        style=OverlayStyle.subtitle,
        brand_tokens={"colors": {"hero": "#22D3EE"}},
    )
    assert len(inp.word_timestamps) == 3
    assert inp.style == OverlayStyle.subtitle
    assert inp.narration_duration_sec == 0.0  # 기본값


def test_overlay_input_style_from_string():
    """style을 문자열로 넘겨도 OverlayStyle Enum으로 자동 변환되어야 한다."""
    from app.services.overlay_generator_service import (
        OverlayInput,
        OverlayStyle,
        WordTimestamp,
    )

    timestamps = [WordTimestamp(word="test", start=0.0, end=0.3)]
    inp = OverlayInput(
        word_timestamps=timestamps,
        style="emphasis",  # type: ignore[arg-type]  # 문자열 전달
        brand_tokens={},
    )
    assert inp.style == OverlayStyle.emphasis


def test_overlay_output_construction():
    """OverlayOutput dataclass가 유효한 인수로 생성 가능해야 한다."""
    from app.services.overlay_generator_service import OverlayOutput

    out = OverlayOutput(
        remotion_jsx="<SubtitleOverlay />",
        composition_id="SubtitleOverlay",
        duration_frames=330,
    )
    assert out.fps == 30  # 기본값
    assert out.asset_paths == []  # 기본 빈 목록
    assert out.duration_frames == 330


# ─────────────────────────────────────────────────────────────────────────────
# test_generate_raises_not_implemented — AC #5: 스켈레톤 NotImplementedError
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_raises_not_implemented():
    """generate() 호출 시 NotImplementedError가 발생해야 한다 (ISS-152 구현 전)."""
    from app.services.overlay_generator_service import (
        OverlayGeneratorService,
        OverlayInput,
        OverlayStyle,
        WordTimestamp,
    )

    service = OverlayGeneratorService()
    timestamps = [WordTimestamp(word="테스트", start=0.0, end=0.5)]
    inp = OverlayInput(
        word_timestamps=timestamps,
        style=OverlayStyle.subtitle,
        brand_tokens={"colors": {"hero": "#22D3EE"}},
    )

    with pytest.raises(NotImplementedError, match="ISS-152"):
        service.generate(inp)


# ─────────────────────────────────────────────────────────────────────────────
# test_validate_input_rejects_empty — AC #5: 빈 word_timestamps 거부
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_input_rejects_empty_word_timestamps():
    """word_timestamps가 빈 리스트이면 ValueError가 발생해야 한다."""
    from app.services.overlay_generator_service import (
        OverlayGeneratorService,
        OverlayInput,
        OverlayStyle,
    )

    service = OverlayGeneratorService()
    inp = OverlayInput(
        word_timestamps=[],
        style=OverlayStyle.subtitle,
        brand_tokens={},
    )

    with pytest.raises(ValueError, match="word_timestamps"):
        service._validate_input(inp)


# ─────────────────────────────────────────────────────────────────────────────
# test_calc_duration_frames — 마지막 1s 홀드 포함 프레임 계산
# ─────────────────────────────────────────────────────────────────────────────

def test_calc_duration_frames_basic():
    """마지막 1s 홀드 포함 프레임 수가 올바르게 계산되어야 한다."""
    from app.services.overlay_generator_service import OverlayGeneratorService

    service = OverlayGeneratorService(fps=30)
    # (10.0 + 1.0) * 30 = 330
    assert service._calc_duration_frames(10.0) == 330


def test_calc_duration_frames_fractional():
    """소수점 초를 올림 처리해야 한다."""
    from app.services.overlay_generator_service import OverlayGeneratorService

    service = OverlayGeneratorService(fps=30)
    # (5.1 + 1.0) * 30 = 183.0 → ceil = 183
    assert service._calc_duration_frames(5.1) == 183


def test_calc_duration_frames_custom_fps():
    """fps를 변경해도 올바른 프레임 수가 계산되어야 한다."""
    from app.services.overlay_generator_service import OverlayGeneratorService

    service = OverlayGeneratorService(fps=24)
    # (4.0 + 1.0) * 24 = 120
    assert service._calc_duration_frames(4.0) == 120


# ─────────────────────────────────────────────────────────────────────────────
# test_overlay_style_enum — OverlayStyle Enum 값 검증
# ─────────────────────────────────────────────────────────────────────────────

def test_overlay_style_enum_values():
    """OverlayStyle Enum이 3가지 값을 가져야 한다."""
    from app.services.overlay_generator_service import OverlayStyle

    assert OverlayStyle.subtitle.value == "subtitle"
    assert OverlayStyle.emphasis.value == "emphasis"
    assert OverlayStyle.animation.value == "animation"


# ─────────────────────────────────────────────────────────────────────────────
# test_service_invalid_fps — fps 검증
# ─────────────────────────────────────────────────────────────────────────────

def test_service_rejects_zero_fps():
    """fps=0이면 ValueError가 발생해야 한다."""
    from app.services.overlay_generator_service import OverlayGeneratorService

    with pytest.raises(ValueError, match="fps"):
        OverlayGeneratorService(fps=0)
