"""
Template / TemplateScene 모델 — 갤러리 데이터 정규화

기존 frontend/data/ 정적 JSON → DB로 정규화하여 동적 관리.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import aiosqlite
import logging

logger = logging.getLogger(__name__)
DB_PATH = "./omni_db.sqlite"


class TemplatePlatform(str, Enum):
    YOUTUBE   = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK    = "tiktok"
    ALL       = "all"


class TemplateCategory(str, Enum):
    EDUCATION    = "education"
    MARKETING    = "marketing"
    TUTORIAL     = "tutorial"
    STORYTELLING = "storytelling"
    PROMOTION    = "promotion"
    NEWS         = "news"


class TemplateLayoutType(str, Enum):
    TEXT_CENTER  = "text-center"
    TEXT_IMAGE   = "text-image"
    INFOGRAPHIC  = "infographic"
    LIST_REVEAL  = "list-reveal"
    FULL_VISUAL  = "full-visual"
    SPLIT_SCREEN = "split-screen"
    GRAPH_FOCUS  = "graph-focus"


# ── Pydantic 스키마 ──────────────────────────────────────────────────

class TemplateSceneCreate(BaseModel):
    order:        int
    layout_type:  TemplateLayoutType
    default_text: Optional[str] = None
    duration_sec: int           = 5
    animation:    str           = "fadeIn"


class TemplateCreate(BaseModel):
    name:          str              = Field(..., min_length=1, max_length=100)
    description:   Optional[str]   = None
    platform:      TemplatePlatform
    category:      TemplateCategory
    thumbnail_url: Optional[str]   = None
    preview_url:   Optional[str]   = None
    is_public:     bool             = True
    scenes:        List[TemplateSceneCreate] = []


class TemplateSceneResponse(BaseModel):
    id:           int
    template_id:  int
    order:        int
    layout_type:  str
    default_text: Optional[str]
    duration_sec: int
    animation:    str


class TemplateResponse(BaseModel):
    id:            int
    name:          str
    description:   Optional[str]
    platform:      str
    category:      str
    thumbnail_url: Optional[str]
    preview_url:   Optional[str]
    is_public:     bool
    use_count:     int
    scenes:        List[TemplateSceneResponse] = []
    created_at:    str
    updated_at:    str


# ── DB 스키마 ────────────────────────────────────────────────────────

CREATE_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS templates (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    description   TEXT,
    platform      TEXT    NOT NULL DEFAULT 'youtube',
    category      TEXT    NOT NULL DEFAULT 'education',
    thumbnail_url TEXT,
    preview_url   TEXT,
    is_public     INTEGER NOT NULL DEFAULT 1,
    use_count     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_TEMPLATE_SCENES_TABLE = """
CREATE TABLE IF NOT EXISTS template_scenes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id  INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    scene_order  INTEGER NOT NULL DEFAULT 0,
    layout_type  TEXT    NOT NULL DEFAULT 'text-center',
    default_text TEXT,
    duration_sec INTEGER NOT NULL DEFAULT 5,
    animation    TEXT    NOT NULL DEFAULT 'fadeIn'
);
"""

# 주의: ORDER는 SQLite 예약어 — scene_order 컬럼명 사용
CREATE_TEMPLATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_templates_platform  ON templates(platform);",
    "CREATE INDEX IF NOT EXISTS idx_templates_category  ON templates(category);",
    "CREATE INDEX IF NOT EXISTS idx_tscenes_template_id ON template_scenes(template_id);",
]


# ── CRUD ─────────────────────────────────────────────────────────────

class TemplateCRUD:

    @staticmethod
    async def init_table() -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(CREATE_TEMPLATES_TABLE)
            await db.execute(CREATE_TEMPLATE_SCENES_TABLE)
            for sql in CREATE_TEMPLATE_INDEXES:
                await db.execute(sql)
            await db.commit()
        logger.info("✅ templates / template_scenes 테이블 초기화 완료")

    @staticmethod
    async def create(data: TemplateCreate) -> TemplateResponse:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """INSERT INTO templates
                   (name, description, platform, category, thumbnail_url, preview_url, is_public)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (data.name, data.description, data.platform.value, data.category.value,
                 data.thumbnail_url, data.preview_url, int(data.is_public)),
            )
            tid = cursor.lastrowid
            for scene in data.scenes:
                await db.execute(
                    """INSERT INTO template_scenes
                       (template_id, scene_order, layout_type, default_text, duration_sec, animation)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (tid, scene.order, scene.layout_type.value,
                     scene.default_text, scene.duration_sec, scene.animation),
                )
            await db.commit()
        return await TemplateCRUD.get(tid)

    @staticmethod
    async def get(template_id: int) -> Optional[TemplateResponse]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            t = await (await db.execute(
                "SELECT * FROM templates WHERE id = ?", (template_id,)
            )).fetchone()
            if not t:
                return None
            scenes = await (await db.execute(
                "SELECT * FROM template_scenes WHERE template_id = ? ORDER BY scene_order",
                (template_id,),
            )).fetchall()
        return _build(t, scenes)

    @staticmethod
    async def list(
        platform:    Optional[TemplatePlatform] = None,
        category:    Optional[TemplateCategory] = None,
        public_only: bool = True,
    ) -> List[TemplateResponse]:
        conds, params = [], []
        if public_only:           conds.append("is_public = 1")
        if platform is not None:  conds.append("platform = ?"); params.append(platform.value)
        if category is not None:  conds.append("category = ?"); params.append(category.value)
        where = f"WHERE {' AND '.join(conds)}" if conds else ""

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                f"SELECT * FROM templates {where} ORDER BY use_count DESC", params
            )).fetchall()
            result = []
            for t in rows:
                scenes = await (await db.execute(
                    "SELECT * FROM template_scenes WHERE template_id = ? ORDER BY scene_order",
                    (t["id"],),
                )).fetchall()
                result.append(_build(t, scenes))
        return result

    @staticmethod
    async def increment_use_count(template_id: int) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE templates SET use_count = use_count + 1 WHERE id = ?",
                (template_id,),
            )
            await db.commit()

    @staticmethod
    async def delete(template_id: int) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM templates WHERE id = ?", (template_id,)
            )
            await db.commit()
        return cursor.rowcount > 0


def _build(t_row, s_rows) -> TemplateResponse:
    return TemplateResponse(
        id=t_row["id"], name=t_row["name"], description=t_row["description"],
        platform=t_row["platform"], category=t_row["category"],
        thumbnail_url=t_row["thumbnail_url"], preview_url=t_row["preview_url"],
        is_public=bool(t_row["is_public"]), use_count=t_row["use_count"],
        scenes=[
            TemplateSceneResponse(
                id=s["id"], template_id=s["template_id"], order=s["scene_order"],
                layout_type=s["layout_type"], default_text=s["default_text"],
                duration_sec=s["duration_sec"], animation=s["animation"],
            )
            for s in s_rows
        ],
        created_at=t_row["created_at"], updated_at=t_row["updated_at"],
    )
