"""Brand Template API 엔드포인트"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.brand_template import (
    BrandTemplate,
    BrandTemplateCreateRequest,
    BrandTemplateUpdateRequest,
    BrandTemplateResponse,
    BrandTemplateListResponse,
    BrandTemplateDeleteResponse,
)

# In-memory store (로컬 개발용, 프로덕션은 DB 연동)
_brand_templates: dict[str, dict] = {}

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_response(data: dict) -> BrandTemplateResponse:
    """딕셔너리 → BrandTemplateResponse 변환"""
    return BrandTemplateResponse(**data)


@router.post("", response_model=BrandTemplateResponse, status_code=201)
async def create_brand_template(request: BrandTemplateCreateRequest):
    """
    브랜드 템플릿 생성

    **기능**:
    - 프로젝트에 새 브랜드 템플릿을 추가합니다.
    - `is_default: true`로 생성하면 동일 프로젝트의 기존 기본 템플릿이 해제됩니다.
    """
    try:
        template = BrandTemplate(
            project_id=request.project_id,
            name=request.name,
            is_default=request.is_default,
            intro=request.intro,
            outro=request.outro,
            voice_config=request.voice_config,
        )

        # is_default=True 이면 같은 프로젝트의 기존 기본 템플릿 해제
        if template.is_default:
            for tid, tdata in _brand_templates.items():
                if tdata["project_id"] == request.project_id and tdata["is_default"]:
                    _brand_templates[tid]["is_default"] = False
                    _brand_templates[tid]["updated_at"] = datetime.utcnow().isoformat()

        _brand_templates[template.id] = template.model_dump()

        logger.info(f"Brand template created: {template.id} (project: {request.project_id})")
        return _to_response(_brand_templates[template.id])

    except Exception as e:
        logger.error(f"Brand template creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}", response_model=BrandTemplateListResponse)
async def list_brand_templates(project_id: str):
    """
    프로젝트의 브랜드 템플릿 목록 조회

    **기능**:
    - 특정 프로젝트에 속한 모든 브랜드 템플릿을 반환합니다.
    - 기본 템플릿이 목록 상단에 오도록 정렬됩니다.
    """
    try:
        project_templates = [
            t for t in _brand_templates.values()
            if t["project_id"] == project_id
        ]
        # 기본 템플릿 우선 정렬, 그 다음 생성일시 최신순
        project_templates.sort(key=lambda t: (not t["is_default"], t["created_at"]), reverse=False)

        templates = [_to_response(t) for t in project_templates]

        logger.info(f"Listed {len(templates)} brand templates for project: {project_id}")
        return BrandTemplateListResponse(
            templates=templates,
            total=len(templates),
            project_id=project_id,
        )

    except Exception as e:
        logger.error(f"Failed to list brand templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=BrandTemplateResponse)
async def get_brand_template(template_id: str):
    """
    브랜드 템플릿 단건 조회

    **기능**:
    - 템플릿 ID로 특정 브랜드 템플릿을 조회합니다.
    """
    if template_id not in _brand_templates:
        raise HTTPException(status_code=404, detail="Brand template not found")

    return _to_response(_brand_templates[template_id])


@router.put("/{template_id}", response_model=BrandTemplateResponse)
async def update_brand_template(template_id: str, request: BrandTemplateUpdateRequest):
    """
    브랜드 템플릿 수정

    **기능**:
    - 지정된 필드만 부분 수정합니다 (PATCH 방식).
    - `is_default: true`로 변경하면 동일 프로젝트의 기존 기본 템플릿이 해제됩니다.
    """
    if template_id not in _brand_templates:
        raise HTTPException(status_code=404, detail="Brand template not found")

    try:
        current = _brand_templates[template_id]
        update_data = request.model_dump(exclude_unset=True)

        # is_default 변경 시 같은 프로젝트의 기존 기본 템플릿 해제
        if update_data.get("is_default") is True:
            project_id = current["project_id"]
            for tid, tdata in _brand_templates.items():
                if tid != template_id and tdata["project_id"] == project_id and tdata["is_default"]:
                    _brand_templates[tid]["is_default"] = False
                    _brand_templates[tid]["updated_at"] = datetime.utcnow().isoformat()

        # 중첩 모델(IntroConfig, OutroConfig, VoiceConfig) 병합
        for key in ("intro", "outro", "voice_config"):
            if key in update_data and isinstance(update_data[key], dict):
                current[key].update(update_data[key])
                del update_data[key]

        current.update(update_data)
        current["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Brand template updated: {template_id}")
        return _to_response(current)

    except Exception as e:
        logger.error(f"Failed to update brand template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", response_model=BrandTemplateDeleteResponse)
async def delete_brand_template(template_id: str):
    """
    브랜드 템플릿 삭제

    **기능**:
    - 지정된 브랜드 템플릿을 인메모리 저장소에서 삭제합니다.
    """
    if template_id not in _brand_templates:
        raise HTTPException(status_code=404, detail="Brand template not found")

    del _brand_templates[template_id]
    logger.info(f"Brand template deleted: {template_id}")

    return BrandTemplateDeleteResponse(
        id=template_id,
        message="Brand template deleted successfully",
    )


@router.put("/{template_id}/set-default", response_model=BrandTemplateResponse)
async def set_default_brand_template(template_id: str):
    """
    기본 브랜드 템플릿 지정

    **기능**:
    - 지정된 템플릿을 해당 프로젝트의 기본 템플릿으로 설정합니다.
    - 동일 프로젝트의 기존 기본 템플릿은 자동으로 해제됩니다.
    """
    if template_id not in _brand_templates:
        raise HTTPException(status_code=404, detail="Brand template not found")

    try:
        project_id = _brand_templates[template_id]["project_id"]

        # 같은 프로젝트의 기존 기본 템플릿 해제
        for tid, tdata in _brand_templates.items():
            if tdata["project_id"] == project_id and tdata["is_default"]:
                _brand_templates[tid]["is_default"] = False
                _brand_templates[tid]["updated_at"] = datetime.utcnow().isoformat()

        # 새 기본 템플릿 지정
        _brand_templates[template_id]["is_default"] = True
        _brand_templates[template_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Default brand template set: {template_id} (project: {project_id})")
        return _to_response(_brand_templates[template_id])

    except Exception as e:
        logger.error(f"Failed to set default brand template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
