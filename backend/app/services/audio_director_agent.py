"""Audio Director Agent - 오디오 생성 및 검증

LangGraph 기반 에이전트로 스크립트를 받아 고품질 오디오를 생성합니다.

워크플로우:
1. 스크립트 로드
2. TTS 생성 (ElevenLabs)
3. STT 검증 (OpenAI Whisper)
4. 정확도 계산
5. Zero-Fault Loop (95% 미만 시 재생성, 최대 5회)
6. Neo4j에 오디오 메타데이터 저장

참고: 영상 생성은 app.services.director_agent.VideoDirectorAgent 사용
"""
from typing import Dict, Any, Optional, TypedDict
import logging
from datetime import datetime
from contextlib import nullcontext
from pathlib import Path
import os

from langgraph.graph import StateGraph, END
from difflib import SequenceMatcher

from app.core.config import get_settings
from app.services.tts_service import get_tts_service
from app.services.stt_service import get_stt_service
from app.services.neo4j_client import get_neo4j_client

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class DirectorState(TypedDict):
    """Director 에이전트 상태"""
    # 입력
    script: str
    campaign_name: str
    topic: str
    voice_id: Optional[str]  # 커스텀 음성 ID (옵션)
    language: str  # 기본값: "ko"

    # TTS 설정
    tts_model: Optional[str]
    stability: Optional[float]
    similarity_boost: Optional[float]

    # 생성된 오디오
    audio_bytes: Optional[bytes]
    audio_file_path: Optional[str]

    # STT 검증
    transcription: Optional[str]
    similarity_score: Optional[float]

    # Zero-Fault Loop
    attempt: int
    max_attempts: int
    accuracy_threshold: float

    # 메타데이터
    duration_seconds: Optional[float]
    created_at: Optional[str]

    # 에러
    error: Optional[str]
    success: bool


class DirectorAgent:
    """Director 에이전트 - 오디오 생성 및 검증"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tts_service = get_tts_service()
        self.stt_service = get_stt_service()
        self.neo4j_client = get_neo4j_client()

        # 오디오 저장 디렉토리
        self.audio_dir = Path("./generated_audio")
        self.audio_dir.mkdir(exist_ok=True)

        # LangGraph 워크플로우 구축
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구축"""
        workflow = StateGraph(DirectorState)

        # 노드 추가
        workflow.add_node("generate_tts", self._generate_tts)
        workflow.add_node("verify_stt", self._verify_stt)
        workflow.add_node("check_accuracy", self._check_accuracy)
        workflow.add_node("save_audio", self._save_audio)
        workflow.add_node("retry", self._retry)

        # 엣지 정의
        workflow.set_entry_point("generate_tts")
        workflow.add_edge("generate_tts", "verify_stt")
        workflow.add_edge("verify_stt", "check_accuracy")

        # 조건부 엣지: 정확도 체크 후 성공/재시도/실패
        workflow.add_conditional_edges(
            "check_accuracy",
            self._route_after_check,
            {
                "save": "save_audio",
                "retry": "retry",
                "end": END
            }
        )

        workflow.add_edge("retry", "generate_tts")
        workflow.add_edge("save_audio", END)

        return workflow.compile()

    def _route_after_check(self, state: DirectorState) -> str:
        """정확도 체크 후 라우팅"""
        if state.get("error"):
            return "end"

        if state["similarity_score"] >= state["accuracy_threshold"]:
            return "save"

        if state["attempt"] >= state["max_attempts"]:
            return "end"

        return "retry"

    async def _generate_tts(self, state: DirectorState) -> DirectorState:
        """1단계: TTS 생성"""
        span_context = logfire.span("director.generate_tts", attempt=state["attempt"]) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info(f"Generating TTS (attempt {state['attempt']}/{state['max_attempts']})")

                # TTS 생성
                audio_bytes = await self.tts_service.generate_audio(
                    text=state["script"],
                    voice_id=state.get("voice_id"),
                    model=state.get("tts_model", "tts-1")
                )

                state["audio_bytes"] = audio_bytes
                self.logger.info(f"TTS generated: {len(audio_bytes)} bytes")

                return state

            except Exception as e:
                self.logger.error(f"TTS generation failed: {e}")
                state["error"] = f"TTS 생성 실패: {str(e)}"
                state["success"] = False
                return state

    async def _verify_stt(self, state: DirectorState) -> DirectorState:
        """2단계: STT 검증"""
        span_context = logfire.span("director.verify_stt") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                if not state.get("audio_bytes"):
                    raise ValueError("No audio to verify")

                self.logger.info("Transcribing audio with Whisper STT")

                # STT 변환
                transcription = await self.stt_service.transcribe(
                    audio_bytes=state["audio_bytes"],
                    language=state.get("language", "ko")
                )

                state["transcription"] = transcription
                self.logger.info(f"STT result: {transcription[:100]}...")

                return state

            except Exception as e:
                self.logger.error(f"STT verification failed: {e}")
                state["error"] = f"STT 검증 실패: {str(e)}"
                state["success"] = False
                return state

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산 (0.0 ~ 1.0)"""
        # 공백 제거 후 비교
        text1_clean = text1.replace(" ", "").replace("\n", "").lower()
        text2_clean = text2.replace(" ", "").replace("\n", "").lower()

        return SequenceMatcher(None, text1_clean, text2_clean).ratio()

    async def _check_accuracy(self, state: DirectorState) -> DirectorState:
        """3단계: 정확도 계산"""
        span_context = logfire.span("director.check_accuracy") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                original = state["script"]
                transcribed = state.get("transcription", "")

                if not transcribed:
                    raise ValueError("No transcription to check")

                # 유사도 계산
                similarity = self._calculate_similarity(original, transcribed)
                state["similarity_score"] = similarity

                self.logger.info(
                    f"Similarity score: {similarity:.2%} "
                    f"(threshold: {state['accuracy_threshold']:.2%})"
                )

                if similarity >= state["accuracy_threshold"]:
                    self.logger.info("✓ Accuracy check passed!")
                    state["success"] = True
                else:
                    self.logger.warning(
                        f"✗ Accuracy below threshold. "
                        f"Attempt {state['attempt']}/{state['max_attempts']}"
                    )

                return state

            except Exception as e:
                self.logger.error(f"Accuracy check failed: {e}")
                state["error"] = f"정확도 계산 실패: {str(e)}"
                state["success"] = False
                return state

    async def _retry(self, state: DirectorState) -> DirectorState:
        """재시도 준비"""
        state["attempt"] += 1
        self.logger.info(f"Retrying TTS generation (attempt {state['attempt']}/{state['max_attempts']})")
        return state

    async def _save_audio(self, state: DirectorState) -> DirectorState:
        """4단계: 오디오 저장"""
        span_context = logfire.span("director.save_audio") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                # 파일명 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_topic = state["topic"].replace(" ", "_").replace("/", "_")[:50]
                filename = f"{timestamp}_{safe_topic}.mp3"
                file_path = self.audio_dir / filename

                # 파일 저장
                with open(file_path, "wb") as f:
                    f.write(state["audio_bytes"])

                state["audio_file_path"] = str(file_path)
                state["created_at"] = datetime.now().isoformat()

                self.logger.info(f"Audio saved: {file_path}")

                # Neo4j에 메타데이터 저장
                await self._save_to_neo4j(state)

                return state

            except Exception as e:
                self.logger.error(f"Failed to save audio: {e}")
                state["error"] = f"오디오 저장 실패: {str(e)}"
                state["success"] = False
                return state

    async def _save_to_neo4j(self, state: DirectorState):
        """Neo4j에 오디오 메타데이터 저장"""
        try:
            query = """
            MERGE (c:Campaign {name: $campaign_name})
            CREATE (a:Audio {
                topic: $topic,
                file_path: $file_path,
                script: $script,
                transcription: $transcription,
                similarity_score: $similarity_score,
                attempts: $attempts,
                language: $language,
                created_at: $created_at
            })
            CREATE (a)-[:BELONGS_TO]->(c)
            RETURN a
            """

            self.neo4j_client.query(
                query,
                campaign_name=state["campaign_name"],
                topic=state["topic"],
                file_path=state["audio_file_path"],
                script=state["script"],
                transcription=state.get("transcription"),
                similarity_score=state.get("similarity_score"),
                attempts=state["attempt"],
                language=state.get("language", "ko"),
                created_at=state.get("created_at")
            )

            self.logger.info(f"Audio metadata saved to Neo4j: {state['topic']}")

        except Exception as e:
            self.logger.error(f"Failed to save to Neo4j: {e}")

    async def generate_audio(
        self,
        script: str,
        campaign_name: str,
        topic: str,
        voice_id: Optional[str] = None,
        language: str = "ko",
        accuracy_threshold: float = 0.95,
        max_attempts: int = 5
    ) -> Dict[str, Any]:
        """
        오디오 생성 메인 함수

        Args:
            script: 스크립트 텍스트
            campaign_name: 캠페인명
            topic: 소제목
            voice_id: 커스텀 음성 ID (옵션)
            language: 언어 코드 (기본값: "ko")
            accuracy_threshold: 정확도 임계값 (기본값: 0.95)
            max_attempts: 최대 시도 횟수 (기본값: 5)

        Returns:
            생성된 오디오 정보
        """
        span_context = logfire.span(
            "director.generate_audio_main",
            campaign=campaign_name,
            topic=topic
        ) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            # 초기 상태 설정
            initial_state: DirectorState = {
                "script": script,
                "campaign_name": campaign_name,
                "topic": topic,
                "voice_id": voice_id,
                "language": language,
                "tts_model": "tts-1",  # OpenAI TTS 기본 모델
                "stability": None,
                "similarity_boost": None,
                "audio_bytes": None,
                "audio_file_path": None,
                "transcription": None,
                "similarity_score": None,
                "attempt": 1,
                "max_attempts": max_attempts,
                "accuracy_threshold": accuracy_threshold,
                "duration_seconds": None,
                "created_at": None,
                "error": None,
                "success": False
            }

            # LangGraph 워크플로우 실행
            try:
                final_state = await self.workflow.ainvoke(initial_state)

                if final_state.get("error"):
                    return {
                        "success": False,
                        "error": final_state["error"],
                        "attempts": final_state["attempt"]
                    }

                if not final_state.get("success"):
                    return {
                        "success": False,
                        "error": f"정확도 임계값 {accuracy_threshold:.0%}에 도달하지 못했습니다",
                        "similarity_score": final_state.get("similarity_score"),
                        "attempts": final_state["attempt"],
                        "transcription": final_state.get("transcription")
                    }

                return {
                    "success": True,
                    "campaign_name": campaign_name,
                    "topic": topic,
                    "audio_file_path": final_state["audio_file_path"],
                    "script": script,
                    "transcription": final_state.get("transcription"),
                    "similarity_score": final_state.get("similarity_score"),
                    "attempts": final_state["attempt"],
                    "language": language,
                    "created_at": final_state.get("created_at")
                }

            except Exception as e:
                self.logger.error(f"Director workflow failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }


# 싱글톤 인스턴스
_director_agent_instance = None


def get_director_agent() -> DirectorAgent:
    """Director 에이전트 싱글톤 인스턴스"""
    global _director_agent_instance
    if _director_agent_instance is None:
        _director_agent_instance = DirectorAgent()
    return _director_agent_instance
