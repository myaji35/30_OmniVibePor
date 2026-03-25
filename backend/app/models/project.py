"""
Project 모델 — User ↔ Campaign 사이의 프로젝트 레이어

BMAD Data 계층: User → Project → Campaign → Content

주의: campaigns 테이블에 project_id 컬럼이 없으면 마이그레이션 필요.
      현재는 projects 단독으로 동작하며, campaign_count는 연동 시 활성화.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import aiosqlite
import logging

logger = logging.getLogger(__name__)
DB_PATH = "./omni_db.sqlite"


class ProjectStatus(str, Enum):
    DRAFT     = "draft"
    ACTIVE    = "active"
    COMPLETED = "completed"
    ARCHIVED  = "archived"


class ProjectPlatform(str, Enum):
    YOUTUBE   = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK    = "tiktok"
    ALL       = "all"


# ── Pydantic 스키마 ──────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name:        str              = Field(..., min_length=1, max_length=100)
    description: Optional[str]   = Field(None, max_length=500)
    platform:    ProjectPlatform  = ProjectPlatform.YOUTUBE
    template_id: Optional[int]   = None
    user_id:     int


class ProjectUpdate(BaseModel):
    name:        Optional[str]            = None
    description: Optional[str]           = None
    platform:    Optional[ProjectPlatform]= None
    status:      Optional[ProjectStatus]  = None


class ProjectResponse(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    platform:    str
    status:      str
    template_id: Optional[int]
    user_id:     int
    created_at:  str
    updated_at:  str


# ── DB 스키마 ────────────────────────────────────────────────────────

CREATE_PROJECTS_TABLE = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    description TEXT,
    platform    TEXT    NOT NULL DEFAULT 'youtube',
    status      TEXT    NOT NULL DEFAULT 'draft',
    template_id INTEGER,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_PROJECT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_projects_status  ON projects(status);",
]


# ── CRUD ─────────────────────────────────────────────────────────────

class ProjectCRUD:

    @staticmethod
    async def init_table() -> None:
        """앱 시작 시 테이블 및 인덱스 초기화"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(CREATE_PROJECTS_TABLE)
            for sql in CREATE_PROJECT_INDEXES:
                await db.execute(sql)
            await db.commit()
        logger.info("✅ projects 테이블 초기화 완료")

    @staticmethod
    async def create(data: ProjectCreate) -> ProjectResponse:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """INSERT INTO projects (user_id, name, description, platform, template_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (data.user_id, data.name, data.description,
                 data.platform.value, data.template_id),
            )
            await db.commit()
            row = await (await db.execute(
                "SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)
            )).fetchone()
        return _to_response(row)

    @staticmethod
    async def get(project_id: int) -> Optional[ProjectResponse]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            )).fetchone()
        return _to_response(row) if row else None

    @staticmethod
    async def list_by_user(
        user_id: int,
        status: Optional[ProjectStatus] = None,
    ) -> List[ProjectResponse]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if status:
                rows = await (await db.execute(
                    "SELECT * FROM projects WHERE user_id = ? AND status = ? "
                    "ORDER BY updated_at DESC",
                    (user_id, status.value),
                )).fetchall()
            else:
                rows = await (await db.execute(
                    "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,),
                )).fetchall()
        return [_to_response(r) for r in rows]

    @staticmethod
    async def update(project_id: int, data: ProjectUpdate) -> Optional[ProjectResponse]:
        fields, values = [], []
        if data.name        is not None: fields.append("name = ?");        values.append(data.name)
        if data.description is not None: fields.append("description = ?"); values.append(data.description)
        if data.platform    is not None: fields.append("platform = ?");    values.append(data.platform.value)
        if data.status      is not None: fields.append("status = ?");      values.append(data.status.value)
        if not fields:
            return await ProjectCRUD.get(project_id)
        fields.append("updated_at = datetime('now')")
        values.append(project_id)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", values
            )
            await db.commit()
        return await ProjectCRUD.get(project_id)

    @staticmethod
    async def delete(project_id: int) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM projects WHERE id = ?", (project_id,)
            )
            await db.commit()
        return cursor.rowcount > 0


def _to_response(row) -> ProjectResponse:
    return ProjectResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        platform=row["platform"],
        status=row["status"],
        template_id=row["template_id"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
