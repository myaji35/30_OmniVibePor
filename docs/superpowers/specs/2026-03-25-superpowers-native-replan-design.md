# Superpowers Native Replan — Design Spec

> **Date**: 2026-03-25
> **Version**: 1.1
> **Author**: Claude (Superpowers Brainstorming)
> **Status**: Approved (Revised after spec review)
> **Approach**: Superpowers Native (접근법 1)

---

## 0. Prerequisites

### Superpowers 스킬 가용성 확인

아래 스킬은 Claude Code superpowers 플러그인에서 제공되며 `Skill` 도구로 호출한다.

| 스킬 | 정식 명칭 | 용도 | Fallback |
|------|-----------|------|----------|
| brainstorming | `superpowers:brainstorming` | 설계 탐색 및 검증 | Plan 문서 수동 작성 |
| writing-plans | `superpowers:writing-plans` | 구현 계획 수립 | TodoWrite 수동 생성 |
| executing-plans | `superpowers:executing-plans` | 계획 기반 구현 | 직접 코딩 |
| TDD | `superpowers:test-driven-development` | 테스트 우선 개발 | 구현 후 테스트 |
| verification | `superpowers:verification-before-completion` | 완료 전 검증 | 수동 체크리스트 |
| code-review | `superpowers:requesting-code-review` | 코드 리뷰 | git diff 수동 검토 |
| debugging | `superpowers:systematic-debugging` | 체계적 디버깅 | 수동 디버깅 |
| ship | `/ship` (gstack skill) | 커밋+PR+배포 | git commit + push 수동 |

**Fallback 정책**: 스킬이 사용 불가능한 경우 Fallback 열의 대체 방법으로 자동 전환.

### Legacy REALPLAN.md 처리

- `legacy_docs/REALPLAN.md`가 존재 (Rails 8 Admin Dashboard용, Phase 0.x 번호 체계)
- **이 파일은 현재 프로젝트와 무관하며 legacy_docs/에 그대로 보존**
- 신규 `REALPLAN.md`는 **프로젝트 루트**에 생성 (경로 충돌 없음)

### 현재 진행 중 작업과의 통합

- PDCA 현재 상태: `template-start` feature, "do" phase 40%
- Phase 1 태스크 중 일부는 이미 구현됨 (git staged 상태):
  - error_handler.py, cloudinary_fallback.py, elevenlabs_credit_check.py
  - TextImage.tsx, GraphFocus.tsx, SplitScreen.tsx
  - 테스트/문서 파일 이동 완료
- **REALPLAN.md 생성 시 이미 완료된 태스크는 `completed` 상태로 표기**
- `template-start` 잔여 작업은 Phase 2 Task 2.2에 흡수

---

## 1. Overview

OmniVibe Pro의 기존 PDCA 기획 4개 + 보충안 6개 Gap을 **REALPLAN.md**로 통합하고,
`/auto`, `/phase`, `/health` 커맨드에 superpowers 스킬 체인을 완전 연결하여
`/auto "MVP 완성"` 한 마디로 전체 개발 파이프라인을 자동 실행할 수 있게 한다.

### 결정 사항

| 항목 | 결정 |
|------|------|
| 범위 | 기획 통합 + 워크플로우 파이프라인 둘 다 (C) |
| 우선순위 | Week 1~4 로드맵 전체 순서대로 (E) |
| 워크플로우 깊이 | superpowers 전체 스킬 체인 완전 자동 오케스트레이션 (C) |
| Phase 단위 | Week 단위 대단위 Phase 1~4 (A) |
| 접근법 | Superpowers Native — REALPLAN.md 중심 (접근법 1) |

---

## 2. REALPLAN.md 구조

REALPLAN.md는 `/auto`, `/phase`의 실행 대상이자 superpowers 스킬 체인의 선언부.

### 구조

```markdown
# OmniVibe Pro — REALPLAN.md

## Meta
- project: OmniVibe Pro
- total_phases: 4
- skill_chain: [brainstorming, writing-plans, executing-plans, TDD,
                verification, code-review, health, ship]
- phase_unit: week

## Phase N: {title} (Week N)
### Skills Pipeline
- pre: /health
- plan: brainstorming
- design: writing-plans
- implement: executing-plans + TDD
- verify: verification-before-completion
- review: code-review
- post: /health → ship

### Tasks
- N.1: {task description}
- N.2: ...

### Dependencies
- N.1 → N.2 (순차)
- [N.1, N.3] 병렬 가능

### Success Criteria
- [ ] ...

### References
- docs/01-plan/features/...
- docs/04-report/...
```

### 설계 포인트

1. **Skills Pipeline 선언** — 각 Phase에 스킬 호출 순서 명시
2. **Tasks** — Day 단위 태스크 목록 (Phase 자체는 Week 단위)
3. **Dependencies** — 태스크 간 의존성 + 병렬 가능 여부
4. **References** — 기존 PDCA 문서 참조 (삭제하지 않음)

---

## 3. Phase 1~4 상세

### Phase 1: 기반 정비 + 경로B 완성 (Week 1)

**목표**: 코드 깨끗하게 + VIDEOGEN 파이프라인 100% 동작

| Task | 내용 | 병렬 | 의존 | 상태 |
|------|------|------|------|------|
| 1.1 | 코드 위생 정리: ._* 삭제, 테스트/문서 파일 정리, 중복 코드 통합 | [1.1, 1.3, 1.5] 병렬 | - | completed (git staged) |
| 1.2 | 글로벌 에러 핸들러: error_handler.py, ElevenLabs 크레딧 체크, Cloudinary fallback | - | 1.1 | completed (git staged) |
| 1.3 | VIDEOGEN 누락 레이아웃 3종: TextImage, GraphFocus, SplitScreen | [1.1, 1.3, 1.5] 병렬 | - | completed (git staged) |
| 1.4 | VIDEOGEN E2E 실 테스트: MP3+SRT → MP4 전체 파이프라인 | - | 1.3 | pending (검증 필요) |
| 1.5 | Docker healthcheck + 백업 스크립트 | [1.1, 1.3, 1.5] 병렬 | - | completed (git staged) |

> **Note**: Task 상태 필드는 REALPLAN.md에서도 동일하게 사용. 값: `pending`, `in_progress`, `completed`, `skipped`

**Success Criteria**:
- ._* 파일 0건, 루트 산재 파일 0건
- error_handler.py 동작 (4개 에러코드)
- MP3+SRT → MP4 E2E 성공
- Docker healthcheck 전 컨테이너 healthy
- VIDEOGEN Match Rate 85% → 95%+

**References**:
- docs/01-plan/features/vrew-videogen-pipeline.plan.md
- docs/02-design/features/vrew-videogen-pipeline.design.md
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §4, §7

---

### Phase 2: 네비게이션 + 데이터 모델 (Week 2)

**목표**: 사용자가 길을 잃지 않는 앱 + 정규화된 데이터

| Task | 내용 | 병렬 | 의존 |
|------|------|------|------|
| 2.1 | 3-Tier 사이드바 + ProductionStepper (대시보드/프로덕션/리소스/설정) | [2.1, 2.3, 2.5] 병렬 | - |
| 2.2 | 프로젝트 컨텍스트: /project/[id]/ 라우트 + ProjectContextProvider + 브레드크럼 | - | 2.1 |
| 2.3 | 데이터 모델 정규화: Project, Template, TemplateScene, Subtitle 모델 | [2.1, 2.3, 2.5] 병렬 | - |
| 2.4 | 운영 알림 연동: Celery Slack 알림, API P95 경고, ErrorBoundary UI | - | 2.3 |
| 2.5 | Remotion Design 문서 역추적 작성 | [2.1, 2.3, 2.5] 병렬 | - |

**Success Criteria**:
- 15개 페이지 3-Tier 네비게이션 접근 가능
- /project/[id]/ URL 구조 동작
- Project, Template 모델 CRUD API 동작
- Celery 실패 시 Slack 알림 수신
- remotion-integration.design.md 완성

**References**:
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §1, §2, §3

---

### Phase 3: 경로A 착수 + GTM (Week 3)

**목표**: VREW 인앱 편집기 기본 동작 + 과금 체계 구축

| Task | 내용 | 병렬 | 의존 |
|------|------|------|------|
| 3.1 | VREW 레이어: SubtitleTimeline, ScriptSubtitleSync, Whisper 토큰 타이밍 API | [3.1, 3.2] 병렬 | - |
| 3.2 | Tier별 Quota: Subscription 테이블, quota.py 연동, 업그레이드 유도 UI | [3.1, 3.2] 병렬 | - |
| 3.3 | 온보딩 플로우: OnboardingTour.tsx, 10분 내 첫 영상 목표 | - | 3.2 |
| 3.4 | WebSocket 안정화: 재연결 시 진행률 동기화, Redis 상태 캐싱 | - | 3.1 |

**Success Criteria**:
- SubtitleTimeline에서 자막 토큰 편집 가능
- Whisper 타이밍 오차 < 0.2초
- 4개 Tier Quota 동작 (Free: 렌더 3회/월)
- 온보딩 투어 완주율 측정 가능
- WebSocket 재연결 시 진행률 유실 없음

**References**:
- docs/01-plan/features/vrew-videogen-pipeline.plan.md §5
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §6

---

### Phase 4: 통합 테스트 + 런칭 준비 (Week 4)

**목표**: Creator 페르소나 전체 User Flow 동작 + 프로덕션 배포

| Task | 내용 | 병렬 | 의존 |
|------|------|------|------|
| 4.1 | E2E 통합 테스트: Creator/Marketer Flow, 실패 시나리오 10개 | - | - |
| 4.2 | 성능 최적화: API P95 < 3s, 렌더링 < 2min, 번들 < 3MB | [4.2, 4.4] 병렬 | 4.1 |
| 4.3 | 프로덕션 배포: Vultr VPS, SSL + Nginx, 환경변수 | - | 4.2 |
| 4.4 | 런칭 콘텐츠: 데모 영상 5개, 갤러리 템플릿 20개, README 업데이트 | [4.2, 4.4] 병렬 | 4.1 |
| 4.5 | Neo4j GraphRAG 활성화: SIMILAR_TO 파이프라인, 성과→최적화 루프 | - | 4.3 |

**Success Criteria**:
- Creator User Flow 100% 동작 (10개 페이지 순환)
- 실패 시나리오 10개 모두 사용자 친화적 에러 메시지
- API P95 < 3초, 렌더링 < 2분
- https://omnivibepro.com 프로덕션 접속 가능
- 갤러리 20개+ 템플릿

**References**:
- docs/01-plan/features/template-gallery.plan.md
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §1.2, §8

---

## 4. `/auto` 스킬 체인 오케스트레이션

### 7-Step 실행 흐름

```
/auto "Phase N 완료"
  │
  ├─ Step 0: PRE
  │   └─ /health (경량 점검 10초)
  │       └─ FAIL → 자동 복구 → 3회 실패 시 중단
  │
  ├─ Step 1: PLAN
  │   └─ brainstorming
  │       └─ Plan/Design 문서 있으면 스킵
  │       └─ 없으면 자동 생성 → 대표님 승인 대기
  │
  ├─ Step 2: DESIGN
  │   └─ writing-plans
  │       └─ 태스크를 병렬/순차 그룹으로 분해
  │       └─ 파일별 변경 목록 + 예상 소요시간
  │
  ├─ Step 3: IMPLEMENT
  │   └─ executing-plans + TDD
  │       └─ 병렬 그룹 실행
  │       └─ 각 태스크: 테스트 먼저 → 구현 → 통과
  │       └─ 실패 → systematic-debugging 자동 호출
  │
  ├─ Step 4: VERIFY
  │   └─ verification-before-completion
  │       └─ Success Criteria 체크리스트 검증
  │       └─ 타입 체크 + 린트 + 빌드 통과
  │
  ├─ Step 5: REVIEW
  │   └─ code-review
  │       └─ git diff 기반 리뷰
  │       └─ 이슈 발견 → 자동 수정 → 재리뷰 (최대 3회)
  │
  ├─ Step 6: POST
  │   └─ /health (전체 점검) → ship (커밋+푸시)
  │       └─ REALPLAN.md Phase 상태 → "completed"
  │
  └─ Step 7: REPORT
      └─ 생성/수정 파일, 테스트 결과, 다음 단계
```

### 스킵 조건

| 조건 | 스킵 대상 |
|------|-----------|
| Plan/Design 문서 존재 | brainstorming |
| 코드 정리 태스크 (H-1~H-6) | TDD |
| 문서 작업 (Design 문서 역추적 등) | code-review |
| `/phase` (단일 Phase) | brainstorming (이미 계획됨) |
| `/auto` 다중 Phase | 스킵 없음 (Phase마다 전체 체인) |

### 대표님 개입 포인트

| 지점 | 트리거 | 대기 방식 |
|------|--------|-----------|
| 새 설계 필요 | brainstorming에서 Plan 없는 태스크 | 설계안 → 승인 대기 |
| 파괴적 작업 | DB 스키마 변경, API 삭제 등 | 알림 → 대표님 명시적 확인 대기 |
| 3회 실패 | systematic-debugging 한계 | 에스컬레이션 보고 |
| Phase 완료 | 항상 | 보고서 출력 (응답 불필요) |

---

## 5. 커맨드 수정 사항

### `/auto` (auto.md)

**관계: 7-Step 스킬 체인이 기존 Step 3을 래핑(wrap)한다. 기존 로직은 보존.**

- 기존 TodoWrite, Task 도구, 병렬 그룹 실행, 메타 학습, 비용 추정 로직 → 그대로 유지
- 7-Step 체인의 Step 3 (IMPLEMENT) 단계에서 기존 auto.md의 병렬/순차 실행 로직을 내부적으로 호출
- 차이: 기존 Step 3 앞뒤로 PLAN/DESIGN/VERIFY/REVIEW/POST 단계가 추가됨
- REALPLAN.md에서 Phase의 skills_pipeline 읽기
- 각 Phase에 대해 7-Step 스킬 체인 실행
- 스킵 조건 적용
- 다중 Phase 시 Phase마다 체인 순환

### `/phase` (phase.md)

Step 1.5 "Skills Pipeline 확인" 추가.
- brainstorming 스킵 (이미 계획됨)
- writing-plans부터 시작
- 나머지는 `/auto`와 동일한 스킬 체인

### `/health` (health.md)

5번째 점검 카테고리 "Superpowers Pipeline" 추가.
- REALPLAN.md 존재 및 파싱 가능 여부
- 각 Phase 상태: REALPLAN.md 내 인라인 상태 마커로 추적
  - `- [ ] Phase 1: 기반 정비` → pending
  - `- [~] Phase 2: 네비게이션` → in_progress
  - `- [x] Phase 1: 기반 정비` → completed
- 마지막 스킬 체인 실행 결과: `.claude/superpowers_log.json`에 기록
  ```json
  {"phase": 1, "timestamp": "2026-03-25T14:30:00Z", "result": "success", "duration_min": 38}
  ```
- 미완료 Phase 알림

---

## 6. 기존 체계 공존 규칙

### 체계 분담

| 상황 | 사용 체계 |
|------|-----------|
| Phase 단위 자동 실행 | `/auto` + superpowers |
| Feature 단위 기획 | `/pdca plan` + bkit |
| 시스템 상태 확인 | `/health` |
| 단독 코드 리뷰 | `superpowers:code-review` |
| VIDEOGEN 영상 생성 | VIDEOGEN 스킬 (독립) |
| Gap 분석 | `bkit:gap-detector` (독립) |
| 버그 수정 | `superpowers:systematic-debugging` |

### 충돌 방지 원칙

1. **REALPLAN.md = Phase(Week) 단위, PDCA = Feature 단위** — 다른 축
2. **REALPLAN.md가 PDCA 문서를 References로 참조** — 복사 안 함
3. **bkit 에이전트 독립 동작 유지** — `/auto` 중에도 별도 호출 가능
4. **새 Feature 추가 시**: `/pdca plan` → PDCA 문서 생성 → REALPLAN.md에 태스크 추가

### 신규 Feature 추가 워크플로우

```
1. /pdca plan {feature} → Plan 문서 생성
2. /pdca design {feature} → Design 문서 생성
3. REALPLAN.md Phase N에 태스크 추가 + References 링크
4. /auto "Phase N 완료" → superpowers 스킬 체인 실행
```

---

## 7. 산출물 목록

| # | 파일 | 작업 | 내용 |
|---|------|------|------|
| 1 | `REALPLAN.md` | 신규 | Phase 1~4 + 스킬 체인 선언 |
| 2 | `.claude/commands/auto.md` | 수정 | 7-Step 스킬 체인 오케스트레이션 |
| 3 | `.claude/commands/phase.md` | 수정 | Skills Pipeline + 부분 스킬 체인 |
| 4 | `.claude/commands/health.md` | 수정 | Superpowers Pipeline 점검 추가 |

기존 보존 (변경 없음):
- `docs/01-plan/`, `docs/02-design/`, `docs/03-analysis/`, `docs/04-report/`
- `.claude/skills/videogen/`
- `.claude/ULW_CHECKLIST.md`, `.claude/LEVEL5_WORKFLOW.md`

---

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-25 | 초안 작성 (brainstorming 5개 섹션) |
| 1.1 | 2026-03-25 | Spec 리뷰 반영: Prerequisites 추가, Legacy REALPLAN 처리, 스킬 가용성 확인, Phase 1 태스크 상태 반영, /auto 래핑 관계 명확화, /health 상태 추적 포맷, 파괴적 작업 확인 방식 변경 |

_Approved by: 대표님 (2026-03-25)_
_Spec created via: superpowers:brainstorming_
