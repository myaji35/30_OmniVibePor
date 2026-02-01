# OmniVibe Pro - 빠른 시작 가이드

**대표님을 위한 3단계 실행 가이드** 🚀

---

## 📋 사전 요구사항

- ✅ Docker 설치됨 (Docker v29.2.0)
- ❌ Docker Compose 필요 (현재 미설치)

---

## 🎯 Step 1: Docker Compose 설치 (5분)

### Option A: 자동 설치 스크립트 (권장) ⭐
```bash
chmod +x INSTALL_DOCKER_COMPOSE.sh
./INSTALL_DOCKER_COMPOSE.sh
```

스크립트가 다음을 안내합니다:
1. Homebrew로 설치
2. 수동 다운로드
3. Docker Desktop 설치 (가장 쉬움)

### Option B: 수동 설치 (Homebrew)
```bash
# Homebrew로 docker-compose 설치
brew install docker-compose

# 확인
docker-compose --version
```

### Option C: Docker Desktop (가장 쉬움)
```bash
# 다운로드 페이지 열기
open "https://www.docker.com/products/docker-desktop/"

# DMG 파일 다운로드 → 설치 → 실행
```

**Docker Desktop 장점**:
- ✅ Docker + Compose 한번에 설치
- ✅ GUI로 컨테이너 관리
- ✅ 자동 업데이트
- ✅ macOS 최적화

---

## 🎯 Step 2: 환경 변수 설정 (3분)

```bash
cd backend

# .env 파일 생성
cp .env.example .env

# 편집기로 열기
nano .env
# 또는
code .env
# 또는
vi .env
```

**필수 API 키 입력**:
```env
# OpenAI (Whisper STT용)
OPENAI_API_KEY=sk-proj-...

# ElevenLabs (TTS용)
ELEVENLABS_API_KEY=...

# Logfire (모니터링용)
LOGFIRE_TOKEN=...

# Secret Key (아무 값이나)
SECRET_KEY=your-secret-key-change-in-production
```

**선택 API 키** (나중에 설정 가능):
```env
YOUTUBE_API_KEY=...
GOOGLE_VEO_API_KEY=...
HEYGEN_API_KEY=...
```

저장: `Ctrl+X` → `Y` → `Enter` (nano 기준)

---

## 🎯 Step 3: 실행 (1분)

### Option A: 자동 데모 (권장)
```bash
make demo
```

자동으로 실행:
1. 서비스 시작 (FastAPI, Celery, Redis, Neo4j)
2. API 테스트 실행
3. 대시보드 열기

### Option B: 단계별 실행
```bash
# 1. 서비스 시작
make up

# 2. 헬스체크
./check_services.sh

# 3. API 테스트
./test_api.sh

# 4. 대시보드 열기
make docs    # http://localhost:8000/docs
make flower  # http://localhost:5555
```

---

## 🌐 접속 주소

| 서비스 | URL | 설명 |
|--------|-----|------|
| **FastAPI** | http://localhost:8000 | 메인 API |
| **API 문서** | http://localhost:8000/docs | Swagger UI |
| **Flower** | http://localhost:5555 | Celery 모니터링 |
| **Neo4j** | http://localhost:7474 | 그래프 DB (ID: neo4j, PW: omnivibe_password_2026) |

---

## 🧪 첫 번째 API 테스트

### 1. 음성 목록 조회
```bash
curl http://localhost:8000/api/v1/audio/voices | jq '.'
```

**예상 응답**:
```json
{
  "voices": {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "domi": "AZnzlk1XvdvUeBnXmlld",
    ...
  },
  "total": 9
}
```

### 2. Zero-Fault Audio 생성
```bash
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 테스트입니다.",
    "language": "ko"
  }' | jq '.'
```

**예상 응답**:
```json
{
  "status": "processing",
  "task_id": "abc-123-def-456",
  "message": "Zero-Fault Audio 생성 시작..."
}
```

### 3. 작업 상태 확인
```bash
# task_id를 위에서 복사
curl "http://localhost:8000/api/v1/audio/status/abc-123-def-456" | jq '.'
```

### 4. 오디오 다운로드
```bash
curl "http://localhost:8000/api/v1/audio/download/abc-123-def-456" \
  -o verified_audio.mp3

# 재생
open verified_audio.mp3
```

---

## 📊 모니터링

### Flower (Celery 작업 모니터링)
```bash
open http://localhost:5555
```

확인 가능:
- 실행 중인 작업
- 완료된 작업
- 실패한 작업
- 워커 상태

### API 문서 (Swagger UI)
```bash
open http://localhost:8000/docs
```

모든 API 엔드포인트 테스트 가능

---

## 🛑 서비스 중지

```bash
# 서비스 중지
make down

# 또는
docker compose down
```

---

## 🔧 트러블슈팅

### 문제 1: Port already in use
**해결**:
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8000
lsof -i :6379

# 프로세스 종료
kill -9 <PID>
```

### 문제 2: API 키 오류
**해결**:
```bash
# .env 파일 확인
cat .env | grep API_KEY

# 컨테이너 재시작
make restart
```

### 문제 3: Celery 작업 실행 안됨
**해결**:
```bash
# Celery Worker 로그 확인
make logs-celery

# Worker 재시작
docker compose restart celery_worker
```

---

## 📁 유용한 Makefile 명령어

```bash
make help          # 모든 명령어 보기
make up            # 서비스 시작
make down          # 서비스 중지
make restart       # 재시작
make status        # 상태 확인
make logs          # 로그 확인
make test-api      # API 테스트
make clean         # 생성 파일 정리
make clean-all     # 완전 초기화
```

---

## 🎉 성공 확인

다음이 모두 작동하면 성공입니다:

- ✅ `make up` 실행 성공
- ✅ http://localhost:8000 접속 가능
- ✅ http://localhost:8000/docs 접속 가능
- ✅ http://localhost:5555 접속 가능
- ✅ `curl http://localhost:8000/api/v1/audio/voices` 성공
- ✅ Zero-Fault Audio 생성 성공

---

## 📞 다음 단계

### Phase 0 기능 (자가학습 시스템)
```bash
# 썸네일 학습 API
curl "http://localhost:8000/api/v1/thumbnails/search?query=AI"

# 성과 추적 API
curl "http://localhost:8000/api/v1/performance/insights/test_user"
```

### Phase 1 기능 (Zero-Fault Audio)
```bash
# 배치 오디오 생성
curl -X POST "http://localhost:8000/api/v1/audio/batch-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["첫 번째", "두 번째", "세 번째"]
  }'
```

### Phase 2 예정 (LangGraph Agents)
- Writer 에이전트 (스크립트 생성)
- Director 에이전트 (영상 제작)
- Marketer 에이전트 (배포 자동화)

---

## 📖 추가 문서

- **DOCKER_SETUP.md** - Docker Compose 설치 상세 가이드
- **RUN_TESTS.md** - 테스트 실행 가이드
- **ULTRAPILOT_COMPLETE.md** - 완료 보고서
- **PHASE1_POC_COMPLETE.md** - Phase 1 상세 보고서

---

**작성자**: Claude (Sonnet 4.5)
**대표님, 이 가이드대로만 하시면 5-10분 안에 전체 시스템 실행 가능합니다!** 🚀
