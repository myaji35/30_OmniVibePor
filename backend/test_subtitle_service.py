"""자막 생성 서비스 테스트

SubtitleService의 주요 기능을 테스트합니다:
1. Whisper API를 통한 자막 생성
2. SRT 형식 변환
3. 타임스탬프 포맷팅
4. 세그먼트 병합
5. 다국어 자막 생성

사용법:
    python test_subtitle_service.py

참고:
    - OPENAI_API_KEY 환경 변수 필요
    - 테스트용 오디오 파일 필요
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.subtitle_service import get_subtitle_service


async def test_basic_subtitle_generation():
    """기본 자막 생성 테스트"""
    print("\n" + "="*60)
    print("테스트 1: 기본 자막 생성")
    print("="*60)

    service = get_subtitle_service()

    # 테스트용 오디오 파일 경로 (실제 파일로 교체 필요)
    audio_path = "./outputs/audio/test_audio.mp3"

    if not Path(audio_path).exists():
        print(f"⚠️  테스트 오디오 파일이 없습니다: {audio_path}")
        print("   실제 오디오 파일을 준비하거나 경로를 수정하세요.")
        return

    try:
        result = await service.generate_subtitles(
            audio_path=audio_path,
            language="ko",
            granularity="segment",
            user_id="test_user",
            project_id="test_project"
        )

        print(f"✅ 자막 생성 성공!")
        print(f"   - SRT 파일: {result['srt_path']}")
        print(f"   - 세그먼트 수: {result['segments'].__len__()}")
        print(f"   - 오디오 길이: {result['duration']:.2f}초")
        print(f"   - 언어: {result['language']}")
        print(f"   - 단어 수: {result['word_count']}")
        print(f"   - API 비용: ${result['cost_usd']:.6f}")

        # 첫 3개 세그먼트 출력
        print("\n📝 첫 3개 자막 세그먼트:")
        for i, seg in enumerate(result['segments'][:3], 1):
            start = service._format_timestamp(seg['start'])
            end = service._format_timestamp(seg['end'])
            print(f"   {i}. [{start} --> {end}] {seg['text']}")

    except Exception as e:
        print(f"❌ 실패: {e}")


async def test_timestamp_formatting():
    """타임스탬프 포맷팅 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 타임스탬프 포맷팅")
    print("="*60)

    service = get_subtitle_service()

    test_cases = [
        (0.0, "00:00:00,000"),
        (1.5, "00:00:01,500"),
        (62.123, "00:01:02,123"),
        (3665.789, "01:01:05,789"),
    ]

    for seconds, expected in test_cases:
        result = service._format_timestamp(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds}초 → {result} (기대값: {expected})")


def test_srt_content_generation():
    """SRT 콘텐츠 생성 테스트"""
    print("\n" + "="*60)
    print("테스트 3: SRT 콘텐츠 생성")
    print("="*60)

    service = get_subtitle_service()

    segments = [
        {"start": 0.0, "end": 2.5, "text": "안녕하세요."},
        {"start": 2.5, "end": 5.0, "text": "오늘은 좋은 날씨입니다."},
        {"start": 5.0, "end": 8.0, "text": "여러분과 함께 할 내용이 있습니다."},
    ]

    srt_content = service._generate_srt_content(segments)

    print("생성된 SRT 콘텐츠:")
    print("-" * 60)
    print(srt_content)
    print("-" * 60)

    # SRT 형식 검증
    lines = srt_content.strip().split("\n")
    expected_lines = len(segments) * 4  # 각 세그먼트당 4줄 (인덱스, 타임스탬프, 텍스트, 빈 줄)

    if len(lines) == expected_lines:
        print("✅ SRT 형식이 올바릅니다.")
    else:
        print(f"❌ SRT 형식 오류: {len(lines)}줄 (기대값: {expected_lines}줄)")


def test_segment_merging():
    """세그먼트 병합 테스트"""
    print("\n" + "="*60)
    print("테스트 4: 세그먼트 병합")
    print("="*60)

    service = get_subtitle_service()

    segments = [
        {"start": 0.0, "end": 1.0, "text": "안녕"},
        {"start": 1.0, "end": 2.0, "text": "하세요"},
        {"start": 2.0, "end": 3.0, "text": "여러분"},
        {"start": 3.0, "end": 4.0, "text": "반갑습니다"},
    ]

    print(f"원본 세그먼트: {len(segments)}개")
    for seg in segments:
        print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}")

    merged = service.merge_subtitle_segments(
        segments,
        max_duration=3.0,
        max_chars=50
    )

    print(f"\n병합 후: {len(merged)}개")
    for seg in merged:
        print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}")

    if len(merged) < len(segments):
        print("✅ 세그먼트 병합 성공")
    else:
        print("⚠️  병합이 수행되지 않았습니다.")


async def test_multilingual_subtitles():
    """다국어 자막 생성 테스트"""
    print("\n" + "="*60)
    print("테스트 5: 다국어 자막 생성")
    print("="*60)

    service = get_subtitle_service()

    audio_path = "./outputs/audio/test_audio.mp3"

    if not Path(audio_path).exists():
        print(f"⚠️  테스트 오디오 파일이 없습니다: {audio_path}")
        return

    try:
        results = await service.generate_subtitles_for_multiple_languages(
            audio_path=audio_path,
            languages=["ko", "en"],
            output_dir="./outputs/subtitles",
            user_id="test_user",
            project_id="test_project"
        )

        print(f"✅ 다국어 자막 생성 완료:")
        for lang, result in results.items():
            if "error" in result:
                print(f"   ❌ {lang}: {result['error']}")
            else:
                print(f"   ✅ {lang}: {result['srt_path']}")
                print(f"      - 세그먼트: {len(result['segments'])}개")
                print(f"      - 비용: ${result['cost_usd']:.6f}")

    except Exception as e:
        print(f"❌ 실패: {e}")


def test_subtitle_styles():
    """자막 스타일 테스트"""
    print("\n" + "="*60)
    print("테스트 6: 자막 스타일 프리셋")
    print("="*60)

    service = get_subtitle_service()

    print("사용 가능한 스타일 프리셋:")
    for style_name, style_config in service.SUBTITLE_STYLES.items():
        print(f"\n  🎨 {style_name}:")
        for key, value in style_config.items():
            print(f"     - {key}: {value}")


async def test_video_subtitle_overlay():
    """비디오 자막 오버레이 테스트"""
    print("\n" + "="*60)
    print("테스트 7: 비디오 자막 오버레이")
    print("="*60)

    service = get_subtitle_service()

    video_path = "./outputs/video/test_video.mp4"
    srt_path = "./outputs/subtitles/test_audio.srt"
    output_path = "./outputs/video/test_video_subtitled.mp4"

    if not Path(video_path).exists():
        print(f"⚠️  테스트 비디오 파일이 없습니다: {video_path}")
        return

    if not Path(srt_path).exists():
        print(f"⚠️  SRT 파일이 없습니다: {srt_path}")
        print("   먼저 자막 생성 테스트를 실행하세요.")
        return

    try:
        result_path = await service.apply_subtitles_to_video(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
            style="youtube"
        )

        print(f"✅ 자막 오버레이 성공!")
        print(f"   출력 파일: {result_path}")

    except Exception as e:
        print(f"❌ 실패: {e}")


def test_file_validation():
    """파일 형식 검증 테스트"""
    print("\n" + "="*60)
    print("테스트 8: 파일 형식 검증")
    print("="*60)

    service = get_subtitle_service()

    audio_test_cases = [
        ("test.mp3", True),
        ("test.wav", True),
        ("test.m4a", True),
        ("test.txt", False),
        ("test.jpg", False),
    ]

    print("오디오 형식 검증:")
    for filename, expected in audio_test_cases:
        result = service.validate_audio_format(filename)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {filename}: {result}")

    video_test_cases = [
        ("test.mp4", True),
        ("test.mov", True),
        ("test.avi", True),
        ("test.txt", False),
        ("test.mp3", False),
    ]

    print("\n비디오 형식 검증:")
    for filename, expected in video_test_cases:
        result = service.validate_video_format(filename)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {filename}: {result}")


async def main():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("SubtitleService 테스트 시작")
    print("="*60)

    # 동기 테스트
    test_timestamp_formatting()
    test_srt_content_generation()
    test_segment_merging()
    test_subtitle_styles()
    test_file_validation()

    # 비동기 테스트 (실제 오디오 파일 필요)
    print("\n" + "="*60)
    print("비동기 테스트 (오디오 파일 필요)")
    print("="*60)

    await test_basic_subtitle_generation()
    await test_multilingual_subtitles()
    await test_video_subtitle_overlay()

    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
