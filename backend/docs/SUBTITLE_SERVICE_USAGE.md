# SubtitleService 사용 가이드

## 개요

`SubtitleService`는 OpenAI Whisper API를 활용하여 오디오 파일에서 자막을 자동 생성하는 서비스입니다. SRT 형식의 자막 파일을 생성하고, FFmpeg를 통해 비디오에 자막을 오버레이(번인)할 수 있습니다.

## 주요 기능

### 1. 기본 자막 생성
- OpenAI Whisper API를 통한 STT (Speech-to-Text)
- 타임스탬프 기반 세그먼트 추출
- SRT 형식 자막 파일 생성

### 2. 타임스탬프 세분화
- **Segment 수준**: 문장/구절 단위 (기본값)
- **Word 수준**: 단어 단위 타임스탬프

### 3. 자막 스타일 프리셋
- **default**: 기본 스타일 (흰색, 검은색 외곽선)
- **youtube**: YouTube 최적화 (큰 폰트, 두꺼운 외곽선)
- **tiktok**: TikTok 스타일 (노란색, 굵은 글씨)
- **instagram**: Instagram 최적화
- **minimal**: 미니멀 스타일

### 4. 고급 기능
- 다국어 자막 생성
- 세그먼트 병합 (가독성 향상)
- FFmpeg 자막 오버레이
- 비용 추적 통합

---

## 빠른 시작

### 기본 사용법

```python
from app.services.subtitle_service import get_subtitle_service

# 서비스 인스턴스 가져오기
subtitle_service = get_subtitle_service()

# 자막 생성
result = await subtitle_service.generate_subtitles(
    audio_path="./audio/my_audio.mp3",
    language="ko",
    user_id="user_123",
    project_id="project_456"
)

print(f"SRT 파일: {result['srt_path']}")
print(f"세그먼트 수: {len(result['segments'])}")
print(f"비용: ${result['cost_usd']:.6f}")
```

### SRT 파일 출력 예시

```srt
1
00:00:00,000 --> 00:00:02,500
안녕하세요. 오늘은 좋은 날씨입니다.

2
00:00:02,500 --> 00:00:05,000
여러분과 함께 할 내용이 있습니다.

3
00:00:05,000 --> 00:00:08,500
먼저 프로젝트 개요를 설명하겠습니다.
```

---

## 상세 사용 예제

### 1. 단어 수준 타임스탬프

```python
result = await subtitle_service.generate_subtitles(
    audio_path="./audio/my_audio.mp3",
    language="ko",
    granularity="word",  # 단어 수준
    user_id="user_123"
)

# 각 단어의 타임스탬프 확인
for seg in result['segments'][:5]:
    print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
```

출력:
```
[0.00s - 0.50s] 안녕하세요
[0.50s - 1.00s] 오늘은
[1.00s - 1.50s] 좋은
[1.50s - 2.00s] 날씨입니다
```

### 2. 다국어 자막 생성

```python
results = await subtitle_service.generate_subtitles_for_multiple_languages(
    audio_path="./audio/presentation.mp3",
    languages=["ko", "en", "ja"],
    output_dir="./outputs/subtitles",
    user_id="user_123"
)

for lang, result in results.items():
    print(f"{lang}: {result['srt_path']}")
```

출력:
```
ko: ./outputs/subtitles/presentation_ko.srt
en: ./outputs/subtitles/presentation_en.srt
ja: ./outputs/subtitles/presentation_ja.srt
```

### 3. 세그먼트 병합 (가독성 향상)

짧은 세그먼트를 병합하여 자막 가독성을 높입니다.

```python
# 원본 자막 생성
result = await subtitle_service.generate_subtitles(
    audio_path="./audio/my_audio.mp3",
    language="ko",
    granularity="word"  # 단어 수준
)

# 세그먼트 병합
merged_segments = subtitle_service.merge_subtitle_segments(
    segments=result['segments'],
    max_duration=5.0,  # 최대 5초
    max_chars=80       # 최대 80자
)

# 병합된 자막으로 SRT 생성
srt_content = subtitle_service._generate_srt_content(merged_segments)
with open("./merged_subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)
```

### 4. 비디오에 자막 오버레이

```python
# YouTube 스타일로 자막 오버레이
output_path = await subtitle_service.apply_subtitles_to_video(
    video_path="./video/my_video.mp4",
    srt_path="./subtitles/my_video.srt",
    output_path="./video/my_video_subtitled.mp4",
    style="youtube"
)

print(f"자막이 적용된 영상: {output_path}")
```

### 5. 커스텀 자막 스타일

```python
custom_style = {
    "fontsize": 36,
    "font": "Comic Sans MS",
    "primary_colour": "&HFF00FF&",  # 마젠타
    "outline_colour": "&H000000&",
    "outline": 3,
    "bold": 1
}

output_path = await subtitle_service.apply_subtitles_to_video(
    video_path="./video/my_video.mp4",
    srt_path="./subtitles/my_video.srt",
    output_path="./video/my_video_custom.mp4",
    custom_style=custom_style
)
```

---

## API 레퍼런스

### `generate_subtitles()`

오디오 파일에서 SRT 자막 생성

**Parameters:**
- `audio_path` (str): 오디오 파일 경로
- `language` (str, optional): 언어 코드 (기본값: "ko")
- `output_srt_path` (str, optional): SRT 파일 저장 경로 (None이면 자동 생성)
- `granularity` (str, optional): 타임스탬프 세분화 ("segment" 또는 "word", 기본값: "segment")
- `user_id` (str, optional): 사용자 ID (비용 추적용)
- `project_id` (str, optional): 프로젝트 ID (비용 추적용)

**Returns:**
```python
{
    "srt_path": str,              # 생성된 SRT 파일 경로
    "segments": List[Dict],       # 자막 세그먼트 리스트
    "duration": float,            # 오디오 총 길이 (초)
    "language": str,              # 감지된 언어
    "word_count": int,            # 단어 수
    "cost_usd": float             # API 비용
}
```

### `apply_subtitles_to_video()`

FFmpeg를 사용하여 비디오에 자막 오버레이

**Parameters:**
- `video_path` (str): 원본 비디오 파일 경로
- `srt_path` (str): SRT 자막 파일 경로
- `output_path` (str): 출력 비디오 파일 경로
- `style` (str, optional): 자막 스타일 프리셋 (기본값: "default")
- `custom_style` (Dict, optional): 커스텀 스타일 설정

**Returns:**
- `str`: 출력 비디오 파일 경로

### `generate_subtitles_for_multiple_languages()`

여러 언어로 자막 생성

**Parameters:**
- `audio_path` (str): 오디오 파일 경로
- `languages` (List[str]): 언어 코드 리스트 (예: ["ko", "en", "ja"])
- `output_dir` (str, optional): 출력 디렉토리
- `user_id` (str, optional): 사용자 ID
- `project_id` (str, optional): 프로젝트 ID

**Returns:**
```python
{
    "ko": {"srt_path": "...", "segments": [...], ...},
    "en": {"srt_path": "...", "segments": [...], ...},
    ...
}
```

### `merge_subtitle_segments()`

짧은 자막 세그먼트를 병합하여 가독성 향상

**Parameters:**
- `segments` (List[Dict]): 원본 세그먼트 리스트
- `max_duration` (float, optional): 병합된 세그먼트 최대 길이 (초, 기본값: 5.0)
- `max_chars` (int, optional): 병합된 세그먼트 최대 글자 수 (기본값: 80)

**Returns:**
- `List[Dict]`: 병합된 세그먼트 리스트

---

## 지원 형식

### 오디오 형식
- MP3 (.mp3)
- MP4 Audio (.mp4)
- MPEG (.mpeg, .mpga)
- M4A (.m4a)
- WAV (.wav)
- WebM (.webm)

### 비디오 형식
- MP4 (.mp4)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)
- WebM (.webm)

---

## 자막 스타일 프리셋

### default
```python
{
    "fontsize": 24,
    "font": "Arial",
    "primary_colour": "&HFFFFFF&",  # 흰색
    "outline_colour": "&H000000&",  # 검은색
    "outline": 1,
    "bold": 0
}
```

### youtube
```python
{
    "fontsize": 28,
    "font": "Arial",
    "primary_colour": "&HFFFFFF&",
    "outline_colour": "&H000000&",
    "outline": 2,
    "bold": 0
}
```

### tiktok
```python
{
    "fontsize": 32,
    "font": "Impact",
    "primary_colour": "&HFFFF00&",  # 노란색
    "outline_colour": "&H000000&",
    "outline": 3,
    "bold": 1
}
```

### instagram
```python
{
    "fontsize": 30,
    "font": "Helvetica",
    "primary_colour": "&HFFFFFF&",
    "outline_colour": "&H000000&",
    "outline": 2,
    "bold": 1
}
```

### minimal
```python
{
    "fontsize": 22,
    "font": "Helvetica",
    "primary_colour": "&HFFFFFF&",
    "outline_colour": "&H000000&",
    "outline": 1,
    "bold": 0
}
```

---

## 비용 추적

자막 생성 시 Whisper API 비용이 자동으로 추적됩니다.

```python
result = await subtitle_service.generate_subtitles(
    audio_path="./audio/my_audio.mp3",
    language="ko",
    user_id="user_123",
    project_id="project_456"
)

print(f"API 비용: ${result['cost_usd']:.6f}")
```

### Whisper API 가격
- **$0.006 / 분**

예시:
- 5분 오디오: $0.030
- 30분 오디오: $0.180
- 1시간 오디오: $0.360

---

## 에러 처리

```python
try:
    result = await subtitle_service.generate_subtitles(
        audio_path="./audio/my_audio.mp3",
        language="ko"
    )
except FileNotFoundError as e:
    print(f"파일을 찾을 수 없습니다: {e}")
except ValueError as e:
    print(f"형식 오류: {e}")
except RuntimeError as e:
    print(f"처리 중 오류 발생: {e}")
```

---

## 성능 최적화 팁

### 1. Segment vs Word
- **Segment**: 빠르고 비용 효율적 (문장 단위)
- **Word**: 정밀하지만 세그먼트 수가 많음 (단어 단위)

### 2. 세그먼트 병합
- 단어 수준 자막을 생성한 후 `merge_subtitle_segments()`로 병합
- 가독성 향상 + 자막 수 감소

### 3. 다국어 자막
- 여러 언어가 필요한 경우 `generate_subtitles_for_multiple_languages()` 사용
- 병렬 처리로 시간 절약

---

## 주의사항

### FFmpeg 필수
자막 오버레이 기능을 사용하려면 FFmpeg가 설치되어야 합니다.

**설치 방법:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

### 환경 변수
`.env` 파일에 OpenAI API 키를 설정해야 합니다.

```bash
OPENAI_API_KEY=sk-...
```

---

## 트러블슈팅

### 1. "FFmpeg not found" 에러
**해결책:** FFmpeg를 설치하세요 (위 설치 방법 참조)

### 2. "Unsupported audio format" 에러
**해결책:** 지원되는 오디오 형식으로 변환하세요
```bash
ffmpeg -i input.opus -c:a libmp3lame output.mp3
```

### 3. "Word-level timestamps not available" 경고
**해결책:** Whisper API가 단어 수준 타임스탬프를 제공하지 못하는 경우입니다. 자동으로 segment 수준으로 폴백됩니다.

### 4. 자막이 비디오에 나타나지 않음
**해결책:**
- SRT 파일의 타임스탬프가 비디오 길이를 초과하는지 확인
- FFmpeg 로그에서 에러 메시지 확인

---

## 통합 예제

### 완전한 워크플로우

```python
import asyncio
from app.services.subtitle_service import get_subtitle_service

async def create_multilingual_subtitled_video():
    """다국어 자막이 포함된 비디오 생성"""
    service = get_subtitle_service()

    # 1. 오디오에서 자막 생성
    ko_result = await service.generate_subtitles(
        audio_path="./audio/presentation.mp3",
        language="ko",
        output_srt_path="./subtitles/presentation_ko.srt",
        user_id="user_123",
        project_id="project_456"
    )

    print(f"한국어 자막 생성 완료: {ko_result['srt_path']}")
    print(f"비용: ${ko_result['cost_usd']:.6f}")

    # 2. 세그먼트 병합 (가독성 향상)
    merged_segments = service.merge_subtitle_segments(
        segments=ko_result['segments'],
        max_duration=4.0,
        max_chars=60
    )

    # 3. 병합된 자막으로 새 SRT 생성
    merged_srt = service._generate_srt_content(merged_segments)
    with open("./subtitles/presentation_ko_merged.srt", "w", encoding="utf-8") as f:
        f.write(merged_srt)

    # 4. 비디오에 자막 오버레이
    output_video = await service.apply_subtitles_to_video(
        video_path="./video/presentation.mp4",
        srt_path="./subtitles/presentation_ko_merged.srt",
        output_path="./video/presentation_ko_subtitled.mp4",
        style="youtube"
    )

    print(f"자막 오버레이 완료: {output_video}")

    # 5. 다른 언어로도 자막 생성
    en_result = await service.generate_subtitles(
        audio_path="./audio/presentation.mp3",
        language="en",
        output_srt_path="./subtitles/presentation_en.srt",
        user_id="user_123",
        project_id="project_456"
    )

    print(f"영어 자막 생성 완료: {en_result['srt_path']}")

    return {
        "ko_video": output_video,
        "ko_srt": "./subtitles/presentation_ko_merged.srt",
        "en_srt": en_result['srt_path'],
        "total_cost": ko_result['cost_usd'] + en_result['cost_usd']
    }

# 실행
result = asyncio.run(create_multilingual_subtitled_video())
print(f"\n총 비용: ${result['total_cost']:.6f}")
```

---

## 라이선스 및 제한사항

### OpenAI API 사용 제한
- 오디오 파일 크기: 최대 25MB
- 지원 언어: 99개 언어 (자세한 내용은 OpenAI 문서 참조)

### FFmpeg 라이선스
- FFmpeg는 LGPL/GPL 라이선스입니다.
- 상업적 사용 시 라이선스 확인 필요

---

## 참고 자료

- [OpenAI Whisper API 문서](https://platform.openai.com/docs/guides/speech-to-text)
- [SRT 형식 명세](https://en.wikipedia.org/wiki/SubRip)
- [FFmpeg 문서](https://ffmpeg.org/documentation.html)
- [FFmpeg Subtitles 필터](https://ffmpeg.org/ffmpeg-filters.html#subtitles)
