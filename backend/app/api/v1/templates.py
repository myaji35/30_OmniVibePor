"""Templates CRUD API"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from app.models.template import (
    TemplateCRUD,
    TemplateCreate,
    TemplateResponse,
    TemplatePlatform,
    TemplateCategory,
)

router = APIRouter(prefix="/templates")


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    platform: Optional[TemplatePlatform] = Query(None),
    category: Optional[TemplateCategory] = Query(None),
):
    """템플릿 목록 조회 (플랫폼/카테고리 필터)"""
    return await TemplateCRUD.list(platform=platform, category=category)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int):
    """단일 템플릿 조회"""
    template = await TemplateCRUD.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(data: TemplateCreate):
    """새 템플릿 생성"""
    return await TemplateCRUD.create(data)


@router.post("/{template_id}/use", status_code=204)
async def use_template(template_id: int):
    """템플릿 사용 횟수 증가"""
    template = await TemplateCRUD.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await TemplateCRUD.increment_use_count(template_id)


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: int):
    """템플릿 삭제"""
    deleted = await TemplateCRUD.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
