# Superpowers Native Replan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** REALPLAN.md를 생성하고 /auto, /phase, /health 커맨드에 superpowers 스킬 체인을 연결하여 `/auto "Phase 1 완료"` 한 마디로 전체 개발 파이프라인을 자동 실행할 수 있게 한다.

**Architecture:** REALPLAN.md가 중앙 허브로서 Phase 1~4 태스크와 Skills Pipeline을 선언한다. /auto 커맨드는 REALPLAN.md를 읽고 7-Step 스킬 체인(health→brainstorming→writing-plans→executing-plans+TDD→verification→code-review→ship)을 오케스트레이션한다. 기존 /auto 로직은 보존되고, 7-Step 체인이 이를 래핑한다.

**Tech Stack:** Claude Code commands (.md), superpowers skills, git

**Spec:** `docs/superpowers/specs/2026-03-25-superpowers-native-replan-design.md`

---

## File Structure

| # | File | Action | Responsibility |
|---|------|--------|---------------|
| 1 | `REALPLAN.md` | Create | Phase 1~4 정의, Skills Pipeline 선언, 태스크/의존성/성공기준 |
| 2 | `.claude/commands/auto.md` | Modify | Step 3에 7-Step 스킬 체인 래핑 로직 추가 |
| 3 | `.claude/commands/phase.md` | Modify | Step 1.5 Skills Pipeline 확인 + 부분 스킬 체인 |
| 4 | `.claude/commands/health.md` | Modify | 5번째 카테고리 Superpowers Pipeline 추가 |

---

## Task 1: REALPLAN.md 생성

**Files:**
- Create: `REALPLAN.md` (project root)

- [ ] **Step 1: REALPLAN.md 파일 생성 — Meta 섹션**

```markdown
# OmniVibe Pro — REALPLAN.md

## Meta
- **project**: OmniVibe Pro
- **total_phases**: 4
- **phase_unit**: week
- **skill_chain**: [brainstorming, writing-plans, executing-plans, TDD, verification, code-review, health, ship]
- **created**: 2026-03-25
- **spec**: docs/superpowers/specs/2026-03-25-superpowers-native-replan-design.md

## Status
- [x] Phase 1: 기반 정비 + 경로B 완성
- [ ] Phase 2: 네비게이션 + 데이터 모델
- [ ] Phase 3: 경로A 착수 + GTM
- [ ] Phase 4: 통합 테스트 + 런칭 준비
```

- [ ] **Step 2: Phase 1 섹션 작성**

Phase 1의 Skills Pipeline, Tasks (상태 포함), Dependencies, Success Criteria, References를 Spec 섹션 3의 Phase 1 정의를 그대로 반영하여 작성한다.

핵심 포인트:
- Task 1.1, 1.2, 1.3, 1.5 → `completed` 상태
- Task 1.4 → `pending` 상태
- Skills Pipeline: pre(/health) → plan(brainstorming) → design(writing-plans) → implement(executing-plans+TDD) → verify(verification) → review(code-review) → post(/health→ship)
- Dependencies: [1.1, 1.3, 1.5] 병렬, 1.1→1.2, 1.3→1.4
- Success Criteria 5개 체크리스트
- References: vrew-videogen-pipeline.plan.md, design.md, SUPPLEMENTARY_PLAN §4,§7

- [ ] **Step 3: Phase 2 섹션 작성**

Spec 섹션 3의 Phase 2 정의 반영:
- Tasks 2.1~2.5, 모두 `pending`
- Dependencies: [2.1, 2.3, 2.5] 병렬, 2.1→2.2, 2.3→2.4
- template-start 잔여 작업이 Task 2.2에 흡수됨을 명시
- Success Criteria 5개
- References: SUPPLEMENTARY_PLAN §1, §2, §3

- [ ] **Step 4: Phase 3 섹션 작성**

Spec 섹션 3의 Phase 3 정의 반영:
- Tasks 3.1~3.4, 모두 `pending`
- Dependencies: [3.1, 3.2] 병렬, 3.2→3.3, 3.1→3.4
- Success Criteria 5개
- References: vrew-videogen-pipeline.plan.md §5, SUPPLEMENTARY_PLAN §6

- [ ] **Step 5: Phase 4 섹션 작성**

Spec 섹션 3의 Phase 4 정의 반영:
- Tasks 4.1~4.5, 모두 `pending`
- Dependencies: 4.1→[4.2, 4.4], 4.2→4.3, 4.3→4.5
- Success Criteria 5개
- References: template-gallery.plan.md, SUPPLEMENTARY_PLAN §1.2, §8

- [ ] **Step 6: REALPLAN.md 내용 검증**

검증 체크리스트:
- 4개 Phase 모두 존재
- 각 Phase에 Skills Pipeline, Tasks, Dependencies, Success Criteria, References 존재
- Phase 1 태스크 상태 반영 (4 completed, 1 pending)
- Phase 2~4 모두 pending
- Status 섹션의 체크박스가 Phase 상태와 일치
- 모든 References 경로가 실제 존재하는 파일

- [ ] **Step 7: 커밋**

```bash
git add REALPLAN.md
git commit -m "feat: REALPLAN.md 생성 — Phase 1~4 + superpowers 스킬 체인 선언"
git push
```

---

## Task 2: /auto 커맨드 수정

**Files:**
- Modify: `.claude/commands/auto.md`

- [ ] **Step 1: Step 3 직전에 Superpowers 스킬 체인 정의 섹션 추가**

`.claude/commands/auto.md`에서 `### Step 3: 자율 실행` 바로 앞에 다음 섹션을 삽입:

```markdown
### Superpowers Skills Pipeline (v1.1)

`/auto`는 REALPLAN.md의 각 Phase에 대해 7-Step 스킬 체인을 실행합니다.
기존 자율 실행 로직(TodoWrite, Task 도구, 병렬 그룹)은 보존되며,
7-Step 체인의 Step 3(IMPLEMENT) 단계에서 내부적으로 호출됩니다.

#### 7-Step 스킬 체인

| Step | 이름 | 스킬 | 스킵 조건 |
|------|------|------|-----------|
| 0 | PRE | /health (경량) | 없음 (항상 실행) |
| 1 | PLAN | superpowers:brainstorming | Plan/Design 문서 존재 시 |
| 2 | DESIGN | superpowers:writing-plans | 없음 |
| 3 | IMPLEMENT | superpowers:executing-plans + superpowers:test-driven-development | TDD: 코드 정리/인프라 태스크 시 |
| 4 | VERIFY | superpowers:verification-before-completion | 없음 |
| 5 | REVIEW | superpowers:requesting-code-review | 문서 작업 시 |
| 6 | POST | /health (전체) → /ship or git commit+push | 없음 |

#### Fallback 정책
스킬 사용 불가 시:
- brainstorming → Plan 문서 수동 확인
- writing-plans → TodoWrite 수동 생성
- executing-plans → 직접 코딩
- TDD → 구현 후 테스트
- verification → 수동 체크리스트
- code-review → git diff 수동 검토
- /ship → git commit + push 수동

#### 대표님 개입 포인트
- 새 설계 필요 시 → 설계안 제시 후 승인 대기
- 파괴적 작업(DB 스키마 변경, API 삭제) → 알림 후 명시적 확인 대기
- 3회 실패 → systematic-debugging 후에도 미해결 시 에스컬레이션
- Phase 완료 시 → 보고서 출력 (응답 불필요)

#### 실행 결과 로깅
스킬 체인 실행 결과를 `.claude/superpowers_log.json`에 기록:
```json
{"phase": 1, "timestamp": "2026-03-25T14:30:00Z", "result": "success", "duration_min": 38}
```
```

- [ ] **Step 2: Step 3 제목과 내용 수정**

기존 `### Step 3: 자율 실행`을 찾아서 제목을 다음으로 변경:

```markdown
### Step 3: 자율 실행 (Superpowers Enhanced)
```

그리고 Step 3 첫 번째 문단 바로 뒤에 다음 내용 추가:

```markdown
**REALPLAN.md 연동**:
1. REALPLAN.md에서 요청된 Phase의 `Skills Pipeline` 섹션을 읽는다
2. 위 "7-Step 스킬 체인"에 따라 각 Step을 순차 실행한다
3. Step 3(IMPLEMENT)에서 기존 자율 실행 로직(TodoWrite, Task 도구, 병렬 그룹)을 호출한다
4. 다중 Phase 실행 시 각 Phase마다 7-Step 체인을 순환한다
5. Phase 완료 시 REALPLAN.md Status 섹션을 업데이트한다: `- [ ]` → `- [x]`
6. 실행 결과를 `.claude/superpowers_log.json`에 기록한다
```

- [ ] **Step 3: 변경 내용 검증**

검증 체크리스트:
- Superpowers Skills Pipeline 섹션이 Step 3 직전에 존재
- 7-Step 테이블에 7개 행 존재 (Step 0~6)
- 스킵 조건 컬럼이 각 Step에 명시됨
- Fallback 정책 7개 항목
- 대표님 개입 포인트 4개 항목
- Step 3 제목에 "(Superpowers Enhanced)" 포함
- REALPLAN.md 연동 6단계 로직 포함
- 기존 자율 실행 로직(TodoWrite, Task, 병렬 그룹, 메타 학습, 비용 추정)이 삭제되지 않았음

- [ ] **Step 4: 커밋**

```bash
git add .claude/commands/auto.md
git commit -m "feat: /auto 커맨드에 superpowers 7-Step 스킬 체인 오케스트레이션 추가"
git push
```

---

## Task 3: /phase 커맨드 수정

**Files:**
- Modify: `.claude/commands/phase.md`

- [ ] **Step 1: Step 1과 Step 2 사이에 Step 1.5 삽입**

`.claude/commands/phase.md`에서 `### Step 2: 실행 계획 생성` 바로 앞에 다음을 삽입:

```markdown
### Step 1.5: Skills Pipeline 확인

REALPLAN.md에서 요청된 Phase의 Skills Pipeline을 확인합니다.

1. REALPLAN.md 파싱 → 해당 Phase의 Skills Pipeline 섹션 읽기
2. **brainstorming 스킵** (이미 계획된 Phase를 실행하므로)
3. writing-plans부터 시작하여 다음 순서로 진행:
   - writing-plans → executing-plans + TDD → verification → code-review → ship
4. 스킵 조건은 `/auto`의 "7-Step 스킬 체인" 테이블과 동일 적용
5. Fallback 정책도 `/auto`와 동일

**`/auto`와의 차이점**:
- `/auto`: brainstorming 포함, 다중 Phase 가능
- `/phase`: brainstorming 스킵, 단일 Phase만 실행
```

- [ ] **Step 2: Step 3 제목 수정**

기존 `### Step 3: 자율 실행`을 다음으로 변경:

```markdown
### Step 3: 자율 실행 (Superpowers Enhanced)
```

그리고 첫 줄 뒤에 추가:

```markdown
Skills Pipeline에 따라 writing-plans → executing-plans+TDD → verification → code-review → ship 순서로 실행합니다.
Phase 완료 시 REALPLAN.md Status 섹션을 업데이트하고 `.claude/superpowers_log.json`에 결과를 기록합니다.
```

- [ ] **Step 3: 변경 내용 검증**

검증 체크리스트:
- Step 1.5가 Step 1과 Step 2 사이에 존재
- brainstorming 스킵 명시
- /auto와의 차이점 명시
- Step 3 제목에 "(Superpowers Enhanced)" 포함
- REALPLAN.md 업데이트 + 로깅 명시
- 기존 로직(TodoWrite, Task 도구, 병렬 그룹, 에러 처리, 메타 학습)이 삭제되지 않았음

- [ ] **Step 4: 커밋**

```bash
git add .claude/commands/phase.md
git commit -m "feat: /phase 커맨드에 Skills Pipeline 확인 + 부분 스킬 체인 추가"
git push
```

---

## Task 4: /health 커맨드 수정

**Files:**
- Modify: `.claude/commands/health.md`

- [ ] **Step 1: 5번째 점검 카테고리 추가**

`.claude/commands/health.md`에서 `#### Code Quality 문제` 섹션 뒤, `### Step 4: 헬스 리포트 생성` 앞에 다음을 삽입:

```markdown
#### Superpowers Pipeline 점검

**REALPLAN.md 존재 확인**
- 탐지: 프로젝트 루트에 `REALPLAN.md` 존재 여부
- 자동 수정: 없음
- 에스컬레이션: 파일 부재 시 "REALPLAN.md가 없습니다. `/auto` 실행 전 생성이 필요합니다" 알림

**Phase 상태 확인**
- 탐지: REALPLAN.md의 Status 섹션 파싱
  - `- [x]` → completed
  - `- [~]` → in_progress
  - `- [ ]` → pending
- 출력: 각 Phase 상태 표시

**마지막 스킬 체인 실행 결과**
- 탐지: `.claude/superpowers_log.json` 읽기
- 출력: 마지막 실행 Phase, 시각, 결과, 소요시간
- 파일 없으면: "스킬 체인 실행 기록 없음" 표시

**미완료 Phase 알림**
- 탐지: pending 상태인 Phase 중 다음 실행 가능한 것 식별
- 출력: "Next: Phase N 실행 가능 (`/auto "Phase N 완료"`)"
```

- [ ] **Step 2: Step 1 헬스 체크 카테고리에 5번째 추가**

`### Step 1: 헬스 체크 카테고리 분석` 섹션에서 기존 4개 카테고리 리스트를 찾아 5번째 추가:

```markdown
5. Superpowers Pipeline (스킬 체인)
```

- [ ] **Step 3: 헬스 리포트 출력 예시에 5번째 카테고리 추가**

`### Step 4: 헬스 리포트 생성` 섹션의 출력 예시에 다음을 추가:

```
✅ Superpowers Pipeline (4/4)
  ✅ REALPLAN.md: Valid (4 phases defined)
  ✅ Phase status: Phase 1 completed, Phase 2-4 pending
  ✅ Last skill chain: 2026-03-25 14:30 → Phase 1 성공 (38분)
  ✅ Next action: Phase 2 실행 가능 (/auto "Phase 2 완료")
```

- [ ] **Step 4: 변경 내용 검증**

검증 체크리스트:
- Superpowers Pipeline 섹션이 Code Quality 뒤에 존재
- 4개 점검 항목 (REALPLAN.md 존재, Phase 상태, 마지막 실행, 미완료 알림)
- Step 1에 5번째 카테고리 추가됨
- 헬스 리포트 출력 예시에 Superpowers Pipeline 카테고리 포함
- 기존 4개 카테고리(Infrastructure, Dependencies, Configuration, Code Quality) 변경 없음

- [ ] **Step 5: 커밋**

```bash
git add .claude/commands/health.md
git commit -m "feat: /health 커맨드에 Superpowers Pipeline 점검 카테고리 추가"
git push
```

---

## Task 5: 통합 검증 + 최종 커밋

**Files:**
- Verify: `REALPLAN.md`, `.claude/commands/auto.md`, `.claude/commands/phase.md`, `.claude/commands/health.md`

- [ ] **Step 1: REALPLAN.md 파싱 검증**

REALPLAN.md가 올바르게 구성되었는지 확인:
- Meta 섹션의 필수 필드 존재 (project, total_phases, phase_unit, skill_chain)
- Status 섹션의 체크박스 4개 존재
- Phase 1~4 각각에 Skills Pipeline, Tasks, Dependencies, Success Criteria, References 존재
- Phase 1 Task 상태: 4 completed + 1 pending
- 모든 References 경로가 실제 파일로 존재하는지 확인:
  ```bash
  # 참조 파일 존재 확인
  ls docs/01-plan/features/vrew-videogen-pipeline.plan.md
  ls docs/02-design/features/vrew-videogen-pipeline.design.md
  ls docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md
  ls docs/01-plan/features/template-gallery.plan.md
  ```

- [ ] **Step 2: 커맨드 파일 무결성 검증**

각 커맨드 파일이 기존 로직을 보존하면서 새 섹션이 추가되었는지 확인:
- `auto.md`: "Superpowers Skills Pipeline" 섹션 존재 + "Superpowers Enhanced" 포함 + 기존 TodoWrite/Task/메타학습 로직 보존
- `phase.md`: "Step 1.5" 존재 + "Superpowers Enhanced" 포함 + 기존 병렬 그룹/에러 처리 보존
- `health.md`: "Superpowers Pipeline" 섹션 존재 + 기존 4개 카테고리 변경 없음

- [ ] **Step 3: superpowers_log.json 초기화**

`.claude/superpowers_log.json` 초기 파일 생성:
```json
[]
```

- [ ] **Step 4: 최종 커밋**

```bash
git add .claude/superpowers_log.json
git commit -m "chore: superpowers 실행 로그 파일 초기화"
git push
```

---

## Summary

| Task | 파일 | 작업 | 예상 시간 |
|------|------|------|-----------|
| Task 1 | REALPLAN.md | 신규 생성 (Phase 1~4) | 5분 |
| Task 2 | .claude/commands/auto.md | 7-Step 스킬 체인 래핑 추가 | 3분 |
| Task 3 | .claude/commands/phase.md | Step 1.5 + 부분 스킬 체인 | 2분 |
| Task 4 | .claude/commands/health.md | Superpowers Pipeline 카테고리 | 3분 |
| Task 5 | 전체 | 통합 검증 + 로그 초기화 | 2분 |
| **Total** | **4 files** | | **~15분** |
