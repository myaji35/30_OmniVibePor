---
name: PMF 및 GTM 전략 분석
description: OmniVibe Pro 타겟 페르소나, 가격 체계 문제점, 첫 100명 유료 전환 전략
type: project
---

2026-04-03 비즈니스 분석 결과 요약.

**Why:** Phase 4 런칭 전 PMF 가설 명확화 필요.
**How to apply:** 기능 우선순위 결정 시 이 분석 기반으로 Must/Should/Won't 판단.

**핵심 타겟**: 1인 크리에이터(Creator $19)가 시장 크기는 크나, 마케터(Pro $49)가 LTV 높음.

**가격 체계 주요 문제**
- Free: 렌더 3회/월 → 너무 제한적, 5회+워터마크로 변경 권고
- Enterprise $499: 즉시 결제 → "데모 요청" CTA로 변경 필요
- 연간 할인 20% → 25%로 상향 권고

**MVP 필수 페이지 (Must 8개)**
dashboard, gallery, produce, audio, subtitle-editor, render, pricing, project/[id]

**즉시 제거 대상**
- /test-websocket (개발 전용 페이지, 사용자 노출 금지)
- /production (/studio와 통합)

**Phase 5로 연기 대상**
- /strategy, /director, /writer (미완성 노출 시 신뢰도 하락)

**첫 100명 전환 KPI (런칭 후 60일)**
- 가입자 500명, Free→Creator 전환율 5%, MRR $700+, 온보딩 첫 영상 완성률 40%+

**Plan 문서**: docs/01-plan/features/business-analysis-pmf.plan.md
