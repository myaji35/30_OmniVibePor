"""Presentation API 엔드포인트"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from pathlib import Path
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


@router.post("/upload", response_model=PresentationUploadResponse)
async def upload_presentation(
    file: UploadFile = File(..., description="PDF 파일"),
    project_id: str = Form(..., description="프로젝트 ID"),
    dpi: int = Form(200, description="슬라이드 이미지 해상도 (DPI)"),
    lang: str = Form("kor+eng", description="OCR 언어")
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

        # 슬라이드 정보 생성
        slides = []
        for i, image_path in enumerate(image_paths, start=1):
            slides.append(
                SlideInfo(
                    slide_number=i,
                    image_path=image_path,
                    ocr_text=None  # OCR은 선택적으로 나중에 추가 가능
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
            slide_models.append(SlideData(
                slide_number=s["slide_number"],
                title=f"슬라이드 {s['slide_number']}",
                content=s.get("ocr_text") or f"슬라이드 {s['slide_number']} 내용",
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
    """
    5. 프리젠테이션 영상 생성 (비동기)

    **워크플로우**:
    1. Celery 작업 큐에 등록
    2. 백그라운드에서 FFmpeg 영상 생성
    3. 상태는 /presentations/{id}로 확인

    **출력**: celery_task_id, 예상 완료 시간
    """
    try:
        logger.info(f"Starting video generation for presentation: {presentation_id}")

        # Neo4j에서 프리젠테이션 조회
        neo4j_client = get_neo4j_client()
        query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        RETURN p
        """
        result = neo4j_client.execute_query(
            query=query,
            parameters={"presentation_id": presentation_id}
        )

        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Presentation not found")

        presentation_data = result[0]["p"]

        # 필수 데이터 확인
        if not presentation_data.get("audio_path"):
            raise HTTPException(
                status_code=400,
                detail="Audio not generated. Generate audio first."
            )

        if not presentation_data.get("slides_data"):
            raise HTTPException(
                status_code=400,
                detail="No slides available."
            )

        # Celery 작업 실행
        video_generator = get_video_generator()
        estimated_time = video_generator.estimate_generation_time(
            total_slides=presentation_data["total_slides"]
        )

        task = generate_presentation_video_task.delay(
            presentation_id=presentation_id,
            slides=presentation_data["slides_data"],
            audio_path=presentation_data["audio_path"],
            output_filename=f"{presentation_id}.mp4",
            transition_effect=request.transition_effect.value,
            transition_duration=request.transition_duration,
            bgm_path=request.bgm_path,
            bgm_volume=request.bgm_volume
        )

        logger.info(
            f"Video generation task created: {presentation_id}, "
            f"task_id: {task.id}, "
            f"estimated_time: {estimated_time}s"
        )

        return GenerateVideoResponse(
            presentation_id=presentation_id,
            video_path=None,
            celery_task_id=task.id,
            status=PresentationStatus.VIDEO_RENDERING,
            estimated_completion_time=estimated_time
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
