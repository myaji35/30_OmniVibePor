"""비디오 메타데이터 API 테스트 스크립트

사용법:
    python3 test_video_metadata.py [프로젝트_ID]

예시:
    python3 test_video_metadata.py proj_abc123def456
"""
import sys
import asyncio
from app.api.v1.editor import get_project_video_metadata
from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import (
    Neo4jCRUDManager,
    UserModel,
    ProjectModel,
    Platform,
    VideoModel
)


async def create_test_data():
    """테스트용 데이터 생성"""
    print("Creating test data...")

    client = get_neo4j_client()
    crud = Neo4jCRUDManager(client)

    # 테스트 사용자 생성
    user = UserModel(
        email="test@omnivibepro.com",
        name="Test User"
    )

    try:
        created_user = crud.create_user(user)
        print(f"✅ User created: {created_user['user_id']}")
    except Exception as e:
        print(f"⚠️  User creation failed (may already exist): {e}")
        created_user = {"user_id": user.user_id}

    # 테스트 프로젝트 생성
    project = ProjectModel(
        title="Test Video Project",
        topic="Testing video metadata extraction",
        platform=Platform.YOUTUBE
    )

    try:
        created_project = crud.create_project(created_user["user_id"], project)
        print(f"✅ Project created: {created_project['project_id']}")
    except Exception as e:
        print(f"⚠️  Project creation failed (may already exist): {e}")
        created_project = {"project_id": project.project_id}

    # 테스트 비디오 생성 (더미 경로)
    video = VideoModel(
        file_path="/tmp/test_video.mp4",
        duration=60.0,
        resolution="1920x1080",
        format="mp4",
        veo_prompt="Test video"
    )

    try:
        created_video = crud.create_video(
            created_project["project_id"],
            "audio_dummy123",  # 더미 오디오 ID
            video
        )
        print(f"✅ Video created: {created_video['video_id']}")
    except Exception as e:
        print(f"⚠️  Video creation failed: {e}")
        created_video = {"video_id": video.video_id}

    return created_project["project_id"]


async def test_api(project_id: str):
    """API 엔드포인트 테스트"""
    print(f"\n{'='*60}")
    print(f"Testing API with project_id: {project_id}")
    print(f"{'='*60}\n")

    try:
        result = await get_project_video_metadata(project_id)

        print("✅ API Response:")
        print(f"  Project ID: {result.project_id}")
        print(f"  Video ID: {result.video_id}")
        print(f"  Video Path: {result.video_path}")
        print(f"  Duration: {result.duration}s")
        print(f"  Resolution: {result.resolution.width}x{result.resolution.height}")
        print(f"  Frame Rate: {result.frame_rate} FPS")
        print(f"  Codec: {result.codec}")
        print(f"  Audio Codec: {result.audio_codec}")
        print(f"  Bitrate: {result.bitrate} bps")
        print(f"  File Size: {result.file_size} bytes")
        print(f"  Format: {result.format_name}")
        print(f"  Sections: {len(result.sections)} sections")

        if result.sections:
            print("\n  Section Details:")
            for section in result.sections:
                print(f"    - {section.type}: {section.start_time}s ~ {section.end_time}s ({section.duration}s)")

        return True

    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 함수"""
    print("="*60)
    print("OmniVibe Pro - Video Metadata API Test")
    print("="*60)

    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        print(f"Using provided project_id: {project_id}\n")
    else:
        print("No project_id provided. Creating test data...\n")
        project_id = await create_test_data()

    success = await test_api(project_id)

    print("\n" + "="*60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check errors above.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
