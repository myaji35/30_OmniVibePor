"""OpenAI TTS (Text-to-Speech) 서비스"""
from typing import Optional
import asyncio
from pathlib import Path
import hashlib
import logging
from contextlib import nullcontext
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class TTSService:
    """
    OpenAI TTS 서비스

    특징:
    - 6가지 음성 지원 (alloy, echo, fable, onyx, nova, shimmer)
    - 한국어 지원 우수
    - 저렴한 비용 ($0.015/1000자)
    - 고품질 음성 (tts-1-hd 모델 사용 가능)
    """

    # OpenAI TTS 음성 옵션
    VOICES = {
        "alloy": "alloy",      # 중성적
        "echo": "echo",        # 남성
        "fable": "fable",      # 영국식
        "onyx": "onyx",        # 남성, 깊은 목소리
        "nova": "nova",        # 여성
        "shimmer": "shimmer",  # 여성, 부드러움
    }

    def __init__(self, output_dir: str = "./outputs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "tts-1",  # tts-1 (빠름, 저렴) or tts-1-hd (고품질)
        **kwargs
    ) -> bytes:
        """
        TTS 오디오 생성

        Args:
            text: 변환할 텍스트
            voice_id: 음성 ID (alloy, echo, fable, onyx, nova, shimmer)
            model: OpenAI TTS 모델 (tts-1 또는 tts-1-hd)
            **kwargs: 호환성을 위한 추가 파라미터 (무시됨)

        Returns:
            오디오 바이트 (MP3)
        """
        span_context = logfire.span("openai.tts.generate") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context:
            # 기본 음성 설정
            if voice_id is None or voice_id not in self.VOICES:
                voice_id = "alloy"

            # 텍스트 길이 로깅
            char_count = len(text)
            self.logger.info(
                f"Generating TTS with OpenAI: {char_count} chars, voice={voice_id}, model={model}"
            )

            try:
                # OpenAI TTS API 호출
                response = await client.audio.speech.create(
                    model=model,
                    voice=voice_id,
                    input=text,
                    response_format="mp3"
                )

                # 스트림을 bytes로 변환
                audio_bytes = response.content

                # 비용 추적 ($0.015/1000 chars for tts-1, $0.030/1000 for tts-1-hd)
                cost_per_1k = 0.015 if model == "tts-1" else 0.030
                estimated_cost = (char_count / 1000) * cost_per_1k

                self.logger.info(
                    f"Generated {len(audio_bytes)} bytes audio, "
                    f"estimated cost: ${estimated_cost:.4f}"
                )

                return audio_bytes

            except Exception as e:
                self.logger.error(f"OpenAI TTS generation failed: {e}")
                raise

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

    async def clone_voice(
        self,
        name: str,
        description: str,
        audio_files: list[str]
    ) -> str:
        """
        음성 클로닝 (OpenAI TTS는 미지원)

        OpenAI TTS는 사전 정의된 6개 음성만 사용 가능합니다.
        음성 클로닝이 필요한 경우 ElevenLabs 등 다른 서비스를 사용하세요.
        """
        raise NotImplementedError(
            "OpenAI TTS does not support voice cloning. "
            "Use one of the 6 built-in voices: alloy, echo, fable, onyx, nova, shimmer"
        )

    def get_available_voices(self) -> dict:
        """사용 가능한 음성 목록 반환"""
        return {
            "alloy": "중성적인 목소리",
            "echo": "남성 목소리",
            "fable": "영국식 악센트",
            "onyx": "남성, 깊은 목소리",
            "nova": "여성 목소리",
            "shimmer": "여성, 부드러운 목소리"
        }


# 싱글톤 인스턴스
_tts_service_instance = None


def get_tts_service() -> TTSService:
    """TTS 서비스 싱글톤 인스턴스"""
    global _tts_service_instance
    if _tts_service_instance is None:
        _tts_service_instance = TTSService()
    return _tts_service_instance
