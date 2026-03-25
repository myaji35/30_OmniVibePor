# Lipsync Service - Quick Start Guide

## 빠른 시작 (5분)

### 1. 환경 변수 설정

`.env` 파일에 HeyGen API 키 추가:

```bash
# HeyGen API 설정
HEYGEN_API_KEY=your_heygen_api_key_here
HEYGEN_API_ENDPOINT=https://api.heygen.com/v1

# 출력 디렉토리
LIPSYNC_OUTPUT_DIR=./outputs/lipsync
```

### 2. 테스트 파일 준비

```bash
# 테스트용 샘플 파일 다운로드 (예시)
mkdir -p test_inputs
cd test_inputs

# 또는 직접 준비
# - video.mp4 (입력 영상)
# - audio.mp3 (입력 오디오)
```

### 3. 립싱크 생성 테스트

```bash
# 자동 모드 (HeyGen 우선)
python test_lipsync.py \
  --video test_inputs/video.mp4 \
  --audio test_inputs/audio.mp3 \
  --method auto
```

### 4. 결과 확인

```bash
# 출력 파일 확인
ls -lh outputs/lipsync/synced.mp4

# 재생
open outputs/lipsync/synced.mp4
```

## 사용 방법

### Python 코드에서 사용

```python
import asyncio
from app.services.lipsync_service import get_lipsync_service

async def main():
    lipsync = get_lipsync_service()

    result = await lipsync.generate_lipsync(
        video_path="./inputs/video.mp4",
        audio_path="./inputs/audio.mp3",
        output_path="./outputs/synced.mp4",
        method="auto"  # "heygen" 또는 "wav2lip"
    )

    print(f"완료! 비용: ${result['cost_usd']:.2f}")
    await lipsync.close()

asyncio.run(main())
```

### Celery Task로 사용

```python
from app.tasks.video_tasks import generate_lipsync_task

# 비동기 작업 큐에 추가
task = generate_lipsync_task.delay(
    video_path="./inputs/video.mp4",
    audio_path="./inputs/audio.mp3",
    output_path="./outputs/synced.mp4",
    method="auto",
    user_id="user123"
)

print(f"Task ID: {task.id}")

# 결과 대기 (블로킹)
result = task.get(timeout=600)
print(result)
```

### FastAPI 엔드포인트 추가 (예시)

`backend/app/api/v1/lipsync.py` 생성:

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

from app.tasks.video_tasks import generate_lipsync_task

router = APIRouter(prefix="/lipsync", tags=["lipsync"])


@router.post("/create")
async def create_lipsync(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    method: str = Form("auto")
):
    """
    립싱크 영상 생성 요청

    - **video**: 입력 영상 파일 (MP4)
    - **audio**: 입력 오디오 파일 (MP3, WAV)
    - **method**: 사용할 방법 (auto, heygen, wav2lip)
    """
    # 고유 ID 생성
    job_id = str(uuid.uuid4())

    # 파일 저장
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)

    video_path = upload_dir / f"{job_id}_video.mp4"
    audio_path = upload_dir / f"{job_id}_audio.mp3"
    output_path = Path("./outputs/lipsync") / f"{job_id}_synced.mp4"

    with open(video_path, "wb") as f:
        f.write(await video.read())

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Celery 작업 큐에 추가
    task = generate_lipsync_task.delay(
        video_path=str(video_path),
        audio_path=str(audio_path),
        output_path=str(output_path),
        method=method
    )

    return {
        "job_id": job_id,
        "task_id": task.id,
        "status": "processing",
        "message": "Lipsync generation started"
    }


@router.get("/status/{task_id}")
async def get_lipsync_status(task_id: str):
    """
    립싱크 작업 상태 조회
    """
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    task = AsyncResult(task_id, app=celery_app)

    if task.ready():
        result = task.result
        return {
            "status": "completed",
            "result": result
        }
    else:
        return {
            "status": "processing",
            "progress": "in_progress"
        }
```

### API 라우터 등록

`backend/app/api/v1/__init__.py`에 추가:

```python
from .lipsync import router as lipsync_router

# main.py에서 등록
app.include_router(lipsync_router, prefix="/api/v1")
```

## 비용 계산

### HeyGen API 비용

| 영상 길이 | 비용 (USD) |
|---------|-----------|
| 10초    | $0.50     |
| 30초    | $1.50     |
| 60초    | $3.00     |
| 120초   | $6.00     |

### Wav2Lip (무료)

- 로컬 GPU 실행: **무료**
- 단점: GPU 필수, 속도 느림

## 문제 해결

### HeyGen API 키 에러

```bash
# 환경 변수 확인
echo $HEYGEN_API_KEY

# .env 파일 확인
cat backend/.env | grep HEYGEN
```

### Wav2Lip 모델 없음

```bash
# Wav2Lip 설치
git clone https://github.com/Rudrabha/Wav2Lip.git
cd Wav2Lip
pip install -r requirements.txt

# 모델 다운로드
wget "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip.pth" -O "checkpoints/wav2lip.pth"

# 환경 변수 설정
export WAV2LIP_MODEL_PATH=$(pwd)/checkpoints/wav2lip.pth
```

### GPU 없음 에러

```bash
# CPU 모드 사용 (느림)
export LIPSYNC_GPU_ENABLED=false

# 또는 HeyGen만 사용
# method="heygen" 으로 강제
```

## 다음 단계

1. **프로덕션 배포**: Celery Worker와 Redis 설정
2. **모니터링**: Logfire 대시보드에서 비용 추적
3. **최적화**: 캐싱 및 배치 처리 설정

자세한 내용은 [LIPSYNC_SERVICE.md](./docs/LIPSYNC_SERVICE.md) 참고
