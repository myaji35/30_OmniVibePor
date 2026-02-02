"""프롬프트 변형 생성 예시 (독립 실행)

의존성 없이 프롬프트 변형 로직만 테스트합니다.
"""


class PromptVariationGenerator:
    """프롬프트 변형 생성기 (독립 버전)"""

    # 카메라 앵글 변형
    CAMERA_ANGLES = {
        "close_up": "Close-up shot, tight framing on subject",
        "medium_shot": "Medium shot, waist-up view of subject",
        "wide_shot": "Wide shot, full body view with environment"
    }

    # 조명 스타일 변형
    LIGHTING_STYLES = {
        "natural": "Natural lighting, soft daylight, realistic shadows",
        "dramatic": "Dramatic lighting, high contrast, cinematic mood lighting",
        "soft": "Soft lighting, diffused light, gentle shadows, bright and airy"
    }

    # 색감 변형
    COLOR_TONES = {
        "warm": "Warm color grading, golden hour tones, orange and yellow hues",
        "cool": "Cool color grading, blue and teal tones, modern aesthetic",
        "neutral": "Neutral color grading, balanced tones, natural colors"
    }

    @classmethod
    def generate_camera_angle_variation(cls, base_prompt: str):
        """카메라 앵글 변형 생성"""
        variations = []
        for angle_key, angle_desc in cls.CAMERA_ANGLES.items():
            variations.append({
                "type": "camera_angle",
                "variation_key": angle_key,
                "prompt": f"{base_prompt}. {angle_desc}",
                "description": angle_desc
            })
        return variations

    @classmethod
    def generate_lighting_variation(cls, base_prompt: str):
        """조명 스타일 변형 생성"""
        variations = []
        for lighting_key, lighting_desc in cls.LIGHTING_STYLES.items():
            variations.append({
                "type": "lighting",
                "variation_key": lighting_key,
                "prompt": f"{base_prompt}. {lighting_desc}",
                "description": lighting_desc
            })
        return variations

    @classmethod
    def generate_color_tone_variation(cls, base_prompt: str):
        """색감 변형 생성"""
        variations = []
        for tone_key, tone_desc in cls.COLOR_TONES.items():
            variations.append({
                "type": "color_tone",
                "variation_key": tone_key,
                "prompt": f"{base_prompt}. {tone_desc}",
                "description": tone_desc
            })
        return variations


def print_variations(variations, title):
    """변형 출력"""
    print(f"\n{title}")
    print("=" * 80)
    for i, var in enumerate(variations, 1):
        print(f"\n[변형 {i}] {var['variation_key'].upper().replace('_', ' ')}")
        print(f"프롬프트: {var['prompt']}")
        print(f"설명: {var['description']}")


def main():
    base_prompt = "Modern studio setting, friendly female presenter explaining a concept"

    print("\n" + "=" * 80)
    print("프롬프트 변형 생성 예시")
    print("=" * 80)
    print(f"\n원본 프롬프트:")
    print(f"  {base_prompt}")

    # 1. 카메라 앵글 변형
    camera_variations = PromptVariationGenerator.generate_camera_angle_variation(base_prompt)
    print_variations(camera_variations, "1. 카메라 앵글 변형 (3가지)")

    # 2. 조명 스타일 변형
    lighting_variations = PromptVariationGenerator.generate_lighting_variation(base_prompt)
    print_variations(lighting_variations, "2. 조명 스타일 변형 (3가지)")

    # 3. 색감 변형
    color_variations = PromptVariationGenerator.generate_color_tone_variation(base_prompt)
    print_variations(color_variations, "3. 색감 변형 (3가지)")

    # 통계
    print("\n" + "=" * 80)
    print("총 변형 개수 확인")
    print("=" * 80)
    print(f"카메라 앵글: {len(camera_variations)}개")
    print(f"조명 스타일: {len(lighting_variations)}개")
    print(f"색감: {len(color_variations)}개")
    print(f"전체: {len(camera_variations) + len(lighting_variations) + len(color_variations)}개")

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
