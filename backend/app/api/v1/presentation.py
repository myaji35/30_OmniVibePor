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
from app.services.slide_timing_analyzer import SlideTimingAnalyzer
from app.services.presentation_video_generator import get_video_generator
from app.services.neo4j_client import get_neo4j_client
from app.tasks.presentation_tasks import generate_presentation_video_task

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

        # Neo4j에 프리젠테이션 저장
        neo4j_client = get_neo4j_client()
        presentation_model = PresentationModel(
            presentation_id=presentation_id,
            project_id=project_id,
            pdf_path=pdf_path,
            total_slides=len(slides),
            slides_data=[slide.model_dump() for slide in slides],
            status=PresentationStatus.UPLOADED
        )

        query = """
        MATCH (project:Project {project_id: $project_id})
        CREATE (p:Presentation $presentation_data)
        CREATE (project)-[:HAS_PRESENTATION]->(p)
        RETURN p
        """

        neo4j_client.execute_query(
            query=query,
            parameters={
                "project_id": project_id,
                "presentation_data": presentation_model.model_dump()
            }
        )

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
    """
    2. 나레이션 스크립트 생성

    **워크플로우**:
    1. Neo4j에서 슬라이드 정보 조회
    2. LLM으로 슬라이드별 나레이션 스크립트 생성
    3. 예상 시간 계산
    4. Neo4j 업데이트

    **출력**: 전체 스크립트, 슬라이드별 스크립트, 예상 시간
    """
    try:
        logger.info(f"Generating script for presentation: {presentation_id}")

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

        # 스크립트 생성
        converter = SlideToScriptConverter()
        script_result = await converter.convert_slides_to_script(
            slides=presentation_data["slides_data"],
            tone=request.tone,
            target_duration_per_slide=request.target_duration_per_slide
        )

        # 슬라이드 정보 업데이트
        slides_with_script = []
        for i, slide_data in enumerate(presentation_data["slides_data"]):
            slide_script = script_result.slide_scripts[i]
            slides_with_script.append(
                SlideInfo(
                    slide_number=slide_data["slide_number"],
                    image_path=slide_data["image_path"],
                    ocr_text=slide_data.get("ocr_text"),
                    script=slide_script["script"],
                    duration=slide_script["estimated_duration"]
                )
            )

        # Neo4j 업데이트
        update_query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        SET p.full_script = $full_script,
            p.slides_data = $slides_data,
            p.status = $status,
            p.updated_at = datetime()
        RETURN p
        """

        neo4j_client.execute_query(
            query=update_query,
            parameters={
                "presentation_id": presentation_id,
                "full_script": script_result.full_script,
                "slides_data": [s.model_dump() for s in slides_with_script],
                "status": PresentationStatus.SCRIPT_GENERATED.value
            }
        )

        logger.info(
            f"Script generated: {presentation_id}, "
            f"total_duration: {script_result.total_duration:.1f}s"
        )

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
    """
    3. TTS 오디오 생성

    **워크플로우**:
    1. Neo4j에서 전체 스크립트 조회
    2. TTS로 오디오 생성
    3. Whisper STT로 검증
    4. Neo4j 업데이트

    **출력**: audio_path, duration, whisper_result
    """
    try:
        logger.info(f"Generating audio for presentation: {presentation_id}")

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

        # 스크립트 확인
        script = request.script or presentation_data.get("full_script")
        if not script:
            raise HTTPException(
                status_code=400,
                detail="No script available. Generate script first."
            )

        # TTS 오디오 생성
        tts_service = get_tts_service()
        audio_bytes = await tts_service.generate_audio(
            text=script,
            voice_id=request.voice_id,
            model=request.model
        )

        # 오디오 저장
        audio_filename = f"{presentation_id}.mp3"
        audio_path = await tts_service.save_audio(
            audio_bytes=audio_bytes,
            filename=audio_filename,
            text=script
        )

        # Whisper STT 검증
        stt_service = get_stt_service()
        whisper_result = await stt_service.transcribe_with_timestamps(
            audio_file_path=audio_path,
            language="ko"
        )

        # 정확도 계산 (간단한 비교)
        from difflib import SequenceMatcher
        accuracy = SequenceMatcher(None, script, whisper_result["text"]).ratio()

        # Neo4j 업데이트
        update_query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        SET p.audio_path = $audio_path,
            p.audio_duration = $duration,
            p.status = $status,
            p.updated_at = datetime(),
            p.metadata.whisper_result = $whisper_result
        RETURN p
        """

        neo4j_client.execute_query(
            query=update_query,
            parameters={
                "presentation_id": presentation_id,
                "audio_path": audio_path,
                "duration": whisper_result["duration"],
                "status": PresentationStatus.AUDIO_GENERATED.value,
                "whisper_result": whisper_result
            }
        )

        logger.info(
            f"Audio generated: {presentation_id}, "
            f"duration: {whisper_result['duration']:.1f}s, "
            f"accuracy: {accuracy:.2%}"
        )

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
    """
    4. 슬라이드 타이밍 분석

    **워크플로우**:
    1. Whisper 타임스탬프 분석
    2. 슬라이드별 시작/종료 시간 매칭
    3. Neo4j 업데이트

    **출력**: 슬라이드별 타이밍 정보
    """
    try:
        logger.info(f"Analyzing timing for presentation: {presentation_id}")

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

        # Whisper 결과 확인
        whisper_result = presentation_data.get("metadata", {}).get("whisper_result")
        if not whisper_result and not request.manual_timings:
            raise HTTPException(
                status_code=400,
                detail="No audio or manual timings available."
            )

        # 수동 타이밍이 있으면 사용
        if request.manual_timings:
            slides_with_timing = []
            current_time = 0.0

            for i, slide_data in enumerate(presentation_data["slides_data"]):
                duration = request.manual_timings[i]
                slides_with_timing.append(
                    SlideInfo(
                        **slide_data,
                        start_time=current_time,
                        end_time=current_time + duration,
                        duration=duration
                    )
                )
                current_time += duration

            total_duration = current_time

        else:
            # Whisper 타임스탬프 기반 자동 분석
            analyzer = SlideTimingAnalyzer()
            slide_scripts = [
                {"slide_number": s["slide_number"], "script": s["script"]}
                for s in presentation_data["slides_data"]
            ]

            timing_results = await analyzer.analyze_timing(
                whisper_result=whisper_result,
                slide_scripts=slide_scripts,
                audio_path=presentation_data["audio_path"]
            )

            slides_with_timing = [
                SlideInfo(
                    slide_number=t.slide_number,
                    image_path=presentation_data["slides_data"][i]["image_path"],
                    script=presentation_data["slides_data"][i]["script"],
                    start_time=t.start_time,
                    end_time=t.end_time,
                    duration=t.duration
                )
                for i, t in enumerate(timing_results)
            ]

            total_duration = timing_results[-1].end_time if timing_results else 0

        # Neo4j 업데이트
        update_query = """
        MATCH (p:Presentation {presentation_id: $presentation_id})
        SET p.slides_data = $slides_data,
            p.status = $status,
            p.updated_at = datetime()
        RETURN p
        """

        neo4j_client.execute_query(
            query=update_query,
            parameters={
                "presentation_id": presentation_id,
                "slides_data": [s.model_dump() for s in slides_with_timing],
                "status": PresentationStatus.TIMING_ANALYZED.value
            }
        )

        logger.info(
            f"Timing analyzed: {presentation_id}, "
            f"total_duration: {total_duration:.1f}s"
        )

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
    """
    6. 프리젠테이션 상세 조회

    **출력**: 전체 메타데이터 (슬라이드, 스크립트, 타이밍, 영상)
    """
    try:
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

        # SlideInfo 변환
        slides = [SlideInfo(**s) for s in presentation_data.get("slides_data", [])]

        return PresentationDetailResponse(
            presentation_id=presentation_data["presentation_id"],
            project_id=presentation_data["project_id"],
            pdf_path=presentation_data["pdf_path"],
            total_slides=presentation_data["total_slides"],
            slides=slides,
            full_script=presentation_data.get("full_script"),
            audio_path=presentation_data.get("audio_path"),
            video_path=presentation_data.get("video_path"),
            status=PresentationStatus(presentation_data["status"]),
            created_at=presentation_data["created_at"],
            updated_at=presentation_data["updated_at"],
            metadata=presentation_data.get("metadata", {})
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
