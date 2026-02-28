"""Remotion 멀티포맷 렌더링 Celery 태스크

Remotion CLI를 subprocess로 실행하여 영상을 렌더링하고,
멀티포맷(YouTube/Instagram/TikTok) 출력을 지원합니다.
"""
import subprocess
import json
import os
import asyncio
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cloudinary 업로드 설정
# ---------------------------------------------------------------------------
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = bool(os.environ.get('CLOUDINARY_CLOUD_NAME'))
except ImportError:
    CLOUDINARY_AVAILABLE = False


def upload_to_cloudinary(file_path: str, fmt: str, task_id: str) -> str:
    """렌더링 결과물을 Cloudinary에 업로드하고 secure_url을 반환한다.

    Cloudinary 환경변수가 설정되어 있지 않거나 패키지가 없으면
    로컬 파일 경로를 그대로 반환한다 (graceful fallback).

    Args:
        file_path: 업로드할 로컬 파일 경로
        fmt: 포맷 이름 (youtube / instagram / tiktok)
        task_id: Celery 태스크 ID (public_id 구성에 사용)

    Returns:
        Cloudinary secure_url 또는 로컬 파일 경로
    """
    if CLOUDINARY_AVAILABLE and os.path.exists(file_path):
        try:
            cloudinary.config(
                cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
                api_key=os.environ.get('CLOUDINARY_API_KEY'),
                api_secret=os.environ.get('CLOUDINARY_API_SECRET')
            )
            result = cloudinary.uploader.upload(
                file_path,
                resource_type="video",
                public_id=f"omnivibe/{task_id}/{fmt}",
                overwrite=True
            )
            url = result.get('secure_url', file_path)
            logger.info(f"Cloudinary upload OK: {url}")
            return url
        except Exception as e:
            logger.warning(f"Cloudinary upload failed ({fmt}), falling back to local path: {e}")
            return file_path
    # 환경변수 미설정 또는 파일 없음 → 로컬 경로 반환
    return file_path


# ---------------------------------------------------------------------------
# WebSocket 진행률 브로드캐스트 헬퍼
# ---------------------------------------------------------------------------

async def _broadcast_render_progress(
    task_id: str,
    progress: int,
    fmt: str,
    message: str
) -> None:
    """WebSocket manager를 통해 렌더링 진행률을 실시간으로 push한다.

    Celery 워커 컨텍스트(동기)에서 호출될 때는
    ``asyncio.run()`` 또는 ``loop.run_until_complete()``로 감싸서 사용한다.
    WebSocket 전송 실패는 조용히 무시하여 렌더링 태스크에 영향을 주지 않는다.

    Args:
        task_id: Celery 태스크 ID (project_id로 사용)
        progress: 진행률 0~100
        fmt: 현재 렌더링 중인 포맷 이름
        message: 사용자에게 표시할 메시지
    """
    try:
        from app.services.websocket_manager import get_websocket_manager
        manager = get_websocket_manager()
        await manager.broadcast_progress(
            project_id=task_id,
            task_name="render_video",
            progress=progress / 100.0,
            status="in_progress",
            message=message,
            metadata={"format": fmt, "progress_pct": progress}
        )
    except Exception as e:
        logger.debug(f"WebSocket broadcast skipped: {e}")


def _sync_broadcast(task_id: str, progress: int, fmt: str, message: str) -> None:
    """동기 컨텍스트(Celery 워커)에서 WebSocket broadcast를 실행하는 래퍼."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 이벤트 루프가 실행 중인 경우 (예: uvloop 환경)
            loop.create_task(
                _broadcast_render_progress(task_id, progress, fmt, message)
            )
        else:
            loop.run_until_complete(
                _broadcast_render_progress(task_id, progress, fmt, message)
            )
    except RuntimeError:
        # 이벤트 루프가 없는 순수 동기 환경
        try:
            asyncio.run(
                _broadcast_render_progress(task_id, progress, fmt, message)
            )
        except Exception as e:
            logger.debug(f"WebSocket asyncio.run failed: {e}")
    except Exception as e:
        logger.debug(f"WebSocket sync wrapper failed: {e}")


try:
    from app.tasks.celery_app import celery_app
except ImportError:
    celery_app = None


def render_video_subprocess(
    composition_id: str,
    props: dict,
    output_path: str,
    quality: str = "medium"
) -> tuple:
    """
    Remotion CLI를 subprocess로 실행하여 영상 렌더링
    실제 환경에서는 npx remotion render 사용
    """
    frontend_dir = "/Volumes/E_SSD/02_GitHub.nosync/0030_OmniVibePro/frontend"

    # props를 임시 JSON 파일로 저장
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(props, f)
        props_file = f.name

    try:
        cmd = [
            "npx", "remotion", "render",
            "remotion/Root.tsx",
            composition_id,
            output_path,
            f"--props={props_file}",
        ]

        result = subprocess.run(
            cmd,
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )

        return result.returncode == 0, result.stdout, result.stderr

    finally:
        os.unlink(props_file)


if celery_app:
    @celery_app.task(bind=True, name='render_video_task')
    def render_video_task(self, render_request: dict):
        """멀티포맷 영상 렌더링 Celery 태스크"""
        task_id = self.request.id
        formats = render_request.get('formats', ['youtube'])
        results = {}

        output_dir = Path("/tmp/remotion_renders") / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, fmt in enumerate(formats):
            progress = int((i / len(formats)) * 80)
            progress_message = f'{fmt} 렌더링 중...'

            # Celery 상태 업데이트 (폴링 방식 클라이언트용)
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'current_format': fmt,
                    'message': progress_message
                }
            )

            # WebSocket 직접 push (실시간 클라이언트용)
            _sync_broadcast(task_id, progress, fmt, progress_message)

            output_path = str(output_dir / f"{fmt}.mp4")

            props = {
                'blocks': render_request.get('blocks', []),
                'audioUrl': render_request.get('audio_url', ''),
                'branding': render_request.get('branding', {})
            }

            success, stdout, stderr = render_video_subprocess(
                fmt,
                props,
                output_path,
                render_request.get('quality', 'medium')
            )

            if success and Path(output_path).exists():
                # Cloudinary 업로드: 환경변수 설정 시 CDN URL, 미설정 시 로컬 경로
                results[fmt] = upload_to_cloudinary(output_path, fmt, task_id)
            else:
                logger.error(f"Render failed for {fmt}: {stderr}")
                results[fmt] = None

        # 완료 상태 업데이트
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': '완료'}
        )
        _sync_broadcast(task_id, 100, 'all', '모든 포맷 렌더링 완료')

        return {'task_id': task_id, 'results': results, 'status': 'completed'}
