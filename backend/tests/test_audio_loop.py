"""Zero-Fault Audio Loop 테스트"""
import pytest
from app.services.audio_correction_loop import AudioCorrectionLoop


class TestAudioCorrectionLoop:
    """Audio Correction Loop 테스트"""

    def test_calculate_similarity_identical(self):
        """동일한 텍스트의 유사도는 1.0"""
        loop = AudioCorrectionLoop()

        text = "안녕하세요, 오늘은 AI 트렌드에 대해 알아보겠습니다."
        similarity = loop.calculate_similarity(text, text)

        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """완전히 다른 텍스트의 유사도는 낮음"""
        loop = AudioCorrectionLoop()

        original = "안녕하세요"
        transcribed = "반갑습니다"
        similarity = loop.calculate_similarity(original, transcribed)

        assert similarity < 0.5

    def test_calculate_similarity_case_insensitive(self):
        """대소문자 무시"""
        loop = AudioCorrectionLoop()

        original = "Hello World"
        transcribed = "hello world"
        similarity = loop.calculate_similarity(original, transcribed)

        assert similarity == 1.0

    def test_calculate_similarity_punctuation_ignored(self):
        """구두점 무시"""
        loop = AudioCorrectionLoop()

        original = "Hello, World!"
        transcribed = "Hello World"
        similarity = loop.calculate_similarity(original, transcribed)

        assert similarity == 1.0

    def test_analyze_mismatch(self):
        """불일치 분석"""
        loop = AudioCorrectionLoop()

        original = "안녕하세요 여러분"
        transcribed = "안녕하세요 친구들"
        analysis = loop.analyze_mismatch(original, transcribed)

        assert analysis["mismatched_words"][0]["expected"] == "여러분"
        assert analysis["mismatched_words"][0]["actual"] == "친구들"
        assert analysis["length_difference"] == 0


@pytest.mark.asyncio
async def test_generate_verified_audio_mock():
    """
    오디오 생성 테스트 (실제 API 호출 없이 모킹)

    실제 ElevenLabs + Whisper API를 사용하려면:
    1. .env 파일에 API 키 설정
    2. @pytest.mark.skip 제거
    3. pytest tests/test_audio_loop.py::test_generate_verified_audio_real 실행
    """
    # TODO: Mock 구현
    # 실제 테스트는 API 키 설정 후 실행
    pass


# 실제 API 테스트 (수동 실행)
@pytest.mark.skip(reason="Requires API keys")
@pytest.mark.asyncio
async def test_generate_verified_audio_real():
    """실제 API 테스트 (ElevenLabs + Whisper)"""
    from app.services.audio_correction_loop import get_audio_correction_loop

    loop = get_audio_correction_loop()

    result = await loop.generate_verified_audio(
        text="안녕하세요, 테스트입니다.",
        language="ko",
        save_file=True
    )

    assert result["status"] in ["success", "partial_success"]
    assert result["final_similarity"] > 0.8
    assert result["audio_path"] is not None
