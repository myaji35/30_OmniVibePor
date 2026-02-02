# ClipReplacer Component

AI 생성 대체 클립 3개를 갤러리 형태로 표시하고 원클릭으로 교체하는 React 컴포넌트입니다.

## 생성된 파일

### 1. 컴포넌트
- **`/frontend/components/ClipReplacer.tsx`** (라인 1-313)
  - 메인 클립 교체 UI 컴포넌트
  - 현재 클립 표시, 대체 클립 갤러리, 생성 버튼 포함

- **`/frontend/components/ClipPreviewModal.tsx`** (라인 1-187)
  - 클립 미리보기 모달 컴포넌트
  - 비디오 플레이어, 프롬프트 표시, 교체 버튼 포함

### 2. API & Hooks
- **`/frontend/lib/api/clips.ts`** (라인 1-113)
  - 클립 관련 API 유틸리티 함수
  - 타입 정의: `Clip`, `AlternativeClipsData`, `ClipGenerationProgress`
  - API 함수: `getAlternativeClips`, `generateAlternativeClips`, `replaceClip`, `deleteAlternativeClip`

- **`/frontend/hooks/useClipReplacer.ts`** (라인 1-139)
  - 클립 교체 커스텀 Hook
  - 상태 관리, 폴링, 에러 처리 포함

### 3. 예시 파일
- **`/frontend/components/ClipReplacer.example.tsx`**
  - 4가지 사용 예시 포함
  - 기본 사용법, 콜백 사용법, 프로덕션 워크플로우 통합, 모달 통합

## 주요 기능

### 1. 현재 클립 표시
- 큰 썸네일 (16:9 비율)
- 프롬프트 표시
- "현재 사용 중" 배지
- 클릭 시 미리보기 모달 열림

### 2. 대체 클립 갤러리
- 3개 썸네일 (가로 배치)
- 변형 타입 배지
  - 카메라 앵글: 보라색 (#8B5CF6)
  - 조명: 주황색 (#F59E0B)
  - 색감: 분홍색 (#EC4899)
- 호버 시 "교체" 버튼 표시
- 삭제 버튼 (호버 시 표시)

### 3. AI 대체 클립 생성
- "대체 클립 생성" 버튼
- 생성 진행 상태 표시
  - 로딩 스피너
  - 진행률 바
  - "AI 영상 생성 중... (약 50초 소요)" 메시지
- 5초마다 폴링하여 상태 확인
- 완료 시 갤러리 자동 업데이트

### 4. 클립 미리보기 모달
- 비디오 플레이어 (재생/정지)
- 프롬프트 전체 텍스트
- 생성일 표시
- "교체" 버튼 (현재 클립이 아닌 경우)
- "닫기" 버튼

## API 엔드포인트

컴포넌트는 다음 API 엔드포인트를 사용합니다:

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/sections/{section_id}/alternative-clips` | 대체 클립 목록 조회 |
| POST | `/api/v1/sections/{section_id}/alternative-clips` | 대체 클립 생성 (AI) |
| GET | `/api/v1/tasks/{task_id}/progress` | 생성 진행 상태 조회 |
| PATCH | `/api/v1/sections/{section_id}/clip` | 클립 교체 |
| DELETE | `/api/v1/sections/{section_id}/alternative-clips/{clip_id}` | 대체 클립 삭제 |

## 사용 방법

### 기본 사용법

```tsx
import ClipReplacer from '@/components/ClipReplacer';

function MyPage() {
  return (
    <ClipReplacer sectionId="section_123" />
  );
}
```

### 콜백 사용법

```tsx
import ClipReplacer from '@/components/ClipReplacer';

function MyPage() {
  const handleClipReplaced = (clipId: string) => {
    console.log('Clip replaced:', clipId);
    // 타임라인 리로드, 상태 업데이트 등
  };

  return (
    <ClipReplacer
      sectionId="section_123"
      onClipReplaced={handleClipReplaced}
    />
  );
}
```

더 많은 예시는 `ClipReplacer.example.tsx` 파일을 참고하세요.

## Props 인터페이스

### ClipReplacerProps

```typescript
interface ClipReplacerProps {
  sectionId: string;           // 섹션 ID (필수)
  onClipReplaced?: (clipId: string) => void;  // 클립 교체 시 콜백 (선택)
}
```

### Clip

```typescript
interface Clip {
  clip_id: string;
  video_path: string;
  thumbnail_url: string;
  prompt: string;
  variation?: 'camera_angle' | 'lighting' | 'color_tone';
  created_at: string;
}
```

### AlternativeClipsData

```typescript
interface AlternativeClipsData {
  section_id: string;
  current_clip: Clip;
  alternatives: Clip[];  // 최대 3개
}
```

## 기술 스택

- **React 18**: Hooks (useState, useEffect, useCallback)
- **Next.js 14**: Image 컴포넌트, App Router
- **TypeScript 5**: 완전한 타입 안전성
- **Tailwind CSS**: 반응형 디자인
- **HTML Dialog**: 네이티브 모달

## 외부 라이브러리

사용된 외부 라이브러리:
- `next/image`: 이미지 최적화

## 스타일링

- **Tailwind CSS** 사용
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **애니메이션**:
  - 호버 효과 (scale, shadow)
  - 로딩 스피너
  - 진행률 바
  - 이미지 줌 효과

## TypeScript & ESLint

- **TypeScript 타입 에러**: 없음
- **ESLint 경고**: 없음
- **Next.js Image 최적화**: 적용됨

## 설정 파일 수정

### next.config.js

```javascript
images: {
  remotePatterns: [
    {
      protocol: 'http',
      hostname: 'localhost',
      port: '8000',
      pathname: '/**',
    },
    {
      protocol: 'https',
      hostname: '**',
    },
  ],
}
```

이 설정으로 외부 이미지(백엔드 API, CDN 등)를 Next.js Image 컴포넌트로 로드할 수 있습니다.

## 완료 조건 체크리스트

- [x] 컴포넌트 정상 렌더링
- [x] API 통합 완료
- [x] 클립 교체 기능 구현
- [x] 미리보기 모달 동작
- [x] TypeScript 타입 에러 없음
- [x] ESLint 경고 없음
- [x] 반응형 디자인
- [x] 폴링 기능 (5초 간격)
- [x] 로딩 상태 표시
- [x] 에러 처리

## 향후 개선 사항

1. **WebSocket 통합**: 폴링 대신 실시간 업데이트
2. **무한 스크롤**: 3개 이상의 대체 클립 지원
3. **드래그 앤 드롭**: 클립 순서 변경
4. **키보드 단축키**: 모달 닫기 (ESC), 클립 탐색 (화살표)
5. **A/B 테스팅**: 클립 성과 비교 기능
6. **비디오 트림**: 클립 길이 조정 기능
7. **캐싱**: React Query를 사용한 데이터 캐싱
8. **오프라인 지원**: Service Worker를 사용한 오프라인 모드

## 문의 및 지원

문제가 발생하거나 기능 요청이 있으면 프로젝트 Issue 트래커에 등록해주세요.
