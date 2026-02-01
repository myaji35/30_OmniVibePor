"""
Nano Banana 캐릭터 일관성 서비스

이 서비스는 페르소나 기반으로 일관된 캐릭터 레퍼런스를 생성하고 관리합니다.
같은 페르소나는 항상 같은 캐릭터 이미지를 사용하여 영상 일관성을 보장합니다.
"""
from typing import Dict, Any, Optional, List
import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from contextlib import nullcontext
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.neo4j_client import get_neo4j_client

settings = get_settings()

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class CharacterService:
    """
    캐릭터 일관성 관리 서비스

    주요 기능:
    - 페르소나 기반 캐릭터 레퍼런스 이미지 생성
    - 캐릭터 일관성 유지 (같은 페르소나 = 같은 캐릭터)
    - Neo4j에 캐릭터 정보 저장
    - Nano Banana API 또는 Stable Diffusion 통합
    """

    # 캐릭터 스타일 프리셋
    STYLE_PRESETS = {
        "professional": "professional business attire, modern office, natural lighting, photorealistic",
        "casual": "casual comfortable clothing, relaxed setting, natural lighting, photorealistic",
        "creative": "artistic creative outfit, vibrant background, dynamic lighting, photorealistic",
        "formal": "formal elegant attire, sophisticated background, studio lighting, photorealistic"
    }

    # 연령대별 프롬프트 키워드
    AGE_KEYWORDS = {
        "20-30": "young adult in their 20s",
        "30-40": "professional in their 30s",
        "40-50": "experienced professional in their 40s",
        "50-60": "mature professional in their 50s"
    }

    # 성별별 프롬프트 키워드
    GENDER_KEYWORDS = {
        "male": "man",
        "female": "woman",
        "neutral": "person"
    }

    def __init__(self, output_dir: str = "./outputs/characters"):
        """
        캐릭터 서비스 초기화

        Args:
            output_dir: 캐릭터 이미지 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.neo4j = get_neo4j_client()

        # API 설정
        self.banana_api_key = settings.BANANA_API_KEY
        self.use_banana = self.banana_api_key is not None

        if not self.use_banana:
            self.logger.warning(
                "BANANA_API_KEY not set. Character service will use fallback mode."
            )

    def _generate_character_id(self, persona_id: str) -> str:
        """
        페르소나 ID로부터 고유한 캐릭터 ID 생성

        Args:
            persona_id: 페르소나 ID

        Returns:
            캐릭터 ID (char_로 시작하는 해시값)
        """
        hash_digest = hashlib.sha256(persona_id.encode()).hexdigest()[:16]
        return f"char_{hash_digest}"

    def _build_character_prompt(
        self,
        gender: str,
        age_range: str,
        style: str = "professional",
        additional_traits: Optional[List[str]] = None
    ) -> str:
        """
        캐릭터 생성 프롬프트 구성

        Args:
            gender: 성별 (male, female, neutral)
            age_range: 연령대 (20-30, 30-40, 40-50, 50-60)
            style: 스타일 프리셋 (professional, casual, creative, formal)
            additional_traits: 추가 특징 리스트

        Returns:
            생성된 프롬프트 문자열
        """
        # 기본 프롬프트 구성
        gender_keyword = self.GENDER_KEYWORDS.get(gender, "person")
        age_keyword = self.AGE_KEYWORDS.get(age_range, "professional in their 30s")
        style_preset = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["professional"])

        # 프롬프트 조합
        prompt_parts = [
            f"Portrait of a {gender_keyword}, {age_keyword}",
            style_preset,
            "high quality, detailed face, clear features"
        ]

        # 추가 특징 포함
        if additional_traits:
            prompt_parts.extend(additional_traits)

        prompt = ", ".join(prompt_parts)

        # 네거티브 프롬프트 (생성하지 않을 요소)
        negative_prompt = "blurry, distorted, low quality, cartoon, anime"

        return prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _generate_with_banana(
        self,
        prompt: str,
        character_id: str
    ) -> Dict[str, Any]:
        """
        Nano Banana API를 사용하여 캐릭터 이미지 생성

        Args:
            prompt: 생성 프롬프트
            character_id: 캐릭터 ID

        Returns:
            생성 결과 (이미지 URL 포함)
        """
        span_context = logfire.span("banana.generate_character") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context:
            if not self.use_banana:
                raise ValueError("Banana API key not configured")

            # Banana API 엔드포인트 (실제 API 문서에 따라 수정 필요)
            endpoint = "https://api.banana.dev/generate"

            payload = {
                "prompt": prompt,
                "model": "stable-diffusion-xl",  # 또는 다른 모델
                "width": 512,
                "height": 512,
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }

            headers = {
                "Authorization": f"Bearer {self.banana_api_key}",
                "Content-Type": "application/json"
            }

            self.logger.info(f"Generating character image with Banana API: {character_id}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

            # API 응답에서 이미지 URL 추출 (API 스펙에 따라 수정 필요)
            image_url = result.get("image_url") or result.get("output", {}).get("image_url")

            if not image_url:
                raise ValueError("No image URL in Banana API response")

            self.logger.info(f"Character image generated successfully: {image_url}")

            return {
                "image_url": image_url,
                "generation_time": result.get("generation_time"),
                "model": result.get("model", "stable-diffusion-xl")
            }

    async def _generate_fallback_character(
        self,
        character_id: str,
        gender: str,
        age_range: str
    ) -> Dict[str, Any]:
        """
        Fallback 캐릭터 생성 (Banana API 사용 불가 시)

        실제 프로덕션에서는 Stable Diffusion 로컬 모델 또는
        다른 이미지 생성 API를 사용할 수 있습니다.

        Args:
            character_id: 캐릭터 ID
            gender: 성별
            age_range: 연령대

        Returns:
            Fallback 캐릭터 정보
        """
        self.logger.warning(f"Using fallback character generation for {character_id}")

        # 플레이스홀더 이미지 URL 생성
        # 실제로는 로컬 Stable Diffusion 또는 다른 서비스 사용
        fallback_url = (
            f"https://via.placeholder.com/512x512.png?"
            f"text=Character+{character_id[:8]}"
        )

        return {
            "image_url": fallback_url,
            "generation_time": 0.0,
            "model": "fallback",
            "is_fallback": True
        }

    async def generate_character_reference(
        self,
        persona_id: str,
        gender: str,
        age_range: str,
        style: str = "professional",
        additional_traits: Optional[List[str]] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        캐릭터 레퍼런스 이미지 생성

        Args:
            persona_id: 페르소나 ID
            gender: 성별 (male, female, neutral)
            age_range: 연령대 (20-30, 30-40, 40-50, 50-60)
            style: 스타일 (professional, casual, creative, formal)
            additional_traits: 추가 특징 리스트
            force_regenerate: 기존 캐릭터가 있어도 재생성 여부

        Returns:
            생성된 캐릭터 정보
        """
        span_context = logfire.span("character.generate_reference") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context:
            character_id = self._generate_character_id(persona_id)

            # 기존 캐릭터 확인 (재생성 옵션이 아닌 경우)
            if not force_regenerate:
                existing = await self._get_character_from_neo4j(character_id)
                if existing:
                    self.logger.info(f"Using existing character: {character_id}")
                    return existing

            # 프롬프트 생성
            prompt = self._build_character_prompt(
                gender=gender,
                age_range=age_range,
                style=style,
                additional_traits=additional_traits
            )

            # 이미지 생성
            try:
                if self.use_banana:
                    generation_result = await self._generate_with_banana(prompt, character_id)
                else:
                    generation_result = await self._generate_fallback_character(
                        character_id, gender, age_range
                    )
            except Exception as e:
                self.logger.error(f"Character generation failed: {e}")
                # Fallback으로 전환
                generation_result = await self._generate_fallback_character(
                    character_id, gender, age_range
                )

            # 캐릭터 데이터 구성
            character_data = {
                "character_id": character_id,
                "persona_id": persona_id,
                "reference_image_url": generation_result["image_url"],
                "prompt_template": prompt,
                "gender": gender,
                "age_range": age_range,
                "style": style,
                "additional_traits": additional_traits or [],
                "created_at": datetime.utcnow().isoformat(),
                "generation_metadata": {
                    "model": generation_result.get("model"),
                    "generation_time": generation_result.get("generation_time"),
                    "is_fallback": generation_result.get("is_fallback", False)
                }
            }

            # Neo4j에 저장
            await self.save_character_to_neo4j(persona_id, character_data)

            self.logger.info(f"Character reference created: {character_id}")

            return character_data

    async def get_or_create_character(
        self,
        persona_id: str,
        gender: str,
        age_range: str,
        style: str = "professional",
        additional_traits: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        기존 캐릭터 조회 또는 신규 생성

        같은 페르소나는 항상 같은 캐릭터를 사용하여 일관성 유지

        Args:
            persona_id: 페르소나 ID
            gender: 성별
            age_range: 연령대
            style: 스타일
            additional_traits: 추가 특징

        Returns:
            캐릭터 정보
        """
        span_context = logfire.span("character.get_or_create") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context:
            character_id = self._generate_character_id(persona_id)

            # 기존 캐릭터 조회
            existing = await self._get_character_from_neo4j(character_id)

            if existing:
                self.logger.info(f"Retrieved existing character: {character_id}")
                return existing

            # 없으면 새로 생성
            self.logger.info(f"Creating new character for persona: {persona_id}")
            return await self.generate_character_reference(
                persona_id=persona_id,
                gender=gender,
                age_range=age_range,
                style=style,
                additional_traits=additional_traits
            )

    def character_to_prompt(
        self,
        character_data: Dict[str, Any],
        scene_context: Optional[str] = None
    ) -> str:
        """
        캐릭터 데이터를 영상 생성용 프롬프트로 변환

        Args:
            character_data: 캐릭터 데이터
            scene_context: 장면 컨텍스트 (선택적)

        Returns:
            영상 생성용 프롬프트
        """
        prompt_template = character_data.get("prompt_template", "")

        if scene_context:
            # 장면 컨텍스트 포함
            prompt = f"{prompt_template}, {scene_context}"
        else:
            prompt = prompt_template

        return prompt

    async def _get_character_from_neo4j(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Neo4j에서 캐릭터 조회

        Args:
            character_id: 캐릭터 ID

        Returns:
            캐릭터 정보 (없으면 None)
        """
        query = """
        MATCH (c:Character {character_id: $character_id})
        OPTIONAL MATCH (p:Persona)-[:HAS_CHARACTER]->(c)
        RETURN c.character_id as character_id,
               c.reference_image_url as reference_image_url,
               c.prompt_template as prompt_template,
               c.gender as gender,
               c.age_range as age_range,
               c.style as style,
               c.additional_traits as additional_traits,
               c.created_at as created_at,
               c.generation_metadata as generation_metadata,
               p.persona_id as persona_id
        """

        try:
            results = self.neo4j.query(query, {"character_id": character_id})
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Failed to query character from Neo4j: {e}")
            return None

    async def save_character_to_neo4j(
        self,
        persona_id: str,
        character_data: Dict[str, Any]
    ) -> bool:
        """
        캐릭터 정보를 Neo4j에 저장

        Args:
            persona_id: 페르소나 ID
            character_data: 캐릭터 데이터

        Returns:
            저장 성공 여부
        """
        query = """
        MERGE (p:Persona {persona_id: $persona_id})
        MERGE (c:Character {character_id: $character_id})
        SET c.reference_image_url = $reference_image_url,
            c.prompt_template = $prompt_template,
            c.gender = $gender,
            c.age_range = $age_range,
            c.style = $style,
            c.additional_traits = $additional_traits,
            c.created_at = datetime($created_at),
            c.generation_metadata = $generation_metadata
        MERGE (p)-[:HAS_CHARACTER]->(c)
        RETURN c.character_id as character_id
        """

        params = {
            "persona_id": persona_id,
            "character_id": character_data["character_id"],
            "reference_image_url": character_data["reference_image_url"],
            "prompt_template": character_data["prompt_template"],
            "gender": character_data["gender"],
            "age_range": character_data["age_range"],
            "style": character_data["style"],
            "additional_traits": character_data["additional_traits"],
            "created_at": character_data["created_at"],
            "generation_metadata": character_data["generation_metadata"]
        }

        try:
            result = self.neo4j.query(query, params)
            success = len(result) > 0

            if success:
                self.logger.info(
                    f"Saved character {character_data['character_id']} to Neo4j"
                )
            else:
                self.logger.error("Failed to save character to Neo4j")

            return success
        except Exception as e:
            self.logger.error(f"Error saving character to Neo4j: {e}")
            return False

    async def get_persona_character(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        페르소나의 캐릭터 조회

        Args:
            persona_id: 페르소나 ID

        Returns:
            캐릭터 정보 (없으면 None)
        """
        query = """
        MATCH (p:Persona {persona_id: $persona_id})-[:HAS_CHARACTER]->(c:Character)
        RETURN c.character_id as character_id,
               c.reference_image_url as reference_image_url,
               c.prompt_template as prompt_template,
               c.gender as gender,
               c.age_range as age_range,
               c.style as style,
               c.additional_traits as additional_traits,
               c.created_at as created_at,
               c.generation_metadata as generation_metadata
        """

        try:
            results = self.neo4j.query(query, {"persona_id": persona_id})
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Failed to query persona character: {e}")
            return None

    async def delete_character(self, character_id: str) -> bool:
        """
        캐릭터 삭제

        Args:
            character_id: 캐릭터 ID

        Returns:
            삭제 성공 여부
        """
        query = """
        MATCH (c:Character {character_id: $character_id})
        DETACH DELETE c
        RETURN count(c) as deleted_count
        """

        try:
            result = self.neo4j.query(query, {"character_id": character_id})
            deleted_count = result[0]["deleted_count"] if result else 0

            if deleted_count > 0:
                self.logger.info(f"Deleted character: {character_id}")
                return True
            else:
                self.logger.warning(f"Character not found: {character_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting character: {e}")
            return False


# 싱글톤 인스턴스
_character_service_instance: Optional[CharacterService] = None


def get_character_service() -> CharacterService:
    """
    캐릭터 서비스 싱글톤 인스턴스

    Returns:
        CharacterService 인스턴스
    """
    global _character_service_instance
    if _character_service_instance is None:
        _character_service_instance = CharacterService()
    return _character_service_instance
