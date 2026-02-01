"""DurationLearningSystem - 실시간 시간 예측 학습

REALPLAN.md Phase 3.4 구현

기능:
- 실제 TTS 시간과 예측 시간 비교
- 자동 보정 계수 업데이트
- 학습 데이터 Neo4j 저장
- 언어별/플랫폼별 정확도 추적
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass

from app.services.duration_calculator import get_duration_calculator, Language
from app.services.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


@dataclass
class DurationLearningRecord:
    """시간 예측 학습 레코드"""
    text: str
    language: str
    predicted_duration: float  # 예측 시간 (초)
    actual_duration: float     # 실제 TTS 시간 (초)
    accuracy: float            # 정확도 (%)
    correction_factor: float   # 보정 후 계수
    platform: Optional[str] = None
    voice_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class DurationLearningSystem:
    """실시간 시간 예측 학습 시스템"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j = get_neo4j_client()

    def record_prediction(
        self,
        text: str,
        language: str,
        actual_duration: float,
        platform: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> DurationLearningRecord:
        """
        예측 결과 기록 및 학습

        Args:
            text: 원본 텍스트
            language: 언어 코드
            actual_duration: 실제 TTS 시간 (초)
            platform: 플랫폼 (선택)
            voice_id: 음성 ID (선택)

        Returns:
            학습 레코드
        """
        try:
            # 1. 현재 예측 계산
            lang = Language(language)
            calculator = get_duration_calculator(lang)
            prediction = calculator.calculate(text)
            predicted_duration = prediction['duration']

            # 2. 정확도 계산
            accuracy = self._calculate_accuracy(predicted_duration, actual_duration)

            # 3. 보정 계수 업데이트
            old_factor = calculator.correction_factor
            calculator.update_correction_factor(predicted_duration, actual_duration)
            new_factor = calculator.correction_factor

            # 4. 학습 레코드 생성
            record = DurationLearningRecord(
                text=text,
                language=language,
                predicted_duration=predicted_duration,
                actual_duration=actual_duration,
                accuracy=accuracy,
                correction_factor=new_factor,
                platform=platform,
                voice_id=voice_id,
                timestamp=datetime.now()
            )

            # 5. Neo4j에 저장
            self._save_to_neo4j(record)

            self.logger.info(
                f"[Learning] Language={language}, "
                f"Predicted={predicted_duration:.1f}s, "
                f"Actual={actual_duration:.1f}s, "
                f"Accuracy={accuracy:.1f}%, "
                f"Factor: {old_factor:.3f} → {new_factor:.3f}"
            )

            return record

        except Exception as e:
            self.logger.error(f"Failed to record prediction: {e}")
            raise

    def _calculate_accuracy(self, predicted: float, actual: float) -> float:
        """
        정확도 계산 (%)

        Args:
            predicted: 예측 시간
            actual: 실제 시간

        Returns:
            정확도 (0-100%)
        """
        if actual == 0:
            return 0.0

        error = abs(predicted - actual)
        accuracy = max(0, 100 - (error / actual * 100))
        return accuracy

    def _save_to_neo4j(self, record: DurationLearningRecord):
        """
        학습 레코드를 Neo4j에 저장

        Args:
            record: 학습 레코드
        """
        query = """
        CREATE (lr:LearningRecord {
            text: $text,
            language: $language,
            predicted_duration: $predicted_duration,
            actual_duration: $actual_duration,
            accuracy: $accuracy,
            correction_factor: $correction_factor,
            platform: $platform,
            voice_id: $voice_id,
            timestamp: datetime($timestamp)
        })
        RETURN lr
        """

        params = {
            "text": record.text[:500],  # 텍스트는 500자로 제한
            "language": record.language,
            "predicted_duration": record.predicted_duration,
            "actual_duration": record.actual_duration,
            "accuracy": record.accuracy,
            "correction_factor": record.correction_factor,
            "platform": record.platform,
            "voice_id": record.voice_id,
            "timestamp": record.timestamp.isoformat() if record.timestamp else datetime.now().isoformat()
        }

        self.neo4j.query(query, params)
        self.logger.debug(f"Saved learning record to Neo4j: {record}")

    def get_learning_stats(
        self,
        language: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> Dict:
        """
        학습 통계 조회

        Args:
            language: 언어 필터 (선택)
            platform: 플랫폼 필터 (선택)
            limit: 최대 레코드 수

        Returns:
            통계 정보
        """
        query = """
        MATCH (lr:LearningRecord)
        """

        conditions = []
        params = {"limit": limit}

        if language:
            conditions.append("lr.language = $language")
            params["language"] = language

        if platform:
            conditions.append("lr.platform = $platform")
            params["platform"] = platform

        if conditions:
            query += "WHERE " + " AND ".join(conditions) + " "

        query += """
        WITH lr
        ORDER BY lr.timestamp DESC
        LIMIT $limit
        RETURN
            count(lr) as total_records,
            avg(lr.accuracy) as avg_accuracy,
            avg(lr.correction_factor) as avg_correction_factor,
            min(lr.accuracy) as min_accuracy,
            max(lr.accuracy) as max_accuracy,
            collect({
                predicted: lr.predicted_duration,
                actual: lr.actual_duration,
                accuracy: lr.accuracy,
                timestamp: lr.timestamp
            }) as recent_records
        """

        result = self.neo4j.query(query, params)

        if not result:
            return {
                "total_records": 0,
                "avg_accuracy": 0.0,
                "avg_correction_factor": 1.0,
                "min_accuracy": 0.0,
                "max_accuracy": 0.0,
                "recent_records": []
            }

        return result[0]

    def get_accuracy_by_language(self) -> List[Dict]:
        """
        언어별 정확도 조회

        Returns:
            언어별 통계 리스트
        """
        query = """
        MATCH (lr:LearningRecord)
        WITH lr.language as language,
             count(lr) as total,
             avg(lr.accuracy) as avg_accuracy,
             avg(lr.correction_factor) as avg_factor
        RETURN language, total, avg_accuracy, avg_factor
        ORDER BY total DESC
        """

        results = self.neo4j.query(query, {})
        return results

    def get_accuracy_trend(
        self,
        language: str,
        days: int = 7
    ) -> List[Dict]:
        """
        시간별 정확도 트렌드 조회

        Args:
            language: 언어 코드
            days: 조회 기간 (일)

        Returns:
            트렌드 데이터
        """
        query = """
        MATCH (lr:LearningRecord {language: $language})
        WHERE lr.timestamp >= datetime() - duration({days: $days})
        WITH lr
        ORDER BY lr.timestamp ASC
        RETURN
            lr.timestamp as timestamp,
            lr.accuracy as accuracy,
            lr.correction_factor as correction_factor,
            lr.predicted_duration as predicted,
            lr.actual_duration as actual
        """

        results = self.neo4j.query(query, {"language": language, "days": days})
        return results


# ==================== 싱글톤 인스턴스 ====================

_learning_system: Optional[DurationLearningSystem] = None


def get_learning_system() -> DurationLearningSystem:
    """
    DurationLearningSystem 싱글톤 인스턴스

    Returns:
        DurationLearningSystem 인스턴스
    """
    global _learning_system
    if _learning_system is None:
        _learning_system = DurationLearningSystem()
    return _learning_system
