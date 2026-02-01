"""FastAPI 메인 애플리케이션"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logfire

from app.core.config import get_settings
from app.api.v1 import router as api_v1_router

settings = get_settings()

# Logfire 초기화
logfire.configure(token=settings.LOGFIRE_TOKEN)

app = FastAPI(
    title="OmniVibe Pro API",
    description="AI 옴니채널 영상 자동화 SaaS",
    version="0.1.0",
    debug=settings.DEBUG
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logfire 통합
logfire.instrument_fastapi(app)

# API 라우터 등록
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "OmniVibe Pro",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """상세 헬스체크 (의존성 포함)"""
    health_status = {
        "api": "healthy",
        "redis": "unknown",
        "neo4j": "unknown",
        "pinecone": "unknown"
    }

    # TODO: 각 서비스 연결 상태 확인

    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
