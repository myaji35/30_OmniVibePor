"""Writer 에이전트 - 스크립트 자동 생성

LangGraph 기반 에이전트로 구글 시트의 전략과 소제목을 바탕으로
플랫폼별 최적화된 스크립트를 자동 생성합니다.

워크플로우:
1. 전략 로드 (구글 시트)
2. 소제목 분석
3. Neo4j에서 과거 스타일 검색
4. Claude (Anthropic)로 고품질 초안 생성
5. 플랫폼별 최적화 (YouTube, Instagram, TikTok)
"""
from typing import Dict, Any, List, TypedDict, Optional
import logging
from datetime import datetime
from contextlib import nullcontext

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.services.google_sheets_service import get_sheets_service
from app.services.neo4j_client import get_neo4j_client
from app.services.duration_calculator import get_duration_calculator, Language

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class WriterState(TypedDict):
    """Writer 에이전트 상태"""
    # 입력
    spreadsheet_id: str
    campaign_name: str
    topic: str  # 소제목
    platform: str  # YouTube, Instagram, TikTok
    target_duration: Optional[int]  # 목표 영상 길이 (초)

    # 전략 데이터
    strategy: Optional[Dict[str, Any]]
    target_audience: Optional[str]
    tone: Optional[str]

    # 과거 데이터
    past_scripts: Optional[List[Dict[str, Any]]]

    # 생성된 스크립트
    script: Optional[str]
    hook: Optional[str]  # 첫 3초 훅
    cta: Optional[str]   # Call-to-Action

    # 메타데이터
    estimated_duration: Optional[int]  # 예상 영상 길이 (초)
    created_at: Optional[str]

    # 에러
    error: Optional[str]


class WriterAgent:
    """Writer 에이전트 - 스크립트 자동 생성"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sheets_service = get_sheets_service()
        self.neo4j_client = get_neo4j_client()

        # Claude (Anthropic) LLM 초기화
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",  # Claude 3 Haiku (빠르고 경제적)
            temperature=0.7,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=4096
        )

        # LangGraph 워크플로우 구축
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구축"""
        workflow = StateGraph(WriterState)

        # 노드 추가
        workflow.add_node("load_strategy", self._load_strategy)
        workflow.add_node("search_past_scripts", self._search_past_scripts)
        workflow.add_node("generate_script", self._generate_script)
        workflow.add_node("optimize_platform", self._optimize_for_platform)
        workflow.add_node("save_to_memory", self._save_to_memory)

        # 엣지 정의
        workflow.set_entry_point("load_strategy")
        workflow.add_edge("load_strategy", "search_past_scripts")
        workflow.add_edge("search_past_scripts", "generate_script")
        workflow.add_edge("generate_script", "optimize_platform")
        workflow.add_edge("optimize_platform", "save_to_memory")
        workflow.add_edge("save_to_memory", END)

        return workflow.compile()

    async def _load_strategy(self, state: WriterState) -> WriterState:
        """1단계: 구글 시트에서 전략 로드"""
        span_context = logfire.span("writer.load_strategy") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                # 전략 시트 읽기
                strategy = await self.sheets_service.read_strategy_sheet(
                    state["spreadsheet_id"]
                )

                state["strategy"] = strategy
                state["target_audience"] = strategy.get("타겟", "일반 대중")
                state["tone"] = strategy.get("톤앤매너", "전문적이고 신뢰감 있는")

                self.logger.info(f"Loaded strategy for campaign: {state['campaign_name']}")
                return state

            except Exception as e:
                self.logger.error(f"Failed to load strategy: {e}")
                state["error"] = str(e)
                return state

    async def _search_past_scripts(self, state: WriterState) -> WriterState:
        """2단계: Neo4j GraphRAG에서 고성과 스크립트 검색 (Few-shot Learning)"""
        span_context = logfire.span("writer.search_past") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                # ✅ Week 1: Neo4j Memory 통합
                # 플랫폼 + 톤 기반으로 고성과 스크립트 검색
                platform = state["platform"]
                tone = state.get("tone", "professional")

                # tone을 간단한 키워드로 매핑
                tone_mapping = {
                    "전문적이고 신뢰감 있는": "professional",
                    "활기차고 에너제틱한": "energetic",
                    "친근하고 편안한": "casual",
                    "교육적이고 정보 전달": "educational",
                    "재미있고 유쾌한": "playful",
                    "영감을 주는": "inspiring"
                }
                simple_tone = tone_mapping.get(tone, "professional")

                # Neo4j에서 유사한 고성과 스크립트 검색
                similar_scripts = self.neo4j_client.search_similar_scripts(
                    platform=platform,
                    tone=simple_tone,
                    limit=3,
                    min_performance=8.0  # 8.0점 이상만
                )

                # 검색 결과 변환
                state["past_scripts"] = [
                    {
                        "id": script["id"],
                        "content": script["content"],
                        "performance_score": script["performance_score"],
                        "views": script["views"],
                        "ctr": script["ctr"]
                    }
                    for script in similar_scripts
                ]

                self.logger.info(
                    f"✅ Found {len(similar_scripts)} high-performance scripts "
                    f"(platform={platform}, tone={simple_tone})"
                )
                return state

            except Exception as e:
                self.logger.warning(f"⚠️ Failed to search past scripts: {e}")
                state["past_scripts"] = []
                return state

    async def _generate_script(self, state: WriterState) -> WriterState:
        """3단계: Claude (Anthropic)로 고품질 스크립트 초안 생성"""
        span_context = logfire.span("writer.generate_script") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                # 시스템 프롬프트 구성
                system_prompt = f"""당신은 전문 콘텐츠 작가입니다.

**타겟 오디언스**: {state['target_audience']}
**톤앤매너**: {state['tone']}
**플랫폼**: {state['platform']}

다음 원칙을 따라주세요:
1. 첫 3초 안에 시청자의 관심을 끌어야 합니다 (Hook)
2. 타겟 오디언스가 이해하기 쉬운 언어를 사용하세요
3. 지정된 톤앤매너를 일관되게 유지하세요
4. 플랫폼 특성에 맞는 길이와 구조를 유지하세요
"""

                # ✅ Week 1: Few-shot Learning - 과거 고성과 스크립트 참고
                past_context = ""
                if state.get("past_scripts") and len(state["past_scripts"]) > 0:
                    past_context = "\n\n**🏆 과거 고성과 스크립트 (참고용 - 이 스타일을 학습하여 유사하게 작성):**\n"
                    for idx, script in enumerate(state["past_scripts"], 1):
                        content_preview = script.get('content', '')[:200]  # 처음 200자만
                        score = script.get('performance_score', 0)
                        views = script.get('views', 0)
                        ctr = script.get('ctr', 0) * 100

                        past_context += f"\n### 예시 {idx} (성과: {score}/10, 조회수: {views:,}, CTR: {ctr:.1f}%)\n"
                        past_context += f"{content_preview}...\n"

                # 목표 분량 계산
                target_duration = state.get("target_duration") or 180
                duration_calc = get_duration_calculator(Language.KO)
                word_count_info = duration_calc.estimate_for_target_duration(target_duration)

                target_words = word_count_info['target_words']
                min_words = word_count_info['min_words']
                max_words = word_count_info['max_words']

                # 사용자 프롬프트
                user_prompt = f"""다음 주제로 {state['platform']} 영상 스크립트를 작성해주세요:

**주제**: {state['topic']}
**캠페인**: {state['campaign_name']}
**목표 영상 길이**: {target_duration}초
**필요 글자수**: {target_words}자 (범위: {min_words}~{max_words}자)
{past_context}

다음 형식으로 작성해주세요:

### 훅 (첫 3초)
[강력한 질문이나 놀라운 사실로 시작]

### 본문
[핵심 메시지를 3-5개 포인트로 전달]
[목표 글자수를 충족하도록 충분히 작성하되, 너무 길어지지 않도록 주의]

### CTA (행동 유도)
[시청자에게 구체적인 행동을 요청]

---
**예상 영상 길이**: {target_duration}초
**실제 글자수**: [작성한 총 글자수]
"""

                # LLM 호출
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                response = await self.llm.ainvoke(messages)
                script_content = response.content

                # 스크립트 파싱
                state["script"] = script_content
                state = self._parse_script_sections(state, script_content)
                state["created_at"] = datetime.now().isoformat()

                self.logger.info(f"Generated script for topic: {state['topic']}")
                return state

            except Exception as e:
                self.logger.error(f"Failed to generate script: {e}")
                state["error"] = str(e)
                return state

    def _parse_script_sections(self, state: WriterState, content: str) -> WriterState:
        """스크립트에서 훅, CTA, 예상 길이 추출"""
        try:
            lines = content.split('\n')
            hook_lines = []
            cta_lines = []
            in_hook = False
            in_cta = False

            for line in lines:
                if '훅' in line or 'Hook' in line.upper():
                    in_hook = True
                    in_cta = False
                    continue
                elif 'CTA' in line.upper() or '행동 유도' in line:
                    in_hook = False
                    in_cta = True
                    continue
                elif '본문' in line or 'Body' in line.upper():
                    in_hook = False
                    in_cta = False
                    continue

                if in_hook and line.strip() and not line.startswith('#'):
                    hook_lines.append(line.strip())
                elif in_cta and line.strip() and not line.startswith('#'):
                    cta_lines.append(line.strip())

                # 예상 영상 길이 추출
                if '예상 영상 길이' in line or '예상 길이' in line:
                    import re
                    match = re.search(r'(\d+)\s*초', line)
                    if match:
                        state["estimated_duration"] = int(match.group(1))

            if hook_lines:
                state["hook"] = ' '.join(hook_lines)
            if cta_lines:
                state["cta"] = ' '.join(cta_lines)

        except Exception as e:
            self.logger.warning(f"Failed to parse script sections: {e}")

        return state

    async def _optimize_for_platform(self, state: WriterState) -> WriterState:
        """4단계: 플랫폼별 최적화"""
        span_context = logfire.span("writer.optimize_platform") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            platform = state["platform"].lower()

            # 플랫폼별 권장사항
            platform_tips = {
                "youtube": {
                    "optimal_length": "8-12분",
                    "hook_importance": "처음 15초가 핵심",
                    "cta_position": "영상 중간 + 마지막"
                },
                "instagram": {
                    "optimal_length": "30-90초",
                    "hook_importance": "처음 3초가 생명",
                    "cta_position": "마지막 5초"
                },
                "tiktok": {
                    "optimal_length": "15-60초",
                    "hook_importance": "처음 1초에 결정",
                    "cta_position": "중간부터 자연스럽게"
                }
            }

            if platform in platform_tips:
                tips = platform_tips[platform]
                self.logger.info(
                    f"Platform optimization for {platform}: "
                    f"Optimal length: {tips['optimal_length']}"
                )

            return state

    async def _save_to_memory(self, state: WriterState) -> WriterState:
        """5단계: Neo4j에 스크립트 저장"""
        span_context = logfire.span("writer.save_memory") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                # Neo4j에 스크립트 저장
                query = """
                MERGE (c:Campaign {name: $campaign_name})
                CREATE (s:Script {
                    topic: $topic,
                    script: $script,
                    hook: $hook,
                    cta: $cta,
                    platform: $platform,
                    target_audience: $target_audience,
                    tone: $tone,
                    estimated_duration: $estimated_duration,
                    created_at: $created_at
                })
                CREATE (s)-[:BELONGS_TO]->(c)
                RETURN s
                """

                self.neo4j_client.query(
                    query,
                    campaign_name=state["campaign_name"],
                    topic=state["topic"],
                    script=state["script"],
                    hook=state.get("hook"),
                    cta=state.get("cta"),
                    platform=state["platform"],
                    target_audience=state.get("target_audience"),
                    tone=state.get("tone"),
                    estimated_duration=state.get("estimated_duration"),
                    created_at=state.get("created_at")
                )

                self.logger.info(f"Saved script to Neo4j: {state['topic']}")
                return state

            except Exception as e:
                self.logger.error(f"Failed to save to Neo4j: {e}")
                state["error"] = str(e)
                return state

    async def generate_script(
        self,
        spreadsheet_id: str,
        campaign_name: str,
        topic: str,
        platform: str = "YouTube",
        target_duration: int = 180
    ) -> Dict[str, Any]:
        """
        스크립트 생성 메인 함수

        Args:
            spreadsheet_id: 구글 시트 ID
            campaign_name: 캠페인명
            topic: 소제목
            platform: 플랫폼 (YouTube, Instagram, TikTok)
            target_duration: 목표 영상 길이 (초)

        Returns:
            생성된 스크립트 및 메타데이터
        """
        span_context = logfire.span(
            "writer.generate_script_main",
            spreadsheet_id=spreadsheet_id,
            campaign=campaign_name,
            topic=topic,
            target_duration=target_duration
        ) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            # 초기 상태 설정
            initial_state: WriterState = {
                "spreadsheet_id": spreadsheet_id,
                "campaign_name": campaign_name,
                "topic": topic,
                "platform": platform,
                "target_duration": target_duration,
                "strategy": None,
                "target_audience": None,
                "tone": None,
                "past_scripts": None,
                "script": None,
                "hook": None,
                "cta": None,
                "estimated_duration": None,
                "created_at": None,
                "error": None
            }

            # LangGraph 워크플로우 실행
            try:
                final_state = await self.workflow.ainvoke(initial_state)

                if final_state.get("error"):
                    raise RuntimeError(final_state["error"])

                return {
                    "success": True,
                    "campaign_name": campaign_name,
                    "topic": topic,
                    "platform": platform,
                    "script": final_state["script"],
                    "hook": final_state.get("hook"),
                    "cta": final_state.get("cta"),
                    "estimated_duration": final_state.get("estimated_duration"),
                    "target_audience": final_state.get("target_audience"),
                    "tone": final_state.get("tone"),
                    "created_at": final_state.get("created_at")
                }

            except Exception as e:
                self.logger.error(f"Writer workflow failed: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }


# 싱글톤 인스턴스
_writer_agent_instance = None


def get_writer_agent() -> WriterAgent:
    """Writer 에이전트 싱글톤 인스턴스"""
    global _writer_agent_instance
    if _writer_agent_instance is None:
        _writer_agent_instance = WriterAgent()
    return _writer_agent_instance
