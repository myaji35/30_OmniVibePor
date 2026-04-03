"""CosyVoice2 TTS 서비스 — REST API 클라이언트

CosyVoice2 Docker 서버(port 9880)와 통신하여 TTS를 수행합니다.
기존 TTSService와 동일한 인터페이스를 제공합니다.

특징:
- 무료 (오픈소스 모델)
- 한국어 네이티브 지원
- 제로샷 보이스 클로닝 (5~15초 레퍼런스)
- 남성/여성 사전 학습 음성
"""

from typing import Optional
from pathlib import Path
import hashlib
import logging
import time
import io

import httpx
from pydub import AudioSegment

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# CosyVoice 서버 URL
COSYVOICE_URL = getattr(settings, "COSYVOICE_URL", None) or "http://cosyvoice:9880"

# 음성 매핑
VOICES = {
    "korean_male": "한문남성",
    "korean_female": "한문여성",
    "chinese_male": "중문남성",
    "chinese_female": "중문여성",
    "english_male": "영문남성",
    "english_female": "영문여성",
    "japanese_female": "일문여성",
}


class CosyVoiceTTSService:
    """CosyVoice2 TTS 서비스"""

    def __init__(self, output_dir: str = "./outputs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = COSYVOICE_URL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "cosyvoice2",
        speed: float = 1.0,
        **kwargs,
    ) -> bytes:
        """
        TTS 오디오 생성

        Args:
            text: 변환할 텍스트
            voice_id: 음성 ID (korean_male, korean_female 등)
            model: 무시됨 (CosyVoice2 고정)
            speed: 속도 (0.5~2.0)

        Returns:
            오디오 바이트 (MP3)
        """
        # 음성 매핑
        voice = VOICES.get(voice_id, "한문남성")

        logger.info(
            f"CosyVoice TTS: {len(text)} chars, voice={voice}, speed={speed}"
        )

        start = time.time()

        try:
            response = await self.client.post(
                f"{self.base_url}/tts",
                data={"text": text, "voice": voice, "speed": speed},
            )
            response.raise_for_status()

            wav_bytes = response.content
            duration = response.headers.get("X-Audio-Duration", "unknown")
            gen_time = response.headers.get("X-Generation-Time", "unknown")

            logger.info(
                f"CosyVoice TTS done: {time.time() - start:.2f}s, "
                f"audio_duration={duration}s, gen_time={gen_time}s"
            )

            # WAV → MP3 변환
            mp3_bytes = self._wav_to_mp3(wav_bytes)
            return mp3_bytes

        except httpx.ConnectError:
            logger.error(
                f"CosyVoice server not reachable at {self.base_url}. "
                "Is the cosyvoice Docker container running?"
            )
            raise ConnectionError(
                f"CosyVoice 서버({self.base_url})에 연결할 수 없습니다. "
                "docker-compose up cosyvoice 를 실행하세요."
            )
        except Exception as e:
            logger.error(f"CosyVoice TTS failed: {e}")
            raise

    async def generate_audio_zero_shot(
        self,
        text: str,
        prompt_text: str,
        prompt_audio_path: str,
        speed: float = 1.0,
    ) -> bytes:
        """
        제로샷 보이스 클로닝 TTS

        Args:
            text: 변환할 텍스트
            prompt_text: 레퍼런스 음성의 대사
            prompt_audio_path: 레퍼런스 음성 파일 경로 (5~15초)
            speed: 속도

        Returns:
            오디오 바이트 (MP3)
        """
        logger.info(
            f"CosyVoice Zero-shot: {len(text)} chars, ref={prompt_audio_path}"
        )

        with open(prompt_audio_path, "rb") as f:
            audio_file = f.read()

        try:
            response = await self.client.post(
                f"{self.base_url}/tts/zero_shot",
                data={
                    "text": text,
                    "prompt_text": prompt_text,
                    "speed": speed,
                },
                files={"prompt_audio": ("reference.wav", audio_file, "audio/wav")},
            )
            response.raise_for_status()

            wav_bytes = response.content
            mp3_bytes = self._wav_to_mp3(wav_bytes)

            logger.info(f"Zero-shot TTS done: {len(mp3_bytes)} bytes")
            return mp3_bytes

        except Exception as e:
            logger.error(f"Zero-shot TTS failed: {e}")
            raise

    async def save_audio(
        self,
        audio_bytes: bytes,
        filename: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """오디오 파일 저장"""
        if filename is None:
            if text:
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                filename = f"cosyvoice_{text_hash}.mp3"
            else:
                filename = f"cosyvoice_{int(time.time())}.mp3"

        file_path = self.output_dir / filename

        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        logger.info(f"Saved audio to {file_path}")
        return str(file_path)

    async def clone_voice(
        self,
        name: str,
        description: str,
        audio_files: list[str],
    ) -> str:
        """보이스 클로닝 — CosyVoice는 제로샷으로 처리"""
        logger.info(f"CosyVoice clone_voice called (name={name})")
        return f"cosyvoice_zero_shot:{audio_files[0]}"

    def get_available_voices(self) -> dict:
        """사용 가능한 음성 목록"""
        return {
            "korean_male": "한국어 남성",
            "korean_female": "한국어 여성",
            "english_male": "영어 남성",
            "english_female": "영어 여성",
            "chinese_male": "중국어 남성",
            "chinese_female": "중국어 여성",
            "japanese_female": "일본어 여성",
        }

    async def check_health(self) -> bool:
        """CosyVoice 서버 상태 확인"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            data = response.json()
            return data.get("model_loaded", False)
        except Exception:
            return False

    def _wav_to_mp3(self, wav_bytes: bytes) -> bytes:
        """WAV → MP3 변환"""
        audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        buffer = io.BytesIO()
        audio.export(buffer, format="mp3", bitrate="192k")
        return buffer.getvalue()


# 싱글톤
_cosyvoice_tts_instance = None


def get_cosyvoice_tts_service() -> CosyVoiceTTSService:
    global _cosyvoice_tts_instance
    if _cosyvoice_tts_instance is None:
        _cosyvoice_tts_instance = CosyVoiceTTSService()
    return _cosyvoice_tts_instance
