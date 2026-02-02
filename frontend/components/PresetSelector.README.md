# PresetSelector 컴포넌트

플랫폼별 프리셋과 커스텀 프리셋을 선택할 수 있는 React 컴포넌트입니다.

## 파일 위치

- **메인 컴포넌트**: `/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/frontend/components/PresetSelector.tsx` (507 라인)
- **사용 예시**: `/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/frontend/components/PresetSelector.example.tsx` (234 라인)
- **README**: `/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/frontend/components/PresetSelector.README.md`

## 주요 기능

### 1. 플랫폼 프리셋
- YouTube, Instagram, TikTok 등 플랫폼별 사전 정의된 프리셋 제공
- 플랫폼별 아이콘 및 브랜드 컬러 표시
- 해상도, 종횡비 정보 표시

### 2. 커스텀 프리셋
- 사용자가 생성한 프리셋 목록 표시
- 즐겨찾기 기능 (하트 아이콘 클릭)
- 사용 횟수 및 생성일 표시

### 3. 검색 및 필터
- 실시간 검색 (프리셋 이름 기준)
- 플랫폼별 필터링 (YouTube, Instagram, TikTok)
- 즐겨찾기만 보기 (커스텀 프리셋)

### 4. 프리셋 적용
- 프리셋 선택 시 미리보기
- 하단 고정 "적용" 버튼
- API를 통한 프로젝트 설정 자동 업데이트

## Props 인터페이스

```typescript
interface PresetSelectorProps {
  projectId: string;                                              // 프로젝트 ID (필수)
  onPresetSelected?: (presetId: string, type: 'platform' | 'custom') => void;  // 프리셋 선택 콜백
  onPresetApplied?: () => void;                                   // 프리셋 적용 완료 콜백
}
```

## 주요 컴포넌트 위치

| 기능 | 라인 | 설명 |
|------|------|------|
| **타입 정의** | 19-52 | PlatformPreset, CustomPreset, PresetSelectorProps |
| **헬퍼 함수** | 54-85 | 플랫폼 아이콘, 컬러, 이름 함수 |
| **메인 컴포넌트** | 87-505 | PresetSelector 컴포넌트 |
| **상태 관리** | 98-110 | useState 훅들 |
| **API 호출** | 112-231 | fetchPlatformPresets, fetchCustomPresets, toggleFavorite, applyPreset |
| **필터링 로직** | 233-244 | 검색어 및 필터 타입 기반 필터링 |
| **UI 렌더링** | 253-503 | 검색바, 탭, 프리셋 그리드, 적용 버튼 |

## 사용 예시

### 기본 사용

```tsx
import PresetSelector from '@/components/PresetSelector';

function MyPage() {
  return <PresetSelector projectId="project-123" />;
}
```

### 콜백 함수 활용

```tsx
import PresetSelector from '@/components/PresetSelector';

function MyPage() {
  return (
    <PresetSelector
      projectId="project-123"
      onPresetSelected={(presetId, type) => {
        console.log('선택된 프리셋:', presetId, type);
      }}
      onPresetApplied={() => {
        alert('프리셋이 적용되었습니다!');
      }}
    />
  );
}
```

### 모달 내부 사용

```tsx
import { useState } from 'react';
import PresetSelector from '@/components/PresetSelector';

function MyPage() {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <button onClick={() => setShowModal(true)}>
        프리셋 선택
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto p-6">
            <PresetSelector
              projectId="project-123"
              onPresetApplied={() => {
                setShowModal(false);
              }}
            />
          </div>
        </div>
      )}
    </>
  );
}
```

## API 엔드포인트

### 1. GET /api/v1/presets/platforms

플랫폼 프리셋 목록 조회

**Response:**
```json
{
  "presets": [
    {
      "platform": "youtube",
      "name": "YouTube 16:9",
      "resolution": { "width": 1920, "height": 1080 },
      "aspect_ratio": "16:9",
      "subtitle_style": { ... },
      "bgm_settings": { ... },
      "thumbnail_url": "..."
    }
  ]
}
```

### 2. GET /api/v1/presets/custom

커스텀 프리셋 목록 조회

**Response:**
```json
{
  "presets": [
    {
      "preset_id": "preset-123",
      "name": "내 프리셋",
      "description": "설명",
      "subtitle_style": { ... },
      "bgm_settings": { ... },
      "video_settings": { ... },
      "is_favorite": false,
      "usage_count": 5,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### 3. PUT /api/v1/presets/custom/{preset_id}/favorite

즐겨찾기 토글

**Request:**
```json
{
  "is_favorite": true
}
```

### 4. POST /api/v1/projects/{project_id}/apply-preset

프리셋 적용

**Request:**
```json
{
  "preset_id": "youtube",
  "preset_type": "platform"
}
```

## 사용된 외부 라이브러리

### lucide-react (v0.x)

아이콘 라이브러리로 다음 아이콘 사용:

- `Search`: 검색 입력창
- `Filter`: 필터 드롭다운
- `Heart`: 즐겨찾기 (채워진/비워진 상태)
- `Check`: 선택 배지
- `Youtube`: YouTube 플랫폼 아이콘
- `Instagram`: Instagram 플랫폼 아이콘
- `Music`: TikTok 플랫폼 아이콘

**설치:**
```bash
npm install lucide-react
```

## 디자인 특징

### 플랫폼 컬러

- **YouTube**: 빨강 (#FF0000)
- **Instagram**: 보라-분홍-주황 그라디언트
- **TikTok**: 검정 (#000000)

### 반응형 그리드

- **모바일**: 2열
- **태블릿**: 3열
- **데스크탑**: 4열

### 애니메이션

- 카드 호버: 그림자 확대 (`hover:shadow-lg`)
- 로딩: 펄스 애니메이션 (`animate-pulse`)
- 색상 전환: 부드러운 전환 (`transition-colors`)

## 접근성

- 키보드 네비게이션 지원
- 명확한 포커스 상태 (`focus:ring-2`)
- 의미있는 버튼 레이블
- 색상 대비 준수 (WCAG AA 기준)

## 성능 최적화

- 검색 및 필터링은 클라이언트 사이드에서 실시간 처리
- API 호출은 컴포넌트 마운트 시 1회만 실행
- 불필요한 리렌더링 방지 (메모이제이션 가능)

## 향후 개선 사항

- [ ] 프리셋 미리보기 모달
- [ ] 드래그 앤 드롭 정렬
- [ ] 프리셋 생성/편집 기능
- [ ] 무한 스크롤 (페이지네이션)
- [ ] 프리셋 공유 기능
- [ ] 프리셋 내보내기/가져오기

## 문제 해결

### 프리셋 목록이 표시되지 않음

1. API 서버가 실행 중인지 확인: `http://localhost:8000`
2. 네트워크 탭에서 API 응답 확인
3. CORS 설정 확인

### 즐겨찾기가 저장되지 않음

1. PUT API가 올바르게 구현되었는지 확인
2. 로컬 상태와 서버 상태 동기화 확인

### TypeScript 에러

```bash
npx tsc --noEmit
```

## 라이센스

OmniVibe Pro 프로젝트의 일부로, 내부 사용 전용입니다.
