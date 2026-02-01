"""자막 생성 서비스 (Whisper Timestamps → SRT)

OpenAI Whisper API를 활용하여 오디오 파일에서 타임스탬프 기반 자막을 생성하고
SRT 형식으로 변환합니다. FFmpeg를 통한 비디오 자막 오버레이(번인)도 지원합니다.

주요 기능:
- Whisper API로 단어/세그먼트 수준 타임스탬프 추출
- SRT 형식 자막 파일 생성
- FFmpeg 자막 오버레이 (burn-in)
- 플랫폼별 자막 스타일 프리셋
- 비용 추적 통합
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import subprocess
from contextlib import nullcontext

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.cost_tracker import get_cost_tracker

settings = get_settings()

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class SubtitleService:
    """
    자막 생성 및 영상 오버레이 서비스

    워크플로우:
    1. Whisper API로 오디오 → 타임스탬프 포함 텍스트 변환
    2. 타임스탬프 → SRT 형식 변환
    3. (옵션) FFmpeg로 비디오에 자막 번인
    """

    # 지원 오디오 포맷
    SUPPORTED_AUDIO_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']

    # 지원 비디오 포맷
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

    # 자막 스타일 프리셋
    SUBTITLE_STYLES = {
        "default": {
            "fontsize": 24,
            "font": "Arial",
            "primary_colour": "&HFFFFFF&",  # 흰색
            "outline_colour": "&H000000&",  # 검은색
            "outline": 1,
            "bold": 0
        },
        "youtube": {
            "fontsize": 28,
            "font": "Arial",
            "primary_colour": "&HFFFFFF&",
            "outline_colour": "&H000000&",
            "outline": 2,
            "bold": 0
        },
        "tiktok": {
            "fontsize": 32,
            "font": "Impact",
            "primary_colour": "&HFFFF00&",  # 노란색
            "outline_colour": "&H000000&",
            "outline": 3,
            "bold": 1
        },
        "instagram": {
            "fontsize": 30,
            "font": "Helvetica",
            "primary_colour": "&HFFFFFF&",
            "outline_colour": "&H000000&",
            "outline": 2,
            "bold": 1
        },
        "minimal": {
            "fontsize": 22,
            "font": "Helvetica",
            "primary_colour": "&HFFFFFF&",
            "outline_colour": "&H000000&",
            "outline": 1,
            "bold": 0
        }
    }

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)
        self.cost_tracker = get_cost_tracker()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_subtitles(
        self,
        audio_path: str,
        language: str = "ko",
        output_srt_path: Optional[str] = None,
        granularity: str = "segment",  # "word" 또는 "segment"
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        오디오 파일에서 SRT 자막 생성

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, ja 등)
            output_srt_path: SRT 파일 저장 경로 (None이면 자동 생성)
            granularity: 타임스탬프 세분화 수준 ("word" 또는 "segment")
            user_id: 사용자 ID (비용 추적용)
            project_id: 프로젝트 ID (비용 추적용)

        Returns:
            {
                "srt_path": str,              # 생성된 SRT 파일 경로
                "segments": List[Dict],       # 자막 세그먼트 리스트
                "duration": float,            # 오디오 총 길이 (초)
                "language": str,              # 감지된 언어
                "word_count": int,            # 단어 수
                "cost_usd": float             # API 비용
            }
        """
        span_context = logfire.span("subtitle.generate") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            # 파일 존재 확인
            audio_file = Path(audio_path)
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # 파일 형식 검증
            if not self.validate_audio_format(audio_path):
                raise ValueError(
                    f"Unsupported audio format: {audio_file.suffix}. "
                    f"Supported: {', '.join(self.SUPPORTED_AUDIO_FORMATS)}"
                )

            # SRT 출력 경로 자동 생성
            if output_srt_path is None:
                output_srt_path = str(audio_file.with_suffix('.srt'))

            if LOGFIRE_AVAILABLE:
                span.set_attribute("audio_path", audio_path)
                span.set_attribute("language", language)
                span.set_attribute("granularity", granularity)

            self.logger.info(f"Generating subtitles from: {audio_path}")

            # Whisper API 호출 (타임스탬프 포함)
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=[granularity]
                )

            # 응답 파싱
            segments = self._parse_whisper_response(response, granularity)

            # SRT 콘텐츠 생성
            srt_content = self._generate_srt_content(segments)

            # SRT 파일 저장
            with open(output_srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            self.logger.info(f"SRT file saved: {output_srt_path}")

            # 비용 추적
            duration = response.duration
            cost_record = self.cost_tracker.record_whisper_usage(
                duration_seconds=duration,
                user_id=user_id,
                project_id=project_id,
                metadata={
                    "subtitle_generation": True,
                    "granularity": granularity,
                    "language": language,
                    "segment_count": len(segments)
                }
            )

            result = {
                "srt_path": output_srt_path,
                "segments": segments,
                "duration": duration,
                "language": response.language,
                "word_count": len(response.text.split()),
                "cost_usd": cost_record.cost_usd
            }

            if LOGFIRE_AVAILABLE:
                span.set_attribute("duration", duration)
                span.set_attribute("segment_count", len(segments))
                span.set_attribute("cost_usd", cost_record.cost_usd)

            return result

    def _parse_whisper_response(
        self,
        response: Any,
        granularity: str
    ) -> List[Dict[str, Any]]:
        """
        Whisper API 응답 파싱

        Args:
            response: Whisper API 응답 객체
            granularity: "word" 또는 "segment"

        Returns:
            [
                {
                    "start": float,      # 시작 시간 (초)
                    "end": float,        # 종료 시간 (초)
                    "text": str          # 텍스트
                },
                ...
            ]
        """
        segments = []

        if granularity == "segment":
            # 세그먼트 수준 (문장 단위)
            for seg in response.segments:
                segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })

        elif granularity == "word":
            # 단어 수준
            if hasattr(response, 'words') and response.words:
                for word in response.words:
                    segments.append({
                        "start": word.start,
                        "end": word.end,
                        "text": word.word.strip()
                    })
            else:
                # words가 없으면 segments 사용
                self.logger.warning(
                    "Word-level timestamps not available, falling back to segments"
                )
                return self._parse_whisper_response(response, "segment")

        return segments

    def _generate_srt_content(
        self,
        segments: List[Dict[str, Any]]
    ) -> str:
        """
        자막 세그먼트를 SRT 형식으로 변환

        SRT 형식:
        1
        00:00:00,000 --> 00:00:02,500
        안녕하세요. 오늘은 좋은 날씨입니다.

        2
        00:00:02,500 --> 00:00:05,000
        여러분과 함께 할 내용이 있습니다.

        Args:
            segments: 자막 세그먼트 리스트

        Returns:
            SRT 형식 문자열
        """
        srt_lines = []

        for i, segment in enumerate(segments, 1):
            # 인덱스
            srt_lines.append(str(i))

            # 타임스탬프 (00:00:00,000 --> 00:00:00,000)
            start_ts = self._format_timestamp(segment["start"])
            end_ts = self._format_timestamp(segment["end"])
            srt_lines.append(f"{start_ts} --> {end_ts}")

            # 텍스트
            srt_lines.append(segment["text"])

            # 빈 줄 (세그먼트 구분)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        초 단위 시간을 SRT 타임스탬프 형식으로 변환

        Args:
            seconds: 초 단위 시간 (예: 125.5)

        Returns:
            SRT 타임스탬프 (예: "00:02:05,500")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def apply_subtitles_to_video(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        style: str = "default",
        custom_style: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        FFmpeg를 사용하여 비디오에 자막 오버레이 (burn-in)

        Args:
            video_path: 원본 비디오 파일 경로
            srt_path: SRT 자막 파일 경로
            output_path: 출력 비디오 파일 경로
            style: 자막 스타일 프리셋 ("default", "youtube", "tiktok", etc.)
            custom_style: 커스텀 스타일 설정 (프리셋 무시)

        Returns:
            출력 비디오 파일 경로

        Raises:
            FileNotFoundError: 비디오 또는 SRT 파일이 없는 경우
            ValueError: 비디오 형식이 지원되지 않는 경우
            RuntimeError: FFmpeg 실행 실패
        """
        span_context = logfire.span("subtitle.apply_to_video") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            # 파일 존재 확인
            video_file = Path(video_path)
            srt_file = Path(srt_path)

            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            if not srt_file.exists():
                raise FileNotFoundError(f"SRT file not found: {srt_path}")

            # 비디오 형식 검증
            if not self.validate_video_format(video_path):
                raise ValueError(
                    f"Unsupported video format: {video_file.suffix}. "
                    f"Supported: {', '.join(self.SUPPORTED_VIDEO_FORMATS)}"
                )

            if LOGFIRE_AVAILABLE:
                span.set_attribute("video_path", video_path)
                span.set_attribute("srt_path", srt_path)
                span.set_attribute("style", style)

            self.logger.info(f"Applying subtitles to video: {video_path}")

            # 자막 필터 생성
            subtitle_filter = self._build_subtitle_filter(
                srt_path,
                style,
                custom_style
            )

            # FFmpeg 명령 구성
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", subtitle_filter,
                "-c:a", "copy",  # 오디오는 그대로 복사
                "-y",  # 덮어쓰기
                output_path
            ]

            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            # FFmpeg 실행
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

                if LOGFIRE_AVAILABLE:
                    span.set_attribute("output_path", output_path)

                return output_path

            except FileNotFoundError:
                raise RuntimeError(
                    "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
                )

    def _build_subtitle_filter(
        self,
        srt_path: str,
        style: str = "default",
        custom_style: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        FFmpeg 자막 필터 문자열 생성

        Args:
            srt_path: SRT 파일 경로
            style: 프리셋 스타일 이름
            custom_style: 커스텀 스타일 (프리셋 무시)

        Returns:
            FFmpeg 필터 문자열
        """
        # 스타일 결정
        if custom_style:
            style_config = custom_style
        elif style in self.SUBTITLE_STYLES:
            style_config = self.SUBTITLE_STYLES[style]
        else:
            self.logger.warning(f"Unknown style '{style}', using 'default'")
            style_config = self.SUBTITLE_STYLES["default"]

        # force_style 문자열 생성
        force_style_parts = []

        if "fontsize" in style_config:
            force_style_parts.append(f"Fontsize={style_config['fontsize']}")

        if "font" in style_config:
            force_style_parts.append(f"Fontname={style_config['font']}")

        if "primary_colour" in style_config:
            force_style_parts.append(f"PrimaryColour={style_config['primary_colour']}")

        if "outline_colour" in style_config:
            force_style_parts.append(f"OutlineColour={style_config['outline_colour']}")

        if "outline" in style_config:
            force_style_parts.append(f"Outline={style_config['outline']}")

        if "bold" in style_config:
            force_style_parts.append(f"Bold={style_config['bold']}")

        force_style = ",".join(force_style_parts)

        # 경로에 특수문자가 있을 수 있으므로 이스케이프
        # Windows 경로 처리 (백슬래시 → 슬래시)
        srt_path_escaped = srt_path.replace("\\", "/").replace(":", r"\:")

        # FFmpeg subtitles 필터
        subtitle_filter = f"subtitles={srt_path_escaped}:force_style='{force_style}'"

        return subtitle_filter

    def validate_audio_format(self, file_path: str) -> bool:
        """
        오디오 파일 형식 검증

        Args:
            file_path: 오디오 파일 경로

        Returns:
            지원 형식 여부
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_AUDIO_FORMATS

    def validate_video_format(self, file_path: str) -> bool:
        """
        비디오 파일 형식 검증

        Args:
            file_path: 비디오 파일 경로

        Returns:
            지원 형식 여부
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_VIDEO_FORMATS

    async def generate_subtitles_for_multiple_languages(
        self,
        audio_path: str,
        languages: List[str],
        output_dir: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        여러 언어로 자막 생성 (다국어 지원)

        Args:
            audio_path: 오디오 파일 경로
            languages: 언어 코드 리스트 (예: ["ko", "en", "ja"])
            output_dir: 출력 디렉토리 (None이면 원본과 동일)
            user_id: 사용자 ID
            project_id: 프로젝트 ID

        Returns:
            {
                "ko": {"srt_path": "...", "segments": [...], ...},
                "en": {"srt_path": "...", "segments": [...], ...},
                ...
            }
        """
        results = {}

        audio_file = Path(audio_path)
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = audio_file.parent

        for lang in languages:
            try:
                # 언어별 SRT 파일 경로
                srt_filename = f"{audio_file.stem}_{lang}.srt"
                srt_path = str(output_path / srt_filename)

                self.logger.info(f"Generating {lang} subtitles...")

                result = await self.generate_subtitles(
                    audio_path=audio_path,
                    language=lang,
                    output_srt_path=srt_path,
                    user_id=user_id,
                    project_id=project_id
                )

                results[lang] = result

            except Exception as e:
                self.logger.error(f"Failed to generate {lang} subtitles: {e}")
                results[lang] = {"error": str(e)}

        return results

    def merge_subtitle_segments(
        self,
        segments: List[Dict[str, Any]],
        max_duration: float = 5.0,
        max_chars: int = 80
    ) -> List[Dict[str, Any]]:
        """
        짧은 자막 세그먼트를 병합하여 가독성 향상

        Args:
            segments: 원본 세그먼트 리스트
            max_duration: 병합된 세그먼트 최대 길이 (초)
            max_chars: 병합된 세그먼트 최대 글자 수

        Returns:
            병합된 세그먼트 리스트
        """
        if not segments:
            return []

        merged = []
        current = {
            "start": segments[0]["start"],
            "end": segments[0]["end"],
            "text": segments[0]["text"]
        }

        for segment in segments[1:]:
            duration = segment["end"] - current["start"]
            combined_text = current["text"] + " " + segment["text"]

            # 병합 조건 체크
            if (duration <= max_duration and
                len(combined_text) <= max_chars):
                # 병합
                current["end"] = segment["end"]
                current["text"] = combined_text
            else:
                # 현재 세그먼트 저장 후 새로운 세그먼트 시작
                merged.append(current)
                current = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
                }

        # 마지막 세그먼트 추가
        merged.append(current)

        return merged


# 싱글톤 인스턴스
_subtitle_service_instance: Optional[SubtitleService] = None


def get_subtitle_service() -> SubtitleService:
    """SubtitleService 싱글톤 인스턴스 반환"""
    global _subtitle_service_instance

    if _subtitle_service_instance is None:
        _subtitle_service_instance = SubtitleService()

    return _subtitle_service_instance
