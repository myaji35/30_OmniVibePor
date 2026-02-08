"""E2E Test: Remotion Video Rendering

Remotion 렌더링 테스트:
- Props 변환
- 비동기 렌더링
- 플랫폼별 최적화
- Cloudinary 업로드
"""
import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.e2e
class TestRemotionRendering:
    """Remotion 렌더링 E2E 테스트"""

    async def test_props_conversion(
        self,
        client: AsyncClient,
        sample_storyboard_blocks,
        sample_campaign_data
    ):
        """Storyboard Blocks → Remotion Props 변환"""
        request_data = {
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": sample_campaign_data,
            "audio_url": "https://example.com/audio.mp3"
        }

        response = await client.post("/api/v1/remotion/convert-props", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "props" in data

        props = data["props"]

        # Props 구조 검증
        assert "platform" in props
        assert "composition" in props
        assert "concept" in props
        assert "scenes" in props
        assert "audio" in props
        assert "metadata" in props

        # Scenes 검증
        assert len(props["scenes"]) == len(sample_storyboard_blocks)

        for idx, scene in enumerate(props["scenes"]):
            assert scene["id"] == f"scene_{idx}"
            assert "text" in scene
            assert "duration" in scene
            assert "startTime" in scene
            assert "endTime" in scene

        # Metadata 검증
        assert props["metadata"]["sceneCount"] == len(sample_storyboard_blocks)
        assert props["metadata"]["totalDuration"] > 0

        print(f"\n✅ Props 변환 성공:")
        print(f"   씬 개수: {len(props['scenes'])}")
        print(f"   총 길이: {props['metadata']['totalDuration']}초")
        print(f"   플랫폼: {props['platform']}")

    async def test_remotion_render_youtube(
        self,
        client: AsyncClient,
        sample_storyboard_blocks
    ):
        """YouTube 영상 렌더링"""
        request_data = {
            "content_id": 8888,
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": {
                "gender": "male",
                "tone": "professional",
                "style": "cinematic",
                "platform": "YouTube"
            },
            "audio_url": None,
            "composition_id": "OmniVibeComposition"
        }

        response = await client.post("/api/v1/remotion/render", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["status"] == "processing"

        task_id = data["task_id"]
        print(f"\n🎬 YouTube 렌더링 시작 (Task: {task_id})")

        # 간단한 상태 확인만 (실제 렌더링은 너무 오래 걸림)
        await asyncio.sleep(2)

        status_response = await client.get(f"/api/v1/remotion/status/{task_id}")
        status_data = status_response.json()

        assert status_data["status"] in ["pending", "processing", "completed"]
        print(f"   상태: {status_data['status']}")

    async def test_remotion_compositions_list(self, client: AsyncClient):
        """사용 가능한 Composition 목록 조회"""
        response = await client.get("/api/v1/remotion/compositions")

        assert response.status_code == 200
        compositions = response.json()

        assert isinstance(compositions, list)
        assert len(compositions) > 0

        for comp in compositions:
            assert "id" in comp
            assert "name" in comp
            assert "description" in comp
            assert "defaultProps" in comp

        print(f"\n✅ Composition 목록 조회 성공:")
        for comp in compositions:
            print(f"   - {comp['id']}: {comp['name']}")

    async def test_remotion_validate_installation(self, client: AsyncClient):
        """Remotion 설치 검증"""
        response = await client.get("/api/v1/remotion/validate")

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "ok":
            print(f"\n✅ Remotion 설치 확인:")
            print(f"   버전: {data['details']['version']}")
            print(f"   경로: {data['details']['frontend_path']}")
            print(f"   설치 상태: {data['details']['installed']}")

            assert data["details"]["installed"] is True
        else:
            pytest.fail(f"Remotion not installed: {data['details']}")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.platform
class TestPlatformOptimization:
    """플랫폼별 최적화 테스트"""

    @pytest.mark.parametrize("platform,expected_resolution", [
        ("YouTube", "1920x1080"),
        ("Instagram", "1080x1350"),
        ("TikTok", "1080x1920"),
        ("Facebook", "1280x720")
    ])
    async def test_platform_specific_props(
        self,
        client: AsyncClient,
        sample_storyboard_blocks,
        platform: str,
        expected_resolution: str
    ):
        """플랫폼별 Props 생성 테스트"""
        request_data = {
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": {
                "gender": "male",
                "tone": "professional",
                "style": "cinematic",
                "platform": platform
            }
        }

        response = await client.post("/api/v1/remotion/convert-props", json=request_data)

        assert response.status_code == 200
        data = response.json()

        props = data["props"]

        # 플랫폼 검증
        assert props["platform"] == platform

        # 해상도 검증
        composition = props["composition"]
        actual_resolution = f"{composition['width']}x{composition['height']}"
        assert actual_resolution == expected_resolution

        print(f"\n✅ {platform} Props 검증:")
        print(f"   해상도: {actual_resolution}")
        print(f"   FPS: {composition['fps']}")
        print(f"   Bitrate: {composition['bitrate']}")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.error
class TestRemotionErrors:
    """Remotion 에러 핸들링 테스트"""

    async def test_invalid_storyboard_blocks(self, client: AsyncClient):
        """잘못된 Storyboard Blocks"""
        request_data = {
            "storyboard_blocks": [],  # 빈 배열
            "campaign_concept": {
                "platform": "YouTube"
            }
        }

        response = await client.post("/api/v1/remotion/convert-props", json=request_data)

        # 빈 블록은 에러 또는 빈 Props 반환
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert len(data["props"]["scenes"]) == 0

        print("\n✅ 빈 블록 처리 검증 완료")

    async def test_missing_required_fields(self, client: AsyncClient):
        """필수 필드 누락"""
        request_data = {
            "storyboard_blocks": [{"text": "test"}]
            # campaign_concept 누락
        }

        response = await client.post("/api/v1/remotion/convert-props", json=request_data)

        assert response.status_code == 422  # Validation Error
        print("\n✅ 필수 필드 누락 에러 정상 처리")

    async def test_invalid_composition_id(
        self,
        client: AsyncClient,
        sample_storyboard_blocks
    ):
        """존재하지 않는 Composition ID"""
        request_data = {
            "content_id": 7777,
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": {
                "platform": "YouTube"
            },
            "composition_id": "NonExistentComposition"
        }

        response = await client.post("/api/v1/remotion/render", json=request_data)

        # Task는 시작되지만 나중에 실패할 것
        assert response.status_code in [200, 400, 404]

        print("\n✅ 잘못된 Composition ID 처리 검증 완료")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.performance
class TestRemotionPerformance:
    """Remotion 성능 테스트"""

    async def test_props_conversion_speed(
        self,
        client: AsyncClient,
        sample_storyboard_blocks
    ):
        """Props 변환 속도 측정"""
        import time

        request_data = {
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": {
                "platform": "YouTube"
            }
        }

        start_time = time.time()
        response = await client.post("/api/v1/remotion/convert-props", json=request_data)
        elapsed = time.time() - start_time

        assert response.status_code == 200

        print(f"\n📊 Props 변환 성능:")
        print(f"   소요 시간: {elapsed:.3f}초")
        print(f"   목표: < 1초")

        # Props 변환은 매우 빨라야 함 (1초 이내)
        assert elapsed < 1.0, f"Props conversion too slow: {elapsed:.3f}s"

    async def test_concurrent_props_conversion(self, client: AsyncClient):
        """동시 다발적 Props 변환"""
        import time

        request_data = {
            "storyboard_blocks": [
                {"block_type": "hook", "text": "Test", "duration": 5}
            ],
            "campaign_concept": {"platform": "YouTube"}
        }

        # 10개 동시 요청
        start_time = time.time()
        tasks = [
            client.post("/api/v1/remotion/convert-props", json=request_data)
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # 모두 성공해야 함
        for response in responses:
            assert response.status_code == 200

        print(f"\n📊 동시 처리 성능:")
        print(f"   10개 요청 처리: {elapsed:.3f}초")
        print(f"   평균: {elapsed/10:.3f}초/요청")

        # 동시 처리는 순차 처리보다 빨라야 함
        assert elapsed < 5.0, f"Concurrent processing too slow: {elapsed:.3f}s"
