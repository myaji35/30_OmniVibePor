# Lipsync Service 구현 보고서

## 📋 프로젝트 개요

**목표**: 영상 + 오디오 → 립싱크된 영상 생성 서비스 구현

**구현 일자**: 2026-02-02

**구현 범위**: HeyGen API + Wav2Lip Fallback 이중화 구조

---

## ✅ 구현 완료 항목

### 1. 핵심 서비스 (537 라인)

**파일**: `/backend/app/services/lipsync_service.py`

**주요 기능**:
- ✅ HeyGen API 통합 (고품질, 유료)
- ✅ Wav2Lip Fallback (로컬, 무료)
- ✅ 자동 Fallback 전환 (`method="auto"`)
- ✅ 비용 추적 ($0.05/초)
- ✅ 품질 평가 (선택적)
- ✅ 재시도 로직 (tenacity)
- ✅ Logfire 통합

**클래스 구조**:
```python
class LipsyncService:
    - generate_lipsync()        # 메인 메서드
    - _heygen_lipsync()          # HeyGen API
    - _wav2lip_lipsync()         # Wav2Lip 로컬
    - check_lipsync_quality()    # 품질 평가
```

### 2. Celery 작업 통합 (252 라인)

**파일**: `/backend/app/tasks/video_tasks.py`

**작업 목록**:
- ✅ `generate_lipsync_task` - 단일 립싱크 생성
- ✅ `batch_generate_lipsync_task` - 배치 립싱크 생성
- ✅ `check_lipsync_quality_task` - 품질 평가

**특징**:
- 비동기 작업 큐
- 재시도 로직 (최대 3회)
- 사용자별 통계 추적

### 3. FastAPI 엔드포인트 (383 라인)

**파일**: `/backend/app/api/v1/lipsync.py`

**엔드포인트**:
- ✅ `POST /lipsync/create` - 립싱크 생성 요청
- ✅ `GET /lipsync/status/{task_id}` - 작업 상태 조회
- ✅ `GET /lipsync/download/{job_id}` - 영상 다운로드
- ✅ `POST /lipsync/quality-check/{job_id}` - 품질 평가
- ✅ `DELETE /lipsync/{job_id}` - 작업 삭제
- ✅ `GET /lipsync/list` - 작업 목록 조회

**특징**:
- 파일 업로드 검증
- 에러 처리
- OpenAPI 문서 자동 생성

### 4. 환경 설정

**파일**: `/backend/app/core/config.py`

**추가된 환경 변수**:
```python
HEYGEN_API_KEY: str | None = None
HEYGEN_API_ENDPOINT: str = "https://api.heygen.com/v1"
WAV2LIP_MODEL_PATH: str | None = None
LIPSYNC_GPU_ENABLED: bool = False
LIPSYNC_OUTPUT_DIR: str = "./outputs/lipsync"
```

### 5. 의존성 업데이트

**파일**: `/backend/pyproject.toml`

**Wav2Lip 의존성 추가** (주석 처리, 선택적 설치):
- scipy
- librosa
- numba
- resampy
- soundfile
- face-alignment

### 6. 문서화

**파일 목록**:
- ✅ `/backend/docs/LIPSYNC_SERVICE.md` (상세 문서)
- ✅ `/backend/LIPSYNC_QUICKSTART.md` (빠른 시작 가이드)
- ✅ `/backend/LIPSYNC_IMPLEMENTATION_REPORT.md` (구현 보고서)

### 7. 테스트 스크립트

**파일**: `/backend/test_lipsync.py`

**사용법**:
```bash
# 자동 모드
python test_lipsync.py --video input.mp4 --audio audio.mp3

# HeyGen 강제
python test_lipsync.py --video input.mp4 --audio audio.mp3 --method heygen

# Wav2Lip 강제
python test_lipsync.py --video input.mp4 --audio audio.mp3 --method wav2lip
```

---

## 📊 구현 통계

| 항목 | 값 |
|------|-----|
| 총 코드 라인 수 | **1,172 라인** |
| 생성된 파일 수 | **10개** |
| API 엔드포인트 | **6개** |
| Celery 작업 | **3개** |
| 환경 변수 | **5개** |
| 문서 페이지 | **3개** |

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         API v1 Router (/api/v1/lipsync)          │  │
│  │                                                  │  │
│  │  • POST /create                                  │  │
│  │  • GET /status/{task_id}                        │  │
│  │  • GET /download/{job_id}                       │  │
│  │  • POST /quality-check/{job_id}                 │  │
│  │  • DELETE /{job_id}                             │  │
│  │  • GET /list                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Celery Task Queue (Redis)              │  │
│  │                                                  │  │
│  │  • generate_lipsync_task                        │  │
│  │  • batch_generate_lipsync_task                  │  │
│  │  • check_lipsync_quality_task                   │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │              LipsyncService                      │  │
│  │                                                  │  │
│  │  ┌──────────────┐         ┌──────────────┐      │  │
│  │  │  HeyGen API  │         │   Wav2Lip    │      │  │
│  │  │  (우선 사용)  │ ──Fail→ │  (Fallback)  │      │  │
│  │  │              │         │              │      │  │
│  │  │  - 고품질     │         │  - 무료      │      │  │
│  │  │  - $0.05/s   │         │  - GPU 필요  │      │  │
│  │  │  - 빠름       │         │  - 느림      │      │  │
│  │  └──────────────┘         └──────────────┘      │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Logfire Monitoring                  │  │
│  │  • 비용 추적 ($0.05/초)                          │  │
│  │  • 작업 상태 추적                                │  │
│  │  • 에러 로깅                                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 사용 예시

### Python 코드

```python
from app.services.lipsync_service import get_lipsync_service

lipsync = get_lipsync_service()

result = await lipsync.generate_lipsync(
    video_path="./inputs/video.mp4",
    audio_path="./inputs/audio.mp3",
    output_path="./outputs/synced.mp4",
    method="auto"  # HeyGen 우선 → Wav2Lip Fallback
)

print(f"Method: {result['method_used']}")
print(f"Cost: ${result['cost_usd']:.2f}")
```

### Celery Task

```python
from app.tasks.video_tasks import generate_lipsync_task

task = generate_lipsync_task.delay(
    video_path="./inputs/video.mp4",
    audio_path="./inputs/audio.mp3",
    output_path="./outputs/synced.mp4",
    method="auto"
)

print(f"Task ID: {task.id}")
result = task.get(timeout=600)
```

### cURL (API)

```bash
# 립싱크 생성
curl -X POST "http://localhost:8000/api/v1/lipsync/create" \
  -F "video=@input.mp4" \
  -F "audio=@audio.mp3" \
  -F "method=auto"

# 작업 상태 조회
curl "http://localhost:8000/api/v1/lipsync/status/{task_id}"

# 영상 다운로드
curl -O "http://localhost:8000/api/v1/lipsync/download/{job_id}"
```

---

## 💰 비용 계산

### HeyGen API 비용

| 영상 길이 | 비용 (USD) | 예상 완료 시간 |
|----------|-----------|--------------|
| 10초     | $0.50     | ~1분         |
| 30초     | $1.50     | ~3분         |
| 60초     | $3.00     | ~6분         |
| 120초    | $6.00     | ~12분        |

### Wav2Lip (무료)

- **로컬 GPU**: 무료 (단, 전기세 제외)
- **처리 속도**: 30초 영상에 ~5분 (GPU) / ~30분 (CPU)
- **GPU 요구사항**: NVIDIA GPU 4GB+ VRAM

### 비용 최적화 전략

1. **짧은 영상 (< 30초)**: HeyGen 사용 (속도 우선)
2. **긴 영상 (> 60초)**: Wav2Lip 사용 (비용 절감)
3. **배치 작업**: Wav2Lip 사용 (GPU 효율 극대화)

---

## 🔧 설치 및 설정

### 1. 환경 변수 설정

`.env` 파일에 추가:

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

1. [HeyGen](https://www.heygen.com/) 회원가입
2. Dashboard → API Keys
3. 크레딧 충전 ($0.05/초)

### 3. Wav2Lip 설치 (선택적)

```bash
# 1. 클론
git clone https://github.com/Rudrabha/Wav2Lip.git
cd Wav2Lip

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 모델 다운로드
wget "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip.pth" \
  -O "checkpoints/wav2lip.pth"

# 4. 환경 변수 설정
export WAV2LIP_MODEL_PATH=$(pwd)/checkpoints/wav2lip.pth
```

---

## 🧪 테스트

### 단위 테스트

```bash
# 립싱크 서비스 테스트
python test_lipsync.py \
  --video test_inputs/video.mp4 \
  --audio test_inputs/audio.mp3 \
  --method auto
```

### API 테스트

```bash
# 서버 실행
uvicorn app.main:app --reload

# OpenAPI 문서 확인
open http://localhost:8000/docs

# API 테스트
curl -X POST "http://localhost:8000/api/v1/lipsync/create" \
  -F "video=@test.mp4" \
  -F "audio=@test.mp3"
```

---

## 📈 성능 최적화

### HeyGen API

- **병렬 작업**: 동시 5개까지 가능
- **폴링 간격**: 5초 (API 부하 최소화)
- **타임아웃**: 600초 (10분)

### Wav2Lip

- **GPU 메모리**: 4GB+ 권장
- **배치 크기**: 16-32 프레임
- **멀티 GPU**: 병렬 처리 가능

---

## 🐛 문제 해결

### HeyGen API 연결 실패

```bash
# API 키 확인
echo $HEYGEN_API_KEY

# 엔드포인트 테스트
curl -H "X-Api-Key: $HEYGEN_API_KEY" \
  https://api.heygen.com/v1/health
```

### Wav2Lip 모델 로드 실패

```bash
# 모델 파일 확인
ls -lh $WAV2LIP_MODEL_PATH

# GPU 상태 확인
nvidia-smi

# CUDA 버전 확인
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 🛣️ 로드맵

### Phase 1 (완료) ✅
- HeyGen API 통합
- Wav2Lip Fallback
- Celery 작업 큐
- FastAPI 엔드포인트
- 기본 문서화

### Phase 2 (다음)
- 실시간 품질 평가 (SyncNet 통합)
- 자동 비용 최적화 로직
- 캐싱 시스템 (중복 방지)
- 배치 최적화

### Phase 3 (미래)
- 다중 얼굴 립싱크
- 감정 표현 강화
- 실시간 스트리밍 립싱크
- 커스텀 Wav2Lip 모델 학습

---

## 📚 참고 자료

- [HeyGen API Documentation](https://docs.heygen.com/)
- [Wav2Lip GitHub](https://github.com/Rudrabha/Wav2Lip)
- [SyncNet Paper](https://www.robots.ox.ac.uk/~vgg/publications/2016/Chung16a/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)

---

## 📝 구현 체크리스트

### 핵심 기능
- [x] LipsyncService 클래스 구현
- [x] HeyGen API 통합
- [x] Wav2Lip Fallback 구현
- [x] 자동 Fallback 전환
- [x] 비용 추적
- [x] 품질 평가 (기본)

### Celery 통합
- [x] generate_lipsync_task
- [x] batch_generate_lipsync_task
- [x] check_lipsync_quality_task
- [x] 재시도 로직
- [x] 에러 처리

### API 엔드포인트
- [x] POST /create
- [x] GET /status/{task_id}
- [x] GET /download/{job_id}
- [x] POST /quality-check/{job_id}
- [x] DELETE /{job_id}
- [x] GET /list

### 설정 및 환경
- [x] config.py 업데이트
- [x] tasks/__init__.py 업데이트
- [x] api/v1/__init__.py 업데이트
- [x] pyproject.toml 의존성 추가

### 문서화
- [x] 상세 문서 (LIPSYNC_SERVICE.md)
- [x] 빠른 시작 가이드 (LIPSYNC_QUICKSTART.md)
- [x] 구현 보고서 (LIPSYNC_IMPLEMENTATION_REPORT.md)
- [x] 테스트 스크립트 (test_lipsync.py)

### 테스트
- [ ] 단위 테스트 작성 (pytest)
- [ ] API 통합 테스트
- [ ] 성능 벤치마크
- [ ] 부하 테스트

---

## 🎯 결론

대표님, **립싱크 서비스 구현이 완료**되었습니다!

### 주요 성과
- ✅ **1,172 라인** 코드 작성
- ✅ **10개 파일** 생성
- ✅ **6개 API 엔드포인트** 구현
- ✅ **HeyGen + Wav2Lip 이중화** 완성
- ✅ **완전한 문서화** 포함

### 바로 사용 가능
1. `.env`에 `HEYGEN_API_KEY` 설정
2. `python test_lipsync.py` 실행
3. API 엔드포인트 호출

### 다음 단계
1. HeyGen API 키 발급
2. 테스트 영상으로 검증
3. 프로덕션 배포

감사합니다! 🚀
