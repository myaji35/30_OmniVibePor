"""Edge-TTS 서비스 — Microsoft 무료 TTS

edge-tts 라이브러리를 사용하여 무료 한국어 TTS를 제공합니다.
기존 TTSService와 동일한 인터페이스를 제공합니다.

특징:
- 완전 무료 (Microsoft Edge 읽기 엔진)
- 한국어 네이티브 지원 (InJoon 남성, SunHi 여성)
- API 키 불필요
- pip install edge-tts 만으로 사용 가능
"""

from typing import Optional
from pathlib import Path
import hashlib
import logging
import asyncio

import edge_tts

logger = logging.getLogger(__name__)

# 음성 매핑
VOICES = {
    "ko-male": "ko-KR-InJoonNeural",
    "ko-female": "ko-KR-SunHiNeural",
    "en-male": "en-US-GuyNeural",
    "en-female": "en-US-JennyNeural",
    "ja-female": "ja-JP-NanamiNeural",
    # ElevenLabs voice ID 호환 — 기본 한국어 남성으로 매핑
    "pNInz6obpgDQGcFmaJgB": "ko-KR-InJoonNeural",
    "EXAVITQu4vr4xnSDxMaL": "ko-KR-SunHiNeural",
    "cgSgspJ2msm6clMCkdW9": "ko-KR-SunHiNeural",
    "iP95p4xoKVk53GoZ742B": "ko-KR-InJoonNeural",
    "onwK4e9ZLuTAKqWW03F9": "ko-KR-InJoonNeural",
}

DEFAULT_VOICE = "ko-KR-InJoonNeural"


class EdgeTTSService:
    """Edge-TTS 서비스"""

    def __init__(self, output_dir: str = "./outputs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: str = "edge-tts",
        speed: float = 1.0,
        **kwargs,
    ) -> bytes:
        """텍스트를 오디오로 변환 (bytes 반환)"""
        voice = VOICES.get(voice_id or "", DEFAULT_VOICE)
        rate = f"+{int((speed - 1) * 100)}%" if speed >= 1 else f"-{int((1 - speed) * 100)}%"

        communicate = edge_tts.Communicate(text, voice, rate=rate)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        logger.info(f"Edge-TTS 생성 완료: voice={voice}, {len(text)}자 → {len(audio_data)} bytes")
        return audio_data

    async def generate_and_save(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_filename: Optional[str] = None,
        speed: float = 1.0,
        **kwargs,
    ) -> str:
        """텍스트를 오디오로 변환하고 파일로 저장"""
        audio_bytes = await self.generate_audio(text, voice_id=voice_id, speed=speed, **kwargs)

        if not output_filename:
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_filename = f"tts_{text_hash}.mp3"

        output_path = self.output_dir / output_filename
        output_path.write_bytes(audio_bytes)

        logger.info(f"Edge-TTS 파일 저장: {output_path}")
        return str(output_path)
