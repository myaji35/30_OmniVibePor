"""클라이언트 관리 API

클라이언트 CRUD 엔드포인트 구현
- Neo4j 기반 클라이언트 관리
- 브랜드 정보, 산업 분야, 담당자 정보 저장
"""
from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.models.client import (
    ClientCreate,
    ClientUpdate,
    Client,
    ClientModel
)
from app.services.neo4j_client import get_neo4j_client

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

class ClientService:
    """클라이언트 CRUD 서비스 (Neo4j 기반)"""

    def __init__(self, neo4j_client):
        self.client = neo4j_client

    def create_client(self, client: ClientModel) -> dict:
        """클라이언트 생성"""
        query = """
        CREATE (c:Client {
            client_id: $client_id,
            name: $name,
            brand_color: $brand_color,
            logo_url: $logo_url,
            industry: $industry,
            contact_email: $contact_email,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN c.client_id as client_id,
               c.name as name,
               c.brand_color as brand_color,
               c.logo_url as logo_url,
               c.industry as industry,
               c.contact_email as contact_email,
               c.created_at as created_at,
               c.updated_at as updated_at
        """

        params = {
            "client_id": client.client_id,
            "name": client.name,
            "brand_color": client.brand_color,
            "logo_url": client.logo_url,
            "industry": client.industry,
            "contact_email": client.contact_email,
            "created_at": client.created_at.isoformat(),
            "updated_at": client.updated_at.isoformat()
        }

        result = self.client.query(query, params)

        if result:
            return result[0]
        return None

    def get_client(self, client_id: str) -> Optional[dict]:
        """클라이언트 조회"""
        query = """
        MATCH (c:Client {client_id: $client_id})
        RETURN c.client_id as client_id,
               c.name as name,
               c.brand_color as brand_color,
               c.logo_url as logo_url,
               c.industry as industry,
               c.contact_email as contact_email,
               c.created_at as created_at,
               c.updated_at as updated_at
        """

        result = self.client.query(query, {"client_id": client_id})

        if result:
            return result[0]
        return None

    def get_all_clients(
        self,
        industry: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """모든 클라이언트 조회 (필터링 및 페이징)"""
        if industry:
            query = """
            MATCH (c:Client)
            WHERE c.industry = $industry
            RETURN c.client_id as client_id,
                   c.name as name,
                   c.brand_color as brand_color,
                   c.logo_url as logo_url,
                   c.industry as industry,
                   c.contact_email as contact_email,
                   c.created_at as created_at,
                   c.updated_at as updated_at
            ORDER BY c.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            params = {"industry": industry, "skip": skip, "limit": limit}
        else:
            query = """
            MATCH (c:Client)
            RETURN c.client_id as client_id,
                   c.name as name,
                   c.brand_color as brand_color,
                   c.logo_url as logo_url,
                   c.industry as industry,
                   c.contact_email as contact_email,
                   c.created_at as created_at,
                   c.updated_at as updated_at
            ORDER BY c.created_at DESC
            SKIP $skip
            LIMIT $limit
            """
            params = {"skip": skip, "limit": limit}

        return self.client.query(query, params)

    def update_client(self, client_id: str, updates: dict) -> bool:
        """클라이언트 업데이트"""
        if not updates:
            return True

        # updated_at 자동 갱신
        updates["updated_at"] = datetime.utcnow().isoformat()

        # SET 절 생성
        set_clauses = ", ".join([f"c.{key} = ${key}" for key in updates.keys()])

        query = f"""
        MATCH (c:Client {{client_id: $client_id}})
        SET {set_clauses}
        RETURN c.client_id as client_id
        """

        params = {"client_id": client_id, **updates}
        result = self.client.query(query, params)

        return len(result) > 0

    def delete_client(self, client_id: str) -> bool:
        """클라이언트 삭제"""
        query = """
        MATCH (c:Client {client_id: $client_id})
        DETACH DELETE c
        RETURN count(c) as deleted_count
        """

        result = self.client.query(query, {"client_id": client_id})

        if result and result[0].get("deleted_count", 0) > 0:
            return True
        return False


def get_client_service() -> ClientService:
    """클라이언트 서비스 인스턴스"""
    neo4j_client = get_neo4j_client()
    return ClientService(neo4j_client)


# ==================== API Endpoints ====================

@router.post("/clients", response_model=Client, status_code=201)
async def create_client(request: ClientCreate):
    """
    **클라이언트 생성**

    새로운 클라이언트를 생성합니다.

    - **name**: 클라이언트 이름 (필수)
    - **brand_color**: 브랜드 컬러 (Hex 형식, 예: #FF5733)
    - **logo_url**: 로고 URL
    - **industry**: 산업 분야 (예: IT, 제조, 교육 등)
    - **contact_email**: 담당자 이메일

    **반환값**: 생성된 클라이언트 정보
    """
    try:
        service = get_client_service()

        # 클라이언트 모델 생성
        client_model = ClientModel(
            name=request.name,
            brand_color=request.brand_color,
            logo_url=request.logo_url,
            industry=request.industry,
            contact_email=request.contact_email
        )

        # Neo4j에 저장
        result = service.create_client(client_model)

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create client"
            )

        logger.info(f"Client created: {result['client_id']}")
        return Client(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/clients", response_model=List[Client])
async def get_clients(
    industry: Optional[str] = Query(None, description="산업 분야 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 개수")
):
    """
    **클라이언트 목록 조회**

    모든 클라이언트를 조회합니다. 산업 분야로 필터링 가능합니다.

    - **industry**: 산업 분야 필터 (선택)
    - **skip**: 건너뛸 개수 (기본: 0)
    - **limit**: 최대 개수 (기본: 100, 최대: 1000)

    **반환값**: 클라이언트 목록
    """
    try:
        service = get_client_service()

        clients = service.get_all_clients(
            industry=industry,
            skip=skip,
            limit=limit
        )

        logger.info(f"Retrieved {len(clients)} clients")
        return [Client(**c) for c in clients]

    except Exception as e:
        logger.error(f"Failed to get clients: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    """
    **클라이언트 조회**

    클라이언트 ID로 단일 클라이언트 정보를 조회합니다.

    - **client_id**: 클라이언트 고유 ID

    **반환값**: 클라이언트 상세 정보
    """
    try:
        service = get_client_service()

        result = service.get_client(client_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Client not found: {client_id}"
            )

        logger.info(f"Retrieved client: {client_id}")
        return Client(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, request: ClientUpdate):
    """
    **클라이언트 수정**

    클라이언트 정보를 부분적으로 수정합니다.

    - **client_id**: 클라이언트 ID
    - **name**: 새로운 이름 (선택)
    - **brand_color**: 새로운 브랜드 컬러 (선택)
    - **logo_url**: 새로운 로고 URL (선택)
    - **industry**: 새로운 산업 분야 (선택)
    - **contact_email**: 새로운 담당자 이메일 (선택)

    **반환값**: 수정된 클라이언트 정보
    """
    try:
        service = get_client_service()

        # 클라이언트 존재 확인
        existing = service.get_client(client_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Client not found: {client_id}"
            )

        # 수정할 필드만 추출
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.brand_color is not None:
            updates["brand_color"] = request.brand_color
        if request.logo_url is not None:
            updates["logo_url"] = request.logo_url
        if request.industry is not None:
            updates["industry"] = request.industry
        if request.contact_email is not None:
            updates["contact_email"] = request.contact_email

        if not updates:
            # 수정할 내용이 없으면 기존 정보 반환
            return Client(**existing)

        # Neo4j 업데이트
        success = service.update_client(client_id, updates)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update client"
            )

        # 수정된 클라이언트 조회
        updated = service.get_client(client_id)

        logger.info(f"Client updated: {client_id}")
        return Client(**updated)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/clients/{client_id}", status_code=204)
async def delete_client(client_id: str):
    """
    **클라이언트 삭제**

    클라이언트 및 관련된 모든 데이터를 삭제합니다.

    - **client_id**: 삭제할 클라이언트 ID

    **반환값**: 없음 (204 No Content)

    **주의**: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        service = get_client_service()

        # 클라이언트 존재 확인
        existing = service.get_client(client_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Client not found: {client_id}"
            )

        # 클라이언트 삭제
        success = service.delete_client(client_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete client"
            )

        logger.info(f"Client deleted: {client_id}")
        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete client: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
