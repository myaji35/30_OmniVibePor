"""OpenAI Whisper STT (Speech-to-Text) 서비스"""
from typing import Optional
import tempfile
from pathlib import Path
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logfire

from app.core.config import get_settings

settings = get_settings()


class STTService:
    """
    OpenAI Whisper v3 Speech-to-Text

    특징:
    - 99개 언어 지원
    - 높은 정확도
    - 타임스탬프 지원
    - 자동 언어 감지
    - Zero-Fault Audio Loop의 검증 단계에 사용
    """

    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logfire.get_logger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def transcribe(
        self,
        audio_file_path: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        language: str = "ko",
        response_format: str = "text",
        temperature: float = 0.0
    ) -> str:
        """
        음성을 텍스트로 변환

        Args:
            audio_file_path: 오디오 파일 경로
            audio_bytes: 오디오 바이트 (파일 경로 대신 사용 가능)
            language: 언어 코드 (ko, en 등)
            response_format: 응답 형식 (text, json, srt, vtt)
            temperature: 샘플링 온도 (0.0-1.0)

        Returns:
            변환된 텍스트
        """
        with self.logger.span("whisper.transcribe") as span:
            # 오디오 소스 확인
            if audio_file_path is None and audio_bytes is None:
                raise ValueError("Either audio_file_path or audio_bytes must be provided")

            # 바이트를 임시 파일로 저장
            if audio_bytes:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    audio_file_path = temp_file.name

            # 파일 크기 로깅
            file_size = Path(audio_file_path).stat().st_size
            span.set_attribute("file_size_bytes", file_size)
            span.set_attribute("language", language)

            # Whisper API 호출
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format=response_format,
                    temperature=temperature
                )

            # 응답 형식에 따라 텍스트 추출
            if response_format == "text":
                result_text = transcript
            elif response_format == "json":
                result_text = transcript.text
            else:
                result_text = str(transcript)

            # 비용 추적 (대략 1분당 $0.006)
            # 오디오 길이는 정확히 알 수 없으므로 파일 크기로 추정
            # 대략 1MB ≈ 1분 (MP3 128kbps 기준)
            estimated_minutes = file_size / (1024 * 1024)
            estimated_cost = estimated_minutes * 0.006
            self.logger.info(
                f"Transcribed ~{estimated_minutes:.2f}min audio, "
                f"estimated cost: ${estimated_cost:.4f}"
            )

            return result_text.strip()

    async def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: str = "ko"
    ) -> dict:
        """
        타임스탬프 포함 변환

        Args:
            audio_file_path: 오디오 파일 경로
            language: 언어 코드

        Returns:
            {"text": "전체 텍스트", "segments": [...]}
        """
        with self.logger.span("whisper.transcribe_with_timestamps"):
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            return {
                "text": transcript.text,
                "language": transcript.language,
                "duration": transcript.duration,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text
                    }
                    for seg in transcript.segments
                ]
            }

    async def translate_to_english(
        self,
        audio_file_path: str
    ) -> str:
        """
        음성을 영어로 번역 (Whisper의 translate 기능)

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            영어로 번역된 텍스트
        """
        with self.logger.span("whisper.translate"):
            with open(audio_file_path, "rb") as audio_file:
                translation = self.client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

            return translation.strip()

    def validate_audio_format(self, file_path: str) -> bool:
        """
        오디오 파일 형식 검증

        Args:
            file_path: 오디오 파일 경로

        Returns:
            지원 형식 여부
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.SUPPORTED_FORMATS


# 싱글톤 인스턴스
_stt_service_instance = None


def get_stt_service() -> STTService:
    """STT 서비스 싱글톤 인스턴스"""
    global _stt_service_instance
    if _stt_service_instance is None:
        _stt_service_instance = STTService()
    return _stt_service_instance
