# Campaigns API 구현 완료

## 개요

Studio 워크플로우의 캠페인 관리를 위한 RESTful API가 구현되었습니다.

## 구현 파일

### 1. **backend/app/models/campaign.py**
캠페인 데이터 모델 정의:
- `CampaignBase`: 기본 캠페인 필드
- `CampaignCreate`: 생성 요청
- `CampaignUpdate`: 업데이트 요청 (부분 업데이트)
- `Campaign`: 응답 모델
- Enum 클래스들: `CampaignStatus`, `ConceptGender`, `ConceptTone`, `ConceptStyle`

### 2. **backend/app/api/v1/campaigns.py**
API 엔드포인트 구현:
- 8개의 주요 엔드포인트
- Cloudinary 통합 (파일 업로드)
- 임시 인메모리 저장소 (SQLite 구현 전)

## API 엔드포인트

### 1. POST `/api/v1/campaigns/`
**새 캠페인 생성**

**요청 바디**:
```json
{
  "client_id": 1,
  "name": "2024 봄 시즌 캠페인",
  "concept_gender": "female",
  "concept_tone": "friendly",
  "concept_style": "soft",
  "target_duration": 60,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "voice_name": "Rachel",
  "intro_duration": 5,
  "outro_duration": 5,
  "bgm_volume": 0.3,
  "auto_deploy": false,
  "status": "active"
}
```

**응답**: 생성된 캠페인 정보 (201 Created)

---

### 2. GET `/api/v1/campaigns/`
**캠페인 목록 조회**

**쿼리 파라미터**:
- `client_id` (optional): 특정 클라이언트의 캠페인 필터링
- `status` (optional): 상태 필터링 (active, paused, completed, archived)
- `page` (default: 1): 페이지 번호
- `page_size` (default: 20, max: 100): 페이지 크기

**예시**:
```
GET /api/v1/campaigns/?client_id=1&status=active&page=1&page_size=20
```

**응답**:
```json
{
  "campaigns": [...],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### 3. GET `/api/v1/campaigns/{campaign_id}`
**특정 캠페인 조회**

**응답**: 캠페인 상세 정보

---

### 4. PATCH `/api/v1/campaigns/{campaign_id}`
**캠페인 정보 업데이트**

**요청 바디** (부분 업데이트):
```json
{
  "name": "수정된 캠페인 이름",
  "target_duration": 90,
  "status": "paused"
}
```

**응답**: 수정된 캠페인 정보

---

### 5. DELETE `/api/v1/campaigns/{campaign_id}`
**캠페인 삭제**

**응답**: 204 No Content

---

### 6. GET `/api/v1/campaigns/{campaign_id}/schedule`
**캠페인의 콘텐츠 스케줄 조회**

**응답**:
```json
{
  "campaign_id": 1,
  "schedules": [],
  "total": 0
}
```

*참고: SQLite content_schedule 테이블 구현 후 실제 데이터 반환*

---

### 7. POST `/api/v1/campaigns/{campaign_id}/resources`
**캠페인 리소스 업로드**

**폼 데이터**:
- `file`: 업로드할 파일 (multipart/form-data)
- `resource_type`: "intro", "outro", "bgm" 중 하나

**지원 포맷**:
- 비디오 (intro, outro): mp4, mov, avi
- 오디오 (bgm): mp3, wav, m4a

**예시 (cURL)**:
```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/1/resources" \
  -F "file=@intro_video.mp4" \
  -F "resource_type=intro"
```

**응답**:
```json
{
  "resource_type": "intro",
  "url": "https://res.cloudinary.com/.../intro_video.mp4",
  "public_id": "campaigns/1/intro/campaign_1_intro",
  "duration": 5.2,
  "format": "mp4"
}
```

**자동 업데이트**: 업로드 시 캠페인의 해당 필드가 자동으로 업데이트됩니다:
- `intro` -> `intro_video_url`, `intro_duration`
- `outro` -> `outro_video_url`, `outro_duration`
- `bgm` -> `bgm_url`

---

### 8. GET `/api/v1/campaigns/{campaign_id}/resources`
**캠페인 리소스 조회**

**응답**:
```json
{
  "campaign_id": 1,
  "resources": {
    "intro": {
      "url": "https://res.cloudinary.com/.../intro.mp4",
      "duration": 5
    },
    "outro": {
      "url": "https://res.cloudinary.com/.../outro.mp4",
      "duration": 5
    },
    "bgm": {
      "url": "https://res.cloudinary.com/.../bgm.mp3",
      "volume": 0.3
    }
  }
}
```

---

## 데이터 모델

### Campaign 필드 설명

| 필드 | 타입 | 설명 | 필수 여부 |
|------|------|------|-----------|
| `id` | int | 캠페인 ID (자동 생성) | - |
| `client_id` | int | 클라이언트 ID | ✅ |
| `name` | str | 캠페인 이름 | ✅ |
| `concept_gender` | enum | 컨셉 성별 (female, male, neutral) | ❌ |
| `concept_tone` | enum | 컨셉 톤 (professional, friendly, humorous, serious) | ❌ |
| `concept_style` | enum | 컨셉 스타일 (soft, intense, calm, energetic) | ❌ |
| `target_duration` | int | 목표 영상 길이 (초, 10-600) | ❌ |
| `voice_id` | str | ElevenLabs Voice ID | ❌ |
| `voice_name` | str | 음성 이름 (표시용) | ❌ |
| `intro_video_url` | str | 인트로 영상 URL | ❌ |
| `intro_duration` | int | 인트로 길이 (초, 0-10) | ❌ (기본값: 5) |
| `outro_video_url` | str | 엔딩 영상 URL | ❌ |
| `outro_duration` | int | 엔딩 길이 (초, 0-10) | ❌ (기본값: 5) |
| `bgm_url` | str | 배경음악 URL | ❌ |
| `bgm_volume` | float | BGM 볼륨 (0.0-1.0) | ❌ (기본값: 0.3) |
| `publish_schedule` | str | 발행 스케줄 | ❌ |
| `auto_deploy` | bool | 자동 배포 여부 | ❌ (기본값: false) |
| `status` | enum | 캠페인 상태 (active, paused, completed, archived) | ❌ (기본값: active) |
| `created_at` | datetime | 생성 시간 | - |
| `updated_at` | datetime | 수정 시간 | - |

---

## 통합 완료 사항

### 1. 라우터 등록
- `backend/app/api/v1/__init__.py`에 campaigns 라우터 추가
- FastAPI 메인 앱에 자동 등록

### 2. OpenAPI 태그
- `backend/app/main.py`에 "Campaigns" 태그 추가
- Swagger UI에서 확인 가능: http://localhost:8000/docs

### 3. Cloudinary 통합
- 파일 업로드 시 `get_cloudinary_service()` 사용
- 비디오/오디오 업로드 및 URL 자동 저장
- 폴더 구조: `campaigns/{campaign_id}/{resource_type}/`

---

## TODO: SQLite 통합 예정

현재는 임시 인메모리 저장소를 사용하고 있습니다.  
SQLite 구현 시 다음 작업이 필요합니다:

1. **테이블 마이그레이션**:
   ```sql
   CREATE TABLE campaigns (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       client_id INTEGER NOT NULL,
       name TEXT NOT NULL,
       concept_gender TEXT,
       concept_tone TEXT,
       concept_style TEXT,
       target_duration INTEGER,
       voice_id TEXT,
       voice_name TEXT,
       intro_video_url TEXT,
       intro_duration INTEGER DEFAULT 5,
       outro_video_url TEXT,
       outro_duration INTEGER DEFAULT 5,
       bgm_url TEXT,
       bgm_volume REAL DEFAULT 0.3,
       publish_schedule TEXT,
       auto_deploy INTEGER DEFAULT 0,
       status TEXT DEFAULT 'active',
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (client_id) REFERENCES clients(id)
   );
   ```

2. **CRUD 함수 교체**:
   - `_campaigns_store` 제거
   - SQLite 쿼리로 교체

3. **content_schedule 연동**:
   - `GET /campaigns/{campaign_id}/schedule` 실제 구현

---

## 테스트 예시

### 1. 캠페인 생성
```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "name": "2024 여름 캠페인",
    "concept_gender": "female",
    "concept_tone": "friendly",
    "target_duration": 60
  }'
```

### 2. 캠페인 목록 조회
```bash
curl "http://localhost:8000/api/v1/campaigns/?client_id=1"
```

### 3. 리소스 업로드
```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/1/resources" \
  -F "file=@intro.mp4" \
  -F "resource_type=intro"
```

---

## 프론트엔드 통합 가이드

### TypeScript 타입 정의
```typescript
enum CampaignStatus {
  ACTIVE = "active",
  PAUSED = "paused",
  COMPLETED = "completed",
  ARCHIVED = "archived"
}

interface Campaign {
  id: number;
  client_id: number;
  name: string;
  concept_gender?: "female" | "male" | "neutral";
  concept_tone?: "professional" | "friendly" | "humorous" | "serious";
  concept_style?: "soft" | "intense" | "calm" | "energetic";
  target_duration?: number;
  voice_id?: string;
  voice_name?: string;
  intro_video_url?: string;
  intro_duration: number;
  outro_video_url?: string;
  outro_duration: number;
  bgm_url?: string;
  bgm_volume: number;
  publish_schedule?: string;
  auto_deploy: boolean;
  status: CampaignStatus;
  created_at: string;
  updated_at: string;
}
```

### API 호출 예시 (fetch)
```typescript
// 캠페인 생성
const createCampaign = async (data: CampaignCreate) => {
  const response = await fetch("http://localhost:8000/api/v1/campaigns/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return await response.json();
};

// 파일 업로드
const uploadResource = async (campaignId: number, file: File, type: string) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("resource_type", type);
  
  const response = await fetch(
    `http://localhost:8000/api/v1/campaigns/${campaignId}/resources`,
    { method: "POST", body: formData }
  );
  return await response.json();
};
```

---

## 완료 체크리스트

- ✅ Pydantic 모델 정의 (`campaign.py`)
- ✅ 8개 API 엔드포인트 구현
- ✅ 클라이언트별 필터링 지원
- ✅ 페이징 지원
- ✅ 부분 업데이트 (PATCH)
- ✅ Cloudinary 파일 업로드 통합
- ✅ 라우터 등록 (`__init__.py`)
- ✅ OpenAPI 태그 추가 (`main.py`)
- ✅ 구문 검사 통과

---

## 다음 단계

1. **SQLite 데이터베이스 구현** (Task 1)
2. **Clients API 구현** (Task 2)
3. **Content Schedule API 구현** (Task 4)
4. **통합 테스트 작성**
