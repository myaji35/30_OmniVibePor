"""WebSocket 연결 관리자

프로젝트별로 여러 클라이언트의 WebSocket 연결을 관리하고,
Celery 작업 진행 상태를 실시간으로 브로드캐스트합니다.
"""

from typing import Dict, List, Set
from fastapi import WebSocket
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # project_id: Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket, project_id: str):
        """클라이언트 연결"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()

        self.active_connections[project_id].add(websocket)
        self.logger.info(
            f"WebSocket connected: project={project_id}, "
            f"total={len(self.active_connections[project_id])}"
        )

    def disconnect(self, websocket: WebSocket, project_id: str):
        """클라이언트 연결 해제"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)

            # 연결이 없으면 삭제
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

        self.logger.info(f"WebSocket disconnected: project={project_id}")

    async def send_to_project(self, project_id: str, message: dict):
        """특정 프로젝트의 모든 클라이언트에게 메시지 전송"""
        if project_id not in self.active_connections:
            self.logger.warning(
                f"No active connections for project: {project_id}"
            )
            return

        disconnected = []

        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                disconnected.append(websocket)

        # 연결 끊긴 클라이언트 정리
        for ws in disconnected:
            self.disconnect(ws, project_id)

    async def broadcast_progress(
        self,
        project_id: str,
        task_name: str,
        progress: float,
        status: str,
        message: str = "",
        metadata: dict = None
    ):
        """진행률 브로드캐스트

        Args:
            project_id: 프로젝트 ID
            task_name: 작업 이름
            progress: 진행률 (0.0 ~ 1.0)
            status: 작업 상태 (pending, in_progress, completed, failed)
            message: 상세 메시지
            metadata: 추가 메타데이터

        Example:
            await manager.broadcast_progress(
                project_id="campaign_001",
                task_name="audio_generation",
                progress=0.5,
                status="in_progress",
                message="Generating TTS audio...",
                metadata={"file_size": 1024, "duration": 60}
            )
        """
        event = {
            "type": "progress",
            "project_id": project_id,
            "task_name": task_name,
            "progress": progress,
            "status": status,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        await self.send_to_project(project_id, event)

    async def broadcast_error(
        self,
        project_id: str,
        task_name: str,
        error: str,
        details: dict = None
    ):
        """에러 브로드캐스트

        Args:
            project_id: 프로젝트 ID
            task_name: 작업 이름
            error: 에러 메시지
            details: 에러 상세 정보

        Example:
            await manager.broadcast_error(
                project_id="campaign_001",
                task_name="audio_generation",
                error="TTS API rate limit exceeded",
                details={"retry_after": 60, "error_code": "429"}
            )
        """
        event = {
            "type": "error",
            "project_id": project_id,
            "task_name": task_name,
            "error": error,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }

        await self.send_to_project(project_id, event)

    async def broadcast_completion(
        self,
        project_id: str,
        task_name: str,
        result: dict
    ):
        """완료 이벤트 브로드캐스트

        Args:
            project_id: 프로젝트 ID
            task_name: 작업 이름
            result: 작업 결과

        Example:
            await manager.broadcast_completion(
                project_id="campaign_001",
                task_name="audio_generation",
                result={
                    "audio_url": "https://cdn.example.com/audio.mp3",
                    "duration": 60.5,
                    "accuracy": 0.98
                }
            )
        """
        event = {
            "type": "completed",
            "project_id": project_id,
            "task_name": task_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        await self.send_to_project(project_id, event)

    async def broadcast_status(
        self,
        project_id: str,
        task_name: str,
        status: str,
        message: str = "",
        metadata: dict = None
    ):
        """작업 상태 변경 브로드캐스트

        Args:
            project_id: 프로젝트 ID
            task_name: 작업 이름
            status: 작업 상태 (queued, started, retry, revoked)
            message: 상세 메시지
            metadata: 추가 메타데이터

        Example:
            await manager.broadcast_status(
                project_id="campaign_001",
                task_name="audio_generation",
                status="retry",
                message="Retrying due to temporary error",
                metadata={"attempt": 2, "max_retries": 3}
            )
        """
        event = {
            "type": "status",
            "project_id": project_id,
            "task_name": task_name,
            "status": status,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        await self.send_to_project(project_id, event)

    def get_connection_count(self, project_id: str) -> int:
        """특정 프로젝트의 활성 연결 수 반환"""
        return len(self.active_connections.get(project_id, set()))

    def get_all_connection_counts(self) -> Dict[str, int]:
        """모든 프로젝트의 활성 연결 수 반환"""
        return {
            project_id: len(connections)
            for project_id, connections in self.active_connections.items()
        }


# 싱글톤 인스턴스
_manager: ConnectionManager = None


def get_websocket_manager() -> ConnectionManager:
    """WebSocket Manager 싱글톤

    Returns:
        ConnectionManager 인스턴스

    Example:
        from app.services.websocket_manager import get_websocket_manager

        manager = get_websocket_manager()
        await manager.broadcast_progress(
            project_id="campaign_001",
            task_name="audio_generation",
            progress=0.5,
            status="in_progress"
        )
    """
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
