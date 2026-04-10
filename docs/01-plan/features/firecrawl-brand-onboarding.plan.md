# Feature Plan — Firecrawl MCP 기반 거래처 브랜드 자동 온보딩

- **Issue**: ISS-085 (replaces ISS-066 original manual wizard)
- **Parent**: ISS-033 (Agency SaaS Multivertical)
- **Source**: YouTube T0CMHwVh0u4 Level 4 "Firecrawl MCP for Branding"
- **Status**: PLAN (draft)
- **Priority**: P1

---

## 1. Why (배경)

### 1.1 대표님 질문 (2026-04-10)
> "가끔 1인 에이전시 회원(소상공인)을 거론하면서 로고, 상호, 주소 등을 입력하라고 하는데 준비되어 있나?"

**현재 상태 (검증 결과)**:
- DB: `clients` 테이블 존재 (id, name, brand_color, logo_url, industry, contact_email, created_at, updated_at) — 3 rows
- UI: `frontend/components/ClientsList.tsx` 리스트 뷰만 존재
- 누락: `/onboarding`, `/clients/new`, `/clients/[id]/edit` 페이지 전부 없음
- 누락 컬럼: address, phone, website_url, tagline
- 상태: **입력 UI 전무**. 데이터는 테스트 seed 3건뿐.

### 1.2 YouTube Level 4 발견
영상에서 Duncan이 Firecrawl MCP로 "고객사 기존 웹사이트 URL 1줄" → 로고/컬러/카피/타이포를 자동 추출하여 새 랜딩을 만드는 기법 시연.

### 1.3 재설계 철학 전환
기존 ISS-066 안: **5필드 수동 입력 폼** (name/brand_color/logo upload/industry/email)
신규 ISS-085 안: **URL 1필드 입력 → 자동 추출 → 사용자 확인/수정**

**사용자 마찰 비교**:
- 기존: 5~10분 (로고 다운로드 → 업로드 → 컬러 색상표 선택 → 문구 작성)
- 신규: 30초 ~ 1분 (URL 붙여넣기 → 자동 추출 대기 → 확인 클릭)

### 1.4 1인 에이전시 회원 페르소나 정합
1인 에이전시 회원은 동시에 8~20개 거래처 관리 → 거래처별 10분 × 20 = 200분(3시간+) 입력 부담.
자동 추출 시 30초 × 20 = 10분. **95% 시간 절약**.

---

## 2. What (기능 명세)

### 2.1 사용자 흐름 (5-step → 2-step 축약)

```
[기존 ISS-066]
Step 1: 거래처명 입력
Step 2: 브랜드 컬러 선택
Step 3: 로고 파일 업로드
Step 4: 업종 선택
Step 5: 연락처 입력

[신규 ISS-085]
Step 1: 거래처 웹사이트 URL 붙여넣기 (또는 "웹사이트 없음" 수동 경로)
         ↓
     [Firecrawl MCP crawl + AI 분석]
         ↓
Step 2: 추출 결과 확인 + 필요 시 수정 ("이 정보가 맞나요?" 검토 UI)
         ↓
     [저장]
```

### 2.2 Firecrawl MCP 추출 필드

| 추출 필드 | 추출 전략 | 기본값 (fail) |
|---|---|---|
| `name` | `<title>` 또는 `og:site_name` | URL의 도메인명 |
| `logo_url` | `<link rel="icon">`, `og:image`, header `<img>` 중 가장 큰 이미지 | null |
| `brand_color` | CSS 변수 `--primary` + header 배경 픽셀 샘플링 | `#00A1E0` (SLDS default) |
| `tagline` | `<meta name="description">` 또는 hero section h1/h2 | null |
| `address` | footer 파싱 (정규식: 시/구/동 패턴) | null |
| `phone` | `tel:` 링크 또는 footer 정규식 | null |
| `industry` | AI 분류 (LLM: tagline + meta → vertical enum) | "general" |
| `testimonials` | "후기", "리뷰" 섹션 최대 3개 | [] |

### 2.3 신규 DB 컬럼 (clients 테이블 확장)

```sql
ALTER TABLE clients ADD COLUMN website_url TEXT;
ALTER TABLE clients ADD COLUMN address TEXT;
ALTER TABLE clients ADD COLUMN phone TEXT;
ALTER TABLE clients ADD COLUMN tagline TEXT;
ALTER TABLE clients ADD COLUMN auto_extracted_at DATETIME;
ALTER TABLE clients ADD COLUMN extract_source TEXT;  -- 'firecrawl' | 'manual' | 'csv_import'
ALTER TABLE clients ADD COLUMN extract_raw_json TEXT;  -- 원본 추출 결과 (감사용)
```

**주의**: 본 작업은 **ISS-089 Phase 0-B 완료 후** Alembic 마이그레이션으로 진행 (migration revision 002).

### 2.4 신규 API 엔드포인트

```
POST /api/v1/clients/extract
  body: { "website_url": "https://example-clinic.com" }
  response: {
    "extracted": {
      "name": "...",
      "logo_url": "https://cdn.example.com/logo.png",
      "brand_color": "#...",
      ...
    },
    "confidence": 0.85,
    "fallback_used": false
  }

POST /api/v1/clients
  body: { ...extracted fields (user-confirmed)... }
  response: { "id": 4, "created_at": "..." }
```

### 2.5 신규 Frontend 페이지

```
frontend/app/clients/new/page.tsx   (NEW)
  - URL 입력 폼
  - 로딩 (Firecrawl crawl 중)
  - 추출 결과 프리뷰 + 수정 UI
  - 저장 버튼

frontend/app/clients/page.tsx   (NEW or enhance existing list)
frontend/app/clients/[id]/edit/page.tsx   (NEW)
frontend/components/clients/BrandPreviewCard.tsx   (NEW)
frontend/components/clients/ExtractionConfidenceBadge.tsx   (NEW)
```

### 2.6 Fallback 전략

Firecrawl 실패/timeout/제한 시:
1. **Level 1 fallback**: 사용자에게 "웹사이트 파싱 실패. 수동 입력으로 전환" 옵션 제공
2. **Level 2 fallback**: 기존 5-field 수동 폼 재사용 (폐기하지 않고 보조 경로)
3. **Level 3 fallback**: CSV 일괄 import (20개 거래처 한 번에)

---

## 3. How (구현 단계)

### Stage 0: 도구 선정 (0.5일) ✅ 완료 (2026-04-10)
- [x] Firecrawl 조사: Free 500크레딧, Hobby $16/월, MCP 공식 존재
- [x] 네이버 API 조사: 공식 Place API 없음, Search API 최대 5건 제한
- [x] **결정: Firecrawl 보류 → 자체 Playwright 크롤러 우선 개발**
- [x] 이유: 외부 API 의존 최소화, 네이버 스마트플레이스 대응, 비용 $0
- [ ] Firecrawl은 향후 글로벌 확장 시 MCP로 추가 (옵션 유지)

### Stage 1: Backend 추출 서비스 (1일)
- [ ] `backend/app/services/brand_extractor_service.py` (NEW, Pattern A 5회차 후보)
- [ ] `brand_extractor_profile.py` — 추출 전략 상수/fallback 체인
- [ ] MCP client wrapper
- [ ] LLM 기반 vertical 분류 (llm_profile.py의 task 추가)
- [ ] `POST /api/v1/clients/extract` endpoint

### Stage 2: DB 마이그레이션 (0.5일, Phase 0-B 완료 후)
- [ ] Alembic revision 002: clients 테이블 컬럼 추가
- [ ] client.py 모델 업데이트

### Stage 3: Frontend 온보딩 UI (1.5일)
- [ ] `/clients/new` 페이지 (URL 입력 → 추출 → 확인)
- [ ] BrandPreviewCard 컴포넌트 (추출 결과 미리보기)
- [ ] Confidence badge
- [ ] 수동 폼 fallback 경로

### Stage 4: 검증 (0.5일)
- [ ] 실 병의원 3곳 URL 테스트 (의료광고법 섹션 회피)
- [ ] 실 학원 2곳, 마트 1곳 URL 테스트
- [ ] 한국어 사이트 특화 이슈 수집

**총 예상**: 3.5 ~ 4일

---

## 4. Dependencies

**Blocking**:
- **ISS-089** (Phase 0-B PostgreSQL + Alembic) — 마이그레이션 인프라 필요
- **ISS-044** (llm_profile.py) ✅ DONE — vertical 분류 task 추가

**Enables**:
- ISS-033 Agency SaaS 회원 가입 플로우 완성
- ISS-087 21st.dev 블록 라이브러리 (추출된 brand_color 자동 주입)
- ISS-064 Marp hybrid (거래처 brand_color → Marp theme 변수 주입)

---

## 5. Risks

| R# | 리스크 | 완화 |
|---|---|---|
| R1 | Firecrawl 요금 폭증 (1인 에이전시 20 거래처 × 가입) | 캐싱 + 월 1회 재추출 제한 |
| R2 | 의료광고법 민감 섹션 크롤링 | robots.txt 존중 + 거래처 사전 동의 체크박스 |
| R3 | 한국어 사이트 로고 탐지 실패 (일반 img 태그 뒤섞임) | LLM fallback: 스크린샷 → 로고 위치 추출 |
| R4 | 수동 폼 fallback UX 이중 유지 부담 | 동일 form 컴포넌트 재사용 (DRY) |
| R5 | 개인정보 (주소/전화) 저장 법적 책임 | 암호화 + 회원 동의 명시 |

---

## 6. Success Metrics

- **시간 단축**: 거래처 1개 등록 = 기존 10분 → 1분 (90% 절감)
- **완료율**: 온보딩 flow 완료율 60% → 90% (마찰 감소)
- **정확도**: 자동 추출 필드 수정 없이 그대로 저장 비율 70%+
- **1인 에이전시 MVWL #1 달성 기여**: 거래처 20개 등록까지 20분 내

---

## 7. Open Questions

1. Firecrawl MCP vs 자체 Playwright crawler — 요금/컨트롤 trade-off
2. 로고 이미지 CDN 호스팅: Cloudinary 기존 계정 재사용 vs 별도 bucket
3. `extract_raw_json` 보관 기간 (GDPR/개인정보 30일 후 삭제?)
4. 거래처 동의서 전자 서명 기능 필요 여부

---

## 8. Next Action (대표님 승인 후)

1. Stage 0 Firecrawl 요금 조사 (30분) → 결정
2. 승인되면 ISS-089 Phase 0-B 완료 대기 → Stage 1 착수
3. 병행: ISS-090 Marp spike (독립 작업)

---

**Linked**:
- `docs/01-plan/features/marp-slide-system.plan.md` (ISS-064, 본 plan과 brand_color 공유)
- `backend/app/services/llm_profile.py` (vertical 분류 task 추가 대상)
- `frontend/components/ClientsList.tsx` (기존 리스트, 확장 대상)
