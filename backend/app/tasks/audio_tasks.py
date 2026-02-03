"""Celery 오디오 작업 (Zero-Fault Audio Loop)"""
import logging
from typing import Optional, Dict
import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path

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


@celery_app.task(
    name="remove_silence_from_audio",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def remove_silence_task(
    self,
    audio_url: str,
    threshold_db: int = -40,
    min_silence_duration: float = 0.5
) -> Dict:
    """
    무음 구간 자동 제거 Celery 작업

    Args:
        audio_url: 오디오 파일 URL
        threshold_db: 무음 기준 (dB)
        min_silence_duration: 최소 무음 길이 (초)

    Returns:
        {
            "success": bool,
            "processed_audio_url": str,
            "original_duration": float,
            "new_duration": float,
            "removed_segments": [{"start": float, "end": float}]
        }
    """
    logger.info(f"Starting silence removal - Audio: {audio_url}, Threshold: {threshold_db}dB")

    tracker = ProgressTracker(
        task=self,
        project_id="silence_removal",
        task_name="remove_silence"
    )

    try:
        # 1. 시작 (0%)
        tracker.update(10, "processing", "무음 제거 작업 시작")

        # 2. 오디오 다운로드 (로컬 파일이면 스킵)
        if audio_url.startswith("http"):
            import requests
            response = requests.get(audio_url)
            response.raise_for_status()

            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_input.write(response.content)
            temp_input.close()
            input_path = temp_input.name
        else:
            input_path = audio_url

        tracker.update(20, "processing", "오디오 파일 다운로드 완료")

        # 3. 원본 길이 측정
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        original_duration = float(subprocess.check_output(duration_cmd).decode().strip())
        logger.info(f"Original duration: {original_duration:.2f}s")

        tracker.update(30, "processing", f"원본 길이: {original_duration:.2f}초")

        # 4. 무음 구간 감지
        detect_cmd = [
            "ffmpeg", "-i", input_path,
            "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_duration}",
            "-f", "null", "-"
        ]

        result = subprocess.run(detect_cmd, capture_output=True, text=True)
        silence_log = result.stderr

        # 무음 구간 파싱
        removed_segments = []
        lines = silence_log.split('\n')
        silence_start = None

        for line in lines:
            if 'silence_start' in line:
                silence_start = float(line.split('silence_start: ')[1].strip())
            elif 'silence_end' in line and silence_start is not None:
                silence_end = float(line.split('silence_end: ')[1].split('|')[0].strip())
                removed_segments.append({"start": silence_start, "end": silence_end})
                silence_start = None

        logger.info(f"Detected {len(removed_segments)} silence segments")
        tracker.update(50, "processing", f"무음 구간 감지 완료: {len(removed_segments)}개")

        # 5. 무음 제거
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_output.close()

        remove_cmd = [
            "ffmpeg", "-i", input_path,
            "-af", f"silenceremove=start_periods=1:start_duration=0:start_threshold={threshold_db}dB:detection=peak,silenceremove=stop_periods=-1:stop_duration={min_silence_duration}:stop_threshold={threshold_db}dB:detection=peak",
            "-c:a", "libmp3lame", "-b:a", "192k",
            temp_output.name, "-y"
        ]

        subprocess.run(remove_cmd, check=True, capture_output=True)
        tracker.update(80, "processing", "무음 제거 완료")

        # 6. 새로운 길이 측정
        new_duration = float(subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            temp_output.name
        ]).decode().strip())

        logger.info(f"New duration: {new_duration:.2f}s (removed {original_duration - new_duration:.2f}s)")

        # 7. Cloudinary 업로드 (선택)
        # TODO: Cloudinary 업로드 구현
        processed_audio_url = temp_output.name  # 임시로 로컬 경로 반환

        tracker.update(90, "processing", "처리된 파일 저장 완료")

        # 8. 임시 파일 정리
        if audio_url.startswith("http"):
            os.unlink(input_path)

        # 완료
        result = {
            "success": True,
            "processed_audio_url": processed_audio_url,
            "original_duration": original_duration,
            "new_duration": new_duration,
            "removed_segments": removed_segments,
            "task_id": self.request.id
        }

        tracker.complete(result)
        logger.info(f"✅ Silence removal completed: {original_duration:.2f}s → {new_duration:.2f}s")

        return result

    except Exception as e:
        logger.error(f"❌ Silence removal failed: {e}")
        tracker.error(str(e), {"audio_url": audio_url})

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id
        }


@celery_app.task(
    name="remove_fillers_from_audio",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def remove_fillers_task(
    self,
    audio_url: str,
    filler_words: list[str] = None,
    language: str = "ko"
) -> Dict:
    """
    필러 워드 자동 제거 Celery 작업

    Args:
        audio_url: 오디오 파일 URL
        filler_words: 제거할 필러 워드 목록
        language: 언어 코드

    Returns:
        {
            "success": bool,
            "processed_audio_url": str,
            "transcript": str,
            "removed_words": [{"word": str, "start": float, "end": float}],
            "original_duration": float,
            "new_duration": float
        }
    """
    if filler_words is None:
        filler_words = ["음", "어", "그", "저", "아"]

    logger.info(f"Starting filler removal - Audio: {audio_url}, Fillers: {filler_words}")

    tracker = ProgressTracker(
        task=self,
        project_id="filler_removal",
        task_name="remove_fillers"
    )

    try:
        # 1. 시작 (0%)
        tracker.update(10, "processing", "필러 워드 제거 작업 시작")

        # 2. 오디오 다운로드
        if audio_url.startswith("http"):
            import requests
            response = requests.get(audio_url)
            response.raise_for_status()

            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_input.write(response.content)
            temp_input.close()
            input_path = temp_input.name
        else:
            input_path = audio_url

        tracker.update(20, "processing", "오디오 파일 다운로드 완료")

        # 3. Whisper STT with word-level timestamps
        from openai import OpenAI
        client = OpenAI()

        tracker.update(30, "processing", "Whisper STT 실행 중...")

        with open(input_path, "rb") as audio_file:
            transcript_result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        logger.info(f"Transcript: {transcript_result.text}")
        tracker.update(50, "processing", "STT 완료, 필러 워드 감지 중...")

        # 4. 필러 워드 감지
        removed_words = []
        filler_segments = []  # FFmpeg에서 제거할 구간 (시작, 끝)

        if hasattr(transcript_result, 'words') and transcript_result.words:
            for word_data in transcript_result.words:
                word_text = word_data.word.strip()

                # 필러 워드 매칭 (공백 제거하고 비교)
                if any(filler.strip() in word_text for filler in filler_words):
                    removed_words.append({
                        "word": word_text,
                        "start": word_data.start,
                        "end": word_data.end
                    })
                    filler_segments.append((word_data.start, word_data.end))

        logger.info(f"Detected {len(removed_words)} filler words")
        tracker.update(60, "processing", f"필러 워드 감지 완료: {len(removed_words)}개")

        # 5. 원본 길이 측정
        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        original_duration = float(subprocess.check_output(duration_cmd).decode().strip())

        # 6. FFmpeg로 필러 워드 구간 제거
        if filler_segments:
            # FFmpeg select 필터를 사용해 특정 구간 제거
            # between(t,start,end) 함수로 제거할 구간 지정
            select_expr = "1"
            for start, end in filler_segments:
                select_expr += f"*not(between(t,{start},{end}))"

            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_output.close()

            # aselect로 구간 선택, asetpts로 타임스탬프 재조정
            remove_cmd = [
                "ffmpeg", "-i", input_path,
                "-af", f"aselect='{select_expr}',asetpts=N/SR/TB",
                "-c:a", "libmp3lame", "-b:a", "192k",
                temp_output.name, "-y"
            ]

            subprocess.run(remove_cmd, check=True, capture_output=True)
            tracker.update(80, "processing", "필러 워드 제거 완료")

            # 7. 새로운 길이 측정
            new_duration = float(subprocess.check_output([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                temp_output.name
            ]).decode().strip())

            processed_audio_url = temp_output.name
        else:
            # 필러 워드가 없으면 원본 그대로
            logger.info("No filler words detected, returning original audio")
            processed_audio_url = input_path
            new_duration = original_duration

        logger.info(f"New duration: {new_duration:.2f}s (removed {original_duration - new_duration:.2f}s)")

        # 8. Cloudinary 업로드 (선택)
        # TODO: Cloudinary 업로드 구현

        tracker.update(90, "processing", "처리된 파일 저장 완료")

        # 9. 임시 파일 정리
        if audio_url.startswith("http"):
            os.unlink(input_path)

        # 완료
        result = {
            "success": True,
            "processed_audio_url": processed_audio_url,
            "transcript": transcript_result.text,
            "removed_words": removed_words,
            "original_duration": original_duration,
            "new_duration": new_duration,
            "task_id": self.request.id
        }

        tracker.complete(result)
        logger.info(f"✅ Filler removal completed: {len(removed_words)} words removed")

        return result

    except Exception as e:
        logger.error(f"❌ Filler removal failed: {e}")
        tracker.error(str(e), {"audio_url": audio_url})

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": str(e),
            "task_id": self.request.id
        }
