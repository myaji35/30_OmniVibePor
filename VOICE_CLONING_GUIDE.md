# Voice Cloning 가이드 🎤

**완료일**: 2026-02-01
**상태**: ✅ 완료
**기능**: 녹음된 목소리를 학습하여 커스텀 TTS 생성

---

## 🎯 기능 개요

사용자가 **자신의 목소리를 녹음**하면, ElevenLabs가 학습하여 **커스텀 음성**을 생성합니다.
이후 모든 TTS 생성 시 사용자만의 목소리로 영상을 제작할 수 있습니다.

### ✨ 핵심 기능
- ✅ **오디오 파일 업로드** (MP3, WAV 등)
- ✅ **ElevenLabs Voice Cloning** (1-3분 학습)
- ✅ **Neo4j GraphRAG 저장** (성과 분석 연동)
- ✅ **커스텀 음성으로 TTS 생성**
- ✅ **음성 관리** (조회, 삭제)

---

## 📋 요구사항

| 항목 | 요구사항 |
|------|----------|
| **최소 오디오 길이** | 1분 이상 |
| **권장 오디오 길이** | 3-5분 (고품질) |
| **파일 형식** | MP3, WAV, M4A, FLAC, OGG |
| **샘플레이트** | 22050 Hz 이상 |
| **배경 노이즈** | 최소화 필요 (조용한 환경) |
| **발화 내용** | 다양한 문장 권장 (감정 변화) |
| **파일 크기** | 10MB 이상 권장 |
| **ElevenLabs 플랜** | Pro 플랜 이상 |

---

## 🔄 워크플로우

```
[1. 사용자 녹음]
   - 다양한 문장 읽기 (3-5분)
   - 깨끗한 환경에서 녹음
   ↓
[2. 파일 업로드]
   POST /api/v1/voice/clone
   - user_id, voice_name, audio_file
   ↓
[3. ElevenLabs 학습]
   - 음성 특징 분석
   - 억양, 톤, 발음 패턴 학습
   - 학습 시간: 1-3분
   ↓
[4. voice_id 생성]
   - V_abc123... (고유 ID)
   ↓
[5. Neo4j 저장]
   (User)-[:HAS_VOICE]->(CustomVoice)
   - GraphRAG로 성과 분석 연동
   ↓
[6. TTS 생성]
   POST /api/v1/audio/generate
   - voice_id: "V_abc123..."
   - 사용자만의 목소리로 영상 제작!
```

---

## 🌐 API 엔드포인트

### 1️⃣ 음성 클로닝

**POST** `/api/v1/voice/clone`

```bash
curl -X POST "http://localhost:8000/api/v1/voice/clone" \
  -F "user_id=user123" \
  -F "voice_name=김대표님" \
  -F "description=대표님의 목소리" \
  -F "audio_file=@recording.mp3"
```

**응답**:
```json
{
  "voice_id": "V_abc123...",
  "name": "김대표님",
  "status": "ready",
  "message": "Voice '김대표님' cloned successfully!"
}
```

---

### 2️⃣ 사용자의 모든 커스텀 음성 조회

**GET** `/api/v1/voice/list/{user_id}`

```bash
curl "http://localhost:8000/api/v1/voice/list/user123"
```

**응답**:
```json
{
  "voices": [
    {
      "voice_id": "V_abc123...",
      "name": "김대표님",
      "description": "대표님의 목소리",
      "category": "cloned",
      "created_at": "2026-02-01T12:00:00Z"
    },
    {
      "voice_id": "V_def456...",
      "name": "narrator_voice",
      "description": "내레이터 음성",
      "category": "cloned",
      "created_at": "2026-02-01T10:30:00Z"
    }
  ],
  "total": 2
}
```

---

### 3️⃣ 음성 정보 조회

**GET** `/api/v1/voice/info/{voice_id}`

```bash
curl "http://localhost:8000/api/v1/voice/info/V_abc123..."
```

**응답**:
```json
{
  "voice_id": "V_abc123...",
  "name": "김대표님",
  "description": "대표님의 목소리",
  "category": "cloned",
  "created_at": "2026-02-01T12:00:00Z"
}
```

---

### 4️⃣ 커스텀 음성으로 TTS 생성

**POST** `/api/v1/audio/generate`

```bash
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 이것은 제 목소리로 생성된 오디오입니다.",
    "voice_id": "V_abc123...",
    "language": "ko",
    "user_id": "user123"
  }'
```

**응답**:
```json
{
  "status": "processing",
  "task_id": "xyz-789-...",
  "message": "Zero-Fault Audio 생성 시작..."
}
```

**상태 확인**:
```bash
curl "http://localhost:8000/api/v1/audio/status/xyz-789-..."
```

**다운로드**:
```bash
curl "http://localhost:8000/api/v1/audio/download/xyz-789-..." \
  -o my_voice_audio.mp3
```

---

### 5️⃣ 음성 삭제

**DELETE** `/api/v1/voice/{voice_id}`

```bash
curl -X DELETE "http://localhost:8000/api/v1/voice/V_abc123..."
```

**응답**:
```json
{
  "success": true,
  "message": "Voice V_abc123... deleted successfully"
}
```

---

### 6️⃣ 오디오 파일 검증 (업로드 전)

**POST** `/api/v1/voice/validate`

```bash
curl -X POST "http://localhost:8000/api/v1/voice/validate" \
  -F "audio_file=@recording.mp3"
```

**응답**:
```json
{
  "valid": true,
  "duration_seconds": 185.3,
  "file_size_mb": 3.2,
  "format": "mp3",
  "warnings": []
}
```

**경고 예시**:
```json
{
  "valid": true,
  "duration_seconds": 45.0,
  "file_size_mb": 0.8,
  "format": "mp3",
  "warnings": [
    "Audio file is small. Recommend 3-5 minutes for best quality.",
    "Audio duration is less than 1 minute. Recommend 3+ minutes."
  ]
}
```

---

## 📊 Neo4j GraphRAG 활용

### 그래프 모델

```
(User {id: "user123"})
    ↓
  [:HAS_VOICE]
    ↓
(CustomVoice {
    voice_id: "V_abc123...",
    name: "김대표님",
    created_at: "2026-02-01T12:00:00Z"
})
```

### 성과 분석 연동 (향후)

```
(CustomVoice)
    ↑
  [:USES_VOICE]
    ↑
(Content {title: "AI 트렌드 2026"})
    ↓
  [:ACHIEVED]
    ↓
(Metrics {
    views: 15000,
    performance_score: 85
})
```

**분석 쿼리 예시**:
```cypher
// 특정 음성으로 만든 컨텐츠의 평균 성과
MATCH (v:CustomVoice {name: "김대표님"})
      <-[:USES_VOICE]-(c:Content)-[:ACHIEVED]->(m:Metrics)
RETURN AVG(m.performance_score) as avg_score,
       AVG(m.views) as avg_views

// 결과: 김대표님 목소리로 만든 영상이 평균 85점!
```

---

## 🎬 실전 사용 예시

### 시나리오 1: 개인 브랜딩 채널

```bash
# 1. 대표님 목소리 녹음 (5분)
ffmpeg -i raw_recording.wav -ar 22050 recording.mp3

# 2. 음성 클로닝
curl -X POST "http://localhost:8000/api/v1/voice/clone" \
  -F "user_id=user123" \
  -F "voice_name=김대표님" \
  -F "audio_file=@recording.mp3"

# 응답: voice_id: "V_abc123..."

# 3. 스크립트로 영상 제작
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 오늘은 AI 트렌드에 대해 알아보겠습니다...",
    "voice_id": "V_abc123...",
    "language": "ko"
  }'

# 4. 30개 영상 배치 제작
curl -X POST "http://localhost:8000/api/v1/audio/batch-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["스크립트1...", "스크립트2...", "..."],
    "voice_id": "V_abc123...",
    "language": "ko"
  }'
```

---

### 시나리오 2: 다중 음성 관리

```bash
# 1. 여러 음성 클로닝
# - 김대표님 (공식 채널용)
# - narrator_voice (내레이션용)
# - casual_voice (브이로그용)

# 2. 상황별 음성 선택
# 공식 발표 영상
POST /api/v1/audio/generate
{
  "voice_id": "V_formal_voice...",  # 김대표님
  "text": "공식 발표 내용..."
}

# 내레이션 영상
POST /api/v1/audio/generate
{
  "voice_id": "V_narrator...",  # narrator_voice
  "text": "스토리텔링 내용..."
}

# 브이로그
POST /api/v1/audio/generate
{
  "voice_id": "V_casual...",  # casual_voice
  "text": "일상 이야기..."
}
```

---

## 🧪 테스트

### 1. 로컬 테스트

```bash
# 1. 서비스 시작
cd backend
docker compose up -d

# 2. 테스트 녹음 파일 준비
# (MacOS: QuickTime으로 녹음)
# recording.mp3 파일 생성

# 3. 음성 클로닝
curl -X POST "http://localhost:8000/api/v1/voice/clone" \
  -F "user_id=test_user" \
  -F "voice_name=테스트_음성" \
  -F "audio_file=@recording.mp3"

# 4. 음성 목록 확인
curl "http://localhost:8000/api/v1/voice/list/test_user"

# 5. TTS 생성
curl -X POST "http://localhost:8000/api/v1/audio/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "테스트 음성입니다.",
    "voice_id": "V_...",
    "language": "ko"
  }'
```

---

### 2. API 문서 확인

```bash
# Swagger UI
http://localhost:8000/docs

# Voice Cloning 섹션에서 모든 엔드포인트 확인 가능
```

---

## 💡 녹음 팁

### 고품질 음성 클로닝을 위한 가이드

1. **조용한 환경**
   - 배경 노이즈 최소화
   - 에어컨, 선풍기 끄기
   - 문 닫기

2. **다양한 문장 읽기**
   - 짧은 문장 + 긴 문장
   - 질문 + 평서문 + 감탄문
   - 감정 변화 (기쁨, 진지함, 설명)

3. **일관된 톤**
   - 평소 말하는 속도로
   - 과도한 연기 금지
   - 자연스럽게

4. **권장 분량**
   - 최소: 1분 (100-150 단어)
   - 권장: 3-5분 (400-600 단어)
   - 최대: 10분

5. **샘플 스크립트**
   ```
   안녕하세요, 저는 OmniVibe Pro를 사용하는 콘텐츠 크리에이터입니다.
   오늘은 제 목소리를 클로닝하여 다양한 영상을 제작해보겠습니다.

   AI 기술의 발전으로 이제는 누구나 쉽게 고품질 영상을 만들 수 있습니다.
   여러분도 함께 시작해보시겠어요?

   (이런 식으로 3-5분 분량)
   ```

---

## 🚨 트러블슈팅

### 문제 1: "Voice cloning failed"

**원인**: 오디오 파일 품질 문제

**해결**:
```bash
# 1. 파일 검증
curl -X POST "http://localhost:8000/api/v1/voice/validate" \
  -F "audio_file=@recording.mp3"

# 2. ffmpeg로 재인코딩
ffmpeg -i recording.mp3 -ar 22050 -ac 1 -b:a 128k recording_fixed.mp3

# 3. 재시도
```

---

### 문제 2: "Audio file is small"

**원인**: 녹음 시간이 너무 짧음

**해결**:
- 최소 1분 이상 녹음
- 권장: 3-5분

---

### 문제 3: "Invalid format"

**원인**: 지원하지 않는 파일 형식

**해결**:
```bash
# MP3로 변환
ffmpeg -i recording.wav -codec:a libmp3lame -b:a 128k recording.mp3
```

---

## 📈 성과 분석 (향후)

### 음성별 성과 비교

```python
# Neo4j 쿼리로 음성별 성과 분석
query = """
MATCH (v:CustomVoice)<-[:USES_VOICE]-(c:Content)-[:ACHIEVED]->(m:Metrics)
RETURN v.name as voice_name,
       COUNT(c) as total_contents,
       AVG(m.views) as avg_views,
       AVG(m.performance_score) as avg_score
ORDER BY avg_score DESC
"""

# 결과:
# voice_name       | total_contents | avg_views | avg_score
# "김대표님"       | 25             | 15000     | 85.3
# "narrator_voice" | 18             | 12000     | 78.1
# "casual_voice"   | 10             | 8000      | 65.5

# → "김대표님" 음성이 가장 높은 성과!
```

---

## 🎉 완료 요약

### 구현된 기능 (6개)
1. ✅ **VoiceCloningService** (300+ 줄)
2. ✅ **Voice API 엔드포인트** (5개)
3. ✅ **Neo4j CustomVoice 노드** (GraphRAG)
4. ✅ **오디오 파일 검증**
5. ✅ **커스텀 음성 TTS 생성**
6. ✅ **음성 관리** (조회, 삭제)

### 파일 구조
```
backend/
├── app/
│   ├── services/
│   │   └── voice_cloning_service.py    ✅ NEW (300+ 줄)
│   ├── api/v1/
│   │   └── voice.py                    ✅ NEW (350+ 줄)
│   └── services/
│       └── neo4j_client.py             ✅ UPDATED (CustomVoice 메서드)
VOICE_CLONING_GUIDE.md                  ✅ NEW (이 파일)
```

---

**작성자**: Claude (Sonnet 4.5)
**대표님의 요청으로 Voice Cloning 기능 완성!** 🎤🚀

이제 대표님만의 목소리로 무제한 컨텐츠를 제작하실 수 있습니다!
