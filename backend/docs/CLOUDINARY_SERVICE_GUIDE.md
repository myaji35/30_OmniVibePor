# Cloudinary 미디어 최적화 서비스 가이드

## 개요

Cloudinary를 사용한 영상/이미지 업로드, 변환, 최적화 서비스입니다.

### 주요 기능

✅ **영상/이미지 업로드 및 관리**
- 안전한 클라우드 저장소
- 자동 메타데이터 추출
- CDN을 통한 빠른 전송

✅ **플랫폼별 자동 변환**
- YouTube (1920x1080, 16:9)
- Instagram Feed (1080x1080, 1:1)
- Instagram Story/Reels (1080x1920, 9:16)
- TikTok (1080x1920, 9:16)
- Facebook (1280x720, 16:9)

✅ **자동 썸네일 생성**
- 영상 특정 시점에서 추출
- 고품질 이미지 생성
- 자동 해상도 최적화

✅ **비용 추적**
- 변환 횟수 실시간 추적
- 무료 Tier 잔여량 모니터링
- Neo4j + Logfire 통합

---

## 파일 구조

```
backend/
├── app/
│   ├── services/
│   │   └── cloudinary_service.py      # 메인 서비스
│   └── api/v1/
│       └── media.py                    # API 엔드포인트
├── test_cloudinary_service.py          # 테스트 스크립트
└── CLOUDINARY_SERVICE_GUIDE.md         # 이 파일
```

---

## 환경 설정

### 1. Cloudinary 계정 생성

1. [Cloudinary](https://cloudinary.com/) 가입
2. Dashboard에서 다음 정보 확인:
   - Cloud Name
   - API Key
   - API Secret

### 2. 환경 변수 설정

`.env` 파일에 추가:

```bash
# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 3. 의존성 확인

`pyproject.toml`에 이미 포함되어 있습니다:

```toml
cloudinary = "^1.38.0"
httpx = "^0.26.0"
```

---

## 사용법

### 1. 서비스 초기화

```python
from app.services.cloudinary_service import get_cloudinary_service

service = get_cloudinary_service()
```

### 2. 영상 업로드

```python
# 로컬 파일 업로드
result = await service.upload_video(
    video_path="./my_video.mp4",
    folder="videos/youtube",
    user_id="user_123",
    project_id="project_456"
)

print(f"업로드 완료: {result['secure_url']}")
print(f"Public ID: {result['public_id']}")
print(f"영상 길이: {result['duration']:.2f}초")
```

### 3. 플랫폼별 변환

```python
# YouTube용 변환 (1920x1080, 16:9)
youtube_path = await service.transform_video_for_platform(
    public_id="videos/youtube/my_video",
    platform="youtube",
    user_id="user_123",
    project_id="project_456"
)

print(f"YouTube용 영상: {youtube_path}")

# TikTok용 변환 (1080x1920, 9:16)
tiktok_path = await service.transform_video_for_platform(
    public_id="videos/youtube/my_video",
    platform="tiktok",
    user_id="user_123",
    project_id="project_456"
)

print(f"TikTok용 영상: {tiktok_path}")
```

### 4. 썸네일 생성

```python
# 영상 3초 시점에서 썸네일 생성
thumbnail_url = await service.generate_thumbnail(
    video_public_id="videos/youtube/my_video",
    time_offset=3.0,
    width=1280,
    height=720,
    output_path="./thumbnail.jpg",  # 로컬 저장 (옵션)
    user_id="user_123",
    project_id="project_456"
)

print(f"썸네일 URL: {thumbnail_url}")
```

### 5. 최적화된 URL 생성

```python
# 자동 품질/포맷 최적화
optimized_url = service.get_optimized_url(
    public_id="images/my_image",
    resource_type="image"
)

print(f"최적화된 URL: {optimized_url}")
```

### 6. 에셋 삭제

```python
# 영상 삭제
deleted = await service.delete_asset(
    public_id="videos/youtube/my_video",
    resource_type="video"
)

print(f"삭제 {'성공' if deleted else '실패'}")
```

---

## API 엔드포인트

### 1. 플랫폼 목록 조회

```bash
GET /api/v1/media/platforms
```

**응답**:
```json
{
  "platforms": {
    "youtube": {
      "resolution": "1920x1080",
      "aspect_ratio": "16:9",
      "quality": "auto:best",
      "format": "mp4"
    },
    "tiktok": {
      "resolution": "1080x1920",
      "aspect_ratio": "9:16",
      "quality": "auto:good",
      "format": "mp4"
    }
  },
  "count": 6
}
```

### 2. 영상 업로드

```bash
POST /api/v1/media/upload/video
Content-Type: multipart/form-data

file: (binary)
folder: "videos"
user_id: "user_123"
project_id: "project_456"
```

**응답**:
```json
{
  "public_id": "videos/video_abc123",
  "url": "http://res.cloudinary.com/.../video_abc123.mp4",
  "secure_url": "https://res.cloudinary.com/.../video_abc123.mp4",
  "format": "mp4",
  "duration": 45.2,
  "width": 1920,
  "height": 1080,
  "bytes": 12345678
}
```

### 3. 영상 변환

```bash
POST /api/v1/media/transform/video
Content-Type: application/json

{
  "public_id": "videos/video_abc123",
  "platform": "youtube",
  "user_id": "user_123",
  "project_id": "project_456"
}
```

**응답**:
```json
{
  "status": "success",
  "platform": "youtube",
  "resolution": "1920x1080",
  "aspect_ratio": "16:9",
  "output_path": "/path/to/youtube_video_abc123.mp4",
  "message": "youtube용 영상 변환 완료"
}
```

### 4. 썸네일 생성

```bash
POST /api/v1/media/thumbnail/generate
Content-Type: application/json

{
  "video_public_id": "videos/video_abc123",
  "time_offset": 3.0,
  "width": 1280,
  "height": 720,
  "download": false
}
```

**응답**:
```json
{
  "status": "success",
  "thumbnail_url": "https://res.cloudinary.com/.../video_abc123.jpg",
  "resolution": "1280x720",
  "time_offset": 3.0
}
```

### 5. 에셋 정보 조회

```bash
GET /api/v1/media/asset/{public_id}?resource_type=video
```

**응답**:
```json
{
  "status": "success",
  "asset": {
    "public_id": "videos/video_abc123",
    "format": "mp4",
    "width": 1920,
    "height": 1080,
    "bytes": 12345678,
    "duration": 45.2,
    "created_at": "2026-02-02T12:00:00Z",
    "url": "http://res.cloudinary.com/.../video_abc123.mp4",
    "secure_url": "https://res.cloudinary.com/.../video_abc123.mp4"
  }
}
```

### 6. 에셋 삭제

```bash
DELETE /api/v1/media/asset/{public_id}?resource_type=video
```

---

## 플랫폼별 변환 설정

| 플랫폼 | 해상도 | 비율 | 품질 | 포맷 |
|--------|--------|------|------|------|
| YouTube | 1920x1080 | 16:9 | auto:best | mp4 |
| Instagram Feed | 1080x1080 | 1:1 | auto:good | mp4 |
| Instagram Story | 1080x1920 | 9:16 | auto:good | mp4 |
| Instagram Reels | 1080x1920 | 9:16 | auto:good | mp4 |
| TikTok | 1080x1920 | 9:16 | auto:good | mp4 |
| Facebook | 1280x720 | 16:9 | auto:good | mp4 |

---

## 비용 구조

### Cloudinary 무료 Tier

- **월간 변환 횟수**: 25,000회
- **저장공간**: 25GB
- **대역폭**: 25GB/월

### 초과 시 비용

- **변환**: $0.10 / 1,000회
- **저장공간**: $0.18 / GB / 월
- **대역폭**: $0.10 / GB

### 비용 추적

```python
from app.services.cost_tracker import get_cost_tracker

tracker = get_cost_tracker()

# 총 비용 조회
total_cost = tracker.get_total_cost(
    provider=APIProvider.CLOUDINARY,
    user_id="user_123"
)

print(f"총 비용: ${total_cost['total_cost']:.2f}")
print(f"변환 횟수: {total_cost['record_count']}")
```

---

## 테스트

### 기본 테스트

```bash
python test_cloudinary_service.py
```

**출력 예시**:
```
================================================================================
Cloudinary 미디어 최적화 서비스 테스트
================================================================================

1. 플랫폼별 영상 변환 설정:
--------------------------------------------------------------------------------

youtube:
  해상도: 1920x1080
  비율: 16:9
  품질: auto:best

tiktok:
  해상도: 1080x1920
  비율: 9:16
  품질: auto:good

...
```

### 실제 업로드 테스트

`test_cloudinary_service.py`에서 주석 해제:

```python
# 실제 업로드 테스트 (주석 해제하여 사용)
asyncio.run(test_upload_and_transform())
```

**주의**: 실제 Cloudinary API를 호출하므로 비용이 발생할 수 있습니다.

---

## 워크플로우 예시

### 1. YouTube 쇼츠 → 다채널 배포

```python
from app.services.cloudinary_service import get_cloudinary_service

service = get_cloudinary_service()

# 1. 원본 영상 업로드
result = await service.upload_video(
    video_path="./original_video.mp4",
    folder="videos/shorts",
    user_id="user_123",
    project_id="shorts_001"
)

public_id = result["public_id"]

# 2. 플랫폼별 변환
platforms = ["youtube", "instagram_reels", "tiktok"]
outputs = {}

for platform in platforms:
    output_path = await service.transform_video_for_platform(
        public_id=public_id,
        platform=platform,
        user_id="user_123",
        project_id="shorts_001"
    )
    outputs[platform] = output_path
    print(f"{platform}: {output_path}")

# 3. 썸네일 생성 (중간 지점)
thumbnail_url = await service.generate_thumbnail(
    video_public_id=public_id,
    time_offset=result["duration"] / 2,  # 중간 지점
    width=1280,
    height=720
)

print(f"썸네일: {thumbnail_url}")

# 4. 각 플랫폼에 배포 (별도 로직)
# ...
```

### 2. 썸네일 A/B 테스트

```python
# 영상의 여러 시점에서 썸네일 생성
time_offsets = [0, 5, 10, 15, 20]  # 0초, 5초, 10초, ...
thumbnails = []

for offset in time_offsets:
    url = await service.generate_thumbnail(
        video_public_id="videos/my_video",
        time_offset=offset,
        width=1280,
        height=720
    )
    thumbnails.append({
        "time": offset,
        "url": url
    })

# 각 썸네일로 A/B 테스트 진행
# ...
```

---

## 트러블슈팅

### 1. 업로드 실패

**증상**: `upload_video` 호출 시 에러 발생

**해결책**:
1. 환경 변수 확인 (CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET)
2. 파일 크기 확인 (Free tier: 100MB 제한)
3. 파일 포맷 확인 (지원 포맷: MP4, MOV, AVI, MKV)

### 2. 변환 실패

**증상**: `transform_video_for_platform` 호출 시 에러

**해결책**:
1. `public_id`가 올바른지 확인
2. 플랫폼명 확인 (`/api/v1/media/platforms`로 지원 목록 조회)
3. 원본 영상이 Cloudinary에 업로드되었는지 확인

### 3. 무료 Tier 초과

**증상**: 로그에 "FREE tier exceeded" 경고

**해결책**:
1. 월간 변환 횟수 확인 (25,000회 제한)
2. 비용 추적 시스템으로 사용량 모니터링
3. 필요시 유료 플랜 업그레이드

---

## 모범 사례

### 1. Public ID 명명 규칙

```python
# 좋은 예
public_id = "videos/youtube/2026/02/my_video_123"

# 나쁜 예
public_id = "abc123"
```

**이유**: 폴더 구조로 관리하면 나중에 찾기 쉽습니다.

### 2. 변환 결과 캐싱

```python
# 동일한 영상을 여러 번 변환하지 않도록 캐싱
cached_outputs = {}

if platform in cached_outputs:
    output_path = cached_outputs[platform]
else:
    output_path = await service.transform_video_for_platform(...)
    cached_outputs[platform] = output_path
```

### 3. 에러 핸들링

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def upload_with_retry(video_path):
    return await service.upload_video(video_path=video_path)
```

---

## 다음 단계

- [x] Cloudinary 서비스 구현
- [x] API 엔드포인트 추가
- [x] 비용 추적 통합
- [ ] Celery 백그라운드 작업 추가 (대용량 파일 처리)
- [ ] 썸네일 A/B 테스트 자동화
- [ ] 플랫폼별 자동 배포 연동

---

## 참고 자료

- [Cloudinary 공식 문서](https://cloudinary.com/documentation)
- [Cloudinary Python SDK](https://cloudinary.com/documentation/python_integration)
- [Video Transformation Guide](https://cloudinary.com/documentation/video_transformation_reference)
