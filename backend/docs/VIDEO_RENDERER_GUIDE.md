# VideoRenderer 사용 가이드

## 개요

`VideoRenderer`는 FFmpeg 기반의 고품질 영상 렌더링 시스템입니다. 여러 영상 클립을 병합하고, 오디오를 믹싱하며, 자막을 추가하고, 플랫폼별로 최적화하는 전체 파이프라인을 제공합니다.

## 주요 기능

### 1. 클립 병합
- 여러 영상 클립을 하나로 병합
- 31가지 전환 효과 지원 (fade, wipe, slide, dissolve 등)
- 전환 효과 지속 시간 조절 가능

### 2. 오디오 믹싱
- 나레이션 오디오 추가
- BGM (배경음악) 믹싱
- BGM 볼륨 조절 (0.0-1.0)

### 3. 자막 오버레이
- SRT 자막 파일 지원
- 5가지 스타일 프리셋 (default, youtube, tiktok, instagram, minimal)
- 폰트 크기, 색상, 테두리 커스터마이징

### 4. 플랫폼별 최적화
- YouTube: 1920x1080 (16:9), 8M bitrate
- Instagram 피드: 1080x1350 (4:5), 5M bitrate
- Instagram 스토리/릴스: 1080x1920 (9:16), 4M bitrate
- TikTok: 1080x1920 (9:16), 4M bitrate
- Facebook: 1280x720 (16:9), 6M bitrate

## API 엔드포인트

### 1. 전체 렌더링 파이프라인

**엔드포인트**: `POST /api/v1/video/render`

**요청 예시**:
```json
{
  "video_clips": [
    "./outputs/videos/clip1.mp4",
    "./outputs/videos/clip2.mp4",
    "./outputs/videos/clip3.mp4"
  ],
  "audio_path": "./outputs/audio/narration.mp3",
  "subtitle_path": "./outputs/subtitles/script.srt",
  "transitions": ["fade", "wipeleft", "slideup"],
  "bgm_path": "./assets/bgm/background.mp3",
  "bgm_volume": 0.2,
  "transition_duration": 0.5,
  "platform": "youtube"
}
```

**응답 예시**:
```json
{
  "status": "success",
  "output_path": "./outputs/videos/final_1234567890.mp4",
  "file_size_mb": 45.67,
  "render_time": 12.34,
  "steps": {
    "merge_clips": {
      "output_path": "./outputs/videos/merged_xxx.mp4",
      "method": "xfade",
      "clip_count": 3,
      "transitions_used": ["fade", "wipeleft", "slideup"],
      "elapsed_time": 5.2
    },
    "audio_mix": {
      "output_path": "./outputs/videos/with_audio_xxx.mp4",
      "has_bgm": true,
      "bgm_volume": 0.2,
      "elapsed_time": 3.1
    },
    "subtitles": {
      "output_path": "./outputs/videos/with_subtitle_xxx.mp4",
      "style": "youtube",
      "elapsed_time": 2.8
    },
    "platform_optimize": {
      "output_path": "./outputs/videos/final_1234567890.mp4",
      "platform": "youtube",
      "resolution": "1920x1080",
      "bitrate": "8M",
      "elapsed_time": 4.5
    }
  }
}
```

### 2. 클립 병합만 수행

**엔드포인트**: `POST /api/v1/video/merge-clips`

**요청 예시**:
```json
{
  "clips": [
    "./outputs/videos/scene1.mp4",
    "./outputs/videos/scene2.mp4",
    "./outputs/videos/scene3.mp4"
  ],
  "transitions": ["fade", "wipeleft"],
  "transition_duration": 0.5,
  "output_filename": "merged_scenes.mp4"
}
```

### 3. 플랫폼 최적화만 수행

**엔드포인트**: `POST /api/v1/video/optimize`

**요청 예시**:
```json
{
  "video_path": "./outputs/videos/original.mp4",
  "platform": "instagram",
  "output_filename": "instagram_optimized.mp4"
}
```

### 4. 사용 가능한 전환 효과 조회

**엔드포인트**: `GET /api/v1/video/transitions`

**응답 예시**:
```json
{
  "transitions": {
    "fade": "페이드 전환 (기본)",
    "wipeleft": "왼쪽에서 와이프",
    "wiperight": "오른쪽에서 와이프",
    "slideleft": "왼쪽으로 슬라이드",
    "slideright": "오른쪽으로 슬라이드",
    "circlecrop": "원형 크롭 전환",
    "dissolve": "디졸브 전환",
    "pixelize": "픽셀화 전환"
  },
  "total": 31
}
```

### 5. 지원 플랫폼 조회

**엔드포인트**: `GET /api/v1/video/platforms`

**응답 예시**:
```json
{
  "platforms": {
    "youtube": {
      "description": "YouTube 최적화 (Full HD, 16:9)",
      "resolution": "1920x1080",
      "bitrate": "8M",
      "fps": 30
    },
    "instagram": {
      "description": "Instagram 피드 최적화 (4:5)",
      "resolution": "1080x1350",
      "bitrate": "5M",
      "fps": 30
    }
  }
}
```

### 6. 자막 스타일 조회

**엔드포인트**: `GET /api/v1/video/subtitle-styles`

**응답 예시**:
```json
{
  "styles": {
    "default": "기본 스타일 (하단 중앙, 흰색 글자, 검은색 테두리)",
    "youtube": "YouTube 스타일 (큰 폰트, 하단 중앙)",
    "tiktok": "TikTok 스타일 (노란색, 중앙, 큰 폰트)",
    "instagram": "Instagram 스타일 (하단 중앙)",
    "minimal": "미니멀 스타일 (작은 폰트, 얇은 테두리)"
  }
}
```

### 7. 영상 다운로드

**엔드포인트**: `GET /api/v1/video/download/{filename}`

**사용법**:
1. `/video/render`로 렌더링
2. 응답의 `output_path`에서 파일명 추출 (예: `final_1234567890.mp4`)
3. `/video/download/final_1234567890.mp4`로 다운로드

### 8. 헬스 체크

**엔드포인트**: `GET /api/v1/video/health`

**응답 예시**:
```json
{
  "status": "healthy",
  "ffmpeg_version": "ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers",
  "output_dir": "./outputs/videos",
  "output_dir_writable": true
}
```

## Python SDK 사용법

### 기본 사용

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

print(f"렌더링 완료: {result['output_path']}")
print(f"파일 크기: {result['file_size_mb']} MB")
print(f"렌더링 시간: {result['render_time']}초")
```

### 클립 병합만 수행

```python
# 전환 효과 없이 단순 병합
result = renderer.merge_clips(
    clips=["clip1.mp4", "clip2.mp4"],
    output_path="merged.mp4"
)

# 전환 효과와 함께 병합
result = renderer.merge_clips(
    clips=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    output_path="merged_with_transitions.mp4",
    transitions=["fade", "wipeleft"],
    transition_duration=0.5
)
```

### 오디오 믹싱

```python
# 나레이션만 추가
result = renderer.add_audio_mix(
    video_path="video.mp4",
    audio_path="narration.mp3",
    output_path="with_audio.mp4"
)

# 나레이션 + BGM 믹싱
result = renderer.add_audio_mix(
    video_path="video.mp4",
    audio_path="narration.mp3",
    bgm_path="background.mp3",
    output_path="with_audio_and_bgm.mp4",
    bgm_volume=0.2  # BGM 볼륨 20%
)
```

### 자막 추가

```python
result = renderer.add_subtitles_overlay(
    video_path="video.mp4",
    subtitle_path="subtitles.srt",
    output_path="with_subtitles.mp4",
    style="youtube"  # 또는 "tiktok", "instagram", "minimal"
)
```

### 플랫폼별 최적화

```python
# YouTube 최적화 (1920x1080, 16:9)
result = renderer.optimize_for_platform(
    video_path="original.mp4",
    platform="youtube",
    output_path="youtube.mp4"
)

# Instagram 피드 최적화 (1080x1350, 4:5)
result = renderer.optimize_for_platform(
    video_path="original.mp4",
    platform="instagram",
    output_path="instagram.mp4"
)

# TikTok 최적화 (1080x1920, 9:16)
result = renderer.optimize_for_platform(
    video_path="original.mp4",
    platform="tiktok",
    output_path="tiktok.mp4"
)
```

## 전환 효과 목록

### 기본 전환
- `fade`: 페이드 (가장 자연스러움)
- `dissolve`: 디졸브
- `pixelize`: 픽셀화

### 와이프 전환
- `wipeleft`: 왼쪽에서 와이프
- `wiperight`: 오른쪽에서 와이프
- `wipeup`: 위에서 와이프
- `wipedown`: 아래에서 와이프

### 슬라이드 전환
- `slideleft`: 왼쪽으로 슬라이드
- `slideright`: 오른쪽으로 슬라이드
- `slideup`: 위로 슬라이드
- `slidedown`: 아래로 슬라이드

### 부드러운 전환
- `smoothleft`: 부드러운 왼쪽 전환
- `smoothright`: 부드러운 오른쪽 전환
- `smoothup`: 부드러운 위쪽 전환
- `smoothdown`: 부드러운 아래쪽 전환

### 형태 전환
- `circlecrop`: 원형 크롭
- `circleopen`: 원형 열기
- `circleclose`: 원형 닫기
- `rectcrop`: 사각형 크롭

### 창문 전환
- `vertopen`: 수직 열기
- `vertclose`: 수직 닫기
- `horzopen`: 수평 열기
- `horzclose`: 수평 닫기

### 대각선 전환
- `diagtl`: 대각선 (왼쪽 위)
- `diagtr`: 대각선 (오른쪽 위)
- `diagbl`: 대각선 (왼쪽 아래)
- `diagbr`: 대각선 (오른쪽 아래)

### 특수 전환
- `distance`: 거리 왜곡
- `radial`: 방사형
- `fadeblack`: 검은색으로 페이드
- `fadewhite`: 흰색으로 페이드

## 자막 파일 형식 (SRT)

자막 파일은 SRT (SubRip Subtitle) 형식을 사용합니다.

**예시** (`subtitles.srt`):
```
1
00:00:00,000 --> 00:00:03,000
안녕하세요, OmniVibe Pro입니다.

2
00:00:03,500 --> 00:00:07,000
오늘은 영상 렌더링 시스템을 소개합니다.

3
00:00:07,500 --> 00:00:11,000
여러 클립을 병합하고 자막을 추가할 수 있습니다.
```

## 성능 최적화 팁

### 1. 클립 병합
- **전환 효과 없음**: 재인코딩 없이 복사 (`-c copy`) → 매우 빠름
- **전환 효과 있음**: xfade 필터 사용 → 재인코딩 필요 (느림)
- **권장**: 전환이 필요한 부분만 xfade 사용

### 2. 오디오 믹싱
- **나레이션만**: 영상 재인코딩 없음 (`-c:v copy`) → 빠름
- **BGM 포함**: amix 필터 사용, 영상은 복사 → 빠름

### 3. 자막 오버레이
- **subtitles 필터**: 영상 재인코딩 필요 → 느림
- **권장**: 최종 단계에서 한 번만 적용

### 4. 플랫폼 최적화
- **scale 필터**: 해상도 변경 시 재인코딩 필요 → 느림
- **권장**: 미리 해상도를 고려하여 촬영/생성

### 5. 렌더링 순서 최적화
```
권장 순서:
1. 클립 병합 (전환 효과)
2. 오디오 믹싱 (영상 복사)
3. 자막 오버레이 (재인코딩)
4. 플랫폼 최적화 (재인코딩)
```

## 트러블슈팅

### FFmpeg 관련

**문제**: `FFmpeg not found`
**해결**:
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# Windows
# https://ffmpeg.org/ 에서 다운로드
```

**문제**: `Unknown codec` 에러
**해결**: FFmpeg를 최신 버전으로 업데이트
```bash
brew upgrade ffmpeg  # macOS
```

### 파일 경로 관련

**문제**: `File not found` 에러
**해결**: 절대 경로 사용 또는 현재 작업 디렉토리 확인
```python
from pathlib import Path

# 상대 경로를 절대 경로로 변환
clip_path = str(Path("./outputs/videos/clip1.mp4").resolve())
```

### 성능 관련

**문제**: 렌더링이 너무 느림
**해결**:
1. 전환 효과 최소화
2. 클립 개수 줄이기
3. 해상도 미리 맞추기 (플랫폼 최적화 생략)
4. H.264 하드웨어 인코딩 사용 (GPU 가속)

**문제**: 메모리 부족
**해결**:
1. 클립을 작은 단위로 분할
2. 임시 파일 주기적으로 삭제
3. 해상도 낮추기

## 사용 사례

### 사례 1: YouTube 영상 제작
```python
renderer = get_video_renderer()

# 1. 여러 장면 병합
await renderer.render_video(
    video_clips=[
        "intro.mp4",
        "main_content.mp4",
        "outro.mp4"
    ],
    audio_path="narration.mp3",
    subtitle_path="script.srt",
    transitions=["fade", "dissolve"],
    bgm_path="background_music.mp3",
    bgm_volume=0.15,
    platform="youtube"
)
```

### 사례 2: 멀티 플랫폼 배포
```python
# 1. 마스터 영상 렌더링 (최고 품질)
master = await renderer.render_video(
    video_clips=clips,
    audio_path=audio,
    subtitle_path=subtitle,
    output_path="master.mp4"
)

# 2. 플랫폼별 최적화
for platform in ["youtube", "instagram", "tiktok"]:
    renderer.optimize_for_platform(
        video_path="master.mp4",
        platform=platform,
        output_path=f"{platform}_optimized.mp4"
    )
```

### 사례 3: 클립 스타일 영상 (전환 효과 많이 사용)
```python
# 짧은 클립들을 빠르게 전환하는 영상
clips = [f"clip_{i}.mp4" for i in range(10)]
transitions = ["fade", "wipeleft", "wiperight", "slideup", "slidedown"] * 2

await renderer.render_video(
    video_clips=clips,
    audio_path="upbeat_music.mp3",
    transitions=transitions[:len(clips)-1],
    transition_duration=0.3,  # 빠른 전환
    platform="tiktok"
)
```

## 비용 추적

VideoRenderer는 Logfire를 통해 렌더링 시간을 추적합니다:

- **merge_clips**: 클립 병합 시간
- **audio_mix**: 오디오 믹싱 시간
- **subtitles**: 자막 오버레이 시간
- **platform_optimize**: 플랫폼 최적화 시간

각 단계별 시간은 응답의 `steps` 객체에서 확인할 수 있습니다.

## 향후 계획

- [ ] 하드웨어 가속 (GPU) 지원
- [ ] 실시간 프리뷰
- [ ] 커스텀 전환 효과 (LUT 기반)
- [ ] 오디오 이펙트 (노이즈 제거, 이퀄라이저)
- [ ] 배치 렌더링 (여러 영상 동시 처리)
- [ ] 진행률 추적 (Celery 통합)

## 라이선스

FFmpeg는 LGPL/GPL 라이선스를 따릅니다. 상업적 사용 시 라이선스를 확인하세요.

---

**문의**: OmniVibe Pro 팀
**버전**: 1.0.0
**최종 업데이트**: 2026-02-02
