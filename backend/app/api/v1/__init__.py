"""API v1 라우터"""
from fastapi import APIRouter

from .thumbnail_learner import router as thumbnail_router
from .performance import router as performance_router
from .audio import router as audio_router
from .voice import router as voice_router
from .sheets import router as sheets_router
from .writer import router as writer_router
from .director import router as director_router
from .continuity import router as continuity_router
from .projects import router as projects_router
from .lipsync import router as lipsync_router
from .costs import router as costs_router
from .video import router as video_router
from .media import router as media_router
from .websocket import router as websocket_router
from .editor import router as editor_router
from .bgm import router as bgm_router
from .presets import router as presets_router

router = APIRouter()

# 서브 라우터 등록
router.include_router(thumbnail_router, prefix="/thumbnails", tags=["Thumbnail Learning"])
router.include_router(performance_router, prefix="/performance", tags=["Performance Tracking"])
router.include_router(audio_router, prefix="/audio", tags=["Zero-Fault Audio"])
router.include_router(voice_router, prefix="/voice", tags=["Voice Cloning"])
router.include_router(sheets_router, tags=["Google Sheets"])
router.include_router(writer_router, tags=["Writer Agent"])
router.include_router(director_router, tags=["Director Agent"])
router.include_router(continuity_router, tags=["Continuity Agent"])
router.include_router(projects_router, tags=["Project Management"])
router.include_router(lipsync_router, tags=["Lipsync"])
router.include_router(costs_router, tags=["Cost Tracking"])
router.include_router(video_router, prefix="/video", tags=["Video Rendering"])
router.include_router(media_router, prefix="/media", tags=["Media Optimization"])
router.include_router(editor_router, tags=["Video Editor"])
router.include_router(bgm_router, tags=["BGM Editor"])
router.include_router(presets_router, tags=["Custom Presets"])
router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
