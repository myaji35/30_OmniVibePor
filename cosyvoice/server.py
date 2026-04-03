"""
CosyVoice2 REST API Server

FastAPI 기반 TTS 서버
- POST /tts          : 기본 TTS (사전 학습 음성)
- POST /tts/zero_shot : 제로샷 보이스 클로닝 (5초 레퍼런스)
- GET  /voices       : 사용 가능한 음성 목록
- GET  /health       : 헬스체크
"""

import argparse
import io
import os
import logging
import time
import uuid
from pathlib import Path

import torch
import torchaudio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CosyVoice2 TTS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model reference
cosyvoice_model = None
OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_model():
    """CosyVoice2 모델 로드"""
    global cosyvoice_model

    model_dir = os.environ.get("MODEL_DIR", "pretrained_models/CosyVoice2-0.5B")

    # Download if not exists
    if not os.path.exists(model_dir):
        logger.info("Model not found, downloading...")
        from download_model import MODEL_DIR  # triggers download
        model_dir = MODEL_DIR

    logger.info(f"Loading CosyVoice2 model from {model_dir}...")
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice2
        cosyvoice_model = CosyVoice2(model_dir, load_jit=False, load_trt=False)
        logger.info("CosyVoice2 model loaded successfully!")
    except ImportError:
        # Fallback: try AutoModel
        try:
            from cosyvoice.cli.model import AutoModel
            cosyvoice_model = AutoModel(model_dir)
            logger.info("CosyVoice2 model loaded via AutoModel!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise


@app.on_event("startup")
async def startup():
    load_model()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": cosyvoice_model is not None,
        "device": str(next(cosyvoice_model.model.parameters()).device)
        if cosyvoice_model
        else "none",
    }


@app.get("/voices")
async def list_voices():
    """사용 가능한 사전 학습 음성 목록"""
    # CosyVoice2-0.5B 기본 음성
    return {
        "voices": [
            {"id": "중문여성", "name": "Chinese Female", "language": "zh"},
            {"id": "중문남성", "name": "Chinese Male", "language": "zh"},
            {"id": "영문여성", "name": "English Female", "language": "en"},
            {"id": "영문남성", "name": "English Male", "language": "en"},
            {"id": "일문여성", "name": "Japanese Female", "language": "ja"},
            {"id": "한문여성", "name": "Korean Female", "language": "ko"},
            {"id": "한문남성", "name": "Korean Male", "language": "ko"},
        ],
        "supports_zero_shot": True,
        "supports_cross_lingual": True,
    }


@app.post("/tts")
async def text_to_speech(
    text: str = Form(..., description="변환할 텍스트"),
    voice: str = Form("한문남성", description="음성 ID"),
    speed: float = Form(1.0, description="속도 (0.5~2.0)"),
):
    """
    기본 TTS — 사전 학습 음성 사용

    Returns: audio/wav 스트림
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        start = time.time()
        logger.info(f"TTS request: {len(text)} chars, voice={voice}, speed={speed}")

        # Generate speech
        output_list = list(cosyvoice_model.inference_sft(text, voice, speed=speed))

        if not output_list:
            raise HTTPException(status_code=500, detail="No audio generated")

        # Concatenate all chunks
        audio_chunks = [chunk["tts_speech"] for chunk in output_list]
        audio = torch.cat(audio_chunks, dim=-1)

        # Convert to WAV bytes
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio, 22050, format="wav")
        buffer.seek(0)

        elapsed = time.time() - start
        logger.info(f"TTS completed in {elapsed:.2f}s, audio length: {audio.shape[-1] / 22050:.1f}s")

        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={
                "X-Audio-Duration": str(audio.shape[-1] / 22050),
                "X-Generation-Time": f"{elapsed:.2f}",
            },
        )

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/zero_shot")
async def zero_shot_tts(
    text: str = Form(..., description="변환할 텍스트"),
    prompt_text: str = Form(..., description="레퍼런스 음성의 대사"),
    prompt_audio: UploadFile = File(..., description="레퍼런스 음성 파일 (5~15초)"),
    speed: float = Form(1.0, description="속도"),
):
    """
    제로샷 보이스 클로닝 TTS

    5~15초 길이의 레퍼런스 음성으로 새로운 음성을 생성합니다.

    Returns: audio/wav 스트림
    """
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        start = time.time()
        logger.info(
            f"Zero-shot TTS: {len(text)} chars, prompt_text={len(prompt_text)} chars"
        )

        # Save uploaded audio temporarily
        temp_path = OUTPUT_DIR / f"ref_{uuid.uuid4().hex[:8]}.wav"
        audio_bytes = await prompt_audio.read()
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Load reference audio
        prompt_speech, sr = torchaudio.load(str(temp_path))
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            prompt_speech = resampler(prompt_speech)

        # Generate with zero-shot cloning
        output_list = list(
            cosyvoice_model.inference_zero_shot(
                text, prompt_text, prompt_speech, speed=speed
            )
        )

        # Cleanup temp file
        temp_path.unlink(missing_ok=True)

        if not output_list:
            raise HTTPException(status_code=500, detail="No audio generated")

        audio_chunks = [chunk["tts_speech"] for chunk in output_list]
        audio = torch.cat(audio_chunks, dim=-1)

        buffer = io.BytesIO()
        torchaudio.save(buffer, audio, 22050, format="wav")
        buffer.seek(0)

        elapsed = time.time() - start
        logger.info(
            f"Zero-shot TTS completed in {elapsed:.2f}s, "
            f"audio length: {audio.shape[-1] / 22050:.1f}s"
        )

        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={
                "X-Audio-Duration": str(audio.shape[-1] / 22050),
                "X-Generation-Time": f"{elapsed:.2f}",
            },
        )

    except Exception as e:
        logger.error(f"Zero-shot TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/save")
async def tts_and_save(
    text: str = Form(...),
    voice: str = Form("한문남성"),
    filename: str = Form(None),
    speed: float = Form(1.0),
):
    """TTS 생성 + 파일 저장 → 파일 경로 반환"""
    if cosyvoice_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        output_list = list(cosyvoice_model.inference_sft(text, voice, speed=speed))

        if not output_list:
            raise HTTPException(status_code=500, detail="No audio generated")

        audio_chunks = [chunk["tts_speech"] for chunk in output_list]
        audio = torch.cat(audio_chunks, dim=-1)

        if not filename:
            filename = f"tts_{uuid.uuid4().hex[:8]}.wav"

        file_path = OUTPUT_DIR / filename
        torchaudio.save(str(file_path), audio, 22050)

        return {
            "file_path": str(file_path),
            "filename": filename,
            "duration": audio.shape[-1] / 22050,
            "sample_rate": 22050,
        }

    except Exception as e:
        logger.error(f"TTS save failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9880)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
