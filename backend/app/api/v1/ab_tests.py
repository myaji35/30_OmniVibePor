"""A/B 테스트 관리 API

Studio 워크플로우에서 동일한 스크립트에 대한 여러 변형을 생성하고,
각 변형의 성과를 비교하여 최적의 버전을 찾는 기능입니다.

주요 기능:
- A/B 테스트 변형 생성
- 변형 목록 조회
- 성과 기록 (조회수, 참여율)
- 성과 비교 및 최고 변형 분석
"""
from typing import List
import logging
import sqlite3
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.ab_test import (
    ABTestCreate,
    ABTestUpdate,
    ABTest,
    ABTestListResponse,
    ABTestTrackRequest,
    ABTestComparisonResponse
)

router = APIRouter(prefix="/ab-tests", tags=["A/B Tests"])
logger = logging.getLogger(__name__)

# SQLite DB 경로
DB_PATH = "omni_db.sqlite"


def get_db_connection():
    """SQLite 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== API Endpoints ====================

@router.post("/", response_model=ABTest, status_code=201)
async def create_ab_test(ab_test: ABTestCreate):
    """
    **새 A/B 테스트 변형 생성**

    동일한 콘텐츠(content_id)에 대해 여러 변형을 생성합니다.
    각 변형은 variant_name(A, B, C...)으로 구분됩니다.

    **요청 필드**:
    - **content_id**: 콘텐츠 ID (content_schedule)
    - **variant_name**: 변형 이름 (A, B, C...)
    - **script_version**: 스크립트 버전 (선택)
    - **audio_url**: 오디오 URL (선택)
    - **video_url**: 비디오 URL (선택)

    **반환값**: 생성된 A/B 테스트 정보
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 중복 체크 (content_id + variant_name)
        cursor.execute(
            "SELECT id FROM ab_tests WHERE content_id = ? AND variant_name = ?",
            (ab_test.content_id, ab_test.variant_name)
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Variant '{ab_test.variant_name}' already exists for content_id {ab_test.content_id}"
            )

        # 삽입
        cursor.execute(
            """
            INSERT INTO ab_tests (content_id, variant_name, script_version, audio_url, video_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ab_test.content_id,
                ab_test.variant_name,
                ab_test.script_version,
                ab_test.audio_url,
                ab_test.video_url
            )
        )
        conn.commit()
        test_id = cursor.lastrowid

        # 조회
        cursor.execute(
            """
            SELECT id, content_id, variant_name, script_version, audio_url, video_url,
                   views, engagement_rate, created_at
            FROM ab_tests
            WHERE id = ?
            """,
            (test_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return ABTest(
            id=row["id"],
            content_id=row["content_id"],
            variant_name=row["variant_name"],
            script_version=row["script_version"],
            audio_url=row["audio_url"],
            video_url=row["video_url"],
            views=row["views"],
            engagement_rate=row["engagement_rate"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B 테스트 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 테스트 생성 실패: {str(e)}")


@router.get("/{content_id}", response_model=ABTestListResponse)
async def get_ab_tests_by_content(content_id: int):
    """
    **특정 콘텐츠의 모든 A/B 테스트 변형 조회**

    content_id에 속한 모든 변형을 조회합니다.

    **경로 파라미터**:
    - **content_id**: 콘텐츠 ID

    **반환값**: A/B 테스트 목록
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, content_id, variant_name, script_version, audio_url, video_url,
                   views, engagement_rate, created_at
            FROM ab_tests
            WHERE content_id = ?
            ORDER BY created_at ASC
            """,
            (content_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        tests = [
            ABTest(
                id=row["id"],
                content_id=row["content_id"],
                variant_name=row["variant_name"],
                script_version=row["script_version"],
                audio_url=row["audio_url"],
                video_url=row["video_url"],
                views=row["views"],
                engagement_rate=row["engagement_rate"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
            for row in rows
        ]

        return ABTestListResponse(tests=tests, total=len(tests))

    except Exception as e:
        logger.error(f"A/B 테스트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 테스트 조회 실패: {str(e)}")


@router.post("/{test_id}/track", response_model=ABTest)
async def track_ab_test_performance(test_id: int, track_data: ABTestTrackRequest):
    """
    **A/B 테스트 성과 기록**

    특정 변형의 조회수와 참여율을 업데이트합니다.

    **경로 파라미터**:
    - **test_id**: A/B 테스트 ID

    **요청 필드**:
    - **views**: 조회수
    - **engagement_rate**: 참여율 (%)

    **반환값**: 업데이트된 A/B 테스트 정보
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 존재 확인
        cursor.execute("SELECT id FROM ab_tests WHERE id = ?", (test_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"A/B 테스트 ID {test_id}를 찾을 수 없습니다")

        # 업데이트
        cursor.execute(
            """
            UPDATE ab_tests
            SET views = ?, engagement_rate = ?
            WHERE id = ?
            """,
            (track_data.views, track_data.engagement_rate, test_id)
        )
        conn.commit()

        # 조회
        cursor.execute(
            """
            SELECT id, content_id, variant_name, script_version, audio_url, video_url,
                   views, engagement_rate, created_at
            FROM ab_tests
            WHERE id = ?
            """,
            (test_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return ABTest(
            id=row["id"],
            content_id=row["content_id"],
            variant_name=row["variant_name"],
            script_version=row["script_version"],
            audio_url=row["audio_url"],
            video_url=row["video_url"],
            views=row["views"],
            engagement_rate=row["engagement_rate"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"성과 기록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성과 기록 실패: {str(e)}")


@router.get("/{content_id}/comparison", response_model=ABTestComparisonResponse)
async def compare_ab_tests(content_id: int):
    """
    **A/B 테스트 성과 비교**

    특정 콘텐츠의 모든 변형을 비교하고, 최고 성과 변형을 찾습니다.
    참여율(engagement_rate) 기준으로 최고 변형을 선정합니다.

    **경로 파라미터**:
    - **content_id**: 콘텐츠 ID

    **반환값**: 비교 결과 및 최고 변형
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, content_id, variant_name, script_version, audio_url, video_url,
                   views, engagement_rate, created_at
            FROM ab_tests
            WHERE content_id = ?
            ORDER BY engagement_rate DESC, views DESC
            """,
            (content_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Content ID {content_id}에 대한 A/B 테스트가 없습니다"
            )

        tests = [
            ABTest(
                id=row["id"],
                content_id=row["content_id"],
                variant_name=row["variant_name"],
                script_version=row["script_version"],
                audio_url=row["audio_url"],
                video_url=row["video_url"],
                views=row["views"],
                engagement_rate=row["engagement_rate"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
            for row in rows
        ]

        # 최고 성과 변형 (이미 DESC 정렬되어 첫 번째가 최고)
        best = tests[0]

        return ABTestComparisonResponse(
            content_id=content_id,
            tests=tests,
            best_variant=best.variant_name,
            best_engagement=best.engagement_rate
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B 테스트 비교 실패: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 테스트 비교 실패: {str(e)}")


@router.put("/{test_id}", response_model=ABTest)
async def update_ab_test(test_id: int, update_data: ABTestUpdate):
    """
    **A/B 테스트 업데이트**

    변형의 스크립트, 오디오 URL, 비디오 URL을 업데이트합니다.

    **경로 파라미터**:
    - **test_id**: A/B 테스트 ID

    **요청 필드** (선택):
    - **script_version**: 스크립트 버전
    - **audio_url**: 오디오 URL
    - **video_url**: 비디오 URL

    **반환값**: 업데이트된 A/B 테스트 정보
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 존재 확인
        cursor.execute("SELECT id FROM ab_tests WHERE id = ?", (test_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"A/B 테스트 ID {test_id}를 찾을 수 없습니다")

        # 업데이트할 필드 수집
        updates = []
        params = []
        if update_data.script_version is not None:
            updates.append("script_version = ?")
            params.append(update_data.script_version)
        if update_data.audio_url is not None:
            updates.append("audio_url = ?")
            params.append(update_data.audio_url)
        if update_data.video_url is not None:
            updates.append("video_url = ?")
            params.append(update_data.video_url)

        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="업데이트할 필드가 없습니다")

        params.append(test_id)
        query = f"UPDATE ab_tests SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

        # 조회
        cursor.execute(
            """
            SELECT id, content_id, variant_name, script_version, audio_url, video_url,
                   views, engagement_rate, created_at
            FROM ab_tests
            WHERE id = ?
            """,
            (test_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return ABTest(
            id=row["id"],
            content_id=row["content_id"],
            variant_name=row["variant_name"],
            script_version=row["script_version"],
            audio_url=row["audio_url"],
            video_url=row["video_url"],
            views=row["views"],
            engagement_rate=row["engagement_rate"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B 테스트 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 테스트 업데이트 실패: {str(e)}")


@router.delete("/{test_id}", status_code=204)
async def delete_ab_test(test_id: int):
    """
    **A/B 테스트 삭제**

    특정 변형을 삭제합니다.

    **경로 파라미터**:
    - **test_id**: A/B 테스트 ID

    **반환값**: 없음 (204 No Content)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 존재 확인
        cursor.execute("SELECT id FROM ab_tests WHERE id = ?", (test_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"A/B 테스트 ID {test_id}를 찾을 수 없습니다")

        # 삭제
        cursor.execute("DELETE FROM ab_tests WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()

        return JSONResponse(status_code=204, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B 테스트 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"A/B 테스트 삭제 실패: {str(e)}")
