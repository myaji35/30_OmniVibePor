"""
글로벌 에러 핸들러 미들웨어

모든 예외를 포착하여 사용자 친화적인 JSON 응답으로 변환한다.
에러 코드, 메시지, 권장 액션을 포함한다.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

logger = logging.getLogger(__name__)

# ── 에러 코드 정의 ──────────────────────────────────────────────────────────
ERROR_CODES: dict[str, dict] = {
    # 외부 API 관련
    "CREDIT_EXHAUSTED":   {"status": 402, "message": "API 크레딧이 부족합니다. 빌링 페이지에서 충전하세요.", "action": "billing_redirect"},
    "API_TIMEOUT":        {"status": 504, "message": "외부 API 응답이 지연되고 있습니다. 잠시 후 재시도하세요.", "action": "retry_later"},
    "API_RATE_LIMITED":   {"status": 429, "message": "API 호출 한도를 초과했습니다.", "action": "retry_later"},

    # 렌더링 관련
    "RENDER_OOM":         {"status": 507, "message": "렌더링 메모리가 부족합니다. 해상도를 낮춰 재시도하세요.", "action": "reduce_quality"},
    "RENDER_CODEC_ERROR": {"status": 500, "message": "영상 인코딩 중 오류가 발생했습니다.", "action": "contact_support"},
    "RENDER_TIMEOUT":     {"status": 504, "message": "렌더링 시간이 초과되었습니다. 영상 길이를 줄여보세요.", "action": "reduce_length"},

    # 업로드 관련
    "UPLOAD_FAILED":      {"status": 502, "message": "파일 업로드에 실패했습니다. 재시도 버튼을 클릭하세요.", "action": "retry_upload"},
    "FILE_TOO_LARGE":     {"status": 413, "message": "파일 크기가 너무 큽니다. 100MB 이하로 압축해주세요.", "action": "compress_file"},
    "INVALID_FORMAT":     {"status": 415, "message": "지원하지 않는 파일 형식입니다.", "action": "check_format"},

    # 인프라 관련
    "WORKER_DOWN":        {"status": 503, "message": "작업 처리 서버가 점검 중입니다. 잠시 후 재시도하세요.", "action": "retry_later"},
    "DB_CONNECTION":      {"status": 503, "message": "데이터베이스 연결에 실패했습니다.", "action": "retry_later"},
    "CACHE_ERROR":        {"status": 500, "message": "캐시 서버 오류가 발생했습니다.", "action": "retry_later"},

    # 인증/권한 관련
    "QUOTA_EXCEEDED":     {"status": 403, "message": "이번 달 사용량 한도를 초과했습니다. 플랜을 업그레이드하세요.", "action": "upgrade_plan"},
    "TOKEN_EXPIRED":      {"status": 401, "message": "로그인이 만료되었습니다. 다시 로그인하세요.", "action": "relogin"},
    "UNAUTHORIZED":       {"status": 401, "message": "인증이 필요합니다.", "action": "relogin"},

    # 기본
    "UNKNOWN":            {"status": 500, "message": "알 수 없는 오류가 발생했습니다.", "action": "contact_support"},
}


class AppError(Exception):
    """애플리케이션 전용 에러 — error_code로 적절한 응답 자동 생성"""
    def __init__(self, error_code: str, detail: str | None = None):
        self.error_code = error_code
        self.detail = detail
        super().__init__(detail or ERROR_CODES.get(error_code, {}).get("message", ""))


def _build_response(error_code: str, detail: str | None = None, extra: dict | None = None) -> JSONResponse:
    """에러 코드 → JSONResponse 변환"""
    info = ERROR_CODES.get(error_code, ERROR_CODES["UNKNOWN"])
    body = {
        "error_code": error_code,
        "message": detail or info["message"],
        "action": info["action"],
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=info["status"], content=body)


# ── 핸들러 함수들 ─────────────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """AppError 전용 핸들러"""
    logger.error(f"[{exc.error_code}] {request.url}: {exc.detail}")
    return _build_response(exc.error_code, exc.detail)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTPException → 통일된 형식으로 변환"""
    # 상태 코드별 에러 코드 매핑
    code_map = {
        401: "UNAUTHORIZED",
        403: "QUOTA_EXCEEDED",
        404: "UNKNOWN",
        429: "API_RATE_LIMITED",
        413: "FILE_TOO_LARGE",
    }
    error_code = code_map.get(exc.status_code, "UNKNOWN")
    info = ERROR_CODES.get(error_code, ERROR_CODES["UNKNOWN"])
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": str(exc.detail),
            "action": info["action"],
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 유효성 검사 에러 → 사용자 친화적 메시지"""
    errors = []
    for e in exc.errors():
        field = " → ".join(str(loc) for loc in e["loc"])
        errors.append({"field": field, "message": e["msg"]})

    logger.warning(f"[VALIDATION_ERROR] {request.url}: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "입력값이 올바르지 않습니다.",
            "action": "check_input",
            "errors": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """모든 미처리 예외 포착"""
    tb = traceback.format_exc()
    logger.error(f"[UNHANDLED] {request.url}\n{tb}")
    return _build_response("UNKNOWN", detail="서버 내부 오류가 발생했습니다.")


def register_error_handlers(app) -> None:
    """FastAPI 앱에 모든 에러 핸들러 등록 — main.py에서 호출"""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    logger.info("✅ 글로벌 에러 핸들러 등록 완료")
