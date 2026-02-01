"""Celery Director Tasks - 영상 생성 작업

Video Director Agent를 Celery로 비동기 실행하는 작업들

작업 유형:
1. generate_video_from_script_task: 스크립트 → 완성된 영상
2. batch_generate_videos_task: 여러 영상 배치 생성
3. regenerate_video_with_edits_task: 기존 영상 재생성 (수정본)
"""
import logging
import asyncio
from typing import Optional, Dict, List
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.services.director_agent import get_video_director_agent
from app.services.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_video_from_script",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5분
    time_limit=3600,  # 1시간 타임아웃
    soft_time_limit=3300  # 55분 soft 타임아웃
)
def generate_video_from_script_task(
    self,
    project_id: str,
    script: str,
    audio_path: str,
    persona_id: Optional[str] = None,
    gender: str = "female",
    age_range: str = "30-40",
    character_style: str = "professional",
    user_id: Optional[str] = None
) -> Dict:
    """
    스크립트와 오디오로 완성된 영상 생성 Celery 작업

    Args:
        project_id: 프로젝트 ID
        script: 스크립트 텍스트
        audio_path: 오디오 파일 경로
        persona_id: 페르소나 ID
        gender: 성별
        age_range: 연령대
        character_style: 캐릭터 스타일
        user_id: 사용자 ID

    Returns:
        {
            "status": "success" | "error",
            "project_id": str,
            "final_video_path": str,
            "total_duration": float,
            "total_cost_usd": float,
            "cost_breakdown": dict,
            "task_id": str
        }
    """
    logger.info(
        f"Starting video generation task - "
        f"project: {project_id}, user: {user_id or 'anonymous'}, "
        f"task_id: {self.request.id}"
    )

    start_time = datetime.now()

    try:
        # Video Director Agent 실행
        director = get_video_director_agent()
        result = asyncio.run(
            director.generate_video(
                project_id=project_id,
                script=script,
                audio_path=audio_path,
                persona_id=persona_id,
                gender=gender,
                age_range=age_range,
                character_style=character_style
            )
        )

        # Celery 작업 정보 추가
        result["task_id"] = self.request.id
        result["user_id"] = user_id
        result["execution_time_seconds"] = (
            datetime.now() - start_time
        ).total_seconds()

        # 성공 로깅
        if result.get("success"):
            logger.info(
                f"Video generation task completed - "
                f"project: {project_id}, "
                f"duration: {result.get('total_duration', 0):.1f}s, "
                f"cost: ${result.get('total_cost_usd', 0):.2f}, "
                f"execution time: {result['execution_time_seconds']:.1f}s"
            )
        else:
            logger.error(
                f"Video generation task failed - "
                f"project: {project_id}, error: {result.get('error')}"
            )

        return result

    except Exception as e:
        logger.error(f"Video generation task failed: {e}")

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying video generation task... "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # 최종 실패
        return {
            "status": "error",
            "error": str(e),
            "project_id": project_id,
            "task_id": self.request.id,
            "user_id": user_id
        }


@celery_app.task(
    name="batch_generate_videos",
    bind=True,
    time_limit=7200,  # 2시간
    soft_time_limit=7000
)
def batch_generate_videos_task(
    self,
    video_requests: List[Dict],
    user_id: Optional[str] = None
) -> Dict:
    """
    여러 영상 배치 생성 Celery 작업

    Args:
        video_requests: [
            {
                "project_id": str,
                "script": str,
                "audio_path": str,
                "persona_id": str (옵션),
                "gender": str,
                "age_range": str,
                "character_style": str
            },
            ...
        ]
        user_id: 사용자 ID

    Returns:
        {
            "status": "completed" | "error",
            "results": [...],
            "summary": {
                "total": int,
                "success": int,
                "failed": int,
                "total_duration": float,
                "total_cost_usd": float,
                "execution_time_seconds": float
            }
        }
    """
    logger.info(
        f"Starting batch video generation task - "
        f"total: {len(video_requests)}, user: {user_id or 'anonymous'}"
    )

    start_time = datetime.now()

    try:
        director = get_video_director_agent()
        results = []

        # 각 영상 순차 처리
        for i, request in enumerate(video_requests):
            logger.info(
                f"Processing video {i+1}/{len(video_requests)}: "
                f"project={request['project_id']}"
            )

            try:
                result = asyncio.run(
                    director.generate_video(
                        project_id=request["project_id"],
                        script=request["script"],
                        audio_path=request["audio_path"],
                        persona_id=request.get("persona_id"),
                        gender=request.get("gender", "female"),
                        age_range=request.get("age_range", "30-40"),
                        character_style=request.get("character_style", "professional")
                    )
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Batch item {i+1} failed: {e}")
                results.append({
                    "status": "error",
                    "error": str(e),
                    "project_id": request["project_id"]
                })

        # 통계 계산
        summary = {
            "total": len(results),
            "success": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "total_duration": sum(r.get("total_duration", 0) for r in results),
            "total_cost_usd": sum(r.get("total_cost_usd", 0) for r in results),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds()
        }

        logger.info(
            f"Batch video generation completed - "
            f"success: {summary['success']}/{summary['total']}, "
            f"cost: ${summary['total_cost_usd']:.2f}, "
            f"time: {summary['execution_time_seconds']:.1f}s"
        )

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "user_id": user_id,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Batch video generation task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id,
            "task_id": self.request.id
        }


@celery_app.task(
    name="regenerate_video_with_edits",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    time_limit=3600,
    soft_time_limit=3300
)
def regenerate_video_with_edits_task(
    self,
    original_project_id: str,
    edited_script: str,
    edited_audio_path: Optional[str] = None,
    keep_character: bool = True,
    user_id: Optional[str] = None
) -> Dict:
    """
    기존 영상을 수정하여 재생성 Celery 작업

    Args:
        original_project_id: 원본 프로젝트 ID
        edited_script: 수정된 스크립트
        edited_audio_path: 수정된 오디오 경로 (옵션, 없으면 재생성)
        keep_character: 기존 캐릭터 유지 여부
        user_id: 사용자 ID

    Returns:
        영상 생성 결과
    """
    logger.info(
        f"Starting video regeneration task - "
        f"original: {original_project_id}, "
        f"keep_character: {keep_character}, "
        f"user: {user_id or 'anonymous'}"
    )

    try:
        # 새 프로젝트 ID 생성
        new_project_id = f"{original_project_id}_edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # TODO: 원본 프로젝트에서 페르소나/캐릭터 정보 로드
        # 현재는 기본값 사용
        persona_id = None
        gender = "female"
        age_range = "30-40"
        character_style = "professional"

        # if keep_character:
        #     # Neo4j에서 원본 프로젝트의 캐릭터 정보 조회
        #     pass

        # 오디오 경로 결정
        audio_path = edited_audio_path or f"./generated_audio/{new_project_id}.mp3"

        # 영상 재생성
        director = get_video_director_agent()
        result = asyncio.run(
            director.generate_video(
                project_id=new_project_id,
                script=edited_script,
                audio_path=audio_path,
                persona_id=persona_id,
                gender=gender,
                age_range=age_range,
                character_style=character_style
            )
        )

        result["task_id"] = self.request.id
        result["user_id"] = user_id
        result["original_project_id"] = original_project_id
        result["is_regeneration"] = True

        logger.info(
            f"Video regeneration task completed - "
            f"new project: {new_project_id}, "
            f"cost: ${result.get('total_cost_usd', 0):.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"Video regeneration task failed: {e}")

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying video regeneration task... "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # 최종 실패
        return {
            "status": "error",
            "error": str(e),
            "original_project_id": original_project_id,
            "task_id": self.request.id,
            "user_id": user_id
        }


@celery_app.task(name="estimate_video_cost")
def estimate_video_cost_task(
    script_length: int,
    video_duration: int,
    platform: str = "YouTube"
) -> Dict:
    """
    영상 생성 예상 비용 계산 Celery 작업

    Args:
        script_length: 스크립트 글자 수
        video_duration: 예상 영상 길이 (초)
        platform: 플랫폼 (YouTube, Instagram, TikTok 등)

    Returns:
        {
            "total_cost_usd": float,
            "breakdown": {
                "writer_agent": float,
                "tts": float,
                "stt": float,
                "character": float,
                "video_generation": float,
                "lipsync": float
            }
        }
    """
    logger.info(
        f"Estimating video cost - "
        f"script_length: {script_length}, "
        f"video_duration: {video_duration}s, "
        f"platform: {platform}"
    )

    try:
        cost_tracker = get_cost_tracker()
        estimates = cost_tracker.estimate_project_cost(
            script_length=script_length,
            video_duration=video_duration,
            platform=platform
        )

        logger.info(
            f"Cost estimate calculated - "
            f"total: ${estimates['total']:.2f}"
        )

        return {
            "status": "success",
            "total_cost_usd": estimates["total"],
            "breakdown": {
                k: v for k, v in estimates.items() if k != "total"
            },
            "script_length": script_length,
            "video_duration": video_duration,
            "platform": platform
        }

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="get_project_cost_report")
def get_project_cost_report_task(
    project_id: str,
    user_id: Optional[str] = None
) -> Dict:
    """
    프로젝트 비용 리포트 조회 Celery 작업

    Args:
        project_id: 프로젝트 ID
        user_id: 사용자 ID

    Returns:
        {
            "status": "success" | "error",
            "project_id": str,
            "total_cost_usd": float,
            "by_provider": dict,
            "record_count": int
        }
    """
    logger.info(f"Generating cost report for project: {project_id}")

    try:
        cost_tracker = get_cost_tracker()
        total_cost = cost_tracker.get_total_cost(
            project_id=project_id,
            user_id=user_id
        )

        logger.info(
            f"Cost report generated - "
            f"project: {project_id}, "
            f"total: ${total_cost['total_cost']:.2f}"
        )

        return {
            "status": "success",
            "project_id": project_id,
            "user_id": user_id,
            **total_cost
        }

    except Exception as e:
        logger.error(f"Cost report generation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "project_id": project_id
        }
