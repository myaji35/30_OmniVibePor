# Neo4j GraphRAG Schema Design

**프로젝트**: OmniVibe Pro
**버전**: 1.0
**작성일**: 2026-02-02
**목적**: 사용자 페르소나, 프로젝트 히스토리, 성과 메트릭을 그래프로 저장하여 AI 에이전트의 컨텍스트 학습

---

## 1. 노드 타입 (Node Types)

### 1.1 User (사용자)
사용자 계정 정보를 저장합니다.

**속성 (Properties)**:
- `user_id` (string, unique): 사용자 고유 ID
- `email` (string): 이메일
- `name` (string): 사용자 이름
- `created_at` (datetime): 계정 생성일
- `subscription_tier` (string): 구독 등급 (free, pro, enterprise)

**인덱스**:
```cypher
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
```

---

### 1.2 Persona (페르소나)
사용자의 콘텐츠 제작 페르소나 정보입니다.

**속성**:
- `persona_id` (string, unique): 페르소나 고유 ID
- `gender` (string): 성별 (male, female, neutral)
- `tone` (string): 어조 (professional, casual, energetic, calm)
- `style` (string): 스타일 (교육, 엔터테인먼트, 뉴스, 리뷰)
- `voice_id` (string): ElevenLabs 음성 ID
- `character_reference_url` (string): Nano Banana 캐릭터 이미지 URL
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE CONSTRAINT persona_id_unique IF NOT EXISTS FOR (p:Persona) REQUIRE p.persona_id IS UNIQUE;
```

---

### 1.3 Project (프로젝트)
사용자의 영상 제작 프로젝트입니다.

**속성**:
- `project_id` (string, unique): 프로젝트 고유 ID
- `title` (string): 프로젝트 제목
- `topic` (string): 주제
- `platform` (string): 타겟 플랫폼 (youtube, instagram, facebook)
- `status` (string): 상태 (draft, script_ready, production, published)
- `created_at` (datetime): 생성일
- `updated_at` (datetime): 수정일
- `publish_scheduled_at` (datetime): 예정 발행일

**인덱스**:
```cypher
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE;
CREATE INDEX project_created IF NOT EXISTS FOR (p:Project) ON (p.created_at);
CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status);
```

---

### 1.4 Script (스크립트)
Writer 에이전트가 생성한 스크립트입니다.

**속성**:
- `script_id` (string, unique): 스크립트 고유 ID
- `content` (string): 스크립트 전문
- `platform` (string): 최적화된 플랫폼
- `word_count` (int): 단어 수
- `estimated_duration` (int): 예상 재생 시간 (초)
- `version` (int): 버전 번호 (1, 2, 3...)
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE CONSTRAINT script_id_unique IF NOT EXISTS FOR (s:Script) REQUIRE s.script_id IS UNIQUE;
```

---

### 1.5 Audio (오디오)
Director 에이전트가 생성한 TTS 오디오입니다.

**속성**:
- `audio_id` (string, unique): 오디오 고유 ID
- `file_path` (string): 저장 경로 (S3/Cloudinary URL)
- `voice_id` (string): 사용된 ElevenLabs 음성 ID
- `duration` (float): 재생 시간 (초)
- `stt_accuracy` (float): Whisper STT 검증 정확도 (0.0 ~ 1.0)
- `retry_count` (int): 재생성 시도 횟수
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE CONSTRAINT audio_id_unique IF NOT EXISTS FOR (a:Audio) REQUIRE a.audio_id IS UNIQUE;
```

---

### 1.6 Video (비디오)
Director 에이전트가 생성한 최종 영상입니다.

**속성**:
- `video_id` (string, unique): 비디오 고유 ID
- `file_path` (string): 저장 경로
- `duration` (float): 재생 시간 (초)
- `resolution` (string): 해상도 (1920x1080, 1080x1920 등)
- `format` (string): 파일 포맷 (mp4, webm)
- `veo_prompt` (string): Google Veo 생성 프롬프트
- `lipsync_enabled` (boolean): 립싱크 적용 여부
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:Video) REQUIRE v.video_id IS UNIQUE;
```

---

### 1.7 Thumbnail (썸네일)
Marketer 에이전트가 생성한 썸네일 이미지입니다.

**속성**:
- `thumbnail_id` (string, unique): 썸네일 고유 ID
- `file_url` (string): 이미지 URL
- `prompt` (string): DALL-E 생성 프롬프트
- `platform` (string): 최적화된 플랫폼
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE CONSTRAINT thumbnail_id_unique IF NOT EXISTS FOR (t:Thumbnail) REQUIRE t.thumbnail_id IS UNIQUE;
```

---

### 1.8 Metrics (성과 메트릭)
발행된 콘텐츠의 성과 데이터입니다.

**속성**:
- `metrics_id` (string, unique): 메트릭 고유 ID
- `views` (int): 조회수
- `likes` (int): 좋아요 수
- `comments` (int): 댓글 수
- `shares` (int): 공유 수
- `watch_time` (int): 총 시청 시간 (초)
- `engagement_rate` (float): 참여율 (0.0 ~ 1.0)
- `ctr` (float): 클릭률 (0.0 ~ 1.0)
- `performance_score` (float): 종합 성과 점수 (0 ~ 100)
- `measured_at` (datetime): 측정일

**인덱스**:
```cypher
CREATE INDEX metrics_performance IF NOT EXISTS FOR (m:Metrics) ON (m.performance_score);
CREATE INDEX metrics_measured IF NOT EXISTS FOR (m:Metrics) ON (m.measured_at);
```

---

### 1.9 CustomVoice (커스텀 음성)
사용자가 업로드한 커스텀 음성 클론 정보입니다.

**속성**:
- `voice_id` (string, unique): ElevenLabs voice_id
- `name` (string): 음성 이름
- `description` (string): 설명
- `file_path` (string): 원본 오디오 파일 경로
- `created_at` (datetime): 생성일
- `metadata` (map): 추가 메타데이터 (JSON)

**인덱스**:
```cypher
CREATE CONSTRAINT custom_voice_id_unique IF NOT EXISTS FOR (cv:CustomVoice) REQUIRE cv.voice_id IS UNIQUE;
```

---

### 1.10 Content (레거시 콘텐츠)
과거 성과 데이터를 저장한 기존 콘텐츠 노드입니다.

**속성**:
- `content_id` (string, unique): 콘텐츠 고유 ID
- `title` (string): 제목
- `platform` (string): 플랫폼
- `created_at` (datetime): 생성일

**인덱스**:
```cypher
CREATE INDEX content_id IF NOT EXISTS FOR (c:Content) ON (c.content_id);
```

---

## 2. 관계 타입 (Relationship Types)

### 2.1 User ↔ Persona
```
(User)-[:HAS_PERSONA]->(Persona)
```
**의미**: 사용자가 소유한 페르소나
**속성**: 없음

---

### 2.2 User ↔ Project
```
(User)-[:OWNS]->(Project)
```
**의미**: 사용자가 소유한 프로젝트
**속성**: 없음

---

### 2.3 Project ↔ Persona
```
(Project)-[:USES_PERSONA]->(Persona)
```
**의미**: 프로젝트에서 사용하는 페르소나
**속성**: 없음

---

### 2.4 Project ↔ Script
```
(Project)-[:HAS_SCRIPT]->(Script)
```
**의미**: 프로젝트의 스크립트
**속성**:
- `selected` (boolean): 최종 선택된 스크립트 여부

---

### 2.5 Script ↔ Audio
```
(Script)-[:GENERATED_AUDIO]->(Audio)
```
**의미**: 스크립트로부터 생성된 오디오
**속성**: 없음

---

### 2.6 Audio ↔ Video
```
(Audio)-[:USED_IN_VIDEO]->(Video)
```
**의미**: 비디오에 사용된 오디오
**속성**: 없음

---

### 2.7 Project ↔ Video
```
(Project)-[:HAS_VIDEO]->(Video)
```
**의미**: 프로젝트의 최종 영상
**속성**: 없음

---

### 2.8 Project ↔ Thumbnail
```
(Project)-[:HAS_THUMBNAIL]->(Thumbnail)
```
**의미**: 프로젝트의 썸네일
**속성**: 없음

---

### 2.9 Video ↔ Metrics
```
(Video)-[:ACHIEVED]->(Metrics)
```
**의미**: 영상이 달성한 성과
**속성**: 없음

---

### 2.10 User ↔ CustomVoice
```
(User)-[:HAS_VOICE]->(CustomVoice)
```
**의미**: 사용자의 커스텀 음성
**속성**: 없음

---

### 2.11 User ↔ Content (레거시)
```
(User)-[:CREATED]->(Content)
(Content)-[:ACHIEVED]->(Metrics)
(Content)-[:HAS_THUMBNAIL]->(Thumbnail)
```
**의미**: 기존 성과 데이터 구조 (하위 호환)
**속성**: 없음

---

## 3. 그래프 구조 예시

### 3.1 완전한 프로젝트 워크플로우
```
(User:user123)
  ├─[:HAS_PERSONA]→(Persona:persona_abc)
  └─[:OWNS]→(Project:proj_001)
      ├─[:USES_PERSONA]→(Persona:persona_abc)
      ├─[:HAS_SCRIPT]→(Script:script_v1)
      │   └─[:GENERATED_AUDIO]→(Audio:audio_001)
      │       └─[:USED_IN_VIDEO]→(Video:video_final)
      ├─[:HAS_VIDEO]→(Video:video_final)
      │   └─[:ACHIEVED]→(Metrics:metrics_week1)
      └─[:HAS_THUMBNAIL]→(Thumbnail:thumb_001)
```

---

## 4. Cypher 쿼리 예제

### 4.1 스키마 생성 (Constraints & Indexes)
```cypher
-- User
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE INDEX user_email IF NOT EXISTS
FOR (u:User) ON (u.email);

-- Persona
CREATE CONSTRAINT persona_id_unique IF NOT EXISTS
FOR (p:Persona) REQUIRE p.persona_id IS UNIQUE;

-- Project
CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.project_id IS UNIQUE;

CREATE INDEX project_created IF NOT EXISTS
FOR (p:Project) ON (p.created_at);

CREATE INDEX project_status IF NOT EXISTS
FOR (p:Project) ON (p.status);

-- Script
CREATE CONSTRAINT script_id_unique IF NOT EXISTS
FOR (s:Script) REQUIRE s.script_id IS UNIQUE;

-- Audio
CREATE CONSTRAINT audio_id_unique IF NOT EXISTS
FOR (a:Audio) REQUIRE a.audio_id IS UNIQUE;

-- Video
CREATE CONSTRAINT video_id_unique IF NOT EXISTS
FOR (v:Video) REQUIRE v.video_id IS UNIQUE;

-- Thumbnail
CREATE CONSTRAINT thumbnail_id_unique IF NOT EXISTS
FOR (t:Thumbnail) REQUIRE t.thumbnail_id IS UNIQUE;

-- Metrics
CREATE INDEX metrics_performance IF NOT EXISTS
FOR (m:Metrics) ON (m.performance_score);

CREATE INDEX metrics_measured IF NOT EXISTS
FOR (m:Metrics) ON (m.measured_at);

-- CustomVoice
CREATE CONSTRAINT custom_voice_id_unique IF NOT EXISTS
FOR (cv:CustomVoice) REQUIRE cv.voice_id IS UNIQUE;

-- Content (레거시)
CREATE INDEX content_id IF NOT EXISTS
FOR (c:Content) ON (c.content_id);
```

---

### 4.2 사용자 및 페르소나 생성
```cypher
-- 사용자 생성
CREATE (u:User {
  user_id: "user_12345",
  email: "user@example.com",
  name: "홍길동",
  created_at: datetime(),
  subscription_tier: "pro"
})

-- 페르소나 생성 및 연결
CREATE (p:Persona {
  persona_id: "persona_abc",
  gender: "female",
  tone: "professional",
  style: "교육",
  voice_id: "21m00Tcm4TlvDq8ikWAM",
  character_reference_url: "https://cloudinary.com/char_ref.png",
  created_at: datetime()
})

MERGE (u:User {user_id: "user_12345"})
MERGE (p:Persona {persona_id: "persona_abc"})
CREATE (u)-[:HAS_PERSONA]->(p)
```

---

### 4.3 프로젝트 생성 및 워크플로우
```cypher
-- 프로젝트 생성
MERGE (u:User {user_id: $user_id})
CREATE (proj:Project {
  project_id: $project_id,
  title: "AI 트렌드 2026",
  topic: "인공지능",
  platform: "youtube",
  status: "draft",
  created_at: datetime(),
  updated_at: datetime(),
  publish_scheduled_at: datetime("2026-02-15T10:00:00Z")
})
CREATE (u)-[:OWNS]->(proj)

-- 페르소나 연결
MERGE (proj:Project {project_id: $project_id})
MERGE (p:Persona {persona_id: $persona_id})
CREATE (proj)-[:USES_PERSONA]->(p)

-- 스크립트 생성
CREATE (s:Script {
  script_id: $script_id,
  content: $script_content,
  platform: "youtube",
  word_count: 500,
  estimated_duration: 180,
  version: 1,
  created_at: datetime()
})
MERGE (proj:Project {project_id: $project_id})
CREATE (proj)-[:HAS_SCRIPT {selected: true}]->(s)

-- 오디오 생성
CREATE (a:Audio {
  audio_id: $audio_id,
  file_path: "s3://bucket/audio_001.mp3",
  voice_id: "21m00Tcm4TlvDq8ikWAM",
  duration: 185.5,
  stt_accuracy: 0.98,
  retry_count: 1,
  created_at: datetime()
})
MERGE (s:Script {script_id: $script_id})
CREATE (s)-[:GENERATED_AUDIO]->(a)

-- 비디오 생성
CREATE (v:Video {
  video_id: $video_id,
  file_path: "s3://bucket/video_final.mp4",
  duration: 190.0,
  resolution: "1920x1080",
  format: "mp4",
  veo_prompt: "Professional educator explaining AI trends in modern office",
  lipsync_enabled: true,
  created_at: datetime()
})
MERGE (proj:Project {project_id: $project_id})
MERGE (a:Audio {audio_id: $audio_id})
CREATE (proj)-[:HAS_VIDEO]->(v)
CREATE (a)-[:USED_IN_VIDEO]->(v)

-- 성과 데이터 저장
CREATE (m:Metrics {
  metrics_id: randomUUID(),
  views: 15000,
  likes: 850,
  comments: 120,
  shares: 45,
  watch_time: 2550000,
  engagement_rate: 0.067,
  ctr: 0.089,
  performance_score: 78.5,
  measured_at: datetime()
})
MERGE (v:Video {video_id: $video_id})
CREATE (v)-[:ACHIEVED]->(m)
```

---

### 4.4 Writer 에이전트 - 고성과 패턴 조회
```cypher
-- 사용자의 과거 고성과 스크립트 분석
MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
      -[:HAS_SCRIPT]->(s:Script)
      -[:GENERATED_AUDIO]->()-[:USED_IN_VIDEO]->(v:Video)
      -[:ACHIEVED]->(m:Metrics)
WHERE m.performance_score >= 70
RETURN s.content AS script_sample,
       proj.topic AS topic,
       proj.platform AS platform,
       m.performance_score AS score,
       m.engagement_rate AS engagement
ORDER BY m.performance_score DESC
LIMIT 10
```

---

### 4.5 Director 에이전트 - 오디오 품질 통계
```cypher
-- 사용자의 오디오 생성 품질 분석
MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
      -[:HAS_SCRIPT]->(s:Script)
      -[:GENERATED_AUDIO]->(a:Audio)
RETURN avg(a.stt_accuracy) AS avg_accuracy,
       avg(a.retry_count) AS avg_retries,
       count(a) AS total_audios,
       min(a.stt_accuracy) AS min_accuracy
```

---

### 4.6 Marketer 에이전트 - 플랫폼별 성과 분석
```cypher
-- 플랫폼별 평균 성과 조회
MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
      -[:HAS_VIDEO]->(v:Video)
      -[:ACHIEVED]->(m:Metrics)
RETURN proj.platform AS platform,
       count(v) AS total_videos,
       avg(m.views) AS avg_views,
       avg(m.engagement_rate) AS avg_engagement,
       avg(m.performance_score) AS avg_score
ORDER BY avg_score DESC
```

---

### 4.7 고성과 썸네일 패턴 분석
```cypher
-- 높은 CTR을 기록한 썸네일 패턴 조회
MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
      -[:HAS_THUMBNAIL]->(t:Thumbnail)
MATCH (proj)-[:HAS_VIDEO]->(v:Video)-[:ACHIEVED]->(m:Metrics)
WHERE m.ctr >= 0.08
RETURN t.file_url AS thumbnail_url,
       t.prompt AS prompt,
       proj.platform AS platform,
       m.ctr AS click_through_rate,
       m.views AS views
ORDER BY m.ctr DESC
LIMIT 5
```

---

### 4.8 커스텀 음성 관리
```cypher
-- 커스텀 음성 저장
MERGE (u:User {user_id: $user_id})
CREATE (cv:CustomVoice {
  voice_id: $voice_id,
  name: $name,
  description: $description,
  file_path: $file_path,
  created_at: datetime(),
  metadata: $metadata
})
CREATE (u)-[:HAS_VOICE]->(cv)

-- 커스텀 음성 조회
MATCH (u:User {user_id: $user_id})-[:HAS_VOICE]->(cv:CustomVoice)
RETURN cv.voice_id AS voice_id,
       cv.name AS name,
       cv.description AS description,
       cv.created_at AS created_at
ORDER BY cv.created_at DESC
```

---

## 5. 성능 최적화 전략

### 5.1 인덱스 활용 권장
- **User**: `user_id`, `email`에 인덱스
- **Project**: `created_at`, `status`에 인덱스
- **Metrics**: `performance_score`, `measured_at`에 인덱스

### 5.2 쿼리 최적화 패턴
```cypher
-- 나쁜 예: 전체 스캔
MATCH (u:User)-[:OWNS]->(p:Project)
WHERE u.user_id = "user_12345"
RETURN p

-- 좋은 예: 인덱스 활용
MATCH (u:User {user_id: "user_12345"})-[:OWNS]->(p:Project)
RETURN p
```

### 5.3 데이터 정리 정책
- **Metrics**: 6개월 이상 경과한 저성과 데이터 아카이빙
- **Audio/Video**: 프로젝트 완료 후 30일 경과 시 파일 경로만 유지

---

## 6. 확장 계획

### 6.1 향후 추가 노드
- `Deployment`: 자동 배포 기록
- `A/BTest`: A/B 테스트 결과
- `Audience`: 타겟 오디언스 세그먼트
- `Campaign`: 마케팅 캠페인

### 6.2 향후 추가 관계
- `(User)-[:FOLLOWS]->(User)`: 팀 협업
- `(Project)-[:VARIANT_OF]->(Project)`: 프로젝트 변형
- `(Video)-[:REMIX_OF]->(Video)`: 리믹스 추적

---

## 7. 백업 및 마이그레이션

### 7.1 데이터 백업
```bash
# Neo4j 덤프
neo4j-admin dump --database=neo4j --to=/backup/neo4j-$(date +%Y%m%d).dump

# 복원
neo4j-admin load --from=/backup/neo4j-20260202.dump --database=neo4j --force
```

### 7.2 스키마 마이그레이션
- 버전 관리: `app/migrations/neo4j/`에 Cypher 스크립트 저장
- 적용 순서: `001_initial_schema.cypher`, `002_add_custom_voice.cypher` 등

---

## 8. 보안 및 접근 제어

### 8.1 사용자 격리
```cypher
-- 사용자별 데이터 접근 제한
MATCH (u:User {user_id: $current_user_id})-[:OWNS]->(proj:Project)
RETURN proj
```

### 8.2 민감 정보 암호화
- `email`, `file_path` 등은 애플리케이션 레벨에서 암호화 권장
- Neo4j는 그래프 구조 저장에 집중

---

**문서 버전**: 1.0
**최종 수정일**: 2026-02-02
**작성자**: OmniVibe Pro Development Team
