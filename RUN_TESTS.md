# OmniVibe Pro - 테스트 실행 가이드

**작성일**: 2026-02-01
**Phase**: Option 2 - Docker Compose & API 테스트

---

## 🚀 빠른 시작

### 1. 환경 확인
```bash
# Docker 확인
docker --version

# Docker Compose 확인 (v2)
docker compose version

# 또는 standalone (v1)
docker-compose --version
```

**참고**:
- macOS/Linux에서 Docker Desktop 설치 시 `docker compose` (v2) 사용
- standalone 설치 시 `docker-compose` (v1) 사용

### 2. 프로젝트 디렉토리 이동
```bash
cd "30_OmniVibePro/backend"
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# API 키 입력 (필수!)
nano .env  # 또는 vi, code 등
```

**필수 API 키**:
```env
OPENAI_API_KEY=sk-...          # Whisper STT용
ELEVENLABS_API_KEY=...         # TTS용
LOGFIRE_TOKEN=...              # 모니터링용
```

---

## 🐳 Docker Compose 실행

### Option A: Makefile 사용 (권장)
```bash
# 전체 서비스 시작
make up

# 헬스체크
make health

# 서비스 상태
make status

# 로그 확인
make logs

# 서비스 중지
make down
```

### Option B: 직접 명령어
```bash
# Docker Compose v2
docker compose up -d

# Docker Compose v1 (standalone)
docker-compose up -d

# 상태 확인
docker compose ps

# 로그
docker compose logs -f

# 중지
docker compose down
```

---

## 🏥 서비스 헬스체크

### 자동 스크립트 실행
```bash
chmod +x check_services.sh
./check_services.sh
```

### 수동 확인
```bash
# FastAPI
curl http://localhost:8000/
curl http://localhost:8000/health

# API 문서
open http://localhost:8000/docs

# Flower (Celery 모니터링)
open http://localhost:5555

# Neo4j 브라우저
open http://localhost:7474
```

**Neo4j 로그인**:
- Username: `neo4j`
- Password: `omnivibe_password_2026`

---

## 🧪 API 통합 테스트

### 자동 테스트 실행
```bash
chmod +x test_api.sh
./test_api.sh
```

### 테스트 항목
1. ✅ Root Health Check
2. ✅ API Health Check
3. ✅ List Available Voices
4. ✅ Check API Usage
5. ✅ Generate Verified Audio (Zero-Fault Loop)
6. ✅ Task Status Monitoring
7. ✅ Audio Download
8. ✅ Thumbnail Learning API
9. ✅ Performance Tracking API

### 수동 API 테스트

#### 1. 음성 목록 조회
```bash
curl http://localhost:8000/api/v1/audio/voices | jq '.'
```

#### 2. 오디오 생성 (Zero-Fault Audio)
```bash
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 테스트입니다.",
    "language": "ko",
    "user_id": "test_user"
  }' | jq '.'
```

**응답 예시**:
```json
{
  "status": "processing",
  "task_id": "abc-123-def-456",
  "message": "Zero-Fault Audio 생성 시작..."
}
```

#### 3. 작업 상태 확인
```bash
# task_id를 위 응답에서 복사
TASK_ID="abc-123-def-456"

curl "http://localhost:8000/api/v1/audio/status/$TASK_ID" | jq '.'
```

**진행 중**:
```json
{
  "task_id": "abc-123-def-456",
  "status": "STARTED"
}
```

**완료**:
```json
{
  "task_id": "abc-123-def-456",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "audio_path": "./outputs/audio/tts_abc12345.mp3",
    "attempts": 2,
    "final_similarity": 0.985
  }
}
```

#### 4. 오디오 다운로드
```bash
curl "http://localhost:8000/api/v1/audio/download/$TASK_ID" \
  -o verified_audio.mp3

# 재생 (macOS)
open verified_audio.mp3
```

---

## 🌸 Flower 모니터링

### 접속
```bash
open http://localhost:5555
```

### 확인 항목
- ✅ Active tasks (실행 중인 작업)
- ✅ Completed tasks (완료된 작업)
- ✅ Failed tasks (실패한 작업)
- ✅ Worker status (워커 상태)
- ✅ Task history (작업 히스토리)

---

## 🧪 Pytest 테스트

### 전체 테스트
```bash
make test

# 또는
cd backend
poetry run pytest tests/ -v
```

### 특정 테스트
```bash
# Audio Loop 테스트만
poetry run pytest tests/test_audio_loop.py -v

# 설정 테스트만
poetry run pytest tests/test_config.py -v
```

---

## 📊 Celery 작업 확인

### Celery Worker 로그
```bash
# Makefile
make logs-celery

# Docker Compose
docker compose logs -f celery_worker
```

### Celery 작업 실행 (Python)
```python
from app.tasks.audio_tasks import generate_verified_audio_task

# 작업 실행
task = generate_verified_audio_task.delay(
    text="안녕하세요, 테스트입니다.",
    language="ko",
    user_id="test_user"
)

# 작업 ID
print(task.id)

# 결과 조회
from app.tasks.celery_app import celery_app
result = celery_app.AsyncResult(task.id)
print(result.status)
print(result.result)
```

---

## 🔧 트러블슈팅

### 1. Docker Compose 실행 실패
```bash
# 포트 충돌 확인
lsof -i :8000  # FastAPI
lsof -i :6379  # Redis
lsof -i :7474  # Neo4j
lsof -i :5555  # Flower

# 기존 컨테이너 정리
docker compose down -v
docker system prune -a
```

### 2. Celery 작업이 실행되지 않음
```bash
# Celery Worker 재시작
docker compose restart celery_worker

# 로그 확인
docker compose logs celery_worker

# Redis 연결 확인
docker compose exec redis redis-cli ping
```

### 3. API 키 오류
```bash
# .env 파일 확인
cat .env | grep API_KEY

# 컨테이너에 환경 변수 전달 확인
docker compose exec api env | grep API_KEY
```

### 4. Neo4j 연결 실패
```bash
# Neo4j 로그 확인
docker compose logs neo4j

# 브라우저에서 접속
open http://localhost:7474

# Cypher 쿼리 테스트
# Username: neo4j
# Password: omnivibe_password_2026
MATCH (n) RETURN count(n)
```

---

## 🎯 성능 벤치마크

### Zero-Fault Audio Loop
```bash
# 10개 오디오 생성 (배치 테스트)
curl -X POST "http://localhost:8000/api/v1/audio/batch-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "첫 번째 테스트",
      "두 번째 테스트",
      "세 번째 테스트",
      "네 번째 테스트",
      "다섯 번째 테스트",
      "여섯 번째 테스트",
      "일곱 번째 테스트",
      "여덟 번째 테스트",
      "아홉 번째 테스트",
      "열 번째 테스트"
    ],
    "language": "ko",
    "user_id": "benchmark_user"
  }'
```

**예상 결과**:
- 평균 재시도: 1.8회
- 평균 정확도: 97.2%
- 평균 처리 시간: 8초/건

---

## 📁 생성된 파일 위치

```bash
# 오디오 파일
./outputs/audio/tts_*.mp3

# 임베딩 시각화
./embeddings_viz/

# 로그
./logs/

# 테스트 결과
./test_verified_audio.mp3
```

---

## 🎉 전체 시스템 데모

### 1단계: 서비스 시작
```bash
make up
```

### 2단계: 헬스체크
```bash
./check_services.sh
```

### 3단계: API 테스트
```bash
./test_api.sh
```

### 4단계: 대시보드 확인
```bash
make docs    # API 문서
make flower  # Celery 모니터링
make neo4j   # Neo4j 브라우저
```

---

## 📞 문제 발생 시

1. **로그 확인**
   ```bash
   make logs
   ```

2. **서비스 재시작**
   ```bash
   make restart
   ```

3. **완전 초기화**
   ```bash
   make clean-all
   make init
   ```

4. **이슈 보고**
   - GitHub Issues: `https://github.com/your-repo/issues`

---

**작성자**: Claude (Sonnet 4.5)
**ULW Ultrapilot 모드로 작성됨** 🚀
