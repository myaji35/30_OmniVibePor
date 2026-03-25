# VideoRenderer - FFmpeg 기반 영상 렌더링 시스템

## 빠른 시작

### 1. 의존성 설치

```bash
# FFmpeg 설치 (macOS)
brew install ffmpeg

# FFmpeg 설치 (Ubuntu)
sudo apt-get install ffmpeg

# Python 패키지 설치
poetry install
```

### 2. API 서버 실행

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

### 3. API 테스트

```bash
# 기본 정보 조회
./test_video_api.sh

# 또는 직접 cURL 사용
curl http://localhost:8000/api/v1/video/health
```

### 4. 영상 렌더링

```bash
curl -X POST "http://localhost:8000/api/v1/video/render" \
  -H "Content-Type: application/json" \
  -d '{
    "video_clips": ["./outputs/videos/clip1.mp4", "./outputs/videos/clip2.mp4"],
    "audio_path": "./outputs/audio/narration.mp3",
    "transitions": ["fade"],
    "platform": "youtube"
  }'
```

## 주요 기능

### ✅ 클립 병합
- 여러 영상 클립을 하나로 병합
- 31가지 전환 효과 (fade, wipe, slide, dissolve 등)
- 전환 효과 없는 빠른 concat 모드

### ✅ 오디오 믹싱
- 나레이션 오디오 추가
- BGM (배경음악) 믹싱
- BGM 볼륨 조절 (0.0-1.0)

### ✅ 자막 오버레이
- SRT 자막 파일 지원
- 5가지 스타일 프리셋
- 폰트, 색상, 위치 커스터마이징

### ✅ 플랫폼별 최적화
- YouTube: 1920x1080 (16:9)
- Instagram 피드: 1080x1350 (4:5)
- Instagram 스토리/릴스: 1080x1920 (9:16)
- TikTok: 1080x1920 (9:16)
- Facebook: 1280x720 (16:9)

## 파일 구조

```
backend/
├── app/
│   ├── services/
│   │   └── video_renderer.py          # VideoRenderer 메인 클래스
│   └── api/
│       └── v1/
│           └── video.py                # Video API 엔드포인트
├── docs/
│   └── VIDEO_RENDERER_GUIDE.md        # 상세 사용 가이드
├── test_video_renderer.py              # Python 테스트 스크립트
├── test_video_api.sh                   # API 테스트 스크립트
└── outputs/
    ├── videos/                         # 렌더링된 영상 저장소
    └── audio/                          # 오디오 파일 저장소
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/video/render` | POST | 전체 렌더링 파이프라인 |
| `/api/v1/video/merge-clips` | POST | 클립 병합만 수행 |
| `/api/v1/video/optimize` | POST | 플랫폼 최적화만 수행 |
| `/api/v1/video/transitions` | GET | 사용 가능한 전환 효과 조회 |
| `/api/v1/video/platforms` | GET | 지원 플랫폼 조회 |
| `/api/v1/video/subtitle-styles` | GET | 자막 스타일 조회 |
| `/api/v1/video/download/{filename}` | GET | 렌더링된 영상 다운로드 |
| `/api/v1/video/health` | GET | 헬스 체크 |

## Python SDK 사용 예시

```python
from app.services.video_renderer import get_video_renderer

renderer = get_video_renderer()

# 전체 렌더링 파이프라인
result = await renderer.render_video(
    video_clips=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    audio_path="narration.mp3",
    output_path="final.mp4",
    subtitle_path="subtitles.srt",
    transitions=["fade", "wipeleft"],
    bgm_path="background.mp3",
    bgm_volume=0.2,
    platform="youtube"
)

print(f"✅ 렌더링 완료: {result['output_path']}")
print(f"📦 파일 크기: {result['file_size_mb']} MB")
print(f"⏱️  렌더링 시간: {result['render_time']}초")
```

## 전환 효과 (일부)

| 효과 | 설명 |
|-----|------|
| `fade` | 페이드 전환 (기본) |
| `wipeleft` | 왼쪽에서 와이프 |
| `slideleft` | 왼쪽으로 슬라이드 |
| `circlecrop` | 원형 크롭 전환 |
| `dissolve` | 디졸브 전환 |
| `pixelize` | 픽셀화 전환 |

**전체 31가지 전환 효과 지원** (상세 목록은 `/api/v1/video/transitions` 참조)

## 성능 최적화

### 빠른 렌더링 (전환 효과 없음)
```python
# 재인코딩 없이 복사 (매우 빠름)
result = renderer.merge_clips(
    clips=["clip1.mp4", "clip2.mp4"],
    output_path="merged.mp4"
    # transitions 생략
)
```

### 고품질 렌더링 (전환 효과 있음)
```python
# xfade 필터 사용 (재인코딩 필요, 느림)
result = renderer.merge_clips(
    clips=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    output_path="merged.mp4",
    transitions=["fade", "wipeleft"]
)
```

### 멀티 플랫폼 배포
```python
# 1. 마스터 영상 렌더링
master = await renderer.render_video(...)

# 2. 각 플랫폼별 최적화
for platform in ["youtube", "instagram", "tiktok"]:
    renderer.optimize_for_platform(
        video_path="master.mp4",
        platform=platform,
        output_path=f"{platform}.mp4"
    )
```

## 트러블슈팅

### FFmpeg not found
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

### 렌더링이 너무 느림
1. 전환 효과 최소화 (재인코딩이 필요함)
2. 해상도를 미리 맞추기 (플랫폼 최적화 생략)
3. 클립 개수 줄이기

### 파일을 찾을 수 없음
```python
# 상대 경로 대신 절대 경로 사용
from pathlib import Path
clip_path = str(Path("./outputs/videos/clip1.mp4").resolve())
```

## 상세 문서

- [📖 VideoRenderer 사용 가이드](./docs/VIDEO_RENDERER_GUIDE.md)
- [🎬 API 문서](http://localhost:8000/docs) (서버 실행 후)

## 사용 사례

### 1. YouTube 영상 제작
```python
await renderer.render_video(
    video_clips=["intro.mp4", "main.mp4", "outro.mp4"],
    audio_path="narration.mp3",
    subtitle_path="script.srt",
    transitions=["fade", "dissolve"],
    bgm_path="background.mp3",
    bgm_volume=0.15,
    platform="youtube"
)
```

### 2. 멀티 플랫폼 배포
```python
# 마스터 영상 생성
master = await renderer.render_video(...)

# 플랫폼별 최적화
for platform in ["youtube", "instagram", "tiktok"]:
    renderer.optimize_for_platform(
        video_path="master.mp4",
        platform=platform,
        output_path=f"{platform}_optimized.mp4"
    )
```

### 3. 클립 스타일 영상 (빠른 전환)
```python
clips = [f"clip_{i}.mp4" for i in range(10)]
transitions = ["fade", "wipeleft", "wiperight"] * 3

await renderer.render_video(
    video_clips=clips,
    audio_path="upbeat_music.mp3",
    transitions=transitions[:len(clips)-1],
    transition_duration=0.3,  # 빠른 전환
    platform="tiktok"
)
```

## 비용 추적

VideoRenderer는 Logfire를 통해 각 단계별 렌더링 시간을 추적합니다:

```python
result = await renderer.render_video(...)

print(result['steps'])
# {
#   "merge_clips": {"elapsed_time": 5.2},
#   "audio_mix": {"elapsed_time": 3.1},
#   "subtitles": {"elapsed_time": 2.8},
#   "platform_optimize": {"elapsed_time": 4.5}
# }
```

## 라이선스

FFmpeg는 LGPL/GPL 라이선스를 따릅니다. 상업적 사용 시 라이선스를 확인하세요.

---

**버전**: 1.0.0
**최종 업데이트**: 2026-02-02
**문의**: OmniVibe Pro 팀
