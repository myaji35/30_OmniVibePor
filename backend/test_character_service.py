"""
CharacterService 기본 기능 테스트

이 스크립트는 CharacterService의 주요 기능을 테스트합니다:
- 캐릭터 ID 생성
- 프롬프트 생성
- 캐릭터 조회/생성 로직
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.character_service import get_character_service


async def test_character_service():
    """CharacterService 기본 기능 테스트"""
    print("=" * 60)
    print("CharacterService 테스트 시작")
    print("=" * 60)

    service = get_character_service()

    # 테스트 페르소나 데이터
    test_persona_id = "persona_test_001"
    test_gender = "female"
    test_age_range = "30-40"
    test_style = "professional"

    print("\n[1] 캐릭터 ID 생성 테스트")
    print("-" * 60)
    character_id = service._generate_character_id(test_persona_id)
    print(f"  페르소나 ID: {test_persona_id}")
    print(f"  생성된 캐릭터 ID: {character_id}")
    assert character_id.startswith("char_"), "캐릭터 ID는 'char_'로 시작해야 합니다"
    print("  ✓ 캐릭터 ID 생성 성공")

    print("\n[2] 캐릭터 프롬프트 생성 테스트")
    print("-" * 60)
    prompt = service._build_character_prompt(
        gender=test_gender,
        age_range=test_age_range,
        style=test_style
    )
    print(f"  생성된 프롬프트:")
    print(f"  {prompt}")
    assert "woman" in prompt.lower(), "성별 키워드가 포함되어야 합니다"
    assert "30s" in prompt.lower(), "연령대 키워드가 포함되어야 합니다"
    assert "professional" in prompt.lower(), "스타일 키워드가 포함되어야 합니다"
    print("  ✓ 프롬프트 생성 성공")

    print("\n[3] 추가 특징 포함 프롬프트 테스트")
    print("-" * 60)
    prompt_with_traits = service._build_character_prompt(
        gender="male",
        age_range="40-50",
        style="casual",
        additional_traits=["glasses", "friendly smile"]
    )
    print(f"  생성된 프롬프트:")
    print(f"  {prompt_with_traits}")
    assert "glasses" in prompt_with_traits, "추가 특징이 포함되어야 합니다"
    assert "friendly smile" in prompt_with_traits, "추가 특징이 포함되어야 합니다"
    print("  ✓ 추가 특징 포함 프롬프트 생성 성공")

    print("\n[4] 다양한 스타일 프리셋 테스트")
    print("-" * 60)
    styles = ["professional", "casual", "creative", "formal"]
    for style in styles:
        prompt = service._build_character_prompt(
            gender="neutral",
            age_range="30-40",
            style=style
        )
        assert style in prompt.lower(), f"{style} 스타일이 포함되어야 합니다"
        print(f"  ✓ {style} 스타일 프롬프트 생성 성공")

    print("\n[5] Fallback 캐릭터 생성 테스트")
    print("-" * 60)
    fallback_result = await service._generate_fallback_character(
        character_id=character_id,
        gender=test_gender,
        age_range=test_age_range
    )
    print(f"  Fallback 이미지 URL: {fallback_result['image_url']}")
    print(f"  모델: {fallback_result['model']}")
    print(f"  Fallback 여부: {fallback_result.get('is_fallback', False)}")
    assert fallback_result["is_fallback"] is True, "Fallback 플래그가 설정되어야 합니다"
    assert "image_url" in fallback_result, "이미지 URL이 반환되어야 합니다"
    print("  ✓ Fallback 캐릭터 생성 성공")

    print("\n[6] 캐릭터 데이터 → 프롬프트 변환 테스트")
    print("-" * 60)
    character_data = {
        "character_id": character_id,
        "prompt_template": "Professional woman in her 30s, business casual"
    }

    # 장면 컨텍스트 없이
    prompt1 = service.character_to_prompt(character_data)
    print(f"  기본 프롬프트: {prompt1}")

    # 장면 컨텍스트 포함
    prompt2 = service.character_to_prompt(
        character_data,
        scene_context="presenting in a conference room"
    )
    print(f"  장면 포함 프롬프트: {prompt2}")
    assert "conference room" in prompt2, "장면 컨텍스트가 포함되어야 합니다"
    print("  ✓ 프롬프트 변환 성공")

    print("\n" + "=" * 60)
    print("모든 테스트 통과! ✓")
    print("=" * 60)

    # Neo4j 연결 테스트 (선택적)
    print("\n[추가] Neo4j 연결 테스트")
    print("-" * 60)
    try:
        existing = await service._get_character_from_neo4j(character_id)
        print(f"  Neo4j 조회 결과: {existing}")
        print("  ✓ Neo4j 연결 성공")
    except Exception as e:
        print(f"  ⚠ Neo4j 연결 실패 (정상 - 컨테이너 실행 시 사용 가능): {e}")


if __name__ == "__main__":
    asyncio.run(test_character_service())
