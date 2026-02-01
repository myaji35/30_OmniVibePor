"""Google Sheets API 엔드포인트"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import logging

from app.services.google_sheets_service import get_sheets_service
from app.services.neo4j_client import get_neo4j_client

router = APIRouter(prefix="/sheets", tags=["Google Sheets"])
logger = logging.getLogger(__name__)


class SheetConnectionRequest(BaseModel):
    """시트 연결 요청"""
    spreadsheet_url: str
    sheet_name: Optional[str] = None


class SheetReadRequest(BaseModel):
    """시트 읽기 요청"""
    spreadsheet_id: str
    range_name: str


class SheetWriteRequest(BaseModel):
    """시트 쓰기 요청"""
    spreadsheet_id: str
    range_name: str
    values: List[List[Any]]


class StatusUpdateRequest(BaseModel):
    """콘텐츠 상태 업데이트 요청"""
    spreadsheet_id: str
    row_index: int
    status: str
    sheet_name: str = "스케줄"


@router.get("/status")
async def check_sheets_status():
    """
    Google Sheets API 연결 상태 확인
    """
    sheets_service = get_sheets_service()

    return {
        "available": sheets_service.is_available(),
        "message": "Google Sheets API is ready" if sheets_service.is_available()
                   else "Google Sheets credentials not configured"
    }


@router.get("/saved-sheets")
async def get_saved_sheets():
    """
    Neo4j에 저장된 구글 시트 목록 조회
    """
    neo4j_client = get_neo4j_client()

    try:
        query = """
        MATCH (s:GoogleSheet)
        RETURN s.spreadsheet_id AS spreadsheet_id,
               s.url AS url,
               s.title AS title,
               s.connected_at AS connected_at,
               s.last_accessed AS last_accessed
        ORDER BY s.last_accessed DESC
        """

        results = neo4j_client.query(query)

        sheets = []
        for record in results:
            sheets.append({
                "spreadsheet_id": record.get("spreadsheet_id"),
                "url": record.get("url"),
                "title": record.get("title"),
                "connected_at": record.get("connected_at"),
                "last_accessed": record.get("last_accessed")
            })

        return {
            "success": True,
            "total": len(sheets),
            "sheets": sheets
        }

    except Exception as e:
        logger.error(f"Error getting saved sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect")
async def connect_sheet(request: SheetConnectionRequest):
    """
    구글 시트 연결 테스트

    - 시트 URL에서 ID 추출
    - 시트 접근 권한 확인
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Google Sheets service is not configured. Please add credentials."
        )

    # URL에서 스프레드시트 ID 추출
    spreadsheet_id = sheets_service.get_spreadsheet_id_from_url(request.spreadsheet_url)

    if not spreadsheet_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid Google Sheets URL. Please provide a valid spreadsheet URL."
        )

    try:
        # 연결 테스트 (메타데이터 가져오기로 변경 - 시트 이름 불필요)
        # 스프레드시트 메타데이터를 가져와서 접근 권한 확인
        import asyncio
        from datetime import datetime

        def _get_metadata():
            return sheets_service.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()

        metadata = await asyncio.to_thread(_get_metadata)

        # 시트 제목 가져오기
        sheet_title = metadata.get('properties', {}).get('title', 'Untitled')

        # Neo4j에 저장
        neo4j_client = get_neo4j_client()
        try:
            query = """
            MERGE (s:GoogleSheet {spreadsheet_id: $spreadsheet_id})
            SET s.url = $url,
                s.title = $title,
                s.connected_at = $connected_at,
                s.last_accessed = $last_accessed
            RETURN s
            """

            neo4j_client.query(
                query,
                spreadsheet_id=spreadsheet_id,
                url=request.spreadsheet_url,
                title=sheet_title,
                connected_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat()
            )

            logger.info(f"Saved Google Sheet connection to Neo4j: {spreadsheet_id}")
        except Exception as neo4j_error:
            logger.warning(f"Failed to save to Neo4j (non-critical): {neo4j_error}")

        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "title": sheet_title,
            "message": "Successfully connected to Google Sheets"
        }

    except Exception as e:
        logger.error(f"Failed to connect to sheet: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to access Google Sheet. Error: {str(e)}"
        )


@router.post("/read")
async def read_sheet(request: SheetReadRequest):
    """
    시트 데이터 읽기

    Args:
        spreadsheet_id: 스프레드시트 ID
        range_name: 읽을 범위 (예: 'Sheet1!A1:D10')
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        data = await sheets_service.read_sheet(
            request.spreadsheet_id,
            request.range_name
        )

        return {
            "success": True,
            "rows": len(data),
            "data": data
        }

    except Exception as e:
        logger.error(f"Error reading sheet: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/write")
async def write_sheet(request: SheetWriteRequest):
    """
    시트 데이터 쓰기

    Args:
        spreadsheet_id: 스프레드시트 ID
        range_name: 쓸 범위
        values: 쓸 데이터
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        updated_cells = await sheets_service.write_sheet(
            request.spreadsheet_id,
            request.range_name,
            request.values
        )

        return {
            "success": True,
            "updated_cells": updated_cells
        }

    except Exception as e:
        logger.error(f"Error writing sheet: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/strategy/{spreadsheet_id}")
async def get_strategy(
    spreadsheet_id: str,
    sheet_name: str = "전략"
):
    """
    전략 시트 읽기

    전략 시트 구조:
    | 항목 | 내용 |
    |------|------|
    | 캠페인명 | ... |
    | 타겟 | ... |
    | 톤앤매너 | ... |
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        strategy = await sheets_service.read_strategy_sheet(spreadsheet_id, sheet_name)

        return {
            "success": True,
            "strategy": strategy
        }

    except Exception as e:
        logger.error(f"Error reading strategy: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedule/{spreadsheet_id}")
async def get_schedule(
    spreadsheet_id: str,
    sheet_name: str = "스케줄"
):
    """
    콘텐츠 스케줄 시트 읽기

    스케줄 시트 구조:
    | 날짜 | 주제 | 플랫폼 | 상태 |
    |------|------|--------|------|
    | 2024-01-15 | ... | YouTube | 대기 |
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        schedule = await sheets_service.read_content_schedule(spreadsheet_id, sheet_name)

        return {
            "success": True,
            "total_items": len(schedule),
            "schedule": schedule
        }

    except Exception as e:
        logger.error(f"Error reading schedule: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaign/{spreadsheet_id}/{campaign_name}")
async def get_campaign_contents(
    spreadsheet_id: str,
    campaign_name: str,
    sheet_name: str = "스케줄"
):
    """
    특정 캠페인의 콘텐츠(소제목) 목록 조회

    캠페인명으로 스케줄 시트를 필터링하여
    해당 캠페인의 모든 콘텐츠를 반환합니다.

    Args:
        spreadsheet_id: 스프레드시트 ID
        campaign_name: 캠페인명
        sheet_name: 시트 이름 (기본값: '스케줄')
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        contents = await sheets_service.get_campaign_contents(
            spreadsheet_id,
            campaign_name,
            sheet_name
        )

        return {
            "success": True,
            "campaign_name": campaign_name,
            "total_contents": len(contents),
            "contents": contents
        }

    except Exception as e:
        logger.error(f"Error getting campaign contents: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update-status")
async def update_status(request: StatusUpdateRequest):
    """
    콘텐츠 상태 업데이트

    Args:
        spreadsheet_id: 스프레드시트 ID
        row_index: 행 번호 (1부터 시작, 헤더 포함)
        status: 새 상태
        sheet_name: 시트 이름
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        success = await sheets_service.update_content_status(
            request.spreadsheet_id,
            request.row_index,
            request.status,
            request.sheet_name
        )

        return {
            "success": success,
            "message": f"Updated row {request.row_index} to status: {request.status}"
        }

    except Exception as e:
        logger.error(f"Error updating status: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resources/{spreadsheet_id}")
async def get_resources(
    spreadsheet_id: str,
    campaign_name: Optional[str] = None,
    topic: Optional[str] = None,
    sheet_name: str = "리소스"
):
    """
    리소스 시트 읽기

    리소스 시트 구조:
    | 캠페인명 | 소제목 | 리소스명 | 리소스타입 | URL/경로 | 용도 | 업로드일 |
    |---------|--------|----------|------------|----------|------|----------|
    | AI자동화 | 소개편 | logo.png | image | gs://... | 인트로 | 2026-01-01 |

    Args:
        spreadsheet_id: 스프레드시트 ID
        campaign_name: 필터링할 캠페인명 (옵션)
        topic: 필터링할 소제목 (옵션)
        sheet_name: 시트 이름 (기본값: '리소스')
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        resources = await sheets_service.read_resources_sheet(
            spreadsheet_id,
            campaign_name=campaign_name,
            topic=topic,
            sheet_name=sheet_name
        )

        return {
            "success": True,
            "total_resources": len(resources),
            "campaign_name": campaign_name,
            "topic": topic,
            "resources": resources
        }

    except Exception as e:
        logger.error(f"Error reading resources: {e}")
        raise HTTPException(status_code=400, detail=str(e))


class ResourceAddRequest(BaseModel):
    """리소스 추가 요청"""
    spreadsheet_id: str
    campaign_name: str
    topic: str
    resource_name: str
    resource_type: str  # image, video, pdf, audio
    url: str
    purpose: Optional[str] = ""
    sheet_name: str = "리소스"


@router.post("/resources/add")
async def add_resource(request: ResourceAddRequest):
    """
    리소스 시트에 새 리소스 추가

    Args:
        spreadsheet_id: 스프레드시트 ID
        campaign_name: 캠페인명
        topic: 소제목
        resource_name: 리소스명
        resource_type: 리소스 타입 (image, video, pdf, audio)
        url: 리소스 URL 또는 경로
        purpose: 용도 (인트로, 메인, CTA 등)
        sheet_name: 시트 이름 (기본값: '리소스')
    """
    sheets_service = get_sheets_service()

    if not sheets_service.is_available():
        raise HTTPException(status_code=503, detail="Google Sheets service not available")

    try:
        success = await sheets_service.add_resource_to_sheet(
            spreadsheet_id=request.spreadsheet_id,
            campaign_name=request.campaign_name,
            topic=request.topic,
            resource_name=request.resource_name,
            resource_type=request.resource_type,
            url=request.url,
            purpose=request.purpose or "",
            sheet_name=request.sheet_name
        )

        return {
            "success": success,
            "message": f"Added resource '{request.resource_name}' to '{request.sheet_name}' sheet"
        }

    except Exception as e:
        logger.error(f"Error adding resource: {e}")
        raise HTTPException(status_code=400, detail=str(e))
