# 📋 OmniVibe Pro — 기획 보충안

> **작성일**: 2026-03-08
> **기준 분석**: 프로젝트 실제 코드, 기존 기획 문서 5건, Git 히스토리 39커밋
> **목적**: 기존 기획에 **빠져 있거나 약한 6개 영역**을 식별하고 보충한다

---

## 0. 현황 요약 (Fact 기반)

| 지표 | 수치 |
|------|------|
| Backend 서비스 | 47개 모듈 / 45,374줄 |
| Backend API 라우터 | 30개 그룹 |
| Frontend 페이지 | 15개 라우트 |
| Frontend 컴포넌트 | 64개 TSX |
| Celery 태스크 | 11개 모듈 |
| VIDEOGEN 스킬 Match Rate | 62% (경로B 85%, 경로A 0%) |
| Phase 8 Match Rate | 82% → 93% (보정) |
| 최근 3주 작업 | UI 테마, 갤러리, VIDEOGEN 스킬, 템플릿 시작 |

### 기존 기획 문서 현황

| 문서 | 최종 수정 | 커버 범위 |
|------|-----------|-----------|
| `GAP_ANALYSIS_AND_MISSION_LIST.md` | 2026-02-08 | MISSION 1~8, 2주 로드맵 |
| `QUICK_START_ACTION_PLAN.md` | 2026-02-08 | Day-by-day 실행 계획 |
| `vrew-videogen-pipeline.plan.md` | 2026-03-07 | 경로 A/B 통합 파이프라인 |
| `phase8-gap-analysis.md` | 2026-02-17 | 설계 vs 구현 비교 |
| `vrew-videogen-pipeline.analysis.md` | 2026-03-07 | VIDEOGEN Gap 분석 |

### ❌ 기존 기획에 빠져있는 것들

1. **사용자 여정(User Journey)** — 누가, 어떤 순서로, 어떤 화면을 거치는지 정의 없음
2. **페이지 간 네비게이션 설계** — 15개 페이지가 존재하나 흐름도 없음
3. **데이터 모델 전체 ERD** — 개별 모델만 존재, 관계도 부재
4. **에러 핸들링 & 복구 전략** — Happy path만 설계, 실패 시나리오 없음
5. **운영 전략 (Ops)** — 모니터링, 알림, 백업, 롤백 미정의
6. **Go-to-Market (GTM)** — SaaS 가격 정책, 온보딩 플로우 미정의

---

## 1. 사용자 여정 (User Journey Map)

### 1.1 페르소나 정의

| 페르소나 | 설명 | 핵심 니즈 | 진입 경로 |
|---------|------|-----------|-----------|
| **Creator 김** | 1인 유튜버, 주 3회 업로드 | 영상 제작 시간 단축 (8시간→30분) | 홈 → 갤러리 → 템플릿 시작 |
| **Marketer 박** | 기업 마케팅팀, 다채널 운영 | 채널별 영상 자동화 | 홈 → 대시보드 → 캠페인 생성 |
| **Producer 이** | 영상 프로덕션 디렉터 | 정밀 편집 + AI 보조 | 홈 → 스튜디오 → 스크립트→영상 |

### 1.2 Core User Flow (Creator 김 기준)

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  홈 (/)  │───▶│ 갤러리    │───▶│ 스크립트  │───▶│ 스토리보드│───▶│ 스튜디오  │
│          │    │ /gallery  │    │ /writer   │    │/storyboard│   │ /studio  │
│ 템플릿   │    │ 템플릿    │    │ AI 작성   │    │ 블록 편집 │    │ Preview  │
│ 선택     │    │ 미리보기  │    │ 톤/길이   │    │ 씬 배치   │    │ Remotion │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                     │
                                                                     ▼
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 대시보드 │◀───│ 배포     │◀───│ 오디오    │◀───│ 자막 편집 │◀───│ 렌더링   │
│/dashboard│    │(배포패널) │    │ /audio   │    │/subtitle │    │ Celery   │
│ 성과 추적│    │ YT/IG/TT │    │ TTS+검증 │    │ 타이밍   │    │ 진행률   │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 1.3 페이지별 역할 & 진입/퇴출 조건

| 페이지 | 진입 조건 | 핵심 액션 | 퇴출 조건 (다음 단계로 넘어가려면) |
|--------|-----------|-----------|----------------------------------|
| `/` (홈) | 없음 | 템플릿 선택 or 새 프로젝트 | 프로젝트 생성됨 |
| `/gallery` | 없음 | 템플릿 미리보기, "이 템플릿으로 시작" | 템플릿 ID 선택됨 |
| `/writer` | 프로젝트 ID | 주제·톤·플랫폼 입력 → AI 스크립트 생성 | `script.status = 'approved'` |
| `/director` | 승인된 스크립트 | 블록 분할 → 씬 배치 | `storyboard.status = 'ready'` |
| `/storyboard` | 스토리보드 | 블록 순서 변경, 배경 지정 | 모든 블록에 배경 지정됨 |
| `/audio` | 스토리보드 완성 | TTS 생성 → Zero-Fault 검증 | `audio.accuracy >= 99%` |
| `/subtitle-editor` | 오디오 생성 완료 | Whisper 타이밍 보정, 스타일 | 자막 JSON 확정 |
| `/studio` | 자막 + 오디오 확정 | Remotion 미리보기, 최종 조정 | 사용자 "렌더링 시작" 클릭 |
| `/production` | 렌더링 완료 | 플랫폼 선택 → 배포 | 배포 완료 or 예약됨 |
| `/dashboard` | 배포 완료 | 성과 추적, 다음 캠페인 시작 | (순환) |
| `/upload` | 언제든 | 음성 샘플, PDF 업로드 | 파일 업로드 완료 |
| `/schedule` | 캠페인 존재 | 캘린더 뷰, 게시 일정 관리 | 일정 확정 |
| `/presentation` | PDF 업로드 완료 | PDF→슬라이드→영상 자동 변환 | 영상 렌더링 완료 |

---

## 2. 네비게이션 & 정보 구조 (IA)

### 2.1 GNB(Global Navigation Bar) 설계

현재 15개 페이지가 평면적으로 나열되어 있다. **3-Tier 네비게이션**으로 구조화한다.

```
🏠 OmniVibe Pro
├── 📊 대시보드          /dashboard
├── 🎬 프로덕션 ─────────────────────────────┐
│   ├── ✍️ 스크립트 작성     /writer          │ Production
│   ├── 🎬 디렉터          /director         │ Pipeline
│   ├── 📋 스토리보드       /storyboard       │ (순서대로
│   ├── 🔊 오디오 생성      /audio            │  진행되는
│   ├── 📝 자막 편집        /subtitle-editor  │  워크플로우)
│   ├── 🖥️ 스튜디오        /studio           │
│   └── 🚀 배포            /production        │
│                                             │
├── 📁 리소스 ────────────────────────────────┤
│   ├── 🖼️ 갤러리(템플릿)   /gallery          │ Resource
│   ├── 📤 업로드           /upload           │ Management
│   ├── 📄 프레젠테이션     /presentation     │
│   └── 📅 일정 관리        /schedule         │
│                                             │
└── ⚙️ 설정                                   │
    ├── 🔑 API 키 관리                        │
    ├── 🎤 음성 프로필                         │
    └── 💳 빌링                                │
```

### 2.2 구현 액션 아이템

| # | 작업 | 파일 | 우선순위 |
|---|------|------|---------|
| N-1 | `AppShell.tsx`에 3-Tier 사이드바 구현 | `components/AppShell.tsx` | P0 |
| N-2 | 프로덕션 파이프라인 스텝 인디케이터 | `components/ProductionStepper.tsx` (신규) | P0 |
| N-3 | 각 페이지 상단에 "현재 단계" 브레드크럼 | `components/Breadcrumb.tsx` (신규) | P1 |
| N-4 | 프로젝트 컨텍스트 유지 (URL: `/project/[id]/writer`) | `app/project/[id]/` 라우트 구조 변경 | P2 |

---

## 3. 데이터 모델 ERD (전체 관계도)

### 3.1 Core Entity Relationship

```
┌─────────────┐     1:N     ┌─────────────┐     1:N     ┌─────────────┐
│    User      │────────────▶│   Project    │────────────▶│  Campaign   │
│              │             │              │             │             │
│ id           │             │ id           │             │ id          │
│ email        │             │ name         │             │ name        │
│ plan (tier)  │             │ user_id (FK) │             │ project_id  │
│ voice_id     │             │ template_id  │             │ platform    │
│ created_at   │             │ status       │             │ status      │
└─────────────┘             └─────────────┘             └──────┬──────┘
                                                               │ 1:N
                                                               ▼
┌─────────────┐     1:1     ┌─────────────┐     1:N     ┌─────────────┐
│   Audio      │◀────────────│   Content    │────────────▶│ ScriptBlock │
│              │             │              │             │             │
│ id           │             │ id           │             │ id          │
│ content_id   │             │ campaign_id  │             │ content_id  │
│ audio_url    │             │ script       │             │ block_type  │
│ accuracy     │             │ audio_id     │             │ text        │
│ stt_text     │             │ video_url    │             │ order       │
│ iterations   │             │ status       │             │ start_time  │
└─────────────┘             └─────────────┘             │ duration    │
                                   │ 1:N                │ bg_url      │
                                   ▼                    └─────────────┘
                            ┌─────────────┐
                            │  Subtitle    │
                            │              │
                            │ id           │
                            │ content_id   │
                            │ text         │
                            │ start_ms     │
                            │ end_ms       │
                            │ style_preset │
                            └─────────────┘

┌─────────────┐     1:N     ┌─────────────┐
│  Template    │────────────▶│ TemplateScene│
│              │             │              │
│ id           │             │ id           │
│ name         │             │ template_id  │
│ platform     │             │ layout_type  │
│ thumbnail    │             │ order        │
│ category     │             │ default_text │
└─────────────┘             └─────────────┘

┌─────────────┐             ┌─────────────┐
│ Subscription │             │ ABTest       │
│              │             │              │
│ id           │             │ id           │
│ user_id      │             │ content_id   │
│ plan         │             │ variant_a    │
│ stripe_id    │             │ variant_b    │
│ status       │             │ winner       │
└─────────────┘             └─────────────┘
```

### 3.2 GraphRAG (Neo4j) 노드/관계

```
(:User)-[:OWNS]->(:Project)
(:Project)-[:HAS]->(:Campaign)
(:Campaign)-[:CONTAINS]->(:Content)
(:Content)-[:HAS_BLOCKS]->(:ScriptBlock)
(:Content)-[:GENERATED_WITH]->(:Audio)
(:Content)-[:RENDERED_AS]->(:Video)

(:Content)-[:SIMILAR_TO {score: float}]->(:Content)
(:User)-[:PREFERS {weight: float}]->(:Tone)
(:Content)-[:PERFORMED {views, ctr, retention}]->(:Platform)
```

### 3.3 구현 액션 아이템

| # | 작업 | 우선순위 |
|---|------|---------|
| D-1 | `Project` 모델 신규 생성 (User↔Campaign 사이 레이어) | P1 |
| D-2 | `Template`, `TemplateScene` 모델 생성 (갤러리 데이터 정규화) | P1 |
| D-3 | `Subtitle` 모델 독립 테이블 분리 (현재 Content JSON에 내장) | P2 |
| D-4 | Neo4j `:SIMILAR_TO` 관계 자동 생성 파이프라인 | P2 |

---

## 4. 에러 핸들링 & 복구 전략

### 4.1 실패 시나리오 맵

기존 기획은 Happy Path만 다루고 있다. 아래 실패 시나리오를 보충한다.

| 단계 | 실패 시나리오 | 현재 처리 | 보충 필요 |
|------|-------------|-----------|-----------|
| TTS 생성 | ElevenLabs API 타임아웃 | `tenacity` 재시도 있음 | ✅ 충분 |
| TTS 생성 | ElevenLabs 크레딧 소진 | ❌ 미처리 | 🔴 사전 잔여량 체크 + 사용자 알림 |
| STT 검증 | Whisper API 오류 | `max_iterations` 제한 | ⚠️ 부분 성공 시 사용자 선택지 제공 필요 |
| Remotion 렌더 | OOM (메모리 부족) | ❌ 미처리 | 🔴 메모리 모니터링 + 해상도 fallback |
| Remotion 렌더 | FFmpeg 코덱 오류 | stderr 로깅만 | 🔴 사용자에게 구체적 에러 메시지 필요 |
| Celery 워커 | 워커 다운 | ❌ 미처리 | 🔴 헬스체크 + 자동 재시작 |
| Cloudinary | 업로드 실패 | 단순 Exception | 🔴 로컬 파일 보존 + 재업로드 버튼 |
| Neo4j | 연결 끊김 | graceful degradation 없음 | ⚠️ Neo4j 없어도 동작하도록 fallback |
| WebSocket | 연결 끊김 | 프론트 reconnect 있음 | ⚠️ 재연결 시 진행률 동기화 필요 |
| 결제 | Stripe Webhook 누락 | ❌ 미처리 | 🔴 Webhook 재시도 + 수동 확인 API |

### 4.2 글로벌 에러 처리 패턴

```python
# 보충 필요: backend/app/middleware/error_handler.py (신규)

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

ERROR_CODES = {
    "CREDIT_EXHAUSTED": {"status": 402, "message": "API 크레딧이 부족합니다", "action": "billing_redirect"},
    "RENDER_OOM":       {"status": 507, "message": "렌더링 메모리 부족", "action": "reduce_quality"},
    "WORKER_DOWN":      {"status": 503, "message": "작업 처리 서버 점검 중", "action": "retry_later"},
    "UPLOAD_FAILED":    {"status": 502, "message": "파일 업로드 실패", "action": "retry_upload"},
}

async def global_error_handler(request: Request, exc: Exception):
    error_code = getattr(exc, 'error_code', 'UNKNOWN')
    error_info = ERROR_CODES.get(error_code, {"status": 500, "message": str(exc), "action": "contact_support"})

    logger.error(f"[{error_code}] {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=error_info["status"],
        content={
            "error_code": error_code,
            "message": error_info["message"],
            "action": error_info["action"],
        }
    )
```

### 4.3 구현 액션 아이템

| # | 작업 | 우선순위 |
|---|------|---------|
| E-1 | `error_handler.py` 글로벌 미들웨어 생성 | P0 |
| E-2 | ElevenLabs 크레딧 사전 체크 API | P0 |
| E-3 | Celery 워커 헬스체크 + Docker restart policy | P1 |
| E-4 | Cloudinary 업로드 실패 시 로컬 파일 보존 로직 | P1 |
| E-5 | 프론트엔드 에러 바운더리 + 사용자 친화적 에러 UI | P1 |
| E-6 | WebSocket 재연결 시 상태 동기화 | P2 |

---

## 5. 운영 전략 (Ops & Observability)

### 5.1 현황

기존 기획에 운영 관련 내용이 거의 없다. 배포 가이드(`VULTR_DEPLOYMENT_GUIDE.md`)만 존재하고, 운영 중 모니터링·알림·백업 전략이 부재하다.

### 5.2 보충: 3-Layer 모니터링

```
Layer 1: 인프라 (서버/컨테이너)
├── Docker 컨테이너 상태 (healthcheck)
├── 디스크 사용량 (outputs/, generated_audio/)
├── 메모리/CPU 사용률
└── 알림: 디스크 80% → Slack/Email

Layer 2: 애플리케이션 (API/Task)
├── API 응답 시간 (P50, P95, P99)
├── Celery 태스크 성공/실패율
├── WebSocket 동시 연결 수
└── 알림: API P95 > 5s → 경고 / 태스크 실패율 > 10% → 긴급

Layer 3: 비즈니스 (사용자 행동)
├── 일일 영상 렌더링 수
├── TTS 생성 성공률
├── 사용자 퍼널 전환율 (Writer → Director → Audio → Render)
└── 알림: 일일 렌더링 0건 → 이상 징후
```

### 5.3 백업 전략

| 대상 | 방법 | 주기 | 보존 기간 |
|------|------|------|-----------|
| SQLite DB | `sqlite3 .backup` → S3 | 매일 03:00 | 30일 |
| Neo4j | `neo4j-admin dump` → S3 | 주 1회 일요일 | 90일 |
| Redis | RDB 스냅샷 | 매 6시간 | 7일 |
| Cloudinary 미디어 | Cloudinary 자체 백업 | 자동 | 무제한 |
| `.env` / 시크릿 | 암호화 → 별도 저장소 | 변경 시 | 영구 |

### 5.4 구현 액션 아이템

| # | 작업 | 우선순위 |
|---|------|---------|
| O-1 | Docker healthcheck 추가 (backend, celery, redis, neo4j) | P0 |
| O-2 | `scripts/backup.sh` 자동 백업 스크립트 | P1 |
| O-3 | API 응답시간 로깅 미들웨어 (이미 `middleware/performance.py` 존재 → 알림 연동) | P1 |
| O-4 | Celery 태스크 실패 알림 (Slack Webhook) | P1 |
| O-5 | 디스크 사용량 cron 모니터링 | P2 |

---

## 6. Go-to-Market (GTM) 전략

### 6.1 가격 정책 (Tier 설계)

기존 기획에 Stripe 빌링 구현은 있으나, **가격 정책 자체**가 정의되지 않았다.

| Tier | 월 가격 | 영상 렌더링 | TTS 생성 | 음성 클로닝 | 대상 |
|------|---------|------------|----------|------------|------|
| **Free** | $0 | 3회/월 | 10회/월 | ❌ | 체험 사용자 |
| **Creator** | $29 | 30회/월 | 100회/월 | 1 보이스 | 1인 크리에이터 |
| **Pro** | $79 | 100회/월 | 무제한 | 3 보이스 | 전문 프로듀서 |
| **Enterprise** | $249 | 무제한 | 무제한 | 10 보이스 | 에이전시/기업 |

### 6.2 온보딩 플로우

```
회원가입 → 플랜 선택 → 첫 프로젝트 가이드 투어 → 템플릿으로 첫 영상 만들기
         (30초)     (1분)        (2분 인터랙티브)       (5분)

Target: 가입 후 10분 내 첫 영상 렌더링 완료
```

### 6.3 Quota 시스템 연동

현재 `middleware/quota.py`가 존재하나, 위 Tier별 한도와 연결되어 있지 않다.

| # | 작업 | 우선순위 |
|---|------|---------|
| G-1 | Tier별 quota 설정 테이블 생성 | P1 |
| G-2 | `quota.py` ↔ `subscription.plan` 연동 | P1 |
| G-3 | 한도 초과 시 업그레이드 유도 UI | P2 |
| G-4 | 온보딩 투어 컴포넌트 (`components/OnboardingTour.tsx`) | P2 |

---

## 7. 코드 위생 (Tech Debt Cleanup)

프로젝트 분석에서 발견된 기술 부채를 정리한다.

| # | 이슈 | 해결 | 우선순위 |
|---|------|------|---------|
| H-1 | `._` macOS 리소스 포크 파일 대량 존재 | `.gitignore`에 `._*` 추가 + `find . -name '._*' -delete` | P0 |
| H-2 | `backend/` 루트에 테스트 파일 30+개 산재 | `backend/tests/`로 이동 + pytest 설정 업데이트 | P1 |
| H-3 | `backend/` 루트에 마크다운 15+개 산재 | `backend/docs/`로 이동 | P1 |
| H-4 | `rate_limiter.py` + `rate_limit.py` 중복 | 하나로 통합 | P1 |
| H-5 | `agents/director_agent.py` + `services/director_agent.py` 중복 | 역할 명확 분리 또는 통합 | P1 |
| H-6 | `frontend/app/production/` 내 `._._.*` 이상 파일 | 삭제 | P0 |

---

## 8. 통합 로드맵 (2026-03-08 ~ 04-05, 4주)

기존 MISSION 1~8 + 이번 보충안을 통합한 우선순위 로드맵.

### Week 1 (03/08~03/14): 🧹 기반 정비 + 경로B 완성

| Day | 작업 | 관련 항목 |
|-----|------|-----------|
| Day 1 | 코드 위생 정리 (H-1~H-6) | Tech Debt |
| Day 2 | 글로벌 에러 핸들러 구현 (E-1, E-2) | 에러 전략 |
| Day 3 | VIDEOGEN 누락 레이아웃 3종 (TextImage, GraphFocus, SplitScreen) | Gap P2 |
| Day 4 | VIDEOGEN E2E 실 테스트 (MP3+SRT → MP4) | Gap P1 |
| Day 5 | Docker healthcheck + 백업 스크립트 (O-1, O-2) | 운영 |

### Week 2 (03/15~03/21): 🧭 네비게이션 + 데이터 모델

| Day | 작업 | 관련 항목 |
|-----|------|-----------|
| Day 1-2 | 3-Tier 사이드바 + 프로덕션 스테퍼 (N-1, N-2) | 네비게이션 |
| Day 3 | `Project` 모델 + `Template` 모델 생성 (D-1, D-2) | 데이터 모델 |
| Day 4 | Celery 실패 알림 + API 성능 로깅 알림 연동 (O-3, O-4) | 운영 |
| Day 5 | 프론트엔드 에러 바운더리 UI (E-5) | 에러 전략 |

### Week 3 (03/22~03/28): 🎬 경로A 착수 + GTM

| Day | 작업 | 관련 항목 |
|-----|------|-----------|
| Day 1-2 | SubtitleTimeline.tsx + ScriptSubtitleSync.tsx (경로A Phase 1) | VREW 레이어 |
| Day 3 | Tier별 Quota 시스템 (G-1, G-2) | GTM |
| Day 4 | 온보딩 투어 컴포넌트 (G-4) | GTM |
| Day 5 | WebSocket 재연결 상태 동기화 (E-6) | 에러 전략 |

### Week 4 (03/29~04/05): 🚀 통합 테스트 + 런칭 준비

| Day | 작업 | 관련 항목 |
|-----|------|-----------|
| Day 1-2 | E2E 통합 테스트 (전체 User Flow 검증) | 사용자 여정 |
| Day 3 | 성능 최적화 (API P95 < 3s, 렌더링 < 2min) | 운영 |
| Day 4 | Production 환경 최종 배포 테스트 | 운영 |
| Day 5 | 데모 영상 5개 생성 + 런칭 체크리스트 확인 | GTM |

---

## 9. 성공 기준 (보충)

기존 기획의 KPI에 추가:

### 제품 완성도
- [ ] 15개 페이지 모두 3-Tier 네비게이션으로 접근 가능
- [ ] Creator 페르소나 User Flow 100% 동작 (홈→갤러리→...→대시보드)
- [ ] 모든 실패 시나리오에 사용자 친화적 에러 메시지 표시

### 운영 안정성
- [ ] Docker healthcheck 100% 통과
- [ ] 자동 백업 스크립트 cron 등록
- [ ] Celery 태스크 실패율 < 5%
- [ ] API P95 응답시간 < 3초

### 비즈니스
- [ ] 4개 Tier 가격 정책 Stripe에 등록
- [ ] Quota 초과 시 업그레이드 유도 UI 동작
- [ ] 가입 → 첫 영상 렌더링 10분 이내 달성

---

## 10. 체크리스트 총정리

### P0 (이번 주 내 필수)

- [ ] H-1: `._*` 파일 정리 + `.gitignore` 업데이트
- [ ] H-6: `frontend/app/production/` 이상 파일 삭제
- [ ] E-1: 글로벌 에러 핸들러 미들웨어
- [ ] E-2: ElevenLabs 크레딧 사전 체크
- [ ] N-1: AppShell 3-Tier 사이드바
- [ ] N-2: 프로덕션 파이프라인 스텝 인디케이터
- [ ] O-1: Docker healthcheck 전 컨테이너

### P1 (2주 내)

- [ ] H-2~H-5: 테스트 파일 정리, 중복 코드 제거
- [ ] D-1, D-2: Project, Template 모델 생성
- [ ] E-3~E-5: Celery 헬스체크, Cloudinary fallback, 에러 UI
- [ ] O-2~O-4: 백업, 성능 로깅, 태스크 실패 알림
- [ ] G-1, G-2: Quota ↔ Subscription 연동

### P2 (4주 내)

- [ ] N-3, N-4: 브레드크럼, 프로젝트별 URL 구조
- [ ] D-3, D-4: Subtitle 분리, Neo4j SIMILAR_TO
- [ ] E-6: WebSocket 재연결 동기화
- [ ] G-3, G-4: 업그레이드 유도 UI, 온보딩 투어
- [ ] O-5: 디스크 모니터링

---

_작성: Claude (Zero-Guess 원칙 — 모든 수치는 실제 코드/파일 확인 기반)_
_BMAD 분류: Business(GTM, 페르소나) + Model(ERD) + Action(에러, 운영) + Data(백업)_
_BKIT 순서: Behavior(User Journey) → Knowledge(ERD) → Interface(네비게이션) → Test(성공 기준)_
