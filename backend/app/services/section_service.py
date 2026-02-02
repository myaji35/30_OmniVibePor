"""섹션(콘티) 관리 서비스

콘티 섹션(훅/본문/CTA) 정보를 Neo4j에서 조회하고 관리합니다.
"""
from typing import List, Dict, Optional, Any
import logging
import os
import subprocess
from pathlib import Path

from app.services.neo4j_client import Neo4jClient
from app.models.neo4j_models import (
    SectionType,
    SectionDetailModel,
    SectionMetadataModel,
    ProjectSectionsResponse
)

logger = logging.getLogger(__name__)


class SectionService:
    """섹션(콘티) 관리 서비스"""

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Args:
            neo4j_client: Neo4j 클라이언트 인스턴스
        """
        self.client = neo4j_client

    def get_project_sections(self, project_id: str) -> ProjectSectionsResponse:
        """
        프로젝트의 모든 섹션 정보 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            프로젝트 섹션 응답 객체

        Raises:
            ValueError: 프로젝트를 찾을 수 없는 경우
        """
        # 1. Neo4j에서 섹션 정보 조회
        query = """
        MATCH (proj:Project {project_id: $project_id})
        OPTIONAL MATCH (proj)-[:HAS_SECTION]->(s:Section)
        RETURN proj.project_id as project_id,
               collect({
                   section_id: s.section_id,
                   type: s.type,
                   order: s.order,
                   script: s.script,
                   start_time: s.start_time,
                   end_time: s.end_time,
                   duration: s.duration,
                   video_clip_path: s.video_clip_path,
                   audio_segment_path: s.audio_segment_path,
                   thumbnail_url: s.thumbnail_url,
                   word_count: s.word_count,
                   estimated_duration: s.estimated_duration,
                   actual_duration: s.actual_duration
               }) as sections
        ORDER BY s.order
        """

        results = self.client.query(query, {"project_id": project_id})

        if not results:
            raise ValueError(f"Project not found: {project_id}")

        result = results[0]
        sections_data = result.get("sections", [])

        # 2. None 필터링 및 섹션 객체 생성
        sections = []
        total_duration = 0.0

        for section_data in sections_data:
            # None 값 체크 (섹션이 없는 경우)
            if not section_data.get("section_id"):
                continue

            metadata = SectionMetadataModel(
                word_count=section_data.get("word_count", 0),
                estimated_duration=section_data.get("estimated_duration", 0.0),
                actual_duration=section_data.get("actual_duration", 0.0)
            )

            section = SectionDetailModel(
                section_id=section_data["section_id"],
                type=SectionType(section_data["type"]),
                order=section_data["order"],
                script=section_data.get("script", ""),
                start_time=section_data.get("start_time", 0.0),
                end_time=section_data.get("end_time", 0.0),
                duration=section_data.get("duration", 0.0),
                video_clip_path=section_data.get("video_clip_path"),
                audio_segment_path=section_data.get("audio_segment_path"),
                thumbnail_url=section_data.get("thumbnail_url"),
                metadata=metadata
            )

            sections.append(section)
            total_duration += section.duration

        return ProjectSectionsResponse(
            project_id=project_id,
            sections=sections,
            total_duration=total_duration
        )

    def create_section(
        self,
        project_id: str,
        section_type: SectionType,
        order: int,
        script: str,
        start_time: float = 0.0,
        end_time: float = 0.0,
        word_count: int = 0,
        estimated_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        섹션 생성

        Args:
            project_id: 프로젝트 ID
            section_type: 섹션 타입 (hook, body, cta)
            order: 섹션 순서
            script: 스크립트 내용
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)
            word_count: 단어 수
            estimated_duration: 예상 시간 (초)

        Returns:
            생성된 섹션 정보
        """
        import uuid

        section_id = f"section_{uuid.uuid4().hex[:12]}"
        duration = end_time - start_time

        query = """
        MATCH (proj:Project {project_id: $project_id})
        CREATE (s:Section {
            section_id: $section_id,
            type: $type,
            order: $order,
            script: $script,
            start_time: $start_time,
            end_time: $end_time,
            duration: $duration,
            word_count: $word_count,
            estimated_duration: $estimated_duration,
            actual_duration: $duration,
            created_at: datetime()
        })
        CREATE (proj)-[:HAS_SECTION]->(s)
        RETURN s.section_id as section_id,
               s.type as type,
               s.order as order,
               s.script as script,
               s.start_time as start_time,
               s.end_time as end_time,
               s.duration as duration
        """

        result = self.client.query(query, {
            "project_id": project_id,
            "section_id": section_id,
            "type": section_type.value,
            "order": order,
            "script": script,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "word_count": word_count,
            "estimated_duration": estimated_duration
        })

        if result:
            logger.info(f"Created section {section_id} for project {project_id}")
            return result[0]
        else:
            raise ValueError(f"Failed to create section for project {project_id}")

    def update_section_media(
        self,
        section_id: str,
        video_clip_path: Optional[str] = None,
        audio_segment_path: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> bool:
        """
        섹션 미디어 정보 업데이트

        Args:
            section_id: 섹션 ID
            video_clip_path: 비디오 클립 경로
            audio_segment_path: 오디오 세그먼트 경로
            thumbnail_url: 썸네일 URL

        Returns:
            업데이트 성공 여부
        """
        updates = {}
        if video_clip_path is not None:
            updates["video_clip_path"] = video_clip_path
        if audio_segment_path is not None:
            updates["audio_segment_path"] = audio_segment_path
        if thumbnail_url is not None:
            updates["thumbnail_url"] = thumbnail_url

        if not updates:
            return False

        set_clauses = ", ".join([f"s.{key} = ${key}" for key in updates.keys()])
        query = f"""
        MATCH (s:Section {{section_id: $section_id}})
        SET {set_clauses}
        RETURN s.section_id as section_id
        """

        params = {"section_id": section_id, **updates}
        result = self.client.query(query, params)

        if result:
            logger.info(f"Updated media for section {section_id}: {list(updates.keys())}")
            return True
        else:
            logger.warning(f"Section not found: {section_id}")
            return False

    def generate_section_thumbnail(
        self,
        section_id: str,
        video_path: str,
        timestamp: float,
        output_dir: str = "/tmp/thumbnails"
    ) -> Optional[str]:
        """
        FFmpeg를 사용하여 섹션별 썸네일 생성

        Args:
            section_id: 섹션 ID
            video_path: 비디오 파일 경로
            timestamp: 썸네일 추출 시간 (초)
            output_dir: 출력 디렉토리

        Returns:
            생성된 썸네일 경로 (실패 시 None)
        """
        try:
            # 출력 디렉토리 생성
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # 썸네일 파일명
            thumbnail_filename = f"{section_id}_thumbnail.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)

            # FFmpeg 명령어
            command = [
                "ffmpeg",
                "-ss", str(timestamp),  # 시간 지정
                "-i", video_path,  # 입력 비디오
                "-vframes", "1",  # 1 프레임만 추출
                "-q:v", "2",  # 품질 (1-31, 낮을수록 좋음)
                "-y",  # 덮어쓰기
                thumbnail_path
            ]

            # FFmpeg 실행
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )

            if result.returncode == 0 and os.path.exists(thumbnail_path):
                logger.info(f"Generated thumbnail for section {section_id}: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.error(f"FFmpeg failed: {result.stderr.decode('utf-8')}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout for section {section_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for section {section_id}: {e}")
            return None

    def delete_section(self, section_id: str) -> bool:
        """
        섹션 삭제

        Args:
            section_id: 섹션 ID

        Returns:
            삭제 성공 여부
        """
        query = """
        MATCH (s:Section {section_id: $section_id})
        DETACH DELETE s
        RETURN count(s) as deleted_count
        """

        result = self.client.query(query, {"section_id": section_id})
        deleted_count = result[0]["deleted_count"] if result else 0

        if deleted_count > 0:
            logger.info(f"Deleted section {section_id}")
            return True
        else:
            logger.warning(f"Section not found: {section_id}")
            return False


def get_section_service(neo4j_client: Neo4jClient) -> SectionService:
    """섹션 서비스 팩토리 함수"""
    return SectionService(neo4j_client)
