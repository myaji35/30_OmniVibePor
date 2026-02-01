#!/usr/bin/env python3
"""
Neo4j 데이터베이스 초기화 스크립트

이 스크립트는 다음 작업을 수행합니다:
1. Neo4j 연결 확인
2. 스키마 생성 (Constraints & Indexes)
3. 샘플 데이터 생성 (옵션)
4. 데이터베이스 초기화 (옵션, 위험)

실행 방법:
    python scripts/init_neo4j.py --create-schema
    python scripts/init_neo4j.py --create-schema --create-samples
    python scripts/init_neo4j.py --reset  # 주의: 모든 데이터 삭제!
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import (
    UserModel,
    PersonaModel,
    ProjectModel,
    ScriptModel,
    AudioModel,
    VideoModel,
    MetricsModel,
    Neo4jCRUDManager,
    SubscriptionTier,
    Gender,
    Tone,
    ContentStyle,
    Platform,
    ProjectStatus,
)
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_schema(client):
    """Neo4j 스키마 생성 (Constraints & Indexes)"""
    logger.info("Creating Neo4j schema...")

    schema_queries = [
        # User
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)",

        # Persona
        "CREATE CONSTRAINT persona_id_unique IF NOT EXISTS FOR (p:Persona) REQUIRE p.persona_id IS UNIQUE",

        # Project
        "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
        "CREATE INDEX project_created IF NOT EXISTS FOR (p:Project) ON (p.created_at)",
        "CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status)",

        # Script
        "CREATE CONSTRAINT script_id_unique IF NOT EXISTS FOR (s:Script) REQUIRE s.script_id IS UNIQUE",

        # Audio
        "CREATE CONSTRAINT audio_id_unique IF NOT EXISTS FOR (a:Audio) REQUIRE a.audio_id IS UNIQUE",

        # Video
        "CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:Video) REQUIRE v.video_id IS UNIQUE",

        # Thumbnail
        "CREATE CONSTRAINT thumbnail_id_unique IF NOT EXISTS FOR (t:Thumbnail) REQUIRE t.thumbnail_id IS UNIQUE",

        # Metrics
        "CREATE INDEX metrics_performance IF NOT EXISTS FOR (m:Metrics) ON (m.performance_score)",
        "CREATE INDEX metrics_measured IF NOT EXISTS FOR (m:Metrics) ON (m.measured_at)",

        # CustomVoice
        "CREATE CONSTRAINT custom_voice_id_unique IF NOT EXISTS FOR (cv:CustomVoice) REQUIRE cv.voice_id IS UNIQUE",

        # Content (레거시 호환)
        "CREATE INDEX content_id IF NOT EXISTS FOR (c:Content) ON (c.content_id)",
    ]

    for query in schema_queries:
        try:
            client.query(query)
            logger.info(f"✓ {query.split('IF NOT EXISTS')[0].strip()}")
        except Exception as e:
            logger.error(f"✗ Failed: {query[:50]}... - {e}")

    logger.info("Schema creation completed!")


def create_sample_data(client):
    """샘플 데이터 생성"""
    logger.info("Creating sample data...")

    crud = Neo4jCRUDManager(client)

    # 1. 샘플 사용자 생성
    user = UserModel(
        email="demo@omnivibepro.com",
        name="데모 사용자",
        subscription_tier=SubscriptionTier.PRO,
    )
    created_user = crud.create_user(user)
    user_id = created_user["user_id"]
    logger.info(f"✓ Created user: {user_id}")

    # 2. 페르소나 생성
    persona = PersonaModel(
        gender=Gender.FEMALE,
        tone=Tone.PROFESSIONAL,
        style=ContentStyle.EDUCATION,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # ElevenLabs Rachel
        character_reference_url="https://example.com/character_ref.png",
    )
    created_persona = crud.create_persona(user_id, persona)
    persona_id = created_persona["persona_id"]
    logger.info(f"✓ Created persona: {persona_id}")

    # 3. 프로젝트 생성
    project = ProjectModel(
        title="AI 트렌드 2026",
        topic="인공지능",
        platform=Platform.YOUTUBE,
        status=ProjectStatus.SCRIPT_READY,
        publish_scheduled_at=datetime.utcnow() + timedelta(days=7),
    )
    created_project = crud.create_project(user_id, project, persona_id)
    project_id = created_project["project_id"]
    logger.info(f"✓ Created project: {project_id}")

    # 4. 스크립트 생성 (3개 버전)
    scripts = [
        ScriptModel(
            content="안녕하세요! 오늘은 2026년 AI 트렌드에 대해 알아보겠습니다. "
                    "첫 번째는 멀티모달 AI의 확산입니다...",
            platform=Platform.YOUTUBE,
            word_count=500,
            estimated_duration=180,
            version=1,
        ),
        ScriptModel(
            content="2026년 AI 업계의 가장 뜨거운 키워드는 무엇일까요? "
                    "바로 AGI와 개인화입니다...",
            platform=Platform.YOUTUBE,
            word_count=480,
            estimated_duration=175,
            version=2,
        ),
        ScriptModel(
            content="AI 기술의 발전이 우리 삶을 어떻게 바꿀까요? "
                    "2026년 핵심 트렌드를 함께 살펴봅시다...",
            platform=Platform.YOUTUBE,
            word_count=520,
            estimated_duration=190,
            version=3,
        ),
    ]

    script_ids = []
    for idx, script in enumerate(scripts):
        created_script = crud.create_script(project_id, script, selected=(idx == 0))
        script_ids.append(created_script["script_id"])
        logger.info(f"✓ Created script v{script.version}: {created_script['script_id']}")

    # 5. 선택된 스크립트에 오디오 생성
    selected_script_id = script_ids[0]
    audio = AudioModel(
        file_path="s3://omnivibe-demo/audio_001.mp3",
        voice_id="21m00Tcm4TlvDq8ikWAM",
        duration=185.5,
        stt_accuracy=0.98,
        retry_count=1,
    )
    created_audio = crud.create_audio(selected_script_id, audio)
    audio_id = created_audio["audio_id"]
    logger.info(f"✓ Created audio: {audio_id}")

    # 6. 비디오 생성
    video = VideoModel(
        file_path="s3://omnivibe-demo/video_final.mp4",
        duration=190.0,
        resolution="1920x1080",
        format="mp4",
        veo_prompt="Professional Korean female educator explaining AI trends in modern office setting",
        lipsync_enabled=True,
    )
    created_video = crud.create_video(project_id, audio_id, video)
    video_id = created_video["video_id"]
    logger.info(f"✓ Created video: {video_id}")

    # 7. 성과 메트릭 생성 (시간별 3개)
    metrics_data = [
        {"days_ago": 0, "views": 1500, "likes": 85, "comments": 12, "shares": 5},
        {"days_ago": 1, "views": 5200, "likes": 320, "comments": 45, "shares": 18},
        {"days_ago": 2, "views": 15000, "likes": 850, "comments": 120, "shares": 45},
    ]

    for data in metrics_data:
        metrics = MetricsModel(
            views=data["views"],
            likes=data["likes"],
            comments=data["comments"],
            shares=data["shares"],
            watch_time=data["views"] * 170,  # 평균 시청 시간
            engagement_rate=(data["likes"] + data["comments"]) / max(data["views"], 1),
            ctr=0.089,
            performance_score=min(100, (data["likes"] / max(data["views"], 1)) * 1000 + 50),
            measured_at=datetime.utcnow() - timedelta(days=data["days_ago"]),
        )
        created_metrics = crud.create_metrics(video_id, metrics)
        logger.info(f"✓ Created metrics (day -{data['days_ago']}): {created_metrics['metrics_id']}")

    # 8. 추가 프로젝트 생성 (Instagram)
    project2 = ProjectModel(
        title="AI 툴 리뷰: ChatGPT vs Claude",
        topic="AI 도구 비교",
        platform=Platform.INSTAGRAM,
        status=ProjectStatus.PUBLISHED,
        publish_scheduled_at=datetime.utcnow() - timedelta(days=3),
    )
    created_project2 = crud.create_project(user_id, project2, persona_id)
    logger.info(f"✓ Created second project: {created_project2['project_id']}")

    logger.info("\n" + "="*50)
    logger.info("Sample data creation completed!")
    logger.info("="*50)
    logger.info(f"User ID: {user_id}")
    logger.info(f"Persona ID: {persona_id}")
    logger.info(f"Project ID: {project_id}")
    logger.info(f"Video ID: {video_id}")
    logger.info("="*50)


def reset_database(client):
    """데이터베이스 초기화 (모든 노드 및 관계 삭제) - 위험!"""
    logger.warning("⚠️  WARNING: This will delete ALL data in the database!")
    confirmation = input("Type 'DELETE ALL DATA' to confirm: ")

    if confirmation != "DELETE ALL DATA":
        logger.info("Reset cancelled.")
        return

    logger.info("Resetting database...")

    # 모든 노드 및 관계 삭제
    query = "MATCH (n) DETACH DELETE n"
    client.query(query)

    logger.info("✓ All nodes and relationships deleted")

    # 스키마 재생성
    create_schema(client)

    logger.info("Database reset completed!")


def verify_connection(client):
    """Neo4j 연결 확인"""
    logger.info("Verifying Neo4j connection...")

    try:
        result = client.query("RETURN 1 as test")
        if result and result[0]["test"] == 1:
            logger.info("✓ Neo4j connection successful!")
            return True
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        return False

    return False


def show_statistics(client):
    """데이터베이스 통계 표시"""
    logger.info("\nDatabase Statistics:")
    logger.info("="*50)

    stats_query = """
    MATCH (n)
    RETURN labels(n)[0] as label, count(n) as count
    ORDER BY count DESC
    """

    results = client.query(stats_query)

    for row in results:
        logger.info(f"{row['label']:20s}: {row['count']:5d}")

    logger.info("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="Neo4j 데이터베이스 초기화 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/init_neo4j.py --create-schema
  python scripts/init_neo4j.py --create-schema --create-samples
  python scripts/init_neo4j.py --reset
  python scripts/init_neo4j.py --stats
        """
    )

    parser.add_argument(
        "--create-schema",
        action="store_true",
        help="스키마 생성 (Constraints & Indexes)",
    )

    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="샘플 데이터 생성",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="데이터베이스 초기화 (모든 데이터 삭제)",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="데이터베이스 통계 표시",
    )

    args = parser.parse_args()

    # 인자가 없으면 도움말 표시
    if not any([args.create_schema, args.create_samples, args.reset, args.stats]):
        parser.print_help()
        sys.exit(1)

    # Neo4j 클라이언트 초기화
    try:
        client = get_neo4j_client()
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j client: {e}")
        logger.error("Please check your .env file and Neo4j connection settings.")
        sys.exit(1)

    # 연결 확인
    if not verify_connection(client):
        sys.exit(1)

    # 작업 수행
    try:
        if args.reset:
            reset_database(client)

        if args.create_schema:
            create_schema(client)

        if args.create_samples:
            create_sample_data(client)

        if args.stats:
            show_statistics(client)

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        client.close()
        logger.info("Neo4j connection closed.")


if __name__ == "__main__":
    main()
