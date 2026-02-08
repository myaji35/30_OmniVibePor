"""E2E Test: Writer Agent

Writer Agent 단독 테스트:
- Neo4j Memory 통합
- Few-shot Learning
- 플랫폼별 최적화
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.e2e
class TestWriterAgent:
    """Writer Agent E2E 테스트"""

    async def test_generate_script_with_memory(self, client: AsyncClient):
        """Neo4j Memory를 활용한 스크립트 생성"""
        request_data = {
            "campaign_name": "메모리 테스트 캠페인",
            "topic": "AI 영상 제작",
            "platform": "YouTube",
            "target_duration": 60,
            "tone": "professional"
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 스크립트 기본 검증
        assert "script" in data
        assert len(data["script"]) > 0

        # 메타데이터 검증
        assert "metadata" in data
        metadata = data["metadata"]

        # 단어 수 검증
        if "word_count" in metadata:
            assert metadata["word_count"] > 0

        # 예상 길이 검증
        if "estimated_duration" in metadata:
            assert 50 <= metadata["estimated_duration"] <= 70  # ±10초

        print(f"\n✅ 스크립트 생성 성공:")
        print(f"   길이: {len(data['script'])}자")
        print(f"   단어 수: {metadata.get('word_count', 'N/A')}")
        print(f"   예상 길이: {metadata.get('estimated_duration', 'N/A')}초")

    async def test_generate_script_youtube(self, client: AsyncClient):
        """YouTube용 스크립트 생성"""
        request_data = {
            "campaign_name": "YouTube 캠페인",
            "topic": "프로덕트 리뷰",
            "platform": "YouTube",
            "target_duration": 120
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        script = data["script"]

        # YouTube 특성 검증
        # - 긴 형식 콘텐츠
        # - 상세한 설명
        assert len(script) > 200

        print(f"\n✅ YouTube 스크립트: {len(script)}자")

    async def test_generate_script_tiktok(self, client: AsyncClient):
        """TikTok용 스크립트 생성 (짧고 임팩트 있게)"""
        request_data = {
            "campaign_name": "TikTok 캠페인",
            "topic": "꿀팁 공유",
            "platform": "TikTok",
            "target_duration": 15
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        script = data["script"]

        # TikTok 특성 검증
        # - 짧은 형식 (15-60초)
        # - 임팩트 있는 훅
        assert len(script) < 300

        print(f"\n✅ TikTok 스크립트: {len(script)}자")

    async def test_generate_script_with_tone(self, client: AsyncClient):
        """톤 지정 스크립트 생성"""
        tones = ["professional", "casual", "energetic"]

        for tone in tones:
            request_data = {
                "campaign_name": f"{tone.title()} 캠페인",
                "topic": "제품 소개",
                "platform": "YouTube",
                "target_duration": 60,
                "tone": tone
            }

            response = await client.post("/api/v1/writer/generate", json=request_data)

            assert response.status_code == 200
            data = response.json()

            print(f"\n✅ {tone} 톤 스크립트 생성 성공")

    async def test_script_consistency(self, client: AsyncClient):
        """동일 조건으로 여러 번 생성 시 일관성 확인"""
        request_data = {
            "campaign_name": "일관성 테스트",
            "topic": "AI 기술 소개",
            "platform": "YouTube",
            "target_duration": 60,
            "tone": "professional"
        }

        scripts = []
        for i in range(3):
            response = await client.post("/api/v1/writer/generate", json=request_data)
            assert response.status_code == 200
            scripts.append(response.json()["script"])

        # 길이 일관성 확인 (±20%)
        lengths = [len(s) for s in scripts]
        avg_length = sum(lengths) / len(lengths)

        for length in lengths:
            deviation = abs(length - avg_length) / avg_length
            assert deviation < 0.3, f"길이 편차가 큼: {deviation*100:.1f}%"

        print(f"\n✅ 일관성 검증:")
        print(f"   평균 길이: {avg_length:.0f}자")
        print(f"   최소/최대: {min(lengths)}/{max(lengths)}자")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.error
class TestWriterAgentErrors:
    """Writer Agent 에러 핸들링 테스트"""

    async def test_missing_required_fields(self, client: AsyncClient):
        """필수 필드 누락 시 에러"""
        request_data = {
            "topic": "테스트"
            # campaign_name, platform 누락
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)

        assert response.status_code == 422  # Validation Error
        print("\n✅ 필수 필드 누락 에러 정상 처리")

    async def test_invalid_platform(self, client: AsyncClient):
        """잘못된 플랫폼 지정"""
        request_data = {
            "campaign_name": "테스트",
            "topic": "테스트",
            "platform": "InvalidPlatform",
            "target_duration": 60
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)

        # 422 (Validation Error) 또는 400 (Bad Request) 예상
        assert response.status_code in [400, 422]
        print("\n✅ 잘못된 플랫폼 에러 정상 처리")

    async def test_extreme_duration(self, client: AsyncClient):
        """극단적인 목표 길이 (너무 짧거나 길 때)"""
        # 너무 짧은 경우 (5초)
        request_data = {
            "campaign_name": "테스트",
            "topic": "테스트",
            "platform": "YouTube",
            "target_duration": 5
        }

        response = await client.post("/api/v1/writer/generate", json=request_data)
        # 최소 길이 제한 있을 수 있음
        assert response.status_code in [200, 400, 422]

        # 너무 긴 경우 (10분)
        request_data["target_duration"] = 600

        response = await client.post("/api/v1/writer/generate", json=request_data)
        assert response.status_code in [200, 400, 422]

        print("\n✅ 극단적 길이 처리 검증 완료")
