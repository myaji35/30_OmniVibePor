#!/bin/bash
# Docker Compose 자동 설치 스크립트 (macOS)

set -e

echo "🚀 Docker Compose 설치 시작"
echo "======================================"

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 현재 상태 확인
echo -e "\n${YELLOW}1. 현재 Docker 상태 확인${NC}"
if command -v docker &> /dev/null; then
    echo -e "  Docker: ${GREEN}✓ 설치됨${NC}"
    docker --version
else
    echo -e "  Docker: ${RED}✗ 미설치${NC}"
    echo "  Docker를 먼저 설치해주세요: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# 2. Docker Compose 확인
echo -e "\n${YELLOW}2. Docker Compose 확인${NC}"

if docker compose version &> /dev/null; then
    echo -e "  docker compose: ${GREEN}✓ 이미 설치됨${NC}"
    docker compose version
    exit 0
elif command -v docker-compose &> /dev/null; then
    echo -e "  docker-compose: ${GREEN}✓ 이미 설치됨${NC}"
    docker-compose --version
    exit 0
else
    echo -e "  Docker Compose: ${YELLOW}⚠ 미설치${NC}"
fi

# 3. 설치 방법 선택
echo -e "\n${YELLOW}3. 설치 방법 선택${NC}"
echo "  [1] Homebrew로 설치 (권장)"
echo "  [2] 수동 다운로드로 설치"
echo "  [3] Docker Desktop 설치 (가장 쉬움)"
echo ""
read -p "선택하세요 (1-3): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Homebrew로 docker-compose 설치 중...${NC}"

        if ! command -v brew &> /dev/null; then
            echo -e "${RED}Homebrew가 설치되어 있지 않습니다.${NC}"
            echo "Homebrew 설치: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi

        brew install docker-compose

        echo -e "\n${GREEN}✓ 설치 완료!${NC}"
        docker-compose --version
        ;;

    2)
        echo -e "\n${YELLOW}수동으로 Docker Compose CLI 플러그인 설치 중...${NC}"

        # 아키텍처 확인
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-darwin-aarch64"
            echo "  아키텍처: Apple Silicon (arm64)"
        else
            COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-darwin-x86_64"
            echo "  아키텍처: Intel (x86_64)"
        fi

        # Docker CLI 플러그인 디렉토리 생성
        DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
        mkdir -p $DOCKER_CONFIG/cli-plugins

        # 다운로드
        echo "  다운로드 중: $COMPOSE_URL"
        curl -SL $COMPOSE_URL -o $DOCKER_CONFIG/cli-plugins/docker-compose

        # 실행 권한 부여
        chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

        echo -e "\n${GREEN}✓ 설치 완료!${NC}"
        docker compose version
        ;;

    3)
        echo -e "\n${YELLOW}Docker Desktop 설치 안내${NC}"
        echo ""
        echo "  1. 브라우저에서 다음 URL 접속:"
        echo "     https://www.docker.com/products/docker-desktop/"
        echo ""
        echo "  2. 'Download for Mac' 클릭"
        echo ""
        echo "  3. DMG 파일 다운로드 후 설치"
        echo ""
        echo "  4. Docker Desktop 실행"
        echo ""
        echo "  5. 이 스크립트를 다시 실행하세요"
        echo ""

        read -p "브라우저에서 다운로드 페이지를 여시겠습니까? (y/n): " open_browser
        if [ "$open_browser" = "y" ] || [ "$open_browser" = "Y" ]; then
            open "https://www.docker.com/products/docker-desktop/"
        fi
        exit 0
        ;;

    *)
        echo -e "${RED}잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

# 4. 설치 확인
echo -e "\n${YELLOW}4. 설치 확인${NC}"

if docker compose version &> /dev/null; then
    echo -e "  docker compose: ${GREEN}✓ 사용 가능${NC}"
    docker compose version
elif command -v docker-compose &> /dev/null; then
    echo -e "  docker-compose: ${GREEN}✓ 사용 가능${NC}"
    docker-compose --version
else
    echo -e "  ${RED}✗ 설치에 실패했습니다.${NC}"
    exit 1
fi

# 5. 다음 단계 안내
echo -e "\n${GREEN}======================================"
echo "✓ Docker Compose 설치 완료!"
echo "======================================${NC}"
echo ""
echo "다음 단계:"
echo "  1. cd backend"
echo "  2. cp .env.example .env"
echo "  3. nano .env  (API 키 입력)"
echo "  4. make demo"
echo ""
echo "또는:"
echo "  - make up      : 서비스 시작"
echo "  - make status  : 상태 확인"
echo "  - make logs    : 로그 확인"
echo "  - make down    : 서비스 중지"
echo ""
