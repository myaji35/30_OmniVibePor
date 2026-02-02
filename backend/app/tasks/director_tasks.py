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
from app.tasks.progress_tracker import ProgressTracker, BatchProgressTracker
from app.utils.progress_mapper import ProgressMapper

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

    # 진행률 추적기 초기화
    tracker = ProgressTracker(
        task=self,
        project_id=project_id,
        task_name="video_generation"
    )

    start_time = datetime.now()

    try:
        # 1. 시작 (0%)
        tracker.update(
            ProgressMapper.get_director_progress("start"),
            "processing",
            "영상 생성 작업 시작"
        )

        # 2. 캐릭터 로드 (5%)
        tracker.update(
            ProgressMapper.get_director_progress("load_character"),
            "processing",
            "캐릭터 레퍼런스 로드 중..."
        )

        # 3. 스크립트 분석 (10%)
        tracker.update(
            ProgressMapper.get_director_progress("parse_script"),
            "processing",
            "스크립트 분석 중..."
        )

        # 4. 영상 생성 (10% → 60%)
        tracker.update(
            ProgressMapper.get_director_progress("generate_videos", 0.0),
            "processing",
            "영상 클립 생성 시작..."
        )

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

        # 5. 영상 생성 완료 (60%)
        tracker.update(
            ProgressMapper.get_director_progress("generate_videos", 1.0),
            "processing",
            "영상 클립 생성 완료"
        )

        # 6. 립싱크 적용 (75%)
        tracker.update(
            ProgressMapper.get_director_progress("lipsync"),
            "processing",
            "립싱크 적용 중..."
        )

        # 7. 자막 생성 (85%)
        tracker.update(
            ProgressMapper.get_director_progress("subtitles"),
            "processing",
            "자막 생성 중..."
        )

        # 8. 최종 렌더링 (95%)
        tracker.update(
            ProgressMapper.get_director_progress("render"),
            "processing",
            "최종 렌더링 중..."
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

            # 9. 완료 (100%)
            tracker.complete({
                "final_video_path": result.get("final_video_path"),
                "total_duration": result.get("total_duration", 0),
                "total_cost_usd": result.get("total_cost_usd", 0),
                "execution_time_seconds": result["execution_time_seconds"]
            })
        else:
            logger.error(
                f"Video generation task failed - "
                f"project: {project_id}, error: {result.get('error')}"
            )

            # 에러 브로드캐스트
            tracker.error(
                result.get('error', 'Unknown error'),
                {"project_id": project_id, "result": result}
            )

        return result

    except Exception as e:
        logger.error(f"Video generation task failed: {e}")

        # 에러 브로드캐스트
        tracker.error(
            str(e),
            {"project_id": project_id, "traceback": str(e)}

        )

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

    # 배치 진행률 추적기 초기화
    batch_tracker = BatchProgressTracker(
        task=self,
        project_id=f"batch_{self.request.id}",
        task_name="batch_video_generation",
        total_items=len(video_requests)
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

            # 개별 아이템 시작 (0%)
            batch_tracker.update_item(
                i, 0.0, "processing",
                f"영상 {i+1}/{len(video_requests)} 생성 시작"
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

                # 개별 아이템 완료 (100%)
                batch_tracker.update_item(
                    i, 1.0, "processing",
                    f"영상 {i+1}/{len(video_requests)} 생성 완료"
                )

            except Exception as e:
                logger.error(f"Batch item {i+1} failed: {e}")
                results.append({
                    "status": "error",
                    "error": str(e),
                    "project_id": request["project_id"]
                })

                # 개별 아이템 실패 처리 (진행률은 1.0으로 카운트)
                batch_tracker.update_item(
                    i, 1.0, "processing",
                    f"영상 {i+1}/{len(video_requests)} 실패"
                )

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

        # 배치 작업 완료 브로드캐스트
        batch_tracker.complete({
            "total": summary['total'],
            "success": summary['success'],
            "failed": summary['failed'],
            "total_cost_usd": summary['total_cost_usd'],
            "execution_time_seconds": summary['execution_time_seconds']
        })

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "user_id": user_id,
            "task_id": self.request.id
        }

    except Exception as e:
        logger.error(f"Batch video generation task failed: {e}")

        # 배치 작업 에러 브로드캐스트
        batch_tracker.error(
            str(e),
            {"user_id": user_id, "total_requests": len(video_requests)}
        )

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


@celery_app.task(
    bind=True,
    name="generate_alternative_clip",
    max_retries=3,
    default_retry_delay=60
)
def generate_alternative_clip_task(
    self,
    section_id: str,
    clip_id: str,
    prompt: str,
    variation_type: str,
    duration: int = 5,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict:
    """
    대체 클립 생성 Celery 작업 (비동기)

    Args:
        section_id: 섹션 ID
        clip_id: 클립 ID
        prompt: 영상 생성 프롬프트
        variation_type: 변형 타입 (camera_angle, lighting, color_tone)
        duration: 영상 길이 (초)
        user_id: 사용자 ID
        project_id: 프로젝트 ID

    Returns:
        {
            "status": "success" | "error",
            "clip_id": str,
            "video_path": str,
            "thumbnail_url": str,
            "veo_job_id": str
        }
    """
    logger.info(
        f"Starting alternative clip generation - "
        f"section: {section_id}, "
        f"clip: {clip_id}, "
        f"variation: {variation_type}"
    )

    try:
        from app.services.veo_service import get_veo_service
        from app.services.cloudinary_service import get_cloudinary_service
        from app.models.neo4j_models import Neo4jCRUDManager
        from app.services.neo4j_client import get_neo4j_client
        import asyncio

        veo_service = get_veo_service()
        cloudinary_service = get_cloudinary_service()
        neo4j_client = get_neo4j_client()
        crud = Neo4jCRUDManager(neo4j_client)

        # 1. Veo API로 영상 생성 시작
        logger.info(f"Calling Veo API with prompt: {prompt[:100]}...")
        
        async def generate_video():
            return await veo_service.generate_video(
                prompt=prompt,
                duration=duration,
                style="commercial",
                aspect_ratio="16:9"
            )
        
        veo_result = asyncio.run(generate_video())
        
        veo_job_id = veo_result.get("job_id")
        
        if not veo_job_id:
            raise Exception("Veo API did not return job_id")
        
        logger.info(f"Veo job started: {veo_job_id}")

        # 2. 상태 체크 및 다운로드 대기 (폴링)
        max_wait_time = 300  # 5분
        check_interval = 10  # 10초마다 체크
        elapsed_time = 0
        
        video_url = None
        
        async def check_status():
            return await veo_service.check_status(veo_job_id)
        
        while elapsed_time < max_wait_time:
            import time
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            status_result = asyncio.run(check_status())
            status = status_result.get("status")
            
            logger.info(
                f"Veo job status: {status} "
                f"(progress: {status_result.get('progress', 0)}%)"
            )
            
            if status == "completed":
                video_url = status_result.get("video_url")
                logger.info(f"Video generation completed: {video_url}")
                break
            elif status == "failed":
                error_msg = status_result.get("error", "Unknown error")
                raise Exception(f"Veo job failed: {error_msg}")
        
        if not video_url:
            raise Exception(f"Video generation timeout after {max_wait_time}s")

        # 3. 영상 다운로드
        from pathlib import Path
        output_dir = Path("./outputs/alternative_clips")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        video_filename = f"{clip_id}.mp4"
        
        async def download_video():
            return await veo_service.download_video(video_url, video_filename)
        
        video_path = asyncio.run(download_video())
        
        logger.info(f"Video downloaded: {video_path}")

        # 4. Cloudinary 업로드
        async def upload_video():
            return await cloudinary_service.upload_video(
                video_path=str(video_path),
                folder="alternative_clips",
                user_id=user_id,
                project_id=project_id
            )
        
        cloudinary_result = asyncio.run(upload_video())
        
        cloudinary_public_id = cloudinary_result.get("public_id")
        cloudinary_url = cloudinary_result.get("secure_url")
        
        logger.info(f"Video uploaded to Cloudinary: {cloudinary_public_id}")

        # 5. 썸네일 생성
        async def generate_thumbnail():
            return await cloudinary_service.generate_thumbnail(
                video_public_id=cloudinary_public_id,
                time_offset=1.0,
                width=1280,
                height=720,
                user_id=user_id,
                project_id=project_id
            )
        
        thumbnail_url = asyncio.run(generate_thumbnail())
        
        logger.info(f"Thumbnail generated: {thumbnail_url}")

        # 6. Neo4j 상태 업데이트
        crud.update_alternative_clip_status(
            clip_id=clip_id,
            status="completed",
            video_path=cloudinary_url,
            thumbnail_url=thumbnail_url
        )
        
        logger.info(
            f"Alternative clip generation completed - "
            f"clip: {clip_id}, "
            f"video: {cloudinary_url}"
        )

        return {
            "status": "success",
            "clip_id": clip_id,
            "video_path": cloudinary_url,
            "thumbnail_url": thumbnail_url,
            "veo_job_id": veo_job_id,
            "cloudinary_public_id": cloudinary_public_id,
            "section_id": section_id,
            "variation_type": variation_type
        }

    except Exception as e:
        logger.error(f"Alternative clip generation failed: {e}", exc_info=True)

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying alternative clip generation... "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        # Neo4j 상태를 failed로 업데이트
        try:
            from app.models.neo4j_models import Neo4jCRUDManager
            from app.services.neo4j_client import get_neo4j_client
            
            neo4j_client = get_neo4j_client()
            crud = Neo4jCRUDManager(neo4j_client)
            crud.update_alternative_clip_status(
                clip_id=clip_id,
                status="failed"
            )
        except Exception as update_error:
            logger.error(f"Failed to update clip status: {update_error}")

        # 최종 실패
        return {
            "status": "error",
            "error": str(e),
            "clip_id": clip_id,
            "section_id": section_id,
            "task_id": self.request.id
        }
