# 비용 추적 API 문서

OmniVibe Pro의 모든 외부 API 호출 비용을 추적하고 분석하는 API입니다.

## 개요

비용 추적 시스템은 다음 API 제공자의 비용을 자동으로 추적합니다:

- **OpenAI**: GPT-4, Whisper, TTS
- **Anthropic**: Claude (Opus, Sonnet, Haiku)
- **ElevenLabs**: TTS, Voice Cloning
- **Google Veo**: 영상 생성
- **HeyGen**: 립싱크
- **Nano Banana**: 캐릭터 생성
- **Cloudinary**: 미디어 최적화

## API 엔드포인트

### 1. 총 비용 조회

```http
GET /api/v1/costs/total
```

**쿼리 파라미터**:
- `user_id` (선택): 사용자 ID로 필터링
- `project_id` (선택): 프로젝트 ID로 필터링
- `provider` (선택): API 제공자로 필터링 (예: `openai`, `elevenlabs`)
- `start_date` (선택): 시작 날짜 (ISO 8601 형식)
- `end_date` (선택): 종료 날짜 (ISO 8601 형식)

**응답 예시**:
```json
{
  "total_cost": 15.42,
  "record_count": 128,
  "by_provider": {
    "openai": 5.32,
    "elevenlabs": 8.10,
    "google_veo": 2.00
  },
  "query_params": {
    "user_id": "user_abc123",
    "start_date": "2026-01-01T00:00:00",
    "end_date": "2026-02-02T23:59:59"
  }
}
```

**사용 예시**:
```bash
# 전체 비용 조회
curl http://localhost:8000/api/v1/costs/total

# 특정 사용자의 비용 조회
curl "http://localhost:8000/api/v1/costs/total?user_id=user_abc123"

# 최근 7일 비용 조회
curl "http://localhost:8000/api/v1/costs/total?start_date=2026-01-26T00:00:00&end_date=2026-02-02T23:59:59"

# OpenAI API 비용만 조회
curl "http://localhost:8000/api/v1/costs/total?provider=openai"
```

---

### 2. 일별 비용 트렌드

```http
GET /api/v1/costs/trend
```

**쿼리 파라미터**:
- `days` (선택, 기본: 7): 조회할 일수 (1-90일)
- `user_id` (선택): 사용자 ID로 필터링
- `project_id` (선택): 프로젝트 ID로 필터링

**응답 예시**:
```json
[
  {
    "date": "2026-02-02",
    "total_cost": 3.25,
    "by_provider": {
      "openai": 1.15,
      "elevenlabs": 2.10
    }
  },
  {
    "date": "2026-02-01",
    "total_cost": 2.80,
    "by_provider": {
      "openai": 0.90,
      "elevenlabs": 1.90
    }
  }
]
```

**사용 예시**:
```bash
# 최근 7일 트렌드
curl http://localhost:8000/api/v1/costs/trend

# 최근 30일 트렌드
curl "http://localhost:8000/api/v1/costs/trend?days=30"

# 특정 프로젝트의 최근 14일 트렌드
curl "http://localhost:8000/api/v1/costs/trend?days=14&project_id=proj_xyz789"
```

---

### 3. 제공자별 비용 분석

```http
GET /api/v1/costs/by-provider
```

**쿼리 파라미터**:
- `days` (선택, 기본: 30): 조회할 일수 (1-365일)
- `user_id` (선택): 사용자 ID로 필터링
- `project_id` (선택): 프로젝트 ID로 필터링

**응답 예시**:
```json
{
  "total_cost": 45.67,
  "period_days": 30,
  "providers": [
    {
      "provider": "elevenlabs",
      "cost": 18.50,
      "percentage": 40.5
    },
    {
      "provider": "google_veo",
      "cost": 15.00,
      "percentage": 32.8
    },
    {
      "provider": "openai",
      "cost": 12.17,
      "percentage": 26.7
    }
  ]
}
```

**사용 예시**:
```bash
# 최근 30일 제공자별 비용
curl http://localhost:8000/api/v1/costs/by-provider

# 최근 7일 제공자별 비용
curl "http://localhost:8000/api/v1/costs/by-provider?days=7"
```

---

### 4. 프로젝트별 비용 조회

```http
GET /api/v1/costs/by-project/{project_id}
```

**경로 파라미터**:
- `project_id` (필수): 프로젝트 ID

**쿼리 파라미터**:
- `start_date` (선택): 시작 날짜 (ISO 8601 형식)
- `end_date` (선택): 종료 날짜 (ISO 8601 형식)

**응답 예시**:
```json
{
  "project_id": "proj_xyz789",
  "total_cost": 9.33,
  "record_count": 15,
  "by_provider": {
    "google_veo": 6.00,
    "heygen": 3.00,
    "elevenlabs": 0.15,
    "openai": 0.18
  },
  "period": {
    "start_date": null,
    "end_date": null
  }
}
```

**사용 예시**:
```bash
# 프로젝트 전체 비용
curl http://localhost:8000/api/v1/costs/by-project/proj_xyz789

# 특정 기간 프로젝트 비용
curl "http://localhost:8000/api/v1/costs/by-project/proj_xyz789?start_date=2026-02-01T00:00:00"
```

---

### 5. 프로젝트 비용 예상

```http
POST /api/v1/costs/estimate
```

**요청 본문**:
```json
{
  "script_length": 500,
  "video_duration": 60,
  "platform": "YouTube"
}
```

**응답 예시**:
```json
{
  "writer_agent": 0.12,
  "tts": 0.15,
  "stt": 0.01,
  "character": 0.05,
  "video_generation": 6.00,
  "lipsync": 3.00,
  "total": 9.33
}
```

**사용 예시**:
```bash
curl -X POST http://localhost:8000/api/v1/costs/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "script_length": 500,
    "video_duration": 60,
    "platform": "YouTube"
  }'
```

**비용 계산 로직**:

| 단계 | API | 계산 방식 |
|------|-----|----------|
| Writer Agent | Claude Haiku | 글자 수 기반 토큰 계산 |
| TTS | ElevenLabs | $0.30 / 1,000자 |
| STT | Whisper | $0.006 / 분 |
| 캐릭터 생성 | Nano Banana | $0.05 / 이미지 |
| 영상 생성 | Google Veo | $0.10 / 초 |
| 립싱크 | HeyGen | $0.05 / 초 |

---

### 6. CSV 내보내기

```http
GET /api/v1/costs/export
```

**쿼리 파라미터**:
- `user_id` (선택): 사용자 ID로 필터링
- `project_id` (선택): 프로젝트 ID로 필터링
- `provider` (선택): API 제공자로 필터링
- `start_date` (선택): 시작 날짜 (ISO 8601 형식)
- `end_date` (선택): 종료 날짜 (ISO 8601 형식)

**응답**:
- CSV 파일 다운로드

**CSV 포맷**:
```csv
Date,Total Cost (USD),Provider Breakdown
2026-02-02,$3.2500,"openai: $1.1500, elevenlabs: $2.1000"
2026-02-01,$2.8000,"openai: $0.9000, elevenlabs: $1.9000"
```

**사용 예시**:
```bash
# 전체 데이터 내보내기
curl http://localhost:8000/api/v1/costs/export -o costs.csv

# 특정 프로젝트 데이터 내보내기
curl "http://localhost:8000/api/v1/costs/export?project_id=proj_xyz789" -o project_costs.csv

# 최근 30일 데이터 내보내기
curl "http://localhost:8000/api/v1/costs/export?start_date=2026-01-03T00:00:00" -o recent_costs.csv
```

---

### 7. 대시보드 데이터

```http
GET /api/v1/costs/dashboard
```

**쿼리 파라미터**:
- `user_id` (선택): 사용자 ID로 필터링

**응답 예시**:
```json
{
  "total_cost_today": 1.25,
  "total_cost_week": 8.50,
  "total_cost_month": 45.67,
  "daily_trend": [
    {
      "date": "2026-02-02",
      "total_cost": 3.25,
      "by_provider": {
        "openai": 1.15,
        "elevenlabs": 2.10
      }
    }
  ],
  "by_provider": {
    "elevenlabs": 18.50,
    "google_veo": 15.00,
    "openai": 12.17
  },
  "top_projects": []
}
```

**사용 예시**:
```bash
# 전체 대시보드 데이터
curl http://localhost:8000/api/v1/costs/dashboard

# 특정 사용자 대시보드 데이터
curl "http://localhost:8000/api/v1/costs/dashboard?user_id=user_abc123"
```

---

## 가격표 (2026년 2월 기준)

### OpenAI

| 서비스 | 입력 (1K 토큰) | 출력 (1K 토큰) | 기타 |
|--------|----------------|----------------|------|
| GPT-4 | $0.03 | $0.06 | - |
| GPT-4 Turbo | $0.01 | $0.03 | - |
| Whisper | - | - | $0.006 / 분 |
| TTS | - | - | $0.015 / 1K 자 |

### Anthropic

| 서비스 | 입력 (1K 토큰) | 출력 (1K 토큰) |
|--------|----------------|----------------|
| Claude Opus | $0.015 | $0.075 |
| Claude Sonnet | $0.003 | $0.015 |
| Claude Haiku | $0.00025 | $0.00125 |

### ElevenLabs

| 서비스 | 가격 |
|--------|------|
| TTS | $0.30 / 1K 자 |
| Voice Cloning | $10 / 음성 |

### Google Veo

| 서비스 | 가격 |
|--------|------|
| 영상 생성 | $0.10 / 초 |

### HeyGen

| 서비스 | 가격 |
|--------|------|
| 립싱크 | $0.05 / 초 |

### Nano Banana

| 서비스 | 가격 |
|--------|------|
| 캐릭터 생성 | $0.05 / 이미지 |

### Cloudinary

| 서비스 | 가격 |
|--------|------|
| 미디어 변환 | $0.10 / 1K 변환 |

---

## 통합 예시

### 프론트엔드에서 대시보드 구현

```typescript
// 대시보드 데이터 조회
async function loadDashboard(userId: string) {
  const response = await fetch(
    `http://localhost:8000/api/v1/costs/dashboard?user_id=${userId}`
  );
  const data = await response.json();

  // 오늘/이번 주/이번 달 비용 표시
  displayCostSummary({
    today: data.total_cost_today,
    week: data.total_cost_week,
    month: data.total_cost_month
  });

  // 일별 트렌드 차트 그리기
  drawTrendChart(data.daily_trend);

  // 제공자별 비용 파이 차트 그리기
  drawProviderPieChart(data.by_provider);
}

// 프로젝트 생성 전 비용 예상
async function estimateProjectCost(scriptLength: number, videoDuration: number) {
  const response = await fetch('http://localhost:8000/api/v1/costs/estimate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_length: scriptLength,
      video_duration: videoDuration,
      platform: 'YouTube'
    })
  });
  const estimate = await response.json();

  // 예상 비용 표시
  displayEstimate(estimate);

  // 사용자 확인
  if (confirm(`예상 비용: $${estimate.total}. 계속하시겠습니까?`)) {
    createProject();
  }
}
```

---

## 테스트

테스트 스크립트를 사용하여 모든 엔드포인트를 테스트할 수 있습니다:

```bash
cd backend
python3 test_costs_api.py
```

또는 개별 엔드포인트를 테스트:

```bash
# 총 비용 조회
curl http://localhost:8000/api/v1/costs/total

# 일별 트렌드 조회
curl http://localhost:8000/api/v1/costs/trend?days=7

# 비용 예상
curl -X POST http://localhost:8000/api/v1/costs/estimate \
  -H "Content-Type: application/json" \
  -d '{"script_length": 500, "video_duration": 60, "platform": "YouTube"}'
```

---

## 주의사항

1. **날짜 형식**: 모든 날짜는 ISO 8601 형식 (예: `2026-02-02T14:30:00`)을 사용해야 합니다.

2. **Provider 값**: 유효한 provider 값은 다음과 같습니다:
   - `openai`
   - `anthropic`
   - `elevenlabs`
   - `google_veo`
   - `heygen`
   - `nano_banana`
   - `cloudinary`

3. **비용 단위**: 모든 비용은 USD로 표시됩니다.

4. **CSV 내보내기**: 현재는 일별 집계 데이터만 내보냅니다. 개별 레코드 내보내기는 향후 추가 예정입니다.

5. **Top Projects**: 대시보드의 `top_projects` 필드는 향후 구현 예정입니다.

---

## API 스키마

FastAPI는 자동으로 OpenAPI 스키마를 생성합니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 문의

API에 대한 문의사항이나 버그 리포트는 이슈로 등록해주세요.
