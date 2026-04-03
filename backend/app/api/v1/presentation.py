"""Presentation API 엔드포인트"""
import asyncio
import logging
import re
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
import uuid

from app.models.presentation import (
    PresentationUploadRequest,
    PresentationUploadResponse,
    GenerateScriptRequest,
    GenerateScriptResponse,
    GenerateAudioRequest,
    GenerateAudioResponse,
    AnalyzeTimingRequest,
    AnalyzeTimingResponse,
    GenerateVideoRequest,
    GenerateVideoResponse,
    PresentationDetailResponse,
    PresentationListResponse,
    SlideInfo,
    PresentationStatus,
    PresentationModel
)
from app.services.pdf_to_slides_service import get_pdf_to_slides_service
from app.services.slide_to_script_converter import SlideToScriptConverter
from app.services.tts_service import get_tts_service
from app.services.stt_service import get_stt_service

# Optional imports (graceful fallback)
try:
    from app.services.slide_timing_analyzer import SlideTimingAnalyzer
except ImportError:
    SlideTimingAnalyzer = None

try:
    from app.services.presentation_video_generator import get_video_generator
except ImportError:
    get_video_generator = None

try:
    from app.tasks.presentation_tasks import generate_presentation_video_task
except ImportError:
    generate_presentation_video_task = None

# In-memory presentation store (replaces Neo4j for local dev)
_presentations: dict = {}

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 헬퍼 함수
# ============================================================

def _substitute_variables(text: str, variables: dict) -> str:
    """
    {{변수명}} 패턴을 실제 값으로 치환한다.

    지원 변수:
        presentation_title  : PDF 파일명 or 첫 슬라이드 OCR 텍스트 앞 50자
        date                : 현재 날짜 (YYYY년 MM월)
        slide_count         : 슬라이드 수
        author              : project_id
    """
    def replacer(match):
        key = match.group(1).strip()
        return str(variables.get(key, match.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", replacer, text)


def _build_variables(pdata: dict) -> dict:
    """presentation 데이터에서 변수 딕셔너리를 구성한다."""
    import datetime

    # presentation_title: pdf_path에서 줄기 이름, 없으면 첫 슬라이드 OCR
    pdf_path = pdata.get("pdf_path", "")
    title = Path(pdf_path).stem if pdf_path else "발표자료"
    slides = pdata.get("slides_data", [])
    if not title and slides:
        first_ocr = (slides[0].get("ocr_text") or "").strip()
        title = first_ocr[:50] if first_ocr else "발표자료"

    now = datetime.datetime.now()
    return {
        "presentation_title": title,
        "date": now.strftime("%Y년 %m월"),
        "slide_count": str(len(slides)),
        "author": pdata.get("project_id", ""),
    }


def _generate_title_image(
    output_path: str,
    title: str,
    subtitle: str,
    bg_color: str = "#16325C",
    width: int = 1920,
    height: int = 1080,
) -> None:
    """
    PIL을 사용해 단색 배경 + 제목/부제목 이미지를 생성한다.
    한국어 폰트가 없으면 기본 폰트로 fallback한다.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed — skipping title image generation")
        raise

    # hex → RGB 변환
    hex_color = bg_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    img = Image.new("RGB", (width, height), (r, g, b))
    draw = ImageDraw.Draw(img)

    # 폰트 탐색 (한국어 우선, 없으면 기본 폰트)
    korean_fonts = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",       # macOS
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Ubuntu
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/Windows/Fonts/malgun.ttf",                         # Windows
    ]

    title_font = None
    subtitle_font = None
    for font_path in korean_fonts:
        if Path(font_path).exists():
            try:
                title_font = ImageFont.truetype(font_path, 80)
                subtitle_font = ImageFont.truetype(font_path, 40)
                break
            except Exception:
                continue

    if title_font is None:
        # 기본 폰트 fallback (크기 지정 불가)
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # 제목 — 수직 중앙에서 약간 위
    _draw_centered_text(draw, title, title_font, (255, 255, 255), width, height // 2 - 60)

    # 부제목 — 제목 아래
    if subtitle:
        _draw_centered_text(draw, subtitle, subtitle_font, (200, 200, 200), width, height // 2 + 60)

    img.save(output_path, "PNG")


def _draw_centered_text(draw, text: str, font, color, canvas_width: int, y: int) -> None:
    """텍스트를 수평 중앙 정렬로 그린다."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
    except AttributeError:
        # 구버전 Pillow
        text_width, _ = draw.textsize(text, font=font)

    x = (canvas_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)


async def _generate_segment_video(
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
) -> None:
    """
    단일 이미지 + 오디오 → MP4 세그먼트를 생성한다.
    audio_path가 비어 있으면 무음으로 처리한다.
    """
    import subprocess

    # concat 방식: 단일 이미지를 duration 동안 표시
    concat_tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    abs_image = str(Path(image_path).resolve())
    concat_tmp.write(f"file '{abs_image}'\n")
    concat_tmp.write(f"duration {duration}\n")
    concat_tmp.write(f"file '{abs_image}'\n")  # FFmpeg 마지막 프레임 반복 필요
    concat_tmp.close()

    if audio_path and Path(audio_path).exists():
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_tmp.name,
            "-i", str(Path(audio_path).resolve()),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            output_path,
        ]
    else:
        # 무음 — 지정 duration 사용
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_tmp.name,
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            "-movflags", "+faststart",
            output_path,
        ]

    result = await asyncio.to_thread(
        subprocess.run, cmd, capture_output=True, text=True, timeout=120
    )
    Path(concat_tmp.name).unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg segment failed: {result.stderr[-400:]}")


@router.post("/upload", response_model=PresentationUploadResponse)
async def upload_presentation(
    file: UploadFile = File(..., description="PDF 파일"),
    project_id: str = Form(..., description="프로젝트 ID"),
    dpi: int = Form(200, description="슬라이드 이미지 해상도 (DPI)"),
    lang: str = Form("kor+eng", description="OCR 언어"),
    template_id: Optional[str] = Form(None, description="브랜드 템플릿 ID (인트로/아웃트로 적용)"),
):
    """
    1. PDF 업로드 및 처리

    **워크플로우**:
    1. PDF 파일 저장
    2. PDF를 개별 슬라이드 이미지로 변환
    3. OCR로 텍스트 추출 (선택적)
    4. Neo4j에 프리젠테이션 생성

    **출력**: presentation_id, 슬라이드 목록
    """
    try:
        from urllib.parse import unquote
        
        logger.info(f"Uploading presentation PDF: {file.filename}, project_id: {project_id}")

        # PDF 파일 읽기
        pdf_bytes = await file.read()

        # PDF 저장
        pdf_service = get_pdf_to_slides_service()
        # UTF-8 URL 인코딩된 파일명 복호화
        decoded_filename = unquote(file.filename)
        
        pdf_path = await pdf_service.save_uploaded_pdf(
            file_data=pdf_bytes,
            user_id=project_id,
            original_filename=decoded_filename
        )

        # PDF → 슬라이드 이미지 변환
        image_paths = await pdf_service.convert_pdf_to_images(
            pdf_path=pdf_path,
            dpi=dpi
        )

        # OCR 텍스트 추출
        ocr_texts = await pdf_service.extract_text_from_slides(
            image_paths=image_paths,
            lang=lang
        )

        # 슬라이드 정보 생성
        slides = []
        for i, image_path in enumerate(image_paths, start=1):
            slides.append(
                SlideInfo(
                    slide_number=i,
                    image_path=image_path,
                    ocr_text=ocr_texts[i - 1] if i - 1 < len(ocr_texts) else None
                )
            )

        # 프리젠테이션 ID 생성
        presentation_id = f"pres_{uuid.uuid4().hex[:12]}"

        # In-memory 저장 (로컬 개발용, 프로덕션은 Neo4j)
        import datetime
        _presentations[presentation_id] = {
            "presentation_id": presentation_id,
            "project_id": project_id,
            "pdf_path": pdf_path,
            "total_slides": len(slides),
            "slides_data": [slide.model_dump() for slide in slides],
            "status": PresentationStatus.UPLOADED.value,
            "full_script": None,
            "audio_path": None,
            "video_path": None,
            "template_id": template_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "metadata": {},
        }

        logger.info(
            f"Presentation uploaded: {presentation_id}, "
            f"total_slides: {len(slides)}"
        )

        return PresentationUploadResponse(
            presentation_id=presentation_id,
            pdf_path=pdf_path,
            total_slides=len(slides),
            slides=slides,
            status=PresentationStatus.UPLOADED
        )

    except Exception as e:
        logger.error(f"Presentation upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{presentation_id}/generate-script", response_model=GenerateScriptResponse)
async def generate_script(
    presentation_id: str,
    request: GenerateScriptRequest
):
    """2. 나레이션 스크립트 생성 (인메모리)"""
    try:
        logger.info(f"Generating script for presentation: {presentation_id}")

        if presentation_id not in _presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")

        presentation_data = _presentations[presentation_id]

        # SlideData 모델로 변환
        from app.services.slide_to_script_converter import SlideData, ToneType
        slide_models = []
        for s in presentation_data["slides_data"]:
            ocr_text = s.get("ocr_text") or ""
            # OCR 텍스트가 있으면 활용, 없으면 더미
            title = ocr_text[:50] if ocr_text else f"슬라이드 {s['slide_number']}"
            content = ocr_text if ocr_text else f"슬라이드 {s['slide_number']} 내용"
            slide_models.append(SlideData(
                slide_number=s["slide_number"],
                title=title,
                content=content,
            ))

        converter = SlideToScriptConverter()
        script_result = await converter.convert_slides_to_script(
            slides=slide_models,
            tone=ToneType(request.tone or "professional"),
            target_duration_per_slide=request.target_duration_per_slide or 15.0
        )

        # 슬라이드 정보 업데이트
        slides_with_script = []
        for i, slide_data in enumerate(presentation_data["slides_data"]):
            script_text = script_result.slide_scripts[i]["script"] if i < len(script_result.slide_scripts) else ""
            duration = script_result.slide_scripts[i].get("estimated_duration", 15.0) if i < len(script_result.slide_scripts) else 15.0
            slides_with_script.append(
                SlideInfo(
                    slide_number=slide_data["slide_number"],
                    image_path=slide_data["image_path"],
                    ocr_text=slide_data.get("ocr_text"),
                    script=script_text,
                    duration=duration
                )
            )

        # 인메모리 업데이트
        import datetime
        _presentations[presentation_id]["full_script"] = script_result.full_script
        _presentations[presentation_id]["slides_data"] = [s.model_dump() for s in slides_with_script]
        _presentations[presentation_id]["status"] = PresentationStatus.SCRIPT_GENERATED.value
        _presentations[presentation_id]["updated_at"] = datetime.datetime.now().isoformat()

        logger.info(f"Script generated: {presentation_id}, total_duration: {script_result.total_duration:.1f}s")

        return GenerateScriptResponse(
            presentation_id=presentation_id,
            full_script=script_result.full_script,
            slides=slides_with_script,
            estimated_total_duration=script_result.total_duration,
            status=PresentationStatus.SCRIPT_GENERATED
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{presentation_id}/generate-audio", response_model=GenerateAudioResponse)
async def generate_audio(
    presentation_id: str,
    request: GenerateAudioRequest
):
    """3. TTS 오디오 생성 (인메모리 + CosyVoice/OpenAI)"""
    try:
        logger.info(f"Generating audio for presentation: {presentation_id}")

        if presentation_id not in _presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")

        presentation_data = _presentations[presentation_id]

        script = request.script or presentation_data.get("full_script")
        if not script:
            raise HTTPException(status_code=400, detail="No script available. Generate script first.")

        # TTS 오디오 생성
        tts_service = get_tts_service()
        voice_id = request.voice_id or "korean_male"
        audio_bytes = await tts_service.generate_audio(
            text=script,
            voice_id=voice_id,
            model=request.model or "cosyvoice2"
        )

        # 오디오 저장
        audio_filename = f"{presentation_id}.mp3"
        audio_path = await tts_service.save_audio(
            audio_bytes=audio_bytes,
            filename=audio_filename,
            text=script
        )

        # STT 검증 (선택적 — Whisper 없으면 스킵)
        whisper_result = {"text": "", "duration": 0.0, "segments": []}
        accuracy = 0.0
        try:
            stt_service = get_stt_service()
            whisper_result = await stt_service.transcribe_with_timestamps(
                audio_file_path=audio_path, language="ko"
            )
            from difflib import SequenceMatcher
            accuracy = SequenceMatcher(None, script, whisper_result["text"]).ratio()
        except Exception as stt_err:
            logger.warning(f"STT verification skipped: {stt_err}")
            # 오디오 길이를 스크립트 기반으로 추정 (한국어 ~4자/초)
            whisper_result["duration"] = len(script) / 4.0

        # 인메모리 업데이트
        import datetime
        _presentations[presentation_id]["audio_path"] = audio_path
        _presentations[presentation_id]["status"] = PresentationStatus.AUDIO_GENERATED.value
        _presentations[presentation_id]["updated_at"] = datetime.datetime.now().isoformat()
        _presentations[presentation_id]["metadata"]["whisper_result"] = whisper_result

        logger.info(f"Audio generated: {presentation_id}, duration: {whisper_result['duration']:.1f}s")

        return GenerateAudioResponse(
            presentation_id=presentation_id,
            audio_path=audio_path,
            duration=whisper_result["duration"],
            whisper_result=whisper_result,
            accuracy=accuracy,
            status=PresentationStatus.AUDIO_GENERATED
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{presentation_id}/analyze-timing", response_model=AnalyzeTimingResponse)
async def analyze_timing(
    presentation_id: str,
    request: AnalyzeTimingRequest
):
    """4. 슬라이드 타이밍 분석 (인메모리 — 스크립트 기반 균등 분배)"""
    try:
        logger.info(f"Analyzing timing for presentation: {presentation_id}")

        if presentation_id not in _presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")

        presentation_data = _presentations[presentation_id]
        slides_data = presentation_data["slides_data"]

        # 스크립트 기반 타이밍 계산 (글자 수 비례 배분)
        total_chars = sum(len(s.get("script") or "") for s in slides_data)
        total_audio_duration = presentation_data.get("metadata", {}).get("whisper_result", {}).get("duration", 0)
        if total_audio_duration <= 0:
            # 추정: 한국어 ~4자/초
            total_audio_duration = total_chars / 4.0 if total_chars > 0 else len(slides_data) * 15.0

        slides_with_timing = []
        current_time = 0.0

        for slide_data in slides_data:
            script_len = len(slide_data.get("script") or "")
            ratio = script_len / total_chars if total_chars > 0 else 1.0 / len(slides_data)
            duration = round(total_audio_duration * ratio, 1)

            slides_with_timing.append(
                SlideInfo(
                    slide_number=slide_data["slide_number"],
                    image_path=slide_data["image_path"],
                    script=slide_data.get("script"),
                    start_time=round(current_time, 1),
                    end_time=round(current_time + duration, 1),
                    duration=duration,
                )
            )
            current_time += duration

        total_duration = round(current_time, 1)

        # 인메모리 업데이트
        import datetime
        _presentations[presentation_id]["slides_data"] = [s.model_dump() for s in slides_with_timing]
        _presentations[presentation_id]["status"] = PresentationStatus.TIMING_ANALYZED.value
        _presentations[presentation_id]["updated_at"] = datetime.datetime.now().isoformat()

        logger.info(f"Timing analyzed: {presentation_id}, total_duration: {total_duration:.1f}s")

        return AnalyzeTimingResponse(
            presentation_id=presentation_id,
            slides=slides_with_timing,
            total_duration=total_duration,
            status=PresentationStatus.TIMING_ANALYZED
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timing analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{presentation_id}/generate-video", response_model=GenerateVideoResponse)
async def generate_video(
    presentation_id: str,
    request: GenerateVideoRequest
):
    """5. FFmpeg 영상 생성 (동기 — 인메모리, 인트로/아웃트로 지원)"""
    import subprocess
    import datetime

    try:
        logger.info(f"Starting video generation for presentation: {presentation_id}")

        if presentation_id not in _presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")

        pdata = _presentations[presentation_id]

        if not pdata.get("audio_path"):
            raise HTTPException(status_code=400, detail="Audio not generated.")

        slides = pdata["slides_data"]
        audio_path = pdata["audio_path"]
        output_dir = Path("./outputs/video")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{presentation_id}.mp4"

        # ── 브랜드 템플릿 조회 ──────────────────────────────────────
        template_id = pdata.get("template_id") or (
            request.template_id if hasattr(request, "template_id") else None
        )
        template_data = None
        if template_id:
            try:
                from app.api.v1.brand_templates import _brand_templates
                template_data = _brand_templates.get(template_id)
                if template_data is None:
                    logger.warning(f"template_id={template_id} not found — skipping intro/outro")
            except Exception as tmpl_err:
                logger.warning(f"Failed to load brand template: {tmpl_err}")

        # ── 변수 딕셔너리 구성 ──────────────────────────────────────
        variables = _build_variables(pdata)

        # ── 인트로 세그먼트 생성 ────────────────────────────────────
        intro_segment_path: Optional[str] = None
        if template_data:
            intro_cfg = template_data.get("intro", {})
            if intro_cfg.get("enabled", True) and intro_cfg.get("script", ""):
                try:
                    intro_script = _substitute_variables(intro_cfg["script"], variables)
                    intro_title = _substitute_variables(
                        intro_cfg.get("title_template", variables["presentation_title"]),
                        variables,
                    )
                    intro_subtitle = _substitute_variables(
                        intro_cfg.get("subtitle_template", variables["date"]),
                        variables,
                    )
                    intro_duration = float(intro_cfg.get("duration", 3.0))

                    # 배경 이미지 생성
                    intro_img_path = str(output_dir / f"{presentation_id}_intro_bg.png")
                    bg_color = intro_cfg.get("background_color", "#16325C")
                    _generate_title_image(
                        output_path=intro_img_path,
                        title=intro_title,
                        subtitle=intro_subtitle,
                        bg_color=bg_color,
                    )

                    # 인트로 TTS
                    tts_service = get_tts_service()
                    voice_cfg = template_data.get("voice_config", {})
                    intro_audio_bytes = await tts_service.generate_audio(
                        text=intro_script,
                        voice_id=voice_cfg.get("voice_id", "onyx"),
                        model="tts-1",
                    )
                    intro_audio_path = str(output_dir / f"{presentation_id}_intro.mp3")
                    with open(intro_audio_path, "wb") as f:
                        f.write(intro_audio_bytes)

                    # 인트로 MP4 세그먼트
                    intro_segment_path = str(output_dir / f"{presentation_id}_intro.mp4")
                    await _generate_segment_video(
                        image_path=intro_img_path,
                        audio_path=intro_audio_path,
                        output_path=intro_segment_path,
                        duration=intro_duration,
                    )
                    logger.info(f"Intro segment created: {intro_segment_path}")
                except Exception as intro_err:
                    logger.warning(f"Intro generation failed (skipping): {intro_err}")
                    intro_segment_path = None

        # ── 본편 슬라이드 세그먼트 ─────────────────────────────────
        main_segment_path = str(output_dir / f"{presentation_id}_main.mp4")

        main_concat = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        for slide in slides:
            img_path = Path(slide["image_path"]).resolve()
            duration = slide.get("duration") or 15.0
            main_concat.write(f"file '{img_path}'\n")
            main_concat.write(f"duration {duration}\n")
        if slides:
            last_img = Path(slides[-1]["image_path"]).resolve()
            main_concat.write(f"file '{last_img}'\n")
        main_concat.close()

        main_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", main_concat.name,
            "-i", str(Path(audio_path).resolve()),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            main_segment_path,
        ]
        logger.info(f"Running FFmpeg (main): {' '.join(main_cmd[:6])}...")
        main_result = await asyncio.to_thread(
            subprocess.run, main_cmd, capture_output=True, text=True, timeout=300
        )
        Path(main_concat.name).unlink(missing_ok=True)

        if main_result.returncode != 0:
            logger.error(f"FFmpeg main failed: {main_result.stderr[-500:]}")
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {main_result.stderr[-200:]}")

        # ── 아웃트로 세그먼트 생성 ──────────────────────────────────
        outro_segment_path: Optional[str] = None
        if template_data:
            outro_cfg = template_data.get("outro", {})
            if outro_cfg.get("enabled", True) and outro_cfg.get("script", ""):
                try:
                    outro_script = _substitute_variables(outro_cfg["script"], variables)
                    outro_duration = float(outro_cfg.get("duration", 4.0))
                    cta_text = outro_cfg.get("cta_text", "구독 · 좋아요 · 공유")
                    contact_info = outro_cfg.get("contact_info", "")

                    # 아웃트로 배경 (어두운 배경)
                    outro_img_path = str(output_dir / f"{presentation_id}_outro_bg.png")
                    _generate_title_image(
                        output_path=outro_img_path,
                        title=cta_text,
                        subtitle=contact_info,
                        bg_color="#0D1B2A",
                    )

                    # 아웃트로 TTS
                    tts_service = get_tts_service()
                    voice_cfg = template_data.get("voice_config", {})
                    outro_audio_bytes = await tts_service.generate_audio(
                        text=outro_script,
                        voice_id=voice_cfg.get("voice_id", "onyx"),
                        model="tts-1",
                    )
                    outro_audio_path = str(output_dir / f"{presentation_id}_outro.mp3")
                    with open(outro_audio_path, "wb") as f:
                        f.write(outro_audio_bytes)

                    # 아웃트로 MP4 세그먼트
                    outro_segment_path = str(output_dir / f"{presentation_id}_outro.mp4")
                    await _generate_segment_video(
                        image_path=outro_img_path,
                        audio_path=outro_audio_path,
                        output_path=outro_segment_path,
                        duration=outro_duration,
                    )
                    logger.info(f"Outro segment created: {outro_segment_path}")
                except Exception as outro_err:
                    logger.warning(f"Outro generation failed (skipping): {outro_err}")
                    outro_segment_path = None

        # ── 최종 concat (인트로 + 본편 + 아웃트로) ─────────────────
        segments = []
        if intro_segment_path and Path(intro_segment_path).exists():
            segments.append(intro_segment_path)
        segments.append(main_segment_path)
        if outro_segment_path and Path(outro_segment_path).exists():
            segments.append(outro_segment_path)

        if len(segments) == 1:
            # 인트로/아웃트로 없음 → 본편 그대로 이동
            import shutil
            shutil.move(main_segment_path, str(output_path))
        else:
            # FFmpeg concat (demuxer — 이미 인코딩된 스트림 합치기)
            final_concat = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
            for seg in segments:
                final_concat.write(f"file '{Path(seg).resolve()}'\n")
            final_concat.close()

            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", final_concat.name,
                "-c", "copy",
                "-movflags", "+faststart",
                str(output_path),
            ]
            logger.info(f"Running FFmpeg (final concat): {len(segments)} segments")
            concat_result = await asyncio.to_thread(
                subprocess.run, concat_cmd, capture_output=True, text=True, timeout=300
            )
            Path(final_concat.name).unlink(missing_ok=True)

            if concat_result.returncode != 0:
                logger.error(f"FFmpeg final concat failed: {concat_result.stderr[-500:]}")
                # 본편만이라도 저장
                import shutil
                shutil.copy(main_segment_path, str(output_path))
                logger.warning("Falling back to main segment only")

        # ── 임시 세그먼트 파일 정리 ─────────────────────────────────
        for seg in [intro_segment_path, main_segment_path, outro_segment_path]:
            if seg and seg != str(output_path):
                Path(seg).unlink(missing_ok=True)

        # 인메모리 업데이트
        _presentations[presentation_id]["video_path"] = str(output_path)
        _presentations[presentation_id]["status"] = PresentationStatus.VIDEO_READY.value
        _presentations[presentation_id]["updated_at"] = datetime.datetime.now().isoformat()

        file_size = output_path.stat().st_size / 1024 / 1024
        logger.info(f"Video generated: {output_path} ({file_size:.1f}MB)")

        return GenerateVideoResponse(
            presentation_id=presentation_id,
            video_path=str(output_path),
            celery_task_id="local_ffmpeg",
            status=PresentationStatus.VIDEO_READY,
            estimated_completion_time=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{presentation_id}", response_model=PresentationDetailResponse)
async def get_presentation(presentation_id: str):
    """6. 프리젠테이션 상세 조회 (인메모리)"""
    try:
        if presentation_id not in _presentations:
            raise HTTPException(status_code=404, detail="Presentation not found")

        p = _presentations[presentation_id]
        slides = [SlideInfo(**s) for s in p.get("slides_data", [])]

        return PresentationDetailResponse(
            presentation_id=p["presentation_id"],
            project_id=p["project_id"],
            pdf_path=p["pdf_path"],
            total_slides=p["total_slides"],
            slides=slides,
            full_script=p.get("full_script"),
            audio_path=p.get("audio_path"),
            video_path=p.get("video_path"),
            status=PresentationStatus(p["status"]),
            created_at=p["created_at"],
            updated_at=p["updated_at"],
            metadata=p.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get presentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/presentations", response_model=PresentationListResponse)
async def list_presentations(
    project_id: str,
    page: int = 1,
    page_size: int = 20
):
    """
    7. 프로젝트의 프리젠테이션 목록

    **출력**: 프리젠테이션 목록 (페이지네이션)
    """
    try:
        neo4j_client = get_neo4j_client()

        # 전체 개수 조회
        count_query = """
        MATCH (project:Project {project_id: $project_id})-[:HAS_PRESENTATION]->(p:Presentation)
        RETURN count(p) as total
        """
        count_result = neo4j_client.execute_query(
            query=count_query,
            parameters={"project_id": project_id}
        )
        total = count_result[0]["total"] if count_result else 0

        # 목록 조회
        skip = (page - 1) * page_size
        list_query = """
        MATCH (project:Project {project_id: $project_id})-[:HAS_PRESENTATION]->(p:Presentation)
        RETURN p
        ORDER BY p.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = neo4j_client.execute_query(
            query=list_query,
            parameters={
                "project_id": project_id,
                "skip": skip,
                "limit": page_size
            }
        )

        presentations = []
        for record in result:
            p = record["p"]
            # 첫 슬라이드 썸네일
            thumbnail_url = None
            if p.get("slides_data") and len(p["slides_data"]) > 0:
                thumbnail_url = p["slides_data"][0].get("image_path")

            presentations.append({
                "presentation_id": p["presentation_id"],
                "project_id": p["project_id"],
                "total_slides": p["total_slides"],
                "status": p["status"],
                "created_at": p["created_at"],
                "updated_at": p["updated_at"],
                "thumbnail_url": thumbnail_url
            })

        return PresentationListResponse(
            presentations=presentations,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to list presentations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
