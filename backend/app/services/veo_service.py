"""Google Veo API Service - AI 영상 생성

REALPLAN.md Phase 4.1 구현

기능:
- 텍스트 프롬프트 → 시네마틱 영상 생성
- 캐릭터 레퍼런스 이미지 지원
- 영상 스타일 커스터마이징
- 생성 상태 추적
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import nullcontext

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class VeoService:
    """
    Google Veo API 서비스

    특징:
    - 최대 1080p HD 영상 생성
    - 다양한 스타일 (cinematic, realistic, animated)
    - 캐릭터 일관성 유지
    - 비용: ~$0.10/영상 (5초 기준)
    """

    # Veo 영상 스타일 옵션
    STYLES = {
        "cinematic": "Cinematic, professional lighting, depth of field",
        "realistic": "Photorealistic, natural lighting, 4K quality",
        "animated": "3D animated, colorful, stylized",
        "documentary": "Documentary style, natural, handheld camera",
        "commercial": "Commercial advertising style, bright, polished"
    }

    # 영상 길이 옵션 (초)
    DURATIONS = [3, 5, 10, 15, 30]

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "./outputs/videos"
    ):
        """
        Args:
            api_key: Google Veo API 키 (없으면 설정에서 가져옴)
            output_dir: 생성된 영상 저장 경로
        """
        self.api_key = api_key or settings.GOOGLE_VEO_API_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Google Veo API 엔드포인트
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=120.0,
            headers={
                "Content-Type": "application/json"
            }
        )

        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        style: str = "cinematic",
        reference_image: Optional[str] = None,
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> Dict:
        """
        텍스트 프롬프트로 영상 생성

        Args:
            prompt: 영상 생성 프롬프트
            duration: 영상 길이 (초, 3/5/10/15/30)
            style: 영상 스타일
            reference_image: 캐릭터 레퍼런스 이미지 URL 또는 경로
            aspect_ratio: 화면 비율 (16:9, 9:16, 1:1)
            **kwargs: 추가 파라미터

        Returns:
            {
                "job_id": "작업 ID",
                "status": "queued" | "processing" | "completed" | "failed",
                "video_url": "생성된 영상 URL (완료 시)",
                "estimated_time": 예상 대기 시간 (초)
            }
        """
        span_context = logfire.span("veo.generate_video") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context as span:
            # 1. 프롬프트 강화
            enhanced_prompt = self._enhance_prompt(prompt, style)

            # 2. API 요청 데이터
            request_data = {
                "prompt": enhanced_prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "output_format": "mp4"
            }

            # 캐릭터 레퍼런스 추가
            if reference_image:
                request_data["reference_image"] = reference_image
                request_data["character_consistency"] = True

            self.logger.info(
                f"Generating video with Veo: {duration}s, style={style}, "
                f"aspect_ratio={aspect_ratio}"
            )

            # Logfire 속성
            if LOGFIRE_AVAILABLE:
                span.set_attribute("prompt_length", len(prompt))
                span.set_attribute("duration", duration)
                span.set_attribute("style", style)
                span.set_attribute("has_reference", bool(reference_image))

            try:
                # 3. Google Veo API 호출
                response = await self.client.post(
                    "/models/veo:generate",
                    json=request_data,
                    params={"key": self.api_key}
                )
                response.raise_for_status()

                result = response.json()

                # 4. 응답 처리
                job_id = result.get("name", "")  # e.g., "operations/abc123"

                self.logger.info(f"Veo video generation started: job_id={job_id}")

                return {
                    "job_id": job_id,
                    "status": "queued",
                    "video_url": None,
                    "estimated_time": duration * 10,  # 대략 10배 소요
                    "prompt": enhanced_prompt
                }

            except httpx.HTTPStatusError as e:
                self.logger.error(f"Veo API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                self.logger.error(f"Veo video generation failed: {e}")
                raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30)
    )
    async def check_status(self, job_id: str) -> Dict:
        """
        영상 생성 상태 확인

        Args:
            job_id: 작업 ID

        Returns:
            {
                "status": "queued" | "processing" | "completed" | "failed",
                "video_url": "생성된 영상 URL (완료 시)",
                "progress": 진행률 (0-100),
                "error": 에러 메시지 (실패 시)
            }
        """
        try:
            response = await self.client.get(
                f"/{job_id}",
                params={"key": self.api_key}
            )
            response.raise_for_status()

            result = response.json()

            # 상태 파싱
            done = result.get("done", False)

            if done:
                if "error" in result:
                    return {
                        "status": "failed",
                        "video_url": None,
                        "progress": 100,
                        "error": result["error"].get("message", "Unknown error")
                    }
                else:
                    # 성공
                    video_data = result.get("response", {}).get("video", {})
                    video_url = video_data.get("uri", "")

                    return {
                        "status": "completed",
                        "video_url": video_url,
                        "progress": 100,
                        "error": None
                    }
            else:
                # 진행 중
                metadata = result.get("metadata", {})
                progress = metadata.get("progressPercentage", 0)

                return {
                    "status": "processing",
                    "video_url": None,
                    "progress": progress,
                    "error": None
                }

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Status check error: {e.response.status_code}")
            raise
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            raise

    async def download_video(self, video_url: str, filename: str) -> Path:
        """
        생성된 영상 다운로드

        Args:
            video_url: 영상 URL
            filename: 저장할 파일명

        Returns:
            저장된 파일 경로
        """
        output_path = self.output_dir / filename

        self.logger.info(f"Downloading video from {video_url} to {output_path}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(video_url)
                response.raise_for_status()

                # 파일 저장
                output_path.write_bytes(response.content)

                self.logger.info(f"Video downloaded: {output_path} ({len(response.content)} bytes)")

                return output_path

        except Exception as e:
            self.logger.error(f"Video download failed: {e}")
            raise

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """
        프롬프트에 스타일 지시어 추가

        Args:
            prompt: 기본 프롬프트
            style: 스타일 키

        Returns:
            강화된 프롬프트
        """
        style_directive = self.STYLES.get(style, self.STYLES["cinematic"])

        enhanced = f"{prompt}. {style_directive}"

        self.logger.debug(f"Enhanced prompt: {enhanced}")

        return enhanced

    async def generate_from_script_section(
        self,
        section_text: str,
        section_type: str,
        duration: int,
        character_reference: Optional[str] = None
    ) -> Dict:
        """
        스크립트 섹션에서 영상 프롬프트 자동 생성 및 영상 생성

        Args:
            section_text: 섹션 텍스트 (훅/본문/CTA)
            section_type: 섹션 유형 ("hook", "body", "cta")
            duration: 영상 길이 (초)
            character_reference: 캐릭터 레퍼런스 이미지

        Returns:
            generate_video() 결과
        """
        # 섹션 유형별 기본 프롬프트
        prompts = {
            "hook": "Modern studio setting, friendly female presenter looking at camera, bright professional lighting, shallow depth of field",
            "body": "Professional presenter explaining concept, engaging hand gestures, well-lit studio background, medium shot",
            "cta": "Presenter smiling and gesturing towards call-to-action text, warm lighting, close-up shot"
        }

        base_prompt = prompts.get(section_type, prompts["body"])

        self.logger.info(f"Generating video for {section_type}: {section_text[:50]}...")

        return await self.generate_video(
            prompt=base_prompt,
            duration=duration,
            style="commercial",
            reference_image=character_reference,
            aspect_ratio="16:9"
        )

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()


# ==================== 싱글톤 인스턴스 ====================

_veo_service: Optional[VeoService] = None


def get_veo_service() -> VeoService:
    """
    VeoService 싱글톤 인스턴스

    Returns:
        VeoService 인스턴스
    """
    global _veo_service
    if _veo_service is None:
        _veo_service = VeoService()
    return _veo_service
