"""Cloudinary 서비스 테스트

사용법:
    python test_cloudinary_service.py
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.cloudinary_service import get_cloudinary_service


async def test_cloudinary_service():
    """Cloudinary 서비스 테스트"""
    print("=" * 80)
    print("Cloudinary 미디어 최적화 서비스 테스트")
    print("=" * 80)

    service = get_cloudinary_service()

    # 1. 플랫폼별 변환 설정 확인
    print("\n1. 플랫폼별 영상 변환 설정:")
    print("-" * 80)
    from app.services.cloudinary_service import PLATFORM_TRANSFORMATIONS

    for platform, config in PLATFORM_TRANSFORMATIONS.items():
        print(f"\n{platform}:")
        print(f"  해상도: {config['width']}x{config['height']}")
        print(f"  비율: {config['aspect_ratio']}")
        print(f"  품질: {config['quality']}")

    # 2. URL 생성 테스트 (실제 업로드 없이)
    print("\n\n2. 최적화된 URL 생성 테스트:")
    print("-" * 80)

    # 샘플 public_id로 URL 생성 테스트
    sample_id = "sample_video_123"

    # 이미지 최적화 URL
    image_url = service.get_optimized_url(
        public_id=sample_id,
        resource_type="image"
    )
    print(f"\n이미지 최적화 URL:")
    print(f"  {image_url}")

    # 영상 최적화 URL
    video_url = service.get_optimized_url(
        public_id=sample_id,
        resource_type="video",
        transformations=[
            {"width": 1920, "height": 1080, "crop": "fill"},
            {"quality": "auto:best"}
        ]
    )
    print(f"\n영상 최적화 URL:")
    print(f"  {video_url}")

    # 3. 플랫폼별 변환 URL 생성
    print("\n\n3. 플랫폼별 변환 URL (YouTube, Instagram, TikTok):")
    print("-" * 80)

    platforms = ["youtube", "instagram_feed", "instagram_story", "tiktok"]
    for platform in platforms:
        config = PLATFORM_TRANSFORMATIONS[platform]

        import cloudinary.utils
        url, _ = cloudinary.utils.cloudinary_url(
            sample_id,
            resource_type="video",
            transformation=[
                {
                    "width": config["width"],
                    "height": config["height"],
                    "crop": config["crop"]
                },
                {
                    "quality": config["quality"]
                }
            ],
            secure=True
        )

        print(f"\n{platform}:")
        print(f"  해상도: {config['width']}x{config['height']}")
        print(f"  URL: {url}")

    # 4. 썸네일 생성 URL
    print("\n\n4. 썸네일 생성 URL:")
    print("-" * 80)

    import cloudinary.utils
    thumbnail_url, _ = cloudinary.utils.cloudinary_url(
        sample_id,
        resource_type="video",
        format="jpg",
        transformation=[
            {"start_offset": "3.0s"},
            {"width": 1280, "height": 720, "crop": "fill"},
            {"quality": "auto:best"}
        ],
        secure=True
    )

    print(f"\n썸네일 URL (3초 시점, 1280x720):")
    print(f"  {thumbnail_url}")

    # 5. 비용 추적 테스트
    print("\n\n5. 비용 추적 테스트:")
    print("-" * 80)

    service._track_transformation_cost(
        count=10,
        user_id="test_user",
        project_id="test_project",
        metadata={"operation": "test_transform"}
    )

    print(f"\n변환 횟수: {service._transformation_count}")
    print(f"무료 tier 잔여: {25000 - service._transformation_count} 회")

    # 6. Public ID 생성 테스트
    print("\n\n6. Public ID 생성:")
    print("-" * 80)

    for i in range(3):
        video_id = service._generate_public_id("video")
        image_id = service._generate_public_id("image")
        print(f"\n생성 {i+1}:")
        print(f"  Video ID: {video_id}")
        print(f"  Image ID: {image_id}")

    print("\n\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)

    print("\n\n실제 업로드/변환 테스트를 위해서는:")
    print("1. .env 파일에 Cloudinary 계정 정보 설정")
    print("2. 테스트 영상/이미지 파일 준비")
    print("3. 아래 함수 주석 해제:")
    print("   - test_upload_and_transform()")
    print("   - test_thumbnail_generation()")


async def test_upload_and_transform():
    """실제 업로드 및 변환 테스트 (주석 처리됨)"""
    # 주의: 이 함수는 실제 Cloudinary API를 호출하므로
    # 비용이 발생할 수 있습니다.

    service = get_cloudinary_service()

    # 테스트 영상 파일 경로
    test_video = "./test_video.mp4"

    if not Path(test_video).exists():
        print(f"테스트 영상 파일이 없습니다: {test_video}")
        return

    # 1. 영상 업로드
    print("\n1. 영상 업로드:")
    upload_result = await service.upload_video(
        video_path=test_video,
        folder="test",
        user_id="test_user",
        project_id="test_project"
    )
    print(f"업로드 완료: {upload_result['public_id']}")
    print(f"URL: {upload_result['secure_url']}")

    # 2. 플랫폼별 변환
    print("\n2. YouTube용 변환:")
    youtube_video = await service.transform_video_for_platform(
        public_id=upload_result["public_id"],
        platform="youtube",
        user_id="test_user",
        project_id="test_project"
    )
    print(f"변환 완료: {youtube_video}")

    # 3. 썸네일 생성
    print("\n3. 썸네일 생성:")
    thumbnail_url = await service.generate_thumbnail(
        video_public_id=upload_result["public_id"],
        time_offset=3.0,
        width=1280,
        height=720,
        user_id="test_user",
        project_id="test_project"
    )
    print(f"썸네일 URL: {thumbnail_url}")

    # 4. 에셋 정보 조회
    print("\n4. 에셋 정보:")
    asset_info = await service.get_asset_info(
        public_id=upload_result["public_id"]
    )
    print(f"포맷: {asset_info['format']}")
    print(f"해상도: {asset_info['width']}x{asset_info['height']}")
    print(f"크기: {asset_info['bytes'] / 1024 / 1024:.2f} MB")
    print(f"길이: {asset_info['duration']:.2f}초")

    # 5. 에셋 삭제
    print("\n5. 에셋 삭제:")
    deleted = await service.delete_asset(
        public_id=upload_result["public_id"]
    )
    print(f"삭제 {'성공' if deleted else '실패'}")


if __name__ == "__main__":
    asyncio.run(test_cloudinary_service())

    # 실제 업로드 테스트 (주석 해제하여 사용)
    # asyncio.run(test_upload_and_transform())
