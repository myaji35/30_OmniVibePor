"""SQLite 연결 테스트 (서버 없이 직접 DB 테스트)

Backend SQLite 클라이언트가 Frontend DB를 정상적으로 읽을 수 있는지 확인합니다.
"""
import asyncio
import sys
from pathlib import Path

# Backend app 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.db.sqlite_client import (
    get_sqlite_client,
    get_campaign_db,
    get_content_schedule_db
)


async def test_db_connection():
    """DB 연결 테스트"""
    print("\n[TEST 1] SQLite DB 연결 테스트")
    print("-" * 50)

    client = get_sqlite_client()
    print(f"✅ DB 경로: {client.db_path}")

    if not client.db_path.exists():
        print(f"❌ DB 파일이 존재하지 않습니다!")
        return False

    print(f"✅ DB 파일 존재 확인")
    return True


async def test_campaign_read():
    """Campaign 읽기 테스트"""
    print("\n[TEST 2] Campaign 데이터 읽기")
    print("-" * 50)

    campaign_db = get_campaign_db()

    # 전체 개수
    count = await campaign_db.count()
    print(f"✅ 총 {count}개 캠페인 발견")

    # 목록 조회
    campaigns = await campaign_db.get_all(limit=5)
    print(f"\n첫 5개 캠페인:")
    for campaign in campaigns:
        print(f"  - [{campaign['id']}] {campaign['name']} ({campaign['status']})")

    # 특정 캠페인 상세 조회
    if campaigns:
        first_id = campaigns[0]['id']
        detail = await campaign_db.get_by_id(first_id)
        print(f"\n캠페인 ID {first_id} 상세:")
        print(f"  - Client ID: {detail['client_id']}")
        print(f"  - Concept Gender: {detail.get('concept_gender', 'N/A')}")
        print(f"  - Target Duration: {detail.get('target_duration', 'N/A')}초")
        print(f"  - Voice ID: {detail.get('voice_id', 'N/A')}")

    return count > 0


async def test_campaign_create():
    """Campaign 생성 테스트"""
    print("\n[TEST 3] Campaign 생성")
    print("-" * 50)

    from datetime import datetime

    campaign_db = get_campaign_db()

    campaign_data = {
        "name": f"Backend 테스트 캠페인 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "SQLite 통합 테스트용 캠페인",
        "client_id": 1,
        "status": "active",
        "concept_gender": "female",
        "concept_tone": "friendly",
        "concept_style": "soft",
        "target_duration": 60,
        "voice_id": "test_voice_backend",
        "voice_name": "백엔드 테스트 음성"
    }

    campaign_id = await campaign_db.create(campaign_data)
    print(f"✅ Campaign 생성 성공: ID = {campaign_id}")

    # 생성 확인
    created = await campaign_db.get_by_id(campaign_id)
    print(f"  - Name: {created['name']}")
    print(f"  - Created At: {created['created_at']}")

    return campaign_id


async def test_campaign_update(campaign_id: int):
    """Campaign 업데이트 테스트"""
    print(f"\n[TEST 4] Campaign 업데이트 (ID: {campaign_id})")
    print("-" * 50)

    campaign_db = get_campaign_db()

    updates = {
        "target_duration": 90,
        "status": "paused"
    }

    success = await campaign_db.update(campaign_id, updates)
    print(f"✅ Campaign 업데이트 {'성공' if success else '실패'}")

    # 업데이트 확인
    updated = await campaign_db.get_by_id(campaign_id)
    print(f"  - Target Duration: {updated['target_duration']}초")
    print(f"  - Status: {updated['status']}")
    print(f"  - Updated At: {updated['updated_at']}")

    return success


async def test_content_schedule_read():
    """Content Schedule 읽기 테스트"""
    print("\n[TEST 5] Content Schedule 데이터 읽기")
    print("-" * 50)

    content_db = get_content_schedule_db()

    # Campaign ID 1의 콘텐츠 조회
    contents = await content_db.get_by_campaign(1)
    print(f"✅ Campaign 1에 {len(contents)}개 콘텐츠 발견")

    if contents:
        print(f"\n첫 3개 콘텐츠:")
        for content in contents[:3]:
            print(f"  - [{content['id']}] {content['topic']}")
            print(f"    Platform: {content['platform']}, Status: {content['status']}")

    return len(contents)


async def test_content_schedule_create():
    """Content Schedule 생성 테스트"""
    print("\n[TEST 6] Content Schedule 생성")
    print("-" * 50)

    from datetime import datetime

    content_db = get_content_schedule_db()

    content_data = {
        "campaign_id": 1,
        "topic": "Backend 테스트 콘텐츠",
        "subtitle": f"SQLite 통합 테스트 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "platform": "Youtube",
        "publish_date": "2026-03-15",
        "status": "draft",
        "target_audience": "개발자",
        "keywords": "SQLite, Backend, 통합테스트"
    }

    content_id = await content_db.create(content_data)
    print(f"✅ Content Schedule 생성 성공: ID = {content_id}")

    # 생성 확인
    created = await content_db.get_by_id(content_id)
    print(f"  - Topic: {created['topic']}")
    print(f"  - Platform: {created['platform']}")
    print(f"  - Created At: {created['created_at']}")

    return content_id


async def test_data_persistence():
    """데이터 영속성 확인"""
    print("\n[TEST 7] 데이터 영속성 확인")
    print("-" * 50)

    import sqlite3

    db_path = Path(__file__).parent.parent / "frontend" / "data" / "omnivibe.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Campaign 총 개수
    cursor.execute("SELECT COUNT(*) FROM campaigns")
    campaign_count = cursor.fetchone()[0]

    # Content Schedule 총 개수
    cursor.execute("SELECT COUNT(*) FROM content_schedule")
    content_count = cursor.fetchone()[0]

    # 최근 생성된 Campaign
    cursor.execute("""
        SELECT id, name, created_at
        FROM campaigns
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest_campaign = cursor.fetchone()

    # 최근 생성된 Content
    cursor.execute("""
        SELECT id, topic, created_at
        FROM content_schedule
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest_content = cursor.fetchone()

    conn.close()

    print(f"✅ DB 영속성 확인 완료:")
    print(f"  - Campaigns: {campaign_count}개")
    print(f"  - Content Schedules: {content_count}개")

    if latest_campaign:
        print(f"\n최근 Campaign:")
        print(f"  - ID: {latest_campaign[0]}")
        print(f"  - Name: {latest_campaign[1]}")
        print(f"  - Created: {latest_campaign[2]}")

    if latest_content:
        print(f"\n최근 Content:")
        print(f"  - ID: {latest_content[0]}")
        print(f"  - Topic: {latest_content[1]}")
        print(f"  - Created: {latest_content[2]}")

    return True


async def main():
    """전체 테스트 실행"""
    print("=" * 50)
    print("Backend SQLite 통합 테스트 (Direct DB Access)")
    print("=" * 50)

    try:
        # Test 1: DB 연결
        if not await test_db_connection():
            return

        # Test 2: Campaign 읽기
        if not await test_campaign_read():
            print("❌ Campaign 데이터가 없습니다.")
            return

        # Test 3: Campaign 생성
        new_campaign_id = await test_campaign_create()

        # Test 4: Campaign 업데이트
        if new_campaign_id:
            await test_campaign_update(new_campaign_id)

        # Test 5: Content Schedule 읽기
        await test_content_schedule_read()

        # Test 6: Content Schedule 생성
        await test_content_schedule_create()

        # Test 7: 데이터 영속성 확인
        await test_data_persistence()

        print("\n" + "=" * 50)
        print("✅ 모든 테스트 완료!")
        print("=" * 50)
        print("\n✨ Backend와 Frontend가 동일한 SQLite DB를 공유합니다.")
        print("   Backend 재시작 후에도 데이터가 유지됩니다.")

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
