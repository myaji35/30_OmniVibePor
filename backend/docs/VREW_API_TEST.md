# Vrew 기능 API 테스트 가이드

## 개요
이 문서는 OmniVibe Pro의 Vrew 기능 API를 테스트하는 방법을 설명합니다.

## 전제 조건
1. Backend 서버 실행 중 (`uvicorn app.main:app --reload`)
2. Celery worker 실행 중 (`celery -A app.tasks.celery_app worker --loglevel=info`)
3. Redis 실행 중
4. OpenAI API 키 설정 (필러 워드 제거용)

## 1. 무음 제거 API

### 엔드포인트
```
POST /api/v1/audio/remove-silence
```

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/audio/remove-silence" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "threshold_db": -40,
    "min_silence_duration": 0.5
  }'
```

### Response
```json
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "message": "무음 제거 작업 시작. /audio/status/abc123-def456-ghi789로 진행 상황 확인하세요.",
  "original_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
}
```

### 작업 상태 확인
```bash
curl "http://localhost:8000/api/v1/audio/status/{task_id}"
```

### 완료 시 응답
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "processed_audio_url": "/tmp/tmpXXXXXX.mp3",
    "original_duration": 60.5,
    "new_duration": 55.2,
    "removed_segments": [
      {"start": 10.5, "end": 11.2},
      {"start": 25.3, "end": 27.1}
    ]
  }
}
```

## 2. 필러 워드 제거 API

### 엔드포인트
```
POST /api/v1/audio/remove-fillers
```

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/audio/remove-fillers" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/korean-audio.mp3",
    "filler_words": ["음", "어", "그", "저", "아"],
    "language": "ko"
  }'
```

### Response
```json
{
  "success": true,
  "task_id": "xyz789-abc123-def456",
  "message": "필러 워드 제거 작업 시작. /audio/status/xyz789-abc123-def456로 진행 상황 확인하세요.",
  "original_audio_url": "https://example.com/korean-audio.mp3"
}
```

### 완료 시 응답
```json
{
  "task_id": "xyz789-abc123-def456",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "processed_audio_url": "/tmp/tmpYYYYYY.mp3",
    "transcript": "안녕하세요 저는 오늘 영상을 만들었습니다",
    "removed_words": [
      {"word": "음", "start": 5.2, "end": 5.5},
      {"word": "어", "start": 12.1, "end": 12.3}
    ],
    "original_duration": 60.0,
    "new_duration": 58.5
  }
}
```

## 3. 로컬 파일 테스트

### 로컬 오디오 파일 사용
```bash
# 1. 테스트 오디오 생성 (macOS)
say -o /tmp/test_audio.aiff "안녕하세요 음 저는 어 오늘 영상을 만들었습니다"
ffmpeg -i /tmp/test_audio.aiff -acodec libmp3lame /tmp/test_audio.mp3

# 2. 필러 워드 제거 테스트
curl -X POST "http://localhost:8000/api/v1/audio/remove-fillers" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "/tmp/test_audio.mp3",
    "filler_words": ["음", "어"],
    "language": "ko"
  }'
```

## 4. Python 테스트 스크립트

### 실행 방법
```bash
cd backend
python test_vrew_api.py
```

### 스크립트 내용
- 무음 제거 API 테스트
- 필러 워드 제거 API 테스트
- 작업 상태 폴링
- 결과 출력

## 5. API 문서

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

## 주요 파라미터

### 무음 제거
- `threshold_db`: 무음 기준 (dB)
  - 기본값: -40dB
  - 범위: -80dB ~ -20dB
  - 낮을수록 더 작은 소리도 무음으로 인식
- `min_silence_duration`: 최소 무음 길이 (초)
  - 기본값: 0.5초
  - 범위: 0.1초 ~ 5.0초
  - 이보다 짧은 무음은 제거하지 않음

### 필러 워드 제거
- `filler_words`: 제거할 필러 워드 목록
  - 기본값: ["음", "어", "그", "저", "아"]
  - 언어별로 커스터마이징 가능
- `language`: 언어 코드
  - 기본값: "ko"
  - 지원: ko, en, ja, zh 등 (Whisper 지원 언어)

## FFmpeg 명령어 (내부 구현)

### 무음 감지
```bash
ffmpeg -i input.mp3 \
  -af "silencedetect=noise=-40dB:d=0.5" \
  -f null -
```

### 무음 제거
```bash
ffmpeg -i input.mp3 \
  -af "silenceremove=start_periods=1:start_duration=0:start_threshold=-40dB:detection=peak,silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB:detection=peak" \
  -c:a libmp3lame -b:a 192k \
  output.mp3
```

### 특정 구간 제거 (필러 워드)
```bash
ffmpeg -i input.mp3 \
  -af "aselect='1*not(between(t,5.2,5.5))*not(between(t,12.1,12.3))',asetpts=N/SR/TB" \
  -c:a libmp3lame -b:a 192k \
  output.mp3
```

## Whisper STT (필러 워드 감지)

### OpenAI Whisper API
```python
from openai import OpenAI

client = OpenAI()

with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )

# Word-level timestamps
for word_data in transcript.words:
    print(f"{word_data.word} ({word_data.start}s - {word_data.end}s)")
```

## 에러 처리

### Celery 작업 실패 시
- 자동 재시도 (최대 3회)
- 재시도 간격: 30초
- 최종 실패 시 에러 응답

### 일반적인 에러
1. **오디오 다운로드 실패**
   - 원인: 잘못된 URL, 네트워크 에러
   - 해결: URL 확인, 네트워크 상태 확인

2. **FFmpeg 처리 실패**
   - 원인: 지원하지 않는 포맷, 손상된 파일
   - 해결: 파일 포맷 확인 (MP3, WAV, M4A 권장)

3. **Whisper STT 실패**
   - 원인: OpenAI API 키 누락, 할당량 초과
   - 해결: API 키 확인, 할당량 확인

## TODO

### Cloudinary 업로드
현재는 로컬 파일 경로를 반환하지만, 추후 Cloudinary에 업로드하여 URL 반환 예정:

```python
import cloudinary.uploader

# 업로드
upload_result = cloudinary.uploader.upload(
    temp_output.name,
    resource_type="video",
    folder="omnivibe/processed_audio"
)

processed_audio_url = upload_result["secure_url"]
```

### WebSocket 실시간 진행률
현재는 polling 방식이지만, 추후 WebSocket으로 실시간 진행률 브로드캐스트 예정

## 참고
- FFmpeg 문서: https://ffmpeg.org/ffmpeg-filters.html#silencedetect
- OpenAI Whisper API: https://platform.openai.com/docs/guides/speech-to-text
- Celery 문서: https://docs.celeryq.dev/
