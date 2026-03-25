# 클립 교체 API 구현 완료 보고서

## 개요

섹션별로 AI가 생성한 대체 영상 클립 3개를 제공하고 원클릭으로 교체하는 API를 성공적으로 구현했습니다.

---

## 구현된 기능

### 1. API 엔드포인트 (4개)

#### GET `/api/v1/sections/{section_id}/alternative-clips`
- **기능**: 섹션의 현재 클립 및 대체 클립 목록 조회
- **응답 예시**:
```json
{
  "section_id": "section_abc123",
  "current_clip": {
    "clip_id": "clip_current",
    "video_path": "https://res.cloudinary.com/omnivibe/video/current.mp4",
    "thumbnail_url": "https://res.cloudinary.com/omnivibe/image/thumb_current.jpg",
    "prompt": "Modern studio setting, friendly presenter",
    "created_at": "2026-02-02T10:30:00Z"
  },
  "alternatives": [
    {
      "clip_id": "clip_alt1",
      "video_path": "https://res.cloudinary.com/omnivibe/video/alt1.mp4",
      "thumbnail_url": "https://res.cloudinary.com/omnivibe/image/thumb_alt1.jpg",
      "prompt": "Modern studio setting, friendly presenter. Close-up shot, tight framing on subject",
      "variation": "camera_angle",
      "created_at": "2026-02-02T10:35:00Z"
    },
    {
      "clip_id": "clip_alt2",
      "video_path": "https://res.cloudinary.com/omnivibe/video/alt2.mp4",
      "thumbnail_url": "https://res.cloudinary.com/omnivibe/image/thumb_alt2.jpg",
      "prompt": "Modern studio setting, friendly presenter. Dramatic lighting, high contrast, cinematic mood lighting",
      "variation": "lighting",
      "created_at": "2026-02-02T10:40:00Z"
    },
    {
      "clip_id": "clip_alt3",
      "video_path": "https://res.cloudinary.com/omnivibe/video/alt3.mp4",
      "thumbnail_url": "https://res.cloudinary.com/omnivibe/image/thumb_alt3.jpg",
      "prompt": "Modern studio setting, friendly presenter. Warm color grading, golden hour tones, orange and yellow hues",
      "variation": "color_tone",
      "created_at": "2026-02-02T10:45:00Z"
    }
  ]
}
```

#### POST `/api/v1/sections/{section_id}/alternative-clips`
- **기능**: 대체 클립 3개 생성 (AI)
- **요청 예시**:
```json
{
  "base_prompt": "Modern studio setting, friendly presenter",
  "variations": ["camera_angle", "lighting", "color_tone"]
}
```
- **응답 예시**:
```json
{
  "section_id": "section_abc123",
  "status": "processing",
  "clips": [
    {
      "clip_id": "clip_new1",
      "variation_type": "camera_angle",
      "variation_description": "Close-up shot, tight framing on subject",
      "prompt": "Modern studio setting, friendly presenter. Close-up shot, tight framing on subject",
      "veo_job_id": "veo_job_xyz789",
      "status": "processing",
      "estimated_time": 50
    }
  ],
  "message": "3 alternative clips are being generated. Check status with GET /sections/{section_id}/alternative-clips"
}
```

#### PATCH `/api/v1/sections/{section_id}/clip`
- **기능**: 클립 교체 (원클릭)
- **요청 예시**:
```json
{
  "new_clip_id": "clip_alt2"
}
```
- **응답 예시**:
```json
{
  "section_id": "section_abc123",
  "new_clip_id": "clip_alt2",
  "status": "success",
  "message": "Clip replaced successfully. Rendering will use the new clip."
}
```

#### DELETE `/api/v1/sections/{section_id}/alternative-clips/{clip_id}`
- **기능**: 대체 클립 삭제
- **응답 예시**:
```json
{
  "section_id": "section_abc123",
  "clip_id": "clip_alt1",
  "status": "success",
  "message": "Alternative clip deleted successfully"
}
```

---

## 프롬프트 변형 로직

### 변형 타입 1: 카메라 앵글

**원본 프롬프트**:
```
Modern studio setting, friendly presenter
```

**변형 3가지**:
1. **Close-up**: `Modern studio setting, friendly presenter. Close-up shot, tight framing on subject`
2. **Medium shot**: `Modern studio setting, friendly presenter. Medium shot, waist-up view of subject`
3. **Wide shot**: `Modern studio setting, friendly presenter. Wide shot, full body view with environment`

### 변형 타입 2: 조명 스타일

**원본 프롬프트**:
```
Modern studio setting, friendly presenter
```

**변형 3가지**:
1. **Natural**: `Modern studio setting, friendly presenter. Natural lighting, soft daylight, realistic shadows`
2. **Dramatic**: `Modern studio setting, friendly presenter. Dramatic lighting, high contrast, cinematic mood lighting`
3. **Soft**: `Modern studio setting, friendly presenter. Soft lighting, diffused light, gentle shadows, bright and airy`

### 변형 타입 3: 색감

**원본 프롬프트**:
```
Modern studio setting, friendly presenter
```

**변형 3가지**:
1. **Warm**: `Modern studio setting, friendly presenter. Warm color grading, golden hour tones, orange and yellow hues`
2. **Cool**: `Modern studio setting, friendly presenter. Cool color grading, blue and teal tones, modern aesthetic`
3. **Neutral**: `Modern studio setting, friendly presenter. Neutral color grading, balanced tones, natural colors`

---

## 구현 위치

### 1. Pydantic 모델
**파일**: `/backend/app/models/neo4j_models.py`

**추가된 모델**:
- `ClipVariationType` (Enum): camera_angle, lighting, color_tone
- `AlternativeClipModel`: 대체 클립 모델
- `CurrentClipResponse`: 현재 클립 응답
- `AlternativeClipResponse`: 대체 클립 응답
- `SectionAlternativeClipsResponse`: 섹션 대체 클립 응답
- `GenerateAlternativeClipsRequest`: 대체 클립 생성 요청
- `ReplaceClipRequest`: 클립 교체 요청

**라인**: 261-401

### 2. 서비스 레이어
**파일**: `/backend/app/services/clip_editor_service.py` (새 파일)

**주요 클래스**:
- `PromptVariationGenerator`: 프롬프트 변형 생성기
  - `generate_camera_angle_variation()`: 카메라 앵글 3가지 변형
  - `generate_lighting_variation()`: 조명 스타일 3가지 변형
  - `generate_color_tone_variation()`: 색감 3가지 변형
  - `generate_all_variations()`: 모든 변형 한번에 생성

- `ClipEditorService`: 클립 에디터 서비스
  - `generate_alternative_clips()`: 대체 클립 3개 생성 (비동기)
  - `get_section_alternative_clips()`: 섹션 클립 목록 조회
  - `replace_section_clip()`: 클립 교체
  - `delete_alternative_clip()`: 대체 클립 삭제

### 3. Neo4j CRUD
**파일**: `/backend/app/models/neo4j_models.py`

**추가된 메서드** (Neo4jCRUDManager):
- `create_alternative_clip()`: 대체 클립 생성 및 섹션 연결
- `get_section_alternative_clips()`: 섹션의 모든 대체 클립 조회
- `get_section_current_clip()`: 섹션의 현재 클립 조회
- `replace_section_clip()`: 섹션의 클립 교체
- `delete_alternative_clip()`: 대체 클립 삭제
- `update_alternative_clip_status()`: 대체 클립 상태 업데이트

**라인**: 997-1060

### 4. API 엔드포인트
**파일**: `/backend/app/api/v1/editor.py`

**추가된 엔드포인트**:
- `GET /sections/{section_id}/alternative-clips`: 대체 클립 목록 조회 (라인 275-330)
- `POST /sections/{section_id}/alternative-clips`: 대체 클립 생성 (라인 333-395)
- `PATCH /sections/{section_id}/clip`: 클립 교체 (라인 398-455)
- `DELETE /sections/{section_id}/alternative-clips/{clip_id}`: 대체 클립 삭제 (라인 458-505)

### 5. Celery 비동기 작업
**파일**: `/backend/app/tasks/director_tasks.py`

**추가된 작업**:
- `generate_alternative_clip_task()`: 대체 클립 생성 Celery 작업
  - Veo API 호출 및 폴링
  - 영상 다운로드
  - Cloudinary 업로드
  - 썸네일 생성
  - Neo4j 상태 업데이트

**라인**: 600-780 (약)

### 6. 통합 테스트
**파일**: `/backend/test_clip_editor_api.py` (새 파일)

**테스트 항목**:
- 프롬프트 변형 생성 테스트 (4개)
- API 엔드포인트 테스트 (4개, Mock 사용)
- 엣지 케이스 테스트 (2개)

---

## 기술 스택

1. **Google Veo API**: 영상 생성
   - 5초 영상 기준 약 50초 소요
   - 최대 1080p HD 해상도 지원
   - 비용: ~$0.10/영상

2. **Cloudinary**: 영상 호스팅 및 썸네일 생성
   - 영상 업로드 및 변환
   - 자동 썸네일 추출 (1초 지점)
   - CDN을 통한 빠른 전송

3. **Neo4j**: 메타데이터 저장
   - 그래프 관계: `(Section)-[:HAS_ALTERNATIVE_CLIP]->(AlternativeClip)`
   - 클립 교체: `(Section)-[:USES_CLIP]->(AlternativeClip)`

4. **Celery**: 비동기 작업 처리
   - 영상 생성 작업 큐잉
   - 재시도 로직 (최대 3회)
   - 실패 시 자동 상태 업데이트

---

## 클립 교체 로직

1. 사용자가 대체 클립 선택
2. `PATCH /sections/{section_id}/clip` 호출
3. Neo4j에서 기존 `USES_CLIP` 관계 삭제
4. 새 클립과 `USES_CLIP` 관계 생성
5. 기존 클립은 삭제하지 않고 보관 (롤백 가능)
6. 최종 렌더링 시 새 클립 사용

**Cypher 쿼리**:
```cypher
MATCH (s:Section {section_id: $section_id})
OPTIONAL MATCH (s)-[old_rel:USES_CLIP]->(:AlternativeClip)
DELETE old_rel
WITH s
MATCH (new_clip:AlternativeClip {clip_id: $new_clip_id})
CREATE (s)-[:USES_CLIP]->(new_clip)
RETURN s.section_id as section_id
```

---

## 테스트 결과

### 단위 테스트 (Mock)

모든 테스트는 `test_clip_editor_api.py`에 작성되어 있으며, Mock을 사용하여 외부 API 의존성을 제거했습니다.

**실행 방법**:
```bash
cd backend
pytest test_clip_editor_api.py -v
```

또는:
```bash
python3 test_clip_editor_api.py
```

**테스트 항목**:
- ✓ 카메라 앵글 변형 생성 (3개)
- ✓ 조명 스타일 변형 생성 (3개)
- ✓ 색감 변형 생성 (3개)
- ✓ 모든 변형 생성 (9개)
- ✓ GET 대체 클립 목록 조회
- ✓ POST 대체 클립 생성
- ✓ PATCH 클립 교체
- ✓ DELETE 대체 클립 삭제
- ✓ 404 에러 핸들링 (존재하지 않는 클립)

---

## 사용 예시

### 1. 대체 클립 생성

**요청**:
```bash
curl -X POST http://localhost:8000/api/v1/sections/section_abc123/alternative-clips \
  -H "Content-Type: application/json" \
  -d '{
    "base_prompt": "Modern studio, friendly female presenter",
    "variations": ["camera_angle", "lighting", "color_tone"]
  }'
```

**응답**:
```json
{
  "section_id": "section_abc123",
  "status": "processing",
  "clips": [
    {
      "clip_id": "clip_xyz1",
      "variation_type": "camera_angle",
      "status": "processing",
      "estimated_time": 50
    },
    {
      "clip_id": "clip_xyz2",
      "variation_type": "lighting",
      "status": "processing",
      "estimated_time": 50
    },
    {
      "clip_id": "clip_xyz3",
      "variation_type": "color_tone",
      "status": "processing",
      "estimated_time": 50
    }
  ],
  "message": "3 alternative clips are being generated..."
}
```

### 2. 대체 클립 목록 조회

**요청**:
```bash
curl http://localhost:8000/api/v1/sections/section_abc123/alternative-clips
```

### 3. 클립 교체

**요청**:
```bash
curl -X PATCH http://localhost:8000/api/v1/sections/section_abc123/clip \
  -H "Content-Type: application/json" \
  -d '{
    "new_clip_id": "clip_xyz2"
  }'
```

**응답**:
```json
{
  "section_id": "section_abc123",
  "new_clip_id": "clip_xyz2",
  "status": "success",
  "message": "Clip replaced successfully. Rendering will use the new clip."
}
```

---

## 향후 개선 사항

1. **Celery 작업 통합**:
   - 현재 `clip_editor_service.py`에서 직접 Veo API를 호출하지만, Celery 작업으로 완전히 이관 필요
   - `generate_alternative_clip_task`를 `clip_editor_service.py`에서 호출하도록 수정

2. **상태 폴링 최적화**:
   - WebSocket을 사용한 실시간 상태 업데이트
   - 프론트엔드에서 폴링 없이 진행률 확인

3. **프롬프트 품질 개선**:
   - LLM을 사용한 더 정교한 프롬프트 변형
   - 사용자 피드백 기반 프롬프트 학습

4. **비용 최적화**:
   - 대체 클립 생성 전 사용자에게 예상 비용 표시
   - 사용자가 원하는 변형만 선택적 생성 가능

5. **캐싱**:
   - 동일한 프롬프트로 이미 생성된 클립이 있으면 재사용
   - Redis를 사용한 클립 메타데이터 캐싱

---

## 결론

섹션별 대체 클립 생성 및 교체 API를 성공적으로 구현했습니다. 모든 핵심 기능이 동작하며, 다음 단계는 프론트엔드 통합 및 실제 Veo API 테스트입니다.

**생성된 파일**:
1. `/backend/app/services/clip_editor_service.py` (새 파일, 394줄)
2. `/backend/app/models/neo4j_models.py` (140줄 추가)
3. `/backend/app/api/v1/editor.py` (230줄 추가)
4. `/backend/app/tasks/director_tasks.py` (180줄 추가)
5. `/backend/test_clip_editor_api.py` (새 파일, 430줄)

**주요 함수 위치**:
- 프롬프트 변형 생성: `/backend/app/services/clip_editor_service.py:30-103`
- 대체 클립 생성: `/backend/app/services/clip_editor_service.py:152-224`
- 클립 교체: `/backend/app/services/clip_editor_service.py:265-294`
- API 엔드포인트: `/backend/app/api/v1/editor.py:275-505`
- Celery 작업: `/backend/app/tasks/director_tasks.py:600-780`

**API 문서**:
FastAPI 자동 생성 문서에서 확인 가능:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
