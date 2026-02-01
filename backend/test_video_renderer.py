"""VideoRenderer 기본 기능 테스트"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.video_renderer import (
    get_video_renderer,
    PLATFORM_SPECS,
    TRANSITION_EFFECTS,
    SUBTITLE_STYLES
)


async def test_info():
    """사용 가능한 옵션 정보 출력"""
    renderer = get_video_renderer()

    print("=" * 80)
    print("🎬 VideoRenderer 정보")
    print("=" * 80)

    print("\n📱 사용 가능한 플랫폼:")
    for name, desc in renderer.get_available_platforms().items():
        spec = PLATFORM_SPECS[name]
        print(f"  • {name}: {desc}")
        print(f"    - 해상도: {spec['resolution']}, 비트레이트: {spec['bitrate']}, FPS: {spec['fps']}")

    print("\n🎞️  사용 가능한 전환 효과 (일부):")
    transitions = list(renderer.get_available_transitions().items())[:10]
    for name, desc in transitions:
        print(f"  • {name}: {desc}")
    print(f"  ... 총 {len(TRANSITION_EFFECTS)}가지 전환 효과 지원")

    print("\n📝 사용 가능한 자막 스타일:")
    for name, desc in renderer.get_available_subtitle_styles().items():
        print(f"  • {name}: {desc}")

    print("\n" + "=" * 80)


async def test_render_simple():
    """단순 렌더링 테스트 (클립 1개 + 오디오)"""
    renderer = get_video_renderer()

    # 테스트용 오디오 파일 경로
    audio_dir = Path("./outputs/audio")
    audio_files = list(audio_dir.glob("*.mp3"))

    if not audio_files:
        print("❌ 테스트용 오디오 파일이 없습니다.")
        print(f"   {audio_dir}에 .mp3 파일을 생성하세요.")
        return

    audio_path = str(audio_files[0])
    print(f"\n✅ 테스트용 오디오: {audio_path}")

    # 임시 테스트 영상 생성 (FFmpeg로 단색 영상)
    import subprocess

    test_clip = "./outputs/videos/test_clip.mp4"
    Path("./outputs/videos").mkdir(parents=True, exist_ok=True)

    print("\n📹 테스트용 영상 생성 중...")
    subprocess.run([
        "ffmpeg",
        "-f", "lavfi",
        "-i", "color=c=blue:s=1920x1080:d=5",
        "-c:v", "libx264",
        "-y",
        test_clip
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    print(f"✅ 테스트 클립 생성: {test_clip}")

    # 렌더링 실행
    print("\n🎬 렌더링 시작...")

    output_path = "./outputs/videos/test_final.mp4"

    result = await renderer.render_video(
        video_clips=[test_clip],
        audio_path=audio_path,
        output_path=output_path,
        platform="youtube"
    )

    print("\n" + "=" * 80)
    print("✅ 렌더링 완료!")
    print("=" * 80)
    print(f"출력 파일: {result['output_path']}")
    print(f"파일 크기: {result['file_size_mb']} MB")
    print(f"렌더링 시간: {result['render_time']}초")
    print("\n단계별 정보:")
    for step, info in result['steps'].items():
        print(f"  • {step}: {info}")
    print("=" * 80)


async def main():
    """메인 테스트"""
    print("\n🎬 VideoRenderer 테스트\n")

    # 1. 정보 출력
    await test_info()

    # 2. 단순 렌더링 테스트
    try:
        await test_render_simple()
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
