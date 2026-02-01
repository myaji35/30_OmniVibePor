"""Zero-Fault Audio Correction Loop - TTS → STT → 검증 → 재생성"""
from typing import Optional, Dict
from difflib import SequenceMatcher
import re
import logfire

from .tts_service import get_tts_service
from .stt_service import get_stt_service


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
        max_attempts: int = 5
    ):
        """
        Args:
            accuracy_threshold: 정확도 임계값 (0.0-1.0)
            max_attempts: 최대 재시도 횟수
        """
        self.tts = get_tts_service()
        self.stt = get_stt_service()
        self.accuracy_threshold = accuracy_threshold
        self.max_attempts = max_attempts
        self.logger = logfire.get_logger(__name__)

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
                "iterations": [각 시도별 상세 정보]
            }
        """
        with self.logger.span("audio_correction_loop.generate") as main_span:
            main_span.set_attribute("text_length", len(text))
            main_span.set_attribute("target_accuracy", self.accuracy_threshold)

            iterations = []
            best_audio = None
            best_similarity = 0.0
            best_audio_path = None

            for attempt in range(1, self.max_attempts + 1):
                with self.logger.span(f"attempt_{attempt}"):
                    self.logger.info(f"🔄 Attempt {attempt}/{self.max_attempts}")

                    # 1. TTS 생성
                    audio_bytes = await self.tts.generate_audio(
                        text=text,
                        voice_id=voice_id,
                        **tts_kwargs
                    )

                    # 2. STT 검증
                    transcribed = await self.stt.transcribe(
                        audio_bytes=audio_bytes,
                        language=language
                    )

                    # 3. 유사도 계산
                    similarity = self.calculate_similarity(text, transcribed)

                    # 4. 분석
                    mismatch_analysis = self.analyze_mismatch(text, transcribed)

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
                            "audio_bytes": audio_bytes,
                            "attempts": attempt,
                            "final_similarity": similarity,
                            "original_text": text,
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
                "audio_bytes": best_audio,
                "attempts": self.max_attempts,
                "final_similarity": best_similarity,
                "original_text": text,
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
