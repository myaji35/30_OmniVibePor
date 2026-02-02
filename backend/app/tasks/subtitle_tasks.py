"""Celery 자막 작업 (미리보기 생성, 자막 오버레이)"""
import logging
from typing import Dict, Optional
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.services.subtitle_editor_service import get_subtitle_editor_service
from app.services.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_subtitle_preview",
    bind=True,
    max_retries=2,
    default_retry_delay=10
)
def generate_subtitle_preview_task(
    self,
    project_id: str,
    video_path: str,
    srt_path: str,
    start_time: float = 0.0,
    duration: float = 5.0,
    style: Optional[Dict] = None
) -> Dict:
    """
    자막 미리보기 생성 Celery 작업

    Args:
        project_id: 프로젝트 ID
        video_path: 원본 비디오 경로
        srt_path: SRT 자막 파일 경로
        start_time: 시작 시간 (초)
        duration: 미리보기 길이 (초, 기본 5초)
        style: 적용할 자막 스타일 (None이면 프로젝트 스타일 사용)

    Returns:
        {
            "status": "success" | "failed",
            "preview_path": str,
            "expires_at": str (ISO 8601),
            "style": Dict,
            "task_id": str,
            "error": str (실패 시)
        }
    """
    logger.info(
        f"Starting subtitle preview task - "
        f"project: {project_id}, video: {video_path}, "
        f"start: {start_time}s, duration: {duration}s, "
        f"task_id: {self.request.id}"
    )

    try:
        # 서비스 인스턴스 가져오기
        neo4j_client = get_neo4j_client()
        subtitle_service = get_subtitle_editor_service()

        # 미리보기 생성
        result = subtitle_service.generate_preview(
            project_id=project_id,
            video_path=video_path,
            srt_path=srt_path,
            start_time=start_time,
            duration=duration,
            style=style
        )

        logger.info(f"Subtitle preview completed: {result['preview_path']}")

        return {
            "status": "success",
            "preview_path": result["preview_path"],
            "expires_at": result["expires_at"].isoformat(),
            "style": result["style"],
            "task_id": self.request.id
        }

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id
        }

    except Exception as e:
        error_msg = f"Subtitle preview failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 재시도 (최대 2회)
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying subtitle preview task ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id
        }


@celery_app.task(
    name="apply_subtitles_to_video",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def apply_subtitles_to_video_task(
    self,
    project_id: str,
    video_path: str,
    srt_path: str,
    output_path: str,
    style: Optional[Dict] = None
) -> Dict:
    """
    비디오에 자막 오버레이 적용 Celery 작업

    Args:
        project_id: 프로젝트 ID
        video_path: 원본 비디오 경로
        srt_path: SRT 자막 파일 경로
        output_path: 출력 비디오 경로
        style: 적용할 자막 스타일 (None이면 프로젝트 스타일 사용)

    Returns:
        {
            "status": "success" | "failed",
            "output_path": str,
            "style": Dict,
            "task_id": str,
            "error": str (실패 시)
        }
    """
    logger.info(
        f"Starting subtitle overlay task - "
        f"project: {project_id}, video: {video_path}, "
        f"output: {output_path}, task_id: {self.request.id}"
    )

    try:
        # 서비스 인스턴스 가져오기
        neo4j_client = get_neo4j_client()
        subtitle_service = get_subtitle_editor_service()

        # 스타일 결정
        if style is None:
            style = subtitle_service.get_project_style(project_id)

        # ASS 파일 생성
        ass_path = Path(srt_path).with_suffix('.ass')
        subtitle_service.srt_to_ass(srt_path, str(ass_path), style)

        # 자막 오버레이
        result_path = subtitle_service.apply_subtitles_to_video(
            video_path=video_path,
            ass_path=str(ass_path),
            output_path=output_path
        )

        logger.info(f"Subtitle overlay completed: {result_path}")

        return {
            "status": "success",
            "output_path": result_path,
            "style": style,
            "task_id": self.request.id
        }

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id
        }

    except RuntimeError as e:
        error_msg = f"FFmpeg error: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id
        }

    except Exception as e:
        error_msg = f"Subtitle overlay failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 재시도 (최대 3회)
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying subtitle overlay task ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "status": "failed",
            "error": error_msg,
            "task_id": self.request.id
        }


@celery_app.task(
    name="batch_generate_subtitles",
    bind=True
)
def batch_generate_subtitles_task(
    self,
    project_ids: list[str]
) -> Dict:
    """
    여러 프로젝트의 자막을 배치로 생성

    Args:
        project_ids: 프로젝트 ID 리스트

    Returns:
        {
            "status": "success" | "partial" | "failed",
            "total": int,
            "success": int,
            "failed": int,
            "results": List[Dict],
            "task_id": str
        }
    """
    logger.info(
        f"Starting batch subtitle generation - "
        f"projects: {len(project_ids)}, task_id: {self.request.id}"
    )

    from app.services.subtitle_service import get_subtitle_service
    from app.models.neo4j_models import Neo4jCRUDManager

    neo4j_client = get_neo4j_client()
    crud = Neo4jCRUDManager(neo4j_client)
    subtitle_service = get_subtitle_service()

    results = []
    success_count = 0
    failed_count = 0

    for project_id in project_ids:
        try:
            # 프로젝트의 오디오 파일 조회
            project = crud.get_project(project_id)
            if not project:
                results.append({
                    "project_id": project_id,
                    "status": "failed",
                    "error": "Project not found"
                })
                failed_count += 1
                continue

            videos = crud.get_project_videos(project_id)
            if not videos:
                results.append({
                    "project_id": project_id,
                    "status": "failed",
                    "error": "No video found"
                })
                failed_count += 1
                continue

            video = videos[0]
            audio_path = Path(video["file_path"]).with_suffix('.mp3')

            if not audio_path.exists():
                results.append({
                    "project_id": project_id,
                    "status": "failed",
                    "error": "Audio file not found"
                })
                failed_count += 1
                continue

            # 자막 생성 (동기 함수를 직접 호출)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                subtitle_service.generate_subtitles(
                    audio_path=str(audio_path),
                    language="ko",
                    project_id=project_id
                )
            )
            loop.close()

            results.append({
                "project_id": project_id,
                "status": "success",
                "srt_path": result["srt_path"],
                "duration": result["duration"]
            })
            success_count += 1

            logger.info(f"Subtitle generated for project {project_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to generate subtitle for project {project_id}: {error_msg}")
            results.append({
                "project_id": project_id,
                "status": "failed",
                "error": error_msg
            })
            failed_count += 1

    # 전체 상태 결정
    if failed_count == 0:
        overall_status = "success"
    elif success_count == 0:
        overall_status = "failed"
    else:
        overall_status = "partial"

    logger.info(
        f"Batch subtitle generation completed - "
        f"total: {len(project_ids)}, success: {success_count}, failed: {failed_count}"
    )

    return {
        "status": overall_status,
        "total": len(project_ids),
        "success": success_count,
        "failed": failed_count,
        "results": results,
        "task_id": self.request.id
    }
