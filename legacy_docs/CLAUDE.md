# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OmniVibe Pro는 **Vibe Coding 방법론** 기반의 AI 옴니채널 영상 자동화 SaaS 플랫폼입니다. 구글 시트 기반 전략 수립부터 AI 에이전트 협업, 음성/영상 생성 및 보정, 다채널 자동 배포까지 전 과정을 자동화합니다.

### Core Philosophy

- **Vibe-Driven**: 사용자 성향(남/여, 부드러움/전문성)을 학습한 페르소나 기반 콘텐츠 생산
- **Agentic Workflow**: 작가/감독/마케터 에이전트의 협업 체계
- **Zero-Fault Audio**: TTS → STT → 검증 → 재생성 루프로 99% 정확도 달성
- **Consistent Persona**: 영상 내 캐릭터 일관성 유지

## Architecture

### Tech Stack

**Backend**
- **FastAPI** (Python 3.11+): AI 파이프라인 및 에이전트 관리
  - LangGraph: 에이전트 상태 관리 및 워크플로우 오케스트레이션
  - Celery + Redis: 비동기 작업 큐 (비디오 렌더링 등)
  - Logfire: 실시간 관측성 및 API 비용 추적 (선택적)

- **Ruby on Rails 8**: 관리자 대시보드 및 비즈니스 로직
  - Hotwire (Turbo + Stimulus): 실시간 UI 업데이트 (WebSocket 대체)
  - SQLite3: 개발 환경 데이터베이스
  - PostgreSQL: 프로덕션 환경 데이터베이스

**Frontend**
- **Next.js 14** (User Studio UI)
  - React 18 + TypeScript
  - Tailwind CSS + Framer Motion
  - SQLite3: 로컬 스크립트/오디오 캐싱
  - Zustand: 상태 관리

- **Rails + Hotwire** (Admin Dashboard)
  - Turbo Frames/Streams: 페이지 새로고침 없는 실시간 UI
  - Stimulus: 가벼운 JavaScript 컨트롤러
  - ViewComponent: 재사용 가능한 컴포넌트

**AI Services**
- ElevenLabs: Professional Voice Cloning
- OpenAI Whisper v3: STT 기반 오디오 검증
- Anthropic Claude: 스크립트 생성 (현재 Haiku 모델 사용)
- Google Veo: 시네마틱 영상 생성
- HeyGen/Wav2Lip: 립싱크

**Data & Memory**
- Google Sheets: 전략 및 스케줄 연동
- Neo4j: GraphRAG 장기 메모리
- Pinecone: 벡터 검색
- Cloudinary: 플랫폼별 미디어 최적화

### Agent Architecture

3개의 전문 에이전트가 협업하는 구조:

1. **The Writer** (`backend/app/services/writer_agent.py`)
   - 구글 시트에서 전략/소재 로드
   - LangGraph 기반 워크플로우
   - Neo4j에서 과거 스크립트 검색
   - Anthropic Claude로 페르소나 기반 스크립트 생성

2. **The Director** (`backend/app/services/director_agent.py`, `audio_director_agent.py`)
   - Zero-Fault Audio Loop: TTS → STT → 원본 대조 → 재생성
   - Google Veo + Nano Banana로 일관된 캐릭터 영상 생성
   - HeyGen/Wav2Lip 립싱크 처리

3. **The Marketer** (향후 구현)
   - 썸네일 자동 생성
   - 카피 문구 추천
   - 다채널 자동 배포

### Key Services

**Audio Pipeline**
- `tts_service.py`: ElevenLabs TTS 생성
- `stt_service.py`: OpenAI Whisper STT 변환
- `audio_correction_loop.py`: Zero-Fault 보정 루프
- `text_normalizer.py`: 메타데이터 제거 (TTS가 "### 훅" 같은 텍스트를 읽지 않도록)

**Content Management**
- `google_sheets_service.py`: 전략/스케줄 동기화
- `duration_calculator.py`: 텍스트 → 예상 오디오 시간 계산
- `duration_learning_system.py`: 실제 TTS 시간 기반 자동 학습

**Video Production**
- `video_renderer.py`: FFmpeg 기반 영상 렌더링
- `lipsync_service.py`: 립싱크 처리
- `subtitle_service.py`: 자막 생성

## Development Commands

### Backend

```bash
# 개발 서버 실행 (포트 8000)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 의존성 설치
poetry install

# 테스트 실행
pytest

# 린팅
ruff check .
black --check .

# 타입 체크
mypy app/
```

### Frontend

```bash
# 개발 서버 실행 (포트 3020)
cd frontend
npm run dev

# 의존성 설치
npm install

# 빌드
npm run build

# 프로덕션 서버
npm start

# 린팅
npm run lint
```

### Full Workflow E2E Test

```bash
# 스크립트 생성 → 오디오 생성 전체 파이프라인 테스트
cd frontend
bash test_full_workflow_e2e.sh
```

## Configuration

### Environment Variables

**Backend** (`backend/.env`):
- `ANTHROPIC_API_KEY`: Claude API 키 (스크립트 생성)
- `OPENAI_API_KEY`: OpenAI API 키 (Whisper STT, DALL-E)
- `ELEVENLABS_API_KEY`: ElevenLabs TTS API 키
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j 연결 정보
- `REDIS_URL`: Redis 연결 (Celery 작업 큐)
- `LOGFIRE_TOKEN`: Logfire 관측성 (선택적)

**Frontend** (`frontend/.env.local`):
- `ANTHROPIC_API_KEY`: Claude API 키 (프론트엔드에서 직접 호출용)

### Known Issues & Workarounds

**transformers UTF-8 인코딩 문제**
- `langchain_anthropic` → `langchain_core` → `transformers` 체인에서 UTF-8 디코딩 실패
- **영향받는 모듈**: Writer Agent, Thumbnail Learner, Continuity Agent, Storyboard Agent, Presentation Agent
- **현재 상태**: 백엔드 API 라우터에서 비활성화됨 (`backend/app/api/v1/__init__.py`)
- **임시 해결책**: Writer Agent는 프론트엔드에서 Anthropic API 직접 호출 (`frontend/app/api/writer-generate/route.ts`)
- **근본 해결**: transformers 라이브러리 재설치 또는 버전 다운그레이드 필요

**Anthropic API 모델 제한**
- 현재 API 키는 `claude-3-haiku-20240307`만 접근 가능
- `claude-3-5-sonnet-20241022`는 "not_found_error" 반환
- 프론트엔드 Writer Generate 라우트에서 Haiku 모델 사용 중

## Frontend Architecture

### Main Pages

- `/` (`frontend/app/page.tsx`): 랜딩 페이지
- `/studio` (`frontend/app/studio/page.tsx`): 메인 워크플로우 UI
  - 클라이언트/캠페인 선택
  - 구글 시트 연동
  - 스크립트 생성 (캐시 지원)
  - 오디오 생성
  - 비디오 렌더링
  - 스토리보드 생성

### API Routes

**스크립트 생성**
- `POST /api/writer-generate`: Anthropic Claude로 스크립트 생성
  - SQLite에 자동 저장/로드 (캐싱)
  - `regenerate: true` 플래그로 강제 재생성

**구글 시트 연동**
- `POST /api/sheets-connect`: 스프레드시트 ID 연결
- `GET /api/sheets-status`: 연결 상태 확인
- `POST /api/sheets-schedule`: 스케줄 데이터 로드

**캠페인/클라이언트**
- `GET /api/campaigns`: 캠페인 목록
- `GET /api/clients`: 클라이언트 목록

### SQLite Caching

프론트엔드는 SQLite3를 사용하여 스크립트/오디오 결과를 로컬 캐싱합니다:

```typescript
// frontend/lib/db/scripts.ts
interface ScriptRecord {
  content_id: number
  campaign_name: string
  topic: string
  platform: string
  script: string
  hook?: string
  body?: string
  cta?: string
  generated_at: string
  metadata?: any
}
```

캐시된 스크립트는 Studio UI에서 "💾 저장된 스크립트 사용" 배지로 표시되며, "🔄 스크립트 재생성" 버튼으로 강제 재생성 가능합니다.

## Backend API Structure

### Main Endpoints

**Voice Cloning**
- `POST /api/v1/voice/clone`: 음성 클로닝
- `GET /api/v1/voice/list/{user_id}`: 커스텀 음성 조회

**Zero-Fault Audio**
- `POST /api/v1/audio/generate`: 오디오 생성 (TTS + STT 검증 루프)
- `GET /api/v1/audio/status/{task_id}`: 작업 상태 조회
- `GET /api/v1/audio/download/{task_id}`: 오디오 다운로드

**Google Sheets**
- `POST /api/v1/sheets/connect`: 스프레드시트 연결
- `GET /api/v1/sheets/strategy`: 전략 시트 읽기
- `GET /api/v1/sheets/schedule`: 스케줄 시트 읽기

**Video Rendering**
- `POST /api/v1/video/render`: 비디오 렌더링
- `GET /api/v1/video/status/{task_id}`: 렌더링 상태

**WebSocket**
- `ws://localhost:8000/api/v1/ws/progress/{task_id}`: 실시간 진행 상황

### Celery Tasks

비동기 작업은 Celery + Redis로 처리:
- `backend/app/tasks/audio_tasks.py`: 오디오 생성 작업
- `backend/app/tasks/presentation_tasks.py`: 프레젠테이션 비디오 생성

## API 호출 패턴

### Writer Agent (프론트엔드에서 직접 호출)

```typescript
const response = await fetch('/api/writer-generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_id: 1001,
    campaign_name: '테스트 캠페인',
    topic: 'AI 음성 합성 기술',
    platform: 'YouTube',
    target_duration: 30,
    regenerate: false // true면 캐시 무시하고 재생성
  })
})
```

### Audio Generation (백엔드 API)

```bash
# 1. 오디오 생성 시작
curl -X POST http://localhost:8000/api/v1/audio/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 오디오 생성 테스트입니다.",
    "voice_id": "rachel",
    "language": "ko",
    "accuracy_threshold": 0.95,
    "max_attempts": 3
  }'

# 2. 상태 확인 (task_id는 응답에서 받음)
curl http://localhost:8000/api/v1/audio/status/{task_id}

# 3. 완료 시 결과 확인
# response.info.result.audio_path
# response.info.result.final_similarity
```

## Code Patterns

### Error Handling

모든 외부 API 호출은 재시도 로직 포함:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_external_api():
    # API 호출
    pass
```

### LangGraph Agent Pattern

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    input: str
    result: str
    error: Optional[str]

workflow = StateGraph(AgentState)
workflow.add_node("process", process_node)
workflow.add_edge("process", END)
workflow.set_entry_point("process")
app = workflow.compile()
```

### Logfire Integration

```python
# Optional: Logfire가 설치되어 있을 때만 사용
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except:
    LOGFIRE_AVAILABLE = False

# 사용 시
span_context = logfire.span("operation") if LOGFIRE_AVAILABLE else nullcontext()
with span_context:
    # 작업 수행
    pass
```

## Ports

- **Backend**: 8000
- **Frontend**: 3020
- **Redis**: 6379 (로컬)
- **Neo4j**: 7687 (볼트 프로토콜)

## Important Notes

1. **transformers 라이브러리 문제로 인해 여러 AI 에이전트가 백엔드에서 비활성화**되어 있습니다. 프론트엔드에서 Anthropic API를 직접 호출하는 방식으로 우회 중입니다.

2. **포트 설정**: 프론트엔드는 3020, 백엔드는 8000 사용. Studio 페이지의 모든 API 호출은 `http://localhost:8000` 사용.

3. **캐싱 전략**: 스크립트 생성 결과는 SQLite에 자동 저장되며, 동일한 `content_id`로 재요청 시 캐시 반환. `regenerate: true` 플래그로 강제 재생성 가능.

4. **Zero-Fault Audio**: 오디오 생성은 비동기 작업으로 처리되며, 정확도가 임계값(기본 0.95)에 도달할 때까지 최대 3회 재시도합니다.

5. **API 키 제한**: 현재 Anthropic API 키는 Claude 3 Haiku 모델만 접근 가능합니다. Sonnet 3.5 사용 시 API 키 업그레이드 필요.
