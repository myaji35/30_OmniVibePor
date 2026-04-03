"""멀티채널 배포 API — 예약 발행 + 성과 추적 → GraphRAG 피드백

ISS-010: Phase 5.4
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/publish", tags=["Multi-Channel Publish"])
logger = logging.getLogger(__name__)


class PublishRequest(BaseModel):
    """배포 요청"""
    content_id: Optional[int] = Field(None, description="콘텐츠 스케줄 ID")
    title: str = Field(..., description="콘텐츠 제목")
    channel: str = Field(..., description="채널 (youtube, instagram, tiktok, blog)")
    content_url: str = Field(..., description="콘텐츠 파일 URL (영상/프레젠테이션)")
    description: Optional[str] = Field(None, description="설명")
    tags: list[str] = Field(default=[], description="태그")
    schedule_at: Optional[str] = Field(None, description="예약 발행 시간 (ISO 8601). 없으면 즉시")
    campaign_id: Optional[int] = Field(None, description="캠페인 ID")


class PublishResult(BaseModel):
    """배포 결과"""
    publish_id: str
    channel: str
    status: str  # scheduled, published, failed
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    platform_url: Optional[str] = None
    message: str


class PerformanceFeedback(BaseModel):
    """성과 피드백"""
    content_id: str
    channel: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    watch_time_avg: float = 0.0  # 초
    score: float = 0.0  # 0~10
    collected_at: str


@router.post("/schedule", response_model=PublishResult)
async def schedule_publish(request: PublishRequest):
    """
    콘텐츠 예약 발행

    - schedule_at이 있으면 예약, 없으면 즉시 발행 큐에 추가
    - 실제 플랫폼 API 연동은 향후 확장
    - 현재는 상태 관리 + 스케줄 DB 저장
    """
    try:
        import uuid
        publish_id = str(uuid.uuid4())[:12]

        scheduled_at = request.schedule_at
        status = "scheduled" if scheduled_at else "publishing"

        # 콘텐츠 스케줄 DB에 저장
        try:
            from app.db.sqlite_client import get_content_schedule_db
            db = get_content_schedule_db()
            if request.content_id:
                db.update(request.content_id, {
                    "status": status,
                    "publish_date": scheduled_at or datetime.utcnow().isoformat(),
                    "notes": f"publish_id={publish_id}",
                })
        except Exception as e:
            logger.warning(f"DB update failed: {e}")

        # Celery 태스크로 예약 발행 (향후 확장)
        # publish_to_channel_task.apply_async(args=[publish_id], eta=schedule_at)

        # GraphRAG에 발행 이벤트 기록
        await _record_publish_event(publish_id, request)

        logger.info(f"Content scheduled: {publish_id} → {request.channel} ({status})")

        return PublishResult(
            publish_id=publish_id,
            channel=request.channel,
            status=status,
            scheduled_at=scheduled_at,
            published_at=None if scheduled_at else datetime.utcnow().isoformat(),
            platform_url=None,
            message=f"{'예약 완료' if scheduled_at else '발행 큐에 추가됨'}: {request.channel}",
        )
    except Exception as e:
        logger.error(f"Publish failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_performance_feedback(feedback: PerformanceFeedback):
    """
    성과 데이터 제출 → GraphRAG에 저장 → 전략 피드백 루프

    성과 데이터를 Neo4j에 저장하여 다음 전략 수립 시 활용합니다.
    """
    try:
        await _store_performance_to_graphrag(feedback)

        # 점수 기반 자동 태그
        tags = []
        if feedback.score >= 8.0:
            tags.append("high_performer")
        elif feedback.score >= 5.0:
            tags.append("average")
        else:
            tags.append("needs_improvement")

        if feedback.engagement_rate >= 5.0:
            tags.append("high_engagement")

        return {
            "status": "recorded",
            "content_id": feedback.content_id,
            "score": feedback.score,
            "tags": tags,
            "message": "성과 데이터가 GraphRAG에 저장되었습니다. 다음 전략에 반영됩니다.",
        }
    except Exception as e:
        logger.error(f"Feedback recording failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels")
async def list_available_channels():
    """지원 채널 목록"""
    return {
        "channels": [
            {
                "id": "youtube",
                "name": "YouTube",
                "formats": ["video"],
                "status": "ready",
                "api_connected": False,
                "description": "영상 업로드 + 제목/설명/태그 자동 설정",
            },
            {
                "id": "instagram",
                "name": "Instagram",
                "formats": ["video", "image"],
                "status": "ready",
                "api_connected": False,
                "description": "릴스/피드 게시 + 해시태그 자동 생성",
            },
            {
                "id": "tiktok",
                "name": "TikTok",
                "formats": ["video"],
                "status": "ready",
                "api_connected": False,
                "description": "숏폼 영상 업로드 + 트렌딩 해시태그",
            },
            {
                "id": "blog",
                "name": "블로그",
                "formats": ["article", "presentation"],
                "status": "ready",
                "api_connected": False,
                "description": "네이버/티스토리 블로그 포스팅",
            },
        ]
    }


@router.get("/history")
async def get_publish_history(
    channel: Optional[str] = None,
    limit: int = 20,
):
    """발행 이력 조회"""
    try:
        from app.db.sqlite_client import get_content_schedule_db
        db = get_content_schedule_db()
        items = db.list_all(limit=limit)

        if channel:
            items = [i for i in items if i.get("platform", "").lower() == channel.lower()]

        published = [i for i in items if i.get("status") in ("published", "scheduled")]

        return {
            "total": len(published),
            "items": published[:limit],
        }
    except Exception as e:
        return {"total": 0, "items": [], "error": str(e)}


async def _record_publish_event(publish_id: str, request: PublishRequest):
    """Neo4j에 발행 이벤트 기록"""
    try:
        from app.services.neo4j_client import get_neo4j_client
        client = get_neo4j_client()
        if client:
            await client.run_query(
                """
                MERGE (p:PublishEvent {publish_id: $pid})
                SET p.channel = $channel, p.title = $title,
                    p.content_url = $url, p.created_at = datetime()
                """,
                {"pid": publish_id, "channel": request.channel,
                 "title": request.title, "url": request.content_url}
            )
    except Exception as e:
        logger.warning(f"Neo4j publish event record failed: {e}")


async def _store_performance_to_graphrag(feedback: PerformanceFeedback):
    """성과 데이터를 Neo4j GraphRAG에 저장"""
    try:
        from app.services.neo4j_client import get_neo4j_client
        client = get_neo4j_client()
        if client:
            await client.run_query(
                """
                MERGE (p:Performance {content_id: $cid, channel: $ch})
                SET p.views = $views, p.likes = $likes, p.comments = $comments,
                    p.shares = $shares, p.engagement_rate = $er,
                    p.watch_time_avg = $wta, p.score = $score,
                    p.collected_at = $cat
                """,
                {
                    "cid": feedback.content_id, "ch": feedback.channel,
                    "views": feedback.views, "likes": feedback.likes,
                    "comments": feedback.comments, "shares": feedback.shares,
                    "er": feedback.engagement_rate, "wta": feedback.watch_time_avg,
                    "score": feedback.score, "cat": feedback.collected_at,
                }
            )
    except Exception as e:
        logger.warning(f"Neo4j performance store failed: {e}")
