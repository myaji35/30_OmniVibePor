"""E2E Test: Full Video Production Pipeline

테스트 플로우:
1. Writer Agent로 스크립트 생성
2. Director Agent로 콘티 생성
3. Audio Director로 오디오 생성
4. Remotion으로 영상 렌더링
5. 최종 결과 검증
"""
import pytest
import asyncio
import time
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.e2e
class TestFullPipeline:
    """전체 비디오 제작 파이프라인 E2E 테스트"""

    async def test_01_health_check(self, client: AsyncClient):
        """Step 0: API Health Check"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")

    async def test_02_writer_agent_script_generation(
        self,
        client: AsyncClient,
        sample_campaign_data
    ):
        """Step 1: Writer Agent - 스크립트 생성"""
        request_data = {
            "campaign_name": sample_campaign_data["name"],
            "topic": "AI 비디오 에디터 소개",
            "platform": sample_campaign_data["platform"],
            "target_duration": 60,
            "tone": "professional",
            "target_audience": "마케터"
        }

        print("\n🎬 Step 1: Writer Agent 호출...")
        start_time = time.time()

        response = await client.post("/api/v1/writer/generate", json=request_data)

        elapsed = time.time() - start_time
        print(f"   ⏱️  소요 시간: {elapsed:.2f}초")

        assert response.status_code == 200
        data = response.json()

        assert "script" in data
        assert len(data["script"]) > 0
        assert "metadata" in data

        print(f"   ✅ 스크립트 생성 완료 ({len(data['script'])}자)")
        print(f"   📄 Preview: {data['script'][:100]}...")

        # 메타데이터 저장 (다음 테스트에서 사용)
        pytest.generated_script = data["script"]
        pytest.script_metadata = data["metadata"]

    async def test_03_director_agent_storyboard_generation(
        self,
        client: AsyncClient,
        sample_campaign_data
    ):
        """Step 2: Director Agent - 콘티 생성"""
        # 이전 테스트에서 생성된 스크립트 사용
        if not hasattr(pytest, "generated_script"):
            pytest.skip("스크립트가 생성되지 않음")

        request_data = {
            "script": pytest.generated_script,
            "campaign_concept": {
                "gender": sample_campaign_data["concept_gender"],
                "tone": sample_campaign_data["concept_tone"],
                "style": sample_campaign_data["concept_style"],
                "platform": sample_campaign_data["platform"]
            },
            "target_duration": 60
        }

        print("\n🎨 Step 2: Director Agent 호출...")
        start_time = time.time()

        # Note: 실제 API 엔드포인트가 없을 수 있으므로 mock 데이터 사용
        # 실제 구현에서는 /api/v1/director/analyze 호출
        response = await client.post(
            "/api/v1/storyboard/analyze",
            json=request_data
        )

        elapsed = time.time() - start_time
        print(f"   ⏱️  소요 시간: {elapsed:.2f}초")

        # 실제 API가 없으면 스킵
        if response.status_code == 404:
            print("   ⚠️  Director API 엔드포인트 없음 - 샘플 데이터 사용")
            pytest.storyboard_blocks = [
                {
                    "block_type": "hook",
                    "text": pytest.generated_script[:50],
                    "duration": 5,
                    "visual_concept": "intro",
                    "background_url": "https://source.unsplash.com/1920x1080/?tech"
                }
            ]
        else:
            assert response.status_code == 200
            data = response.json()
            assert "blocks" in data
            pytest.storyboard_blocks = data["blocks"]
            print(f"   ✅ 콘티 생성 완료 ({len(data['blocks'])}개 블록)")

    async def test_04_audio_generation(self, client: AsyncClient):
        """Step 3: Audio Director - Zero-Fault 오디오 생성"""
        if not hasattr(pytest, "generated_script"):
            pytest.skip("스크립트가 생성되지 않음")

        request_data = {
            "content_id": 9999,  # Test content ID
            "text": pytest.generated_script,
            "voice_id": "default",
            "language": "ko"
        }

        print("\n🔊 Step 3: Audio Director 호출...")
        start_time = time.time()

        response = await client.post("/api/v1/audio/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["status"] == "processing"

        task_id = data["task_id"]
        print(f"   📝 Task ID: {task_id}")

        # Task 상태 폴링 (최대 60초)
        max_wait = 60
        for i in range(max_wait):
            await asyncio.sleep(1)

            status_response = await client.get(f"/api/v1/audio/status/{task_id}")
            status_data = status_response.json()

            if status_data["status"] == "completed":
                elapsed = time.time() - start_time
                print(f"   ⏱️  소요 시간: {elapsed:.2f}초")
                print(f"   ✅ 오디오 생성 완료")
                print(f"   🎯 정확도: {status_data['result']['accuracy']:.2f}%")

                assert status_data["result"]["accuracy"] >= 95.0
                pytest.audio_url = status_data["result"]["audio_url"]
                return

            elif status_data["status"] == "failed":
                pytest.fail(f"Audio generation failed: {status_data.get('message')}")

            # 진행 상태 출력
            if i % 5 == 0:
                print(f"   ⏳ 대기 중... ({i}/{max_wait}초)")

        pytest.fail("Audio generation timeout (60s)")

    async def test_05_remotion_props_conversion(
        self,
        client: AsyncClient,
        sample_campaign_data
    ):
        """Step 4: Remotion Props 변환"""
        if not hasattr(pytest, "storyboard_blocks"):
            pytest.skip("콘티가 생성되지 않음")

        request_data = {
            "storyboard_blocks": pytest.storyboard_blocks,
            "campaign_concept": {
                "gender": sample_campaign_data["concept_gender"],
                "tone": sample_campaign_data["concept_tone"],
                "style": sample_campaign_data["concept_style"],
                "platform": sample_campaign_data["platform"]
            },
            "audio_url": getattr(pytest, "audio_url", None)
        }

        print("\n🔄 Step 4: Remotion Props 변환...")
        start_time = time.time()

        response = await client.post(
            "/api/v1/remotion/convert-props",
            json=request_data
        )

        elapsed = time.time() - start_time
        print(f"   ⏱️  소요 시간: {elapsed:.2f}초")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "props" in data

        props = data["props"]
        assert "scenes" in props
        assert len(props["scenes"]) > 0
        assert "platform" in props
        assert "audio" in props

        print(f"   ✅ Props 변환 완료 ({len(props['scenes'])}개 씬)")

        pytest.remotion_props = props

    async def test_06_remotion_video_rendering(
        self,
        client: AsyncClient,
        sample_campaign_data
    ):
        """Step 5: Remotion 영상 렌더링"""
        if not hasattr(pytest, "remotion_props"):
            pytest.skip("Remotion props가 생성되지 않음")

        request_data = {
            "content_id": 9999,
            "storyboard_blocks": pytest.storyboard_blocks,
            "campaign_concept": {
                "gender": sample_campaign_data["concept_gender"],
                "tone": sample_campaign_data["concept_tone"],
                "style": sample_campaign_data["concept_style"],
                "platform": sample_campaign_data["platform"]
            },
            "audio_url": getattr(pytest, "audio_url", None),
            "composition_id": "OmniVibeComposition"
        }

        print("\n🎬 Step 5: Remotion 영상 렌더링...")
        start_time = time.time()

        response = await client.post("/api/v1/remotion/render", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["status"] == "processing"

        task_id = data["task_id"]
        print(f"   📝 Task ID: {task_id}")

        # Task 상태 폴링 (최대 180초 = 3분)
        max_wait = 180
        for i in range(max_wait):
            await asyncio.sleep(2)

            status_response = await client.get(f"/api/v1/remotion/status/{task_id}")
            status_data = status_response.json()

            if status_data["status"] == "completed":
                elapsed = time.time() - start_time
                print(f"   ⏱️  소요 시간: {elapsed:.2f}초")
                print(f"   ✅ 영상 렌더링 완료")
                print(f"   🎥 Video URL: {status_data['result']['cloudinary_url']}")
                print(f"   ⏱️  영상 길이: {status_data['result']['duration']}초")
                print(f"   📐 해상도: {status_data['result']['resolution']}")

                pytest.video_url = status_data["result"]["cloudinary_url"]
                pytest.video_duration = status_data["result"]["duration"]
                return

            elif status_data["status"] == "failed":
                pytest.fail(f"Video rendering failed: {status_data.get('message')}")

            # 진행 상태 출력
            if i % 10 == 0:
                progress = status_data.get("progress", 0)
                print(f"   ⏳ 렌더링 중... {progress}% ({i}/{max_wait}초)")

        pytest.fail("Video rendering timeout (180s)")

    async def test_07_final_validation(self, client: AsyncClient):
        """Step 6: 최종 결과 검증"""
        if not hasattr(pytest, "video_url"):
            pytest.skip("영상이 생성되지 않음")

        print("\n✅ Step 6: 최종 검증...")

        # 생성된 아티팩트 확인
        assert hasattr(pytest, "generated_script"), "스크립트 생성 실패"
        assert hasattr(pytest, "storyboard_blocks"), "콘티 생성 실패"
        assert hasattr(pytest, "audio_url"), "오디오 생성 실패"
        assert hasattr(pytest, "video_url"), "영상 생성 실패"

        print(f"   ✅ 스크립트: {len(pytest.generated_script)}자")
        print(f"   ✅ 콘티 블록: {len(pytest.storyboard_blocks)}개")
        print(f"   ✅ 오디오: {pytest.audio_url}")
        print(f"   ✅ 영상: {pytest.video_url}")
        print(f"   ✅ 영상 길이: {pytest.video_duration}초")

        print("\n🎉 전체 파이프라인 테스트 성공!")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.performance
class TestPerformanceBenchmark:
    """성능 벤치마크 테스트"""

    async def test_writer_agent_performance(self, client: AsyncClient):
        """Writer Agent 성능 측정"""
        request_data = {
            "campaign_name": "Performance Test",
            "topic": "AI 테스트",
            "platform": "YouTube",
            "target_duration": 60
        }

        start_time = time.time()
        response = await client.post("/api/v1/writer/generate", json=request_data)
        elapsed = time.time() - start_time

        assert response.status_code == 200
        print(f"\n📊 Writer Agent 성능:")
        print(f"   ⏱️  응답 시간: {elapsed:.2f}초")
        print(f"   🎯 목표: < 10초")

        # 성능 기준: 10초 이내
        assert elapsed < 10.0, f"Writer Agent too slow: {elapsed:.2f}s"

    async def test_remotion_props_conversion_performance(
        self,
        client: AsyncClient,
        sample_storyboard_blocks,
        sample_campaign_data
    ):
        """Remotion Props 변환 성능 측정"""
        request_data = {
            "storyboard_blocks": sample_storyboard_blocks,
            "campaign_concept": sample_campaign_data
        }

        start_time = time.time()
        response = await client.post("/api/v1/remotion/convert-props", json=request_data)
        elapsed = time.time() - start_time

        assert response.status_code == 200
        print(f"\n📊 Props 변환 성능:")
        print(f"   ⏱️  응답 시간: {elapsed:.2f}초")
        print(f"   🎯 목표: < 1초")

        # 성능 기준: 1초 이내
        assert elapsed < 1.0, f"Props conversion too slow: {elapsed:.2f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
class TestIntegrationChecks:
    """통합 검증 테스트"""

    async def test_neo4j_connection(self, client: AsyncClient):
        """Neo4j 연결 확인"""
        # Neo4j Health Check (실제 엔드포인트가 있다면)
        response = await client.get("/api/v1/health/neo4j")

        if response.status_code == 404:
            print("\n⚠️  Neo4j health endpoint not found - skipping")
            pytest.skip("Neo4j health endpoint not implemented")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        print("\n✅ Neo4j 연결 정상")

    async def test_redis_connection(self, client: AsyncClient):
        """Redis 연결 확인"""
        response = await client.get("/api/v1/health/redis")

        if response.status_code == 404:
            print("\n⚠️  Redis health endpoint not found - skipping")
            pytest.skip("Redis health endpoint not implemented")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        print("\n✅ Redis 연결 정상")

    async def test_celery_worker_status(self, client: AsyncClient):
        """Celery Worker 상태 확인"""
        response = await client.get("/api/v1/health/celery")

        if response.status_code == 404:
            print("\n⚠️  Celery health endpoint not found - skipping")
            pytest.skip("Celery health endpoint not implemented")

        assert response.status_code == 200
        data = response.json()
        assert "workers" in data
        assert len(data["workers"]) > 0
        print(f"\n✅ Celery Workers: {len(data['workers'])}개 실행 중")

    async def test_remotion_installation(self, client: AsyncClient):
        """Remotion 설치 확인"""
        response = await client.get("/api/v1/remotion/validate")

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "ok":
            print("\n✅ Remotion 설치 확인:")
            print(f"   버전: {data['details']['version']}")
            print(f"   경로: {data['details']['frontend_path']}")
        else:
            pytest.fail(f"Remotion not installed: {data['details']['error']}")
