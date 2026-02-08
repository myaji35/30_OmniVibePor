# OmniVibe Pro - Claude 작업 가이드

## 📌 프로젝트 개요

**OmniVibe Pro**는 AI 기반 영상 자동화 SaaS 플랫폼으로, '바이브 코딩(Vibe Coding)' 방법론을 기반으로 영상 제작 전 과정을 자동화합니다.

### 핵심 가치 제안
- **Zero-Fault Audio**: ElevenLabs TTS → OpenAI Whisper STT → 검증 루프를 통한 99% 정확도
- **GraphRAG 기반 메모리**: Neo4j를 활용한 컨텍스트 보존 및 자가학습
- **멀티채널 자동화**: 구글 시트 전략 수립부터 영상 생성, 배포까지 전 과정 자동화
- **Salesforce Lightning Design System (SLDS)**: 엔터프라이즈급 UI/UX

---

## 🛠 기술 스택

### Backend (FastAPI)
```
핵심 프레임워크:
- FastAPI 0.109+         : ASGI 기반 고성능 웹 프레임워크
- Python 3.11+           : 비동기 처리, 타입 힌팅
- Uvicorn                : ASGI 서버

AI & LLM:
- LangGraph 0.0.26+      : AI 에이전트 오케스트레이션
- LangChain 0.1+         : LLM 추상화 레이어
- OpenAI API             : GPT-4, Whisper STT
- Anthropic API          : Claude 3.5 Sonnet
- ElevenLabs             : 음성 클로닝 및 TTS

태스크 큐 & 캐싱:
- Celery 5.3+            : 비동기 작업 처리
- Redis 7                : 메시지 브로커, 캐싱

데이터베이스:
- SQLite                 : 로컬 개발 및 경량 운영
- Neo4j 5.16             : GraphRAG 메모리 저장소
- Pinecone               : 벡터 임베딩 검색

미디어 처리:
- FFmpeg                 : 영상/오디오 인코딩
- PyDub                  : 오디오 편집
- OpenCV                 : 이미지/영상 처리
- Pillow                 : 이미지 변환

클라우드 서비스:
- Cloudinary             : 미디어 CDN 및 변환
- Google Sheets API      : 전략 관리
```

### Frontend (Next.js)
```
핵심 프레임워크:
- Next.js 14.1           : React 기반 풀스택 프레임워크
- React 18.2             : UI 라이브러리
- TypeScript 5           : 타입 안정성

상태 관리:
- Zustand 4.5            : 경량 상태 관리
- TanStack Query 5.17    : 서버 상태 동기화

UI/UX:
- Tailwind CSS 3.4       : 유틸리티 퍼스트 CSS
- Framer Motion 12       : 애니메이션
- Lucide React           : 아이콘 라이브러리
- SLDS Design Tokens     : Salesforce 스타일 시스템

영상 렌더링:
- Remotion 4.0           : React 기반 영상 렌더링
- WaveSurfer.js 7.12     : 오디오 시각화

드래그 앤 드롭:
- @dnd-kit               : 현대적 DnD 라이브러리
- @hello-pangea/dnd      : React Beautiful DnD 포크
```

### 인프라 & 배포
```
컨테이너화:
- Docker                 : 컨테이너 런타임
- Docker Compose         : 멀티 컨테이너 오케스트레이션
- Nginx                  : 리버스 프록시, SSL 터미네이션

배포 환경:
- Vultr VPS              : 프로덕션 서버
- Production 포트        : Frontend 3020, Backend 8000
- Development 포트       : Frontend 4024, Backend 8000

모니터링:
- Logfire (Optional)     : 옵저버빌리티
- Celery Flower          : 태스크 모니터링
```

---

## 🎯 주요 기능

### 1. Voice Cloning (음성 클로닝)
**경로**: `/api/v1/voice/*`
- ElevenLabs Professional Voice Cloning API 연동
- 사용자 맞춤형 TTS 모델 생성
- 음성 샘플 업로드 → 학습 → 커스텀 보이스 생성

**핵심 서비스**:
- `app/services/voice_cloning_service.py`

### 2. Zero-Fault Audio Generation
**경로**: `/api/v1/audio/*`
- TTS 생성 → STT 검증 → 오류 감지 → 재생성 루프
- 99% 정확도 달성 목표
- Celery 비동기 작업으로 처리

**핵심 서비스**:
- `app/services/tts_service.py` - TTS 생성
- `app/services/stt_service.py` - STT 검증
- `app/services/audio_correction_loop.py` - 검증 루프
- `app/tasks/audio_tasks.py` - Celery 태스크

### 3. AI Content Production Pipeline
**경로**: `/api/v1/content/*`, `/api/v1/campaigns/*`
- **Director Agent**: 전체 워크플로우 오케스트레이션
- **Writer Agent**: 스크립트 작성 및 최적화
- **Continuity Agent**: 브랜드 일관성 유지
- **YouTube Thumbnail Learner**: 썸네일 성과 분석 및 학습

**핵심 서비스**:
- `app/agents/director_agent.py`
- `app/services/writer_agent.py`
- `app/services/continuity_agent.py`
- `app/services/youtube_thumbnail_learner.py`

### 4. Presentation to Video (PDF → 영상)
**경로**: `/api/v1/presentation/*`
- PDF 슬라이드 → 이미지 추출 → 스크립트 생성 → 타이밍 분석 → 영상 렌더링
- 자동 자막 생성 및 동기화
- Google Sheets 기반 일정 관리

**핵심 서비스**:
- `app/services/pdf_to_slides_service.py` - PDF 처리
- `app/services/slide_to_script_converter.py` - 스크립트 생성
- `app/services/video_editor_service.py` - 영상 편집

### 5. GraphRAG Memory System
**경로**: Neo4j 데이터베이스
- 사용자 인터랙션, 성과 데이터, 컨텍스트를 그래프로 저장
- 시간에 따른 학습 및 최적화
- Pinecone 벡터 검색과 결합

**핵심 서비스**:
- `app/services/neo4j_client.py`
- `app/services/embedding_visualizer.py`

### 6. Performance Tracking & Analytics
**경로**: `/api/v1/performance/*`
- 멀티 플랫폼 성과 추적 (YouTube, Instagram, TikTok 등)
- 자가학습 시스템: 성과 데이터 → GraphRAG 저장 → 다음 컨텐츠 최적화
- 실시간 대시보드

**핵심 서비스**:
- `app/services/content_performance_tracker.py`

### 7. Remotion Video Rendering
**경로**: `frontend/remotion/*`
- React 컴포넌트로 영상 프로그래밍
- 스토리보드 기반 자동 렌더링
- 타임라인 편집 UI

**핵심 컴포넌트**:
- `frontend/remotion/Composition.tsx`
- `frontend/components/StoryboardEditor.tsx`

### 8. WebSocket Real-time Updates
**경로**: `/ws/*`
- 작업 진행 상황 실시간 전송
- 프론트엔드 진행률 표시
- Celery 태스크 상태와 동기화

**핵심 모듈**:
- `app/api/v1/websocket.py`
- `frontend/hooks/useWebSocket.ts`

---

## 📂 프로젝트 구조

```
0030_OmniVibePro/
├── backend/                          # FastAPI 백엔드
│   ├── app/
│   │   ├── agents/                   # AI 에이전트 (Director)
│   │   ├── api/v1/                   # API 라우터
│   │   │   ├── audio.py              # 오디오 생성 API
│   │   │   ├── voice.py              # 음성 클로닝 API
│   │   │   ├── campaigns.py          # 캠페인 관리 API
│   │   │   ├── content.py            # 컨텐츠 생성 API
│   │   │   ├── performance.py        # 성과 추적 API
│   │   │   ├── presentation.py       # PDF → 영상 API
│   │   │   └── websocket.py          # WebSocket 엔드포인트
│   │   ├── auth/                     # 인증/인가 모듈
│   │   ├── core/                     # 설정, 시크릿 관리
│   │   ├── db/                       # 데이터베이스 연결
│   │   ├── middleware/               # Rate Limiting, CORS, Security
│   │   ├── models/                   # Pydantic 모델
│   │   ├── services/                 # 비즈니스 로직
│   │   │   ├── voice_cloning_service.py
│   │   │   ├── tts_service.py
│   │   │   ├── stt_service.py
│   │   │   ├── audio_correction_loop.py
│   │   │   ├── director_agent.py
│   │   │   ├── writer_agent.py
│   │   │   ├── continuity_agent.py
│   │   │   ├── neo4j_client.py
│   │   │   ├── pdf_to_slides_service.py
│   │   │   ├── slide_to_script_converter.py
│   │   │   ├── video_editor_service.py
│   │   │   ├── content_performance_tracker.py
│   │   │   └── youtube_thumbnail_learner.py
│   │   ├── tasks/                    # Celery 태스크
│   │   │   ├── celery_app.py
│   │   │   ├── audio_tasks.py
│   │   │   └── video_tasks.py
│   │   ├── utils/                    # 유틸리티 함수
│   │   └── main.py                   # FastAPI 앱 진입점
│   ├── tests/                        # 테스트 코드
│   ├── scripts/                      # 유틸리티 스크립트
│   ├── outputs/                      # 생성된 파일 저장
│   ├── requirements.txt              # Python 의존성
│   ├── Dockerfile                    # 개발 컨테이너
│   ├── Dockerfile.production         # 프로덕션 컨테이너
│   └── docker-compose.yml            # 로컬 개발 환경
│
├── frontend/                         # Next.js 프론트엔드
│   ├── app/                          # Next.js App Router
│   │   ├── page.tsx                  # 홈 페이지
│   │   ├── layout.tsx                # 루트 레이아웃
│   │   ├── dashboard/                # 대시보드
│   │   ├── production/               # 영상 제작 페이지
│   │   └── api/                      # API 라우트 핸들러
│   │       ├── backend-status/
│   │       ├── campaigns/
│   │       ├── content-script/
│   │       ├── storyboard/
│   │       └── writer-generate/
│   ├── components/                   # React 컴포넌트
│   │   ├── slds/                     # Salesforce Design System 컴포넌트
│   │   │   ├── base/                 # Button, Badge, Input
│   │   │   ├── layout/               # Card, Layout
│   │   │   └── feedback/             # ProgressBar, Toast
│   │   ├── StoryboardEditor.tsx      # 스토리보드 편집기
│   │   ├── SubtitleEditor.tsx        # 자막 편집기
│   │   └── AudioWaveform.tsx         # 오디오 시각화
│   ├── remotion/                     # Remotion 영상 렌더링
│   │   ├── Composition.tsx
│   │   └── Video.tsx
│   ├── hooks/                        # Custom React Hooks
│   │   ├── useWebSocket.ts           # WebSocket 연결
│   │   └── useBackendStatus.ts       # 백엔드 상태 체크
│   ├── lib/                          # 유틸리티 라이브러리
│   ├── data/                         # 정적 데이터
│   ├── package.json                  # Node.js 의존성
│   ├── tailwind.config.ts            # Tailwind + SLDS 토큰
│   ├── Dockerfile.production         # 프로덕션 컨테이너
│   └── next.config.js                # Next.js 설정
│
├── nginx/                            # Nginx 리버스 프록시
│   ├── nginx.conf                    # 프로덕션 설정
│   └── ssl/                          # SSL 인증서
│
├── docs/                             # 프로젝트 문서
│   ├── IMPLEMENTATION_SUMMARY.md     # 구현 요약
│   ├── QUICK_START_ACTION_PLAN.md    # 빠른 시작 가이드
│   ├── REMOTION_INTEGRATION_PLAN.md  # Remotion 통합 계획
│   ├── VULTR_DEPLOYMENT_GUIDE.md     # 배포 가이드
│   └── WEEK1_KICKOFF_SUMMARY.md      # Week 1 킥오프
│
├── scripts/                          # 유틸리티 스크립트
├── docker-compose.yml                # 로컬 개발 환경
├── docker-compose.production.yml     # 프로덕션 환경
├── deploy-vultr.sh                   # Vultr 배포 스크립트
└── README.md                         # 프로젝트 소개
```

---

## 💻 개발 가이드라인

### 1. 코드 작성 원칙

#### Backend (Python/FastAPI)
```python
# 1. 타입 힌팅 필수
from typing import Optional, List, Dict
from pydantic import BaseModel

async def get_audio_status(task_id: str) -> Optional[Dict[str, Any]]:
    pass

# 2. Pydantic 모델 사용
class AudioGenerateRequest(BaseModel):
    script: str
    voice_id: str
    max_iterations: int = 5

# 3. 비동기 처리 우선
@app.post("/api/v1/audio/generate")
async def generate_audio(request: AudioGenerateRequest):
    task = generate_audio_task.delay(request.dict())
    return {"task_id": task.id}

# 4. 에러 핸들링
from fastapi import HTTPException

try:
    result = await tts_service.generate(script)
except Exception as e:
    logger.error(f"TTS generation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# 5. 로깅 표준
import logging
logger = logging.getLogger(__name__)

logger.info(f"Audio generation started: {task_id}")
logger.error(f"Failed to generate audio: {error}")
```

#### Frontend (TypeScript/React)
```typescript
// 1. 타입 안정성
interface Campaign {
  id: string;
  title: string;
  status: 'draft' | 'in_progress' | 'completed';
}

// 2. Zustand 상태 관리
import { create } from 'zustand';

interface CampaignStore {
  campaigns: Campaign[];
  addCampaign: (campaign: Campaign) => void;
}

export const useCampaignStore = create<CampaignStore>((set) => ({
  campaigns: [],
  addCampaign: (campaign) =>
    set((state) => ({ campaigns: [...state.campaigns, campaign] })),
}));

// 3. TanStack Query 서버 상태
import { useQuery } from '@tanstack/react-query';

export function useCampaigns() {
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const res = await fetch('/api/campaigns');
      return res.json();
    },
  });
}

// 4. SLDS 컴포넌트 사용
import { Button, Card, Badge } from '@/components/slds';

<Card
  title="캠페인 관리"
  icon={<CalendarIcon />}
  action={<Button variant="brand">새 캠페인</Button>}
>
  <Badge variant="success">진행 중</Badge>
</Card>

// 5. Tailwind SLDS 토큰
<div className="bg-slds-background text-slds-text-heading p-slds-medium rounded-slds">
  <h1 className="text-slds-heading-large">제목</h1>
</div>
```

### 2. Salesforce Lightning Design System (SLDS) 준수

**OmniVibe Pro는 엔터프라이즈급 UI/UX를 위해 Salesforce Lightning Design System을 엄격히 준수합니다.**

#### 핵심 UI/UX 원칙

##### 1. 레이아웃 구조
- **3-Column Layout**: 좌측(Navigation), 중앙(Main Workspace), 우측(Contextual Sidebar/Activity) 구조를 기본으로 합니다.
- **Card 기반 설계**: 모든 독립된 데이터 단위는 `Card` 컴포넌트로 그룹화하며, 상단에 명확한 Header와 Action 버튼을 배치합니다.
- **Compact Header**: 핵심 정보(KPI, 요약 데이터)는 항상 상단에 고정하여 가시성을 확보합니다.

##### 2. 디자인 토큰 및 스타일
- **Color Palette**: Salesforce Blue(`#00A1E0`), 중립 배경색(`#F3F2F2`), 텍스트 강조색(`#16325C`)을 주로 사용합니다.
- **Spacing & Radius**: Padding은 기본 `1rem`, Border-radius는 `0.25rem`(4px)을 사용하여 기업용 소프트웨어의 신뢰감을 줍니다.
- **Typography**: 위계(Hierarchy)를 명확히 합니다. 제목은 Bold, 본문은 Regular로 구분하며 가독성을 최우선으로 합니다.

##### 3. Action-Oriented UX
- 사용자가 데이터를 조회한 후 다음 행동(예: 오디오 생성, 영상 편집)을 즉시 수행할 수 있도록 상단이나 카드 우측 상단에 **Global Actions**를 배치합니다.

#### 레이아웃 구현 예제

```typescript
// 3-Column Layout
<div className="flex h-screen">
  {/* Left Navigation */}
  <aside className="w-64 bg-slds-background-alt border-r border-slds-border">
    <Navigation />
  </aside>

  {/* Main Workspace */}
  <main className="flex-1 p-slds-large overflow-y-auto">
    {/* Compact Header - KPI 요약 */}
    <div className="bg-white rounded-slds border border-slds-border p-slds-medium mb-slds-large">
      <div className="flex justify-between items-center">
        <h1 className="text-slds-heading-large text-slds-text-heading">Audio Production</h1>
        <div className="flex gap-4 text-sm">
          <div>
            <div className="text-slds-text-weak">Total Jobs</div>
            <div className="text-2xl font-bold text-slds-brand">24</div>
          </div>
          <div>
            <div className="text-slds-text-weak">Success Rate</div>
            <div className="text-2xl font-bold text-slds-success">99%</div>
          </div>
        </div>
      </div>
    </div>

    {/* Card 기반 컨텐츠 */}
    <Card title="주요 작업 영역">
      {/* Content */}
    </Card>
  </main>

  {/* Right Sidebar (Optional) */}
  <aside className="w-80 bg-slds-background border-l border-slds-border">
    <ActivityFeed />
  </aside>
</div>

// Card 기반 설계
<Card
  title="Audio Zero-Fault 작업"
  icon={<MicIcon />}
  action={
    <Button variant="brand" icon={<PlusIcon />}>
      새 작업
    </Button>
  }
  footer={
    <div className="flex justify-between">
      <Badge variant="info">3건 진행 중</Badge>
      <Button variant="neutral" size="small">전체 보기</Button>
    </div>
  }
>
  <ProgressBar value={75} variant="success" showLabel />
</Card>
```

#### 컬러 시스템 가이드

```typescript
// ===== Primary Colors =====
// Salesforce Blue - 주요 액션, 브랜드 색상
#00A1E0 (slds-brand)
<Button variant="brand">저장하기</Button>

// 중립 배경 - 페이지 전체 배경
#F3F2F2 (slds-background)
<div className="bg-slds-background">

// 텍스트 강조 - 제목, 중요 텍스트
#16325C (slds-text-heading)
<h1 className="text-slds-text-heading">


// ===== Status Colors =====
// Success - 완료, 성공 상태
#4BCA81 (slds-success)
<Badge variant="success">완료</Badge>

// Warning - 대기, 주의 필요
#FFB75D (slds-warning)
<Badge variant="warning">대기 중</Badge>

// Error - 실패, 삭제 등 위험한 액션
#EA001E (slds-error)
<Button variant="destructive">삭제</Button>

// Info - 진행 중, 정보성 상태
#5867E8 (slds-info)
<Badge variant="info">진행 중</Badge>


// ===== Text Hierarchy =====
text-slds-text-heading     // #16325C (제목, 강조 텍스트)
text-slds-text-body        // #3E3E3C (본문 텍스트)
text-slds-text-weak        // #706E6B (보조 텍스트, 메타 정보)


// ===== Backgrounds & Borders =====
bg-slds-background         // #F3F2F2 (페이지 배경)
bg-slds-background-alt     // #FFFFFF (카드, 사이드바 배경)
border-slds-border         // #DDDBDA (구분선, 테두리)


// ===== Spacing Tokens =====
p-slds-small              // 0.5rem (8px)
p-slds-medium             // 1rem (16px)
p-slds-large              // 1.5rem (24px)
rounded-slds              // 0.25rem (4px)
```

#### SLDS 컴포넌트 사용 원칙

```typescript
// 1. 항상 SLDS 컴포넌트를 우선 사용
import { Button, Card, Badge, ProgressBar } from '@/components/slds';

// ❌ 잘못된 예
<button className="bg-blue-500 text-white px-4 py-2">버튼</button>

// ✅ 올바른 예
<Button variant="brand">버튼</Button>


// 2. Card로 데이터 그룹화
// ❌ 잘못된 예
<div className="border rounded p-4">
  <h3>제목</h3>
  <p>내용</p>
</div>

// ✅ 올바른 예
<Card title="제목" icon={<Icon />}>
  <p>내용</p>
</Card>


// 3. 상태 표시는 Badge 사용
// ❌ 잘못된 예
<span className="bg-green-500 text-white px-2 py-1 rounded">완료</span>

// ✅ 올바른 예
<Badge variant="success">완료</Badge>


// 4. 진행률은 ProgressBar 사용
// ❌ 잘못된 예
<div className="w-full bg-gray-200">
  <div className="bg-blue-500" style={{ width: '75%' }} />
</div>

// ✅ 올바른 예
<ProgressBar value={75} variant="success" showLabel />
```

### 3. Git 커밋 규칙

```bash
# Conventional Commits 형식 (한국어)
feat: SLDS 카드 컴포넌트 추가
fix: 오디오 생성 시 타임아웃 버그 수정
refactor: TTS 서비스 비동기 처리 개선
docs: API 문서 업데이트
test: 오디오 검증 루프 테스트 추가
chore: Celery 워커 설정 변경

# 예시
git commit -m "feat: Zero-Fault Audio 검증 루프 구현

- TTS 생성 → STT 검증 → 재생성 파이프라인
- 최대 5회 반복 검증
- Celery 비동기 작업으로 처리

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 4. 환경 변수 관리

#### Backend `.env`
```bash
# API Keys
ELEVENLABS_API_KEY=your_elevenlabs_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=sqlite:///omni_db.sqlite
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=omnivibe2026

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Cloud Services
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Monitoring (Optional)
LOGFIRE_TOKEN=your_logfire_token
```

#### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

### 5. 테스트 작성 가이드

```python
# Backend 테스트 (pytest)
import pytest
from app.services.tts_service import TTSService

@pytest.mark.asyncio
async def test_tts_generation():
    service = TTSService()
    result = await service.generate("안녕하세요", voice_id="test_voice")
    assert result.success is True
    assert result.audio_url is not None

# E2E 테스트
def test_audio_zero_fault_pipeline():
    """Zero-Fault Audio 전체 파이프라인 테스트"""
    # 1. TTS 생성
    # 2. STT 검증
    # 3. 재생성 루프
    # 4. 최종 결과 검증
    pass
```

```typescript
// Frontend 테스트 (Jest/React Testing Library)
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/slds';

test('SLDS Button renders correctly', () => {
  render(<Button variant="brand">클릭</Button>);
  expect(screen.getByText('클릭')).toBeInTheDocument();
});
```

### 6. 성능 최적화 원칙

```python
# Backend
# 1. Celery로 무거운 작업 비동기 처리
@celery_app.task(bind=True)
def generate_audio_task(self, script: str, voice_id: str):
    self.update_state(state='PROGRESS', meta={'progress': 10})
    # 작업 실행
    self.update_state(state='PROGRESS', meta={'progress': 100})

# 2. Redis 캐싱
from redis import Redis
redis_client = Redis.from_url(settings.REDIS_URL)

cached = redis_client.get(f"campaign:{campaign_id}")
if cached:
    return json.loads(cached)

# 3. 데이터베이스 쿼리 최적화
# - 필요한 필드만 조회
# - N+1 문제 방지
```

```typescript
// Frontend
// 1. React.memo로 불필요한 리렌더 방지
export const ExpensiveComponent = React.memo(({ data }) => {
  // 렌더링 로직
});

// 2. useCallback으로 함수 메모이제이션
const handleClick = useCallback(() => {
  // 핸들러 로직
}, [dependencies]);

// 3. 이미지 최적화
import Image from 'next/image';

<Image
  src="/thumbnail.jpg"
  alt="썸네일"
  width={800}
  height={450}
  loading="lazy"
/>

// 4. Code Splitting
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>로딩 중...</p>,
});
```

---

## 🚀 배포 정보

### 로컬 개발 환경
```bash
# 1. 백엔드 실행
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Celery 워커 실행 (별도 터미널)
cd backend
celery -A app.tasks.celery_app worker --loglevel=info

# 3. Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 4. Neo4j 실행 (Docker)
docker run -d -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/omnivibe2026 \
  neo4j:5.16

# 5. 프론트엔드 실행
cd frontend
npm install
npm run dev  # http://localhost:3020
```

### Docker Compose 개발 환경
```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker

# 중지
docker-compose down
```

### 프로덕션 배포 (Vultr)
```bash
# 1. 서버 접속
ssh root@your-vultr-ip

# 2. 프로젝트 클론
git clone https://github.com/yourusername/0030_OmniVibePro.git
cd 0030_OmniVibePro

# 3. 환경 변수 설정
cp backend/.env.production.template backend/.env.production
# .env.production 파일 편집하여 실제 API 키 입력

# 4. 배포 스크립트 실행
chmod +x deploy-vultr.sh
./deploy-vultr.sh

# 5. 서비스 확인
docker-compose -f docker-compose.production.yml ps
curl http://localhost/health
```

### 프로덕션 URL
- **Frontend**: https://omnivibepro.com (또는 http://your-vultr-ip:3020)
- **Backend API**: https://api.omnivibepro.com (또는 http://your-vultr-ip:8000)
- **API Docs**: https://api.omnivibepro.com/docs
- **Neo4j Browser**: http://your-vultr-ip:7474
- **Celery Flower**: http://your-vultr-ip:5555 (Optional)

### 주요 포트
```
3020   : Frontend (Next.js) Production
8000   : Backend (FastAPI) API
6379   : Redis (Task Queue)
7474   : Neo4j HTTP (Browser)
7687   : Neo4j Bolt (DB Connection)
80/443 : Nginx (Reverse Proxy, SSL)
```

---

## 📊 모니터링 & 로깅

### 로그 확인
```bash
# Docker Compose 로그
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f celery-worker

# 백엔드 로그 파일
tail -f backend/logs/app.log

# Nginx 로그
tail -f nginx/logs/access.log
tail -f nginx/logs/error.log
```

### Celery 작업 모니터링
```bash
# Flower 실행 (Optional)
cd backend
celery -A app.tasks.celery_app flower --port=5555

# 브라우저에서 http://localhost:5555 접속
```

### 데이터베이스 관리
```bash
# Neo4j Browser
http://localhost:7474
# 로그인: neo4j / omnivibe2026

# SQLite 데이터베이스
sqlite3 backend/omni_db.sqlite
.tables
SELECT * FROM campaigns;
```

---

## 🔧 트러블슈팅

### 자주 발생하는 문제

#### 1. Celery 작업이 실행되지 않음
```bash
# Redis 연결 확인
redis-cli ping  # 응답: PONG

# Celery 워커 재시작
cd backend
./stop_celery.sh
./start_celery.sh

# Celery 작업 확인
celery -A app.tasks.celery_app inspect active
```

#### 2. Neo4j 연결 실패
```bash
# Neo4j 컨테이너 상태 확인
docker ps | grep neo4j

# Neo4j 로그 확인
docker logs omnivibe-neo4j

# 비밀번호 초기화 (필요 시)
docker exec -it omnivibe-neo4j cypher-shell -u neo4j -p omnivibe2026
```

#### 3. 프론트엔드 빌드 오류
```bash
# node_modules 재설치
cd frontend
rm -rf node_modules package-lock.json
npm install

# Next.js 캐시 삭제
rm -rf .next
npm run build
```

#### 4. API 요청 CORS 에러
```python
# backend/app/main.py에서 CORS 설정 확인
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3020", "https://omnivibepro.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📚 추가 리소스

### 프로젝트 문서
- `/docs/IMPLEMENTATION_SUMMARY.md` - 구현 요약
- `/docs/QUICK_START_ACTION_PLAN.md` - 빠른 시작 가이드
- `/docs/VULTR_DEPLOYMENT_GUIDE.md` - 배포 가이드
- `/docs/REMOTION_INTEGRATION_PLAN.md` - Remotion 통합 계획

### Backend 문서
- `/backend/API_DOCUMENTATION.md` - API 전체 명세
- `/backend/CHARACTER_SERVICE_README.md` - 캐릭터 서비스
- `/backend/LIPSYNC_QUICKSTART.md` - 립싱크 가이드
- `/backend/SECURITY_GUIDE.md` - 보안 가이드

### Frontend 문서
- `/frontend/SUBTITLE_EDITOR_USAGE.md` - 자막 편집기 사용법
- `/frontend/WEBSOCKET_CLIENT_GUIDE.md` - WebSocket 클라이언트

### 외부 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 공식 문서](https://nextjs.org/docs)
- [Remotion 공식 문서](https://www.remotion.dev/docs)
- [Salesforce Lightning Design System](https://www.lightningdesignsystem.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)

---

## 🎯 현재 개발 상태 (2026-02-08 기준)

### ✅ 완료된 기능
- Voice Cloning API 연동
- Zero-Fault Audio Pipeline
- SLDS 디자인 시스템 통합
- Remotion 영상 렌더링 설정
- Docker 기반 프로덕션 배포
- Celery 비동기 작업 처리
- Neo4j GraphRAG 기본 구조
- WebSocket 실시간 통신

### 🚧 진행 중
- AI Director Agent 고도화
- 멀티 플랫폼 성과 추적
- 자동 자막 생성 최적화
- Thumbnail 학습 시스템

### 📋 예정 기능
- 실시간 협업 편집
- A/B 테스트 자동화
- 다국어 TTS 지원
- 영상 템플릿 마켓플레이스

---

## 📞 문의 및 지원

**프로젝트 소유자**: Gagahoho, Inc.
**CEO**: 강승식
**개발 방법론**: Vibe Coding
**라이선스**: MIT

---

**마지막 업데이트**: 2026-02-08
**문서 버전**: 1.0.0
