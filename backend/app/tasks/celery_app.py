"""Celery 애플리케이션 설정 - 성능 최적화"""
import logging
import time
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
from celery.schedules import crontab
from kombu import Queue, Exchange

from app.core.config import get_settings

settings = get_settings()

# Celery 앱 초기화
celery_app = Celery(
    "omnivibe",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# ==================== 우선순위 큐 정의 ====================
# high: 실시간 오디오 생성, 긴급 작업
# default: 일반 영상 렌더링
# low: 배치 작업, 통계 생성

default_exchange = Exchange('default', type='direct')

celery_app.conf.task_queues = (
    Queue('high_priority', exchange=default_exchange, routing_key='high', priority=10),
    Queue('default', exchange=default_exchange, routing_key='default', priority=5),
    Queue('low_priority', exchange=default_exchange, routing_key='low', priority=1),
)

celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_default_exchange = 'default'
celery_app.conf.task_default_routing_key = 'default'

# ==================== Celery 최적화 설정 ====================
celery_app.conf.update(
    # 직렬화
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 타임존
    timezone='Asia/Seoul',
    enable_utc=True,

    # Task 추적
    task_track_started=True,
    task_send_sent_event=True,

    # 시간 제한
    task_time_limit=30 * 60,  # 30분 하드 제한
    task_soft_time_limit=25 * 60,  # 25분 소프트 제한

    # Worker 최적화
    worker_prefetch_multiplier=4,  # 동시 처리 4개 (변경: 1 → 4)
    worker_max_tasks_per_child=100,  # 100개 처리 후 재시작 (변경: 50 → 100)
    worker_disable_rate_limits=False,

    # Retry 전략 (Exponential Backoff)
    task_acks_late=True,  # Task 완료 후 ACK (실패 시 재시도)
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 기본 재시도 대기: 60초
    task_max_retries=3,  # 최대 재시도: 3회

    # Result Backend 최적화
    result_expires=3600,  # 결과 1시간 후 자동 삭제
    result_persistent=False,  # 결과 영구 저장 비활성화 (메모리 절약)

    # Broker 최적화
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,

    # 우선순위 활성화
    task_inherit_parent_priority=True,

    # Beat (스케줄러) 설정
    beat_schedule={
        'cleanup-old-results': {
            'task': 'cleanup_old_task_results',
            'schedule': 3600.0,  # 1시간마다
        },
        # Week 5: Quota 관리
        'reset-monthly-quotas': {
            'task': 'quota.reset_monthly_quotas',
            'schedule': crontab(day_of_month='1', hour='0', minute='0'),  # 매월 1일 00:00
        },
        'check-quota-warnings': {
            'task': 'quota.check_quota_warnings',
            'schedule': crontab(hour='9', minute='0'),  # 매일 09:00
        },
        'generate-usage-report': {
            'task': 'quota.generate_usage_report',
            'schedule': crontab(day_of_month='28', hour='23', minute='0'),  # 매월 28일 23:00
        },
        # Cloudinary fallback 재업로드 (10분마다)
        'retry-fallback-uploads': {
            'task': 'app.tasks.background_tasks.retry_fallback_uploads',
            'schedule': 600.0,
        },
        # 디스크 모니터링 (30분마다)
        'monitor-disk-usage': {
            'task': 'app.tasks.background_tasks.monitor_disk_usage',
            'schedule': 1800.0,
        },
    },
)

# Task 자동 발견
celery_app.autodiscover_tasks(['app.tasks'])

logger = logging.getLogger(__name__)


# ==================== Celery 시그널 (성능 모니터링) ====================

# Task 실행 시간 추적용 딕셔너리
task_start_times = {}


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """작업 시작 전 로깅 및 시간 기록"""
    task_start_times[task_id] = time.time()
    logger.info(
        f"⏱️  Task started: {task.name} (ID: {task_id[:8]}...)"
        f" | Args: {args[:2] if args else '[]'}..."
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """작업 완료 후 로깅 및 실행 시간 측정"""
    if task_id in task_start_times:
        elapsed = time.time() - task_start_times[task_id]
        logger.info(
            f"✅ Task completed: {task.name} (ID: {task_id[:8]}...)"
            f" | Duration: {elapsed:.2f}s"
        )
        del task_start_times[task_id]
    else:
        logger.info(f"✅ Task completed: {task.name} (ID: {task_id[:8]}...)")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """작업 실패 시 로깅"""
    if task_id in task_start_times:
        elapsed = time.time() - task_start_times[task_id]
        logger.error(
            f"❌ Task failed: {sender.name} (ID: {task_id[:8]}...)"
            f" | Duration: {elapsed:.2f}s | Error: {exception}"
        )
        del task_start_times[task_id]
    else:
        logger.error(
            f"❌ Task failed: {sender.name} (ID: {task_id[:8]}...)"
            f" | Error: {exception}"
        )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **kwargs):
    """작업 재시도 시 로깅"""
    logger.warning(
        f"🔄 Task retry: {sender.name} (ID: {task_id[:8]}...)"
        f" | Reason: {reason}"
    )


# ==================== 유틸리티 작업 ====================

@celery_app.task(name="health_check", queue='high_priority')
def health_check():
    """Celery 워커 헬스체크"""
    return {"status": "healthy", "message": "Celery worker is running"}


@celery_app.task(name="cleanup_old_task_results", queue='low_priority')
def cleanup_old_task_results():
    """오래된 Task 결과 정리 (1시간마다 실행)"""
    from celery.result import AsyncResult

    # Redis에서 만료된 결과 삭제 (자동으로 처리되지만 명시적 정리)
    logger.info("🧹 Cleaning up old task results...")

    # 여기에 추가 정리 로직 구현 가능
    # 예: 파일 시스템의 임시 파일 삭제 등

    return {"status": "success", "message": "Old task results cleaned up"}


# ==================== Task 우선순위 헬퍼 ====================

def get_task_priority(task_name: str) -> str:
    """Task 이름에 따른 우선순위 반환"""
    high_priority_tasks = [
        'generate_verified_audio_task',
        'health_check',
    ]

    low_priority_tasks = [
        'batch_generate_verified_audio_task',
        'cleanup_old_task_results',
    ]

    if any(name in task_name for name in high_priority_tasks):
        return 'high_priority'
    elif any(name in task_name for name in low_priority_tasks):
        return 'low_priority'
    else:
        return 'default'


# ── Slack 알림 유틸 ──────────────────────────────────────────────────
def _send_slack_alert(message: str) -> None:
    """SLACK_WEBHOOK_URL이 설정된 경우에만 발송 (fail-safe)"""
    webhook_url = settings.SLACK_WEBHOOK_URL
    if not webhook_url:
        return
    try:
        import urllib.request, json as _json
        payload = _json.dumps({"text": message}).encode()
        req = urllib.request.Request(
            webhook_url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        logger.warning(f"Slack 알림 발송 실패 (무시): {e}")


@task_failure.connect
def task_failure_alert(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """작업 실패 시 Slack 알림 (기존 로깅 핸들러와 별도)"""
    task_name = getattr(sender, 'name', 'unknown')
    short_id  = (task_id or '')[:8]
    _send_slack_alert(
        f":red_circle: *Celery Task 실패*\n"
        f">Task: `{task_name}` (ID: `{short_id}...`)\n"
        f">Error: `{exception}`"
    )
