"""Video Director Agent - 영상 생성 오케스트레이션

LangGraph 기반 에이전트로 오디오 + 스크립트 → 완성된 영상 자동 생성

워크플로우:
1. 캐릭터 로드/생성 (Nano Banana)
2. 영상 클립 생성 (Google Veo)
3. 립싱크 적용 (HeyGen/Wav2Lip)
4. 자막 생성 (Whisper Timestamps)
5. 최종 렌더링 (FFmpeg)
6. 플랫폼 최적화 (Cloudinary)
"""
from typing import Dict, Any, Optional, List, TypedDict
import logging
from datetime import datetime
from contextlib import nullcontext
from pathlib import Path
import re
import asyncio

from langgraph.graph import StateGraph, END

from app.core.config import get_settings
from app.services.character_service import get_character_service
from app.services.veo_service import get_veo_service
from app.services.lipsync_service import get_lipsync_service
from app.services.stt_service import get_stt_service
from app.services.neo4j_client import get_neo4j_client
from app.services.cost_tracker import get_cost_tracker, APIService

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class VideoClip(TypedDict):
    """영상 클립 정보"""
    section_type: str  # "hook", "body", "cta"
    section_text: str
    duration: float
    video_job_id: Optional[str]
    video_url: Optional[str]
    local_path: Optional[str]


class DirectorState(TypedDict):
    """Director 에이전트 상태"""
    # 입력
    project_id: str
    script: str
    audio_path: str

    # 페르소나/캐릭터
    persona_id: Optional[str]
    gender: Optional[str]  # "male", "female", "neutral"
    age_range: Optional[str]  # "20-30", "30-40", "40-50", "50-60"
    character_style: Optional[str]  # "professional", "casual", "creative", "formal"

    # 캐릭터 정보
    character_id: Optional[str]
    character_reference_url: Optional[str]

    # 스크립트 분석
    script_sections: Optional[List[Dict[str, Any]]]
    total_duration: Optional[float]

    # 영상 클립
    video_clips: Optional[List[VideoClip]]

    # 립싱크
    raw_video_path: Optional[str]
    lipsynced_video_path: Optional[str]
    lipsync_cost_usd: Optional[float]

    # 자막
    subtitles: Optional[List[Dict[str, Any]]]
    subtitle_srt_path: Optional[str]

    # 최종 결과
    final_video_path: Optional[str]
    optimized_video_url: Optional[str]

    # 비용 추적
    total_cost_usd: Optional[float]
    cost_breakdown: Optional[Dict[str, float]]

    # 메타데이터
    created_at: Optional[str]
    completed_at: Optional[str]

    # 에러
    error: Optional[str]
    success: bool


class VideoDirectorAgent:
    """Video Director Agent - 영상 생성 오케스트레이션"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 서비스 초기화
        self.character_service = get_character_service()
        self.veo_service = get_veo_service()
        self.lipsync_service = get_lipsync_service()
        self.stt_service = get_stt_service()
        self.neo4j_client = get_neo4j_client()
        self.cost_tracker = get_cost_tracker()

        # 출력 디렉토리
        self.video_dir = Path("./outputs/videos")
        self.video_dir.mkdir(parents=True, exist_ok=True)

        # LangGraph 워크플로우 구축
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구축"""
        workflow = StateGraph(DirectorState)

        # 노드 추가
        workflow.add_node("load_character", self._load_character)
        workflow.add_node("parse_script", self._parse_script)
        workflow.add_node("generate_video_clips", self._generate_video_clips)
        workflow.add_node("wait_for_videos", self._wait_for_videos)
        workflow.add_node("merge_clips", self._merge_clips)
        workflow.add_node("apply_lipsync", self._apply_lipsync)
        workflow.add_node("generate_subtitles", self._generate_subtitles)
        workflow.add_node("render_final_video", self._render_final_video)
        workflow.add_node("save_metadata", self._save_metadata)

        # 엣지 정의
        workflow.set_entry_point("load_character")
        workflow.add_edge("load_character", "parse_script")
        workflow.add_edge("parse_script", "generate_video_clips")
        workflow.add_edge("generate_video_clips", "wait_for_videos")
        workflow.add_edge("wait_for_videos", "merge_clips")
        workflow.add_edge("merge_clips", "apply_lipsync")
        workflow.add_edge("apply_lipsync", "generate_subtitles")
        workflow.add_edge("generate_subtitles", "render_final_video")
        workflow.add_edge("render_final_video", "save_metadata")
        workflow.add_edge("save_metadata", END)

        return workflow.compile()

    async def _load_character(self, state: DirectorState) -> DirectorState:
        """1단계: 캐릭터 정보 로드/생성"""
        span_context = logfire.span("director.load_character") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info(f"Loading character for persona: {state.get('persona_id')}")

                # 페르소나 정보 기본값 설정
                persona_id = state.get("persona_id") or "default_persona"
                gender = state.get("gender") or "female"
                age_range = state.get("age_range") or "30-40"
                character_style = state.get("character_style") or "professional"

                # 캐릭터 조회 또는 생성
                character = await self.character_service.get_or_create_character(
                    persona_id=persona_id,
                    gender=gender,
                    age_range=age_range,
                    style=character_style
                )

                state["character_id"] = character["character_id"]
                state["character_reference_url"] = character["reference_image_url"]

                self.logger.info(
                    f"Character loaded: {character['character_id']} "
                    f"(reference: {character['reference_image_url'][:50]}...)"
                )

                # 캐릭터 생성 비용 기록 (신규 생성 시)
                if not character.get("generation_metadata", {}).get("is_fallback"):
                    self.cost_tracker.record_character_generation_usage(
                        count=1,
                        project_id=state["project_id"]
                    )

                return state

            except Exception as e:
                self.logger.error(f"Failed to load character: {e}")
                state["error"] = f"캐릭터 로드 실패: {str(e)}"
                state["success"] = False
                return state

    def _parse_script_sections(self, script: str) -> List[Dict[str, Any]]:
        """스크립트를 섹션별로 분할 (훅, 본문, CTA)"""
        sections = []

        # 메타데이터 제거된 순수 스크립트
        lines = script.strip().split("\n")
        current_section = {"type": "body", "text": "", "duration": 0}

        for line in lines:
            line = line.strip()

            # 메타데이터 라인 스킵
            if line.startswith("###") or line.startswith("---"):
                continue

            # 훅 섹션 감지
            if "훅" in line or "HOOK" in line.upper():
                if current_section["text"]:
                    sections.append(current_section)
                current_section = {"type": "hook", "text": "", "duration": 0}
                continue

            # CTA 섹션 감지
            if "CTA" in line.upper() or "행동 유도" in line or "마무리" in line:
                if current_section["text"]:
                    sections.append(current_section)
                current_section = {"type": "cta", "text": "", "duration": 0}
                continue

            # 텍스트 추가
            if line:
                current_section["text"] += line + " "

        # 마지막 섹션 추가
        if current_section["text"]:
            sections.append(current_section)

        # 섹션별 예상 duration 계산 (한국어 기준: 초당 약 4-5음절)
        for section in sections:
            char_count = len(section["text"].replace(" ", ""))
            section["duration"] = max(3, char_count / 4.5)  # 최소 3초

        self.logger.info(
            f"Parsed {len(sections)} sections: "
            f"{[s['type'] for s in sections]}"
        )

        return sections

    async def _parse_script(self, state: DirectorState) -> DirectorState:
        """2단계: 스크립트 분석 및 섹션 분할"""
        span_context = logfire.span("director.parse_script") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Parsing script into sections")

                sections = self._parse_script_sections(state["script"])

                state["script_sections"] = sections
                state["total_duration"] = sum(s["duration"] for s in sections)

                self.logger.info(
                    f"Script parsed: {len(sections)} sections, "
                    f"total duration: {state['total_duration']:.1f}s"
                )

                return state

            except Exception as e:
                self.logger.error(f"Failed to parse script: {e}")
                state["error"] = f"스크립트 분석 실패: {str(e)}"
                state["success"] = False
                return state

    async def _generate_video_clips(self, state: DirectorState) -> DirectorState:
        """3단계: 섹션별 영상 클립 생성 (Google Veo)"""
        span_context = logfire.span("director.generate_video_clips") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Generating video clips with Veo")

                sections = state["script_sections"]
                clips: List[VideoClip] = []

                for section in sections:
                    self.logger.info(
                        f"Generating {section['type']} clip "
                        f"({section['duration']:.1f}s): {section['text'][:50]}..."
                    )

                    # Veo API 호출
                    veo_result = await self.veo_service.generate_from_script_section(
                        section_text=section["text"],
                        section_type=section["type"],
                        duration=int(section["duration"]),
                        character_reference=state["character_reference_url"]
                    )

                    clip: VideoClip = {
                        "section_type": section["type"],
                        "section_text": section["text"],
                        "duration": section["duration"],
                        "video_job_id": veo_result.get("job_id"),
                        "video_url": None,
                        "local_path": None
                    }

                    clips.append(clip)

                    # 비용 기록
                    self.cost_tracker.record_video_generation_usage(
                        service=APIService.VEO_VIDEO,
                        duration_seconds=section["duration"],
                        project_id=state["project_id"],
                        metadata={
                            "section_type": section["type"],
                            "job_id": clip["video_job_id"]
                        }
                    )

                state["video_clips"] = clips

                self.logger.info(f"All video clips generation started: {len(clips)} clips")

                return state

            except Exception as e:
                self.logger.error(f"Failed to generate video clips: {e}")
                state["error"] = f"영상 클립 생성 실패: {str(e)}"
                state["success"] = False
                return state

    async def _wait_for_videos(self, state: DirectorState) -> DirectorState:
        """4단계: 영상 생성 완료 대기"""
        span_context = logfire.span("director.wait_for_videos") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Waiting for video generation to complete")

                clips = state["video_clips"]

                for i, clip in enumerate(clips):
                    job_id = clip["video_job_id"]
                    self.logger.info(f"Checking status for clip {i+1}/{len(clips)}: {job_id}")

                    # 상태 확인 (최대 10분 대기)
                    max_wait = 600
                    poll_interval = 10
                    elapsed = 0

                    while elapsed < max_wait:
                        status = await self.veo_service.check_status(job_id)

                        if status["status"] == "completed":
                            clip["video_url"] = status["video_url"]

                            # 다운로드
                            filename = f"{state['project_id']}_clip_{i}_{clip['section_type']}.mp4"
                            local_path = await self.veo_service.download_video(
                                status["video_url"],
                                filename
                            )
                            clip["local_path"] = str(local_path)

                            self.logger.info(f"Clip {i+1} completed: {local_path}")
                            break

                        elif status["status"] == "failed":
                            raise RuntimeError(
                                f"Video generation failed for clip {i+1}: "
                                f"{status.get('error')}"
                            )

                        # 대기
                        self.logger.info(
                            f"Clip {i+1} in progress: {status.get('progress', 0)}%"
                        )
                        await asyncio.sleep(poll_interval)
                        elapsed += poll_interval

                    if not clip.get("local_path"):
                        raise TimeoutError(
                            f"Video generation timeout for clip {i+1}"
                        )

                self.logger.info("All video clips completed")

                return state

            except Exception as e:
                self.logger.error(f"Failed to wait for videos: {e}")
                state["error"] = f"영상 생성 대기 실패: {str(e)}"
                state["success"] = False
                return state

    async def _merge_clips(self, state: DirectorState) -> DirectorState:
        """5단계: 클립 병합 (FFmpeg)"""
        span_context = logfire.span("director.merge_clips") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Merging video clips with FFmpeg")

                clips = state["video_clips"]

                # FFmpeg concat 리스트 파일 생성
                concat_file = self.video_dir / f"{state['project_id']}_concat.txt"
                with open(concat_file, "w") as f:
                    for clip in clips:
                        f.write(f"file '{clip['local_path']}'\n")

                # 병합된 영상 경로
                merged_path = self.video_dir / f"{state['project_id']}_merged.mp4"

                # FFmpeg 실행
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c", "copy",
                    str(merged_path)
                ]

                self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise RuntimeError(
                        f"FFmpeg merge failed: {stderr.decode()}"
                    )

                state["raw_video_path"] = str(merged_path)

                self.logger.info(f"Video clips merged: {merged_path}")

                return state

            except Exception as e:
                self.logger.error(f"Failed to merge clips: {e}")
                state["error"] = f"클립 병합 실패: {str(e)}"
                state["success"] = False
                return state

    async def _apply_lipsync(self, state: DirectorState) -> DirectorState:
        """6단계: 립싱크 적용 (HeyGen/Wav2Lip)"""
        span_context = logfire.span("director.apply_lipsync") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Applying lipsync to video")

                video_path = state["raw_video_path"]
                audio_path = state["audio_path"]
                output_path = str(
                    self.video_dir / f"{state['project_id']}_lipsynced.mp4"
                )

                # 립싱크 생성
                lipsync_result = await self.lipsync_service.generate_lipsync(
                    video_path=video_path,
                    audio_path=audio_path,
                    output_path=output_path,
                    method="auto"
                )

                state["lipsynced_video_path"] = lipsync_result["output_path"]
                state["lipsync_cost_usd"] = lipsync_result.get("cost_usd", 0.0)

                self.logger.info(
                    f"Lipsync applied: {lipsync_result['method_used']}, "
                    f"cost: ${lipsync_result.get('cost_usd', 0):.3f}"
                )

                # 비용 기록 (HeyGen 사용 시)
                if lipsync_result["method_used"] == "heygen":
                    self.cost_tracker.record_video_generation_usage(
                        service=APIService.HEYGEN_LIPSYNC,
                        duration_seconds=lipsync_result.get("duration", 0),
                        project_id=state["project_id"]
                    )

                return state

            except Exception as e:
                self.logger.error(f"Failed to apply lipsync: {e}")
                state["error"] = f"립싱크 적용 실패: {str(e)}"
                state["success"] = False
                return state

    async def _generate_subtitles(self, state: DirectorState) -> DirectorState:
        """7단계: 자막 생성 (Whisper Timestamps)"""
        span_context = logfire.span("director.generate_subtitles") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Generating subtitles with Whisper")

                # Whisper로 타임스탬프 포함 전사
                audio_path = state["audio_path"]

                # 오디오 파일 읽기
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()

                # Whisper 전사 (타임스탬프 포함)
                # TODO: Whisper API에 timestamp 옵션 추가 필요
                transcription = await self.stt_service.transcribe(
                    audio_bytes=audio_bytes,
                    language="ko"
                )

                # SRT 파일 생성 (임시: 간단한 구현)
                # 실제로는 Whisper의 word-level timestamps 사용
                srt_path = self.video_dir / f"{state['project_id']}_subtitles.srt"

                # 임시: 스크립트를 균등하게 분할
                sections = state["script_sections"]
                srt_lines = []
                start_time = 0.0

                for i, section in enumerate(sections):
                    end_time = start_time + section["duration"]

                    srt_lines.append(f"{i+1}")
                    srt_lines.append(
                        f"{self._format_srt_time(start_time)} --> "
                        f"{self._format_srt_time(end_time)}"
                    )
                    srt_lines.append(section["text"].strip())
                    srt_lines.append("")

                    start_time = end_time

                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(srt_lines))

                state["subtitle_srt_path"] = str(srt_path)

                self.logger.info(f"Subtitles generated: {srt_path}")

                # Whisper 비용 기록
                duration = sum(s["duration"] for s in sections)
                self.cost_tracker.record_whisper_usage(
                    duration_seconds=duration,
                    project_id=state["project_id"]
                )

                return state

            except Exception as e:
                self.logger.error(f"Failed to generate subtitles: {e}")
                state["error"] = f"자막 생성 실패: {str(e)}"
                state["success"] = False
                return state

    def _format_srt_time(self, seconds: float) -> str:
        """초를 SRT 시간 포맷으로 변환 (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def _render_final_video(self, state: DirectorState) -> DirectorState:
        """8단계: 최종 렌더링 (자막 오버레이)"""
        span_context = logfire.span("director.render_final_video") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Rendering final video with subtitles")

                video_path = state["lipsynced_video_path"]
                srt_path = state["subtitle_srt_path"]
                output_path = str(
                    self.video_dir / f"{state['project_id']}_final.mp4"
                )

                # FFmpeg로 자막 오버레이
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-vf", f"subtitles={srt_path}",
                    "-c:a", "copy",
                    output_path
                ]

                self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise RuntimeError(
                        f"FFmpeg render failed: {stderr.decode()}"
                    )

                state["final_video_path"] = output_path
                state["completed_at"] = datetime.now().isoformat()
                state["success"] = True

                self.logger.info(f"Final video rendered: {output_path}")

                return state

            except Exception as e:
                self.logger.error(f"Failed to render final video: {e}")
                state["error"] = f"최종 렌더링 실패: {str(e)}"
                state["success"] = False
                return state

    async def _save_metadata(self, state: DirectorState) -> DirectorState:
        """9단계: 메타데이터 저장 (Neo4j)"""
        span_context = logfire.span("director.save_metadata") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            try:
                self.logger.info("Saving video metadata to Neo4j")

                # 비용 집계
                total_cost = self.cost_tracker.get_total_cost(
                    project_id=state["project_id"]
                )

                state["total_cost_usd"] = total_cost["total_cost"]
                state["cost_breakdown"] = total_cost["by_provider"]

                # Neo4j 저장
                query = """
                MERGE (p:Project {project_id: $project_id})
                CREATE (v:Video {
                    video_id: $video_id,
                    script: $script,
                    character_id: $character_id,
                    total_duration: $total_duration,
                    final_video_path: $final_video_path,
                    subtitle_srt_path: $subtitle_srt_path,
                    total_cost_usd: $total_cost_usd,
                    cost_breakdown: $cost_breakdown,
                    created_at: $created_at,
                    completed_at: $completed_at
                })
                CREATE (v)-[:BELONGS_TO]->(p)
                RETURN v
                """

                video_id = f"video_{state['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                self.neo4j_client.query(
                    query,
                    project_id=state["project_id"],
                    video_id=video_id,
                    script=state["script"],
                    character_id=state.get("character_id"),
                    total_duration=state.get("total_duration"),
                    final_video_path=state.get("final_video_path"),
                    subtitle_srt_path=state.get("subtitle_srt_path"),
                    total_cost_usd=state.get("total_cost_usd"),
                    cost_breakdown=state.get("cost_breakdown"),
                    created_at=state.get("created_at"),
                    completed_at=state.get("completed_at")
                )

                self.logger.info(
                    f"Video metadata saved: {video_id}, "
                    f"total cost: ${state['total_cost_usd']:.2f}"
                )

                return state

            except Exception as e:
                self.logger.error(f"Failed to save metadata: {e}")
                # 메타데이터 저장 실패는 치명적이지 않음
                return state

    async def generate_video(
        self,
        project_id: str,
        script: str,
        audio_path: str,
        persona_id: Optional[str] = None,
        gender: str = "female",
        age_range: str = "30-40",
        character_style: str = "professional"
    ) -> Dict[str, Any]:
        """
        영상 생성 메인 함수

        Args:
            project_id: 프로젝트 ID
            script: 스크립트 텍스트
            audio_path: 오디오 파일 경로
            persona_id: 페르소나 ID (옵션)
            gender: 성별
            age_range: 연령대
            character_style: 캐릭터 스타일

        Returns:
            생성된 영상 정보
        """
        span_context = logfire.span(
            "director.generate_video_main",
            project=project_id
        ) if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            # 초기 상태 설정
            initial_state: DirectorState = {
                "project_id": project_id,
                "script": script,
                "audio_path": audio_path,
                "persona_id": persona_id,
                "gender": gender,
                "age_range": age_range,
                "character_style": character_style,
                "character_id": None,
                "character_reference_url": None,
                "script_sections": None,
                "total_duration": None,
                "video_clips": None,
                "raw_video_path": None,
                "lipsynced_video_path": None,
                "lipsync_cost_usd": None,
                "subtitles": None,
                "subtitle_srt_path": None,
                "final_video_path": None,
                "optimized_video_url": None,
                "total_cost_usd": None,
                "cost_breakdown": None,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
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
                        "project_id": project_id
                    }

                if not final_state.get("success"):
                    return {
                        "success": False,
                        "error": "영상 생성에 실패했습니다",
                        "project_id": project_id
                    }

                return {
                    "success": True,
                    "project_id": project_id,
                    "final_video_path": final_state["final_video_path"],
                    "subtitle_srt_path": final_state.get("subtitle_srt_path"),
                    "character_id": final_state.get("character_id"),
                    "total_duration": final_state.get("total_duration"),
                    "total_cost_usd": final_state.get("total_cost_usd"),
                    "cost_breakdown": final_state.get("cost_breakdown"),
                    "created_at": final_state.get("created_at"),
                    "completed_at": final_state.get("completed_at")
                }

            except Exception as e:
                self.logger.error(f"Director workflow failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "project_id": project_id
                }


# 싱글톤 인스턴스
_video_director_agent_instance = None


def get_video_director_agent() -> VideoDirectorAgent:
    """Video Director 에이전트 싱글톤 인스턴스"""
    global _video_director_agent_instance
    if _video_director_agent_instance is None:
        _video_director_agent_instance = VideoDirectorAgent()
    return _video_director_agent_instance
