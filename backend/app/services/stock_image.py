"""
Unsplash 스톡 이미지 검색 서비스
무료 고품질 스톡 이미지 검색 및 다운로드
"""
import os
import logging
from typing import Optional
import httpx
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


class StockImageService:
    """Unsplash 스톡 이미지 검색 서비스"""

    def __init__(self, access_key: Optional[str] = None):
        """
        Args:
            access_key: Unsplash Access Key (없으면 환경변수에서 로드)
        """
        self.access_key = access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.base_url = "https://api.unsplash.com"

        if not self.access_key:
            logger.warning("UNSPLASH_ACCESS_KEY가 설정되지 않았습니다")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    async def search_images(
        self,
        query: str,
        per_page: int = 10,
        orientation: str = "landscape",
        page: int = 1
    ) -> list[dict]:
        """
        Unsplash에서 이미지 검색

        Args:
            query: 검색 키워드 (영문)
            per_page: 결과 개수 (최대 30)
            orientation: landscape | portrait | squarish
            page: 페이지 번호

        Returns:
            [
                {
                    "id": "abc123",
                    "description": "Modern office workspace",
                    "url_regular": "https://images.unsplash.com/...",
                    "url_full": "https://images.unsplash.com/...",
                    "width": 1920,
                    "height": 1080,
                    "photographer": "John Doe",
                    "photographer_url": "https://unsplash.com/@johndoe",
                    "download_location": "https://api.unsplash.com/photos/abc123/download"
                },
                ...
            ]

        Raises:
            Exception: API 호출 실패 시
        """
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY가 설정되지 않았습니다")

        try:
            logger.info(f"Unsplash 검색 시작: {query}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search/photos",
                    params={
                        "query": query,
                        "per_page": min(per_page, 30),  # 최대 30개
                        "orientation": orientation,
                        "page": page,
                        "client_id": self.access_key
                    },
                    timeout=10.0
                )

                response.raise_for_status()
                data = response.json()

                results = [
                    {
                        "id": photo['id'],
                        "description": photo.get('description') or photo.get('alt_description') or "No description",
                        "url_regular": photo['urls']['regular'],
                        "url_full": photo['urls']['full'],
                        "url_thumb": photo['urls']['thumb'],
                        "width": photo['width'],
                        "height": photo['height'],
                        "photographer": photo['user']['name'],
                        "photographer_url": photo['user']['links']['html'],
                        "download_location": photo['links']['download_location']
                    }
                    for photo in data['results']
                ]

                logger.info(f"Unsplash 검색 완료: {len(results)}개 결과")
                return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Unsplash API 오류: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unsplash 검색 실패: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    async def download_and_upload(
        self,
        unsplash_url: str,
        photo_id: Optional[str] = None,
        download_location: Optional[str] = None
    ) -> str:
        """
        Unsplash 이미지를 Cloudinary에 업로드

        Args:
            unsplash_url: Unsplash 이미지 URL
            photo_id: Unsplash 사진 ID (다운로드 추적용)
            download_location: 다운로드 추적 엔드포인트

        Returns:
            Cloudinary URL (https://res.cloudinary.com/...)

        Raises:
            Exception: 업로드 실패 시
        """
        try:
            logger.info(f"Unsplash 이미지 다운로드 & 업로드 시작: {photo_id or unsplash_url[:50]}")

            # Unsplash 다운로드 추적 (API 정책 준수)
            if download_location:
                await self._trigger_download(download_location)

            # Cloudinary에 업로드
            result = cloudinary.uploader.upload(
                unsplash_url,
                folder="backgrounds/stock",
                resource_type="image",
                tags=["unsplash", "stock", "background"]
            )

            logger.info(f"Cloudinary 업로드 완료: {result['secure_url']}")
            return result['secure_url']

        except Exception as e:
            logger.error(f"Unsplash 이미지 업로드 실패: {e}")
            raise

    async def _trigger_download(self, download_location: str):
        """
        Unsplash 다운로드 이벤트 트리거 (API 정책 필수)
        """
        try:
            async with httpx.AsyncClient() as client:
                await client.get(
                    download_location,
                    params={"client_id": self.access_key},
                    timeout=5.0
                )
                logger.debug("Unsplash 다운로드 이벤트 트리거 완료")
        except Exception as e:
            logger.warning(f"Unsplash 다운로드 이벤트 실패 (무시): {e}")

    async def get_random_image(
        self,
        query: Optional[str] = None,
        orientation: str = "landscape"
    ) -> dict:
        """
        랜덤 이미지 1개 가져오기

        Args:
            query: 검색 키워드 (선택)
            orientation: landscape | portrait | squarish

        Returns:
            search_images()와 동일한 형식의 dict 1개
        """
        try:
            logger.info(f"Unsplash 랜덤 이미지 요청: {query or 'all'}")

            async with httpx.AsyncClient() as client:
                params = {
                    "orientation": orientation,
                    "client_id": self.access_key
                }
                if query:
                    params["query"] = query

                response = await client.get(
                    f"{self.base_url}/photos/random",
                    params=params,
                    timeout=10.0
                )

                response.raise_for_status()
                photo = response.json()

                return {
                    "id": photo['id'],
                    "description": photo.get('description') or photo.get('alt_description') or "No description",
                    "url_regular": photo['urls']['regular'],
                    "url_full": photo['urls']['full'],
                    "url_thumb": photo['urls']['thumb'],
                    "width": photo['width'],
                    "height": photo['height'],
                    "photographer": photo['user']['name'],
                    "photographer_url": photo['user']['links']['html'],
                    "download_location": photo['links']['download_location']
                }

        except Exception as e:
            logger.error(f"Unsplash 랜덤 이미지 실패: {e}")
            raise
