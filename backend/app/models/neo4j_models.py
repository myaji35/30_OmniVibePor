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


class SectionType(str, Enum):
    """섹션 타입"""
    HOOK = "hook"
    BODY = "body"
    CTA = "cta"


class SectionModel(BaseModel):
    """콘티 섹션 모델"""
    section_id: str = Field(default_factory=lambda: f"section_{uuid.uuid4().hex[:12]}")
    type: SectionType
    order: int
    script: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    video_clip_path: Optional[str] = None
    audio_segment_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SectionMetadataModel(BaseModel):
    """섹션 메타데이터"""
    word_count: int
    estimated_duration: float
    actual_duration: float


class SectionDetailModel(BaseModel):
    """섹션 상세 정보"""
    section_id: str
    type: SectionType
    order: int
    script: str
    start_time: float
    end_time: float
    duration: float
    video_clip_path: Optional[str] = None
    audio_segment_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: SectionMetadataModel


class ProjectSectionsResponse(BaseModel):
    """프로젝트 섹션 응답"""
    project_id: str
    sections: List[SectionDetailModel]
    total_duration: float


# ==================== Clip Editor Models ====================

class ClipVariationType(str, Enum):
    """클립 변형 타입"""
    CAMERA_ANGLE = "camera_angle"
    LIGHTING = "lighting"
    COLOR_TONE = "color_tone"


class AlternativeClipModel(BaseModel):
    """대체 클립 모델"""
    clip_id: str = Field(default_factory=lambda: f"clip_{uuid.uuid4().hex[:12]}")
    video_path: str = ""
    thumbnail_url: str = ""
    prompt: str
    variation_type: ClipVariationType
    variation_description: str
    cloudinary_public_id: Optional[str] = None
    veo_job_id: Optional[str] = None
    status: str = "generating"  # generating, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CurrentClipResponse(BaseModel):
    """현재 클립 정보"""
    clip_id: str
    video_path: str
    thumbnail_url: str
    prompt: str
    created_at: str


class AlternativeClipResponse(BaseModel):
    """대체 클립 정보"""
    clip_id: str
    video_path: str
    thumbnail_url: str
    prompt: str
    variation: str
    created_at: str


class SectionAlternativeClipsResponse(BaseModel):
    """섹션 대체 클립 응답"""
    section_id: str
    current_clip: Optional[CurrentClipResponse] = None
    alternatives: List[AlternativeClipResponse] = Field(default_factory=list)


class GenerateAlternativeClipsRequest(BaseModel):
    """대체 클립 생성 요청"""
    base_prompt: Optional[str] = None
    variations: Optional[List[str]] = Field(
        default_factory=lambda: ["camera_angle", "lighting", "color_tone"]
    )


class SubtitleStyleModel(BaseModel):
    """자막 스타일 모델"""
    style_id: str = Field(default_factory=lambda: f"style_{uuid.uuid4().hex[:12]}")
    font_family: str = Field(default="Arial", description="폰트 패밀리")
    font_size: int = Field(default=24, ge=24, le=72, description="폰트 크기 (24-72)")
    font_color: str = Field(default="#FFFFFF", description="폰트 색상 (HEX)")
    background_color: str = Field(default="#000000", description="배경 색상 (HEX)")
    background_opacity: float = Field(default=0.7, ge=0.0, le=1.0, description="배경 투명도 (0.0-1.0)")
    position: str = Field(default="bottom", description="위치 (top/center/bottom)")
    vertical_offset: int = Field(default=0, ge=-100, le=100, description="수직 오프셋 (-100~100)")
    alignment: str = Field(default="center", description="정렬 (left/center/right)")
    outline_width: int = Field(default=1, ge=0, le=4, description="아웃라인 두께 (0-4)")
    outline_color: str = Field(default="#000000", description="아웃라인 색상 (HEX)")
    shadow_enabled: bool = Field(default=False, description="그림자 활성화")
    shadow_offset_x: int = Field(default=2, ge=-10, le=10, description="그림자 X 오프셋")
    shadow_offset_y: int = Field(default=2, ge=-10, le=10, description="그림자 Y 오프셋")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SubtitleStyleUpdateRequest(BaseModel):
    """자막 스타일 업데이트 요청"""
    font_family: Optional[str] = Field(None, description="폰트 패밀리")
    font_size: Optional[int] = Field(None, ge=24, le=72, description="폰트 크기 (24-72)")
    font_color: Optional[str] = Field(None, description="폰트 색상 (HEX)")
    background_color: Optional[str] = Field(None, description="배경 색상 (HEX)")
    background_opacity: Optional[float] = Field(None, ge=0.0, le=1.0, description="배경 투명도 (0.0-1.0)")
    position: Optional[str] = Field(None, description="위치 (top/center/bottom)")
    vertical_offset: Optional[int] = Field(None, ge=-100, le=100, description="수직 오프셋 (-100~100)")
    alignment: Optional[str] = Field(None, description="정렬 (left/center/right)")
    outline_width: Optional[int] = Field(None, ge=0, le=4, description="아웃라인 두께 (0-4)")
    outline_color: Optional[str] = Field(None, description="아웃라인 색상 (HEX)")
    shadow_enabled: Optional[bool] = Field(None, description="그림자 활성화")
    shadow_offset_x: Optional[int] = Field(None, ge=-10, le=10, description="그림자 X 오프셋")
    shadow_offset_y: Optional[int] = Field(None, ge=-10, le=10, description="그림자 Y 오프셋")


class SubtitlePreviewRequest(BaseModel):
    """자막 미리보기 요청"""
    start_time: float = Field(default=0.0, ge=0.0, description="시작 시간 (초)")
    duration: float = Field(default=5.0, ge=1.0, le=10.0, description="미리보기 길이 (1-10초)")
    style: Optional[SubtitleStyleUpdateRequest] = Field(None, description="적용할 스타일")


class SubtitleStyleResponse(BaseModel):
    """자막 스타일 응답"""
    project_id: str
    font_family: str
    font_size: int
    font_color: str
    background_color: str
    background_opacity: float
    position: str
    vertical_offset: int
    alignment: str
    outline_width: int
    outline_color: str
    shadow_enabled: bool
    shadow_offset_x: int
    shadow_offset_y: int
    srt_file_path: Optional[str] = None
    updated_at: Optional[datetime] = None


class SubtitlePreviewResponse(BaseModel):
    """자막 미리보기 응답"""
    project_id: str
    preview_url: str
    expires_at: datetime
    style: SubtitleStyleResponse


class ReplaceClipRequest(BaseModel):
    """클립 교체 요청"""
    new_clip_id: str


class BGMSettingsModel(BaseModel):
    """BGM 설정 모델"""
    bgm_file_path: str = Field(..., description="업로드된 BGM 파일 경로")
    volume: float = Field(default=0.3, ge=0.0, le=1.0, description="볼륨 (0.0-1.0)")
    fade_in_duration: float = Field(default=2.0, ge=0.0, le=10.0, description="페이드 인 길이 (초)")
    fade_out_duration: float = Field(default=2.0, ge=0.0, le=10.0, description="페이드 아웃 길이 (초)")
    start_time: float = Field(default=0.0, ge=0.0, description="BGM 시작 시간 (초)")
    end_time: Optional[float] = Field(default=None, ge=0.0, description="BGM 종료 시간 (null이면 끝까지)")
    loop: bool = Field(default=True, description="반복 재생 여부")
    ducking_enabled: bool = Field(default=True, description="음성 구간에서 BGM 볼륨 자동 감소")
    ducking_level: float = Field(default=0.3, ge=0.1, le=0.5, description="덕킹 시 볼륨 레벨 (0.1-0.5)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BGMUpdateRequest(BaseModel):
    """BGM 설정 업데이트 요청"""
    volume: Optional[float] = Field(None, ge=0.0, le=1.0, description="볼륨 (0.0-1.0)")
    fade_in_duration: Optional[float] = Field(None, ge=0.0, le=10.0, description="페이드 인 길이 (초)")
    fade_out_duration: Optional[float] = Field(None, ge=0.0, le=10.0, description="페이드 아웃 길이 (초)")
    start_time: Optional[float] = Field(None, ge=0.0, description="BGM 시작 시간 (초)")
    end_time: Optional[float] = Field(None, description="BGM 종료 시간 (null이면 끝까지)")
    loop: Optional[bool] = Field(None, description="반복 재생 여부")
    ducking_enabled: Optional[bool] = Field(None, description="음성 구간에서 BGM 볼륨 자동 감소")
    ducking_level: Optional[float] = Field(None, ge=0.1, le=0.5, description="덕킹 시 볼륨 레벨 (0.1-0.5)")


class BGMInfoResponse(BaseModel):
    """BGM 정보 응답"""
    project_id: str
    bgm_file_path: str
    volume: float
    fade_in_duration: float
    fade_out_duration: float
    start_time: float
    end_time: Optional[float]
    loop: bool
    ducking_enabled: bool
    ducking_level: float
    created_at: datetime
    updated_at: datetime


# ==================== Custom Preset Models ====================

class VideoSettingsModel(BaseModel):
    """비디오 설정 모델"""
    resolution: Dict[str, int] = Field(
        default={"width": 1920, "height": 1080},
        description="해상도"
    )
    aspect_ratio: str = Field(default="16:9", description="종횡비")
    frame_rate: int = Field(default=30, ge=24, le=60, description="프레임레이트 (24-60)")
    bitrate: int = Field(default=5000, ge=1000, le=50000, description="비트레이트 (kbps)")
    transition_style: str = Field(default="fade", description="전환 스타일")
    color_grading: str = Field(default="natural", description="컬러 그레이딩")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomPresetModel(BaseModel):
    """커스텀 프리셋 모델"""
    preset_id: str = Field(default_factory=lambda: f"preset_{uuid.uuid4().hex[:12]}")
    user_id: str
    name: str = Field(..., min_length=1, max_length=100, description="프리셋 이름")
    description: Optional[str] = Field(None, max_length=500, description="프리셋 설명")
    subtitle_style: SubtitleStyleModel = Field(..., description="자막 스타일")
    bgm_settings: BGMSettingsModel = Field(..., description="BGM 설정")
    video_settings: VideoSettingsModel = Field(
        default_factory=VideoSettingsModel,
        description="비디오 설정"
    )
    is_favorite: bool = Field(default=False, description="즐겨찾기 여부")
    usage_count: int = Field(default=0, ge=0, description="사용 횟수")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomPresetCreateRequest(BaseModel):
    """커스텀 프리셋 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100, description="프리셋 이름")
    description: Optional[str] = Field(None, max_length=500, description="프리셋 설명")
    subtitle_style: Optional[SubtitleStyleModel] = Field(None, description="자막 스타일")
    bgm_settings: Optional[BGMSettingsModel] = Field(None, description="BGM 설정")
    video_settings: Optional[VideoSettingsModel] = Field(None, description="비디오 설정")
    is_favorite: bool = Field(default=False, description="즐겨찾기 여부")


class CustomPresetUpdateRequest(BaseModel):
    """커스텀 프리셋 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="프리셋 이름")
    description: Optional[str] = Field(None, max_length=500, description="프리셋 설명")
    subtitle_style: Optional[SubtitleStyleModel] = Field(None, description="자막 스타일")
    bgm_settings: Optional[BGMSettingsModel] = Field(None, description="BGM 설정")
    video_settings: Optional[VideoSettingsModel] = Field(None, description="비디오 설정")
    is_favorite: Optional[bool] = Field(None, description="즐겨찾기 여부")


class CustomPresetResponse(BaseModel):
    """커스텀 프리셋 응답"""
    preset_id: str
    user_id: str
    name: str
    description: Optional[str]
    subtitle_style: Dict[str, Any]
    bgm_settings: Dict[str, Any]
    video_settings: Dict[str, Any]
    is_favorite: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CustomPresetListResponse(BaseModel):
    """커스텀 프리셋 목록 응답"""
    presets: List[CustomPresetResponse]
    total: int


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

    # ==================== Clip Editor CRUD ====================

    def create_alternative_clip(
        self,
        section_id: str,
        clip: AlternativeClipModel
    ) -> Dict:
        """대체 클립 생성 및 섹션 연결"""
        query = """
        MATCH (s:Section {section_id: $section_id})
        CREATE (c:AlternativeClip {
            clip_id: $clip_id,
            video_path: $video_path,
            thumbnail_url: $thumbnail_url,
            prompt: $prompt,
            variation_type: $variation_type,
            variation_description: $variation_description,
            cloudinary_public_id: $cloudinary_public_id,
            veo_job_id: $veo_job_id,
            status: $status,
            created_at: datetime($created_at)
        })
        CREATE (s)-[:HAS_ALTERNATIVE_CLIP]->(c)
        RETURN c.clip_id as clip_id,
               c.video_path as video_path,
               c.thumbnail_url as thumbnail_url,
               c.prompt as prompt,
               c.variation_type as variation_type,
               c.variation_description as variation_description,
               c.status as status,
               c.created_at as created_at
        """
        params = {"section_id": section_id, **clip.model_dump()}
        result = self.client.query(query, params)
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            return row
        return {}

    def get_section_alternative_clips(self, section_id: str) -> List[Dict]:
        """섹션의 모든 대체 클립 조회"""
        query = """
        MATCH (s:Section {section_id: $section_id})-[:HAS_ALTERNATIVE_CLIP]->(c:AlternativeClip)
        RETURN c.clip_id as clip_id,
               c.video_path as video_path,
               c.thumbnail_url as thumbnail_url,
               c.prompt as prompt,
               c.variation_type as variation_type,
               c.variation_description as variation_description,
               c.cloudinary_public_id as cloudinary_public_id,
               c.status as status,
               c.created_at as created_at
        ORDER BY c.created_at DESC
        """
        results = self.client.query(query, {"section_id": section_id})
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
        return results

    def get_section_current_clip(self, section_id: str) -> Optional[Dict]:
        """섹션의 현재 클립 조회"""
        query = """
        MATCH (s:Section {section_id: $section_id})
        OPTIONAL MATCH (s)-[:USES_CLIP]->(current:AlternativeClip)
        RETURN s.section_id as section_id,
               s.video_clip_path as default_video_path,
               s.thumbnail_url as default_thumbnail,
               current.clip_id as clip_id,
               current.video_path as video_path,
               current.thumbnail_url as thumbnail_url,
               current.prompt as prompt,
               current.created_at as created_at
        """
        result = self.client.query(query, {"section_id": section_id})
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            return row
        return None

    def replace_section_clip(self, section_id: str, new_clip_id: str) -> bool:
        """섹션의 클립 교체"""
        query = """
        MATCH (s:Section {section_id: $section_id})
        OPTIONAL MATCH (s)-[old_rel:USES_CLIP]->(:AlternativeClip)
        DELETE old_rel
        WITH s
        MATCH (new_clip:AlternativeClip {clip_id: $new_clip_id})
        CREATE (s)-[:USES_CLIP]->(new_clip)
        RETURN s.section_id as section_id
        """
        result = self.client.query(query, {
            "section_id": section_id,
            "new_clip_id": new_clip_id
        })
        return len(result) > 0

    def delete_alternative_clip(self, clip_id: str) -> bool:
        """대체 클립 삭제"""
        query = """
        MATCH (c:AlternativeClip {clip_id: $clip_id})
        DETACH DELETE c
        RETURN count(c) as deleted_count
        """
        result = self.client.query(query, {"clip_id": clip_id})
        return result[0]["deleted_count"] > 0 if result else False

    def update_alternative_clip_status(
        self,
        clip_id: str,
        status: str,
        video_path: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> bool:
        """대체 클립 상태 업데이트"""
        set_clauses = ["c.status = $status"]
        params = {"clip_id": clip_id, "status": status}

        if video_path:
            set_clauses.append("c.video_path = $video_path")
            params["video_path"] = video_path

        if thumbnail_url:
            set_clauses.append("c.thumbnail_url = $thumbnail_url")
            params["thumbnail_url"] = thumbnail_url

        query = f"""
        MATCH (c:AlternativeClip {{clip_id: $clip_id}})
        SET {", ".join(set_clauses)}
        RETURN c.clip_id as clip_id
        """
        result = self.client.query(query, params)
        return len(result) > 0

    # ==================== Subtitle Style CRUD ====================

    def create_or_update_subtitle_style(
        self,
        project_id: str,
        style: Dict[str, Any]
    ) -> Dict:
        """프로젝트 자막 스타일 생성 또는 업데이트"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        MERGE (proj)-[:HAS_SUBTITLE_STYLE]->(st:SubtitleStyle)
        SET st.font_family = $font_family,
            st.font_size = $font_size,
            st.font_color = $font_color,
            st.background_color = $background_color,
            st.background_opacity = $background_opacity,
            st.position = $position,
            st.vertical_offset = $vertical_offset,
            st.alignment = $alignment,
            st.outline_width = $outline_width,
            st.outline_color = $outline_color,
            st.shadow_enabled = $shadow_enabled,
            st.shadow_offset_x = $shadow_offset_x,
            st.shadow_offset_y = $shadow_offset_y,
            st.updated_at = datetime()
        RETURN st
        """
        params = {"project_id": project_id, **style}
        result = self.client.query(query, params)
        return result[0] if result else {}

    def get_subtitle_style(self, project_id: str) -> Optional[Dict]:
        """프로젝트 자막 스타일 조회"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[:HAS_SUBTITLE_STYLE]->(st:SubtitleStyle)
        RETURN st.font_family as font_family,
               st.font_size as font_size,
               st.font_color as font_color,
               st.background_color as background_color,
               st.background_opacity as background_opacity,
               st.position as position,
               st.vertical_offset as vertical_offset,
               st.alignment as alignment,
               st.outline_width as outline_width,
               st.outline_color as outline_color,
               st.shadow_enabled as shadow_enabled,
               st.shadow_offset_x as shadow_offset_x,
               st.shadow_offset_y as shadow_offset_y,
               st.updated_at as updated_at
        """
        result = self.client.query(query, {"project_id": project_id})
        if result:
            row = result[0]
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            return row
        return None

    # ==================== BGM CRUD ====================

    def create_or_update_bgm_settings(
        self,
        project_id: str,
        bgm_settings: Dict[str, Any]
    ) -> Dict:
        """프로젝트 BGM 설정 생성 또는 업데이트"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        MERGE (proj)-[:HAS_BGM_SETTINGS]->(bgm:BGMSettings)
        SET bgm.bgm_file_path = $bgm_file_path,
            bgm.volume = $volume,
            bgm.fade_in_duration = $fade_in_duration,
            bgm.fade_out_duration = $fade_out_duration,
            bgm.start_time = $start_time,
            bgm.end_time = $end_time,
            bgm.loop = $loop,
            bgm.ducking_enabled = $ducking_enabled,
            bgm.ducking_level = $ducking_level,
            bgm.updated_at = datetime($updated_at)
        ON CREATE SET bgm.created_at = datetime($created_at)
        RETURN bgm.bgm_file_path as bgm_file_path,
               bgm.volume as volume,
               bgm.fade_in_duration as fade_in_duration,
               bgm.fade_out_duration as fade_out_duration,
               bgm.start_time as start_time,
               bgm.end_time as end_time,
               bgm.loop as loop,
               bgm.ducking_enabled as ducking_enabled,
               bgm.ducking_level as ducking_level,
               bgm.created_at as created_at,
               bgm.updated_at as updated_at
        """
        params = {"project_id": project_id, **bgm_settings}
        result = self.client.query(query, params)
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            return row
        return {}

    def get_bgm_settings(self, project_id: str) -> Optional[Dict]:
        """프로젝트 BGM 설정 조회"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[:HAS_BGM_SETTINGS]->(bgm:BGMSettings)
        RETURN bgm.bgm_file_path as bgm_file_path,
               bgm.volume as volume,
               bgm.fade_in_duration as fade_in_duration,
               bgm.fade_out_duration as fade_out_duration,
               bgm.start_time as start_time,
               bgm.end_time as end_time,
               bgm.loop as loop,
               bgm.ducking_enabled as ducking_enabled,
               bgm.ducking_level as ducking_level,
               bgm.created_at as created_at,
               bgm.updated_at as updated_at
        """
        result = self.client.query(query, {"project_id": project_id})
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            return row
        return None

    def update_bgm_settings(
        self,
        project_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """프로젝트 BGM 설정 부분 업데이트"""
        import datetime as dt

        set_clauses = [f"bgm.{key} = ${key}" for key in updates.keys()]
        set_clauses.append("bgm.updated_at = datetime($updated_at)")

        query = f"""
        MATCH (proj:Project {{project_id: $project_id}})-[:HAS_BGM_SETTINGS]->(bgm:BGMSettings)
        SET {", ".join(set_clauses)}
        RETURN bgm.bgm_file_path as bgm_file_path
        """

        params = {
            "project_id": project_id,
            "updated_at": dt.datetime.utcnow().isoformat(),
            **updates
        }
        result = self.client.query(query, params)
        return len(result) > 0

    def delete_bgm_settings(self, project_id: str) -> bool:
        """프로젝트 BGM 설정 삭제"""
        query = """
        MATCH (proj:Project {project_id: $project_id})-[:HAS_BGM_SETTINGS]->(bgm:BGMSettings)
        DETACH DELETE bgm
        RETURN count(bgm) as deleted_count
        """
        result = self.client.query(query, {"project_id": project_id})
        return result[0]["deleted_count"] > 0 if result else False

    # ==================== Custom Preset CRUD ====================

    def create_custom_preset(
        self,
        user_id: str,
        preset: CustomPresetModel
    ) -> Dict:
        """커스텀 프리셋 생성"""
        import json

        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (cp:CustomPreset {
            preset_id: $preset_id,
            name: $name,
            description: $description,
            subtitle_style: $subtitle_style,
            bgm_settings: $bgm_settings,
            video_settings: $video_settings,
            is_favorite: $is_favorite,
            usage_count: $usage_count,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        CREATE (u)-[:HAS_PRESET]->(cp)
        RETURN cp.preset_id as preset_id,
               cp.name as name,
               cp.description as description,
               cp.subtitle_style as subtitle_style,
               cp.bgm_settings as bgm_settings,
               cp.video_settings as video_settings,
               cp.is_favorite as is_favorite,
               cp.usage_count as usage_count,
               cp.created_at as created_at,
               cp.updated_at as updated_at
        """

        params = {
            "user_id": user_id,
            "preset_id": preset.preset_id,
            "name": preset.name,
            "description": preset.description,
            "subtitle_style": json.dumps(preset.subtitle_style.model_dump(mode='json')),
            "bgm_settings": json.dumps(preset.bgm_settings.model_dump(mode='json')),
            "video_settings": json.dumps(preset.video_settings.model_dump(mode='json')),
            "is_favorite": preset.is_favorite,
            "usage_count": preset.usage_count,
            "created_at": preset.created_at.isoformat(),
            "updated_at": preset.updated_at.isoformat()
        }

        result = self.client.query(query, params)
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            # JSON 문자열을 파싱
            if row.get('subtitle_style'):
                row['subtitle_style'] = json.loads(row['subtitle_style'])
            if row.get('bgm_settings'):
                row['bgm_settings'] = json.loads(row['bgm_settings'])
            if row.get('video_settings'):
                row['video_settings'] = json.loads(row['video_settings'])
            return row
        return {}

    def get_user_custom_presets(
        self,
        user_id: str,
        favorite_only: bool = False
    ) -> List[Dict]:
        """사용자의 커스텀 프리셋 목록 조회"""
        import json

        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_PRESET]->(cp:CustomPreset)
        """

        if favorite_only:
            query += "WHERE cp.is_favorite = true "

        query += """
        RETURN cp.preset_id as preset_id,
               cp.name as name,
               cp.description as description,
               cp.subtitle_style as subtitle_style,
               cp.bgm_settings as bgm_settings,
               cp.video_settings as video_settings,
               cp.is_favorite as is_favorite,
               cp.usage_count as usage_count,
               cp.created_at as created_at,
               cp.updated_at as updated_at
        ORDER BY cp.is_favorite DESC, cp.usage_count DESC, cp.created_at DESC
        """

        results = self.client.query(query, {"user_id": user_id})
        for row in results:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            # JSON 문자열을 파싱
            if row.get('subtitle_style'):
                row['subtitle_style'] = json.loads(row['subtitle_style'])
            if row.get('bgm_settings'):
                row['bgm_settings'] = json.loads(row['bgm_settings'])
            if row.get('video_settings'):
                row['video_settings'] = json.loads(row['video_settings'])
        return results

    def get_custom_preset(self, preset_id: str) -> Optional[Dict]:
        """커스텀 프리셋 상세 조회"""
        import json

        query = """
        MATCH (cp:CustomPreset {preset_id: $preset_id})
        OPTIONAL MATCH (u:User)-[:HAS_PRESET]->(cp)
        RETURN cp.preset_id as preset_id,
               cp.name as name,
               cp.description as description,
               cp.subtitle_style as subtitle_style,
               cp.bgm_settings as bgm_settings,
               cp.video_settings as video_settings,
               cp.is_favorite as is_favorite,
               cp.usage_count as usage_count,
               cp.created_at as created_at,
               cp.updated_at as updated_at,
               u.user_id as user_id
        """

        result = self.client.query(query, {"preset_id": preset_id})
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            # JSON 문자열을 파싱
            if row.get('subtitle_style'):
                row['subtitle_style'] = json.loads(row['subtitle_style'])
            if row.get('bgm_settings'):
                row['bgm_settings'] = json.loads(row['bgm_settings'])
            if row.get('video_settings'):
                row['video_settings'] = json.loads(row['video_settings'])
            return row
        return None

    def update_custom_preset(
        self,
        preset_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """커스텀 프리셋 수정"""
        import json
        import datetime as dt

        # JSON 직렬화가 필요한 필드 처리
        if 'subtitle_style' in updates and isinstance(updates['subtitle_style'], dict):
            updates['subtitle_style'] = json.dumps(updates['subtitle_style'])
        if 'bgm_settings' in updates and isinstance(updates['bgm_settings'], dict):
            updates['bgm_settings'] = json.dumps(updates['bgm_settings'])
        if 'video_settings' in updates and isinstance(updates['video_settings'], dict):
            updates['video_settings'] = json.dumps(updates['video_settings'])

        set_clauses = [f"cp.{key} = ${key}" for key in updates.keys()]
        set_clauses.append("cp.updated_at = datetime($updated_at)")

        query = f"""
        MATCH (cp:CustomPreset {{preset_id: $preset_id}})
        SET {", ".join(set_clauses)}
        RETURN cp.preset_id as preset_id
        """

        params = {
            "preset_id": preset_id,
            "updated_at": dt.datetime.utcnow().isoformat(),
            **updates
        }

        result = self.client.query(query, params)
        return len(result) > 0

    def delete_custom_preset(self, preset_id: str) -> bool:
        """커스텀 프리셋 삭제"""
        query = """
        MATCH (cp:CustomPreset {preset_id: $preset_id})
        DETACH DELETE cp
        RETURN count(cp) as deleted_count
        """
        result = self.client.query(query, {"preset_id": preset_id})
        return result[0]["deleted_count"] > 0 if result else False

    def increment_preset_usage(self, preset_id: str) -> bool:
        """프리셋 사용 횟수 증가"""
        query = """
        MATCH (cp:CustomPreset {preset_id: $preset_id})
        SET cp.usage_count = cp.usage_count + 1,
            cp.updated_at = datetime()
        RETURN cp.preset_id as preset_id
        """
        result = self.client.query(query, {"preset_id": preset_id})
        return len(result) > 0

    def apply_custom_preset_to_project(
        self,
        project_id: str,
        preset_id: str
    ) -> bool:
        """프로젝트에 커스텀 프리셋 적용"""
        query = """
        MATCH (proj:Project {project_id: $project_id})
        MATCH (cp:CustomPreset {preset_id: $preset_id})
        MERGE (proj)-[:USES_CUSTOM_PRESET]->(cp)
        SET cp.usage_count = cp.usage_count + 1,
            cp.updated_at = datetime()
        RETURN proj.project_id as project_id
        """
        result = self.client.query(query, {
            "project_id": project_id,
            "preset_id": preset_id
        })
        return len(result) > 0

    def get_project_custom_preset(self, project_id: str) -> Optional[Dict]:
        """프로젝트에 적용된 커스텀 프리셋 조회"""
        import json

        query = """
        MATCH (proj:Project {project_id: $project_id})-[:USES_CUSTOM_PRESET]->(cp:CustomPreset)
        RETURN cp.preset_id as preset_id,
               cp.name as name,
               cp.description as description,
               cp.subtitle_style as subtitle_style,
               cp.bgm_settings as bgm_settings,
               cp.video_settings as video_settings,
               cp.is_favorite as is_favorite,
               cp.usage_count as usage_count,
               cp.created_at as created_at,
               cp.updated_at as updated_at
        """

        result = self.client.query(query, {"project_id": project_id})
        if result:
            row = result[0]
            if row.get('created_at'):
                row['created_at'] = row['created_at'].to_native()
            if row.get('updated_at'):
                row['updated_at'] = row['updated_at'].to_native()
            # JSON 문자열을 파싱
            if row.get('subtitle_style'):
                row['subtitle_style'] = json.loads(row['subtitle_style'])
            if row.get('bgm_settings'):
                row['bgm_settings'] = json.loads(row['bgm_settings'])
            if row.get('video_settings'):
                row['video_settings'] = json.loads(row['video_settings'])
            return row
        return None

    # ==================== Platform Preset Application ====================

    def apply_platform_preset_to_project(
        self,
        project_id: str,
        platform: str,
        preset_settings: Dict[str, Any]
    ) -> Dict:
        """프로젝트에 플랫폼 프리셋 적용 및 기록"""
        import json

        application_id = f"preset_app_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        query = """
        MATCH (proj:Project {project_id: $project_id})
        CREATE (preset:PlatformPresetApplication {
            application_id: $application_id,
            platform: $platform,
            applied_at: datetime($applied_at),
            preset_settings: $preset_settings
        })
        CREATE (proj)-[:USES_PLATFORM_PRESET]->(preset)
        RETURN preset.application_id as application_id,
               preset.platform as platform,
               preset.applied_at as applied_at,
               preset.preset_settings as preset_settings
        """

        params = {
            "project_id": project_id,
            "application_id": application_id,
            "platform": platform,
            "applied_at": now.isoformat(),
            "preset_settings": json.dumps(preset_settings)
        }

        result = self.client.query(query, params)
        if result:
            row = result[0]
            if row.get('applied_at'):
                row['applied_at'] = row['applied_at'].to_native()
            if row.get('preset_settings'):
                row['preset_settings'] = json.loads(row['preset_settings'])
            return row
        return {}

    def get_project_platform_preset(self, project_id: str) -> Optional[Dict]:
        """프로젝트에 적용된 플랫폼 프리셋 조회"""
        import json

        query = """
        MATCH (proj:Project {project_id: $project_id})-[:USES_PLATFORM_PRESET]->(preset:PlatformPresetApplication)
        RETURN preset.application_id as application_id,
               preset.platform as platform,
               preset.applied_at as applied_at,
               preset.preset_settings as preset_settings
        ORDER BY preset.applied_at DESC
        LIMIT 1
        """

        result = self.client.query(query, {"project_id": project_id})
        if result:
            row = result[0]
            if row.get('applied_at'):
                row['applied_at'] = row['applied_at'].to_native()
            if row.get('preset_settings'):
                row['preset_settings'] = json.loads(row['preset_settings'])
            return row
        return None

    def get_project_preset_history(self, project_id: str) -> List[Dict]:
        """프로젝트의 프리셋 적용 이력 조회"""
        import json

        query = """
        MATCH (proj:Project {project_id: $project_id})-[:USES_PLATFORM_PRESET]->(preset:PlatformPresetApplication)
        RETURN preset.application_id as application_id,
               preset.platform as platform,
               preset.applied_at as applied_at,
               preset.preset_settings as preset_settings
        ORDER BY preset.applied_at DESC
        """

        results = self.client.query(query, {"project_id": project_id})
        for row in results:
            if row.get('applied_at'):
                row['applied_at'] = row['applied_at'].to_native()
            if row.get('preset_settings'):
                row['preset_settings'] = json.loads(row['preset_settings'])
        return results
