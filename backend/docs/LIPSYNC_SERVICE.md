# Lipsync Service Documentation

## 개요

`LipsyncService`는 오디오와 영상을 립싱크하는 서비스입니다. HeyGen API를 우선 사용하고, 실패 시 Wav2Lip으로 자동 전환하는 이중화 구조를 제공합니다.

## 아키텍처

```
┌─────────────────────────────────────┐
│       LipsyncService                │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ HeyGen API   │  │  Wav2Lip    │ │
│  │ (우선 사용)   │  │ (Fallback)  │ │
│  │              │  │             │ │
│  │ - 고품질      │  │ - 무료      │ │
│  │ - 유료        │  │ - GPU 필요  │ │
│  │ - 빠름        │  │ - 느림      │ │
│  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────┘
         │
         ▼
  Celery Task Queue
         │
         ▼
   video_tasks.py
```

## 주요 기능

### 1. 립싱크 생성 (`generate_lipsync`)

영상 + 오디오 → 립싱크된 영상

**파라미터:**
- `video_path`: 입력 영상 경로
- `audio_path`: 입력 오디오 경로
- `output_path`: 출력 영상 경로
- `method`: 사용할 방법 (`"auto"`, `"heygen"`, `"wav2lip"`)

**반환값:**
```python
{
    "status": "success",
    "output_path": "/path/to/output.mp4",
    "method_used": "heygen",
    "duration": 30.5,
    "cost_usd": 1.525
}
```

### 2. 배치 립싱크 (`batch_generate_lipsync_task`)

여러 영상을 한 번에 립싱크

**파라미터:**
- `video_audio_pairs`: `[(video1, audio1), (video2, audio2), ...]`
- `output_paths`: `[output1, output2, ...]`
- `method`: 사용할 방법

**반환값:**
```python
{
    "status": "completed",
    "results": [...],
    "summary": {
        "total": 5,
        "success": 4,
        "failed": 1,
        "total_duration": 150.5,
        "total_cost_usd": 7.525
    }
}
```

### 3. 품질 평가 (`check_lipsync_quality`)

립싱크 품질 점수 계산

**반환값:**
```python
{
    "sync_score": 0.85,
    "audio_quality": 0.90,
    "video_quality": 0.88
}
```

## 설치 및 설정

### 1. 환경 변수 설정

`.env` 파일에 다음 추가:

```bash
# HeyGen API (필수)
HEYGEN_API_KEY=your_heygen_api_key
HEYGEN_API_ENDPOINT=https://api.heygen.com/v1

# Wav2Lip (선택적)
WAV2LIP_MODEL_PATH=/path/to/wav2lip_checkpoint.pth
LIPSYNC_GPU_ENABLED=true
LIPSYNC_OUTPUT_DIR=./outputs/lipsync
```

### 2. HeyGen API 키 발급

1. [HeyGen 웹사이트](https://www.heygen.com/) 회원가입
2. API 키 발급 (Dashboard → API Keys)
3. 크레딧 충전 ($0.05/초)

### 3. Wav2Lip 설치 (선택적)

Wav2Lip은 로컬 GPU에서 실행되는 오픈소스 모델입니다.

```bash
# 1. Wav2Lip 클론
git clone https://github.com/Rudrabha/Wav2Lip.git

# 2. 의존성 설치
cd Wav2Lip
pip install -r requirements.txt

# 3. 사전학습 모델 다운로드
wget "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip.pth" -O "checkpoints/wav2lip.pth"

# 4. 환경 변수 설정
export WAV2LIP_MODEL_PATH=$(pwd)/checkpoints/wav2lip.pth
```

**주의:**
- Wav2Lip는 GPU 필수 (CUDA 11.0+)
- CPU 실행 시 매우 느림 (30초 영상에 10분 이상)
- VRAM 4GB 이상 권장

## 사용 예시

### Python 코드

```python
from app.services.lipsync_service import get_lipsync_service

# 싱글톤 인스턴스
lipsync = get_lipsync_service()

# 립싱크 생성
result = await lipsync.generate_lipsync(
    video_path="./inputs/video.mp4",
    audio_path="./inputs/audio.mp3",
    output_path="./outputs/synced.mp4",
    method="auto"  # HeyGen 우선 → Wav2Lip Fallback
)

print(f"Method used: {result['method_used']}")
print(f"Cost: ${result['cost_usd']:.2f}")
```

### Celery Task

```python
from app.tasks.video_tasks import generate_lipsync_task

# 비동기 작업 실행
task = generate_lipsync_task.delay(
    video_path="./inputs/video.mp4",
    audio_path="./inputs/audio.mp3",
    output_path="./outputs/synced.mp4",
    method="auto",
    user_id="user123"
)

# 작업 ID
print(f"Task ID: {task.id}")

# 결과 대기
result = task.get(timeout=600)
print(result)
```

### FastAPI 엔드포인트 (예시)

```python
from fastapi import APIRouter, UploadFile
from app.tasks.video_tasks import generate_lipsync_task

router = APIRouter()

@router.post("/lipsync")
async def create_lipsync(
    video: UploadFile,
    audio: UploadFile,
    method: str = "auto"
):
    # 파일 저장
    video_path = f"./uploads/{video.filename}"
    audio_path = f"./uploads/{audio.filename}"
    output_path = f"./outputs/lipsync_{video.filename}"

    # Celery 작업 실행
    task = generate_lipsync_task.delay(
        video_path, audio_path, output_path, method
    )

    return {
        "task_id": task.id,
        "status": "processing"
    }
```

## 비용 계산

### HeyGen API 비용

- **기본 요금**: $0.05/초
- **예시**:
  - 10초 영상: $0.50
  - 30초 영상: $1.50
  - 60초 영상: $3.00

### Wav2Lip 비용

- **무료** (로컬 실행)
- **GPU 비용** (클라우드 GPU 사용 시):
  - AWS p3.2xlarge: $3.06/시간
  - GCP NVIDIA T4: $0.35/시간

### 비용 최적화 전략

1. **짧은 영상 → HeyGen** (속도 우선)
2. **긴 영상 → Wav2Lip** (비용 절감)
3. **배치 작업 → Wav2Lip** (GPU 효율 극대화)

```python
# 자동 최적화 로직 예시
if duration < 30:
    method = "heygen"  # 빠른 처리
else:
    method = "wav2lip"  # 비용 절감
```

## 에러 처리

### 1. HeyGen API 에러

**원인:**
- API 키 만료
- 크레딧 부족
- 네트워크 타임아웃

**해결:**
- 자동 Wav2Lip Fallback
- 재시도 (최대 3회)

### 2. Wav2Lip 에러

**원인:**
- 모델 파일 없음
- GPU 메모리 부족
- CUDA 드라이버 문제

**해결:**
- 모델 파일 다운로드
- 배치 크기 감소
- CPU 모드 사용 (느림)

### 3. 일반 에러

```python
try:
    result = await lipsync.generate_lipsync(...)
except FileNotFoundError as e:
    # 입력 파일 없음
    print(f"File not found: {e}")
except TimeoutError as e:
    # HeyGen 작업 타임아웃
    print(f"Timeout: {e}")
except RuntimeError as e:
    # Wav2Lip 실행 실패
    print(f"Runtime error: {e}")
```

## 성능 최적화

### 1. HeyGen 최적화

- **병렬 작업**: 동시 5개 작업까지 가능
- **폴링 간격**: 5초 (API 부하 최소화)
- **타임아웃**: 600초 (긴 영상 대비)

### 2. Wav2Lip 최적화

- **GPU 메모리**: 4GB 이상 권장
- **배치 크기**: 작업당 16-32 프레임
- **멀티 프로세싱**: 여러 GPU 사용 시

```python
# Wav2Lip 병렬 실행 (멀티 GPU)
tasks = [
    generate_lipsync_task.delay(v, a, o, method="wav2lip")
    for v, a, o in video_audio_output_triplets
]
```

## 품질 관리

### 1. 자동 품질 평가

```python
quality = await lipsync.check_lipsync_quality(output_path)

if quality["sync_score"] < 0.8:
    # 재생성
    result = await lipsync.generate_lipsync(..., method="heygen")
```

### 2. 수동 품질 기준

- **Sync Score**: 0.85+ (매우 좋음), 0.70-0.85 (양호), 0.70 미만 (재생성)
- **Audio Quality**: 0.90+ (최상), 0.80-0.90 (양호)
- **Video Quality**: 0.85+ (최상), 0.75-0.85 (양호)

## 모니터링

### Logfire 추적

```python
# 자동으로 Logfire에 추적됨
# - 작업 ID
# - 방법 (HeyGen/Wav2Lip)
# - 소요 시간
# - 비용
# - 에러 (발생 시)
```

### Celery Flower

```bash
# Flower 실행
celery -A app.tasks.celery_app flower

# 웹 UI: http://localhost:5555
```

## 문제 해결

### HeyGen API 연결 실패

```bash
# 1. API 키 확인
echo $HEYGEN_API_KEY

# 2. 엔드포인트 테스트
curl -H "X-Api-Key: $HEYGEN_API_KEY" https://api.heygen.com/v1/health
```

### Wav2Lip 모델 로드 실패

```bash
# 1. 모델 파일 존재 확인
ls -lh $WAV2LIP_MODEL_PATH

# 2. GPU 상태 확인
nvidia-smi

# 3. CUDA 버전 확인
python -c "import torch; print(torch.cuda.is_available())"
```

## 로드맵

### Phase 1 (현재)
- HeyGen API 통합
- Wav2Lip Fallback
- Celery 작업 큐

### Phase 2 (다음)
- 실시간 품질 평가 (SyncNet)
- 자동 비용 최적화
- 캐싱 시스템 (중복 방지)

### Phase 3 (미래)
- 다중 얼굴 립싱크
- 감정 표현 강화
- 실시간 스트리밍 립싱크

## 참고 자료

- [HeyGen API Docs](https://docs.heygen.com/)
- [Wav2Lip GitHub](https://github.com/Rudrabha/Wav2Lip)
- [SyncNet Paper](https://www.robots.ox.ac.uk/~vgg/publications/2016/Chung16a/)
