# SavePresetModal 컴포넌트

프로젝트의 현재 설정을 커스텀 프리셋으로 저장하는 React 모달 컴포넌트입니다.

## 파일 위치

- **컴포넌트**: `/frontend/components/SavePresetModal.tsx`
- **API 클라이언트**: `/frontend/lib/api/presets.ts`
- **사용 예시**: `/frontend/components/SavePresetModal.example.tsx`

## 주요 기능

### 1. 프리셋 정보 입력
- **프리셋 이름**: 필수 입력 (1-50자)
- **설명**: 선택 입력 (최대 200자)
- **즐겨찾기**: 토글 스위치로 설정

### 2. 설정 미리보기
접을 수 있는(collapsible) 섹션으로 현재 프로젝트의 설정을 미리 확인:
- 자막 스타일 (폰트, 크기, 위치, 정렬)
- BGM 설정 (볼륨, 페이드 인/아웃, 트랙 이름)
- 영상 설정 (해상도, FPS, 비율, 품질)

### 3. 유효성 검증
- 실시간 입력 유효성 검증
- 에러 메시지 표시
- 유효하지 않을 때 저장 버튼 비활성화

### 4. API 통합
현재 프로젝트 설정을 자동으로 로드하여 프리셋으로 저장:
- `GET /api/v1/projects/{project_id}/subtitles`
- `GET /api/v1/projects/{project_id}/bgm`
- `GET /api/v1/projects/{project_id}/video/metadata`
- `POST /api/v1/presets/custom`

## Props 인터페이스

```typescript
interface SavePresetModalProps {
  projectId: string;       // 프로젝트 ID (필수)
  isOpen: boolean;         // 모달 열림/닫힘 상태
  onClose: () => void;     // 모달 닫기 콜백
  onSaved?: (presetId: string) => void;  // 저장 성공 콜백 (선택)
}
```

## 사용 예시

```tsx
import { useState } from 'react';
import SavePresetModal from '@/components/SavePresetModal';

function MyProjectPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const projectId = "my-project-id";

  return (
    <>
      <button onClick={() => setIsModalOpen(true)}>
        프리셋으로 저장
      </button>

      <SavePresetModal
        projectId={projectId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaved={(presetId) => {
          console.log('프리셋 저장 완료:', presetId);
          // 토스트 알림 표시 또는 프리셋 목록 갱신
        }}
      />
    </>
  );
}
```

## API 클라이언트 함수

### 프로젝트 설정 조회

```typescript
// 자막 스타일 가져오기
const subtitleStyle = await getProjectSubtitleSettings(projectId);

// BGM 설정 가져오기
const bgmSettings = await getProjectBGMSettings(projectId);

// 영상 설정 가져오기
const videoSettings = await getProjectVideoSettings(projectId);

// 모든 설정 한번에 가져오기
const projectSettings = await getProjectSettings(projectId);
```

### 프리셋 관리

```typescript
// 프리셋 생성
const preset = await createCustomPreset({
  name: "유튜브 쇼츠 기본",
  description: "쇼츠용 기본 설정",
  is_favorite: true,
  settings: projectSettings
});

// 프리셋 목록 조회
const { presets, total } = await getCustomPresets();

// 단일 프리셋 조회
const preset = await getCustomPreset(presetId);

// 프리셋 삭제
await deleteCustomPreset(presetId);

// 프로젝트에 프리셋 적용
await applyPresetToProject(projectId, presetId);
```

## 데이터 타입

### ProjectSettings
```typescript
interface ProjectSettings {
  subtitle_style?: SubtitleStyle;
  bgm_settings?: BGMSettings;
  video_settings?: VideoSettings;
}
```

### SubtitleStyle
```typescript
interface SubtitleStyle {
  font_family?: string;
  font_size?: number;
  color?: string;
  background_color?: string;
  position?: 'top' | 'middle' | 'bottom';
  alignment?: 'left' | 'center' | 'right';
}
```

### BGMSettings
```typescript
interface BGMSettings {
  volume?: number;
  fade_in?: number;
  fade_out?: number;
  track_url?: string;
  track_name?: string;
}
```

### VideoSettings
```typescript
interface VideoSettings {
  resolution?: string;
  fps?: number;
  aspect_ratio?: string;
  quality?: 'low' | 'medium' | 'high' | 'ultra';
}
```

## UI 구성

### 헤더
- 제목: "프리셋 저장"
- 닫기 버튼 (X 아이콘)

### 입력 필드
1. **프리셋 이름** (필수)
   - 텍스트 입력
   - 최대 50자
   - 실시간 문자 수 카운터
   - 유효성 검증 에러 표시

2. **설명** (선택)
   - 텍스트 영역 (3줄)
   - 최대 200자
   - 실시간 문자 수 카운터

3. **즐겨찾기**
   - 토글 스위치
   - 기본값: false

### 설정 미리보기
- 접을 수 있는 섹션
- 화살표 아이콘으로 상태 표시
- 그리드 레이아웃 (2열)
- 작은 텍스트로 간결하게 표시

### 하단 버튼
- **취소**: 회색, 왼쪽 정렬
- **저장**: 파랑, 오른쪽 정렬
  - 유효하지 않을 때: 회색, 비활성화
  - 저장 중: 스피너 + "저장 중..." 텍스트

## 사용자 경험 (UX)

### 로딩 상태
- 프로젝트 설정 로드 중: 중앙 스피너 표시
- 저장 중: 버튼 내 작은 스피너 + 텍스트 변경

### 에러 처리
- API 에러 발생 시: 상단에 빨간 배경의 에러 메시지 표시
- 유효성 검증 실패: 필드 하단에 빨간 텍스트로 에러 표시

### 모달 닫기
- 닫기 버튼 클릭
- 모달 외부 (backdrop) 클릭
- ESC 키 (브라우저 기본 동작)

### 저장 후 동작
1. 성공 시:
   - `onSaved` 콜백 호출 (presetId 전달)
   - 모달 자동 닫기
   - 폼 데이터 초기화

2. 실패 시:
   - 에러 메시지 표시
   - 모달은 열린 상태 유지
   - 사용자가 재시도 가능

## 기술 스택

- **React**: 함수형 컴포넌트 + Hooks
- **TypeScript**: 완전한 타입 안전성
- **HTML Dialog API**: 네이티브 모달 구현
- **Tailwind CSS**: 유틸리티 퍼스트 스타일링
- **Fetch API**: REST API 통신

## 스타일링 특징

### 색상
- Primary (파랑): `bg-blue-500`, `hover:bg-blue-600`
- Success (초록): `bg-green-50`, `border-green-200`
- Error (빨강): `bg-red-50`, `border-red-200`
- Neutral (회색): `bg-gray-50`, `text-gray-700`

### 반응형
- 모달 최대 너비: `max-w-2xl`
- 컨텐츠 최대 높이: `max-h-[70vh]` (스크롤 가능)
- 비디오 최대 높이: `max-h-[60vh]`

### 애니메이션
- 토글 스위치: `transition-transform`, `transition-colors`
- 버튼: `transition-colors`
- 스피너: `animate-spin`
- 화살표: `transition-transform` + `rotate-90`

## 접근성 (Accessibility)

- `aria-label` 속성 사용 (닫기 버튼, 토글)
- `htmlFor` 속성으로 label-input 연결
- `disabled` 상태 명확한 시각적 표시
- 키보드 네비게이션 지원 (브라우저 기본)

## 브라우저 호환성

- **HTML Dialog API**: Chrome 37+, Safari 15.4+, Firefox 98+
- **Tailwind CSS**: 모든 모던 브라우저
- **Fetch API**: 모든 모던 브라우저

## 향후 개선 사항

1. **토스트 알림**: 저장 성공 시 토스트 알림 표시 (현재는 콘솔 로그)
2. **프리셋 태그**: 프리셋에 태그 추가 기능
3. **프리셋 공유**: 다른 사용자와 프리셋 공유 기능
4. **프리셋 검색**: 저장된 프리셋 중 선택하여 비교
5. **설정 차이 표시**: 현재 설정과 기존 프리셋의 차이 하이라이트

## 문제 해결

### 모달이 열리지 않음
- `isOpen` prop이 `true`로 설정되었는지 확인
- 브라우저가 HTML Dialog API를 지원하는지 확인

### 프로젝트 설정을 불러올 수 없음
- `projectId`가 유효한지 확인
- 백엔드 API 엔드포인트가 구현되어 있는지 확인
- 네트워크 탭에서 API 응답 확인

### 저장이 실패함
- 프리셋 이름이 입력되었는지 확인
- 유효성 검증을 통과했는지 확인
- 백엔드 API 엔드포인트 구현 확인
- 콘솔 에러 메시지 확인

## 라이센스

이 컴포넌트는 OmniVibe Pro 프로젝트의 일부입니다.
