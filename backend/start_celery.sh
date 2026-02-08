#!/bin/bash

# OmniVibe Pro - Celery Worker & Beat 시작 스크립트

set -e

echo "🚀 Starting OmniVibe Pro Celery Services..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Virtual environment 활성화
if [ -d "venv" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Redis 확인
echo -e "${YELLOW}🔍 Checking Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not running. Starting...${NC}"
    redis-server --daemonize yes
    sleep 2
fi

# Celery Worker 시작 (우선순위 큐 지원)
echo -e "${GREEN}🔧 Starting Celery Worker...${NC}"
celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=high_priority,default,low_priority \
    --max-tasks-per-child=100 \
    --time-limit=1800 \
    --soft-time-limit=1500 \
    --detach \
    --logfile=logs/celery_worker.log \
    --pidfile=celery_worker.pid

echo -e "${GREEN}✅ Celery Worker started${NC}"

# Celery Beat 시작 (스케줄러)
echo -e "${GREEN}📅 Starting Celery Beat...${NC}"
celery -A app.tasks.celery_app beat \
    --loglevel=info \
    --detach \
    --logfile=logs/celery_beat.log \
    --pidfile=celery_beat.pid

echo -e "${GREEN}✅ Celery Beat started${NC}"

# Flower 시작 (모니터링 UI)
echo -e "${GREEN}🌸 Starting Flower...${NC}"
celery -A app.tasks.celery_app flower \
    --conf=flower_config.py \
    --detach \
    --logfile=logs/flower.log \
    --pidfile=flower.pid

echo -e "${GREEN}✅ Flower started on http://localhost:5555${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All Celery services started!${NC}"
echo "=========================================="
echo ""
echo "Monitoring:"
echo "  - Flower UI: http://localhost:5555"
echo "  - Worker Log: tail -f logs/celery_worker.log"
echo "  - Beat Log: tail -f logs/celery_beat.log"
echo ""
echo "Stop services:"
echo "  ./stop_celery.sh"
echo ""
