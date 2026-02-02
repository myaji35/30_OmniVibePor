# SlideTimingAnalyzer 사용 가이드

## 개요

`SlideTimingAnalyzer`는 Whisper STT 결과의 타임스탬프를 분석하여 슬라이드별 타이밍을 자동으로 매칭하는 서비스입니다.

### 주요 기능

- **Whisper 타임스탬프 파싱**: `verbose_json` 형식의 Whisper API 응답 처리
- **스크립트-세그먼트 매칭**: difflib 기반 텍스트 유사도 계산 (임계값 80% 이상)
- **타이밍 자동 계산**: 슬라이드별 시작/종료 시간 자동 추출
- **타이밍 조정**: 겹침 제거, 갭 최소화
- **정확도 검증**: 매칭 신뢰도 및 전체 정확도 계산 (목표 90% 이상)
- **Neo4j 연동**: Slide 노드에 타이밍 정보 자동 업데이트

---

## 설치

이미 프로젝트에 포함되어 있습니다. 의존성:

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.0"
neo4j = "^5.0"
```

---

## 기본 사용법

### 1. 서비스 인스턴스 가져오기

```python
from app.services.slide_timing_analyzer import get_slide_timing_analyzer

analyzer = get_slide_timing_analyzer()
```

### 2. Whisper 타임스탬프 분석

```python
# Whisper API 응답 (verbose_json 형식)
whisper_result = {
    "text": "안녕하세요. 오늘은 OmniVibe Pro를 소개해드리겠습니다...",
    "language": "ko",
    "duration": 15.5,
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "안녕하세요."
        },
        {
            "id": 1,
            "start": 2.5,
            "end": 6.8,
            "text": "오늘은 OmniVibe Pro를 소개해드리겠습니다."
        },
        {
            "id": 2,
            "start": 6.8,
            "end": 12.3,
            "text": "OmniVibe Pro는 AI 기반 영상 자동화 플랫폼입니다."
        }
    ]
}

# 슬라이드 스크립트
slide_scripts = [
    {"slide_number": 1, "script": "안녕하세요. 오늘은 OmniVibe Pro를 소개해드리겠습니다."},
    {"slide_number": 2, "script": "OmniVibe Pro는 AI 기반 영상 자동화 플랫폼입니다."}
]

# 타이밍 분석
timings = await analyzer.analyze_timing(
    whisper_result=whisper_result,
    slide_scripts=slide_scripts,
    audio_path="/path/to/audio.mp3",
    project_id="proj_abc123"  # Neo4j 업데이트 원하면 제공
)

# 결과 출력
for timing in timings:
    print(f"슬라이드 {timing.slide_number}:")
    print(f"  시작: {timing.start_time:.2f}초")
    print(f"  종료: {timing.end_time:.2f}초")
    print(f"  길이: {timing.duration:.2f}초")
    print(f"  신뢰도: {timing.confidence:.2%}")
```

**출력 예시:**
```
슬라이드 1:
  시작: 0.00초
  종료: 6.80초
  길이: 6.80초
  신뢰도: 95.23%

슬라이드 2:
  시작: 6.80초
  종료: 12.30초
  길이: 5.50초
  신뢰도: 98.76%
```

---

## 고급 사용법

### 1. STT Service와 통합

```python
from app.services.stt_service import get_stt_service
from app.services.slide_timing_analyzer import get_slide_timing_analyzer

stt_service = get_stt_service()
analyzer = get_slide_timing_analyzer()

# Step 1: Whisper STT 실행 (타임스탬프 포함)
whisper_result = await stt_service.transcribe_with_timestamps(
    audio_file_path="/path/to/narration.mp3",
    language="ko"
)

# Step 2: 슬라이드 타이밍 분석
slide_scripts = [
    {"slide_number": 1, "script": "첫 번째 슬라이드 내용"},
    {"slide_number": 2, "script": "두 번째 슬라이드 내용"},
    {"slide_number": 3, "script": "세 번째 슬라이드 내용"}
]

timings = await analyzer.analyze_timing(
    whisper_result=whisper_result,
    slide_scripts=slide_scripts,
    audio_path="/path/to/narration.mp3",
    project_id="proj_abc123"
)
```

### 2. 정확도 검증

```python
# 예상 길이 리스트 (옵션)
expected_durations = [5.0, 8.0, 7.5]

# 정확도 검증
accuracy = analyzer.validate_timing_accuracy(
    slide_timings=timings,
    expected_durations=expected_durations
)

print(f"전체 정확도: {accuracy:.2f}%")

if accuracy < 90.0:
    print("⚠️ 정확도가 90% 미만입니다. 스크립트를 재확인하세요.")
else:
    print("✅ 정확도 검증 통과!")
```

### 3. 수동 타이밍 조정

```python
# 타이밍 분석 후 수동 조정 (예: 겹침 발생 시)
adjusted_timings = analyzer.adjust_timing(
    slide_timings=timings,
    total_audio_duration=20.5
)

# 조정 전후 비교
for original, adjusted in zip(timings, adjusted_timings):
    print(f"슬라이드 {original.slide_number}:")
    print(f"  원본: {original.start_time:.2f}s - {original.end_time:.2f}s")
    print(f"  조정: {adjusted.start_time:.2f}s - {adjusted.end_time:.2f}s")
```

---

## Neo4j 스키마 업데이트

### Slide 노드 타이밍 필드

`analyze_timing()` 호출 시 `project_id`를 제공하면 자동으로 Neo4j에 업데이트됩니다.

**업데이트되는 필드:**
- `start_time`: 시작 시간 (초)
- `end_time`: 종료 시간 (초)
- `duration`: 지속 시간 (초)
- `confidence`: 매칭 신뢰도 (0.0-1.0)
- `matched_text`: 매칭된 Whisper 텍스트
- `timing_updated_at`: 업데이트 시각 (Neo4j datetime)

**Cypher 쿼리 예시:**
```cypher
MATCH (proj:Project {project_id: "proj_abc123"})
      -[:HAS_PRESENTATION]->(:Presentation)
      -[:HAS_SLIDE]->(slide:Slide)
RETURN slide.slide_number,
       slide.start_time,
       slide.end_time,
       slide.duration,
       slide.confidence
ORDER BY slide.slide_number
```

---

## 매칭 알고리즘 상세

### 1. 텍스트 정규화

매칭 전에 텍스트를 정규화합니다:

- 소문자 변환
- 문장부호 제거 (일부)
- 연속 공백을 단일 공백으로

**예시:**
```python
# 원본
"안녕하세요! 오늘은... OmniVibe Pro를 소개합니다."

# 정규화 후
"안녕하세요 오늘은 omnivibe pro를 소개합니다"
```

### 2. 슬라이딩 윈도우 매칭

각 슬라이드 스크립트에 대해:

1. Whisper 세그먼트를 1개부터 N개까지 윈도우로 결합
2. 각 윈도우와 스크립트의 유사도 계산 (SequenceMatcher)
3. 가장 유사한 윈도우 선택 (임계값 80% 이상)

**유사도 계산:**
```python
from difflib import SequenceMatcher

matcher = SequenceMatcher(None, normalized_script, normalized_segment)
similarity = matcher.ratio()  # 0.0 ~ 1.0
```

### 3. 타이밍 조정 규칙

- **겹침 발생 시**: 경계를 중간 지점으로 조정
- **갭 0.5초 이하**: 갭을 메우기 (각 슬라이드를 절반씩 확장/축소)
- **마지막 슬라이드**: 전체 오디오 길이까지 확장 (갭 1초 이하인 경우)

---

## 에러 처리

### 매칭 실패 시

스크립트와 매칭되는 세그먼트가 없으면:

```python
SlideTimingModel(
    slide_number=1,
    start_time=0.0,
    end_time=0.0,
    duration=0.0,
    confidence=0.0,
    matched_text=""
)
```

**해결 방법:**
1. 스크립트와 실제 나레이션이 일치하는지 확인
2. Whisper STT 정확도 확인
3. 임계값 조정 (`MIN_SIMILARITY_THRESHOLD` 기본값: 0.80)

### Neo4j 업데이트 실패 시

로그에 경고 메시지만 출력되고, 예외는 발생하지 않습니다.

```
WARNING: Failed to update Neo4j timing for slide 2
```

**해결 방법:**
1. Neo4j 연결 상태 확인
2. `project_id`가 올바른지 확인
3. Presentation → Slide 관계가 존재하는지 확인

---

## 테스트

테스트 파일: `/backend/test_slide_timing_analyzer.py`

```bash
# 로컬 환경 (Poetry)
poetry run python test_slide_timing_analyzer.py

# Docker 환경
docker-compose exec backend python test_slide_timing_analyzer.py
```

**테스트 시나리오:**
1. 기본 텍스트 매칭
2. 복잡한 스크립트 매칭 (문장부호, 공백 차이)
3. 타이밍 조정 (겹침, 갭 처리)
4. 정확도 검증
5. 저신뢰도 시나리오 (매칭 실패)

---

## 성능 최적화

### 1. 윈도우 크기 제한

세그먼트가 매우 많은 경우 (100개 이상), 윈도우 크기를 제한하여 성능 개선:

```python
# slide_timing_analyzer.py 수정
MAX_WINDOW_SIZE = 20  # 최대 20개 세그먼트까지만 윈도우 생성

for window_size in range(1, min(len(segments) + 1, MAX_WINDOW_SIZE)):
    # ...
```

### 2. 캐싱

동일 오디오에 대해 반복 분석 시 결과 캐싱:

```python
import functools

@functools.lru_cache(maxsize=128)
def _cached_similarity(text1: str, text2: str) -> float:
    return self._calculate_similarity(text1, text2)
```

---

## 문제 해결 (Troubleshooting)

### Q1: 신뢰도가 낮게 나옵니다 (< 80%)

**원인:**
- 스크립트와 실제 나레이션 불일치
- Whisper STT 오류
- 문장부호/공백 차이

**해결:**
1. 스크립트를 실제 나레이션과 일치하도록 수정
2. Whisper STT 재실행 (temperature=0.0으로 정확도 향상)
3. 정규화 규칙 확인

### Q2: 슬라이드 타이밍이 겹칩니다

**원인:**
- Whisper 세그먼트 자체가 겹침
- 매칭 알고리즘 오류

**해결:**
- `adjust_timing()` 함수가 자동으로 조정합니다
- 로그에서 조정 내역 확인:
  ```
  DEBUG: Adjusted overlap between slide 1 and 2 at 5.25s
  ```

### Q3: 마지막 슬라이드가 오디오 끝까지 안 갑니다

**원인:**
- 마지막 슬라이드와 오디오 끝의 갭이 1초 초과

**해결:**
- 갭이 1초 이하면 자동 확장됩니다
- 수동으로 조정:
  ```python
  timings[-1].end_time = total_audio_duration
  timings[-1].duration = timings[-1].end_time - timings[-1].start_time
  ```

---

## 관련 파일

- **서비스**: `/backend/app/services/slide_timing_analyzer.py`
- **모델**: `/backend/app/models/neo4j_models.py` (SlideTimingModel 등)
- **테스트**: `/backend/test_slide_timing_analyzer.py`
- **STT 서비스**: `/backend/app/services/stt_service.py`
- **Neo4j 클라이언트**: `/backend/app/services/neo4j_client.py`

---

## 참고 자료

- [Whisper API Documentation](https://platform.openai.com/docs/guides/speech-to-text)
- [difflib - Python 공식 문서](https://docs.python.org/3/library/difflib.html)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
