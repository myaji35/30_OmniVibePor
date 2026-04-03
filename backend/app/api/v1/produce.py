"""멀티포맷 콘텐츠 생산 API — 영상 + 프레젠테이션 + 나레이션

ISS-009: Phase 5.3
"""
import logging
import os
import tempfile
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/produce", tags=["Content Production"])
logger = logging.getLogger(__name__)


class ProduceRequest(BaseModel):
    """콘텐츠 생산 요청"""
    script: str = Field(..., min_length=1, description="스크립트 텍스트")
    brand_name: str = Field("OmniVibe Pro", description="브랜드명")
    channel: str = Field("youtube", description="채널 (youtube, instagram, tiktok, blog)")
    format: str = Field("presentation", description="출력 포맷 (video, presentation, narration)")
    title: Optional[str] = Field(None, description="제목")
    theme: str = Field("dark", description="테마 (dark, light, corporate)")
    voice: str = Field("ko-KR-SunHiNeural", description="나레이션 음성")
    voice_rate: str = Field("-5%", description="음성 속도")


@router.post("/presentation")
async def produce_presentation(request: ProduceRequest):
    """
    스크립트 → 프레젠테이션 HTML 자동 생성

    키보드 방향키로 슬라이드 넘김 가능.
    브라우저에서 Ctrl+P로 PDF 저장 가능.
    """
    try:
        from app.services.presentation_generator import get_presentation_generator
        gen = get_presentation_generator()
        result = await gen.generate(
            script=request.script,
            brand_name=request.brand_name,
            title=request.title,
            theme=request.theme,
        )
        return result
    except Exception as e:
        logger.error(f"Presentation generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/narration")
async def produce_narration(request: ProduceRequest):
    """
    스크립트 → 나레이션 MP3 자동 생성 (edge-tts, 무료)
    """
    try:
        import edge_tts
        import asyncio

        output_dir = os.path.join(os.path.dirname(__file__), "../../../outputs/narrations")
        os.makedirs(output_dir, exist_ok=True)

        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"narration_{ts}.mp3"
        filepath = os.path.join(output_dir, filename)

        communicate = edge_tts.Communicate(
            text=request.script,
            voice=request.voice,
            rate=request.voice_rate,
        )

        submaker = edge_tts.SubMaker()
        with open(filepath, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # SRT 자막
        srt_path = filepath.replace(".mp3", ".srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(submaker.get_srt())

        size = os.path.getsize(filepath)
        logger.info(f"Narration generated: {filename} ({size//1024}KB)")

        return {
            "filename": filename,
            "download_url": f"/outputs/narrations/{filename}",
            "srt_url": f"/outputs/narrations/{filename.replace('.mp3', '.srt')}",
            "size": size,
            "size_human": f"{size//1024}KB",
            "voice": request.voice,
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="edge-tts가 설치되지 않았습니다: pip install edge-tts")
    except Exception as e:
        logger.error(f"Narration generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_tts_voices():
    """사용 가능한 한국어 TTS 음성 목록"""
    return {
        "voices": [
            {"id": "ko-KR-SunHiNeural", "name": "선희", "gender": "여성", "desc": "밝고 명확, 나레이션 최적"},
            {"id": "ko-KR-InJoonNeural", "name": "인준", "gender": "남성", "desc": "안정적, 뉴스 톤"},
            {"id": "ko-KR-BongJinNeural", "name": "봉진", "gender": "남성", "desc": "차분한 톤"},
            {"id": "ko-KR-YuJinNeural", "name": "유진", "gender": "여성", "desc": "젊은 여성"},
            {"id": "ko-KR-SeoHyeonNeural", "name": "서현", "gender": "여성", "desc": "전문적"},
            {"id": "ko-KR-GookMinNeural", "name": "국민", "gender": "남성", "desc": "젊은 남성"},
            {"id": "ko-KR-JiMinNeural", "name": "지민", "gender": "여성", "desc": "부드러운 톤"},
            {"id": "ko-KR-SoonBokNeural", "name": "순복", "gender": "여성", "desc": "따뜻한 톤"},
        ]
    }
