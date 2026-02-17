"""
Unit 테스트: Writer Agent (Text Helpers)
"""
import pytest
from app.utils.text_helpers import (
    normalize_script,
    calculate_duration,
    extract_keywords,
    split_into_blocks
)


class TestScriptNormalization:
    """스크립트 정규화 테스트"""

    def test_remove_markdown_headers(self):
        """Markdown 헤더 제거"""
        input_text = "### 훅\n여러분, 오늘은..."
        expected = "여러분, 오늘은..."
        assert normalize_script(input_text) == expected

    def test_remove_brackets(self):
        """괄호 주석 제거"""
        input_text = "여러분 [강조], 오늘은..."
        expected = "여러분 , 오늘은..."
        assert normalize_script(input_text) == expected

    def test_remove_special_characters(self):
        """특수문자 제거"""
        input_text = "• 첫 번째\n- 두 번째\n* 세 번째"
        result = normalize_script(input_text)
        assert "•" not in result
        assert "-" not in result
        assert "*" not in result

    def test_remove_consecutive_spaces(self):
        """연속 공백 제거"""
        input_text = "여러분,    오늘은     좋은  날입니다."
        result = normalize_script(input_text)
        assert "    " not in result
        assert "  " not in result


class TestDurationCalculation:
    """스크립트 길이 계산 테스트"""

    def test_korean_short_text(self):
        """한국어 짧은 텍스트"""
        text = "여러분, 오늘은 특별한 날입니다."
        duration = calculate_duration(text, language="ko")
        assert 3 <= duration <= 5  # 3-5초 예상

    def test_korean_long_text(self):
        """한국어 긴 텍스트"""
        text = """
        여러분, 오늘은 AI가 자동으로 영상을 만들어주는
        놀라운 시스템을 소개합니다.
        이 시스템은 스크립트 작성부터 음성 생성,
        영상 편집까지 모든 과정을 자동화합니다.
        """
        duration = calculate_duration(text, language="ko")
        assert 15 <= duration <= 25

    def test_english_text(self):
        """영어 텍스트"""
        text = "Hello, welcome to our AI video automation platform."
        duration = calculate_duration(text, language="en")
        assert 3 <= duration <= 6

    def test_empty_text(self):
        """빈 텍스트"""
        text = ""
        duration = calculate_duration(text)
        assert duration == 0


class TestKeywordExtraction:
    """키워드 추출 테스트"""

    def test_extract_korean_keywords(self):
        """한국어 키워드 추출"""
        text = "AI 비디오 자동화 시스템을 소개합니다."
        keywords = extract_keywords(text, language="ko")
        assert "AI" in keywords
        assert "비디오" in keywords
        assert "자동화" in keywords

    def test_extract_english_keywords(self):
        """영어 키워드 추출"""
        text = "Introducing our revolutionary AI video automation system."
        keywords = extract_keywords(text, language="en")
        assert "AI" in keywords or "video" in keywords

    def test_filter_stopwords(self):
        """불용어 필터링"""
        text = "이것은 매우 좋은 시스템입니다."
        keywords = extract_keywords(text, language="ko")
        # 불용어 제외 확인
        assert "이것은" not in keywords
        assert "매우" not in keywords


class TestScriptBlockSplitting:
    """스크립트 블록 분할 테스트"""

    def test_split_by_paragraphs(self):
        """문단별 분할"""
        text = """
        여러분, 오늘은 특별한 날입니다.

        AI가 자동으로 영상을 만들어줍니다.

        지금 바로 시작하세요!
        """
        blocks = split_into_blocks(text, method="paragraph")
        assert len(blocks) >= 3

    def test_split_by_duration(self):
        """시간별 분할 (10초 단위)"""
        text = """
        여러분, 오늘은 AI가 자동으로 영상을 만들어주는
        놀라운 시스템을 소개합니다.
        이 시스템은 스크립트 작성부터 음성 생성,
        영상 편집까지 모든 과정을 자동화합니다.
        지금 바로 시작해보세요!
        """
        blocks = split_into_blocks(text, method="duration", max_duration=10)
        assert len(blocks) >= 2

        # 각 블록 10초 이하 확인
        for block in blocks:
            duration = calculate_duration(block["text"])
            assert duration <= 12  # 약간의 여유

    def test_block_metadata(self):
        """블록 메타데이터 생성"""
        text = "여러분, 오늘은 특별한 날입니다.\n\nAI가 자동으로 영상을 만듭니다."
        blocks = split_into_blocks(text, method="paragraph")

        for block in blocks:
            assert "text" in block
            assert "duration" in block
            assert "type" in block  # hook, body, cta 등


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
