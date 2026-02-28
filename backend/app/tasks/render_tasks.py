"""Remotion 멀티포맷 렌더링 Celery 태스크

Remotion CLI를 subprocess로 실행하여 영상을 렌더링하고,
멀티포맷(YouTube/Instagram/TikTok) 출력을 지원합니다.
"""
import subprocess
import json
import os
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'current_format': fmt,
                    'message': f'{fmt} 렌더링 중...'
                }
            )

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
                # Cloudinary 업로드 (실제 환경)
                results[fmt] = output_path  # 임시로 로컬 경로 반환
            else:
                logger.error(f"Render failed for {fmt}: {stderr}")
                results[fmt] = None

        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': '완료'}
        )

        return {'task_id': task_id, 'results': results, 'status': 'completed'}
