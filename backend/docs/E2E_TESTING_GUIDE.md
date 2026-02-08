# E2E Testing Guide - OmniVibe Pro

> **전체 파이프라인 E2E 테스트 가이드**
> **Writer Agent → Director Agent → Audio → Remotion 렌더링**

---

## 📋 목차

1. [테스트 개요](#테스트-개요)
2. [테스트 구조](#테스트-구조)
3. [실행 방법](#실행-방법)
4. [테스트 시나리오](#테스트-시나리오)
5. [성능 벤치마크](#성능-벤치마크)
6. [CI/CD 통합](#cicd-통합)
7. [트러블슈팅](#트러블슈팅)

---

## 테스트 개요

### 테스트 범위

OmniVibe Pro의 E2E 테스트는 다음을 검증합니다:

1. **Writer Agent**: 스크립트 자동 생성 (Neo4j Memory 활용)
2. **Director Agent**: 콘티 자동 생성
3. **Audio Director**: Zero-Fault 오디오 생성 (99% 정확도)
4. **Remotion Service**: 영상 렌더링 및 Cloudinary 업로드
5. **Integration**: 전체 파이프라인 통합

### 테스트 철학

- **실제 환경 모방**: 프로덕션과 동일한 API 호출
- **비동기 처리**: Celery Task 상태 폴링
- **성능 측정**: 각 단계별 소요 시간 기록
- **에러 핸들링**: 예외 상황 검증

---

## 테스트 구조

```
backend/tests/
├── __init__.py
├── e2e/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures & Configuration
│   ├── test_full_pipeline.py       # 전체 파이프라인 테스트
│   ├── test_writer_agent.py        # Writer Agent 단독 테스트
│   └── test_remotion_rendering.py  # Remotion 렌더링 테스트
├── test_audio_loop.py              # Audio Loop 단위 테스트
└── ...
```

### 테스트 Fixtures

**`conftest.py`**에 정의된 공통 Fixtures:

```python
@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client for API testing"""

@pytest.fixture
def sample_campaign_data() -> dict:
    """Sample campaign configuration"""

@pytest.fixture
def sample_script() -> str:
    """Sample script text"""

@pytest.fixture
def sample_storyboard_blocks() -> list:
    """Sample storyboard blocks"""
```

---

## 실행 방법

### 1. 필수 패키지 설치

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov httpx
```

### 2. 서비스 시작

E2E 테스트는 실제 서비스가 실행 중이어야 합니다:

```bash
# Backend API 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Celery Worker 시작 (별도 터미널)
celery -A app.tasks.celery_app worker --loglevel=info

# Redis & Neo4j 시작 (Docker)
docker-compose up -d redis neo4j
```

### 3. 테스트 실행

#### 전체 테스트 실행

```bash
./run_tests.sh all
```

#### E2E 테스트만 실행

```bash
./run_tests.sh e2e
```

#### 개별 테스트 파일 실행

```bash
# 전체 파이프라인 테스트
pytest tests/e2e/test_full_pipeline.py -v

# Writer Agent 테스트
pytest tests/e2e/test_writer_agent.py -v

# Remotion 렌더링 테스트
pytest tests/e2e/test_remotion_rendering.py -v
```

#### 특정 테스트 클래스 실행

```bash
pytest tests/e2e/test_full_pipeline.py::TestFullPipeline -v
```

#### 특정 테스트 메서드 실행

```bash
pytest tests/e2e/test_full_pipeline.py::TestFullPipeline::test_01_health_check -v
```

#### 마커별 실행

```bash
# 성능 테스트만
pytest tests/e2e/ -m performance

# 에러 핸들링 테스트만
pytest tests/e2e/ -m error

# 느린 테스트 제외
pytest tests/e2e/ -m "not slow"
```

---

## 테스트 시나리오

### 1. 전체 파이프라인 테스트

**파일**: `test_full_pipeline.py::TestFullPipeline`

**테스트 플로우**:
```
Step 0: Health Check
   ↓
Step 1: Writer Agent - 스크립트 생성
   ↓
Step 2: Director Agent - 콘티 생성
   ↓
Step 3: Audio Director - 오디오 생성 (Zero-Fault Loop)
   ↓
Step 4: Remotion Props 변환
   ↓
Step 5: Remotion 영상 렌더링
   ↓
Step 6: 최종 검증
```

**실행**:
```bash
pytest tests/e2e/test_full_pipeline.py::TestFullPipeline -v
```

**예상 소요 시간**: 3-5분 (렌더링 포함)

**출력 예시**:
```
✅ Step 1: Writer Agent 호출...
   ⏱️  소요 시간: 8.23초
   ✅ 스크립트 생성 완료 (456자)
   📄 Preview: 여러분, 오늘은 놀라운 AI 비디오 에디터를...

✅ Step 2: Director Agent 호출...
   ⏱️  소요 시간: 3.45초
   ✅ 콘티 생성 완료 (5개 블록)

✅ Step 3: Audio Director 호출...
   ⏱️  소요 시간: 45.12초
   ✅ 오디오 생성 완료
   🎯 정확도: 98.5%

✅ Step 4: Remotion Props 변환...
   ⏱️  소요 시간: 0.15초
   ✅ Props 변환 완료 (5개 씬)

✅ Step 5: Remotion 영상 렌더링...
   ⏱️  소요 시간: 120.34초
   ✅ 영상 렌더링 완료
   🎥 Video URL: https://res.cloudinary.com/...
   ⏱️  영상 길이: 60초

✅ Step 6: 최종 검증...
   ✅ 스크립트: 456자
   ✅ 콘티 블록: 5개
   ✅ 오디오: https://...
   ✅ 영상: https://...

🎉 전체 파이프라인 테스트 성공!
```

### 2. Writer Agent 테스트

**파일**: `test_writer_agent.py`

**테스트 케이스**:
- ✅ Neo4j Memory를 활용한 스크립트 생성
- ✅ 플랫폼별 스크립트 (YouTube, TikTok)
- ✅ 톤별 스크립트 (professional, casual, energetic)
- ✅ 스크립트 일관성 검증
- ❌ 에러 핸들링 (필수 필드 누락, 잘못된 플랫폼)

**실행**:
```bash
pytest tests/e2e/test_writer_agent.py -v
```

### 3. Remotion 렌더링 테스트

**파일**: `test_remotion_rendering.py`

**테스트 케이스**:
- ✅ Props 변환
- ✅ 플랫폼별 최적화 (YouTube 1920x1080, TikTok 1080x1920)
- ✅ Composition 목록 조회
- ✅ Remotion 설치 검증
- ❌ 에러 핸들링 (빈 블록, 잘못된 Composition ID)

**실행**:
```bash
pytest tests/e2e/test_remotion_rendering.py -v
```

### 4. 통합 검증 테스트

**파일**: `test_full_pipeline.py::TestIntegrationChecks`

**테스트 케이스**:
- ✅ Neo4j 연결 확인
- ✅ Redis 연결 확인
- ✅ Celery Worker 상태 확인
- ✅ Remotion 설치 확인

**실행**:
```bash
pytest tests/e2e/test_full_pipeline.py::TestIntegrationChecks -v
```

---

## 성능 벤치마크

### 성능 테스트 실행

```bash
./run_tests.sh performance
```

### 성능 기준 (KPI)

| 컴포넌트 | 목표 시간 | 현재 평균 | 상태 |
|---------|----------|----------|------|
| Writer Agent | < 10초 | 8.5초 | ✅ |
| Director Agent | < 5초 | 3.8초 | ✅ |
| Audio Generation | < 60초 | 45초 | ✅ |
| Props Conversion | < 1초 | 0.2초 | ✅ |
| Remotion Render | < 120초 | 105초 | ✅ |

### 성능 벤치마크 테스트

**파일**: `test_full_pipeline.py::TestPerformanceBenchmark`

```bash
pytest tests/e2e/test_full_pipeline.py::TestPerformanceBenchmark -v
```

**출력 예시**:
```
📊 Writer Agent 성능:
   ⏱️  응답 시간: 8.23초
   🎯 목표: < 10초

📊 Props 변환 성능:
   ⏱️  응답 시간: 0.15초
   🎯 목표: < 1초

📊 동시 처리 성능:
   10개 요청 처리: 2.34초
   평균: 0.23초/요청
```

---

## CI/CD 통합

### GitHub Actions 설정

**`.github/workflows/test.yml`**:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      neo4j:
        image: neo4j:5.16
        env:
          NEO4J_AUTH: neo4j/testpassword
        ports:
          - 7474:7474
          - 7687:7687

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx

      - name: Run E2E tests
        env:
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: testpassword
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/e2e/ -m "not slow" -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

### GitLab CI 설정

**`.gitlab-ci.yml`**:

```yaml
test:e2e:
  stage: test
  image: python:3.11
  services:
    - redis:7-alpine
    - neo4j:5.16
  variables:
    NEO4J_AUTH: neo4j/testpassword
    REDIS_URL: redis://redis:6379/0
  script:
    - cd backend
    - pip install -r requirements.txt pytest pytest-asyncio httpx
    - pytest tests/e2e/ -m "not slow" -v
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage.xml
```

---

## 트러블슈팅

### 문제 1: Tests not found

**증상**:
```
ERROR: file or directory not found: tests/e2e/
```

**해결**:
```bash
# 올바른 디렉토리에서 실행
cd backend
pytest tests/e2e/ -v
```

### 문제 2: Connection refused (Redis/Neo4j)

**증상**:
```
ConnectionError: Error connecting to Redis
```

**해결**:
```bash
# Redis & Neo4j 시작
docker-compose up -d redis neo4j

# 연결 확인
docker ps | grep redis
docker ps | grep neo4j
```

### 문제 3: Backend API not running

**증상**:
```
httpx.ConnectError: [Errno 61] Connection refused
```

**해결**:
```bash
# Backend API 시작
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 별도 터미널에서 테스트 실행
pytest tests/e2e/ -v
```

### 문제 4: Celery task timeout

**증상**:
```
AssertionError: Audio generation timeout (60s)
```

**해결**:
```bash
# Celery Worker 시작 확인
celery -A app.tasks.celery_app worker --loglevel=info

# Worker 로그 확인
docker logs -f omnivibe-celery-worker

# Task 상태 확인
docker exec -it omnivibe-redis redis-cli
LLEN celery
```

### 문제 5: Test failed but no error message

**증상**:
테스트 실패하지만 명확한 에러 메시지 없음

**해결**:
```bash
# 더 상세한 로그 출력
pytest tests/e2e/ -v -s --log-cli-level=DEBUG

# 특정 테스트만 실행
pytest tests/e2e/test_full_pipeline.py::TestFullPipeline::test_01_health_check -v -s
```

---

## 유용한 명령어

### 테스트 마커 확인

```bash
pytest --markers
```

### 테스트 목록 확인 (실행하지 않음)

```bash
pytest tests/e2e/ --collect-only
```

### 실패한 테스트만 재실행

```bash
pytest tests/e2e/ --lf
```

### Coverage Report 생성

```bash
./run_tests.sh coverage
```

HTML 리포트: `backend/htmlcov/index.html`

### Watch Mode (자동 재실행)

```bash
pip install pytest-watch
pytest-watch tests/e2e/ -c
```

---

## 참고 자료

- **Pytest 공식 문서**: https://docs.pytest.org/
- **pytest-asyncio**: https://github.com/pytest-dev/pytest-asyncio
- **HTTPX**: https://www.python-httpx.org/
- **OmniVibe Pro API 문서**: http://localhost:8000/docs

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro QA Team
