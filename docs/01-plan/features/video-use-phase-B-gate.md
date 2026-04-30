# Phase B Gate — Edit Mode 풀스택 진입 조건

**Issue**: ISS-154 (SP-B1)
**Status**: BLOCKED_AT_GATE (2026-04-30 기준)
**Source Plan**: docs/01-plan/features/video-use-integration.plan.md §5
**CEO 검토**: ISS-155 Q4 반영 (2026-04-30)
**Eng 검토**: ISS-156 CONDITIONAL_PASS 반영 (2026-04-30)

---

## Gate 판정 근거

### 현황 요약 (2026-04-30 사실 확인)

| 항목 | 요구 | 현황 | 판정 |
|---|---|---|---|
| PMF 인터뷰 원본 데이터 | 10명 중 5명 니즈 명시 | 가설적 페르소나 5명 (실인터뷰 0건) | FAIL |
| Scribe STT 비용 측정 | Edit 실원가 ≤ 5,000원 | 추정치만 존재 (실측 없음) | FAIL |
| Remotion 실제 렌더 smoke | 완료 | 인터페이스 계약 + mock만 | FAIL |
| ffmpeg iOS MP4 실제 출력 | 완료 | SoT 호출 검증만 | FAIL |
| Scribe 실제 픽스처 | 완료 | mock만 | FAIL |

**결론**: Gate 5개 항목 전체 FAIL. Phase B 착수 불가. BLOCKED_AT_GATE 처리.

---

## 진입 조건 (모두 충족 시 ISS-154 READY 복귀)

### G1. PMF 신호 (CEO 결정 ISS-155 Q4 반영)

원래 조건: ISS-033 페르소나 5명 중 3명 니즈 명시
**변경된 조건 (ISS-155 Q4)**: 합산 10명(medical 5 + 다른 vertical 5) 중 5명 이상이 "거래처 raw 영상 편집" 니즈 명시

- 인터뷰 원본 데이터 저장 경로: `docs/05-research/pmf-interviews/` (디렉터리 미존재 — 인터뷰 진행 시 생성)
- 현재 `docs/audience/agency-video-personas-2026-04-29.md`는 **가설적 페르소나** (방법론 한계 명시됨). PMF 인터뷰 카운트 불인정.
- 검증 책임: 대표님이 직접 인터뷰 진행 + 결과 첨부 → ISS-165 처리
- 인터뷰 최소 기준: 1인 에이전시 사업자 or 병원 실장급 이상, 30분 이상 대화, 녹취/메모 첨부

### G2. Cost Model (CEO 결정 ISS-155 Q4 반영)

원래 조건: Scribe STT 1편당 ≤ 500원
**변경된 조건 (ISS-155 Q4)**: Edit 1편 실원가 ≤ 5,000원 (Generation 374원 대비 13.4배 한도)

- Scribe 비용 추정: ElevenLabs $0.40/분 × 5분 영상 = $2.00 = 약 2,640원
- 나머지 여유: 5,000 - 2,640 = 2,360원 (ffmpeg 처리 + Cloudinary 업로드)
- 비용 측정 방법: 실제 5분 영상 3편 처리 후 API 청구액 실측
- 가격 정책: Generation 정액 + Edit 종량제 분리 정책 확정 필수
- 검증 책임: ISS-162~164 Eng 보강 완료 후 실측 가능

### G3. Eng 보강 (ISS-156 Eng 검토 P0 반영)

Phase B 진입 전 아래 4건이 모두 완료되어야 한다:

| # | ISS | 내용 | 우선순위 |
|---|---|---|---|
| G3-a | ISS-162 | Remotion 실제 렌더 smoke 테스트 (현재 인터페이스만) | P1 |
| G3-b | ISS-163 | ffmpeg iOS MP4 실제 출력 검증 (현재 SoT 호출만) | P1 |
| G3-c | ISS-164 | Scribe 실제 응답 픽스처 확보 + Whisper fallback 라우터 | P1 |
| G3-d | ISS-165 | PMF 인터뷰 10명 진행 (비기술, 대표님 직접) | P1 |

---

## Gate 통과 시 산출물 — Phase B 4주 분해 (후보)

Gate 충족 시 ISS-154 status를 READY로 복귀시키고 아래 USER_STORY를 registry에 발급한다.
**현재는 registry에 추가 금지 — 문서에만 기록.**

| ISS | 주차 | USER_STORY |
|---|---|---|
| SP-B1.1 | W1 | video-use Python skill을 sub-process로 호출하는 어댑터 (`raw_footage_editor_service.py`) |
| SP-B1.2 | W1 | Edit Mode UI 진입점 — `/edit` 별도 라우트 (CEO Q3 결정) |
| SP-B1.3 | W2 | Director Agent에 Edit Mode 분기 추가 |
| SP-B1.4 | W2 | 거래처 검수 링크 발송 (화이트라벨) |
| SP-B1.5 | W3 | Cost Model 동적 계산 (편당 분 단위 과금) |
| SP-B1.6 | W3 | Edit Mode 회귀 테스트 + 모니터링 |
| SP-B1.7 | W4 | Beta 사용자 5명 출시 + 피드백 수집 |

---

## Unblock 체크리스트

Gate 재진입 조건 (모두 DONE 시 ISS-154 READY 전환):

- [ ] G3-a: ISS-162 DONE (Remotion smoke)
- [ ] G3-b: ISS-163 DONE (ffmpeg iOS 실출력)
- [ ] G3-c: ISS-164 DONE (Scribe 픽스처 + Whisper fallback)
- [ ] G1: ISS-165 DONE (PMF 인터뷰 10명 — 5명 이상 Edit 니즈 확인)
- [ ] G2: Edit 실원가 ≤ 5,000원 실측 확인 (ISS-162~164 완료 후 측정)

---

**Created**: 2026-04-30
**Next Review**: ISS-162~165 완료 시 자동 재평가
