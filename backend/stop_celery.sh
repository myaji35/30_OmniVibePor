#!/bin/bash

# OmniVibe Pro - Celery 서비스 중지 스크립트

set -e

echo "🛑 Stopping OmniVibe Pro Celery Services..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Celery Worker 중지
if [ -f "celery_worker.pid" ]; then
    echo -e "${RED}🔧 Stopping Celery Worker...${NC}"
    kill $(cat celery_worker.pid) 2>/dev/null || true
    rm celery_worker.pid
    echo -e "${GREEN}✅ Celery Worker stopped${NC}"
fi

# Celery Beat 중지
if [ -f "celery_beat.pid" ]; then
    echo -e "${RED}📅 Stopping Celery Beat...${NC}"
    kill $(cat celery_beat.pid) 2>/dev/null || true
    rm celery_beat.pid
    echo -e "${GREEN}✅ Celery Beat stopped${NC}"
fi

# Flower 중지
if [ -f "flower.pid" ]; then
    echo -e "${RED}🌸 Stopping Flower...${NC}"
    kill $(cat flower.pid) 2>/dev/null || true
    rm flower.pid
    echo -e "${GREEN}✅ Flower stopped${NC}"
fi

# 남아있는 Celery 프로세스 정리
echo -e "${RED}🧹 Cleaning up remaining processes...${NC}"
pkill -f "celery.*omnivibe" 2>/dev/null || true

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All Celery services stopped!${NC}"
echo "=========================================="
