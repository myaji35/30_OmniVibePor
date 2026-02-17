"""
Quota 관리 Middleware
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.user import UserCRUD
from app.services.neo4j_client import get_neo4j_client
from app.auth.jwt import verify_access_token


class QuotaMiddleware(BaseHTTPMiddleware):
    """
    API 호출 시 사용자의 Quota를 확인하는 Middleware

    영상 생성 관련 API에서만 Quota를 체크합니다.
    """

    # Quota 체크가 필요한 엔드포인트
    QUOTA_REQUIRED_PATHS = [
        "/api/v1/video/render",
        "/api/v1/audio/generate",
        "/api/v1/writer/generate",
        "/api/v1/remotion/render"
    ]

    async def dispatch(self, request: Request, call_next):
        """요청 전처리: Quota 확인"""

        # Quota 체크가 필요한 경로인지 확인
        if not any(request.url.path.startswith(path) for path in self.QUOTA_REQUIRED_PATHS):
            # Quota 체크 불필요, 다음으로 진행
            return await call_next(request)

        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # 인증 없이는 Quota 체크 불가 (auth middleware에서 처리됨)
            return await call_next(request)

        token = auth_header.replace("Bearer ", "")

        # 토큰 검증 및 사용자 정보 추출
        payload = verify_access_token(token)
        if not payload:
            return await call_next(request)

        user_id = payload.get("user_id")
        if not user_id:
            return await call_next(request)

        # Neo4j에서 사용자 Quota 조회
        neo4j_client = get_neo4j_client()
        user_crud = UserCRUD(neo4j_client)

        user = user_crud.get_user_by_id(user_id)
        if not user:
            return await call_next(request)

        quota_limit = user.get("quota_limit", 10)
        quota_used = user.get("quota_used", 0)

        # Quota 초과 체크
        if quota_used >= quota_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Quota exceeded",
                    "message": f"You have reached your monthly limit of {quota_limit} videos.",
                    "quota_limit": quota_limit,
                    "quota_used": quota_used,
                    "quota_remaining": 0,
                    "upgrade_url": "/billing/plans"
                }
            )

        # Quota 체크 통과, 요청 처리
        response = await call_next(request)

        # 성공적인 응답 (200번대)인 경우 quota_used 증가
        if 200 <= response.status_code < 300:
            # POST 요청만 Quota 소진 (조회는 제외)
            if request.method == "POST":
                user_crud.update_user(user_id, {
                    "quota_used": quota_used + 1
                })

        return response


class QuotaChecker:
    """
    수동으로 Quota를 체크하는 헬퍼 클래스
    """

    @staticmethod
    async def check_and_increment(user_id: str) -> bool:
        """
        사용자의 Quota를 체크하고 1 증가

        Args:
            user_id: 사용자 ID

        Returns:
            bool: Quota 사용 가능 여부

        Raises:
            HTTPException: Quota 초과 시
        """
        neo4j_client = get_neo4j_client()
        user_crud = UserCRUD(neo4j_client)

        user = user_crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        quota_limit = user.get("quota_limit", 10)
        quota_used = user.get("quota_used", 0)

        if quota_used >= quota_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Quota exceeded",
                    "message": f"You have reached your monthly limit of {quota_limit} videos.",
                    "quota_limit": quota_limit,
                    "quota_used": quota_used,
                    "quota_remaining": 0,
                    "upgrade_url": "/billing/plans"
                }
            )

        # Quota 증가
        user_crud.update_user(user_id, {
            "quota_used": quota_used + 1
        })

        return True

    @staticmethod
    async def get_quota_status(user_id: str) -> dict:
        """
        사용자의 Quota 상태 조회

        Args:
            user_id: 사용자 ID

        Returns:
            dict: Quota 정보
        """
        neo4j_client = get_neo4j_client()
        user_crud = UserCRUD(neo4j_client)

        user = user_crud.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        quota_limit = user.get("quota_limit", 10)
        quota_used = user.get("quota_used", 0)
        quota_remaining = max(0, quota_limit - quota_used)

        return {
            "quota_limit": quota_limit,
            "quota_used": quota_used,
            "quota_remaining": quota_remaining,
            "usage_percentage": (quota_used / quota_limit * 100) if quota_limit > 0 else 0,
            "is_exceeded": quota_used >= quota_limit
        }
