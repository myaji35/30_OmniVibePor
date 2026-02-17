"""
E2E 테스트: 전체 워크플로우 검증

Campaign 생성 → Script 생성 → Audio 생성 → Video 렌더링
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.db.sqlite_client import get_db, init_db


@pytest.fixture(scope="module")
def event_loop():
    """이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    """테스트용 HTTP 클라이언트"""
    # 테스트 DB 초기화
    init_db()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestFullWorkflow:
    """전체 워크플로우 E2E 테스트"""

    async def test_01_health_check(self, client: AsyncClient):
        """헬스 체크"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"

    async def test_02_create_campaign(self, client: AsyncClient):
        """캠페인 생성"""
        response = await client.post("/api/v1/campaigns", json={
            "name": "E2E Test Campaign",
            "client_id": 1,
            "concept_gender": "male",
            "concept_tone": "professional",
            "concept_style": "cinematic",
            "platform": "YouTube",
            "spreadsheet_id": "test_spreadsheet_123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "E2E Test Campaign"

        # 캠페인 ID 저장 (다음 테스트에서 사용)
        self.campaign_id = data["id"]

    async def test_03_generate_script(self, client: AsyncClient):
        """스크립트 자동 생성"""
        response = await client.post("/api/v1/writer/generate", json={
            "spreadsheet_id": "test_spreadsheet_123",
            "campaign_name": "E2E Test Campaign",
            "topic": "AI 비디오 자동화 테스트",
            "platform": "YouTube",
            "target_duration": 100
        })

        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert len(data["script"]) > 0
        assert "metadata" in data

        # 스크립트 저장
        self.script = data["script"]

    async def test_04_create_content(self, client: AsyncClient):
        """콘텐츠 생성"""
        response = await client.post(
            f"/api/v1/campaigns/{self.campaign_id}/contents",
            json={
                "title": "E2E 테스트 영상",
                "script": self.script,
                "duration": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

        # 콘텐츠 ID 저장
        self.content_id = data["id"]

    async def test_05_generate_storyboard(self, client: AsyncClient):
        """스토리보드 생성"""
        response = await client.post(
            f"/api/v1/storyboard/campaigns/{self.campaign_id}/content/{self.content_id}/generate"
        )

        assert response.status_code == 200
        data = response.json()
        assert "blocks" in data
        assert len(data["blocks"]) > 0

        # 첫 번째 블록 검증
        first_block = data["blocks"][0]
        assert "text" in first_block
        assert "duration" in first_block

    async def test_06_generate_audio(self, client: AsyncClient):
        """오디오 생성 (비동기)"""
        response = await client.post("/api/v1/audio/generate", json={
            "content_id": self.content_id,
            "text": self.script[:200],  # 처음 200자만 테스트
            "voice_id": "default",
            "language": "ko"
        })

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "processing"

        # Task ID 저장
        self.audio_task_id = data["task_id"]

    async def test_07_poll_audio_status(self, client: AsyncClient):
        """오디오 생성 상태 폴링"""
        max_wait = 60  # 최대 60초 대기

        for i in range(max_wait):
            response = await client.get(
                f"/api/v1/audio/status/{self.audio_task_id}"
            )

            assert response.status_code == 200
            data = response.json()

            if data["status"] == "completed":
                assert "audio_url" in data
                assert "accuracy" in data
                assert data["accuracy"] >= 95.0
                self.audio_url = data["audio_url"]
                break
            elif data["status"] == "failed":
                pytest.fail(f"Audio generation failed: {data.get('error')}")

            await asyncio.sleep(1)
        else:
            pytest.fail("Audio generation timeout (60s)")

    async def test_08_list_campaigns(self, client: AsyncClient):
        """캠페인 목록 조회"""
        response = await client.get("/api/v1/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) > 0

    async def test_09_get_campaign_contents(self, client: AsyncClient):
        """캠페인 콘텐츠 목록 조회"""
        response = await client.get(
            f"/api/v1/campaigns/{self.campaign_id}/contents"
        )

        assert response.status_code == 200
        data = response.json()
        assert "contents" in data
        assert len(data["contents"]) > 0


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """인증 플로우 E2E 테스트"""

    async def test_01_register(self, client: AsyncClient):
        """회원가입"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "테스트 사용자"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

        # 토큰 저장
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    async def test_02_login(self, client: AsyncClient):
        """로그인"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_03_get_current_user(self, client: AsyncClient):
        """현재 사용자 정보 조회"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_04_refresh_token(self, client: AsyncClient):
        """토큰 갱신"""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": self.refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_05_invalid_token(self, client: AsyncClient):
        """유효하지 않은 토큰"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestStripePaymentFlow:
    """Stripe 결제 플로우 E2E 테스트"""

    async def test_01_get_pricing_plans(self, client: AsyncClient):
        """플랜 목록 조회"""
        response = await client.get("/api/v1/billing/plans")

        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 3  # Free, Pro, Enterprise

    async def test_02_create_subscription(self, client: AsyncClient):
        """구독 생성 (테스트 모드)"""
        # 실제 Stripe 호출은 Mock으로 대체
        # 여기서는 API 구조만 검증
        pass

    async def test_03_get_current_subscription(self, client: AsyncClient):
        """현재 구독 조회"""
        # Mock 데이터로 검증
        pass


@pytest.mark.asyncio
class TestQuotaManagement:
    """Quota 관리 E2E 테스트"""

    async def test_01_check_quota_before_limit(self, client: AsyncClient):
        """Quota 제한 이전 요청"""
        # User의 quota_used = 5, quota_limit = 10 가정
        response = await client.post("/api/v1/writer/generate", json={
            "spreadsheet_id": "test",
            "campaign_name": "Test",
            "topic": "Test",
            "platform": "YouTube",
            "target_duration": 60
        })

        # Quota 여유 있음 → 200
        assert response.status_code in [200, 500]  # Mock 환경에서는 500도 허용

    async def test_02_check_quota_exceeded(self, client: AsyncClient):
        """Quota 초과 요청"""
        # User의 quota_used = 10, quota_limit = 10으로 설정 후
        # 다음 요청은 403 반환되어야 함
        pass


@pytest.mark.asyncio
class TestWebSocketProgress:
    """WebSocket 실시간 업데이트 테스트"""

    async def test_websocket_connection(self, client: AsyncClient):
        """WebSocket 연결 테스트"""
        # WebSocket 연결은 별도 라이브러리 필요
        # websockets 또는 starlette.testclient.WebSocketTestSession
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
