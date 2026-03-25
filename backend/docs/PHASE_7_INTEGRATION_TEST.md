# Phase 7 Integration Test Guide

## Overview

이 문서는 Phase 7 (PDF Presentation Mode)의 통합 테스트 가이드입니다.

**테스트 범위**:
- PDF 업로드 → 슬라이드 추출
- 슬라이드 → 나레이션 스크립트 생성
- TTS 오디오 생성
- Whisper 타이밍 분석
- 영상 생성 (FFmpeg + 화면 전환)

**목표**:
- 엔드투엔드 워크플로우 검증
- 슬라이드 타이밍 정확도 90%+ 확인
- 화면 전환 효과 정상 작동 확인

---

## Prerequisites

### 1. System Requirements

- Docker Desktop 실행 중
- Python 3.11+
- Node.js 18+
- Tesseract OCR 설치
- FFmpeg 설치

### 2. 환경 변수 확인

```bash
# backend/.env
ANTHROPIC_API_KEY=your_api_key
ELEVENLABS_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key  # Whisper API
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
REDIS_URL=redis://localhost:6379
```

### 3. Tesseract 언어 데이터 설치

```bash
# macOS
brew install tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr-kor tesseract-ocr-eng

# 확인
tesseract --list-langs
# kor, eng 포함되어야 함
```

### 4. 테스트 데이터 준비

```bash
cd backend
mkdir -p test_data
# test_data/sample_presentation.pdf 파일을 넣으세요
```

---

## Test Execution

### Option 1: Automated Script (권장)

```bash
cd backend
./test_presentation_integration.sh
```

**스크립트 동작**:
1. Health Check
2. PDF 업로드 (POST /presentations/upload)
3. 스크립트 생성 (POST /presentations/{id}/generate-script)
4. 오디오 생성 (POST /presentations/{id}/generate-audio)
5. 타이밍 분석 (POST /presentations/{id}/analyze-timing)
6. 영상 생성 (POST /presentations/{id}/generate-video)
7. 상태 폴링 (GET /presentations/{id})

**예상 소요 시간**:
- 10슬라이드 기준: 약 5-10분
- TTS 생성: 슬라이드당 10-30초
- Whisper 분석: 1-2분
- FFmpeg 렌더링: 2-5분

---

### Option 2: Manual API Testing

#### Step 1: Health Check

```bash
curl http://localhost:8123/api/v1/health | jq '.'
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "neo4j": "connected",
    "redis": "connected"
  }
}
```

---

#### Step 2: Upload PDF

```bash
curl -X POST http://localhost:8123/api/v1/presentations/upload \
  -F "file=@test_data/sample_presentation.pdf" \
  -F "project_id=test-project-001" \
  -F "dpi=200" \
  -F "lang=kor+eng" | jq '.'
```

**Expected Response**:
```json
{
  "success": true,
  "presentation_id": "pres_abc123",
  "project_id": "test-project-001",
  "pdf_filename": "sample_presentation.pdf",
  "total_slides": 10,
  "slides": [
    {
      "slide_id": "slide-001",
      "slide_number": 1,
      "image_path": "/slides/pres_abc123/slide-001.png",
      "extracted_text": "...",
      "confidence": 0.95,
      "word_count": 25
    }
  ],
  "status": "UPLOADED",
  "created_at": "2026-02-02T10:30:00Z"
}
```

**검증 항목**:
- ✅ total_slides > 0
- ✅ 각 슬라이드에 image_path 존재
- ✅ extracted_text가 비어있지 않음
- ✅ confidence > 0.7
- ✅ status = "UPLOADED"

---

#### Step 3: Generate Narration Script

```bash
PRESENTATION_ID="pres_abc123"

curl -X POST http://localhost:8123/api/v1/presentations/${PRESENTATION_ID}/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "tone": "professional",
    "target_duration_per_slide": 15.0
  }' | jq '.'
```

**Expected Response**:
```json
{
  "success": true,
  "presentation_id": "pres_abc123",
  "script": "안녕하세요. 오늘은 OmniVibe Pro를 소개하겠습니다...",
  "total_duration": 150.0,
  "slide_scripts": [
    {
      "slide_number": 1,
      "script": "안녕하세요...",
      "estimated_duration": 15.2
    }
  ],
  "status": "SCRIPT_GENERATED"
}
```

**검증 항목**:
- ✅ script가 비어있지 않음
- ✅ slide_scripts 개수 = total_slides
- ✅ total_duration ≈ target_duration_per_slide × total_slides
- ✅ status = "SCRIPT_GENERATED"

---

#### Step 4: Generate TTS Audio

```bash
curl -X POST http://localhost:8123/api/v1/presentations/${PRESENTATION_ID}/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75
  }' | jq '.'
```

**Expected Response**:
```json
{
  "success": true,
  "presentation_id": "pres_abc123",
  "audio_path": "/audio/pres_abc123_narration.mp3",
  "duration": 148.5,
  "file_size": 2458000,
  "status": "AUDIO_GENERATED"
}
```

**검증 항목**:
- ✅ audio_path 파일 존재
- ✅ duration > 0
- ✅ file_size > 100000 (100KB+)
- ✅ status = "AUDIO_GENERATED"

**수동 검증**:
```bash
# 오디오 재생
afplay /path/to/audio/pres_abc123_narration.mp3
```

---

#### Step 5: Analyze Slide Timing

```bash
curl -X POST http://localhost:8123/api/v1/presentations/${PRESENTATION_ID}/analyze-timing | jq '.'
```

**Expected Response**:
```json
{
  "success": true,
  "presentation_id": "pres_abc123",
  "timing": [
    {
      "slide_number": 1,
      "start_time": 0.0,
      "end_time": 14.8,
      "duration": 14.8,
      "confidence": 0.95
    },
    {
      "slide_number": 2,
      "start_time": 14.8,
      "end_time": 29.5,
      "duration": 14.7,
      "confidence": 0.92
    }
  ],
  "avg_confidence": 0.94,
  "status": "TIMING_ANALYZED"
}
```

**검증 항목**:
- ✅ timing 배열 개수 = total_slides
- ✅ avg_confidence > 0.90 (90%+ 정확도)
- ✅ 각 슬라이드의 start_time < end_time
- ✅ 슬라이드 간 중복/갭 없음 (± 0.5초 이내)
- ✅ 마지막 슬라이드 end_time ≈ audio duration
- ✅ status = "TIMING_ANALYZED"

**정확도 계산**:
```python
# confidence = 1.0 - (text_diff / total_text_length)
# text_diff: Whisper 인식 텍스트와 스크립트의 차이
# 90%+ = 텍스트 매칭률 90% 이상
```

---

#### Step 6: Generate Presentation Video

```bash
curl -X POST http://localhost:8123/api/v1/presentations/${PRESENTATION_ID}/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "transition_effect": "fade",
    "transition_duration": 0.5,
    "bgm_settings": {
      "enabled": false
    }
  }' | jq '.'
```

**Expected Response**:
```json
{
  "success": true,
  "presentation_id": "pres_abc123",
  "task_id": "celery-task-123",
  "status": "VIDEO_GENERATING",
  "message": "영상 생성이 시작되었습니다. 작업 ID: celery-task-123"
}
```

**검증 항목**:
- ✅ task_id 반환됨
- ✅ status = "VIDEO_GENERATING"

---

#### Step 7: Poll Video Generation Status

```bash
# 3초마다 폴링
while true; do
  curl -s http://localhost:8123/api/v1/presentations/${PRESENTATION_ID} | jq '.status'
  sleep 3
done
```

**Status 변화**:
1. `VIDEO_GENERATING` → 진행 중
2. `VIDEO_READY` → 완료
3. `FAILED` → 실패

**완료 시 Response**:
```json
{
  "presentation_id": "pres_abc123",
  "status": "VIDEO_READY",
  "video_path": "/videos/pres_abc123_presentation.mp4",
  "video_duration": 148.5,
  "file_size": 25000000,
  "created_at": "2026-02-02T10:30:00Z",
  "completed_at": "2026-02-02T10:35:30Z"
}
```

**검증 항목**:
- ✅ status = "VIDEO_READY"
- ✅ video_path 파일 존재
- ✅ video_duration ≈ audio_duration
- ✅ file_size > 1MB

**수동 검증**:
```bash
# 영상 재생
open /path/to/videos/pres_abc123_presentation.mp4

# FFprobe로 메타데이터 확인
ffprobe -v quiet -print_format json -show_format -show_streams \
  /path/to/videos/pres_abc123_presentation.mp4 | jq '.'
```

---

## Frontend Integration Test

### 1. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

### 2. 브라우저 테스트

```
http://localhost:3020/presentation
```

**테스트 시나리오**:

#### Scenario 1: PDF 업로드
1. "PDF 파일 업로드" 버튼 클릭
2. `test_data/sample_presentation.pdf` 선택
3. 업로드 진행률 표시 확인
4. 슬라이드 썸네일 리스트 표시 확인

#### Scenario 2: 스크립트 생성
1. "스크립트 생성" 버튼 클릭
2. 톤 선택 (Professional/Friendly/Educational)
3. 목표 시간 입력 (예: 15초)
4. 생성된 나레이션 확인
5. 슬라이드 선택 후 나레이션 편집 테스트

#### Scenario 3: 오디오 생성
1. "오디오 생성" 버튼 클릭
2. 음성 선택 (ElevenLabs voice ID)
3. 생성 대기 (로딩 인디케이터)
4. 오디오 플레이어 표시 확인
5. 재생 테스트

#### Scenario 4: 타이밍 분석
1. "타이밍 분석" 버튼 클릭
2. Whisper 분석 대기
3. 슬라이드별 타이밍 정보 표시 확인
4. 타임라인 바에서 슬라이드 구간 표시 확인

#### Scenario 5: 영상 생성
1. "영상 생성" 버튼 클릭
2. 화면 전환 효과 선택 (Fade/Slide/Zoom)
3. BGM 설정 (활성화/비활성화, 볼륨)
4. 생성 진행률 폴링 확인 (3초 간격)
5. 완료 후 다운로드 버튼 표시
6. 영상 다운로드 및 재생 테스트

---

## Success Criteria

### Backend Tests

- [x] PDF 업로드 성공 (200 OK)
- [x] 슬라이드 추출 성공 (image_path 존재)
- [x] OCR 텍스트 추출 성공 (extracted_text 비어있지 않음)
- [x] 나레이션 스크립트 생성 성공
- [x] TTS 오디오 생성 성공 (mp3 파일 존재)
- [x] Whisper 타이밍 분석 성공 (confidence 90%+)
- [x] 영상 생성 성공 (mp4 파일 존재)
- [x] 화면 전환 효과 정상 작동 (fade/slide/zoom)

### Frontend Tests

- [x] PDF 업로드 UI 정상 작동
- [x] 슬라이드 썸네일 리스트 표시
- [x] 나레이션 편집기 정상 작동
- [x] 진행 상황 추적 (6단계)
- [x] 에러 처리 (네트워크 에러, API 에러)
- [x] 로딩 상태 표시
- [x] 영상 다운로드 버튼 표시

### Performance Tests

- [x] 10슬라이드 영상 생성 < 10분
- [x] TTS 생성 시간 슬라이드당 < 30초
- [x] Whisper 분석 < 2분
- [x] FFmpeg 렌더링 < 5분

### Quality Tests

- [x] 슬라이드 타이밍 정확도 90%+
- [x] 오디오 품질 (노이즈 없음, 명확한 발음)
- [x] 영상 품질 (1920x1080, 깨짐 없음)
- [x] 화면 전환 부드러움 (0.5초 fade)

---

## Troubleshooting

### Issue 1: Tesseract 언어 데이터 없음

**에러**:
```
Error opening data file /usr/share/tesseract-ocr/4.00/tessdata/kor.traineddata
```

**해결**:
```bash
# macOS
brew install tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr-kor tesseract-ocr-eng

# 확인
tesseract --list-langs | grep kor
```

---

### Issue 2: FFmpeg 없음

**에러**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**해결**:
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# 확인
ffmpeg -version
```

---

### Issue 3: ElevenLabs API 키 없음

**에러**:
```
Unauthorized: Invalid API key
```

**해결**:
```bash
# .env 파일에 추가
ELEVENLABS_API_KEY=your_api_key_here

# Docker 재시작
docker-compose down
docker-compose up -d
```

---

### Issue 4: Whisper API 키 없음

**에러**:
```
OpenAI API Error: Invalid API key
```

**해결**:
```bash
# .env 파일에 추가
OPENAI_API_KEY=your_openai_api_key_here

# Docker 재시작
docker-compose restart
```

---

### Issue 5: 슬라이드 타이밍 정확도 낮음

**증상**: avg_confidence < 0.90

**원인**:
1. TTS 발음과 스크립트 불일치
2. Whisper 인식 오류
3. 스크립트에 메타데이터 포함 (###, ---)

**해결**:
1. `text_normalizer.py` 확인 (메타데이터 제거)
2. TTS 음성 품질 높이기 (stability 0.5 → 0.7)
3. Whisper 모델 변경 (v3 → v3-turbo)

---

### Issue 6: 영상 생성 실패

**에러**:
```
Celery task failed: FFmpeg error
```

**해결**:
```bash
# Celery 로그 확인
docker-compose logs celery

# FFmpeg 수동 테스트
ffmpeg -i slide1.png -i slide2.png \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=9.5[out]" \
  -map "[out]" output.mp4

# 슬라이드 이미지 존재 확인
ls -la /path/to/slides/
```

---

## Performance Metrics

### Expected Timing (10 Slides)

| Step | Expected Time | Notes |
|------|--------------|-------|
| PDF Upload | 5-10s | Depends on file size |
| Slide Extraction | 10-20s | 200 DPI, 10 slides |
| OCR Text Extraction | 15-30s | Tesseract Korean + English |
| Script Generation | 20-40s | Claude 3 Haiku LLM |
| TTS Audio Generation | 2-5min | ElevenLabs API, 10 slides |
| Whisper Analysis | 1-2min | OpenAI Whisper v3 |
| Video Rendering | 2-5min | FFmpeg with transitions |
| **Total** | **5-10min** | Full workflow |

### Resource Usage

- **CPU**: 2-4 cores (FFmpeg 렌더링 시 최대)
- **Memory**: 2-4GB (이미지 버퍼, 오디오 처리)
- **Disk**: 슬라이드당 500KB-1MB (PNG)
- **Network**: TTS + Whisper API 호출 대역폭

---

## Next Steps

### Phase 7 완료 후

1. **Phase 8: Voice Cloning**
   - ElevenLabs Voice Cloning API 통합
   - 사용자 음성 샘플 업로드
   - 커스텀 음성으로 나레이션 생성

2. **Phase 9: Real-time Collaboration**
   - WebSocket 기반 실시간 편집
   - 다중 사용자 협업
   - 변경 사항 실시간 동기화

3. **Phase 10: Auto Distribution**
   - YouTube/Instagram/TikTok 자동 업로드
   - 플랫폼별 최적화 (해상도, 포맷)
   - 스케줄링 및 배포 관리

---

## Conclusion

Phase 7 통합 테스트를 통해 다음을 검증합니다:

✅ PDF → 슬라이드 추출 (OCR)
✅ 슬라이드 → 나레이션 스크립트 생성 (LLM)
✅ 스크립트 → 오디오 생성 (ElevenLabs)
✅ 오디오 → 타이밍 분석 (Whisper)
✅ 슬라이드 + 오디오 + 타이밍 → 영상 생성 (FFmpeg)

**Phase 7 완료 조건**:
- 엔드투엔드 테스트 성공
- 타이밍 정확도 90%+
- 화면 전환 효과 정상 작동

테스트 결과를 `PHASE_7_TEST_REPORT.md`에 기록하세요.
