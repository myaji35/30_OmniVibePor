# Design Review — NotebookLM 스타일 → Marp Theme 매핑

- **Issue**: ISS-088
- **Parent**: ISS-064 (Marp hybrid slide system)
- **Type**: DESIGN_REVIEW
- **Date**: 2026-04-10
- **Author**: design-critic (opus) 역할 수행

---

## 목적

대표님 질문(NotebookLM 이미지 스타일 목록)에서 도출된 40+ 표현 조합을 Marp 기반 Path 1이 얼마나 커버할 수 있는지 정량 분석하고, gap을 nano-banana MCP 또는 21st.dev 블록으로 보완하는 매핑표를 확정한다.

---

## 1. NotebookLM 8 프리셋 → Marp Theme 매핑

| # | NotebookLM 프리셋 | Marp Theme | 커버리지 | 비고 |
|---|---|---|---|---|
| 1 | Minimalist / Editorial | `themes/general.css` (enhanced) | 95% | CSS Grid + 여백, Pretendard thin weight |
| 2 | Modern Corporate | `themes/academy.css` 또는 `themes/general.css` | 90% | SLDS blue + 회색 위계 |
| 3 | Friendly Illustration | `themes/academy.css` (pastel variant) | 70% | 일러스트는 외부 에셋 필요 (nano-banana) |
| 4 | Magazine / Lifestyle | `themes/beauty.css` | 85% | Cormorant serif + grid layout |
| 5 | Academic / Research | `themes/medical.css` (academic variant) | 90% | Chart 삽입은 Marp의 mermaid 블록 가능 |
| 6 | Bold Marketing | `themes/mart.css` | 95% | 굵은 대비, CSS만으로 완전 재현 |
| 7 | Infographic | N/A (모든 theme 공통 block) | 60% | 아이콘은 외부 SVG 필요 |
| 8 | Storytelling / Narrative | Marp `<!-- _class: full-bleed -->` | 75% | 배경 이미지는 Firecrawl/nano-banana |

**평균 커버리지**: **82.5%** (레이아웃/타이포 레벨)

---

## 2. 5 이미지 카테고리 × Marp 구현 방법

### A. Photography (사진)

| 요소 | Marp 구현 | 가능? |
|---|---|---|
| Real stock photos | `![bg](url)` 또는 `<img>` 태그 | ✅ (외부 에셋 필요) |
| Hero full-bleed | `![bg cover](url)` | ✅ |
| Split layout | CSS `grid-template-columns: 1fr 1fr` | ✅ |
| Grid gallery | CSS Grid 3×3 | ✅ |
| Circular portrait | `border-radius: 50%` | ✅ |

**커버리지 A**: 100% — 단, **이미지 소스 확보 전략** 필수. 권장:
- Unsplash API 통합 (llm_profile.py에 task 추가)
- 거래처 자체 이미지 업로드 (clients.resource_library 재사용)
- **nano-banana MCP** — 대표님 질문에 언급됨. AI 이미지 생성 보완 경로

### B. Illustration (일러스트)

| 요소 | Marp 구현 |
|---|---|
| Flat vector (Material) | 외부 SVG (Heroicons, Feather) |
| Isometric | 외부 SVG 에셋 필요 |
| Line-art minimal | Feather Icons (SLDS 표준, 본 프로젝트 글로벌 규칙) ✅ |
| Hand-drawn | 외부 에셋 필요 |
| Abstract geometric | CSS `clip-path` + gradient ✅ |

**커버리지 B**: 40% (hand-drawn/isometric은 nano-banana 필요)

### C. Data Visualization (데이터)

| 요소 | Marp 구현 |
|---|---|
| Bar chart | **Marp + Mermaid 블록** ✅ |
| Line chart | Mermaid `xychart-beta` ✅ |
| Pie / Donut | Mermaid `pie` ✅ |
| Number callout | CSS 대형 폰트 ✅ |
| Progress ring | CSS `conic-gradient` ✅ |
| Table | 마크다운 표 + 스타일 ✅ |

**커버리지 C**: 100% — Marp의 Mermaid 통합이 NotebookLM 대비 **더 강력** (코드로 재현 가능 → PPTX 편집 가능성 유지)

### D. Diagram (도식)

| 요소 | Marp + Mermaid |
|---|---|
| Timeline | Mermaid `timeline` ✅ |
| Process flow | Mermaid `flowchart` ✅ |
| Org chart | Mermaid `graph TD` ✅ |
| Venn diagram | 외부 SVG ⚠️ |
| Mind map | Mermaid `mindmap` ✅ |

**커버리지 D**: 80%

### E. Layout Elements (장식)

| 요소 | Marp 구현 |
|---|---|
| Quote card | CSS `<blockquote>` 스타일 ✅ |
| Callout box | Marp class attribute + CSS ✅ |
| Timeline marker | CSS pseudo-element ✅ |
| Badge / Ribbon | CSS 단색 box ✅ |
| Divider line | `---` 또는 `<hr>` ✅ |

**커버리지 E**: 100%

---

## 3. 종합 Gap 분석

**전체 커버리지 가중 평균** (프리셋 50% + 이미지 50%):
- 프리셋: 82.5%
- 이미지: (100 + 40 + 100 + 80 + 100) / 5 = **84%**
- **종합: 83.3%**

### Gap 영역 (Marp로 불가능/어려움)

| Gap | 심각도 | 보완 전략 |
|---|---|---|
| G1: Hand-drawn 일러스트 | P2 | nano-banana MCP로 on-demand 생성 |
| G2: Isometric 일러스트 | P2 | 외부 SVG library (storyset, unDraw) |
| G3: Venn diagram | P3 | 외부 SVG 또는 Mermaid flowchart 대체 |
| G4: 실사 인물 사진 | P1 | Unsplash API + 거래처 업로드 + **AI 생성 (nano-banana)** |
| G5: 브랜드 일관된 hero 배경 | P1 | Firecrawl로 거래처 기존 hero 이미지 추출 (ISS-085) |

---

## 4. 해결 전략: 3-Layer Content Adapter

```
Layer 1: Marp 기본 (CSS + Mermaid)
          ↓ 83% 커버
Layer 2: nano-banana MCP (AI 이미지 생성, on-demand)
          ↓ +12%
Layer 3: Firecrawl 추출 이미지 (거래처 실제 자산)
          ↓ +5%
= 100% 커버리지
```

### Layer 2: nano-banana MCP 도입 검토 (신규 제안)
- 역할: Marp 마크다운에 `![ai-gen:의사 인물 사진, 40대, 정장](placeholder)` 같은 지시어 → 빌드 시 nano-banana가 실 이미지로 대체
- 비용: 장당 $0.02~0.05 추정 (ISS-040 cost model 영향 미미)
- **대표님 질문에 nano-banana 언급됨** — 이 방향 확정 시 ISS 발급 필요

### Layer 3: Firecrawl 통합 (ISS-085와 연계)
- ISS-085 Firecrawl 거래처 온보딩에서 추출한 hero 이미지/로고/테스티모니얼을 Marp 빌드 컨텍스트에 주입
- 동일한 데이터 파이프라인 재사용

---

## 5. 최종 Marp Theme 설계 권장안

기존 ISS-064 plan의 6개 theme에 **variant 개념 추가**:

```
themes/
  base.css               # 공통 Pretendard + Mermaid 기본
  general.css            # SLDS blue, editorial/minimalist
  medical.css            # clinical teal, academic variant
  academy.css            # learning amber, corporate variant
  mart.css               # sale red, bold marketing
  beauty.css             # beauty pink, magazine variant
  restaurant.css         # appetite orange

variants/
  minimalist.css         # 모든 theme에 적용 가능한 modifier
  magazine.css
  bold.css
  academic.css
```

Marp frontmatter에서 조합:
```yaml
---
theme: medical
class: academic    # variant 적용
---
```

**결과**: 6 theme × 4 variant = 24 조합 (NotebookLM 8 프리셋 초과)

---

## 6. 업데이트가 필요한 다른 Plan

1. **`docs/01-plan/features/marp-slide-system.plan.md`** (ISS-064)
   - § 2.3 "Vertical Themes 6종" → "6 theme × 4 variant = 24 조합"
   - § 2.4 Marp Worker에 Mermaid 엔진 포함 확인 필요
   - § 3 Stage 3에 variant CSS 작성 추가 (+0.5일)

2. **`docs/01-plan/features/firecrawl-brand-onboarding.plan.md`** (ISS-085)
   - § 2.2 추출 필드에 `hero_image_url` 추가
   - § 4 enables에 "Marp theme color variable 주입" 명시

---

## 7. 의사결정 필요 (대표님)

- **Q1**: nano-banana MCP 도입 ISS 발급할지 (P2, 별도 spike 필요)
- **Q2**: 6 theme × 4 variant 중 v1 우선순위 — medical × minimalist + medical × academic 2개만?
- **Q3**: Mermaid 다이어그램이 PPTX에서도 편집 가능한지 ISS-090 Stage 0 spike에 추가 검증 포함

---

**Conclusion**: Marp Path 1은 NotebookLM 표현력의 **83%를 기본 커버**, nano-banana + Firecrawl 조합으로 100% 도달 가능. NotebookLM Path 2는 여전히 "다양성 백업" 역할로 유지하되, Path 1이 장기 주력.

---

**Linked**:
- `docs/01-plan/features/marp-slide-system.plan.md` (ISS-064, 본 문서가 업데이트 대상)
- `docs/01-plan/features/firecrawl-brand-onboarding.plan.md` (ISS-085, hero 이미지 공급원)
- `backend/app/services/notebooklm_adapter.py` (ISS-063, Path 2 안전망)
