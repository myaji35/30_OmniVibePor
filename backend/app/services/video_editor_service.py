"""FFmpeg 기반 영상 편집 서비스"""
from typing import List, Dict, Tuple
from pathlib import Path
import asyncio
import subprocess
import hashlib
import time
# Logfire는 optional
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from app.core.config import get_settings
from app.services.stt_service import get_stt_service

settings = get_settings()


class VideoEditorService:
    """
import logging
    FFmpeg 기반 슬라이드 영상 편집

    특징:
    - 슬라이드 이미지 + 음성 자동 동기화
    - 타임스탬프 기반 슬라이드 전환
    - 1920x1080 Full HD 출력
    - MP4 (H.264) 형식
    """

    def __init__(self, output_dir: str = "./outputs/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.stt_service = get_stt_service()

    async def create_slide_video(
        self,
        slide_images: List[str],
        audio_files: List[str],
        output_filename: str = None
    ) -> str:
        """
        슬라이드 이미지 + 음성으로 영상 생성

        Args:
            slide_images: 슬라이드 이미지 경로 리스트
            audio_files: 각 슬라이드의 음성 파일 경로 리스트
            output_filename: 출력 파일명 (없으면 자동 생성)

        Returns:
            생성된 영상 파일 경로
        """
        with self.logger.span("video_editor.create_slide_video") as span:
            if len(slide_images) != len(audio_files):
                raise ValueError(
                    f"Slide images ({len(slide_images)}) and audio files "
                    f"({len(audio_files)}) count mismatch"
                )

            total_slides = len(slide_images)
            span.set_attribute("total_slides", total_slides)

            # 1. 각 음성 파일의 길이 계산
            durations = await self._get_audio_durations(audio_files)

            self.logger.info(f"Audio durations: {durations}")

            # 2. 슬라이드별 영상 클립 생성
            video_clips = []
            for i, (image, audio, duration) in enumerate(zip(slide_images, audio_files, durations)):
                clip_path = await self._create_single_clip(
                    image_path=image,
                    audio_path=audio,
                    duration=duration,
                    index=i
                )
                video_clips.append(clip_path)

            # 3. 모든 클립 결합
            final_video = await self._concat_videos(video_clips, output_filename)

            # 4. 임시 클립 삭제
            for clip in video_clips:
                try:
                    Path(clip).unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp clip {clip}: {e}")

            self.logger.info(f"Video created successfully: {final_video}")

            return final_video

    async def _get_audio_durations(self, audio_files: List[str]) -> List[float]:
        """
        각 음성 파일의 길이 계산

        Args:
            audio_files: 음성 파일 경로 리스트

        Returns:
            길이(초) 리스트
        """
        durations = []

        for audio_file in audio_files:
            # FFprobe로 길이 확인
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_file
            ]

            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                duration = float(result.stdout.strip())
                durations.append(duration)

            except Exception as e:
                self.logger.error(f"Failed to get duration for {audio_file}: {e}")
                # Fallback: 5초로 가정
                durations.append(5.0)

        return durations

    async def _create_single_clip(
        self,
        image_path: str,
        audio_path: str,
        duration: float,
        index: int
    ) -> str:
        """
        단일 슬라이드 클립 생성 (이미지 + 음성)

        Args:
            image_path: 슬라이드 이미지 경로
            audio_path: 음성 파일 경로
            duration: 클립 길이 (초)
            index: 슬라이드 인덱스

        Returns:
            생성된 클립 경로
        """
        timestamp = int(time.time())
        clip_filename = f"clip_{timestamp}_{index:03d}.mp4"
        clip_path = self.output_dir / "temp" / clip_filename

        # temp 디렉토리 생성
        clip_path.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg 명령어
        cmd = [
            "ffmpeg",
            "-loop", "1",  # 이미지 루프
            "-i", image_path,  # 입력 이미지
            "-i", audio_path,  # 입력 음성
            "-c:v", "libx264",  # H.264 코덱
            "-t", str(duration),  # 길이
            "-pix_fmt", "yuv420p",  # 픽셀 포맷
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",  # 1920x1080 패딩
            "-c:a", "aac",  # AAC 오디오 코덱
            "-shortest",  # 짧은 쪽에 맞춤
            "-y",  # 덮어쓰기
            str(clip_path)
        ]

        try:
            await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                check=True
            )

            self.logger.info(f"Created clip {index + 1}: {clip_path}")

            return str(clip_path)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise

    async def _concat_videos(
        self,
        video_clips: List[str],
        output_filename: str = None
    ) -> str:
        """
        여러 영상 클립 결합

        Args:
            video_clips: 영상 클립 경로 리스트
            output_filename: 출력 파일명

        Returns:
            최종 영상 경로
        """
        if output_filename is None:
            timestamp = int(time.time())
            output_filename = f"presentation_{timestamp}.mp4"

        output_path = self.output_dir / output_filename

        # concat 파일 생성 (FFmpeg concat demuxer 사용)
        concat_file = self.output_dir / "temp" / f"concat_{int(time.time())}.txt"
        concat_file.parent.mkdir(parents=True, exist_ok=True)

        with open(concat_file, "w") as f:
            for clip in video_clips:
                f.write(f"file '{Path(clip).absolute()}'\n")

        # FFmpeg concat
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",  # 재인코딩 없이 결합
            "-y",
            str(output_path)
        ]

        try:
            await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                check=True
            )

            self.logger.info(f"Concatenated {len(video_clips)} clips: {output_path}")

            # concat 파일 삭제
            concat_file.unlink()

            return str(output_path)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg concat error: {e.stderr.decode()}")
            raise

    async def add_background_music(
        self,
        video_path: str,
        music_path: str,
        music_volume: float = 0.2
    ) -> str:
        """
        배경 음악 추가

        Args:
            video_path: 영상 파일 경로
            music_path: 배경 음악 파일 경로
            music_volume: 음악 볼륨 (0.0-1.0)

        Returns:
            배경 음악이 추가된 영상 경로
        """
        timestamp = int(time.time())
        output_filename = f"video_with_bgm_{timestamp}.mp4"
        output_path = self.output_dir / output_filename

        cmd = [
            "ffmpeg",
            "-i", video_path,  # 원본 영상
            "-i", music_path,  # 배경 음악
            "-filter_complex",
            f"[1:a]volume={music_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first",
            "-c:v", "copy",  # 영상 재인코딩 안 함
            "-c:a", "aac",
            "-y",
            str(output_path)
        ]

        try:
            await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                check=True
            )

            self.logger.info(f"Added background music: {output_path}")

            return str(output_path)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg BGM error: {e.stderr.decode()}")
            raise


# 싱글톤 인스턴스
_video_editor_service_instance = None


def get_video_editor_service() -> VideoEditorService:
    """Video Editor 서비스 싱글톤 인스턴스"""
    global _video_editor_service_instance
    if _video_editor_service_instance is None:
        _video_editor_service_instance = VideoEditorService()
    return _video_editor_service_instance
