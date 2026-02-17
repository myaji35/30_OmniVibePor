#!/bin/bash

# OmniVibe Pro 자동 배포 스크립트
# Vultr 서버: 158.247.235.31

set -e

SERVER_IP="158.247.235.31"
SSH_USER="root"

echo "=================================="
echo "  OmniVibe Pro 자동 배포"
echo "=================================="
echo "서버: $SERVER_IP"
echo ""

# 1. SSH 연결 테스트
echo "[1/6] SSH 연결 테스트..."
if sshpass -p 'B6n!o]U@[5P}tL)H' ssh -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP "echo 'SSH 연결 성공'" 2>/dev/null; then
    echo "✅ SSH 연결 성공"
else
    echo "⚠️  sshpass가 설치되지 않았습니다. 설치 중..."
    brew install hudochenkov/sshpass/sshpass 2>/dev/null || {
        echo "❌ sshpass 설치 실패. 수동으로 진행해주세요."
        echo ""
        echo "수동 배포 명령어:"
        echo "ssh root@$SERVER_IP"
        exit 1
    }
fi

# 2. 서버 초기 설정
echo ""
echo "[2/6] 서버 초기 설정..."
sshpass -p 'B6n!o]U@[5P}tL)H' ssh -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP << 'ENDSSH'
    # 시스템 업데이트
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get upgrade -y

    # Docker 설치
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
    fi

    # Docker Compose 설치
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi

    # 필수 패키지
    apt-get install -y git nginx certbot python3-certbot-nginx ufw

    # 방화벽 설정
    ufw --force enable
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp

    # 프로젝트 디렉토리
    mkdir -p /root/omnivibe

    echo "✅ 서버 초기 설정 완료"
ENDSSH

# 3. 프로젝트 파일 업로드
echo ""
echo "[3/6] 프로젝트 파일 업로드..."
sshpass -p 'B6n!o]U@[5P}tL)H' rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude 'venv' \
  --exclude '.git' \
  --exclude '*.sqlite' \
  --exclude 'outputs' \
  --exclude '__pycache__' \
  --exclude '.deploy_credentials' \
  ./ $SSH_USER@$SERVER_IP:/root/omnivibe/

echo "✅ 파일 업로드 완료"

# 4. .env 파일 생성
echo ""
echo "[4/6] .env 파일 생성..."
sshpass -p 'B6n!o]U@[5P}tL)H' ssh -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP << 'ENDSSH'
    cd /root/omnivibe

    # SECRET_KEY 생성
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    cat > .env << EOF
ENV=production
DEBUG=False
SECRET_KEY=$SECRET_KEY

DATABASE_URL=sqlite:///omni_db.sqlite
REDIS_URL=redis://redis:6379/0

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_prod_password_2026

ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

STRIPE_SECRET_KEY=your_key_here
STRIPE_WEBHOOK_SECRET=your_key_here

CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret

FORCE_HTTPS=False
EOF

    echo "✅ .env 파일 생성 완료"
ENDSSH

# 5. Docker Compose 배포
echo ""
echo "[5/6] Docker Compose 배포..."
sshpass -p 'B6n!o]U@[5P}tL)H' ssh -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP << 'ENDSSH'
    cd /root/omnivibe

    # 기존 컨테이너 중지
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

    # 새 컨테이너 시작
    docker-compose -f docker-compose.prod.yml up -d

    echo "✅ Docker 컨테이너 시작 완료"
ENDSSH

# 6. 배포 확인
echo ""
echo "[6/6] 배포 확인..."
sleep 10

sshpass -p 'B6n!o]U@[5P}tL)H' ssh -o StrictHostKeyChecking=no $SSH_USER@$SERVER_IP << 'ENDSSH'
    cd /root/omnivibe

    echo ""
    echo "컨테이너 상태:"
    docker-compose -f docker-compose.prod.yml ps

    echo ""
    echo "Health Check:"
    curl -s http://localhost:8000/health || echo "⚠️  Backend 아직 시작 중..."
ENDSSH

echo ""
echo "=================================="
echo "  배포 완료!"
echo "=================================="
echo ""
echo "✅ 배포 성공!"
echo ""
echo "🌐 접속 정보:"
echo "  - API: http://$SERVER_IP:8000/docs"
echo "  - Frontend: http://$SERVER_IP:3020"
echo "  - Health: http://$SERVER_IP:8000/health"
echo ""
echo "📝 다음 단계:"
echo "  1. .env 파일에 실제 API 키 입력"
echo "  2. 도메인 DNS 설정"
echo "  3. HTTPS 설정"
echo ""
echo "🔐 .env 파일 수정:"
echo "  ssh root@$SERVER_IP"
echo "  cd /root/omnivibe"
echo "  nano .env"
echo ""
