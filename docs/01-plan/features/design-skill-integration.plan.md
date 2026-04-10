# Feature Plan — Claude Design Skill 도입 + design-critic 통합

- **Issue**: ISS-086
- **Source**: YouTube T0CMHwVh0u4 Level 3 "How to Install Design Skills"
- **Priority**: P2
- **Status**: PLAN

---

## 1. 스킬 존재 확인 결과

### 발견된 Design 관련 스킬 (5개)

| # | 스킬 | 경로 | 역할 |
|---|---|---|---|
| 1 | **frontend-design** (공식) | `~/.claude/plugins/.../frontend-design/` | **핵심**: "AI slop" 방지, 의도적 미학, 대담한 디자인 방향 |
| 2 | design-consultation (gstack) | `~/.claude/skills/gstack/design-consultation/` | 디자인 시스템 컨설팅 (DESIGN.md 생성) |
| 3 | design-review (gstack) | `~/.claude/skills/gstack/design-review/` | 라이브 사이트 시각 감사 + 자동 fix |
| 4 | plan-design-review (gstack) | `~/.claude/skills/gstack/plan-design-review/` | Plan 문서 디자인 차원 리뷰 |
| 5 | bkit:phase-5-design-system | bkit 플러그인 | 디자인 시스템/토큰/컴포넌트 구축 |

### frontend-design 스킬 핵심 특징
- **"AI slop" 감지 내장**: generic 폰트(Arial, Inter), 의미 없는 그라디언트, 가운데 정렬 5-카드 그리드 금지
- **Tone 스펙트럼**: brutally minimal, luxury/refined, editorial/magazine 등 극단적 방향 권장
- **Typography 우선**: "distinctive display font + refined body font" 쌍
- **Production-grade 코드**: 실제 작동하는 HTML/CSS/JS/React 출력

---

## 2. 역할 분담 매트릭스

### 현재 harness design-critic vs frontend-design 스킬

| 차원 | harness design-critic | frontend-design 스킬 |
|---|---|---|
| **발동 시점** | GENERATE_CODE 완료 후 자동 | 컴포넌트 신규 작성 시 수동/자동 |
| **역할** | 사후 감사 (DESIGN_REVIEW) | 사전 설계 (코딩 전 미학 결정) |
| **AI slop** | 4 규칙 감지 | 완전한 anti-slop 가이드라인 내장 |
| **출력** | 점수 + DESIGN_FIX 이슈 | 실제 코드 (컴포넌트 레벨) |
| **brand-dna 연동** | surfaces 규칙 검증 | 미연동 (범용) |

### 통합 방안: **사전-사후 2단계**

```
[컴포넌트 신규 작성 시]
    │
    ├──→ Step 1: frontend-design 스킬 invoke
    │    "brand-dna.json + SLDS 토큰 기반으로 OmniVibe 톤에 맞는 코드 생성"
    │
    ├──→ Step 2: 코드 작성 (agent-harness)
    │
    └──→ Step 3: design-critic 자동 감사
         "brand-dna anti_patterns + AI slop 4항목 검증"
         → 통과 → DONE
         → 미달 → DESIGN_FIX 이슈 → Step 2 재실행
```

**핵심 통합 지점**: frontend-design 스킬에 OmniVibe의 brand-dna.json을 컨텍스트로 주입.

---

## 3. 병렬 variant 생성 워크플로우

YouTube Level 3의 "Run Parallel Agents" 기법 적용:

```
[사용자 요청: "병의원 Hero 섹션 만들어줘"]
    │
    ├──→ Agent A: frontend-design (minimalist tone)
    │    → hero-v1-minimal.tsx
    │
    ├──→ Agent B: frontend-design (magazine tone)
    │    → hero-v2-magazine.tsx
    │
    └──→ Agent C: frontend-design (bold marketing tone)
         → hero-v3-bold.tsx
         
[3개 동시 렌더 → 사용자 선택]
```

**구현 방법**: Claude Code의 `Agent` 도구로 3개 subagent 병렬 스폰.
각 subagent에 동일한 brand-dna.json + 다른 tone 파라미터 주입.

---

## 4. Pilot 검증 제안

### 대상: `/clients/new` 페이지 (ISS-085 Firecrawl 온보딩)

이유:
- 아직 구현 전이라 기존 코드와 충돌 없음
- URL 입력 → 추출 결과 프리뷰 → 수정 → 저장의 4단계 flow
- BrandPreviewCard, ExtractionConfidenceBadge 등 2개 신규 컴포넌트
- brand-dna surfaces.internal_workspace (SLDS 라이트) 적용 대상

### Pilot 계획
1. frontend-design 스킬 invoke: `/clients/new` 전체 페이지 + 2 컴포넌트
2. 3 variant 병렬 생성 (minimal, SLDS standard, bold)
3. design-critic 자동 감사: brand-dna anti_patterns 검증
4. 대표님 선택 → 확정 variant 기준으로 이후 페이지 톤 고정

---

## 5. 구현 단계

### Stage 0: 설정 (0.5일)
- [ ] frontend-design 스킬이 세션에서 정상 로드되는지 확인
- [ ] brand-dna.json을 스킬 컨텍스트에 주입하는 방법 검증 (CLAUDE.md 지시 또는 프롬프트 prefix)
- [ ] design-critic agent에 frontend-design anti-slop 규칙 머지

### Stage 1: Pilot — /clients/new (1일)
- [ ] 3 variant 병렬 생성
- [ ] design-critic 자동 감사
- [ ] 대표님 선택

### Stage 2: 워크플로우 표준화 (0.5일)
- [ ] harness에 `UI_DESIGN` 이슈 시 자동으로 frontend-design invoke + 3 variant 생성 규칙 추가
- [ ] design-critic에 frontend-design 통과 기준 통합

**총 예상**: 2일

---

## 6. Dependencies

- **ISS-085** (Firecrawl 온보딩) — Pilot 대상 페이지
- **ISS-089** (Phase 0-B PostgreSQL) — /clients/new 페이지가 PG에 저장

---

## 7. Risks

| R# | 리스크 | 완화 |
|---|---|---|
| R1 | frontend-design 스킬이 brand-dna 컨텍스트를 무시 | CLAUDE.md에 "frontend-design invoke 시 반드시 brand-dna.json 참조" 명시 |
| R2 | 3 variant 병렬 생성 시 Opus 비용 폭증 | variant 생성은 sonnet 사용 (design-critic만 opus) |
| R3 | SLDS 표준과 frontend-design의 "대담한 미학" 충돌 | surfaces 규칙으로 내부=SLDS, 외부=대담 분리 |
