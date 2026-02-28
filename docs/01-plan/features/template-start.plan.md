# Plan: template-start

## 기능 개요

**"이 템플릿으로 시작" 기능**

갤러리(`/gallery`)에서 템플릿 카드의 "사용" 버튼 클릭 시, 해당 템플릿의 메타데이터(이름, 씬 수, 분위기, 플랫폼, githubUrl 등)를 스튜디오(`/studio`)에 자동으로 pre-fill하여 즉시 제작을 시작할 수 있게 하는 기능.

---

## 문제 정의 (As-Is)

- `TemplateCard.tsx`의 "사용" 버튼은 `router.push('/studio?template={id}')` 로 라우팅
- `studio/page.tsx`는 `useSearchParams()`로 `contentId`, `duration`, `mode` 등은 처리하지만, **`template` 파라미터는 전혀 처리하지 않음**
- 결과: 갤러리에서 "사용"을 눌러도 스튜디오가 빈 상태로 열림 → UX 단절

---

## 목표 (To-Be)

1. `/studio?template=submagic` 진입 시 → 해당 템플릿 데이터를 자동 로드
2. 스튜디오 캠페인명, 스크립트 블록, duration, 분위기 등이 pre-fill됨
3. 사용자는 바로 스크립트 편집 또는 영상 생성 단계로 진입 가능

---

## 핵심 요구사항

### FR-01: Template 파라미터 파싱
- `useSearchParams().get('template')` 로 template ID 추출
- `REMOTION_SHOWCASE` 데이터에서 해당 ID 매핑

### FR-02: 스튜디오 초기 상태 pre-fill
- `selectedCampaign.name` → 템플릿 name 기반 자동 설정
- `duration` → 템플릿 duration 값
- `blockItems` → 템플릿 sceneCount 기반 기본 씬 블록 생성
- 분위기(tone), 플랫폼(platform) → 스튜디오 관련 상태에 반영

### FR-03: 템플릿 출처 표시 배너
- 스튜디오 상단에 "Submagic 템플릿 기반으로 시작" 배너 표시
- githubUrl 있으면 소스 링크 제공
- 닫기(X) 버튼으로 배너 숨기기 가능

### FR-04: 갤러리 "사용" 버튼 UX 개선
- 클릭 시 로딩 상태 표시 (짧은 transition)
- 툴팁: "스튜디오에서 이 템플릿으로 바로 시작합니다"

---

## 기술 범위

### 수정 파일
| 파일 | 변경 내용 |
|------|-----------|
| `frontend/app/studio/page.tsx` | `template` searchParam 처리 로직 추가 |
| `frontend/components/gallery/TemplateCard.tsx` | "사용" 버튼 UX 개선 (로딩 상태) |
| `frontend/data/remotion-showcase.ts` | 기존 파일 활용 (변경 없음) |

### 신규 파일
| 파일 | 내용 |
|------|------|
| `frontend/lib/template-loader.ts` | template ID → Studio 초기 state 변환 유틸 |
| `frontend/components/studio/TemplateBanner.tsx` | 템플릿 출처 배너 컴포넌트 |

---

## 데이터 플로우

```
Gallery Page
  └─ TemplateCard "사용" 클릭
      └─ router.push('/studio?template=submagic')
           └─ Studio Page 마운트
               └─ useSearchParams().get('template') → 'submagic'
                   └─ loadTemplatePreset('submagic')
                       └─ REMOTION_SHOWCASE 조회
                           └─ { name, duration, sceneCount, tone, platform, githubUrl }
                               ├─ setCampaignName('Submagic')
                               ├─ setDuration(30)
                               ├─ setBlocks(generateSceneBlocks(5))
                               └─ setTemplateBanner({ name, githubUrl })
```

---

## 비기능 요구사항

- template 파라미터가 없거나 매핑 안 될 경우 → 기존 빈 스튜디오 동작 유지
- 렌더링 깜빡임 없이 초기 마운트 시 한 번만 적용 (`useEffect` + 빈 의존성 배열 활용)
- TypeScript 타입 안정성 유지

---

## 성공 기준

- [ ] 갤러리 "사용" 클릭 → 스튜디오 캠페인명/duration/씬블록 자동 세팅
- [ ] 템플릿 배너가 스튜디오 상단에 표시되고 닫기 가능
- [ ] template 파라미터 없을 때 기존 동작 완전 동일
- [ ] TypeScript 오류 0건

---

## 예상 구현 복잡도

**Low-Medium** — 새 API 없음, 기존 state 패턴 활용, 데이터는 클라이언트 사이드 정적 매핑

---

_작성일: 2026-03-01_
_Phase: Plan_
