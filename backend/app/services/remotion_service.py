"""Remotion Service - React 기반 영상 렌더링 서비스

Remotion을 활용한 프로그래매틱 비디오 생성:
- Director Agent가 생성한 콘티(Storyboard Blocks)를 Remotion Props로 변환
- Celery를 통한 비동기 렌더링
- Cloudinary 자동 업로드
- WebSocket 실시간 진행 상태 업데이트

Features:
- Platform-specific optimization (YouTube, Instagram, TikTok)
- Dynamic composition rendering
- Audio synchronization
- Transition effects
- Professional video quality
"""

import os
import json
import subprocess
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
import logging

from app.core.config import get_settings
from app.services.cloudinary_service import CloudinaryService
from app.services.websocket_manager import get_websocket_manager

settings = get_settings()
logger = logging.getLogger(__name__)

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


# Platform-specific composition settings
PLATFORM_COMPOSITIONS = {
    "YouTube": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "codec": "h264",
        "bitrate": "8M",
        "audio_bitrate": "192k"
    },
    "Instagram": {
        "width": 1080,
        "height": 1350,  # 4:5 feed
        "fps": 30,
        "codec": "h264",
        "bitrate": "5M",
        "audio_bitrate": "128k"
    },
    "TikTok": {
        "width": 1080,
        "height": 1920,  # 9:16 vertical
        "fps": 30,
        "codec": "h264",
        "bitrate": "4M",
        "audio_bitrate": "128k"
    },
    "Facebook": {
        "width": 1280,
        "height": 720,
        "fps": 30,
        "codec": "h264",
        "bitrate": "6M",
        "audio_bitrate": "128k"
    }
}


class RemotionService:
    """Remotion 기반 영상 렌더링 서비스"""

    def __init__(self):
        self.cloudinary = CloudinaryService()
        self.ws_manager = get_websocket_manager()
        self.frontend_dir = Path(settings.BASE_DIR).parent / "frontend"
        self.output_dir = Path(settings.OUTPUTS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_storyboard_to_props(
        self,
        storyboard_blocks: List[Dict[str, Any]],
        campaign_concept: Dict[str, str],
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Director Agent의 Storyboard Blocks를 Remotion Props로 변환

        Args:
            storyboard_blocks: Director Agent가 생성한 콘티 블록 리스트
            campaign_concept: 캠페인 컨셉 (gender, tone, style, platform)
            audio_url: 오디오 파일 URL (Zero-Fault Audio Director 출력)

        Returns:
            Remotion composition props
        """
        platform = campaign_concept.get("platform", "YouTube")

        # Remotion Scene 구조로 변환
        scenes = []
        cumulative_start = 0

        for idx, block in enumerate(storyboard_blocks):
            scene = {
                "id": f"scene_{idx}",
                "type": block.get("block_type", "body"),  # hook, intro, body, cta, outro
                "text": block.get("text", ""),
                "duration": block.get("duration", 5),  # 초 단위
                "startTime": cumulative_start,
                "endTime": cumulative_start + block.get("duration", 5),
                "visualConcept": block.get("visual_concept", ""),
                "backgroundUrl": block.get("background_url", ""),
                "transitionEffect": block.get("transition_effect", "fade")
            }
            scenes.append(scene)
            cumulative_start += block.get("duration", 5)

        # Remotion Props 구조
        props = {
            "platform": platform,
            "composition": PLATFORM_COMPOSITIONS.get(platform, PLATFORM_COMPOSITIONS["YouTube"]),
            "concept": {
                "gender": campaign_concept.get("gender", "neutral"),
                "tone": campaign_concept.get("tone", "professional"),
                "style": campaign_concept.get("style", "cinematic")
            },
            "scenes": scenes,
            "audio": {
                "url": audio_url,
                "volume": 1.0
            },
            "branding": {
                "logo": campaign_concept.get("logo_url", ""),
                "colors": {
                    "primary": campaign_concept.get("primary_color", "#00A1E0"),
                    "secondary": campaign_concept.get("secondary_color", "#16325C")
                }
            },
            "metadata": {
                "totalDuration": cumulative_start,
                "sceneCount": len(scenes)
            }
        }

        logger.info(f"✅ Converted {len(scenes)} blocks to Remotion props for {platform}")
        return props

    async def render_video_with_remotion(
        self,
        content_id: int,
        props: Dict[str, Any],
        composition_id: str = "OmniVibeComposition"
    ) -> Dict[str, Any]:
        """Remotion으로 영상 렌더링 (비동기)

        Args:
            content_id: 콘텐츠 ID (WebSocket 진행 상태 업데이트용)
            props: Remotion composition props
            composition_id: Remotion composition ID (frontend에서 정의)

        Returns:
            렌더링 결과 (로컬 파일 경로, Cloudinary URL)
        """
        try:
            # WebSocket: 렌더링 시작 알림
            await self._send_progress(content_id, "rendering", 0, "Remotion 렌더링 시작...")

            # Props를 JSON 파일로 저장
            props_file = self.output_dir / f"props_{content_id}.json"
            with open(props_file, "w", encoding="utf-8") as f:
                json.dump(props, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 Props saved to {props_file}")

            # 출력 파일 경로
            output_filename = f"video_{content_id}_{int(asyncio.get_event_loop().time())}.mp4"
            output_path = self.output_dir / output_filename

            # Remotion CLI 명령어 구성
            platform = props.get("platform", "YouTube")
            composition = PLATFORM_COMPOSITIONS.get(platform, PLATFORM_COMPOSITIONS["YouTube"])

            remotion_command = [
                "npx",
                "remotion",
                "render",
                composition_id,
                str(output_path),
                f"--props={props_file}",
                f"--width={composition['width']}",
                f"--height={composition['height']}",
                f"--fps={composition['fps']}",
                f"--codec={composition['codec']}",
                "--concurrency=4"  # 병렬 렌더링
            ]

            # WebSocket: 렌더링 진행
            await self._send_progress(content_id, "rendering", 30, "Remotion CLI 실행 중...")

            # Remotion 렌더링 실행
            logger.info(f"🎬 Starting Remotion render: {' '.join(remotion_command)}")

            process = await asyncio.create_subprocess_exec(
                *remotion_command,
                cwd=str(self.frontend_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 실시간 로그 출력 및 진행률 업데이트
            async def read_stream(stream, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode('utf-8').strip()
                    if text:
                        logger.info(f"Remotion: {text}")

                        # 진행률 파싱 (Remotion은 프레임 진행률을 출력)
                        if "Rendering frames" in text:
                            await self._send_progress(content_id, "rendering", 50, text)
                        elif "Encoding" in text:
                            await self._send_progress(content_id, "rendering", 80, text)

            # stdout/stderr 동시 읽기
            await asyncio.gather(
                read_stream(process.stdout),
                read_stream(process.stderr, is_stderr=True)
            )

            await process.wait()

            if process.returncode != 0:
                raise RuntimeError(f"Remotion render failed with exit code {process.returncode}")

            logger.info(f"✅ Remotion render completed: {output_path}")

            # WebSocket: Cloudinary 업로드 시작
            await self._send_progress(content_id, "uploading", 85, "Cloudinary 업로드 중...")

            # Cloudinary 업로드
            cloudinary_result = self.cloudinary.upload_video(
                str(output_path),
                folder=f"omnivibe/content_{content_id}",
                public_id=f"video_{content_id}",
                resource_type="video"
            )

            video_url = cloudinary_result.get("secure_url")
            logger.info(f"☁️ Video uploaded to Cloudinary: {video_url}")

            # WebSocket: 완료
            await self._send_progress(content_id, "completed", 100, "렌더링 완료!")

            return {
                "status": "success",
                "local_path": str(output_path),
                "cloudinary_url": video_url,
                "duration": props["metadata"]["totalDuration"],
                "platform": platform,
                "resolution": f"{composition['width']}x{composition['height']}"
            }

        except Exception as e:
            logger.error(f"❌ Remotion render failed: {e}")
            await self._send_progress(content_id, "failed", 0, f"렌더링 실패: {str(e)}")
            raise

    async def _send_progress(
        self,
        content_id: int,
        stage: str,
        progress: int,
        message: str
    ):
        """WebSocket으로 진행 상태 전송"""
        try:
            await self.ws_manager.broadcast(
                f"content_{content_id}",
                {
                    "content_id": content_id,
                    "stage": stage,
                    "progress": progress,
                    "message": message
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send progress via WebSocket: {e}")

    def get_available_compositions(self) -> List[Dict[str, Any]]:
        """사용 가능한 Remotion Composition 목록 조회

        Returns:
            Composition 메타데이터 리스트
        """
        # 실제로는 frontend의 remotion.config.ts를 파싱하거나
        # Remotion API를 호출하여 동적으로 가져와야 함
        # 여기서는 기본 Composition만 반환

        return [
            {
                "id": "OmniVibeComposition",
                "name": "OmniVibe Default Composition",
                "description": "기본 콘티 기반 영상 생성",
                "defaultProps": {
                    "platform": "YouTube",
                    "scenes": []
                }
            },
            {
                "id": "MinimalComposition",
                "name": "Minimal Style Composition",
                "description": "미니멀 스타일 영상",
                "defaultProps": {
                    "platform": "Instagram",
                    "scenes": []
                }
            }
        ]

    async def validate_remotion_installation(self) -> Dict[str, Any]:
        """Remotion CLI 설치 상태 확인

        Returns:
            설치 상태 및 버전 정보
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "npx",
                "remotion",
                "--version",
                cwd=str(self.frontend_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            version = stdout.decode('utf-8').strip()

            if process.returncode == 0:
                return {
                    "installed": True,
                    "version": version,
                    "frontend_path": str(self.frontend_dir)
                }
            else:
                return {
                    "installed": False,
                    "error": stderr.decode('utf-8').strip()
                }

        except Exception as e:
            logger.error(f"Failed to validate Remotion installation: {e}")
            return {
                "installed": False,
                "error": str(e)
            }


# Singleton instance
_remotion_service_instance = None


def get_remotion_service() -> RemotionService:
    """Remotion Service 싱글톤 인스턴스 반환"""
    global _remotion_service_instance
    if _remotion_service_instance is None:
        _remotion_service_instance = RemotionService()
    return _remotion_service_instance
