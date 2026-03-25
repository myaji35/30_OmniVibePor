#!/usr/bin/env python3
"""Lipsync Service 테스트 스크립트

사용법:
    python test_lipsync.py --video input.mp4 --audio audio.mp3 --method auto
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.lipsync_service import get_lipsync_service
from app.core.config import get_settings


async def test_lipsync(
    video_path: str,
    audio_path: str,
    output_path: str,
    method: str = "auto"
):
    """
    립싱크 서비스 테스트

    Args:
        video_path: 입력 영상 경로
        audio_path: 입력 오디오 경로
        output_path: 출력 영상 경로
        method: 사용할 방법 ("auto", "heygen", "wav2lip")
    """
    print("=" * 60)
    print("🎬 Lipsync Service Test")
    print("=" * 60)

    # 설정 확인
    settings = get_settings()
    print(f"\n📋 Configuration:")
    print(f"  - HeyGen API Key: {'✅ Set' if settings.HEYGEN_API_KEY else '❌ Not set'}")
    print(f"  - Wav2Lip Model: {'✅ Set' if settings.WAV2LIP_MODEL_PATH else '❌ Not set'}")
    print(f"  - GPU Enabled: {settings.LIPSYNC_GPU_ENABLED}")
    print(f"  - Method: {method}")

    # 입력 파일 확인
    print(f"\n📁 Input Files:")
    video_exists = Path(video_path).exists()
    audio_exists = Path(audio_path).exists()
    print(f"  - Video: {video_path} {'✅' if video_exists else '❌ NOT FOUND'}")
    print(f"  - Audio: {audio_path} {'✅' if audio_exists else '❌ NOT FOUND'}")

    if not video_exists or not audio_exists:
        print("\n❌ Error: Input files not found!")
        return

    # 립싱크 서비스 초기화
    print(f"\n🚀 Starting lipsync generation...")
    lipsync = get_lipsync_service()

    try:
        # 립싱크 생성
        result = await lipsync.generate_lipsync(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path,
            method=method
        )

        # 결과 출력
        print(f"\n✅ Lipsync generation completed!")
        print(f"\n📊 Result:")
        print(f"  - Status: {result['status']}")
        print(f"  - Method Used: {result['method_used']}")
        print(f"  - Output Path: {result['output_path']}")
        print(f"  - Duration: {result['duration']:.1f}s")
        print(f"  - Cost: ${result.get('cost_usd', 0):.3f}")

        # 품질 평가 (선택적)
        if Path(output_path).exists():
            print(f"\n🔍 Checking quality...")
            quality = await lipsync.check_lipsync_quality(output_path)
            print(f"  - Sync Score: {quality['sync_score']:.2f}")
            print(f"  - Audio Quality: {quality['audio_quality']:.2f}")
            print(f"  - Video Quality: {quality['video_quality']:.2f}")

    except Exception as e:
        print(f"\n❌ Lipsync generation failed:")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await lipsync.close()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Lipsync Service 테스트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 자동 방법 (HeyGen 우선 → Wav2Lip Fallback)
  python test_lipsync.py --video input.mp4 --audio audio.mp3

  # HeyGen 강제 사용
  python test_lipsync.py --video input.mp4 --audio audio.mp3 --method heygen

  # Wav2Lip 강제 사용
  python test_lipsync.py --video input.mp4 --audio audio.mp3 --method wav2lip
        """
    )

    parser.add_argument(
        "--video",
        required=True,
        help="입력 영상 파일 경로"
    )

    parser.add_argument(
        "--audio",
        required=True,
        help="입력 오디오 파일 경로"
    )

    parser.add_argument(
        "--output",
        help="출력 영상 파일 경로 (기본: ./outputs/lipsync/synced.mp4)"
    )

    parser.add_argument(
        "--method",
        choices=["auto", "heygen", "wav2lip"],
        default="auto",
        help="사용할 립싱크 방법 (기본: auto)"
    )

    args = parser.parse_args()

    # 출력 경로 설정
    if not args.output:
        output_dir = Path("./outputs/lipsync")
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output = str(output_dir / "synced.mp4")

    # 테스트 실행
    asyncio.run(test_lipsync(
        video_path=args.video,
        audio_path=args.audio,
        output_path=args.output,
        method=args.method
    ))


if __name__ == "__main__":
    main()
