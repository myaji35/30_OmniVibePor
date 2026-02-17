#!/bin/bash

# Vultr 서버 배포 스크립트
# 사용법: ./deploy_to_vultr.sh <server-ip>

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  OmniVibe Pro - Vultr 배포 스크립트${NC}"
echo -e "${GREEN}=====================================${NC}\n"

# 서버 IP 입력
if [ -z "$1" ]; then
    read -p "Vultr 서버 IP 주소를 입력하세요: " SERVER_IP
else
    SERVER_IP=$1
fi

read -p "SSH 사용자명 (기본: deploy): " SSH_USER
SSH_USER=${SSH_USER:-deploy}

echo -e "\n${YELLOW}배포 대상:${NC} $SSH_USER@$SERVER_IP"
read -p "계속하시겠습니까? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "배포 취소"
    exit 0
fi

echo -e "\n${GREEN}[1/6] 프로젝트 파일 동기화${NC}"
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude 'venv' \
  --exclude '.git' --exclude '*.sqlite' --exclude 'outputs' \
  ./ $SSH_USER@$SERVER_IP:/home/$SSH_USER/omnivibe/

echo -e "\n${GREEN}[2/6] 환경 변수 설정 확인${NC}"
ssh $SSH_USER@$SERVER_IP "cd /home/$SSH_USER/omnivibe && \
  if [ ! -f .env ]; then \
    echo '.env 파일이 없습니다. 서버에서 직접 생성하세요.'; \
    exit 1; \
  else \
    echo '.env 파일 존재 확인'; \
  fi"

echo -e "\n${GREEN}[3/6] Docker 이미지 빌드${NC}"
ssh $SSH_USER@$SERVER_IP "cd /home/$SSH_USER/omnivibe && \
  docker-compose -f docker-compose.prod.yml build"

echo -e "\n${GREEN}[4/6] 기존 컨테이너 중지${NC}"
ssh $SSH_USER@$SERVER_IP "cd /home/$SSH_USER/omnivibe && \
  docker-compose -f docker-compose.prod.yml down || true"

echo -e "\n${GREEN}[5/6] 새 컨테이너 시작${NC}"
ssh $SSH_USER@$SERVER_IP "cd /home/$SSH_USER/omnivibe && \
  docker-compose -f docker-compose.prod.yml up -d"

echo -e "\n${GREEN}[6/6] 배포 확인${NC}"
sleep 5
ssh $SSH_USER@$SERVER_IP "cd /home/$SSH_USER/omnivibe && \
  docker-compose -f docker-compose.prod.yml ps"

echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}  배포 완료!${NC}"
echo -e "${GREEN}=====================================${NC}\n"

echo -e "Health Check: ${YELLOW}curl http://$SERVER_IP:8000/health${NC}"
echo -e "Frontend: ${YELLOW}http://$SERVER_IP:3020${NC}\n"

echo -e "${YELLOW}다음 단계:${NC}"
echo "1. DNS A 레코드 설정: $SERVER_IP"
echo "2. Nginx 설정 확인"
echo "3. Let's Encrypt SSL 설정"
echo "4. 백업 Cron 설정\n"
