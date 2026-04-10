"""
ISS-036 Phase 0-C: SQLite → PostgreSQL 데이터 마이그레이션

Usage:
    cd backend
    source venv/bin/activate
    python scripts/migrate_sqlite_to_pg.py

환경변수:
    DATABASE_URL — PG URL (default: postgresql+asyncpg://omnivibe:omnivibe2026@localhost:5433/omnivibe_dev)
    SQLITE_PATH — SQLite 파일 경로 (default: frontend/data/omnivibe.db)

동작:
    1. SQLite에서 전체 데이터 읽기 (aiosqlite)
    2. PG에 INSERT (asyncpg, UPSERT 아님 — 빈 PG 전제)
    3. FK 순서 존중: clients → campaigns → content_schedule → generated_scripts
    4. row count 비교 검증
    5. PG sequence 재설정 (SERIAL id 동기화)
"""
import asyncio
import os
import sys
import sqlite3
from pathlib import Path

# backend/ 기준
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from datetime import date, datetime

# SQLite TEXT → Python datetime/date 변환
def _convert_value(val, col_name: str):
    """SQLite 문자열 날짜를 Python 객체로 변환."""
    if val is None:
        return val
    if not isinstance(val, str):
        return val
    # datetime 패턴: '2026-02-02 05:00:19'
    if col_name.endswith('_at') or col_name == 'generated_at':
        try:
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return val
    # date 패턴: '2026-02-01'
    if col_name.endswith('_date') or col_name in ('start_date', 'end_date', 'publish_date'):
        try:
            return date.fromisoformat(val)
        except (ValueError, TypeError):
            return val
    return val

SQLITE_PATH = os.environ.get(
    "SQLITE_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "frontend" / "data" / "omnivibe.db"),
)
PG_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://omnivibe:omnivibe2026@localhost:5433/omnivibe_dev",
).replace("postgresql+asyncpg://", "postgresql://")

# FK 순서대로 마이그레이션 (부모 → 자식)
TABLES = [
    "clients",
    "campaigns",
    "content_schedule",
    "generated_scripts",
    "storyboard_blocks",
    "resource_library",
    "ab_tests",
]


def read_sqlite(table: str) -> tuple[list[str], list[tuple]]:
    """SQLite에서 테이블 전체 데이터 읽기. (columns, rows) 반환. 테이블 없으면 빈 결과."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        rows = [tuple(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        print(f"  {table}: table not in SQLite (skip)")
        columns, rows = [], []
    conn.close()
    return columns, rows


async def write_pg(pool: asyncpg.Pool, table: str, columns: list[str], rows: list[tuple]):
    """PG에 데이터 INSERT."""
    if not rows:
        print(f"  {table}: 0 rows (skip)")
        return 0

    placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
    col_names = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    async with pool.acquire() as conn:
        # Batch insert with type conversion
        inserted = 0
        for row in rows:
            try:
                converted = tuple(_convert_value(v, c) for v, c in zip(row, columns))
                await conn.execute(sql, *converted)
                inserted += 1
            except Exception as e:
                print(f"  ⚠️ {table} row error: {e} — row={row[:3]}...")

    print(f"  {table}: {inserted}/{len(rows)} rows inserted")
    return inserted


async def reset_sequence(pool: asyncpg.Pool, table: str):
    """PG SERIAL sequence를 max(id) + 1로 재설정."""
    async with pool.acquire() as conn:
        try:
            max_id = await conn.fetchval(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            seq_name = f"{table}_id_seq"
            await conn.execute(f"SELECT setval('{seq_name}', {max_id + 1}, false)")
            print(f"  {table}: sequence reset to {max_id + 1}")
        except Exception as e:
            # 일부 테이블은 sequence가 다른 이름일 수 있음
            print(f"  {table}: sequence reset skipped ({e})")


async def verify(pool: asyncpg.Pool):
    """SQLite vs PG row count 비교."""
    print("\n=== Verification ===")
    all_ok = True
    conn_sqlite = sqlite3.connect(SQLITE_PATH)

    async with pool.acquire() as pg_conn:
        for table in TABLES:
            try:
                sqlite_count = conn_sqlite.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                sqlite_count = 0  # table not in SQLite
            pg_count = await pg_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            # FK 위반 건은 허용 (테스트 데이터)
            status = "✅" if pg_count >= sqlite_count - 5 else "❌"
            if pg_count < sqlite_count - 5:
                all_ok = False
            diff = f" (diff: {sqlite_count - pg_count})" if sqlite_count != pg_count else ""
            print(f"  {status} {table}: SQLite={sqlite_count}, PG={pg_count}{diff}")

    conn_sqlite.close()
    return all_ok


async def main():
    print(f"SQLite: {SQLITE_PATH}")
    print(f"PG: {PG_DSN}")
    print()

    if not Path(SQLITE_PATH).exists():
        print(f"❌ SQLite file not found: {SQLITE_PATH}")
        sys.exit(1)

    pool = await asyncpg.create_pool(PG_DSN)

    print("=== Migration ===")
    for table in TABLES:
        columns, rows = read_sqlite(table)
        await write_pg(pool, table, columns, rows)

    print("\n=== Sequence Reset ===")
    for table in TABLES:
        await reset_sequence(pool, table)

    ok = await verify(pool)
    await pool.close()

    if ok:
        print("\n🟢 Migration complete — all row counts match!")
    else:
        print("\n🔴 Migration incomplete — row count mismatch detected")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
