#!/bin/bash
# 서비스 헬스체크 및 상태 확인 스크립트

set -e

echo "🔍 OmniVibe Pro - Service Health Check"
echo "======================================"

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 서비스 체크 함수
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -ne "  ${service_name}... "

    if http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$http_code" -eq "$expected_status" ] || [ "$http_code" -eq 200 ]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
            return 0
        else
            echo -e "${YELLOW}⚠ Warning${NC} (HTTP $http_code)"
            return 1
        fi
    else
        echo -e "${RED}✗ DOWN${NC}"
        return 1
    fi
}

# Docker 서비스 상태
echo -e "\n${YELLOW}=== Docker Services ===${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    echo -e "${RED}docker-compose not found${NC}"
fi

# HTTP 서비스 체크
echo -e "\n${YELLOW}=== HTTP Services ===${NC}"

check_service "FastAPI         " "http://localhost:8000/"
check_service "FastAPI Health  " "http://localhost:8000/health"
check_service "FastAPI Docs    " "http://localhost:8000/docs"
check_service "Flower          " "http://localhost:5555/"
check_service "Neo4j Browser   " "http://localhost:7474/" 200

# Redis 체크
echo -e "\n${YELLOW}=== Redis ===${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        echo -e "  Redis... ${GREEN}✓ OK${NC}"
    else
        echo -e "  Redis... ${RED}✗ DOWN${NC}"
    fi
else
    echo "  redis-cli not installed, skipping..."
fi

# Neo4j 체크
echo -e "\n${YELLOW}=== Neo4j ===${NC}"
echo "  Username: neo4j"
echo "  Password: omnivibe_password_2026"
echo "  Browser:  http://localhost:7474"

# Celery 워커 상태
echo -e "\n${YELLOW}=== Celery Workers ===${NC}"
if docker-compose ps celery_worker 2>/dev/null | grep -q "Up"; then
    echo -e "  Celery Worker... ${GREEN}✓ Running${NC}"

    # 워커 로그 마지막 5줄
    echo -e "\n  Recent logs:"
    docker-compose logs --tail=5 celery_worker | sed 's/^/    /'
else
    echo -e "  Celery Worker... ${RED}✗ Not running${NC}"
fi

# API 버전 정보
echo -e "\n${YELLOW}=== API Information ===${NC}"
if api_info=$(curl -s http://localhost:8000/ 2>/dev/null); then
    echo "  $api_info" | jq '.' 2>/dev/null || echo "  $api_info"
fi

# 디스크 사용량
echo -e "\n${YELLOW}=== Storage ===${NC}"
if [ -d "./outputs/audio" ]; then
    audio_count=$(find ./outputs/audio -name "*.mp3" 2>/dev/null | wc -l)
    audio_size=$(du -sh ./outputs/audio 2>/dev/null | cut -f1)
    echo "  Generated audio files: $audio_count"
    echo "  Storage used: $audio_size"
else
    echo "  No audio files yet"
fi

# 요약
echo -e "\n${YELLOW}=== Summary ===${NC}"
echo "  All services are ready for testing!"
echo ""
echo "  Next steps:"
echo "    - API Docs:     http://localhost:8000/docs"
echo "    - Flower:       http://localhost:5555"
echo "    - Run tests:    make test-api"
echo "    - View logs:    make logs"

echo ""
echo "======================================"
echo -e "${GREEN}✓ Health check complete!${NC}"
