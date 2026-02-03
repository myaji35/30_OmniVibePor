"""Storyboard 콘티 블록 자동 생성 API"""
from fastapi import APIRouter, HTTPException, Path
from typing import Optional
import logging

from app.models.storyboard import (
    GenerateStoryboardRequest,
    GenerateStoryboardResponse,
    StoryboardBlock,
    StoryboardBlockUpdate
)
from app.tasks.storyboard_tasks import generate_storyboard_task
from app.agents.director_agent import get_director_graph

router = APIRouter(prefix="/storyboard", tags=["Storyboard"])
logger = logging.getLogger(__name__)


@router.post(
    "/campaigns/{campaign_id}/content/{content_id}/generate",
    response_model=GenerateStoryboardResponse
)
async def generate_storyboard(
    campaign_id: int = Path(..., description="캠페인 ID"),
    content_id: int = Path(..., description="콘텐츠 ID"),
    request: GenerateStoryboardRequest = ...,
    async_mode: bool = True
):
    """
    스크립트로 콘티 블록 자동 생성

    **LangGraph Director Agent가 수행하는 작업:**
    1. 스크립트 의미 분석 및 블록 분할
    2. 각 블록의 핵심 키워드 추출
    3. 비주얼 컨셉 생성 (분위기, 색감, 스타일)
    4. 배경 자동 추천 (AI 생성, 스톡, 단색)
    5. 전환 효과 자동 배정 (감정 변화 고려)

    **Args:**
    - campaign_id: 캠페인 ID
    - content_id: 콘텐츠 ID
    - request.script: 스크립트 전체 텍스트
    - request.campaign_concept: 캠페인 컨셉 (gender, tone, style, platform)
    - request.target_duration: 목표 영상 길이 (초, 15~600)
    - async_mode: 비동기 실행 여부 (True: Celery, False: 동기)

    **Returns:**
    - success: 성공 여부
    - storyboard_blocks: 생성된 콘티 블록 리스트
    - total_blocks: 총 블록 수
    - estimated_duration: 예상 영상 길이 (초)
    """
    logger.info(
        f"Storyboard generation request - "
        f"campaign_id: {campaign_id}, content_id: {content_id}, "
        f"script_length: {len(request.script)}, "
        f"target_duration: {request.target_duration}s, "
        f"async_mode: {async_mode}"
    )

    try:
        if async_mode:
            # Celery 비동기 실행 (권장)
            task = generate_storyboard_task.apply_async(
                kwargs={
                    "campaign_id": campaign_id,
                    "content_id": content_id,
                    "script": request.script,
                    "campaign_concept": request.campaign_concept.model_dump(),
                    "target_duration": request.target_duration
                }
            )

            logger.info(
                f"Storyboard generation task submitted: "
                f"content_id={content_id}, task_id={task.id}"
            )

            return GenerateStoryboardResponse(
                success=True,
                storyboard_blocks=[],
                total_blocks=0,
                estimated_duration=0.0,
                error=f"Task submitted with ID: {task.id}. Use /storyboard/task/{task.id} to check status."
            )

        else:
            # 동기 실행 (테스트용)
            logger.warning(
                f"Synchronous storyboard generation requested for content: {content_id}. "
                f"This may take time. Consider using async_mode=True."
            )

            director_graph = get_director_graph()

            # Initial state 구성
            initial_state = {
                "script": request.script,
                "campaign_concept": request.campaign_concept.model_dump(),
                "target_duration": request.target_duration,
                "keywords": [],
                "visual_concepts": [],
                "storyboard_blocks": [],
                "background_suggestions": [],
                "transition_effects": [],
                "error": None
            }

            # Director Agent 실행
            result = director_graph.invoke(initial_state)

            if result.get("error"):
                raise HTTPException(
                    status_code=500,
                    detail=result["error"]
                )

            # StoryboardBlock 모델로 변환
            storyboard_blocks = [
                StoryboardBlock(**block) for block in result["storyboard_blocks"]
            ]

            # 예상 길이 계산
            estimated_duration = sum(
                block.end_time - block.start_time for block in storyboard_blocks
            )

            return GenerateStoryboardResponse(
                success=True,
                storyboard_blocks=storyboard_blocks,
                total_blocks=len(storyboard_blocks),
                estimated_duration=estimated_duration
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Storyboard generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"콘티 블록 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Celery 작업 상태 조회

    **Args:**
    - task_id: Celery 작업 ID

    **Returns:**
    - status: 작업 상태 (PENDING, STARTED, SUCCESS, FAILURE)
    - result: 작업 결과 (SUCCESS 시)
    - error: 에러 메시지 (FAILURE 시)
    """
    from celery.result import AsyncResult

    try:
        task = AsyncResult(task_id)

        if task.state == "PENDING":
            return {
                "status": "PENDING",
                "message": "작업이 대기 중입니다"
            }
        elif task.state == "STARTED":
            return {
                "status": "STARTED",
                "message": "작업이 실행 중입니다"
            }
        elif task.state == "SUCCESS":
            return {
                "status": "SUCCESS",
                "result": task.result
            }
        elif task.state == "FAILURE":
            return {
                "status": "FAILURE",
                "error": str(task.info)
            }
        else:
            return {
                "status": task.state,
                "message": f"알 수 없는 상태: {task.state}"
            }

    except Exception as e:
        logger.error(f"Task status retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"작업 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/campaigns/{campaign_id}/content/{content_id}/blocks",
    response_model=GenerateStoryboardResponse
)
async def get_storyboard_blocks(
    campaign_id: int = Path(..., description="캠페인 ID"),
    content_id: int = Path(..., description="콘텐츠 ID")
):
    """
    저장된 콘티 블록 조회

    **Args:**
    - campaign_id: 캠페인 ID
    - content_id: 콘텐츠 ID

    **Returns:**
    - storyboard_blocks: 콘티 블록 리스트
    """
    logger.info(f"Retrieving storyboard blocks - content_id: {content_id}")

    try:
        # TODO: SQLite/Neo4j에서 저장된 블록 조회
        # 현재는 빈 리스트 반환
        return GenerateStoryboardResponse(
            success=True,
            storyboard_blocks=[],
            total_blocks=0,
            estimated_duration=0.0,
            error="데이터베이스 연동 미구현"
        )

    except Exception as e:
        logger.error(f"Storyboard retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"콘티 블록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put(
    "/campaigns/{campaign_id}/content/{content_id}/blocks/{block_id}",
    response_model=StoryboardBlock
)
async def update_storyboard_block(
    campaign_id: int = Path(..., description="캠페인 ID"),
    content_id: int = Path(..., description="콘텐츠 ID"),
    block_id: int = Path(..., description="블록 ID"),
    update: StoryboardBlockUpdate = ...
):
    """
    콘티 블록 수정

    **Args:**
    - campaign_id: 캠페인 ID
    - content_id: 콘텐츠 ID
    - block_id: 블록 ID
    - update: 수정할 필드

    **Returns:**
    - 수정된 블록 정보
    """
    logger.info(f"Updating storyboard block - block_id: {block_id}")

    try:
        # TODO: SQLite/Neo4j에서 블록 업데이트
        raise HTTPException(
            status_code=501,
            detail="블록 수정 기능은 아직 구현되지 않았습니다"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Block update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"블록 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete(
    "/campaigns/{campaign_id}/content/{content_id}/blocks/{block_id}"
)
async def delete_storyboard_block(
    campaign_id: int = Path(..., description="캠페인 ID"),
    content_id: int = Path(..., description="콘텐츠 ID"),
    block_id: int = Path(..., description="블록 ID")
):
    """
    콘티 블록 삭제

    **Args:**
    - campaign_id: 캠페인 ID
    - content_id: 콘텐츠 ID
    - block_id: 블록 ID

    **Returns:**
    - success: 성공 여부
    """
    logger.info(f"Deleting storyboard block - block_id: {block_id}")

    try:
        # TODO: SQLite/Neo4j에서 블록 삭제
        raise HTTPException(
            status_code=501,
            detail="블록 삭제 기능은 아직 구현되지 않았습니다"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Block deletion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"블록 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Storyboard API 상태 확인
    """
    try:
        director_graph = get_director_graph()
        return {
            "status": "healthy",
            "message": "Storyboard API is ready",
            "director_agent": {
                "engine": "LangGraph",
                "llm": "GPT-4",
                "features": [
                    "스크립트 의미 분석",
                    "키워드 추출",
                    "비주얼 컨셉 생성",
                    "배경 자동 추천",
                    "전환 효과 배정"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }
