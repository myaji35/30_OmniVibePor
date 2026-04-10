# Feature Plan — Marp + NotebookLM Hybrid Slide System (Phase 4 재설계)

- **Issue**: ISS-064
- **Parent**: ISS-033 (Agency SaaS Multivertical Plan) Phase 4
- **Status**: PLAN (draft)
- **Author**: product-manager (opus)
- **Date**: 2026-04-10
- **Strategy path**: Path 1 (Marp 주력) + Path 2 (NotebookLM 수동) 하이브리드

---

## 1. Why (재설계 배경)

### 1.1 기존 Phase 4 설계 한계
기존 Phase 4(`vrew-videogen-pipeline.plan.md`)는 Puppeteer + HTML/CSS 템플릿 기반 슬라이드 렌더링 설계였다. 문제점:
- HTML/CSS 템플릿 수동 작성 부담 (레이아웃 8종 × vertical 6종 = 48개)
- PDF/PPTX/PNG 별도 파이프라인 필요
- 한국어 폰트 처리 반복 구현
- "회원이 PPTX 다운받아 편집"이 기술적으로 단절

### 1.2 외부 변화
- **2026-04-09**: Marp(Markdown Presentation Ecosystem) `/marp` Claude skill 출시 확인
- Marp CLI 1회 호출로 `.md → .pdf + .pptx + .png` 동시 출력
- CSS theme 시스템 + Pretendard 등 @font-face 지원
- **2026-02-18**: NotebookLM Studio 공식 PDF/PPTX export 지원

### 1.3 재설계 핵심 가치
| 가치 | 기존 | 재설계 |
|---|---|---|
| 템플릿 관리 | HTML/CSS 48개 파일 | Marp CSS theme 6개 |
| 출력 포맷 | Puppeteer × 3회 | Marp CLI × 1회 |
| 개발 공수 | Phase 4 1주 | 3~5일 (-30~40%) |
| 회원 편집 | PDF only | PPTX 편집 가능 |
| 다양성 백업 | 없음 | NotebookLM 수동 경로 (Path 2) |

---

## 2. What (기능 명세)

### 2.1 하이브리드 3-Path 구조

```
[사용자 입력: 스크립트 or 원고]
          │
          ├──→ Path 1 (Marp 주력, 자동) ────────┐
          │    1. Slide Layout Agent              │
          │       (GPT-4o-mini, script → markdown)│
          │    2. Marp CLI (CSS theme)             │
          │    3. PDF + PPTX + PNG 동시 출력       │
          │                                        │
          ├──→ Path 2 (NotebookLM, 수동) ─────────┤
          │    1. 회원이 NotebookLM Studio에서     │
          │       수동으로 PDF 생성                 │
          │    2. OmniVibe에 PDF 업로드            │
          │    3. notebooklm_adapter (ISS-063)     │
          │       워터마크 crop                     │
          │    4. 기존 PDF 파이프라인 재사용        │
          │                                        │
          └──→ Path 3 (회원 자체 PDF) ────────────┤
               1. 회원이 PPT/Keynote로 만든 PDF    │
               2. 업로드 → 그대로 처리             │
                                                   │
                                                   ▼
                              [presentation_video_generator]
                              (공통 후처리: 영상 렌더링)
```

### 2.2 Slide Layout Agent (신규, Path 1 전용)
- **역할**: 스크립트/원고 텍스트 → Marp 마크다운 자동 생성
- **모델**: GPT-4o-mini (싸고 충분)
- **입출력**:
  - Input: `{"script": "...", "vertical": "medical", "slide_count_target": 8, "tone": "professional"}`
  - Output: Marp 마크다운 + frontmatter (`theme: medical`)
- **프롬프트 원칙**:
  - 슬라이드당 1 핵심 메시지
  - 제목(`##`) + 2~4 불릿 + optional 인용구
  - 이미지 placeholder: `![bg](@@IMAGE_SLOT_N@@)` (후처리에서 실 이미지 주입)
  - 마지막 슬라이드는 CTA 고정
- **llm_profile.py 통합**: `task="slide_to_script"` 재활용 또는 신규 task `"script_to_slide_md"` 추가

### 2.3 Marp CSS Theme 6종 (vertical별)

| vertical | 파일 | 컬러 | 폰트 | 비고 |
|---|---|---|---|---|
| medical | `themes/medical.css` | #0891b2 (clinical teal) | Pretendard + Noto Sans KR | 의료광고법 톤 유의 |
| academy | `themes/academy.css` | #f59e0b (learning amber) | Pretendard | 교육 친근 |
| mart | `themes/mart.css` | #dc2626 (sale red) | Pretendard Bold heavy | 가격 강조 |
| beauty | `themes/beauty.css` | #ec4899 (beauty pink) | Pretendard + Cormorant | 감성 세리프 |
| restaurant | `themes/restaurant.css` | #d97706 (appetite orange) | Pretendard | 따뜻한 톤 |
| general | `themes/general.css` | #00A1E0 (SLDS blue) | Pretendard | fallback |

각 theme는 공통 `themes/base.css`를 @import하여 중복 제거.

### 2.4 Marp Worker 컨테이너 (신규)
- **이유**: Marp CLI는 Node + Chromium 의존 → 기존 FastAPI 컨테이너에 넣으면 이미지 비대
- **이름**: `marp-worker`
- **Base image**: `marpteam/marp-cli:latest`
- **인터페이스**: HTTP (FastAPI sidecar) or stdin 파이프 (Celery task)
- **API**: `POST /render` with `{markdown, theme, output_formats: ["pdf","pptx","png"]}`
- **Docker Compose**: `docker-compose.yml`에 추가

### 2.5 `slide_render_profile.py` (Pattern A 4회차)
Atomic Option Group 패턴 4회차 적용 대상 (ffmpeg→llm→tts→slide_render).

**단일 책임**: Marp CLI 호출 시 필요한 options/theme/resolution/font 표준화.

```python
# 예시 시그니처
SLIDE_RESOLUTIONS = {
    "youtube_16x9": (1920, 1080),
    "instagram_1x1": (1080, 1080),
    "tiktok_9x16": (1080, 1920),
}
THEME_CATALOG = {"medical", "academy", "mart", "beauty", "restaurant", "general"}

def marp_safe_cli_args(*, markdown_path, theme, output_format, resolution, output_dir):
    """Marp CLI 안전 인자 생성 (iOS 호환 PNG + 표준 PPTX)"""

def marp_safe_render_all_formats(*, markdown_path, theme, resolution, output_dir):
    """PDF + PNG 2종 출력 (PPTX는 ISS-090 NOGO로 제외, Path 4 python-pptx로 별도)"""

def verify_marp_output(*, output_path, expected_pages):
    """co-located verifier — 페이지 수 + 파일 크기 검증"""
```

### 2.6 ~~PPTX 차별화 가치~~ → ❌ REJECTED (ISS-090 Spike 결과)

> **ISS-090 NOGO (2026-04-10)**: Marp CLI v4.3.1의 PPTX 출력은 **이미지 PPTX**임이 확인됨.
> 각 슬라이드 = 단일 `<a:blipFill>` 배경 이미지, `<a:t>` 텍스트 노드 0개, python-pptx shapes 0개.
> **편집 불가능 → 이 섹션의 가치 제안 전면 폐기.**

**대안 (Path 4 제안)**:
- python-pptx로 직접 PPTX 빌드 (`SlideBuilder` 서비스) — 진짜 텍스트 레이어 생성
- Marp CSS theme → 레이아웃 스펙 역할로 재활용 (python-pptx slide master 매핑)
- 별도 ISS 발급 필요 (spike: python-pptx 편집 가능성은 이미 검증됨 — 라이브러리 자체가 텍스트 기반)

**Marp 잔존 가치**: PDF + PNG 출력은 여전히 유효. CSS theme 6종의 관리 이점 유지.

**수정된 출력 포맷**: ~~PDF + PPTX + PNG 3종~~ → **PDF + PNG 2종** (Marp) + **PPTX 1종** (python-pptx, Path 4)

---

## 3. How (구현 단계)

### Stage 1: 기반 (1일)
- [ ] `marp-worker` Dockerfile 작성 (~10 lines)
- [ ] `docker-compose.yml` 에 service 추가
- [ ] `backend/app/services/slide_render_profile.py` 초안 (Pattern A 4회차)
- [ ] `backend/themes/marp/base.css` + `general.css` 2종 초안

### Stage 2: Slide Layout Agent (1일)
- [ ] `llm_profile.py`에 `script_to_slide_md` task 추가
- [ ] `backend/app/agents/slide_layout_agent.py` 작성
- [ ] 테스트: 샘플 스크립트 → 마크다운 → Marp CLI → PDF 출력 확인
- [ ] 비용 측정 (GPT-4o-mini 토큰, ISS-040 cost model 업데이트)

### Stage 3: Vertical Themes (1~2일)
- [ ] medical, academy, mart CSS theme 작성 (우선 3종)
- [ ] beauty, restaurant, general 작성
- [ ] Pretendard @font-face 로컬 hosting 검증
- [ ] 6개 theme별 샘플 PDF 생성 + 대표님 검토

### Stage 4: 기존 파이프라인 통합 (1일)
- [ ] `presentation_video_generator`에 `source: "marp" | "notebooklm" | "user_pdf"` 분기
- [ ] Marp 경로: `marp-worker`로 마크다운 전송 → PDF 받음 → 기존 파이프라인 투입
- [ ] NotebookLM 경로: ISS-063 `notebooklm_adapter` 재사용
- [ ] User PDF 경로: no-op

### Stage 5: API + UI (0.5일)
- [ ] `POST /api/v1/slides/generate` (Path 1 전용)
- [ ] `/brand-templates` 페이지에 "Marp theme 미리보기" 추가
- [ ] 회원 대시보드에 PPTX 다운로드 버튼

**총 예상**: 4.5~5.5일 (기존 Phase 4 1주 대비 20~35% 절감)

---

## 4. Acceptance (완료 기준)

- [ ] `marp-slide-system.plan.md` 본 문서 (✅ 이 파일)
- [ ] `slide_render_profile.py` 설계 초안 (본 문서 § 2.5)
- [ ] Vertical theme 6종 명세 (본 문서 § 2.3)
- [ ] 한국어 폰트 처리 전략: Pretendard @font-face, 로컬 호스팅
- [ ] Slide Layout Agent 설계: GPT-4o-mini, `script_to_slide_md` task
- [ ] Marp CLI 통합: `marp-worker` sidecar 컨테이너 + HTTP API
- [ ] PPTX 차별화 가치 명세 (본 문서 § 2.6)
- [ ] 기존 Phase 4 plan과 delta 비교 (본 문서 § 5)
- [ ] 예상 작업량 3~5일 (본 문서 § 3)

---

## 5. 기존 Phase 4 Plan과 Delta 비교

| 항목 | 기존 (vrew-videogen-pipeline) | 재설계 (Marp 하이브리드) | Delta |
|---|---|---|---|
| 템플릿 수 | HTML/CSS 48개 (8 × 6) | Marp CSS 6개 + base 1개 | **-85%** 유지보수 |
| 렌더 엔진 | Puppeteer (Python) | Marp CLI (Node sidecar) | **+마이그** 복잡도 +1 |
| 출력 포맷 | Puppeteer 3회 호출 | Marp CLI 1회 호출 | **3x 성능** |
| 한국어 폰트 | 각 템플릿 수동 | `base.css` 단일 @font-face | **DRY 확보** |
| 회원 편집 | PDF only | PDF + 편집 가능 PPTX | **+신기능** |
| 다양성 백업 | 없음 | NotebookLM Path 2 | **+리스크 헷지** |
| 개발 공수 | 7일 | 4.5~5.5일 | **-25~35%** |
| 운영 비용 | Chromium in FastAPI | 전용 sidecar | 컨테이너 +1개 |
| 롤백 가능성 | 어려움 | 쉬움 (source 파라미터) | **+유연성** |

### 주의사항 (전환 리스크)
- **리스크 R1**: Marp theme 한국어 렌더링 엣지 케이스 (줄바꿈, 자간)
  - **완화**: Stage 3 검토 gate에서 대표님 시각 승인
- **리스크 R2**: marp-worker 운영 부담 (Node 생태 운영 경험 필요)
  - **완화**: Marp CLI는 self-contained, auto-restart 설정
- **리스크 R3**: Slide Layout Agent 품질 변동 (GPT-4o-mini)
  - **완화**: Path 2(NotebookLM 수동) 즉시 대체 가능
- **리스크 R4**: PPTX 편집 기대 gap (Marp PPTX는 "이미지 PPTX" 가능성)
  - **완화**: Stage 2 초기에 실 PPTX 열어서 편집 가능성 검증 필수

---

## 6. Dependencies

### 선행 (blocking)
- **ISS-036 Phase 0-A ~ 0-D**: PostgreSQL 마이그레이션 (slide_assets 테이블 이관 대상)
- **ISS-033**: Agency SaaS plan 확정 (vertical 6종 기준)
- **ISS-063**: notebooklm_adapter (Path 2 재사용) ✅ **DONE**
- **ISS-044**: llm_profile (Slide Layout Agent 통합 기반) ✅ **DONE**

### 후속 (enables)
- Phase 5: 영상 렌더 파이프라인 (Marp PDF 투입)
- Phase 6: 회원 편집 UX (PPTX 다운/업 플로우)

---

## 7. Open Questions (대표님 승인 대기)

1. **marp-worker 컨테이너 추가 승인** — Docker Compose에 1개 sidecar 추가 (운영 부담 증가)
2. **Pretendard 라이선스 확인** — 상용 SaaS에 embed 가능 여부 (공식 OFL 확인 필요)
3. **Marp PPTX 편집 가능성 선확인** — Stage 0로 분리, 1시간 spike
4. **vertical theme 6종 vs 12종** — ISS-033 MVWL은 medical 단일, 6종은 v1.1 ramp-up

---

## 8. Next Actions

- [x] 본 plan 문서 작성 완료
- [ ] plan-ceo-reviewer + plan-eng-reviewer 2중 검토 (자동 디스패치)
- [ ] 검토 통과 후 ISS-033 plan_revisions에 Path 1 확정 기록
- [ ] Stage 0 spike: Marp PPTX 편집 가능성 1시간 검증
- [ ] Stage 1 착수 시점: ISS-036 Phase 0-D 완료 후 (약 2~3주 후)

---

**Linked**:
- `docs/01-plan/features/vrew-videogen-pipeline.plan.md` (기존 설계, 본 문서가 대체)
- `backend/app/services/notebooklm_adapter.py` (Path 2, ISS-063)
- `backend/app/services/llm_profile.py` (Slide Layout Agent 기반, ISS-044)
- `backend/app/services/tts_profile.py` (Pattern A 3회차, 본 문서 § 2.5는 4회차)
- `backend/app/services/ffmpeg_profile.py` (Pattern A 1회차, ISS-037)
