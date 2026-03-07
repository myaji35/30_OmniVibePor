# Design: vrew-videogen-pipeline

> Plan 문서: `docs/01-plan/features/vrew-videogen-pipeline.plan.md`

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                    영상 제작 진입 경로 (2가지 병행)                       │
├─────────────────────────────┬───────────────────────────────────────┤
│  경로 A — 인앱 편집기          │  경로 B — VIDEOGEN Claude Code Skill  │
│                             │                                       │
│  스튜디오 UI                  │  input/dubbing.mp3                    │
│    └─ TTS (ElevenLabs)      │  input/subtitles.srt                  │
│    └─ STT (Whisper)         │         │                             │
│    └─ SubtitleTokens        │         ▼                             │
│    └─ AI 소스 (Pexels/Kling) │  SKILL.md 지시서 실행                   │
│         │                   │    └─ scene-analyzer.ts               │
│         ▼                   │    └─ layout-selector.ts              │
│  Remotion SceneRenderer     │    └─ remotion-codegen.ts             │
│         │                   │         │                             │
│         ▼                   │         ▼                             │
│  output MP4                 │  output/final_{ts}.mp4                │
└─────────────────────────────┴───────────────────────────────────────┘
                  ↓ (공통 출구)
         REMOTION_SHOWCASE 템플릿 등록 → 갤러리 노출
```

---

## 2. 경로 B 상세 설계 — VIDEOGEN Claude Code Skill

### 2-A. 파일 구조

```
.claude/skills/videogen/
  ├── SKILL.md                    # Claude Code 실행 지시서 (진입점)
  ├── scene-analyzer.ts           # SRT 파싱 → scenes.json
  ├── layout-selector.ts          # 씬 내용 분석 → 레이아웃 결정
  ├── remotion-codegen.ts         # scenes.json → Remotion 컴포넌트 생성
  ├── templates/                  # 씬 타입별 Remotion 베이스 컴포넌트
  │     ├── TextCenter.tsx        # 중앙 대형 텍스트
  │     ├── Infographic.tsx       # 카운터/차트 중앙집중
  │     ├── ListReveal.tsx        # 목록 순차 등장
  │     ├── TextImage.tsx         # 텍스트 + 이미지 분할
  │     ├── GraphFocus.tsx        # 그래프/데이터 중앙 배치
  │     ├── SplitScreen.tsx       # 2분할 비교
  │     └── FullVisual.tsx        # 전체 배경 + 자막 오버레이
  └── styles/
        └── monoDark.ts           # 글로벌 디자인 토큰

videogen/
  ├── input/
  │     ├── dubbing.mp3           # 더빙 오디오 (필수)
  │     └── subtitles.srt         # 자막 파일 (필수)
  ├── workspace/                  # 생성 코드 임시 저장
  │     ├── scenes.json
  │     └── src/
  │           ├── compositions/
  │           │     └── GeneratedVideo.tsx
  │           └── scenes/
  │                 ├── Scene1.tsx
  │                 ├── Scene2.tsx
  │                 └── ...
  └── output/
        ├── preview_{timestamp}.mp4    # DEV_MODE 검증용
        └── final_{timestamp}.mp4     # 최종 결과
```

---

### 2-B. SKILL.md 설계 (Claude Code 지시서)

```markdown
# VIDEOGEN Skill — Claude Code 실행 지시서

## 사전 확인
1. `videogen/input/dubbing.mp3` 존재 확인
2. `videogen/input/subtitles.srt` 존재 확인
3. 없으면 에러 메시지 출력 후 중단

## 실행 순서

### Step 1: SRT 분석
`npx ts-node .claude/skills/videogen/scene-analyzer.ts`
→ `videogen/workspace/scenes.json` 생성
→ 씬 수, 총 자막 수, 총 재생시간 출력

### Step 2: 레이아웃 결정
`npx ts-node .claude/skills/videogen/layout-selector.ts`
→ 각 씬에 layout 필드 추가된 scenes.json 업데이트
→ 씬별 레이아웃 배정 결과 출력

### Step 3: Remotion 코드 생성
`npx ts-node .claude/skills/videogen/remotion-codegen.ts`
→ `videogen/workspace/src/` 하위 컴포넌트 생성

### Step 4: 검증 렌더 (DEV_MODE)
`cd videogen/workspace && DEV_MODE=true npx remotion render`
→ `videogen/output/preview_{timestamp}.mp4` 생성
→ 각 씬 우상단에 "SCENE N" 오버레이 확인

### Step 5: 검증
- preview MP4를 열어 씬 번호와 레이아웃 확인
- 오류 씬 발견 시: layout-selector.ts 수정 후 Step 3으로 복귀
- 모든 씬 정상이면 Step 6 진행

### Step 6: 최종 렌더
`cd videogen/workspace && DEV_MODE=false npx remotion render`
→ `videogen/output/final_{timestamp}.mp4` 저장
→ 완료 보고: 총 씬 수, 재생시간, 파일 크기

## 디자인 원칙 (반드시 준수)
- 모노 다크 테마 (`styles/monoDark.ts` 참조)
- 인포그래픽: 핵심 객체 화면 중앙 집중
- 씬 내 자막 전환: 점진적 fadeIn + slideUp
- 한 씬에 하나의 핵심 메시지
```

---

### 2-C. scene-analyzer.ts 설계

```typescript
// 입력: videogen/input/subtitles.srt
// 출력: videogen/workspace/scenes.json

interface SubtitleToken {
  index: number
  startMs: number
  endMs: number
  text: string
}

interface Scene {
  id: number
  startMs: number
  endMs: number
  subtitles: SubtitleToken[]
  layout: string        // layout-selector가 채움
  contentType: string   // 'hook' | 'intro' | 'body' | 'cta'
  durationFrames: number // 30fps 기준
}

// 씬 경계 판단 기준
const SCENE_GAP_THRESHOLD_MS = 1500  // 자막 간 gap > 1.5초 → 씬 분리

// contentType 자동 추론
// - 첫 씬 → 'hook'
// - 마지막 씬 → 'cta'
// - 중간 씬 → 'body'
// - 시간 < 전체의 15% → 'intro'
```

---

### 2-D. layout-selector.ts 설계

```typescript
// 씬 내용 분석 → 레이아웃 자동 결정

function selectLayout(scene: Scene): LayoutType {
  const text = scene.subtitles.map(s => s.text).join(' ')
  const subtitleCount = scene.subtitles.length

  // 규칙 기반 선택 (우선순위 순)
  if (hasNumber(text) && isPercentageOrStat(text))  return 'infographic'
  if (hasBulletList(text) || subtitleCount >= 4)     return 'list-reveal'
  if (hasComparisonKeyword(text))                    return 'split-screen'
  if (hasGraphKeyword(text))                         return 'graph-focus'
  if (scene.contentType === 'hook')                  return 'text-center'  // 훅은 항상 중앙
  if (scene.contentType === 'cta')                   return 'text-center'
  return 'text-center'  // 기본값
}

type LayoutType =
  | 'text-center'
  | 'infographic'
  | 'list-reveal'
  | 'text-image'
  | 'graph-focus'
  | 'split-screen'
  | 'full-visual'
```

---

### 2-E. monoDark.ts 디자인 토큰

```typescript
export const MONO_DARK = {
  // 배경
  background:  '#0A0A0A',   // 페이지 배경 (거의 검정)
  surface:     '#141414',   // 카드/패널 배경
  surfaceAlt:  '#1C1C1C',   // 보조 패널
  border:      '#2A2A2A',   // 구분선

  // 텍스트
  textPrimary:   '#E5E5E5', // 메인 텍스트
  textSecondary: '#888888', // 보조 텍스트
  textAccent:    '#FFFFFF', // 강조 흰색

  // 포인트
  highlight:   '#00FF88',   // 네온 그린 (수치 강조)
  highlightAlt:'#00CFFF',   // 네온 블루 (보조 강조)
  warning:     '#FFB800',   // 경고/주목

  // 타이포
  fontPrimary: '"JetBrains Mono", "Fira Code", "SF Mono", monospace',
  fontDisplay: '"Inter", "Pretendard", sans-serif',  // 한글 포함 씬

  // 크기 (1920×1080 기준)
  fontSizeXL:  120,  // 훅 대형 텍스트
  fontSizeLG:  72,   // 씬 제목
  fontSizeMD:  48,   // 본문 텍스트
  fontSizeSM:  32,   // 자막
  fontSizeXS:  24,   // 보조 텍스트

  // 여백
  paddingOuter: 80,  // 화면 외곽 여백
  paddingInner: 40,  // 요소 내부 여백
} as const
```

---

### 2-F. 자막 애니메이션 시스템 설계

```typescript
// 씬 내 자막 전환 로직 (Remotion spring/interpolate 사용)

interface SubtitleAnimConfig {
  effect: AnimEffect
  durationFrames: number  // 등장 애니메이션 길이 (기본 15프레임)
  exitFrames: number      // 퇴장 애니메이션 길이 (기본 8프레임)
}

type AnimEffect =
  | 'fadeIn'       // 기본 등장
  | 'slideUp'      // 아래→위 슬라이드
  | 'typewriter'   // 글자 단위 순차 reveal
  | 'wordPop'      // 단어 단위 scale bounce
  | 'highlight'    // 배경 색상 sweep
  | 'counter'      // 숫자 카운트업
  | 'drawLine'     // 라인 drawOn
  | 'glitch'       // 노이즈 + 색상 분리

// 씬 타입별 기본 애니메이션 매핑
const DEFAULT_ANIM: Record<string, AnimEffect> = {
  hook:  'glitch',      // 임팩트
  intro: 'fadeIn',      // 부드럽게
  body:  'slideUp',     // 일관성
  cta:   'wordPop',     // 행동 유도
}

// 자막 순차 등장 로직
// 씬 시작 → 자막1 등장 → 유지 → 자막2 교체 → ... → 씬 종료 fadeOut
// 전환 시: 이전 자막 opacity 0→1(진입), 퇴장 자막 opacity 1→0
```

---

### 2-G. SceneNumberOverlay 컴포넌트 (DEV 전용)

```tsx
// DEV_MODE=true 시 모든 씬에 자동 삽입

const SceneNumberOverlay: React.FC<{ sceneId: number; layout: string }> = ({
  sceneId, layout
}) => {
  if (process.env.DEV_MODE !== 'true') return null
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 9999 }}>
      {/* 씬 번호 (우상단) */}
      <div style={{
        position: 'absolute', top: 20, right: 20,
        background: 'rgba(255, 0, 0, 0.85)',
        color: 'white', padding: '6px 16px',
        fontFamily: 'monospace', fontSize: 22, fontWeight: 700,
        borderRadius: 4,
      }}>
        SCENE {sceneId}
      </div>
      {/* 레이아웃 타입 (좌상단) */}
      <div style={{
        position: 'absolute', top: 20, left: 20,
        background: 'rgba(0, 100, 255, 0.85)',
        color: 'white', padding: '6px 16px',
        fontFamily: 'monospace', fontSize: 18,
        borderRadius: 4,
      }}>
        {layout}
      </div>
    </AbsoluteFill>
  )
}
```

---

## 3. 경로 A 상세 설계 — 인앱 편집기

### 3-A. SubtitleTimeline 컴포넌트

```tsx
// frontend/components/vrew/SubtitleTimeline.tsx

interface SubtitleTimelineProps {
  audioUrl: string           // 더빙 오디오 URL
  tokens: SubtitleToken[]    // Whisper STT 결과
  onTokenUpdate: (tokens: SubtitleToken[]) => void
}

// 레이아웃
// ┌──────────────────────────────────────────────────┐
// │ 오디오 파형 (WaveSurfer.js) — 전체 너비           │
// ├──────────────────────────────────────────────────┤
// │ [토큰1][토큰2][토큰3] ← 드래그로 타이밍 조정       │
// │  0.0s   0.4s   0.8s                              │
// └──────────────────────────────────────────────────┘
```

### 3-B. AI 소스 생성 API (Backend)

```
POST /api/v1/videogen/generate-prompt
  입력: { script: string, sceneType: 'hook'|'body'|'cta' }
  출력: { visualPrompt: string, keywords: string[] }

POST /api/v1/videogen/search-stock
  입력: { keywords: string[], duration: number }
  출력: { videos: StockVideo[] }

POST /api/v1/videogen/generate-ai-video
  입력: { visualPrompt: string, duration: number, provider: string }
  출력: { taskId: string }   // Celery 비동기

GET /api/v1/videogen/task/{taskId}
  출력: { status, progress, videoUrl? }
```

---

## 4. 공통 — Remotion SceneRenderer 설계

```tsx
// frontend/remotion/SceneRenderer.tsx

interface SceneRendererProps {
  videoSrc?: string          // 경로 A만 사용 (AI/스톡 소스)
  subtitles: SubtitleToken[] // A/B 공통
  layout: LayoutType         // A/B 공통
  style: typeof MONO_DARK    // A/B 공통
  sceneId: number            // DEV 오버레이용
  totalDurationMs: number
  startMs: number
}

// 레이어 구조 (z-index 순)
// Layer 1 (z=1): 배경 — videoSrc 있으면 영상, 없으면 MONO_DARK.background
// Layer 2 (z=2): 레이아웃 컴포넌트 (텍스트/인포그래픽/리스트 등)
// Layer 3 (z=3): 자막 트랙 (토큰 단위 순차 애니메이션)
// Layer 4 (z=4): 브랜딩 (로고, 워터마크) — 선택적
// Layer 9999: SceneNumberOverlay (DEV_MODE만)
```

---

## 5. 템플릿 등록 플로우

```typescript
// 렌더 완료 후 템플릿 등록

interface VideoGenTemplate {
  id: string                  // 파일명 기반 자동 생성
  name: string                // 사용자 입력
  description: string
  thumbnailUrl: string        // 첫 프레임 자동 추출
  videoUrl: string            // Cloudinary 업로드 URL
  scenesJson: Scene[]         // scenes.json 원본
  remotionComponent: string   // 컴포넌트 코드 경로
  platform: string[]
  tone: string[]
  duration: number
  sceneCount: number
  isMonoDark: boolean         // 경로 B는 항상 true
  source: 'videogen-skill' | 'studio-editor'
  createdAt: string
}

// REMOTION_SHOWCASE 배열에 추가
// → frontend/data/remotion-showcase.ts 업데이트
// → 갤러리(/gallery) 즉시 노출
```

---

## 6. 신규 파일 목록 (전체)

### 경로 B (VIDEOGEN 스킬) — 구현 우선

| 파일 | 타입 | 역할 |
|------|------|------|
| `.claude/skills/videogen/SKILL.md` | 신규 | Claude Code 실행 지시서 |
| `.claude/skills/videogen/scene-analyzer.ts` | 신규 | SRT → scenes.json |
| `.claude/skills/videogen/layout-selector.ts` | 신규 | 레이아웃 자동 결정 |
| `.claude/skills/videogen/remotion-codegen.ts` | 신규 | Remotion 코드 생성기 |
| `.claude/skills/videogen/templates/TextCenter.tsx` | 신규 | 중앙 텍스트 레이아웃 |
| `.claude/skills/videogen/templates/Infographic.tsx` | 신규 | 인포그래픽 레이아웃 |
| `.claude/skills/videogen/templates/ListReveal.tsx` | 신규 | 리스트 순차 등장 |
| `.claude/skills/videogen/templates/TextImage.tsx` | 신규 | 텍스트+이미지 분할 |
| `.claude/skills/videogen/templates/GraphFocus.tsx` | 신규 | 그래프 중앙 |
| `.claude/skills/videogen/templates/SplitScreen.tsx` | 신규 | 2분할 비교 |
| `.claude/skills/videogen/templates/FullVisual.tsx` | 신규 | 전체 배경+자막 |
| `.claude/skills/videogen/styles/monoDark.ts` | 신규 | 디자인 토큰 |
| `frontend/remotion/SceneRenderer.tsx` | 신규 | 씬 합성 컴포넌트 |
| `frontend/remotion/SubtitleTrack.tsx` | 신규 | 자막 애니메이션 트랙 |
| `frontend/remotion/MotionGraphics.tsx` | 신규 | 카운터/라인/하이라이트 |
| `frontend/remotion/SceneNumberOverlay.tsx` | 신규 | DEV 씬 번호 오버레이 |

### 경로 A (인앱 편집기) — 이후 구현

| 파일 | 타입 | 역할 |
|------|------|------|
| `frontend/components/vrew/SubtitleTimeline.tsx` | 신규 | 자막+파형 타임라인 |
| `frontend/components/vrew/ScriptSubtitleSync.tsx` | 신규 | 씬↔자막 동기화 편집 |
| `frontend/components/videogen/SceneSourcePicker.tsx` | 신규 | 씬별 소스 선택 UI |
| `frontend/components/videogen/VisualPromptCard.tsx` | 신규 | AI 장면 묘사 카드 |
| `backend/app/services/visual_prompt_extractor.py` | 신규 | GPT-4 prompt 추출 |
| `backend/app/services/stock_video_service.py` | 신규 | Pexels API |
| `backend/app/services/ai_video_gen_service.py` | 신규 | AI 영상 생성 |
| `backend/app/tasks/videogen_tasks.py` | 신규 | Celery 태스크 |
| `backend/app/api/v1/videogen.py` | 신규 | API 라우터 |

---

## 7. 구현 순서 (경로 B 우선)

```
Phase 1 — 스킬 인프라
  1. monoDark.ts 디자인 토큰 작성
  2. scene-analyzer.ts 완성 (SRT 파서)
  3. SKILL.md 작성

Phase 2 — 레이아웃 템플릿
  4. layout-selector.ts 로직
  5. TextCenter.tsx (기본 레이아웃)
  6. Infographic.tsx (카운터 포함)
  7. ListReveal.tsx
  8. 나머지 레이아웃 4종

Phase 3 — Remotion 코어
  9. SceneRenderer.tsx
  10. SubtitleTrack.tsx (7종 애니메이션)
  11. MotionGraphics.tsx
  12. SceneNumberOverlay.tsx

Phase 4 — 코드 생성기 + 렌더
  13. remotion-codegen.ts
  14. E2E 테스트 (SRT → MP4)
  15. 템플릿 등록 플로우

Phase 5 — 경로 A 인앱 편집기
  16. SubtitleTimeline.tsx
  17. Backend API (videogen, subtitle)
  18. AI 소스 생성 서비스
```

---

## 8. 성공 기준 (검증 체크리스트)

### 경로 B
- [ ] `input/` MP3+SRT → SKILL.md 실행 → `output/final.mp4` 자동 생성
- [ ] 씬 번호 오버레이 (DEV_MODE=true) 정상 표시
- [ ] 7종 자막 애니메이션 모두 동작
- [ ] 모노 다크 테마 일관 적용 (배경 #0A0A0A)
- [ ] 인포그래픽 씬: 카운터 오브젝트 중앙 집중
- [ ] SRT gap 1.5초 기준 씬 분리 정확성 ≥ 90%

### 경로 A
- [ ] Whisper STT 타이밍 오차 < 0.2초
- [ ] AI 소스 자동 배치 (수작업 없이 초안 완성)
- [ ] Remotion 실시간 미리보기 반영 (편집 후 3초 내)

### 공통
- [ ] 원클릭 MP4 렌더링 완료
- [ ] 우수 결과물 → 갤러리 템플릿 등록 동작

---

_작성일: 2026-03-07_
_Phase: Design_
_Status: Ready for Implementation (경로 B 우선)_
