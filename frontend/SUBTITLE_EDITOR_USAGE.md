# SubtitleEditor 컴포넌트 사용 가이드

## 개요

SubtitleEditor는 자막 위치, 스타일, 크기를 실시간으로 조정할 수 있는 React 컴포넌트입니다.

## 설치된 의존성

```json
{
  "lodash.debounce": "^4.0.8",
  "@types/lodash.debounce": "^4.0.9"
}
```

## 생성된 파일

### 1. 타입 정의
- **경로**: `/frontend/lib/types/subtitle.ts`
- **라인**: 1-47
- **내용**: SubtitleStyle, SubtitleEditorProps, API 응답 타입

### 2. 프리셋 상수
- **경로**: `/frontend/lib/constants/subtitlePresets.ts`
- **라인**: 1-102
- **내용**: 플랫폼별 프리셋 (YouTube, TikTok, Instagram, Minimal)

### 3. 메인 컴포넌트
- **경로**: `/frontend/components/SubtitleEditor.tsx`
- **라인**: 1-695
- **내용**: 전체 자막 에디터 UI 및 로직

## 사용 방법

### 기본 사용

```tsx
import SubtitleEditor from '@/components/SubtitleEditor';

export default function SubtitleEditorPage() {
  return (
    <div className="h-screen">
      <SubtitleEditor
        projectId="project-123"
      />
    </div>
  );
}
```

### 초기 스타일 지정

```tsx
import SubtitleEditor from '@/components/SubtitleEditor';
import { SubtitleStyle } from '@/lib/types/subtitle';

const initialStyle: SubtitleStyle = {
  font_family: 'Roboto',
  font_size: 42,
  font_color: '#FFFFFF',
  background_color: '#000000',
  background_opacity: 0.7,
  position: 'bottom',
  vertical_offset: 80,
  alignment: 'center',
  outline_width: 2,
  outline_color: '#000000',
  shadow_enabled: true,
  shadow_offset_x: 2,
  shadow_offset_y: 2,
};

export default function SubtitleEditorPage() {
  return (
    <SubtitleEditor
      projectId="project-123"
      initialStyle={initialStyle}
    />
  );
}
```

### 스타일 변경 핸들러

```tsx
import SubtitleEditor from '@/components/SubtitleEditor';
import { SubtitleStyle } from '@/lib/types/subtitle';

export default function SubtitleEditorPage() {
  const handleStyleChange = (style: SubtitleStyle) => {
    console.log('Style changed:', style);
    // 상위 컴포넌트에서 스타일 상태 업데이트
  };

  return (
    <SubtitleEditor
      projectId="project-123"
      onStyleChange={handleStyleChange}
    />
  );
}
```

### 미리보기 요청 핸들러

```tsx
import SubtitleEditor from '@/components/SubtitleEditor';

export default function SubtitleEditorPage() {
  const handlePreviewRequest = () => {
    console.log('Preview requested');
    // 미리보기 생성 시 추가 작업
  };

  return (
    <SubtitleEditor
      projectId="project-123"
      onPreviewRequest={handlePreviewRequest}
    />
  );
}
```

## 주요 기능

### 1. 폰트 설정
- 폰트 패밀리 (7가지 옵션: Roboto, Montserrat, Poppins, Arial, Helvetica, Noto Sans KR, Nanum Gothic)
- 폰트 크기 (24px ~ 72px)
- 폰트 색상 (컬러 피커 + 텍스트 입력)

### 2. 배경 설정
- 배경 색상 (컬러 피커 + 텍스트 입력)
- 배경 투명도 (0% ~ 100%)

### 3. 위치 및 정렬
- 위치 (상단/중앙/하단)
- 수직 오프셋 (0px ~ 200px)
- 정렬 (왼쪽/중앙/오른쪽)

### 4. 아웃라인 설정
- 아웃라인 두께 (0px ~ 8px)
- 아웃라인 색상 (컬러 피커 + 텍스트 입력)

### 5. 그림자 설정
- 그림자 활성화/비활성화
- X 오프셋 (-10px ~ 10px)
- Y 오프셋 (-10px ~ 10px)

### 6. 프리셋
- **YouTube**: 큰 폰트, 명확한 배경
- **TikTok**: 중앙 배치, 강렬한 아웃라인 (분홍색)
- **Instagram**: 작은 폰트, 세련된 디자인
- **Minimal**: 배경 없음, 깔끔한 아웃라인

### 7. 실시간 미리보기
- 좌측 패널에서 설정 변경 시 우측 패널에서 즉시 반영
- 미리보기 영상 생성 버튼 (POST /api/v1/projects/{project_id}/subtitles/preview)

### 8. 자동 저장
- Debounce 1초 적용
- 설정 변경 시 자동으로 API에 저장 (PATCH 요청)
- 프리셋 적용 시 즉시 저장

## API 통합

### GET /api/v1/projects/{project_id}/subtitles
기존 자막 스타일 로드

**응답 예시**:
```json
{
  "subtitle_id": "sub-123",
  "project_id": "project-123",
  "style": {
    "font_family": "Roboto",
    "font_size": 42,
    "font_color": "#FFFFFF",
    "background_color": "#000000",
    "background_opacity": 0.7,
    "position": "bottom",
    "vertical_offset": 80,
    "alignment": "center",
    "outline_width": 2,
    "outline_color": "#000000",
    "shadow_enabled": true,
    "shadow_offset_x": 2,
    "shadow_offset_y": 2
  },
  "created_at": "2026-02-02T10:00:00Z",
  "updated_at": "2026-02-02T10:30:00Z"
}
```

### PATCH /api/v1/projects/{project_id}/subtitles
자막 스타일 업데이트 (Debounce 1초)

**요청 예시**:
```json
{
  "style": {
    "font_family": "Montserrat",
    "font_size": 48,
    ...
  }
}
```

### POST /api/v1/projects/{project_id}/subtitles/preview
미리보기 영상 생성

**응답 예시**:
```json
{
  "preview_url": "http://localhost:8000/previews/preview-123.mp4",
  "thumbnail_url": "http://localhost:8000/previews/preview-123.jpg",
  "created_at": "2026-02-02T10:45:00Z"
}
```

## 디자인 특징

### 반응형 디자인
- 모바일: 세로 레이아웃 (컨트롤 → 미리보기)
- 데스크톱: 가로 레이아웃 (컨트롤 50% | 미리보기 50%)

### 색상 시스템
- 기본: Tailwind CSS 색상 팔레트
- 프리셋 버튼: 호버 시 blue-50 배경
- 미리보기: 16:9 비율 유지

### 애니메이션
- 로딩 스피너: animate-spin
- 버튼 호버: transition-all
- 메시지 자동 사라짐: 2초 후

## 컴포넌트 구조

```
SubtitleEditor
├── 좌측 패널 (lg:w-1/2)
│   ├── 헤더
│   ├── 에러/성공 메시지
│   ├── 프리셋 선택 (4개)
│   ├── 폰트 설정 섹션
│   ├── 배경 설정 섹션
│   ├── 위치 및 정렬 섹션
│   ├── 아웃라인 설정 섹션
│   └── 그림자 설정 섹션
└── 우측 패널 (lg:w-1/2)
    ├── 미리보기 컨테이너 (16:9)
    │   ├── 배경 (그라데이션)
    │   └── 자막 레이어 (실시간 반영)
    ├── 미리보기 생성 버튼
    └── 현재 스타일 정보
```

## TypeScript 타입 안정성

모든 타입이 정의되어 있으며, 타입 에러 없이 컴파일됩니다:

```bash
$ npx tsc --noEmit --skipLibCheck
# ✅ 타입 에러 없음
```

## 다음 단계

1. **백엔드 API 구현**: 위의 3개 엔드포인트 구현 필요
2. **실제 영상 미리보기**: FFmpeg로 실제 영상에 자막 렌더링
3. **폰트 로딩**: Google Fonts API 통합
4. **프리셋 확장**: 사용자 커스텀 프리셋 저장 기능
5. **실시간 협업**: WebSocket으로 여러 사용자 동시 편집

## 문제 해결

### 폰트가 미리보기에 표시되지 않음
→ 해당 폰트가 브라우저에 설치되어 있는지 확인 (Google Fonts 링크 추가 필요)

### API 호출 실패
→ 백엔드 서버가 http://localhost:8000에서 실행 중인지 확인

### Debounce가 작동하지 않음
→ lodash.debounce 패키지가 설치되어 있는지 확인

## 라이센스

이 컴포넌트는 OmniVibe Pro 프로젝트의 일부입니다.
