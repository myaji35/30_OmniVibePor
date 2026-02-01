# OmniVibe Pro - RAL Plan (Rapid Action Launch Plan)
## Ultra Work 모드 빌드 실행 계획서

**작성일**: 2026-02-01
**목표**: PoC → Alpha → Beta → Launch 단계별 완성
**예상 기간**: 8-12주

---

## Phase 0: 프로젝트 초기화 (Week 1)

### 0.1 프로젝트 구조 설계
```
omnivibe-pro/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph 에이전트 (Writer, Director, Marketer)
│   │   ├── services/        # 외부 API 연동 (ElevenLabs, Whisper, Veo 등)
│   │   ├── core/            # 설정, 로깅, 의존성
│   │   ├── api/             # FastAPI 라우터
│   │   ├── models/          # Pydantic 모델
│   │   ├── tasks/           # Celery 작업
│   │   └── utils/           # 헬퍼 함수
│   ├── tests/
│   ├── pyproject.toml       # Poetry 설정
│   ├── .env.example
│   └── docker-compose.yml
├── frontend/                # Next.js 대시보드 (Beta 단계)
├── docs/
│   ├── api/                 # API 문서
│   └── architecture/        # 아키텍처 다이어그램
├── prd.md
├── CLAUDE.md
└── RALPLAN.md
```

### 0.2 핵심 의존성 정의 (pyproject.toml)
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
langgraph = "^0.0.26"
celery = {extras = ["redis"], version = "^5.3.6"}
redis = "^5.0.1"
logfire = "^0.2.0"
openai = "^1.12.0"              # Whisper API
elevenlabs = "^0.2.26"
pinecone-client = "^3.0.0"
neo4j = "^5.16.0"
google-api-python-client = "^2.115.0"  # Google Sheets
cloudinary = "^1.38.0"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
tenacity = "^8.2.3"             # 재시도 로직
httpx = "^0.26.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
black = "^24.1.1"
ruff = "^0.1.14"
```

### 0.3 환경 변수 템플릿 (.env.example)
```env
# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Logfire
LOGFIRE_TOKEN=your_logfire_token

# AI Services
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
GOOGLE_VEO_API_KEY=...

# Memory Systems
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...

# Google Services
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json

# Media
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# HeyGen (Optional)
HEYGEN_API_KEY=...
```

---

## Phase 1: PoC - Zero-Fault Audio Pipeline (Week 2-3)

### 목표
ElevenLabs TTS → Whisper STT → 검증 → 재생성 루프 구현

### 1.1 ElevenLabs TTS 서비스
**파일**: `backend/app/services/tts_service.py`

```python
from elevenlabs import VoiceSettings, generate, set_api_key
from tenacity import retry, stop_after_attempt, wait_exponential
import logfire

class TTSService:
    def __init__(self, api_key: str):
        set_api_key(api_key)
        self.logger = logfire.get_logger(__name__)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_audio(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        model: str = "eleven_multilingual_v2"
    ) -> bytes:
        """TTS 생성 + Logfire 비용 추적"""
        with self.logger.span("elevenlabs.generate"):
            audio = generate(
                text=text,
                voice=voice_id,
                model=model,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            # 비용 추적 로직
            self.logger.info(f"Generated {len(text)} chars")
            return audio
```

### 1.2 Whisper STT 서비스
**파일**: `backend/app/services/stt_service.py`

```python
from openai import OpenAI
import tempfile
import logfire

class STTService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logfire.get_logger(__name__)

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Whisper v3로 STT 변환"""
        with self.logger.span("whisper.transcribe"):
            with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                f.write(audio_bytes)
                f.flush()

                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="ko"  # 또는 사용자 설정에 따라 동적
                )
                return transcript.text
```

### 1.3 Zero-Fault Audio Loop
**파일**: `backend/app/services/audio_loop.py`

```python
from difflib import SequenceMatcher
import logfire

class AudioCorrectionLoop:
    def __init__(self, tts: TTSService, stt: STTService):
        self.tts = tts
        self.stt = stt
        self.logger = logfire.get_logger(__name__)
        self.accuracy_threshold = 0.95
        self.max_attempts = 5

    def calculate_similarity(self, original: str, transcribed: str) -> float:
        """문자열 유사도 계산"""
        return SequenceMatcher(None, original.lower(), transcribed.lower()).ratio()

    async def generate_verified_audio(self, text: str, voice_id: str) -> bytes:
        """검증된 오디오 생성 (최대 5회 시도)"""
        for attempt in range(1, self.max_attempts + 1):
            with self.logger.span(f"audio_loop.attempt_{attempt}"):
                # 1. TTS 생성
                audio = await self.tts.generate_audio(text, voice_id)

                # 2. STT 검증
                transcribed = await self.stt.transcribe(audio)

                # 3. 유사도 계산
                similarity = self.calculate_similarity(text, transcribed)
                self.logger.info(f"Attempt {attempt}: similarity={similarity:.2%}")

                # 4. 임계값 체크
                if similarity >= self.accuracy_threshold:
                    self.logger.info(f"✓ Audio verified at attempt {attempt}")
                    return audio

                # 5. 발음 오류 분석 (옵션)
                self.logger.warning(f"✗ Mismatch: '{text}' != '{transcribed}'")

        # 최대 시도 후에도 실패 시 경고와 함께 마지막 오디오 반환
        self.logger.error(f"Failed to achieve {self.accuracy_threshold:.0%} accuracy")
        return audio
```

### 1.4 Celery 작업 정의
**파일**: `backend/app/tasks/audio_tasks.py`

```python
from celery import Celery
from app.services.audio_loop import AudioCorrectionLoop
from app.core.config import settings

celery_app = Celery("omnivibe", broker=settings.CELERY_BROKER_URL)

@celery_app.task(name="generate_verified_audio")
def generate_verified_audio_task(text: str, voice_id: str, user_id: str):
    """비동기 오디오 생성 작업"""
    loop = AudioCorrectionLoop(tts_service, stt_service)
    audio_bytes = loop.generate_verified_audio(text, voice_id)

    # S3 또는 로컬 저장
    file_path = f"./outputs/{user_id}/audio_{hash(text)}.mp3"
    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    return {"status": "completed", "file_path": file_path}
```

### 1.5 FastAPI 엔드포인트
**파일**: `backend/app/api/v1/audio.py`

```python
from fastapi import APIRouter, BackgroundTasks
from app.tasks.audio_tasks import generate_verified_audio_task

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/generate")
async def generate_audio(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    user_id: str = "default"
):
    """TTS 생성 + STT 검증"""
    task = generate_verified_audio_task.delay(text, voice_id, user_id)
    return {"task_id": task.id, "status": "processing"}

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Celery 작업 상태 조회"""
    from app.tasks.audio_tasks import celery_app
    task = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.status, "result": task.result}
```

---

## Phase 2: Alpha - LangGraph Agents (Week 4-6)

### 2.1 LangGraph 에이전트 상태 정의
**파일**: `backend/app/agents/state.py`

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_script: str
    persona: dict  # {"gender": "female", "tone": "professional", "style": "교육"}
    audio_files: list[str]
    video_files: list[str]
    platform: str  # "youtube" | "instagram" | "facebook"
    status: str
```

### 2.2 Writer 에이전트
**파일**: `backend/app/agents/writer.py`

```python
from langgraph.graph import StateGraph, END
from openai import OpenAI
import logfire

class WriterAgent:
    def __init__(self, openai_key: str, neo4j_memory, pinecone_memory):
        self.client = OpenAI(api_key=openai_key)
        self.neo4j = neo4j_memory
        self.pinecone = pinecone_memory
        self.logger = logfire.get_logger(__name__)

    def load_user_context(self, user_id: str) -> dict:
        """Neo4j + Pinecone에서 사용자 취향 로드"""
        # GraphRAG 쿼리: 과거 성과 높은 스크립트 패턴
        graph_context = self.neo4j.query(
            "MATCH (u:User {id: $user_id})-[:CREATED]->(s:Script)-[:ACHIEVED]->(m:Metrics) "
            "WHERE m.engagement_rate > 0.05 "
            "RETURN s.topic, s.style, m.engagement_rate "
            "ORDER BY m.engagement_rate DESC LIMIT 5",
            {"user_id": user_id}
        )

        # Pinecone: 유사 주제 검색
        vector_context = self.pinecone.query(...)

        return {"graph": graph_context, "vector": vector_context}

    def generate_scripts(self, state: AgentState) -> AgentState:
        """플랫폼별 스크립트 3종 생성"""
        with self.logger.span("writer.generate_scripts"):
            context = self.load_user_context(state.get("user_id"))

            system_prompt = f"""
            당신은 '{state['persona']['tone']}' 톤의 {state['persona']['gender']} 작가입니다.
            플랫폼: {state['platform']}
            과거 성과: {context['graph']}

            주어진 주제로 {state['platform']} 맞춤 스크립트 3종을 작성하세요.
            """

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": state['messages'][-1]['content']}
                ]
            )

            state['current_script'] = response.choices[0].message.content
            state['status'] = "script_ready"
            return state
```

### 2.3 Director 에이전트
**파일**: `backend/app/agents/director.py`

```python
class DirectorAgent:
    def __init__(self, audio_loop, veo_service, banana_service):
        self.audio_loop = audio_loop
        self.veo = veo_service
        self.banana = banana_service
        self.logger = logfire.get_logger(__name__)

    async def produce_video(self, state: AgentState) -> AgentState:
        """오디오 + 비주얼 생성 및 합성"""
        with self.logger.span("director.produce"):
            # 1. 캐릭터 레퍼런스 생성 (첫 실행 시만)
            if not state.get("character_ref"):
                char_ref = await self.banana.generate_reference(state['persona'])
                state['character_ref'] = char_ref

            # 2. Zero-Fault Audio 생성
            audio = await self.audio_loop.generate_verified_audio(
                state['current_script'],
                state['persona']['voice_id']
            )
            state['audio_files'].append(audio)

            # 3. Google Veo 영상 생성 (캐릭터 일관성 유지)
            video = await self.veo.generate_video(
                prompt=self._script_to_visual_prompt(state['current_script']),
                character_reference=state['character_ref'],
                duration=len(state['current_script']) // 15  # 대략 15자/초
            )
            state['video_files'].append(video)

            # 4. 립싱크 (옵션)
            if state.get('enable_lipsync'):
                synced_video = await self.heygen.sync_lips(video, audio)
                state['video_files'][-1] = synced_video

            state['status'] = "production_complete"
            return state
```

### 2.4 Marketer 에이전트
**파일**: `backend/app/agents/marketer.py`

```python
class MarketerAgent:
    def __init__(self, cloudinary_service, social_apis):
        self.cloudinary = cloudinary_service
        self.social = social_apis
        self.logger = logfire.get_logger(__name__)

    async def distribute(self, state: AgentState) -> AgentState:
        """썸네일 생성 + 카피 작성 + 다채널 배포"""
        with self.logger.span("marketer.distribute"):
            # 1. 썸네일 생성 (DALL-E 3)
            thumbnail = await self._generate_thumbnail(state['current_script'])

            # 2. 카피 문구 3종 생성
            captions = await self._generate_captions(state)

            # 3. Cloudinary 최적화
            optimized = await self.cloudinary.optimize_for_platform(
                video=state['video_files'][-1],
                platform=state['platform']
            )

            # 4. 자동 배포
            if state.get('auto_publish'):
                result = await self.social.publish(
                    platform=state['platform'],
                    video=optimized,
                    thumbnail=thumbnail,
                    caption=captions[0],  # 사용자 선택 또는 첫번째
                    schedule=state.get('publish_time')
                )
                state['publish_result'] = result

            state['status'] = "published"
            return state
```

### 2.5 LangGraph 워크플로우 조합
**파일**: `backend/app/agents/workflow.py`

```python
from langgraph.graph import StateGraph, END

def create_omnivibe_workflow():
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("writer", writer_agent.generate_scripts)
    workflow.add_node("director", director_agent.produce_video)
    workflow.add_node("marketer", marketer_agent.distribute)

    # 엣지 정의
    workflow.set_entry_point("writer")
    workflow.add_edge("writer", "director")
    workflow.add_edge("director", "marketer")
    workflow.add_edge("marketer", END)

    return workflow.compile()

# 실행
app = create_omnivibe_workflow()
result = await app.ainvoke({
    "messages": [{"role": "user", "content": "AI 트렌드 2026"}],
    "persona": {"gender": "female", "tone": "professional", "voice_id": "..."},
    "platform": "youtube",
    "audio_files": [],
    "video_files": [],
    "status": "initialized"
})
```

---

## Phase 3: Beta - Integration & Optimization (Week 7-9)

### 3.1 Google Sheets 커넥터
**파일**: `backend/app/services/sheets_service.py`

```python
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class SheetsConnector:
    def __init__(self, credentials_path: str):
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        self.service = build('sheets', 'v4', credentials=creds)

    def load_strategy(self, spreadsheet_id: str, range_name: str = "전략!A2:E"):
        """구글 시트에서 전략 및 소재목 로드"""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        rows = result.get('values', [])
        # [날짜, 주제, 플랫폼, 스타일, 발행시간]
        return [
            {
                "date": row[0],
                "topic": row[1],
                "platform": row[2],
                "style": row[3],
                "publish_time": row[4]
            }
            for row in rows
        ]
```

### 3.2 Cloudinary 최적화
**파일**: `backend/app/services/cloudinary_service.py`

```python
import cloudinary
import cloudinary.uploader

class CloudinaryService:
    PLATFORM_SPECS = {
        "youtube": {"width": 1920, "height": 1080, "format": "mp4"},
        "instagram": {"width": 1080, "height": 1920, "format": "mp4"},  # 세로
        "facebook": {"width": 1280, "height": 720, "format": "mp4"}
    }

    async def optimize_for_platform(self, video_path: str, platform: str) -> str:
        """플랫폼별 해상도/포맷 최적화"""
        spec = self.PLATFORM_SPECS[platform]

        result = cloudinary.uploader.upload_large(
            video_path,
            resource_type="video",
            transformation=[
                {"width": spec["width"], "height": spec["height"], "crop": "fill"},
                {"quality": "auto", "fetch_format": spec["format"]}
            ]
        )

        return result['secure_url']
```

### 3.3 Neo4j 메모리 구조
**Cypher 쿼리 예시**:
```cypher
// 사용자 페르소나 저장
CREATE (u:User {id: "user123"})
CREATE (p:Persona {gender: "female", tone: "professional", style: "교육"})
CREATE (u)-[:HAS_PERSONA]->(p)

// 스크립트 성과 저장
CREATE (s:Script {id: "script456", topic: "AI 트렌드", content: "..."})
CREATE (m:Metrics {views: 15000, engagement_rate: 0.08, ctr: 0.12})
CREATE (u)-[:CREATED]->(s)-[:ACHIEVED]->(m)

// 추천 쿼리 (과거 성과 기반)
MATCH (u:User {id: $user_id})-[:CREATED]->(s:Script)-[:ACHIEVED]->(m:Metrics)
WHERE m.engagement_rate > 0.05
RETURN s.topic, s.style, avg(m.engagement_rate) as avg_engagement
ORDER BY avg_engagement DESC
```

---

## Phase 4: Launch - SaaS Dashboard (Week 10-12)

### 4.1 Next.js 프론트엔드 구조
```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── signup/
│   ├── dashboard/
│   │   ├── strategy/       # 구글 시트 연동
│   │   ├── scripts/        # 스크립트 초안 리뷰
│   │   ├── production/     # 영상 생성 모니터링
│   │   └── analytics/      # 성과 대시보드
│   └── layout.tsx
├── components/
│   ├── AgentStatus.tsx     # LangGraph 상태 시각화
│   ├── AudioPlayer.tsx
│   └── VideoPreview.tsx
└── lib/
    └── api-client.ts       # FastAPI 연동
```

### 4.2 핵심 UI 컴포넌트
**파일**: `frontend/components/AgentStatus.tsx`
```tsx
"use client"

import { useEffect, useState } from 'react'

export function AgentStatus({ taskId }: { taskId: string }) {
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`http://localhost:8000/audio/status/${taskId}`)
      const data = await res.json()
      setStatus(data)

      if (data.status === 'completed') clearInterval(interval)
    }, 2000)

    return () => clearInterval(interval)
  }, [taskId])

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-semibold">에이전트 진행 상태</h3>
      <div className="mt-2 space-y-2">
        <Step name="Writer" status={status?.writer} />
        <Step name="Director" status={status?.director} />
        <Step name="Marketer" status={status?.marketer} />
      </div>
    </div>
  )
}
```

---

## 핵심 검증 지표 (KPI)

### PoC 단계
- [ ] TTS → STT 정확도 95% 이상 달성
- [ ] 평균 재시도 횟수 2회 이하
- [ ] Logfire 대시보드에서 API 비용 실시간 추적

### Alpha 단계
- [ ] 3개 에이전트 순차 실행 성공
- [ ] Neo4j에 사용자 페르소나 및 성과 데이터 저장
- [ ] Pinecone 벡터 검색 응답 시간 < 500ms

### Beta 단계
- [ ] 구글 시트 연동 후 자동 스케줄링
- [ ] Cloudinary 3개 플랫폼 동시 최적화 성공
- [ ] 평균 영상 생성 시간 < 10분 (Veo 대기 제외)

### Launch 단계
- [ ] Next.js 대시보드 실시간 에이전트 상태 표시
- [ ] 사용자당 월 100개 영상 처리 가능
- [ ] 다채널 자동 배포 성공률 98% 이상

---

## 리스크 관리

### 기술적 리스크
1. **Google Veo API 접근 제한**
   - 대안: Runway Gen-3 또는 Pika Labs
   - 현재 상태: Veo는 제한된 얼리억세스

2. **Nano Banana 안정성**
   - 대안: IP-Adapter + ControlNet (Stable Diffusion)
   - 검증 필요: 캐릭터 일관성 품질

3. **HeyGen 비용**
   - 대안: 오픈소스 Wav2Lip (GPU 필요)
   - 예상 비용: $0.05/초

### 운영 리스크
1. **API 비용 폭발**
   - 완화: Logfire로 실시간 모니터링 + 사용자별 할당량
   - 예상 월 비용: 사용자당 $50-100 (1000개 영상 기준)

2. **Celery 작업 큐 병목**
   - 완화: Redis Cluster + 워커 수평 확장
   - 모니터링: Flower 대시보드

---

## 다음 단계 액션

### 즉시 시작 (Week 1)
1. ✅ 프로젝트 디렉토리 구조 생성
2. ✅ Poetry 초기화 및 의존성 설치
3. ✅ Docker Compose (FastAPI + Redis + Neo4j + Pinecone)
4. ✅ .env 파일 설정 및 API 키 발급

### Week 2-3 집중
- Zero-Fault Audio Loop 완성
- Pytest 통합 테스트 작성
- Logfire 대시보드 구성

### 주간 체크포인트
- 매주 금요일: 데모 영상 생성 성공
- 격주: PRD 업데이트 및 로드맵 조정

---

**승인 대기**: 이 계획을 기반으로 즉시 프로젝트 초기화를 시작하시겠습니까?
