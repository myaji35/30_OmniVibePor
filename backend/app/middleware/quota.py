"""
Quota 관리 Middleware — Tier별 한도 연동

4개 플랜 Tier:
  free       → 렌더 3/월,  오디오 10/월
  creator    → 렌더 30/월, 오디오 100/월
  pro        → 렌더 100/월, 오디오 무제한(-1)
  enterprise → 모두 무제한(-1)
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.jwt import verify_access_token
import logging

logger = logging.getLogger(__name__)

# ── Tier별 한도 정의 ────────────────────────────────────────────────
# -1 = 무제한
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free":       {"render": 3,   "audio": 10,  "voice_clone": 0},
    "creator":    {"render": 30,  "audio": 100, "voice_clone": 1},
    "pro":        {"render": 100, "audio": -1,  "voice_clone": 3},
    "enterprise": {"render": -1,  "audio": -1,  "voice_clone": 10},
}

# 기본 플랜 (미설정 사용자)
DEFAULT_PLAN = "free"

# Quota 체크 경로 → 소모 유형 매핑
QUOTA_PATH_MAP: dict[str, str] = {
    "/api/v1/video/render":    "render",
    "/api/v1/remotion/render": "render",
    "/api/v1/audio/generate":  "audio",
    "/api/v1/writer/generate": "audio",  # TTS 포함
    "/api/v1/voice/clone":     "voice_clone",
}


def _get_quota_type(path: str) -> str | None:
    for prefix, quota_type in QUOTA_PATH_MAP.items():
        if path.startswith(prefix):
            return quota_type
    return None


def _get_redis_client():
    """Redis 클라이언트 (실패 시 None 반환 — fail-open)"""
    try:
        import redis
        from app.core.config import get_settings
        return redis.from_url(get_settings().REDIS_URL, decode_responses=True, socket_timeout=1)
    except Exception:
        return None


def _get_usage_key(user_id: str, quota_type: str) -> str:
    """Redis 키: 월별 리셋 포함"""
    from datetime import datetime
    ym = datetime.utcnow().strftime("%Y%m")
    return f"quota:{user_id}:{quota_type}:{ym}"


def get_current_usage(user_id: str, quota_type: str) -> int:
    """현재 사용량 조회 (Redis)"""
    rc = _get_redis_client()
    if not rc:
        return 0
    try:
        val = rc.get(_get_usage_key(user_id, quota_type))
        return int(val) if val else 0
    except Exception:
        return 0


def increment_usage(user_id: str, quota_type: str) -> int:
    """사용량 1 증가 → 새 값 반환"""
    rc = _get_redis_client()
    if not rc:
        return 0
    try:
        key = _get_usage_key(user_id, quota_type)
        new_val = rc.incr(key)
        # 이달 말까지 TTL 설정 (최대 32일)
        if new_val == 1:
            rc.expire(key, 32 * 24 * 3600)
        return new_val
    except Exception as e:
        logger.warning(f"Quota increment 실패 (무시): {e}")
        return 0


def get_quota_status(user_id: str, plan: str) -> dict:
    """사용자의 전체 Quota 현황"""
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS[DEFAULT_PLAN])
    result = {}
    for qt, limit in limits.items():
        used = get_current_usage(user_id, qt)
        result[qt] = {
            "used":      used,
            "limit":     limit,
            "remaining": -1 if limit == -1 else max(0, limit - used),
            "exceeded":  False if limit == -1 else used >= limit,
        }
    return result


class QuotaMiddleware(BaseHTTPMiddleware):
    """Tier별 Quota 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        # POST 요청 + 해당 경로만 체크
        if request.method != "POST":
            return await call_next(request)

        quota_type = _get_quota_type(request.url.path)
        if not quota_type:
            return await call_next(request)

        # 토큰에서 user_id, plan 추출
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        payload = verify_access_token(auth_header[7:])
        if not payload:
            return await call_next(request)

        user_id = payload.get("user_id") or payload.get("sub")
        plan    = payload.get("plan", DEFAULT_PLAN)

        if not user_id:
            return await call_next(request)

        # 한도 확인
        limit = PLAN_LIMITS.get(plan, PLAN_LIMITS[DEFAULT_PLAN]).get(quota_type, 0)

        if limit == -1:
            # 무제한 플랜 — 사용량만 기록
            increment_usage(user_id, quota_type)
            return await call_next(request)

        used = get_current_usage(user_id, quota_type)
        if used >= limit:
            logger.warning(f"[QUOTA] 초과: user={user_id}, plan={plan}, type={quota_type}, {used}/{limit}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error_code":  "QUOTA_EXCEEDED",
                    "message":     f"이번 달 {quota_type} 한도({limit}회)를 초과했습니다. 플랜을 업그레이드하세요.",
                    "action":      "upgrade_plan",
                    "quota_used":  used,
                    "quota_limit": limit,
                    "plan":        plan,
                    "upgrade_url": "/settings/billing",
                },
            )

        # 통과 → 요청 실행
        response = await call_next(request)

        # 성공 응답에만 사용량 증가
        if 200 <= response.status_code < 300:
            increment_usage(user_id, quota_type)

        return response


class QuotaChecker:
    """수동 Quota 체크 헬퍼 (서비스 레이어에서 직접 호출 시 사용)"""

    @staticmethod
    def check(user_id: str, plan: str, quota_type: str) -> None:
        """한도 초과 시 HTTPException 발생"""
        limit = PLAN_LIMITS.get(plan, PLAN_LIMITS[DEFAULT_PLAN]).get(quota_type, 0)
        if limit == -1:
            return
        used = get_current_usage(user_id, quota_type)
        if used >= limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code":  "QUOTA_EXCEEDED",
                    "message":     f"이번 달 {quota_type} 한도({limit}회)를 초과했습니다.",
                    "action":      "upgrade_plan",
                    "quota_used":  used,
                    "quota_limit": limit,
                },
            )

    @staticmethod
    def increment(user_id: str, quota_type: str) -> int:
        return increment_usage(user_id, quota_type)

    @staticmethod
    def status(user_id: str, plan: str) -> dict:
        return get_quota_status(user_id, plan)
