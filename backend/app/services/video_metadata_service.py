"""비디오 메타데이터 추출 서비스

FFmpeg의 ffprobe를 사용하여 영상 파일의 메타데이터를 추출합니다.
"""
import subprocess
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoMetadataService:
    """비디오 메타데이터 추출 서비스"""

    def __init__(self):
        """FFmpeg/ffprobe 사용 가능 여부 확인"""
        self.ffprobe_available = self._check_ffprobe()

    def _check_ffprobe(self) -> bool:
        """ffprobe 명령어 사용 가능 여부 확인"""
        try:
            subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            logger.info("ffprobe is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffprobe is not available. Install FFmpeg to use this service.")
            return False

    def extract_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        FFmpeg ffprobe를 사용하여 비디오 메타데이터 추출

        Args:
            video_path: 비디오 파일 경로

        Returns:
            메타데이터 딕셔너리 (실패 시 None)
        """
        if not self.ffprobe_available:
            logger.error("ffprobe is not available")
            return None

        # 파일 존재 확인
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        try:
            # ffprobe 명령어 실행
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            # JSON 파싱
            metadata = json.loads(result.stdout)

            # 메타데이터 정리
            parsed = self._parse_ffprobe_output(metadata, video_path)

            logger.info(f"Successfully extracted metadata from {video_path}")
            return parsed

        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe command failed: {e}")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"ffprobe timeout for {video_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ffprobe output: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting metadata: {e}")
            return None

    def _parse_ffprobe_output(self, metadata: Dict[str, Any], video_path: str) -> Dict[str, Any]:
        """
        ffprobe 출력을 파싱하여 필요한 정보만 추출

        Args:
            metadata: ffprobe 원본 출력
            video_path: 비디오 파일 경로

        Returns:
            정리된 메타데이터
        """
        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])

        # 비디오 스트림 찾기
        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"),
            None
        )

        # 오디오 스트림 찾기
        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"),
            None
        )

        # 기본값 설정
        parsed = {
            "video_path": video_path,
            "duration": float(format_info.get("duration", 0)),
            "file_size": int(format_info.get("size", 0)),
            "bitrate": int(format_info.get("bit_rate", 0)),
            "format_name": format_info.get("format_name", "unknown"),
            "codec": None,
            "frame_rate": None,
            "resolution": {"width": 0, "height": 0},
            "audio_codec": None,
        }

        # 비디오 스트림 정보
        if video_stream:
            parsed["codec"] = video_stream.get("codec_name", "unknown")
            parsed["resolution"]["width"] = video_stream.get("width", 0)
            parsed["resolution"]["height"] = video_stream.get("height", 0)

            # 프레임 레이트 계산
            r_frame_rate = video_stream.get("r_frame_rate", "0/1")
            if "/" in r_frame_rate:
                num, denom = r_frame_rate.split("/")
                try:
                    parsed["frame_rate"] = float(num) / float(denom) if float(denom) != 0 else 0
                except (ValueError, ZeroDivisionError):
                    parsed["frame_rate"] = 0
            else:
                parsed["frame_rate"] = float(r_frame_rate)

        # 오디오 스트림 정보
        if audio_stream:
            parsed["audio_codec"] = audio_stream.get("codec_name", "unknown")

        return parsed

    def get_video_sections(
        self,
        neo4j_client,
        project_id: str,
        video_id: str
    ) -> List[Dict[str, Any]]:
        """
        Neo4j에서 비디오 섹션 정보 조회

        Args:
            neo4j_client: Neo4j 클라이언트
            project_id: 프로젝트 ID
            video_id: 비디오 ID

        Returns:
            섹션 목록 (hook, body, cta 등)
        """
        try:
            # TODO: Neo4j에 섹션 정보가 저장되어 있다면 조회
            # 현재는 더미 데이터 반환 (추후 구현)
            query = """
            MATCH (proj:Project {project_id: $project_id})
                  -[:HAS_VIDEO]->(v:Video {video_id: $video_id})
            OPTIONAL MATCH (v)-[:HAS_SECTION]->(sec:Section)
            RETURN sec.type as type,
                   sec.start_time as start_time,
                   sec.end_time as end_time,
                   sec.duration as duration
            ORDER BY sec.start_time
            """

            results = neo4j_client.query(
                query,
                {"project_id": project_id, "video_id": video_id}
            )

            # 섹션 정보가 없으면 빈 리스트 반환
            sections = []
            for row in results:
                if row.get("type"):  # 섹션이 존재하는 경우만
                    sections.append({
                        "type": row["type"],
                        "start_time": float(row["start_time"] or 0),
                        "end_time": float(row["end_time"] or 0),
                        "duration": float(row["duration"] or 0)
                    })

            return sections

        except Exception as e:
            logger.error(f"Failed to get video sections from Neo4j: {e}")
            return []


# 싱글톤 인스턴스
_video_metadata_service_instance = None


def get_video_metadata_service() -> VideoMetadataService:
    """비디오 메타데이터 서비스 싱글톤 인스턴스"""
    global _video_metadata_service_instance
    if _video_metadata_service_instance is None:
        _video_metadata_service_instance = VideoMetadataService()
    return _video_metadata_service_instance
