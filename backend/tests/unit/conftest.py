"""Unit 테스트 전용 conftest — app.main import 없이 순수 단위 테스트 지원."""
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
