"""Continuity Agent - 스크립트 기반 콘티 자동 생성

LangGraph 기반 에이전트로 스크립트를 분석하여 씬별 콘티를 자동 생성합니다.

워크플로우:
1. 스크립트 분석 및 씬 분할
2. 각 씬의 카메라 워크 자동 제안
3. 리소스 자동 매핑
4. 사용자 수정 반영 (Hybrid 모드)
5. Neo4j에 콘티 저장
"""
from typing import Dict, Any, List, TypedDict, Optional
import logging
from datetime import datetime
from contextlib import nullcontext
import json
import re

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.services.neo4j_client import get_neo4j_client
from app.services.resource_manager import get_resource_manager, Resource

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class CameraWork:
    """카메라 워크 상수"""
    CLOSE_UP = "클로즈업 (CU)"
    MEDIUM_SHOT = "미디엄샷 (MS)"
    FULL_SHOT = "풀샷 (FS)"
    WIDE_SHOT = "와이드샷 (WS)"

    PAN_LEFT = "좌측 팬"
    PAN_RIGHT = "우측 팬"
    TILT_UP = "위로 틸트"
    TILT_DOWN = "아래로 틸트"

    ZOOM_IN = "줌인"
    ZOOM_OUT = "줌아웃"

    FIXED = "고정샷"


class Scene:
    """씬(장면) 모델"""
    def __init__(
        self,
        scene_number: int,
        start_time: float,
        end_time: float,
        script_text: str,
        camera_work: str,
        resource_ids: Optional[List[str]] = None,
        bgm_file: Optional[str] = None,
        sfx_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.scene_number = scene_number
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.script_text = script_text
        self.camera_work = camera_work
        self.resource_ids = resource_ids or []
        self.bgm_file = bgm_file
        self.sfx_file = sfx_file
        self.metadata = metadata or {}


class ContinuityState(TypedDict):
    """Continuity Agent 상태"""
    # 입력
    script: str
    campaign_name: str
    topic: str
    platform: str
    resources: Optional[List[Resource]]  # 구글 시트에서 로드된 리소스
    mode: str  # "auto" | "manual" | "hybrid"

    # 생성된 씬 목록
    scenes: Optional[List[Scene]]

    # 메타데이터
    total_duration: Optional[float]
    created_at: Optional[str]

    # 에러
    error: Optional[str]
    success: bool


class ContinuityAgent:
    """Continuity Agent - 콘티 자동 생성"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j_client = get_neo4j_client()
        self.resource_manager = get_resource_manager()

        # Claude (Anthropic) LLM 초기화
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.3,  # 콘티는 일관성이 중요하므로 낮게
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=4096
        )

        # LangGraph 워크플로우 구축
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구축"""
        workflow = StateGraph(ContinuityState)

        # 노드 추가
        workflow.add_node("analyze_script", self._analyze_script)
        workflow.add_node("divide_scenes", self._divide_scenes)
        workflow.add_node("suggest_camera", self._suggest_camera_work)
        workflow.add_node("map_resources", self._map_resources)
        workflow.add_node("save_continuity", self._save_continuity)

        # 엣지 정의
        workflow.set_entry_point("analyze_script")
        workflow.add_edge("analyze_script", "divide_scenes")
        workflow.add_edge("divide_scenes", "suggest_camera")
        workflow.add_edge("suggest_camera", "map_resources")
        workflow.add_edge("map_resources", "save_continuity")
        workflow.add_edge("save_continuity", END)

        return workflow.compile()

    async def _analyze_script(self, state: ContinuityState) -> ContinuityState:
        """1단계: 스크립트 분석"""
        span_context = logfire.span("continuity.analyze_script") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                script = state["script"]

                # 스크립트 길이 추정 (1분당 약 150-180 단어)
                char_count = len(script.replace(" ", ""))
                estimated_duration = (char_count / 5) * 0.5  # 한국어 기준 (초 단위)

                state["total_duration"] = estimated_duration

                self.logger.info(
                    f"Script analyzed: {char_count} chars, "
                    f"estimated {estimated_duration:.1f}s"
                )

                return state

            except Exception as e:
                self.logger.error(f"Script analysis failed: {e}")
                state["error"] = str(e)
                return state

    async def _divide_scenes(self, state: ContinuityState) -> ContinuityState:
        """2단계: 씬 자동 분할"""
        span_context = logfire.span("continuity.divide_scenes") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                script = state["script"]
                platform = state["platform"]

                # Claude에게 씬 분할 요청
                system_prompt = """당신은 전문 영상 연출가입니다.
주어진 스크립트를 씬(장면)으로 자동 분할하세요.

규칙:
1. 각 씬은 논리적으로 구분되는 내용 단위로 나눕니다
2. YouTube는 5-10개 씬, Instagram은 3-5개 씬, TikTok은 2-4개 씬을 권장합니다
3. 인트로, 메인, CTA는 반드시 별도 씬으로 구분합니다

출력 형식 (JSON):
{
  "scenes": [
    {
      "scene_number": 1,
      "type": "intro",
      "script_text": "안녕하세요...",
      "duration_seconds": 5
    },
    {
      "scene_number": 2,
      "type": "main",
      "script_text": "첫 번째로...",
      "duration_seconds": 15
    }
  ]
}
"""

                user_prompt = f"""다음 스크립트를 씬으로 분할하세요:

**플랫폼**: {platform}
**스크립트**:
{script}

JSON 형식으로만 응답하세요."""

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                response = await self.llm.ainvoke(messages)

                # JSON 파싱
                content = response.content
                # ```json 제거
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                scene_data = json.loads(content)

                # Scene 객체 생성
                scenes = []
                current_time = 0.0

                for scene_info in scene_data["scenes"]:
                    duration = scene_info["duration_seconds"]
                    scene = Scene(
                        scene_number=scene_info["scene_number"],
                        start_time=current_time,
                        end_time=current_time + duration,
                        script_text=scene_info["script_text"],
                        camera_work="",  # 다음 단계에서 설정
                        metadata={"type": scene_info.get("type", "main")}
                    )
                    scenes.append(scene)
                    current_time += duration

                state["scenes"] = scenes
                self.logger.info(f"Divided into {len(scenes)} scenes")

                return state

            except Exception as e:
                self.logger.error(f"Scene division failed: {e}")
                state["error"] = str(e)
                return state

    async def _suggest_camera_work(self, state: ContinuityState) -> ContinuityState:
        """3단계: 카메라 워크 자동 제안"""
        span_context = logfire.span("continuity.suggest_camera") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                scenes = state["scenes"]

                # Claude에게 각 씬의 카메라 워크 제안 요청
                system_prompt = """당신은 전문 촬영 감독입니다.
각 씬에 적합한 카메라 워크를 제안하세요.

카메라 워크 옵션:
- 클로즈업 (CU): 얼굴이나 제품 강조
- 미디엄샷 (MS): 상반신, 대화 장면
- 풀샷 (FS): 전신, 액션 장면
- 와이드샷 (WS): 전체 장면, 배경 강조

- 줌인: 강조 효과
- 줌아웃: 전체 맥락 보여주기
- 팬 (좌/우): 공간 탐색
- 틸트 (상/하): 위아래 이동

- 고정샷: 안정적인 설명

출력 형식 (JSON):
{
  "cameras": [
    "클로즈업 (CU)",
    "미디엄샷 (MS) + 줌인",
    "와이드샷 (WS)"
  ]
}
"""

                scene_descriptions = [
                    f"씬 {scene.scene_number}: {scene.metadata.get('type', 'main')} - {scene.script_text[:50]}..."
                    for scene in scenes
                ]

                user_prompt = f"""다음 씬들의 카메라 워크를 제안하세요:

{chr(10).join(scene_descriptions)}

JSON 형식으로만 응답하세요."""

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                response = await self.llm.ainvoke(messages)

                # JSON 파싱
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                camera_data = json.loads(content)

                # 씬에 카메라 워크 할당
                for idx, scene in enumerate(scenes):
                    if idx < len(camera_data["cameras"]):
                        scene.camera_work = camera_data["cameras"][idx]
                    else:
                        scene.camera_work = CameraWork.MEDIUM_SHOT  # 기본값

                self.logger.info("Camera work suggested for all scenes")

                return state

            except Exception as e:
                self.logger.error(f"Camera work suggestion failed: {e}")
                # 에러 발생 시 기본 카메라 워크 설정
                for scene in state["scenes"]:
                    if not scene.camera_work:
                        scene.camera_work = CameraWork.MEDIUM_SHOT
                return state

    async def _map_resources(self, state: ContinuityState) -> ContinuityState:
        """4단계: 리소스 자동 매핑 (구글 시트 '리소스' 탭 활용)"""
        span_context = logfire.span("continuity.map_resources") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                scenes = state["scenes"]
                resources = state.get("resources") or []

                if not resources:
                    self.logger.info("No resources provided - continuity will be created without resources")
                    # 모든 씬의 resource_ids를 빈 리스트로 설정
                    for scene in scenes:
                        if not hasattr(scene, 'resource_ids') or scene.resource_ids is None:
                            scene.resource_ids = []
                    return state

                # Claude에게 리소스 매핑 요청
                system_prompt = """당신은 영상 제작 전문가입니다.
각 씬에 적합한 리소스(이미지, 영상, PDF)를 매핑하세요.

리소스의 '용도' 필드를 참고하세요:
- "인트로": 인트로 씬에 사용
- "메인": 본론 씬에 사용
- "CTA": 행동 유도 씬에 사용
- "썸네일": 썸네일용 (씬에 매핑 X)

규칙:
1. 인트로 씬에는 용도가 "인트로"인 리소스 우선 배치
2. 메인 씬에는 용도가 "메인"인 리소스 분산 배치
3. CTA 씬에는 용도가 "CTA"인 리소스 배치
4. 같은 리소스를 여러 씬에 중복 사용 가능

출력 형식 (JSON):
{
  "mappings": [
    {"scene_number": 1, "resource_names": ["logo.png"]},
    {"scene_number": 2, "resource_names": ["slide1.pdf", "demo.mp4"]},
    {"scene_number": 3, "resource_names": ["cta_image.jpg"]}
  ]
}
"""

                scene_descriptions = [
                    {
                        "scene_number": scene.scene_number,
                        "type": scene.metadata.get("type", "main"),
                        "script_preview": scene.script_text[:100]
                    }
                    for scene in scenes
                ]

                # Resource 객체를 dict로 변환 (구글 시트 리소스 형식)
                resource_descriptions = []
                for res in resources:
                    if isinstance(res, dict):
                        # 이미 dict 형태 (구글 시트에서 온 경우)
                        resource_descriptions.append({
                            "name": res.get("리소스명", ""),
                            "type": res.get("리소스타입", ""),
                            "purpose": res.get("용도", "")
                        })
                    else:
                        # Resource 객체인 경우
                        resource_descriptions.append({
                            "name": res.name,
                            "type": res.type,
                            "purpose": res.metadata.get("purpose", "")
                        })

                user_prompt = f"""씬과 리소스를 매핑하세요:

**씬 목록**:
{json.dumps(scene_descriptions, ensure_ascii=False, indent=2)}

**리소스 목록**:
{json.dumps(resource_descriptions, ensure_ascii=False, indent=2)}

JSON 형식으로만 응답하세요."""

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                response = await self.llm.ainvoke(messages)

                # JSON 파싱
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                mapping_data = json.loads(content)

                # 씬에 리소스 이름 할당
                for mapping in mapping_data["mappings"]:
                    scene_num = mapping["scene_number"]
                    for scene in scenes:
                        if scene.scene_number == scene_num:
                            scene.resource_ids = mapping["resource_names"]
                            break

                self.logger.info("Resources mapped to scenes")

                return state

            except Exception as e:
                self.logger.error(f"Resource mapping failed: {e}")
                return state

    async def _save_continuity(self, state: ContinuityState) -> ContinuityState:
        """5단계: Neo4j에 콘티 저장"""
        span_context = logfire.span("continuity.save") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                scenes = state["scenes"]
                campaign_name = state["campaign_name"]
                topic = state["topic"]

                # Continuity 노드 생성
                continuity_id = f"cont_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                query = """
                MERGE (c:Campaign {name: $campaign_name})
                CREATE (cont:Continuity {
                    id: $continuity_id,
                    topic: $topic,
                    platform: $platform,
                    total_duration: $total_duration,
                    scene_count: $scene_count,
                    created_at: $created_at
                })
                CREATE (cont)-[:BELONGS_TO]->(c)
                RETURN cont
                """

                self.neo4j_client.query(
                    query,
                    campaign_name=campaign_name,
                    continuity_id=continuity_id,
                    topic=topic,
                    platform=state["platform"],
                    total_duration=state.get("total_duration"),
                    scene_count=len(scenes),
                    created_at=datetime.now().isoformat()
                )

                # 각 씬 저장
                for scene in scenes:
                    scene_query = """
                    MATCH (cont:Continuity {id: $continuity_id})
                    CREATE (s:Scene {
                        scene_number: $scene_number,
                        start_time: $start_time,
                        end_time: $end_time,
                        duration: $duration,
                        script_text: $script_text,
                        camera_work: $camera_work,
                        resource_ids: $resource_ids,
                        bgm_file: $bgm_file,
                        sfx_file: $sfx_file
                    })
                    CREATE (s)-[:PART_OF]->(cont)
                    RETURN s
                    """

                    self.neo4j_client.query(
                        scene_query,
                        continuity_id=continuity_id,
                        scene_number=scene.scene_number,
                        start_time=scene.start_time,
                        end_time=scene.end_time,
                        duration=scene.duration,
                        script_text=scene.script_text,
                        camera_work=scene.camera_work,
                        resource_ids=scene.resource_ids,
                        bgm_file=scene.bgm_file,
                        sfx_file=scene.sfx_file
                    )

                state["created_at"] = datetime.now().isoformat()
                state["success"] = True

                self.logger.info(f"Continuity saved: {continuity_id} with {len(scenes)} scenes")

                return state

            except Exception as e:
                self.logger.error(f"Failed to save continuity: {e}")
                state["error"] = str(e)
                state["success"] = False
                return state

    async def generate_continuity(
        self,
        script: str,
        campaign_name: str,
        topic: str,
        platform: str = "YouTube",
        resources: Optional[List[Resource]] = None,
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        콘티 생성 메인 함수

        Args:
            script: 스크립트 텍스트
            campaign_name: 캠페인명
            topic: 소제목
            platform: 플랫폼 (YouTube, Instagram, TikTok)
            resources: 리소스 목록 (옵션)
            mode: "auto" | "manual" | "hybrid"

        Returns:
            생성된 콘티 정보
        """
        span_context = logfire.span(
            "continuity.generate_main",
            campaign=campaign_name,
            topic=topic
        ) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            # 초기 상태 설정
            initial_state: ContinuityState = {
                "script": script,
                "campaign_name": campaign_name,
                "topic": topic,
                "platform": platform,
                "resources": resources,
                "mode": mode,
                "scenes": None,
                "total_duration": None,
                "created_at": None,
                "error": None,
                "success": False
            }

            # LangGraph 워크플로우 실행
            try:
                final_state = await self.workflow.ainvoke(initial_state)

                if final_state.get("error"):
                    raise RuntimeError(final_state["error"])

                # 씬 정보를 직렬화 가능한 형태로 변환
                scenes_data = [
                    {
                        "scene_number": scene.scene_number,
                        "start_time": scene.start_time,
                        "end_time": scene.end_time,
                        "duration": scene.duration,
                        "script_text": scene.script_text,
                        "camera_work": scene.camera_work,
                        "resource_ids": scene.resource_ids,
                        "bgm_file": scene.bgm_file,
                        "sfx_file": scene.sfx_file,
                        "metadata": scene.metadata
                    }
                    for scene in final_state["scenes"]
                ]

                return {
                    "success": True,
                    "campaign_name": campaign_name,
                    "topic": topic,
                    "platform": platform,
                    "total_duration": final_state.get("total_duration"),
                    "scene_count": len(scenes_data),
                    "scenes": scenes_data,
                    "created_at": final_state.get("created_at")
                }

            except Exception as e:
                self.logger.error(f"Continuity generation failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }


# 싱글톤 인스턴스
_continuity_agent_instance = None


def get_continuity_agent() -> ContinuityAgent:
    """Continuity Agent 싱글톤 인스턴스"""
    global _continuity_agent_instance
    if _continuity_agent_instance is None:
        _continuity_agent_instance = ContinuityAgent()
    return _continuity_agent_instance
