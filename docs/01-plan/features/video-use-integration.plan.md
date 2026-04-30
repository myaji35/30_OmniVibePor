# Video-Use Integration Plan — Raw Footage Auto-Edit Mode

**Issue**: ISS-147
**Status**: Plan v1 (2026-04-30)
**Owner**: Claude (실행) + 강승식 대표 (방향 컨펌)
**Source**: https://github.com/browser-use/video-use (5.5K ⭐)

---

## 1. 배경 — 영상 제작의 2 카테고리 분기

OmniVibe Pro는 지금까지 **Generation Mode** (스크립트 → TTS+Remotion 합성) 단일 트랙으로 운영되었다.
Agency SaaS 멀티버티컬 plan(ISS-033) 추진 과정에서 **거래처가 보낸 raw 촬영본을 자동 편집**해야 하는 시나리오가 명확해졌다.
browser-use/video-use가 이 시나리오의 OSS 표준이 되었으므로 **두 번째 카테고리로 정식 편입**한다.

| 카테고리 | Generation Mode (기존) | Edit Mode (신규) |
|---|---|---|
| 입력 | 스크립트 / PDF / 시트 | Raw 촬영본 폴더 |
| 음성 처리 | ElevenLabs **TTS** | ElevenLabs **STT (Scribe)** |
| LLM 역할 | Director가 생성 지휘 | LLM이 transcript 읽고 EDL 작성 |
| 렌더 엔진 | Remotion 4.0 (합성) | ffmpeg cut + Remotion 오버레이 |
| 검증 루프 | TTS→STT 재생성 (Zero-Fault Audio) | Self-Eval → 재렌더 (최대 3회) |
| 사용 사례 | 광고, 시술 소개, 강의 | 토킹 헤드, 인터뷰, 현장 정리 |

**공유 자산** (절대 분리 금지): `ffmpeg_profile.py` SoT, `brand-dna.json`, ElevenLabs API 키, Remotion 4.0.429.

---

## 2. 목표

- **Phase A (1주)**: video-use의 Remotion 오버레이 자동 생성 부분만 떼어 우리 백엔드에 포팅. **Generation Mode에도 즉시 가치** (자막 수동 편집 70% 절감 예상).
- **Phase B (4주, PMF 검증 후)**: Edit Mode 풀스택 도입. Agency SaaS Phase 2.

---

## 3. 사전 검증 결과 (2026-04-30)

| 항목 | 결과 | 비고 |
|---|---|---|
| 라이선스 | **확인 불가** (LICENSE 파일 없음) | 도입 전 fork + LICENSE 명시 필수. MIT 추정이지만 작성자 confirm 필요 |
| Remotion 충돌 | **없음** | video-use는 Python only, Remotion은 외부 호출. 우리 4.0.429 그대로 사용 |
| Python 의존성 | requests, librosa, matplotlib, pillow, numpy | 우리 backend에 librosa/matplotlib만 추가하면 됨 |
| ElevenLabs 키 | **공유 가능** | 기존 TTS용 키로 Scribe STT 호출 가능 |
| ffmpeg | 동일 SoT 사용 가능 | 단, video-use 내부 ffmpeg 호출을 우리 `ffmpeg_profile.py`로 강제 wrap 필요 |

---

## 4. Phase A — Remotion Overlay Auto-Gen (1주)

### 4.1 산출물
`backend/app/services/overlay_generator_service.py` (신규)

### 4.2 입출력 계약
```python
# 입력
@dataclass
class OverlayInput:
    word_timestamps: list[WordTimestamp]  # [{word, start, end, speaker_id}]
    style: OverlayStyle  # subtitle / emphasis / animation
    brand_tokens: dict   # brand-dna.json design_tokens

# 출력
@dataclass
class OverlayOutput:
    remotion_jsx: str           # 직접 렌더 가능한 React 컴포넌트
    composition_id: str         # Remotion <Composition id=>
    duration_frames: int        # 30fps 기준
    asset_paths: list[str]      # 폰트/이미지 경로
```

### 4.3 video-use에서 가져올 부분
- `helpers/transcribe.py` — ElevenLabs Scribe 단일 파일 STT (이미 우리도 STT 있지만 word-level + speaker 강화)
- `helpers/timeline_view.py`의 word-segment grouping 로직 — 자막 청킹(2단어 UPPERCASE 등)
- Duration rules — 단순 카드 5–7s, 복합 8–14s, 마지막 1s 홀드, 병렬 reveal 금지

### 4.4 통합 지점
- `app/agents/director_agent.py` → 자막 생성 단계에서 `overlay_generator_service` 호출
- `app/services/audio_correction_loop.py` → STT 결과를 Scribe 형식으로 변환
- `frontend/remotion/Composition.tsx` → 새 `<SubtitleOverlay>` 컴포넌트 슬롯 추가

### 4.5 검증
- [ ] 기존 SubtitleEditor 결과와 자동 생성 결과 동일성 (word-level diff)
- [ ] 30ms 오디오 페이드 자동 적용
- [ ] iOS MP4 출력 확인 (ffmpeg_profile.py SoT 통과)

---

## 5. Phase B — Edit Mode Full Stack (4주, PMF 후)

### 5.1 진입 조건 (Gate)
- ISS-033 medical-dermatology v1 페르소나 5명 인터뷰 완료
- 5명 중 3명 이상이 "거래처 raw 영상 편집 니즈" 명시
- 1편당 Scribe STT 비용 ≤ 500원 (현재 Cost Model 374원 + 여유)

### 5.2 산출물
- `backend/app/services/raw_footage_editor_service.py` — video-use Python skill을 sub-process로 호출
- `frontend/app/edit/page.tsx` — Edit Mode UI (외부 다크/보라 톤, brand-dna 옵션 A 외부 표면)
- `app/agents/director_agent.py` — Edit Mode 분기 추가

### 5.3 Edit Mode 워크플로우
```
사용자가 raw 폴더 업로드 (또는 거래처가 카카오톡/이메일로 전송)
  → backend가 폴더 구조 inventory
  → video-use Skill 실행 (transcribe → pack → LLM EDL → cut → overlay → self-eval)
  → ffmpeg_profile.py로 최종 재인코딩
  → Cloudinary 업로드
  → 거래처 검수 링크 발송 (화이트라벨)
```

---

## 6. 통합 제약 (절대 위반 금지)

1. **`ffmpeg_profile.py` SoT 강제** — video-use 출력은 반드시 우리 프로파일로 재인코딩. 직접 출력 금지.
2. **`brand-dna.json` 옵션 A 이원화 유지** — Edit Mode UI는 외부 다크/보라 (스튜디오 톤), 내부 SLDS Blue 표면.
3. **Director Agent 래핑** — video-use는 항상 Director의 sub-agent로 호출. 사용자가 직접 video-use와 대화하지 않음.
4. **Remotion 4.0.429 버전 잠금** — video-use가 다른 버전 요구하면 우리 fork에서 핀.
5. **ElevenLabs 키 단일화** — TTS + Scribe STT 동일 키. 신규 키 발급 금지.
6. **fork 필수** — `gagahoho-inc/video-use` fork 후 LICENSE 추가 + 우리 SoT 통합 패치.

---

## 7. Open Questions — 결정 완료 (v1.1, 2026-04-30)

CEO 검토(ISS-155) + Eng 검토(ISS-156) 완료. 모든 Q 결정 확정.

| # | 질문 | **결정** | 출처 |
|---|---|---|---|
| Q1 | Phase A를 ISS-033 v1에 편입? | **A 편입** — Remotion 오버레이는 medical에도 즉시 가치 | ISS-155 Q1 |
| Q2 | video-use 도입 방식? | **A fork** — SoT 강제 + LICENSE 명시 (`gagahoho-inc/video-use`) | ISS-155 Q2 |
| Q3 | Edit Mode UI 진입점? | **A /edit 별도 라우트** (CEO Q3 결정으로 추천 B에서 A로 변경) | ISS-155 Q3 |
| Q4 | Phase B 진입 PMF 임계치? | **변경** — 합산 10명(medical 5 + 다른 vertical 5) 중 5명 이상 + Edit 실원가 ≤ 5,000원 | ISS-155 Q4 |

### Eng 보강 사항 (ISS-156 CONDITIONAL_PASS)

Phase B 진입 전 P0 보강 4건 필수:

| # | ISS | 내용 | 분류 |
|---|---|---|---|
| 1 | ISS-162 | Remotion 실제 렌더 smoke 테스트 | Eng P0 |
| 2 | ISS-163 | ffmpeg iOS MP4 실제 출력 검증 | Eng P0 |
| 3 | ISS-164 | Scribe 실제 픽스처 확보 + Whisper fallback 라우터 | Eng P1 |
| 4 | ISS-165 | PMF 인터뷰 10명 (대표님 직접) | PMF P1 |

상세 Gate 조건: `docs/01-plan/features/video-use-phase-B-gate.md`

---

## 8. Risk Register

| # | 리스크 | 임팩트 | 대응 |
|---|---|---|---|
| R1 | video-use 라이선스 미확인 | High | fork 시 작성자 컨택 + 자체 LICENSE 명시 |
| R2 | Scribe STT 비용 폭주 | Medium | 1편당 한도 + 캐시 적극 활용 |
| R3 | Director Agent 통합 복잡도 | Medium | Phase A는 Director 우회, Phase B만 통합 |
| R4 | Edit Mode UX 인지 부조화 | High | 외부 다크 톤 명확히 분리 + 온보딩 가이드 |
| R5 | ffmpeg 체인 우회로 SoT 위반 | Critical | sub-process 출력을 강제 재인코딩 hook |

---

## 9. 다음 액션

1. **Q1~Q4 대표님 컨펌** — Open Questions 결정
2. **video-use fork** — `gagahoho-inc/video-use` 생성 + LICENSE 추가
3. **Phase A 착수** — `overlay_generator_service.py` 스켈레톤 작성 → ISS-147에 USER_STORY 파생
4. **Cost Model 갱신** — Scribe STT 1분당 $0.40 기준 1편 추정치 산출 후 `project_cost_model.md` 업데이트

---

**Last Updated**: 2026-04-30
**Plan Version**: v1.1 (CEO/Eng 검토 반영 — ISS-155, ISS-156)
