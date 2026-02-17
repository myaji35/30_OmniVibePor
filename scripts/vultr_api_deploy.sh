#!/bin/bash

# Vultr API를 사용한 자동 배포 스크립트

set -e

echo "================================"
echo "  Vultr API 자동 배포"
echo "================================"

# Vultr API Key 확인
if [ -z "$VULTR_API_KEY" ]; then
    echo ""
    echo "❌ VULTR_API_KEY 환경 변수가 설정되지 않았습니다."
    echo ""
    echo "📝 Vultr API Key 발급 방법:"
    echo "1. https://my.vultr.com/settings/#settingsapi 접속"
    echo "2. 'Enable API' 클릭"
    echo "3. 'Generate API Key' 클릭"
    echo "4. API Key 복사"
    echo ""
    echo "💡 사용법:"
    echo "export VULTR_API_KEY='your_api_key_here'"
    echo "./scripts/vultr_api_deploy.sh"
    echo ""
    exit 1
fi

SERVER_IP="123.45.67.89"

echo ""
echo "🚀 배포 서버: $SERVER_IP"
echo ""

# 1. SSH 연결 테스트
echo "[1/5] SSH 연결 테스트..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$SERVER_IP "echo 'SSH 연결 성공'" 2>/dev/null; then
    echo "✅ SSH 연결 성공"
else
    echo "❌ SSH 연결 실패"
    echo ""
    echo "💡 해결 방법:"
    echo "1. Vultr 대시보드에서 서버 상태 확인"
    echo "2. SSH 키 등록 여부 확인"
    echo "3. 방화벽 설정 확인"
    echo ""
    exit 1
fi

# 2. 초기 설정 스크립트 업로드
echo ""
echo "[2/5] 초기 설정 스크립트 업로드..."
scp -o StrictHostKeyChecking=no scripts/vultr_initial_setup.sh root@$SERVER_IP:/root/

# 3. 초기 설정 실행
echo ""
echo "[3/5] 서버 초기 설정 실행 (약 5분 소요)..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "bash /root/vultr_initial_setup.sh"

# 4. 프로젝트 파일 업로드
echo ""
echo "[4/5] 프로젝트 파일 업로드..."
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude 'venv' \
  --exclude '.git' --exclude '*.sqlite' --exclude 'outputs' \
  --exclude '__pycache__' \
  ./ root@$SERVER_IP:/home/deploy/omnivibe/

# 5. .env 파일 생성 안내
echo ""
echo "[5/5] 환경 변수 설정 필요..."
echo ""
echo "⚠️  다음 명령으로 .env 파일을 생성하세요:"
echo ""
echo "ssh deploy@$SERVER_IP"
echo "cd /home/deploy/omnivibe"
echo "nano .env"
echo ""
echo "📋 .env 파일 템플릿:"
echo "================================"
cat << 'EOF'
ENV=production
DEBUG=False
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(32))">

DATABASE_URL=sqlite:///omni_db.sqlite
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=strong_password_here

ELEVENLABS_API_KEY=sk_...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

FORCE_HTTPS=True
EOF
echo "================================"
echo ""
echo "✅ 초기 설정 완료!"
echo ""
echo "🔐 deploy 사용자 비밀번호: omnivibe2026"
echo ""
echo "📝 다음 단계:"
echo "1. ssh deploy@$SERVER_IP"
echo "2. cd /home/deploy/omnivibe"
echo "3. nano .env (위 템플릿 복사)"
echo "4. docker-compose -f docker-compose.prod.yml up -d"
echo ""
