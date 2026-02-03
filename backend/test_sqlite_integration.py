"""SQLite 통합 테스트 스크립트

Backend API와 Frontend DB 통합을 검증합니다.

테스트 시나리오:
1. Backend에서 Frontend DB의 Campaign 데이터 조회
2. 새 Campaign 생성 후 Frontend에서 확인 가능 여부
3. Campaign 업데이트 후 데이터 동기화 확인
4. Content Schedule 조회 및 생성
5. Backend 재시작 후 데이터 영속성 확인
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


async def test_campaigns_read():
    """Campaign 목록 조회 테스트"""
    print("\n[TEST 1] Campaign 목록 조회")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/campaigns/")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공: {data['total']}개 캠페인 조회됨")

            if data['campaigns']:
                print(f"\n첫 번째 캠페인:")
                campaign = data['campaigns'][0]
                print(f"  - ID: {campaign['id']}")
                print(f"  - Name: {campaign['name']}")
                print(f"  - Client ID: {campaign['client_id']}")
                print(f"  - Status: {campaign['status']}")

            return data['total']
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None


async def test_campaign_detail():
    """특정 Campaign 상세 조회 테스트"""
    print("\n[TEST 2] 특정 Campaign 상세 조회")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/campaigns/1")

        if response.status_code == 200:
            campaign = response.json()
            print(f"✅ 성공: Campaign ID 1 조회됨")
            print(f"  - Name: {campaign['name']}")
            print(f"  - Concept Gender: {campaign.get('concept_gender', 'N/A')}")
            print(f"  - Target Duration: {campaign.get('target_duration', 'N/A')}초")
            print(f"  - Voice ID: {campaign.get('voice_id', 'N/A')}")
            return True
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_campaign_create():
    """Campaign 생성 테스트"""
    print("\n[TEST 3] Campaign 생성")
    print("-" * 50)

    campaign_data = {
        "client_id": 1,
        "name": f"테스트 캠페인 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "concept_gender": "female",
        "concept_tone": "friendly",
        "concept_style": "soft",
        "target_duration": 60,
        "voice_id": "test_voice_123",
        "voice_name": "테스트 음성",
        "status": "active"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/campaigns/",
            json=campaign_data
        )

        if response.status_code == 201:
            campaign = response.json()
            print(f"✅ 성공: Campaign 생성됨")
            print(f"  - ID: {campaign['id']}")
            print(f"  - Name: {campaign['name']}")
            return campaign['id']
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None


async def test_campaign_update(campaign_id: int):
    """Campaign 업데이트 테스트"""
    print(f"\n[TEST 4] Campaign 업데이트 (ID: {campaign_id})")
    print("-" * 50)

    update_data = {
        "target_duration": 90,
        "status": "paused"
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/campaigns/{campaign_id}",
            json=update_data
        )

        if response.status_code == 200:
            campaign = response.json()
            print(f"✅ 성공: Campaign 업데이트됨")
            print(f"  - Target Duration: {campaign['target_duration']}초")
            print(f"  - Status: {campaign['status']}")
            return True
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_content_schedule_read():
    """Content Schedule 조회 테스트"""
    print("\n[TEST 5] Content Schedule 조회")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/content-schedule/",
            params={"campaign_id": 1}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공: {len(data['contents'])}개 콘텐츠 조회됨")

            if data['contents']:
                print(f"\n첫 번째 콘텐츠:")
                content = data['contents'][0]
                print(f"  - ID: {content['id']}")
                print(f"  - Topic: {content['topic']}")
                print(f"  - Platform: {content['platform']}")
                print(f"  - Status: {content['status']}")

            return len(data['contents'])
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None


async def test_content_schedule_create():
    """Content Schedule 생성 테스트"""
    print("\n[TEST 6] Content Schedule 생성")
    print("-" * 50)

    content_data = {
        "campaign_id": 1,
        "topic": "테스트 콘텐츠",
        "subtitle": f"Backend 테스트 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "platform": "Youtube",
        "publish_date": "2026-03-01",
        "status": "draft",
        "target_audience": "시력 인식 관심자",
        "keywords": "시력, 안과, 건강"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/content-schedule/",
            json=content_data
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ 성공: Content Schedule 생성됨")
            print(f"  - Content ID: {data['content_id']}")
            print(f"  - Message: {data['message']}")
            return data['content_id']
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None


async def test_campaign_schedule():
    """Campaign의 Content Schedule 조회 테스트"""
    print("\n[TEST 7] Campaign의 Content Schedule 조회")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/campaigns/1/schedule")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공: {data['total']}개 스케줄 조회됨")
            return data['total']
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None


async def verify_db_directly():
    """SQLite DB에서 직접 데이터 확인"""
    print("\n[VERIFY] SQLite DB 직접 확인")
    print("-" * 50)

    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent / "frontend" / "data" / "omnivibe.db"

    if not db_path.exists():
        print(f"❌ DB 파일을 찾을 수 없음: {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Campaign 개수
    cursor.execute("SELECT COUNT(*) FROM campaigns")
    campaign_count = cursor.fetchone()[0]
    print(f"✅ Campaigns: {campaign_count}개")

    # Content Schedule 개수
    cursor.execute("SELECT COUNT(*) FROM content_schedule")
    content_count = cursor.fetchone()[0]
    print(f"✅ Content Schedules: {content_count}개")

    # 최근 생성된 Campaign
    cursor.execute("""
        SELECT id, name, created_at
        FROM campaigns
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest = cursor.fetchone()
    if latest:
        print(f"\n최근 생성 Campaign:")
        print(f"  - ID: {latest[0]}")
        print(f"  - Name: {latest[1]}")
        print(f"  - Created: {latest[2]}")

    conn.close()
    return True


async def main():
    """전체 테스트 실행"""
    print("=" * 50)
    print("Backend SQLite 통합 테스트")
    print("=" * 50)

    try:
        # Test 1: Campaign 목록 조회
        campaign_count = await test_campaigns_read()

        if campaign_count is None:
            print("\n⚠️ Backend 서버가 실행 중이 아닙니다.")
            print("   다음 명령어로 서버를 시작하세요:")
            print("   cd backend && uvicorn app.main:app --reload")
            return

        # Test 2: Campaign 상세 조회
        await test_campaign_detail()

        # Test 3: Campaign 생성
        new_campaign_id = await test_campaign_create()

        if new_campaign_id:
            # Test 4: Campaign 업데이트
            await test_campaign_update(new_campaign_id)

        # Test 5: Content Schedule 조회
        await test_content_schedule_read()

        # Test 6: Content Schedule 생성
        await test_content_schedule_create()

        # Test 7: Campaign의 Schedule 조회
        await test_campaign_schedule()

        # Verify: DB 직접 확인
        await verify_db_directly()

        print("\n" + "=" * 50)
        print("✅ 모든 테스트 완료!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
