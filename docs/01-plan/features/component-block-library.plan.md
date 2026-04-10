# Feature Plan — 21st.dev 스타일 컴포넌트 블록 라이브러리

- **Issue**: ISS-087
- **Source**: YouTube T0CMHwVh0u4 Level 3 "How to Pull Components from 21st.dev"
- **Priority**: P2
- **Status**: PLAN

---

## 1. 현재 상태

`/brand-templates` 페이지: empty state ("아직 템플릿이 없습니다") + 4 placeholder 변수 (`{{presentation_title}}` 등). 사실상 미구현.

## 2. 21st.dev 도입 조사

### 21st.dev란?
- Figma-grade React/Tailwind 컴포넌트 저장소
- Claude Code에서 MCP로 직접 컴포넌트를 끌어와서 조립 가능 (YouTube 영상 시연)
- 라이선스: 컴포넌트별 상이 (MIT/Apache 2.0 등)

### MCP 유무
- 21st.dev 공식 MCP: **미확인** — YouTube 영상에서는 Firecrawl로 21st.dev 사이트를 크롤해서 컴포넌트 코드를 가져오는 방식 시연
- **대안**: 직접 컴포넌트 카탈로그를 OmniVibe 내부에 구축 (21st.dev "스타일"만 차용, 코드는 자체 작성)

### 본 프로젝트 판단
21st.dev를 MCP로 연동하기보다, **21st.dev의 "카테고리별 블록 조립" 패러다임**을 차용하여 **자체 블록 라이브러리**를 구축하는 것이 적합:
- SLDS 디자인 토큰과 21st.dev 기본 스타일 충돌 회피
- brand-dna surfaces 규칙 완전 준수 가능
- 라이선스 의존성 0

---

## 3. 블록 카테고리 정의

| # | 블록 카테고리 | 설명 | 슬라이드 용도 |
|---|---|---|---|
| 1 | **Hero** | 전면 배경 이미지 + 헤드라인 + CTA | 첫 슬라이드 |
| 2 | **Split** | 좌 이미지 / 우 텍스트 (또는 반대) | 시술/서비스 소개 |
| 3 | **Grid** | 2×2 또는 3×3 카드 그리드 | 메뉴/가격표/서비스 목록 |
| 4 | **Quote** | 따옴표 + 인물 사진 + 이름 | 환자 후기/리뷰 |
| 5 | **Infographic** | 아이콘 + 숫자 + 짧은 텍스트 | 통계/성과/비교 |
| 6 | **CTA** | 연락처 + 지도 + 행동 유도 | 마지막 슬라이드 |

---

## 4. 업종 × 블록 2D 매트릭스

ISS-056 (voice × vertical) 패턴 재사용:

| | Hero | Split | Grid | Quote | Infographic | CTA |
|---|---|---|---|---|---|---|
| **medical** | 원장 + 클리닉 외관 | 시술 전/후 | 시술 메뉴 3~6개 | 환자 후기 | 시술 건수/만족도 | 진료 예약 |
| **academy** | 학원 로고 + 슬로건 | 커리큘럼 소개 | 과목별 강좌 | 수강생 합격 후기 | 합격률/수강생 수 | 무료 상담 |
| **mart** | 이번 주 특가 배너 | 인기 상품 | 카테고리별 가격 | 고객 리뷰 | 할인율/매장 수 | 배달 주문 |
| **beauty** | 시술 결과 비포애프터 | 시술 과정 | 가격표 | 고객 후기 | 시술 건수 | 예약 |
| **restaurant** | 대표 메뉴 사진 | 셰프 소개 | 전체 메뉴 | 방문 후기 | 평점/리뷰 수 | 예약/배달 |
| **general** | 브랜드 로고 + 슬로건 | 서비스 소개 | 서비스 목록 | 고객 추천 | 핵심 수치 | 문의 |

**총 36개 블록 variant** (6 vertical × 6 category)

v1 scope: **medical × 6 블록 = 6개만** (MVWL 정합)

---

## 5. 구현 단계

### Stage 1: 블록 컴포넌트 설계 (1일)
- [ ] `frontend/components/blocks/HeroBlock.tsx` (props: title, subtitle, bgImage, cta)
- [ ] `frontend/components/blocks/SplitBlock.tsx`
- [ ] `frontend/components/blocks/GridBlock.tsx`
- [ ] `frontend/components/blocks/QuoteBlock.tsx`
- [ ] `frontend/components/blocks/InfographicBlock.tsx`
- [ ] `frontend/components/blocks/CTABlock.tsx`
- [ ] 공통 props interface: `BlockProps { vertical, brandColor, content, images }`

### Stage 2: medical variant 6개 (1일)
- [ ] 각 블록에 medical 프리셋 (컬러 #0891b2, 의료 용어, 시술 이미지 slot)
- [ ] `/brand-templates` 페이지 재구성: 블록 카탈로그 UI (드래그 가능)
- [ ] 블록 미리보기 렌더

### Stage 3: Marp/python-pptx 통합 (0.5일)
- [ ] 블록 → Marp 마크다운 변환 함수 (ISS-064 Stage 2 연동)
- [ ] 블록 → python-pptx 슬라이드 변환 함수 (Path 4)

### Stage 4: 나머지 vertical (Phase 2, 별도 ISS)
- academy, mart, beauty, restaurant, general 각 6 블록씩 추가

**v1 총 예상**: 2.5일

---

## 6. Dependencies

- **ISS-085** Firecrawl 온보딩 → 거래처 brand_color/logo 자동 주입
- **ISS-064** Marp 하이브리드 → 블록 → 마크다운 변환
- **ISS-086** Design Skill → 블록 variant 품질 보장

---

## 7. Risks

| R# | 리스크 | 완화 |
|---|---|---|
| R1 | 36 variant 관리 부담 | v1은 medical 6개만. 나머지는 PMF 후 |
| R2 | 블록 조합 시 레이아웃 깨짐 | CSS Grid 기반 + 블록 간 spacing 토큰 통일 |
| R3 | 이미지 slot 관리 복잡 | Cloudinary URL 패턴 + ISS-085 추출 이미지 재사용 |
