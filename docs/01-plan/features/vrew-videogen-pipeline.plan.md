# Plan: vrew-videogen-pipeline

## 1. Overview

**Feature**: VREW + VIDEOGEN + REMOTION 통합 영상 자동화 파이프라인
**Project Level**: Enterprise
**Priority**: Critical
**PDCA Phase**: Plan
**Created**: 2026-03-07

---

## 2. 컨셉 정의

### "3-Engine 협업 아키텍처"

```
┌─────────────────────────────────────────────────────────────┐
│              OmniVibe Pro — 영상 자동화 파이프라인               │
├───────────────┬──────────────────┬──────────────────────────┤
│   VREW 레이어   │  VIDEOGEN 레이어   │    REMOTION 레이어         │
│               │                  │                          │
│  스크립트 편집  │  AI 영상 소스 생성  │  React 기반 최종 렌더링      │
│  자막 자동 동기 │  (음성+배경+B-롤)  │  (타이포+모션+컴포지션)      │
│  타이밍 정렬   │  장면별 AI 생성    │  프로그래머블 영상 출력       │
└───────────────┴──────────────────┴──────────────────────────┘
```

---

## 3. 문제 정의 (As-Is)

| 현황 | 문제 |
|------|------|
| 스크립트 → 영상 파이프라인 단절 | 작성·자막·타이밍이 별도 도구(VREW 등)에서만 가능 |
| AI 영상 소스 없음 | B-롤, 배경 영상을 수작업으로 준비 |
| Remotion 미활용 | 컴포지션 기능만 있고, 실제 소스와 연결 안 됨 |
| 반복 수작업 병목 | 스크립트 수정 시 자막·영상·오디오를 매번 수동 재작업 |

---

## 4. 목표 (To-Be)

> "스크립트 한 줄 쓰면 — 자막이 붙고, AI가 장면을 채우고, Remotion이 완성본을 출력한다"

**영상 제작 진입 경로는 2가지를 병행 지원한다:**

| 경로 | 설명 | 대상 사용자 |
|------|------|-------------|
| **경로 A: 인앱 편집기** | OmniVibe 스튜디오 UI에서 스크립트 작성 → AI 소스 배치 → Remotion 렌더 | 일반 사용자 |
| **경로 B: VIDEOGEN 스킬** | 더빙(MP3)+자막(SRT)을 input 폴더에 넣으면 Claude Code 스킬이 자동으로 Remotion 영상 생성 | 파워 유저 / 자동화 워크플로우 |

---

## 5. 경로 A — 인앱 편집기 (VREW 레이어)

### 핵심 UX
```
[Hook 씬 — 5초]  "이거 알면 유튜브 100만 뚝딱"
   ▼ 오디오 파형 시각화 (WaveSurfer.js)
   ▼ 자막 토큰: [이거][알면][유튜브][100만][뚝딱]  ← 단어 단위 클릭 편집
   ▼ 타이밍 핀: 0.0s — 0.4s — 0.8s — 1.6s — 2.5s
```

### 기능 요구사항 (FR)
| ID | 기능 |
|----|------|
| FR-V01 | ScriptBlock ↔ 오디오 세그먼트 자동 매핑 (Whisper STT 타이밍) |
| FR-V02 | 자막 토큰 단위 드래그 타이밍 조정 |
| FR-V03 | 씬 분할/병합 (Block 추가/삭제 → 오디오 자동 재생성) |
| FR-V04 | 자막 스타일 프리셋 (위치, 폰트, 색상, 애니메이션) |
| FR-V05 | 오디오 파형 + 자막 타임라인 통합 뷰 |

### 신규 컴포넌트
| 파일 | 역할 |
|------|------|
| `components/vrew/SubtitleTimeline.tsx` | 자막 토큰 + 오디오 파형 타임라인 |
| `components/vrew/ScriptSubtitleSync.tsx` | 씬 ↔ 자막 동기화 편집기 |

---

## 6. 경로 B — VIDEOGEN 스킬 (Claude Code Skill)

### 개요

VIDEOGEN은 **Claude Code 스킬**로 구현된다.
사용자가 `input/` 폴더에 더빙(MP3)과 자막(SRT)을 넣으면,
Claude Code가 스킬을 실행하여 Remotion 코드를 자동 생성·반복 수정하고,
`output/` 폴더에 최종 MP4를 렌더링한다.

```
input/
  ├── dubbing.mp3          # 더빙 오디오
  └── subtitles.srt        # 자막 (타이밍 포함)
         │
         ▼  [VIDEOGEN Skill 실행]
output/
  └── final_{timestamp}.mp4
```

### VIDEOGEN 파이프라인 상세

#### Step 1 — SRT 분석 → 씬 구조 추출

```
SRT 파싱 규칙:
- 씬 경계: 자막 간 gap > 1.5초 or 명시적 [SCENE] 태그
- 씬은 여러 자막을 포함할 수 있음 (1:N 관계)
- 각 자막 토큰: { index, startMs, endMs, text }

출력 (scenes.json):
{
  "scenes": [
    {
      "id": 1,
      "startMs": 0, "endMs": 8500,
      "subtitles": [
        { "startMs": 0,    "endMs": 2500, "text": "안녕하세요" },
        { "startMs": 2800, "endMs": 5000, "text": "오늘은 AI 영상을" },
        { "startMs": 5200, "endMs": 8500, "text": "배워봅니다" }
      ],
      "layout": "text-center",
      "contentType": "intro"
    }
  ]
}
```

#### Step 2 — 씬별 레이아웃 구성 (Remotion 코드 생성)

Claude Code가 씬 내용을 분석하여 레이아웃을 선택하고 Remotion 코드를 자동 생성한다.

**레이아웃 종류:**

| 레이아웃 | 용도 | 구성 |
|---------|------|------|
| `text-center` | 핵심 메시지, 훅 | 중앙 대형 텍스트 + 배경 |
| `text-image` | 설명 + 시각 보조 | 좌측 텍스트 / 우측 이미지 |
| `infographic` | 수치, 통계 | 중앙 집중형 객체 (카운터, 차트) |
| `list-reveal` | 목록형 설명 | 항목 순차 등장 |
| `full-visual` | 임팩트 씬 | 전체 배경 + 자막 오버레이 |
| `split-screen` | 비교, 대조 | 2분할 레이아웃 |
| `graph-focus` | 데이터 시각화 | 그래프/차트 중앙 배치 |

**디자인 시스템 — 모노 다크 테마:**
```typescript
const MONO_DARK = {
  background: '#0A0A0A',    // 다크 배경
  surface:    '#141414',    // 카드/패널
  border:     '#2A2A2A',    // 구분선
  primary:    '#E5E5E5',    // 메인 텍스트
  secondary:  '#888888',    // 보조 텍스트
  accent:     '#FFFFFF',    // 강조
  highlight:  '#00FF88',    // 포인트 (네온 그린)
  fontFamily: '"JetBrains Mono", monospace',
}
```

**인포그래픽 원칙:** 핵심 객체 화면 중앙 집중, 여백 최소 80px, 씬당 1개 메시지

#### Step 3 — 자막 프레임 애니메이션

씬 내 자막이 바뀔 때마다 점진적 등장 애니메이션 적용.

```
씬 시작 → 자막1 fadeIn+slideUp → 유지 → 자막2 교체(fadeOut+fadeIn) → ... → 씬 종료 fadeOut
```

**텍스트 애니메이션 효과:**

| 효과 | 용도 |
|------|------|
| `fadeIn` + `slideUp` | 기본 자막 등장 |
| `typewriter` | 긴 텍스트 순차 reveal |
| `wordPop` | 키워드 단어 단위 강조 |
| `highlight` | 중요 구절 배경 sweep |
| `counter` | 숫자 카운트업 (0→N) |
| `drawLine` | 구분선/언더라인 |
| `glitch` | 임팩트 씬 오프닝 |

#### Step 4 — Remotion 코드 생성 및 반복 수정

```
1. scene-analyzer.ts → workspace/scenes.json
2. remotion-codegen.ts → workspace/src/GeneratedVideo.tsx + Scene{N}.tsx
3. npx remotion render (DEV_MODE=true) → output/preview_{ts}.mp4
4. 장면 번호 오버레이로 씬 검증 (각 씬 우상단 "SCENE N" 표시)
5. 오류 발견 시 Step 2 복귀 → 수정 반복
6. 통과 시 DEV_MODE=false → output/final_{ts}.mp4 최종 렌더
```

#### Step 5 — 우수 결과물 템플릿 등록

```
output/final_{ts}.mp4 검토 통과
  └─ scenes.json + Remotion 컴포넌트 저장
  └─ 썸네일 자동 추출 (첫 프레임)
  └─ REMOTION_SHOWCASE 배열에 추가 → 갤러리(/gallery) 즉시 노출
```

### VIDEOGEN 스킬 파일 구조
```
.claude/skills/videogen/
  ├── SKILL.md              # Claude Code 지시서 (실행 순서 정의)
  ├── scene-analyzer.ts     # SRT → scenes.json 파서
  ├── layout-selector.ts    # 씬 내용 → 레이아웃 자동 선택
  ├── remotion-codegen.ts   # scenes.json → Remotion 컴포넌트 생성
  ├── templates/            # 씬 타입별 Remotion 베이스 템플릿
  │     ├── TextCenter.tsx
  │     ├── Infographic.tsx
  │     ├── ListReveal.tsx
  │     └── GraphFocus.tsx
  └── styles/monoDark.ts    # 글로벌 디자인 토큰

videogen/
  ├── input/                # 사용자 입력 폴더
  └── output/               # 렌더링 결과 폴더
```

---

## 7. 경로 A/B 공통 — REMOTION 렌더러

두 경로 모두 최종 출력은 Remotion을 사용한다.

### 컴포지션 구조
```tsx
<Composition>
  {scenes.map((scene, i) => (
    <Sequence from={scene.startFrame} durationInFrames={scene.frames}>
      <SceneRenderer
        videoSrc={scene.videoUrl}       // 경로A: VIDEOGEN API 소스 / 경로B: 없음(순수 그래픽)
        subtitles={scene.subtitles}      // 공통: 자막 토큰
        overlays={scene.overlays}        // 공통: 모션 그래픽
        layout={scene.layout}            // 공통: 레이아웃 타입
        style={MONO_DARK}                // 공통: 모노 다크 테마
      />
    </Sequence>
  ))}
  <BackgroundMusic src={bgMusic} />
</Composition>
```

### 기능 요구사항 (FR)
| ID | 기능 |
|----|------|
| FR-R01 | SceneRenderer: 영상+자막+오버레이 합성 |
| FR-R02 | SubtitleTrack: 토큰 단위 자막 애니메이션 |
| FR-R03 | MotionGraphics: 카운터, 진행바, 하이라이트 |
| FR-R04 | 스타일 프리셋: 5종 (mono-dark, minimal, bold, corporate, trendy) |
| FR-R05 | 실시간 Player 미리보기 |
| FR-R06 | 원클릭 MP4 렌더링 (renderMedia) |

---

## 8. 경로 A 전용 — AI 소스 생성 (VIDEOGEN API)

경로 A(인앱 편집기)에서 씬별 영상 소스를 AI로 자동 생성한다.

### 소스 전략
```
ScriptBlock 씬 타입
  ├─ hook    → AI 생성 (Stability/Kling) — 강렬한 비주얼
  ├─ body    → Pexels/Unsplash 스톡 — 키워드 자동 추출
  ├─ cta     → 내부 브랜드 에셋
  └─ custom  → 사용자 업로드
```

### AI 소스 파이프라인
```
ScriptBlock.content
  → GPT-4 visual prompt 추출
  → Provider 선택 (Pexels 무료 / Stability 중간 / Kling 고품질)
  → Celery 비동기 생성 → Cloudinary 업로드
  → scene_video_url → Remotion SceneRenderer에 주입
```

### 신규 컴포넌트/서비스
| 파일 | 역할 |
|------|------|
| `components/videogen/SceneSourcePicker.tsx` | 씬별 소스 선택/교체 UI |
| `components/videogen/VisualPromptCard.tsx` | AI 장면 묘사 표시 + 재생성 |
| `services/visual_prompt_extractor.py` | GPT-4 visual prompt 추출 |
| `services/stock_video_service.py` | Pexels/Unsplash API |
| `services/ai_video_gen_service.py` | Stability/Kling 연동 |
| `tasks/videogen_tasks.py` | Celery 비동기 태스크 |

---

## 9. 전체 데이터 플로우 비교

### 경로 A (인앱 편집기)
```
스튜디오 UI 스크립트 작성
  → TTS (ElevenLabs) → STT (Whisper) → SubtitleTokens
  → VIDEOGEN API: visual prompt → 소스 영상 (Celery 병렬)
  → Remotion: 소스+자막+모션그래픽 합성
  → MP4 출력
```

### 경로 B (VIDEOGEN 스킬)
```
input/dubbing.mp3 + input/subtitles.srt
  → Claude Code 스킬: SRT 파싱 → 씬 구조 분석
  → 씬별 레이아웃 결정 → Remotion 코드 자동 생성
  → 검증 렌더(장면 번호 오버레이) → 수정 반복
  → output/final_{ts}.mp4 출력
  → (선택) 템플릿 등록 → 갤러리 노출
```

---

## 10. 구현 우선순위 (Phased)

### Phase 1 — VREW 레이어 (Week 1)
- SubtitleTimeline 컴포넌트
- Whisper STT → 토큰 타이밍 추출
- 자막 스타일 프리셋

### Phase 2 — VIDEOGEN 스킬 (Week 2) ← 경로 B
- SKILL.md 작성 (Claude Code 지시서)
- scene-analyzer.ts (SRT 파서)
- layout-selector.ts + remotion-codegen.ts
- 장면 번호 오버레이 디버깅 시스템
- 모노 다크 테마 + 7종 텍스트 애니메이션

### Phase 3 — REMOTION 합성 강화 (Week 3)
- SceneRenderer 컴포넌트 완성
- SubtitleTrack 동기화
- MotionGraphics 라이브러리

### Phase 4 — VIDEOGEN API + 전체 통합 (Week 4) ← 경로 A 완성
- GPT-4 visual prompt 추출
- Pexels 스톡 영상 연동
- E2E 파이프라인 통합
- 템플릿 등록 플로우

---

## 11. 성공 기준

### 경로 A
- [ ] 스크립트 블록 → 자막 자동 동기화 (Whisper 타이밍 오차 < 0.2초)
- [ ] 씬별 AI/스톡 소스 자동 배치
- [ ] Remotion 실시간 미리보기 (편집 후 3초 내)

### 경로 B (VIDEOGEN 스킬)
- [ ] `input/` MP3+SRT → `output/` MP4 자동 생성 (Claude Code 스킬 실행)
- [ ] 씬 번호 오버레이로 장면 검증 가능
- [ ] 모노 다크 테마 일관 적용
- [ ] 씬 내 자막 전환 시 점진적 애니메이션 (7종)
- [ ] 인포그래픽 씬: 핵심 객체 중앙 집중

### 공통
- [ ] 원클릭 MP4 렌더링 완료
- [ ] 우수 결과물 → 갤러리 템플릿 등록 플로우 동작
- [ ] VREW / VIDEOGEN 대비 차별화: 프로그래머블 모션 그래픽

---

## 12. 기존 기능과의 통합 포인트

| 기존 기능 | 통합 방식 |
|-----------|-----------|
| `template-start` | VIDEOGEN 결과 → 템플릿 등록 → 갤러리 "사용" 가능 |
| `Zero-Fault Audio` | TTS/STT 결과를 VREW 레이어(경로 A)에 피드 / 경로 B는 MP3 직접 사용 |
| `StoryboardEditor` | VIDEOGEN API 소스를 스토리보드 씬에 자동 배치 (경로 A) |
| `Remotion Composition` | SceneRenderer로 교체/확장 (A/B 공통) |
| `Celery Task` | videogen_tasks 추가 (경로 A) |
| `Cloudinary` | AI 생성 영상 CDN 업로드 (경로 A) / 최종 MP4 업로드 (경로 B) |
| `REMOTION_SHOWCASE` | 템플릿 등록 시 배열에 추가 (A/B 공통) |

---

_작성일: 2026-03-07_
_Phase: Plan_
_Status: Draft — Design 단계 진입 준비_
