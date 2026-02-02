# 자막 조정 API 문서

영상의 자막 위치, 스타일, 크기를 조정하고 실시간 미리보기를 제공하는 API입니다.

## 목차

1. [개요](#개요)
2. [API 엔드포인트](#api-엔드포인트)
3. [자막 스타일 설정](#자막-스타일-설정)
4. [사용 예시](#사용-예시)
5. [FFmpeg 명령어](#ffmpeg-명령어)

---

## 개요

### 주요 기능

- **자막 스타일 조정**: 폰트, 색상, 위치, 아웃라인, 그림자 등 14가지 항목 조정
- **Neo4j 저장**: 프로젝트별 스타일 설정을 영구 저장
- **실시간 미리보기**: 변경사항을 5초 샘플 영상으로 즉시 확인
- **FFmpeg 오버레이**: ASS 형식 자막을 비디오에 번인(burn-in)

### 기술 스택

- **백엔드**: FastAPI + Pydantic
- **데이터베이스**: Neo4j (스타일 저장)
- **비디오 처리**: FFmpeg (ASS 자막 오버레이)
- **비동기 작업**: Celery (미리보기 생성)
- **포맷**: SRT → ASS 변환

---

## API 엔드포인트

### 1. 자막 스타일 조회

프로젝트의 현재 자막 스타일을 조회합니다. 설정이 없으면 기본 스타일을 반환합니다.

```http
GET /api/v1/projects/{project_id}/subtitles
```

#### 응답 예시

```json
{
  "project_id": "proj_abc123",
  "font_family": "Arial",
  "font_size": 24,
  "font_color": "#FFFFFF",
  "background_color": "#000000",
  "background_opacity": 0.7,
  "position": "bottom",
  "vertical_offset": 0,
  "alignment": "center",
  "outline_width": 1,
  "outline_color": "#000000",
  "shadow_enabled": false,
  "shadow_offset_x": 2,
  "shadow_offset_y": 2,
  "srt_file_path": "/path/to/video.srt",
  "updated_at": "2026-02-02T10:30:00Z"
}
```

---

### 2. 자막 스타일 업데이트

자막 스타일의 특정 필드를 업데이트합니다. (Partial Update)

```http
PATCH /api/v1/projects/{project_id}/subtitles
```

#### 요청 본문

```json
{
  "font_size": 32,
  "font_color": "#FFFF00",
  "background_opacity": 0.5,
  "position": "top",
  "outline_width": 2
}
```

#### 응답 예시

```json
{
  "project_id": "proj_abc123",
  "font_family": "Arial",
  "font_size": 32,
  "font_color": "#FFFF00",
  "background_color": "#000000",
  "background_opacity": 0.5,
  "position": "top",
  "vertical_offset": 0,
  "alignment": "center",
  "outline_width": 2,
  "outline_color": "#000000",
  "shadow_enabled": false,
  "shadow_offset_x": 2,
  "shadow_offset_y": 2,
  "updated_at": "2026-02-02T10:35:00Z"
}
```

---

### 3. 자막 미리보기 생성

변경된 스타일을 적용한 5초 샘플 영상을 생성합니다.

```http
POST /api/v1/projects/{project_id}/subtitles/preview
```

#### 요청 본문

```json
{
  "start_time": 0.0,
  "duration": 5.0,
  "style": {
    "font_size": 28,
    "font_color": "#00FF00",
    "outline_width": 2
  }
}
```

#### 응답 예시

```json
{
  "project_id": "proj_abc123",
  "preview_url": "/media/previews/preview_proj_abc123_20260202_103500.mp4",
  "expires_at": "2026-02-02T11:35:00Z",
  "style": {
    "project_id": "proj_abc123",
    "font_family": "Arial",
    "font_size": 28,
    "font_color": "#00FF00",
    "background_color": "#000000",
    "background_opacity": 0.7,
    "position": "bottom",
    "vertical_offset": 0,
    "alignment": "center",
    "outline_width": 2,
    "outline_color": "#000000",
    "shadow_enabled": false,
    "shadow_offset_x": 2,
    "shadow_offset_y": 2
  }
}
```

---

## 자막 스타일 설정

### 조정 가능한 항목

| 항목 | 타입 | 범위/값 | 설명 |
|------|------|---------|------|
| `font_family` | string | 폰트 이름 | 폰트 패밀리 (예: Arial, Noto Sans KR) |
| `font_size` | int | 24-72 | 폰트 크기 (픽셀) |
| `font_color` | string | HEX | 폰트 색상 (예: #FFFFFF) |
| `background_color` | string | HEX | 배경 색상 (예: #000000) |
| `background_opacity` | float | 0.0-1.0 | 배경 투명도 (0=투명, 1=불투명) |
| `position` | string | top/center/bottom | 자막 위치 |
| `vertical_offset` | int | -100~100 | 수직 오프셋 (픽셀) |
| `alignment` | string | left/center/right | 수평 정렬 |
| `outline_width` | int | 0-4 | 아웃라인 두께 (픽셀) |
| `outline_color` | string | HEX | 아웃라인 색상 (예: #000000) |
| `shadow_enabled` | bool | true/false | 그림자 활성화 |
| `shadow_offset_x` | int | -10~10 | 그림자 X 오프셋 |
| `shadow_offset_y` | int | -10~10 | 그림자 Y 오프셋 |

### 프리셋 스타일

#### 유튜브 스타일
```json
{
  "font_family": "Arial",
  "font_size": 28,
  "font_color": "#FFFFFF",
  "background_opacity": 0.8,
  "outline_width": 2,
  "position": "bottom"
}
```

#### 틱톡 스타일
```json
{
  "font_family": "Impact",
  "font_size": 36,
  "font_color": "#FFFF00",
  "outline_width": 3,
  "outline_color": "#000000",
  "position": "center"
}
```

#### 인스타그램 스타일
```json
{
  "font_family": "Helvetica",
  "font_size": 30,
  "font_color": "#FFFFFF",
  "outline_width": 2,
  "position": "bottom"
}
```

#### 미니멀 스타일
```json
{
  "font_family": "Helvetica",
  "font_size": 22,
  "font_color": "#FFFFFF",
  "background_opacity": 0.3,
  "outline_width": 1,
  "position": "bottom"
}
```

---

## 사용 예시

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = "proj_abc123"

# 1. 자막 스타일 조회
response = requests.get(f"{BASE_URL}/projects/{PROJECT_ID}/subtitles")
current_style = response.json()
print(f"현재 폰트 크기: {current_style['font_size']}")

# 2. 스타일 업데이트
update_data = {
    "font_size": 32,
    "font_color": "#FFFF00",
    "position": "top"
}
response = requests.patch(
    f"{BASE_URL}/projects/{PROJECT_ID}/subtitles",
    json=update_data
)
print(f"업데이트 완료: {response.status_code}")

# 3. 미리보기 생성
preview_request = {
    "start_time": 0.0,
    "duration": 5.0,
    "style": {
        "font_size": 28,
        "outline_width": 2
    }
}
response = requests.post(
    f"{BASE_URL}/projects/{PROJECT_ID}/subtitles/preview",
    json=preview_request
)
preview_data = response.json()
print(f"미리보기 URL: {preview_data['preview_url']}")
print(f"만료 시간: {preview_data['expires_at']}")
```

### cURL

```bash
# 자막 스타일 조회
curl -X GET "http://localhost:8000/api/v1/projects/proj_abc123/subtitles"

# 스타일 업데이트
curl -X PATCH "http://localhost:8000/api/v1/projects/proj_abc123/subtitles" \
  -H "Content-Type: application/json" \
  -d '{
    "font_size": 32,
    "font_color": "#FFFF00",
    "position": "top"
  }'

# 미리보기 생성
curl -X POST "http://localhost:8000/api/v1/projects/proj_abc123/subtitles/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": 0.0,
    "duration": 5.0,
    "style": {
      "font_size": 28,
      "outline_width": 2
    }
  }'
```

### JavaScript (Fetch API)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const PROJECT_ID = 'proj_abc123';

// 자막 스타일 조회
async function getSubtitleStyle() {
  const response = await fetch(`${BASE_URL}/projects/${PROJECT_ID}/subtitles`);
  const style = await response.json();
  console.log('현재 스타일:', style);
  return style;
}

// 스타일 업데이트
async function updateSubtitleStyle(updates) {
  const response = await fetch(`${BASE_URL}/projects/${PROJECT_ID}/subtitles`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  const updatedStyle = await response.json();
  console.log('업데이트된 스타일:', updatedStyle);
  return updatedStyle;
}

// 미리보기 생성
async function generatePreview(startTime, duration, styleOverrides) {
  const response = await fetch(`${BASE_URL}/projects/${PROJECT_ID}/subtitles/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_time: startTime,
      duration: duration,
      style: styleOverrides
    })
  });
  const preview = await response.json();
  console.log('미리보기 URL:', preview.preview_url);
  return preview;
}

// 사용 예시
(async () => {
  await updateSubtitleStyle({ font_size: 32, font_color: '#FFFF00' });
  await generatePreview(0.0, 5.0, { outline_width: 2 });
})();
```

---

## FFmpeg 명령어

### SRT → ASS 변환 후 오버레이

```bash
# 1. ASS 파일 생성 (subtitle_editor_service.py가 자동 처리)
# SRT → ASS 변환 + 스타일 적용

# 2. FFmpeg로 비디오에 자막 오버레이
ffmpeg -i input_video.mp4 \
  -vf "ass=subtitle.ass" \
  -c:a copy \
  -c:v libx264 \
  -preset fast \
  -y output_video.mp4
```

### 미리보기 생성 (5초 샘플)

```bash
ffmpeg -ss 0.0 -i input_video.mp4 \
  -t 5.0 \
  -vf "ass=subtitle.ass" \
  -c:a copy \
  -c:v libx264 \
  -preset ultrafast \
  -y preview_5sec.mp4
```

### ASS 스타일 구조 예시

```ass
[Script Info]
Title: OmniVibe Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,32,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H80000000&,0,0,0,0,100,100,0,0,1,2,0,2,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.50,Default,,0,0,0,,안녕하세요. 오늘은 좋은 날씨입니다.
```

---

## 에러 처리

### 404 Not Found

```json
{
  "detail": "Project not found: proj_invalid"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "font_size"],
      "msg": "ensure this value is less than or equal to 72",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error: FFmpeg not found"
}
```

---

## 파일 위치

- **API 엔드포인트**: `/backend/app/api/v1/editor.py:276-571`
- **서비스 로직**: `/backend/app/services/subtitle_editor_service.py`
- **Pydantic 모델**: `/backend/app/models/neo4j_models.py:314-391`
- **Neo4j CRUD**: `/backend/app/models/neo4j_models.py:1062-1128`
- **Celery 태스크**: `/backend/app/tasks/subtitle_tasks.py`

---

## 다음 단계

1. **프론트엔드 통합**: React/Vue로 자막 스타일 편집 UI 구현
2. **실시간 미리보기**: WebSocket으로 실시간 미리보기 스트리밍
3. **AI 추천**: 과거 성과 데이터 기반 최적 스타일 추천
4. **다국어 지원**: 한국어, 영어, 일본어 자막 동시 생성
5. **자동 싱크**: Whisper 타임스탬프 기반 자막 싱크 자동 조정

---

**문서 작성일**: 2026-02-02
**버전**: 1.0.0
**작성자**: Claude (OmniVibe Pro Team)
