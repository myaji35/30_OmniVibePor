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

---

## Phase 1: 기반 정비 + 경로B 완성 (Week 1)

**목표**: 코드 깨끗하게 + VIDEOGEN 파이프라인 100% 동작

### Skills Pipeline
- pre: /health
- plan: superpowers:brainstorming
- design: superpowers:writing-plans
- implement: superpowers:executing-plans + superpowers:test-driven-development
- verify: superpowers:verification-before-completion
- review: superpowers:requesting-code-review
- post: /health → ship

### Tasks

| Task | 내용 | 병렬 | 의존 | 상태 |
|------|------|------|------|------|
| 1.1 | 코드 위생 정리: ._* 삭제, 테스트/문서 파일 정리, 중복 코드 통합 | [1.1, 1.3, 1.5] 병렬 | - | completed |
| 1.2 | 글로벌 에러 핸들러: error_handler.py, ElevenLabs 크레딧 체크, Cloudinary fallback | - | 1.1 | completed |
| 1.3 | VIDEOGEN 누락 레이아웃 3종: TextImage, GraphFocus, SplitScreen | [1.1, 1.3, 1.5] 병렬 | - | completed |
| 1.4 | VIDEOGEN E2E 실 테스트: MP3+SRT → MP4 전체 파이프라인 | - | 1.3 | pending |
| 1.5 | Docker healthcheck + 백업 스크립트 | [1.1, 1.3, 1.5] 병렬 | - | completed |

### Dependencies
- [1.1, 1.3, 1.5] 병렬 실행 가능
- 1.1 → 1.2 (코드 정리 후 에러 핸들러)
- 1.3 → 1.4 (레이아웃 구현 후 E2E 테스트)

### Success Criteria
- [ ] ._* 파일 0건, 루트 산재 파일 0건
- [x] error_handler.py 동작 (4개 에러코드)
- [ ] MP3+SRT → MP4 E2E 성공
- [x] Docker healthcheck 전 컨테이너 healthy
- [ ] VIDEOGEN Match Rate 85% → 95%+

### References
- docs/01-plan/features/vrew-videogen-pipeline.plan.md
- docs/02-design/features/vrew-videogen-pipeline.design.md
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §4, §7

---

## Phase 2: 네비게이션 + 데이터 모델 (Week 2)

**목표**: 사용자가 길을 잃지 않는 앱 + 정규화된 데이터

### Skills Pipeline
- pre: /health
- plan: superpowers:brainstorming
- design: superpowers:writing-plans
- implement: superpowers:executing-plans + superpowers:test-driven-development
- verify: superpowers:verification-before-completion
- review: superpowers:requesting-code-review
- post: /health → ship

### Tasks

| Task | 내용 | 병렬 | 의존 | 상태 |
|------|------|------|------|------|
| 2.1 | 3-Tier 사이드바 + ProductionStepper (대시보드/프로덕션/리소스/설정) | [2.1, 2.3, 2.5] 병렬 | - | pending |
| 2.2 | 프로젝트 컨텍스트: /project/[id]/ 라우트 + ProjectContextProvider + 브레드크럼 (template-start 잔여 작업 흡수) | - | 2.1 | pending |
| 2.3 | 데이터 모델 정규화: Project, Template, TemplateScene, Subtitle 모델 | [2.1, 2.3, 2.5] 병렬 | - | pending |
| 2.4 | 운영 알림 연동: Celery Slack 알림, API P95 경고, ErrorBoundary UI | - | 2.3 | pending |
| 2.5 | Remotion Design 문서 역추적 작성 (remotion-integration.design.md) | [2.1, 2.3, 2.5] 병렬 | - | pending |

### Dependencies
- [2.1, 2.3, 2.5] 병렬 실행 가능
- 2.1 → 2.2 (사이드바 완성 후 프로젝트 컨텍스트)
- 2.3 → 2.4 (모델 정규화 후 운영 알림)

### Success Criteria
- [ ] 15개 페이지 3-Tier 네비게이션 접근 가능
- [ ] /project/[id]/ URL 구조 동작
- [ ] Project, Template 모델 CRUD API 동작
- [ ] Celery 실패 시 Slack 알림 수신
- [ ] remotion-integration.design.md 완성

### References
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §1, §2, §3
- docs/01-plan/features/template-start.plan.md

---

## Phase 3: 경로A 착수 + GTM (Week 3)

**목표**: VREW 인앱 편집기 기본 동작 + 과금 체계 구축

### Skills Pipeline
- pre: /health
- plan: superpowers:brainstorming
- design: superpowers:writing-plans
- implement: superpowers:executing-plans + superpowers:test-driven-development
- verify: superpowers:verification-before-completion
- review: superpowers:requesting-code-review
- post: /health → ship

### Tasks

| Task | 내용 | 병렬 | 의존 | 상태 |
|------|------|------|------|------|
| 3.1 | VREW 레이어: SubtitleTimeline, ScriptSubtitleSync, Whisper 토큰 타이밍 API | [3.1, 3.2] 병렬 | - | pending |
| 3.2 | Tier별 Quota: Subscription 테이블, quota.py 연동, 업그레이드 유도 UI | [3.1, 3.2] 병렬 | - | pending |
| 3.3 | 온보딩 플로우: OnboardingTour.tsx, 10분 내 첫 영상 목표 | - | 3.2 | pending |
| 3.4 | WebSocket 안정화: 재연결 시 진행률 동기화, Redis 상태 캐싱 | - | 3.1 | pending |

### Dependencies
- [3.1, 3.2] 병렬 실행 가능
- 3.2 → 3.3 (Quota 완성 후 온보딩)
- 3.1 → 3.4 (VREW 레이어 후 WebSocket 안정화)

### Success Criteria
- [ ] SubtitleTimeline에서 자막 토큰 편집 가능
- [ ] Whisper 타이밍 오차 < 0.2초
- [ ] 4개 Tier Quota 동작 (Free: 렌더 3회/월)
- [ ] 온보딩 투어 완주율 측정 가능
- [ ] WebSocket 재연결 시 진행률 유실 없음

### References
- docs/01-plan/features/vrew-videogen-pipeline.plan.md §5
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §6

---

## Phase 4: 통합 테스트 + 런칭 준비 (Week 4)

**목표**: Creator 페르소나 전체 User Flow 동작 + 프로덕션 배포

### Skills Pipeline
- pre: /health
- plan: superpowers:brainstorming
- design: superpowers:writing-plans
- implement: superpowers:executing-plans + superpowers:test-driven-development
- verify: superpowers:verification-before-completion
- review: superpowers:requesting-code-review
- post: /health → ship

### Tasks

| Task | 내용 | 병렬 | 의존 | 상태 |
|------|------|------|------|------|
| 4.1 | E2E 통합 테스트: Creator/Marketer Flow, 실패 시나리오 10개 | - | - | pending |
| 4.2 | 성능 최적화: API P95 < 3s, 렌더링 < 2min, 번들 < 3MB | [4.2, 4.4] 병렬 | 4.1 | pending |
| 4.3 | 프로덕션 배포: Vultr VPS, SSL + Nginx, 환경변수 | - | 4.2 | pending |
| 4.4 | 런칭 콘텐츠: 데모 영상 5개, 갤러리 템플릿 20개, README 업데이트 | [4.2, 4.4] 병렬 | 4.1 | pending |
| 4.5 | Neo4j GraphRAG 활성화: SIMILAR_TO 파이프라인, 성과→최적화 루프 | - | 4.3 | pending |

### Dependencies
- 4.1 → [4.2, 4.4] (E2E 통과 후 최적화/콘텐츠)
- [4.2, 4.4] 병렬 실행 가능
- 4.2 → 4.3 (최적화 후 배포)
- 4.3 → 4.5 (배포 후 GraphRAG)

### Success Criteria
- [ ] Creator User Flow 100% 동작 (10개 페이지 순환)
- [ ] 실패 시나리오 10개 모두 사용자 친화적 에러 메시지
- [ ] API P95 < 3초, 렌더링 < 2분
- [ ] https://omnivibepro.com 프로덕션 접속 가능
- [ ] 갤러리 20개+ 템플릿

### References
- docs/01-plan/features/template-gallery.plan.md
- docs/04-report/SUPPLEMENTARY_PLAN_2026-03-08.md §1.2, §8
