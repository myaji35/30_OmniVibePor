# Video Metadata API Documentation

## 개요

영상 파일의 메타데이터를 추출하고 조회하는 API입니다.
FFmpeg의 `ffprobe`를 사용하여 영상 정보를 분석합니다.

## 엔드포인트

### 1. GET /api/v1/projects/{project_id}/video/metadata

**설명**: 프로젝트의 최신 영상 메타데이터 조회

**요청 예시**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/video/metadata"
```

**응답 예시**:
```json
{
  "project_id": "proj_abc123",
  "video_id": "video_def456",
  "video_path": "/path/to/video.mp4",
  "duration": 62.5,
  "frame_rate": 30.0,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "codec": "h264",
  "audio_codec": "aac",
  "bitrate": 5000000,
  "file_size": 39062500,
  "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
  "created_at": "2026-02-02T10:30:00Z",
  "sections": [
    {
      "type": "hook",
      "start_time": 0.0,
      "end_time": 5.0,
      "duration": 5.0
    },
    {
      "type": "body",
      "start_time": 5.0,
      "end_time": 55.0,
      "duration": 50.0
    },
    {
      "type": "cta",
      "start_time": 55.0,
      "end_time": 62.5,
      "duration": 7.5
    }
  ]
}
```

### 2. GET /api/v1/projects/{project_id}/videos/{video_id}/metadata

**설명**: 프로젝트의 특정 영상 메타데이터 조회

**요청 예시**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/videos/video_def456/metadata"
```

**응답 예시**: (위와 동일)

## 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `project_id` | string | 프로젝트 ID |
| `video_id` | string | 비디오 ID |
| `video_path` | string | 비디오 파일 경로 |
| `duration` | float | 영상 길이 (초) |
| `frame_rate` | float | 프레임 레이트 (FPS) |
| `resolution.width` | int | 가로 해상도 (픽셀) |
| `resolution.height` | int | 세로 해상도 (픽셀) |
| `codec` | string | 비디오 코덱 (예: h264, hevc, vp9) |
| `audio_codec` | string | 오디오 코덱 (예: aac, mp3, opus) |
| `bitrate` | int | 비트레이트 (bps) |
| `file_size` | int | 파일 크기 (bytes) |
| `format_name` | string | 포맷 이름 |
| `created_at` | datetime | 생성 시간 (ISO 8601) |
| `sections` | array | 비디오 섹션 목록 |

### 섹션 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | string | 섹션 타입 (hook, body, cta) |
| `start_time` | float | 시작 시간 (초) |
| `end_time` | float | 종료 시간 (초) |
| `duration` | float | 섹션 길이 (초) |

## 에러 응답

### 404 Not Found
```json
{
  "detail": "Project not found: proj_abc123"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to extract metadata from video: /path/to/video.mp4. Make sure FFmpeg is installed and the file exists."
}
```

## 요구사항

### 1. FFmpeg 설치

API를 사용하기 전에 시스템에 FFmpeg가 설치되어 있어야 합니다.

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Docker**:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
```

### 2. 비디오 파일 경로

- 비디오 파일은 API 서버에서 접근 가능한 경로에 있어야 합니다.
- Neo4j에 저장된 `file_path`가 실제 파일 시스템 경로와 일치해야 합니다.

## 사용 예시

### Python (httpx)

```python
import httpx

async def get_video_metadata(project_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}/video/metadata"
        )
        response.raise_for_status()
        return response.json()

# 사용
metadata = await get_video_metadata("proj_abc123")
print(f"Duration: {metadata['duration']}s")
print(f"Resolution: {metadata['resolution']['width']}x{metadata['resolution']['height']}")
```

### JavaScript (Axios)

```javascript
const axios = require('axios');

async function getVideoMetadata(projectId) {
    const response = await axios.get(
        `http://localhost:8000/api/v1/projects/${projectId}/video/metadata`
    );
    return response.data;
}

// 사용
getVideoMetadata('proj_abc123')
    .then(metadata => {
        console.log(`Duration: ${metadata.duration}s`);
        console.log(`Resolution: ${metadata.resolution.width}x${metadata.resolution.height}`);
    });
```

### cURL

```bash
# 기본 요청
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/video/metadata"

# 예쁘게 출력 (jq 사용)
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/video/metadata" | jq .

# 특정 필드만 추출
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/video/metadata" | jq '{duration, resolution, codec}'
```

## 테스트

프로젝트에 테스트 스크립트가 포함되어 있습니다:

```bash
cd backend

# 테스트 데이터 자동 생성 후 테스트
python3 test_video_metadata.py

# 특정 프로젝트 ID로 테스트
python3 test_video_metadata.py proj_abc123
```

## 주의사항

1. **파일 크기**: 매우 큰 비디오 파일의 경우 메타데이터 추출에 시간이 걸릴 수 있습니다.
2. **타임아웃**: ffprobe 실행은 30초 타임아웃이 적용됩니다.
3. **섹션 정보**: 현재 섹션 정보는 Neo4j에 저장된 데이터를 조회합니다. 섹션 정보가 없으면 빈 배열이 반환됩니다.
4. **파일 경로**: 상대 경로가 아닌 절대 경로로 저장하는 것을 권장합니다.

## 향후 개선 사항

- [ ] 비디오 섹션 자동 감지 (AI 기반)
- [ ] 썸네일 추출 API
- [ ] 비디오 자르기/합치기 API
- [ ] 실시간 스트리밍 메타데이터 지원
- [ ] 클라우드 스토리지 직접 조회 (S3, GCS)

## 관련 문서

- [API 전체 문서](../API_DOCUMENTATION.md)
- [Neo4j 스키마 문서](./NEO4J_SCHEMA.md)
- [FFmpeg 공식 문서](https://ffmpeg.org/documentation.html)
