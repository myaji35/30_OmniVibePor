"""Whisper 토큰 타이밍 API — word-level timestamp 추출 및 ScriptBlock 매핑"""
import logging
import tempfile
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional

from app.services.stt_service import STTService
from app.services.whisper_timestamp_service import (
    extract_word_timestamps,
    map_timestamps_to_blocks,
    timestamps_to_remotion_sequence,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class WhisperTimingResponse(BaseModel):
    """Whisper 타이밍 응답"""
    text: str
    language: str
    duration: float
    words: list[dict]
    remotion_sequences: list[dict]
    blocks: list[dict]


class WhisperReanalyzeRequest(BaseModel):
    """Whisper 재분석 요청 (기존 오디오 URL 기반)"""
    audio_url: str = Field(..., description="오디오 파일 URL")
    language: str = Field("ko", description="언어 코드")
    block_types: list[str] = Field(
        default=["hook", "body", "cta"],
        description="ScriptBlock 타입 목록"
    )
    fps: int = Field(30, ge=1, le=60, description="Remotion FPS")


@router.post("/timing/extract", response_model=WhisperTimingResponse)
async def extract_timing(
    audio: UploadFile = File(...),
    language: str = Form("ko"),
    fps: int = Form(30),
    block_types: str = Form("hook,body,cta"),
):
    """
    오디오 파일에서 word-level timestamp 추출

    **워크플로우**:
    1. 오디오 파일 업로드
    2. Whisper API로 word-level transcription
    3. SubtitleToken[] 형태로 변환 (ms 단위)
    4. Remotion Sequence props 변환
    5. ScriptBlock 타이밍 매핑

    **오차 목표**: < 0.2초
    """
    tmp_path = None
    try:
        # 임시 파일 저장
        suffix = os.path.splitext(audio.filename or ".mp3")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Whisper STT (word-level timestamps)
        stt = STTService()
        result = await stt.transcribe_with_timestamps(
            audio_file_path=tmp_path,
            language=language,
        )

        # word-level timestamp 추출
        words = extract_word_timestamps(result)

        if not words:
            raise HTTPException(
                status_code=422,
                detail="Whisper가 단어를 감지하지 못했습니다. 오디오를 확인하세요."
            )

        # Remotion Sequence 변환
        remotion_seqs = timestamps_to_remotion_sequence(words, fps=fps)

        # ScriptBlock 매핑
        types_list = [t.strip() for t in block_types.split(",") if t.strip()]
        blocks = map_timestamps_to_blocks(words, block_types=types_list, fps=fps)

        # SubtitleToken 형태 (ms 단위)
        word_tokens = [
            {
                "index": i,
                "word": w.word,
                "startMs": round(w.start * 1000),
                "endMs": round(w.end * 1000),
            }
            for i, w in enumerate(words)
        ]

        total_duration = words[-1].end if words else 0.0

        return WhisperTimingResponse(
            text=" ".join(w.word for w in words),
            language=language,
            duration=total_duration,
            words=word_tokens,
            remotion_sequences=remotion_seqs,
            blocks=[
                {
                    "type": b.type,
                    "text": b.text,
                    "startTime": b.startTime,
                    "duration": b.duration,
                    "wordCount": len(b.words),
                }
                for b in blocks
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Whisper timing extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"타이밍 추출 실패: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/timing/reanalyze")
async def reanalyze_timing(request: WhisperReanalyzeRequest):
    """
    기존 오디오 URL로 Whisper 재분석

    ScriptSubtitleSync에서 'Whisper 재분석' 버튼 클릭 시 호출.
    URL에서 오디오를 다운로드 → word-level timestamp 추출.
    """
    try:
        import httpx

        # 오디오 다운로드
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(request.audio_url)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"오디오 다운로드 실패: HTTP {resp.status_code}"
                )
            audio_bytes = resp.content

        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            stt = STTService()
            result = await stt.transcribe_with_timestamps(
                audio_file_path=tmp_path,
                language=request.language,
            )

            words = extract_word_timestamps(result)

            if not words:
                raise HTTPException(
                    status_code=422,
                    detail="Whisper가 단어를 감지하지 못했습니다."
                )

            remotion_seqs = timestamps_to_remotion_sequence(words, fps=request.fps)
            blocks = map_timestamps_to_blocks(
                words, block_types=request.block_types, fps=request.fps
            )

            word_tokens = [
                {
                    "index": i,
                    "word": w.word,
                    "startMs": round(w.start * 1000),
                    "endMs": round(w.end * 1000),
                }
                for i, w in enumerate(words)
            ]

            return {
                "text": " ".join(w.word for w in words),
                "language": request.language,
                "duration": words[-1].end if words else 0.0,
                "words": word_tokens,
                "remotion_sequences": remotion_seqs,
                "blocks": [
                    {
                        "type": b.type,
                        "text": b.text,
                        "startTime": b.startTime,
                        "duration": b.duration,
                        "wordCount": len(b.words),
                    }
                    for b in blocks
                ],
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Whisper reanalyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"재분석 실패: {str(e)}")
