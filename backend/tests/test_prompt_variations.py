"""프롬프트 변형 생성 예시

PromptVariationGenerator의 동작을 확인하는 간단한 스크립트입니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.clip_editor_service import PromptVariationGenerator


def print_variations(variations, title):
    """변형 출력"""
    print(f"\n{title}")
    print("=" * 80)
    for i, var in enumerate(variations, 1):
        print(f"\n{i}. {var['variation_key'].upper()}")
        print(f"   프롬프트: {var['prompt']}")
        print(f"   설명: {var['description']}")


def main():
    base_prompt = "Modern studio setting, friendly female presenter explaining a concept"

    print("\n" + "=" * 80)
    print("프롬프트 변형 생성 예시")
    print("=" * 80)
    print(f"\n원본 프롬프트: {base_prompt}")

    # 1. 카메라 앵글 변형
    camera_variations = PromptVariationGenerator.generate_camera_angle_variation(base_prompt)
    print_variations(camera_variations, "1. 카메라 앵글 변형 (3가지)")

    # 2. 조명 스타일 변형
    lighting_variations = PromptVariationGenerator.generate_lighting_variation(base_prompt)
    print_variations(lighting_variations, "2. 조명 스타일 변형 (3가지)")

    # 3. 색감 변형
    color_variations = PromptVariationGenerator.generate_color_tone_variation(base_prompt)
    print_variations(color_variations, "3. 색감 변형 (3가지)")

    # 4. 모든 변형
    all_variations = PromptVariationGenerator.generate_all_variations(base_prompt)

    print("\n" + "=" * 80)
    print("총 변형 개수 확인")
    print("=" * 80)
    print(f"카메라 앵글: {len(all_variations['camera_angle'])}개")
    print(f"조명 스타일: {len(all_variations['lighting'])}개")
    print(f"색감: {len(all_variations['color_tone'])}개")
    print(f"전체: {sum(len(v) for v in all_variations.values())}개")

    # 5. 특정 변형 가져오기
    print("\n" + "=" * 80)
    print("특정 변형 1개 가져오기 예시")
    print("=" * 80)

    specific_var = PromptVariationGenerator.get_variation_by_type(
        base_prompt,
        variation_type="lighting",
        variation_key="dramatic"
    )

    print(f"\n변형 타입: {specific_var['type']}")
    print(f"변형 키: {specific_var['variation_key']}")
    print(f"프롬프트: {specific_var['prompt']}")
    print(f"설명: {specific_var['description']}")

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
