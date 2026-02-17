"""멀티 플랫폼 컨텐츠 성과 추적 및 자가학습 시스템"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
# Logfire는 optional
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings

settings = get_settings()


class ContentPerformanceTracker:
    """
    YouTube, Facebook, Instagram 등 멀티 플랫폼의
    자신이 게시한 컨텐츠 성과를 추적하고 학습하는 시스템
    """

    def __init__(self, neo4j_client, pinecone_index, thumbnail_learner):
        self.neo4j = neo4j_client
        self.pinecone = pinecone_index
        self.thumbnail_learner = thumbnail_learner
        self.logger = logging.getLogger(__name__)

        # YouTube Data API
        self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

    # ==================== YouTube 성과 추적 ====================

    async def track_youtube_performance(
        self,
        channel_id: str,
        user_id: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        자신의 YouTube 채널 영상들의 성과 추적

        Args:
            channel_id: YouTube 채널 ID
            user_id: 사용자 ID (Neo4j 저장용)
            days_back: 조회 기간 (일)

        Returns:
            성과 데이터 리스트
        """
        with self.logger.span("youtube.track_performance"):
            try:
                # 1. 채널의 최근 업로드 영상 가져오기
                videos = await self._get_channel_videos(channel_id, days_back)

                performance_data = []

                for video in videos:
                    video_id = video['id']['videoId']

                    # 2. 상세 통계 조회
                    stats = await self._get_video_stats(video_id)

                    if not stats:
                        continue

                    # 3. 성과 지표 계산
                    metrics = self._calculate_engagement_metrics(stats)

                    # 4. 썸네일 URL
                    thumbnail_url = video['snippet']['thumbnails']['high']['url']

                    # 5. 데이터 구조화
                    perf_data = {
                        'platform': 'youtube',
                        'video_id': video_id,
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'][:500],
                        'thumbnail_url': thumbnail_url,
                        'published_at': video['snippet']['publishedAt'],
                        'views': stats['viewCount'],
                        'likes': stats.get('likeCount', 0),
                        'comments': stats.get('commentCount', 0),
                        'engagement_rate': metrics['engagement_rate'],
                        'ctr_estimate': metrics['ctr_estimate'],
                        'performance_score': metrics['performance_score'],
                        'user_id': user_id
                    }

                    performance_data.append(perf_data)

                self.logger.info(f"Tracked {len(performance_data)} YouTube videos")
                return performance_data

            except HttpError as e:
                self.logger.error(f"YouTube API error: {e}")
                return []

    async def _get_channel_videos(self, channel_id: str, days_back: int) -> List[Dict]:
        """채널의 최근 영상 목록"""
        published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'

        response = self.youtube.search().list(
            part="snippet,id",
            channelId=channel_id,
            type="video",
            order="date",
            publishedAfter=published_after,
            maxResults=50
        ).execute()

        return response.get('items', [])

    async def _get_video_stats(self, video_id: str) -> Optional[Dict]:
        """영상 상세 통계"""
        try:
            response = self.youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()

            items = response.get('items', [])
            if not items:
                return None

            stats = items[0]['statistics']
            return {
                'viewCount': int(stats.get('viewCount', 0)),
                'likeCount': int(stats.get('likeCount', 0)),
                'commentCount': int(stats.get('commentCount', 0))
            }

        except HttpError:
            return None

    def _calculate_engagement_metrics(self, stats: Dict) -> Dict:
        """
        인게이지먼트 지표 계산

        - engagement_rate: (좋아요 + 댓글) / 조회수
        - ctr_estimate: 댓글/조회수 * 100 (추정 CTR)
        - performance_score: 종합 점수 (0-100)
        """
        views = stats['viewCount']
        likes = stats.get('likeCount', 0)
        comments = stats.get('commentCount', 0)

        if views == 0:
            return {
                'engagement_rate': 0,
                'ctr_estimate': 0,
                'performance_score': 0
            }

        engagement_rate = (likes + comments) / views
        ctr_estimate = (comments / views) * 100

        # 종합 점수 (가중 평균)
        # 조회수(40%) + 인게이지먼트(40%) + CTR(20%)
        view_score = min(views / 10000, 1) * 40  # 1만 조회수 = 만점
        engagement_score = min(engagement_rate * 1000, 1) * 40
        ctr_score = min(ctr_estimate, 1) * 20

        performance_score = view_score + engagement_score + ctr_score

        return {
            'engagement_rate': engagement_rate,
            'ctr_estimate': ctr_estimate,
            'performance_score': performance_score
        }

    # ==================== Facebook 성과 추적 ====================

    async def track_facebook_performance(
        self,
        page_id: str,
        user_id: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Facebook 페이지 게시물 성과 추적

        Facebook Graph API 사용
        """
        with self.logger.span("facebook.track_performance"):
            # TODO: Facebook Graph API 연동
            # 현재는 구조만 정의
            self.logger.info("Facebook tracking - implementation pending")
            return []

            # 예상 구현:
            # import requests
            # url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
            # params = {
            #     'access_token': settings.FACEBOOK_ACCESS_TOKEN,
            #     'fields': 'id,message,full_picture,created_time,insights.metric(post_impressions,post_engaged_users)',
            #     'since': (datetime.now() - timedelta(days=days_back)).isoformat()
            # }
            # response = requests.get(url, params=params)
            # ...

    # ==================== Instagram 성과 추적 ====================

    async def track_instagram_performance(
        self,
        instagram_account_id: str,
        user_id: str,
        days_back: int = 30
    ) -> List[Dict]:
        """
        Instagram 비즈니스 계정 게시물 성과 추적

        Instagram Graph API 사용
        """
        with self.logger.span("instagram.track_performance"):
            # TODO: Instagram Graph API 연동
            self.logger.info("Instagram tracking - implementation pending")
            return []

    # ==================== Neo4j 성과 데이터 저장 ====================

    async def save_to_neo4j(self, performance_data: List[Dict]):
        """
        성과 데이터를 Neo4j에 그래프 형태로 저장

        그래프 구조:
        (User)-[:CREATED]->(Content)-[:HAS_THUMBNAIL]->(Thumbnail)
        (Content)-[:ACHIEVED]->(Metrics)
        (Content)-[:PUBLISHED_ON]->(Platform)
        """
        with self.logger.span("neo4j.save_performance"):
            for data in performance_data:
                # Cypher 쿼리 실행
                query = """
                MERGE (u:User {id: $user_id})
                MERGE (c:Content {
                    id: $video_id,
                    platform: $platform
                })
                SET c.title = $title,
                    c.description = $description,
                    c.published_at = datetime($published_at)

                MERGE (t:Thumbnail {url: $thumbnail_url})
                SET t.analyzed_at = datetime()

                MERGE (m:Metrics {
                    content_id: $video_id,
                    measured_at: datetime()
                })
                SET m.views = $views,
                    m.likes = $likes,
                    m.comments = $comments,
                    m.engagement_rate = $engagement_rate,
                    m.ctr_estimate = $ctr_estimate,
                    m.performance_score = $performance_score

                MERGE (u)-[:CREATED]->(c)
                MERGE (c)-[:HAS_THUMBNAIL]->(t)
                MERGE (c)-[:ACHIEVED]->(m)

                // 고성과 컨텐츠 라벨링 (performance_score >= 70)
                WITH c, m
                WHERE m.performance_score >= 70
                SET c:HighPerformance
                """

                self.neo4j.query(query, parameters=data)

            self.logger.info(f"Saved {len(performance_data)} records to Neo4j")

    # ==================== Pinecone 성과 패턴 저장 ====================

    async def save_to_pinecone(self, performance_data: List[Dict]):
        """
        고성과 썸네일을 Pinecone에 저장하여 향후 생성 시 참고

        - 고성과 (performance_score >= 70): 긍정적 패턴
        - 저성과 (performance_score < 30): 부정적 패턴 (피해야 할 패턴)
        """
        with self.logger.span("pinecone.save_performance"):
            vectors = []

            for data in performance_data:
                # 썸네일 임베딩
                embedding = await self.thumbnail_learner.embed_thumbnail(data['thumbnail_url'])

                # 성과 레벨 분류
                score = data['performance_score']
                if score >= 70:
                    performance_label = "high"
                elif score >= 40:
                    performance_label = "medium"
                else:
                    performance_label = "low"

                # 메타데이터 (자신의 컨텐츠 표시)
                metadata = {
                    'video_id': data['video_id'],
                    'title': data['title'],
                    'platform': data['platform'],
                    'views': data['views'],
                    'engagement_rate': data['engagement_rate'],
                    'performance_score': score,
                    'performance_label': performance_label,
                    'thumbnail_url': data['thumbnail_url'],
                    'is_own_content': True,  # 자신의 컨텐츠 표시
                    'user_id': data['user_id']
                }

                vectors.append((
                    f"own_{data['platform']}_{data['video_id']}",
                    embedding,
                    metadata
                ))

            # Pinecone에 배치 업로드
            self.pinecone.upsert(vectors=vectors)
            self.logger.info(f"Stored {len(vectors)} performance patterns in Pinecone")

    # ==================== 통합 자가학습 워크플로우 ====================

    async def run_self_learning_workflow(
        self,
        user_id: str,
        youtube_channel_id: Optional[str] = None,
        facebook_page_id: Optional[str] = None,
        instagram_account_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict:
        """
        멀티 플랫폼 성과 추적 및 학습 워크플로우 실행

        Returns:
            학습 결과 요약
        """
        with self.logger.span("self_learning.workflow"):
            all_performance_data = []

            # 1. YouTube 성과 추적
            if youtube_channel_id:
                yt_data = await self.track_youtube_performance(
                    youtube_channel_id,
                    user_id,
                    days_back
                )
                all_performance_data.extend(yt_data)

            # 2. Facebook 성과 추적
            if facebook_page_id:
                fb_data = await self.track_facebook_performance(
                    facebook_page_id,
                    user_id,
                    days_back
                )
                all_performance_data.extend(fb_data)

            # 3. Instagram 성과 추적
            if instagram_account_id:
                ig_data = await self.track_instagram_performance(
                    instagram_account_id,
                    user_id,
                    days_back
                )
                all_performance_data.extend(ig_data)

            if not all_performance_data:
                return {
                    'status': 'no_data',
                    'message': '추적할 컨텐츠가 없습니다.'
                }

            # 4. Neo4j에 저장
            await self.save_to_neo4j(all_performance_data)

            # 5. Pinecone에 저장
            await self.save_to_pinecone(all_performance_data)

            # 6. 성과 요약
            summary = self._generate_summary(all_performance_data)

            return {
                'status': 'completed',
                'tracked_contents': len(all_performance_data),
                'summary': summary
            }

    def _generate_summary(self, performance_data: List[Dict]) -> Dict:
        """성과 데이터 요약"""
        if not performance_data:
            return {}

        total = len(performance_data)
        high_perf = sum(1 for d in performance_data if d['performance_score'] >= 70)
        medium_perf = sum(1 for d in performance_data if 40 <= d['performance_score'] < 70)
        low_perf = sum(1 for d in performance_data if d['performance_score'] < 40)

        avg_views = sum(d['views'] for d in performance_data) / total
        avg_engagement = sum(d['engagement_rate'] for d in performance_data) / total
        avg_score = sum(d['performance_score'] for d in performance_data) / total

        # 최고 성과 컨텐츠
        best = max(performance_data, key=lambda x: x['performance_score'])

        return {
            'total_contents': total,
            'high_performance': high_perf,
            'medium_performance': medium_perf,
            'low_performance': low_perf,
            'avg_views': int(avg_views),
            'avg_engagement_rate': avg_engagement,
            'avg_performance_score': avg_score,
            'best_content': {
                'title': best['title'],
                'platform': best['platform'],
                'views': best['views'],
                'score': best['performance_score']
            }
        }

    # ==================== 자가학습 기반 썸네일 생성 ====================

    async def generate_learned_thumbnail(
        self,
        script: str,
        user_id: str,
        user_persona: Dict
    ) -> Dict:
        """
        자신의 과거 성과 + 타인의 고성과 패턴을 모두 반영한 썸네일 생성

        학습 우선순위:
        1. 자신의 고성과 컨텐츠 (70점 이상)
        2. 타인의 고성과 컨텐츠 (10만 조회수 이상)
        3. 자신의 중성과 컨텐츠 (40-70점)
        """
        with self.logger.span("generate.learned_thumbnail"):
            # 1. 키워드 추출
            keywords = await self.thumbnail_learner._extract_keywords(script)

            # 2. 자신의 고성과 컨텐츠 검색 (Neo4j)
            own_high_perf = self._query_own_high_performance(user_id, keywords)

            # 3. Pinecone에서 유사 패턴 검색 (자신 + 타인)
            text_embedding = await self.thumbnail_learner.embed_text(keywords)

            # 자신의 고성과 패턴
            own_patterns = self.pinecone.query(
                vector=text_embedding,
                top_k=5,
                filter={
                    "is_own_content": {"$eq": True},
                    "user_id": {"$eq": user_id},
                    "performance_label": {"$eq": "high"}
                },
                include_metadata=True
            )

            # 타인의 고성과 패턴
            others_patterns = await self.thumbnail_learner.find_similar_successful_thumbnails(
                keywords,
                top_k=5
            )

            # 4. DALL-E 프롬프트 생성 (학습 반영)
            prompt = self._build_learned_prompt(
                keywords,
                user_persona,
                own_patterns,
                others_patterns,
                own_high_perf
            )

            # 5. 카피 생성 (자신의 성과 패턴 반영)
            captions = await self._generate_learned_captions(
                script,
                own_high_perf,
                others_patterns
            )

            return {
                'thumbnail_prompt': prompt,
                'captions': captions,
                'learning_sources': {
                    'own_high_performance': len(own_patterns.get('matches', [])),
                    'others_high_performance': len(others_patterns),
                    'neo4j_insights': len(own_high_perf)
                }
            }

    def _query_own_high_performance(self, user_id: str, keywords: str) -> List[Dict]:
        """Neo4j에서 자신의 고성과 컨텐츠 조회"""
        query = """
        MATCH (u:User {id: $user_id})-[:CREATED]->(c:HighPerformance)-[:ACHIEVED]->(m:Metrics)
        WHERE c.title CONTAINS $keywords OR c.description CONTAINS $keywords
        RETURN c.title as title,
               c.description as description,
               m.performance_score as score,
               m.views as views
        ORDER BY m.performance_score DESC
        LIMIT 5
        """

        results = self.neo4j.query(query, {
            'user_id': user_id,
            'keywords': keywords.split()[0] if keywords else ""
        })

        return results

    def _build_learned_prompt(
        self,
        keywords: str,
        persona: Dict,
        own_patterns: Dict,
        others_patterns: List[Dict],
        neo4j_insights: List[Dict]
    ) -> str:
        """학습 데이터 기반 DALL-E 프롬프트 구성"""

        own_insights = ""
        if own_patterns.get('matches'):
            own_insights = f"""
YOUR PAST SUCCESSES (learn from these):
{chr(10).join(f"- {m['metadata']['title']} (Score: {m['metadata']['performance_score']:.1f})" for m in own_patterns['matches'][:3])}
"""

        others_insights = f"""
INDUSTRY TOP PERFORMERS:
{chr(10).join(f"- {p['title']} ({p['views']:,} views)" for p in others_patterns[:3])}
"""

        prompt = f"""
Create a YouTube thumbnail optimized for maximum performance:

Topic: {keywords}
Style: {persona.get('style', 'professional')}

{own_insights}
{others_insights}

Apply learned patterns:
- Color schemes that worked for you
- Layout compositions from top performers
- Text overlay strategies
- High contrast and eye-catching elements

Generate a thumbnail that combines YOUR proven success patterns with industry best practices.
"""

        return prompt.strip()

    async def _generate_learned_captions(
        self,
        script: str,
        own_high_perf: List[Dict],
        others_patterns: List[Dict]
    ) -> List[str]:
        """자신의 성과 + 타인의 패턴 기반 카피 생성"""

        own_titles = [p['title'] for p in own_high_perf] if own_high_perf else []
        others_titles = [p['title'] for p in others_patterns[:5]]

        system_prompt = f"""
당신은 데이터 기반 카피라이터입니다.

사용자의 과거 고성과 타이틀:
{chr(10).join(f"- {t}" for t in own_titles) if own_titles else "- (아직 데이터 없음)"}

업계 고성과 타이틀:
{chr(10).join(f"- {t}" for t in others_titles)}

사용자의 성공 패턴을 우선 반영하되, 업계 트렌드도 참고하여 카피를 작성하세요.
"""

        response = await asyncio.to_thread(
            self.thumbnail_learner.openai.chat.completions.create,
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 스크립트로 3가지 카피 작성:\n{script[:500]}"}
            ],
            temperature=0.8,
            n=3
        )

        return [choice.message.content.strip() for choice in response.choices]
