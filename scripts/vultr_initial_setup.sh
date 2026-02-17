#!/bin/bash

# Vultr 서버 초기 설정 스크립트
# 서버에서 직접 실행: bash vultr_initial_setup.sh

set -e

echo "================================"
echo "  Vultr 서버 초기 설정"
echo "================================"

# 1. 시스템 업데이트
echo "[1/8] 시스템 업데이트..."
apt update && apt upgrade -y

# 2. 필수 패키지 설치
echo "[2/8] 필수 패키지 설치..."
apt install -y curl git ufw htop

# 3. Docker 설치
echo "[3/8] Docker 설치..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 4. Docker Compose 설치
echo "[4/8] Docker Compose 설치..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 5. deploy 사용자 생성
echo "[5/8] deploy 사용자 생성..."
if id "deploy" &>/dev/null; then
    echo "deploy 사용자 이미 존재"
else
    adduser --disabled-password --gecos "" deploy
    echo "deploy:omnivibe2026" | chpasswd
    usermod -aG sudo,docker deploy
    echo "deploy ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi

# 6. 방화벽 설정
echo "[6/8] 방화벽 설정..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 3020/tcp

# 7. Nginx 설치
echo "[7/8] Nginx 설치..."
apt install -y nginx certbot python3-certbot-nginx

# 8. 프로젝트 디렉토리 생성
echo "[8/8] 프로젝트 디렉토리 생성..."
mkdir -p /home/deploy/omnivibe
chown -R deploy:deploy /home/deploy/omnivibe

echo "================================"
echo "  초기 설정 완료!"
echo "================================"
echo ""
echo "다음 단계:"
echo "1. 로컬에서 프로젝트 파일 업로드"
echo "2. .env 파일 설정"
echo "3. docker-compose up"
echo ""
echo "deploy 사용자 비밀번호: omnivibe2026"
echo "SSH: ssh deploy@$(curl -s ifconfig.me)"
