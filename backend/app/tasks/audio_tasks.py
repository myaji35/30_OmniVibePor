"""Celery 오디오 작업 (Zero-Fault Audio Loop)"""
import logging
from typing import Optional, Dict
import asyncio

from app.tasks.celery_app import celery_app
from app.services.audio_correction_loop import get_audio_correction_loop


logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_verified_audio",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def generate_verified_audio_task(
    self,
    text: str,
    voice_id: Optional[str] = None,
    language: str = "ko",
    user_id: Optional[str] = None,
    **kwargs
) -> Dict:
    """
    Zero-Fault Audio 생성 Celery 작업

    Args:
        text: 변환할 텍스트
        voice_id: 음성 ID
        language: 언어 코드
        user_id: 사용자 ID
        **kwargs: AudioCorrectionLoop에 전달할 추가 파라미터

    Returns:
        {
            "status": "success" | "partial_success" | "failed",
            "audio_path": "저장된 파일 경로",
            "task_id": "Celery 작업 ID",
            ...
        }
    """
    # 로깅 정보
    logger.info(f"Starting audio generation task - Text length: {len(text)}, User: {user_id or 'anonymous'}, Task ID: {self.request.id}")

    try:
        # AudioCorrectionLoop 실행 (비동기 → 동기 변환)
        loop = get_audio_correction_loop()
        result = asyncio.run(
            loop.generate_verified_audio(
                text=text,
                voice_id=voice_id,
                language=language,
                save_file=True,
                **kwargs
            )
        )

        # Celery 작업 ID 추가
        result["task_id"] = self.request.id
        result["user_id"] = user_id

        # 상태에 따라 로깅
        if result["status"] == "success":
            logger.info(
                f"✅ Audio generation succeeded for user {user_id}, "
                f"similarity: {result['final_similarity']:.2%}"
            )
        else:
            logger.warning(
                f"⚠️ Audio generation partial/failed for user {user_id}, "
                f"status: {result['status']}"
            )

        return result

    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")

        # 재시도 로직
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        # 최종 실패
        return {
            "status": "error",
            "error": str(e),
            "task_id": self.request.id,
            "user_id": user_id
        }


@celery_app.task(name="batch_generate_verified_audio")
def batch_generate_verified_audio_task(
    texts: list[str],
    voice_id: Optional[str] = None,
    language: str = "ko",
    user_id: Optional[str] = None
) -> Dict:
    """
    여러 텍스트 배치 처리 Celery 작업

    Args:
        texts: 텍스트 리스트
        voice_id: 음성 ID
        language: 언어 코드
        user_id: 사용자 ID

    Returns:
        {"results": [...], "summary": {...}}
    """
    logger.info(f"Starting batch audio generation - Total texts: {len(texts)}, User: {user_id or 'anonymous'}")

    try:
        loop = get_audio_correction_loop()
        results = asyncio.run(
            loop.batch_generate(
                texts=texts,
                voice_id=voice_id,
                language=language
            )
        )

        # 통계
        summary = {
            "total": len(texts),
            "success": sum(1 for r in results if r["status"] == "success"),
            "partial": sum(1 for r in results if r["status"] == "partial_success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "avg_similarity": sum(r["final_similarity"] for r in results) / len(results)
        }

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id
        }
