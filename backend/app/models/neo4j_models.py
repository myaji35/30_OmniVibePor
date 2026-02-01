"""Neo4j GraphRAG 데이터 모델 및 CRUD 클래스"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import uuid


# ==================== Enums ====================

class SubscriptionTier(str, Enum):
    """구독 등급"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Gender(str, Enum):
    """성별"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class Tone(str, Enum):
    """어조"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENERGETIC = "energetic"
    CALM = "calm"


class ContentStyle(str, Enum):
    """콘텐츠 스타일"""
    EDUCATION = "교육"
    ENTERTAINMENT = "엔터테인먼트"
    NEWS = "뉴스"
    REVIEW = "리뷰"


class Platform(str, Enum):
    """플랫폼"""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class ProjectStatus(str, Enum):
    """프로젝트 상태"""
    DRAFT = "draft"
    SCRIPT_READY = "script_ready"
    PRODUCTION = "production"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ==================== Pydantic Models ====================

class UserModel(BaseModel):
    """사용자 모델"""
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PersonaModel(BaseModel):
    """페르소나 모델"""
    persona_id: str = Field(default_factory=lambda: f"persona_{uuid.uuid4().hex[:12]}")
    gender: Gender
    tone: Tone
    style: ContentStyle
    voice_id: str
    character_reference_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProjectModel(BaseModel):
    """프로젝트 모델"""
    project_id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    title: str
    topic: str
    platform: Platform
    status: ProjectStatus = ProjectStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    publish_scheduled_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScriptModel(BaseModel):
    """스크립트 모델"""
    script_id: str = Field(default_factory=lambda: f"script_{uuid.uuid4().hex[:12]}")
    content: str
    platform: Platform
    word_count: int
    estimated_duration: int  # 초 단위
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioModel(BaseModel):
    """오디오 모델"""
    audio_id: str = Field(default_factory=lambda: f"audio_{uuid.uuid4().hex[:12]}")
    file_path: str
    voice_id: str
    duration: float
    stt_accuracy: float
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VideoModel(BaseModel):
    """비디오 모델"""
    video_id: str = Field(default_factory=lambda: f"video_{uuid.uuid4().hex[:12]}")
    file_path: str
    duration: float
    resolution: str
    format: str
    veo_prompt: str
    lipsync_enabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThumbnailModel(BaseModel):
    """썸네일 모델"""
    thumbnail_id: str = Field(default_factory=lambda: f"thumb_{uuid.uuid4().hex[:12]}")
    file_url: str
    prompt: str
    platform: Platform
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsModel(BaseModel):
    """성과 메트릭 모델"""
    metrics_id: str = Field(default_factory=lambda: f"metrics_{uuid.uuid4().hex[:12]}")
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    watch_time: int = 0  # 초 단위
    engagement_rate: float = 0.0
    ctr: float = 0.0
    performance_score: float = 0.0
    measured_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomVoiceModel(BaseModel):
    """커스텀 음성 모델"""
    voice_id: str
    name: str
    description: str = ""
    file_path: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== Neo4j CRUD Manager ====================

class Neo4jCRUDManager:
    """Neo4j CRUD 작업 매니저"""

    def __init__(self, neo4j_client):
        """
        Args:
            neo4j_client: Neo4jClient 인스턴스
        """
        self.client = neo4j_client

    # ==================== User CRUD ====================

    def create_user(self, user: UserModel) -> Dict:
        """사용자 생성"""
        query = """
        CREATE (u:User {
            user_id: $user_id,
            email: $email,
            name: $name,
            created_at: datetime($created_at),
            subscription_tier: $subscription_tier
        })
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.created_at as created_at,
               u.subscription_tier as subscription_tier
        """
        result = self.client.query(query, user.model_dump())
        return result[0] if result else {}

    def get_user(self, user_id: str) -> Optional[Dict]:
        """사용자 조회"""
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u.user_id as user_id,
               u.email as email,
               u.name as name,
               u.created_at as created_at,
               u.subscription_tier as subscription_tier
        """
        result = self.client.query(query, {"user_id": user_id})
        return result[0] if result else None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """사용자 정보 업데이트"""
        set_clauses = ", ".join([f"u.{key} = ${key}" for key in updates.keys()])
        query = f"""
        MATCH (u:User {{user_id: $user_id}})
        SET {set_clauses}
        RETURN u.user_id as user_id
        """
        params = {"user_id": user_id, **updates}
        result = self.client.query(query, params)
        return len(result) > 0

    def delete_user(self, user_id: str) -> bool:
        """사용자 삭제 (모든 관계 포함)"""
        query = """
        MATCH (u:User {user_id: $user_id})
        DETACH DELETE u
        RETURN count(u) as deleted_count
        """
        result = self.client.query(query, {"user_id": user_id})
        return result[0]["deleted_count"] > 0 if result else False

    # ==================== Persona CRUD ====================

    def create_persona(self, user_id: str, persona: PersonaModel) -> Dict:
        """페르소나 생성 및 사용자 연결"""
        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (p:Persona {
            persona_id: $persona_id,
            gender: $gender,
            tone: $tone,
            style: $style,
            voice_id: $voice_id,
            character_reference_url: $character_reference_url,
            created_at: datetime($created_at)
        })
        CREATE (u)-[:HAS_PERSONA]->(p)
        RETURN p.persona_id as persona_id,
               p.gender as gender,
               p.tone as tone,
               p.style as style,
               p.voice_id as voice_id,
               p.created_at as created_at
        """
        params = {"user_id": user_id, **persona.model_dump()}
        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_user_personas(self, user_id: str) -> List[Dict]:
        """사용자의 모든 페르소나 조회"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_PERSONA]->(p:Persona)
        RETURN p.persona_id as persona_id,
               p.gender as gender,
               p.tone as tone,
               p.style as style,
               p.voice_id as voice_id,
               p.character_reference_url as character_reference_url,
               p.created_at as created_at
        ORDER BY p.created_at DESC
        """
        return self.client.query(query, {"user_id": user_id})

    def get_persona(self, persona_id: str) -> Optional[Dict]:
        """페르소나 조회"""
        query = """
        MATCH (p:Persona {persona_id: $persona_id})
        RETURN p.persona_id as persona_id,
               p.gender as gender,
               p.tone as tone,
               p.style as style,
               p.voice_id as voice_id,
               p.character_reference_url as character_reference_url,
               p.created_at as created_at
        """
        result = self.client.query(query, {"persona_id": persona_id})
        return result[0] if result else None

    def delete_persona(self, persona_id: str) -> bool:
        """페르소나 삭제"""
        query = """
        MATCH (p:Persona {persona_id: $persona_id})
        DETACH DELETE p
        RETURN count(p) as deleted_count
        """
        result = self.client.query(query, {"persona_id": persona_id})
        return result[0]["deleted_count"] > 0 if result else False

    # ==================== Project CRUD ====================

    def create_project(self, user_id: str, project: ProjectModel, persona_id: Optional[str] = None) -> Dict:
        """프로젝트 생성"""
        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (proj:Project {
            project_id: $project_id,
            title: $title,
            topic: $topic,
            platform: $platform,
            status: $status,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            publish_scheduled_at: datetime($publish_scheduled_at)
        })
        CREATE (u)-[:OWNS]->(proj)
        """

        params = {"user_id": user_id, **project.model_dump()}

        # 페르소나 연결
        if persona_id:
            query += """
            WITH proj
            MATCH (p:Persona {persona_id: $persona_id})
            CREATE (proj)-[:USES_PERSONA]->(p)
            """
            params["persona_id"] = persona_id

        query += """
        RETURN proj.project_id as project_id,
               proj.title as title,
               proj.topic as topic,
               proj.platform as platform,
               proj.status as status,
               proj.created_at as created_at,
               proj.updated_at as updated_at,
               proj.publish_scheduled_at as publish_scheduled_at
        """

        result = self.client.query(query, params)
        if result:
            # Neo4j DateTime을 Python datetime으로 변환
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            if row.get('publish_scheduled_at'):
                row['publish_scheduled_at'] = row['publish_scheduled_at'].to_native()
            return row
        return {}

    def get_project(self, project_id: str) -> Optional[Dict]:
        """프로젝트 조회"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        OPTIONAL MATCH (proj)-[:USES_PERSONA]->(p:Persona)
        RETURN proj.project_id as project_id,
               proj.title as title,
               proj.topic as topic,
               proj.platform as platform,
               proj.status as status,
               proj.created_at as created_at,
               proj.updated_at as updated_at,
               proj.publish_scheduled_at as publish_scheduled_at,
               p.persona_id as persona_id
        """
        result = self.client.query(query, {"project_id": project_id})
        if result:
            # Neo4j DateTime을 Python datetime으로 변환
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            if row.get('publish_scheduled_at'):
                row['publish_scheduled_at'] = row['publish_scheduled_at'].to_native()
            return row
        return None

    def get_user_projects(self, user_id: str, status: Optional[ProjectStatus] = None) -> List[Dict]:
        """사용자의 프로젝트 목록 조회"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
        """

        if status:
            query += "WHERE proj.status = $status "

        query += """
        OPTIONAL MATCH (proj)-[:USES_PERSONA]->(p:Persona)
        RETURN proj.project_id as project_id,
               proj.title as title,
               proj.topic as topic,
               proj.platform as platform,
               proj.status as status,
               proj.created_at as created_at,
               proj.updated_at as updated_at,
               p.persona_id as persona_id
        ORDER BY proj.created_at DESC
        """

        params = {"user_id": user_id}
        if status:
            params["status"] = status.value

        results = self.client.query(query, params)
        # Neo4j DateTime을 Python datetime으로 변환
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
        return results

    def update_project_status(self, project_id: str, status: ProjectStatus) -> bool:
        """프로젝트 상태 업데이트"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        SET proj.status = $status,
            proj.updated_at = datetime()
        RETURN proj.project_id as project_id
        """
        result = self.client.query(query, {"project_id": project_id, "status": status.value})
        return len(result) > 0

    def delete_project(self, project_id: str) -> bool:
        """프로젝트 삭제 (모든 관련 노드 및 관계 포함)"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        OPTIONAL MATCH (proj)-[*]->(related)
        DETACH DELETE proj, related
        RETURN count(proj) as deleted_count
        """
        result = self.client.query(query, {"project_id": project_id})
        return result[0]["deleted_count"] > 0 if result else False

    # ==================== Script CRUD ====================

    def create_script(self, project_id: str, script: ScriptModel, selected: bool = False) -> Dict:
        """스크립트 생성 및 프로젝트 연결"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        CREATE (s:Script {
            script_id: $script_id,
            content: $content,
            platform: $platform,
            word_count: $word_count,
            estimated_duration: $estimated_duration,
            version: $version,
            created_at: datetime($created_at)
        })
        CREATE (proj)-[:HAS_SCRIPT {selected: $selected}]->(s)
        RETURN s.script_id as script_id,
               s.content as content,
               s.platform as platform,
               s.word_count as word_count,
               s.estimated_duration as estimated_duration,
               s.version as version,
               s.created_at as created_at
        """
        params = {"project_id": project_id, "selected": selected, **script.model_dump()}
        result = self.client.query(query, params)
        if result:
            # Neo4j DateTime을 Python datetime으로 변환
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            return row
        return {}

    def get_project_scripts(self, project_id: str) -> List[Dict]:
        """프로젝트의 모든 스크립트 조회"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[r:HAS_SCRIPT]->(s:Script)
        RETURN s.script_id as script_id,
               s.content as content,
               s.platform as platform,
               s.word_count as word_count,
               s.estimated_duration as estimated_duration,
               s.version as version,
               s.created_at as created_at,
               r.selected as selected
        ORDER BY s.version DESC
        """
        results = self.client.query(query, {"project_id": project_id})
        # Neo4j DateTime을 Python datetime으로 변환
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
        return results

    def select_script(self, project_id: str, script_id: str) -> bool:
        """스크립트 선택 (다른 스크립트는 선택 해제)"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[r:HAS_SCRIPT]->(:Script)
        SET r.selected = false
        WITH proj
        MATCH (proj)-[r2:HAS_SCRIPT]->(s:Script {script_id: $script_id})
        SET r2.selected = true
        RETURN s.script_id as script_id
        """
        result = self.client.query(query, {"project_id": project_id, "script_id": script_id})
        return len(result) > 0

    # ==================== Audio CRUD ====================

    def create_audio(self, script_id: str, audio: AudioModel) -> Dict:
        """오디오 생성 및 스크립트 연결"""
        query = """
        MATCH (s:Script {script_id: $script_id})
        CREATE (a:Audio {
            audio_id: $audio_id,
            file_path: $file_path,
            voice_id: $voice_id,
            duration: $duration,
            stt_accuracy: $stt_accuracy,
            retry_count: $retry_count,
            created_at: datetime($created_at)
        })
        CREATE (s)-[:GENERATED_AUDIO]->(a)
        RETURN a.audio_id as audio_id,
               a.file_path as file_path,
               a.duration as duration,
               a.stt_accuracy as stt_accuracy,
               a.retry_count as retry_count,
               a.created_at as created_at
        """
        params = {"script_id": script_id, **audio.model_dump()}
        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_script_audios(self, script_id: str) -> List[Dict]:
        """스크립트의 모든 오디오 조회"""
        query = """
        MATCH (s:Script {script_id: $script_id})-[:GENERATED_AUDIO]->(a:Audio)
        RETURN a.audio_id as audio_id,
               a.file_path as file_path,
               a.voice_id as voice_id,
               a.duration as duration,
               a.stt_accuracy as stt_accuracy,
               a.retry_count as retry_count,
               a.created_at as created_at
        ORDER BY a.created_at DESC
        """
        return self.client.query(query, {"script_id": script_id})

    # ==================== Video CRUD ====================

    def create_video(self, project_id: str, audio_id: str, video: VideoModel) -> Dict:
        """비디오 생성 및 프로젝트, 오디오 연결"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        MATCH (a:Audio {audio_id: $audio_id})
        CREATE (v:Video {
            video_id: $video_id,
            file_path: $file_path,
            duration: $duration,
            resolution: $resolution,
            format: $format,
            veo_prompt: $veo_prompt,
            lipsync_enabled: $lipsync_enabled,
            created_at: datetime($created_at)
        })
        CREATE (proj)-[:HAS_VIDEO]->(v)
        CREATE (a)-[:USED_IN_VIDEO]->(v)
        RETURN v.video_id as video_id,
               v.file_path as file_path,
               v.duration as duration,
               v.resolution as resolution,
               v.format as format,
               v.created_at as created_at
        """
        params = {"project_id": project_id, "audio_id": audio_id, **video.model_dump()}
        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_project_videos(self, project_id: str) -> List[Dict]:
        """프로젝트의 모든 비디오 조회"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[:HAS_VIDEO]->(v:Video)
        RETURN v.video_id as video_id,
               v.file_path as file_path,
               v.duration as duration,
               v.resolution as resolution,
               v.format as format,
               v.veo_prompt as veo_prompt,
               v.lipsync_enabled as lipsync_enabled,
               v.created_at as created_at
        ORDER BY v.created_at DESC
        """
        return self.client.query(query, {"project_id": project_id})

    # ==================== Metrics CRUD ====================

    def create_metrics(self, video_id: str, metrics: MetricsModel) -> Dict:
        """메트릭 생성 및 비디오 연결"""
        query = """
        MATCH (v:Video {video_id: $video_id})
        CREATE (m:Metrics {
            metrics_id: $metrics_id,
            views: $views,
            likes: $likes,
            comments: $comments,
            shares: $shares,
            watch_time: $watch_time,
            engagement_rate: $engagement_rate,
            ctr: $ctr,
            performance_score: $performance_score,
            measured_at: datetime($measured_at)
        })
        CREATE (v)-[:ACHIEVED]->(m)
        RETURN m.metrics_id as metrics_id,
               m.views as views,
               m.performance_score as performance_score,
               m.measured_at as measured_at
        """
        params = {"video_id": video_id, **metrics.model_dump()}
        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_video_metrics(self, video_id: str) -> List[Dict]:
        """비디오의 모든 메트릭 조회 (시계열)"""
        query = """
        MATCH (v:Video {video_id: $video_id})-[:ACHIEVED]->(m:Metrics)
        RETURN m.metrics_id as metrics_id,
               m.views as views,
               m.likes as likes,
               m.comments as comments,
               m.shares as shares,
               m.watch_time as watch_time,
               m.engagement_rate as engagement_rate,
               m.ctr as ctr,
               m.performance_score as performance_score,
               m.measured_at as measured_at
        ORDER BY m.measured_at DESC
        """
        return self.client.query(query, {"video_id": video_id})

    def update_metrics(self, metrics_id: str, updates: Dict[str, Any]) -> bool:
        """메트릭 업데이트"""
        set_clauses = ", ".join([f"m.{key} = ${key}" for key in updates.keys()])
        query = f"""
        MATCH (m:Metrics {{metrics_id: $metrics_id}})
        SET {set_clauses}
        RETURN m.metrics_id as metrics_id
        """
        params = {"metrics_id": metrics_id, **updates}
        result = self.client.query(query, params)
        return len(result) > 0

    # ==================== Analytics Queries ====================

    def get_user_performance_summary(self, user_id: str, days: int = 30) -> Dict:
        """사용자 성과 요약 (최근 N일)"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
              -[:HAS_VIDEO]->(v:Video)
              -[:ACHIEVED]->(m:Metrics)
        WHERE datetime() - m.measured_at <= duration({days: $days})
        RETURN count(DISTINCT v) as total_videos,
               sum(m.views) as total_views,
               avg(m.engagement_rate) as avg_engagement,
               avg(m.performance_score) as avg_performance_score,
               max(m.performance_score) as best_performance_score
        """
        result = self.client.query(query, {"user_id": user_id, "days": days})
        return result[0] if result else {}

    def get_platform_analytics(self, user_id: str) -> List[Dict]:
        """플랫폼별 성과 분석"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
              -[:HAS_VIDEO]->(v:Video)
              -[:ACHIEVED]->(m:Metrics)
        RETURN proj.platform as platform,
               count(DISTINCT v) as total_videos,
               avg(m.views) as avg_views,
               avg(m.engagement_rate) as avg_engagement,
               avg(m.performance_score) as avg_score
        ORDER BY avg_score DESC
        """
        return self.client.query(query, {"user_id": user_id})

    def get_high_performance_patterns(
        self,
        user_id: str,
        min_score: float = 70.0,
        limit: int = 10
    ) -> List[Dict]:
        """고성과 스크립트 패턴 분석"""
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
              -[:HAS_SCRIPT]->(s:Script)
              -[:GENERATED_AUDIO]->()-[:USED_IN_VIDEO]->(v:Video)
              -[:ACHIEVED]->(m:Metrics)
        WHERE m.performance_score >= $min_score
        RETURN s.script_id as script_id,
               s.content as content,
               proj.topic as topic,
               proj.platform as platform,
               m.performance_score as score,
               m.engagement_rate as engagement
        ORDER BY m.performance_score DESC
        LIMIT $limit
        """
        return self.client.query(query, {
            "user_id": user_id,
            "min_score": min_score,
            "limit": limit
        })
