"""BGM 편집 서비스

영상 배경음악(BGM)의 볼륨, 페이드, 구간을 조정하고 오디오 믹싱을 수행합니다.
"""
import os
import subprocess
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class BGMEditorService:
    """BGM 편집 및 오디오 믹싱 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(settings.AUDIO_OUTPUT_DIR) / "bgm"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate_audio_file(self, file_path: str) -> bool:
        """
        오디오 파일 검증 (FFmpeg probe)

        Args:
            file_path: 오디오 파일 경로

        Returns:
            검증 성공 여부
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Audio file not found: {file_path}")
            return False

        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                self.logger.error(f"FFprobe failed: {result.stderr}")
                return False

            metadata = json.loads(result.stdout)

            # 오디오 스트림 확인
            audio_streams = [
                s for s in metadata.get("streams", [])
                if s.get("codec_type") == "audio"
            ]

            if not audio_streams:
                self.logger.error(f"No audio stream found in {file_path}")
                return False

            # 지원 포맷 확인
            format_name = metadata.get("format", {}).get("format_name", "")
            supported_formats = ["mp3", "wav", "aac", "flac", "ogg", "m4a"]

            if not any(fmt in format_name for fmt in supported_formats):
                self.logger.error(f"Unsupported audio format: {format_name}")
                return False

            self.logger.info(f"Audio file validated: {file_path} (format: {format_name})")
            return True

        except subprocess.TimeoutExpired:
            self.logger.error(f"FFprobe timeout: {file_path}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse FFprobe output: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Audio validation failed: {e}", exc_info=True)
            return False

    def get_audio_duration(self, file_path: str) -> float:
        """
        오디오 파일 길이 조회 (초 단위)

        Args:
            file_path: 오디오 파일 경로

        Returns:
            오디오 길이 (초)
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                self.logger.error(f"Failed to get audio duration: {result.stderr}")
                return 0.0

            metadata = json.loads(result.stdout)
            duration = float(metadata.get("format", {}).get("duration", 0.0))

            return duration

        except Exception as e:
            self.logger.error(f"Failed to get audio duration: {e}", exc_info=True)
            return 0.0

    def extract_voice_timestamps(
        self,
        audio_path: str,
        whisper_result: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[float, float]]:
        """
        Whisper STT 결과에서 음성 구간 타임스탬프 추출

        Args:
            audio_path: 오디오 파일 경로
            whisper_result: Whisper STT 결과 (segments 포함)

        Returns:
            음성 구간 리스트 [(start, end), ...]
        """
        if not whisper_result or "segments" not in whisper_result:
            self.logger.warning("No Whisper result provided, skipping ducking")
            return []

        voice_segments = []

        for segment in whisper_result.get("segments", []):
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)

            if start < end:
                voice_segments.append((start, end))

        self.logger.info(f"Extracted {len(voice_segments)} voice segments from Whisper result")
        return voice_segments

    def build_ducking_filter(
        self,
        voice_segments: List[Tuple[float, float]],
        normal_volume: float,
        ducking_volume: float
    ) -> str:
        """
        FFmpeg 볼륨 필터 생성 (음성 구간에서 BGM 볼륨 감소)

        Args:
            voice_segments: 음성 구간 리스트 [(start, end), ...]
            normal_volume: 일반 볼륨
            ducking_volume: 덕킹 시 볼륨

        Returns:
            FFmpeg 볼륨 필터 문자열
        """
        if not voice_segments:
            return f"volume={normal_volume}"

        # FFmpeg volume 필터의 enable 옵션 사용
        filter_parts = []

        for i, (start, end) in enumerate(voice_segments):
            # 음성 구간에서 볼륨 감소
            filter_parts.append(
                f"volume={ducking_volume}:enable='between(t,{start},{end})'"
            )

        # 음성 구간 외에는 일반 볼륨
        all_filter = ",".join(filter_parts)
        all_filter += f",volume={normal_volume}"

        return all_filter

    def apply_bgm_effects(
        self,
        input_path: str,
        output_path: str,
        volume: float = 0.3,
        fade_in_duration: float = 2.0,
        fade_out_duration: float = 2.0,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        loop: bool = False,
        target_duration: Optional[float] = None,
        voice_segments: Optional[List[Tuple[float, float]]] = None,
        ducking_enabled: bool = True,
        ducking_level: float = 0.3
    ) -> bool:
        """
        BGM에 볼륨, 페이드, 루프 효과 적용

        Args:
            input_path: 입력 BGM 파일 경로
            output_path: 출력 파일 경로
            volume: 볼륨 (0.0-1.0)
            fade_in_duration: 페이드 인 길이 (초)
            fade_out_duration: 페이드 아웃 길이 (초)
            start_time: BGM 시작 시간 (초)
            end_time: BGM 종료 시간 (None이면 끝까지)
            loop: 반복 재생 여부
            target_duration: 목표 길이 (루프 시 필요)
            voice_segments: 음성 구간 타임스탬프 리스트
            ducking_enabled: 덕킹 활성화 여부
            ducking_level: 덕킹 시 볼륨 레벨

        Returns:
            성공 여부
        """
        try:
            # FFmpeg 필터 체인 구성
            filters = []

            # 1. 구간 자르기 (start_time, end_time)
            if start_time > 0 or end_time is not None:
                trim_filter = f"atrim=start={start_time}"
                if end_time is not None:
                    trim_filter += f":end={end_time}"
                filters.append(trim_filter)
                filters.append("asetpts=PTS-STARTPTS")  # 타임스탬프 재설정

            # 2. 루프 (target_duration에 맞춰)
            if loop and target_duration:
                # aloop 필터: -1은 무한 루프, size는 샘플 수
                loop_count = int(target_duration / self.get_audio_duration(input_path)) + 1
                filters.append(f"aloop=loop={loop_count}:size=2e+09")
                filters.append(f"atrim=duration={target_duration}")

            # 3. 볼륨 조절 (덕킹 적용 여부)
            if ducking_enabled and voice_segments:
                ducking_filter = self.build_ducking_filter(
                    voice_segments,
                    normal_volume=volume,
                    ducking_volume=ducking_level
                )
                filters.append(ducking_filter)
            else:
                filters.append(f"volume={volume}")

            # 4. 페이드 인
            if fade_in_duration > 0:
                filters.append(f"afade=t=in:st=0:d={fade_in_duration}")

            # 5. 페이드 아웃
            if fade_out_duration > 0:
                # 페이드 아웃 시작 시간 계산
                duration = target_duration if loop and target_duration else self.get_audio_duration(input_path)
                fade_out_start = max(0, duration - fade_out_duration)
                filters.append(f"afade=t=out:st={fade_out_start}:d={fade_out_duration}")

            filter_chain = ",".join(filters)

            # FFmpeg 명령어 실행
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-af", filter_chain,
                "-y",  # 덮어쓰기
                output_path
            ]

            self.logger.info(f"Applying BGM effects: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.logger.error(f"FFmpeg failed: {result.stderr}")
                return False

            self.logger.info(f"BGM effects applied successfully: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg timeout during BGM processing")
            return False
        except Exception as e:
            self.logger.error(f"Failed to apply BGM effects: {e}", exc_info=True)
            return False

    def mix_audio(
        self,
        voice_path: str,
        bgm_path: str,
        output_path: str,
        voice_volume: float = 1.0,
        bgm_volume: float = 0.3
    ) -> bool:
        """
        음성과 BGM 믹싱

        Args:
            voice_path: 음성 파일 경로
            bgm_path: BGM 파일 경로 (이미 효과 적용됨)
            output_path: 출력 파일 경로
            voice_volume: 음성 볼륨 (0.0-1.0)
            bgm_volume: BGM 볼륨 (0.0-1.0)

        Returns:
            성공 여부
        """
        try:
            # FFmpeg 오디오 믹싱
            # amix 필터를 사용하여 두 오디오 믹싱
            cmd = [
                "ffmpeg",
                "-i", voice_path,
                "-i", bgm_path,
                "-filter_complex",
                f"[0:a]volume={voice_volume}[a0];"
                f"[1:a]volume={bgm_volume}[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2",
                "-y",
                output_path
            ]

            self.logger.info(f"Mixing audio: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.logger.error(f"Audio mixing failed: {result.stderr}")
                return False

            self.logger.info(f"Audio mixed successfully: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg timeout during audio mixing")
            return False
        except Exception as e:
            self.logger.error(f"Failed to mix audio: {e}", exc_info=True)
            return False

    def process_bgm_for_project(
        self,
        project_id: str,
        voice_audio_path: str,
        bgm_file_path: str,
        bgm_settings: Dict[str, Any],
        whisper_result: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        프로젝트의 BGM 처리 및 믹싱 (전체 파이프라인)

        Args:
            project_id: 프로젝트 ID
            voice_audio_path: 음성 오디오 경로
            bgm_file_path: BGM 파일 경로
            bgm_settings: BGM 설정 (volume, fade, ducking 등)
            whisper_result: Whisper STT 결과 (덕킹용)

        Returns:
            최종 믹싱된 오디오 파일 경로
        """
        try:
            # 1. BGM 파일 검증
            if not self.validate_audio_file(bgm_file_path):
                self.logger.error(f"Invalid BGM file: {bgm_file_path}")
                return None

            # 2. 음성 오디오 길이 조회
            voice_duration = self.get_audio_duration(voice_audio_path)
            if voice_duration == 0:
                self.logger.error(f"Invalid voice audio: {voice_audio_path}")
                return None

            # 3. 음성 구간 추출 (덕킹용)
            voice_segments = []
            if bgm_settings.get("ducking_enabled") and whisper_result:
                voice_segments = self.extract_voice_timestamps(voice_audio_path, whisper_result)

            # 4. BGM 효과 적용
            bgm_processed_path = self.output_dir / f"{project_id}_bgm_processed.mp3"

            success = self.apply_bgm_effects(
                input_path=bgm_file_path,
                output_path=str(bgm_processed_path),
                volume=bgm_settings.get("volume", 0.3),
                fade_in_duration=bgm_settings.get("fade_in_duration", 2.0),
                fade_out_duration=bgm_settings.get("fade_out_duration", 2.0),
                start_time=bgm_settings.get("start_time", 0.0),
                end_time=bgm_settings.get("end_time"),
                loop=bgm_settings.get("loop", True),
                target_duration=voice_duration,
                voice_segments=voice_segments,
                ducking_enabled=bgm_settings.get("ducking_enabled", True),
                ducking_level=bgm_settings.get("ducking_level", 0.3)
            )

            if not success:
                self.logger.error("Failed to apply BGM effects")
                return None

            # 5. 음성 + BGM 믹싱
            final_output_path = self.output_dir / f"{project_id}_final_mixed.mp3"

            success = self.mix_audio(
                voice_path=voice_audio_path,
                bgm_path=str(bgm_processed_path),
                output_path=str(final_output_path),
                voice_volume=1.0,  # 음성은 항상 100%
                bgm_volume=1.0  # BGM은 이미 볼륨 조절됨
            )

            if not success:
                self.logger.error("Failed to mix audio")
                return None

            self.logger.info(f"BGM processing complete: {final_output_path}")
            return str(final_output_path)

        except Exception as e:
            self.logger.error(f"BGM processing failed: {e}", exc_info=True)
            return None


# 싱글톤 인스턴스
_bgm_editor_service_instance = None


def get_bgm_editor_service() -> BGMEditorService:
    """BGM 편집 서비스 싱글톤 인스턴스"""
    global _bgm_editor_service_instance
    if _bgm_editor_service_instance is None:
        _bgm_editor_service_instance = BGMEditorService()
    return _bgm_editor_service_instance
