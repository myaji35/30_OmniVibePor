"""Lipsync Service - 오디오와 영상 립싱크 생성

HeyGen API와 Wav2Lip Fallback을 지원하는 이중화 립싱크 서비스

기능:
- HeyGen API 우선 사용 (고품질, 유료)
- Wav2Lip Fallback (오픈소스, 로컬/GPU)
- 자동 품질 평가
- 비용 추적 및 최적화
"""

import logging
import asyncio
import subprocess
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from contextlib import nullcontext
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class LipsyncService:
    """
    립싱크 영상 생성 서비스

    특징:
    - HeyGen API 우선 사용 (고품질)
    - Wav2Lip Fallback (로컬 실행)
    - 자동 Fallback 전환
    - 품질 평가 (선택적)
    - 비용 추적
    """

    # 지원하는 립싱크 방법
    METHODS = Literal["auto", "heygen", "wav2lip"]

    # HeyGen API 비용 (USD)
    HEYGEN_COST_PER_SECOND = 0.05  # $0.05/초

    def __init__(
        self,
        heygen_api_key: Optional[str] = None,
        heygen_endpoint: Optional[str] = None,
        wav2lip_model_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        gpu_enabled: bool = False
    ):
        """
        Args:
            heygen_api_key: HeyGen API 키
            heygen_endpoint: HeyGen API 엔드포인트
            wav2lip_model_path: Wav2Lip 모델 경로
            output_dir: 출력 디렉토리
            gpu_enabled: GPU 사용 여부 (Wav2Lip)
        """
        self.heygen_api_key = heygen_api_key or settings.HEYGEN_API_KEY
        self.heygen_endpoint = heygen_endpoint or settings.HEYGEN_API_ENDPOINT
        self.wav2lip_model_path = wav2lip_model_path or settings.WAV2LIP_MODEL_PATH
        self.gpu_enabled = gpu_enabled or settings.LIPSYNC_GPU_ENABLED

        # 출력 디렉토리 설정
        self.output_dir = Path(output_dir or settings.LIPSYNC_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # HeyGen HTTP 클라이언트
        self.heygen_client = httpx.AsyncClient(
            base_url=self.heygen_endpoint,
            timeout=300.0,
            headers={
                "X-Api-Key": self.heygen_api_key if self.heygen_api_key else "",
                "Content-Type": "application/json"
            }
        ) if self.heygen_api_key else None

        logger.info(
            f"LipsyncService initialized - "
            f"HeyGen: {bool(self.heygen_api_key)}, "
            f"Wav2Lip: {bool(self.wav2lip_model_path)}, "
            f"GPU: {self.gpu_enabled}"
        )

    async def generate_lipsync(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        립싱크 영상 생성 (메인 메서드)

        Args:
            video_path: 입력 영상 경로
            audio_path: 입력 오디오 경로
            output_path: 출력 영상 경로
            method: 사용할 방법 ("auto", "heygen", "wav2lip")

        Returns:
            {
                "status": "success" | "failed",
                "output_path": str,
                "method_used": "heygen" | "wav2lip",
                "duration": float,
                "cost_usd": float (HeyGen 사용 시),
                "quality_score": float (선택적)
            }
        """
        span_context = logfire.span("lipsync.generate") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context as span:
            logger.info(
                f"Starting lipsync generation - "
                f"video: {video_path}, audio: {audio_path}, method: {method}"
            )

            if LOGFIRE_AVAILABLE:
                span.set_attribute("method", method)
                span.set_attribute("video_path", video_path)
                span.set_attribute("audio_path", audio_path)

            # 1. 입력 파일 검증
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # 2. 방법 선택 및 실행
            if method == "auto":
                # HeyGen 우선 시도 → 실패 시 Wav2Lip
                if self.heygen_api_key:
                    try:
                        result = await self._heygen_lipsync(
                            video_path, audio_path, output_path
                        )
                        result["method_used"] = "heygen"
                        logger.info("Lipsync completed with HeyGen")
                        return result
                    except Exception as e:
                        logger.warning(f"HeyGen failed, falling back to Wav2Lip: {e}")

                # Wav2Lip Fallback
                result = await self._wav2lip_lipsync(
                    video_path, audio_path, output_path
                )
                result["method_used"] = "wav2lip"
                logger.info("Lipsync completed with Wav2Lip")
                return result

            elif method == "heygen":
                if not self.heygen_api_key:
                    raise ValueError("HeyGen API key not configured")
                result = await self._heygen_lipsync(video_path, audio_path, output_path)
                result["method_used"] = "heygen"
                return result

            elif method == "wav2lip":
                result = await self._wav2lip_lipsync(video_path, audio_path, output_path)
                result["method_used"] = "wav2lip"
                return result

            else:
                raise ValueError(f"Invalid method: {method}. Use 'auto', 'heygen', or 'wav2lip'")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30)
    )
    async def _heygen_lipsync(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        HeyGen API를 사용한 립싱크 생성

        Args:
            video_path: 입력 영상 경로
            audio_path: 입력 오디오 경로
            output_path: 출력 영상 경로

        Returns:
            {
                "status": "success",
                "output_path": str,
                "duration": float,
                "cost_usd": float
            }
        """
        if not self.heygen_client:
            raise RuntimeError("HeyGen client not initialized")

        logger.info("Starting HeyGen lipsync generation")

        try:
            # 1. 영상/오디오 업로드
            video_url = await self._upload_to_heygen(video_path, "video")
            audio_url = await self._upload_to_heygen(audio_path, "audio")

            logger.info(f"Uploaded - video: {video_url}, audio: {audio_url}")

            # 2. 립싱크 작업 생성
            response = await self.heygen_client.post(
                "/lipsync/create",
                json={
                    "video_url": video_url,
                    "audio_url": audio_url,
                    "output_format": "mp4",
                    "quality": "high"
                }
            )
            response.raise_for_status()

            result = response.json()
            job_id = result.get("job_id")

            if not job_id:
                raise ValueError("HeyGen did not return job_id")

            logger.info(f"HeyGen job created: {job_id}")

            # 3. 작업 완료 대기 (polling)
            video_url = await self._wait_for_heygen_job(job_id)

            # 4. 결과 다운로드
            await self._download_video(video_url, output_path)

            # 5. 영상 길이 계산 (비용 산정)
            duration = await self._get_video_duration(output_path)
            cost_usd = duration * self.HEYGEN_COST_PER_SECOND

            logger.info(f"HeyGen lipsync completed - duration: {duration}s, cost: ${cost_usd:.2f}")

            return {
                "status": "success",
                "output_path": output_path,
                "duration": duration,
                "cost_usd": cost_usd
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HeyGen API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"HeyGen lipsync failed: {e}")
            raise

    async def _upload_to_heygen(self, file_path: str, file_type: str) -> str:
        """
        HeyGen에 파일 업로드

        Args:
            file_path: 파일 경로
            file_type: 파일 타입 ("video" | "audio")

        Returns:
            업로드된 파일 URL
        """
        if not self.heygen_client:
            raise RuntimeError("HeyGen client not initialized")

        logger.info(f"Uploading {file_type} to HeyGen: {file_path}")

        # 1. 업로드 URL 요청
        response = await self.heygen_client.post(
            "/upload/url",
            json={"file_type": file_type}
        )
        response.raise_for_status()

        upload_data = response.json()
        upload_url = upload_data.get("upload_url")
        file_url = upload_data.get("file_url")

        # 2. 파일 업로드
        with open(file_path, "rb") as f:
            async with httpx.AsyncClient() as client:
                upload_response = await client.put(
                    upload_url,
                    content=f.read()
                )
                upload_response.raise_for_status()

        logger.info(f"Uploaded {file_type}: {file_url}")

        return file_url

    async def _wait_for_heygen_job(
        self,
        job_id: str,
        max_wait: int = 600,
        poll_interval: int = 5
    ) -> str:
        """
        HeyGen 작업 완료 대기

        Args:
            job_id: 작업 ID
            max_wait: 최대 대기 시간 (초)
            poll_interval: 폴링 간격 (초)

        Returns:
            생성된 영상 URL
        """
        if not self.heygen_client:
            raise RuntimeError("HeyGen client not initialized")

        logger.info(f"Waiting for HeyGen job: {job_id}")

        elapsed = 0
        while elapsed < max_wait:
            response = await self.heygen_client.get(f"/lipsync/status/{job_id}")
            response.raise_for_status()

            status_data = response.json()
            status = status_data.get("status")

            if status == "completed":
                video_url = status_data.get("result_url")
                if not video_url:
                    raise ValueError("HeyGen job completed but no result_url")
                logger.info(f"HeyGen job completed: {video_url}")
                return video_url

            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                raise RuntimeError(f"HeyGen job failed: {error}")

            # 진행 중
            progress = status_data.get("progress", 0)
            logger.info(f"HeyGen job in progress: {progress}%")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"HeyGen job timeout after {max_wait}s")

    async def _wav2lip_lipsync(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Wav2Lip 로컬 실행 (Fallback)

        Args:
            video_path: 입력 영상 경로
            audio_path: 입력 오디오 경로
            output_path: 출력 영상 경로

        Returns:
            {
                "status": "success",
                "output_path": str,
                "duration": float
            }
        """
        logger.info("Starting Wav2Lip lipsync generation (local)")

        if not self.wav2lip_model_path or not Path(self.wav2lip_model_path).exists():
            raise FileNotFoundError(
                "Wav2Lip model not found. "
                "Please set WAV2LIP_MODEL_PATH or install Wav2Lip."
            )

        try:
            # Wav2Lip inference.py 실행
            # 주의: Wav2Lip는 별도 설치 필요
            cmd = [
                "python", "Wav2Lip/inference.py",
                "--checkpoint_path", self.wav2lip_model_path,
                "--face", video_path,
                "--audio", audio_path,
                "--outfile", output_path
            ]

            if self.gpu_enabled:
                # GPU 사용 시 추가 플래그
                cmd.extend(["--device", "cuda"])
            else:
                cmd.extend(["--device", "cpu"])

            logger.info(f"Running Wav2Lip: {' '.join(cmd)}")

            # 서브프로세스 실행
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Wav2Lip failed: {error_msg}")

            # 출력 파일 검증
            if not Path(output_path).exists():
                raise FileNotFoundError(f"Wav2Lip output not found: {output_path}")

            # 영상 길이 계산
            duration = await self._get_video_duration(output_path)

            logger.info(f"Wav2Lip lipsync completed - duration: {duration}s")

            return {
                "status": "success",
                "output_path": output_path,
                "duration": duration,
                "cost_usd": 0.0  # Wav2Lip는 무료
            }

        except Exception as e:
            logger.error(f"Wav2Lip lipsync failed: {e}")
            raise

    async def _download_video(self, video_url: str, output_path: str) -> None:
        """
        영상 다운로드

        Args:
            video_url: 영상 URL
            output_path: 저장 경로
        """
        logger.info(f"Downloading video from {video_url} to {output_path}")

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(video_url)
            response.raise_for_status()

            # 파일 저장
            Path(output_path).write_bytes(response.content)

            logger.info(f"Video downloaded: {output_path} ({len(response.content)} bytes)")

    async def _get_video_duration(self, video_path: str) -> float:
        """
        영상 길이 계산 (ffprobe 사용)

        Args:
            video_path: 영상 파일 경로

        Returns:
            영상 길이 (초)
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {stderr.decode()}")

            duration = float(stdout.decode().strip())
            return duration

        except Exception as e:
            logger.warning(f"Failed to get video duration: {e}, using default 10s")
            return 10.0  # 기본값

    async def check_lipsync_quality(self, video_path: str) -> Dict[str, float]:
        """
        립싱크 품질 평가 (선택적)

        Args:
            video_path: 평가할 영상 경로

        Returns:
            {
                "sync_score": float (0-1),
                "audio_quality": float (0-1),
                "video_quality": float (0-1)
            }

        Note:
            실제 구현 시 SyncNet 등의 모델 필요
            현재는 더미 구현
        """
        logger.info(f"Checking lipsync quality: {video_path}")

        # TODO: 실제 품질 평가 로직 구현
        # SyncNet 또는 유사 모델 사용

        return {
            "sync_score": 0.85,
            "audio_quality": 0.90,
            "video_quality": 0.88
        }

    async def close(self):
        """리소스 정리"""
        if self.heygen_client:
            await self.heygen_client.aclose()


# ==================== 싱글톤 인스턴스 ====================

_lipsync_service: Optional[LipsyncService] = None


def get_lipsync_service() -> LipsyncService:
    """
    LipsyncService 싱글톤 인스턴스

    Returns:
        LipsyncService 인스턴스
    """
    global _lipsync_service
    if _lipsync_service is None:
        _lipsync_service = LipsyncService()
    return _lipsync_service
