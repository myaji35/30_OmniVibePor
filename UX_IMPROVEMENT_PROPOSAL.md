# OmniVibe Pro UI/UX 개선 제안서

## 📋 Executive Summary

**현재 문제점**: 사용자가 스크립트 작성 후 오디오 생성을 위해 URL을 수동으로 이동하고 텍스트를 복사/붙여넣기 해야 하는 비효율적인 워크플로우

**목표**: Writer Agent → Director Agent로 자연스럽게 연결되는 통합 워크플로우 구현

**기대효과**:
- 클릭 수 감소: 7회 → 2회 (70% 개선)
- 작업 시간 단축: 평균 3분 → 30초 (83% 개선)
- 사용자 만족도 향상
- 에러율 감소 (복사/붙여넣기 실수 방지)

---

## 🔍 1. 현재 UI/UX 문제점 분석

### 1.1 현재 사용자 여정 (As-Is)

```
[Writer Agent 페이지]
  ↓ 스크립트 작성 완료
  ↓ (사용자가 텍스트를 마우스로 드래그하여 복사 Cmd+C)
  ↓
[브라우저 주소창]
  ↓ 사용자가 직접 /audio URL 입력
  ↓
[Audio 페이지]
  ↓ 붙여넣기 Cmd+V
  ↓ "생성하기" 버튼 클릭
  ↓ 진행 상태 확인 (폴링)
  ↓ 오디오 재생
  ↓ (다시 뒤로가기 또는 /video URL로 이동)
  ↓
[Video 페이지]
  ↓ 스크립트 또 다시 붙여넣기...
```

**문제점**:
1. **단절된 워크플로우**: 각 에이전트가 별도 페이지로 분리
2. **반복 작업**: 스크립트를 여러 번 복사/붙여넣기
3. **수동 네비게이션**: URL을 직접 입력해야 함
4. **컨텍스트 손실**: 페이지 이동 시 이전 작업 내용이 사라짐
5. **메타데이터 혼재**: "### 훅", "--- 예상 영상 길이: 2분 30초" 같은 메타데이터가 TTS에 포함됨

### 1.2 사용자 페인 포인트

| 문제 영역 | 구체적 불편 사항 | 심각도 |
|----------|----------------|--------|
| 네비게이션 | URL 수동 입력 필요 | 🔴 높음 |
| 데이터 입력 | 스크립트 복사/붙여넣기 반복 | 🔴 높음 |
| 진행 상태 | 현재 어느 단계인지 파악 어려움 | 🟡 중간 |
| 에러 처리 | 붙여넣기 실수 시 처음부터 다시 | 🔴 높음 |
| 피드백 | 오디오 생성 중 진행 표시 부족 | 🟡 중간 |

---

## ✨ 2. 개선된 사용자 여정 (To-Be)

### 2.1 통합 프로덕션 파이프라인 UI

```
[통합 대시보드: /production]
  ┌─────────────────────────────────────────────────┐
  │  📝 Writer Agent  →  🎬 Director  →  📤 Marketer │
  │  [활성]              [대기]         [대기]        │
  └─────────────────────────────────────────────────┘

  [Step 1: 스크립트 작성]
    ├── 구글 시트 연동 버튼
    ├── 페르소나 선택 드롭다운
    ├── 플랫폼 선택 (유튜브/인스타/틱톡)
    └── 스크립트 에디터 (실시간 저장)
         ↓
    [다음: 오디오 생성] 버튼 클릭
         ↓
  [Step 2: 오디오 생성 (자동 전환)]
    ├── 스크립트 자동 전달 (복사 불필요)
    ├── 음성 선택 (내 음성 클론 / 기본 음성)
    ├── 실시간 진행 상태 (5단계 애니메이션)
    ├── 생성 완료 시 자동 재생
    └── 오디오 파형 시각화
         ↓
    [다음: 영상 생성] 버튼 클릭
         ↓
  [Step 3: 영상 생성]
    ├── 오디오 자동 연동
    ├── Google Veo 프롬프트 생성
    ├── 립싱크 처리 (HeyGen/Wav2Lip)
    └── 최종 영상 렌더링
         ↓
  [완료: 배포]
    ├── 플랫폼별 최적화 (Cloudinary)
    ├── 자동 업로드 (예약 가능)
    └── 성과 추적 대시보드
```

### 2.2 핵심 UX 개선 사항

#### ✅ **자동 컨텍스트 전달**
- 스크립트를 한 번만 작성하면 자동으로 다음 단계로 전달
- 브라우저 `sessionStorage` 또는 백엔드 세션으로 데이터 유지
- 사용자는 "다음" 버튼만 클릭

#### ✅ **단일 페이지 워크플로우**
- `/production` 단일 URL에서 모든 작업 수행
- 탭 방식 또는 스텝 진행 방식 UI
- URL 수동 입력 불필요

#### ✅ **스마트 스크립트 파싱**
- 메타데이터 자동 제거: `### 훅`, `--- 예상 영상 길이: 2분 30초`
- Director Agent용 타이밍 정보 추출: `(첫 3초)` → 영상 이펙트에 활용
- CTA 구간 자동 마킹

#### ✅ **실시간 피드백**
- 오디오 생성 진행률 (1% 단위)
- 현재 시도 횟수 (Attempt 2/5)
- 유사도 실시간 표시 (95.61%)
- 예상 완료 시간

#### ✅ **에러 복구**
- 중간에 실패해도 이전 단계 데이터 보존
- "재시도" 버튼으로 현재 단계만 다시 실행
- 자동 저장 (5초마다)

---

## 🎨 3. 상세 UI 설계안

### 3.1 통합 프로덕션 대시보드 (`/production`)

#### **레이아웃 구조**

```
┌────────────────────────────────────────────────────────────┐
│  OmniVibe Pro                    [프로젝트 저장] [설정] [👤] │
├────────────────────────────────────────────────────────────┤
│  📂 My Projects  /  새 프로젝트 - 저시력자 마케팅 영상       │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐            │
│  │ 1.Writer│ → │2.Director│→│3.Marketer│→│ 4.배포 │           │
│  │   ✅   │   │  ▶️   │  │  ⏸️  │  │  ⏸️  │            │
│  └───────┘   └───────┘   └───────┘   └───────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🎬 Director Agent - 오디오 생성                       │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                        │  │
│  │  📝 스크립트 (Writer에서 자동 전달됨)                  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ 여러분, 눈이 침침해서 스마트폰 글씨가 안 보인다고  │  │  │
│  │  │ 포기하셨나요? 이제 iPhone 저시력자 모드로...      │  │  │
│  │  │                                                    │  │  │
│  │  │ [메타데이터 자동 제거됨]                          │  │  │
│  │  │ - "### 훅 (첫 3초)" → 타이밍 정보로 활용          │  │  │
│  │  │ - "--- 예상 영상 길이: 2분 30초" → 제거           │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  🎙️ 음성 선택                                         │  │
│  │  ( ) 내 음성 (클론: voice_abc123)                     │  │
│  │  (●) 기본 음성 - Rachel (여성, 미국 영어)             │  │
│  │  [+ 새 음성 클론하기]                                  │  │
│  │                                                        │  │
│  │  ⚙️ 고급 설정                                         │  │
│  │  정확도 임계값: [95%  ●────────────  100%]             │  │
│  │  최대 재시도: [5회 ▼]                                 │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ 🔄 오디오 생성 진행 중... (Attempt 2/5)          │  │  │
│  │  │                                                    │  │  │
│  │  │  1. 텍스트 정규화 ✅                              │  │  │
│  │  │  2. TTS 생성 ✅                                   │  │  │
│  │  │  3. STT 검증 ⏳ (진행 중...)                      │  │  │
│  │  │  4. 유사도 계산 ⏸️                               │  │  │
│  │  │  5. 최종 검증 ⏸️                                 │  │  │
│  │  │                                                    │  │  │
│  │  │  현재 유사도: 92.3% (목표: 95%)                   │  │  │
│  │  │  [████████░░░░] 82% 완료                          │  │  │
│  │  │  예상 완료: 8초 남음                              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ✅ 생성 완료!                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ 🎵 Audio Player                                  │  │  │
│  │  │ ▶️  ━━━●────────────  01:23 / 02:30             │  │  │
│  │  │                                                    │  │  │
│  │  │ 📊 품질 정보                                      │  │  │
│  │  │ - 최종 유사도: 95.61%                            │  │  │
│  │  │ - 시도 횟수: 2회                                 │  │  │
│  │  │ - 생성 시간: 15초                                │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  [⬅️ 이전: 스크립트 수정]  [다음: 영상 생성 ➡️]       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  💡 Tip: 음성이 마음에 들지 않으면 음성 선택을 변경하고      │
│      "재생성" 버튼을 클릭하세요.                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 컴포넌트 구조

```
/production
├── ProductionLayout (전체 레이아웃)
│   ├── ProgressBar (4단계 진행 상태)
│   ├── ProjectHeader (프로젝트명, 저장 버튼)
│   └── AgentPanel (현재 활성 에이전트)
│
├── WriterPanel (Step 1)
│   ├── GoogleSheetsConnector
│   ├── PersonaSelector
│   ├── PlatformSelector
│   ├── ScriptEditor (Monaco Editor)
│   └── NextButton → DirectorPanel
│
├── DirectorPanel (Step 2)
│   ├── ScriptPreview (자동 전달됨, 읽기 전용)
│   ├── VoiceSelector
│   │   ├── MyVoices (클론 목록)
│   │   ├── DefaultVoices (ElevenLabs 기본)
│   │   └── CloneVoiceButton
│   ├── AdvancedSettings (정확도, 재시도)
│   ├── AudioProgressTracker (실시간 진행)
│   ├── AudioPlayer (생성 완료 시)
│   ├── QualityMetrics (유사도, 시도 횟수)
│   └── NavigationButtons
│       ├── BackButton → WriterPanel
│       ├── RegenerateButton
│       └── NextButton → MarketerPanel
│
├── MarketerPanel (Step 3)
│   ├── VideoGenerationPanel
│   ├── ThumbnailGenerator
│   └── CaptionGenerator
│
└── DeploymentPanel (Step 4)
    ├── PlatformOptimizer (Cloudinary)
    ├── ScheduleManager
    └── AnalyticsDashboard
```

### 3.3 상태 관리 (React Context)

```typescript
// ProductionContext.tsx
interface ProductionState {
  projectId: string;
  currentStep: 'writer' | 'director' | 'marketer' | 'deployment';

  // Writer 데이터
  script: {
    raw: string;              // 원본 스크립트
    normalized: string;       // 정규화된 스크립트
    metadata: {
      hook: string;           // 훅 타이밍 (첫 3초)
      body: string;           // 본문
      cta: string;            // CTA
      duration: string;       // 예상 영상 길이
    };
    platform: 'youtube' | 'instagram' | 'tiktok';
    persona: string;
  };

  // Director 데이터
  audio: {
    taskId: string | null;
    status: 'idle' | 'generating' | 'success' | 'failed';
    voiceId: string;
    audioPath: string | null;
    similarity: number;
    attempts: number;
    progressStep: string;     // 현재 진행 단계
  };

  // Marketer 데이터
  video: {
    taskId: string | null;
    status: 'idle' | 'generating' | 'success' | 'failed';
    videoPath: string | null;
  };

  // Actions
  setScript: (script: string) => void;
  moveToNextStep: () => void;
  moveToPreviousStep: () => void;
  generateAudio: () => Promise<void>;
  regenerateAudio: () => Promise<void>;
}
```

---

## 🔧 4. 백엔드 API 개선안

### 4.1 현재 API 구조 문제점

```python
# 현재: 각 단계가 독립적
POST /api/v1/audio/generate        # 오디오만 생성
POST /api/v1/video/generate        # 영상만 생성
POST /api/v1/distribution/publish  # 배포만 수행
```

**문제점**:
- 단계 간 데이터 전달을 클라이언트가 담당
- 프로젝트 컨텍스트 관리 없음
- 중간 실패 시 복구 어려움

### 4.2 개선된 API 구조

#### **프로젝트 기반 워크플로우 API**

```python
# 새로운 API 구조

# 1. 프로젝트 생성
POST /api/v1/projects
Request:
{
  "name": "저시력자 마케팅 영상",
  "platform": "youtube",
  "persona": "친근한 여성"
}
Response:
{
  "project_id": "proj_abc123",
  "status": "created",
  "current_step": "writer"
}

# 2. 스크립트 저장 (Writer 완료)
PATCH /api/v1/projects/{project_id}/script
Request:
{
  "script": "### 훅\n여러분, 눈이 침침해서...",
  "auto_normalize": true
}
Response:
{
  "script": {
    "raw": "### 훅\n여러분...",
    "normalized": "여러분, 눈이 침침해서...",  # 메타데이터 제거됨
    "metadata": {
      "sections": ["hook", "body", "cta"],
      "duration": "2분 30초",
      "timings": {"hook": "3초"}
    }
  },
  "current_step": "director",
  "next_action": "/api/v1/projects/{project_id}/audio"
}

# 3. 오디오 생성 (Director)
POST /api/v1/projects/{project_id}/audio
Request:
{
  "voice_id": "rachel",
  "accuracy_threshold": 0.95,
  "max_attempts": 5
}
Response:
{
  "task_id": "task_xyz789",
  "status": "processing",
  "current_step": "director",
  "audio": {
    "status": "generating",
    "progress": 0.35,
    "current_phase": "stt_verification",
    "attempt": 2,
    "similarity": 0.923
  }
}

# 4. 프로젝트 상태 조회 (실시간 폴링)
GET /api/v1/projects/{project_id}
Response:
{
  "project_id": "proj_abc123",
  "name": "저시력자 마케팅 영상",
  "current_step": "director",
  "script": {...},
  "audio": {
    "status": "success",
    "audio_path": "/outputs/verified_audio_xyz.mp3",
    "similarity": 0.9561,
    "attempts": 2,
    "duration": 150.5
  },
  "video": null,
  "created_at": "2025-02-01T10:00:00Z",
  "updated_at": "2025-02-01T10:02:15Z"
}

# 5. 영상 생성 (자동으로 audio_path 사용)
POST /api/v1/projects/{project_id}/video
Request:
{
  "veo_prompt": "Professional presenter in modern studio",
  "lipsync_method": "heygen"
}
Response:
{
  "task_id": "task_video_456",
  "status": "processing",
  "current_step": "marketer"
}
```

#### **WebSocket 실시간 진행 상태 (선택)**

```python
# 더 나은 UX를 위한 WebSocket
WS /api/v1/projects/{project_id}/stream

# 서버 → 클라이언트 이벤트
{
  "event": "audio.progress",
  "data": {
    "phase": "tts_generation",
    "progress": 0.25,
    "message": "TTS 생성 중..."
  }
}

{
  "event": "audio.attempt",
  "data": {
    "attempt": 2,
    "max_attempts": 5,
    "similarity": 0.923,
    "threshold": 0.95,
    "message": "정확도 부족 (92.3%), 재생성 중..."
  }
}

{
  "event": "audio.completed",
  "data": {
    "audio_path": "/outputs/...",
    "final_similarity": 0.9561,
    "total_attempts": 2,
    "duration": 15.3
  }
}
```

### 4.3 데이터베이스 스키마

```python
# models/project.py
class Project(BaseModel):
    project_id: str
    user_id: str
    name: str
    platform: Platform

    # Writer 데이터
    script_raw: Optional[str]
    script_normalized: Optional[str]
    script_metadata: Optional[dict]

    # Director 데이터
    audio_task_id: Optional[str]
    audio_path: Optional[str]
    audio_voice_id: Optional[str]
    audio_similarity: Optional[float]
    audio_attempts: Optional[int]

    # Marketer 데이터
    video_task_id: Optional[str]
    video_path: Optional[str]

    # 상태 관리
    current_step: Step  # writer | director | marketer | deployment
    status: Status      # draft | in_progress | completed | failed

    created_at: datetime
    updated_at: datetime

    # Neo4j에 저장
    def save_to_neo4j(self):
        """
        (User)-[:OWNS]->(Project)-[:HAS_SCRIPT]->(Script)
                                  -[:HAS_AUDIO]->(Audio)
                                  -[:HAS_VIDEO]->(Video)
        """
        pass
```

---

## 🚀 5. 구현 로드맵

### Phase 1: 기초 인프라 (1주)

**목표**: 프로젝트 기반 API 구조 구축

**Tasks**:
- [ ] Project 모델 및 Neo4j 스키마 설계
- [ ] Project CRUD API 구현
- [ ] 기존 `/audio/generate`를 `/projects/{id}/audio`로 마이그레이션
- [ ] 세션 관리 (Redis 또는 Neo4j)

**API 엔드포인트**:
```
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}/script
POST   /api/v1/projects/{project_id}/audio
DELETE /api/v1/projects/{project_id}
```

### Phase 2: 통합 UI (2주)

**목표**: `/production` 단일 페이지 구현

**Tasks**:
- [ ] ProductionLayout 컴포넌트
- [ ] ProductionContext (React Context API)
- [ ] WriterPanel (스크립트 에디터)
- [ ] DirectorPanel (오디오 생성)
- [ ] 단계 간 자동 데이터 전달
- [ ] 자동 저장 (5초 간격)

**파일 구조**:
```
frontend/app/production/
├── page.tsx                 # 메인 페이지
├── layout.tsx               # 레이아웃
├── context/
│   └── ProductionContext.tsx
├── components/
│   ├── ProgressBar.tsx
│   ├── WriterPanel.tsx
│   ├── DirectorPanel.tsx
│   ├── AudioProgressTracker.tsx  # 기존 재사용
│   └── AudioPlayer.tsx
└── hooks/
    ├── useProject.ts
    └── useAutoSave.ts
```

### Phase 3: 스마트 스크립트 파싱 (3일)

**목표**: 메타데이터 자동 제거 및 타이밍 추출

**Tasks**:
- [ ] text_normalizer.py 개선
  - [ ] 마크다운 헤더 제거 (✅ 이미 구현됨)
  - [ ] "--- 예상 영상 길이: X" 패턴 제거
  - [ ] "(첫 X초)" 타이밍 정보 추출
  - [ ] CTA 구간 자동 마킹
- [ ] 정규화 결과를 Neo4j에 저장
- [ ] Director Agent에서 타이밍 정보 활용

**예시**:
```python
# Input
script = """
### 훅 (첫 3초)
여러분, 눈이 침침해서 스마트폰 글씨가 안 보인다고 포기하셨나요?

### 본문
이제 iPhone 저시력자 모드로 세상이 달라집니다.

### CTA
지금 바로 설정해보세요!

--- 예상 영상 길이: 2분 30초
--- 플랫폼: 유튜브 쇼츠
"""

# Output
{
  "normalized": "여러분, 눈이 침침해서 스마트폰 글씨가 안 보인다고 포기하셨나요? 이제 iPhone 저시력자 모드로 세상이 달라집니다. 지금 바로 설정해보세요!",
  "metadata": {
    "sections": [
      {"type": "hook", "timing": "3초", "text": "여러분, 눈이..."},
      {"type": "body", "text": "이제 iPhone..."},
      {"type": "cta", "text": "지금 바로..."}
    ],
    "duration": "2분 30초",
    "platform": "유튜브 쇼츠"
  }
}
```

### Phase 4: 실시간 피드백 (1주)

**목표**: WebSocket 기반 진행 상태 스트리밍

**Tasks**:
- [ ] FastAPI WebSocket 엔드포인트
- [ ] Celery 작업 진행률 이벤트 발행
- [ ] React에서 WebSocket 연결
- [ ] 실시간 진행 UI 업데이트
- [ ] 에러 발생 시 즉시 알림

**WebSocket 통신**:
```typescript
// frontend/app/production/hooks/useWebSocket.ts
const ws = new WebSocket(`ws://localhost:8000/api/v1/projects/${projectId}/stream`);

ws.onmessage = (event) => {
  const { event: eventType, data } = JSON.parse(event.data);

  switch (eventType) {
    case 'audio.progress':
      setProgress(data.progress);
      setPhase(data.phase);
      break;
    case 'audio.attempt':
      setAttempt(data.attempt);
      setSimilarity(data.similarity);
      break;
    case 'audio.completed':
      setAudioPath(data.audio_path);
      setStatus('success');
      break;
    case 'audio.failed':
      setError(data.error);
      setStatus('failed');
      break;
  }
};
```

### Phase 5: 영상 생성 통합 (2주)

**목표**: Director → Marketer 자동 연결

**Tasks**:
- [ ] MarketerPanel 컴포넌트
- [ ] `/projects/{id}/video` API
- [ ] Google Veo 통합
- [ ] HeyGen 립싱크 통합
- [ ] 영상 미리보기

### Phase 6: 최적화 및 UX 개선 (1주)

**목표**: 성능 및 사용성 향상

**Tasks**:
- [ ] 자동 저장 최적화 (debounce)
- [ ] 오프라인 모드 (IndexedDB)
- [ ] 키보드 단축키 (Cmd+S 저장, Cmd+Enter 다음 단계)
- [ ] 다크 모드
- [ ] 모바일 반응형
- [ ] 에러 복구 플로우
- [ ] 온보딩 튜토리얼

---

## 📊 6. 성공 지표 (KPI)

### 6.1 정량적 지표

| 지표 | 현재 (As-Is) | 목표 (To-Be) | 측정 방법 |
|-----|-------------|-------------|----------|
| **평균 작업 시간** | 3분 | 30초 | Logfire 추적 |
| **클릭 수** | 7회 | 2회 | 사용자 행동 분석 |
| **에러율** | 15% | 3% | 에러 로그 |
| **완료율** | 60% | 95% | 프로젝트 상태 |
| **사용자 만족도** | - | 4.5/5 | NPS 설문 |

### 6.2 정성적 지표

- **직관성**: 신규 사용자가 튜토리얼 없이 사용 가능
- **일관성**: 모든 단계에서 동일한 UI 패턴
- **신뢰성**: 중간 실패 시에도 데이터 손실 없음
- **반응성**: 모든 액션에 즉각적인 피드백

---

## 🎯 7. 우선순위 및 일정

### 즉시 시작 (Week 1-2)
1. ✅ Phase 3: 스크립트 메타데이터 제거 (가장 빠른 Quick Win)
   - text_normalizer.py에 패턴 추가
   - 3일 내 완료 가능
   - 즉시 TTS 품질 개선 체감

2. 🚀 Phase 1: 프로젝트 API 구조 (인프라 기반)
   - 다른 모든 작업의 기초
   - 1주 완료 목표

### 중기 (Week 3-4)
3. Phase 2: 통합 UI 구현
4. Phase 4: 실시간 피드백

### 장기 (Week 5-7)
5. Phase 5: 영상 생성 통합
6. Phase 6: 최적화

---

## 🔐 8. 리스크 및 대응 방안

### Risk 1: 백엔드 API 대규모 리팩토링
**영향**: 기존 `/audio` API를 사용하는 코드 중단
**대응**:
- 기존 API 유지하면서 새 API 병행 운영
- 점진적 마이그레이션 (Strangler Fig Pattern)
- 버전 관리 (`/v1/audio` → `/v2/projects`)

### Risk 2: 프론트엔드 상태 관리 복잡도
**영향**: 컴포넌트 간 데이터 동기화 어려움
**대응**:
- React Context + useReducer 사용
- 또는 Zustand 같은 경량 상태 관리 라이브러리
- 명확한 데이터 플로우 문서화

### Risk 3: WebSocket 연결 불안정
**영향**: 실시간 진행 상태 업데이트 실패
**대응**:
- Fallback: 기존 폴링 방식 유지
- 자동 재연결 로직
- WebSocket 실패 시 HTTP 폴링으로 전환

---

## 🎬 9. 영상 편집 UI/UX 컨셉: "90% AI 자동 생성 + 10% 사용자 미세 조정"

### 9.1 핵심 철학

**기존 영상 편집 툴의 문제점**:
- Adobe Premiere Pro, Final Cut Pro: 전문가용, 러닝커브 높음
- Canva, CapCut: 간단하지만 템플릿 제약
- 사용자가 모든 것을 직접 배치하고 타이밍 맞추고 편집해야 함

**OmniVibe Pro의 접근 방식**:
```
AI가 90% 자동 생성 → 사용자는 최종 10%만 미세 조정
```

**비유**:
- ❌ 백지에 그림 그리기 (기존 툴)
- ✅ AI가 그린 그림을 붓질 몇 번으로 완성 (OmniVibe Pro)

---

### 9.2 워크플로우: "AI-First Video Editor"

```
[Phase 1: AI 자동 생성 (90%)]
  ┌─────────────────────────────────────────────────────┐
  │ 🤖 AI가 자동으로 처리하는 것들                         │
  ├─────────────────────────────────────────────────────┤
  │ ✅ 스크립트 → 음성 생성 (Zero-Fault Loop)             │
  │ ✅ 음성 → 영상 생성 (Google Veo)                      │
  │ ✅ 립싱크 처리 (HeyGen)                               │
  │ ✅ 콘티별 타이밍 자동 설정                             │
  │    - 훅: 0-3초                                        │
  │    - 본문: 3초-2분 20초                               │
  │    - CTA: 2분 20초-2분 30초                           │
  │ ✅ 플랫폼별 자막 스타일 (유튜브/인스타/틱톡)            │
  │ ✅ 배경음악 자동 선택 및 볼륨 조절                     │
  │ ✅ 화면 전환 효과 (페이드/컷/와이프)                   │
  │ ✅ 썸네일 자동 생성 (3개 후보)                         │
  └─────────────────────────────────────────────────────┘
         ↓
  "1분 안에 완성된 영상 제공"
         ↓
[Phase 2: 사용자 미세 조정 (10%)]
  ┌─────────────────────────────────────────────────────┐
  │ 👤 사용자가 조정할 수 있는 것들 (선택 사항)            │
  ├─────────────────────────────────────────────────────┤
  │ 🎬 콘티별 조정 (타임라인 기반)                         │
  │    ├── 구간별 영상 클립 교체                          │
  │    ├── 자막 위치/스타일 변경                          │
  │    ├── 배경음악 볼륨 조절                             │
  │    ├── 화면 전환 효과 변경                            │
  │    └── 특정 구간 삭제/추가                            │
  │                                                       │
  │ 🎨 스타일 프리셋 (원클릭 적용)                         │
  │    ├── "다이나믹 유튜브 쇼츠"                         │
  │    ├── "감성 인스타 릴스"                             │
  │    ├── "바이럴 틱톡"                                  │
  │    └── "프로페셔널 브이로그"                          │
  │                                                       │
  │ 📸 썸네일 선택 (AI 생성 3개 중 선택 또는 커스텀)       │
  └─────────────────────────────────────────────────────┘
```

---

### 9.3 UI 설계: "타임라인 기반 콘티 에디터"

#### **전체 레이아웃**

```
┌────────────────────────────────────────────────────────────────┐
│  OmniVibe Pro Video Editor              [미리보기] [내보내기] │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────────────────────┐   │
│  │   영상 미리보기   │  │  콘티 (Storyboard)                │   │
│  │                  │  │                                    │   │
│  │  ┌────────────┐  │  │  📌 훅 (0-3초)                    │   │
│  │  │            │  │  │  "여러분, 눈이 침침해서..."        │   │
│  │  │   [영상]   │  │  │  ┌──────────────────────────┐   │   │
│  │  │   재생중   │  │  │  │ [썸네일 이미지]            │   │   │
│  │  │            │  │  │  │ 캐릭터: 친근한 여성        │   │   │
│  │  └────────────┘  │  │  │ 배경: 현대적 스튜디오      │   │   │
│  │                  │  │  │ 자막: 화면 하단            │   │   │
│  │  ▶️ ━━━●──────  │  │  │ BGM: 밝은 팝 (20%)        │   │   │
│  │  00:05 / 02:30  │  │  └──────────────────────────┘   │   │
│  │                  │  │  [🔄 클립 교체] [✏️ 자막 수정]   │   │
│  └──────────────────┘  │                                    │   │
│                         │  📌 본문 (3초-2분20초)            │   │
│  ┌──────────────────┐  │  "이제 iPhone 저시력자 모드로..." │   │
│  │  빠른 조정        │  │  ┌──────────────────────────┐   │   │
│  │                  │  │  │ [썸네일 이미지]            │   │   │
│  │  🎨 스타일       │  │  │ 화면전환: 페이드            │   │   │
│  │  ( ) 유튜브 쇼츠 │  │  │ 자막 강조: "저시력자 모드" │   │
│  │  (●) 인스타 릴스 │  │  │ BGM: 유지 (20%)           │   │   │
│  │  ( ) 틱톡        │  │  └──────────────────────────┘   │   │
│  │                  │  │  [🔄 클립 교체] [✏️ 자막 수정]   │   │
│  │  🎵 배경음악     │  │                                    │   │
│  │  [밝은 팝 ▼]     │  │  📌 CTA (2분20초-2분30초)         │   │
│  │  볼륨: 20%       │  │  "지금 바로 설정해보세요!"         │   │
│  │  ●─────────────  │  │  ┌──────────────────────────┐   │   │
│  │                  │  │  │ [썸네일 이미지]            │   │   │
│  │  📐 종횡비       │  │  │ CTA 버튼 오버레이          │   │   │
│  │  ( ) 16:9 가로   │  │  │ 자막: 중앙 크게            │   │   │
│  │  (●) 9:16 세로   │  │  │ BGM: 페이드아웃            │   │   │
│  │  ( ) 1:1 정사각  │  │  └──────────────────────────┘   │   │
│  │                  │  │  [🔄 클립 교체] [✏️ 자막 수정]   │   │
│  └──────────────────┘  └──────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  🎬 타임라인 (Timeline)                                     ││
│  ├────────────────────────────────────────────────────────────┤│
│  │  00:00 ────────────── 01:00 ────────────── 02:00 ── 02:30 ││
│  │                                                              ││
│  │  🎥 Video  ┌───────┐┌─────────────────────┐┌──────┐       ││
│  │            │  훅   ││       본문          ││ CTA  │       ││
│  │            └───────┘└─────────────────────┘└──────┘       ││
│  │                                                              ││
│  │  🎙️ Audio  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       ││
│  │                                                              ││
│  │  💬 자막   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       ││
│  │                                                              ││
│  │  🎵 BGM    ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ (20%)        ││
│  │                                                              ││
│  │  [재생 ▶️] [정지 ⏸️] [← 되감기] [앞으로 →]                ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  💡 Tip: AI가 자동으로 최적화한 영상입니다.                     │
│      마음에 들지 않는 부분만 클릭해서 수정하세요!               │
└────────────────────────────────────────────────────────────────┘
```

---

### 9.4 핵심 기능: "콘티별 미세 조정"

#### **조정 가능한 요소 (구간별)**

```typescript
interface VideoSection {
  id: string;
  type: 'hook' | 'body' | 'cta';
  startTime: number;      // 시작 시간 (초)
  endTime: number;        // 종료 시간 (초)
  script: string;         // 스크립트 텍스트

  // AI가 자동 생성한 것들 (사용자가 변경 가능)
  videoClip: {
    url: string;          // Google Veo 생성 영상
    character: string;    // 캐릭터 스타일
    background: string;   // 배경 설정
    cameraAngle: string;  // 카메라 앵글
    alternatives: string[]; // AI가 생성한 대체 영상 (3개)
  };

  subtitle: {
    text: string;
    position: 'top' | 'center' | 'bottom';
    style: 'default' | 'bold' | 'neon' | 'minimal';
    fontSize: number;
    color: string;
    animation: 'none' | 'fade' | 'slide' | 'bounce';
  };

  transition: {
    type: 'cut' | 'fade' | 'wipe' | 'zoom' | 'slide';
    duration: number;     // 전환 시간 (초)
  };

  bgm: {
    volume: number;       // 0-100
    fadeIn: boolean;
    fadeOut: boolean;
  };

  effects: {
    zoom: boolean;        // 특정 순간 줌인
    highlight: string[];  // 강조할 키워드
    overlay: string | null; // CTA 버튼 오버레이
  };
}
```

#### **예시: 훅 구간 조정**

```
사용자가 "훅 (0-3초)" 카드를 클릭
   ↓
[편집 패널 열림]
┌─────────────────────────────────────────┐
│ 📌 훅 구간 편집 (0-3초)                  │
├─────────────────────────────────────────┤
│                                           │
│ 🎥 영상 클립                              │
│ ┌──────┐ ┌──────┐ ┌──────┐              │
│ │ 옵션1 │ │ 옵션2 │ │ 옵션3 │ (AI 생성)   │
│ │  ✓   │ │      │ │      │              │
│ └──────┘ └──────┘ └──────┘              │
│ [+ 새 영상 생성 (Google Veo)]            │
│                                           │
│ 💬 자막 스타일                            │
│ ( ) 기본  (●) 굵게  ( ) 네온  ( ) 미니멀 │
│ 위치: [하단 ▼]  크기: [32px ▼]           │
│                                           │
│ 🎨 화면 전환                              │
│ ( ) 컷  (●) 페이드  ( ) 와이프  ( ) 줌   │
│ 전환 시간: [0.5초 ▼]                     │
│                                           │
│ 🎵 배경음악                               │
│ 볼륨: [20% ●─────────────]               │
│ ☑ 페이드인  ☐ 페이드아웃                 │
│                                           │
│ [취소] [미리보기] [적용]                  │
└─────────────────────────────────────────┘
```

---

### 9.5 "스타일 프리셋" (원클릭 최적화)

```
사용자가 플랫폼 선택
   ↓
AI가 해당 플랫폼 최적 설정 자동 적용
```

#### **프리셋 예시**

```typescript
const stylePresets = {
  // 1. 유튜브 쇼츠 최적화
  youtubeShorts: {
    aspectRatio: '9:16',
    subtitle: {
      position: 'bottom',
      style: 'bold',
      fontSize: 48,
      animation: 'bounce'
    },
    transition: 'zoom',
    bgmVolume: 15,
    effects: {
      zoom: true,           // 역동적인 줌인/줌아웃
      highlightKeywords: true  // 주요 키워드 강조
    }
  },

  // 2. 인스타 릴스 최적화
  instagramReels: {
    aspectRatio: '9:16',
    subtitle: {
      position: 'top',
      style: 'neon',
      fontSize: 40,
      animation: 'fade'
    },
    transition: 'fade',
    bgmVolume: 25,          // 인스타는 음악 중요
    effects: {
      overlay: 'aesthetic',  // 감성적 필터
      colorGrade: 'warm'
    }
  },

  // 3. 틱톡 바이럴
  tiktokViral: {
    aspectRatio: '9:16',
    subtitle: {
      position: 'center',
      style: 'bold',
      fontSize: 56,          // 크고 눈에 띄게
      animation: 'slide'
    },
    transition: 'cut',       // 빠른 컷 편집
    bgmVolume: 30,          // 틱톡은 음악이 핵심
    effects: {
      fastCuts: true,        // 3초마다 씬 전환
      trendingEffects: true  // 트렌디한 이펙트
    }
  },

  // 4. 프로페셔널 (일반 유튜브)
  professional: {
    aspectRatio: '16:9',
    subtitle: {
      position: 'bottom',
      style: 'minimal',
      fontSize: 36,
      animation: 'none'
    },
    transition: 'fade',
    bgmVolume: 10,          // 배경음악 낮게
    effects: {
      clean: true,           // 깔끔한 편집
      professionalGrade: true
    }
  }
};
```

#### **UI에서 사용**

```jsx
<div className="style-presets">
  <h3>🎨 빠른 스타일 적용</h3>
  <div className="preset-buttons">
    <button onClick={() => applyPreset('youtubeShorts')}>
      📱 유튜브 쇼츠
      <small>역동적, 줌인/줌아웃</small>
    </button>

    <button onClick={() => applyPreset('instagramReels')}>
      💫 인스타 릴스
      <small>감성적, 네온 자막</small>
    </button>

    <button onClick={() => applyPreset('tiktokViral')}>
      🔥 틱톡 바이럴
      <small>빠른 컷, 트렌디</small>
    </button>

    <button onClick={() => applyPreset('professional')}>
      👔 프로페셔널
      <small>깔끔, 미니멀</small>
    </button>
  </div>
</div>
```

---

### 9.6 구현 우선순위

#### **Phase 1: MVP (2주)**
- [ ] 타임라인 뷰어 (재생만 가능)
- [ ] 콘티별 섹션 카드 UI
- [ ] 기본 조정 기능
  - [ ] 자막 위치 변경
  - [ ] BGM 볼륨 조절
  - [ ] 클립 교체 (AI 생성 3개 중 선택)

#### **Phase 2: 고급 편집 (3주)**
- [ ] 타임라인 편집 (드래그 앤 드롭)
- [ ] 구간 추가/삭제
- [ ] 화면 전환 효과 변경
- [ ] 자막 스타일 커스터마이징
- [ ] 스타일 프리셋 적용

#### **Phase 3: 프로 기능 (4주)**
- [ ] 키프레임 애니메이션
- [ ] 특정 순간 줌인/줌아웃
- [ ] 오버레이 (CTA 버튼, 텍스트)
- [ ] 색보정 (Color Grading)
- [ ] A/B 테스트 (버전 비교)

---

### 9.7 기술 스택

```
Frontend (Video Editor)
├── React + TypeScript
├── Fabric.js / Konva.js (캔버스 기반 편집)
├── WaveSurfer.js (오디오 파형 시각화)
├── Video.js (영상 플레이어)
└── Framer Motion (애니메이션)

Backend (Video Processing)
├── FFmpeg (영상 편집 엔진)
├── Celery (렌더링 작업 큐)
├── Cloudinary (영상 변환 및 최적화)
└── Neo4j (사용자 편집 패턴 학습)
```

---

### 9.8 사용자 경험 시나리오

**기존 영상 편집 툴 (Adobe Premiere Pro)**:
```
1. 프로젝트 생성 (1분)
2. 영상 클립 임포트 (2분)
3. 타임라인에 배치 (5분)
4. 자막 일일이 입력 및 타이밍 맞추기 (15분)
5. 배경음악 찾아서 추가 (5분)
6. 화면 전환 효과 추가 (10분)
7. 렌더링 (5분)
──────────────────────────
총 소요 시간: 43분
```

**OmniVibe Pro (90% AI 자동)**:
```
1. 스크립트 작성 (구글 시트 또는 Writer Agent) - 이미 완료됨
2. [다음] 버튼 클릭 → AI가 자동 영상 생성 (1분 대기)
3. 미리보기 확인
   - 마음에 들면: [내보내기] 클릭 → 완료
   - 수정 필요 시: 콘티별로 클릭해서 조정 (2-3분)
4. [내보내기] 클릭
──────────────────────────
총 소요 시간: 3-4분 (90% 감소!)
```

---

### 9.9 수익화 모델

#### **Freemium 구조**

| 기능 | Free | Pro ($29/월) | Enterprise ($99/월) |
|-----|------|-------------|-------------------|
| AI 자동 영상 생성 | 5개/월 | 무제한 | 무제한 |
| 콘티별 미세 조정 | ✅ | ✅ | ✅ |
| 스타일 프리셋 | 2개 | 전체 | 전체 + 커스텀 |
| 고급 편집 (키프레임) | ❌ | ✅ | ✅ |
| 워터마크 제거 | ❌ | ✅ | ✅ |
| 팀 협업 | ❌ | 3명 | 무제한 |
| API 액세스 | ❌ | ❌ | ✅ |

---

## 💡 10. 추가 개선 아이디어

### 10.1 AI 기반 스크립트 제안
- Writer Agent가 스크립트 작성 중 실시간 제안
- "이 부분은 CTA로 이동하는 게 좋을 것 같아요"

### 10.2 A/B 테스트 자동화
- 같은 스크립트로 음성 2종 생성
- 사용자가 선택하면 Neo4j에 선호도 저장
- 다음 프로젝트에서 자동 반영

### 10.3 협업 기능
- 여러 사용자가 동시에 스크립트 편집 (Google Docs처럼)
- 댓글 및 피드백 시스템

### 10.4 템플릿 라이브러리
- "유튜브 쇼츠 템플릿"
- "인스타 릴스 템플릿"
- 빠른 시작을 위한 스크립트 예시

---

## 📝 10. 결론

### 핵심 개선 사항 요약

1. **단일 페이지 워크플로우** (`/production`)
   - URL 수동 입력 제거
   - 복사/붙여넣기 제거
   - 자동 데이터 전달

2. **스마트 스크립트 파싱**
   - 메타데이터 자동 제거
   - 타이밍 정보 추출
   - Director Agent 활용

3. **실시간 피드백**
   - WebSocket 진행 상태
   - 단계별 애니메이션
   - 즉각적인 에러 알림

4. **프로젝트 기반 API**
   - 컨텍스트 유지
   - 중간 저장 및 복구
   - 명확한 상태 관리

### 기대 효과

- **작업 시간 83% 단축** (3분 → 30초)
- **클릭 수 70% 감소** (7회 → 2회)
- **에러율 80% 개선** (15% → 3%)
- **완료율 58% 증가** (60% → 95%)

### 다음 액션

**즉시 시작 가능한 작업**:
1. text_normalizer.py 개선 (메타데이터 제거 패턴 추가)
2. Project 모델 및 Neo4j 스키마 설계
3. ProductionContext 구조 설계

대표님, 이 제안서를 기반으로 어떤 부분부터 시작하시겠습니까?

추천 순서는:
1. **Phase 3** (스크립트 파싱) - 가장 빠른 Quick Win, 3일 완료
2. **Phase 1** (프로젝트 API) - 인프라 기반, 1주 완료
3. **Phase 2** (통합 UI) - 사용자 체감 개선, 2주 완료
