"""Neo4j GraphRAG 클라이언트"""
from typing import List, Dict, Any
from neo4j import GraphDatabase
import logging
from contextlib import nullcontext

from app.core.config import get_settings

settings = get_settings()

# Logfire 사용 가능 여부 확인
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class Neo4jClient:
    """Neo4j 데이터베이스 클라이언트 (GraphRAG)"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.logger = logging.getLogger(__name__)

    def close(self):
        """연결 종료"""
        self.driver.close()

    def query(self, cypher: str, parameters: Dict[str, Any] = None, **kwargs) -> List[Dict]:
        """
        Cypher 쿼리 실행

        Args:
            cypher: Cypher 쿼리 문자열
            parameters: 쿼리 파라미터 (딕셔너리)
            **kwargs: 추가 파라미터 (keyword arguments로 전달)

        Returns:
            쿼리 결과 (딕셔너리 리스트)
        """
        # parameters와 kwargs 병합
        all_params = parameters or {}
        all_params.update(kwargs)

        with self.driver.session() as session:
            result = session.run(cypher, all_params)
            return [dict(record) for record in result]

    def create_indexes(self):
        """필수 인덱스 생성"""
        span_context = logfire.span("neo4j.create_indexes") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            with self.driver.session() as session:
                # User ID 인덱스 (레거시)
                session.run("CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)")

                # Content ID 인덱스 (레거시)
                session.run("CREATE INDEX content_id IF NOT EXISTS FOR (c:Content) ON (c.id)")

                # HighPerformance 라벨 인덱스 (레거시)
                session.run("CREATE INDEX high_perf IF NOT EXISTS FOR (c:HighPerformance) ON (c.id)")

                self.logger.info("Neo4j indexes created")

    def create_full_schema(self):
        """전체 스키마 생성 (Constraints & Indexes)"""
        span_context = logfire.span("neo4j.create_full_schema") if LOGFIRE_AVAILABLE else nullcontext()

        with span_context:
            with self.driver.session() as session:
                schema_queries = [
                    # User
                    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                    "CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email)",

                    # Persona
                    "CREATE CONSTRAINT persona_id_unique IF NOT EXISTS FOR (p:Persona) REQUIRE p.persona_id IS UNIQUE",

                    # Project
                    "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_id IS UNIQUE",
                    "CREATE INDEX project_created IF NOT EXISTS FOR (p:Project) ON (p.created_at)",
                    "CREATE INDEX project_status IF NOT EXISTS FOR (p:Project) ON (p.status)",

                    # Script
                    "CREATE CONSTRAINT script_id_unique IF NOT EXISTS FOR (s:Script) REQUIRE s.script_id IS UNIQUE",

                    # Audio
                    "CREATE CONSTRAINT audio_id_unique IF NOT EXISTS FOR (a:Audio) REQUIRE a.audio_id IS UNIQUE",

                    # Video
                    "CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:Video) REQUIRE v.video_id IS UNIQUE",

                    # Thumbnail
                    "CREATE CONSTRAINT thumbnail_id_unique IF NOT EXISTS FOR (t:Thumbnail) REQUIRE t.thumbnail_id IS UNIQUE",

                    # Metrics
                    "CREATE INDEX metrics_performance IF NOT EXISTS FOR (m:Metrics) ON (m.performance_score)",
                    "CREATE INDEX metrics_measured IF NOT EXISTS FOR (m:Metrics) ON (m.measured_at)",

                    # CustomVoice
                    "CREATE CONSTRAINT custom_voice_id_unique IF NOT EXISTS FOR (cv:CustomVoice) REQUIRE cv.voice_id IS UNIQUE",

                    # Character (캐릭터 일관성)
                    "CREATE CONSTRAINT character_id_unique IF NOT EXISTS FOR (c:Character) REQUIRE c.character_id IS UNIQUE",
                    "CREATE INDEX character_created IF NOT EXISTS FOR (c:Character) ON (c.created_at)",

                    # Content (레거시)
                    "CREATE INDEX content_id IF NOT EXISTS FOR (c:Content) ON (c.content_id)",

                    # Section (콘티 섹션)
                    "CREATE CONSTRAINT section_id_unique IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE",
                    "CREATE INDEX section_order IF NOT EXISTS FOR (s:Section) ON (s.order)",
                    "CREATE INDEX section_type IF NOT EXISTS FOR (s:Section) ON (s.type)",

                    # CustomPreset (커스텀 프리셋)
                    "CREATE CONSTRAINT preset_id_unique IF NOT EXISTS FOR (cp:CustomPreset) REQUIRE cp.preset_id IS UNIQUE",
                    "CREATE INDEX preset_created IF NOT EXISTS FOR (cp:CustomPreset) ON (cp.created_at)",
                    "CREATE INDEX preset_favorite IF NOT EXISTS FOR (cp:CustomPreset) ON (cp.is_favorite)",
                    "CREATE INDEX preset_usage IF NOT EXISTS FOR (cp:CustomPreset) ON (cp.usage_count)",

                    # PlatformPresetApplication (플랫폼 프리셋 적용 기록)
                    "CREATE CONSTRAINT platform_preset_app_id_unique IF NOT EXISTS FOR (ppa:PlatformPresetApplication) REQUIRE ppa.application_id IS UNIQUE",
                    "CREATE INDEX platform_preset_app_applied IF NOT EXISTS FOR (ppa:PlatformPresetApplication) ON (ppa.applied_at)",
                    "CREATE INDEX platform_preset_app_platform IF NOT EXISTS FOR (ppa:PlatformPresetApplication) ON (ppa.platform)",

                    # Presentation (프레젠테이션)
                    "CREATE CONSTRAINT presentation_id_unique IF NOT EXISTS FOR (pres:Presentation) REQUIRE pres.presentation_id IS UNIQUE",
                    "CREATE INDEX presentation_created IF NOT EXISTS FOR (pres:Presentation) ON (pres.created_at)",

                    # Slide (슬라이드)
                    "CREATE CONSTRAINT slide_id_unique IF NOT EXISTS FOR (s:Slide) REQUIRE s.slide_id IS UNIQUE",
                    "CREATE INDEX slide_number IF NOT EXISTS FOR (s:Slide) ON (s.slide_number)",
                    "CREATE INDEX slide_confidence IF NOT EXISTS FOR (s:Slide) ON (s.confidence)",
                ]

                for query in schema_queries:
                    try:
                        session.run(query)
                    except Exception as e:
                        self.logger.warning(f"Schema query failed: {query[:50]}... - {e}")

                self.logger.info("Full Neo4j schema created")

    # ==================== 성과 데이터 쿼리 ====================

    def get_user_high_performance_content(
        self,
        user_id: str,
        min_score: float = 70,
        limit: int = 10
    ) -> List[Dict]:
        """사용자의 고성과 컨텐츠 조회"""
        query = """
        MATCH (u:User {id: $user_id})-[:CREATED]->(c:Content)-[:ACHIEVED]->(m:Metrics)
        WHERE m.performance_score >= $min_score
        RETURN c.id as content_id,
               c.title as title,
               c.platform as platform,
               m.views as views,
               m.performance_score as score,
               m.engagement_rate as engagement_rate
        ORDER BY m.performance_score DESC
        LIMIT $limit
        """

        return self.query(query, {
            'user_id': user_id,
            'min_score': min_score,
            'limit': limit
        })

    def get_thumbnail_patterns(
        self,
        user_id: str,
        performance_label: str = "high"
    ) -> List[Dict]:
        """특정 성과 레벨의 썸네일 패턴 조회"""
        query = """
        MATCH (u:User {id: $user_id})-[:CREATED]->(c:Content)-[:HAS_THUMBNAIL]->(t:Thumbnail)
        MATCH (c)-[:ACHIEVED]->(m:Metrics)
        WHERE (m.performance_score >= 70 AND $performance_label = 'high')
           OR (m.performance_score >= 40 AND m.performance_score < 70 AND $performance_label = 'medium')
           OR (m.performance_score < 40 AND $performance_label = 'low')
        RETURN t.url as thumbnail_url,
               c.title as title,
               m.performance_score as score
        ORDER BY m.performance_score DESC
        """

        return self.query(query, {
            'user_id': user_id,
            'performance_label': performance_label
        })

    def get_platform_insights(self, user_id: str) -> Dict:
        """플랫폼별 성과 인사이트"""
        query = """
        MATCH (u:User {id: $user_id})-[:CREATED]->(c:Content)-[:ACHIEVED]->(m:Metrics)
        RETURN c.platform as platform,
               COUNT(c) as total_contents,
               AVG(m.views) as avg_views,
               AVG(m.engagement_rate) as avg_engagement,
               AVG(m.performance_score) as avg_score
        ORDER BY avg_score DESC
        """

        results = self.query(query, {'user_id': user_id})

        return {
            result['platform']: {
                'total_contents': result['total_contents'],
                'avg_views': result['avg_views'],
                'avg_engagement': result['avg_engagement'],
                'avg_score': result['avg_score']
            }
            for result in results
        }

    # ==================== 커스텀 음성 관리 ====================

    def save_custom_voice(
        self,
        user_id: str,
        voice_id: str,
        name: str,
        description: str = "",
        file_path: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict:
        """
        커스텀 음성을 Neo4j에 저장

        Args:
            user_id: 사용자 ID
            voice_id: ElevenLabs voice_id
            name: 음성 이름
            description: 음성 설명
            file_path: 원본 오디오 파일 경로
            metadata: 추가 메타데이터

        Returns:
            저장된 음성 정보
        """
        import datetime

        query = """
        MERGE (u:User {id: $user_id})
        CREATE (v:CustomVoice {
            voice_id: $voice_id,
            name: $name,
            description: $description,
            file_path: $file_path,
            created_at: datetime($created_at),
            metadata: $metadata
        })
        CREATE (u)-[:HAS_VOICE]->(v)
        RETURN v.voice_id as voice_id,
               v.name as name,
               v.created_at as created_at
        """

        metadata = metadata or {}
        created_at = datetime.datetime.utcnow().isoformat()

        result = self.query(query, {
            'user_id': user_id,
            'voice_id': voice_id,
            'name': name,
            'description': description,
            'file_path': file_path,
            'created_at': created_at,
            'metadata': metadata
        })

        self.logger.info(f"Saved custom voice {voice_id} for user {user_id}")

        return result[0] if result else {}

    def get_user_custom_voices(self, user_id: str) -> List[Dict]:
        """
        사용자의 모든 커스텀 음성 조회

        Args:
            user_id: 사용자 ID

        Returns:
            커스텀 음성 리스트
        """
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_VOICE]->(v:CustomVoice)
        RETURN v.voice_id as voice_id,
               v.name as name,
               v.description as description,
               v.created_at as created_at,
               v.metadata as metadata
        ORDER BY v.created_at DESC
        """

        return self.query(query, {'user_id': user_id})

    def get_custom_voice_by_id(self, voice_id: str) -> Dict:
        """
        voice_id로 커스텀 음성 조회

        Args:
            voice_id: ElevenLabs voice_id

        Returns:
            커스텀 음성 정보
        """
        query = """
        MATCH (v:CustomVoice {voice_id: $voice_id})
        OPTIONAL MATCH (u:User)-[:HAS_VOICE]->(v)
        RETURN v.voice_id as voice_id,
               v.name as name,
               v.description as description,
               v.file_path as file_path,
               v.created_at as created_at,
               v.metadata as metadata,
               u.id as user_id
        """

        results = self.query(query, {'voice_id': voice_id})
        return results[0] if results else {}

    def delete_custom_voice(self, voice_id: str) -> bool:
        """
        커스텀 음성 삭제

        Args:
            voice_id: ElevenLabs voice_id

        Returns:
            삭제 성공 여부
        """
        query = """
        MATCH (v:CustomVoice {voice_id: $voice_id})
        DETACH DELETE v
        RETURN count(v) as deleted_count
        """

        result = self.query(query, {'voice_id': voice_id})
        deleted_count = result[0]['deleted_count'] if result else 0

        if deleted_count > 0:
            self.logger.info(f"Deleted custom voice {voice_id}")
            return True
        else:
            self.logger.warning(f"Custom voice {voice_id} not found")
            return False

    # ==================== Project & Workflow 관리 ====================

    def create_project_workflow(
        self,
        user_id: str,
        project_data: Dict[str, Any],
        persona_id: str = None
    ) -> Dict:
        """
        프로젝트 워크플로우 생성 (User → Project → Persona 연결)

        Args:
            user_id: 사용자 ID
            project_data: 프로젝트 데이터 (title, topic, platform, status 등)
            persona_id: 페르소나 ID (옵션)

        Returns:
            생성된 프로젝트 정보
        """
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

        params = {"user_id": user_id, **project_data}

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
               proj.status as status,
               proj.created_at as created_at
        """

        result = self.query(query, params)
        return result[0] if result else {}

    def get_project_full_context(self, project_id: str) -> Dict:
        """
        프로젝트의 전체 컨텍스트 조회 (스크립트, 오디오, 비디오, 메트릭 포함)

        Args:
            project_id: 프로젝트 ID

        Returns:
            프로젝트 전체 정보
        """
        query = """
        MATCH (proj:Project {project_id: $project_id})
        OPTIONAL MATCH (proj)-[:USES_PERSONA]->(persona:Persona)
        OPTIONAL MATCH (proj)-[:HAS_SCRIPT]->(script:Script)
        OPTIONAL MATCH (script)-[:GENERATED_AUDIO]->(audio:Audio)
        OPTIONAL MATCH (audio)-[:USED_IN_VIDEO]->(video:Video)
        OPTIONAL MATCH (video)-[:ACHIEVED]->(metrics:Metrics)

        RETURN proj.project_id as project_id,
               proj.title as title,
               proj.topic as topic,
               proj.platform as platform,
               proj.status as status,
               proj.created_at as created_at,
               proj.updated_at as updated_at,
               proj.publish_scheduled_at as publish_scheduled_at,
               persona.persona_id as persona_id,
               persona.gender as persona_gender,
               persona.tone as persona_tone,
               collect(DISTINCT {
                   script_id: script.script_id,
                   content: script.content,
                   version: script.version
               }) as scripts,
               collect(DISTINCT {
                   audio_id: audio.audio_id,
                   file_path: audio.file_path,
                   stt_accuracy: audio.stt_accuracy
               }) as audios,
               collect(DISTINCT {
                   video_id: video.video_id,
                   file_path: video.file_path,
                   duration: video.duration
               }) as videos,
               collect(DISTINCT {
                   metrics_id: metrics.metrics_id,
                   views: metrics.views,
                   performance_score: metrics.performance_score
               }) as metrics
        """

        result = self.query(query, {"project_id": project_id})
        return result[0] if result else {}

    def get_user_analytics_dashboard(self, user_id: str, days: int = 30) -> Dict:
        """
        사용자 분석 대시보드 데이터 조회

        Args:
            user_id: 사용자 ID
            days: 조회 기간 (일)

        Returns:
            대시보드 데이터
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
        OPTIONAL MATCH (proj)-[:HAS_VIDEO]->(v:Video)-[:ACHIEVED]->(m:Metrics)
        WHERE datetime() - m.measured_at <= duration({days: $days})

        WITH u, proj, v, m
        RETURN count(DISTINCT proj) as total_projects,
               count(DISTINCT v) as total_videos,
               sum(m.views) as total_views,
               avg(m.engagement_rate) as avg_engagement,
               avg(m.performance_score) as avg_performance_score,
               max(m.performance_score) as best_performance_score,
               collect(DISTINCT proj.platform) as platforms_used
        """

        result = self.query(query, {"user_id": user_id, "days": days})
        return result[0] if result else {}

    def get_top_performing_content(
        self,
        user_id: str,
        limit: int = 10,
        min_score: float = 70.0
    ) -> List[Dict]:
        """
        사용자의 고성과 콘텐츠 조회 (Writer 에이전트용)

        Args:
            user_id: 사용자 ID
            limit: 조회 개수
            min_score: 최소 성과 점수

        Returns:
            고성과 콘텐츠 리스트
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[:OWNS]->(proj:Project)
              -[:HAS_SCRIPT]->(s:Script)
              -[:GENERATED_AUDIO]->()-[:USED_IN_VIDEO]->(v:Video)
              -[:ACHIEVED]->(m:Metrics)
        WHERE m.performance_score >= $min_score
        RETURN s.script_id as script_id,
               s.content as script_content,
               proj.topic as topic,
               proj.platform as platform,
               m.performance_score as score,
               m.engagement_rate as engagement,
               m.views as views,
               m.measured_at as measured_at
        ORDER BY m.performance_score DESC
        LIMIT $limit
        """

        return self.query(query, {
            "user_id": user_id,
            "limit": limit,
            "min_score": min_score
        })

    # ==================== Writer Agent Memory (Week 1) ====================

    def search_similar_scripts(
        self,
        platform: str,
        tone: str,
        limit: int = 3,
        min_performance: float = 8.0
    ) -> List[Dict[str, Any]]:
        """
        유사한 스타일의 고성과 스크립트 검색 (Writer Agent용)

        Args:
            platform: 플랫폼 (YouTube, Instagram, TikTok)
            tone: 톤 (professional, energetic, casual, educational, playful, inspiring)
            limit: 반환할 최대 개수
            min_performance: 최소 성과 점수

        Returns:
            고성과 스크립트 리스트
        """
        query = """
        MATCH (s:Script)
        WHERE s.platform = $platform
          AND s.tone = $tone
          AND s.performance_score >= $min_performance
        RETURN s.id AS id,
               s.content AS content,
               s.performance_score AS performance_score,
               s.views AS views,
               s.ctr AS ctr,
               s.word_count AS word_count,
               s.gender AS gender
        ORDER BY s.performance_score DESC
        LIMIT $limit
        """

        return self.query(query, {
            "platform": platform,
            "tone": tone,
            "min_performance": min_performance,
            "limit": limit
        })

    def save_script_to_memory(
        self,
        script_id: str,
        content: str,
        platform: str,
        tone: str,
        gender: str,
        word_count: int,
        campaign_id: str = None,
        performance_score: float = None,
        views: int = 0,
        ctr: float = 0.0
    ) -> bool:
        """
        새 스크립트를 GraphRAG Memory에 저장

        Args:
            script_id: 스크립트 고유 ID
            content: 스크립트 전문
            platform: 플랫폼
            tone: 톤
            gender: 성별
            word_count: 단어 수
            campaign_id: 캠페인 ID (선택)
            performance_score: 성과 점수 (선택)
            views: 조회수
            ctr: 클릭률

        Returns:
            성공 여부
        """
        try:
            query = """
            CREATE (s:Script {
                id: $script_id,
                content: $content,
                platform: $platform,
                tone: $tone,
                gender: $gender,
                word_count: $word_count,
                performance_score: $performance_score,
                views: $views,
                ctr: $ctr,
                created_at: datetime()
            })
            """

            self.query(query, {
                "script_id": script_id,
                "content": content,
                "platform": platform,
                "tone": tone,
                "gender": gender,
                "word_count": word_count,
                "performance_score": performance_score,
                "views": views,
                "ctr": ctr
            })

            # Campaign 관계 연결
            if campaign_id:
                link_query = """
                MATCH (s:Script {id: $script_id})
                MATCH (c:Campaign {id: $campaign_id})
                CREATE (s)-[:BELONGS_TO]->(c)
                """
                self.query(link_query, {
                    "script_id": script_id,
                    "campaign_id": campaign_id
                })

            self.logger.info(f"✅ Script saved to memory: {script_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Script save failed: {e}")
            return False

    # ==================== Content Similarity (SIMILAR_TO) ====================

    async def create_similar_to_relationship(
        self,
        content_id_1: int,
        content_id_2: int,
        similarity_score: float
    ) -> Dict:
        """
        두 Content 노드 간 SIMILAR_TO 관계 생성

        Args:
            content_id_1: 소스 콘텐츠 ID
            content_id_2: 타겟 콘텐츠 ID
            similarity_score: 유사도 점수 (0.0 ~ 1.0)

        Returns:
            생성된 관계 정보
        """
        try:
            query = """
            MATCH (c1:Content {id: $content_id_1})
            MATCH (c2:Content {id: $content_id_2})
            MERGE (c1)-[r:SIMILAR_TO]->(c2)
            SET r.score = $similarity_score,
                r.updated_at = datetime()
            RETURN c1.id AS source_id,
                   c2.id AS target_id,
                   r.score AS score
            """

            result = self.query(query, {
                "content_id_1": content_id_1,
                "content_id_2": content_id_2,
                "similarity_score": similarity_score
            })

            self.logger.info(
                f"SIMILAR_TO relationship created: {content_id_1} -> {content_id_2} "
                f"(score: {similarity_score:.2f})"
            )
            return result[0] if result else {}

        except Exception as e:
            self.logger.error(f"Failed to create SIMILAR_TO relationship: {e}")
            return {}

    async def get_similar_content(
        self,
        content_id: int,
        limit: int = 5
    ) -> list:
        """
        주어진 콘텐츠와 유사한 콘텐츠 조회 (score DESC 정렬)

        Args:
            content_id: 콘텐츠 ID
            limit: 반환할 최대 개수

        Returns:
            유사 콘텐츠 리스트 [{id, score, title}, ...]
        """
        try:
            query = """
            MATCH (c:Content {id: $content_id})-[r:SIMILAR_TO]->(similar:Content)
            RETURN similar.id AS id,
                   r.score AS score,
                   similar.title AS title
            ORDER BY r.score DESC
            LIMIT $limit
            """

            results = self.query(query, {
                "content_id": content_id,
                "limit": limit
            })

            self.logger.info(
                f"Found {len(results)} similar contents for content_id={content_id}"
            )
            return results

        except Exception as e:
            self.logger.error(f"Failed to get similar content: {e}")
            return []

    async def build_similarity_pipeline(self, content_id: int) -> Dict:
        """
        태그/플랫폼 기반 유사도 파이프라인 실행

        주어진 콘텐츠의 tags/platform을 다른 모든 Content 노드와 비교하여
        score > 0.3인 경우 SIMILAR_TO 관계를 자동 생성합니다.

        유사도 계산: matching_tags / total_unique_tags

        Args:
            content_id: 기준 콘텐츠 ID

        Returns:
            파이프라인 실행 결과 {relationships_created, content_id}
        """
        try:
            # 1. 기준 콘텐츠의 태그와 플랫폼 조회
            source_query = """
            MATCH (c:Content {id: $content_id})
            RETURN c.id AS id,
                   c.tags AS tags,
                   c.platform AS platform,
                   c.title AS title
            """
            source_results = self.query(source_query, {"content_id": content_id})

            if not source_results:
                self.logger.warning(f"Content not found: {content_id}")
                return {"relationships_created": 0, "content_id": content_id}

            source = source_results[0]
            source_tags = set(source.get("tags") or [])
            source_platform = source.get("platform", "")

            # 2. 다른 모든 Content 노드 조회
            others_query = """
            MATCH (c:Content)
            WHERE c.id <> $content_id
            RETURN c.id AS id,
                   c.tags AS tags,
                   c.platform AS platform,
                   c.title AS title
            """
            others = self.query(others_query, {"content_id": content_id})

            # 3. 유사도 계산 및 관계 생성
            relationships_created = 0
            for other in others:
                other_tags = set(other.get("tags") or [])
                other_platform = other.get("platform", "")

                # 태그 기반 유사도 계산
                all_tags = source_tags | other_tags
                if not all_tags:
                    # 태그가 없으면 플랫폼만 비교
                    score = 0.5 if source_platform and source_platform == other_platform else 0.0
                else:
                    matching_tags = source_tags & other_tags
                    score = len(matching_tags) / len(all_tags)

                    # 같은 플랫폼이면 보너스 점수
                    if source_platform and source_platform == other_platform:
                        score = min(1.0, score + 0.1)

                # score > 0.3 이면 관계 생성
                if score > 0.3:
                    await self.create_similar_to_relationship(
                        content_id_1=content_id,
                        content_id_2=other["id"],
                        similarity_score=round(score, 4)
                    )
                    relationships_created += 1

            self.logger.info(
                f"Similarity pipeline completed for content_id={content_id}: "
                f"{relationships_created} relationships created"
            )
            return {
                "relationships_created": relationships_created,
                "content_id": content_id
            }

        except Exception as e:
            self.logger.error(f"Similarity pipeline failed for content_id={content_id}: {e}")
            return {"relationships_created": 0, "content_id": content_id}


# 싱글톤 인스턴스
_neo4j_client_instance = None


def get_neo4j_client() -> Neo4jClient:
    """Neo4j 클라이언트 싱글톤 인스턴스"""
    global _neo4j_client_instance
    if _neo4j_client_instance is None:
        _neo4j_client_instance = Neo4jClient()
    return _neo4j_client_instance
