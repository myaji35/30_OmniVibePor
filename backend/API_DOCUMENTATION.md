# OmniVibe Pro API Documentation

## Overview

**OmniVibe Pro**는 AI 기반 옴니채널 영상 자동화 SaaS 플랫폼입니다.
구글 시트 기반 전략 수립부터 AI 에이전트 협업, 영상 생성/보정, 다채널 자동 배포까지 전 과정을 자동화합니다.

- **Version**: 1.0.0
- **License**: MIT
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`

---

## Quick Links

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Authentication

현재 API는 인증 없이 사용 가능합니다. 프로덕션 환경에서는 API 키 또는 JWT 토큰 기반 인증이 필요합니다.

### Required Environment Variables

```bash
# ElevenLabs Voice Cloning & TTS
export ELEVENLABS_API_KEY=your_elevenlabs_api_key

# OpenAI Whisper STT & GPT
export OPENAI_API_KEY=your_openai_api_key

# Google Sheets API
export GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials/google-sheets-credentials.json

# Neo4j GraphRAG
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# Pinecone Vector DB (Optional)
export PINECONE_API_KEY=your_pinecone_api_key
export PINECONE_INDEX_NAME=omnivibe-thumbnails

# Redis (Celery)
export REDIS_URL=redis://localhost:6379/0

# Logfire (Optional)
export LOGFIRE_TOKEN=your_logfire_token
```

---

## Core Features

### 1. Voice Cloning
녹음된 목소리를 학습하여 커스텀 TTS를 생성합니다. 사용자만의 목소리로 무제한 컨텐츠를 제작하세요.

### 2. Zero-Fault Audio
ElevenLabs TTS → OpenAI Whisper STT → 검증 → 재생성 루프를 통해 99% 정확도의 오디오를 생성합니다.

### 3. Thumbnail Learning
타인의 고성과 썸네일을 학습하고 자동으로 최적화된 썸네일과 카피를 생성합니다.

### 4. Performance Tracking
멀티 플랫폼 성과 분석 및 자가학습 시스템으로 점점 더 좋은 컨텐츠를 자동 생성합니다.

### 5. AI Agent Orchestration
- **Writer Agent**: 구글 시트 기반 전략 수립 및 스크립트 자동 생성
- **Director Agent**: Zero-Fault Audio 생성 및 검증
- **Continuity Agent**: 콘티 자동 생성 및 리소스 매핑

---

## API Endpoints

### Health & Status

#### `GET /`
Welcome Page & Health Check

**Example Request:**
```bash
curl http://localhost:8000/
```

**Example Response:**
```json
{
  "status": "healthy",
  "service": "OmniVibe Pro",
  "version": "1.0.0",
  "message": "🎬 AI-powered Omnichannel Video Automation",
  "docs": "/docs",
  "redoc": "/redoc",
  "features": {
    "voice_cloning": "✅ Enabled",
    "zero_fault_audio": "✅ Enabled",
    "performance_tracking": "✅ Enabled",
    "thumbnail_learning": "✅ Enabled"
  }
}
```

#### `GET /health`
Detailed Health Check (서비스 연결 상태 확인)

---

## Voice Cloning API

### `POST /api/v1/voice/clone`
음성 클로닝 - 녹음된 오디오로 커스텀 음성 생성

**Request (multipart/form-data):**
- `user_id` (required): 사용자 ID
- `voice_name` (required): 음성 이름 (예: "김대표님")
- `description` (optional): 음성 설명
- `audio_file` (required): 녹음된 오디오 파일 (MP3, WAV, M4A, FLAC, OGG)

**Requirements:**
- 최소 오디오 길이: 1분 이상
- 권장 오디오 길이: 3-5분 (고품질)
- 샘플레이트: 22050 Hz 이상
- 배경 노이즈: 최소화 필요

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/voice/clone" \
  -F "user_id=user123" \
  -F "voice_name=김대표님" \
  -F "description=대표님의 목소리" \
  -F "audio_file=@recording.mp3"
```

**Example Response:**
```json
{
  "voice_id": "V_abc123...",
  "name": "김대표님",
  "status": "ready",
  "message": "Voice '김대표님' cloned successfully! You can now use it for TTS generation."
}
```

---

### `GET /api/v1/voice/list/{user_id}`
사용자의 모든 커스텀 음성 조회

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/voice/list/user123"
```

**Example Response:**
```json
{
  "voices": [
    {
      "voice_id": "V_abc123...",
      "name": "김대표님",
      "description": "대표님의 목소리",
      "category": "cloned",
      "created_at": "2026-02-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /api/v1/voice/info/{voice_id}`
음성 정보 조회

---

### `DELETE /api/v1/voice/{voice_id}`
커스텀 음성 삭제 (ElevenLabs와 Neo4j에서 모두 삭제)

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/voice/V_abc123..."
```

---

### `POST /api/v1/voice/validate`
오디오 파일 검증 (업로드 전 사전 확인용)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/voice/validate" \
  -F "audio_file=@recording.mp3"
```

**Example Response:**
```json
{
  "valid": true,
  "duration_seconds": 185.3,
  "file_size_mb": 3.2,
  "format": "mp3",
  "warnings": [
    "Audio file is small. Recommend 3-5 minutes for best quality."
  ]
}
```

---

## Zero-Fault Audio API

### `POST /api/v1/audio/generate`
Zero-Fault Audio 생성 (비동기 처리)

**워크플로우:**
1. ElevenLabs TTS로 오디오 생성
2. OpenAI Whisper STT로 검증
3. 원본과 비교 (유사도 계산)
4. 정확도 95% 미만이면 재생성 (최대 5회)
5. 검증된 오디오 반환

**Request Body:**
```json
{
  "text": "변환할 텍스트 (최대 5000자)",
  "voice_id": "rachel",
  "language": "ko",
  "user_id": "user123",
  "accuracy_threshold": 0.95,
  "max_attempts": 5
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 오늘은 AI 기술에 대해 이야기해볼게요.",
    "voice_id": "rachel",
    "language": "ko",
    "user_id": "user123",
    "accuracy_threshold": 0.95,
    "max_attempts": 5
  }'
```

**Example Response:**
```json
{
  "status": "processing",
  "task_id": "abc123-def456-ghi789",
  "message": "Zero-Fault Audio 생성 시작. /audio/status/{task_id}로 진행 상황 확인하세요.",
  "text_preview": "안녕하세요, 오늘은 AI 기술에 대해 이야기해볼게요."
}
```

---

### `GET /api/v1/audio/status/{task_id}`
Celery 작업 상태 조회

**상태:**
- `PENDING`: 대기 중
- `STARTED`: 실행 중
- `SUCCESS`: 완료
- `FAILURE`: 실패
- `RETRY`: 재시도 중

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/audio/status/abc123-def456-ghi789"
```

**Example Response (SUCCESS):**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "audio_path": "./generated_audio/verified_audio_abc123.mp3",
    "attempts": 2,
    "final_similarity": 0.97,
    "transcribed_text": "안녕하세요, 오늘은 AI 기술에 대해 이야기해볼게요.",
    "original_text": "안녕하세요, 오늘은 AI 기술에 대해 이야기해볼게요.",
    "normalized_text": "안녕하세요, 오늘은 에이아이 기술에 대해 이야기해볼게요.",
    "normalization_mappings": {
      "AI": "에이아이"
    }
  }
}
```

---

### `GET /api/v1/audio/download/{task_id}`
생성된 오디오 파일 다운로드

**사용법:**
1. `/audio/generate`로 작업 시작
2. `/audio/status/{task_id}`로 완료 확인
3. `/audio/download/{task_id}`로 파일 다운로드

**Example Request:**
```bash
curl -O "http://localhost:8000/api/v1/audio/download/abc123-def456-ghi789"
```

---

### `POST /api/v1/audio/batch-generate`
여러 텍스트 배치 처리 (최대 100개)

**사용 사례:**
- 시리즈 영상의 여러 스크립트 한번에 처리
- 챕터별 오디오 생성

**Request Body:**
```json
{
  "texts": [
    "첫 번째 텍스트",
    "두 번째 텍스트",
    "세 번째 텍스트"
  ],
  "voice_id": "rachel",
  "language": "ko",
  "user_id": "user123"
}
```

---

### `POST /api/v1/audio/normalize-text`
한국어 텍스트 정규화 (숫자 → 한글)

**변환 규칙:**
- 연도: 2024년 → 이천이십사년
- 날짜: 1월 15일 → 일월 십오일
- 금액: 2,000원 → 이천원
- 개수: 3개 → 세개
- 나이: 25살 → 스물다섯살
- 시간: 2시 30분 → 두시 삼십분
- 전화번호: 010-1234-5678 → 공일공 일이삼사 오육칠팔
- 퍼센트: 95.5% → 구십오점오퍼센트

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/audio/normalize-text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다."
  }'
```

**Example Response:**
```json
{
  "original": "2024년 1월 15일, 사과 3개를 2,000원에 샀습니다.",
  "normalized": "이천이십사년 일월 십오일, 사과 세개를 이천원에 샀습니다.",
  "mappings": {
    "2024년": "이천이십사년",
    "1월": "일월",
    "15일": "십오일",
    "3개": "세개",
    "2,000원": "이천원"
  }
}
```

---

### `GET /api/v1/audio/voices`
사용 가능한 음성 목록 (ElevenLabs 기본 음성)

---

### `GET /api/v1/audio/usage`
ElevenLabs API 사용량 조회 (총 생성 문자 수, 예상 비용)

---

## Google Sheets API

### `GET /api/v1/sheets/status`
Google Sheets API 연결 상태 확인

---

### `POST /api/v1/sheets/connect`
구글 시트 연결 테스트

**Request Body:**
```json
{
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "sheet_name": "전략"
}
```

**Example Response:**
```json
{
  "success": true,
  "spreadsheet_id": "1abc123...",
  "title": "OmniVibe Pro 전략",
  "message": "Successfully connected to Google Sheets"
}
```

---

### `GET /api/v1/sheets/saved-sheets`
Neo4j에 저장된 구글 시트 목록 조회

---

### `POST /api/v1/sheets/read`
시트 데이터 읽기

**Request Body:**
```json
{
  "spreadsheet_id": "1abc123...",
  "range_name": "Sheet1!A1:D10"
}
```

---

### `POST /api/v1/sheets/write`
시트 데이터 쓰기

---

### `GET /api/v1/sheets/strategy/{spreadsheet_id}`
전략 시트 읽기

**전략 시트 구조:**
```
| 항목 | 내용 |
|------|------|
| 캠페인명 | AI 자동화 시리즈 |
| 타겟 | 스타트업 대표, 마케터 |
| 톤앤매너 | 전문적이면서 친근한 |
```

---

### `GET /api/v1/sheets/schedule/{spreadsheet_id}`
콘텐츠 스케줄 시트 읽기

**스케줄 시트 구조:**
```
| 날짜 | 주제 | 플랫폼 | 상태 |
|------|------|--------|------|
| 2024-01-15 | AI 소개편 | YouTube | 대기 |
```

---

### `GET /api/v1/sheets/campaign/{spreadsheet_id}/{campaign_name}`
특정 캠페인의 콘텐츠(소제목) 목록 조회

---

### `POST /api/v1/sheets/update-status`
콘텐츠 상태 업데이트

---

### `GET /api/v1/sheets/resources/{spreadsheet_id}`
리소스 시트 읽기

**리소스 시트 구조:**
```
| 캠페인명 | 소제목 | 리소스명 | 리소스타입 | URL/경로 | 용도 | 업로드일 |
|---------|--------|----------|------------|----------|------|----------|
| AI자동화 | 소개편 | logo.png | image | gs://... | 인트로 | 2026-01-01 |
```

---

### `POST /api/v1/sheets/resources/add`
리소스 시트에 새 리소스 추가

---

## Writer Agent API

### `POST /api/v1/writer/generate`
스크립트 자동 생성

**LangGraph 기반 Writer 에이전트가:**
1. 구글 시트에서 전략 로드
2. Neo4j에서 과거 스크립트 검색
3. Claude (Anthropic)로 고품질 스크립트 초안 생성
4. 플랫폼별 최적화
5. Neo4j에 저장

**Request Body:**
```json
{
  "spreadsheet_id": "1abc123...",
  "campaign_name": "AI 자동화 시리즈",
  "topic": "소개편",
  "platform": "YouTube"
}
```

**Example Response:**
```json
{
  "success": true,
  "campaign_name": "AI 자동화 시리즈",
  "topic": "소개편",
  "platform": "YouTube",
  "script": "안녕하세요, 여러분...",
  "hook": "3초 안에 여러분의 주목을 끌 수 있는 한 마디...",
  "cta": "지금 바로 구독 버튼을 눌러주세요!",
  "estimated_duration": 180,
  "target_audience": "스타트업 대표, 마케터",
  "tone": "전문적이면서 친근한",
  "created_at": "2026-02-01T12:00:00Z"
}
```

---

### `GET /api/v1/writer/health`
Writer 에이전트 상태 확인

---

## Director Agent API

### `POST /api/v1/director/generate-audio`
오디오 생성 및 검증 (Zero-Fault Loop)

**LangGraph 기반 Director 에이전트가:**
1. TTS 생성 (ElevenLabs)
2. STT 검증 (OpenAI Whisper)
3. 유사도 계산
4. 95% 이상 정확도 달성까지 반복 (최대 5회)
5. Neo4j에 저장

**Request Body:**
```json
{
  "script": "안녕하세요, 여러분...",
  "campaign_name": "AI 자동화 시리즈",
  "topic": "소개편",
  "voice_id": "V_abc123...",
  "language": "ko",
  "accuracy_threshold": 0.95,
  "max_attempts": 5
}
```

---

### `GET /api/v1/director/download-audio/{filename}`
생성된 오디오 파일 다운로드

---

### `GET /api/v1/director/health`
Director 에이전트 상태 확인

---

## Continuity Agent API

### `POST /api/v1/continuity/generate`
콘티 자동 생성

**LangGraph 기반 Continuity Agent가:**
1. 스크립트를 씬으로 자동 분할
2. 각 씬의 카메라 워크 제안
3. 리소스 자동 매핑
4. Neo4j에 저장

**Request Body:**
```json
{
  "script": "안녕하세요, 여러분...",
  "campaign_name": "AI 자동화 시리즈",
  "topic": "소개편",
  "platform": "YouTube",
  "mode": "auto",
  "spreadsheet_id": "1abc123...",
  "resource_urls": []
}
```

**Example Response:**
```json
{
  "success": true,
  "campaign_name": "AI 자동화 시리즈",
  "topic": "소개편",
  "platform": "YouTube",
  "total_duration": 180.5,
  "scene_count": 10,
  "scenes": [
    {
      "scene_number": 1,
      "start_time": 0.0,
      "end_time": 15.0,
      "duration": 15.0,
      "script_text": "안녕하세요, 여러분...",
      "camera_work": "Close-up, 정면",
      "resource_ids": ["res_123", "res_456"],
      "bgm_file": "intro_music.mp3",
      "sfx_file": null,
      "metadata": {}
    }
  ],
  "created_at": "2026-02-01T12:00:00Z"
}
```

---

### `POST /api/v1/continuity/upload-resource`
리소스 업로드 (이미지, PDF, 영상)

**Request (multipart/form-data):**
- `file` (required): 업로드할 파일
- `campaign_name` (optional): 캠페인명

---

### `POST /api/v1/continuity/convert-pdf`
PDF → 이미지 변환 (페이지별 이미지로 변환)

---

### `GET /api/v1/continuity/health`
Continuity Agent 상태 확인

---

## Thumbnail Learning API

### `POST /api/v1/thumbnails/learn`
유튜브 고성과 영상의 썸네일 + 타이틀 패턴 학습

**Request Body:**
```json
{
  "query": "AI 트렌드 2026",
  "min_views": 100000,
  "max_results": 50
}
```

**Note:** Pinecone 초기화 후 사용 가능

---

### `POST /api/v1/thumbnails/generate`
학습된 패턴 기반 썸네일 + 카피 생성

---

### `GET /api/v1/thumbnails/search`
텍스트 기반 유사 고성과 썸네일 검색

---

## Performance Tracking API

### `POST /api/v1/performance/track`
멀티 플랫폼 컨텐츠 성과 추적 및 자가학습

**조회수 + 좋아요 + 댓글**을 종합 분석하여 다음 썸네일 제작에 반영

**Request Body:**
```json
{
  "user_id": "user123",
  "youtube_channel_id": "UCabc123...",
  "facebook_page_id": "fb_page_123",
  "instagram_account_id": "ig_account_123",
  "days_back": 30
}
```

---

### `POST /api/v1/performance/generate-learned`
자가학습 기반 썸네일 + 카피 생성

**학습 우선순위:**
1. 자신의 고성과 컨텐츠 (70점 이상)
2. 타인의 고성과 컨텐츠 (10만 조회수 이상)
3. 자신의 중성과 컨텐츠 (40-70점)

---

### `GET /api/v1/performance/insights/{user_id}`
사용자의 컨텐츠 성과 인사이트 조회

**Returns:**
- 플랫폼별 평균 성과
- 고성과/중성과/저성과 컨텐츠 비율
- 최고 성과 컨텐츠
- 개선이 필요한 영역

---

### `POST /api/v1/performance/visualize-embeddings`
TensorFlow Embedding Projector로 썸네일 임베딩 시각화

**시각화 내용:**
- 고성과 vs 저성과 썸네일 클러스터
- 자신의 컨텐츠 vs 타인의 컨텐츠 분포
- 플랫폼별 (YouTube, Facebook, Instagram) 패턴
- t-SNE, PCA, UMAP 차원 축소

**사용 방법:**
1. 이 API 호출하여 TSV 파일 생성
2. TensorBoard 실행: `tensorboard --logdir=./embeddings_viz`
3. 브라우저에서 http://localhost:6006 접속

---

### `GET /api/v1/performance/download-visualization`
임베딩 시각화 HTML 파일 다운로드

---

## Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | Bad Request | 잘못된 요청 (필수 파라미터 누락, 잘못된 형식 등) |
| 401 | Unauthorized | 인증 실패 (API 키 누락/만료) |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 500 | Internal Server Error | 서버 내부 오류 |
| 503 | Service Unavailable | 서비스 사용 불가 (외부 API 연결 실패 등) |

---

## Rate Limits

현재 Rate Limit은 설정되지 않았습니다. 프로덕션 환경에서는 다음과 같은 제한이 적용될 예정입니다:

- **Voice Cloning**: 시간당 10회
- **Audio Generation**: 분당 100회
- **Google Sheets API**: 분당 60회

---

## Webhooks (Coming Soon)

비동기 작업 완료 시 웹훅으로 알림을 받을 수 있습니다.

**지원 예정 이벤트:**
- `audio.generation.completed`
- `script.generation.completed`
- `continuity.generation.completed`
- `performance.analysis.completed`

---

## Best Practices

### 1. 텍스트 정규화
TTS 생성 전에 반드시 `/api/v1/audio/normalize-text` 엔드포인트를 사용하여 숫자를 한글로 변환하세요.

### 2. 작업 상태 폴링
비동기 작업 (`/audio/generate`, `/audio/batch-generate` 등)의 경우, 상태를 주기적으로 확인하세요 (2-5초 간격 권장).

### 3. 오디오 파일 검증
음성 클로닝 전에 `/api/v1/voice/validate` 엔드포인트로 오디오 파일을 미리 검증하세요.

### 4. 구글 시트 연결
처음 사용 시 `/api/v1/sheets/connect` 엔드포인트로 연결 테스트를 수행하세요.

### 5. 에러 처리
모든 API 호출에서 에러 응답을 처리하고, 필요시 재시도 로직을 구현하세요.

---

## Support

- **Email**: support@omnivibepro.com
- **GitHub Issues**: https://github.com/omnivibe-pro/issues
- **Documentation**: [https://docs.omnivibepro.com](https://docs.omnivibepro.com)

---

## Changelog

### Version 1.0.0 (2026-02-01)
- Initial release
- Voice Cloning API
- Zero-Fault Audio API
- Google Sheets Integration
- Writer, Director, Continuity Agents
- Thumbnail Learning & Performance Tracking (Experimental)

---

**License**: MIT | **Status**: Production Ready ✅
