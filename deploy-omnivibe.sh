#!/bin/bash
set -euo pipefail

# ============================================================
# OmniVibe Pro — Vultr 배포 스크립트 v2
# Server: 158.247.235.31
# URL: http://omnivibepro.158.247.235.31.nip.io:3020 (frontend)
#      http://158.247.235.31:8020 (backend API)
# Strategy: 서버에서 순차 빌드 (메모리 절약)
# ============================================================

SERVER="root@158.247.235.31"
REMOTE_DIR="/opt/omnivibe_pro"

echo "🚀 OmniVibe Pro 배포 시작 (v2 — 순차 빌드)..."
echo "   서버: $SERVER"
echo "   경로: $REMOTE_DIR"
echo ""

# ── Step 1: 서버 준비 ────────────────────────────────────────
echo "📁 Step 1: 서버 준비..."
ssh -o StrictHostKeyChecking=no $SERVER "mkdir -p $REMOTE_DIR && docker system prune -f 2>/dev/null | tail -1"

# ── Step 2: 소스 전송 ────────────────────────────────────────
echo "📦 Step 2: 소스 전송 중..."
COPYFILE_DISABLE=1 tar cf - \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='outputs' \
  --exclude='uploads' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='._*' \
  backend/ frontend/ docker-compose.vultr.yml nginx/ 2>/dev/null | \
  ssh $SERVER "cd $REMOTE_DIR && tar xf - --overwrite"

# docker-compose.vultr.yml → docker-compose.yml
ssh $SERVER "cd $REMOTE_DIR && cp docker-compose.vultr.yml docker-compose.yml"

# .env 전송
if [ -f "backend/.env" ]; then
    echo "🔑 .env 전송..."
    scp -q -o StrictHostKeyChecking=no backend/.env $SERVER:$REMOTE_DIR/backend/.env
fi

echo "✅ 소스 전송 완료"

# ── Step 3: 기존 컨테이너 정리 ───────────────────────────────
echo "🧹 Step 3: 기존 OmniVibe 컨테이너 정리..."
ssh $SERVER "cd $REMOTE_DIR && docker compose down --remove-orphans 2>/dev/null || true"

# ── Step 4: 순차 빌드 (메모리 절약) ──────────────────────────
echo "🐳 Step 4: Docker 순차 빌드..."

echo "  [1/4] Redis + Neo4j 시작..."
ssh $SERVER "cd $REMOTE_DIR && docker compose up -d omnivibe-redis omnivibe-neo4j"

echo "  [2/4] Backend 빌드 중... (약 3-5분)"
ssh $SERVER "cd $REMOTE_DIR && docker compose build backend celery-worker" 2>&1 | tail -3

echo "  [3/4] Backend + Celery 시작..."
ssh $SERVER "cd $REMOTE_DIR && docker compose up -d backend celery-worker"

echo "  [4/4] Frontend 빌드 중... (약 5-10분, NODE_OPTIONS=1536MB)"
ssh $SERVER "cd $REMOTE_DIR && docker compose build frontend" 2>&1 | tail -3

echo "  Frontend 시작..."
ssh $SERVER "cd $REMOTE_DIR && docker compose up -d frontend"

echo "✅ 모든 컨테이너 시작됨"

# ── Step 5: 헬스체크 ─────────────────────────────────────────
echo "🏥 Step 5: 헬스체크..."

echo -n "  Backend: "
for i in $(seq 1 18); do
    if ssh $SERVER "curl -sf http://localhost:8020/health > /dev/null 2>&1"; then
        echo "✅ ($((i*5))초)"
        break
    fi
    if [ $i -eq 18 ]; then
        echo "❌ 타임아웃"
        echo "  로그: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs backend --tail 30'"
    fi
    sleep 5
done

echo -n "  Frontend: "
for i in $(seq 1 24); do
    if ssh $SERVER "curl -sf http://localhost:3020 > /dev/null 2>&1"; then
        echo "✅ ($((i*5))초)"
        break
    fi
    if [ $i -eq 24 ]; then
        echo "⚠️ 타임아웃 (빌드 시간 초과 가능)"
        echo "  로그: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs frontend --tail 30'"
    fi
    sleep 5
done

# ── Step 6: 결과 ─────────────────────────────────────────────
echo ""
echo "=========================================="
echo "🎉 OmniVibe Pro 배포 완료!"
echo "=========================================="
echo ""
echo "  Frontend: http://omnivibepro.158.247.235.31.nip.io:3020"
echo "  Backend:  http://158.247.235.31:8020"
echo "  API Docs: http://158.247.235.31:8020/docs"
echo ""
echo "  컨테이너 상태:"
ssh $SERVER "docker ps --filter 'name=omnivibe' --format '  {{.Names}}\t{{.Status}}'"
echo ""
