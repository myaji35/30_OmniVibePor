"""설정 테스트"""
import pytest
from app.core.config import Settings


def test_settings_required_fields():
    """필수 환경 변수 확인"""
    required_fields = [
        'SECRET_KEY',
        'REDIS_URL',
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY'
    ]

    # Settings 모델이 필수 필드를 요구하는지 확인
    assert hasattr(Settings, '__annotations__')
    for field in required_fields:
        assert field in Settings.__annotations__


def test_settings_optional_fields():
    """옵션 필드 확인"""
    optional_fields = [
        'HEYGEN_API_KEY',
        'BANANA_API_KEY',
        'YOUTUBE_OAUTH_CLIENT_ID'
    ]

    for field in optional_fields:
        assert field in Settings.__annotations__
        # 옵션 필드는 None 허용
        assert 'None' in str(Settings.__annotations__[field])
