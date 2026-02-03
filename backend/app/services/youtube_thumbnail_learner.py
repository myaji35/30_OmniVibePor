"""유튜브 썸네일 + 카피 AI 학습 모듈 (영상 성과 기반)"""
import asyncio
import logging
from typing import List, Dict, Optional
import requests
from io import BytesIO
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# Logfire는 optional
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()


class YouTubeThumbnailLearner:
    """조회수, CTR, 인게이지먼트 기반 고성과 썸네일 + 타이틀 패턴 학습"""

    def __init__(self, pinecone_index):
        self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        self.pinecone = pinecone_index
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)

        # CLIP 모델 (이미지-텍스트 임베딩)
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    async def collect_top_performing_videos(
        self,
        query: str,
        min_views: int = 100000,
        max_results: int = 50
    ) -> List[Dict]:
        """특정 키워드의 고성과 영상 데이터 수집"""
        with self.logger.span("youtube.collect_videos"):
            try:
                # 1. 검색 (조회수 순)
                search_response = self.youtube.search().list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="viewCount",
                    maxResults=max_results,
                    relevanceLanguage="ko"
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

                # 2. 상세 통계 조회
                videos_response = self.youtube.videos().list(
                    part="statistics,snippet",
                    id=','.join(video_ids)
                ).execute()

                videos_data = []
                for item in videos_response.get('items', []):
                    stats = item['statistics']
                    snippet = item['snippet']

                    view_count = int(stats.get('viewCount', 0))
                    if view_count < min_views:
                        continue

                    # CTR 추정 (좋아요 + 댓글) / 조회수
                    likes = int(stats.get('likeCount', 0))
                    comments = int(stats.get('commentCount', 0))
                    engagement_rate = (likes + comments) / view_count if view_count > 0 else 0

                    videos_data.append({
                        'video_id': item['id'],
                        'title': snippet['title'],
                        'description': snippet['description'][:500],
                        'thumbnail_url': snippet['thumbnails']['high']['url'],
                        'views': view_count,
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': engagement_rate,
                        'channel_title': snippet.get('channelTitle', '')
                    })

                self.logger.info(f"Collected {len(videos_data)} videos for '{query}'")
                return videos_data

            except HttpError as e:
                self.logger.error(f"YouTube API error: {e}")
                return []

    async def analyze_thumbnail_patterns(self, thumbnail_url: str) -> Dict:
        """썸네일 이미지 분석 (색상, 레이아웃, 텍스트 비율 등)"""
        with self.logger.span("thumbnail.analyze_patterns"):
            # 이미지 다운로드
            response = requests.get(thumbnail_url)
            image = Image.open(BytesIO(response.content))

            # 색상 분석
            colors = image.getcolors(maxcolors=1000000)
            dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]

            # 밝기 분석
            grayscale = image.convert('L')
            brightness = sum(grayscale.getdata()) / (grayscale.width * grayscale.height)

            # TODO: OCR로 텍스트 비율 분석 (EasyOCR 또는 Tesseract)
            # TODO: 얼굴 감지 (OpenCV 또는 Face Recognition)

            return {
                'dominant_colors': [rgb for count, rgb in dominant_colors[:3]],
                'brightness': brightness,
                'resolution': f"{image.width}x{image.height}",
                'aspect_ratio': image.width / image.height
            }

    async def embed_thumbnail(self, thumbnail_url: str) -> List[float]:
        """CLIP으로 썸네일 이미지 임베딩"""
        with self.logger.span("clip.embed_image"):
            response = requests.get(thumbnail_url)
            image = Image.open(BytesIO(response.content))

            inputs = self.clip_processor(images=image, return_tensors="pt")
            with torch.no_grad():
                embedding = self.clip_model.get_image_features(**inputs)

            return embedding.cpu().numpy().tolist()[0]

    async def embed_text(self, text: str) -> List[float]:
        """CLIP으로 타이틀/카피 텍스트 임베딩"""
        with self.logger.span("clip.embed_text"):
            inputs = self.clip_processor(text=text, return_tensors="pt", padding=True)
            with torch.no_grad():
                embedding = self.clip_model.get_text_features(**inputs)

            return embedding.cpu().numpy().tolist()[0]

    async def store_in_pinecone(self, videos_data: List[Dict]):
        """Pinecone에 썸네일 + 타이틀 임베딩 저장"""
        with self.logger.span("pinecone.upsert"):
            vectors = []

            for video in videos_data:
                # 썸네일 임베딩
                thumbnail_embedding = await self.embed_thumbnail(video['thumbnail_url'])

                # 패턴 분석
                patterns = await self.analyze_thumbnail_patterns(video['thumbnail_url'])

                # 메타데이터 구성
                metadata = {
                    'video_id': video['video_id'],
                    'title': video['title'],
                    'description': video['description'],
                    'views': video['views'],
                    'engagement_rate': video['engagement_rate'],
                    'thumbnail_url': video['thumbnail_url'],
                    'channel': video['channel_title'],
                    **patterns  # 색상, 밝기 등
                }

                vectors.append((
                    f"thumb_{video['video_id']}",
                    thumbnail_embedding,
                    metadata
                ))

            # Pinecone에 배치 업로드
            self.pinecone.upsert(vectors=vectors)
            self.logger.info(f"Stored {len(vectors)} thumbnails in Pinecone")

    async def find_similar_successful_thumbnails(
        self,
        query_text: str,
        min_views: int = 100000,
        top_k: int = 10
    ) -> List[Dict]:
        """텍스트 기반 유사 고성과 썸네일 검색"""
        with self.logger.span("pinecone.query"):
            # 텍스트를 CLIP 임베딩으로 변환
            text_embedding = await self.embed_text(query_text)

            # Pinecone 검색 (조회수 필터 적용)
            results = self.pinecone.query(
                vector=text_embedding,
                top_k=top_k,
                filter={"views": {"$gte": min_views}},
                include_metadata=True
            )

            return [
                {
                    'video_id': match['metadata']['video_id'],
                    'title': match['metadata']['title'],
                    'thumbnail_url': match['metadata']['thumbnail_url'],
                    'views': match['metadata']['views'],
                    'engagement_rate': match['metadata']['engagement_rate'],
                    'similarity_score': match['score'],
                    'patterns': {
                        'dominant_colors': match['metadata'].get('dominant_colors', []),
                        'brightness': match['metadata'].get('brightness', 0)
                    }
                }
                for match in results['matches']
            ]

    async def generate_optimized_thumbnail_prompt(
        self,
        script: str,
        user_persona: Dict
    ) -> str:
        """학습된 패턴 기반 DALL-E 3 프롬프트 생성"""
        with self.logger.span("generate.thumbnail_prompt"):
            # 1. 스크립트에서 키워드 추출
            keywords = await self._extract_keywords(script)

            # 2. 유사 고성과 썸네일 검색
            similar_thumbs = await self.find_similar_successful_thumbnails(
                query_text=keywords,
                top_k=5
            )

            # 3. 패턴 집계
            avg_brightness = sum(t['patterns']['brightness'] for t in similar_thumbs) / len(similar_thumbs)
            common_colors = self._aggregate_colors([t['patterns']['dominant_colors'] for t in similar_thumbs])

            # 4. DALL-E 프롬프트 생성
            prompt = f"""
Create a high-performing YouTube thumbnail image:

Topic: {keywords}
Style: {user_persona.get('style', 'professional')}
Target audience: {user_persona.get('gender', 'general')} audience

Visual guidelines based on {len(similar_thumbs)} top-performing thumbnails:
- Color palette: {common_colors}
- Brightness level: {'bright' if avg_brightness > 128 else 'balanced'}
- Include bold text overlay
- High contrast and eye-catching composition

Reference successful examples:
{chr(10).join(f"- {t['title']} ({t['views']:,} views)" for t in similar_thumbs[:3])}
"""

            return prompt.strip()

    async def generate_optimized_captions(
        self,
        script: str,
        similar_videos: List[Dict]
    ) -> List[str]:
        """고성과 영상 타이틀 패턴 기반 카피 생성"""
        with self.logger.span("generate.captions"):
            # 성과 좋은 타이틀들 분석
            top_titles = [v['title'] for v in similar_videos[:10]]

            system_prompt = f"""
당신은 유튜브 SEO 전문가입니다. 다음 고성과 타이틀 패턴을 학습하세요:

{chr(10).join(f"- {title}" for title in top_titles)}

이 패턴들의 공통점:
1. 클릭을 유도하는 키워드
2. 숫자 또는 리스트 형식
3. 감정적 트리거 (궁금증, 긴급성)
"""

            user_prompt = f"""
다음 스크립트를 기반으로 3가지 카피 문구를 작성하세요:
{script[:500]}

요구사항:
- 각 40자 이내
- 위 고성과 패턴 적용
- 이모지 포함 (선택)
"""

            response = self.openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                n=3
            )

            return [choice.message.content.strip() for choice in response.choices]

    # 헬퍼 메서드들
    async def _extract_keywords(self, text: str) -> str:
        """GPT로 키워드 추출"""
        response = self.openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract 3-5 key keywords from this text."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def _aggregate_colors(self, color_lists: List[List]) -> str:
        """색상 집계 (가장 빈번한 색상)"""
        # 간단한 구현: 첫 번째 리스트의 색상 반환
        if color_lists and color_lists[0]:
            return f"RGB{tuple(color_lists[0][0])}"
        return "vibrant colors"
