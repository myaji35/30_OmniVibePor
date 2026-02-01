# Swagger UI Configuration Guide

## Overview

OmniVibe Pro API는 FastAPI의 자동 OpenAPI 문서 생성 기능을 활용하여 **Swagger UI**와 **ReDoc**을 제공합니다.

---

## Access Points

### Swagger UI (Interactive API Documentation)
- **URL**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Description**: 인터랙티브 API 문서 (직접 API 테스트 가능)
- **Features**:
  - Deep linking 활성화
  - 인증 정보 자동 저장
  - 요청/응답 시간 표시
  - 필터링 기능
  - Monokai 테마 (코드 하이라이팅)

### ReDoc (Alternative Documentation)
- **URL**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Description**: 읽기 전용 API 문서 (깔끔한 디자인)

### OpenAPI Schema (JSON)
- **URL**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Description**: OpenAPI 3.0 스키마 (자동 생성)

---

## Configuration

### Main Application Settings

위치: `backend/app/main.py`

```python
app = FastAPI(
    title="🎬 OmniVibe Pro API",
    description=CUSTOM_DESCRIPTION,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url=None,  # 기본 docs 비활성화 (커스텀 사용)
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Voice Cloning",
            "description": "🎤 녹음된 목소리를 학습하여 커스텀 TTS 생성",
        },
        {
            "name": "Zero-Fault Audio",
            "description": "🔊 99% 정확도의 검증된 오디오 생성 (TTS + STT Loop)",
        },
        {
            "name": "Thumbnail Learning",
            "description": "🖼️ 타인의 고성과 썸네일 학습 및 자동 생성",
        },
        {
            "name": "Performance Tracking",
            "description": "📊 멀티 플랫폼 성과 분석 및 자가학습 시스템",
        },
    ]
)
```

---

## Custom Swagger UI

커스텀 Swagger UI 엔드포인트가 구현되어 있습니다:

```python
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """커스텀 Swagger UI (Stripe 스타일)"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "deepLinking": True,
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "syntaxHighlight.theme": "monokai",
        },
    )
```

### Custom UI Features:
- **Deep Linking**: URL에 선택한 엔드포인트 정보 포함
- **Persist Authorization**: 새로고침 후에도 인증 정보 유지
- **Display Request Duration**: 요청 소요 시간 표시
- **Filter**: 엔드포인트 검색 기능
- **Syntax Highlighting**: Monokai 테마로 코드 하이라이팅

---

## API Tags

API 엔드포인트는 다음 태그로 그룹화되어 있습니다:

| Tag | Description | Endpoints Count |
|-----|-------------|-----------------|
| **Voice Cloning** | 커스텀 음성 생성 및 관리 | 5 |
| **Zero-Fault Audio** | 검증된 오디오 생성 | 7 |
| **Google Sheets** | 구글 시트 연동 | 10 |
| **Writer Agent** | 스크립트 자동 생성 | 2 |
| **Director Agent** | 오디오 생성 및 검증 | 3 |
| **Continuity Agent** | 콘티 자동 생성 | 4 |
| **Thumbnail Learning** | 썸네일 학습 및 생성 | 3 |
| **Performance Tracking** | 성과 분석 및 자가학습 | 5 |

---

## Example Endpoints Documentation

### Pydantic Models

모든 엔드포인트는 **Pydantic 모델**을 사용하여 요청/응답 스키마를 정의합니다.

예시: `VoiceCloneResponse`

```python
class VoiceCloneResponse(BaseModel):
    """음성 클로닝 응답"""
    voice_id: str = Field(..., description="생성된 음성 ID")
    name: str = Field(..., description="음성 이름")
    status: str = Field(..., description="상태 (ready, training)")
    message: str = Field(..., description="응답 메시지")
```

### Docstrings

모든 엔드포인트는 **상세한 docstring**을 포함하여 Swagger UI에 자동으로 표시됩니다.

예시: `/voice/clone` 엔드포인트

```python
@router.post("/clone", response_model=VoiceCloneResponse)
async def clone_voice(...):
    """
    음성 클로닝 - 녹음된 오디오로 커스텀 음성 생성

    **요구사항**:
    - 최소 오디오 길이: 1분 이상
    - 권장 오디오 길이: 3-5분 (고품질)

    **예시**:
    \```bash
    curl -X POST "http://localhost:8000/api/v1/voice/clone" \\
      -F "user_id=user123" \\
      -F "voice_name=김대표님" \\
      -F "audio_file=@recording.mp3"
    \```
    """
```

---

## Best Practices

### 1. Request/Response Examples

각 엔드포인트의 docstring에 다음을 포함하세요:
- ✅ **요청 예시** (curl 커맨드)
- ✅ **응답 예시** (JSON)
- ✅ **에러 케이스** (가능한 경우)

### 2. Field Descriptions

Pydantic 모델의 모든 필드에 `description`을 추가하세요:

```python
class AudioGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000,
                     description="변환할 텍스트 (최대 5000자)")
    voice_id: Optional[str] = Field(None,
                                   description="음성 ID (기본값: rachel)")
```

### 3. HTTP Status Codes

각 엔드포인트에 적절한 HTTP 상태 코드를 명시하세요:

```python
@router.post("/clone",
             response_model=VoiceCloneResponse,
             status_code=status.HTTP_201_CREATED)
```

### 4. Tags

라우터에 태그를 명시하여 그룹화하세요:

```python
router = APIRouter(prefix="/voice", tags=["Voice Cloning"])
```

---

## Testing Swagger UI

### 1. 서버 시작

Docker Compose 사용:
```bash
cd backend
make up
```

또는 로컬 실행:
```bash
cd backend
make dev
```

### 2. Swagger UI 접속

브라우저에서 다음 주소로 접속:
- http://localhost:8000/docs

### 3. API 테스트

1. 엔드포인트 선택 (예: `POST /api/v1/voice/clone`)
2. **Try it out** 버튼 클릭
3. 요청 파라미터 입력
4. **Execute** 버튼 클릭
5. 응답 확인

---

## Customization

### 1. 테마 변경

`app/main.py`의 `swagger_ui_parameters`에서 테마를 변경할 수 있습니다:

```python
swagger_ui_parameters={
    ...
    "syntaxHighlight.theme": "agate",  # monokai, agate, nord, obsidian
}
```

### 2. Description 커스터마이징

`CUSTOM_DESCRIPTION` 변수를 수정하여 API 소개 페이지를 커스터마이징할 수 있습니다:

```python
CUSTOM_DESCRIPTION = """
## 🚀 Welcome to OmniVibe Pro API
...
"""
```

### 3. OpenAPI Schema 확장

FastAPI의 `openapi_schema` 함수를 오버라이드하여 추가 정보를 제공할 수 있습니다.

---

## Troubleshooting

### Swagger UI가 표시되지 않을 때

1. **서버가 실행 중인지 확인**
   ```bash
   curl http://localhost:8000/
   ```

2. **OpenAPI 스키마가 생성되는지 확인**
   ```bash
   curl http://localhost:8000/openapi.json
   ```

3. **브라우저 캐시 삭제**
   - Chrome/Edge: `Ctrl+Shift+Del`
   - Safari: `Cmd+Option+E`

4. **CORS 설정 확인**
   - `app/main.py`의 CORS 설정 확인

---

## Additional Resources

- [FastAPI Documentation - Swagger UI](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI Configuration](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/)

---

**Last Updated**: 2026-02-02
