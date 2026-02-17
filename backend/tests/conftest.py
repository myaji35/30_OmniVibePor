"""
Pytest 공통 Fixtures 및 설정
"""
import pytest
import asyncio
import os
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.sqlite_client import get_db, init_db


# 테스트 DB 경로
TEST_DB_PATH = "test_omni_db.sqlite"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def event_loop():
    """
    세션 스코프 이벤트 루프
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    테스트 DB 초기화 (세션 시작 시 1회)
    """
    # 기존 테스트 DB 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # 테스트 DB 초기화
    init_db(db_path=TEST_DB_PATH)

    yield

    # 테스트 종료 후 DB 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
async def client():
    """
    테스트용 HTTP 클라이언트 (각 테스트마다 새로 생성)
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def db_session():
    """
    테스트용 DB 세션 (각 테스트마다 롤백)
    """
    engine = create_engine(TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # 테스트 종료 후 롤백
    session.rollback()
    session.close()


@pytest.fixture
def sample_campaign_data():
    """
    샘플 캠페인 데이터
    """
    return {
        "name": "테스트 캠페인",
        "client_id": 1,
        "concept_gender": "male",
        "concept_tone": "professional",
        "concept_style": "cinematic",
        "platform": "YouTube",
        "spreadsheet_id": "test_spreadsheet_123"
    }


@pytest.fixture
def sample_script():
    """
    샘플 스크립트
    """
    return """
    여러분, 오늘은 AI가 자동으로 영상을 만들어주는
    놀라운 시스템을 소개합니다.

    이 시스템은 스크립트 작성부터 음성 생성,
    영상 편집까지 모든 과정을 자동화합니다.

    지금 바로 시작해보세요!
    """


@pytest.fixture
def sample_user_data():
    """
    샘플 사용자 데이터
    """
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "테스트 사용자"
    }


@pytest.fixture
async def authenticated_client(client: AsyncClient, sample_user_data):
    """
    인증된 HTTP 클라이언트
    """
    # 회원가입
    response = await client.post("/api/v1/auth/register", json=sample_user_data)

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]

        # 헤더에 토큰 추가
        client.headers["Authorization"] = f"Bearer {access_token}"

    return client


@pytest.fixture
def mock_stripe_customer():
    """
    Mock Stripe Customer
    """
    return {
        "id": "cus_test123",
        "email": "test@example.com",
        "created": 1704067200,
        "currency": "usd"
    }


@pytest.fixture
def mock_stripe_subscription():
    """
    Mock Stripe Subscription
    """
    return {
        "id": "sub_test123",
        "customer": "cus_test123",
        "status": "active",
        "current_period_start": 1704067200,
        "current_period_end": 1706659200,
        "items": {
            "data": [{
                "price": {
                    "id": "price_pro_monthly",
                    "unit_amount": 4900,
                    "currency": "usd"
                }
            }]
        }
    }


# Pytest 플러그인 설정
def pytest_configure(config):
    """
    Pytest 설정
    """
    # 환경 변수 설정 (테스트 모드)
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    # Stripe 테스트 키 (Mock)
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"

    # AI API 테스트 키 (실제 호출 안 함)
    os.environ["ELEVENLABS_API_KEY"] = "test_key"
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["ANTHROPIC_API_KEY"] = "test_key"


def pytest_collection_modifyitems(config, items):
    """
    테스트 수집 후 커스터마이징
    """
    # e2e 테스트에 slow 마커 자동 추가
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(pytest.mark.slow)
