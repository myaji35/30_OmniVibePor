"""
배경 이미지 생성 테스트
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.image_generation import ImageGenerationService
from app.services.stock_image import StockImageService
from app.services.background_selector import BackgroundSelector


class TestImageGenerationService:
    """DALL-E 이미지 생성 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_enhance_prompt(self):
        """프롬프트 향상 테스트"""
        service = ImageGenerationService()
        prompt = "modern workspace"
        enhanced = service._enhance_prompt(prompt)

        assert "professional" in enhanced.lower() or "cinematic" in enhanced.lower()
        assert "modern workspace" in enhanced

    @pytest.mark.asyncio
    @patch('app.services.image_generation.OpenAI')
    @patch('app.services.image_generation.cloudinary.uploader.upload')
    async def test_generate_background_image(self, mock_upload, mock_openai):
        """배경 이미지 생성 테스트 (Mock)"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(
            url="https://oaidalleapi.../test.png",
            revised_prompt="Enhanced modern workspace"
        )]
        mock_client.images.generate.return_value = mock_response
        mock_openai.return_value = mock_client

        # Mock Cloudinary upload
        mock_upload.return_value = {
            'secure_url': "https://res.cloudinary.com/test.png",
            'width': 1024,
            'height': 1024,
            'public_id': "test_id"
        }

        # 테스트 실행
        service = ImageGenerationService()
        result = await service.generate_background_image(
            prompt="modern workspace",
            style="natural"
        )

        # 검증
        assert result['success'] is True
        assert result['image_url'] == "https://res.cloudinary.com/test.png"
        assert result['width'] == 1024
        assert result['height'] == 1024


class TestStockImageService:
    """Unsplash 스톡 이미지 서비스 테스트"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_search_images(self, mock_client):
        """Unsplash 검색 테스트 (Mock)"""
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 'test123',
                    'description': 'Modern workspace',
                    'urls': {
                        'regular': 'https://images.unsplash.com/regular',
                        'full': 'https://images.unsplash.com/full',
                        'thumb': 'https://images.unsplash.com/thumb'
                    },
                    'width': 1920,
                    'height': 1080,
                    'user': {
                        'name': 'John Doe',
                        'links': {'html': 'https://unsplash.com/@johndoe'}
                    },
                    'links': {
                        'download_location': 'https://api.unsplash.com/photos/test123/download'
                    }
                }
            ]
        }

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # 테스트 실행
        service = StockImageService(access_key="test_key")
        results = await service.search_images(query="workspace")

        # 검증
        assert len(results) == 1
        assert results[0]['id'] == 'test123'
        assert results[0]['photographer'] == 'John Doe'


class TestBackgroundSelector:
    """배경 선택기 테스트"""

    @pytest.mark.asyncio
    async def test_fallback_solid_color(self):
        """Fallback 단색 배경 테스트"""
        selector = BackgroundSelector()

        # Professional mood
        result = selector._fallback_solid_color({"mood": "professional"})
        assert result['background_type'] == "solid_color"
        assert result['source'] == "fallback"
        assert result['metadata']['color'] == "#1F2937"

        # Energetic mood
        result = selector._fallback_solid_color({"mood": "energetic"})
        assert result['metadata']['color'] == "#EF4444"

    @pytest.mark.asyncio
    @patch('app.services.background_selector.ImageGenerationService')
    @patch('app.services.background_selector.StockImageService')
    async def test_select_background_prefer_ai(self, mock_stock, mock_image_gen):
        """배경 선택 - AI 우선 테스트"""
        # Mock AI 생성 성공
        mock_gen_service = MagicMock()
        mock_gen_service.generate_from_keywords = AsyncMock(return_value={
            'success': True,
            'image_url': 'https://cloudinary.com/ai.png',
            'prompt': 'test prompt',
            'dall_e_url': 'https://dalle.com/test.png',
            'width': 1024,
            'height': 1024
        })
        mock_image_gen.return_value = mock_gen_service

        # 테스트 실행
        selector = BackgroundSelector()
        selector.image_gen_service = mock_gen_service

        result = await selector.select_background(
            keywords=["AI", "technology"],
            visual_concept={"mood": "professional"},
            prefer_ai=True
        )

        # 검증
        assert result['background_type'] == "ai_generated"
        assert result['source'] == "dall-e"
        assert result['background_url'] == 'https://cloudinary.com/ai.png'


def test_import_all_modules():
    """모든 모듈 import 테스트"""
    from app.services.image_generation import ImageGenerationService
    from app.services.stock_image import StockImageService
    from app.services.background_selector import BackgroundSelector
    from app.tasks.background_tasks import (
        generate_background_task,
        select_background_auto_task,
        batch_generate_backgrounds_task
    )
    from app.api.v1.backgrounds import router

    assert ImageGenerationService is not None
    assert StockImageService is not None
    assert BackgroundSelector is not None
    assert generate_background_task is not None
    assert router is not None
