# CharacterService 구현 문서

## 개요

`CharacterService`는 Nano Banana를 사용한 일관된 캐릭터 레퍼런스 생성 및 관리 서비스입니다.

### 핵심 기능

1. **캐릭터 일관성 보장**: 동일한 페르소나는 항상 동일한 캐릭터 이미지 사용
2. **Nano Banana API 통합**: Stable Diffusion 기반 고품질 캐릭터 생성
3. **Neo4j 저장**: 캐릭터 정보를 그래프 데이터베이스에 영구 저장
4. **Fallback 모드**: API 사용 불가 시 대체 로직 제공

## 파일 구조

```
backend/
├── app/
│   ├── services/
│   │   ├── character_service.py       # 메인 서비스
│   │   └── neo4j_client.py            # Neo4j 스키마 확장
│   └── core/
│       └── config.py                  # 환경 변수 설정
└── test_character_service.py          # 테스트 스크립트
```

## 설치 및 설정

### 1. 의존성 설치

```bash
cd backend
poetry install
# 또는
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일에 다음 변수를 추가합니다:

```env
# Nano Banana API (선택)
BANANA_API_KEY=your_banana_api_key_here

# 캐릭터 저장 경로
CHARACTER_STORAGE_PATH=./outputs/characters

# Neo4j (필수)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. Neo4j 스키마 초기화

```python
from app.services.neo4j_client import get_neo4j_client

client = get_neo4j_client()
client.create_full_schema()
```

## 사용 예시

### 기본 사용법

```python
from app.services.character_service import get_character_service

# 서비스 인스턴스 가져오기
service = get_character_service()

# 캐릭터 생성 또는 조회
character = await service.get_or_create_character(
    persona_id="persona_001",
    gender="female",
    age_range="30-40",
    style="professional"
)

print(f"캐릭터 ID: {character['character_id']}")
print(f"이미지 URL: {character['reference_image_url']}")
```

### 캐릭터 레퍼런스 생성

```python
# 새 캐릭터 강제 생성
character = await service.generate_character_reference(
    persona_id="persona_002",
    gender="male",
    age_range="40-50",
    style="casual",
    additional_traits=["glasses", "friendly smile"],
    force_regenerate=True
)
```

### 영상 생성용 프롬프트 변환

```python
# 캐릭터 데이터를 Veo API용 프롬프트로 변환
prompt = service.character_to_prompt(
    character_data=character,
    scene_context="presenting in a modern conference room"
)
# 출력: "Professional woman in her 30s, ..., presenting in a modern conference room"
```

### 페르소나의 캐릭터 조회

```python
# 특정 페르소나의 캐릭터 조회
character = await service.get_persona_character("persona_001")

if character:
    print(f"기존 캐릭터 발견: {character['character_id']}")
else:
    print("캐릭터가 없습니다. 새로 생성하세요.")
```

## API 레퍼런스

### CharacterService

#### `generate_character_reference()`

캐릭터 레퍼런스 이미지를 생성합니다.

**파라미터:**
- `persona_id` (str): 페르소나 ID
- `gender` (str): 성별 ('male', 'female', 'neutral')
- `age_range` (str): 연령대 ('20-30', '30-40', '40-50', '50-60')
- `style` (str): 스타일 ('professional', 'casual', 'creative', 'formal')
- `additional_traits` (List[str], optional): 추가 특징 리스트
- `force_regenerate` (bool): 기존 캐릭터 무시하고 재생성 여부

**반환값:**
```python
{
    "character_id": "char_abc123...",
    "persona_id": "persona_001",
    "reference_image_url": "https://...",
    "prompt_template": "Professional woman in her 30s, ...",
    "gender": "female",
    "age_range": "30-40",
    "style": "professional",
    "additional_traits": [],
    "created_at": "2026-02-02T12:00:00",
    "generation_metadata": {
        "model": "stable-diffusion-xl",
        "generation_time": 3.2,
        "is_fallback": False
    }
}
```

#### `get_or_create_character()`

기존 캐릭터를 조회하거나 없으면 생성합니다.

**파라미터:** `generate_character_reference()`와 동일 (force_regenerate 제외)

**반환값:** `generate_character_reference()`와 동일

#### `character_to_prompt()`

캐릭터 데이터를 영상 생성용 프롬프트로 변환합니다.

**파라미터:**
- `character_data` (Dict[str, Any]): 캐릭터 데이터
- `scene_context` (str, optional): 장면 컨텍스트

**반환값:** 변환된 프롬프트 문자열

#### `get_persona_character()`

페르소나의 캐릭터를 조회합니다.

**파라미터:**
- `persona_id` (str): 페르소나 ID

**반환값:** 캐릭터 정보 (없으면 None)

#### `delete_character()`

캐릭터를 삭제합니다.

**파라미터:**
- `character_id` (str): 캐릭터 ID

**반환값:** 삭제 성공 여부 (bool)

## Neo4j 스키마

### 노드

#### `:Character`

**속성:**
- `character_id` (String, UNIQUE): 캐릭터 고유 ID
- `reference_image_url` (String): 레퍼런스 이미지 URL
- `prompt_template` (String): 생성에 사용된 프롬프트
- `gender` (String): 성별
- `age_range` (String): 연령대
- `style` (String): 스타일
- `additional_traits` (List[String]): 추가 특징
- `created_at` (DateTime): 생성 시간
- `generation_metadata` (Map): 생성 메타데이터

### 관계

```cypher
(:Persona)-[:HAS_CHARACTER]->(:Character)
```

### 쿼리 예시

```cypher
// 페르소나의 캐릭터 조회
MATCH (p:Persona {persona_id: "persona_001"})-[:HAS_CHARACTER]->(c:Character)
RETURN c

// 모든 캐릭터 통계
MATCH (c:Character)
RETURN c.gender as gender,
       c.style as style,
       count(*) as count
```

## 테스트

### 기본 테스트 실행

```bash
cd backend
python3 test_character_service.py
```

### 예상 출력

```
============================================================
CharacterService 테스트 시작
============================================================

[1] 캐릭터 ID 생성 테스트
------------------------------------------------------------
  페르소나 ID: persona_test_001
  생성된 캐릭터 ID: char_abc123...
  ✓ 캐릭터 ID 생성 성공

[2] 캐릭터 프롬프트 생성 테스트
------------------------------------------------------------
  생성된 프롬프트:
  Portrait of a woman, professional in their 30s, ...
  ✓ 프롬프트 생성 성공

...

============================================================
모든 테스트 통과! ✓
============================================================
```

## 통합 가이드

### Director 에이전트와 통합

```python
from app.services.character_service import get_character_service
from app.services.veo_service import get_veo_service

# 1. 캐릭터 생성/조회
character_service = get_character_service()
character = await character_service.get_or_create_character(
    persona_id=persona_id,
    gender="female",
    age_range="30-40",
    style="professional"
)

# 2. 영상 생성용 프롬프트 변환
scene_prompt = character_service.character_to_prompt(
    character_data=character,
    scene_context="explaining a product feature enthusiastically"
)

# 3. Google Veo로 영상 생성
veo_service = get_veo_service()
video_result = await veo_service.generate_video(
    prompt=scene_prompt,
    reference_image_url=character["reference_image_url"]
)
```

### Writer 에이전트와 통합

```python
# 스크립트 생성 시 페르소나 정보에 캐릭터 포함
persona_data = {
    "persona_id": "persona_001",
    "gender": "female",
    "age_range": "30-40",
    "tone": "friendly",
    "style": "professional"
}

# 캐릭터 생성
character = await character_service.get_or_create_character(**persona_data)

# 스크립트에 캐릭터 정보 메타데이터 추가
script_metadata = {
    "character_id": character["character_id"],
    "character_prompt": character["prompt_template"]
}
```

## 트러블슈팅

### 1. Banana API 연결 실패

**증상:** "Banana API key not configured" 에러

**해결:**
- `.env` 파일에 `BANANA_API_KEY` 설정
- Fallback 모드 사용 (자동으로 전환됨)

### 2. Neo4j 연결 실패

**증상:** "Failed to query character from Neo4j" 에러

**해결:**
```bash
# Docker로 Neo4j 시작
docker-compose up -d neo4j

# 연결 테스트
docker exec -it omnivibe-neo4j cypher-shell -u neo4j -p your_password
```

### 3. 캐릭터 일관성 문제

**증상:** 같은 페르소나인데 다른 캐릭터가 생성됨

**원인:** 캐릭터 ID 생성 로직이 페르소나 ID를 해시하므로, 페르소나 ID가 달라지면 캐릭터도 달라집니다.

**해결:** 페르소나 ID를 일관되게 유지하세요.

## 향후 개선 사항

1. **로컬 Stable Diffusion 통합**
   - Banana API 의존성 제거
   - 오프라인 캐릭터 생성 지원

2. **캐릭터 변형 생성**
   - 같은 캐릭터의 다양한 표정/포즈
   - ControlNet 통합

3. **캐릭터 버전 관리**
   - 캐릭터 업데이트 이력 저장
   - 이전 버전으로 롤백 기능

4. **성능 최적화**
   - 캐릭터 이미지 캐싱
   - 프롬프트 템플릿 재사용

## 관련 문서

- [CLAUDE.md](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/CLAUDE.md) - 프로젝트 아키텍처
- [Neo4j 클라이언트](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/backend/app/services/neo4j_client.py) - 데이터베이스 연동
- [Veo 서비스](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/backend/app/services/veo_service.py) - 영상 생성 연동

## 라이선스

이 코드는 OmniVibe Pro 프로젝트의 일부이며, 프로젝트 라이선스를 따릅니다.
