"""프로젝트 관리 API

REALPLAN.md Phase 1.2 & 1.3 구현:
- Project CRUD 엔드포인트 (생성, 조회, 수정, 삭제)
- Neo4j GraphRAG 기반 프로젝트 관리
- 프로젝트 기반 오디오 생성 (Strangler Fig Pattern)
"""
from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.neo4j_models import (
    ProjectModel,
    ProjectStatus,
    Platform,
    Neo4jCRUDManager,
    ScriptModel,
    AudioModel
)
from app.services.neo4j_client import get_neo4j_client
from app.tasks.audio_tasks import generate_verified_audio_task

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class ProjectCreateRequest(BaseModel):
    """프로젝트 생성 요청"""
    user_id: str = Field(..., description="사용자 ID")
    title: str = Field(..., min_length=1, max_length=200, description="프로젝트 제목")
    topic: str = Field(..., min_length=1, max_length=500, description="주제")
    platform: Platform = Field(..., description="플랫폼")
    persona_id: Optional[str] = Field(None, description="사용할 페르소나 ID")
    publish_scheduled_at: Optional[datetime] = Field(None, description="발행 예정 시간")


class ProjectUpdateRequest(BaseModel):
    """프로젝트 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="프로젝트 제목")
    topic: Optional[str] = Field(None, min_length=1, max_length=500, description="주제")
    status: Optional[ProjectStatus] = Field(None, description="상태")
    publish_scheduled_at: Optional[datetime] = Field(None, description="발행 예정 시간")


class ProjectResponse(BaseModel):
    """프로젝트 응답"""
    project_id: str
    title: str
    topic: str
    platform: Platform
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    publish_scheduled_at: Optional[datetime] = None
    persona_id: Optional[str] = None


class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답"""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int


# ==================== Helper Functions ====================

def get_crud_manager() -> Neo4jCRUDManager:
    """Neo4j CRUD 매니저 인스턴스"""
    client = get_neo4j_client()
    return Neo4jCRUDManager(client)


# ==================== API Endpoints ====================

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(request: ProjectCreateRequest):
    """
    **프로젝트 생성**

    새로운 영상 제작 프로젝트를 생성합니다.

    - **user_id**: 프로젝트 소유자 (필수)
    - **title**: 프로젝트 제목 (필수)
    - **topic**: 영상 주제 (필수)
    - **platform**: 배포 플랫폼 (youtube, instagram, facebook, tiktok)
    - **persona_id**: 사용할 페르소나 ID (선택)
    - **publish_scheduled_at**: 발행 예정 시간 (선택)

    **반환값**: 생성된 프로젝트 정보
    """
    try:
        crud = get_crud_manager()

        # 사용자 존재 확인
        user = crud.get_user(request.user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {request.user_id}"
            )

        # 페르소나 존재 확인 (지정된 경우)
        if request.persona_id:
            persona = crud.get_persona(request.persona_id)
            if not persona:
                raise HTTPException(
                    status_code=404,
                    detail=f"Persona not found: {request.persona_id}"
                )

        # 프로젝트 생성
        project = ProjectModel(
            title=request.title,
            topic=request.topic,
            platform=request.platform,
            publish_scheduled_at=request.publish_scheduled_at
        )

        result = crud.create_project(
            user_id=request.user_id,
            project=project,
            persona_id=request.persona_id
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create project"
            )

        return ProjectResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """
    **프로젝트 조회**

    프로젝트 ID로 단일 프로젝트 정보를 조회합니다.

    - **project_id**: 프로젝트 고유 ID

    **반환값**: 프로젝트 상세 정보
    """
    try:
        crud = get_crud_manager()
        result = crud.get_project(project_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        return ProjectResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{user_id}/projects", response_model=ProjectListResponse)
async def list_user_projects(
    user_id: str,
    status: Optional[ProjectStatus] = Query(None, description="프로젝트 상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """
    **사용자 프로젝트 목록 조회**

    특정 사용자의 모든 프로젝트를 조회합니다.

    - **user_id**: 사용자 ID (필수)
    - **status**: 상태 필터 (draft, script_ready, production, published, archived)
    - **page**: 페이지 번호 (기본: 1)
    - **page_size**: 페이지당 항목 수 (기본: 20, 최대: 100)

    **반환값**: 프로젝트 목록 및 페이징 정보
    """
    try:
        crud = get_crud_manager()

        # 사용자 존재 확인
        user = crud.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {user_id}"
            )

        # 프로젝트 목록 조회 (페이징 없이 전체 조회)
        all_projects = crud.get_user_projects(user_id, status=status)

        # 페이징 처리
        total = len(all_projects)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        paginated_projects = all_projects[start_idx:end_idx]

        return ProjectListResponse(
            projects=[ProjectResponse(**p) for p in paginated_projects],
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """
    **프로젝트 수정**

    프로젝트 정보를 부분적으로 수정합니다.

    - **project_id**: 프로젝트 ID
    - **title**: 새로운 제목 (선택)
    - **topic**: 새로운 주제 (선택)
    - **status**: 새로운 상태 (선택)
    - **publish_scheduled_at**: 새로운 발행 예정 시간 (선택)

    **반환값**: 수정된 프로젝트 정보
    """
    try:
        crud = get_crud_manager()

        # 프로젝트 존재 확인
        existing = crud.get_project(project_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 수정할 필드만 추출
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.topic is not None:
            updates["topic"] = request.topic
        if request.status is not None:
            updates["status"] = request.status.value
        if request.publish_scheduled_at is not None:
            updates["publish_scheduled_at"] = request.publish_scheduled_at.isoformat()

        # updated_at 자동 갱신
        updates["updated_at"] = datetime.utcnow().isoformat()

        if not updates:
            # 수정할 내용이 없으면 기존 정보 반환
            return ProjectResponse(**existing)

        # Neo4j 업데이트 (일반 필드)
        if updates:
            # status는 별도 메서드 사용
            if "status" in updates:
                status_value = updates.pop("status")
                crud.update_project_status(project_id, ProjectStatus(status_value))

            # 나머지 필드 업데이트
            if updates:
                from app.services.neo4j_client import get_neo4j_client
                client = get_neo4j_client()

                set_clauses = ", ".join([f"proj.{key} = ${key}" for key in updates.keys()])
                query = f"""
                MATCH (proj:Project {{project_id: $project_id}})
                SET {set_clauses}
                RETURN proj.project_id as project_id
                """
                params = {"project_id": project_id, **updates}
                client.query(query, params)

        # 수정된 프로젝트 조회
        updated = crud.get_project(project_id)
        return ProjectResponse(**updated)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """
    **프로젝트 삭제**

    프로젝트 및 관련된 모든 데이터(스크립트, 오디오, 비디오 등)를 삭제합니다.

    - **project_id**: 삭제할 프로젝트 ID

    **반환값**: 없음 (204 No Content)

    **주의**: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        crud = get_crud_manager()

        # 프로젝트 존재 확인
        existing = crud.get_project(project_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 프로젝트 삭제 (CASCADE)
        success = crud.delete_project(project_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete project"
            )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/projects/{project_id}/scripts", response_model=dict, status_code=201)
async def create_project_script(project_id: str, request: dict):
    """
    **프로젝트 스크립트 생성**

    프로젝트에 새로운 스크립트를 추가합니다.

    - **project_id**: 프로젝트 ID
    - **content**: 스크립트 내용 (필수)
    - **platform**: 플랫폼 (필수)
    - **word_count**: 글자 수 (필수)
    - **estimated_duration**: 예상 시간 (초) (필수)

    **반환값**: 생성된 스크립트 정보
    """
    try:
        crud = get_crud_manager()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 스크립트 생성
        script = ScriptModel(
            content=request.get('content', ''),
            platform=request.get('platform', 'youtube'),
            word_count=request.get('word_count', 0),
            estimated_duration=request.get('estimated_duration', 0),
        )

        result = crud.create_script(
            project_id=project_id,
            script=script,
            selected=True  # 첫 번째 스크립트는 자동 선택
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create script"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/projects/{project_id}/scripts", response_model=List[dict])
async def get_project_scripts(project_id: str):
    """
    **프로젝트 스크립트 조회**

    프로젝트에 속한 모든 스크립트(초안 3종)를 조회합니다.

    - **project_id**: 프로젝트 ID

    **반환값**: 스크립트 목록
    """
    try:
        crud = get_crud_manager()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        scripts = crud.get_project_scripts(project_id)
        return scripts

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/projects/{project_id}/videos", response_model=List[dict])
async def get_project_videos(project_id: str):
    """
    **프로젝트 비디오 조회**

    프로젝트에 속한 모든 생성된 비디오를 조회합니다.

    - **project_id**: 프로젝트 ID

    **반환값**: 비디오 목록
    """
    try:
        crud = get_crud_manager()

        # 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        videos = crud.get_project_videos(project_id)
        return videos

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Phase 1.3: Audio API 마이그레이션 ====================

class ProjectAudioGenerateRequest(BaseModel):
    """프로젝트 기반 오디오 생성 요청"""
    script_id: str = Field(..., description="스크립트 ID (프로젝트에 속한 스크립트)")
    voice_id: Optional[str] = Field(None, description="음성 ID (기본값: rachel)")
    accuracy_threshold: float = Field(0.95, ge=0.0, le=1.0, description="정확도 임계값")
    max_attempts: int = Field(5, ge=1, le=10, description="최대 재시도 횟수")


class ProjectAudioResponse(BaseModel):
    """프로젝트 오디오 생성 응답"""
    status: str
    task_id: str
    message: str
    project_id: str
    script_id: str


@router.post("/projects/{project_id}/audio", response_model=ProjectAudioResponse)
async def generate_project_audio(project_id: str, request: ProjectAudioGenerateRequest):
    """
    **프로젝트 기반 오디오 생성 (Phase 1.3: Strangler Fig Pattern)**

    프로젝트에 속한 스크립트로 Zero-Fault Audio를 생성하고 Neo4j에 자동으로 저장합니다.

    **워크플로우**:
    1. 프로젝트 및 스크립트 존재 확인
    2. ElevenLabs TTS로 오디오 생성
    3. OpenAI Whisper STT로 검증
    4. 원본 스크립트와 비교 (유사도 계산)
    5. 정확도 95% 미만이면 재생성 (최대 5회)
    6. Neo4j에 Audio 노드 생성 및 Script와 연결
    7. 검증된 오디오 반환

    **Strangler Fig Pattern**: 기존 `/api/v1/audio/generate`는 유지하면서 새로운 엔드포인트 추가

    - **project_id**: 프로젝트 ID
    - **script_id**: 스크립트 ID (프로젝트에 속해야 함)
    - **voice_id**: 음성 ID (선택)
    - **accuracy_threshold**: 정확도 임계값 (기본: 0.95)
    - **max_attempts**: 최대 재시도 횟수 (기본: 5)

    **반환값**: 작업 상태 및 task_id
    """
    try:
        crud = get_crud_manager()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. 스크립트 존재 및 프로젝트 소속 확인
        scripts = crud.get_project_scripts(project_id)
        script = next((s for s in scripts if s["script_id"] == request.script_id), None)

        if not script:
            raise HTTPException(
                status_code=404,
                detail=f"Script {request.script_id} not found in project {project_id}"
            )

        # 3. 스크립트 내용 추출
        script_content = script["content"]

        logger.info(
            f"Starting project-based audio generation: "
            f"project={project_id}, script={request.script_id}, "
            f"length={len(script_content)} chars"
        )

        # 4. Celery 작업 실행 (기존 태스크 재사용)
        task = generate_verified_audio_task.delay(
            text=script_content,
            voice_id=request.voice_id or "rachel",
            language="ko",  # 프로젝트 기반이므로 한국어로 고정 (추후 확장 가능)
            user_id=None,  # 추후 인증 시스템 통합 시 사용
            accuracy_threshold=request.accuracy_threshold,
            max_attempts=request.max_attempts,
            # 메타데이터로 프로젝트/스크립트 정보 전달
            metadata={
                "project_id": project_id,
                "script_id": request.script_id,
                "save_to_neo4j": True
            }
        )

        return ProjectAudioResponse(
            status="processing",
            task_id=task.id,
            message=f"Zero-Fault Audio 생성 시작. /audio/status/{task.id}로 진행 상황 확인하세요.",
            project_id=project_id,
            script_id=request.script_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project audio generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/projects/{project_id}/scripts/{script_id}/audio", response_model=List[dict])
async def get_script_audio(project_id: str, script_id: str):
    """
    **스크립트 오디오 조회**

    특정 스크립트로 생성된 모든 오디오를 조회합니다.

    - **project_id**: 프로젝트 ID
    - **script_id**: 스크립트 ID

    **반환값**: 오디오 목록 (최신순)
    """
    try:
        crud = get_crud_manager()

        # 1. 프로젝트 존재 확인
        project = crud.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {project_id}"
            )

        # 2. 스크립트 존재 확인
        scripts = crud.get_project_scripts(project_id)
        script = next((s for s in scripts if s["script_id"] == script_id), None)

        if not script:
            raise HTTPException(
                status_code=404,
                detail=f"Script {script_id} not found in project {project_id}"
            )

        # 3. 오디오 목록 조회
        audios = crud.get_script_audios(script_id)
        return audios

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
