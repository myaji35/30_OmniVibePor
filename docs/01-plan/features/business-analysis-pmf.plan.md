# business-analysis-pmf Planning Document

> **Summary**: OmniVibe Pro 비즈니스 관점 이슈 분석 — PMF, MVP 기준, 수익 모델, 경쟁 분석, GTM 전략
>
> **Project**: OmniVibe Pro
> **Version**: 0.1.0
> **Author**: Product Manager Agent
> **Date**: 2026-04-03
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

OmniVibe Pro가 실제로 돈을 버는 제품이 되기 위한 비즈니스 관점 갭을 식별하고,
Phase 4 런칭 준비 전에 전략적 방향을 수정할 기회를 제공한다.

현재 프로젝트는 기술적으로 Phase 3까지 완료된 상태(22페이지, 31개 API, 8개 Remotion Composition)이나,
"누가 왜 돈을 내는가"에 대한 명확한 가설 검증이 선행되지 않았다.

### 1.2 Background

- REALPLAN.md Phase 4 (통합 테스트 + 런칭 준비)가 다음 단계
- 런칭 전 PMF 가설을 명확히 하지 않으면 첫 100명 유료 전환 실패 가능성 높음
- 현재 기능 범위가 매우 넓어(전략 수립 → 영상 생산 → 멀티채널 배포) 핵심 가치 제안이 희석될 위험 존재

### 1.3 Related Documents

- REALPLAN.md — Phase 4, Phase 5 계획
- docs/01-plan/features/template-gallery.plan.md
- docs/01-plan/features/vrew-videogen-pipeline.plan.md
- frontend/app/pricing/page.tsx — 현재 4-Tier 과금 구현

---

## 2. Scope

### 2.1 In Scope

- [x] PMF(Product-Market Fit) 타겟 고객 정의 및 핵심 문제 검증
- [x] MVP 기준 재정의 — 필수 기능 vs 연기 가능 기능
- [x] 4-Tier 가격 체계 적정성 평가
- [x] 경쟁 환경 분석 및 차별점 도출
- [x] 첫 100명 유료 고객 확보 전략(Go-to-Market)
- [x] 22개 페이지 MoSCoW 우선순위 분류

### 2.2 Out of Scope

- 실제 사용자 인터뷰 실행 (이 문서는 가설 기반 분석)
- A/B 테스트 설계 (런칭 후 Phase 5+에서 진행)
- 기술 구현 변경 (분석 결과에 따라 별도 Plan 작성)

---

## 3. PMF 분석

### 3.1 타겟 고객 정의

현재 기능 집합을 기준으로 세 가지 페르소나가 잠재 고객이다.

| 페르소나 | 설명 | 현재 핵심 통증 | 지불 의향 |
|----------|------|---------------|-----------|
| **콘텐츠 크리에이터 (1인)** | YouTube/Instagram/TikTok 채널 운영자, 주 1~3개 영상 제작 | 편집 시간 과다(4~8시간/영상), 나레이션 녹음 장벽 | $15~30/월 |
| **마케터 (팀 소속)** | 브랜드 채널 관리, 제품 설명 영상 정기 제작 필요 | 외주 제작 비용 과다($300~1000/영상), 수정 반복 | $49~99/월 |
| **에듀테크 / 코치** | 강의 영상, 발표 자료 영상화 필요 | PDF → 영상 변환이 수작업, 자막 동기화 어려움 | $19~49/월 |

**핵심 인사이트**: Creator($19) 타겟인 1인 크리에이터가 가장 큰 시장이지만, 전환율이 낮다.
마케터 페르소나(Pro $49)가 실제 LTV(고객 생애 가치)가 높고 전환 의향도 강하다.

### 3.2 현재 기능 vs 핵심 문제 매핑

| 핵심 문제 | 현재 해결 기능 | 완성도 | 격차 |
|-----------|---------------|--------|------|
| 나레이션 자동화 | Zero-Fault Audio (edge-tts/ElevenLabs) | 70% | 음성 품질 선택 UI 미완 |
| 영상 자동 생성 | Remotion VIDEOGEN 파이프라인 | 75% | E2E 성공률 미검증 |
| 템플릿으로 빠른 시작 | Template Gallery (20개 계획) | 30% | 실제 템플릿 0개 |
| 자막 동기화 | SubtitleTimeline + Whisper | 65% | 오차 검증 미완 |
| 멀티채널 배포 | Publish 페이지 | 20% | Phase 5 예정 |

**결론**: 1인 크리에이터 핵심 흐름(스크립트 → 나레이션 → 영상)이 아직 E2E로 연결되지 않은 상태.
PMF를 달성하려면 이 3단계가 "10분 내 첫 영상" 수준으로 매끄러워야 한다.

---

## 4. MVP 기준 재정의

### 4.1 MoSCoW 분류 — 22개 페이지

| 페이지 | 경로 | 분류 | 이유 |
|--------|------|------|------|
| 홈/랜딩 | `/` | **Must** | 첫 인상, 전환 퍼널 시작점 |
| 대시보드 | `/dashboard` | **Must** | 사용자 상태 확인 |
| 갤러리 | `/gallery` | **Must** | 진입 장벽 해소, 빠른 시작 |
| 프로듀스 | `/produce` | **Must** | 핵심 생산 플로우 |
| 오디오 | `/audio` | **Must** | Zero-Fault Audio 차별점 |
| 자막 편집기 | `/subtitle-editor` | **Must** | 영상 품질 핵심 |
| 렌더 | `/render` | **Must** | 최종 결과물 생성 |
| 가격 | `/pricing` | **Must** | 수익 전환 필수 |
| 컨셉 | `/concept` | **Should** | 기획 흐름 지원 |
| 스크립트 편집기 | `/script-editor` | **Should** | 스크립트 세밀 수정 |
| 스토리보드 | `/storyboard` | **Should** | 시각화 지원 |
| 퍼블리시 | `/publish` | **Should** | Phase 4 완성 목표 |
| 전략 | `/strategy` | **Could** | Phase 5 기능 |
| 디렉터 | `/director` | **Could** | AI 오케스트레이션, Phase 5 |
| 라이터 | `/writer` | **Could** | Phase 5 기능 |
| 프레젠테이션 | `/presentation` | **Could** | 에듀테크 니치 |
| 스케줄 | `/schedule` | **Could** | Phase 5 기능 |
| 업로드 | `/upload` | **Should** | 외부 자료 활용 |
| 스튜디오 | `/studio` | **Should** | 콘텐츠 관리 허브 |
| 프로덕션 | `/production` | **Won't (MVP)** | Studio와 중복, 통합 필요 |
| 테스트-웹소켓 | `/test-websocket` | **Won't (MVP)** | 개발 전용, 런칭 전 제거 |
| 프로젝트/[id] | `/project/[id]` | **Must** | 프로젝트 컨텍스트 필수 |

**MVP 필수 페이지 수**: 8개 (Must)
**런칭 후 추가**: 7개 (Should)
**연기/삭제**: 7개 (Could/Won't)

### 4.2 제거/연기 권고

| 항목 | 현재 상태 | 권고 | 이유 |
|------|-----------|------|------|
| `/test-websocket` | 구현됨 | **즉시 제거** | 사용자에게 노출 금지 |
| `/production` | 구현됨 | `/studio`로 통합 | 중복 UX 혼란 |
| `/strategy`, `/director`, `/writer` | 구현됨 | **Phase 5로 연기** | Phase 4 런칭 전에 미완성으로 노출 시 신뢰도 하락 |
| Neo4j GraphRAG | 기본 구조만 | **Phase 4.5 이후** | 런칭에 필수 아님, 비용 증가 |
| ElevenLabs 음성 클로닝 | Creator+에만 포함 | **유지, 단순화** | 차별점이나 설명 복잡 |

---

## 5. 수익 모델 평가

### 5.1 현재 4-Tier 가격 체계 분석

```
Free:        $0   — 렌더 3회/월, 오디오 10회/월
Creator:    $19   — 렌더 30회/월, 음성클론 1개
Pro:        $49   — 렌더 100회/월, API 접근, 우선 지원 (Most Popular)
Enterprise: $499  — 무제한, 화이트라벨, 전담 매니저
```

### 5.2 가격 체계 문제점

**문제 1 — Free tier가 너무 제한적**
- 렌더 3회/월은 체험에 충분하지 않음
- 경쟁사 Canva는 무료로도 상당한 가치 제공
- 권고: Free → **렌더 5회/월 + 워터마크** 전략이 더 효과적 (바이럴 효과)

**문제 2 — Creator($19)와 Pro($49) 격차가 크지 않음**
- Creator에 API 접근 미포함이 차별점으로 약함
- 실제 크리에이터는 API보다 음성 클론 수, 렌더 한도가 더 중요
- 권고: Creator에 **커스텀 썸네일 + 스케줄러** 추가하여 가치 강화

**문제 3 — Enterprise($499) 직접 전환 경로 없음**
- "문의하기" 없이 즉시 결제만 있음
- B2B 고객은 데모, 계약, 커스텀 견적 필요
- 권고: Enterprise는 "데모 요청" CTA로 변경, Calendly 연동

**문제 4 — 연간 할인(20%)이 약함**
- 업계 표준은 연간 결제 시 2개월 무료(~17%) 또는 30~40% 할인
- 권고: **연간 25% 할인** 또는 "2개월 무료" 메시지로 변경

### 5.3 권고 가격 체계

| 티어 | 현재 | 권고 | 변경 이유 |
|------|------|------|-----------|
| Free | 3회 렌더 | **5회 렌더 + 워터마크** | 바이럴, 전환 유도 |
| Creator | $19 | **$19 유지** + 스케줄러 추가 | 가치 강화 |
| Pro | $49 | **$49 유지** + 팀 멤버 3명 | 팀 사용 유도 |
| Enterprise | $499 | **문의 → 데모** | B2B 영업 퍼널 |

---

## 6. 경쟁 분석

### 6.1 직접 경쟁사

| 경쟁사 | 핵심 기능 | 가격 | 약점 |
|--------|-----------|------|------|
| **Pictory** | 텍스트 → 영상 AI | $23~99/월 | Remotion 수준 커스터마이징 불가 |
| **Synthesia** | AI 아바타 영상 | $22~67/월 | 아바타 한정, 범용 영상 불가 |
| **Runway ML** | AI 영상 생성 | $15~76/월 | 프로그래밍 지식 필요 |
| **Opus Clip** | 긴 영상 → 숏폼 클립 | $15~29/월 | 원본 영상 필요, 생성 불가 |
| **HeyGen** | AI 아바타 + 번역 | $29~89/월 | 아바타 중심, 커스터마이징 제한 |

### 6.2 OmniVibe Pro 차별점 (Unique Value Proposition)

**핵심 차별점 3가지**:

1. **React(Remotion) 기반 완전 커스터마이징**
   - 경쟁사들은 템플릿 편집 수준
   - OmniVibe는 코드 수준 커스터마이징 가능
   - 타겟: 개발자 친화적 마케터, 에이전시

2. **Zero-Fault Audio 검증 루프**
   - TTS → STT 자동 검증 → 재생성
   - 경쟁사 대비 발음 오류 자동 수정
   - 한국어 8종 음성 (edge-tts) — 로컬 크리에이터 특화

3. **전략 → 배포 풀파이프라인 (Phase 5)**
   - 단순 영상 생성이 아닌 컨텐츠 운영 자동화
   - GraphRAG 성과 피드백 루프 — 경쟁사 없는 기능

**현재 약점**:
- Phase 5 기능(전략→배포)이 아직 미완성 → 차별점 실증 불가
- 한국어 크리에이터 특화 포지셔닝이 마케팅에 미반영

### 6.3 포지셔닝 권고

```
현재:  "AI 기반 영상 자동화 SaaS" (너무 일반적)

권고:  "한국 크리에이터를 위한 AI 영상 자동화 — 스크립트부터 배포까지"

또는:  "Remotion 기반 프로그래밍 영상 플랫폼 — 개발자 친화 마케터용"
```

---

## 7. Go-to-Market 전략 (첫 100명 유료 전환)

### 7.1 현황 인식

- 현재 가입자 0명 (런칭 전)
- Phase 4 완료 후 omnivibepro.com 공개 예정
- 마케팅 예산 미정

### 7.2 첫 100명 전환 로드맵

**Step 1 — 0→10명: 직접 영업 (런칭 D-14 ~ D+7)**

| 채널 | 방법 | 목표 |
|------|------|------|
| 크리에이터 커뮤니티 | 유튜브 크리에이터 오픈채팅방, 클럽하우스 직접 DM | 10명 베타 초대 |
| 개인 네트워크 | CEO 강승식 LinkedIn/Twitter 공개 빌딩 포스팅 | 5명 무료 체험 |
| Product Hunt 준비 | 한국 시간 기준 화요일 오전 런칭 | 50+ Upvote 목표 |

**Step 2 — 10→50명: 콘텐츠 마케팅 (D+1 ~ D+30)**

| 채널 | 방법 | 목표 |
|------|------|------|
| 데모 영상 | OmniVibe로 만든 영상 5개 YouTube/TikTok 공개 | 1000+ 뷰 |
| "빌드 인 퍼블릭" | 제작 과정 Twitter/LinkedIn 정기 업데이트 | 팔로워 확대 |
| 한국 유튜버 협업 | 무료 Pro 플랜 제공 → 사용 후기 영상 요청 | 협업 3팀 |

**Step 3 — 50→100명: 자동화 퍼널 (D+30 ~ D+60)**

| 채널 | 방법 | 목표 |
|------|------|------|
| Free → Creator 업그레이드 이메일 | 렌더 3회 소진 시 자동 업그레이드 유도 | 30% 전환율 |
| 갤러리 SEO | "유튜브 영상 자동화", "AI 영상 만들기" 키워드 최적화 | 월 500 유기 방문 |
| 레퍼럴 프로그램 | 친구 초대 시 렌더 5회 무료 | 바이럴 계수 1.2+ |

### 7.3 핵심 전환 메트릭 (KPI)

| 메트릭 | 목표 (런칭 후 60일) |
|--------|-------------------|
| 가입자 수 | 500명 |
| Free → Creator 전환율 | 5% (25명) |
| Creator → Pro 전환율 | 20% (5명) |
| MRR (월 반복 수익) | $700+ |
| 첫 영상 완성률 (온보딩) | 40%+ |
| 7일 리텐션 | 30%+ |

---

## 8. 기능 우선순위 최종 정리

### 8.1 Phase 4 런칭 전 반드시 해야 하는 것 (Must)

1. **E2E 플로우 완성**: 갤러리 선택 → 스크립트 → 나레이션 → 렌더 → 다운로드
2. **온보딩 투어 완주 최적화**: 10분 내 첫 영상 완성 경험
3. **Free tier 워터마크 추가**: 바이럴 마케팅 도구로 활용
4. **/test-websocket 페이지 제거**: 사용자 노출 차단
5. **landing page 전환 최적화**: 명확한 USP + CTA

### 8.2 Phase 4 런칭 후 해야 하는 것 (Should)

1. **레퍼럴 프로그램 구현**
2. **이메일 업그레이드 자동화 (Quota 소진 시)**
3. **Enterprise "데모 요청" CTA 변경**
4. **연간 할인 25%로 상향**

### 8.3 Phase 5 이후로 연기 (Could/Won't)

1. **전략 수립 엔진** (/strategy, /director): Phase 5 핵심 — 미완성 노출 금지
2. **멀티채널 배포** (/publish 자동화): Phase 5
3. **GraphRAG 성과 피드백 루프**: Phase 4.5 이후
4. **화이트라벨 API**: Enterprise 전담 영업 확립 후

---

## 9. Success Criteria

### 9.1 Definition of Done

- [ ] 이 분석을 근거로 Phase 4 런칭 체크리스트 업데이트
- [ ] MoSCoW 분류 기반 페이지 접근 제한 or 제거 적용
- [ ] 가격 체계 Free tier 워터마크 + Enterprise CTA 변경
- [ ] GTM 스텝 1 (첫 10명 직접 영업) 실행 계획 수립

### 9.2 Quality Criteria

- [ ] 런칭 후 30일 내 유료 전환 10명 달성
- [ ] 온보딩 첫 영상 완성률 40% 이상
- [ ] NPS (Net Promoter Score) 30+ (초기 10명 기준)

---

## 10. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 한국어 edge-tts 품질이 ElevenLabs 대비 낮아 이탈 | High | Medium | Free tier는 edge-tts, Creator+는 ElevenLabs 분기 적용 |
| 템플릿 20개 준비 전 런칭 → 빈 갤러리 | High | High | Phase 4.4 런칭 콘텐츠 작업에 템플릿 제작 포함, 최소 5개로 소프트 런칭 |
| Remotion E2E 렌더 실패율 > 10% | High | Medium | Phase 4.1 E2E 테스트에서 실패 시나리오 10개 포함 |
| 경쟁사 Pictory/Synthesia 대비 인지도 부족 | Medium | High | "빌드 인 퍼블릭" + 데모 영상 5개로 신뢰 구축 |
| Free tier 남용 → 서버 비용 과다 | Medium | Low | Quota 시스템 Phase 3에서 이미 구현됨 |

---

## 11. Architecture Considerations

### 11.1 Project Level Selection

| Level | Selected |
|-------|:--------:|
| Starter | ☐ |
| Dynamic | ☐ |
| Enterprise | ✅ |

### 11.2 비즈니스 로직 추가가 필요한 영역

| 영역 | 현재 상태 | 필요 작업 |
|------|-----------|-----------|
| Free tier 워터마크 | 없음 | Remotion 렌더링 후 워터마크 오버레이 추가 |
| 업그레이드 이메일 자동화 | 없음 | Celery + SendGrid 연동 |
| Enterprise 데모 요청 | Stripe 즉시 결제만 | Calendly or Hubspot CRM 연동 |
| 레퍼럴 추적 | 없음 | referral_code 필드 + 크레딧 지급 로직 |

---

## 12. Next Steps

1. [ ] CTO 검토 및 승인
2. [ ] Phase 4 런칭 체크리스트에 이 분석 결과 반영
3. [ ] Free tier 워터마크 구현 Design 문서 작성
4. [ ] GTM Step 1 (첫 10명 직접 영업) 실행 계획 별도 문서화
5. [ ] Enterprise CTA 변경 구현 (pricing page 수정)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-03 | Initial draft — PMF, MVP, 수익 모델, 경쟁 분석, GTM | Product Manager Agent |
