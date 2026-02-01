"""API v1 라우터"""
from fastapi import APIRouter

from .thumbnail_learner import router as thumbnail_router
from .performance import router as performance_router
from .audio import router as audio_router
from .voice import router as voice_router

router = APIRouter()

# 서브 라우터 등록
router.include_router(thumbnail_router, prefix="/thumbnails", tags=["Thumbnail Learning"])
router.include_router(performance_router, prefix="/performance", tags=["Performance Tracking"])
router.include_router(audio_router, prefix="/audio", tags=["Zero-Fault Audio"])
router.include_router(voice_router, prefix="/voice", tags=["Voice Cloning"])

# 향후 추가될 라우터들
# router.include_router(agent_router, prefix="/agents", tags=["Agents"])
