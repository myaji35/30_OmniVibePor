"""Whisper Timestamps 기반 슬라이드 타이밍 분석 서비스"""
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import logging
from contextlib import nullcontext

from app.models.neo4j_models import (
    SlideTimingModel,
    SlideScriptModel,
    WhisperResultModel,
    WhisperSegmentModel
)
from app.services.neo4j_client import get_neo4j_client
from app.core.config import get_settings

settings = get_settings()

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class SlideTimingAnalyzer:
    """
    Whisper STT 타임스탬프를 분석하여 슬라이드별 타이밍을 자동 매칭

    주요 기능:
    - Whisper 세그먼트와 슬라이드 스크립트 매칭 (difflib 기반)
    - 슬라이드별 시작/종료 시간 자동 계산
    - 타이밍 정확도 검증 (90% 이상)
    - Neo4j Slide 노드에 타이밍 정보 업데이트
    """

    # 매칭 신뢰도 임계값
    MIN_SIMILARITY_THRESHOLD = 0.80  # 80% 이상 유사도
    HIGH_CONFIDENCE_THRESHOLD = 0.90  # 90% 이상 고신뢰도

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j_client = get_neo4j_client()

    async def analyze_timing(
        self,
        whisper_result: Dict[str, Any],
        slide_scripts: List[Dict[str, str]],
        audio_path: str,
        project_id: Optional[str] = None
    ) -> List[SlideTimingModel]:
        """
        Whisper 결과를 분석하여 슬라이드 타이밍 매칭

        Args:
            whisper_result: Whisper API 응답 (verbose_json 형식)
            slide_scripts: 슬라이드별 스크립트 [{"slide_number": 1, "script": "..."}]
            audio_path: 오디오 파일 경로 (메타데이터용)
            project_id: 프로젝트 ID (Neo4j 업데이트용, 옵션)

        Returns:
            슬라이드 타이밍 리스트
        """
        span_context = logfire.span("slide_timing.analyze") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as span:
            if LOGFIRE_AVAILABLE:
                span.set_attribute("total_slides", len(slide_scripts))
                span.set_attribute("audio_path", audio_path)

            # Whisper 결과 파싱
            whisper_model = WhisperResultModel(**whisper_result)
            self.logger.info(
                f"Analyzing timing for {len(slide_scripts)} slides "
                f"with {len(whisper_model.segments)} Whisper segments"
            )

            # 슬라이드 스크립트를 SlideScriptModel로 변환
            slide_models = [SlideScriptModel(**s) for s in slide_scripts]

            # 슬라이드별 타이밍 계산
            slide_timings = []
            for slide in slide_models:
                timing = await self._analyze_slide_timing(
                    slide=slide,
                    segments=whisper_model.segments,
                    total_duration=whisper_model.duration
                )
                slide_timings.append(timing)

            # 타이밍 조정 (겹침 제거, 갭 최소화)
            adjusted_timings = self.adjust_timing(
                slide_timings=slide_timings,
                total_audio_duration=whisper_model.duration
            )

            # 정확도 검증
            expected_durations = [t.duration for t in slide_timings]
            accuracy = self.validate_timing_accuracy(
                slide_timings=adjusted_timings,
                expected_durations=expected_durations
            )

            self.logger.info(
                f"Timing analysis completed with {accuracy:.2f}% accuracy. "
                f"Average confidence: {sum(t.confidence for t in adjusted_timings) / len(adjusted_timings):.2f}"
            )

            # Neo4j 업데이트 (project_id가 제공된 경우)
            if project_id:
                await self._update_neo4j_timings(
                    project_id=project_id,
                    slide_timings=adjusted_timings
                )

            return adjusted_timings

    async def _analyze_slide_timing(
        self,
        slide: SlideScriptModel,
        segments: List[WhisperSegmentModel],
        total_duration: float
    ) -> SlideTimingModel:
        """
        단일 슬라이드의 타이밍 분석

        Args:
            slide: 슬라이드 스크립트 모델
            segments: Whisper 세그먼트 리스트
            total_duration: 전체 오디오 길이

        Returns:
            슬라이드 타이밍 모델
        """
        # 스크립트와 세그먼트 매칭
        matched_segment_indices = self.match_script_to_segments(
            script=slide.script,
            segments=segments
        )

        if not matched_segment_indices:
            self.logger.warning(
                f"No matching segments found for slide {slide.slide_number}. "
                f"Using zero timing."
            )
            return SlideTimingModel(
                slide_number=slide.slide_number,
                start_time=0.0,
                end_time=0.0,
                duration=0.0,
                confidence=0.0,
                matched_text=""
            )

        # 매칭된 세그먼트에서 타이밍 계산
        matched_segments = [segments[i] for i in matched_segment_indices]
        timing_info = self.calculate_slide_timing(matched_segments)

        # 매칭된 텍스트 결합
        matched_text = " ".join([seg.text.strip() for seg in matched_segments])

        # 신뢰도 계산 (스크립트와 매칭된 텍스트의 유사도)
        confidence = self._calculate_similarity(slide.script, matched_text)

        return SlideTimingModel(
            slide_number=slide.slide_number,
            start_time=timing_info["start_time"],
            end_time=timing_info["end_time"],
            duration=timing_info["duration"],
            confidence=confidence,
            matched_text=matched_text
        )

    def match_script_to_segments(
        self,
        script: str,
        segments: List[WhisperSegmentModel]
    ) -> List[int]:
        """
        스크립트와 Whisper 세그먼트 매칭 (인덱스 반환)

        알고리즘:
        1. 스크립트를 문장 단위로 분리
        2. 각 문장과 연속된 세그먼트 그룹의 유사도 계산
        3. 가장 유사한 세그먼트 그룹 선택 (임계값 80% 이상)

        Args:
            script: 슬라이드 스크립트
            segments: Whisper 세그먼트 리스트

        Returns:
            매칭된 세그먼트 인덱스 리스트
        """
        if not segments:
            return []

        # 스크립트 정규화 (공백, 문장부호 제거)
        normalized_script = self._normalize_text(script)

        # 세그먼트 텍스트를 슬라이딩 윈도우로 결합하여 비교
        best_match_indices = []
        best_similarity = 0.0

        # 윈도우 크기: 1개부터 전체 세그먼트까지
        for window_size in range(1, len(segments) + 1):
            for start_idx in range(len(segments) - window_size + 1):
                end_idx = start_idx + window_size
                segment_group = segments[start_idx:end_idx]

                # 세그먼트 그룹 텍스트 결합
                combined_text = " ".join([seg.text.strip() for seg in segment_group])
                normalized_combined = self._normalize_text(combined_text)

                # 유사도 계산
                similarity = self._calculate_similarity(normalized_script, normalized_combined)

                # 최고 유사도 업데이트
                if similarity > best_similarity and similarity >= self.MIN_SIMILARITY_THRESHOLD:
                    best_similarity = similarity
                    best_match_indices = list(range(start_idx, end_idx))

        if best_match_indices:
            self.logger.debug(
                f"Matched segments {best_match_indices[0]}-{best_match_indices[-1]} "
                f"with similarity {best_similarity:.2%}"
            )

        return best_match_indices

    def calculate_slide_timing(
        self,
        matched_segments: List[WhisperSegmentModel]
    ) -> Dict[str, float]:
        """
        매칭된 세그먼트에서 시작/종료 시간 계산

        Args:
            matched_segments: 매칭된 Whisper 세그먼트 리스트

        Returns:
            {"start_time": float, "end_time": float, "duration": float}
        """
        if not matched_segments:
            return {
                "start_time": 0.0,
                "end_time": 0.0,
                "duration": 0.0
            }

        start_time = matched_segments[0].start
        end_time = matched_segments[-1].end
        duration = end_time - start_time

        return {
            "start_time": round(start_time, 2),
            "end_time": round(end_time, 2),
            "duration": round(duration, 2)
        }

    def validate_timing_accuracy(
        self,
        slide_timings: List[SlideTimingModel],
        expected_durations: List[float]
    ) -> float:
        """
        타이밍 정확도 검증 (0-100%)

        검증 기준:
        - 각 슬라이드의 confidence 평균
        - 예상 길이 대비 실제 길이 오차

        Args:
            slide_timings: 슬라이드 타이밍 리스트
            expected_durations: 예상 지속 시간 리스트

        Returns:
            정확도 (0.0-100.0)
        """
        if not slide_timings:
            return 0.0

        # 신뢰도 평균
        avg_confidence = sum(t.confidence for t in slide_timings) / len(slide_timings)

        # 길이 오차 계산 (옵션)
        duration_accuracy = 1.0
        if len(expected_durations) == len(slide_timings):
            duration_errors = [
                abs(expected - actual.duration) / max(expected, 0.1)
                for expected, actual in zip(expected_durations, slide_timings)
                if expected > 0
            ]
            if duration_errors:
                avg_error = sum(duration_errors) / len(duration_errors)
                duration_accuracy = max(0.0, 1.0 - avg_error)

        # 최종 정확도 (confidence 80%, duration 20% 가중치)
        final_accuracy = (avg_confidence * 0.8 + duration_accuracy * 0.2) * 100

        return round(final_accuracy, 2)

    def adjust_timing(
        self,
        slide_timings: List[SlideTimingModel],
        total_audio_duration: float
    ) -> List[SlideTimingModel]:
        """
        타이밍 미세 조정 (겹침 제거, 갭 최소화)

        조정 규칙:
        1. 슬라이드는 slide_number 순서대로 정렬
        2. 겹침 발생 시: 경계를 중간 지점으로 조정
        3. 갭 발생 시: 0.5초 이하면 메우기
        4. 마지막 슬라이드는 total_audio_duration까지 확장 가능

        Args:
            slide_timings: 원본 슬라이드 타이밍 리스트
            total_audio_duration: 전체 오디오 길이

        Returns:
            조정된 슬라이드 타이밍 리스트
        """
        if not slide_timings:
            return []

        # slide_number 기준 정렬
        sorted_timings = sorted(slide_timings, key=lambda t: t.slide_number)
        adjusted = []

        for i, timing in enumerate(sorted_timings):
            new_timing = timing.model_copy(deep=True)

            # 이전 슬라이드와 겹침/갭 확인
            if i > 0:
                prev_timing = adjusted[-1]

                # 겹침: 경계를 중간 지점으로 조정
                if new_timing.start_time < prev_timing.end_time:
                    midpoint = (prev_timing.end_time + new_timing.start_time) / 2
                    adjusted[-1].end_time = round(midpoint, 2)
                    adjusted[-1].duration = round(
                        adjusted[-1].end_time - adjusted[-1].start_time, 2
                    )
                    new_timing.start_time = round(midpoint, 2)
                    new_timing.duration = round(
                        new_timing.end_time - new_timing.start_time, 2
                    )

                    self.logger.debug(
                        f"Adjusted overlap between slide {prev_timing.slide_number} "
                        f"and {new_timing.slide_number} at {midpoint:.2f}s"
                    )

                # 갭: 0.5초 이하면 메우기
                elif new_timing.start_time - prev_timing.end_time <= 0.5:
                    gap = new_timing.start_time - prev_timing.end_time
                    # 이전 슬라이드를 갭의 절반만큼 연장
                    adjusted[-1].end_time = round(prev_timing.end_time + gap / 2, 2)
                    adjusted[-1].duration = round(
                        adjusted[-1].end_time - adjusted[-1].start_time, 2
                    )
                    # 현재 슬라이드 시작 시간 앞당기기
                    new_timing.start_time = round(new_timing.start_time - gap / 2, 2)
                    new_timing.duration = round(
                        new_timing.end_time - new_timing.start_time, 2
                    )

                    self.logger.debug(
                        f"Filled gap ({gap:.2f}s) between slide {prev_timing.slide_number} "
                        f"and {new_timing.slide_number}"
                    )

            # 마지막 슬라이드: total_audio_duration까지 확장 (갭이 1초 이하인 경우)
            if i == len(sorted_timings) - 1:
                if total_audio_duration - new_timing.end_time <= 1.0:
                    new_timing.end_time = round(total_audio_duration, 2)
                    new_timing.duration = round(
                        new_timing.end_time - new_timing.start_time, 2
                    )
                    self.logger.debug(
                        f"Extended last slide {new_timing.slide_number} to audio end"
                    )

            adjusted.append(new_timing)

        return adjusted

    async def _update_neo4j_timings(
        self,
        project_id: str,
        slide_timings: List[SlideTimingModel]
    ) -> None:
        """
        Neo4j Slide 노드에 타이밍 정보 업데이트

        Args:
            project_id: 프로젝트 ID
            slide_timings: 슬라이드 타이밍 리스트
        """
        span_context = logfire.span("slide_timing.update_neo4j") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context:
            for timing in slide_timings:
                query = """
                MATCH (proj:Project {project_id: $project_id})
                      -[:HAS_PRESENTATION]->(:Presentation)
                      -[:HAS_SLIDE]->(slide:Slide {slide_number: $slide_number})
                SET slide.start_time = $start_time,
                    slide.end_time = $end_time,
                    slide.duration = $duration,
                    slide.confidence = $confidence,
                    slide.matched_text = $matched_text,
                    slide.timing_updated_at = datetime()
                RETURN slide.slide_id as slide_id
                """

                result = self.neo4j_client.query(
                    query,
                    project_id=project_id,
                    slide_number=timing.slide_number,
                    start_time=timing.start_time,
                    end_time=timing.end_time,
                    duration=timing.duration,
                    confidence=timing.confidence,
                    matched_text=timing.matched_text or ""
                )

                if result:
                    self.logger.debug(
                        f"Updated Neo4j timing for slide {timing.slide_number}: "
                        f"{timing.start_time:.2f}s - {timing.end_time:.2f}s "
                        f"(confidence: {timing.confidence:.2%})"
                    )
                else:
                    self.logger.warning(
                        f"Failed to update Neo4j timing for slide {timing.slide_number}"
                    )

    # ==================== Helper Methods ====================

    def _normalize_text(self, text: str) -> str:
        """
        텍스트 정규화 (비교용)

        - 소문자 변환
        - 공백 정규화
        - 문장부호 제거 (일부)

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트
        """
        import re

        # 소문자 변환
        normalized = text.lower()

        # 문장부호 제거 (일부 유지)
        normalized = re.sub(r'[^\w\s가-힣]', '', normalized)

        # 연속 공백을 단일 공백으로
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 유사도 계산 (SequenceMatcher 사용)

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            유사도 (0.0-1.0)
        """
        # 정규화
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)

        # SequenceMatcher로 유사도 계산
        matcher = SequenceMatcher(None, norm1, norm2)
        ratio = matcher.ratio()

        return round(ratio, 4)


# 싱글톤 인스턴스
_slide_timing_analyzer_instance = None


def get_slide_timing_analyzer() -> SlideTimingAnalyzer:
    """SlideTimingAnalyzer 싱글톤 인스턴스"""
    global _slide_timing_analyzer_instance
    if _slide_timing_analyzer_instance is None:
        _slide_timing_analyzer_instance = SlideTimingAnalyzer()
    return _slide_timing_analyzer_instance
