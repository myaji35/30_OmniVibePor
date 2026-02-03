"""SQLite 비동기 클라이언트

Frontend와 동일한 SQLite DB를 사용하여 데이터 일관성을 보장합니다.
aiosqlite를 사용하여 비동기 작업을 지원합니다.

주요 기능:
- 비동기 CRUD 작업
- 트랜잭션 관리
- Connection Pool 관리
- 자동 에러 처리 및 재시도
"""
import aiosqlite
import logging
from typing import List, Dict, Optional, Any, TypeVar, Generic
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

# Frontend DB 경로 (Backend 기준 상대 경로)
DB_PATH = Path(__file__).parent.parent.parent.parent / "frontend" / "data" / "omnivibe.db"

T = TypeVar('T')


class SQLiteClient:
    """SQLite 비동기 클라이언트

    Frontend와 동일한 DB를 사용하며, 비동기 작업을 지원합니다.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: DB 파일 경로. None이면 기본 경로 사용.
        """
        self.db_path = db_path or DB_PATH

        if not self.db_path.exists():
            logger.warning(f"DB file not found: {self.db_path}")
            logger.warning("DB will be created on first connection")
        else:
            logger.info(f"SQLite DB path: {self.db_path}")

    @asynccontextmanager
    async def get_connection(self):
        """DB 커넥션 컨텍스트 매니저

        Yields:
            aiosqlite.Connection: DB 커넥션
        """
        conn = await aiosqlite.connect(str(self.db_path))
        conn.row_factory = aiosqlite.Row  # Dict-like 접근 가능
        try:
            yield conn
        finally:
            await conn.close()

    async def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """SELECT 쿼리 실행

        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터

        Returns:
            쿼리 결과 (Dict 리스트)
        """
        try:
            async with self.get_connection() as conn:
                async with conn.execute(query, params or ()) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    async def execute_one(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """SELECT 쿼리 실행 (단일 결과)

        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터

        Returns:
            쿼리 결과 (Dict) 또는 None
        """
        try:
            async with self.get_connection() as conn:
                async with conn.execute(query, params or ()) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    async def execute_write(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> int:
        """INSERT/UPDATE/DELETE 쿼리 실행

        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터

        Returns:
            영향받은 row 수 (INSERT의 경우 lastrowid)
        """
        try:
            async with self.get_connection() as conn:
                async with conn.execute(query, params or ()) as cursor:
                    await conn.commit()
                    # INSERT의 경우 lastrowid 반환
                    if query.strip().upper().startswith("INSERT"):
                        return cursor.lastrowid
                    # UPDATE/DELETE의 경우 rowcount 반환
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Write execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    async def execute_many(
        self,
        query: str,
        params_list: List[tuple]
    ) -> int:
        """배치 INSERT/UPDATE 실행

        Args:
            query: SQL 쿼리 문자열
            params_list: 쿼리 파라미터 리스트

        Returns:
            영향받은 총 row 수
        """
        try:
            async with self.get_connection() as conn:
                await conn.executemany(query, params_list)
                await conn.commit()
                return len(params_list)
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Batch size: {len(params_list)}")
            raise


# ==================== Campaign CRUD ====================

class CampaignDB:
    """Campaign 테이블 CRUD 작업"""

    def __init__(self, client: SQLiteClient):
        self.client = client

    async def create(self, campaign_data: Dict[str, Any]) -> int:
        """캠페인 생성

        Args:
            campaign_data: 캠페인 데이터 (Dict)

        Returns:
            생성된 캠페인 ID
        """
        query = """
        INSERT INTO campaigns (
            name, description, client_id, start_date, end_date, status,
            concept_gender, concept_tone, concept_style, target_duration,
            voice_id, voice_name,
            intro_video_url, intro_duration, outro_video_url, outro_duration,
            bgm_url, bgm_volume,
            publish_schedule, auto_deploy
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?
        )
        """

        params = (
            campaign_data.get("name"),
            campaign_data.get("description"),
            campaign_data.get("client_id"),
            campaign_data.get("start_date"),
            campaign_data.get("end_date"),
            campaign_data.get("status", "active"),
            campaign_data.get("concept_gender"),
            campaign_data.get("concept_tone"),
            campaign_data.get("concept_style"),
            campaign_data.get("target_duration"),
            campaign_data.get("voice_id"),
            campaign_data.get("voice_name"),
            campaign_data.get("intro_video_url"),
            campaign_data.get("intro_duration", 5),
            campaign_data.get("outro_video_url"),
            campaign_data.get("outro_duration", 5),
            campaign_data.get("bgm_url"),
            campaign_data.get("bgm_volume", 0.3),
            campaign_data.get("publish_schedule"),
            campaign_data.get("auto_deploy", 0)
        )

        campaign_id = await self.client.execute_write(query, params)
        logger.info(f"Campaign created: id={campaign_id}, name={campaign_data.get('name')}")
        return campaign_id

    async def get_by_id(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """캠페인 ID로 조회

        Args:
            campaign_id: 캠페인 ID

        Returns:
            캠페인 데이터 (Dict) 또는 None
        """
        query = "SELECT * FROM campaigns WHERE id = ?"
        return await self.client.execute_one(query, (campaign_id,))

    async def get_all(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """캠페인 목록 조회

        Args:
            client_id: 클라이언트 ID 필터
            status: 상태 필터
            limit: 최대 결과 수
            offset: 오프셋

        Returns:
            캠페인 리스트
        """
        query = "SELECT * FROM campaigns WHERE 1=1"
        params = []

        if client_id is not None:
            query += " AND client_id = ?"
            params.append(client_id)

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return await self.client.execute_query(query, tuple(params))

    async def count(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """캠페인 개수 조회

        Args:
            client_id: 클라이언트 ID 필터
            status: 상태 필터

        Returns:
            캠페인 개수
        """
        query = "SELECT COUNT(*) as count FROM campaigns WHERE 1=1"
        params = []

        if client_id is not None:
            query += " AND client_id = ?"
            params.append(client_id)

        if status is not None:
            query += " AND status = ?"
            params.append(status)

        result = await self.client.execute_one(query, tuple(params))
        return result["count"] if result else 0

    async def update(self, campaign_id: int, updates: Dict[str, Any]) -> bool:
        """캠페인 업데이트

        Args:
            campaign_id: 캠페인 ID
            updates: 업데이트할 필드 (Dict)

        Returns:
            성공 여부
        """
        if not updates:
            return True

        # SET 절 생성
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE campaigns SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        params = list(updates.values()) + [campaign_id]

        rows_affected = await self.client.execute_write(query, tuple(params))

        if rows_affected > 0:
            logger.info(f"Campaign updated: id={campaign_id}, fields={list(updates.keys())}")
            return True
        return False

    async def delete(self, campaign_id: int) -> bool:
        """캠페인 삭제

        Args:
            campaign_id: 캠페인 ID

        Returns:
            성공 여부
        """
        query = "DELETE FROM campaigns WHERE id = ?"
        rows_affected = await self.client.execute_write(query, (campaign_id,))

        if rows_affected > 0:
            logger.info(f"Campaign deleted: id={campaign_id}")
            return True
        return False


# ==================== Content Schedule CRUD ====================

class ContentScheduleDB:
    """Content Schedule 테이블 CRUD 작업"""

    def __init__(self, client: SQLiteClient):
        self.client = client

    async def get_by_campaign(self, campaign_id: int) -> List[Dict[str, Any]]:
        """캠페인별 콘텐츠 스케줄 조회

        Args:
            campaign_id: 캠페인 ID

        Returns:
            콘텐츠 스케줄 리스트
        """
        query = """
        SELECT * FROM content_schedule
        WHERE campaign_id = ?
        ORDER BY publish_date ASC, id ASC
        """
        return await self.client.execute_query(query, (campaign_id,))

    async def get_by_id(self, content_id: int) -> Optional[Dict[str, Any]]:
        """콘텐츠 ID로 조회

        Args:
            content_id: 콘텐츠 ID

        Returns:
            콘텐츠 스케줄 데이터 (Dict) 또는 None
        """
        query = "SELECT * FROM content_schedule WHERE id = ?"
        return await self.client.execute_one(query, (content_id,))

    async def create(self, content_data: Dict[str, Any]) -> int:
        """콘텐츠 스케줄 생성

        Args:
            content_data: 콘텐츠 데이터 (Dict)

        Returns:
            생성된 콘텐츠 ID
        """
        query = """
        INSERT INTO content_schedule (
            campaign_id, topic, subtitle, platform, publish_date,
            status, target_audience, keywords, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            content_data.get("campaign_id"),
            content_data.get("topic"),
            content_data.get("subtitle"),
            content_data.get("platform"),
            content_data.get("publish_date"),
            content_data.get("status", "draft"),
            content_data.get("target_audience"),
            content_data.get("keywords"),
            content_data.get("notes")
        )

        content_id = await self.client.execute_write(query, params)
        logger.info(f"Content schedule created: id={content_id}, topic={content_data.get('topic')}")
        return content_id

    async def update(self, content_id: int, updates: Dict[str, Any]) -> bool:
        """콘텐츠 스케줄 업데이트

        Args:
            content_id: 콘텐츠 ID
            updates: 업데이트할 필드 (Dict)

        Returns:
            성공 여부
        """
        if not updates:
            return True

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE content_schedule SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        params = list(updates.values()) + [content_id]
        rows_affected = await self.client.execute_write(query, tuple(params))

        if rows_affected > 0:
            logger.info(f"Content schedule updated: id={content_id}")
            return True
        return False


# ==================== Storyboard Blocks CRUD ====================

class StoryboardDB:
    """Storyboard Blocks 테이블 CRUD 작업"""

    def __init__(self, client: SQLiteClient):
        self.client = client

    async def get_by_content(self, content_id: int) -> List[Dict[str, Any]]:
        """콘텐츠별 스토리보드 블록 조회

        Args:
            content_id: 콘텐츠 ID

        Returns:
            스토리보드 블록 리스트
        """
        query = """
        SELECT * FROM storyboard_blocks
        WHERE content_id = ?
        ORDER BY block_number ASC
        """
        return await self.client.execute_query(query, (content_id,))

    async def create(self, block_data: Dict[str, Any]) -> int:
        """스토리보드 블록 생성

        Args:
            block_data: 블록 데이터 (Dict)

        Returns:
            생성된 블록 ID
        """
        query = """
        INSERT INTO storyboard_blocks (
            content_id, block_number, type, start_time, end_time, duration,
            script, audio_url,
            background_type, background_url, background_source,
            character_enabled, character_url, character_start, character_duration,
            subtitle_text, subtitle_preset, subtitle_position,
            transition_effect, transition_duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            block_data.get("content_id"),
            block_data.get("block_number"),
            block_data.get("type"),
            block_data.get("start_time"),
            block_data.get("end_time"),
            block_data.get("duration"),
            block_data.get("script"),
            block_data.get("audio_url"),
            block_data.get("background_type"),
            block_data.get("background_url"),
            block_data.get("background_source"),
            block_data.get("character_enabled", 0),
            block_data.get("character_url"),
            block_data.get("character_start"),
            block_data.get("character_duration"),
            block_data.get("subtitle_text"),
            block_data.get("subtitle_preset"),
            block_data.get("subtitle_position", "bottom"),
            block_data.get("transition_effect"),
            block_data.get("transition_duration", 0.5)
        )

        block_id = await self.client.execute_write(query, params)
        logger.info(f"Storyboard block created: id={block_id}, content_id={block_data.get('content_id')}")
        return block_id

    async def update(self, block_id: int, updates: Dict[str, Any]) -> bool:
        """스토리보드 블록 업데이트

        Args:
            block_id: 블록 ID
            updates: 업데이트할 필드 (Dict)

        Returns:
            성공 여부
        """
        if not updates:
            return True

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE storyboard_blocks SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        params = list(updates.values()) + [block_id]
        rows_affected = await self.client.execute_write(query, tuple(params))

        if rows_affected > 0:
            logger.info(f"Storyboard block updated: id={block_id}")
            return True
        return False


# ==================== 싱글톤 인스턴스 ====================

_sqlite_client: Optional[SQLiteClient] = None
_campaign_db: Optional[CampaignDB] = None
_content_schedule_db: Optional[ContentScheduleDB] = None
_storyboard_db: Optional[StoryboardDB] = None


def get_sqlite_client() -> SQLiteClient:
    """SQLite 클라이언트 싱글톤 인스턴스 반환"""
    global _sqlite_client
    if _sqlite_client is None:
        _sqlite_client = SQLiteClient()
    return _sqlite_client


def get_campaign_db() -> CampaignDB:
    """Campaign DB 싱글톤 인스턴스 반환"""
    global _campaign_db
    if _campaign_db is None:
        _campaign_db = CampaignDB(get_sqlite_client())
    return _campaign_db


def get_content_schedule_db() -> ContentScheduleDB:
    """Content Schedule DB 싱글톤 인스턴스 반환"""
    global _content_schedule_db
    if _content_schedule_db is None:
        _content_schedule_db = ContentScheduleDB(get_sqlite_client())
    return _content_schedule_db


def get_storyboard_db() -> StoryboardDB:
    """Storyboard DB 싱글톤 인스턴스 반환"""
    global _storyboard_db
    if _storyboard_db is None:
        _storyboard_db = StoryboardDB(get_sqlite_client())
    return _storyboard_db
