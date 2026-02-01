# Docker Compose 설치 가이드

**현재 상태**: Docker는 설치되어 있지만 Compose 플러그인이 없음
**목표**: Docker Compose를 사용하여 OmniVibe Pro 실행

---

## 🎯 Option 1: Docker Compose v2 플러그인 설치 (권장)

### macOS (Homebrew)
```bash
# 1. Docker Compose CLI 플러그인 설치
brew install docker-compose

# 2. 확인
docker compose version
```

### 또는 수동 설치
```bash
# 1. Docker Compose CLI 플러그인 다운로드
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins

# 2. 최신 버전 다운로드 (Apple Silicon)
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-darwin-aarch64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose

# Intel Mac인 경우
# curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-darwin-x86_64 \
#   -o $DOCKER_CONFIG/cli-plugins/docker-compose

# 3. 실행 권한 부여
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# 4. 확인
docker compose version
```

---

## 🎯 Option 2: Standalone docker-compose 설치

### macOS (Homebrew)
```bash
# 1. Standalone 버전 설치
brew install docker-compose

# 2. 확인
docker-compose --version

# 3. Makefile 수정 (자동으로 처리됨)
```

---

## 🎯 Option 3: Docker Desktop 설치 (가장 쉬움)

### Docker Desktop for Mac
```bash
# 1. Docker Desktop 다운로드
# https://www.docker.com/products/docker-desktop/

# 2. DMG 파일 설치 후 실행

# 3. Docker Desktop 실행하면 자동으로 docker compose 포함됨

# 4. 확인
docker compose version
```

**장점**:
- ✅ Docker + Docker Compose 한번에 설치
- ✅ GUI 제공 (컨테이너 관리 편함)
- ✅ Kubernetes 통합
- ✅ 자동 업데이트

---

## 🔍 현재 상태 확인

```bash
# Docker 확인
docker --version

# Docker Compose 확인
docker compose version       # v2 (플러그인)
# 또는
docker-compose --version     # v1 (standalone)
```

---

## 🚀 설치 후 실행

### 1. 환경 변수 설정
```bash
cd backend
cp .env.example .env
nano .env  # API 키 입력
```

### 2. Docker Compose 실행

#### Option A: docker compose (v2)
```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

#### Option B: docker-compose (v1)
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
docker-compose down
```

#### Option C: Makefile (자동 감지)
```bash
make up      # 자동으로 사용 가능한 명령어 사용
make status
make logs
make down
```

---

## 🎨 Makefile 자동 감지 기능

Makefile이 자동으로 사용 가능한 명령어를 감지합니다:

```makefile
# 자동 감지
DOCKER_COMPOSE = $(shell command -v docker compose 2>/dev/null || echo docker-compose)
```

사용:
```bash
make up    # docker compose 또는 docker-compose 자동 선택
```

---

## 🐛 트러블슈팅

### 문제 1: docker: unknown command: docker compose
**원인**: Docker Compose 플러그인 미설치
**해결**: Option 1 또는 Option 2 실행

### 문제 2: docker-compose: command not found
**원인**: Standalone docker-compose 미설치
**해결**: Option 2 실행

### 문제 3: Permission denied
**원인**: Docker 데몬 권한 문제
**해결**:
```bash
# macOS - Docker Desktop 실행
open -a Docker

# 또는 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
```

---

## 💡 권장 방법

### 대표님께는 **Option 3 (Docker Desktop)** 추천드립니다!

**이유**:
1. ✅ 가장 쉬운 설치
2. ✅ Docker + Compose 한번에 해결
3. ✅ GUI로 컨테이너 관리 편함
4. ✅ macOS 최적화
5. ✅ Flower, Neo4j 등 웹 UI 쉽게 접근

**설치 링크**: https://www.docker.com/products/docker-desktop/

---

## 📋 설치 후 체크리스트

- [ ] Docker 설치 확인: `docker --version`
- [ ] Docker Compose 확인: `docker compose version`
- [ ] Docker 데몬 실행 중: `docker ps`
- [ ] 환경 변수 설정: `.env` 파일 생성
- [ ] 테스트 실행: `make demo`

---

**다음 단계**: 설치 완료 후 `make demo` 실행하시면 됩니다!
