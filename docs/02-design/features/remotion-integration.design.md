# Design: remotion-integration (v1.1 — Reverse-Engineered)

> 이 문서는 구현 완료된 Remotion 통합(v1.1, 97% match rate 33/34)을 기반으로 역설계한 Design 문서입니다.

## 1. Architecture Overview

### Studio ↔ Remotion Player 통합 구조

StudioPreview 컴포넌트가 `@remotion/player`의 `<Player>` 를 직접 임베드하여 실시간 미리보기를 제공합니다.
ScriptBlock 배열이 존재하면 Remotion Player를, 없으면 기존 "Neural Rendering" 대기 UI를 표시하는 조건부 렌더링 방식입니다.

```
┌─────────────────────────────────────────────────┐
│  Studio Page (app/studio/page.tsx)               │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  StudioPreview.tsx                           │ │
│  │                                               │ │
│  │  blocks.length > 0?                          │ │
│  │  ├─ YES → <Player component={Template}       │ │
│  │  │         inputProps={blocks, audioUrl, ...} │ │
│  │  │         fps={30} controls />               │ │
│  │  │                                            │ │
│  │  └─ NO  → Neural Rendering 대기 UI            │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 핵심 설계 결정
- **FPS**: 전 포맷 30fps 고정
- **Duration 계산**: `blocks.reduce(max, b.startTime + b.duration) * 30` 프레임 (Root.tsx의 `calculateMetadata` 동일 로직)
- **Format 선택**: `StudioPreviewProps.format` prop으로 youtube/instagram/tiktok 간 전환
- **Template 분기**: `TEMPLATE_MAP` 상수로 format → Template 컴포넌트 매핑

---

## 2. Scene Components

### 2.1 구현된 씬 컴포넌트 (6종)

| 씬 | 파일 | 용도 | 핵심 애니메이션 |
|-----|------|------|-----------------|
| **HookScene** | `remotion/scenes/HookScene.tsx` | 오프닝 훅, 시선 포착 | 단어별 stagger spring (3프레임 간격), `translateY(40→0)` |
| **IntroScene** | `remotion/scenes/IntroScene.tsx` | 로고/브랜드 소개 | 로고 spring scale, 텍스트 delayed fadeIn (15→30프레임) |
| **BodyScene** | `remotion/scenes/BodyScene.tsx` | 본문 내용 전달 | Ken Burns zoom (1.0→1.1), 단어별 stagger fade |
| **CTAScene** | `remotion/scenes/CTAScene.tsx` | Call-to-Action | 버튼 pulse loop (30프레임 주기), 화살표 bounce (20프레임 주기) |
| **OutroScene** | `remotion/scenes/OutroScene.tsx` | 엔딩, 구독/좋아요 유도 | 로고 spring → 채널명 fade → 액션 버튼 순차 등장, 마지막 0.5초 fadeOut |
| **SlideScene** | `remotion/scenes/SlideScene.tsx` | PDF 슬라이드 프레젠테이션 | Ken Burns (1.0→1.03), 슬라이드 번호 배지, WordSubtitle 컴포넌트 |

### 2.2 SceneByType 라우터

모든 Template(YouTube/Instagram/TikTok)이 동일한 `SceneByType` 분기 함수를 사용합니다:

```typescript
switch (block.type) {
  case 'hook':  → HookScene
  case 'intro': → IntroScene
  case 'body':  → BodyScene
  case 'cta':   → CTAScene
  case 'outro': → OutroScene
  default:      → BodyScene (fallback)
}
```

### 2.3 공통 Props 인터페이스

```typescript
interface ScriptBlock {
  id?: number;
  type: 'hook' | 'intro' | 'body' | 'cta' | 'outro';
  text: string;
  startTime: number;  // seconds
  duration: number;    // seconds
  backgroundUrl?: string;
  animation?: 'fadeIn' | 'slideInUp' | 'slideInLeft' | 'zoomIn';
  fontSize?: number;
  textColor?: string;
  textAlign?: 'left' | 'center' | 'right';
}

interface BrandingConfig {
  logo: string;
  primaryColor: string;        // default: '#00A1E0'
  secondaryColor?: string;
  fontFamily?: string;          // default: 'Inter, sans-serif'
}
```

---

## 3. Audio Synchronization

### 3.1 전체 오디오 동기화

Template 레벨에서 `<Audio src={audioUrl} />` 를 최상위에 배치하여 전체 오디오 트랙을 재생합니다.
각 ScriptBlock의 `startTime`과 `duration`이 `<Sequence from={startTime * 30} durationInFrames={duration * 30}>` 으로 매핑되어 씬과 오디오가 프레임 단위로 동기화됩니다.

### 3.2 Whisper Word-level Timestamp (SlideScene)

SlideScene에서 `WordTimestamp[]` 데이터를 활용한 단어 단위 자막 하이라이트를 구현합니다:

```typescript
interface WordTimestamp {
  word: string;
  start: number;  // 절대 시간(초)
  end: number;
}
```

`WordSubtitle` 컴포넌트가 현재 프레임을 초 단위로 변환한 뒤 `words.findIndex()` 로 현재 발화 중인 단어를 감지하고, 해당 단어만 `primaryColor` + `bold` 로 강조 표시합니다.

### 3.3 타이밍 매핑 흐름

```
Whisper STT Output
  └→ word-level timestamps [{word, start, end}, ...]
       └→ SlideBlock.wordTimestamps에 주입
            └→ WordSubtitle 컴포넌트
                 └→ frame / fps + slideStartTime = currentSecond
                      └→ 현재 단어 하이라이트
```

---

## 4. Backend Rendering Pipeline

### 4.1 이중 API 구조

두 개의 렌더링 API 라우터가 공존합니다:

| 라우터 | 경로 | 용도 |
|--------|------|------|
| `render.py` | `/api/v1/render/*` | 멀티포맷 동시 렌더링 (formats 배열 기반) |
| `remotion.py` | `/api/v1/remotion/*` | Director Agent 연동 렌더링 (storyboard_blocks 기반) |

### 4.2 렌더링 파이프라인 (render.py 경로)

```
POST /render/start
  └→ render_video_task.delay(request)        [Celery]
       └→ for fmt in formats:
            ├→ self.update_state(PROGRESS)    [Celery 상태]
            ├→ _sync_broadcast(ws)            [WebSocket push]
            ├→ render_video_subprocess(...)    [npx remotion render]
            │    └→ Props JSON → tmpfile → subprocess
            │         └→ npx remotion render remotion/Root.tsx {id} {output} --props={file}
            │              └→ timeout: 300초
            └→ upload_to_cloudinary(...)       [CDN 업로드]
                 └→ resource_type="video", public_id="omnivibe/{task_id}/{fmt}"
```

### 4.3 렌더링 파이프라인 (remotion.py 경로)

```
POST /remotion/render
  └→ render_video_with_remotion_task.delay(...)    [Celery, max_retries=2]
       ├→ RemotionService.convert_storyboard_to_props(...)
       │    └→ storyboard_blocks → scenes[] (startTime 누적 계산)
       │    └→ PLATFORM_COMPOSITIONS 기반 해상도/코덱/비트레이트 설정
       └→ RemotionService.render_video_with_remotion(...)
            └→ subprocess + Cloudinary upload + WebSocket progress
```

### 4.4 추가 엔드포인트

| 엔드포인트 | 메서드 | 기능 |
|------------|--------|------|
| `/remotion/compositions` | GET | 사용 가능한 Composition 목록 |
| `/remotion/validate` | GET | Remotion CLI 설치 상태 검증 |
| `/remotion/batch-render` | POST | 여러 영상 동시 렌더링 |
| `/remotion/convert-props` | POST | Storyboard → Props 변환만 (렌더링 없이) |
| `/render/{task_id}/status` | GET | Celery 태스크 상태 조회 |
| `/render/{task_id}/result` | GET | 렌더링 결과 URL 조회 |

### 4.5 Pydantic Models (`backend/app/models/render.py`)

```python
VideoFormat    = youtube | instagram | tiktok
RenderQuality  = low | medium | high
ScriptBlockData  → id, type, text, startTime, duration, backgroundUrl, animation, fontSize, textColor, textAlign
BrandingData     → logo, primaryColor, secondaryColor, fontFamily
RenderRequest    → composition_id, blocks[], audio_url, branding, quality, formats[]
RenderStatus     → task_id, status, progress, format, output_url, error
RenderResult     → task_id, results{fmt→url}, total_duration
```

---

## 5. Multi-Format Support

### 5.1 Frontend Compositions (Root.tsx)

| Composition ID | Template | Width | Height | Aspect Ratio |
|----------------|----------|-------|--------|--------------|
| `youtube` | YouTubeTemplate | 1920 | 1080 | 16:9 |
| `instagram` | InstagramTemplate | 1080 | 1350 | 4:5 |
| `tiktok` | TikTokTemplate | 1080 | 1920 | 9:16 |

### 5.2 Backend Platform Compositions (remotion_service.py)

| Platform | Width | Height | Codec | Video Bitrate | Audio Bitrate |
|----------|-------|--------|-------|---------------|---------------|
| YouTube | 1920 | 1080 | h264 | 8M | 192k |
| Instagram | 1080 | 1350 | h264 | 5M | 128k |
| TikTok | 1080 | 1920 | h264 | 4M | 128k |
| Facebook | 1280 | 720 | h264 | 6M | 128k |

### 5.3 Template별 로고 워터마크 배치

| Template | 로고 위치 | 크기 | 불투명도 |
|----------|-----------|------|----------|
| YouTube | 우측 하단 (padding: 40px) | 120px | 0.8 |
| Instagram | 상단 중앙 (padding: 30px) | 100px | 0.9 |
| TikTok | 하단 중앙 (paddingBottom: 120px) | 80px | 0.85 |

---

## 6. Data Flow Diagram

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Director    │     │  Writer Agent    │     │  ElevenLabs TTS    │
│  Agent       │────→│  (Script)        │────→│  + Whisper STT     │
└──────┬───────┘     └──────────────────┘     └────────┬───────────┘
       │                                                │
       │ storyboard_blocks[]                           │ audioUrl
       │ + campaign_concept                            │ + wordTimestamps[]
       │                                                │
       ▼                                                ▼
┌──────────────────────────────────────────────────────────────┐
│  RemotionService.convert_storyboard_to_props()               │
│  → scenes[], branding, audio, metadata                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
   ┌─────────────────┐      ┌──────────────────────┐
   │  Frontend        │      │  Backend Celery       │
   │  @remotion/player│      │  npx remotion render  │
   │  (실시간 미리보기) │      │  (MP4 출력)           │
   └─────────────────┘      └──────────┬───────────┘
                                        │
                           ┌────────────┴────────────┐
                           │                         │
                           ▼                         ▼
                  ┌─────────────────┐     ┌──────────────────┐
                  │  Local File     │     │  Cloudinary CDN  │
                  │  /tmp/renders/  │     │  omnivibe/{id}/  │
                  └─────────────────┘     └──────────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │  WebSocket Push  │
                                          │  진행률 + 결과 URL │
                                          └──────────────────┘
```

---

## 7. File Structure

### Frontend (Remotion)

```
frontend/
├── remotion/
│   ├── Root.tsx                          # RemotionRoot: 3개 Composition 등록
│   ├── types.ts                          # ScriptBlock, BrandingConfig, VideoTemplateProps,
│   │                                     #   RenderConfig, WordTimestamp
│   ├── templates/
│   │   ├── YouTubeTemplate.tsx           # 1920x1080, 로고 우측하단
│   │   ├── InstagramTemplate.tsx         # 1080x1350, 로고 상단중앙
│   │   └── TikTokTemplate.tsx            # 1080x1920, 로고 하단중앙
│   └── scenes/
│       ├── index.ts                      # barrel export (5종, SlideScene 제외)
│       ├── HookScene.tsx                 # 단어별 stagger spring
│       ├── IntroScene.tsx                # 로고 spring + 텍스트 fade
│       ├── BodyScene.tsx                 # Ken Burns + 단어별 stagger fade
│       ├── CTAScene.tsx                  # pulse 버튼 + bounce 화살표
│       ├── OutroScene.tsx                # 순차 등장 + fadeOut
│       └── SlideScene.tsx                # PDF 슬라이드용, WordSubtitle 내장
│
├── components/studio/
│   └── StudioPreview.tsx                 # @remotion/player <Player> 임베드
│
└── package.json                          # remotion, @remotion/player 의존성
```

### Backend (Rendering Pipeline)

```
backend/app/
├── api/v1/
│   ├── render.py                         # /render/start, /render/{id}/status, /render/{id}/result
│   └── remotion.py                       # /remotion/render, /remotion/status, /remotion/compositions,
│                                         #   /remotion/validate, /remotion/batch-render, /remotion/convert-props
├── models/
│   └── render.py                         # VideoFormat, RenderQuality, ScriptBlockData,
│                                         #   BrandingData, RenderRequest, RenderStatus, RenderResult
├── services/
│   └── remotion_service.py               # RemotionService: props 변환, 렌더링 실행,
│                                         #   PLATFORM_COMPOSITIONS 설정
└── tasks/
    ├── render_tasks.py                   # render_video_task (멀티포맷), upload_to_cloudinary,
    │                                     #   render_video_subprocess, WebSocket broadcast 헬퍼
    └── video_tasks.py                    # render_video_with_remotion_task, validate_remotion_setup_task,
                                          #   batch_render_videos_task
```

---

## 8. 미구현 항목 (1/34)

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 34 | SlideScene barrel export | 미포함 | `scenes/index.ts`에서 SlideScene은 export하지 않음 (독립 사용 전용) |

---

**문서 버전**: 1.1 (Reverse-Engineered)
**작성 기준**: 2026-03-25
**구현 일치율**: 97% (33/34)
