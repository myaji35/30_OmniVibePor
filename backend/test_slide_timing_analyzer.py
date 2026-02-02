"""SlideTimingAnalyzer 테스트"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.slide_timing_analyzer import get_slide_timing_analyzer
from app.models.neo4j_models import WhisperSegmentModel


async def test_basic_matching():
    """기본 텍스트 매칭 테스트"""
    print("\n" + "="*80)
    print("테스트 1: 기본 텍스트 매칭")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 샘플 Whisper 결과
    whisper_result = {
        "text": "안녕하세요. 오늘은 OmniVibe Pro를 소개해드리겠습니다. OmniVibe Pro는 AI 기반 영상 자동화 플랫폼입니다.",
        "language": "ko",
        "duration": 15.5,
        "segments": [
            {"id": 0, "start": 0.0, "end": 2.5, "text": "안녕하세요."},
            {"id": 1, "start": 2.5, "end": 6.8, "text": "오늘은 OmniVibe Pro를 소개해드리겠습니다."},
            {"id": 2, "start": 6.8, "end": 12.3, "text": "OmniVibe Pro는 AI 기반 영상 자동화 플랫폼입니다."},
        ]
    }

    # 슬라이드 스크립트
    slide_scripts = [
        {"slide_number": 1, "script": "안녕하세요. 오늘은 OmniVibe Pro를 소개해드리겠습니다."},
        {"slide_number": 2, "script": "OmniVibe Pro는 AI 기반 영상 자동화 플랫폼입니다."},
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/audio.mp3"
    )

    # 결과 출력
    print(f"\n분석된 슬라이드 수: {len(timings)}")
    for timing in timings:
        print(f"\n슬라이드 {timing.slide_number}:")
        print(f"  시작 시간: {timing.start_time:.2f}초")
        print(f"  종료 시간: {timing.end_time:.2f}초")
        print(f"  지속 시간: {timing.duration:.2f}초")
        print(f"  신뢰도: {timing.confidence:.2%}")
        print(f"  매칭된 텍스트: {timing.matched_text[:50]}...")

    # 검증
    assert len(timings) == 2, "2개의 슬라이드 타이밍이 생성되어야 합니다"
    assert timings[0].start_time == 0.0, "첫 번째 슬라이드는 0초에 시작해야 합니다"
    assert timings[0].confidence >= 0.80, "신뢰도가 80% 이상이어야 합니다"
    assert timings[1].start_time > timings[0].end_time or abs(timings[1].start_time - timings[0].end_time) < 0.1, \
        "슬라이드는 겹치지 않거나 조정되어야 합니다"

    print("\n✅ 테스트 1 통과!")


async def test_complex_matching():
    """복잡한 스크립트 매칭 테스트 (문장부호, 공백 차이)"""
    print("\n" + "="*80)
    print("테스트 2: 복잡한 스크립트 매칭 (정규화 테스트)")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # Whisper 결과 (문장부호 포함)
    whisper_result = {
        "text": "첫번째 슬라이드입니다! 여기서 핵심 개념을 소개합니다... 두번째 슬라이드에서는 실전 예제를 다룹니다.",
        "language": "ko",
        "duration": 20.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "첫번째 슬라이드입니다!"},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "여기서 핵심 개념을 소개합니다..."},
            {"id": 2, "start": 10.0, "end": 18.0, "text": "두번째 슬라이드에서는 실전 예제를 다룹니다."},
        ]
    }

    # 슬라이드 스크립트 (약간 다른 표현)
    slide_scripts = [
        {"slide_number": 1, "script": "첫번째 슬라이드입니다 여기서 핵심 개념을 소개합니다"},
        {"slide_number": 2, "script": "두번째 슬라이드에서는 실전 예제를 다룹니다"},
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/audio2.mp3"
    )

    # 결과 출력
    print(f"\n분석된 슬라이드 수: {len(timings)}")
    for timing in timings:
        print(f"\n슬라이드 {timing.slide_number}:")
        print(f"  시작 시간: {timing.start_time:.2f}초")
        print(f"  종료 시간: {timing.end_time:.2f}초")
        print(f"  신뢰도: {timing.confidence:.2%}")

    # 검증
    assert len(timings) == 2, "2개의 슬라이드 타이밍이 생성되어야 합니다"
    assert timings[0].confidence >= 0.70, "정규화로 인해 유사도가 70% 이상이어야 합니다"

    print("\n✅ 테스트 2 통과!")


async def test_timing_adjustment():
    """타이밍 조정 테스트 (겹침, 갭 처리)"""
    print("\n" + "="*80)
    print("테스트 3: 타이밍 조정 (겹침 제거, 갭 메우기)")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 겹치는 타이밍을 가진 Whisper 결과
    whisper_result = {
        "text": "첫 번째입니다. 두 번째입니다. 세 번째입니다.",
        "language": "ko",
        "duration": 15.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "첫 번째입니다."},
            {"id": 1, "start": 4.5, "end": 10.0, "text": "두 번째입니다."},  # 겹침
            {"id": 2, "start": 12.0, "end": 15.0, "text": "세 번째입니다."},  # 2초 갭
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "첫 번째입니다"},
        {"slide_number": 2, "script": "두 번째입니다"},
        {"slide_number": 3, "script": "세 번째입니다"},
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/audio3.mp3"
    )

    # 결과 출력
    print(f"\n조정된 슬라이드 수: {len(timings)}")
    for timing in timings:
        print(f"\n슬라이드 {timing.slide_number}:")
        print(f"  시작 시간: {timing.start_time:.2f}초")
        print(f"  종료 시간: {timing.end_time:.2f}초")
        print(f"  지속 시간: {timing.duration:.2f}초")

    # 검증: 겹침 없음
    for i in range(len(timings) - 1):
        assert timings[i].end_time <= timings[i + 1].start_time, \
            f"슬라이드 {timings[i].slide_number}와 {timings[i + 1].slide_number}가 겹칩니다"

    # 검증: 마지막 슬라이드가 오디오 끝까지 확장됨
    assert timings[-1].end_time == 15.0, "마지막 슬라이드가 오디오 끝까지 확장되어야 합니다"

    print("\n✅ 테스트 3 통과!")


async def test_accuracy_validation():
    """정확도 검증 테스트"""
    print("\n" + "="*80)
    print("테스트 4: 정확도 검증")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 고신뢰도 매칭 시나리오
    whisper_result = {
        "text": "완벽하게 일치하는 텍스트입니다. 100% 매칭됩니다.",
        "language": "ko",
        "duration": 10.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "완벽하게 일치하는 텍스트입니다."},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "100% 매칭됩니다."},
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "완벽하게 일치하는 텍스트입니다."},
        {"slide_number": 2, "script": "100% 매칭됩니다."},
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/audio4.mp3"
    )

    # 정확도 검증
    expected_durations = [5.0, 5.0]
    accuracy = analyzer.validate_timing_accuracy(
        slide_timings=timings,
        expected_durations=expected_durations
    )

    print(f"\n전체 정확도: {accuracy:.2f}%")
    for timing in timings:
        print(f"슬라이드 {timing.slide_number} 신뢰도: {timing.confidence:.2%}")

    # 검증
    assert accuracy >= 90.0, f"정확도가 90% 이상이어야 합니다 (현재: {accuracy:.2f}%)"
    assert all(t.confidence >= 0.90 for t in timings), "모든 슬라이드의 신뢰도가 90% 이상이어야 합니다"

    print("\n✅ 테스트 4 통과!")


async def test_low_confidence_scenario():
    """저신뢰도 시나리오 테스트 (매칭 실패)"""
    print("\n" + "="*80)
    print("테스트 5: 저신뢰도 시나리오 (매칭 실패 처리)")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 전혀 다른 텍스트
    whisper_result = {
        "text": "이것은 완전히 다른 내용입니다.",
        "language": "ko",
        "duration": 5.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "이것은 완전히 다른 내용입니다."},
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "원본 스크립트와 전혀 관련 없는 텍스트입니다."},
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/audio5.mp3"
    )

    # 결과 출력
    print(f"\n분석된 슬라이드 수: {len(timings)}")
    for timing in timings:
        print(f"\n슬라이드 {timing.slide_number}:")
        print(f"  신뢰도: {timing.confidence:.2%}")
        print(f"  매칭 여부: {'성공' if timing.confidence >= 0.80 else '실패'}")

    # 검증: 낮은 신뢰도
    assert timings[0].confidence < 0.80, "유사도가 낮아야 합니다"

    print("\n✅ 테스트 5 통과!")


async def main():
    """전체 테스트 실행"""
    print("\n" + "="*80)
    print("SlideTimingAnalyzer 테스트 시작")
    print("="*80)

    try:
        await test_basic_matching()
        await test_complex_matching()
        await test_timing_adjustment()
        await test_accuracy_validation()
        await test_low_confidence_scenario()

        print("\n" + "="*80)
        print("🎉 모든 테스트 통과!")
        print("="*80)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
