# 영상 메타데이터 조회 API 구현 완료 보고서

## 작업 개요

프로젝트의 영상 메타데이터를 조회하는 API 엔드포인트를 성공적으로 구현했습니다.
FFmpeg의 ffprobe를 사용하여 영상 파일의 상세 정보를 추출합니다.

## 구현 완료 사항

### 1. 서비스 레이어
**파일**: `/backend/app/services/video_metadata_service.py`

**주요 기능**:
- FFmpeg ffprobe를 사용한 비디오 메타데이터 추출
- 영상 길이, 해상도, 프레임 레이트, 코덱 정보 파싱
- Neo4j에서 비디오 섹션 정보 조회
- 에러 핸들링 및 타임아웃 처리 (30초)

**핵심 메서드**:
- `extract_metadata(video_path)`: FFmpeg로 메타데이터 추출
- `get_video_sections(neo4j_client, project_id, video_id)`: 섹션 정보 조회
- `_parse_ffprobe_output(metadata)`: 원본 데이터 정리

**위치**: 라인 1-210

### 2. API 엔드포인트
**파일**: `/backend/app/api/v1/editor.py`

**엔드포인트**:

1. **GET /api/v1/projects/{project_id}/video/metadata**
   - 프로젝트의 최신 영상 메타데이터 조회
   - 위치: 라인 75-145

2. **GET /api/v1/projects/{project_id}/videos/{video_id}/metadata**
   - 프로젝트의 특정 영상 메타데이터 조회
   - 위치: 라인 148-219

**응답 모델**:
- `VideoMetadataResponse`: 전체 메타데이터 응답
- `VideoResolution`: 해상도 정보
- `VideoSection`: 섹션 정보 (hook, body, cta)

### 3. API 라우터 등록
**파일**: `/backend/app/api/v1/__init__.py`

- editor 라우터를 "Video Editor" 태그로 등록
- 위치: 라인 17, 35

### 4. OpenAPI 태그 추가
**파일**: `/backend/app/main.py`

- "Video Editor" 태그 추가: "🎬 비디오 메타데이터 조회 및 편집 (FFmpeg 기반)"
- 위치: 라인 96-99

## 응답 데이터 구조

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
    }
  ]
}
```

## 기술 스택

- **FFmpeg 8.0.1**: 비디오 메타데이터 추출
- **FastAPI**: REST API 프레임워크
- **Pydantic**: 데이터 검증 및 직렬화
- **Neo4j**: 프로젝트 및 비디오 정보 저장

## 테스트

### 1. FFmpeg 설치 확인
```bash
$ ffprobe -version
ffprobe version 8.0.1
```

### 2. 서비스 초기화 테스트
```bash
$ cd backend
$ python3 -c "from app.services.video_metadata_service import VideoMetadataService; \
              svc = VideoMetadataService(); \
              print('Service initialized:', svc.ffprobe_available)"
Service initialized: True
```

### 3. 통합 테스트 스크립트
**파일**: `/backend/test_video_metadata.py`

```bash
# 테스트 데이터 자동 생성 후 테스트
python3 test_video_metadata.py

# 특정 프로젝트로 테스트
python3 test_video_metadata.py proj_abc123
```

## 생성된 파일 목록

| 파일 경로 | 설명 | 라인 수 |
|----------|------|---------|
| `/backend/app/services/video_metadata_service.py` | 비디오 메타데이터 서비스 | 210 |
| `/backend/app/api/v1/editor.py` | API 엔드포인트 | 220 |
| `/backend/test_video_metadata.py` | 통합 테스트 스크립트 | 120 |
| `/backend/docs/VIDEO_METADATA_API.md` | API 사용 가이드 | 250+ |
| `/backend/VIDEO_METADATA_IMPLEMENTATION.md` | 이 문서 | - |

## API 사용 예시

### cURL
```bash
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/video/metadata" | jq .
```

### Python
```python
import httpx

async def get_metadata(project_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/projects/{project_id}/video/metadata"
        )
        return response.json()

metadata = await get_metadata("proj_abc123")
print(f"Duration: {metadata['duration']}s")
print(f"Resolution: {metadata['resolution']['width']}x{metadata['resolution']['height']}")
```

### JavaScript
```javascript
const axios = require('axios');

const response = await axios.get(
    'http://localhost:8000/api/v1/projects/proj_abc123/video/metadata'
);

console.log(`Duration: ${response.data.duration}s`);
console.log(`Codec: ${response.data.codec}`);
```

## 에러 처리

### 1. FFmpeg 미설치
```json
{
  "detail": "Failed to extract metadata from video: /path/to/video.mp4. Make sure FFmpeg is installed and the file exists."
}
```

**해결**: FFmpeg 설치
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 2. 프로젝트 없음
```json
{
  "detail": "Project not found: proj_abc123"
}
```

### 3. 비디오 없음
```json
{
  "detail": "No video found for project: proj_abc123"
}
```

## 향후 개선 사항

### 단기 (1-2주)
- [ ] 비디오 섹션 자동 감지 (AI 기반)
- [ ] 특정 프레임 썸네일 추출 API
- [ ] 여러 비디오 메타데이터 일괄 조회

### 중기 (1-2개월)
- [ ] 비디오 자르기/합치기 API
- [ ] 자막 추출 및 분석
- [ ] 클라우드 스토리지 직접 조회 (S3, GCS, Cloudinary)

### 장기 (3개월+)
- [ ] 실시간 스트리밍 메타데이터 지원
- [ ] AI 기반 씬 감지
- [ ] 얼굴/객체 인식 통합

## 주요 함수 위치

### video_metadata_service.py
- `VideoMetadataService.__init__()`: 라인 17-19
- `VideoMetadataService._check_ffprobe()`: 라인 21-32
- `VideoMetadataService.extract_metadata()`: 라인 34-74
- `VideoMetadataService._parse_ffprobe_output()`: 라인 76-138
- `VideoMetadataService.get_video_sections()`: 라인 140-175

### editor.py
- `get_project_video_metadata()`: 라인 75-145
- `get_specific_video_metadata()`: 라인 148-219

## 성능 특성

- **FFmpeg 실행 시간**: 일반적으로 0.1-1초 (파일 크기에 따라 다름)
- **타임아웃**: 30초
- **메모리 사용**: 최소 (메타데이터만 추출, 비디오 디코딩 안 함)

## 보안 고려사항

1. **파일 경로 검증**: 현재 Neo4j에 저장된 경로만 사용 (사용자 입력 없음)
2. **명령어 인젝션 방지**: subprocess를 리스트 형태로 사용 (쉘 실행 없음)
3. **타임아웃**: 30초로 제한하여 DOS 공격 방지

## 의존성

### Python 패키지
- `fastapi`: API 프레임워크
- `pydantic`: 데이터 검증
- `neo4j`: 그래프 데이터베이스 클라이언트

### 시스템 요구사항
- FFmpeg 4.0+ (권장: 8.0+)

## 문서

- **API 가이드**: `/backend/docs/VIDEO_METADATA_API.md`
- **구현 보고서**: 이 문서
- **테스트 스크립트**: `/backend/test_video_metadata.py`

## 완료 체크리스트

- [x] 비디오 메타데이터 서비스 구현
- [x] API 엔드포인트 2개 구현
- [x] Neo4j 섹션 정보 조회 통합
- [x] API 라우터 등록
- [x] OpenAPI 태그 추가
- [x] 테스트 스크립트 작성
- [x] API 문서 작성
- [x] FFmpeg 설치 확인
- [x] 문법 체크 완료

## 작업 시간

- **총 작업 시간**: 약 30분
- **파일 생성**: 5개
- **코드 라인**: 약 800줄 (주석 포함)

---

**작업 완료일**: 2026-02-02
**작업자**: Claude (Vibe Coding Lv.4)
**상태**: ✅ 완료
