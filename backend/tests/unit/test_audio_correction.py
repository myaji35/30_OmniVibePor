"""
Unit 테스트: Audio Correction Loop (Zero-Fault)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.audio_correction_loop import AudioCorrectionLoop


class TestAudioCorrectionLoop:
    """AudioCorrectionLoop 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전에 AudioCorrectionLoop 인스턴스 생성"""
        self.loop = AudioCorrectionLoop(
            accuracy_threshold=0.95,
            max_attempts=3,
            enable_normalization=False,  # 테스트 시 정규화 비활성화
            enable_learning=False  # 테스트 시 학습 비활성화
        )

    def test_calculate_similarity_exact_match(self):
        """완전 일치"""
        text1 = "여러분, 오늘은 특별한 날입니다."
        text2 = "여러분, 오늘은 특별한 날입니다."
        similarity = self.loop.calculate_similarity(text1, text2)
        assert similarity >= 0.99

    def test_calculate_similarity_minor_difference(self):
        """미세한 차이"""
        text1 = "여러분, 오늘은 특별한 날입니다."
        text2 = "여러분 오늘은 특별한 날입니다"  # 쉼표 누락
        similarity = self.loop.calculate_similarity(text1, text2)
        assert similarity >= 0.90

    def test_calculate_similarity_major_difference(self):
        """큰 차이"""
        text1 = "여러분, 오늘은 특별한 날입니다."
        text2 = "안녕하세요, 좋은 하루 되세요."
        similarity = self.loop.calculate_similarity(text1, text2)
        assert similarity < 0.50




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
