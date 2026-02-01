"""Celery 애플리케이션 설정"""
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure

from app.core.config import get_settings

settings = get_settings()

# Celery 앱 초기화
celery_app = Celery(
    "omnivibe",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분 제한
    task_soft_time_limit=25 * 60,  # 소프트 제한 25분
    worker_prefetch_multiplier=1,  # 동시 작업 제한
    worker_max_tasks_per_child=50,  # 워커 재시작 (메모리 누수 방지)
)

# Task 자동 발견
celery_app.autodiscover_tasks(['app.tasks'])

logger = logging.getLogger(__name__)


# ==================== Celery 시그널 ====================

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """작업 시작 전 로깅"""
    logger.info(f"Task started: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    """작업 완료 후 로깅"""
    logger.info(f"Task completed: {task.name} (ID: {task_id})")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """작업 실패 시 로깅"""
    logger.error(f"Task failed: {sender.name} (ID: {task_id}), Error: {exception}")


# ==================== 헬스체크 작업 ====================

@celery_app.task(name="health_check")
def health_check():
    """Celery 워커 헬스체크"""
    return {"status": "healthy", "message": "Celery worker is running"}
