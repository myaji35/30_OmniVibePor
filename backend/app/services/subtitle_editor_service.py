"""자막 편집 서비스 (스타일 조정 및 미리보기)

영상의 자막 위치, 스타일, 크기를 조정하고 실시간 미리보기를 제공합니다.
FFmpeg를 사용하여 ASS 형식 자막을 비디오에 오버레이합니다.

주요 기능:
- 자막 스타일 조정 (폰트, 색상, 위치, 아웃라인, 그림자)
- Neo4j에 스타일 저장 및 로드
- FFmpeg 자막 오버레이 (ASS 형식)
- 미리보기 생성 (5초 샘플 영상)
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
import subprocess
import tempfile
from datetime import datetime, timedelta
from contextlib import nullcontext

from app.core.config import get_settings
from app.services.neo4j_client import Neo4jClient
from app.models.neo4j_models import (
    SubtitleStyleUpdateRequest,
    SubtitleStyleResponse
)

settings = get_settings()

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class SubtitleEditorService:
    """
    자막 편집 서비스

    워크플로우:
    1. SRT 파일을 ASS 형식으로 변환
    2. 사용자 스타일을 ASS 스타일로 변환
    3. FFmpeg로 비디오에 자막 오버레이
    4. (미리보기용) 5초 샘플 영상 생성
    """

    # 기본 자막 스타일
    DEFAULT_STYLE = {
        "font_family": "Arial",
        "font_size": 24,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 0.7,
        "position": "bottom",
        "vertical_offset": 0,
        "alignment": "center",
        "outline_width": 1,
        "outline_color": "#000000",
        "shadow_enabled": False,
        "shadow_offset_x": 2,
        "shadow_offset_y": 2
    }

    # 위치별 MarginV 값 (픽셀)
    POSITION_MARGINS = {
        "top": 20,
        "center": None,  # 중앙은 Alignment로만 처리
        "bottom": 20
    }

    # 정렬 값 (ASS 형식)
    ALIGNMENT_VALUES = {
        "left": {"top": 7, "center": 4, "bottom": 1},
        "center": {"top": 8, "center": 5, "bottom": 2},
        "right": {"top": 9, "center": 6, "bottom": 3}
    }

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client
        self.logger = logging.getLogger(__name__)

    def hex_to_ass_color(self, hex_color: str, opacity: float = 1.0) -> str:
        """
        HEX 색상을 ASS 색상 형식으로 변환

        Args:
            hex_color: HEX 색상 (예: "#FFFFFF")
            opacity: 투명도 (0.0-1.0, ASS는 반대로 작동)

        Returns:
            ASS 색상 문자열 (예: "&H00FFFFFF&")
        """
        # HEX에서 # 제거
        hex_color = hex_color.lstrip('#')

        # RGB 추출
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # ASS 투명도 (0=불투명, 255=투명)
        alpha = int((1.0 - opacity) * 255)

        # ASS 형식: &HAABBGGRR& (역순)
        return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}&"

    def get_project_style(self, project_id: str) -> Dict[str, Any]:
        """
        프로젝트의 자막 스타일 조회 (없으면 기본값 반환)

        Args:
            project_id: 프로젝트 ID

        Returns:
            자막 스타일 딕셔너리
        """
        from app.models.neo4j_models import Neo4jCRUDManager
        crud = Neo4jCRUDManager(self.neo4j_client)

        style = crud.get_subtitle_style(project_id)
        if style:
            return style

        # 기본 스타일 반환
        return self.DEFAULT_STYLE.copy()

    def update_project_style(
        self,
        project_id: str,
        style_update: SubtitleStyleUpdateRequest
    ) -> SubtitleStyleResponse:
        """
        프로젝트 자막 스타일 업데이트

        Args:
            project_id: 프로젝트 ID
            style_update: 업데이트할 스타일 필드

        Returns:
            업데이트된 스타일
        """
        span_context = logfire.span("subtitle_editor.update_style") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            from app.models.neo4j_models import Neo4jCRUDManager
            crud = Neo4jCRUDManager(self.neo4j_client)

            # 기존 스타일 로드
            current_style = self.get_project_style(project_id)

            # 업데이트 적용
            update_dict = style_update.model_dump(exclude_none=True)
            current_style.update(update_dict)

            if LOGFIRE_AVAILABLE:
                span.set_attribute("project_id", project_id)
                span.set_attribute("updated_fields", list(update_dict.keys()))

            # Neo4j에 저장
            crud.create_or_update_subtitle_style(project_id, current_style)

            self.logger.info(f"Updated subtitle style for project {project_id}")

            return SubtitleStyleResponse(
                project_id=project_id,
                **current_style
            )

    def srt_to_ass(
        self,
        srt_path: str,
        ass_path: str,
        style: Dict[str, Any]
    ) -> str:
        """
        SRT 파일을 ASS 형식으로 변환하고 스타일 적용

        Args:
            srt_path: 원본 SRT 파일 경로
            ass_path: 출력 ASS 파일 경로
            style: 자막 스타일 딕셔너리

        Returns:
            생성된 ASS 파일 경로
        """
        span_context = logfire.span("subtitle_editor.srt_to_ass") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            if not Path(srt_path).exists():
                raise FileNotFoundError(f"SRT file not found: {srt_path}")

            # ASS 헤더 생성
            ass_header = self._generate_ass_header(style)

            # SRT 읽기
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            # SRT → ASS 이벤트 변환
            ass_events = self._convert_srt_to_ass_events(srt_content)

            # ASS 파일 작성
            ass_content = ass_header + "\n[Events]\n" + ass_events

            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)

            self.logger.info(f"Converted SRT to ASS: {ass_path}")

            if LOGFIRE_AVAILABLE:
                span.set_attribute("srt_path", srt_path)
                span.set_attribute("ass_path", ass_path)

            return ass_path

    def _generate_ass_header(self, style: Dict[str, Any]) -> str:
        """
        ASS 파일 헤더 생성 (스타일 포함)

        Args:
            style: 자막 스타일 딕셔너리

        Returns:
            ASS 헤더 문자열
        """
        # 색상 변환
        primary_color = self.hex_to_ass_color(style["font_color"], 1.0)
        outline_color = self.hex_to_ass_color(style["outline_color"], 1.0)

        # 배경 색상 (투명도 적용)
        back_color = self.hex_to_ass_color(
            style["background_color"],
            style["background_opacity"]
        )

        # 그림자 색상
        if style["shadow_enabled"]:
            shadow_color = "&H80000000&"  # 반투명 검정
        else:
            shadow_color = "&H00000000&"  # 투명

        # 정렬 값 (위치 + 정렬 조합)
        position = style["position"]
        alignment = style["alignment"]
        ass_alignment = self.ALIGNMENT_VALUES[alignment][position]

        # MarginV (수직 여백)
        margin_v = self.POSITION_MARGINS[position] or 0
        margin_v += style["vertical_offset"]

        # Bold/Italic (현재는 기본값)
        bold = 0
        italic = 0

        header = f"""[Script Info]
Title: OmniVibe Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font_family']},{style['font_size']},{primary_color},{primary_color},{outline_color},{back_color},{bold},{italic},0,0,100,100,0,0,1,{style['outline_width']},{style['shadow_offset_x'] if style['shadow_enabled'] else 0},{ass_alignment},20,20,{margin_v},1
"""
        return header

    def _convert_srt_to_ass_events(self, srt_content: str) -> str:
        """
        SRT 콘텐츠를 ASS 이벤트 형식으로 변환

        Args:
            srt_content: SRT 파일 내용

        Returns:
            ASS 이벤트 문자열
        """
        events_header = "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        events = []

        # SRT 파싱
        blocks = srt_content.strip().split('\n\n')

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # 타임스탬프 라인
            timestamp_line = lines[1]
            # 텍스트 라인들
            text_lines = lines[2:]
            text = '\\N'.join(text_lines)  # ASS에서 줄바꿈은 \N

            # 타임스탬프 파싱 (00:00:00,000 --> 00:00:00,000)
            try:
                start_str, end_str = timestamp_line.split(' --> ')
                start_time = self._srt_time_to_ass_time(start_str)
                end_time = self._srt_time_to_ass_time(end_str)
            except:
                continue

            # ASS 이벤트 생성
            event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
            events.append(event)

        return events_header + '\n'.join(events)

    def _srt_time_to_ass_time(self, srt_time: str) -> str:
        """
        SRT 타임스탬프를 ASS 형식으로 변환

        Args:
            srt_time: SRT 타임스탬프 (00:00:00,000)

        Returns:
            ASS 타임스탬프 (0:00:00.00)
        """
        # 00:00:00,000 → 0:00:00.00
        srt_time = srt_time.replace(',', '.')
        parts = srt_time.split(':')
        hours = int(parts[0])
        minutes = parts[1]
        seconds = parts[2][:5]  # 00.00

        return f"{hours}:{minutes}:{seconds}"

    def apply_subtitles_to_video(
        self,
        video_path: str,
        ass_path: str,
        output_path: str
    ) -> str:
        """
        FFmpeg를 사용하여 비디오에 ASS 자막 오버레이

        Args:
            video_path: 원본 비디오 경로
            ass_path: ASS 자막 파일 경로
            output_path: 출력 비디오 경로

        Returns:
            출력 비디오 경로
        """
        span_context = logfire.span("subtitle_editor.apply_to_video") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            if not Path(ass_path).exists():
                raise FileNotFoundError(f"ASS file not found: {ass_path}")

            # ASS 파일 경로 이스케이프 (Windows 호환성)
            ass_path_escaped = ass_path.replace('\\', '/').replace(':', r'\:')

            # FFmpeg 명령
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"ass={ass_path_escaped}",
                '-c:a', 'copy',  # 오디오 복사
                '-c:v', 'libx264',  # H.264 비디오 코덱
                '-preset', 'fast',
                '-y',  # 덮어쓰기
                output_path
            ]

            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            if LOGFIRE_AVAILABLE:
                span.set_attribute("video_path", video_path)
                span.set_attribute("ass_path", ass_path)
                span.set_attribute("output_path", output_path)

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode != 0:
                    error_msg = f"FFmpeg failed (exit code {result.returncode}):\n{result.stderr}"
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)

                self.logger.info(f"Subtitle overlay completed: {output_path}")
                return output_path

            except FileNotFoundError:
                raise RuntimeError(
                    "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
                )

    def generate_preview(
        self,
        project_id: str,
        video_path: str,
        srt_path: str,
        start_time: float = 0.0,
        duration: float = 5.0,
        style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        자막 미리보기 영상 생성 (5초 샘플)

        Args:
            project_id: 프로젝트 ID
            video_path: 원본 비디오 경로
            srt_path: SRT 자막 파일 경로
            start_time: 미리보기 시작 시간 (초)
            duration: 미리보기 길이 (초)
            style: 적용할 스타일 (None이면 프로젝트 스타일 사용)

        Returns:
            {
                "preview_path": str,
                "expires_at": datetime,
                "style": Dict
            }
        """
        span_context = logfire.span("subtitle_editor.generate_preview") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            # 스타일 결정
            if style is None:
                style = self.get_project_style(project_id)

            # 임시 파일 경로
            temp_dir = Path(tempfile.gettempdir()) / "omnivibe_previews"
            temp_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            preview_filename = f"preview_{project_id}_{timestamp}.mp4"
            preview_path = str(temp_dir / preview_filename)

            # ASS 파일 생성
            ass_filename = f"preview_{project_id}_{timestamp}.ass"
            ass_path = str(temp_dir / ass_filename)
            self.srt_to_ass(srt_path, ass_path, style)

            # 미리보기 영상 생성 (trim + 자막 오버레이)
            self._generate_preview_video(
                video_path,
                ass_path,
                preview_path,
                start_time,
                duration
            )

            # 만료 시간 (1시간 후)
            expires_at = datetime.now() + timedelta(hours=1)

            if LOGFIRE_AVAILABLE:
                span.set_attribute("project_id", project_id)
                span.set_attribute("preview_path", preview_path)
                span.set_attribute("duration", duration)

            self.logger.info(f"Preview generated: {preview_path}")

            return {
                "preview_path": preview_path,
                "expires_at": expires_at,
                "style": style
            }

    def _generate_preview_video(
        self,
        video_path: str,
        ass_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ) -> None:
        """
        미리보기 영상 생성 (trim + 자막 오버레이)

        Args:
            video_path: 원본 비디오 경로
            ass_path: ASS 자막 파일 경로
            output_path: 출력 경로
            start_time: 시작 시간 (초)
            duration: 길이 (초)
        """
        # ASS 경로 이스케이프
        ass_path_escaped = ass_path.replace('\\', '/').replace(':', r'\:')

        # FFmpeg 명령
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # 시작 시간
            '-i', video_path,
            '-t', str(duration),  # 길이
            '-vf', f"ass={ass_path_escaped}",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # 빠른 인코딩
            '-y',
            output_path
        ]

        self.logger.debug(f"Preview FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            error_msg = f"Preview generation failed:\n{result.stderr}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


# 싱글톤 인스턴스 (FastAPI 의존성에서 사용)
_subtitle_editor_service_instance: Optional[SubtitleEditorService] = None


def get_subtitle_editor_service() -> SubtitleEditorService:
    """SubtitleEditorService 싱글톤 인스턴스 반환"""
    global _subtitle_editor_service_instance

    from app.services.neo4j_client import get_neo4j_client

    if _subtitle_editor_service_instance is None:
        neo4j_client = get_neo4j_client()
        _subtitle_editor_service_instance = SubtitleEditorService(neo4j_client)

    return _subtitle_editor_service_instance
