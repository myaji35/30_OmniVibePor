#!/bin/bash
set -euo pipefail

# ============================================================
# OmniVibe Pro — Vultr 배포 스크립트
# Server: 158.247.235.31
# URL: http://omnivibepro.158.247.235.31.nip.io (frontend:3020)
#      http://158.247.235.31:8020 (backend API)
# ============================================================

SERVER="root@158.247.235.31"
REMOTE_DIR="/opt/omnivibe_pro"
PROJECT_NAME="omnivibe"

echo "🚀 OmniVibe Pro 배포 시작..."
echo "   서버: $SERVER"
echo "   경로: $REMOTE_DIR"
echo ""

# ── Step 1: 서버 디렉토리 준비 ────────────────────────────────
echo "📁 Step 1: 서버 디렉토리 준비..."
ssh -o StrictHostKeyChecking=no $SERVER "mkdir -p $REMOTE_DIR"

# ── Step 2: 소스 전송 ────────────────────────────────────────
echo "📦 Step 2: 소스 코드 전송 중..."

# git archive로 추적 파일만 전송 (node_modules, .git 제외)
git archive --format=tar HEAD | ssh $SERVER "cd $REMOTE_DIR && tar xf - --overwrite"

# docker-compose.vultr.yml을 docker-compose.yml로 복사
ssh $SERVER "cd $REMOTE_DIR && cp docker-compose.vultr.yml docker-compose.yml"

# .env 파일 전송 (있으면)
if [ -f "backend/.env" ]; then
    echo "🔑 .env 파일 전송..."
    scp -o StrictHostKeyChecking=no backend/.env $SERVER:$REMOTE_DIR/backend/.env
fi

echo "✅ 소스 전송 완료"

# ── Step 3: Docker 빌드 및 실행 ──────────────────────────────
echo "🐳 Step 3: Docker 빌드 및 실행..."

ssh $SERVER "cd $REMOTE_DIR && \
    docker compose down --remove-orphans 2>/dev/null || true && \
    docker compose build --no-cache && \
    docker compose up -d"

echo "✅ 컨테이너 시작됨"

# ── Step 4: 헬스체크 ─────────────────────────────────────────
echo "🏥 Step 4: 헬스체크 대기 (최대 90초)..."

for i in $(seq 1 18); do
    if ssh $SERVER "curl -sf http://localhost:8020/health > /dev/null 2>&1"; then
        echo "✅ Backend 정상 (${i}x5초)"
        break
    fi
    if [ $i -eq 18 ]; then
        echo "❌ Backend 헬스체크 실패 (90초 타임아웃)"
        echo "로그 확인: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs backend'"
        exit 1
    fi
    sleep 5
done

for i in $(seq 1 24); do
    if ssh $SERVER "curl -sf http://localhost:3020 > /dev/null 2>&1"; then
        echo "✅ Frontend 정상 (${i}x5초)"
        break
    fi
    if [ $i -eq 24 ]; then
        echo "⚠️ Frontend 헬스체크 실패 (120초) — 빌드 시간이 오래 걸릴 수 있음"
        echo "로그 확인: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs frontend'"
    fi
    sleep 5
done

# ── Step 5: 결과 출력 ────────────────────────────────────────
echo ""
echo "🎉 OmniVibe Pro 배포 완료!"
echo ""
echo "  Frontend: http://omnivibepro.158.247.235.31.nip.io:3020"
echo "  Backend:  http://158.247.235.31:8020"
echo "  API Docs: http://158.247.235.31:8020/docs"
echo ""
echo "  컨테이너 상태:"
ssh $SERVER "docker ps --filter 'name=omnivibe' --format '  {{.Names}}\t{{.Status}}'"
echo ""
echo "  로그 확인: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'"
