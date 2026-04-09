"""프리젠테이션 영상 생성 서비스 (FFmpeg)

iOS 호환 표준 ffmpeg 옵션은 ffmpeg_profile 모듈에서 단일 관리됨 (ISS-037).
직접 ["-c:v", "libx264", ...] 같은 하드코딩 금지.
"""
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path
import logging
import subprocess
from contextlib import nullcontext

from app.core.config import get_settings
from app.services.ffmpeg_profile import (
    detect_hardware_acceleration,
    ios_safe_audio_encoder_args,
    ios_safe_audio_mux_args,
    ios_safe_full_encode_args,
    ios_safe_video_encoder_args,
    ios_safe_video_output_args,
)

settings = get_settings()

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class PresentationVideoGenerator:
    """
    프리젠테이션 영상 생성 서비스

    특징:
    - FFmpeg 기반 슬라이드 + 오디오 합성
    - 전환 효과 (fade, slide, zoom)
    - 타이밍 정보 기반 자동 동기화
    - 배경음악 믹싱
    - 고해상도 출력 (1920x1080)
    """

    # 기본 해상도
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080

    # 전환 효과 종류
    TRANSITIONS = ["fade", "slide", "zoom", "none"]

    def __init__(self, output_dir: str = "./outputs/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def generate_video(
        self,
        slides: List[Dict[str, Any]],
        audio_path: str,
        output_filename: str,
        transition_effect: str = "fade",
        transition_duration: float = 0.5,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.3
    ) -> str:
        """
        프리젠테이션 영상 생성

        Args:
            slides: 슬라이드 정보 리스트
                [{"image_path": "...", "start_time": 0, "end_time": 5.5, "duration": 5.5}, ...]
            audio_path: 나레이션 오디오 파일 경로
            output_filename: 출력 파일명
            transition_effect: 전환 효과 (fade/slide/zoom/none)
            transition_duration: 전환 시간 (초)
            bgm_path: 배경음악 파일 경로 (옵션)
            bgm_volume: 배경음악 볼륨 (0.0~1.0)

        Returns:
            생성된 영상 파일 경로
        """
        span_context = (
            logfire.span("presentation_video.generate")
            if LOGFIRE_AVAILABLE
            else nullcontext()
        )

        async with span_context:
            self.logger.info(
                f"Generating presentation video: {len(slides)} slides, "
                f"transition={transition_effect}"
            )

            # 검증
            if transition_effect not in self.TRANSITIONS:
                raise ValueError(
                    f"Invalid transition effect: {transition_effect}. "
                    f"Must be one of {self.TRANSITIONS}"
                )

            # 출력 경로
            output_path = self.output_dir / output_filename
            if not output_filename.endswith(".mp4"):
                output_path = output_path.with_suffix(".mp4")

            # 전환 효과가 없으면 단순 합성
            if transition_effect == "none":
                video_path = await self._generate_simple_video(
                    slides=slides,
                    audio_path=audio_path,
                    output_path=str(output_path)
                )
            else:
                video_path = await self._generate_video_with_transitions(
                    slides=slides,
                    audio_path=audio_path,
                    output_path=str(output_path),
                    transition_effect=transition_effect,
                    transition_duration=transition_duration
                )

            # 배경음악 추가 (옵션)
            if bgm_path and Path(bgm_path).exists():
                video_path = await self._add_bgm(
                    video_path=video_path,
                    bgm_path=bgm_path,
                    bgm_volume=bgm_volume
                )

            self.logger.info(f"Video generation complete: {video_path}")
            return video_path

    async def _generate_simple_video(
        self,
        slides: List[Dict[str, Any]],
        audio_path: str,
        output_path: str
    ) -> str:
        """
        전환 효과 없이 단순 영상 생성

        FFmpeg concat demuxer 사용
        """
        # 1. 임시 슬라이드 영상 생성 (이미지 + 시간)
        slide_videos = []
        temp_dir = Path("./temp/slides")
        temp_dir.mkdir(parents=True, exist_ok=True)

        for i, slide in enumerate(slides):
            temp_video = temp_dir / f"slide_{i:03d}.mp4"
            await self._create_slide_video(
                image_path=slide["image_path"],
                duration=slide["duration"],
                output_path=str(temp_video)
            )
            slide_videos.append(str(temp_video))

        # 2. concat 파일 생성
        concat_file = temp_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for video in slide_videos:
                f.write(f"file '{video}'\n")

        # 3. 슬라이드 영상 합치기
        temp_video_path = temp_dir / "merged.mp4"
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(temp_video_path)
        ]
        await self._run_ffmpeg(concat_cmd)

        # 4. 오디오 합성 (iOS 호환 표준은 ffmpeg_profile.ios_safe_audio_mux_args에서 관리)
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video_path),
            "-i", audio_path,
        ]
        final_cmd.extend(ios_safe_audio_mux_args())
        final_cmd.extend(["-shortest", output_path])
        await self._run_ffmpeg(final_cmd)

        # 임시 파일 삭제
        await self._cleanup_temp_files(temp_dir)

        return output_path

    async def _generate_video_with_transitions(
        self,
        slides: List[Dict[str, Any]],
        audio_path: str,
        output_path: str,
        transition_effect: str,
        transition_duration: float
    ) -> str:
        """
        전환 효과를 포함한 영상 생성

        FFmpeg xfade filter 사용
        """
        temp_dir = Path("./temp/slides")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 1. 각 슬라이드를 개별 영상으로 생성
        slide_videos = []
        for i, slide in enumerate(slides):
            temp_video = temp_dir / f"slide_{i:03d}.mp4"
            await self._create_slide_video(
                image_path=slide["image_path"],
                duration=slide["duration"],
                output_path=str(temp_video)
            )
            slide_videos.append(str(temp_video))

        # 2. xfade filter chain 생성
        filter_complex = self._build_xfade_filter(
            slides=slides,
            transition_effect=transition_effect,
            transition_duration=transition_duration
        )

        # 3. FFmpeg 명령어 생성
        inputs = []
        for video in slide_videos:
            inputs.extend(["-i", video])

        temp_video_path = temp_dir / "merged.mp4"

        # Detect hardware acceleration (ffmpeg_profile 단일 관리)
        hw_accel = self._get_hardware_acceleration()
        use_hw = hw_accel is not None

        xfade_cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
        ]
        # 비디오 인코더 (HW 가속 또는 SW ultrafast — 둘 다 iOS 호환 표준 강제됨)
        xfade_cmd.extend(
            ios_safe_video_encoder_args(
                use_hw_acceleration=use_hw,
                preset="ultrafast",  # xfade는 빠른 인코딩 우선
                crf="23",
            )
        )
        # 표준 출력 args (yuv420p, 30fps CFR, faststart)
        xfade_cmd.extend(ios_safe_video_output_args())
        xfade_cmd.append(str(temp_video_path))

        await self._run_ffmpeg(xfade_cmd)

        # 4. 오디오 합성 (iOS 호환 표준은 ffmpeg_profile.ios_safe_audio_mux_args에서 관리)
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video_path),
            "-i", audio_path,
        ]
        final_cmd.extend(ios_safe_audio_mux_args())
        final_cmd.extend(["-shortest", output_path])
        await self._run_ffmpeg(final_cmd)

        # 임시 파일 삭제
        await self._cleanup_temp_files(temp_dir)

        return output_path

    async def _create_slide_video(
        self,
        image_path: str,
        duration: float,
        output_path: str
    ) -> None:
        """
        이미지를 영상으로 변환 (최적화된 FFmpeg 파라미터)
        """
        # Detect hardware acceleration
        hw_accel = self._get_hardware_acceleration()

        cmd = [
            "ffmpeg", "-y",
        ]

        # Add hardware acceleration input if available
        if hw_accel:
            cmd.extend(hw_accel["input"])

        cmd.extend([
            "-loop", "1",
            "-i", image_path,
            "-t", str(duration),
            "-vf", f"scale={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}:force_original_aspect_ratio=decrease,"
                   f"pad={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1",
        ])

        # 비디오 인코더 (HW 가속 또는 SW ultrafast + stillimage tune)
        # ffmpeg_profile이 iOS 호환 profile/level/fps/CFR을 강제 적용
        use_hw = hw_accel is not None
        cmd.extend(
            ios_safe_video_encoder_args(
                use_hw_acceleration=use_hw,
                preset="ultrafast",
                crf="23",
                extra_tune="stillimage" if not use_hw else None,
            )
        )
        cmd.extend(ios_safe_video_output_args())
        cmd.append(output_path)

        await self._run_ffmpeg(cmd)

    def _build_xfade_filter(
        self,
        slides: List[Dict[str, Any]],
        transition_effect: str,
        transition_duration: float
    ) -> str:
        """
        xfade filter chain 생성

        예시:
        [0:v][1:v]xfade=transition=fade:duration=0.5:offset=5.0[v01];
        [v01][2:v]xfade=transition=fade:duration=0.5:offset=10.0[v12];
        """
        if len(slides) == 1:
            return "[0:v]null[out]"

        filter_parts = []
        current_offset = 0.0

        for i in range(len(slides) - 1):
            current_duration = slides[i]["duration"]
            offset = current_offset + current_duration - transition_duration

            if i == 0:
                input_label = f"[0:v][{i+1}:v]"
            else:
                input_label = f"[v{i-1}{i}][{i+1}:v]"

            output_label = f"[v{i}{i+1}]"

            # 마지막 전환
            if i == len(slides) - 2:
                output_label = "[out]"

            filter_parts.append(
                f"{input_label}xfade=transition={transition_effect}:"
                f"duration={transition_duration}:offset={offset:.2f}{output_label}"
            )

            current_offset += current_duration

        return ";".join(filter_parts)

    async def _add_bgm(
        self,
        video_path: str,
        bgm_path: str,
        bgm_volume: float
    ) -> str:
        """
        배경음악 추가 (나레이션과 믹싱)

        Args:
            video_path: 원본 영상 경로
            bgm_path: 배경음악 파일 경로
            bgm_volume: 배경음악 볼륨 (0.0~1.0)

        Returns:
            배경음악이 추가된 영상 경로
        """
        output_path = str(Path(video_path).with_stem(f"{Path(video_path).stem}_with_bgm"))

        # 오디오 믹싱 (narration 1.0, bgm 설정값)
        # ※ aout은 amix filter 결과이므로 -af aresample 미적용 (이중 필터 방지)
        # iOS 호환 표준은 ffmpeg_profile.ios_safe_audio_encoder_args에서 관리
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-stream_loop", "-1",  # BGM 루프
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]volume={bgm_volume}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
        ]
        cmd.extend(ios_safe_audio_encoder_args(include_async_filter=False))
        cmd.extend(["-movflags", "+faststart", output_path])

        await self._run_ffmpeg(cmd)

        # 원본 파일 삭제
        Path(video_path).unlink()

        return output_path

    async def _run_ffmpeg(
        self,
        cmd: List[str],
        progress_callback: Optional[callable] = None
    ) -> None:
        """
        FFmpeg 명령어 실행 (진행률 콜백 지원)

        Args:
            cmd: FFmpeg 명령어 리스트
            progress_callback: 진행률 콜백 함수 (0.0 ~ 1.0)

        Raises:
            RuntimeError: FFmpeg 실행 실패 시
        """
        self.logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

        # Add progress reporting if callback provided
        if progress_callback:
            # Insert progress flag before output file
            output_file = cmd[-1]
            cmd = cmd[:-1] + ["-progress", "pipe:1", output_file]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Monitor progress if callback provided
        if progress_callback:
            asyncio.create_task(
                self._monitor_ffmpeg_progress(process, progress_callback)
            )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode()
            self.logger.error(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"FFmpeg failed with return code {process.returncode}: {error_msg}")

        self.logger.debug("FFmpeg command completed successfully")

    async def _monitor_ffmpeg_progress(
        self,
        process: asyncio.subprocess.Process,
        callback: callable
    ) -> None:
        """
        Monitor FFmpeg progress and call callback

        Args:
            process: FFmpeg subprocess
            callback: Progress callback function
        """
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                # Parse progress (time=00:00:05.00)
                line_str = line.decode().strip()
                if line_str.startswith("out_time_ms="):
                    time_ms = int(line_str.split("=")[1])
                    # TODO: Calculate percentage based on total duration
                    # For now, just report that work is happening
                    callback(0.5)  # 50% placeholder

        except Exception as e:
            self.logger.error(f"Progress monitoring error: {e}")

    async def _cleanup_temp_files(self, temp_dir: Path) -> None:
        """
        임시 파일 삭제
        """
        import shutil
        await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)
        self.logger.debug(f"Cleaned up temp directory: {temp_dir}")

    def _get_hardware_acceleration(self) -> Optional[Dict[str, List[str]]]:
        """
        하드웨어 가속 검출 — ffmpeg_profile.detect_hardware_acceleration()의 wrapper.

        ISS-037 이후 모든 iOS 호환 옵션은 ffmpeg_profile 모듈이 단일 관리한다.
        이 wrapper는 기존 호출 사이트와의 호환성을 위해 유지된다.
        """
        result = detect_hardware_acceleration()
        if result is None:
            self.logger.info("Hardware acceleration not available, using software encoding")
        return result

    def estimate_generation_time(self, total_slides: int) -> int:
        """
        예상 생성 시간 계산

        Args:
            total_slides: 총 슬라이드 수

        Returns:
            예상 시간 (초)
        """
        # Hardware acceleration reduces time by ~50%
        hw_accel = self._get_hardware_acceleration()
        base_time = total_slides * 5 + 10

        if hw_accel:
            return int(base_time * 0.5)  # 50% faster with HW acceleration

        # With ultrafast preset: 20% faster than medium
        return int(base_time * 0.8)


# 싱글톤 인스턴스
_video_generator_instance = None


def get_video_generator() -> PresentationVideoGenerator:
    """PresentationVideoGenerator 싱글톤 인스턴스"""
    global _video_generator_instance
    if _video_generator_instance is None:
        _video_generator_instance = PresentationVideoGenerator()
    return _video_generator_instance
