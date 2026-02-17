"""Zero-Fault Audio Correction Loop - TTS → STT → 검증 → 재생성"""
from typing import Optional, Dict
from difflib import SequenceMatcher
import re
import logging
from contextlib import nullcontext
import io

from app.core.config import get_settings
from .tts_service import get_tts_service
from .stt_service import get_stt_service
from .text_normalizer import get_text_normalizer
from .duration_learning_system import get_learning_system

# Audio duration extraction
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

settings = get_settings()

# Logfire availability check
try:
    import logfire
    LOGFIRE_AVAILABLE = settings.LOGFIRE_TOKEN and settings.LOGFIRE_TOKEN != "your_logfire_token_here"
except Exception:
    LOGFIRE_AVAILABLE = False


class AudioCorrectionLoop:
    """
    Zero-Fault Audio 시스템

    워크플로우:
    1. ElevenLabs TTS로 오디오 생성
    2. OpenAI Whisper STT로 검증
    3. 원본 텍스트와 비교
    4. 정확도 95% 미만이면 재생성
    5. 최대 5회 시도

    목표: 발음 오류 제로화
    """

    def __init__(
        self,
        accuracy_threshold: float = 0.95,
        max_attempts: int = 5,
        enable_normalization: bool = True,
        enable_learning: bool = True
    ):
        """
        Args:
            accuracy_threshold: 정확도 임계값 (0.0-1.0)
            max_attempts: 최대 재시도 횟수
            enable_normalization: 한국어 텍스트 정규화 활성화 여부
            enable_learning: 실시간 학습 시스템 활성화 여부
        """
        self.tts = get_tts_service()
        self.stt = get_stt_service()
        self.normalizer = get_text_normalizer()
        self.learning_system = get_learning_system() if enable_learning else None
        self.accuracy_threshold = accuracy_threshold
        self.max_attempts = max_attempts
        self.enable_normalization = enable_normalization
        self.enable_learning = enable_learning
        self.logger = logging.getLogger(__name__)

    def get_audio_duration(self, audio_bytes: bytes) -> Optional[float]:
        """
        오디오 바이트에서 시간 추출 (초)

        Args:
            audio_bytes: MP3 오디오 바이트

        Returns:
            오디오 시간 (초) 또는 None (추출 실패 시)
        """
        if not PYDUB_AVAILABLE:
            self.logger.warning("pydub not available, cannot extract audio duration")
            return None

        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            duration_seconds = len(audio) / 1000.0  # milliseconds to seconds
            return duration_seconds
        except Exception as e:
            self.logger.error(f"Failed to extract audio duration: {e}")
            return None

    def calculate_similarity(self, original: str, transcribed: str) -> float:
        """
        텍스트 유사도 계산

        Args:
            original: 원본 텍스트
            transcribed: STT로 변환된 텍스트

        Returns:
            유사도 (0.0-1.0)
        """
        # 정규화 (대소문자, 공백, 구두점 제거)
        def normalize(text: str) -> str:
            # 소문자 변환
            text = text.lower()
            # 구두점 제거
            text = re.sub(r'[^\w\s]', '', text)
            # 연속 공백 제거
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        normalized_original = normalize(original)
        normalized_transcribed = normalize(transcribed)

        # SequenceMatcher로 유사도 계산
        similarity = SequenceMatcher(
            None,
            normalized_original,
            normalized_transcribed
        ).ratio()

        return similarity

    def analyze_mismatch(self, original: str, transcribed: str) -> Dict:
        """
        불일치 분석 (디버깅용)

        Args:
            original: 원본 텍스트
            transcribed: STT 텍스트

        Returns:
            분석 결과
        """
        original_words = original.split()
        transcribed_words = transcribed.split()

        # 단어 단위 비교
        mismatched_words = []
        for i, (orig, trans) in enumerate(zip(original_words, transcribed_words)):
            if orig.lower() != trans.lower():
                mismatched_words.append({
                    "position": i,
                    "expected": orig,
                    "actual": trans
                })

        # 길이 차이
        length_diff = abs(len(original_words) - len(transcribed_words))

        return {
            "mismatched_words": mismatched_words,
            "length_difference": length_diff,
            "original_length": len(original_words),
            "transcribed_length": len(transcribed_words)
        }

    async def generate_verified_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "ko",
        save_file: bool = True,
        **tts_kwargs
    ) -> Dict:
        """
        검증된 오디오 생성 (Zero-Fault Loop 실행)

        Args:
            text: 변환할 텍스트
            voice_id: 음성 ID
            language: 언어 코드
            save_file: 파일로 저장 여부
            **tts_kwargs: TTS에 전달할 추가 파라미터

        Returns:
            {
                "status": "success" | "partial_success" | "failed",
                "audio_path": "경로",
                "attempts": 시도 횟수,
                "final_similarity": 최종 유사도,
                "original_text": 원본 텍스트,
                "normalized_text": 정규화된 텍스트,
                "normalization_mappings": 정규화 매핑,
                "iterations": [각 시도별 상세 정보]
            }
        """
        span_context = logfire.span("audio_correction_loop.generate") if LOGFIRE_AVAILABLE else nullcontext()
        with span_context as main_span:
            # 1. 텍스트 정규화 (한국어 숫자 변환)
            normalized_text = text
            normalization_mappings = {}

            if self.enable_normalization and language == "ko":
                normalized_text, normalization_mappings = self.normalizer.normalize_script(text)
                self.logger.info(f"📝 Original: {text}")
                self.logger.info(f"📝 Normalized: {normalized_text}")
                if normalization_mappings:
                    self.logger.info(f"📝 Mappings: {normalization_mappings}")

            # Logfire 속성 설정
            if LOGFIRE_AVAILABLE:
                main_span.set_attribute("original_text_length", len(text))
                main_span.set_attribute("normalized_text_length", len(normalized_text))
                main_span.set_attribute("target_accuracy", self.accuracy_threshold)
                main_span.set_attribute("normalization_enabled", self.enable_normalization)

            iterations = []
            best_audio = None
            best_similarity = 0.0
            best_audio_path = None

            # 정규화된 텍스트로 TTS 생성
            tts_text = normalized_text

            for attempt in range(1, self.max_attempts + 1):
                attempt_span_context = logfire.span(f"attempt_{attempt}") if LOGFIRE_AVAILABLE else nullcontext()
                with attempt_span_context:
                    self.logger.info(f"🔄 Attempt {attempt}/{self.max_attempts}")

                    # 2. TTS 생성 (정규화된 텍스트 사용)
                    audio_bytes = await self.tts.generate_audio(
                        text=tts_text,
                        voice_id=voice_id,
                        **tts_kwargs
                    )

                    # 3. STT 검증
                    transcribed = await self.stt.transcribe(
                        audio_bytes=audio_bytes,
                        language=language
                    )

                    # 4. 유사도 계산 (정규화된 텍스트와 비교)
                    similarity = self.calculate_similarity(tts_text, transcribed)

                    # 5. 분석
                    mismatch_analysis = self.analyze_mismatch(tts_text, transcribed)

                    iteration_info = {
                        "attempt": attempt,
                        "similarity": similarity,
                        "transcribed_text": transcribed,
                        "mismatch_analysis": mismatch_analysis
                    }
                    iterations.append(iteration_info)

                    self.logger.info(
                        f"📊 Similarity: {similarity:.2%} "
                        f"(Threshold: {self.accuracy_threshold:.2%})"
                    )

                    # 최고 결과 추적
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_audio = audio_bytes

                    # 5. 임계값 체크
                    if similarity >= self.accuracy_threshold:
                        self.logger.info(
                            f"✅ SUCCESS at attempt {attempt} "
                            f"(Similarity: {similarity:.2%})"
                        )

                        # 6. 학습 시스템에 실제 오디오 시간 기록
                        if self.enable_learning and self.learning_system:
                            actual_duration = self.get_audio_duration(audio_bytes)
                            if actual_duration:
                                try:
                                    self.learning_system.record_prediction(
                                        text=text,
                                        language=language,
                                        actual_duration=actual_duration,
                                        platform=tts_kwargs.get("platform"),
                                        voice_id=voice_id
                                    )
                                    self.logger.info(
                                        f"📊 Recorded learning data: {actual_duration:.1f}s"
                                    )
                                except Exception as e:
                                    self.logger.warning(f"Failed to record learning data: {e}")

                        # 파일 저장
                        if save_file:
                            audio_path = await self.tts.save_audio(
                                audio_bytes=audio_bytes,
                                text=text
                            )
                        else:
                            audio_path = None

                        return {
                            "status": "success",
                            "audio_path": audio_path,
                            "attempts": attempt,
                            "final_similarity": similarity,
                            "original_text": text,
                            "normalized_text": tts_text,
                            "normalization_mappings": normalization_mappings,
                            "transcribed_text": transcribed,
                            "iterations": iterations
                        }

                    # 불일치 로깅
                    self.logger.warning(
                        f"❌ Mismatch detected:\n"
                        f"  Expected: '{text[:100]}...'\n"
                        f"  Got:      '{transcribed[:100]}...'\n"
                        f"  Mismatched words: {len(mismatch_analysis['mismatched_words'])}"
                    )

            # 최대 시도 후에도 실패
            self.logger.error(
                f"⚠️ Failed to achieve {self.accuracy_threshold:.0%} accuracy "
                f"after {self.max_attempts} attempts. "
                f"Best similarity: {best_similarity:.2%}"
            )

            # 최고 결과 저장
            if save_file and best_audio:
                audio_path = await self.tts.save_audio(
                    audio_bytes=best_audio,
                    text=text
                )
            else:
                audio_path = None

            return {
                "status": "partial_success" if best_similarity > 0.8 else "failed",
                "audio_path": audio_path,
                "attempts": self.max_attempts,
                "original_text": text,
                "normalized_text": tts_text,
                "normalization_mappings": normalization_mappings,
                "final_similarity": best_similarity,
                "transcribed_text": iterations[-1]["transcribed_text"],
                "iterations": iterations,
                "warning": f"Could not achieve target accuracy ({self.accuracy_threshold:.0%})"
            }

    async def batch_generate(
        self,
        texts: list[str],
        voice_id: Optional[str] = None,
        language: str = "ko"
    ) -> list[Dict]:
        """
        여러 텍스트 배치 처리

        Args:
            texts: 텍스트 리스트
            voice_id: 음성 ID
            language: 언어 코드

        Returns:
            각 텍스트의 결과 리스트
        """
        results = []
        for i, text in enumerate(texts):
            self.logger.info(f"Processing batch {i+1}/{len(texts)}")
            result = await self.generate_verified_audio(
                text=text,
                voice_id=voice_id,
                language=language
            )
            results.append(result)

        # 통계
        success_count = sum(1 for r in results if r["status"] == "success")
        avg_attempts = sum(r["attempts"] for r in results) / len(results)
        avg_similarity = sum(r["final_similarity"] for r in results) / len(results)

        self.logger.info(
            f"Batch completed: {success_count}/{len(texts)} succeeded, "
            f"avg attempts: {avg_attempts:.1f}, "
            f"avg similarity: {avg_similarity:.2%}"
        )

        return results


# 싱글톤 인스턴스
_audio_loop_instance = None


def get_audio_correction_loop() -> AudioCorrectionLoop:
    """Audio Correction Loop 싱글톤 인스턴스"""
    global _audio_loop_instance
    if _audio_loop_instance is None:
        _audio_loop_instance = AudioCorrectionLoop()
    return _audio_loop_instance
