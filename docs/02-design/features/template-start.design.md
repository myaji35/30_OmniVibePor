# Design: template-start

> Plan 문서: `docs/01-plan/features/template-start.plan.md`

---

## 1. 아키텍처 개요

```
gallery/page.tsx
  └─ TemplateCard "사용" 버튼
      └─ router.push('/studio?template={id}')
           │
           ▼
studio/page.tsx (StudioPageContent)
  ├─ useSearchParams().get('template') → templateId
  ├─ lib/template-loader.ts
  │     └─ loadTemplatePreset(templateId)
  │         └─ REMOTION_SHOWCASE 매핑 → TemplatePreset
  │
  ├─ useEffect: templateId 있을 때 preset 적용
  │     ├─ setSelectedCampaign({ id: -1, name: preset.name, ... })
  │     ├─ setDuration(preset.duration)
  │     ├─ setBlocks(generateTemplateBlocks(preset))
  │     └─ setTemplateBannerData(preset)
  │
  └─ TemplateBanner 컴포넌트 (상단 표시)
```

---

## 2. 신규 파일 설계

### 2-A. `frontend/lib/template-loader.ts`

```typescript
import { REMOTION_SHOWCASE } from '@/data/remotion-showcase'
import type { ScriptBlock } from '@/lib/blocks/types'

export interface TemplatePreset {
  id: string
  name: string
  duration: number
  sceneCount: number
  tone: string[]
  platform: string[]
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  description: string
}

// template ID → TemplatePreset 변환
export function loadTemplatePreset(templateId: string): TemplatePreset | null {
  const item = REMOTION_SHOWCASE.find((t) => t.id === templateId)
  if (!item) return null
  return {
    id: item.id,
    name: item.name,
    duration: item.duration,
    sceneCount: item.sceneCount,
    tone: item.tone,
    platform: item.platform,
    githubUrl: item.githubUrl,
    liveUrl: item.liveUrl,
    authorName: item.authorName,
    description: item.description,
  }
}

// sceneCount 기반 기본 ScriptBlock 배열 생성
// 구조: hook 1개 + body (sceneCount-2)개 + cta 1개
export function generateTemplateBlocks(preset: TemplatePreset): ScriptBlock[] {
  const blocks: ScriptBlock[] = []
  const perScene = Math.floor(preset.duration / preset.sceneCount)
  let cursor = 0

  // hook
  blocks.push({
    id: 'hook-0',
    type: 'hook',
    content: `[${preset.name}] 후킹 문구를 입력하세요`,
    duration: perScene,
    effects: { fadeIn: true },
    media: {},
    timing: { start: cursor, end: cursor + perScene },
    order: 0,
  })
  cursor += perScene

  // body (sceneCount - 2개)
  const bodyCount = Math.max(1, preset.sceneCount - 2)
  for (let i = 0; i < bodyCount; i++) {
    blocks.push({
      id: `body-${i}`,
      type: 'body',
      content: `본문 ${i + 1}: 내용을 입력하세요`,
      duration: perScene,
      effects: {},
      media: {},
      timing: { start: cursor, end: cursor + perScene },
      order: i + 1,
    })
    cursor += perScene
  }

  // cta
  blocks.push({
    id: 'cta-0',
    type: 'cta',
    content: '좋아요와 구독 부탁드립니다!',
    duration: perScene,
    effects: { highlight: true, fadeOut: true },
    media: {},
    timing: { start: cursor, end: cursor + perScene },
    order: preset.sceneCount - 1,
  })

  return blocks
}
```

---

### 2-B. `frontend/components/studio/TemplateBanner.tsx`

```tsx
'use client'
// Props
interface TemplateBannerProps {
  templateName: string
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  onClose: () => void
}

// 렌더링
// - 상단 보라색 배너: "Submagic 템플릿 기반으로 시작"
// - githubUrl 있으면 "소스 보기 ↗" 링크
// - X 버튼으로 숨기기
// - 애니메이션: slideDown (translateY -100% → 0)
```

**UI 스펙:**
- 배경: `rgba(168,85,247,0.12)` + `border-b border-purple-500/20`
- 아이콘: `Sparkles` (lucide)
- 텍스트: `"{templateName} 템플릿 기반으로 시작합니다"`
- 링크: `ExternalLink` 아이콘 + `"소스 보기"` (githubUrl 있을 때)
- 닫기: `X` 아이콘 버튼 (우측)
- z-index: `z-40`, 스튜디오 헤더 바로 아래

---

## 3. 수정 파일 설계

### 3-A. `studio/page.tsx` — useEffect 추가

기존 searchParams useEffect (`lines 104-131`)에 `template` 파라미터 처리를 추가:

```typescript
// 기존 useEffect 내부에 추가 (line 104 useEffect 안)
const templateParam = searchParams.get('template')
if (templateParam) {
  const preset = loadTemplatePreset(templateParam)
  if (preset) {
    // Campaign 대체 객체 (DB에 없는 가상 캠페인)
    setSelectedCampaign({
      id: -1,
      name: preset.name,
      client_id: 0,
      status: 'active',
      concept_tone: preset.tone[0] || '',
      target_duration: preset.duration,
    })
    setDuration(preset.duration)
    setBlocks(generateTemplateBlocks(preset))
    setTemplateBannerData(preset)  // 새 state
    setWorkflowStep('template_ready')  // 새 workflowStep 값
  }
}
```

**신규 state 추가:**
```typescript
const [templateBannerData, setTemplateBannerData] = useState<TemplatePreset | null>(null)
```

**TemplateBanner 렌더링 위치:** 스튜디오 최상단 (기존 헤더 바로 아래, `<div className="studio-container">` 내부 첫째)

```tsx
{templateBannerData && (
  <TemplateBanner
    templateName={templateBannerData.name}
    githubUrl={templateBannerData.githubUrl}
    liveUrl={templateBannerData.liveUrl}
    authorName={templateBannerData.authorName}
    onClose={() => setTemplateBannerData(null)}
  />
)}
```

---

### 3-B. `TemplateCard.tsx` — "사용" 버튼 UX 개선

```typescript
// 현재 (변경 전)
const handleUseTemplate = () => {
  router.push(`/studio?template=${template.id}`)
}

// 변경 후
const [isNavigating, setIsNavigating] = useState(false)

const handleUseTemplate = () => {
  setIsNavigating(true)
  router.push(`/studio?template=${template.id}`)
  // 500ms 후 리셋 (페이지 이탈로 불필요하지만 안전장치)
  setTimeout(() => setIsNavigating(false), 500)
}

// 버튼 렌더링
<button
  onClick={handleUseTemplate}
  disabled={isNavigating}
  className="..."
>
  {isNavigating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
  {isNavigating ? '로딩...' : '사용'}
</button>
```

---

## 4. 컴포넌트 트리

```
StudioPageContent
  ├─ [NEW] TemplateBanner (templateBannerData 있을 때만)
  ├─ 기존 헤더 / KPI 영역
  ├─ 기존 스크립트 에디터 (blocks pre-filled)
  └─ 기존 프리뷰 / 렌더링 영역
```

---

## 5. 데이터 플로우 상세

```
URL: /studio?template=submagic
  │
  ▼
useEffect([searchParams]) 실행
  │
  ├─ templateParam = 'submagic'
  ├─ loadTemplatePreset('submagic')
  │     └─ REMOTION_SHOWCASE.find(t => t.id === 'submagic')
  │         → { name: 'Submagic', duration: 30, sceneCount: 5, ... }
  │
  ├─ setSelectedCampaign({ id: -1, name: 'Submagic', ... })
  ├─ setDuration(30)
  ├─ setBlocks([hook-0, body-0, body-1, body-2, cta-0])  // 5개 블록
  ├─ setTemplateBannerData({ name: 'Submagic', githubUrl: undefined, ... })
  └─ setWorkflowStep('template_ready')
```

---

## 6. 엣지 케이스

| 상황 | 처리 |
|------|------|
| `?template=존재하지않는ID` | `loadTemplatePreset` → null 반환 → 기존 빈 스튜디오 |
| `?template=` (빈값) | searchParams.get('template') → '' → if 조건 false → 무시 |
| template + contentId 동시 | contentId 우선 처리 (기존 로직 유지), template은 무시 |
| 배너 닫기 후 새로고침 | URL에 template param 남아있으면 배너 재표시 |

---

## 7. TypeScript 타입 정의

```typescript
// lib/template-loader.ts 에서 export
export interface TemplatePreset {
  id: string
  name: string
  duration: number
  sceneCount: number
  tone: string[]
  platform: string[]
  githubUrl?: string
  liveUrl?: string
  authorName?: string
  description: string
}
```

---

## 8. 파일별 변경 요약

| 파일 | 변경 타입 | 주요 변경 |
|------|-----------|-----------|
| `frontend/lib/template-loader.ts` | 신규 | loadTemplatePreset, generateTemplateBlocks |
| `frontend/components/studio/TemplateBanner.tsx` | 신규 | 템플릿 출처 배너 컴포넌트 |
| `frontend/app/studio/page.tsx` | 수정 | template searchParam 처리, templateBannerData state, TemplateBanner 렌더링 |
| `frontend/components/gallery/TemplateCard.tsx` | 수정 | isNavigating state, 로딩 UX 개선 |

---

## 9. 구현 순서

1. `lib/template-loader.ts` 생성 (유틸 먼저)
2. `components/studio/TemplateBanner.tsx` 생성
3. `app/studio/page.tsx` 수정 (import 추가 + useEffect 확장 + 배너 렌더링)
4. `components/gallery/TemplateCard.tsx` 수정 (isNavigating UX)
5. TypeScript 오류 체크 (`npx tsc --noEmit`)
6. 브라우저 E2E 검증

---

_작성일: 2026-03-01_
_Phase: Design_
