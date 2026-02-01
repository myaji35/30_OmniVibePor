# System Health Check & Auto-Recovery Command

**Usage**: `/health` (인자 없음)

## 목적
OmniVibe Pro 시스템의 전체 상태를 점검하고, 발견된 문제를 자동으로 해결합니다.

## 실행 로직

당신은 이제 **Autonomous Health Manager**로 동작합니다.

### Step 1: 헬스 체크 카테고리 분석
다음 4개 카테고리를 순차적으로 점검합니다:
1. Infrastructure (인프라)
2. Dependencies (의존성)
3. Configuration (설정)
4. Code Quality (코드 품질)

### Step 2: 병렬 점검 실행
각 카테고리 내에서는 병렬로 점검을 수행합니다.

```
🏥 시스템 헬스 체크 시작...

[Infrastructure 점검]
- Docker containers 상태 확인 중...
- 포트 가용성 확인 중...
- 볼륨 마운트 확인 중...
- 네트워크 연결 확인 중...

[Dependencies 점검]
- Python 패키지 확인 중...
- Node 패키지 확인 중...
- 시스템 의존성 확인 중...

[Configuration 점검]
- .env 파일 확인 중...
- API 키 유효성 검증 중...
- 데이터베이스 연결 확인 중...
- 외부 서비스 연결 확인 중...

[Code Quality 점검]
- Linting 검사 중...
- Type 검사 중...
- 테스트 실행 중...
- 빌드 검증 중...
```

### Step 3: 문제 탐지 및 자동 복구

각 문제에 대해 다음 로직을 따릅니다:

#### Infrastructure 문제

**컨테이너 다운**
- 탐지: `docker ps | grep {container_name}`
- 자동 수정: `docker-compose up -d {container_name}`
- 에스컬레이션: 3회 재시작 실패 시 사용자에게 로그 제공

**포트 충돌**
- 탐지: `lsof -i :{port}`
- 자동 수정: 충돌 프로세스 종료 (개발 환경만)
- 에스컬레이션: 프로덕션 환경에서는 사용자 확인 필요

**볼륨 마운트 실패**
- 탐지: `docker volume ls` + 컨테이너 inspect
- 자동 수정: `docker-compose down -v && docker-compose up -d`
- 에스컬레이션: 데이터 손실 가능성 있으면 사용자 확인

**네트워크 연결 끊김**
- 탐지: `docker network inspect {network_name}`
- 자동 수정: `docker network connect {network} {container}`
- 에스컬레이션: 네트워크 재생성 필요 시 사용자 확인

#### Dependencies 문제

**Python 패키지 누락**
- 탐지: `poetry check` 또는 `pip list` vs `pyproject.toml`
- 자동 수정: `poetry install` 또는 `pip install -r requirements.txt`
- 에스컬레이션: 버전 충돌 시 사용자 선택 필요

**Node 패키지 누락**
- 탐지: `npm ls` vs `package.json`
- 자동 수정: `npm install` 또는 `yarn install`
- 에스컬레이션: peer dependency 충돌 시 사용자 확인

**시스템 의존성 누락**
- 탐지: `which {command}` (ffmpeg, imagemagick 등)
- 자동 수정:
  - macOS: `brew install {package}`
  - Ubuntu: `sudo apt-get install {package}`
- 에스컬레이션: sudo 권한 필요 시 사용자 확인

#### Configuration 문제

**.env 파일 누락/불완전**
- 탐지: `.env` 파일 존재 확인 + 필수 변수 체크
- 자동 수정: `.env.example`에서 복사 (값은 비워둠)
- 에스컬레이션: **항상 사용자에게 값 입력 요청**

**API 키 유효성 문제**
- 탐지: 각 서비스에 테스트 요청 전송
  - ElevenLabs: `GET /v1/voices`
  - OpenAI: `GET /v1/models`
  - Google Sheets: 테스트 시트 읽기
  - Neo4j: `MATCH (n) RETURN count(n) LIMIT 1`
- 자동 수정: 없음
- 에스컬레이션: **항상 사용자에게 키 재입력 요청**

**데이터베이스 연결 실패**
- 탐지: Neo4j/Redis 연결 테스트
- 자동 수정: 컨테이너 재시작 시도
- 에스컬레이션: 재시작 후에도 실패 시 설정 확인 요청

**외부 서비스 연결 실패**
- 탐지: `curl` 또는 `requests` 테스트
- 자동 수정: 재시도 (exponential backoff)
- 에스컬레이션: 네트워크 문제 또는 서비스 장애 보고

#### Code Quality 문제

**Linting 에러**
- 탐지: `ruff check .` (Python), `eslint .` (JavaScript)
- 자동 수정: `ruff check --fix .`, `eslint --fix .`
- 에스컬레이션: auto-fix 불가능한 에러는 보고만 (수정 안 함)

**Type 에러**
- 탐지: `mypy .` (Python), `tsc --noEmit` (TypeScript)
- 자동 수정: 없음
- 에스컬레이션: **항상 사용자에게 보고** (자동 수정하지 않음)

**테스트 실패**
- 탐지: `pytest`, `npm test`
- 자동 수정: 없음
- 에스컬레이션: **항상 사용자에게 보고** (테스트는 절대 자동 수정 안 함)

**빌드 에러**
- 탐지: `docker-compose build`, `npm run build`
- 자동 수정: 의존성 문제라면 재설치 시도
- 에스컬레이션: 코드 문제라면 사용자에게 보고

### Step 4: 헬스 리포트 생성

모든 점검 완료 후 다음 형식으로 보고합니다:

```
🏥 시스템 헬스 체크 결과

✅ Infrastructure (4/4)
  ✅ Docker containers: All running
    - api: running (healthy)
    - celery_worker: running (healthy)
    - redis: running (healthy)
    - neo4j: running (healthy)
  ✅ Ports: All available
    - 8000: api (available)
    - 6379: redis (available)
    - 7474: neo4j (available)
    - 7687: neo4j bolt (available)
  ✅ Volumes: Mounted correctly
    - neo4j_data: mounted
    - redis_data: mounted
  ✅ Network: Connected
    - omnivibe_network: active

⚠️ Dependencies (3/4)
  ✅ Python packages: All installed (45/45)
  ✅ Node packages: All installed (127/127)
  ❌ System: ffmpeg not found
    → 자동 수정 시도: brew install ffmpeg 실행...
    ✅ 해결 완료 (설치됨)
  ✅ System dependencies: Complete
    - ffmpeg: ✅ installed
    - imagemagick: ✅ installed

✅ Configuration (5/5)
  ✅ .env file: Present (12/12 variables)
  ✅ API keys: All valid
    - ELEVENLABS_API_KEY: ✅ valid (quota: 87%)
    - OPENAI_API_KEY: ✅ valid
    - GOOGLE_SHEETS_CREDENTIALS: ✅ valid
    - PINECONE_API_KEY: ✅ valid
  ✅ Neo4j: Connected (v5.15.0)
    - Status: online
    - Nodes: 1,247
    - Relationships: 3,891
  ✅ Redis: Connected (v7.2.3)
    - Status: online
    - Memory: 2.3 MB / 512 MB
  ✅ ElevenLabs API: Responding (latency: 234ms)

✅ Code Quality (4/4)
  ✅ Linting: No errors
    - ruff: ✅ 0 errors (auto-fixed 3 warnings)
    - eslint: ✅ 0 errors
  ✅ Type check: Passing
    - mypy: ✅ Success
    - tsc: ✅ Success
  ✅ Tests: 45 passed
    - backend: 32 passed, 0 failed
    - frontend: 13 passed, 0 failed
    - Coverage: 78% (target: 80%)
  ✅ Build: Successful
    - backend Docker image: ✅ built
    - frontend bundle: ✅ built (2.3 MB)

🎉 전체 상태: 양호 (16/17 checks passed)
⏱️ 점검 시간: 1분 23초
🔧 자동 수정: 1건 해결

📋 권장 사항:
  • 테스트 커버리지를 80%까지 높이세요 (현재: 78%)
  • ElevenLabs API 쿼터가 87% 사용되었습니다. 곧 리필이 필요할 수 있습니다.
```

### Step 5: 심각한 문제 발견 시

critical 문제가 발견되면 즉시 보고하고 실행을 중단합니다:

```
🚨 치명적인 문제 발견!

❌ Infrastructure: CRITICAL
  ❌ Neo4j: Connection refused
    - Error: Connection refused at localhost:7687
    - 자동 수정 시도: docker-compose restart neo4j
    - 결과: 3회 재시작 실패

    📋 추천 조치:
    1. 로그 확인: docker logs neo4j
    2. 포트 충돌 확인: lsof -i :7687
    3. 데이터 볼륨 확인: docker volume inspect neo4j_data

    대표님, Neo4j 컨테이너를 수동으로 확인해 주세요.
    위 로그를 확인하시겠습니까?

⏸️ 헬스 체크 중단 (critical error)
```

## 자율 실행 규칙

### 1. 자동 수정 권한

**자동 수정 가능** (사용자 확인 불필요):
- Docker 컨테이너 재시작
- 패키지 설치/업데이트
- Linting 자동 수정
- 임시 파일 정리
- 캐시 초기화

**사용자 확인 필요**:
- .env 파일 수정 (값 입력)
- API 키 변경
- 프로덕션 데이터베이스 변경
- sudo 권한이 필요한 작업
- 데이터 손실 가능성이 있는 작업

**절대 자동 수정 금지**:
- 테스트 코드 수정
- Type 에러 수정 (보고만 함)
- 비즈니스 로직 변경

### 2. 재시도 로직

- **일시적 에러**: 3회까지 exponential backoff로 재시도
- **네트워크 에러**: 5회까지 재시도 (1초, 2초, 4초, 8초, 16초)
- **API 에러**: 3회까지 재시도 (rate limit 고려)
- **재시도 실패**: 사용자에게 상세 에러 로그 제공

### 3. 점검 스킵 조건

다음 경우 해당 점검을 스킵합니다:
- 프론트엔드가 없는 경우: Node 패키지 점검 스킵
- CI/CD 환경: Docker 점검 스킵
- 오프라인 모드: 외부 서비스 연결 점검 스킵

## 사전 예방적 헬스 체크

다음 상황에서 자동으로 `/health`를 실행합니다:

### 1. 시작 시 자동 점검
- `/phase` 명령 실행 전
- 서버 재시작 후 첫 요청
- 배포 스크립트 실행 전

### 2. 변경 후 자동 점검
- 의존성 업데이트 후 (`poetry add`, `npm install`)
- Docker 이미지 재빌드 후
- .env 파일 수정 후

### 3. 주기적 자동 점검
- 개발 중: 매 1시간마다 (백그라운드)
- 프로덕션: 매 5분마다 (경량 점검)

### 4. 에러 발생 후 자동 점검
- API 요청 실패 시
- Celery 작업 실패 시
- 예상치 못한 예외 발생 시

## 다른 명령어와의 통합

### `/phase` 연동
```
사용자: /phase 1

AI: Phase 1 실행 전 헬스 체크를 수행합니다...

🏥 시스템 헬스 체크 결과
✅ 전체 상태: 양호 (16/16 checks passed)

✅ 헬스 체크 통과! Phase 1 실행을 시작합니다...
```

### `/auto` 연동
```
/auto 실행 마지막 단계:

✅ 모든 작업 완료
✅ 최종 헬스 체크 실행...

🏥 시스템 헬스 체크 결과
⚠️ 경고 1건 발견
  - 테스트 커버리지: 76% (목표: 80%)

📋 권장 사항: 테스트 추가를 고려하세요.
```

### 사용자 수동 실행
```
사용자: /health

AI: 시스템 헬스 체크를 수행합니다...

[전체 점검 실행]

🎉 전체 상태: 양호
```

## 문제별 트러블슈팅 가이드

### 컨테이너 시작 실패

**증상**: `docker ps`에서 컨테이너가 보이지 않음

**자동 진단**:
1. 로그 확인: `docker logs {container_name}`
2. 이전 컨테이너 확인: `docker ps -a`
3. 포트 충돌 확인: `lsof -i :{port}`
4. 이미지 존재 확인: `docker images`

**자동 수정 시도**:
1. 기존 컨테이너 제거: `docker rm -f {container_name}`
2. 네트워크 재생성: `docker network create omnivibe_network`
3. 재시작: `docker-compose up -d {container_name}`

**에스컬레이션**:
```
❌ {container_name} 컨테이너 시작 실패

자동 수정 3회 실패:
  1차: 컨테이너 재생성 → 실패 (포트 8000 이미 사용 중)
  2차: 충돌 프로세스 종료 → 실패 (프로세스 찾을 수 없음)
  3차: 네트워크 재생성 → 실패 (권한 거부)

📋 수동 조치 필요:
1. 포트를 사용 중인 프로세스 확인:
   $ lsof -i :8000

2. 필요시 프로세스 종료:
   $ kill -9 {PID}

3. Docker 재시작:
   $ docker-compose down && docker-compose up -d

대표님, 위 단계를 진행하시겠습니까?
```

### API 키 유효성 실패

**증상**: API 호출 시 401/403 에러

**자동 진단**:
1. .env 파일에서 키 존재 확인
2. 키 형식 검증 (길이, 접두사)
3. 테스트 요청으로 유효성 확인
4. 쿼터/사용량 확인

**자동 수정 시도**:
- 없음 (보안상 자동 수정 불가)

**에스컬레이션**:
```
❌ ElevenLabs API 키 유효성 실패

Error: 401 Unauthorized
Response: {"detail": "Invalid API key"}

현재 키: sk-...xyzw (마지막 4자리)

📋 해결 방법:
1. ElevenLabs 대시보드에서 키 확인:
   https://elevenlabs.io/api

2. .env 파일 업데이트:
   ELEVENLABS_API_KEY=your-new-key

3. 컨테이너 재시작:
   docker-compose restart api

대표님, 새 API 키를 입력하시겠습니까?
[Yes] [No, 나중에]
```

### 의존성 버전 충돌

**증상**: 패키지 설치 실패

**자동 진단**:
1. `poetry lock` 또는 `npm ls` 실행
2. 충돌하는 패키지 식별
3. 버전 제약 분석

**자동 수정 시도**:
1. 캐시 삭제: `poetry cache clear . --all` / `npm cache clean --force`
2. 재설치: `poetry install` / `npm install`
3. lock 파일 업데이트: `poetry lock --no-update` / `npm update`

**에스컬레이션**:
```
⚠️ 의존성 버전 충돌 발견

Conflict:
  pydantic v2.5.0 requires typing-extensions >=4.6.0
  fastapi v0.104.0 requires typing-extensions >=4.8.0

자동 수정 시도:
  ✅ 캐시 삭제 완료
  ❌ 재설치 실패 (버전 불일치)

📋 권장 해결책:
Option 1: pydantic 업그레이드
  $ poetry add pydantic@^2.6.0

Option 2: fastapi 다운그레이드
  $ poetry add fastapi@^0.103.0

Option 3: typing-extensions 명시적 버전 고정
  $ poetry add typing-extensions@^4.8.0

대표님, 어떤 옵션을 선택하시겠습니까?
[Option 1] [Option 2] [Option 3] [직접 수정]
```

### 테스트 실패

**증상**: `pytest` 또는 `npm test` 실패

**자동 진단**:
1. 실패한 테스트 목록 수집
2. 에러 메시지 분석
3. 최근 변경사항 확인 (git diff)

**자동 수정 시도**:
- 없음 (테스트는 절대 자동 수정하지 않음)

**에스컬레이션**:
```
❌ 테스트 실패 (3/45)

FAILED tests/test_audio.py::test_tts_generation
  AssertionError: Expected status 200, got 500

FAILED tests/test_audio.py::test_stt_accuracy
  AssertionError: Accuracy 0.89 below threshold 0.95

FAILED tests/integration/test_audio_loop.py::test_correction_loop
  TimeoutError: Loop did not converge within 30 seconds

📊 테스트 통계:
  - 총 테스트: 45
  - 성공: 42 (93%)
  - 실패: 3 (7%)
  - 건너뜀: 0
  - 소요 시간: 2분 34초

📋 실패 원인 분석:
1. test_tts_generation: ElevenLabs API 연결 실패 (네트워크?)
2. test_stt_accuracy: STT 정확도 저하 (모델 변경?)
3. test_correction_loop: 타임아웃 (임계값 조정 필요?)

대표님, 테스트 로그를 자세히 확인하시겠습니까?
[Yes] [No] [특정 테스트만 재실행]
```

### 빌드 실패

**증상**: Docker 빌드 또는 npm build 실패

**자동 진단**:
1. 빌드 로그 분석
2. 디스크 공간 확인
3. 메모리 사용량 확인
4. 이전 빌드 아티팩트 확인

**자동 수정 시도**:
1. 빌드 캐시 삭제: `docker builder prune -f`
2. node_modules 재설치: `rm -rf node_modules && npm install`
3. 디스크 공간 확보: `docker system prune -f`

**에스컬레이션**:
```
❌ Docker 빌드 실패

Error at Step 7/12:
  RUN pip install poetry && poetry install --no-dev
  ERROR: No matching distribution found for torch==2.1.0

자동 수정 시도:
  ✅ 빌드 캐시 삭제 완료
  ❌ 재빌드 실패 (같은 에러)
  ✅ 디스크 공간 확보 (12GB 확보)
  ❌ 재빌드 실패 (같은 에러)

📋 원인 분석:
PyPI에서 torch 2.1.0을 찾을 수 없음
가능한 원인:
  1. torch 2.1.0이 현재 Python 버전(3.11)을 지원하지 않음
  2. torch 2.1.0이 macOS ARM64를 지원하지 않음
  3. PyPI 일시적 장애

📋 권장 해결책:
Option 1: torch 버전 업그레이드
  pyproject.toml에서 torch = "^2.2.0"로 변경

Option 2: Python 버전 다운그레이드
  Dockerfile에서 python:3.10-slim 사용

Option 3: 플랫폼 명시
  --platform linux/amd64 플래그 추가

대표님, 어떤 옵션을 선택하시겠습니까?
[Option 1] [Option 2] [Option 3] [직접 수정]
```

## 성능 최적화

### 경량 헬스 체크 (빠른 점검)
자주 실행되는 경우 (매 5분) 경량 버전 사용:
- Docker 컨테이너 상태만 확인
- API 엔드포인트 핑만 확인
- 코드 품질 검사 스킵
- 소요 시간: ~10초

### 전체 헬스 체크 (완전 점검)
수동 실행 또는 중요한 시점 (배포 전):
- 모든 카테고리 전체 점검
- 상세한 진단 및 리포트
- 소요 시간: ~1-2분

### 캐싱 전략
- API 키 유효성: 1시간 캐시
- 패키지 목록: 파일 변경 감지 시만 재점검
- Docker 상태: 캐시 없음 (항상 실시간)

## 헬스 체크 히스토리

모든 헬스 체크 결과를 기록합니다:
- 파일 위치: `.claude/health_history.json`
- 보관 기간: 최근 30일
- 용도: 트렌드 분석, 반복 문제 감지

```json
{
  "timestamp": "2026-02-02T10:30:00Z",
  "overall_status": "healthy",
  "checks_passed": 16,
  "checks_failed": 1,
  "duration_seconds": 83,
  "auto_fixes": 1,
  "categories": {
    "infrastructure": {"status": "healthy", "score": "4/4"},
    "dependencies": {"status": "warning", "score": "3/4"},
    "configuration": {"status": "healthy", "score": "5/5"},
    "code_quality": {"status": "healthy", "score": "4/4"}
  },
  "issues": [
    {
      "category": "dependencies",
      "severity": "warning",
      "problem": "ffmpeg not found",
      "auto_fix": "brew install ffmpeg",
      "result": "resolved"
    }
  ]
}
```

## 메타 학습

헬스 체크 실행 후 패턴을 학습하고 개선합니다:
- 자주 발생하는 문제는 사전 예방 체크리스트에 추가
- 효과적인 자동 수정 방법은 우선순위 상향
- 반복되는 에러는 CLAUDE.md에 트러블슈팅 가이드 추가
- 평균 점검 시간을 추적하여 성능 최적화

이를 통해 다음 헬스 체크는 더 빠르고 정확해집니다.
