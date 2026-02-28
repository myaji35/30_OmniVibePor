# Plan: remotion-integration

## 1. Overview
**Feature**: Remotion 완전 통합 - 실시간 미리보기 + 멀티포맷 렌더링 파이프라인
**Project Level**: Enterprise
**Priority**: High
**PDCA Phase**: Plan

## 2. Problem Statement
현재 OmniVibe Studio는 가짜 "Neural Rendering" UI를 보여주는 상태로,
Remotion 템플릿(YouTube/Instagram/TikTok) 3개가 존재하지만 실제 연결되지 않음.
- `@remotion/player` 미설치 → 실시간 미리보기 불가
- 오디오(ElevenLabs)와 영상 프레임 미동기화
- 씬별 전문 컴포넌트 없음 (단순 ScriptBlock만 존재)
- Backend Remotion 렌더러 미구현 → MP4 출력 불가

## 3. Goals
1. StudioPreview를 실제 Remotion Player로 교체
2. 5개 씬 타입별 전문 컴포넌트 구현 (Hook/Intro/Body/CTA/Outro)
3. Whisper 타임스탬프 → Remotion Sequence 자동 동기화
4. Backend FastAPI + Celery로 멀티포맷 렌더링 (YouTube/IG/TikTok)
5. WebSocket으로 렌더링 진행률 실시간 전송

## 4. Scope

### In Scope
- `@remotion/player` 설치 및 StudioPreview 교체
- `remotion/scenes/` 5개 씬 컴포넌트 신규 구현
- Whisper Word-level Timestamp → Remotion Sequence 매핑
- Backend: `/api/v1/render/` 엔드포인트 + Celery 렌더링 태스크
- 멀티포맷 자동 변환 (1920×1080 / 1080×1350 / 1080×1920)
- WebSocket 렌더링 진행률 연동

### Out of Scope
- Remotion Cloud (자체 서버 렌더링 사용)
- 3D 애니메이션 씬
- 실시간 협업 편집

## 5. Technical Requirements

### Frontend
- `@remotion/player`: ^4.0.0
- `remotion`: ^4.0.0 (이미 Root.tsx에서 사용 중)
- TypeScript strict mode 준수

### Backend
- `@remotion/renderer`: Python subprocess via Docker
- Celery 태스크로 비동기 렌더링
- Cloudinary로 렌더링 결과 업로드

## 6. Implementation Phases

### Phase 1: Remotion Player 통합 (Day 1)
- `@remotion/player` 설치
- `StudioPreview.tsx` → 실제 Player 컴포넌트로 교체
- `Root.tsx` 동적 props 지원

### Phase 2: 씬 컴포넌트 (Day 1-2)
- `remotion/scenes/HookScene.tsx`
- `remotion/scenes/IntroScene.tsx`
- `remotion/scenes/BodyScene.tsx`
- `remotion/scenes/CTAScene.tsx`
- `remotion/scenes/OutroScene.tsx`

### Phase 3: 오디오 동기화 (Day 2-3)
- Whisper 타임스탬프 파싱 유틸리티
- ScriptBlock 자동 타이밍 매핑
- Word-level 자막 컴포넌트

### Phase 4: Backend 렌더링 (Day 3-4)
- `/api/v1/render/start` 엔드포인트
- `render_video_task` Celery 태스크
- Cloudinary 업로드 연동

### Phase 5: 멀티포맷 파이프라인 (Day 4-5)
- YouTube/Instagram/TikTok 동시 렌더링
- WebSocket 진행률 전송
- 렌더링 결과 UI 표시

## 7. Success Criteria
- [ ] StudioPreview에서 실제 Remotion Player 동작
- [ ] 5개 씬 컴포넌트 각각 독립 렌더링 가능
- [ ] 오디오와 자막 타이밍 오차 < 100ms
- [ ] YouTube MP4 렌더링 완료 (테스트 영상)
- [ ] WebSocket으로 렌더링 진행률 수신

## 8. Agent Team Strategy (Enterprise)
| 역할 | 담당 | 작업 |
|------|------|------|
| remotion-architect | 설계 리드 | 씬 구조 설계, 타입 정의 |
| remotion-frontend | 프론트 구현 | Player 통합, 씬 컴포넌트 |
| remotion-backend | 백엔드 구현 | 렌더링 API, Celery 태스크 |
| remotion-qa | 품질 검증 | 렌더링 테스트, 타임스탬프 검증 |

## 9. Timeline
- **Start**: 2026-02-28
- **Target Completion**: 2026-03-04 (5 working days)

## 10. References
- Current Remotion files: `frontend/remotion/`
- Studio page: `frontend/app/studio/page.tsx`
- StudioPreview: `frontend/components/studio/StudioPreview.tsx`
- Remotion docs: https://www.remotion.dev/docs
