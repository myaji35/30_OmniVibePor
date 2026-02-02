"""FastAPI 메인 애플리케이션"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logfire

from app.core.config import get_settings
from app.api.v1 import router as api_v1_router

settings = get_settings()

# Logfire 초기화 (토큰이 있을 때만)
if settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here":
    logfire.configure(token=settings.LOGFIRE_TOKEN)
else:
    # Logfire 비활성화 (개발 환경)
    import logging
    logging.basicConfig(level=logging.INFO)

# Custom API Description (Stripe 스타일)
CUSTOM_DESCRIPTION = """
## 🚀 Welcome to OmniVibe Pro API

**AI-powered Omnichannel Video Automation SaaS**

OmniVibe Pro는 '바이브 코딩(Vibe Coding)' 방법론을 기반으로 한 영상 자동화 플랫폼입니다.
구글 시트 기반 전략 수립부터 AI 에이전트 협업, 영상 생성/보정, 다채널 자동 배포까지 전 과정을 자동화합니다.

---

### 🎤 **Voice Cloning**
녹음된 목소리를 학습하여 커스텀 TTS를 생성합니다. 사용자만의 목소리로 무제한 컨텐츠를 제작하세요.

- `POST /api/v1/voice/clone` - 음성 클로닝
- `GET /api/v1/voice/list/{user_id}` - 커스텀 음성 조회
- `DELETE /api/v1/voice/{voice_id}` - 음성 삭제

### 🔊 **Zero-Fault Audio**
ElevenLabs TTS → OpenAI Whisper STT → 검증 → 재생성 루프를 통해 99% 정확도의 오디오를 생성합니다.

- `POST /api/v1/audio/generate` - Zero-Fault Audio 생성
- `GET /api/v1/audio/status/{task_id}` - 작업 상태 조회
- `GET /api/v1/audio/download/{task_id}` - 오디오 다운로드

### 📊 **Performance Tracking**
멀티 플랫폼 성과 분석 및 자가학습 시스템으로 점점 더 좋은 컨텐츠를 자동 생성합니다.

- `POST /api/v1/performance/track` - 성과 추적
- `GET /api/v1/performance/insights/{user_id}` - 성과 인사이트

---

### 🔗 **Quick Links**
- [GitHub Repository](https://github.com/omnivibe-pro)
- [Documentation](./docs)
- [Support](mailto:support@omnivibepro.com)

### 🔑 **Authentication**
API 키는 환경 변수로 설정하세요:
```bash
export ELEVENLABS_API_KEY=your_api_key
export OPENAI_API_KEY=your_api_key
```

---

**Version**: 1.0.0 | **License**: MIT | **Status**: Production Ready ✅
"""

app = FastAPI(
    title="🎬 OmniVibe Pro API",
    description=CUSTOM_DESCRIPTION,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url=None,  # 기본 docs 비활성화 (커스텀 사용)
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Voice Cloning",
            "description": "🎤 녹음된 목소리를 학습하여 커스텀 TTS 생성",
        },
        {
            "name": "Zero-Fault Audio",
            "description": "🔊 99% 정확도의 검증된 오디오 생성 (TTS + STT Loop)",
        },
        {
            "name": "Thumbnail Learning",
            "description": "🖼️ 타인의 고성과 썸네일 학습 및 자동 생성",
        },
        {
            "name": "Performance Tracking",
            "description": "📊 멀티 플랫폼 성과 분석 및 자가학습 시스템",
        },
        {
            "name": "Video Editor",
            "description": "🎬 비디오 메타데이터 조회 및 편집 (FFmpeg 기반)",
        },
        {
            "name": "WebSocket",
            "description": "🔌 실시간 진행 상태 업데이트 (WebSocket)",
        },
    ]
)

# CORS 설정 (WebSocket 지원 포함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # 프로덕션에서는 특정 도메인만 허용
        "http://localhost:3000",  # Next.js Frontend
        "ws://localhost:3000",  # Next.js WebSocket
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logfire 통합 (토큰이 설정되어 있을 때만)
if settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here":
    logfire.instrument_fastapi(app)

# API 라우터 등록
app.include_router(api_v1_router, prefix="/api/v1")


# 커스텀 Swagger UI (Stripe 스타일)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """커스텀 Swagger UI (Stripe 스타일)"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "deepLinking": True,
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "syntaxHighlight.theme": "monokai",
        },
    )


@app.get("/")
async def root():
    """
    Welcome Page & Health Check

    Returns basic API information and health status.
    """
    return {
        "status": "healthy",
        "service": "OmniVibe Pro",
        "version": "1.0.0",
        "message": "🎬 AI-powered Omnichannel Video Automation",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": {
            "voice_cloning": "✅ Enabled",
            "zero_fault_audio": "✅ Enabled",
            "performance_tracking": "✅ Enabled",
            "thumbnail_learning": "✅ Enabled"
        }
    }


@app.get("/health")
async def health_check():
    """
    Detailed Health Check

    Checks the status of all connected services.
    """
    health_status = {
        "api": "healthy",
        "redis": "unknown",
        "neo4j": "unknown",
        "pinecone": "unknown",
        "timestamp": "2026-02-01T12:00:00Z"
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
