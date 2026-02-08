"""
Flower - Celery Monitoring Tool 설정

실행 방법:
celery -A app.tasks.celery_app flower --conf=flower_config.py
"""

# Flower 서버 설정
port = 5555
address = '0.0.0.0'

# 인증 설정 (프로덕션에서는 반드시 활성화)
# basic_auth = ['admin:omnivibe2026']

# UI 설정
max_tasks = 10000  # 최대 표시 작업 수
db = 'flower.db'  # SQLite DB 경로

# 자동 새로고침
auto_refresh = True
refresh_interval = 5000  # 5초

# Broker API
broker_api = None  # Redis에는 broker_api 불필요

# 통계 수집
enable_events = True

# 로깅
logging = 'INFO'

# Natural time 사용
natural_time = True

# Task timeout (초)
task_runtime_metric_buckets = [
    1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600
]
