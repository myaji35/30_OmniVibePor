# Remotion Integration Guide

## 개요

OmniVibe Pro의 Remotion 통합은 React 기반 프로그래매틱 비디오 생성을 지원합니다. Director Agent가 생성한 Storyboard Blocks를 Remotion Composition으로 변환하여 고품질 영상을 렌더링합니다.

## 아키텍처

```
Director Agent (콘티 생성)
         ↓
Remotion Service (Props 변환)
         ↓
Celery Task Queue (비동기 렌더링)
         ↓
Remotion CLI (React 기반 렌더링)
         ↓
Cloudinary (CDN 업로드)
         ↓
WebSocket (실시간 진행 상태)
```

## 주요 컴포넌트

### 1. Remotion Service (`app/services/remotion_service.py`)

**기능:**
- Storyboard Blocks → Remotion Props 변환
- Remotion CLI 실행 (비동기)
- Cloudinary 자동 업로드
- WebSocket 진행 상태 업데이트

**주요 메서드:**
```python
class RemotionService:
    def convert_storyboard_to_props(
        storyboard_blocks: List[Dict],
        campaign_concept: Dict,
        audio_url: Optional[str]
    ) -> Dict

    async def render_video_with_remotion(
        content_id: int,
        props: Dict,
        composition_id: str = "OmniVibeComposition"
    ) -> Dict

    def get_available_compositions() -> List[Dict]

    async def validate_remotion_installation() -> Dict
```

### 2. Celery Tasks (`app/tasks/video_tasks.py`)

**비동기 렌더링 작업:**

```python
@celery_app.task(name="render_video_with_remotion")
def render_video_with_remotion_task(
    content_id: int,
    storyboard_blocks: List[Dict],
    campaign_concept: Dict,
    audio_url: Optional[str],
    composition_id: str = "OmniVibeComposition"
) -> Dict
```

**배치 렌더링:**
```python
@celery_app.task(name="batch_render_videos")
def batch_render_videos_task(
    render_requests: List[Dict]
) -> Dict
```

### 3. API Endpoints (`app/api/v1/remotion.py`)

#### POST `/api/v1/remotion/render`
영상 렌더링 시작

**Request:**
```json
{
  "content_id": 123,
  "storyboard_blocks": [
    {
      "block_type": "hook",
      "text": "여러분, 오늘은...",
      "duration": 5,
      "visual_concept": "energetic intro",
      "background_url": "https://...",
      "transition_effect": "fade"
    }
  ],
  "campaign_concept": {
    "gender": "male",
    "tone": "professional",
    "style": "cinematic",
    "platform": "YouTube"
  },
  "audio_url": "https://res.cloudinary.com/..."
}
```

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-...",
  "status": "processing",
  "message": "Remotion 렌더링 시작..."
}
```

#### GET `/api/v1/remotion/status/{task_id}`
렌더링 상태 조회

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-...",
  "status": "completed",
  "progress": 100,
  "message": "렌더링 완료!",
  "result": {
    "local_path": "/outputs/video_123.mp4",
    "cloudinary_url": "https://res.cloudinary.com/...",
    "duration": 60,
    "platform": "YouTube",
    "resolution": "1920x1080"
  }
}
```

#### GET `/api/v1/remotion/compositions`
사용 가능한 Composition 목록

**Response:**
```json
[
  {
    "id": "OmniVibeComposition",
    "name": "OmniVibe Default Composition",
    "description": "기본 콘티 기반 영상 생성",
    "defaultProps": {
      "platform": "YouTube",
      "scenes": []
    }
  }
]
```

#### GET `/api/v1/remotion/validate`
Remotion 설치 검증

**Response:**
```json
{
  "status": "ok",
  "message": "✅ Remotion 설정이 정상입니다.",
  "details": {
    "installed": true,
    "version": "4.0.0",
    "frontend_path": "/path/to/frontend"
  }
}
```

## Platform-Specific Settings

Remotion은 플랫폼별 최적화된 영상을 생성합니다:

| Platform | Resolution | FPS | Bitrate | Aspect Ratio |
|----------|-----------|-----|---------|--------------|
| YouTube | 1920x1080 | 30 | 8M | 16:9 |
| Instagram | 1080x1350 | 30 | 5M | 4:5 (Feed) |
| TikTok | 1080x1920 | 30 | 4M | 9:16 (Vertical) |
| Facebook | 1280x720 | 30 | 6M | 16:9 |

## Usage Example

### Python (Backend)

```python
from app.services.remotion_service import get_remotion_service
import asyncio

# Service 인스턴스
remotion = get_remotion_service()

# Storyboard → Props 변환
props = remotion.convert_storyboard_to_props(
    storyboard_blocks=[
        {
            "block_type": "hook",
            "text": "여러분, 오늘은 특별한 날입니다!",
            "duration": 5,
            "visual_concept": "energetic",
            "background_url": "https://...",
            "transition_effect": "fade"
        }
    ],
    campaign_concept={
        "gender": "male",
        "tone": "professional",
        "style": "cinematic",
        "platform": "YouTube"
    },
    audio_url="https://..."
)

# 비동기 렌더링
result = await remotion.render_video_with_remotion(
    content_id=123,
    props=props
)

print(f"Video URL: {result['cloudinary_url']}")
```

### TypeScript (Frontend)

```typescript
// API 호출
const response = await fetch('/api/v1/remotion/render', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_id: 123,
    storyboard_blocks: [...],
    campaign_concept: {...},
    audio_url: "https://..."
  })
});

const { task_id } = await response.json();

// 상태 폴링
const checkStatus = async () => {
  const status = await fetch(`/api/v1/remotion/status/${task_id}`);
  const data = await status.json();

  if (data.status === 'completed') {
    console.log('Video ready:', data.result.cloudinary_url);
  } else if (data.status === 'failed') {
    console.error('Render failed:', data.message);
  } else {
    // 계속 폴링
    setTimeout(checkStatus, 2000);
  }
};

checkStatus();
```

### WebSocket (실시간 진행 상태)

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/progress/123`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Stage: ${data.stage}, Progress: ${data.progress}%`);

  if (data.stage === 'completed') {
    console.log('Render completed!');
  }
};
```

## Celery Worker 실행

Remotion 렌더링은 Celery Worker에서 실행됩니다:

```bash
cd backend

# Redis 시작
redis-server

# Celery Worker 시작
celery -A app.tasks.celery_app worker --loglevel=info
```

## Troubleshooting

### 1. Remotion CLI 설치 확인

```bash
cd frontend
npx remotion --version
```

### 2. Frontend Remotion Composition 확인

Frontend에 다음 Composition이 정의되어 있어야 합니다:

**`frontend/remotion/compositions/OmniVibeComposition.tsx`**

```tsx
import { Composition } from 'remotion';

export const OmniVibeComposition: React.FC = () => {
  return (
    <Composition
      id="OmniVibeComposition"
      component={MyComposition}
      durationInFrames={3000}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

### 3. Props 파일 확인

렌더링 시 Props는 `/backend/outputs/props_{content_id}.json`에 저장됩니다:

```bash
cat backend/outputs/props_123.json
```

### 4. Celery Task 로그 확인

```bash
# Celery worker 로그
tail -f celery.log

# FastAPI 로그
tail -f backend/logs/app.log
```

## Best Practices

### 1. Props 검증
렌더링 전 Props를 검증하여 실패를 방지하세요:

```python
props = remotion.convert_storyboard_to_props(...)

# Props 구조 확인
assert "scenes" in props
assert len(props["scenes"]) > 0
assert "platform" in props
```

### 2. 타임아웃 설정
긴 영상(5분 이상)은 Celery Task 타임아웃을 늘리세요:

```python
@celery_app.task(
    name="render_video_with_remotion",
    bind=True,
    max_retries=2,
    time_limit=1800  # 30분
)
def render_video_with_remotion_task(...):
    ...
```

### 3. 에러 핸들링
렌더링 실패 시 재시도 로직을 활용하세요:

```python
try:
    result = await remotion.render_video_with_remotion(...)
except Exception as e:
    logger.error(f"Render failed: {e}")
    # 재시도 또는 알림
```

### 4. Cloudinary Quota 관리
대용량 영상은 Cloudinary Quota를 소모하므로 주의하세요:

```python
# 로컬 파일만 생성 (Cloudinary 업로드 스킵)
result = await remotion.render_video_with_remotion(
    content_id=123,
    props=props,
    skip_cloudinary=True  # 옵션 추가 필요
)
```

## Week 1 구현 완료 체크리스트

- [x] Neo4j Docker 설치 및 설정
- [x] Script Node 스키마 생성 (10개 샘플 스크립트)
- [x] Neo4j Client Python 모듈 작성
- [x] Writer Agent에 Neo4j Memory 통합 (Few-shot Learning)
- [x] Remotion Player를 Studio UI에 통합 (기존 파일 확인)
- [x] Backend Remotion Service 작성
  - [x] `app/services/remotion_service.py`
  - [x] `app/tasks/video_tasks.py` (Celery Tasks)
  - [x] `app/api/v1/remotion.py` (API Endpoints)
  - [x] API Router 등록

## Next Steps (Week 2 Preview)

Week 2에서는 다음 기능을 구현합니다:

1. **Audio Director Agent 개선**
   - Zero-Fault Loop 정확도 99% 달성
   - 다국어 TTS 지원 (한국어, 영어, 일본어)

2. **Character Consistency**
   - HeyGen Lipsync 통합
   - 캐릭터 일관성 유지 시스템

3. **Performance Tracker**
   - YouTube/Instagram API 연동
   - 자동 성과 추적 및 학습

4. **A/B Testing**
   - 썸네일/제목/CTA A/B 테스트
   - 자동 Winner 선정

---

**Document Version**: 1.0.0
**Last Updated**: 2026-02-08
**Author**: OmniVibe Pro Backend Team
