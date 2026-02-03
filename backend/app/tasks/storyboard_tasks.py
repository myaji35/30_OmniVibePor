"""Celery 콘티 블록 자동 생성 작업"""
import logging
from typing import Dict, Any, List
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.agents.director_agent import get_director_graph
from app.models.storyboard import StoryboardBlock

logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_storyboard_blocks",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes timeout
    soft_time_limit=540,  # 9 minutes soft timeout
    priority=5,
    track_started=True,
    acks_late=True,
    reject_on_worker_lost=True
)
def generate_storyboard_task(
    self,
    campaign_id: int,
    content_id: int,
    script: str,
    campaign_concept: Dict[str, str],
    target_duration: int = 180
) -> Dict[str, Any]:
    """
    콘티 블록 자동 생성 (비동기)

    **LangGraph Director Agent 워크플로우:**
    1. analyze_script: 스크립트 의미 분석 및 블록 분할
    2. extract_keywords: 각 블록의 핵심 키워드 추출
    3. generate_visual_concepts: 비주얼 컨셉 생성
    4. suggest_backgrounds: 배경 자동 추천
    5. assign_transitions: 전환 효과 자동 배정

    Args:
        campaign_id: 캠페인 ID
        content_id: 콘텐츠 ID
        script: 스크립트 전체 텍스트
        campaign_concept: 캠페인 컨셉 딕셔너리
            - gender: 성별 (male, female, neutral)
            - tone: 톤 (professional, casual, energetic, calm)
            - style: 스타일 (modern, classic, creative, formal)
            - platform: 플랫폼 (YouTube, Instagram, TikTok)
        target_duration: 목표 영상 길이 (초)

    Returns:
        {
            "success": bool,
            "campaign_id": int,
            "content_id": int,
            "storyboard_blocks": List[Dict],
            "total_blocks": int,
            "estimated_duration": float,
            "task_id": str,
            "error": str (실패 시)
        }
    """
    logger.info(
        f"Starting storyboard generation task - "
        f"campaign_id: {campaign_id}, content_id: {content_id}, "
        f"script_length: {len(script)}, target_duration: {target_duration}s, "
        f"task_id: {self.request.id}"
    )

    try:
        # Director Agent 가져오기
        director_graph = get_director_graph()

        # Initial state 구성
        initial_state = {
            "script": script,
            "campaign_concept": campaign_concept,
            "target_duration": target_duration,
            "keywords": [],
            "visual_concepts": [],
            "storyboard_blocks": [],
            "background_suggestions": [],
            "transition_effects": [],
            "error": None
        }

        # Director Agent 실행
        logger.info(f"Executing Director Agent for content_id: {content_id}")
        result = director_graph.invoke(initial_state)

        if result.get("error"):
            raise Exception(result["error"])

        storyboard_blocks = result["storyboard_blocks"]
        total_blocks = len(storyboard_blocks)
        estimated_duration = sum(
            block["end_time"] - block["start_time"]
            for block in storyboard_blocks
        )

        logger.info(
            f"Director Agent completed - "
            f"content_id: {content_id}, total_blocks: {total_blocks}, "
            f"estimated_duration: {estimated_duration:.1f}s"
        )

        # SQLite/Neo4j에 저장
        try:
            _save_storyboard_blocks(content_id, storyboard_blocks)
            logger.info(f"Storyboard blocks saved to database - content_id: {content_id}")
        except Exception as e:
            logger.warning(f"Failed to save storyboard blocks to database: {e}")
            # 저장 실패는 치명적이지 않으므로 계속 진행

        # 배경 이미지 생성 작업 트리거 (옵션)
        for block in storyboard_blocks:
            if block.get("background_type") == "ai_generated" and block.get("background_prompt"):
                try:
                    # TODO: 배경 이미지 생성 Celery 작업 트리거
                    # generate_background_image_task.delay(
                    #     content_id=content_id,
                    #     block_id=block["id"],
                    #     prompt=block["background_prompt"]
                    # )
                    logger.debug(
                        f"Background image generation queued - "
                        f"block_order: {block['order']}, prompt: {block['background_prompt']}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to queue background generation: {e}")

        result_data = {
            "success": True,
            "campaign_id": campaign_id,
            "content_id": content_id,
            "storyboard_blocks": storyboard_blocks,
            "total_blocks": total_blocks,
            "estimated_duration": estimated_duration,
            "task_id": self.request.id
        }

        logger.info(
            f"Storyboard generation completed - "
            f"content_id: {content_id}, total_blocks: {total_blocks}"
        )

        return result_data

    except Exception as e:
        logger.error(
            f"Storyboard generation failed - "
            f"content_id: {content_id}, error: {str(e)}",
            exc_info=True
        )

        # 재시도
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying storyboard generation "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "campaign_id": campaign_id,
            "content_id": content_id,
            "storyboard_blocks": [],
            "total_blocks": 0,
            "estimated_duration": 0.0,
            "task_id": self.request.id,
            "error": str(e)
        }


def _save_storyboard_blocks(content_id: int, blocks: List[Dict[str, Any]]) -> None:
    """
    콘티 블록을 SQLite/Neo4j에 저장

    Args:
        content_id: 콘텐츠 ID
        blocks: 콘티 블록 리스트
    """
    # TODO: 실제 데이터베이스 저장 로직 구현
    # 옵션 1: SQLite (빠른 조회용)
    # 옵션 2: Neo4j (관계 그래프용)
    # 옵션 3: 둘 다 (하이브리드)

    try:
        from app.services.neo4j_client import get_neo4j_client

        neo4j_client = get_neo4j_client()

        # Content 노드가 존재하는지 확인
        query_check = """
        MATCH (c:Content {content_id: $content_id})
        RETURN c
        """
        result = neo4j_client.execute_query(
            query=query_check,
            parameters={"content_id": content_id}
        )

        if not result:
            logger.warning(f"Content node not found: {content_id}")
            return

        # 기존 StoryboardBlock 노드 삭제
        query_delete = """
        MATCH (c:Content {content_id: $content_id})-[:HAS_BLOCK]->(b:StoryboardBlock)
        DETACH DELETE b
        """
        neo4j_client.execute_query(
            query=query_delete,
            parameters={"content_id": content_id}
        )

        # 새 StoryboardBlock 노드 생성
        for block in blocks:
            query_create = """
            MATCH (c:Content {content_id: $content_id})
            CREATE (b:StoryboardBlock {
                order: $order,
                script: $script,
                start_time: $start_time,
                end_time: $end_time,
                keywords: $keywords,
                visual_concept: $visual_concept,
                background_type: $background_type,
                background_prompt: $background_prompt,
                transition_effect: $transition_effect,
                subtitle_preset: $subtitle_preset,
                created_at: datetime()
            })
            CREATE (c)-[:HAS_BLOCK]->(b)
            RETURN b
            """

            neo4j_client.execute_query(
                query=query_create,
                parameters={
                    "content_id": content_id,
                    "order": block["order"],
                    "script": block["script"],
                    "start_time": block["start_time"],
                    "end_time": block["end_time"],
                    "keywords": block.get("keywords", []),
                    "visual_concept": str(block.get("visual_concept", {})),
                    "background_type": block.get("background_type", "ai_generated"),
                    "background_prompt": block.get("background_prompt"),
                    "transition_effect": block.get("transition_effect", "fade"),
                    "subtitle_preset": block.get("subtitle_preset", "normal")
                }
            )

        logger.info(f"Saved {len(blocks)} storyboard blocks to Neo4j")

    except Exception as e:
        logger.error(f"Failed to save storyboard blocks to Neo4j: {e}")
        raise


@celery_app.task(
    name="generate_background_image",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=300,
    priority=3
)
def generate_background_image_task(
    self,
    content_id: int,
    block_id: int,
    prompt: str
) -> Dict[str, Any]:
    """
    AI 배경 이미지 생성 (DALL-E)

    Args:
        content_id: 콘텐츠 ID
        block_id: 블록 ID
        prompt: DALL-E 프롬프트

    Returns:
        {
            "success": bool,
            "block_id": int,
            "image_url": str,
            "error": str (실패 시)
        }
    """
    logger.info(
        f"Starting background image generation - "
        f"block_id: {block_id}, prompt: {prompt}"
    )

    try:
        # TODO: DALL-E API 호출하여 배경 이미지 생성
        # from openai import OpenAI
        # client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # response = client.images.generate(
        #     model="dall-e-3",
        #     prompt=prompt,
        #     size="1024x1024",
        #     quality="standard",
        #     n=1
        # )
        # image_url = response.data[0].url

        logger.warning("Background image generation not implemented yet")

        return {
            "success": False,
            "block_id": block_id,
            "image_url": None,
            "error": "Not implemented"
        }

    except Exception as e:
        logger.error(f"Background image generation failed: {e}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            "success": False,
            "block_id": block_id,
            "image_url": None,
            "error": str(e)
        }
