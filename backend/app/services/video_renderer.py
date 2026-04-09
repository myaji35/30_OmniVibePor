"""SlideVideoRenderer - 영상 클립 + 오디오 + 자막 → 최종 렌더링

FFmpeg 기반 고품질 영상 렌더링 시스템:
- 여러 클립 병합 (전환 효과 지원)
- 오디오 믹싱 (나레이션 + BGM)
- 자막 오버레이
- 플랫폼별 최적화 (YouTube, Instagram, TikTok)

iOS 호환 표준 ffmpeg 옵션은 ffmpeg_profile 모듈에서 단일 관리됨 (ISS-037).
"""

from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
import logging
import subprocess
import tempfile
import time
from contextlib import nullcontext
import ffmpeg
import os

from app.core.config import get_settings
from app.services.ffmpeg_profile import (
    IOS_SAFE_AUDIO_SAMPLE_RATE,
    ios_safe_audio_encoder_args,
    ios_safe_audio_mux_args,
    ios_safe_concat_demuxer_args,
    ios_safe_subtitle_burn_args,
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


# 플랫폼별 사양
PLATFORM_SPECS = {
    "youtube": {
        "resolution": "1920x1080",  # 16:9
        "width": 1920,
        "height": 1080,
        "bitrate": "8M",
        "fps": 30,
        "audio_bitrate": "192k",
        "description": "YouTube 최적화 (Full HD, 16:9)"
    },
    "instagram": {
        "resolution": "1080x1350",  # 4:5 (피드)
        "width": 1080,
        "height": 1350,
        "bitrate": "5M",
        "fps": 30,
        "audio_bitrate": "128k",
        "description": "Instagram 피드 최적화 (4:5)"
    },
    "instagram_story": {
        "resolution": "1080x1920",  # 9:16 (스토리/릴스)
        "width": 1080,
        "height": 1920,
        "bitrate": "4M",
        "fps": 30,
        "audio_bitrate": "128k",
        "description": "Instagram 스토리/릴스 최적화 (9:16)"
    },
    "tiktok": {
        "resolution": "1080x1920",  # 9:16
        "width": 1080,
        "height": 1920,
        "bitrate": "4M",
        "fps": 30,
        "audio_bitrate": "128k",
        "description": "TikTok 최적화 (9:16)"
    },
    "facebook": {
        "resolution": "1280x720",  # 16:9 (HD)
        "width": 1280,
        "height": 720,
        "bitrate": "6M",
        "fps": 30,
        "audio_bitrate": "128k",
        "description": "Facebook 최적화 (720p)"
    },
}


# FFmpeg xfade 전환 효과 (30가지 중 엄선)
TRANSITION_EFFECTS = {
    "fade": {
        "name": "fade",
        "description": "페이드 전환 (기본)"
    },
    "wipeleft": {
        "name": "wipeleft",
        "description": "왼쪽에서 와이프"
    },
    "wiperight": {
        "name": "wiperight",
        "description": "오른쪽에서 와이프"
    },
    "wipeup": {
        "name": "wipeup",
        "description": "위에서 와이프"
    },
    "wipedown": {
        "name": "wipedown",
        "description": "아래에서 와이프"
    },
    "slideleft": {
        "name": "slideleft",
        "description": "왼쪽으로 슬라이드"
    },
    "slideright": {
        "name": "slideright",
        "description": "오른쪽으로 슬라이드"
    },
    "slideup": {
        "name": "slideup",
        "description": "위로 슬라이드"
    },
    "slidedown": {
        "name": "slidedown",
        "description": "아래로 슬라이드"
    },
    "circlecrop": {
        "name": "circlecrop",
        "description": "원형 크롭 전환"
    },
    "rectcrop": {
        "name": "rectcrop",
        "description": "사각형 크롭 전환"
    },
    "distance": {
        "name": "distance",
        "description": "거리 왜곡 전환"
    },
    "fadeblack": {
        "name": "fadeblack",
        "description": "검은색으로 페이드"
    },
    "fadewhite": {
        "name": "fadewhite",
        "description": "흰색으로 페이드"
    },
    "radial": {
        "name": "radial",
        "description": "방사형 전환"
    },
    "smoothleft": {
        "name": "smoothleft",
        "description": "부드러운 왼쪽 전환"
    },
    "smoothright": {
        "name": "smoothright",
        "description": "부드러운 오른쪽 전환"
    },
    "smoothup": {
        "name": "smoothup",
        "description": "부드러운 위쪽 전환"
    },
    "smoothdown": {
        "name": "smoothdown",
        "description": "부드러운 아래쪽 전환"
    },
    "circleopen": {
        "name": "circleopen",
        "description": "원형 열기"
    },
    "circleclose": {
        "name": "circleclose",
        "description": "원형 닫기"
    },
    "vertopen": {
        "name": "vertopen",
        "description": "수직 열기"
    },
    "vertclose": {
        "name": "vertclose",
        "description": "수직 닫기"
    },
    "horzopen": {
        "name": "horzopen",
        "description": "수평 열기"
    },
    "horzclose": {
        "name": "horzclose",
        "description": "수평 닫기"
    },
    "dissolve": {
        "name": "dissolve",
        "description": "디졸브 전환"
    },
    "pixelize": {
        "name": "pixelize",
        "description": "픽셀화 전환"
    },
    "diagtl": {
        "name": "diagtl",
        "description": "대각선 (왼쪽 위)"
    },
    "diagtr": {
        "name": "diagtr",
        "description": "대각선 (오른쪽 위)"
    },
    "diagbl": {
        "name": "diagbl",
        "description": "대각선 (왼쪽 아래)"
    },
    "diagbr": {
        "name": "diagbr",
        "description": "대각선 (오른쪽 아래)"
    },
}


# 자막 스타일 프리셋
SUBTITLE_STYLES = {
    "default": {
        "fontsize": 24,
        "fontcolor": "white",
        "borderw": 2,
        "bordercolor": "black",
        "alignment": 2,  # 하단 중앙
        "margin_v": 50,
        "description": "기본 스타일 (하단 중앙, 흰색 글자, 검은색 테두리)"
    },
    "youtube": {
        "fontsize": 28,
        "fontcolor": "white",
        "borderw": 3,
        "bordercolor": "black",
        "alignment": 2,
        "margin_v": 80,
        "description": "YouTube 스타일 (큰 폰트, 하단 중앙)"
    },
    "tiktok": {
        "fontsize": 32,
        "fontcolor": "yellow",
        "borderw": 4,
        "bordercolor": "black",
        "alignment": 5,  # 중앙
        "margin_v": 0,
        "description": "TikTok 스타일 (노란색, 중앙, 큰 폰트)"
    },
    "instagram": {
        "fontsize": 26,
        "fontcolor": "white",
        "borderw": 2,
        "bordercolor": "black",
        "alignment": 2,
        "margin_v": 60,
        "description": "Instagram 스타일 (하단 중앙)"
    },
    "minimal": {
        "fontsize": 22,
        "fontcolor": "white",
        "borderw": 1,
        "bordercolor": "black",
        "alignment": 2,
        "margin_v": 40,
        "description": "미니멀 스타일 (작은 폰트, 얇은 테두리)"
    },
}


class VideoRenderer:
    """
    SlideVideoRenderer - FFmpeg 기반 영상 렌더링 시스템

    주요 기능:
    1. 여러 영상 클립 병합 (전환 효과 지원)
    2. 오디오 믹싱 (나레이션 + BGM)
    3. 자막 오버레이
    4. 플랫폼별 최적화

    사용 예:
        renderer = VideoRenderer()
        result = await renderer.render_video(
            video_clips=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
            audio_path="narration.mp3",
            output_path="final.mp4",
            subtitle_path="subtitles.srt",
            transitions=["fade", "wipeleft", "slideup"],
            bgm_path="background.mp3",
            bgm_volume=0.2
        )
    """

    def __init__(self, output_dir: str = "./outputs/videos"):
        """
        Args:
            output_dir: 렌더링된 영상 저장 경로
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # FFmpeg 설치 확인
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """FFmpeg 설치 확인"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            self.logger.info("✅ FFmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(
                "❌ FFmpeg not found. Please install FFmpeg:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu: apt-get install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org/"
            )
            raise RuntimeError("FFmpeg is required but not installed") from e

    async def render_video(
        self,
        video_clips: List[str],
        audio_path: str,
        output_path: str,
        subtitle_path: Optional[str] = None,
        transitions: Optional[List[str]] = None,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.2,
        transition_duration: float = 0.5,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        최종 영상 렌더링 (전체 파이프라인)

        워크플로우:
        1. 클립 병합 (전환 효과 적용)
        2. 오디오 믹싱 (나레이션 + BGM)
        3. 자막 오버레이
        4. 플랫폼별 최적화

        Args:
            video_clips: 영상 클립 경로 리스트
            audio_path: 나레이션 오디오 경로
            output_path: 최종 영상 저장 경로
            subtitle_path: 자막 파일 경로 (.srt)
            transitions: 전환 효과 리스트 (클립 개수 - 1)
            bgm_path: 배경음악 경로
            bgm_volume: BGM 볼륨 (0.0-1.0)
            transition_duration: 전환 효과 지속 시간 (초)
            platform: 플랫폼별 최적화 ("youtube", "instagram", "tiktok" 등)

        Returns:
            {
                "status": "success",
                "output_path": "최종 영상 경로",
                "file_size_mb": 파일 크기 (MB),
                "render_time": 렌더링 시간 (초),
                "steps": {
                    "merge_clips": {...},
                    "audio_mix": {...},
                    "subtitles": {...},
                    "platform_optimize": {...}
                }
            }
        """
        span_context = logfire.span("video_renderer.render") if LOGFIRE_AVAILABLE else nullcontext()

        async with span_context as main_span:
            start_time = time.time()

            self.logger.info(
                f"🎬 Starting video rendering pipeline:\n"
                f"  Clips: {len(video_clips)}\n"
                f"  Audio: {audio_path}\n"
                f"  Output: {output_path}\n"
                f"  Subtitles: {subtitle_path or 'None'}\n"
                f"  BGM: {bgm_path or 'None'}\n"
                f"  Platform: {platform or 'Generic'}"
            )

            # Logfire 속성
            if LOGFIRE_AVAILABLE:
                main_span.set_attribute("clip_count", len(video_clips))
                main_span.set_attribute("has_subtitles", subtitle_path is not None)
                main_span.set_attribute("has_bgm", bgm_path is not None)
                main_span.set_attribute("platform", platform or "generic")

            steps_info = {}
            current_video = None

            try:
                # 1️⃣ 클립 병합
                if len(video_clips) == 1:
                    self.logger.info("📹 Single clip, skipping merge step")
                    current_video = video_clips[0]
                    steps_info["merge_clips"] = {
                        "skipped": True,
                        "reason": "single_clip"
                    }
                else:
                    merged_path = str(self.output_dir / f"merged_{int(time.time())}.mp4")
                    merge_result = self.merge_clips(
                        clips=video_clips,
                        output_path=merged_path,
                        transitions=transitions,
                        transition_duration=transition_duration
                    )
                    current_video = merged_path
                    steps_info["merge_clips"] = merge_result

                # 2️⃣ 오디오 믹싱
                with_audio_path = str(self.output_dir / f"with_audio_{int(time.time())}.mp4")
                audio_result = self.add_audio_mix(
                    video_path=current_video,
                    audio_path=audio_path,
                    bgm_path=bgm_path,
                    output_path=with_audio_path,
                    bgm_volume=bgm_volume
                )
                current_video = with_audio_path
                steps_info["audio_mix"] = audio_result

                # 3️⃣ 자막 오버레이 (선택적)
                if subtitle_path:
                    with_subtitle_path = str(self.output_dir / f"with_subtitle_{int(time.time())}.mp4")
                    subtitle_result = self.add_subtitles_overlay(
                        video_path=current_video,
                        subtitle_path=subtitle_path,
                        output_path=with_subtitle_path,
                        style=platform or "default"
                    )
                    current_video = with_subtitle_path
                    steps_info["subtitles"] = subtitle_result
                else:
                    self.logger.info("📝 No subtitles, skipping overlay step")
                    steps_info["subtitles"] = {
                        "skipped": True,
                        "reason": "no_subtitle_file"
                    }

                # 4️⃣ 플랫폼별 최적화 (선택적)
                if platform and platform in PLATFORM_SPECS:
                    optimize_result = self.optimize_for_platform(
                        video_path=current_video,
                        platform=platform,
                        output_path=output_path
                    )
                    steps_info["platform_optimize"] = optimize_result
                else:
                    # 최적화 없이 최종 경로로 복사
                    import shutil
                    shutil.copy(current_video, output_path)
                    self.logger.info(f"📦 No platform optimization, copied to {output_path}")
                    steps_info["platform_optimize"] = {
                        "skipped": True,
                        "reason": "no_platform_specified"
                    }

                # 임시 파일 정리
                self._cleanup_temp_files([
                    steps_info.get("merge_clips", {}).get("output_path"),
                    steps_info.get("audio_mix", {}).get("output_path"),
                    steps_info.get("subtitles", {}).get("output_path"),
                ])

                # 최종 통계
                render_time = time.time() - start_time
                file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB

                self.logger.info(
                    f"✅ Rendering completed in {render_time:.1f}s\n"
                    f"  Output: {output_path}\n"
                    f"  Size: {file_size:.2f} MB"
                )

                return {
                    "status": "success",
                    "output_path": output_path,
                    "file_size_mb": round(file_size, 2),
                    "render_time": round(render_time, 2),
                    "steps": steps_info
                }

            except Exception as e:
                self.logger.error(f"❌ Rendering failed: {e}", exc_info=True)
                raise

    def merge_clips(
        self,
        clips: List[str],
        output_path: str,
        transitions: Optional[List[str]] = None,
        transition_duration: float = 0.5
    ) -> Dict[str, Any]:
        """
        여러 클립 병합 (전환 효과 지원)

        Args:
            clips: 영상 클립 경로 리스트
            output_path: 병합된 영상 저장 경로
            transitions: 전환 효과 리스트 (None이면 단순 concat)
            transition_duration: 전환 효과 지속 시간 (초)

        Returns:
            {
                "output_path": "병합된 영상 경로",
                "method": "concat" | "xfade",
                "clip_count": 클립 개수,
                "transitions_used": 사용된 전환 효과
            }
        """
        span_context = logfire.span("video_renderer.merge_clips") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            self.logger.info(f"🔗 Merging {len(clips)} clips...")

            # 전환 효과 없으면 단순 concat
            if not transitions:
                return self._simple_concat(clips, output_path)

            # 전환 효과 개수 검증
            expected_transitions = len(clips) - 1
            if len(transitions) != expected_transitions:
                self.logger.warning(
                    f"⚠️ Transition count mismatch: expected {expected_transitions}, "
                    f"got {len(transitions)}. Using simple concat instead."
                )
                return self._simple_concat(clips, output_path)

            # xfade 필터로 전환 효과 적용
            return self._merge_with_transitions(
                clips, output_path, transitions, transition_duration
            )

    def _simple_concat(self, clips: List[str], output_path: str) -> Dict[str, Any]:
        """
        단순 클립 병합 (전환 효과 없음)

        FFmpeg concat demuxer 사용
        """
        start_time = time.time()

        # concat.txt 파일 생성
        concat_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        )

        try:
            for clip in clips:
                # 절대 경로로 변환
                abs_clip = str(Path(clip).resolve())
                concat_file.write(f"file '{abs_clip}'\n")

            concat_file.close()

            # FFmpeg concat demuxer (재인코딩 없이 빠른 결합)
            # 결합 대상 클립들이 모두 ios_safe 표준으로 인코딩되어 있어야 함
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file.name,
            ]
            cmd.extend(ios_safe_concat_demuxer_args())
            cmd.extend(["-y", output_path])

            self.logger.debug(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            elapsed = time.time() - start_time

            self.logger.info(
                f"✅ Clips concatenated in {elapsed:.1f}s (method: concat)"
            )

            return {
                "output_path": output_path,
                "method": "concat",
                "clip_count": len(clips),
                "transitions_used": None,
                "elapsed_time": round(elapsed, 2)
            }

        finally:
            # concat 파일 삭제
            Path(concat_file.name).unlink(missing_ok=True)

    def _merge_with_transitions(
        self,
        clips: List[str],
        output_path: str,
        transitions: List[str],
        transition_duration: float
    ) -> Dict[str, Any]:
        """
        전환 효과를 적용한 클립 병합

        FFmpeg xfade 필터 사용
        """
        start_time = time.time()

        # 전환 효과 검증 및 매핑
        validated_transitions = []
        for t in transitions:
            if t in TRANSITION_EFFECTS:
                validated_transitions.append(TRANSITION_EFFECTS[t]["name"])
            else:
                self.logger.warning(
                    f"⚠️ Unknown transition '{t}', using 'fade' instead"
                )
                validated_transitions.append("fade")

        # 각 클립의 길이 추출 (xfade offset 계산용)
        clip_durations = []
        for clip in clips:
            probe = ffmpeg.probe(clip)
            duration = float(probe['format']['duration'])
            clip_durations.append(duration)

        self.logger.debug(f"Clip durations: {clip_durations}")

        # xfade 필터 체인 생성
        # [0:v][1:v]xfade=transition=fade:duration=0.5:offset=2.5[v01];
        # [v01][2:v]xfade=transition=wipeleft:duration=0.5:offset=5.0[v02];

        filter_parts = []
        offset = 0.0

        for i, transition in enumerate(validated_transitions):
            if i == 0:
                # 첫 번째 전환: [0:v][1:v]
                offset = clip_durations[0] - transition_duration
                filter_parts.append(
                    f"[0:v][1:v]xfade=transition={transition}:"
                    f"duration={transition_duration}:offset={offset}[v{i+1}]"
                )
            else:
                # 이후 전환: [vN][N+1:v]
                offset += clip_durations[i] - transition_duration
                filter_parts.append(
                    f"[v{i}][{i+1}:v]xfade=transition={transition}:"
                    f"duration={transition_duration}:offset={offset}[v{i+1}]"
                )

        filter_complex = ";".join(filter_parts)
        final_output = f"[v{len(clips)-1}]"

        self.logger.debug(f"Filter complex: {filter_complex}")

        # FFmpeg 명령 구성
        cmd = ["ffmpeg"]

        # 입력 파일들
        for clip in clips:
            cmd.extend(["-i", clip])

        # 필터 및 출력 (iOS 호환 표준은 ffmpeg_profile에서 관리)
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", final_output,
        ])
        cmd.extend(ios_safe_video_encoder_args(preset="medium", crf="23"))
        cmd.extend(ios_safe_video_output_args(threads=None))
        cmd.extend(["-y", output_path])

        self.logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        elapsed = time.time() - start_time

        self.logger.info(
            f"✅ Clips merged with transitions in {elapsed:.1f}s\n"
            f"  Transitions: {', '.join(validated_transitions)}"
        )

        return {
            "output_path": output_path,
            "method": "xfade",
            "clip_count": len(clips),
            "transitions_used": validated_transitions,
            "transition_duration": transition_duration,
            "elapsed_time": round(elapsed, 2)
        }

    def add_audio_mix(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.2
    ) -> Dict[str, Any]:
        """
        오디오 믹싱 (나레이션 + BGM)

        Args:
            video_path: 입력 영상 경로
            audio_path: 나레이션 오디오 경로
            output_path: 출력 영상 경로
            bgm_path: 배경음악 경로 (선택적)
            bgm_volume: BGM 볼륨 (0.0-1.0)

        Returns:
            {
                "output_path": "오디오 믹싱된 영상 경로",
                "has_bgm": True/False,
                "bgm_volume": 볼륨 값
            }
        """
        span_context = logfire.span("video_renderer.audio_mix") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            start_time = time.time()

            if not bgm_path:
                # BGM 없으면 단순 오디오 병합
                self.logger.info("🎵 Adding narration audio (no BGM)...")

                # iOS 호환 표준은 ffmpeg_profile.ios_safe_audio_mux_args에서 관리
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                ]
                cmd.extend(ios_safe_audio_mux_args())
                cmd.extend([
                    "-map", "0:v:0",  # 영상은 첫 번째 입력
                    "-map", "1:a:0",  # 오디오는 두 번째 입력
                    "-shortest",  # 짧은 쪽에 맞춤
                    "-y",
                    output_path
                ])

                self.logger.debug(f"Running: {' '.join(cmd)}")

                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                elapsed = time.time() - start_time

                self.logger.info(f"✅ Audio added in {elapsed:.1f}s")

                return {
                    "output_path": output_path,
                    "has_bgm": False,
                    "bgm_volume": 0.0,
                    "elapsed_time": round(elapsed, 2)
                }

            else:
                # BGM 있으면 amix 필터로 믹싱
                self.logger.info(
                    f"🎵 Mixing narration + BGM (volume: {bgm_volume})..."
                )

                # amix 필터: 나레이션 100% + BGM 20%
                filter_complex = (
                    f"[1:a]volume=1.0[a1];"
                    f"[2:a]volume={bgm_volume}[a2];"
                    f"[a1][a2]amix=inputs=2:duration=first[aout]"
                )

                # BGM 믹스: 비디오는 copy, 오디오는 amix 후 AAC 48kHz
                # ※ aout은 amix filter 결과이므로 -af aresample은 적용하지 않음 (이중 필터 방지)
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                    "-i", bgm_path,
                    "-filter_complex", filter_complex,
                    "-map", "0:v:0",
                    "-map", "[aout]",
                    "-c:v", "copy",
                ]
                # 오디오는 async 필터 제외 (filter_complex amix가 이미 처리)
                cmd.extend(ios_safe_audio_encoder_args(include_async_filter=False))
                cmd.extend([
                    "-movflags", "+faststart",
                    "-shortest",
                    "-y",
                    output_path
                ])

                self.logger.debug(f"Running: {' '.join(cmd)}")

                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                elapsed = time.time() - start_time

                self.logger.info(
                    f"✅ Audio mixed in {elapsed:.1f}s "
                    f"(narration + BGM at {bgm_volume*100:.0f}%)"
                )

                return {
                    "output_path": output_path,
                    "has_bgm": True,
                    "bgm_volume": bgm_volume,
                    "elapsed_time": round(elapsed, 2)
                }

    def add_subtitles_overlay(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style: str = "default"
    ) -> Dict[str, Any]:
        """
        자막 오버레이

        Args:
            video_path: 입력 영상 경로
            subtitle_path: 자막 파일 경로 (.srt)
            output_path: 출력 영상 경로
            style: 자막 스타일 ("default", "youtube", "tiktok", "instagram", "minimal")

        Returns:
            {
                "output_path": "자막이 추가된 영상 경로",
                "style": 사용된 스타일,
                "subtitle_file": 자막 파일 경로
            }
        """
        span_context = logfire.span("video_renderer.add_subtitles") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            start_time = time.time()

            # 스타일 선택
            if style not in SUBTITLE_STYLES:
                self.logger.warning(
                    f"⚠️ Unknown subtitle style '{style}', using 'default'"
                )
                style = "default"

            style_config = SUBTITLE_STYLES[style]

            self.logger.info(
                f"📝 Adding subtitles (style: {style})..."
            )

            # 자막 파일 경로 이스케이프 (Windows 호환)
            subtitle_path_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")

            # subtitles 필터
            # force_style: 스타일 강제 적용
            force_style = (
                f"FontSize={style_config['fontsize']},"
                f"PrimaryColour=&H{self._color_to_ass(style_config['fontcolor'])},"
                f"OutlineColour=&H{self._color_to_ass(style_config['bordercolor'])},"
                f"BorderStyle=1,"
                f"Outline={style_config['borderw']},"
                f"Alignment={style_config['alignment']},"
                f"MarginV={style_config['margin_v']}"
            )

            # 자막 burn-in: 비디오 재인코딩 필수, 오디오 copy
            # iOS 호환 표준은 ffmpeg_profile.ios_safe_subtitle_burn_args에서 관리
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"subtitles={subtitle_path_escaped}:force_style='{force_style}'",
            ]
            cmd.extend(ios_safe_subtitle_burn_args())
            cmd.extend(["-y", output_path])

            self.logger.debug(f"Running: {' '.join(cmd)}")

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            elapsed = time.time() - start_time

            self.logger.info(
                f"✅ Subtitles added in {elapsed:.1f}s (style: {style})"
            )

            return {
                "output_path": output_path,
                "style": style,
                "subtitle_file": subtitle_path,
                "elapsed_time": round(elapsed, 2)
            }

    def optimize_for_platform(
        self,
        video_path: str,
        platform: str,
        output_path: str
    ) -> Dict[str, Any]:
        """
        플랫폼별 최적화 (해상도, 비트레이트, FPS)

        Args:
            video_path: 입력 영상 경로
            platform: 플랫폼 ("youtube", "instagram", "tiktok", "facebook")
            output_path: 출력 영상 경로

        Returns:
            {
                "output_path": "최적화된 영상 경로",
                "platform": 플랫폼 이름,
                "resolution": 해상도,
                "bitrate": 비트레이트
            }
        """
        span_context = logfire.span("video_renderer.platform_optimize") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            start_time = time.time()

            if platform not in PLATFORM_SPECS:
                raise ValueError(
                    f"Unknown platform '{platform}'. "
                    f"Available: {', '.join(PLATFORM_SPECS.keys())}"
                )

            spec = PLATFORM_SPECS[platform]

            self.logger.info(
                f"📱 Optimizing for {platform}:\n"
                f"  Resolution: {spec['resolution']}\n"
                f"  Bitrate: {spec['bitrate']}\n"
                f"  FPS: {spec['fps']}"
            )

            # scale 필터: 종횡비 유지하며 리사이징 + 패딩
            scale_filter = (
                f"scale={spec['width']}:{spec['height']}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={spec['width']}:{spec['height']}:(ow-iw)/2:(oh-ih)/2"
            )

            # 플랫폼별 fps/bitrate는 spec이 우선 (iOS 호환 profile/level/pix_fmt는 표준 유지)
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", scale_filter,
                "-b:v", spec["bitrate"],
            ]
            cmd.extend(ios_safe_video_encoder_args(preset="medium", crf="23"))
            # platform spec fps로 override (ios_safe 기본 30 대신)
            cmd.extend(ios_safe_video_output_args(include_fps=False, threads=None))
            cmd.extend(["-r", str(spec["fps"])])
            # 오디오 인코더 (platform spec bitrate)
            cmd.extend(
                ios_safe_audio_encoder_args(
                    bitrate=spec["audio_bitrate"],
                    include_async_filter=False,  # 단일 영상 변환이라 불필요
                )
            )
            cmd.extend(["-y", output_path])

            self.logger.debug(f"Running: {' '.join(cmd)}")

            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            elapsed = time.time() - start_time

            self.logger.info(
                f"✅ Platform optimization completed in {elapsed:.1f}s"
            )

            return {
                "output_path": output_path,
                "platform": platform,
                "resolution": spec["resolution"],
                "bitrate": spec["bitrate"],
                "fps": spec["fps"],
                "elapsed_time": round(elapsed, 2)
            }

    def _color_to_ass(self, color: str) -> str:
        """
        CSS 색상을 ASS 자막 형식으로 변환

        Args:
            color: CSS 색상 ("white", "black", "yellow" 등)

        Returns:
            ASS 색상 코드 (BGR 형식)
        """
        color_map = {
            "white": "FFFFFF",
            "black": "000000",
            "yellow": "00FFFF",
            "red": "0000FF",
            "green": "00FF00",
            "blue": "FF0000",
            "cyan": "FFFF00",
            "magenta": "FF00FF",
        }

        return color_map.get(color.lower(), "FFFFFF")

    def _cleanup_temp_files(self, file_paths: List[Optional[str]]):
        """임시 파일 정리"""
        for path in file_paths:
            if path and Path(path).exists():
                try:
                    Path(path).unlink()
                    self.logger.debug(f"🗑️  Deleted temp file: {path}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file {path}: {e}")

    def get_available_transitions(self) -> Dict[str, str]:
        """사용 가능한 전환 효과 목록"""
        return {
            name: info["description"]
            for name, info in TRANSITION_EFFECTS.items()
        }

    def get_available_platforms(self) -> Dict[str, str]:
        """사용 가능한 플랫폼 목록"""
        return {
            name: spec["description"]
            for name, spec in PLATFORM_SPECS.items()
        }

    def get_available_subtitle_styles(self) -> Dict[str, str]:
        """사용 가능한 자막 스타일 목록"""
        return {
            name: style["description"]
            for name, style in SUBTITLE_STYLES.items()
        }


# 싱글톤 인스턴스
_renderer_instance = None


def get_video_renderer() -> VideoRenderer:
    """VideoRenderer 싱글톤 인스턴스"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = VideoRenderer()
    return _renderer_instance
