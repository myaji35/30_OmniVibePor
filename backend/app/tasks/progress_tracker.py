"""Celery 진행률 추적 및 WebSocket 이벤트 발행

이 모듈은 Celery 작업의 진행 상황을 추적하고 WebSocket을 통해
실시간으로 클라이언트에 브로드캐스트합니다.

주요 기능:
- Celery task state 업데이트
- WebSocket 진행률 브로드캐스트
- 에러 및 완료 이벤트 발행
- asyncio 이벤트 루프 관리

사용 예시:
    from app.tasks.progress_tracker import ProgressTracker

    @celery_app.task(bind=True)
    def my_task(self, project_id: str):
        tracker = ProgressTracker(
            task=self,
            project_id=project_id,
            task_name="video_generation"
        )

        tracker.update(0.1, "processing", "시작 중...")
        # ... 작업 수행 ...
        tracker.update(0.5, "processing", "절반 완료...")
        # ... 작업 수행 ...
        tracker.complete({"result": "success"})
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from celery import Task


logger = logging.getLogger(__name__)


class ProgressTracker:
    """Celery 작업 진행률 추적 및 WebSocket 브로드캐스트

    Attributes:
        task: Celery Task 인스턴스 (bind=True 필요)
        project_id: 프로젝트 ID
        task_name: 작업 이름 (예: "video_generation", "audio_generation")
        logger: 로거 인스턴스
    """

    def __init__(
        self,
        task: Task,
        project_id: str,
        task_name: str
    ):
        """ProgressTracker 초기화

        Args:
            task: Celery Task 인스턴스 (self.request 접근 위해 bind=True 필요)
            project_id: 프로젝트 ID
            task_name: 작업 이름
        """
        self.task = task
        self.project_id = project_id
        self.task_name = task_name
        self.logger = logging.getLogger(__name__)

        # 초기 상태 로깅
        self.logger.info(
            f"ProgressTracker initialized - "
            f"project: {project_id}, "
            f"task: {task_name}, "
            f"celery_id: {task.request.id}"
        )

    def update(
        self,
        progress: float,
        status: str = "processing",
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """진행률 업데이트 및 WebSocket 브로드캐스트

        Args:
            progress: 진행률 (0.0 ~ 1.0 또는 0 ~ 100)
            status: 상태 ("processing", "completed", "failed")
            message: 상태 메시지
            metadata: 추가 정보 (선택)

        Examples:
            >>> tracker.update(0.0, "processing", "작업 시작")
            >>> tracker.update(50, "processing", "절반 완료")  # 50% -> 0.5로 자동 변환
            >>> tracker.update(1.0, "completed", "완료")
        """
        # 0-100 범위를 0.0-1.0으로 정규화
        if progress > 1.0:
            progress = progress / 100.0

        # 진행률 범위 검증 (0.0 ~ 1.0)
        progress = max(0.0, min(1.0, progress))

        # Celery state 업데이트
        self.task.update_state(
            state=status.upper() if status != "processing" else "PROGRESS",
            meta={
                'progress': progress,
                'message': message,
                'metadata': metadata or {},
                'project_id': self.project_id,
                'task_name': self.task_name
            }
        )

        # 로깅
        self.logger.info(
            f"Progress: {progress*100:.1f}% - "
            f"project: {self.project_id}, "
            f"task: {self.task_name}, "
            f"status: {status}, "
            f"message: {message}"
        )

        # WebSocket 브로드캐스트 (비동기)
        self._broadcast_progress(progress, status, message, metadata)

    def _broadcast_progress(
        self,
        progress: float,
        status: str,
        message: str,
        metadata: Optional[Dict[str, Any]]
    ):
        """WebSocket으로 진행률 브로드캐스트

        Note:
            WebSocketManager가 구현되지 않은 경우 에러 로그만 남기고 계속 진행

        Args:
            progress: 진행률 (0.0 ~ 1.0)
            status: 상태
            message: 메시지
            metadata: 추가 정보
        """
        try:
            # WebSocketManager import (lazy import)
            from app.services.websocket_manager import get_websocket_manager

            manager = get_websocket_manager()

            # asyncio 이벤트 루프 생성 및 실행
            # Celery worker는 동기 환경이므로 새 이벤트 루프 필요
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(
                    manager.broadcast_progress(
                        project_id=self.project_id,
                        task_name=self.task_name,
                        progress=progress,
                        status=status,
                        message=message,
                        metadata=metadata
                    )
                )
            finally:
                loop.close()

        except ImportError:
            # WebSocketManager 미구현 시 로그만 남김
            self.logger.warning(
                f"WebSocketManager not available - progress not broadcast "
                f"(project: {self.project_id}, progress: {progress*100:.1f}%)"
            )
        except Exception as e:
            # WebSocket 브로드캐스트 실패 시에도 작업은 계속 진행
            self.logger.error(
                f"Failed to broadcast progress: {e} "
                f"(project: {self.project_id}, progress: {progress*100:.1f}%)"
            )

    def error(
        self,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """에러 브로드캐스트

        Args:
            error: 에러 메시지
            details: 에러 상세 정보 (선택)

        Examples:
            >>> tracker.error(
            ...     "TTS generation failed",
            ...     {"provider": "ElevenLabs", "code": 429}
            ... )
        """
        # Celery state 업데이트
        self.task.update_state(
            state='FAILURE',
            meta={
                'error': error,
                'details': details or {},
                'project_id': self.project_id,
                'task_name': self.task_name
            }
        )

        # 에러 로깅
        self.logger.error(
            f"Task error - "
            f"project: {self.project_id}, "
            f"task: {self.task_name}, "
            f"error: {error}, "
            f"details: {details}"
        )

        # WebSocket 브로드캐스트
        try:
            from app.services.websocket_manager import get_websocket_manager

            manager = get_websocket_manager()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(
                    manager.broadcast_error(
                        project_id=self.project_id,
                        task_name=self.task_name,
                        error=error,
                        details=details
                    )
                )
            finally:
                loop.close()

        except ImportError:
            self.logger.warning(
                f"WebSocketManager not available - error not broadcast "
                f"(project: {self.project_id})"
            )
        except Exception as e:
            self.logger.error(f"Failed to broadcast error: {e}")

    def complete(
        self,
        result: Dict[str, Any]
    ):
        """완료 브로드캐스트

        Args:
            result: 작업 결과

        Examples:
            >>> tracker.complete({
            ...     "final_video_path": "/path/to/video.mp4",
            ...     "duration": 60.5,
            ...     "cost_usd": 0.45
            ... })
        """
        # Celery state 업데이트
        self.task.update_state(
            state='SUCCESS',
            meta={
                'progress': 1.0,
                'message': 'Completed',
                'result': result,
                'project_id': self.project_id,
                'task_name': self.task_name
            }
        )

        # 완료 로깅
        self.logger.info(
            f"Task completed - "
            f"project: {self.project_id}, "
            f"task: {self.task_name}, "
            f"result: {result}"
        )

        # WebSocket 브로드캐스트
        try:
            from app.services.websocket_manager import get_websocket_manager

            manager = get_websocket_manager()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(
                    manager.broadcast_completion(
                        project_id=self.project_id,
                        task_name=self.task_name,
                        result=result
                    )
                )
            finally:
                loop.close()

        except ImportError:
            self.logger.warning(
                f"WebSocketManager not available - completion not broadcast "
                f"(project: {self.project_id})"
            )
        except Exception as e:
            self.logger.error(f"Failed to broadcast completion: {e}")


class BatchProgressTracker:
    """배치 작업 진행률 추적

    여러 하위 작업의 진행률을 통합하여 전체 진행률 계산

    Examples:
        >>> batch_tracker = BatchProgressTracker(
        ...     task=self,
        ...     project_id="batch_123",
        ...     task_name="batch_video_generation",
        ...     total_items=10
        ... )
        >>>
        >>> for i in range(10):
        ...     # 각 아이템 처리
        ...     batch_tracker.update_item(i, 1.0, "completed", f"Item {i} done")
    """

    def __init__(
        self,
        task: Task,
        project_id: str,
        task_name: str,
        total_items: int
    ):
        """BatchProgressTracker 초기화

        Args:
            task: Celery Task 인스턴스
            project_id: 프로젝트 ID
            task_name: 작업 이름
            total_items: 전체 아이템 수
        """
        self.base_tracker = ProgressTracker(task, project_id, task_name)
        self.total_items = total_items
        self.completed_items = 0
        self.item_progress = {}  # {item_idx: progress_value}

    def update_item(
        self,
        item_idx: int,
        item_progress: float,
        status: str = "processing",
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """개별 아이템 진행률 업데이트

        Args:
            item_idx: 아이템 인덱스 (0부터 시작)
            item_progress: 아이템 진행률 (0.0 ~ 1.0)
            status: 상태
            message: 메시지
            metadata: 추가 정보
        """
        # 아이템 진행률 저장
        self.item_progress[item_idx] = item_progress

        # 아이템 완료 카운트
        if item_progress >= 1.0:
            self.completed_items = sum(
                1 for p in self.item_progress.values() if p >= 1.0
            )

        # 전체 진행률 계산 (각 아이템의 평균)
        overall_progress = sum(self.item_progress.values()) / self.total_items

        # 메시지 생성
        batch_message = (
            f"{message} "
            f"({self.completed_items}/{self.total_items} items completed)"
        )

        # 전체 진행률 업데이트
        self.base_tracker.update(
            progress=overall_progress,
            status=status,
            message=batch_message,
            metadata={
                **(metadata or {}),
                'completed_items': self.completed_items,
                'total_items': self.total_items,
                'current_item': item_idx
            }
        )

    def complete(self, result: Dict[str, Any]):
        """배치 작업 완료"""
        self.base_tracker.complete(result)

    def error(self, error: str, details: Optional[Dict[str, Any]] = None):
        """배치 작업 에러"""
        self.base_tracker.error(error, details)
