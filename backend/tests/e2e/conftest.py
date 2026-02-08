"""E2E Test Fixtures and Configuration"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.config import get_settings

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session"""
    # Use separate test database
    engine = create_engine("sqlite:///test_omni_db.sqlite")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def sample_campaign_data():
    """Sample campaign data for testing"""
    return {
        "name": "E2E Test Campaign",
        "client_id": None,
        "concept_gender": "male",
        "concept_tone": "professional",
        "concept_style": "cinematic",
        "platform": "YouTube"
    }


@pytest.fixture(scope="session")
def sample_script():
    """Sample script for testing"""
    return """여러분, 오늘은 놀라운 AI 비디오 에디터를 소개합니다!
이 에디터는 스크립트만 입력하면 자동으로 멋진 영상을 만들어줍니다.
복잡한 편집 프로그램은 이제 안녕하세요.
지금 바로 시작해보세요!"""


@pytest.fixture(scope="session")
def sample_storyboard_blocks():
    """Sample storyboard blocks for testing"""
    return [
        {
            "block_type": "hook",
            "text": "여러분, 오늘은 놀라운 AI 비디오 에디터를 소개합니다!",
            "duration": 5,
            "visual_concept": "energetic intro",
            "background_url": "https://source.unsplash.com/1920x1080/?technology",
            "transition_effect": "fade"
        },
        {
            "block_type": "body",
            "text": "이 에디터는 스크립트만 입력하면 자동으로 멋진 영상을 만들어줍니다.",
            "duration": 7,
            "visual_concept": "product showcase",
            "background_url": "https://source.unsplash.com/1920x1080/?coding",
            "transition_effect": "wipeleft"
        },
        {
            "block_type": "cta",
            "text": "지금 바로 시작해보세요!",
            "duration": 3,
            "visual_concept": "call to action",
            "background_url": "https://source.unsplash.com/1920x1080/?success",
            "transition_effect": "fade"
        }
    ]
