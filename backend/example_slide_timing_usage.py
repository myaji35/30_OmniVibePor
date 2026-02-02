"""SlideTimingAnalyzer 실전 사용 예제"""
import asyncio
from app.services.slide_timing_analyzer import get_slide_timing_analyzer


async def example_basic_usage():
    """기본 사용 예제"""
    print("\n" + "="*80)
    print("예제 1: 기본 사용법")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # Whisper API 응답 (실제 API 호출 결과와 동일한 형식)
    whisper_result = {
        "text": "안녕하세요, OmniVibe Pro 프레젠테이션을 시작하겠습니다. 오늘은 AI 기반 영상 자동화의 미래를 보여드립니다. 첫 번째로, 바이브 코딩 방법론을 소개합니다. 두 번째로, 실제 사용 사례를 살펴봅니다. 마지막으로, 향후 로드맵을 공유하겠습니다.",
        "language": "ko",
        "duration": 25.8,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 3.5,
                "text": "안녕하세요, OmniVibe Pro 프레젠테이션을 시작하겠습니다."
            },
            {
                "id": 1,
                "start": 3.5,
                "end": 8.2,
                "text": "오늘은 AI 기반 영상 자동화의 미래를 보여드립니다."
            },
            {
                "id": 2,
                "start": 8.2,
                "end": 13.0,
                "text": "첫 번째로, 바이브 코딩 방법론을 소개합니다."
            },
            {
                "id": 3,
                "start": 13.0,
                "end": 18.5,
                "text": "두 번째로, 실제 사용 사례를 살펴봅니다."
            },
            {
                "id": 4,
                "start": 18.5,
                "end": 25.8,
                "text": "마지막으로, 향후 로드맵을 공유하겠습니다."
            }
        ]
    }

    # 슬라이드 스크립트 (프레젠테이션 PDF에서 추출)
    slide_scripts = [
        {"slide_number": 1, "script": "안녕하세요 OmniVibe Pro 프레젠테이션을 시작하겠습니다 오늘은 AI 기반 영상 자동화의 미래를 보여드립니다"},
        {"slide_number": 2, "script": "첫 번째로 바이브 코딩 방법론을 소개합니다"},
        {"slide_number": 3, "script": "두 번째로 실제 사용 사례를 살펴봅니다"},
        {"slide_number": 4, "script": "마지막으로 향후 로드맵을 공유하겠습니다"}
    ]

    # 타이밍 분석 실행
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/presentations/demo_narration.mp3",
        project_id=None  # Neo4j 업데이트 안 함
    )

    # 결과 출력
    print(f"\n분석 완료! 총 {len(timings)}개 슬라이드")
    print("-" * 80)

    for timing in timings:
        print(f"\n슬라이드 {timing.slide_number}:")
        print(f"  ⏱️  시작: {timing.start_time:.2f}초")
        print(f"  ⏱️  종료: {timing.end_time:.2f}초")
        print(f"  ⏱️  길이: {timing.duration:.2f}초")
        print(f"  ✅ 신뢰도: {timing.confidence:.2%}")
        print(f"  📝 매칭된 텍스트: {timing.matched_text[:60]}...")

    # 정확도 검증
    expected_durations = [8.2, 4.8, 5.5, 7.3]
    accuracy = analyzer.validate_timing_accuracy(
        slide_timings=timings,
        expected_durations=expected_durations
    )

    print(f"\n전체 정확도: {accuracy:.2f}%")
    if accuracy >= 90.0:
        print("✅ 정확도 검증 통과! (90% 이상)")
    else:
        print("⚠️  정확도가 90% 미만입니다. 스크립트를 재확인하세요.")


async def example_with_stt_integration():
    """STT Service와 통합 예제"""
    print("\n" + "="*80)
    print("예제 2: STT Service와 통합")
    print("="*80)

    # 실제로는 이렇게 사용합니다:
    # from app.services.stt_service import get_stt_service
    # stt_service = get_stt_service()
    #
    # # Step 1: Whisper STT 실행
    # whisper_result = await stt_service.transcribe_with_timestamps(
    #     audio_file_path="/path/to/narration.mp3",
    #     language="ko"
    # )
    #
    # # Step 2: 슬라이드 타이밍 분석
    # analyzer = get_slide_timing_analyzer()
    # timings = await analyzer.analyze_timing(
    #     whisper_result=whisper_result,
    #     slide_scripts=slide_scripts,
    #     audio_path="/path/to/narration.mp3",
    #     project_id="proj_abc123"
    # )

    print("\n코드 예제:")
    print("""
from app.services.stt_service import get_stt_service
from app.services.slide_timing_analyzer import get_slide_timing_analyzer

stt_service = get_stt_service()
analyzer = get_slide_timing_analyzer()

# Whisper STT 실행 (타임스탬프 포함)
whisper_result = await stt_service.transcribe_with_timestamps(
    audio_file_path="/presentations/narration.mp3",
    language="ko"
)

# 슬라이드 스크립트
slide_scripts = [
    {"slide_number": 1, "script": "첫 번째 슬라이드 내용"},
    {"slide_number": 2, "script": "두 번째 슬라이드 내용"},
    {"slide_number": 3, "script": "세 번째 슬라이드 내용"}
]

# 타이밍 분석 및 Neo4j 자동 업데이트
timings = await analyzer.analyze_timing(
    whisper_result=whisper_result,
    slide_scripts=slide_scripts,
    audio_path="/presentations/narration.mp3",
    project_id="proj_abc123"  # 제공 시 Neo4j 자동 업데이트
)

print(f"슬라이드 1: {timings[0].start_time:.2f}s - {timings[0].end_time:.2f}s")
print(f"슬라이드 2: {timings[1].start_time:.2f}s - {timings[1].end_time:.2f}s")
print(f"슬라이드 3: {timings[2].start_time:.2f}s - {timings[2].end_time:.2f}s")
    """)


async def example_timing_adjustment():
    """타이밍 조정 예제"""
    print("\n" + "="*80)
    print("예제 3: 타이밍 조정 (겹침/갭 처리)")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 겹침과 갭이 있는 Whisper 결과
    whisper_result = {
        "text": "슬라이드 1입니다. 슬라이드 2입니다. 슬라이드 3입니다.",
        "language": "ko",
        "duration": 20.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 6.0, "text": "슬라이드 1입니다."},
            {"id": 1, "start": 5.5, "end": 12.0, "text": "슬라이드 2입니다."},  # 겹침!
            {"id": 2, "start": 15.0, "end": 20.0, "text": "슬라이드 3입니다."}   # 3초 갭
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "슬라이드 1입니다"},
        {"slide_number": 2, "script": "슬라이드 2입니다"},
        {"slide_number": 3, "script": "슬라이드 3입니다"}
    ]

    # 타이밍 분석 (자동 조정 포함)
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/overlap.mp3"
    )

    # 조정 전후 비교
    print("\n원본 Whisper 세그먼트:")
    print(f"  Segment 0: 0.0s - 6.0s")
    print(f"  Segment 1: 5.5s - 12.0s  ⚠️ 겹침 (5.5-6.0)")
    print(f"  Segment 2: 15.0s - 20.0s  ⚠️ 갭 (12.0-15.0)")

    print("\n조정 후 슬라이드 타이밍:")
    for timing in timings:
        print(f"  슬라이드 {timing.slide_number}: {timing.start_time:.2f}s - {timing.end_time:.2f}s")

    # 검증
    for i in range(len(timings) - 1):
        assert timings[i].end_time <= timings[i + 1].start_time, \
            f"슬라이드 {timings[i].slide_number}와 {timings[i + 1].slide_number}가 겹칩니다"

    print("\n✅ 겹침 제거 완료!")
    print("✅ 마지막 슬라이드가 오디오 끝까지 확장됨!")


async def example_accuracy_validation():
    """정확도 검증 예제"""
    print("\n" + "="*80)
    print("예제 4: 정확도 검증")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 고신뢰도 매칭 시나리오
    whisper_result = {
        "text": "슬라이드 1은 완벽하게 일치합니다. 슬라이드 2도 정확히 매칭됩니다.",
        "language": "ko",
        "duration": 10.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "슬라이드 1은 완벽하게 일치합니다."},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "슬라이드 2도 정확히 매칭됩니다."}
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "슬라이드 1은 완벽하게 일치합니다"},
        {"slide_number": 2, "script": "슬라이드 2도 정확히 매칭됩니다"}
    ]

    # 타이밍 분석
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/perfect_match.mp3"
    )

    # 정확도 검증
    expected_durations = [5.0, 5.0]
    accuracy = analyzer.validate_timing_accuracy(
        slide_timings=timings,
        expected_durations=expected_durations
    )

    print(f"\n전체 정확도: {accuracy:.2f}%")

    print("\n슬라이드별 신뢰도:")
    for timing in timings:
        confidence_status = "✅ 고신뢰도" if timing.confidence >= 0.90 else "⚠️  저신뢰도"
        print(f"  슬라이드 {timing.slide_number}: {timing.confidence:.2%} {confidence_status}")

    if accuracy >= 90.0:
        print("\n✅ 정확도 검증 통과!")
    else:
        print("\n⚠️  정확도가 90% 미만입니다.")
        print("   해결 방법:")
        print("   1. 스크립트와 나레이션이 일치하는지 확인")
        print("   2. Whisper STT 재실행 (temperature=0.0)")
        print("   3. 임계값 조정 고려")


async def example_neo4j_integration():
    """Neo4j 연동 예제"""
    print("\n" + "="*80)
    print("예제 5: Neo4j 자동 업데이트")
    print("="*80)

    analyzer = get_slide_timing_analyzer()

    # 샘플 데이터
    whisper_result = {
        "text": "슬라이드 1입니다. 슬라이드 2입니다.",
        "language": "ko",
        "duration": 10.0,
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "슬라이드 1입니다."},
            {"id": 1, "start": 5.0, "end": 10.0, "text": "슬라이드 2입니다."}
        ]
    }

    slide_scripts = [
        {"slide_number": 1, "script": "슬라이드 1입니다"},
        {"slide_number": 2, "script": "슬라이드 2입니다"}
    ]

    # project_id 제공 시 Neo4j 자동 업데이트
    timings = await analyzer.analyze_timing(
        whisper_result=whisper_result,
        slide_scripts=slide_scripts,
        audio_path="/test/neo4j_test.mp3",
        project_id="proj_demo123"  # 🔑 Neo4j 업데이트 활성화
    )

    print("\nNeo4j에 다음 정보가 업데이트됩니다:")
    print("-" * 80)

    for timing in timings:
        print(f"\nSlide 노드 (slide_number={timing.slide_number}):")
        print(f"  start_time: {timing.start_time}")
        print(f"  end_time: {timing.end_time}")
        print(f"  duration: {timing.duration}")
        print(f"  confidence: {timing.confidence}")
        print(f"  matched_text: '{timing.matched_text}'")
        print(f"  timing_updated_at: datetime()")

    print("\nCypher 쿼리로 확인:")
    print("""
MATCH (proj:Project {project_id: "proj_demo123"})
      -[:HAS_PRESENTATION]->(:Presentation)
      -[:HAS_SLIDE]->(slide:Slide)
RETURN slide.slide_number,
       slide.start_time,
       slide.end_time,
       slide.confidence
ORDER BY slide.slide_number
    """)


async def main():
    """모든 예제 실행"""
    print("\n" + "="*80)
    print("SlideTimingAnalyzer 실전 사용 예제")
    print("="*80)

    await example_basic_usage()
    await example_with_stt_integration()
    await example_timing_adjustment()
    await example_accuracy_validation()
    await example_neo4j_integration()

    print("\n" + "="*80)
    print("모든 예제 완료!")
    print("="*80)
    print("\n자세한 사용법은 다음 문서를 참고하세요:")
    print("📖 /backend/docs/SLIDE_TIMING_ANALYZER_USAGE.md")


if __name__ == "__main__":
    asyncio.run(main())
