"""진행률 계산 헬퍼

작업 단계별로 전체 진행률을 계산하는 유틸리티.
각 에이전트/워크플로우의 단계별 가중치를 정의하고,
현재 단계와 하위 진행률을 기반으로 전체 진행률을 계산합니다.

사용 예시:
    # Director Agent 워크플로우
    progress = ProgressMapper.get_director_progress(
        step="generate_videos",
        sub_progress=0.5  # 영상 생성 50% 완료
    )
    # -> 0.45 반환 (전체 진행률 45%)

    # Audio Agent 워크플로우
    progress = ProgressMapper.get_audio_progress(
        step="stt_verification",
        sub_progress=0.8
    )
    # -> 0.64 반환
"""

from typing import Dict, List, Tuple


class ProgressMapper:
    """작업 단계별 진행률 매핑

    각 에이전트 워크플로우의 단계별 가중치를 정의하고
    전체 진행률을 계산합니다.
    """

    # ==================== Director Agent 워크플로우 ====================
    # 각 단계의 **시작 진행률**을 정의
    # 예: "generate_videos": 0.10 → 영상 생성 시작 시점이 전체 10%
    DIRECTOR_STEPS = {
        "start": 0.0,                 # 시작 (0%)
        "load_character": 0.05,       # 캐릭터 로드 시작 (5%)
        "parse_script": 0.10,         # 스크립트 분석 시작 (10%)
        "generate_videos": 0.10,      # 영상 생성 시작 (10% → 60% 범위, 시작점)
        "lipsync": 0.60,              # 립싱크 시작 (60% → 75% 범위, 시작점)
        "subtitles": 0.75,            # 자막 생성 시작 (75% → 85% 범위, 시작점)
        "render": 0.85,               # 최종 렌더링 시작 (85% → 95% 범위, 시작점)
        "complete": 1.0               # 완료 (100%)
    }

    # ==================== Audio Agent 워크플로우 ====================
    # 각 단계의 **시작 진행률**을 정의
    AUDIO_STEPS = {
        "start": 0.0,                 # 시작 (0%)
        "normalize_text": 0.05,       # 텍스트 정규화 시작 (5%)
        "tts_generation": 0.05,       # TTS 생성 시작 (5% → 30% 범위, 시작점)
        "stt_verification": 0.30,     # STT 검증 시작 (30% → 60% 범위, 시작점)
        "similarity_check": 0.60,     # 유사도 체크 시작 (60% → 70% 범위, 시작점)
        "retry_loop": 0.70,           # 재시도 루프 시작 (70% → 90% 범위, 시작점)
        "save_file": 0.90,            # 파일 저장 시작 (90% → 95% 범위, 시작점)
        "complete": 1.0               # 완료 (100%)
    }

    # ==================== Writer Agent 워크플로우 ====================
    WRITER_STEPS = {
        "start": 0.0,
        "load_persona": 0.10,         # 페르소나 로드 (10%)
        "load_strategy": 0.20,        # 전략 로드 (20%)
        "generate_hooks": 0.40,       # 훅 생성 (20% → 40%)
        "generate_body": 0.70,        # 본문 생성 (40% → 70%)
        "generate_cta": 0.85,         # CTA 생성 (85%)
        "optimize_platform": 0.95,    # 플랫폼 최적화 (95%)
        "complete": 1.0               # 완료 (100%)
    }

    # ==================== Video Tasks (Lipsync) 워크플로우 ====================
    LIPSYNC_STEPS = {
        "start": 0.0,
        "upload_video": 0.20,         # 비디오 업로드 (20%)
        "upload_audio": 0.30,         # 오디오 업로드 (30%)
        "processing": 0.80,           # 립싱크 처리 (30% → 80%)
        "download": 0.95,             # 다운로드 (95%)
        "complete": 1.0               # 완료 (100%)
    }

    @staticmethod
    def get_progress(
        step_mapping: Dict[str, float],
        step: str,
        sub_progress: float = 0.0
    ) -> float:
        """단계별 진행률 계산

        Args:
            step_mapping: 단계 매핑 딕셔너리
            step: 현재 단계 이름
            sub_progress: 현재 단계 내 진행률 (0.0 ~ 1.0)

        Returns:
            전체 진행률 (0.0 ~ 1.0)

        Examples:
            >>> ProgressMapper.get_progress(
            ...     ProgressMapper.DIRECTOR_STEPS,
            ...     "generate_videos",
            ...     0.5
            ... )
            0.35  # 10% + (60% - 10%) * 0.5 = 35%
        """
        steps = list(step_mapping.keys())

        # 단계가 존재하지 않으면 0.0 반환
        if step not in steps:
            return 0.0

        current_idx = steps.index(step)

        # 마지막 단계면 1.0 반환
        if current_idx == len(steps) - 1:
            return 1.0

        # 현재 단계의 시작 진행률
        current_progress = step_mapping[step]

        # 다음 단계의 시작 진행률
        next_progress = step_mapping[steps[current_idx + 1]]

        # 현재 단계 내 진행률을 전체 진행률로 변환
        # 예: generate_videos (10% → 60%)에서 sub_progress=0.5면
        #     10% + (60% - 10%) * 0.5 = 35%
        return current_progress + (next_progress - current_progress) * sub_progress

    @staticmethod
    def get_director_progress(step: str, sub_progress: float = 0.0) -> float:
        """Director Agent 진행률 계산

        Args:
            step: 현재 단계 ("start", "load_character", "parse_script", ...)
            sub_progress: 현재 단계 내 진행률 (0.0 ~ 1.0)

        Returns:
            전체 진행률 (0.0 ~ 1.0)
        """
        return ProgressMapper.get_progress(
            ProgressMapper.DIRECTOR_STEPS,
            step,
            sub_progress
        )

    @staticmethod
    def get_audio_progress(step: str, sub_progress: float = 0.0) -> float:
        """Audio Agent 진행률 계산

        Args:
            step: 현재 단계 ("start", "normalize_text", "tts_generation", ...)
            sub_progress: 현재 단계 내 진행률 (0.0 ~ 1.0)

        Returns:
            전체 진행률 (0.0 ~ 1.0)
        """
        return ProgressMapper.get_progress(
            ProgressMapper.AUDIO_STEPS,
            step,
            sub_progress
        )

    @staticmethod
    def get_writer_progress(step: str, sub_progress: float = 0.0) -> float:
        """Writer Agent 진행률 계산

        Args:
            step: 현재 단계 ("start", "load_persona", "generate_hooks", ...)
            sub_progress: 현재 단계 내 진행률 (0.0 ~ 1.0)

        Returns:
            전체 진행률 (0.0 ~ 1.0)
        """
        return ProgressMapper.get_progress(
            ProgressMapper.WRITER_STEPS,
            step,
            sub_progress
        )

    @staticmethod
    def get_lipsync_progress(step: str, sub_progress: float = 0.0) -> float:
        """Lipsync 작업 진행률 계산

        Args:
            step: 현재 단계 ("start", "upload_video", "processing", ...)
            sub_progress: 현재 단계 내 진행률 (0.0 ~ 1.0)

        Returns:
            전체 진행률 (0.0 ~ 1.0)
        """
        return ProgressMapper.get_progress(
            ProgressMapper.LIPSYNC_STEPS,
            step,
            sub_progress
        )

    @staticmethod
    def get_step_list(workflow: str) -> List[str]:
        """워크플로우의 단계 목록 반환

        Args:
            workflow: 워크플로우 이름 ("director", "audio", "writer", "lipsync")

        Returns:
            단계 이름 리스트
        """
        workflow_map = {
            "director": ProgressMapper.DIRECTOR_STEPS,
            "audio": ProgressMapper.AUDIO_STEPS,
            "writer": ProgressMapper.WRITER_STEPS,
            "lipsync": ProgressMapper.LIPSYNC_STEPS
        }

        if workflow not in workflow_map:
            return []

        return list(workflow_map[workflow].keys())

    @staticmethod
    def get_step_range(workflow: str, step: str) -> Tuple[float, float]:
        """특정 단계의 진행률 범위 반환

        Args:
            workflow: 워크플로우 이름
            step: 단계 이름

        Returns:
            (시작_진행률, 종료_진행률) 튜플

        Examples:
            >>> ProgressMapper.get_step_range("director", "generate_videos")
            (0.10, 0.60)
        """
        workflow_map = {
            "director": ProgressMapper.DIRECTOR_STEPS,
            "audio": ProgressMapper.AUDIO_STEPS,
            "writer": ProgressMapper.WRITER_STEPS,
            "lipsync": ProgressMapper.LIPSYNC_STEPS
        }

        if workflow not in workflow_map:
            return (0.0, 0.0)

        steps = workflow_map[workflow]
        if step not in steps:
            return (0.0, 0.0)

        step_list = list(steps.keys())
        current_idx = step_list.index(step)

        start = steps[step]
        end = steps[step_list[current_idx + 1]] if current_idx < len(step_list) - 1 else 1.0

        return (start, end)


class MultiStepProgressCalculator:
    """다단계 작업 진행률 계산기

    여러 단계로 구성된 복잡한 워크플로우의 진행률을 계산합니다.

    Examples:
        >>> calculator = MultiStepProgressCalculator([
        ...     ("audio", 0.3),      # 오디오 생성 30% 가중치
        ...     ("video", 0.6),      # 영상 생성 60% 가중치
        ...     ("subtitle", 0.1)    # 자막 10% 가중치
        ... ])
        >>>
        >>> calculator.update("audio", 1.0)  # 오디오 완료
        >>> calculator.update("video", 0.5)  # 영상 50% 완료
        >>> calculator.get_overall_progress()
        0.6  # 30% * 1.0 + 60% * 0.5 + 10% * 0.0 = 60%
    """

    def __init__(self, steps: List[Tuple[str, float]]):
        """다단계 진행률 계산기 초기화

        Args:
            steps: [(단계명, 가중치), ...] 리스트
                   가중치 합은 1.0이어야 함
        """
        self.steps = steps
        self.progress = {step: 0.0 for step, _ in steps}

        # 가중치 합 검증
        total_weight = sum(weight for _, weight in steps)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                f"Step weights must sum to 1.0, got {total_weight}"
            )

    def update(self, step: str, progress: float):
        """특정 단계의 진행률 업데이트

        Args:
            step: 단계 이름
            progress: 진행률 (0.0 ~ 1.0)
        """
        if step in self.progress:
            self.progress[step] = max(0.0, min(1.0, progress))

    def get_overall_progress(self) -> float:
        """전체 진행률 계산

        Returns:
            전체 진행률 (0.0 ~ 1.0)
        """
        total = 0.0
        for step, weight in self.steps:
            total += self.progress[step] * weight
        return total

    def get_remaining_time_estimate(
        self,
        elapsed_time: float
    ) -> float:
        """남은 시간 추정

        Args:
            elapsed_time: 경과 시간 (초)

        Returns:
            예상 남은 시간 (초)
        """
        current_progress = self.get_overall_progress()
        if current_progress < 0.01:
            return float('inf')

        total_estimated_time = elapsed_time / current_progress
        return total_estimated_time - elapsed_time
