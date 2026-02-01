"""썸네일 학습 API 엔드포인트"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List

from app.services.youtube_thumbnail_learner import YouTubeThumbnailLearner
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# TODO: Pinecone 초기화 (별도 모듈로 분리 예정)
# pinecone_index = ...
# thumbnail_learner = YouTubeThumbnailLearner(pinecone_index)


class LearnRequest(BaseModel):
    """학습 요청 모델"""
    query: str
    min_views: int = 100000
    max_results: int = 50


class GenerateRequest(BaseModel):
    """썸네일 + 카피 생성 요청"""
    script: str
    persona: dict = {
        "gender": "female",
        "style": "professional",
        "tone": "friendly"
    }


@router.post("/learn")
async def learn_from_youtube(
    request: LearnRequest,
    background_tasks: BackgroundTasks
):
    """
    유튜브 고성과 영상의 썸네일 + 타이틀 패턴 학습

    - **query**: 검색 키워드 (예: "AI 트렌드 2026")
    - **min_views**: 최소 조회수 (기본 100,000)
    - **max_results**: 최대 수집 영상 수 (기본 50)
    """
    try:
        with logger.span("api.learn_thumbnails"):
            # TODO: Pinecone 초기화 후 주석 해제
            # learner = YouTubeThumbnailLearner(pinecone_index)

            # 1. 고성과 영상 수집
            # videos = await learner.collect_top_performing_videos(
            #     query=request.query,
            #     min_views=request.min_views,
            #     max_results=request.max_results
            # )

            # 2. 백그라운드에서 Pinecone 저장
            # background_tasks.add_task(learner.store_in_pinecone, videos)

            return {
                "status": "learning_started",
                "query": request.query,
                "message": "Pinecone 초기화 필요 - 구현 예정"
                # "collected_videos": len(videos),
                # "message": f"{len(videos)}개 영상 데이터 수집 완료. 백그라운드에서 학습 중..."
            }

    except Exception as e:
        logger.error(f"Learning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_thumbnail_and_caption(request: GenerateRequest):
    """
    학습된 패턴 기반 썸네일 + 카피 생성

    - **script**: 영상 스크립트
    - **persona**: 사용자 페르소나 (성별, 스타일, 톤)
    """
    try:
        with logger.span("api.generate_assets"):
            # TODO: Pinecone 초기화 후 주석 해제
            # learner = YouTubeThumbnailLearner(pinecone_index)

            # 1. DALL-E 프롬프트 생성
            # thumbnail_prompt = await learner.generate_optimized_thumbnail_prompt(
            #     script=request.script,
            #     user_persona=request.persona
            # )

            # 2. 유사 영상 검색
            # keywords = await learner._extract_keywords(request.script)
            # similar_videos = await learner.find_similar_successful_thumbnails(keywords)

            # 3. 카피 생성
            # captions = await learner.generate_optimized_captions(
            #     script=request.script,
            #     similar_videos=similar_videos
            # )

            return {
                "status": "generation_pending",
                "message": "Pinecone 초기화 필요 - 구현 예정"
                # "thumbnail_prompt": thumbnail_prompt,
                # "captions": captions,
                # "similar_videos_count": len(similar_videos)
            }

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_similar_thumbnails(query: str, top_k: int = 10):
    """
    텍스트 기반 유사 고성과 썸네일 검색

    - **query**: 검색 키워드
    - **top_k**: 반환할 결과 수 (기본 10)
    """
    try:
        with logger.span("api.search_thumbnails"):
            # TODO: Pinecone 초기화 후 주석 해제
            # learner = YouTubeThumbnailLearner(pinecone_index)
            # results = await learner.find_similar_successful_thumbnails(query, top_k=top_k)

            return {
                "status": "search_pending",
                "query": query,
                "message": "Pinecone 초기화 필요 - 구현 예정"
                # "results": results
            }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
