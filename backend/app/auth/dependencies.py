"""FastAPI 인증 의존성"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt_handler import verify_token
from app.models.user import UserRole
from app.services.neo4j_client import Neo4jClient
from app.models.neo4j_models import Neo4jCRUDManager

# HTTP Bearer 스키마 (Authorization: Bearer <token>)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    현재 인증된 사용자 조회

    Args:
        credentials: HTTP Bearer 토큰

    Returns:
        사용자 정보 (user_id, email, role 등)

    Raises:
        HTTPException: 401 - 토큰이 유효하지 않음
        HTTPException: 401 - 사용자를 찾을 수 없음
    """
    token = credentials.credentials

    # 토큰 검증
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Neo4j에서 사용자 조회
    neo4j_client = Neo4jClient()
    crud_manager = Neo4jCRUDManager(neo4j_client)

    user = crud_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 비활성화된 사용자 확인
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    현재 활성화된 사용자 조회 (별칭)

    Args:
        current_user: 현재 사용자

    Returns:
        사용자 정보
    """
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    특정 역할을 가진 사용자만 접근 가능하도록 제한

    Args:
        allowed_roles: 허용된 역할 목록

    Returns:
        의존성 함수

    Example:
        @app.get("/admin/users", dependencies=[Depends(require_role([UserRole.ADMIN]))])
        async def list_users():
            ...
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", UserRole.USER.value)

        # UserRole enum으로 변환
        try:
            user_role_enum = UserRole(user_role)
        except ValueError:
            user_role_enum = UserRole.USER

        if user_role_enum not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
            )

        return current_user

    return role_checker


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)
) -> Optional[dict]:
    """
    선택적 인증 (토큰이 있으면 검증, 없으면 None 반환)

    Args:
        credentials: HTTP Bearer 토큰 (선택)

    Returns:
        사용자 정보 또는 None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
