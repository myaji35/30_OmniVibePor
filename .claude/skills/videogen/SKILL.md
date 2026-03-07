# VIDEOGEN Skill — Claude Code 실행 지시서

> 더빙(MP3) + 자막(SRT) → Remotion 영상 자동 생성

---

## 사전 확인

실행 전 반드시 확인:

```bash
ls videogen/input/
# dubbing.mp3 ✅
# subtitles.srt ✅
```

파일이 없으면 즉시 사용자에게 안내하고 중단.

---

## 실행 순서

### Step 1 — SRT 분석 → 씬 구조 추출

```bash
npx ts-node .claude/skills/videogen/scene-analyzer.ts
```

- 출력: `videogen/workspace/scenes.json`
- 확인: 씬 수, 총 자막 수, 총 재생시간 출력 확인
- 오류 시: SRT 파일 인코딩(UTF-8) 및 형식 확인

### Step 2 — 씬별 레이아웃 결정

```bash
npx ts-node .claude/skills/videogen/layout-selector.ts
```

- 출력: `scenes.json` 에 `layout`, `animation` 필드 추가
- 확인: 각 씬의 레이아웃 배정 결과 검토
- 필요 시 `scenes.json` 을 직접 수정하여 레이아웃 조정 가능

**레이아웃 선택 가이드:**
| 씬 내용 | 적합한 레이아웃 |
|---------|----------------|
| 훅/CTA, 핵심 1문장 | `text-center` |
| 수치, %, 통계 | `infographic` |
| 목록, 항목 나열 | `list-reveal` |
| 비교/대조 | `split-screen` |
| 그래프/차트 언급 | `graph-focus` |
| 영상 소스 있음 | `full-visual` |

### Step 3 — Remotion 코드 생성

```bash
DEV_MODE=true npx ts-node .claude/skills/videogen/remotion-codegen.ts
```

- 출력: `videogen/workspace/src/` 하위 컴포넌트 생성
- DEV_MODE=true: 각 씬에 "SCENE N" 오버레이 추가

### Step 4 — 의존성 설치

```bash
cd videogen/workspace
npm install
cd ../..
```

### Step 5 — 검증 렌더 (DEV_MODE)

```bash
cd videogen/workspace
DEV_MODE=true npx remotion render GeneratedVideo --output ../output/preview_$(date +%s).mp4
cd ../..
```

- `videogen/output/preview_{timestamp}.mp4` 생성
- **반드시 확인:**
  - [ ] 각 씬 우상단에 "SCENE N" 번호 표시되는가
  - [ ] 각 씬 좌상단에 레이아웃명 표시되는가
  - [ ] 자막이 순차 등장하는가
  - [ ] 더빙 오디오가 재생되는가
  - [ ] 씬 전환이 자연스러운가

### Step 6 — 검증 결과 판단

**통과 기준:**
- 씬 번호가 정확히 표시됨
- 레이아웃이 내용에 적합함
- 자막 타이밍이 오디오와 맞음

**수정 필요 시:**
- 레이아웃 문제 → `scenes.json` 의 `layout` 필드 수정 후 Step 3 재실행
- 자막 문제 → `scenes.json` 의 `subtitles` 타이밍 수정 후 Step 3 재실행
- 컴포넌트 오류 → 해당 `Scene{N}.tsx` 직접 수정 후 Step 5 재실행

### Step 7 — 최종 렌더

모든 씬 검증 통과 시:

```bash
cd videogen/workspace
DEV_MODE=false npx remotion render GeneratedVideo --output ../output/final_$(date +%s).mp4
cd ../..
```

- `videogen/output/final_{timestamp}.mp4` 최종 저장

### Step 8 — 완료 보고

다음 정보를 사용자에게 보고:

```
✅ VIDEOGEN 렌더링 완료

📹 출력 파일: videogen/output/final_{timestamp}.mp4
   총 씬 수:   N개
   재생시간:   X초
   파일 크기:  X MB

씬별 레이아웃 요약:
  Scene 1 [HOOK]  → text-center
  Scene 2 [BODY]  → infographic
  ...

💡 잘 만들어졌다면 템플릿 등록을 고려하세요.
   REMOTION_SHOWCASE에 추가하면 갤러리에 즉시 노출됩니다.
```

---

## 디자인 원칙 (반드시 준수)

1. **모노 다크 테마**: 배경 `#0A0A0A`, 텍스트 `#E5E5E5`, 포인트 `#00FF88`
2. **인포그래픽**: 핵심 객체 화면 중앙 집중, 여백 최소 80px
3. **자막 전환**: 씬 내 자막은 순차 점진적 등장 (fadeIn + slideUp)
4. **씬당 1메시지**: 한 씬에 하나의 핵심 메시지
5. **반복 수정**: 완벽한 결과물이 나올 때까지 Step 3~6 반복

---

## 자주 발생하는 오류

### SRT 파싱 실패
```
원인: 인코딩 문제 (UTF-8 아님) 또는 SRT 형식 오류
해결: file -I videogen/input/subtitles.srt 로 인코딩 확인
     iconv -f EUC-KR -t UTF-8 subtitles.srt > subtitles_utf8.srt
```

### Remotion 모듈 없음
```
원인: workspace에 node_modules 없음
해결: cd videogen/workspace && npm install
```

### 씬 수가 너무 많음 (30개 이상)
```
원인: SCENE_GAP_THRESHOLD_MS 너무 낮음
해결: scene-analyzer.ts의 SCENE_GAP_THRESHOLD_MS를 2000~3000으로 조정
```

---

## 템플릿 등록 (선택 사항)

우수한 결과물은 갤러리 템플릿으로 등록:

1. `frontend/data/remotion-showcase.ts` 열기
2. `REMOTION_SHOWCASE` 배열에 항목 추가:
```typescript
{
  id: 'videogen-{timestamp}',
  name: '템플릿 이름',
  description: '설명',
  duration: N,
  sceneCount: N,
  platform: ['youtube'],
  tone: ['professional'],
  // ... 기타 필드
}
```
3. 썸네일: `npx remotion still GeneratedVideo --frame=30` 으로 추출

---

_VIDEOGEN Skill v1.0 — 2026-03-07_
