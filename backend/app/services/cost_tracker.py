"""API 비용 추적 및 토큰 계산 시스템

모든 외부 API 호출의 비용을 실시간으로 추적하고 집계합니다.

지원 API:
- OpenAI (GPT-4, Whisper, TTS)
- Anthropic (Claude)
- ElevenLabs (TTS, Voice Cloning)
- Google Veo (영상 생성)
- HeyGen (립싱크)
- Nano Banana (캐릭터 생성)
- Cloudinary (미디어 최적화)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging

from app.services.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


class APIProvider(str, Enum):
    """지원 API 제공자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ELEVENLABS = "elevenlabs"
    GOOGLE_VEO = "google_veo"
    HEYGEN = "heygen"
    NANO_BANANA = "nano_banana"
    CLOUDINARY = "cloudinary"


class APIService(str, Enum):
    """API 서비스 종류"""
    # OpenAI
    GPT4 = "gpt4"
    GPT4_TURBO = "gpt4_turbo"
    WHISPER = "whisper"
    TTS = "openai_tts"

    # Anthropic
    CLAUDE_OPUS = "claude_opus"
    CLAUDE_SONNET = "claude_sonnet"
    CLAUDE_HAIKU = "claude_haiku"

    # ElevenLabs
    ELEVENLABS_TTS = "elevenlabs_tts"
    VOICE_CLONING = "voice_cloning"

    # Google
    VEO_VIDEO = "veo_video"

    # HeyGen
    HEYGEN_LIPSYNC = "heygen_lipsync"

    # Nano Banana
    CHARACTER_GEN = "character_generation"

    # Cloudinary
    MEDIA_TRANSFORM = "media_transform"


# 가격표 (2026년 2월 기준)
PRICING = {
    # OpenAI
    APIService.GPT4: {
        "input_per_1k_tokens": 0.03,  # $0.03 / 1K tokens
        "output_per_1k_tokens": 0.06,
    },
    APIService.GPT4_TURBO: {
        "input_per_1k_tokens": 0.01,
        "output_per_1k_tokens": 0.03,
    },
    APIService.WHISPER: {
        "per_minute": 0.006,  # $0.006 / minute
    },
    APIService.TTS: {
        "per_1k_chars": 0.015,  # $0.015 / 1K characters
    },

    # Anthropic
    APIService.CLAUDE_OPUS: {
        "input_per_1k_tokens": 0.015,
        "output_per_1k_tokens": 0.075,
    },
    APIService.CLAUDE_SONNET: {
        "input_per_1k_tokens": 0.003,
        "output_per_1k_tokens": 0.015,
    },
    APIService.CLAUDE_HAIKU: {
        "input_per_1k_tokens": 0.00025,
        "output_per_1k_tokens": 0.00125,
    },

    # ElevenLabs
    APIService.ELEVENLABS_TTS: {
        "per_1k_chars": 0.30,  # $0.30 / 1K characters
    },
    APIService.VOICE_CLONING: {
        "per_voice": 10.00,  # $10 per voice clone
    },

    # Google Veo
    APIService.VEO_VIDEO: {
        "per_second": 0.10,  # $0.10 / second of video
    },

    # HeyGen
    APIService.HEYGEN_LIPSYNC: {
        "per_second": 0.05,  # $0.05 / second
    },

    # Nano Banana
    APIService.CHARACTER_GEN: {
        "per_image": 0.05,  # $0.05 / image
    },

    # Cloudinary
    APIService.MEDIA_TRANSFORM: {
        "per_1k_transforms": 0.10,  # $0.10 / 1K transformations
    },
}


@dataclass
class CostRecord:
    """비용 기록"""
    record_id: str
    provider: APIProvider
    service: APIService

    # 사용량
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    characters: Optional[int] = None
    duration_seconds: Optional[float] = None
    count: Optional[int] = None  # 이미지 개수, 변환 횟수 등

    # 비용
    cost_usd: float = 0.0

    # 메타데이터
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = None

    # 추가 정보
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CostTracker:
    """API 비용 추적 시스템"""

    def __init__(self):
        self.neo4j = get_neo4j_client()
        self.logger = logging.getLogger(__name__)
        self._initialize_neo4j_schema()

    def _initialize_neo4j_schema(self):
        """Neo4j 스키마 초기화"""
        try:
            with self.neo4j.driver.session() as session:
                # CostRecord 노드 인덱스
                session.run("""
                    CREATE INDEX cost_record_timestamp IF NOT EXISTS
                    FOR (c:CostRecord) ON (c.timestamp)
                """)

                session.run("""
                    CREATE INDEX cost_record_provider IF NOT EXISTS
                    FOR (c:CostRecord) ON (c.provider)
                """)

                session.run("""
                    CREATE INDEX cost_record_user IF NOT EXISTS
                    FOR (c:CostRecord) ON (c.user_id)
                """)

                self.logger.info("CostTracker Neo4j schema initialized")

        except Exception as e:
            self.logger.warning(f"Failed to initialize Neo4j schema: {e}")

    def calculate_openai_cost(
        self,
        service: APIService,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """OpenAI API 비용 계산"""
        pricing = PRICING[service]
        input_cost = (input_tokens / 1000) * pricing["input_per_1k_tokens"]
        output_cost = (output_tokens / 1000) * pricing["output_per_1k_tokens"]
        return round(input_cost + output_cost, 6)

    def calculate_whisper_cost(
        self,
        duration_seconds: float
    ) -> float:
        """Whisper API 비용 계산"""
        minutes = duration_seconds / 60
        pricing = PRICING[APIService.WHISPER]
        return round(minutes * pricing["per_minute"], 6)

    def calculate_tts_cost(
        self,
        service: APIService,
        characters: int
    ) -> float:
        """TTS API 비용 계산 (OpenAI, ElevenLabs)"""
        pricing = PRICING[service]
        if "per_1k_chars" in pricing:
            return round((characters / 1000) * pricing["per_1k_chars"], 6)
        return 0.0

    def calculate_video_cost(
        self,
        service: APIService,
        duration_seconds: float
    ) -> float:
        """영상 생성 API 비용 계산 (Veo, HeyGen)"""
        pricing = PRICING[service]
        return round(duration_seconds * pricing["per_second"], 4)

    def calculate_image_cost(
        self,
        service: APIService,
        count: int = 1
    ) -> float:
        """이미지 생성 API 비용 계산"""
        pricing = PRICING[service]
        if "per_image" in pricing:
            return round(count * pricing["per_image"], 4)
        return 0.0

    def record_openai_usage(
        self,
        service: APIService,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """OpenAI API 사용 기록"""
        cost = self.calculate_openai_cost(service, input_tokens, output_tokens)

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=APIProvider.OPENAI,
            service=service,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] OpenAI {service.value}: "
            f"{input_tokens}+{output_tokens} tokens = ${cost:.6f}"
        )

        return record

    def record_anthropic_usage(
        self,
        service: APIService,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """Anthropic API 사용 기록"""
        cost = self.calculate_openai_cost(service, input_tokens, output_tokens)

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=APIProvider.ANTHROPIC,
            service=service,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] Anthropic {service.value}: "
            f"{input_tokens}+{output_tokens} tokens = ${cost:.6f}"
        )

        return record

    def record_whisper_usage(
        self,
        duration_seconds: float,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """Whisper API 사용 기록"""
        cost = self.calculate_whisper_cost(duration_seconds)

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=APIProvider.OPENAI,
            service=APIService.WHISPER,
            duration_seconds=duration_seconds,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] Whisper: {duration_seconds:.1f}s = ${cost:.6f}"
        )

        return record

    def record_tts_usage(
        self,
        provider: APIProvider,
        service: APIService,
        characters: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """TTS API 사용 기록 (OpenAI, ElevenLabs)"""
        cost = self.calculate_tts_cost(service, characters)

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=provider,
            service=service,
            characters=characters,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] {provider.value} TTS: {characters} chars = ${cost:.6f}"
        )

        return record

    def record_video_generation_usage(
        self,
        service: APIService,
        duration_seconds: float,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """영상 생성 API 사용 기록 (Veo, HeyGen)"""
        cost = self.calculate_video_cost(service, duration_seconds)

        provider = (
            APIProvider.GOOGLE_VEO if service == APIService.VEO_VIDEO
            else APIProvider.HEYGEN
        )

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=provider,
            service=service,
            duration_seconds=duration_seconds,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] {provider.value}: {duration_seconds}s video = ${cost:.4f}"
        )

        return record

    def record_character_generation_usage(
        self,
        count: int = 1,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """캐릭터 생성 API 사용 기록"""
        cost = self.calculate_image_cost(APIService.CHARACTER_GEN, count)

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=APIProvider.NANO_BANANA,
            service=APIService.CHARACTER_GEN,
            count=count,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] Character Generation: {count} image(s) = ${cost:.4f}"
        )

        return record

    def record_cloudinary_usage(
        self,
        transformation_count: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostRecord:
        """
        Cloudinary 변환 사용 기록

        Cloudinary 무료 Tier: 월 25,000회 변환
        초과 시: $0.10 / 1,000 변환
        """
        # 무료 tier 고려한 비용 계산
        # Note: 실제로는 월별 누적을 추적해야 하지만, 여기서는 단순화
        pricing = PRICING[APIService.MEDIA_TRANSFORM]
        cost = (transformation_count / 1000) * pricing["per_1k_transforms"]

        record = CostRecord(
            record_id=self._generate_record_id(),
            provider=APIProvider.CLOUDINARY,
            service=APIService.MEDIA_TRANSFORM,
            count=transformation_count,
            cost_usd=cost,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )

        self._save_to_neo4j(record)
        self._log_to_logfire(record)

        self.logger.info(
            f"[Cost] Cloudinary: {transformation_count} transformations = ${cost:.4f}"
        )

        return record

    def get_total_cost(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[APIProvider] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """총 비용 조회"""
        try:
            with self.neo4j.driver.session() as session:
                # 쿼리 조건 구성
                conditions = []
                params = {}

                if user_id:
                    conditions.append("c.user_id = $user_id")
                    params["user_id"] = user_id

                if project_id:
                    conditions.append("c.project_id = $project_id")
                    params["project_id"] = project_id

                if provider:
                    conditions.append("c.provider = $provider")
                    params["provider"] = provider.value

                if start_date:
                    conditions.append("c.timestamp >= $start_date")
                    params["start_date"] = start_date.isoformat()

                if end_date:
                    conditions.append("c.timestamp <= $end_date")
                    params["end_date"] = end_date.isoformat()

                where_clause = (
                    f"WHERE {' AND '.join(conditions)}"
                    if conditions else ""
                )

                query = f"""
                    MATCH (c:CostRecord)
                    {where_clause}
                    RETURN
                        SUM(c.cost_usd) as total_cost,
                        COUNT(c) as record_count,
                        c.provider as provider,
                        SUM(c.cost_usd) as provider_cost
                    ORDER BY provider_cost DESC
                """

                result = session.run(query, params)
                records = list(result)

                if not records:
                    return {
                        "total_cost": 0.0,
                        "record_count": 0,
                        "by_provider": {}
                    }

                total = sum(r["total_cost"] or 0 for r in records)
                count = sum(r["record_count"] or 0 for r in records)

                by_provider = {
                    r["provider"]: round(r["provider_cost"] or 0, 4)
                    for r in records
                    if r["provider"]
                }

                return {
                    "total_cost": round(total, 4),
                    "record_count": count,
                    "by_provider": by_provider
                }

        except Exception as e:
            self.logger.error(f"Failed to get total cost: {e}")
            return {
                "total_cost": 0.0,
                "record_count": 0,
                "by_provider": {},
                "error": str(e)
            }

    def get_daily_cost_trend(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """일별 비용 트렌드 조회"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            with self.neo4j.driver.session() as session:
                conditions = [
                    "c.timestamp >= $start_date",
                    "c.timestamp <= $end_date"
                ]
                params = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }

                if user_id:
                    conditions.append("c.user_id = $user_id")
                    params["user_id"] = user_id

                if project_id:
                    conditions.append("c.project_id = $project_id")
                    params["project_id"] = project_id

                where_clause = f"WHERE {' AND '.join(conditions)}"

                query = f"""
                    MATCH (c:CostRecord)
                    {where_clause}
                    WITH
                        date(c.timestamp) as date,
                        c.provider as provider,
                        SUM(c.cost_usd) as daily_cost
                    RETURN
                        date,
                        provider,
                        daily_cost
                    ORDER BY date DESC, daily_cost DESC
                """

                result = session.run(query, params)
                records = list(result)

                # 날짜별로 그룹화
                trend = {}
                for r in records:
                    date_str = str(r["date"])
                    if date_str not in trend:
                        trend[date_str] = {
                            "date": date_str,
                            "total_cost": 0.0,
                            "by_provider": {}
                        }

                    provider = r["provider"]
                    cost = r["daily_cost"] or 0

                    trend[date_str]["total_cost"] += cost
                    trend[date_str]["by_provider"][provider] = round(cost, 4)

                # 리스트로 변환 및 total_cost 반올림
                result_list = []
                for date_str, data in sorted(trend.items(), reverse=True):
                    data["total_cost"] = round(data["total_cost"], 4)
                    result_list.append(data)

                return result_list

        except Exception as e:
            self.logger.error(f"Failed to get daily cost trend: {e}")
            return []

    def estimate_project_cost(
        self,
        script_length: int,  # 글자 수
        video_duration: int,  # 영상 길이 (초)
        platform: str = "YouTube"
    ) -> Dict[str, float]:
        """프로젝트 예상 비용 계산"""
        estimates = {}

        # 1. Writer Agent (Claude Haiku)
        input_tokens = script_length * 2  # 대략 2글자 = 1토큰
        output_tokens = script_length * 3  # 스크립트 생성
        estimates["writer_agent"] = self.calculate_openai_cost(
            APIService.CLAUDE_HAIKU,
            input_tokens,
            output_tokens
        )

        # 2. TTS (ElevenLabs)
        estimates["tts"] = self.calculate_tts_cost(
            APIService.ELEVENLABS_TTS,
            script_length
        )

        # 3. STT (Whisper)
        estimates["stt"] = self.calculate_whisper_cost(video_duration)

        # 4. 캐릭터 생성 (Nano Banana)
        estimates["character"] = self.calculate_image_cost(
            APIService.CHARACTER_GEN,
            1
        )

        # 5. 영상 생성 (Google Veo)
        estimates["video_generation"] = self.calculate_video_cost(
            APIService.VEO_VIDEO,
            video_duration
        )

        # 6. 립싱크 (HeyGen)
        estimates["lipsync"] = self.calculate_video_cost(
            APIService.HEYGEN_LIPSYNC,
            video_duration
        )

        # 총 비용
        estimates["total"] = round(sum(estimates.values()), 4)

        return estimates

    def _generate_record_id(self) -> str:
        """레코드 ID 생성"""
        import uuid
        return f"cost_{uuid.uuid4().hex[:12]}"

    def _save_to_neo4j(self, record: CostRecord):
        """Neo4j에 비용 기록 저장"""
        try:
            with self.neo4j.driver.session() as session:
                query = """
                    CREATE (c:CostRecord {
                        record_id: $record_id,
                        provider: $provider,
                        service: $service,
                        input_tokens: $input_tokens,
                        output_tokens: $output_tokens,
                        characters: $characters,
                        duration_seconds: $duration_seconds,
                        count: $count,
                        cost_usd: $cost_usd,
                        user_id: $user_id,
                        project_id: $project_id,
                        task_id: $task_id,
                        timestamp: $timestamp,
                        metadata: $metadata
                    })
                """

                params = {
                    "record_id": record.record_id,
                    "provider": record.provider.value,
                    "service": record.service.value,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "characters": record.characters,
                    "duration_seconds": record.duration_seconds,
                    "count": record.count,
                    "cost_usd": record.cost_usd,
                    "user_id": record.user_id,
                    "project_id": record.project_id,
                    "task_id": record.task_id,
                    "timestamp": record.timestamp.isoformat(),
                    "metadata": record.metadata
                }

                session.run(query, params)

        except Exception as e:
            self.logger.error(f"Failed to save cost record to Neo4j: {e}")

    def _log_to_logfire(self, record: CostRecord):
        """Logfire에 비용 기록"""
        if not LOGFIRE_AVAILABLE:
            return

        try:
            logfire.info(
                "API Cost Recorded",
                provider=record.provider.value,
                service=record.service.value,
                cost_usd=record.cost_usd,
                user_id=record.user_id,
                project_id=record.project_id,
                task_id=record.task_id
            )
        except Exception as e:
            self.logger.warning(f"Failed to log to Logfire: {e}")


# 싱글톤 인스턴스
_cost_tracker_instance: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """CostTracker 싱글톤 인스턴스 반환"""
    global _cost_tracker_instance

    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker()

    return _cost_tracker_instance
