# Neo4j GraphRAG 사용 가이드

**OmniVibe Pro** - Neo4j 데이터베이스 사용법

---

## 1. 초기 설정

### 1.1 환경 변수 설정
`.env` 파일에 Neo4j 연결 정보를 설정하세요:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### 1.2 스키마 생성
프로젝트 최초 실행 시 스키마를 생성합니다:

```bash
cd /Volumes/Extreme\ SSD/02_GitHub.nosync/30_OmniVibePro/backend
python scripts/init_neo4j.py --create-schema
```

### 1.3 샘플 데이터 생성 (옵션)
테스트를 위한 샘플 데이터를 생성할 수 있습니다:

```bash
python scripts/init_neo4j.py --create-schema --create-samples
```

### 1.4 데이터베이스 초기화 (주의!)
모든 데이터를 삭제하고 스키마를 재생성합니다:

```bash
python scripts/init_neo4j.py --reset
```

---

## 2. Python 코드에서 사용하기

### 2.1 기본 사용법

```python
from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import (
    Neo4jCRUDManager,
    UserModel,
    PersonaModel,
    ProjectModel,
    SubscriptionTier,
    Gender,
    Tone,
    ContentStyle,
    Platform,
    ProjectStatus,
)

# Neo4j 클라이언트 초기화
client = get_neo4j_client()
crud = Neo4jCRUDManager(client)

# 사용자 생성
user = UserModel(
    email="user@example.com",
    name="홍길동",
    subscription_tier=SubscriptionTier.PRO
)
created_user = crud.create_user(user)
print(f"User created: {created_user['user_id']}")

# 페르소나 생성
persona = PersonaModel(
    gender=Gender.FEMALE,
    tone=Tone.PROFESSIONAL,
    style=ContentStyle.EDUCATION,
    voice_id="21m00Tcm4TlvDq8ikWAM"
)
created_persona = crud.create_persona(created_user['user_id'], persona)
print(f"Persona created: {created_persona['persona_id']}")

# 프로젝트 생성
project = ProjectModel(
    title="AI 트렌드 2026",
    topic="인공지능",
    platform=Platform.YOUTUBE,
    status=ProjectStatus.DRAFT
)
created_project = crud.create_project(
    created_user['user_id'],
    project,
    created_persona['persona_id']
)
print(f"Project created: {created_project['project_id']}")

# 완료 후 연결 종료
client.close()
```

---

## 3. Writer 에이전트 연동

Writer 에이전트는 고성과 패턴을 학습하여 스크립트를 생성합니다.

```python
from app.services.neo4j_client import get_neo4j_client

client = get_neo4j_client()

# 사용자의 고성과 콘텐츠 조회
high_performance = client.get_top_performing_content(
    user_id="user_12345",
    limit=10,
    min_score=70.0
)

for content in high_performance:
    print(f"Topic: {content['topic']}")
    print(f"Score: {content['score']}")
    print(f"Engagement: {content['engagement']:.2%}")
    print(f"Script Preview: {content['script_content'][:100]}...")
    print("-" * 50)

client.close()
```

---

## 4. Director 에이전트 연동

Director 에이전트는 스크립트를 오디오와 비디오로 변환합니다.

```python
from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import (
    Neo4jCRUDManager,
    ScriptModel,
    AudioModel,
    VideoModel,
    Platform,
)

client = get_neo4j_client()
crud = Neo4jCRUDManager(client)

# 스크립트 생성
script = ScriptModel(
    content="안녕하세요! 오늘은 AI 트렌드에 대해 알아보겠습니다...",
    platform=Platform.YOUTUBE,
    word_count=500,
    estimated_duration=180,
    version=1
)
created_script = crud.create_script("proj_abc123", script, selected=True)

# 오디오 생성 (Zero-Fault Loop 후)
audio = AudioModel(
    file_path="s3://bucket/audio_001.mp3",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    duration=185.5,
    stt_accuracy=0.98,
    retry_count=1
)
created_audio = crud.create_audio(created_script['script_id'], audio)

# 비디오 생성
video = VideoModel(
    file_path="s3://bucket/video_final.mp4",
    duration=190.0,
    resolution="1920x1080",
    format="mp4",
    veo_prompt="Professional educator explaining AI trends",
    lipsync_enabled=True
)
created_video = crud.create_video(
    "proj_abc123",
    created_audio['audio_id'],
    video
)

print(f"Video created: {created_video['video_id']}")

client.close()
```

---

## 5. Marketer 에이전트 연동

Marketer 에이전트는 성과 데이터를 수집하고 분석합니다.

```python
from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import Neo4jCRUDManager, MetricsModel

client = get_neo4j_client()
crud = Neo4jCRUDManager(client)

# 성과 메트릭 저장
metrics = MetricsModel(
    views=15000,
    likes=850,
    comments=120,
    shares=45,
    watch_time=2550000,
    engagement_rate=0.067,
    ctr=0.089,
    performance_score=78.5
)
created_metrics = crud.create_metrics("video_xyz789", metrics)

# 플랫폼별 성과 분석
analytics = crud.get_platform_analytics("user_12345")

for platform_data in analytics:
    print(f"Platform: {platform_data['platform']}")
    print(f"Total Videos: {platform_data['total_videos']}")
    print(f"Avg Views: {platform_data['avg_views']:.0f}")
    print(f"Avg Score: {platform_data['avg_score']:.1f}")
    print("-" * 50)

client.close()
```

---

## 6. 분석 대시보드

사용자의 전체 성과를 조회합니다.

```python
from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import Neo4jCRUDManager

client = get_neo4j_client()
crud = Neo4jCRUDManager(client)

# 최근 30일 성과 요약
summary = crud.get_user_performance_summary("user_12345", days=30)

print(f"Total Videos: {summary['total_videos']}")
print(f"Total Views: {summary['total_views']:,}")
print(f"Avg Engagement: {summary['avg_engagement']:.2%}")
print(f"Avg Performance: {summary['avg_performance_score']:.1f}")
print(f"Best Performance: {summary['best_performance_score']:.1f}")

# 사용자 분석 대시보드
dashboard = client.get_user_analytics_dashboard("user_12345", days=30)

print(f"\nDashboard Summary:")
print(f"Total Projects: {dashboard['total_projects']}")
print(f"Total Videos: {dashboard['total_videos']}")
print(f"Total Views: {dashboard['total_views']:,}")
print(f"Platforms Used: {', '.join(dashboard['platforms_used'])}")

client.close()
```

---

## 7. 프로젝트 전체 컨텍스트 조회

프로젝트의 모든 관련 데이터를 한 번에 조회합니다.

```python
from app.services.neo4j_client import get_neo4j_client

client = get_neo4j_client()

# 프로젝트 전체 정보 조회
context = client.get_project_full_context("proj_abc123")

print(f"Project: {context['title']}")
print(f"Topic: {context['topic']}")
print(f"Platform: {context['platform']}")
print(f"Status: {context['status']}")
print(f"Persona: {context['persona_gender']} / {context['persona_tone']}")

print(f"\nScripts: {len(context['scripts'])} versions")
for script in context['scripts']:
    if script['script_id']:  # None 체크
        print(f"  - v{script['version']}: {script['content'][:50]}...")

print(f"\nVideos: {len(context['videos'])}")
for video in context['videos']:
    if video['video_id']:
        print(f"  - {video['file_path']} ({video['duration']}s)")

print(f"\nMetrics:")
for metric in context['metrics']:
    if metric['metrics_id']:
        print(f"  - Views: {metric['views']}, Score: {metric['performance_score']}")

client.close()
```

---

## 8. 커스텀 Cypher 쿼리

복잡한 쿼리는 직접 Cypher로 작성할 수 있습니다.

```python
from app.services.neo4j_client import get_neo4j_client

client = get_neo4j_client()

# 특정 플랫폼에서 가장 성과가 좋은 스크립트 패턴 조회
query = """
MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project {platform: $platform})
      -[:HAS_SCRIPT]->(s:Script)
      -[:GENERATED_AUDIO]->()-[:USED_IN_VIDEO]->(v:Video)
      -[:ACHIEVED]->(m:Metrics)
WHERE m.performance_score >= 75
RETURN s.content as script,
       proj.topic as topic,
       m.performance_score as score,
       m.engagement_rate as engagement
ORDER BY m.performance_score DESC
LIMIT 5
"""

results = client.query(query, {
    "user_id": "user_12345",
    "platform": "youtube"
})

for result in results:
    print(f"Topic: {result['topic']}")
    print(f"Score: {result['score']}")
    print(f"Script: {result['script'][:100]}...")
    print("-" * 50)

client.close()
```

---

## 9. 데이터베이스 통계 확인

```bash
# 데이터베이스 통계 조회
python scripts/init_neo4j.py --stats
```

출력 예시:
```
Database Statistics:
==================================================
User                :     1
Persona             :     1
Project             :     2
Script              :     3
Audio               :     1
Video               :     1
Metrics             :     3
==================================================
```

---

## 10. 모범 사례

### 10.1 연결 관리
```python
# 좋은 예: 싱글톤 사용
from app.services.neo4j_client import get_neo4j_client

client = get_neo4j_client()
# ... 작업 수행
client.close()

# 더 좋은 예: Context Manager (향후 구현 예정)
with get_neo4j_client() as client:
    # ... 작업 수행
    pass
```

### 10.2 에러 핸들링
```python
from app.services.neo4j_client import get_neo4j_client
import logging

logger = logging.getLogger(__name__)

try:
    client = get_neo4j_client()
    result = client.query("MATCH (u:User {user_id: $user_id}) RETURN u", {
        "user_id": "user_12345"
    })
except Exception as e:
    logger.error(f"Neo4j query failed: {e}")
    raise
finally:
    client.close()
```

### 10.3 성능 최적화
```python
# 인덱스를 활용한 쿼리
query = """
MATCH (u:User {user_id: $user_id})  # user_id는 인덱스됨
RETURN u
"""

# 불필요한 데이터 조회 방지
query = """
MATCH (proj:Project {project_id: $project_id})
RETURN proj.title, proj.status  # 필요한 필드만 반환
"""
```

---

## 11. 트러블슈팅

### 11.1 연결 오류
```
Error: Failed to connect to Neo4j
```

**해결 방법**:
1. Neo4j가 실행 중인지 확인: `docker ps | grep neo4j`
2. `.env` 파일의 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 확인
3. 방화벽 설정 확인

### 11.2 스키마 오류
```
Error: Constraint already exists
```

**해결 방법**:
```bash
# 기존 스키마 확인
python scripts/init_neo4j.py --stats

# 필요시 초기화
python scripts/init_neo4j.py --reset
```

---

## 12. 관련 문서

- [NEO4J_SCHEMA.md](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/backend/docs/NEO4J_SCHEMA.md) - 전체 스키마 설계
- [CLAUDE.md](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/CLAUDE.md) - 프로젝트 개요
- [RALPLAN.md](/Volumes/Extreme SSD/02_GitHub.nosync/30_OmniVibePro/RALPLAN.md) - 개발 로드맵

---

**작성일**: 2026-02-02
**버전**: 1.0
