# Logfire 관찰성 및 모니터링 설정

> **Pydantic Logfire**를 활용한 FastAPI 애플리케이션 관찰성 구축

## 📋 목차

1. [Logfire란?](#logfire란)
2. [설치 및 설정](#설치-및-설정)
3. [FastAPI 통합](#fastapi-통합)
4. [Celery 추적](#celery-추적)
5. [커스텀 추적](#커스텀-추적)
6. [대시보드 구성](#대시보드-구성)
7. [알림 설정](#알림-설정)

---

## Logfire란?

**Pydantic Logfire**는 FastAPI 애플리케이션을 위한 관찰성 플랫폼입니다.

### 주요 기능

- ✅ **자동 계측**: FastAPI 앱 자동 추적
- ✅ **SQL 쿼리 추적**: Database 쿼리 성능 모니터링
- ✅ **OpenTelemetry 호환**: 표준 프로토콜
- ✅ **실시간 대시보드**: 성능 메트릭 시각화
- ✅ **에러 추적**: 예외 자동 캡처

---

## 설치 및 설정

### 1. Logfire 설치

```bash
pip install logfire
```

### 2. Logfire 계정 생성

https://logfire.pydantic.dev 에서 계정 생성

### 3. 프로젝트 초기화

```bash
logfire auth
logfire init
```

토큰이 `.env`에 자동 저장됩니다:

```bash
LOGFIRE_TOKEN=your_token_here
```

---

## FastAPI 통합

### app/main.py 수정

```python
"""FastAPI 메인 애플리케이션"""
import logfire
from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

# Logfire 초기화
logfire.configure(token=settings.LOGFIRE_TOKEN)

app = FastAPI(title="OmniVibe Pro API")

# FastAPI 자동 계측
logfire.instrument_fastapi(app)

@app.get("/")
async def root():
    """Health check"""
    with logfire.span("root_endpoint"):  # 커스텀 스팬
        return {"status": "healthy"}
```

### 자동으로 추적되는 항목

- ✅ HTTP 요청/응답
- ✅ 응답 시간
- ✅ 에러 및 예외
- ✅ 헤더 및 바디 (선택적)

---

## Celery 추적

### app/tasks/celery_app.py 수정

```python
"""Celery 앱 with Logfire"""
import logfire
from celery import Celery

celery_app = Celery("omnivibe")

# Celery 계측
logfire.instrument_celery(celery_app)

@celery_app.task(name="example_task")
def example_task(arg):
    with logfire.span("task_processing"):
        # Task 로직
        return result
```

---

## 커스텀 추적

### API 엔드포인트에서 커스텀 스팬

```python
from fastapi import APIRouter
import logfire

router = APIRouter()

@router.post("/audio/generate")
async def generate_audio(request: AudioRequest):
    with logfire.span("audio_generation") as span:
        # 메타데이터 추가
        span.set_attribute("text_length", len(request.text))
        span.set_attribute("voice_id", request.voice_id)

        # Zero-Fault Loop 추적
        with logfire.span("tts_generation"):
            audio = await tts_service.generate(request.text)

        with logfire.span("stt_validation"):
            transcript = await stt_service.transcribe(audio)

        accuracy = calculate_similarity(request.text, transcript)
        span.set_attribute("accuracy", accuracy)

        return {"audio_url": audio_url, "accuracy": accuracy}
```

### 에러 추적

```python
try:
    result = risky_operation()
except Exception as e:
    logfire.error(
        "Operation failed",
        error=str(e),
        user_id=user_id,
        operation="risky_operation"
    )
    raise
```

---

## 대시보드 구성

### 1. 대시보드 접속

https://logfire.pydantic.dev 로그인

### 2. 주요 메트릭

#### API 성능
- **P50/P90/P99 Latency**: 응답 시간 분포
- **Requests Per Second**: 초당 요청 수
- **Error Rate**: 에러 발생률

#### Celery 성능
- **Task Throughput**: 작업 처리량
- **Task Duration**: 작업 실행 시간
- **Queue Length**: 대기 중인 작업 수

#### Database 성능
- **Query Time**: SQL 쿼리 실행 시간
- **Slow Queries**: 느린 쿼리 추적 (> 1초)

---

## 알림 설정

### Slack 알림

1. Logfire 대시보드 → **Alerts** → **New Alert**
2. 조건 설정:
   - **Metric**: Error Rate
   - **Threshold**: > 5%
   - **Duration**: 5분 이상
3. **Notification**: Slack Webhook URL 입력

### 이메일 알림

1. **Alerts** → **Email Notifications**
2. 알림 받을 이메일 주소 입력

---

## 비용 추적

Logfire로 AI API 비용 모니터링:

```python
@router.post("/writer/generate")
async def generate_script(request: WriterRequest):
    with logfire.span("writer_agent") as span:
        # Claude API 호출
        response = await claude.generate(request.topic)

        # 토큰 사용량 기록
        span.set_attribute("prompt_tokens", response.usage.prompt_tokens)
        span.set_attribute("completion_tokens", response.usage.completion_tokens)

        # 비용 계산 (Claude Haiku: $0.25/1M input, $1.25/1M output)
        cost = (
            (response.usage.prompt_tokens / 1_000_000) * 0.25 +
            (response.usage.completion_tokens / 1_000_000) * 1.25
        )
        span.set_attribute("cost_usd", round(cost, 4))

        return {"script": response.content, "cost": cost}
```

대시보드에서 `cost_usd` 메트릭을 합산하여 일일/월간 비용 추적 가능.

---

## 성능 최적화 팁

### 1. 샘플링 비율 조정

```python
# 프로덕션에서는 10%만 추적 (비용 절감)
logfire.configure(
    token=settings.LOGFIRE_TOKEN,
    sampling_ratio=0.1 if not settings.DEBUG else 1.0
)
```

### 2. 민감 데이터 제외

```python
logfire.instrument_fastapi(
    app,
    excluded_urls=["/health"],  # Health check 제외
    capture_headers=False,  # 헤더 캡처 비활성화
    capture_request_body=False,  # 요청 바디 캡처 비활성화
)
```

### 3. 배치 전송

```python
logfire.configure(
    token=settings.LOGFIRE_TOKEN,
    batch_span_processor=True,  # 배치로 전송 (성능 향상)
)
```

---

## 트러블슈팅

### 문제 1: 로그가 표시되지 않음

**해결**:
```bash
# 토큰 확인
echo $LOGFIRE_TOKEN

# 네트워크 연결 확인
curl https://logfire-api.pydantic.dev/health

# 로그 레벨 확인
logfire.configure(token=..., send_to_logfire=True, console=True)
```

### 문제 2: 과도한 비용

**해결**:
- 샘플링 비율 낮추기 (`sampling_ratio=0.1`)
- Health check 엔드포인트 제외
- 프로덕션에서만 활성화

---

## 참고 자료

- **Logfire 공식 문서**: https://docs.pydantic.dev/logfire/
- **FastAPI 통합 가이드**: https://docs.pydantic.dev/logfire/integrations/fastapi/
- **Celery 통합**: https://docs.pydantic.dev/logfire/integrations/celery/

---

**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro DevOps Team
