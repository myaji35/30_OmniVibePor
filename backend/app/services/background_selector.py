"""
배경 이미지 자동 선택 서비스
3단계 우선순위 로직으로 최적의 배경 선택
"""
import os
import logging
from typing import Optional
from app.services.image_generation import ImageGenerationService
from app.services.stock_image import StockImageService

logger = logging.getLogger(__name__)


class BackgroundSelector:
    """
    배경 이미지 자동 선택 (3단계 우선순위)

    1순위: 캠페인 리소스 라이브러리 검색 (TODO)
    2순위: DALL-E AI 이미지 생성
    3순위: Unsplash 스톡 이미지
    Fallback: 단색 배경
    """

    def __init__(self):
        self.image_gen_service = ImageGenerationService()
        self.stock_service = StockImageService()

    async def select_background(
        self,
        campaign_id: Optional[int] = None,
        keywords: Optional[list[str]] = None,
        visual_concept: Optional[dict] = None,
        prefer_ai: bool = True
    ) -> dict:
        """
        배경 자동 선택 (3단계 우선순위)

        Args:
            campaign_id: 캠페인 ID (리소스 라이브러리 검색용, 현재 미사용)
            keywords: 배경 키워드 리스트 (예: ["AI", "technology", "future"])
            visual_concept: 비주얼 컨셉 (예: {"mood": "energetic", "color_tone": "bright"})
            prefer_ai: True이면 2순위(AI), False이면 3순위(스톡) 먼저 시도

        Returns:
            {
                "background_type": "uploaded" | "ai_generated" | "stock" | "solid_color",
                "background_url": "https://...",
                "source": "campaign_resources" | "dall-e" | "unsplash" | "fallback",
                "metadata": {...}  # 추가 정보 (프롬프트, 작가 등)
            }
        """
        # 기본값 설정
        keywords = keywords or ["professional", "background"]
        visual_concept = visual_concept or {"mood": "professional", "color_tone": "neutral"}

        logger.info(f"배경 선택 시작 - Keywords: {keywords}, Concept: {visual_concept}")

        # 1순위: 캠페인 리소스 라이브러리 (TODO: SQLite 구현 후)
        if campaign_id:
            resource_result = await self._search_campaign_resources(campaign_id, keywords)
            if resource_result:
                return resource_result

        # 2순위 vs 3순위 (prefer_ai에 따라 순서 변경)
        if prefer_ai:
            # AI 우선
            ai_result = await self._try_ai_generation(keywords, visual_concept)
            if ai_result:
                return ai_result

            # AI 실패 시 스톡 이미지
            stock_result = await self._try_stock_image(keywords)
            if stock_result:
                return stock_result
        else:
            # 스톡 우선
            stock_result = await self._try_stock_image(keywords)
            if stock_result:
                return stock_result

            # 스톡 실패 시 AI 생성
            ai_result = await self._try_ai_generation(keywords, visual_concept)
            if ai_result:
                return ai_result

        # Fallback: 단색 배경
        logger.warning("모든 배경 소스 실패, 단색 배경 사용")
        return self._fallback_solid_color(visual_concept)

    async def _search_campaign_resources(
        self,
        campaign_id: int,
        keywords: list[str]
    ) -> Optional[dict]:
        """
        1순위: 캠페인 리소스 라이브러리 검색

        TODO: SQLite 구현 후 활성화
        """
        logger.info(f"캠페인 리소스 검색 (campaign_id={campaign_id}) - 현재 미구현")
        # from app.lib.db import search_campaign_resources
        # resources = await search_campaign_resources(campaign_id, keywords)
        # if resources:
        #     return {
        #         "background_type": "uploaded",
        #         "background_url": resources[0]['url'],
        #         "source": "campaign_resources",
        #         "metadata": {"resource_id": resources[0]['id']}
        #     }
        return None

    async def _try_ai_generation(
        self,
        keywords: list[str],
        visual_concept: dict
    ) -> Optional[dict]:
        """
        2순위: DALL-E AI 이미지 생성
        """
        try:
            logger.info(f"DALL-E AI 이미지 생성 시도")

            result = await self.image_gen_service.generate_from_keywords(
                keywords=keywords,
                visual_concept=visual_concept,
                style="natural"
            )

            return {
                "background_type": "ai_generated",
                "background_url": result['image_url'],
                "source": "dall-e",
                "metadata": {
                    "prompt": result['prompt'],
                    "revised_prompt": result.get('revised_prompt'),
                    "dall_e_url": result['dall_e_url'],
                    "width": result['width'],
                    "height": result['height']
                }
            }

        except Exception as e:
            logger.error(f"DALL-E 생성 실패: {e}")
            return None

    async def _try_stock_image(
        self,
        keywords: list[str]
    ) -> Optional[dict]:
        """
        3순위: Unsplash 스톡 이미지
        """
        try:
            logger.info(f"Unsplash 스톡 이미지 검색 시도")

            # 키워드 조합 (최대 3개)
            query = " ".join(keywords[:3])

            # 검색
            stock_images = await self.stock_service.search_images(
                query=query,
                per_page=1,
                orientation="landscape"
            )

            if not stock_images:
                logger.warning(f"Unsplash 검색 결과 없음: {query}")
                return None

            # 첫 번째 결과 사용
            first_image = stock_images[0]

            # Cloudinary에 업로드
            cloudinary_url = await self.stock_service.download_and_upload(
                unsplash_url=first_image['url_full'],
                photo_id=first_image['id'],
                download_location=first_image.get('download_location')
            )

            return {
                "background_type": "stock",
                "background_url": cloudinary_url,
                "source": "unsplash",
                "metadata": {
                    "unsplash_id": first_image['id'],
                    "photographer": first_image['photographer'],
                    "photographer_url": first_image['photographer_url'],
                    "description": first_image['description'],
                    "width": first_image['width'],
                    "height": first_image['height']
                }
            }

        except Exception as e:
            logger.error(f"Unsplash 검색 실패: {e}")
            return None

    def _fallback_solid_color(self, visual_concept: dict) -> dict:
        """
        Fallback: 단색 배경

        색상은 visual_concept의 mood에 따라 결정
        """
        mood = visual_concept.get("mood", "professional").lower()

        # mood별 색상 매핑
        color_map = {
            "professional": "#1F2937",  # 다크 그레이
            "friendly": "#F3F4F6",      # 라이트 그레이
            "energetic": "#EF4444",     # 레드
            "calm": "#3B82F6",          # 블루
            "serious": "#111827",       # 거의 블랙
            "humorous": "#FBBF24"       # 옐로우
        }

        fallback_color = color_map.get(mood, "#1F2937")

        logger.info(f"Fallback 단색 배경 사용: {fallback_color} (mood: {mood})")

        return {
            "background_type": "solid_color",
            "background_url": None,
            "source": "fallback",
            "metadata": {
                "color": fallback_color,
                "mood": mood
            }
        }

    async def batch_select_backgrounds(
        self,
        blocks: list[dict],
        campaign_id: Optional[int] = None
    ) -> list[dict]:
        """
        여러 블록의 배경을 일괄 선택

        Args:
            blocks: [{"block_id": 1, "keywords": [...], "visual_concept": {...}}, ...]
            campaign_id: 캠페인 ID

        Returns:
            [{"block_id": 1, "background": {...}}, ...]
        """
        results = []

        for block in blocks:
            block_id = block.get("block_id")
            keywords = block.get("keywords")
            visual_concept = block.get("visual_concept")

            try:
                background = await self.select_background(
                    campaign_id=campaign_id,
                    keywords=keywords,
                    visual_concept=visual_concept
                )

                results.append({
                    "block_id": block_id,
                    "success": True,
                    "background": background
                })

            except Exception as e:
                logger.error(f"블록 {block_id} 배경 선택 실패: {e}")
                results.append({
                    "block_id": block_id,
                    "success": False,
                    "error": str(e)
                })

        return results
