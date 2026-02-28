# Design: upload

## 1. Overview
**Feature**: 목소리 샘플 + PDF 슬라이드 통합 업로드
**PDCA Phase**: Design
**Created**: 2026-02-28
**References**: upload.plan.md

## 2. Component Architecture

```
/app/upload/page.tsx (UploadPage)
├── useDrop(onDrop, accept[]) — 드래그앤드롭 훅
├── formatSize(bytes) — 유틸리티
│
├── <header> — 브레드크럼 + "영상 만들기" CTA (bothReady 시)
├── <main>
│   ├── 타이틀 + 파이프라인 배지
│   ├── <section> Voice Card
│   │   ├── DropZone (파일 미선택 시)
│   │   ├── FilePreview + <audio> (파일 선택 후)
│   │   ├── MetaForm (voiceName, voiceDesc 입력)
│   │   ├── UploadButton (uploadVoice)
│   │   └── SuccessCard (완료 시 voice_id 표시)
│   ├── <section> PDF Card
│   │   ├── DropZone (파일 미선택 시)
│   │   ├── FilePreview (파일 선택 후)
│   │   ├── UploadButton (uploadPdf)
│   │   └── SuccessCard (완료 시 presentation_id, slide_count 표시)
│   ├── CTA Card (bothReady 시만 렌더)
│   └── Guide Cards (3단계 설명)
```

## 3. State Design

```typescript
// UploadState (Voice / PDF 공통)
interface UploadState {
    file: File | null;
    uploading: boolean;
    done: boolean;
    error: string | null;
}

// VoiceResult
interface VoiceResult {
    voice_id: string;      // API: data.voice_id
    voice_name: string;
    status: string;
}

// PdfResult
interface PdfResult {
    presentation_id: string;   // API: data.presentation_id
    slide_count: number;       // API: data.total_slides  ← 주의!
    message: string;
}

// 조합 조건
const bothReady = voiceState.done && pdfState.done;
```

## 4. API 연동 설계

### 4.1 Voice Clone
```
POST /api/v1/voice/clone
Content-Type: multipart/form-data

FormData:
  audio_file: File (MP3/WAV/M4A/FLAC/OGG)
  user_id: "local_user"
  voice_name: string (required)
  description: string (optional)

Response: { voice_id, name, status, message }
파싱: data.voice_id  ← elevenlabs_voice_id fallback 불필요
```

### 4.2 PDF Upload
```
POST /api/v1/presentations/upload
Content-Type: multipart/form-data

FormData:
  file: File (PDF)
  project_id: "proj_{timestamp}"
  dpi: "200"  ← 백엔드 기본값과 일치
  lang: "kor+eng"

Response: { presentation_id, pdf_path, total_slides, slides[], status }
파싱: data.presentation_id, data.total_slides  ← slide_count 아님!
```

### 4.3 Studio 라우팅
```
완료 후 이동: /studio?presentation_id={id}&voice_id={id}

Studio 페이지(page.tsx)에서:
const searchParams = useSearchParams();
const presentationId = searchParams.get("presentation_id");
const voiceId = searchParams.get("voice_id");
→ voiceId를 audio generation voice_id로 자동 설정
→ presentationId로 PDF 슬라이드 로드
```

## 5. 에러 처리

| 상황 | 처리 |
|------|------|
| 잘못된 파일 형식 | error state 설정, 인라인 에러 메시지 표시 |
| 목소리 이름 미입력 | error state "목소리 이름을 입력해주세요." |
| API 실패 (4xx/5xx) | data.detail 파싱 후 error state |
| 네트워크 오류 | instanceof Error 체크 후 메시지 |

## 6. 파일 검증

```typescript
// Voice 파일 검증 (클라이언트)
/\.(mp3|wav|m4a|flac|ogg)$/i.test(file.name)

// PDF 검증 (클라이언트)
file.name.toLowerCase().endsWith(".pdf")

// 서버 검증: /api/v1/voice/validate 엔드포인트 존재
// (향후 개선: 업로드 전 사전 검증 API 호출)
```

## 7. UX Flow

```
사용자 진입 /upload
    ↓
[Voice 카드] 파일 드롭/선택
    ↓ 오디오 미리보기
    ↓ 이름 입력 → "목소리 등록" 클릭
    ↓ 업로드 중 (Loader2 스피너)
    ↓ 완료 ✅ voice_id 표시

[PDF 카드] 파일 드롭/선택
    ↓ "PDF 등록" 클릭
    ↓ 업로드 중 (Loader2 스피너)
    ↓ 완료 ✅ presentation_id + slide_count 표시

[두 카드 모두 완료]
    ↓ 헤더 "영상 만들기" 버튼 노출
    ↓ 하단 CTA 카드 노출
    ↓ 클릭 → /studio?presentation_id=...&voice_id=...
```

## 8. StudioSidebar 연동

```typescript
// /components/studio/StudioSidebar.tsx
// 하단 "목소리 · PDF 업로드" → Link href="/upload"
```

## 9. Studio 페이지 수신 처리 (미구현 → 구현 필요)

```typescript
// /app/studio/page.tsx
const searchParams = useSearchParams();
useEffect(() => {
    const presentationId = searchParams.get("presentation_id");
    const voiceId = searchParams.get("voice_id");
    if (voiceId) {
        // setVoiceId 또는 audio generation 설정에 반영
    }
    if (presentationId) {
        // presentation workflow 시작
    }
}, [searchParams]);
```

## 10. 디자인 토큰

| 요소 | 값 |
|------|----|
| Voice 카드 색상 | `brand-primary-500` (보라) |
| PDF 카드 색상 | `brand-secondary-500` (파랑) |
| 배경 | `#050505` |
| 카드 | `premium-card` + `border border-white/10` |
| 에러 | `red-400 / red-500/10 border` |
| 성공 | `green-400 / green-500/10 border` |
