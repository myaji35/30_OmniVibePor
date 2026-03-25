"""
Cloudinary 업로드 실패 시 로컬 파일 보존 + 재업로드 관리 (E-4)

동작:
1. Cloudinary 업로드 실패 시 outputs/fallback/ 에 파일 복사
2. SQLite fallback_uploads 테이블에 재업로드 대기 등록
3. Celery beat 태스크가 주기적으로 재시도
"""
import shutil
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import aiosqlite

from app.core.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

FALLBACK_DIR = Path(settings.OUTPUTS_DIR) / "fallback"
DB_PATH      = "./omni_db.sqlite"

CREATE_FALLBACK_TABLE = """
CREATE TABLE IF NOT EXISTS fallback_uploads (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    local_path   TEXT    NOT NULL,
    folder       TEXT    NOT NULL DEFAULT 'omnivibe',
    resource_type TEXT   NOT NULL DEFAULT 'video',
    attempts     INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    last_error   TEXT,
    status       TEXT    NOT NULL DEFAULT 'pending',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


async def init_fallback_table() -> None:
    """앱 시작 시 테이블 초기화"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_FALLBACK_TABLE)
        await db.commit()


async def save_fallback(
    src_path:      str,
    folder:        str = "omnivibe",
    resource_type: str = "video",
) -> str:
    """
    업로드 실패한 파일을 로컬에 보존하고 재시도 큐에 등록.

    Returns:
        fallback 로컬 경로
    """
    FALLBACK_DIR.mkdir(parents=True, exist_ok=True)

    src   = Path(src_path)
    dest  = FALLBACK_DIR / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{src.name}"
    shutil.copy2(src, dest)
    logger.info(f"[Fallback] 파일 보존: {dest}")

    # DB 등록
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO fallback_uploads (local_path, folder, resource_type)
               VALUES (?, ?, ?)""",
            (str(dest), folder, resource_type),
        )
        await db.commit()

    return str(dest)


async def get_pending_fallbacks(limit: int = 10) -> list[dict]:
    """재업로드 대기 항목 조회"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            """SELECT * FROM fallback_uploads
               WHERE status = 'pending' AND attempts < max_attempts
               ORDER BY created_at ASC LIMIT ?""",
            (limit,),
        )).fetchall()
    return [dict(r) for r in rows]


async def mark_fallback_success(fallback_id: int, cloudinary_url: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE fallback_uploads
               SET status='completed', updated_at=datetime('now')
               WHERE id=?""",
            (fallback_id,),
        )
        await db.commit()
    logger.info(f"[Fallback] 재업로드 성공: id={fallback_id}, url={cloudinary_url}")


async def mark_fallback_failed(fallback_id: int, error: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(
            "SELECT attempts, max_attempts FROM fallback_uploads WHERE id=?",
            (fallback_id,),
        )).fetchone()
        if row:
            new_attempts = row[0] + 1
            new_status   = "failed" if new_attempts >= row[1] else "pending"
            await db.execute(
                """UPDATE fallback_uploads
                   SET attempts=?, last_error=?, status=?, updated_at=datetime('now')
                   WHERE id=?""",
                (new_attempts, error, new_status, fallback_id),
            )
            await db.commit()


async def retry_pending_uploads() -> dict:
    """
    대기 중인 fallback 파일들을 Cloudinary에 재업로드.
    Celery beat 태스크에서 주기적으로 호출.
    """
    from app.services.cloudinary_service import CloudinaryService  # 순환 import 방지

    pending = await get_pending_fallbacks()
    results = {"success": 0, "failed": 0, "skipped": 0}

    svc = CloudinaryService()

    for item in pending:
        local_path = item["local_path"]
        if not Path(local_path).exists():
            logger.warning(f"[Fallback] 파일 없음, 건너뜀: {local_path}")
            results["skipped"] += 1
            continue

        try:
            if item["resource_type"] == "video":
                result = await svc.upload_video(local_path, folder=item["folder"])
            else:
                result = await svc.upload_image(local_path, folder=item["folder"])

            await mark_fallback_success(item["id"], result.get("secure_url", ""))
            results["success"] += 1
        except Exception as e:
            await mark_fallback_failed(item["id"], str(e))
            results["failed"] += 1

    logger.info(f"[Fallback] 재업로드 결과: {results}")
    return results
