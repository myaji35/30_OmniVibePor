"""ElevenLabs TTS (Text-to-Speech) 서비스"""
from typing import Optional
import asyncio
from pathlib import Path
import hashlib
from elevenlabs import generate, Voice, VoiceSettings, set_api_key
from elevenlabs.api import History
from tenacity import retry, stop_after_attempt, wait_exponential
import logfire

from app.core.config import get_settings

settings = get_settings()
set_api_key(settings.ELEVENLABS_API_KEY)


class TTSService:
    """
import logging
    ElevenLabs Professional Voice Cloning TTS

    특징:
    - 29개 언어 지원 (한국어 포함)
    - 프로페셔널 음성 품질
    - 음성 클로닝 기능
    - 재시도 로직 (네트워크 오류 대응)
    - Logfire 비용 추적
    """

    # 기본 음성 ID (ElevenLabs의 사전 제작 음성)
    VOICE_IDS = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",      # 여성, 미국 영어
        "domi": "AZnzlk1XvdvUeBnXmlld",        # 여성, 미국 영어
        "bella": "EXAVITQu4vr4xnSDxMaL",       # 여성, 미국 영어
        "antoni": "ErXwobaYiN019PkySvjV",      # 남성, 미국 영어
        "elli": "MF3mGyEYCl7XYWbV9V6O",        # 여성, 미국 영어
        "josh": "TxGEqnHWrfWFTfGW9XjX",        # 남성, 미국 영어
        "arnold": "VR6AewLTigWG4xSOukaG",      # 남성, 미국 영어
        "adam": "pNInz6obpgDQGcFmaJgB",        # 남성, 미국 영어
        "sam": "yoZ06aMxZJJ28mfd3POQ",         # 남성, 미국 영어
    }

    def __init__(self, output_dir: str = "./outputs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> bytes:
        """
        TTS 오디오 생성

        Args:
            text: 변환할 텍스트
            voice_id: 음성 ID (기본값: rachel)
            model: ElevenLabs 모델 (multilingual_v2 권장)
            stability: 안정성 (0.0-1.0)
            similarity_boost: 유사도 부스트 (0.0-1.0)
            style: 스타일 강도 (0.0-1.0)
            use_speaker_boost: 스피커 부스트 활성화

        Returns:
            오디오 바이트 (MP3)
        """
        with self.logger.span("elevenlabs.generate_audio") as span:
            # 기본 음성 설정
            if voice_id is None:
                voice_id = self.VOICE_IDS["rachel"]

            # 텍스트 길이 로깅
            char_count = len(text)
            span.set_attribute("char_count", char_count)
            span.set_attribute("voice_id", voice_id)

            # 비동기 실행 (ElevenLabs SDK는 동기식)
            audio_bytes = await asyncio.to_thread(
                generate,
                text=text,
                voice=voice_id,
                model=model,
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost,
                    style=style,
                    use_speaker_boost=use_speaker_boost
                )
            )

            # 비용 추적 (대략 1000자당 $0.30)
            estimated_cost = (char_count / 1000) * 0.30
            self.logger.info(
                f"Generated {char_count} chars audio, estimated cost: ${estimated_cost:.4f}"
            )

            return audio_bytes

    async def save_audio(
        self,
        audio_bytes: bytes,
        filename: Optional[str] = None,
        text: Optional[str] = None
    ) -> str:
        """
        오디오 파일 저장

        Args:
            audio_bytes: 오디오 바이트
            filename: 저장할 파일명 (없으면 자동 생성)
            text: 원본 텍스트 (파일명 생성용)

        Returns:
            저장된 파일 경로
        """
        if filename is None:
            # 텍스트 해시로 파일명 생성
            if text:
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                filename = f"tts_{text_hash}.mp3"
            else:
                import time
                filename = f"tts_{int(time.time())}.mp3"

        file_path = self.output_dir / filename

        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        self.logger.info(f"Saved audio to {file_path}")
        return str(file_path)

    async def generate_and_save(
        self,
        text: str,
        voice_id: Optional[str] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        오디오 생성 후 바로 저장

        Args:
            text: 변환할 텍스트
            voice_id: 음성 ID
            filename: 저장할 파일명
            **kwargs: generate_audio에 전달할 추가 파라미터

        Returns:
            저장된 파일 경로
        """
        audio_bytes = await self.generate_audio(text, voice_id, **kwargs)
        file_path = await self.save_audio(audio_bytes, filename, text)
        return file_path

    def list_available_voices(self) -> dict:
        """사용 가능한 음성 목록"""
        return self.VOICE_IDS

    async def clone_voice(
        self,
        name: str,
        description: str,
        audio_files: list[str]
    ) -> str:
        """
        음성 클로닝 (Pro 플랜 이상 필요)

        Args:
            name: 음성 이름
            description: 음성 설명
            audio_files: 샘플 오디오 파일 경로 리스트

        Returns:
            생성된 음성 ID
        """
        # TODO: ElevenLabs 음성 클로닝 API 구현
        # 현재는 기본 음성만 사용
        raise NotImplementedError("Voice cloning requires Pro plan or higher")

    def get_usage_info(self) -> dict:
        """
        ElevenLabs API 사용량 조회

        Returns:
            사용량 정보 (문자 수, 비용 등)
        """
        # TODO: ElevenLabs API 사용량 조회 구현
        # History API 사용
        try:
            history = History.from_api()
            return {
                "total_characters": getattr(history, 'character_count', 0),
                "status": "active"
            }
        except Exception as e:
            self.logger.error(f"Failed to fetch usage info: {e}")
            return {"status": "error", "message": str(e)}


# 싱글톤 인스턴스
_tts_service_instance = None


def get_tts_service() -> TTSService:
    """TTS 서비스 싱글톤 인스턴스"""
    global _tts_service_instance
    if _tts_service_instance is None:
        _tts_service_instance = TTSService()
    return _tts_service_instance
