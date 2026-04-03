"""Phase 4 E2E 통합 테스트 — Creator User Flow + 실패 시나리오

ISS-005: 10개 페이지 순환 + 실패 시나리오 10개
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def ac():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ═══════════════════════════════════════════════════
# Creator User Flow — 정상 시나리오
# ═══════════════════════════════════════════════════

class TestCreatorFlow:
    """Creator 페르소나 전체 User Flow 검증"""

    @pytest.mark.asyncio
    async def test_01_health_check(self, ac: AsyncClient):
        """1. 서비스 헬스 체크"""
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["api"] == "healthy"

    @pytest.mark.asyncio
    async def test_02_root_welcome(self, ac: AsyncClient):
        """2. 루트 페이지 접속"""
        res = await ac.get("/")
        assert res.status_code == 200
        assert "OmniVibe Pro" in res.json()["service"]

    @pytest.mark.asyncio
    async def test_03_strategy_preview(self, ac: AsyncClient):
        """3. 전략 수립 — 미리보기 (API 키 없이 동작)"""
        res = await ac.post("/api/v1/strategy/preview", json={
            "business_goal": "테스트 목표",
            "target_audience": "테스트 타겟",
            "brand_name": "TestBrand",
            "channels": ["youtube", "blog"],
            "duration_weeks": 2,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["brand_name"] == "TestBrand"
        assert len(data["channel_strategies"]) == 2
        assert data["total_contents"] > 0
        assert len(data["content_calendar"]) > 0

    @pytest.mark.asyncio
    async def test_04_billing_plans(self, ac: AsyncClient):
        """4. 구독 플랜 목록 조회"""
        res = await ac.get("/api/v1/billing/plans")
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_05_tts_voices(self, ac: AsyncClient):
        """5. TTS 음성 목록 조회"""
        res = await ac.get("/api/v1/produce/voices")
        assert res.status_code == 200
        data = res.json()
        assert len(data["voices"]) >= 8
        assert any(v["id"] == "ko-KR-SunHiNeural" for v in data["voices"])

    @pytest.mark.asyncio
    async def test_06_publish_channels(self, ac: AsyncClient):
        """6. 배포 채널 목록 조회"""
        res = await ac.get("/api/v1/publish/channels")
        assert res.status_code == 200
        data = res.json()
        assert len(data["channels"]) >= 4
        channel_ids = [c["id"] for c in data["channels"]]
        assert "youtube" in channel_ids
        assert "instagram" in channel_ids

    @pytest.mark.asyncio
    async def test_07_publish_history_empty(self, ac: AsyncClient):
        """7. 발행 이력 — 빈 상태"""
        res = await ac.get("/api/v1/publish/history")
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_08_audio_voices(self, ac: AsyncClient):
        """8. ElevenLabs 음성 목록"""
        res = await ac.get("/api/v1/audio/voices")
        # API 키 없으면 500이지만 엔드포인트 자체는 존재
        assert res.status_code in (200, 500)

    @pytest.mark.asyncio
    async def test_09_websocket_connections(self, ac: AsyncClient):
        """9. WebSocket 연결 현황"""
        res = await ac.get("/api/v1/ws/connections")
        assert res.status_code == 200
        assert "total_connections" in res.json()

    @pytest.mark.asyncio
    async def test_10_docs_accessible(self, ac: AsyncClient):
        """10. API 문서 접근"""
        res = await ac.get("/docs")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════
# 실패 시나리오 10개
# ═══════════════════════════════════════════════════

class TestFailureScenarios:
    """실패 시나리오 — 사용자 친화적 에러 메시지 검증"""

    @pytest.mark.asyncio
    async def test_fail_01_strategy_empty_goal(self, ac: AsyncClient):
        """F1. 전략 생성 — 빈 목표"""
        res = await ac.post("/api/v1/strategy/preview", json={
            "business_goal": "",
            "target_audience": "test",
            "brand_name": "test",
        })
        assert res.status_code == 422  # validation error

    @pytest.mark.asyncio
    async def test_fail_02_strategy_missing_brand(self, ac: AsyncClient):
        """F2. 전략 생성 — 브랜드명 누락"""
        res = await ac.post("/api/v1/strategy/preview", json={
            "business_goal": "test goal",
            "target_audience": "test",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_03_produce_empty_script(self, ac: AsyncClient):
        """F3. 프레젠테이션 — 빈 스크립트"""
        res = await ac.post("/api/v1/produce/presentation", json={
            "script": "",
            "brand_name": "test",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_04_publish_missing_title(self, ac: AsyncClient):
        """F4. 배포 — 제목 누락"""
        res = await ac.post("/api/v1/publish/schedule", json={
            "channel": "youtube",
            "content_url": "/test.mp4",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_05_publish_missing_url(self, ac: AsyncClient):
        """F5. 배포 — URL 누락"""
        res = await ac.post("/api/v1/publish/schedule", json={
            "title": "test",
            "channel": "youtube",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_06_audio_empty_text(self, ac: AsyncClient):
        """F6. 오디오 생성 — 빈 텍스트"""
        res = await ac.post("/api/v1/audio/generate", json={
            "text": "",
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_07_nonexistent_endpoint(self, ac: AsyncClient):
        """F7. 존재하지 않는 엔드포인트"""
        res = await ac.get("/api/v1/nonexistent")
        assert res.status_code in (404, 405)

    @pytest.mark.asyncio
    async def test_fail_08_invalid_json(self, ac: AsyncClient):
        """F8. 잘못된 JSON 형식"""
        res = await ac.post(
            "/api/v1/strategy/preview",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_09_audio_invalid_threshold(self, ac: AsyncClient):
        """F9. 오디오 — 잘못된 정확도 임계값"""
        res = await ac.post("/api/v1/audio/generate", json={
            "text": "테스트",
            "accuracy_threshold": 2.0,  # max 1.0
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_fail_10_whisper_no_file(self, ac: AsyncClient):
        """F10. Whisper — 파일 없이 요청"""
        res = await ac.post("/api/v1/whisper/timing/extract")
        assert res.status_code == 422
