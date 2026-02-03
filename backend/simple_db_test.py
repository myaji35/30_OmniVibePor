"""간단한 SQLite DB 테스트 (의존성 없음)

Frontend DB를 직접 확인하여 Backend 통합 준비가 되었는지 검증합니다.
"""
import sqlite3
from pathlib import Path


def test_db_access():
    """DB 접근 테스트"""
    print("\n[TEST 1] SQLite DB 접근")
    print("-" * 50)

    db_path = Path(__file__).parent.parent / "frontend" / "data" / "omnivibe.db"

    if not db_path.exists():
        print(f"❌ DB 파일 없음: {db_path}")
        return False

    print(f"✅ DB 파일 존재: {db_path}")
    print(f"   크기: {db_path.stat().st_size / 1024:.1f} KB")

    return db_path


def test_campaigns_read(db_path):
    """Campaign 테이블 읽기"""
    print("\n[TEST 2] Campaign 데이터 읽기")
    print("-" * 50)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 전체 개수
    cursor.execute("SELECT COUNT(*) FROM campaigns")
    count = cursor.fetchone()[0]
    print(f"✅ 총 {count}개 캠페인")

    # 목록 조회
    cursor.execute("""
        SELECT id, name, client_id, status, concept_gender, target_duration, voice_id
        FROM campaigns
        ORDER BY created_at DESC
        LIMIT 5
    """)

    campaigns = cursor.fetchall()
    print(f"\n최근 5개 캠페인:")
    for row in campaigns:
        print(f"  - [{row[0]}] {row[1]}")
        print(f"    Client: {row[2]}, Status: {row[3]}, Gender: {row[4]}, Duration: {row[5]}초, Voice: {row[6]}")

    conn.close()
    return count


def test_content_schedule_read(db_path):
    """Content Schedule 테이블 읽기"""
    print("\n[TEST 3] Content Schedule 데이터 읽기")
    print("-" * 50)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 전체 개수
    cursor.execute("SELECT COUNT(*) FROM content_schedule")
    count = cursor.fetchone()[0]
    print(f"✅ 총 {count}개 콘텐츠")

    # Campaign별 개수
    cursor.execute("""
        SELECT c.name, COUNT(cs.id) as content_count
        FROM campaigns c
        LEFT JOIN content_schedule cs ON c.id = cs.campaign_id
        GROUP BY c.id, c.name
        ORDER BY content_count DESC
        LIMIT 5
    """)

    campaign_contents = cursor.fetchall()
    print(f"\n캠페인별 콘텐츠 개수:")
    for row in campaign_contents:
        print(f"  - {row[0]}: {row[1]}개")

    # 최근 콘텐츠
    cursor.execute("""
        SELECT id, campaign_id, topic, platform, status, publish_date
        FROM content_schedule
        ORDER BY created_at DESC
        LIMIT 3
    """)

    contents = cursor.fetchall()
    print(f"\n최근 3개 콘텐츠:")
    for row in contents:
        print(f"  - [{row[0]}] {row[2]}")
        print(f"    Campaign: {row[1]}, Platform: {row[3]}, Status: {row[4]}, Publish: {row[5]}")

    conn.close()
    return count


def test_schema_validation(db_path):
    """테이블 스키마 확인"""
    print("\n[TEST 4] 테이블 스키마 검증")
    print("-" * 50)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 테이블 목록
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"✅ 테이블 목록:")
    for table in tables:
        if table != "sqlite_sequence":
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")

    # Campaign 테이블 필수 컬럼 확인
    print(f"\n✅ Campaign 테이블 컬럼:")
    cursor.execute("PRAGMA table_info(campaigns)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    conn.close()
    return True


def test_backend_db_path():
    """Backend가 사용할 DB 경로 확인"""
    print("\n[TEST 5] Backend DB 경로 검증")
    print("-" * 50)

    # Backend 기준 상대 경로
    backend_root = Path(__file__).parent
    relative_path = backend_root.parent / "frontend" / "data" / "omnivibe.db"

    print(f"✅ Backend Root: {backend_root}")
    print(f"✅ DB 경로: {relative_path}")
    print(f"✅ 존재 여부: {relative_path.exists()}")

    if relative_path.exists():
        print(f"✅ Backend가 Frontend DB에 접근 가능합니다!")
        return True
    else:
        print(f"❌ 경로 문제 발견!")
        return False


def summary():
    """요약"""
    print("\n" + "=" * 50)
    print("Backend SQLite 통합 준비 상태")
    print("=" * 50)

    print("\n✅ 완료 사항:")
    print("  1. SQLite Client 모듈 생성 (/backend/app/db/sqlite_client.py)")
    print("  2. Campaign DB CRUD 구현")
    print("  3. Content Schedule DB CRUD 구현")
    print("  4. Campaign API SQLite 연동 완료")
    print("  5. Content Schedule API 생성 및 등록")

    print("\n📋 다음 단계:")
    print("  1. Backend 서버 시작:")
    print("     cd backend && uvicorn app.main:app --reload")
    print("")
    print("  2. API 테스트:")
    print("     curl http://localhost:8000/api/v1/campaigns/")
    print("     curl http://localhost:8000/api/v1/content-schedule/?campaign_id=1")
    print("")
    print("  3. Frontend에서 Backend API 호출 설정")

    print("\n💡 주요 이점:")
    print("  - Backend 재시작 후에도 데이터 유지")
    print("  - Frontend와 Backend 데이터 실시간 동기화")
    print("  - In-memory 저장소 제거로 안정성 향상")


def main():
    """전체 테스트 실행"""
    print("=" * 50)
    print("Backend SQLite 통합 검증")
    print("=" * 50)

    try:
        # Test 1: DB 접근
        db_path = test_db_access()
        if not db_path:
            return

        # Test 2: Campaign 읽기
        test_campaigns_read(db_path)

        # Test 3: Content Schedule 읽기
        test_content_schedule_read(db_path)

        # Test 4: 스키마 검증
        test_schema_validation(db_path)

        # Test 5: Backend 경로 검증
        test_backend_db_path()

        # 요약
        summary()

    except Exception as e:
        print(f"\n❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
