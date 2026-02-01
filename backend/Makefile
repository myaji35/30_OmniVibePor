# OmniVibe Pro - Makefile

.PHONY: help install up down logs test test-api clean

# 기본값 - 자동 감지
DOCKER_COMPOSE = $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")
PYTHON = python3
POETRY = poetry

help: ## 도움말 표시
	@echo "OmniVibe Pro - Make Commands"
	@echo "============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Poetry 의존성 설치
	@echo "📦 Installing dependencies..."
	$(POETRY) install

up: ## Docker Compose 서비스 시작
	@echo "🚀 Starting all services..."
	$(DOCKER_COMPOSE) up -d
	@echo "✓ Services started!"
	@echo ""
	@echo "Services running at:"
	@echo "  - FastAPI:  http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Flower:   http://localhost:5555"
	@echo "  - Neo4j:    http://localhost:7474"
	@echo ""
	@$(MAKE) status

down: ## Docker Compose 서비스 중지
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) down

restart: ## 서비스 재시작
	@$(MAKE) down
	@$(MAKE) up

logs: ## 로그 확인 (실시간)
	$(DOCKER_COMPOSE) logs -f

logs-api: ## FastAPI 로그만 확인
	$(DOCKER_COMPOSE) logs -f api

logs-celery: ## Celery Worker 로그만 확인
	$(DOCKER_COMPOSE) logs -f celery_worker

status: ## 서비스 상태 확인
	@echo "📊 Service Status:"
	@$(DOCKER_COMPOSE) ps

health: ## 헬스체크
	@echo "🏥 Health Check..."
	@curl -s http://localhost:8000/ | jq '.'
	@echo ""
	@curl -s http://localhost:8000/health | jq '.'

test: ## 전체 테스트 실행 (pytest)
	@echo "🧪 Running tests..."
	$(POETRY) run pytest tests/ -v --tb=short

test-api: ## API 통합 테스트 실행
	@echo "🧪 Running API integration tests..."
	@chmod +x test_api.sh
	@./test_api.sh

test-unit: ## 유닛 테스트만 실행
	@echo "🧪 Running unit tests..."
	$(POETRY) run pytest tests/test_audio_loop.py -v

shell-api: ## FastAPI 컨테이너 쉘 접속
	$(DOCKER_COMPOSE) exec api /bin/bash

shell-celery: ## Celery Worker 컨테이너 쉘 접속
	$(DOCKER_COMPOSE) exec celery_worker /bin/bash

clean: ## 생성된 파일 정리
	@echo "🧹 Cleaning up..."
	rm -rf outputs/audio/*.mp3
	rm -f test_verified_audio.mp3
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned!"

clean-all: clean down ## 모든 데이터 삭제 (Docker 볼륨 포함)
	@echo "⚠️  Removing Docker volumes..."
	$(DOCKER_COMPOSE) down -v
	@echo "✓ All data removed!"

build: ## Docker 이미지 빌드
	@echo "🔨 Building Docker images..."
	$(DOCKER_COMPOSE) build

flower: ## Flower 대시보드 열기
	@echo "🌸 Opening Flower..."
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Open http://localhost:5555 in your browser"

docs: ## API 문서 열기
	@echo "📖 Opening API documentation..."
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

neo4j: ## Neo4j 브라우저 열기
	@echo "🔗 Opening Neo4j Browser..."
	@open http://localhost:7474 || xdg-open http://localhost:7474 || echo "Open http://localhost:7474 in your browser"

dev: ## 개발 모드 시작 (로컬)
	@echo "💻 Starting development server..."
	$(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

celery-worker: ## Celery Worker 로컬 실행
	@echo "👷 Starting Celery worker..."
	$(POETRY) run celery -A app.tasks.celery_app worker --loglevel=info

celery-flower: ## Flower 로컬 실행
	@echo "🌸 Starting Flower..."
	$(POETRY) run celery -A app.tasks.celery_app flower --port=5555

init: install up ## 초기 설정 (의존성 설치 + 서비스 시작)
	@echo "🎉 Initialization complete!"
	@echo ""
	@$(MAKE) docs

demo: up ## 데모 실행 (서비스 시작 + API 테스트)
	@echo "🎬 Starting demo..."
	@sleep 5
	@$(MAKE) test-api
