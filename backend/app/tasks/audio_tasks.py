"""Celery 오디오 작업 (Zero-Fault Audio Loop)"""
import logging
from typing import Optional, Dict
import asyncio

from app.tasks.celery_app import celery_app
from app.services.audio_correction_loop import get_audio_correction_loop
from app.tasks.progress_tracker import ProgressTracker, BatchProgressTracker
from app.utils.progress_mapper import ProgressMapper


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

    # 진행률 추적기 초기화
    tracker = ProgressTracker(
        task=self,
        project_id=user_id or "anonymous",
        task_name="audio_generation"
    )

    try:
        # 1. 시작 (0%)
        tracker.update(
            ProgressMapper.get_audio_progress("start"),
            "processing",
            "오디오 생성 작업 시작"
        )

        # 2. 텍스트 정규화 (5%)
        tracker.update(
            ProgressMapper.get_audio_progress("normalize_text"),
            "processing",
            "텍스트 정규화 중..."
        )

        # 3. TTS 생성 시작 (5% → 30%)
        tracker.update(
            ProgressMapper.get_audio_progress("tts_generation", 0.0),
            "processing",
            "TTS 음성 생성 시작..."
        )

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

        # 4. TTS 생성 완료 (30%)
        tracker.update(
            ProgressMapper.get_audio_progress("tts_generation", 1.0),
            "processing",
            "TTS 음성 생성 완료"
        )

        # 5. STT 검증 시작 (30% → 60%)
        tracker.update(
            ProgressMapper.get_audio_progress("stt_verification", 0.0),
            "processing",
            "STT 검증 시작..."
        )

        # 6. STT 검증 완료 (60%)
        tracker.update(
            ProgressMapper.get_audio_progress("stt_verification", 1.0),
            "processing",
            "STT 검증 완료"
        )

        # 7. 유사도 체크 (70%)
        tracker.update(
            ProgressMapper.get_audio_progress("similarity_check"),
            "processing",
            f"유사도 체크 완료: {result.get('final_similarity', 0)*100:.1f}%"
        )

        # 8. 파일 저장 (95%)
        tracker.update(
            ProgressMapper.get_audio_progress("save_file"),
            "processing",
            "오디오 파일 저장 중..."
        )

        # Celery 작업 ID 추가
        result["task_id"] = self.request.id
        result["user_id"] = user_id

        # 상태에 따라 로깅 및 완료 처리
        if result["status"] == "success":
            logger.info(
                f"✅ Audio generation succeeded for user {user_id}, "
                f"similarity: {result['final_similarity']:.2%}"
            )

            # 9. 완료 (100%)
            tracker.complete({
                "audio_path": result.get("audio_path"),
                "final_similarity": result.get("final_similarity"),
                "attempts": result.get("attempts", 1),
                "status": "success"
            })
        else:
            logger.warning(
                f"⚠️ Audio generation partial/failed for user {user_id}, "
                f"status: {result['status']}"
            )

            # 부분 성공 또는 실패 처리
            if result["status"] == "partial_success":
                tracker.complete({
                    "audio_path": result.get("audio_path"),
                    "final_similarity": result.get("final_similarity"),
                    "attempts": result.get("attempts", 1),
                    "status": "partial_success"
                })
            else:
                tracker.error(
                    "오디오 생성 실패",
                    {"status": result["status"], "result": result}
                )

        return result

    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")

        # 에러 브로드캐스트
        tracker.error(
            str(e),
            {"user_id": user_id, "text_length": len(text)}

        )

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

    # 배치 진행률 추적기 초기화
    batch_tracker = BatchProgressTracker(
        task=self,
        project_id=user_id or "anonymous",
        task_name="batch_audio_generation",
        total_items=len(texts)
    )

    try:
        # AudioCorrectionLoop는 내부적으로 배치 처리를 수행하므로
        # 여기서는 전체 진행률만 추적
        batch_tracker.update_item(
            0, 0.0, "processing",
            f"배치 오디오 생성 시작 (총 {len(texts)}개)"
        )

        loop = get_audio_correction_loop()
        results = asyncio.run(
            loop.batch_generate(
                texts=texts,
                voice_id=voice_id,
                language=language
            )
        )

        # 배치 완료 시 모든 아이템을 완료로 표시
        for i in range(len(texts)):
            batch_tracker.update_item(
                i, 1.0, "processing",
                f"오디오 {i+1}/{len(texts)} 완료"
            )

        # 통계
        summary = {
            "total": len(texts),
            "success": sum(1 for r in results if r["status"] == "success"),
            "partial": sum(1 for r in results if r["status"] == "partial_success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "avg_similarity": sum(r["final_similarity"] for r in results) / len(results)
        }

        # 배치 작업 완료 브로드캐스트
        batch_tracker.complete({
            "total": summary["total"],
            "success": summary["success"],
            "partial": summary["partial"],
            "failed": summary["failed"],
            "avg_similarity": summary["avg_similarity"]
        })

        return {
            "status": "completed",
            "results": results,
            "summary": summary,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Batch generation failed: {e}")

        # 배치 작업 에러 브로드캐스트
        batch_tracker.error(
            str(e),
            {"user_id": user_id, "total_texts": len(texts)}
        )

        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id
        }
