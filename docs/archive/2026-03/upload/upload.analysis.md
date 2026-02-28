# Upload Feature Analysis Report

> **Analysis Type**: Gap Analysis (Requirements vs Implementation)
>
> **Project**: OmniVibe Pro
> **Version**: 1.0.0
> **Analyst**: bkit-gap-detector
> **Date**: 2026-02-28
> **Design Doc**: Plan 문서 부재 - 대화 기반 요구사항 추출

### Pipeline References

| Phase | Document | Verification Target |
|-------|----------|---------------------|
| Plan | (대화에서 추출) | 10개 기능 요구사항 |
| Backend API | `backend/app/api/v1/voice.py` | Voice Clone 엔드포인트 |
| Backend API | `backend/app/api/v1/presentation.py` | Presentation Upload 엔드포인트 |
| Backend Models | `backend/app/models/presentation.py` | Pydantic 응답 모델 |
| Frontend | `frontend/app/upload/page.tsx` | Upload 페이지 구현 |
| Frontend | `frontend/components/studio/StudioSidebar.tsx` | 사이드바 링크 |

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

사용자 요구사항(목소리 샘플 + PDF 등록 -> 영상 제작 파이프라인)의 프론트엔드 구현이 백엔드 API 스펙과 정확히 일치하는지 검증한다. Plan/Design 문서가 없으므로 대화에서 추출한 10개 기능 요구사항을 기준으로 삼는다.

### 1.2 Analysis Scope

- **요구사항 출처**: 대화에서 추출 (10개 항목)
- **프론트엔드 구현**: `frontend/app/upload/page.tsx` (592 lines)
- **백엔드 API**: `backend/app/api/v1/voice.py`, `backend/app/api/v1/presentation.py`
- **백엔드 모델**: `backend/app/models/presentation.py`
- **타입 정의**: `frontend/lib/types/presentation.ts`
- **분석일**: 2026-02-28

---

## 2. Requirements Gap Analysis

### 2.1 기능 요구사항 체크리스트

| # | 요구사항 | 구현 상태 | 근거 | 비고 |
|---|----------|:---------:|------|------|
| 1 | Voice 업로드: MP3/WAV/M4A/FLAC/OGG 드래그앤드롭 + 파일 선택 | ✅ | `page.tsx:106` 확장자 검증, `page.tsx:292-317` 드롭존 구현 | `useDrop` 커스텀 훅으로 D&D + input file 모두 지원 |
| 2 | Voice 미리보기: 업로드 전 오디오 재생 확인 | ✅ | `page.tsx:112` `URL.createObjectURL`, `page.tsx:341` `<audio>` 태그 | 파일 선택 즉시 미리듣기 가능 |
| 3 | 목소리 이름/설명 입력: 필수/선택 입력 필드 | ✅ | `page.tsx:349-369` 이름(필수), 설명(선택) 입력 | 이름 미입력 시 에러 메시지 표시 (`page.tsx:136`) |
| 4 | Voice API 연동: POST /api/v1/voice/clone | ✅ | `page.tsx:142-168` FormData로 user_id, voice_name, description, audio_file 전송 | 응답에서 `voice_id` 또는 `elevenlabs_voice_id` fallback 처리 |
| 5 | PDF 업로드: PDF 드래그앤드롭 + 파일 선택 | ✅ | `page.tsx:120-127` 확장자 검증, `page.tsx:434-460` 드롭존 | Voice와 동일한 `useDrop` 훅 재사용 |
| 6 | PDF API 연동: POST /api/v1/presentations/upload | ⚠️ | `page.tsx:172-203` FormData 전송 | **2가지 버그 발견** (아래 상세 분석) |
| 7 | 완료 상태 표시: voice_id, presentation_id, slide_count | ⚠️ | `page.tsx:400-411` Voice 완료, `page.tsx:514-529` PDF 완료 | slide_count가 항상 0 표시 (버그) |
| 8 | 스튜디오 연동: 두 파일 완료 시 /studio?... 라우팅 | ⚠️ | `page.tsx:207-212` `goToStudio()` 함수 | Studio 페이지에서 query param을 수신하지 않음 |
| 9 | 에러 처리: 형식 오류, API 실패 메시지 표시 | ✅ | Voice: `page.tsx:107-109,372-377`, PDF: `page.tsx:121-123,486-491` | 파일 형식, API 에러 모두 처리 |
| 10 | 파이프라인 가이드: 사용자에게 흐름 설명 UI | ✅ | `page.tsx:255-268` 상단 스텝 표시, `page.tsx:560-587` 하단 3-step 가이드 카드 | 단계별 시각적 안내 구현 |

### 2.2 Match Rate Summary

```
+---------------------------------------------+
|  Requirements Match Rate: 75%                |
+---------------------------------------------+
|  ✅ 완전 구현:   7 items (70%)               |
|  ⚠️ 부분 구현:   3 items (30%)               |
|  ❌ 미구현:       0 items  (0%)               |
+---------------------------------------------+
```

---

## 3. API Field Mismatch Analysis (Critical Bugs)

### 3.1 Bug #1: PDF 응답 필드명 불일치 (slide_count vs total_slides)

| 항목 | 값 |
|------|-----|
| **심각도** | HIGH |
| **위치** | `frontend/app/upload/page.tsx:195` |
| **증상** | PDF 업로드 성공 후 슬라이드 수가 항상 0으로 표시됨 |

**프론트엔드 코드 (현재):**
```typescript
// page.tsx:37-41 - PdfResult 타입 정의
interface PdfResult {
    presentation_id: string;
    slide_count: number;       // <-- 잘못된 필드명
    message: string;
}

// page.tsx:193-197 - 응답 파싱
setPdfResult({
    presentation_id: data.id || data.presentation_id || `pres_${Date.now()}`,
    slide_count: data.slide_count || 0,   // <-- data.slide_count는 존재하지 않음
    message: data.message || "PDF가 성공적으로 업로드되었습니다.",
});
```

**백엔드 실제 응답 (PresentationUploadResponse):**
```python
# backend/app/models/presentation.py:97-104
class PresentationUploadResponse(BaseModel):
    presentation_id: str
    pdf_path: str
    total_slides: int        # <-- 실제 필드명은 total_slides
    slides: List[SlideInfo]
    status: PresentationStatus
    created_at: datetime
```

**영향 범위:**
- `page.tsx:521-522` - 완료 상태에서 "슬라이드 N장 추출됨" 대신 fallback 메시지 표시
- `frontend/lib/types/presentation.ts:91` - 이미 `total_slides`로 올바르게 정의되어 있으나 upload 페이지에서 참조하지 않음

**수정 방안:**
```typescript
// PdfResult 인터페이스 수정
interface PdfResult {
    presentation_id: string;
    total_slides: number;     // slide_count -> total_slides
    message: string;
}

// 응답 파싱 수정
setPdfResult({
    presentation_id: data.presentation_id || `pres_${Date.now()}`,
    total_slides: data.total_slides || 0,  // slide_count -> total_slides
    message: data.message || "PDF가 성공적으로 업로드되었습니다.",
});
```

---

### 3.2 Bug #2: PDF DPI 값 불일치 (150 vs 200)

| 항목 | 값 |
|------|-----|
| **심각도** | MEDIUM |
| **위치** | `frontend/app/upload/page.tsx:181` |
| **증상** | 슬라이드 이미지 품질이 백엔드 기본값(200 DPI) 대비 25% 저하 |

**프론트엔드 코드:**
```typescript
// page.tsx:181
form.append("dpi", "150");    // 150 DPI 하드코딩
```

**백엔드 기본값:**
```python
# presentation.py:43
dpi: int = Form(200, description="슬라이드 이미지 해상도 (DPI)")

# models/presentation.py:33
dpi: int = Field(200, description="슬라이드 이미지 해상도 (DPI)")
```

**코드베이스 일관성 검증:**
| 파일 | DPI 값 | 상태 |
|------|:------:|:----:|
| `backend/app/api/v1/presentation.py:43` | 200 | 기준값 |
| `backend/app/models/presentation.py:33` | 200 | 일치 |
| `backend/app/services/pdf_processor.py:40` | 200 | 일치 |
| `frontend/components/PresentationMode.tsx:125` | 200 | 일치 |
| `frontend/app/studio/content/[id]/edit/page.tsx:86` | 200 | 일치 |
| `frontend/app/upload/page.tsx:181` | **150** | **불일치** |
| `backend/test_pdf_processor.py:39` | 150 | 테스트용 (의도적) |

프론트엔드 upload 페이지만 유일하게 150을 사용하고 있음. 백엔드 기본값 200과 통일해야 함.

---

### 3.3 Bug #3: Studio 페이지 Query Parameter 미수신

| 항목 | 값 |
|------|-----|
| **심각도** | HIGH |
| **위치** | `frontend/app/studio/page.tsx:101-121` |
| **증상** | Upload에서 전달한 voice_id, presentation_id가 Studio에서 무시됨 |

**Upload 페이지 (송신 측):**
```typescript
// page.tsx:207-212
const goToStudio = () => {
    const params = new URLSearchParams();
    if (pdfResult?.presentation_id) params.set("presentation_id", pdfResult.presentation_id);
    if (voiceResult?.voice_id) params.set("voice_id", voiceResult.voice_id);
    router.push(`/studio?${params.toString()}`);
};
```

**Studio 페이지 (수신 측):**
```typescript
// studio/page.tsx:101-121
const searchParams = useSearchParams();

useEffect(() => {
    const contentIdParam = searchParams.get("contentId");    // contentId만 처리
    const durationParam = searchParams.get("duration");      // duration만 처리
    const modeParam = searchParams.get("mode");              // mode만 처리
    // presentation_id, voice_id에 대한 처리 없음
}, [searchParams]);
```

**결론:** Upload -> Studio 연동이 단방향으로만 구현되어 있음. Studio에서 `presentation_id`와 `voice_id`를 받아 자동 워크플로우를 시작하는 로직이 필요.

---

## 4. API Endpoint Comparison

### 4.1 Voice Clone API

| 항목 | Backend 스펙 | Frontend 구현 | 상태 |
|------|-------------|--------------|:----:|
| Endpoint | `POST /api/v1/voice/clone` | `${API_BASE}/api/v1/voice/clone` | ✅ |
| `user_id` (required) | `Form(...)` | `form.append("user_id", "local_user")` | ⚠️ |
| `voice_name` (required) | `Form(...)` | `form.append("voice_name", voiceName.trim())` | ✅ |
| `description` (optional) | `Form("")` | `form.append("description", voiceDesc.trim() \|\| "사용자 음성 샘플")` | ✅ |
| `audio_file` (required) | `File(...)` | `form.append("audio_file", voiceState.file)` | ✅ |
| Response: `voice_id` | `VoiceCloneResponse.voice_id` | `data.voice_id \|\| data.elevenlabs_voice_id \|\| "test_voice_id"` | ⚠️ |
| Response: `name` | `VoiceCloneResponse.name` | 사용하지 않음 (voiceName으로 대체) | ⚠️ |
| Response: `status` | `VoiceCloneResponse.status` | 사용하지 않음 ("completed" 하드코딩) | ⚠️ |
| Response: `message` | `VoiceCloneResponse.message` | 사용하지 않음 | ⚠️ |

**세부 이슈:**
1. `user_id`가 `"local_user"`로 하드코딩 - 멀티유저 환경에서 문제 (현재 MVP 단계에서는 허용 가능)
2. `voice_id` fallback 체인이 과도함 - `data.elevenlabs_voice_id`는 백엔드 응답에 존재하지 않는 필드
3. 응답의 `status`, `message` 필드를 무시하고 프론트엔드에서 하드코딩

### 4.2 Presentation Upload API

| 항목 | Backend 스펙 | Frontend 구현 | 상태 |
|------|-------------|--------------|:----:|
| Endpoint | `POST /api/v1/presentations/upload` | `${API_BASE}/api/v1/presentations/upload` | ✅ |
| `file` (required) | `File(...)` | `form.append("file", pdfState.file)` | ✅ |
| `project_id` (required) | `Form(...)` | `form.append("project_id", \`proj_${Date.now()}\`)` | ⚠️ |
| `dpi` (optional, default=200) | `Form(200)` | `form.append("dpi", "150")` | ❌ |
| `lang` (optional) | `Form("kor+eng")` | `form.append("lang", "kor+eng")` | ✅ |
| Response: `presentation_id` | `PresentationUploadResponse.presentation_id` | `data.id \|\| data.presentation_id` | ⚠️ |
| Response: `total_slides` | `PresentationUploadResponse.total_slides` | `data.slide_count` (잘못된 필드명) | ❌ |
| Response: `pdf_path` | `PresentationUploadResponse.pdf_path` | 사용하지 않음 | -- |
| Response: `slides[]` | `PresentationUploadResponse.slides` | 사용하지 않음 | -- |
| Response: `status` | `PresentationUploadResponse.status` | 사용하지 않음 | -- |

**세부 이슈:**
1. `project_id`가 타임스탬프 기반 임시 ID - 프로젝트 관리와 연결되지 않음
2. `data.id` fallback은 백엔드 응답에 존재하지 않는 필드
3. **`total_slides` 필드를 `slide_count`로 잘못 참조 (Critical Bug)**

---

## 5. Type System Consistency

### 5.1 Frontend 타입 정의 vs Upload 페이지 로컬 타입

| 항목 | `lib/types/presentation.ts` | `upload/page.tsx` 로컬 타입 | 상태 |
|------|----------------------------|---------------------------|:----:|
| 슬라이드 수 필드 | `total_slides: number` | `slide_count: number` | ❌ 불일치 |
| 응답 타입 사용 | `PresentationUploadResponse` 정의됨 | 자체 `PdfResult` 인터페이스 사용 | ⚠️ |
| Voice 응답 타입 | (미정의) | 자체 `VoiceResult` 인터페이스 사용 | -- |

Upload 페이지가 이미 존재하는 `frontend/lib/types/presentation.ts`의 `PresentationUploadResponse` 타입을 사용하지 않고 독자적인 `PdfResult` 인터페이스를 정의하여 필드명 불일치가 발생했음.

---

## 6. UX/UI Analysis

### 6.1 구현된 UX 패턴

| UX 항목 | 구현 여부 | 품질 |
|---------|:---------:|:----:|
| 드래그앤드롭 시각 피드백 (border 색상 변경) | ✅ | 우수 |
| 파일 선택 후 미리보기 (Voice: 오디오 재생) | ✅ | 우수 |
| 파일 선택 후 미리보기 (PDF: 파일명/크기) | ✅ | 양호 |
| 업로드 중 로딩 스피너 | ✅ | 우수 |
| 완료 상태 체크마크 | ✅ | 우수 |
| 에러 메시지 표시 | ✅ | 우수 |
| 파이프라인 스텝 안내 | ✅ | 우수 |
| 두 파일 완료 시 CTA 버튼 | ✅ | 우수 |
| 파일 제거 (X 버튼) | ✅ | 양호 |
| 반응형 레이아웃 | ✅ | 양호 (lg 브레이크포인트) |

### 6.2 누락된 UX 항목

| 항목 | 설명 | 심각도 |
|------|------|:------:|
| PDF 첫 페이지 썸네일 미리보기 | 업로드 전 PDF 내용 확인 불가 | LOW |
| 파일 크기 제한 안내 | 최대 업로드 크기가 표시되지 않음 | LOW |
| 업로드 진행률 표시 | 대용량 파일 시 진행 상황 불명확 (로딩 스피너만 존재) | MEDIUM |
| 오디오 파일 길이 검증 | 클라이언트 측에서 최소 1분 / 권장 3-5분 검증 없음 | LOW |
| Memory leak 방지 | `URL.createObjectURL` 생성 후 `URL.revokeObjectURL` 호출 없음 | LOW |
| 사이드바 네비게이션 연동 | StudioSidebar에서 /upload 링크 존재 (`page.tsx:82`) | -- (구현됨) |

---

## 7. Architecture / Convention Compliance

### 7.1 Clean Architecture 평가

| 항목 | 평가 | 상태 |
|------|------|:----:|
| API URL 직접 참조 (`process.env`) | 컴포넌트에서 직접 환경변수 참조 | ⚠️ |
| fetch 직접 호출 | Service Layer 미사용 | ⚠️ |
| 공유 타입 미활용 | `lib/types/presentation.ts` 대신 로컬 인터페이스 사용 | ❌ |
| 커스텀 훅 분리 | `useDrop` 훅은 같은 파일 내 정의 (분리 권장) | ⚠️ |

현재 프로젝트 수준(Dynamic)에서 권장하는 `Components -> Services -> API Client` 3계층 구조 대신 컴포넌트에서 직접 fetch를 호출하고 있음. MVP 단계에서는 허용 가능하나 향후 리팩토링 필요.

### 7.2 Naming Convention

| 항목 | 규칙 | 실제 | 상태 |
|------|------|------|:----:|
| 컴포넌트 | PascalCase | `UploadPage` | ✅ |
| 함수 | camelCase | `handleVoiceDrop`, `uploadVoice`, `goToStudio` | ✅ |
| 상수 | UPPER_SNAKE_CASE | `API_BASE` | ✅ |
| 파일 | kebab-case 폴더 | `app/upload/page.tsx` | ✅ |
| 인터페이스 | PascalCase | `UploadState`, `VoiceResult`, `PdfResult` | ✅ |

### 7.3 Import Order

```typescript
// page.tsx 실제 import 순서:
"use client";                                    // 1. Directive
import { useState, useRef, useCallback } from "react";  // 2. External
import { useRouter } from "next/navigation";             // 2. External
import { Mic, ... } from "lucide-react";                 // 2. External
import Link from "next/link";                            // 2. External
// (내부 import 없음 - 자체 완결적 파일)
```

Import 순서는 규칙에 부합. 다만 `@/lib/types/presentation` 등 내부 타입을 활용하면 더 나은 구조.

---

## 8. Overall Scores

```
+---------------------------------------------+
|  Overall Score: 73/100                       |
+---------------------------------------------+
|  Requirements Match:    75% (7.5/10)         |
|  API Consistency:       60% (field mismatches)|
|  Type System:           50% (shared types 미활용)|
|  UX Completeness:       85% (10/12 UX 항목)  |
|  Architecture:          65% (Direct fetch)    |
|  Convention:            95% (naming OK)       |
+---------------------------------------------+

| Category             | Score  | Status |
|:---------------------|:------:|:------:|
| Design Match         |   75%  |   ⚠️   |
| Architecture         |   65%  |   ⚠️   |
| Convention           |   95%  |   ✅   |
| **Overall**          | **73%**|   ⚠️   |
```

---

## 9. Differences Found

### 9.1 Missing Features (Requirements O, Implementation X)

| # | 항목 | 설명 |
|---|------|------|
| -- | (해당 없음) | 10개 요구사항 모두 최소한 부분적으로 구현됨 |

### 9.2 Bugs (Implementation != Specification)

| # | 항목 | Frontend 코드 | Backend 스펙 | 영향 |
|---|------|--------------|-------------|------|
| 1 | PDF 슬라이드 수 필드명 | `data.slide_count` | `total_slides` | HIGH - 항상 0 반환 |
| 2 | PDF DPI 값 | `"150"` | 기본값 `200` | MEDIUM - 이미지 품질 저하 |
| 3 | Studio query param 미수신 | `presentation_id`, `voice_id` 전송 | Studio에서 무시 | HIGH - 연동 단절 |

### 9.3 Code Quality Issues

| # | 항목 | 위치 | 설명 | 영향 |
|---|------|------|------|------|
| 1 | 존재하지 않는 fallback 필드 | `page.tsx:159` | `data.elevenlabs_voice_id` 백엔드 응답에 없음 | LOW |
| 2 | 존재하지 않는 fallback 필드 | `page.tsx:194` | `data.id` 백엔드 응답에 없음 | LOW |
| 3 | 공유 타입 미활용 | `page.tsx:37-41` | `PdfResult` 로컬 정의 vs `PresentationUploadResponse` | MEDIUM |
| 4 | Memory leak | `page.tsx:112` | `URL.createObjectURL` 후 `revokeObjectURL` 미호출 | LOW |
| 5 | user_id 하드코딩 | `page.tsx:145` | `"local_user"` 고정 | LOW (MVP) |
| 6 | project_id 임시값 | `page.tsx:180` | `proj_${Date.now()}` - 프로젝트 관리와 미연결 | MEDIUM |

---

## 10. Recommended Actions

### 10.1 Immediate (24시간 이내)

| Priority | Item | File | Line |
|:--------:|------|------|------|
| 1 | `slide_count` -> `total_slides` 필드명 수정 | `frontend/app/upload/page.tsx` | L39, L195, L521-522 |
| 2 | DPI `"150"` -> `"200"` 수정 | `frontend/app/upload/page.tsx` | L181 |
| 3 | 불필요한 fallback 제거 (`data.id`, `data.elevenlabs_voice_id`) | `frontend/app/upload/page.tsx` | L159, L194 |

### 10.2 Short-term (1주 이내)

| Priority | Item | File | Expected Impact |
|:--------:|------|------|-----------------|
| 1 | Studio 페이지에 `presentation_id`, `voice_id` query param 수신 로직 추가 | `frontend/app/studio/page.tsx` | Upload -> Studio 워크플로우 완성 |
| 2 | `PdfResult` 로컬 인터페이스를 `PresentationUploadResponse` 공유 타입으로 교체 | `frontend/app/upload/page.tsx` | 타입 안전성 향상 |
| 3 | 업로드 진행률 표시 (XMLHttpRequest 또는 fetch stream) | `frontend/app/upload/page.tsx` | 대용량 파일 UX 개선 |
| 4 | `URL.revokeObjectURL` 추가 (컴포넌트 unmount 또는 파일 변경 시) | `frontend/app/upload/page.tsx` | Memory leak 방지 |

### 10.3 Long-term (백로그)

| Item | Description |
|------|-------------|
| Service Layer 분리 | `uploadVoice()`, `uploadPdf()`를 `services/upload.ts`로 분리 |
| `useDrop` 훅 분리 | `hooks/useDrop.ts`로 독립 모듈화 |
| PDF 첫 페이지 썸네일 미리보기 | canvas + pdf.js로 클라이언트 측 렌더링 |
| 클라이언트 측 오디오 길이 검증 | Web Audio API로 duration 체크 후 최소 1분 미달 시 경고 |

---

## 11. Design Document Updates Needed

현재 Plan/Design 문서가 부재하므로 다음 문서 작성을 권장:

- [ ] `docs/01-plan/features/upload.plan.md` - Upload 기능 Plan 문서 신규 작성
- [ ] `docs/02-design/features/upload.design.md` - Upload 기능 Design 문서 신규 작성
- [ ] Voice Clone API 응답 타입을 `frontend/lib/types/` 에 정의 추가

---

## 12. Conclusion

Upload 기능의 전체적인 UI/UX 구현 품질은 우수하나, **백엔드 API 응답 필드명 불일치(`slide_count` vs `total_slides`)와 Studio 연동 미완성이 핵심 문제**이다. 이 2가지 버그를 수정하면 Match Rate가 75% -> 약 90%로 상승할 것으로 예상된다.

```
Match Rate: 75% (< 90% threshold)
=> Act 단계 진행 권장
=> /pdca iterate upload
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-28 | Initial gap analysis | bkit-gap-detector |

---

## 13. Act Phase 수정 결과 (2026-02-28)

### 수정 완료 항목

| Bug | 파일 | 수정 내용 | Status |
|-----|------|---------|--------|
| #1 slide_count → total_slides | frontend/app/upload/page.tsx:194 | `data.slide_count` → `data.total_slides` | ✅ Fixed |
| #2 DPI 150 → 200 | frontend/app/upload/page.tsx:181 | `"150"` → `"200"` | ✅ Fixed |
| #3 Studio params 미수신 | frontend/app/studio/page.tsx:104 | `voice_id`, `presentation_id` params 수신 + 배너 표시 | ✅ Fixed |

### Plan/Design 문서 추가

- [x] `docs/01-plan/features/upload.plan.md` 생성
- [x] `docs/02-design/features/upload.design.md` 생성

### 수정 후 Match Rate

```
3개 버그 수정 완료 (High 2건 + Medium 1건)
예상 Match Rate: 75% → 95%+
```

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-02-28 | Act Phase 버그 3건 수정 + Plan/Design 문서 생성 |
