"""
SQLAlchemy 모델 모음 — ISS-036 Phase 0-A

현재(Phase 0-A Stage 1)는 기존 frontend/data/omnivibe.db 스키마를
SQLAlchemy 2.0 DeclarativeBase로 reverse engineering 한다.
Phase 0-F에서 agencies / agency_members / agency_id 컬럼이 추가될 예정.

모델 순서 (외래키 의존성):
    Client → Campaign → ContentSchedule → GeneratedScript / StoryboardBlock / ResourceLibrary
    AbTest (backend/omni_db.sqlite, 별도)

Phase 0-F에서 추가:
    Agency (새 루트)
    AgencyMember (Agency ↔ User 매핑)
    기존 Client / Campaign 에 agency_id 컬럼 추가
"""
from app.db.models.client import Client
from app.db.models.campaign import Campaign
from app.db.models.content_schedule import ContentSchedule
from app.db.models.generated_script import GeneratedScript
from app.db.models.storyboard_block import StoryboardBlock
from app.db.models.resource_library import ResourceLibrary
from app.db.models.ab_test import AbTest

__all__ = [
    "Client",
    "Campaign",
    "ContentSchedule",
    "GeneratedScript",
    "StoryboardBlock",
    "ResourceLibrary",
    "AbTest",
]
