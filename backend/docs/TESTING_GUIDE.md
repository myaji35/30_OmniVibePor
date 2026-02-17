# OmniVibe Pro Testing Guide

> **완전한 품질 보증을 위한 테스트 전략**

---

## 📋 목차

1. [테스트 개요](#테스트-개요)
2. [테스트 환경 설정](#테스트-환경-설정)
3. [Unit 테스트](#unit-테스트)
4. [Integration 테스트](#integration-테스트)
5. [E2E 테스트](#e2e-테스트)
6. [성능 테스트](#성능-테스트)
7. [보안 테스트](#보안-테스트)
8. [CI/CD 통합](#cicd-통합)

---

## 테스트 개요

### 테스트 피라미드

```
        E2E Tests (5%)
      ─────────────────
     Integration Tests (15%)
   ─────────────────────────────
  Unit Tests (80%)
─────────────────────────────────────
```

### 테스트 커버리지 목표

- **전체 커버리지**: 70% 이상
- **핵심 비즈니스 로직**: 90% 이상
- **API 엔드포인트**: 100%

---

## 테스트 환경 설정

### 1. 의존성 설치

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

### 2. 환경 변수 설정

```bash
# .env.test 파일 생성
TESTING=true
DATABASE_URL=sqlite:///test_omni_db.sqlite

# Mock API 키
ELEVENLABS_API_KEY=test_key
OPENAI_API_KEY=test_key
ANTHROPIC_API_KEY=test_key
STRIPE_SECRET_KEY=sk_test_mock
```

### 3. 테스트 DB 초기화

```bash
python -c "from app.db.sqlite_client import init_db; init_db('test_omni_db.sqlite')"
```

---

## Unit 테스트

### 실행 방법

```bash
# 전체 Unit 테스트
pytest tests/unit/ -v

# 특정 파일
pytest tests/unit/test_writer_agent.py -v

# 커버리지 포함
pytest tests/unit/ -v --cov=app --cov-report=html
```

### 작성된 Unit 테스트

#### 1. Writer Agent (`test_writer_agent.py`)

- **TestScriptNormalization**: 스크립트 정규화
  - Markdown 헤더 제거
  - 괄호 주석 제거
  - 특수문자 제거
  - 연속 공백 제거

- **TestDurationCalculation**: 스크립트 길이 계산
  - 한국어 짧은/긴 텍스트
  - 영어 텍스트
  - 빈 텍스트

- **TestKeywordExtraction**: 키워드 추출
  - 한국어/영어 키워드
  - 불용어 필터링

- **TestScriptBlockSplitting**: 스크립트 블록 분할
  - 문단별 분할
  - 시간별 분할
  - 블록 메타데이터 생성

#### 2. Audio Correction Loop (`test_audio_correction.py`)

- **TestAudioCorrectionLoop**: Zero-Fault 오디오 시스템
  - 유사도 계산 (완전 일치, 미세한 차이, 큰 차이)
  - 재시도 로직
  - TTS/STT 통합

---

## Integration 테스트

### 실행 방법

```bash
# Integration 테스트
pytest tests/integration/ -v -m integration

# 특정 시나리오
pytest tests/integration/test_audio_pipeline.py -v
```

### 주요 Integration 테스트

#### 1. Audio Pipeline (`test_audio_pipeline.py`)

```python
@pytest.mark.asyncio
async def test_zero_fault_loop():
    """Zero-Fault 오디오 생성 전체 플로우"""
    text = "안녕하세요, 테스트입니다."
    voice_id = "V_test_voice"

    result = await zero_fault_audio_generation(
        text=text,
        voice_id=voice_id,
        max_retries=3
    )

    assert result["accuracy"] >= 95.0
    assert result["audio_url"].startswith("http")
    assert result["retries"] <= 3
```

#### 2. Writer + Director Workflow

```python
async def test_script_to_storyboard():
    """스크립트 생성 → 콘티 생성"""
    # 1. Writer Agent로 스크립트 생성
    script = await writer_agent.generate(...)

    # 2. Director Agent로 콘티 생성
    storyboard = await director_agent.analyze(script)

    assert len(storyboard.blocks) > 0
```

---

## E2E 테스트

### 실행 방법

```bash
# E2E 테스트 (시간 소요)
pytest tests/e2e/ -v -m e2e

# 특정 워크플로우
pytest tests/e2e/test_full_workflow.py::TestFullWorkflow::test_01_create_campaign -v
```

### E2E 테스트 시나리오

#### 1. Full Video Creation Workflow (`test_full_workflow.py`)

```
1. Health Check
2. Create Campaign
3. Generate Script (Writer Agent)
4. Create Content
5. Generate Storyboard (Director Agent)
6. Generate Audio (Zero-Fault Loop)
7. Poll Audio Status
8. List Campaigns
9. Get Campaign Contents
```

#### 2. Authentication Flow

```
1. Register (회원가입)
2. Login (로그인)
3. Get Current User (사용자 정보 조회)
4. Refresh Token (토큰 갱신)
5. Invalid Token (유효하지 않은 토큰)
```

#### 3. Stripe Payment Flow

```
1. Get Pricing Plans
2. Create Subscription
3. Get Current Subscription
4. Cancel Subscription
```

#### 4. Quota Management

```
1. Check Quota (정상)
2. Check Quota (초과)
```

---

## 성능 테스트

### Locust 설정 (추후 작성)

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class OmniVibeUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def generate_script(self):
        self.client.post("/api/v1/writer/generate", json={
            "campaign_name": "Test",
            "topic": "AI Video",
            "platform": "YouTube",
            "target_duration": 100
        })

    @task(1)
    def list_campaigns(self):
        self.client.get("/api/v1/campaigns")
```

**실행**:
```bash
locust -f tests/performance/locustfile.py --host http://localhost:8000
```

---

## 보안 테스트

### 1. Bandit (Python 보안 스캔)

```bash
pip install bandit
bandit -r app/ -ll
```

### 2. Safety (의존성 취약점)

```bash
pip install safety
safety check --full-report
```

### 3. OWASP Top 10 체크리스트

- [ ] SQL Injection (SQLAlchemy ORM 사용)
- [ ] XSS (Pydantic 검증)
- [ ] CSRF (FastAPI CORS 설정)
- [ ] 인증/인가 (JWT + OAuth 2.0)
- [ ] 민감한 데이터 노출 (.env 파일 암호화)
- [ ] API Rate Limiting (slowapi)
- [ ] Input Validation (모든 엔드포인트)
- [ ] HTTPS 강제 (프로덕션)

---

## CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run Unit Tests
      run: pytest tests/unit/ -v --cov=app --cov-report=xml

    - name: Run Integration Tests
      run: pytest tests/integration/ -v

    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 테스트 Best Practices

### 1. 테스트 격리

```python
@pytest.fixture(scope="function")
def db_session():
    """각 테스트마다 독립적인 DB 세션"""
    session = Session()
    yield session
    session.rollback()
    session.close()
```

### 2. Mock 사용

```python
from unittest.mock import patch

@patch("app.services.tts_service.elevenlabs_client")
def test_tts_generation(mock_elevenlabs):
    """실제 API 호출 없이 TTS 테스트"""
    mock_elevenlabs.generate.return_value = b"fake_audio_data"
    result = generate_audio("테스트")
    assert result is not None
```

### 3. Parametrize로 여러 케이스 테스트

```python
@pytest.mark.parametrize("text,expected_duration", [
    ("짧은 텍스트", 3),
    ("좀 더 긴 텍스트입니다", 5),
    ("이것은 매우 긴 텍스트로 10초 이상 걸립니다", 12)
])
def test_duration_calculation(text, expected_duration):
    duration = calculate_duration(text)
    assert abs(duration - expected_duration) < 2
```

---

## 테스트 실행 요약

```bash
# 전체 테스트 (빠른 체크)
pytest tests/ -v --tb=short -m "not slow"

# 전체 테스트 (전체)
pytest tests/ -v --cov=app --cov-report=html

# 특정 카테고리만
pytest tests/unit/ -v            # Unit만
pytest tests/integration/ -v     # Integration만
pytest tests/e2e/ -v             # E2E만
```

**커버리지 리포트**: `htmlcov/index.html` 열어보기

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro DevOps Team
