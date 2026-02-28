# Plan: upload

## 1. Overview
**Feature**: 목소리 샘플 + PDF 슬라이드 통합 업로드
**Project Level**: Enterprise
**Priority**: High
**PDCA Phase**: Plan
**Created**: 2026-02-28

## 2. Problem Statement
- NotebookLM 등에서 제작한 고품질 PDF 슬라이드를 OmniVibe Pro에 바로 가져올 수 없음
- 사용자 본인의 목소리(클로닝)를 영상에 적용하려면 ElevenLabs voice_id를 직접 입력해야 하는 높은 진입 장벽
- 두 재료(목소리 + PDF) 등록 후 스튜디오로 원클릭 진입하는 통합 흐름 부재

## 3. Solution Vision
> "재료만 넣으면 AI가 영상을 완성한다"

NotebookLM PDF + 내 목소리 샘플 파일을 /upload 페이지에서 한번에 등록하면,
AI가 슬라이드별 스크립트 생성 → Zero-Fault Audio → Remotion 렌더링까지 자동 완성.

## 4. Core Features

### 4.1 목소리 샘플 등록
- 드래그앤드롭 + 클릭 파일 선택 (MP3, WAV, M4A, FLAC, OGG)
- 업로드 전 오디오 미리듣기 (`<audio>` 태그)
- 목소리 이름(필수) / 설명(선택) 입력
- POST /api/v1/voice/clone 연동
- 완료 시 voice_id 표시

### 4.2 PDF 슬라이드 등록
- 드래그앤드롭 + 클릭 파일 선택 (PDF)
- NotebookLM 슬라이드 PDF 권장 안내
- POST /api/v1/presentations/upload 연동
- 완료 시 presentation_id + 슬라이드 수 표시

### 4.3 스튜디오 연동
- 두 파일 모두 완료 시 헤더/하단 CTA "영상 만들기" 버튼 노출
- `/studio?presentation_id=...&voice_id=...` 로 라우팅
- Studio 페이지에서 query parameter 수신 및 자동 적용

### 4.4 UX 가이드
- 파이프라인 단계 배지: 목소리 등록 → PDF 등록 → AI 스크립트 → 영상 완성
- 3단계 사용 가이드 카드
- 에러 메시지 (파일 형식 오류, API 실패)

## 5. Technical Architecture

### Frontend
- `/app/upload/page.tsx` - 통합 업로드 페이지
- `useDrop` 커스텀 훅 - 드래그앤드롭 로직 추상화
- `/components/studio/StudioSidebar.tsx` - 하단 업로드 링크 연결
- `/app/studio/page.tsx` - query params(presentation_id, voice_id) 수신 처리

### Backend (기존 API 활용)
- `POST /api/v1/voice/clone` - ElevenLabs 음성 클로닝
- `POST /api/v1/presentations/upload` - PDF → 슬라이드 이미지 변환

### API 응답 필드 매핑
```
Voice clone response:
  { voice_id, name, status, message }
  → 프론트엔드: data.voice_id

PDF upload response:
  { presentation_id, pdf_path, total_slides, slides[], status }
  → 프론트엔드: data.presentation_id, data.total_slides
```

## 6. Success Criteria
- [x] 목소리 파일 드래그앤드롭 + 파일 선택 동작
- [x] 오디오 미리보기 동작
- [x] POST /api/v1/voice/clone 정확한 FormData 전송
- [x] PDF 파일 드래그앤드롭 + 파일 선택 동작
- [x] POST /api/v1/presentations/upload 정확한 FormData 전송
- [ ] PDF 완료 시 실제 슬라이드 수 표시 (total_slides 필드 정확히 파싱)
- [ ] /studio 라우팅 시 query params 수신 및 적용
- [x] 에러 메시지 표시
- [x] 파이프라인 가이드 UI

## 7. Known Issues (Gap Analysis 결과)
1. **Bug #1 (HIGH)**: `data.slide_count` → `data.total_slides` 필드명 불일치 → 슬라이드 수 0 표시
2. **Bug #2 (MEDIUM)**: DPI 150 하드코딩 → 백엔드 기본값 200과 불일치
3. **Bug #3 (HIGH)**: Studio 페이지 `useSearchParams`에서 `presentation_id`, `voice_id` 미수신

## 8. Timeline
- **Phase 1** (완료): 업로드 페이지 UI + API 연동
- **Phase 2** (진행): 버그 수정 (Gap Analysis 결과 반영)
- **Phase 3** (예정): Studio 페이지 query params 수신 처리
