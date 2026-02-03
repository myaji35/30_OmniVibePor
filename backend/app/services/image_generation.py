"""
DALL-E 3 이미지 생성 서비스
배경 이미지 자동 생성 및 Cloudinary 업로드
"""
import os
import logging
from typing import Optional
from openai import OpenAI
import cloudinary
import cloudinary.uploader
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Cloudinary 초기화
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


class ImageGenerationService:
    """DALL-E 3 기반 AI 이미지 생성 서비스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API Key (없으면 환경변수에서 로드)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_background_image(
        self,
        prompt: str,
        style: str = "natural",
        size: str = "1024x1024"
    ) -> dict:
        """
        DALL-E 3로 배경 이미지 생성 후 Cloudinary에 업로드

        Args:
            prompt: 이미지 프롬프트 (영문)
            style: natural | vivid (자연스러움 vs 생동감)
            size: 1024x1024 | 1792x1024 | 1024x1792

        Returns:
            {
                "success": True,
                "image_url": "https://res.cloudinary.com/...",
                "prompt": "Modern tech background...",
                "dall_e_url": "https://oaidalleapi...",
                "width": 1024,
                "height": 1024
            }

        Raises:
            Exception: DALL-E 생성 또는 업로드 실패 시
        """
        try:
            logger.info(f"DALL-E 이미지 생성 시작: {prompt[:50]}...")

            # 1. DALL-E 3 이미지 생성
            enhanced_prompt = self._enhance_prompt(prompt)

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,
                quality="hd",
                style=style,
                n=1
            )

            dall_e_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            logger.info(f"DALL-E 생성 완료: {dall_e_url}")

            # 2. Cloudinary에 업로드 (영구 저장)
            cloudinary_result = cloudinary.uploader.upload(
                dall_e_url,
                folder="backgrounds/ai_generated",
                resource_type="image",
                tags=["dall-e", "background", "ai-generated"]
            )

            logger.info(f"Cloudinary 업로드 완료: {cloudinary_result['secure_url']}")

            return {
                "success": True,
                "image_url": cloudinary_result['secure_url'],
                "prompt": prompt,
                "revised_prompt": revised_prompt,
                "dall_e_url": dall_e_url,
                "width": cloudinary_result['width'],
                "height": cloudinary_result['height'],
                "cloudinary_public_id": cloudinary_result['public_id']
            }

        except Exception as e:
            logger.error(f"DALL-E 이미지 생성 실패: {e}")
            raise

    async def optimize_prompt_for_dalle(
        self,
        keywords: list[str],
        visual_concept: dict
    ) -> str:
        """
        키워드 + 비주얼 컨셉 → DALL-E 최적화 프롬프트 변환

        Args:
            keywords: ["AI", "technology", "future"]
            visual_concept: {"mood": "energetic", "color_tone": "bright"}

        Returns:
            "Futuristic AI technology workspace, bright neon colors,
             energetic atmosphere, professional photography,
             high contrast, cinematic lighting"
        """
        system_prompt = """당신은 DALL-E 프롬프트 전문가입니다.
주어진 키워드와 비주얼 컨셉을 DALL-E에 최적화된 영문 프롬프트로 변환하세요.

규칙:
1. 50단어 이내
2. 구체적인 시각적 요소 포함
3. 스타일 키워드 포함 (cinematic, professional, high quality 등)
4. 색감, 조명, 분위기 명시
5. 불필요한 텍스트나 문자 제외

좋은 예:
"Modern minimalist workspace with soft natural lighting, pastel color palette,
 professional photography, clean composition, high quality, 8k resolution"

나쁜 예:
"office" (너무 간략함)
"""

        user_input = f"""키워드: {', '.join(keywords)}
비주얼 컨셉: {visual_concept}

위 정보를 바탕으로 DALL-E 프롬프트를 생성하세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=100,
                temperature=0.7
            )

            optimized_prompt = response.choices[0].message.content.strip()
            logger.info(f"프롬프트 최적화 완료: {optimized_prompt}")

            return optimized_prompt

        except Exception as e:
            logger.warning(f"프롬프트 최적화 실패, 기본 프롬프트 사용: {e}")
            # Fallback: 간단한 조합
            return f"{' '.join(keywords)}, {visual_concept.get('mood', 'professional')}, high quality"

    def _enhance_prompt(self, prompt: str) -> str:
        """
        프롬프트에 기본 스타일 키워드 추가
        """
        base_style = "professional photography, high quality, cinematic"

        if "photography" not in prompt.lower() and "cinematic" not in prompt.lower():
            return f"{prompt}, {base_style}"

        return prompt

    async def generate_from_keywords(
        self,
        keywords: list[str],
        visual_concept: dict,
        style: str = "natural"
    ) -> dict:
        """
        키워드만으로 전체 파이프라인 실행

        Args:
            keywords: 키워드 리스트
            visual_concept: 비주얼 컨셉
            style: DALL-E 스타일

        Returns:
            generate_background_image()와 동일
        """
        # 1. 프롬프트 최적화
        optimized_prompt = await self.optimize_prompt_for_dalle(
            keywords, visual_concept
        )

        # 2. 이미지 생성
        result = await self.generate_background_image(
            prompt=optimized_prompt,
            style=style
        )

        return result
