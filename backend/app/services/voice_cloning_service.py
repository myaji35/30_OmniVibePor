"""ElevenLabs Voice Cloning 서비스"""
from typing import Optional, List, Dict, BinaryIO
import asyncio
import logging
from pathlib import Path
import hashlib
import time
from elevenlabs import ElevenLabs, Voice
from tenacity import retry, stop_after_attempt, wait_exponential
import logfire

from app.core.config import get_settings

settings = get_settings()


class VoiceCloningService:
    """
    ElevenLabs Professional Voice Cloning

    특징:
    - 사용자의 녹음 파일로 커스텀 음성 생성
    - 1분 이상 오디오 샘플 권장 (최고 품질: 3-5분)
    - 학습된 음성으로 무제한 TTS 생성 가능
    - 음성 삭제, 수정 지원
    - Logfire 비용 추적

    요구사항:
    - ElevenLabs Pro 플랜 이상
    - MP3, WAV, M4A 등 오디오 파일
    - 22050 Hz 이상 샘플레이트
    - 깨끗한 녹음 (배경 노이즈 최소화)
    """

    def __init__(self, upload_dir: str = "./uploads/voices"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def clone_voice(
        self,
        name: str,
        audio_file_path: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        음성 클로닝 - 오디오 파일로 커스텀 음성 생성

        Args:
            name: 음성 이름 (예: "김대표님", "narrator_voice")
            audio_file_path: 샘플 오디오 파일 경로
            description: 음성 설명 (선택)
            labels: 메타데이터 라벨 (예: {"user_id": "user123", "gender": "male"})

        Returns:
            {
                "voice_id": "V_abc123...",
                "name": "김대표님",
                "status": "ready",
                "created_at": "2026-02-01T12:00:00Z"
            }

        Raises:
            FileNotFoundError: 오디오 파일이 없을 때
            ValueError: 잘못된 파일 형식
        """
        with self.logger.span("elevenlabs.clone_voice") as span:
            # 파일 존재 확인
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            # 파일 크기 확인
            file_size = audio_path.stat().st_size
            span.set_attribute("file_size_bytes", file_size)
            span.set_attribute("voice_name", name)

            self.logger.info(f"Starting voice cloning: {name} ({file_size / 1024 / 1024:.2f} MB)")

            # ElevenLabs Voice Cloning API 호출
            try:
                with open(audio_file_path, "rb") as audio_file:
                    voice = await asyncio.to_thread(
                        self.client.voices.add,
                        name=name,
                        files=[audio_file],
                        description=description or f"Custom voice cloned from user audio",
                        labels=labels or {}
                    )

                voice_data = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "status": "ready",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }

                self.logger.info(f"Voice cloned successfully: {voice_data['voice_id']}")

                # 비용 추적 (음성 클로닝은 무료, TTS 사용 시 과금)
                span.set_attribute("voice_id", voice_data["voice_id"])

                return voice_data

            except Exception as e:
                self.logger.error(f"Voice cloning failed: {str(e)}")
                raise

    async def get_voice_info(self, voice_id: str) -> Dict:
        """
        음성 정보 조회

        Args:
            voice_id: 음성 ID

        Returns:
            {
                "voice_id": "V_abc123...",
                "name": "김대표님",
                "category": "cloned",
                "description": "...",
                "labels": {...}
            }
        """
        try:
            voice = await asyncio.to_thread(
                self.client.voices.get,
                voice_id=voice_id
            )

            return {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": getattr(voice, 'description', ''),
                "labels": getattr(voice, 'labels', {})
            }
        except Exception as e:
            self.logger.error(f"Failed to get voice info: {str(e)}")
            raise

    async def list_user_voices(self, user_id: str) -> List[Dict]:
        """
        사용자의 모든 커스텀 음성 조회

        Args:
            user_id: 사용자 ID

        Returns:
            [
                {
                    "voice_id": "V_abc123...",
                    "name": "김대표님",
                    "created_at": "2026-02-01T12:00:00Z"
                },
                ...
            ]
        """
        try:
            # ElevenLabs API로 모든 음성 조회
            voices_response = await asyncio.to_thread(
                self.client.voices.get_all
            )

            # 사용자 음성 필터링 (labels에 user_id가 있는 것만)
            user_voices = []
            for voice in voices_response.voices:
                labels = getattr(voice, 'labels', {})
                if labels.get('user_id') == user_id:
                    user_voices.append({
                        "voice_id": voice.voice_id,
                        "name": voice.name,
                        "category": voice.category,
                        "description": getattr(voice, 'description', ''),
                        "created_at": labels.get('created_at', '')
                    })

            return user_voices

        except Exception as e:
            self.logger.error(f"Failed to list user voices: {str(e)}")
            return []

    async def delete_voice(self, voice_id: str) -> bool:
        """
        음성 삭제

        Args:
            voice_id: 삭제할 음성 ID

        Returns:
            성공 여부
        """
        try:
            await asyncio.to_thread(
                self.client.voices.delete,
                voice_id=voice_id
            )

            self.logger.info(f"Voice deleted: {voice_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete voice: {str(e)}")
            return False

    async def save_uploaded_file(
        self,
        file_data: bytes,
        user_id: str,
        original_filename: str
    ) -> str:
        """
        업로드된 오디오 파일 저장

        Args:
            file_data: 파일 바이트
            user_id: 사용자 ID
            original_filename: 원본 파일명

        Returns:
            저장된 파일 경로
        """
        # 파일명 생성 (충돌 방지)
        timestamp = int(time.time())
        file_hash = hashlib.md5(file_data).hexdigest()[:8]
        file_ext = Path(original_filename).suffix or ".mp3"

        filename = f"{user_id}_{timestamp}_{file_hash}{file_ext}"
        file_path = self.upload_dir / filename

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(file_data)

        self.logger.info(f"Saved uploaded file: {file_path} ({len(file_data) / 1024:.2f} KB)")

        return str(file_path)

    async def validate_audio_file(self, file_path: str) -> Dict[str, any]:
        """
        오디오 파일 검증

        Args:
            file_path: 오디오 파일 경로

        Returns:
            {
                "valid": True,
                "duration_seconds": 65.3,
                "file_size_mb": 1.2,
                "format": "mp3",
                "warnings": []
            }
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "valid": False,
                "error": "File not found"
            }

        file_size_mb = path.stat().st_size / 1024 / 1024
        file_ext = path.suffix.lower()

        warnings = []

        # 파일 크기 확인 (10MB 이상 권장)
        if file_size_mb < 1:
            warnings.append("Audio file is small. Recommend 3-5 minutes for best quality.")

        # 파일 형식 확인
        valid_formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        if file_ext not in valid_formats:
            return {
                "valid": False,
                "error": f"Invalid format. Supported: {', '.join(valid_formats)}"
            }

        # TODO: 실제 오디오 길이 분석 (librosa 또는 pydub 사용)
        # 현재는 파일 크기로 추정 (MP3: 약 1MB/분)
        estimated_duration = file_size_mb * 60 if file_ext == '.mp3' else file_size_mb * 10

        if estimated_duration < 60:
            warnings.append("Audio duration is less than 1 minute. Recommend 3+ minutes.")

        return {
            "valid": True,
            "duration_seconds": estimated_duration,
            "file_size_mb": round(file_size_mb, 2),
            "format": file_ext[1:],
            "warnings": warnings
        }


# 싱글톤 인스턴스
_voice_cloning_service_instance = None


def get_voice_cloning_service() -> VoiceCloningService:
    """Voice Cloning 서비스 싱글톤 인스턴스"""
    global _voice_cloning_service_instance
    if _voice_cloning_service_instance is None:
        _voice_cloning_service_instance = VoiceCloningService()
    return _voice_cloning_service_instance
