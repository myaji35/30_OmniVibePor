# PresentationMode Component

> Phase 7 구현: PDF 프리젠테이션 영상 자동 생성 UI

## Overview

PresentationMode는 PDF 파일을 업로드하여 나레이션이 포함된 프리젠테이션 영상을 자동으로 생성하는 컴포넌트입니다.

**주요 기능**:
- PDF 업로드 및 슬라이드 추출
- AI 기반 나레이션 스크립트 자동 생성
- TTS 오디오 생성 및 검증
- Whisper 타임스탬프 기반 타이밍 분석
- FFmpeg 기반 프리젠테이션 영상 생성
- 슬라이드별 나레이션 편집

## Architecture

### 워크플로우

```
1. PDF 업로드
   ↓
2. 슬라이드 추출 (PDF → PNG)
   ↓
3. 스크립트 생성 (LLM)
   ↓
4. 오디오 생성 (TTS)
   ↓
5. 타이밍 분석 (Whisper)
   ↓
6. 영상 생성 (FFmpeg)
```

### API 엔드포인트

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/api/v1/presentation/upload` | POST | PDF 파일 업로드 |
| `/api/v1/presentation/{id}/generate-script` | POST | 스크립트 생성 |
| `/api/v1/presentation/{id}/generate-audio` | POST | TTS 오디오 생성 |
| `/api/v1/presentation/{id}/analyze-timing` | POST | 타이밍 분석 |
| `/api/v1/presentation/{id}/generate-video` | POST | 영상 생성 (비동기) |
| `/api/v1/presentation/{id}` | GET | 프리젠테이션 조회 |

## Usage

### Basic Example

```tsx
import PresentationMode from '@/components/PresentationMode';

export default function MyPage() {
  const handleComplete = (videoPath: string) => {
    console.log('Video ready:', videoPath);
  };

  return (
    <PresentationMode
      projectId="my_project_001"
      onComplete={handleComplete}
    />
  );
}
```

### With Existing Presentation

```tsx
<PresentationMode
  projectId="my_project_001"
  presentationId="pres_abc123"
  onComplete={handleComplete}
/>
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `projectId` | string | Yes | 프로젝트 ID |
| `presentationId` | string \| null | No | 기존 프리젠테이션 ID (재편집 시) |
| `onComplete` | (videoPath: string) => void | No | 영상 생성 완료 콜백 |

## Features

### 1. PDF 업로드

- 파일 선택 UI
- 업로드 진행률 표시
- PDF → 슬라이드 이미지 변환 (200 DPI)
- 슬라이드 썸네일 자동 생성

### 2. 슬라이드 목록

- 왼쪽 사이드바에 모든 슬라이드 표시
- 썸네일 + 번호 + 타이밍 정보
- 클릭하여 슬라이드 선택
- 스크립트 존재 여부 체크 표시

### 3. 나레이션 편집

- 슬라이드별 스크립트 표시
- 실시간 편집 가능
- 글자 수 및 예상 시간 표시
- 저장/취소 기능

### 4. 진행 상태 추적

- 6단계 상태 추적:
  1. `uploaded` - PDF 업로드 완료
  2. `script_generated` - 스크립트 생성 완료
  3. `audio_generated` - 오디오 생성 완료
  4. `timing_analyzed` - 타이밍 분석 완료
  5. `video_rendering` - 영상 렌더링 중
  6. `video_ready` - 영상 생성 완료

- 진행률 바로 시각화
- 각 단계별 버튼 활성화/비활성화

### 5. 오디오 생성

- ElevenLabs TTS 통합
- Whisper STT 검증
- 정확도 체크

### 6. 타이밍 분석

- Whisper 타임스탬프 기반 자동 분석
- 슬라이드별 시작/종료 시간 계산
- 수동 타이밍 조정 지원

### 7. 영상 생성

- FFmpeg 기반 렌더링
- 화면 전환 효과 (fade/slide/zoom/none)
- 배경음악 추가 가능
- Celery 비동기 작업 큐
- 실시간 진행 상황 폴링

## State Management

```typescript
// Main state
const [presentationId, setPresentationId] = useState<string | null>(null);
const [presentation, setPresentation] = useState<Presentation | null>(null);
const [selectedSlideIndex, setSelectedSlideIndex] = useState<number>(0);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// Editing state
const [editingSlideIndex, setEditingSlideIndex] = useState<number | null>(null);
const [editedScript, setEditedScript] = useState<string>("");
```

## Status Flow

```
UPLOADED
  ↓ (Generate Script)
SCRIPT_GENERATED
  ↓ (Generate Audio)
AUDIO_GENERATED
  ↓ (Analyze Timing)
TIMING_ANALYZED
  ↓ (Generate Video)
VIDEO_RENDERING
  ↓ (Auto-polling)
VIDEO_READY
```

## Error Handling

- API 에러 메시지 표시
- 파일 타입 검증 (PDF만 허용)
- 네트워크 에러 처리
- 이미지 로드 실패 처리

## Performance

- 슬라이드 썸네일 lazy loading
- 영상 생성 비동기 처리 (Celery)
- 3초마다 상태 폴링 (렌더링 중일 때)

## Styling

- Tailwind CSS 유틸리티 클래스
- Lucide React 아이콘
- 반응형 그리드 레이아웃 (3:9 비율)
- 일관된 컬러 스키마:
  - Blue: 기본 액션
  - Green: 오디오 생성
  - Purple: 타이밍 분석
  - Red: 영상 생성

## Backend Dependencies

이 컴포넌트가 정상 작동하려면 다음 백엔드 서비스가 필요합니다:

- **PDFToSlidesService**: PDF → 이미지 변환
- **SlideToScriptConverter**: LLM 기반 스크립트 생성
- **TTSService**: ElevenLabs TTS
- **STTService**: OpenAI Whisper
- **SlideTimingAnalyzer**: 타임스탬프 분석
- **PresentationVideoGenerator**: FFmpeg 영상 생성
- **Neo4j**: 프리젠테이션 메타데이터 저장

## Future Enhancements

- [ ] 실시간 WebSocket 진행 상황 (폴링 대체)
- [ ] 슬라이드 전환 효과 미리보기
- [ ] 배경음악 파일 업로드 UI
- [ ] 다중 음성 선택 (슬라이드별 다른 목소리)
- [ ] 슬라이드 순서 변경 (드래그 앤 드롭)
- [ ] 슬라이드 추가/삭제
- [ ] 타이밍 타임라인 편집기
- [ ] 영상 미리보기 플레이어

## Testing

```bash
# 개발 서버 실행
cd frontend
npm run dev

# 브라우저에서 접속
open http://localhost:3020/presentation
```

## Known Issues

1. **이미지 경로**: 백엔드가 반환하는 `image_path`가 `/static/...` 형식이어야 함
2. **CORS**: 프론트엔드와 백엔드가 다른 포트일 경우 CORS 설정 필요
3. **폴링 중복**: 컴포넌트 언마운트 시 폴링 정리 필요 (useEffect cleanup)

## Related Files

- `/frontend/lib/types/presentation.ts` - 타입 정의
- `/frontend/app/presentation/page.tsx` - 테스트 페이지
- `/backend/app/api/v1/presentation.py` - 백엔드 API
- `/backend/app/models/presentation.py` - Pydantic 모델

## License

MIT
