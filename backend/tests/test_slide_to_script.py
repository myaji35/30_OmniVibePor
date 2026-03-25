"""SlideToScriptConverter 테스트

실제 슬라이드 텍스트로 변환 예시를 실행합니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.slide_to_script_converter import (
    SlideToScriptConverter,
    SlideData,
    ToneType
)


# ==================== 테스트 데이터 ====================

SAMPLE_SLIDES = [
    SlideData(
        slide_number=1,
        title="OmniVibe Pro 소개",
        content="""- AI 기반 영상 자동화 플랫폼
- 구글 시트 연동으로 간편한 워크플로우
- 다채널 자동 배포 지원
- Vibe Coding 방법론 적용"""
    ),
    SlideData(
        slide_number=2,
        title="핵심 기능",
        content="""- Writer Agent: 스크립트 자동 생성
- Director Agent: 영상 제작 및 보정
- Marketer Agent: 다채널 배포 자동화
- GraphRAG 기반 학습 시스템"""
    ),
    SlideData(
        slide_number=3,
        title="주요 장점",
        content="""- 시간 절약: 수작업 대비 80% 단축
- 품질 보장: AI 기반 오디오/영상 보정
- 확장성: 다양한 플랫폼 동시 지원
- 학습 기능: 사용할수록 더 나은 결과"""
    )
]


# ==================== 테스트 함수 ====================

async def test_conversion_with_tone(tone: ToneType):
    """특정 톤으로 변환 테스트"""
    print(f"\n{'='*60}")
    print(f"톤: {tone.value.upper()}")
    print(f"{'='*60}\n")

    converter = SlideToScriptConverter()

    result = await converter.convert_slides_to_script(
        slides=SAMPLE_SLIDES,
        tone=tone,
        target_duration_per_slide=15.0
    )

    print("✅ 변환 완료\n")
    print(f"📊 통계:")
    print(f"  - 총 슬라이드: {len(SAMPLE_SLIDES)}개")
    print(f"  - 총 예상 시간: {result.total_duration:.1f}초 ({result.total_duration/60:.1f}분)")
    print(f"  - 슬라이드당 평균: {result.average_duration_per_slide:.1f}초")
    print(f"\n{'='*60}")
    print("📝 전체 나레이션 스크립트:")
    print(f"{'='*60}\n")
    print(result.full_script)

    print(f"\n{'='*60}")
    print("📋 슬라이드별 세부 정보:")
    print(f"{'='*60}\n")
    for slide_script in result.slide_scripts:
        print(f"[슬라이드 {slide_script['slide_number']}]")
        print(f"  예상 시간: {slide_script['estimated_duration']:.1f}초")
        print(f"  글자 수: {slide_script['word_count']}자")
        print(f"  스크립트:\n{slide_script['script']}\n")


async def test_transition_generation():
    """전환 문구 생성 테스트"""
    print(f"\n{'='*60}")
    print("🔗 전환 문구 생성 테스트")
    print(f"{'='*60}\n")

    converter = SlideToScriptConverter()

    for tone in ToneType:
        print(f"\n[{tone.value}]")
        for i in range(3):
            transition = converter.generate_transition(
                current_slide_title="OmniVibe Pro 소개",
                next_slide_title="핵심 기능",
                tone=tone
            )
            print(f"  {i+1}. {transition}")


async def test_script_adjustment():
    """스크립트 길이 조정 테스트"""
    print(f"\n{'='*60}")
    print("✂️ 스크립트 길이 조정 테스트")
    print(f"{'='*60}\n")

    converter = SlideToScriptConverter()

    # 원본 스크립트
    original_script = """
    안녕하세요. 오늘은 OmniVibe Pro를 소개해드리겠습니다.
    OmniVibe Pro는 AI 기반 영상 자동화 플랫폼으로,
    구글 시트와 연동되어 다채널 자동 배포를 지원합니다.
    """

    original_duration = converter.estimate_narration_duration(original_script)
    print(f"원본 스크립트 시간: {original_duration:.1f}초")
    print(f"원본 스크립트:\n{original_script}\n")

    # 목표 시간 (50% 더 짧게)
    target_duration = original_duration * 0.5
    print(f"\n목표 시간: {target_duration:.1f}초 (50% 단축)\n")

    # 조정된 스크립트
    adjusted_script = converter.adjust_script_length(
        script=original_script,
        target_duration=target_duration,
        current_duration=original_duration
    )

    adjusted_duration = converter.estimate_narration_duration(adjusted_script)
    print(f"조정된 스크립트 시간: {adjusted_duration:.1f}초")
    print(f"조정된 스크립트:\n{adjusted_script}\n")


async def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🎬 SlideToScriptConverter 테스트 시작")
    print("="*60)

    # 1. 톤별 변환 테스트
    for tone in ToneType:
        await test_conversion_with_tone(tone)
        print("\n" + "-"*60 + "\n")
        await asyncio.sleep(1)  # API 레이트 리밋 방지

    # 2. 전환 문구 생성 테스트
    await test_transition_generation()

    # 3. 스크립트 길이 조정 테스트 (주석 처리 - API 비용 절감)
    # await test_script_adjustment()

    print("\n" + "="*60)
    print("✅ 모든 테스트 완료!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
