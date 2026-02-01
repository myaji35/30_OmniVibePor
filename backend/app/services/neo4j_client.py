"""Neo4j GraphRAG 클라이언트"""
from typing import List, Dict, Any
from neo4j import GraphDatabase
import logfire

from app.core.config import get_settings

settings = get_settings()


class Neo4jClient:
    """Neo4j 데이터베이스 클라이언트 (GraphRAG)"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.logger = logfire.get_logger(__name__)

    def close(self):
        """연결 종료"""
        self.driver.close()

    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """
        Cypher 쿼리 실행

        Args:
            cypher: Cypher 쿼리 문자열
            parameters: 쿼리 파라미터

        Returns:
            쿼리 결과 (딕셔너리 리스트)
        """
        with self.logger.span("neo4j.query"):
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]

    def create_indexes(self):
        """필수 인덱스 생성"""
        with self.logger.span("neo4j.create_indexes"):
            with self.driver.session() as session:
                # User ID 인덱스
                session.run("CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)")

                # Content ID 인덱스
                session.run("CREATE INDEX content_id IF NOT EXISTS FOR (c:Content) ON (c.id)")

                # HighPerformance 라벨 인덱스
                session.run("CREATE INDEX high_perf IF NOT EXISTS FOR (c:HighPerformance) ON (c.id)")

                self.logger.info("Neo4j indexes created")

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
